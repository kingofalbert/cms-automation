#!/bin/bash

# Simple migration using previously built Docker image
set -e

echo "Running database migrations with existing Docker image..."

# Check if Docker image exists
if ! docker image inspect cms-backend-local:latest > /dev/null 2>&1; then
    echo "Error: Docker image cms-backend-local:latest not found"
    echo "Please rebuild the Docker image first"
    exit 1
fi

# Run migration using existing image
docker run --rm \
  -v /home/kingofalbert/projects/CMS/backend/src:/app/src:ro \
  -v /home/kingofalbert/projects/CMS/backend/migrations:/app/migrations:ro \
  -e DATABASE_URL="postgresql+asyncpg://postgres.twsbhjmlmspjwfystpti:Xieping890\$@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require" \
  -e SECRET_KEY="dummy-secret-for-migrations-12345678-32chars-minimum" \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e ANTHROPIC_API_KEY="dummy-key-12345678" \
  -e CMS_BASE_URL="https://example.com" \
  cms-backend-local:latest \
  /bin/bash -c "python -m alembic upgrade head"

echo "✅ Migrations completed successfully!"
