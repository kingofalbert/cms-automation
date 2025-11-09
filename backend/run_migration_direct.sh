#!/bin/bash

# Direct migration runner for Supabase database
# This script runs Alembic migrations without Docker

set -e

echo "Running database migrations directly..."
echo "Database: aws-1-us-east-1.pooler.supabase.com:5432/postgres"

export DATABASE_URL="postgresql+asyncpg://postgres.twsbhjmlmspjwfystpti:Xieping890\$@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
export SECRET_KEY="dummy-secret-for-migrations-12345678"
export REDIS_URL="redis://localhost:6379/0"
export ANTHROPIC_API_KEY="dummy-key-12345678"
export CMS_BASE_URL="https://example.com"

# Install alembic if not available
python3 -m pip install --quiet alembic sqlalchemy psycopg2-binary asyncpg

# Run migration
cd /home/kingofalbert/projects/CMS/backend
python3 -m alembic upgrade head

echo "✅ Migrations completed successfully!"
