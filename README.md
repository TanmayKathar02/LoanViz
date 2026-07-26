# LoanViz – Transparent Loan Decisions with Full AI Observability

## 🎯 The Problem
STEM students in India take education loans without clarity on hidden fees, future EMIs, or risk. **40%+** report severe anxiety about repayment due to opaque loan terms and fine print.

---

## 💡 The Solution
**LoanViz** is an AI-powered loan assistant that:

- Calculates **EMI** instantly.
- **Detects hidden fees** (processing, insurance, admin charges) from offer text.
- **Assesses risk** (High/Medium/Low) based on EMI-to-income ratio.
- **Explains every decision** – no black boxes.
The entire AI reasoning process (agent steps, tool calls, token usage, latency) is **traced in real-time** via OpenTelemetry and visualized in **SigNoz**.

---

## 🛠️ Tech Stack

ComponentTechnology
**Backend**FastAPI (Python)
**AI Agent**LangChain + LangGraph (Ollama)
**Frontend**Streamlit
**Observability**OpenTelemetry + OpenInference (LangChain instrumentation)
**Monitoring**SigNoz (via Foundry / ClickHouse)
**Deployment**Docker Compose (Foundry)

---

## 🚀 Quick Setup 

### 1. Clone & Start SigNoz
bash

```
git clone <your-repo>
cd loanviz

# Install Foundry & deploy SigNoz
curl -fsSL https://signoz.io/foundry.sh | bash
export PATH="$HOME/.local/bin:$PATH"
foundryctl cast -f casting.yaml   # spins up SigNoz on port 8080
```

### 2. Set Environment Variables
bash

```
export OPENAI_API_KEY="your-deepseek-key"
export OPENAI_BASE_URL="https://api.bluesminds.co"
```

### 3. Run the Backend
bash

```
cd loanviz/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001
```

### 4. Run the Frontend
bash

```
cd loanviz/frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

---

## 🔍 How to Verify Observability (The Hackathon Win)

### 1. Send a Test Request
bash

```
curl -X POST http://localhost:8001/analyze \
	-H "Content-Type: application/json" \
	-d '{"principal":2000000,"annual_rate":8.5,"tenure_months":60,"monthly_income":50000,"loan_offer":"SBI with processing fee"}'
```

### 2. See the Trace in SigNoz

- Open `http://localhost:8080`
- Go to **Traces** → filter by service `loanviz-agent`
- Click the latest trace to view the **waterfall** showing:

- `loan_analysis_workflow` (root)
- `calculate_emi` (child)
- `detect_fees` (child)
- `calculate_risk` (child)

### 3. Custom Dashboard (Import)

- In SigNoz, go to **Dashboards** → **Import JSON**
- Upload `pours/deployment/signoz_dashboard_loanviz.json`
- See metrics: request throughput, p95 latency, hidden fee detection rate, risk distribution.

