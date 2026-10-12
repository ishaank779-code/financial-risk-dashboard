#!/bin/bash
# Quick start script for Financial Risk Dashboard
set -e
cd "$(dirname "$0")"

echo "=== Quilo Financial Risk Dashboard ==="

# Activate venv if present
if [ -d "venv" ]; then
  source venv/bin/activate
elif [ -d "/tmp/frd_venv" ]; then
  source /tmp/frd_venv/bin/activate
fi

export DATABASE_URL="${DATABASE_URL:-mysql+pymysql://riskuser:riskpass@localhost/financial_risk}"
export SECRET_KEY="${SECRET_KEY:-quilo-dev-secret}"

echo "Starting server on http://0.0.0.0:5000 ..."
cd backend
python app.py
