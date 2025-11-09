#!/bin/bash

# Quick migration using existing Docker image and Transaction Pooler
set -e

echo "Running migrations with Transaction Pooler (port 6543)..."

docker run --rm \
  -e "DATABASE_URL=postgresql://postgres.twsbhjmlmspjwfystpti:Xieping890\$@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require" \
  -e "SECRET_KEY=dummy-secret-for-migrations-12345678-32chars-minimum" \
  -e "REDIS_URL=redis://localhost:6379/0" \
  -e "ANTHROPIC_API_KEY=dummy-key-12345678" \
  -e "CMS_BASE_URL=https://example.com" \
  cms-backend-local:latest \
  python -m alembic upgrade head

echo ""
echo "✅ Migration completed!"
