#!/bin/bash

# =============================================================================
# CMS Automation Backend - Production Environment Deployment Script
# Deploy to GCP Cloud Run (Production)
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
log_warning "⚠️  PRODUCTION DEPLOYMENT"
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
log_info "Building Docker image: ${IMAGE_URL}:${IMAGE_TAG}"
log_info "Platform: linux/amd64 (Cloud Run compatible)"
docker buildx build --platform linux/amd64 \
    -t "${IMAGE_URL}:${IMAGE_TAG}" \
    -t "${IMAGE_URL}:latest" \
    --push \
    .

# Deploy to Cloud Run (Production Configuration)
log_info "Deploying to Cloud Run (Production)..."
gcloud run deploy "$SERVICE_NAME" \
    --image "${IMAGE_URL}:${IMAGE_TAG}" \
    --region "$REGION" \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --timeout 600 \
    --concurrency 100 \
    --port 8080 \
    --set-env-vars "ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},LOG_LEVEL=INFO,GOOGLE_DRIVE_FOLDER_ID=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG,DATABASE_POOL_SIZE=5,DATABASE_MAX_OVERFLOW=5" \
    --set-secrets="SECRET_KEY=cms-automation-prod-SECRET_KEY:latest,ANTHROPIC_API_KEY=cms-automation-prod-ANTHROPIC_API_KEY:latest,DATABASE_URL=cms-automation-prod-DATABASE_URL:latest,REDIS_URL=cms-automation-prod-REDIS_URL:latest,CMS_BASE_URL=cms-automation-prod-CMS_BASE_URL:latest,CMS_USERNAME=cms-automation-prod-CMS_USERNAME:latest,CMS_APPLICATION_PASSWORD=cms-automation-prod-CMS_APPLICATION_PASSWORD:latest,CMS_HTTP_AUTH_USERNAME=cms-automation-prod-CMS_HTTP_AUTH_USERNAME:latest,CMS_HTTP_AUTH_PASSWORD=cms-automation-prod-CMS_HTTP_AUTH_PASSWORD:latest,GOOGLE_SERVICE_ACCOUNT_JSON=GOOGLE_SERVICE_ACCOUNT_JSON:latest" \
    --allow-unauthenticated

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format 'value(status.url)')

# Health check
log_info "Running health check..."
HEALTH_STATUS=$(curl -s "${SERVICE_URL}/health" || echo "FAILED")

if [[ "$HEALTH_STATUS" == *"healthy"* || "$HEALTH_STATUS" == *"ok"* ]]; then
    log_success "Health check passed!"
else
    log_error "Health check failed!"
    log_error "Response: $HEALTH_STATUS"
    log_warning "Please check the logs immediately!"
fi

log_success "Production deployment completed!"
echo ""
log_info "========================================="
log_info "Deployment Summary (PRODUCTION)"
log_info "========================================="
log_info "Project ID:    $PROJECT_ID"
log_info "Region:        $REGION"
log_info "Service Name:  $SERVICE_NAME"
log_info "Image Tag:     $IMAGE_TAG"
log_info "Service URL:   $SERVICE_URL"
log_info "========================================="
echo ""
log_warning "Post-Deployment Actions:"
log_warning "1. Monitor logs: gcloud run logs read $SERVICE_NAME --region $REGION"
log_warning "2. Check metrics in GCP Console"
log_warning "3. Test critical endpoints"
log_warning "4. Monitor for 24 hours"
log_warning "5. Update frontend to use: $SERVICE_URL"
echo ""
log_success "Deployment complete! 🎉"
