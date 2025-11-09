#!/bin/bash

# ============================================================================
# Backend E2E Test Clean Start Script
# ============================================================================
# This script starts the backend for E2E testing in a completely clean
# environment by running in a new shell session with fresh environment.
#
# Usage: ./start-backend-e2e-clean.sh
# ============================================================================

set -e

BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/tmp/backend-e2e-clean.log"

echo "🧪 Starting backend for E2E testing (clean environment)..."

# Kill any existing backend process
echo "🔍 Checking for existing backend processes..."
if pgrep -f "uvicorn.*src.main:app" > /dev/null; then
    echo "⚠️  Found existing backend process, killing..."
    pkill -f "uvicorn.*src.main:app" || true
    sleep 2
fi

# Clear the log file
> "$LOG_FILE"

echo "📄 Log file: $LOG_FILE"

# Start backend in a completely new shell session without any inherited env vars
# Use 'env -i' to start with a clean environment
nohup env -i \
    HOME="$HOME" \
    PATH="$PATH" \
    SHELL="$SHELL" \
    USER="$USER" \
    bash -c "
        cd '$BACKEND_DIR' && \
        set -a && \
        source .env && \
        set +a && \
        if [ -d '../.venv' ]; then \
            source ../.venv/bin/activate; \
        elif [ -d '.venv' ]; then \
            source .venv/bin/activate; \
        fi && \
        echo '🚀 Starting uvicorn...' && \
        uvicorn src.main:app --host 0.0.0.0 --port 8000 2>&1
    " > "$LOG_FILE" 2>&1 &

BACKEND_PID=$!
echo "✅ Backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        exit 0
    fi

    ATTEMPT=$((ATTEMPT + 1))
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS..."
    sleep 2
done

echo "❌ Backend failed to start within 60 seconds"
echo ""
echo "📋 Last 50 lines of log:"
tail -50 "$LOG_FILE"
exit 1
