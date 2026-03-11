#!/bin/bash
# CMS Automation Backend Entry Point

set -e

echo "Starting CMS Automation Backend..."

echo "Running database migrations..."
python -m alembic upgrade head || echo "WARNING: Migration failed, continuing anyway"

echo "Starting API Server (Uvicorn)..."
echo "Listening on port: ${PORT:-8080}"
exec uvicorn src.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --workers 1 \
  --log-level info \
  --no-access-log
