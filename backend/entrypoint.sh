#!/bin/bash
# CMS Automation Backend Entry Point
# Supports running as API server or Celery worker

set -e

# Get the service type from environment variable
SERVICE_TYPE="${SERVICE_TYPE:-api}"

echo "Starting CMS Automation Backend - Service Type: $SERVICE_TYPE"

case "$SERVICE_TYPE" in
  api)
    echo "Starting API Server (Uvicorn)..."
    exec uvicorn src.main:app \
      --host 0.0.0.0 \
      --port "${PORT:-8000}" \
      --workers 1 \
      --log-level info \
      --no-access-log
    ;;

  worker)
    echo "Starting Celery Worker with health check server..."

    # Start a simple HTTP health check server in the background
    python3 -m http.server "${PORT:-8080}" &
    HTTP_SERVER_PID=$!

    # Start Celery Worker
    exec celery -A src.workers.celery_app worker \
      --loglevel=info \
      --concurrency=2 \
      --max-tasks-per-child=50 \
      --queues=article_generation,publishing
    ;;

  beat)
    echo "Starting Celery Beat (Scheduler)..."
    exec celery -A src.workers.celery_app beat \
      --loglevel=info
    ;;

  *)
    echo "ERROR: Unknown SERVICE_TYPE: $SERVICE_TYPE"
    echo "Valid options: api, worker, beat"
    exit 1
    ;;
esac
