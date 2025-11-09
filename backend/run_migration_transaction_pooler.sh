#!/bin/bash

# Migration using Transaction Pooler (port 6543)
# This pooler mode is more reliable for migrations

set -e

echo "Running database migrations using Transaction Pooler..."
echo "Host: aws-1-us-east-1.pooler.supabase.com:6543"
echo "Mode: Transaction pooling"

# Build fresh Docker image with latest code
echo "Building Docker image..."
cd /home/kingofalbert/projects/CMS/backend
docker build -t cms-backend-migration:latest . 2>&1 | tail -5

# Run migration using Transaction Pooler (port 6543)
echo "Running Alembic migrations..."
docker run --rm \
  -e DATABASE_URL="postgresql+asyncpg://postgres.twsbhjmlmspjwfystpti:Xieping890\$@aws-1-us-east-1.pooler.supabase.com:6543/postgres?ssl=require" \
  -e SECRET_KEY="dummy-secret-for-migrations-12345678-32chars-minimum" \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e ANTHROPIC_API_KEY="dummy-key-12345678" \
  -e CMS_BASE_URL="https://example.com" \
  cms-backend-migration:latest \
  /bin/bash -c "python -m alembic upgrade head"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migrations completed successfully!"
else
    echo ""
    echo "❌ Migration failed. Trying Direct Connection..."

    # Fallback: Try Direct Connection
    docker run --rm \
      -e DATABASE_URL="postgresql+asyncpg://postgres:Xieping890\$@db.twsbhjmlmspjwfystpti.supabase.co:5432/postgres?ssl=require" \
      -e SECRET_KEY="dummy-secret-for-migrations-12345678-32chars-minimum" \
      -e REDIS_URL="redis://localhost:6379/0" \
      -e ANTHROPIC_API_KEY="dummy-key-12345678" \
      -e CMS_BASE_URL="https://example.com" \
      cms-backend-migration:latest \
      /bin/bash -c "python -m alembic upgrade head"

    if [ $? -eq 0 ]; then
        echo "✅ Migrations completed using Direct Connection!"
    else
        echo "❌ Both attempts failed. Please check database connectivity."
        exit 1
    fi
fi
