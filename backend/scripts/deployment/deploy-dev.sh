#!/bin/bash

# =============================================================================
# CMS Automation Backend - Development Environment Deployment Script
# Deploy to GCP Cloud Run (Development)
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Development Environment Configuration
PROJECT_ID="${GCP_PROJECT_ID_DEV:-cms-automation-dev}"
REGION="${GCP_REGION_DEV:-us-central1}"
SERVICE_NAME="cms-automation-backend"
IMAGE_TAG="${1:-dev-$(date +%Y%m%d-%H%M%S)}"

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

log_info "🚀 Deploying to DEVELOPMENT environment..."
log_info "Project: $PROJECT_ID"
log_info "Region: $REGION"
log_info "Image Tag: $IMAGE_TAG"
echo ""

# Confirm this is development
if [[ "$PROJECT_ID" == *"prod"* ]]; then
    log_error "⚠️  This script is for DEVELOPMENT environment only!"
    log_error "Project ID contains 'prod': $PROJECT_ID"
    log_error "Please use deploy-prod.sh for production deployment"
    exit 1
fi

# Set GCP project
log_info "Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# Build Docker image for linux/amd64 (Cloud Run requirement)
log_info "Building Docker image: gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"
log_info "Platform: linux/amd64 (Cloud Run compatible)"
docker buildx build --platform linux/amd64 \
    -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    --push \
    .

# Deploy to Cloud Run (Development Configuration)
log_info "Deploying to Cloud Run (Development)..."
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    --region "$REGION" \
    --platform managed \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --timeout 600 \
    --concurrency 80 \
    --set-env-vars "ENVIRONMENT=development,GCP_PROJECT_ID=${PROJECT_ID},LOG_LEVEL=DEBUG" \
    --set-secrets="ANTHROPIC_API_KEY=cms-automation-dev-ANTHROPIC_API_KEY:latest,DATABASE_URL=cms-automation-dev-DATABASE_URL:latest,REDIS_URL=cms-automation-dev-REDIS_URL:latest,CMS_BASE_URL=cms-automation-dev-CMS_BASE_URL:latest,CMS_USERNAME=cms-automation-dev-CMS_USERNAME:latest,CMS_APPLICATION_PASSWORD=cms-automation-dev-CMS_APPLICATION_PASSWORD:latest,CMS_HTTP_AUTH_USERNAME=cms-automation-dev-CMS_HTTP_AUTH_USERNAME:latest,CMS_HTTP_AUTH_PASSWORD=cms-automation-dev-CMS_HTTP_AUTH_PASSWORD:latest" \
    --allow-unauthenticated

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --format 'value(status.url)')

log_success "Deployment completed successfully!"
echo ""
log_info "========================================="
log_info "Deployment Summary (DEVELOPMENT)"
log_info "========================================="
log_info "Project ID:    $PROJECT_ID"
log_info "Region:        $REGION"
log_info "Service Name:  $SERVICE_NAME"
log_info "Image Tag:     $IMAGE_TAG"
log_info "Service URL:   $SERVICE_URL"
log_info "========================================="
echo ""
log_info "Next steps:"
log_info "1. Test the service: curl $SERVICE_URL/health"
log_info "2. Check logs: gcloud run logs read $SERVICE_NAME --region $REGION"
log_info "3. Update frontend to use: $SERVICE_URL"
