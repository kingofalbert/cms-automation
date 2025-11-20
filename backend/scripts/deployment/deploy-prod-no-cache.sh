#!/bin/bash

# =============================================================================
# CMS Automation Backend - Production Environment Deployment Script (No Cache)
# Deploy to GCP Cloud Run (Production) with clean Docker build
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Production Environment Configuration
PROJECT_ID="${GCP_PROJECT_ID_PROD:-cmsupload-476323}"
REGION="${GCP_REGION_PROD:-us-east1}"
SERVICE_NAME="cms-automation-backend"
IMAGE_TAG="${1:-prod-v$(date +%Y%m%d)}"
ARTIFACT_REGISTRY_REPO="cms-backend"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# =============================================================================
# Main Deployment Flow
# =============================================================================

log_warning "⚠️  ========================================="
log_warning "⚠️  PRODUCTION DEPLOYMENT (NO CACHE)"
log_warning "⚠️  ========================================="
log_info "Project: $PROJECT_ID"
log_info "Region: $REGION"
log_info "Image Tag: $IMAGE_TAG"
echo ""

# Safety check
if [[ "$PROJECT_ID" != *"prod"* ]]; then
    log_warning "⚠️  Project ID does not contain 'prod': $PROJECT_ID"
    log_warning "This may not be a production project!"
    if [ -z "$FORCE_DEPLOY" ]; then
        read -p "Continue anyway? (yes/no): " FORCE_CONTINUE
        if [ "$FORCE_CONTINUE" != "yes" ]; then
            log_error "Deployment cancelled"
            exit 1
        fi
    else
        log_info "FORCE_DEPLOY is set, continuing..."
    fi
fi

# Confirm deployment
if [ -z "$FORCE_DEPLOY" ]; then
    echo ""
    log_warning "⚠️  This will deploy to PRODUCTION environment!"
    log_warning "⚠️  Users will be affected by this deployment!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        log_error "Deployment cancelled by user"
        exit 1
    fi
else
    log_info "FORCE_DEPLOY is set, skipping confirmation prompt"
fi

# Set GCP project
log_info "Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# Build Docker image for linux/amd64 (Cloud Run requirement)
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${SERVICE_NAME}"
log_info "Building Docker image (NO CACHE): ${IMAGE_URL}:${IMAGE_TAG}"
log_info "Platform: linux/amd64 (Cloud Run compatible)"
docker buildx build --no-cache --platform linux/amd64 \
    -t "${IMAGE_URL}:${IMAGE_TAG}" \
    -t "${IMAGE_URL}:latest" \
    --push \
    .

# Deploy to Cloud Run
log_info "Deploying to Cloud Run (Production)..."
gcloud run deploy "$SERVICE_NAME" \
    --image="${IMAGE_URL}:${IMAGE_TAG}" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8080 \
    --cpu=2 \
    --memory=2Gi \
    --timeout=600 \
    --max-instances=100 \
    --min-instances=1 \
    --service-account="cms-automation-backend@${PROJECT_ID}.iam.gserviceaccount.com" \
    --set-env-vars="ENVIRONMENT=production" \
    --set-env-vars="PYTHONUNBUFFERED=1" \
    --set-env-vars="SERVICE_TYPE=api" \
    --set-env-vars="SUPABASE_URL=${SUPABASE_URL}" \
    --set-env-vars="SUPABASE_KEY=${SUPABASE_KEY}" \
    --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
    --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" \
    --set-env-vars="SECRET_KEY=${SECRET_KEY}" \
    --set-env-vars="REDIS_URL=${REDIS_URL}" \
    --set-env-vars="CMS_BASE_URL=${CMS_BASE_URL}" \
    --set-env-vars="CHROME_DEVTOOLS_URL=${CHROME_DEVTOOLS_URL}" \
    --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
    --concurrency=100

log_success "✅ Deployment complete!"
echo ""
log_info "Service URL: https://${SERVICE_NAME}-$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)' | cut -d/ -f3)"
echo ""