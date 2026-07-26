# LoanViz

**LoanViz** is a financial AI agent designed for education loan transparency. It helps hackathon judges and users understand, analyze, and visualize education loan data through an intelligent conversational interface.

## Features

- **AI-Powered Loan Analysis** — Uses LangChain and OpenAI to provide intelligent insights on education loan applications, terms, and conditions.
- **Real-Time Observability** — Integrated with SigNoz and OpenTelemetry for full tracing, metrics, and monitoring of every AI agent interaction.
- **Interactive Dashboard** — Streamlit-based frontend for querying loan data and visualizing results.
- **FastAPI Backend** — High-performance async API serving loan analysis requests.

## Architecture

```
loanviz/
├── backend/          # FastAPI + LangChain AI agent
│   └── requirements.txt
├── frontend/         # Streamlit dashboard
│   └── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- SigNoz (running at `http://localhost:8080`)
- OpenTelemetry Collector (running at `http://localhost:4317`)
- OpenAI API key

## Getting Started

1. **Clone the repository** and navigate to the project root.
2. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. **Install frontend dependencies:**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```
4. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```
5. **Run the backend:**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```
6. **Run the frontend:**
   ```bash
   cd frontend
   streamlit run app.py
   ```

## Observability

LoanViz uses OpenTelemetry to export traces and metrics to SigNoz, providing end-to-end visibility into:

- LLM calls and token usage
- API request/response latencies
- Error rates and exceptions
- User interaction flows

## Use Case

Built for hackathon judges to test and evaluate AI agent capabilities in the financial domain, specifically focused on making education loan information more transparent and accessible.