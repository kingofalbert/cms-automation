#!/bin/bash

# ============================================================================
# Backend Clean Start Script
# ============================================================================
# This script starts the backend in a clean environment by:
# 1. Unsetting problematic environment variables
# 2. Loading fresh configuration from .env
# 3. Starting uvicorn with correct settings
#
# Usage: ./start-backend-clean.sh
# ============================================================================

set -e

echo "🧹 Cleaning environment variables..."

# Unset all potentially problematic environment variables
unset ALLOWED_ORIGINS
unset CELERY_ACCEPT_CONTENT
unset CELERY_RESULT_BACKEND
unset CELERY_BROKER_URL
unset DATABASE_URL
unset REDIS_URL
unset SECRET_KEY
unset ANTHROPIC_API_KEY
unset CMS_BASE_URL
unset COMPUTER_USE_MODE

echo "✅ Environment variables cleared"

# Change to backend directory
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

echo "📄 Loading configuration from .env..."

# Source the .env file to load fresh configuration
set -a
source .env
set +a

echo "✅ Configuration loaded"

# Verify critical environment variables
echo ""
echo "🔍 Verifying configuration..."
echo "DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "ALLOWED_ORIGINS: $ALLOWED_ORIGINS"
echo "CELERY_ACCEPT_CONTENT: $CELERY_ACCEPT_CONTENT"

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo ""
    echo "🐍 Activating virtual environment..."
    source ../.venv/bin/activate
    echo "✅ Virtual environment activated: $(which python)"
elif [ -d ".venv" ]; then
    echo ""
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
    echo "✅ Virtual environment activated: $(which python)"
else
    echo "⚠️  Warning: No virtual environment found"
fi

# Verify Python version
echo ""
echo "🐍 Python version: $(python --version)"

# Start the backend
echo ""
echo "🚀 Starting backend server..."
echo "================================================"

# Use exec to replace the shell process with uvicorn
# This ensures signals are properly handled
exec uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
