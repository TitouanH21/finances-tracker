#!/bin/bash
set -e

echo "[INFO] Starting Streamlit Finance Tracker..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "[WARN] DATABASE_URL not set, using SQLite"
    export DATABASE_URL="sqlite:///finance.db"
else
    echo "[INFO] Using PostgreSQL: DATABASE_URL is set"
fi

# Start Streamlit
exec streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.headless=true \
    --client.showErrorDetails=false \
    --logger.level=info
