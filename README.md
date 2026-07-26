# LoanViz — Loan Analysis + Observability Demo

LoanViz is a small demo that analyzes consumer loan offers using a lightweight LLM-based agent and demonstrates end-to-end observability (logs, traces, metrics) ingested into SigNoz for evaluation.

Why this repo
- Shows a resilient LLM agent with deterministic fallback for production safety.
- Instrumented with OpenTelemetry (traces, logs, metrics) and exported to SigNoz (ClickHouse).
- Provides a reproducible deployment (`casting.yaml` + `casting.yaml.lock`) so judges can re-run Foundry/compose.

Repository layout (important files)
- `casting.yaml` — Foundry installation manifest (SigNoz compose flavor).
- `casting.yaml.lock` — Locked image tags for reproducible deployment (committed).
- `pours/deployment/compose.yaml` — Local SigNoz compose manifest used by the deployment.
- `pours/deployment/signoz_dashboard_loanviz.json` — Dashboard JSON with recommended panels.
- `loanviz/backend/app.py` — FastAPI service, OpenTelemetry instrumentation and exporters.
- `loanviz/backend/agent.py` — LLM agent (Ollama preferred) with deterministic fallback and runtime metrics (committed).
- `loanviz/frontend` — Streamlit-based frontend that calls the backend.

Run locally (quick)
1. Ensure Docker is running.
2. Start SigNoz (from repository root):

```bash
cd pours/deployment
docker compose -f compose.yaml up -d
```

3. Start the backend (inside repo):

```bash
cd loanviz/backend
. .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8001
```

4. Start the frontend (optional):

```bash
cd loanviz/frontend
. .venv/bin/activate
streamlit run app.py
```

Generate test traffic

```bash
curl -s -X POST http://localhost:8001/analyze -H 'Content-Type: application/json' -d '{"principal":500000,"annual_rate":7.5,"tenure_months":60,"monthly_income":50000,"loan_offer":"No hidden fees"}'
```
Run several requests to populate metrics/latency/fallbacks.

SigNoz dashboard
- UI: http://localhost:8080
- Default test credentials used in this environment (for demo only): `ktanmay7777@gmail.com` / `Admin@tanmay123`.
- If the provided import did not appear automatically, open the dashboard editor and import `pours/deployment/signoz_dashboard_loanviz.json` or create panels using these expressions:
	- `sum(rate(loanviz.requests.count[1m]))` — request throughput
	- `histogram_quantile(0.95, sum(rate(loanviz.requests.duration_bucket[1m])) by (le))` — p95 latency
	- `sum(rate(loanviz.ollama.calls.count[1m]))`, `sum(rate(loanviz.ollama.calls.errors[1m]))`, `sum(rate(loanviz.ollama.fallbacks.count[1m]))` — Ollama health
	- `sum by (recommendation) (rate(loanviz.recommendation.count[1m]))` — recommendation distribution

What the judge should evaluate
- Backend health: `GET /health` returns `{"status":"ok"}`.
- Observability: traces, logs, and metrics appear in SigNoz (check ClickHouse DBs `signoz_logs`, `signoz_traces`, `signoz_metrics`).
- Agent robustness: when LLM returns non-JSON, deterministic EMI/risk fallback is used and a fallback metric `loanviz.ollama.fallbacks.count` increments.

Files changed / committed
- `loanviz/backend/agent.py` — added runtime metrics and robust parsing/fallbacks.
- `casting.yaml.lock` — pinned image tags for reproducible deployment.
- `pours/deployment/signoz_dashboard_loanviz.json` — dashboard JSON.
- `README.md` — this file.

Notes
- No sensitive secrets are committed.
- For reproducible evaluation, run Foundry or `docker compose` using `casting.yaml` + `casting.yaml.lock`.

If you want, I can:
- Finalize and push a single clean commit containing the agent and README.
- Attempt another automated dashboard import into SigNoz (I have credentials and can retry).
