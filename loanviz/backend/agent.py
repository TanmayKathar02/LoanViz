import json
import os

from langchain_openai import ChatOpenAI

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover
    ChatOllama = None

def get_llm():
    """Initialize and return an LLM instance, preferring local Ollama when available."""
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    if ChatOllama is not None and os.getenv("USE_OLLAMA", "true").lower() == "true":
        return ChatOllama(model=ollama_model, temperature=0.2, timeout=60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    return ChatOpenAI(
        model="deepseek-ai/deepseek-v4-flash",
        temperature=0.2,
        openai_api_key=api_key,
        base_url="https://api.bluesminds.com/v1",
        timeout=20,
        max_retries=0,
    )


def run_agent_query(inputs: dict) -> dict:
    """Run the loan analysis agent with the given inputs.

    Args:
        inputs: Dictionary containing:
            - principal (float): Loan principal amount.
            - annual_rate (float): Annual interest rate in percentage.
            - tenure_months (int): Loan tenure in months.
            - monthly_income (float): Monthly income of the borrower.
            - loan_offer (str): Text of the loan offer.

    Returns:
        Dictionary with keys: emi, fees, risk, recommendation.
        On failure, returns a dictionary with an "error" key.
    """
    # Lazy metric instruments (created only at runtime to avoid import-time
    # meter creation before the app sets a MeterProvider)
    _meter = None
    _ollama_calls = None
    _ollama_errors = None
    _ollama_fallbacks = None
    _ollama_latency = None

    def ensure_metrics():
        nonlocal _meter, _ollama_calls, _ollama_errors, _ollama_fallbacks, _ollama_latency
        if _meter is not None:
            return
        try:
            from opentelemetry.metrics import get_meter
            _meter = get_meter("loanviz-agent")
            _ollama_calls = _meter.create_counter(
                "loanviz.ollama.calls.count",
                description="Number of Ollama LLM invocations",
            )
            _ollama_errors = _meter.create_counter(
                "loanviz.ollama.calls.errors",
                description="Number of failed Ollama invocations",
            )
            _ollama_fallbacks = _meter.create_counter(
                "loanviz.ollama.fallbacks.count",
                description="Number of times the agent used deterministic fallback",
            )
            _ollama_latency = _meter.create_histogram(
                "loanviz.ollama.latency",
                unit="ms",
                description="Latency of Ollama LLM invocations in ms",
            )
        except Exception:
            # Metrics are best-effort — if not available, continue without them
            _meter = None

    try:
        principal = inputs["principal"]
        annual_rate = inputs["annual_rate"]
        tenure_months = inputs["tenure_months"]
        monthly_income = inputs["monthly_income"]
        loan_offer = inputs["loan_offer"]

        llm = get_llm()

        # Prepare metrics instruments lazily
        ensure_metrics()

        prompt = (
            f"Given principal {principal}, annual interest rate {annual_rate}%, "
            f"tenure {tenure_months} months, monthly income ₹{monthly_income}, "
            f"and loan offer: {loan_offer}. "
            "Calculate EMI, detect any hidden fees, assess risk based on "
            "EMI-to-income ratio, and provide a recommendation. "
            "Return the result as a valid JSON object with keys: emi, fees, risk, recommendation."
        )

        # Call the LLM and record metrics (best-effort)
        response = None
        content = ""
        try:
            import time as _t
            _start = _t.perf_counter()
            response = llm.invoke(prompt)
            _dur = (_t.perf_counter() - _start) * 1000.0
            if _ollama_calls is not None:
                _ollama_calls.add(1, {})
            if _ollama_latency is not None:
                _ollama_latency.record(_dur, {})
            content = response.content if hasattr(response, "content") else str(response)
        except Exception as _e:
            # record an Ollama invocation error metric
            if _ollama_errors is not None:
                _ollama_errors.add(1, {})
            # continue to fallback path; set content to the exception string
            content = str(_e)

        # Try to parse JSON from the response content
        # The model may wrap JSON in markdown code blocks
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()

        try:
            result = json.loads(json_str)

            # Ensure all expected keys are present with defaults
            return {
                "emi": result.get("emi", 0.0),
                "fees": result.get(
                    "fees",
                    result.get(
                        "hidden_fees",
                        {"has_fee": False},
                    ),
                ),
                "risk": result.get("risk", "UNKNOWN"),
                "recommendation": result.get("recommendation", ""),
            }
        except Exception as parse_err:
            # Log the raw content for debugging and fall back to deterministic
            # EMI + risk calculation so the demo continues even when the LLM
            # output isn't strict JSON.
            # record a fallback metric
            try:
                if _ollama_fallbacks is not None:
                    _ollama_fallbacks.add(1, {})
            except Exception:
                pass
            try:
                from pathlib import Path

                Path("/tmp/loanviz_latest_model_output.txt").write_text(json_str)
            except Exception:
                pass

            # Deterministic EMI calculation
            try:
                P = float(principal)
                annual = float(annual_rate)
                n = int(tenure_months)
                monthly_rate = annual / 12.0 / 100.0
                if monthly_rate == 0:
                    emi = round(P / n, 2)
                else:
                    emi = P * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)
                    emi = round(emi, 2)
            except Exception:
                emi = 0.0

            # Simple fees/risk heuristics
            fees = 0.0
            risk = "UNKNOWN"
            recommendation = ""
            try:
                ratio = emi / float(monthly_income) if float(monthly_income) > 0 else 0
                if ratio < 0.2:
                    risk = "LOW"
                    recommendation = "Approved"
                elif ratio < 0.35:
                    risk = "MEDIUM"
                    recommendation = "Consider with Caution"
                else:
                    risk = "HIGH"
                    recommendation = "Not Recommended"
            except Exception:
                pass

            return {"emi": emi, "fees": {"has_fee": False}, "risk": risk, "recommendation": recommendation}

    except Exception as e:
        return {"error": str(e)}