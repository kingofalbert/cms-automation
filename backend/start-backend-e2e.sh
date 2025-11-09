#!/bin/bash
# Start backend for E2E testing without problematic environment variables

# Unset problematic list-type environment variables
unset ALLOWED_ORIGINS
unset CELERY_ACCEPT_CONTENT

# Start uvicorn
exec .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
