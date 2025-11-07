#!/bin/bash
set -e

# Run migrations against Supabase production database
export DATABASE_URL="postgresql+asyncpg://postgres.twsbhjmlmspjwfystpti:Xieping890\$@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

echo "Running database migrations against Supabase..."
echo "Database: aws-1-us-east-1.pooler.supabase.com:5432/postgres"

# Use production Docker image (which has all dependencies)
# Build the image first if needed
docker build --platform linux/amd64 -t cms-backend-local:latest -f Dockerfile .

# Run migrations using the production image
# IMPORTANT: Mount current directory to use latest migration files
# Provide dummy values for required Settings fields (only DATABASE_URL matters for migrations)
docker run --rm \
  -v "$(pwd):/code" \
  -w /code \
  -e DATABASE_URL="$DATABASE_URL" \
  -e SECRET_KEY="dummy-secret-for-migrations-12345678" \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e ANTHROPIC_API_KEY="dummy-key-12345678" \
  -e CMS_BASE_URL="https://example.com" \
  -e PYTHONDONTWRITEBYTECODE="1" \
  cms-backend-local:latest \
  python -m alembic upgrade head

echo "✅ Migrations completed successfully!"
