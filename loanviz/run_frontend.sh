#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_frontend.sh – Start the LoanViz frontend (Streamlit)
#
# Usage:
#   ./run_frontend.sh
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Install dependencies if needed ──────────────────────────────────────────
if [ ! -d "frontend/.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv frontend/.venv
    source frontend/.venv/bin/activate
    pip install -q -r frontend/requirements.txt
else
    source frontend/.venv/bin/activate
fi

# ── Start Streamlit ─────────────────────────────────────────────────────────
echo "🚀 Starting frontend on http://localhost:8501 ..."
cd frontend
streamlit run app.py --server.port 8501 --server.address 0.0.0.0