#!/bin/bash

# Deployment script with automatic database migration
# Usage: ./deploy.sh [staging|production]

set -e  # Exit on any error

ENVIRONMENT=${1:-staging}
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting deployment to $ENVIRONMENT..."

# Step 1: Run database migration
echo "📦 Running database migration..."
cd "$BACKEND_DIR"

if [ "$ENVIRONMENT" = "production" ]; then
    export DATABASE_URL="$PRODUCTION_DATABASE_URL"
else
    export DATABASE_URL="$STAGING_DATABASE_URL"
fi

# Check current migration status
echo "Current migration status:"
alembic current

# Run migration
echo "Upgrading database schema..."
alembic upgrade head

# Verify migration
echo "New migration status:"
alembic current

# Step 2: Deploy backend to Cloud Run
echo "🌐 Deploying backend to Cloud Run..."

if [ "$ENVIRONMENT" = "production" ]; then
    gcloud run deploy cms-automation-backend \
      --source . \
      --region us-east1 \
      --platform managed \
      --project cmsupload-476323 \
      --allow-unauthenticated
else
    gcloud run deploy cms-automation-backend-staging \
      --source . \
      --region us-east1 \
      --platform managed \
      --project cmsupload-476323 \
      --allow-unauthenticated
fi

# Step 3: Verify deployment
echo "✅ Verifying deployment..."
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_URL="https://cms-automation-backend-XXXXX.run.app"
else
    BACKEND_URL="https://cms-automation-backend-staging-XXXXX.run.app"
fi

echo "Testing health endpoint: $BACKEND_URL/health"
curl -f "$BACKEND_URL/health" || echo "⚠️  Health check failed"

echo "🎉 Deployment complete!"
echo "Backend URL: $BACKEND_URL"
