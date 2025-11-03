#!/bin/bash

# =============================================================================
# CMS Automation Backend - Cloud Run Deployment Script
# =============================================================================
# 
# This script builds the Docker image and deploys it to Google Cloud Run
#
# Usage:
#   ./deploy-to-cloud-run.sh [OPTIONS]
#
# Options:
#   --project-id PROJECT_ID    GCP project ID (required)
#   --region REGION            GCP region (default: us-central1)
#   --image-tag TAG           Docker image tag (default: latest)
#   --dry-run                 Show commands without executing
#   --help                    Show this help message
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Docker installed
#   - GCP project with billing enabled
#   - Required APIs enabled (Cloud Run, Container Registry, Secret Manager)
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=""
REGION="us-central1"
IMAGE_TAG="latest"
DRY_RUN=false
SERVICE_NAME="cms-automation-backend"
IMAGE_NAME="gcr.io/\${PROJECT_ID}/cms-automation-backend"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    sed -n '/^# Usage:/,/^# =/p' "$0" | sed 's/^# //g' | head -n -1
    exit 0
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# =============================================================================
# Validate Prerequisites
# =============================================================================

log_info "Validating prerequisites..."

# Check if project ID is provided
if [ -z "$PROJECT_ID" ]; then
    log_error "Project ID is required. Use --project-id flag."
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI is not installed. Install from: https://cloud.google.com/sdk/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if authenticated with gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    log_error "Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

# Set the project
log_info "Setting GCP project to: $PROJECT_ID"
if [ "$DRY_RUN" = false ]; then
    gcloud config set project "$PROJECT_ID"
fi

# Update image name with actual project ID
IMAGE_NAME="gcr.io/${PROJECT_ID}/cms-automation-backend"

log_success "Prerequisites validated"

# =============================================================================
# Build Docker Image
# =============================================================================

log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

if [ "$DRY_RUN" = true ]; then
    log_info "[DRY RUN] Would execute: docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
else
    cd "$(dirname "$0")/../../"  # Navigate to backend directory
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" -t "${IMAGE_NAME}:latest" .
    log_success "Docker image built successfully"
fi

# =============================================================================
# Push Image to Container Registry
# =============================================================================

log_info "Pushing image to Google Container Registry..."

if [ "$DRY_RUN" = true ]; then
    log_info "[DRY RUN] Would execute: docker push ${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "[DRY RUN] Would execute: docker push ${IMAGE_NAME}:latest"
else
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker

    docker push "${IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${IMAGE_NAME}:latest"
    log_success "Image pushed to Container Registry"
fi

# =============================================================================
# Deploy to Cloud Run
# =============================================================================

log_info "Deploying to Cloud Run..."

DEPLOY_CMD="gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:${IMAGE_TAG} \
    --platform managed \
    --region ${REGION} \
    --memory 1Gi \
    --cpu 1 \
    --timeout 600 \
    --min-instances 0 \
    --max-instances 10 \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager,GCP_PROJECT_ID=${PROJECT_ID},GCP_SECRET_PREFIX=cms-automation-,PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    --project ${PROJECT_ID}"

if [ "$DRY_RUN" = true ]; then
    log_info "[DRY RUN] Would execute:"
    echo "$DEPLOY_CMD"
else
    eval "$DEPLOY_CMD"
    log_success "Deployed to Cloud Run successfully"
fi

# =============================================================================
# Get Service URL
# =============================================================================

if [ "$DRY_RUN" = false ]; then
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --platform managed \
        --region ${REGION} \
        --format 'value(status.url)')
    
    log_success "Service is available at: $SERVICE_URL"
    log_info "Testing health endpoint..."
    
    sleep 10  # Wait for service to be fully ready
    
    if curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health" | grep -q "200"; then
        log_success "Health check passed!"
    else
        log_warning "Health check failed. Check logs: gcloud run logs read ${SERVICE_NAME} --region ${REGION}"
    fi
fi

# =============================================================================
# Summary
# =============================================================================

log_info ""
log_info "========================================="
log_info "Deployment Summary"
log_info "========================================="
log_info "Project ID:    $PROJECT_ID"
log_info "Region:        $REGION"
log_info "Service Name:  $SERVICE_NAME"
log_info "Image:         ${IMAGE_NAME}:${IMAGE_TAG}"
if [ "$DRY_RUN" = false ]; then
    log_info "Service URL:   $SERVICE_URL"
fi
log_info "========================================="
log_info ""

log_success "Deployment completed successfully!"
