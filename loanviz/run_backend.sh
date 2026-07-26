#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_backend.sh – Start the LoanViz backend (FastAPI / uvicorn)
#
# Usage:
#   ./run_backend.sh
#
# The script will look for an OPENAI_API_KEY in the environment. If it is not
# set, it will prompt you to paste it.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Check / prompt for OPENAI_API_KEY ──────────────────────────────────────
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "🔑 OPENAI_API_KEY is not set."
    read -rsp "Please paste your OpenAI / DeepSeek API key (input hidden): " api_key
    echo
    if [ -z "$api_key" ]; then
        echo "❌ No API key provided. Exiting."
        exit 1
    fi
    export OPENAI_API_KEY="$api_key"
fi

echo "✅ OPENAI_API_KEY is set."

# ── Install dependencies if needed ──────────────────────────────────────────
if [ ! -d "backend/.venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv backend/.venv
    source backend/.venv/bin/activate
    pip install -q -r backend/requirements.txt
else
    source backend/.venv/bin/activate
fi

# ── Start uvicorn ───────────────────────────────────────────────────────────
echo "🚀 Starting backend on http://localhost:8000 ..."
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload