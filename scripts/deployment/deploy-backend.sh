#!/bin/bash
# =============================================================================
# CMS Automation - Backend Deployment Script
# =============================================================================
# Deploys the backend to Cloud Run and cleans up old revisions to prevent
# Supabase connection pool exhaustion.
#
# Usage: ./scripts/deployment/deploy-backend.sh
# =============================================================================

set -euo pipefail

# Load deployment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

SERVICE="${BACKEND_SERVICE_NAME}"
REGION="${GCP_REGION}"
PROJECT="${GCP_PROJECT_ID}"

echo "=== Deploying Backend to Cloud Run ==="
echo "Service: ${SERVICE}"
echo "Region:  ${REGION}"
echo "Project: ${PROJECT}"
echo ""

# MUST deploy from backend/ directory
cd "$(dirname "${SCRIPT_DIR}")/../backend"
echo "Working directory: $(pwd)"
echo ""

# Deploy
gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --project "${PROJECT}" \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 5 \
  --set-secrets="SECRET_KEY=cms-automation-prod-SECRET_KEY:latest,DATABASE_URL=cms-automation-prod-DATABASE_URL:latest,REDIS_URL=cms-automation-prod-REDIS_URL:latest,ANTHROPIC_API_KEY=cms-automation-prod-ANTHROPIC_API_KEY:latest,CMS_BASE_URL=cms-automation-prod-CMS_BASE_URL:latest,CMS_USERNAME=cms-automation-prod-CMS_USERNAME:latest,CMS_APPLICATION_PASSWORD=cms-automation-prod-CMS_APPLICATION_PASSWORD:latest,CMS_HTTP_AUTH_USERNAME=cms-automation-prod-CMS_HTTP_AUTH_USERNAME:latest,CMS_HTTP_AUTH_PASSWORD=cms-automation-prod-CMS_HTTP_AUTH_PASSWORD:latest,SUPABASE_SERVICE_ROLE_KEY=supabase-service-role-key:latest,GOOGLE_SERVICE_ACCOUNT_JSON=GOOGLE_SERVICE_ACCOUNT_JSON:latest,ALLOWED_ORIGINS=ALLOWED_ORIGINS:latest,GAS_API_KEY=cms-automation-prod-GAS_API_KEY:latest" \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT},LOG_LEVEL=INFO,GOOGLE_DRIVE_FOLDER_ID=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG,DATABASE_POOL_SIZE=3,DATABASE_MAX_OVERFLOW=2,DATABASE_POOL_RECYCLE=270"

echo ""
echo "=== Cleaning Up Old Revisions ==="
echo "Keeping only the latest revision to prevent Supabase connection pool exhaustion."
echo ""

# Get all revisions except the latest (which is serving traffic)
OLD_REVISIONS=$(gcloud run revisions list \
  --service="${SERVICE}" \
  --region="${REGION}" \
  --project="${PROJECT}" \
  --format="value(name)" \
  --sort-by="~creationTimestamp" | tail -n +2)

if [ -z "${OLD_REVISIONS}" ]; then
  echo "No old revisions to clean up."
else
  COUNT=$(echo "${OLD_REVISIONS}" | wc -l | tr -d ' ')
  echo "Deleting ${COUNT} old revision(s)..."

  # Delete sequentially to avoid API quota issues
  echo "${OLD_REVISIONS}" | while read -r rev; do
    echo "  Deleting ${rev}..."
    gcloud run revisions delete "${rev}" \
      --region="${REGION}" \
      --project="${PROJECT}" \
      --quiet 2>&1 || echo "  Warning: Failed to delete ${rev}, may already be deleted"
    sleep 2  # Avoid API rate limiting
  done

  echo "Old revisions cleaned up."
fi

echo ""
echo "=== Verifying Health ==="
sleep 5  # Wait for new revision to start

HEALTH=$(curl -s --max-time 15 "${BACKEND_URL}/health" 2>&1)
echo "Health check: ${HEALTH}"

if echo "${HEALTH}" | grep -q '"healthy"'; then
  echo ""
  echo "=== Deployment Successful ==="
  echo "Backend URL: ${BACKEND_URL}"
else
  echo ""
  echo "=== WARNING: Health check failed ==="
  echo "Check Cloud Run logs: gcloud run services logs read ${SERVICE} --region ${REGION} --project ${PROJECT} --limit 20"
fi
