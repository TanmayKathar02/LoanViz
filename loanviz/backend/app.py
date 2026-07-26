import logging
import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import get_meter, set_meter_provider
from opentelemetry.sdk._logs import LogRecordProcessor, LoggerProvider, LoggingHandler
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from pydantic import BaseModel, model_validator

from agent import run_agent_query

# ---------------------------------------------------------------------------
# OpenTelemetry setup
# ---------------------------------------------------------------------------
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
otel_logs_endpoint = os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", otel_endpoint)
otel_insecure = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"
resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "loanviz-agent")})

# Trace exporter
tracer_provider = TracerProvider(resource=resource)
otlp_trace_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=otel_insecure)
span_processor = BatchSpanProcessor(otlp_trace_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

# Log exporter
class SimpleLogRecordProcessor(LogRecordProcessor):
    def __init__(self, exporter: OTLPLogExporter):
        self._exporter = exporter

    def emit(self, log_data):
        self._exporter.export([log_data])

    def shutdown(self):
        self._exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._exporter.force_flush(timeout_millis)

logger_provider = LoggerProvider(resource=resource)
log_exporter = OTLPLogExporter(endpoint=otel_logs_endpoint, insecure=otel_insecure)
logger_provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))
set_logger_provider(logger_provider)

# Metric exporter
otlp_metrics_exporter = OTLPMetricExporter(endpoint=otel_endpoint, insecure=otel_insecure)
metrics_reader = PeriodicExportingMetricReader(otlp_metrics_exporter, export_interval_millis=5000)
meter_provider = MeterProvider(metric_readers=[metrics_reader], resource=resource)
set_meter_provider(meter_provider)

meter = get_meter("loanviz-agent")
request_counter = meter.create_counter(
    "loanviz.requests.count",
    description="Total analyze requests processed by LoanViz backend",
)
request_duration_histogram = meter.create_histogram(
    "loanviz.requests.duration",
    unit="ms",
    description="Analyze request duration in milliseconds",
)
recommendation_counter = meter.create_counter(
    "loanviz.recommendation.count",
    description="Count of recommendation outcomes returned by LoanViz agent",
)
risk_counter = meter.create_counter(
    "loanviz.risk.level.count",
    description="Count of risk levels reported by LoanViz agent",
)

# Application logger
logging.basicConfig(level=logging.INFO)
app_logger = logging.getLogger("loanviz")
app_logger.setLevel(logging.INFO)
app_logger.propagate = False
app_logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

LangChainInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="LoanViz Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_months: int
    monthly_income: float
    loan_offer_text: str | None = None
    loan_offer: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_offer_field(cls, values):
        if isinstance(values, dict):
            if values.get("loan_offer_text") is None and values.get("loan_offer") is not None:
                values = dict(values)
                values["loan_offer_text"] = values["loan_offer"]
        return values


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    app_logger.info("health check requested")
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    start_time = time.perf_counter()
    with tracer.start_as_current_span("loan_analysis_workflow") as parent_span:
        parent_span.set_attribute("loan.principal", req.principal)
        parent_span.set_attribute("loan.rate", req.annual_rate)
        parent_span.set_attribute("loan.tenure", req.tenure_months)
        parent_span.set_attribute("loan.monthly_income", req.monthly_income)

        with tracer.start_as_current_span("agent_run") as child_span:
            inputs = {
                "principal": req.principal,
                "annual_rate": req.annual_rate,
                "tenure_months": req.tenure_months,
                "monthly_income": req.monthly_income,
                "loan_offer": req.loan_offer_text,
            }

            result = run_agent_query(inputs)

            recommendation = result.get("recommendation", "")
            decision_value = str(recommendation) if recommendation is not None else "unknown"
            child_span.set_attribute("agent.decision", decision_value)

        parent_span.set_attribute("agent.decision", decision_value)

    duration_ms = (time.perf_counter() - start_time) * 1000
    status = "error" if result.get("error") else "ok"
    risk_value = str(result.get("risk", "UNKNOWN"))

    request_counter.add(
        1,
        {
            "status": status,
            "recommendation": decision_value,
            "risk": risk_value,
        },
    )
    request_duration_histogram.record(duration_ms, {"status": status})
    recommendation_counter.add(1, {"recommendation": decision_value})
    risk_counter.add(1, {"risk": risk_value})

    app_logger.info(
        "analyze request completed",
        extra={
            "status": status,
            "recommendation": decision_value,
            "risk": risk_value,
            "duration_ms": round(duration_ms, 2),
        },
    )

    return result