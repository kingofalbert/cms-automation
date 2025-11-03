#!/bin/bash

# =============================================================================
# CMS Automation Frontend - GCP Deployment Script
# Deploy to Cloud Storage + Cloud CDN
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID=""
BUCKET_NAME=""
REGION="us-central1"
BACKEND_URL=""

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

show_help() {
    cat << HELP
CMS Automation Frontend - GCP Deployment Script

Usage:
    ./deploy-to-gcp.sh --project-id PROJECT_ID --bucket-name BUCKET_NAME --backend-url BACKEND_URL [OPTIONS]

Required Options:
    --project-id PROJECT_ID     GCP project ID
    --bucket-name BUCKET_NAME   Cloud Storage bucket name (e.g., cms-automation-frontend)
    --backend-url BACKEND_URL   Backend API URL (e.g., https://xxx.run.app)

Optional:
    --region REGION            GCP region (default: us-central1)
    --help                     Show this help message

Example:
    ./deploy-to-gcp.sh \\
        --project-id my-project \\
        --bucket-name cms-automation-frontend \\
        --backend-url https://cms-backend-xyz.run.app

Prerequisites:
    - gcloud CLI installed and authenticated
    - Node.js and npm installed
    - GCP project with billing enabled
HELP
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
        --bucket-name)
            BUCKET_NAME="$2"
            shift 2
            ;;
        --backend-url)
            BACKEND_URL="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
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

# Validate required arguments
if [ -z "$PROJECT_ID" ] || [ -z "$BUCKET_NAME" ] || [ -z "$BACKEND_URL" ]; then
    log_error "Missing required arguments"
    show_help
fi

# =============================================================================
# Main Deployment Flow
# =============================================================================

log_info "Starting frontend deployment to GCP..."
log_info "Project: $PROJECT_ID"
log_info "Bucket: $BUCKET_NAME"
log_info "Backend URL: $BACKEND_URL"

# Step 1: Set GCP project
log_info "Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# Step 2: Create bucket if it doesn't exist
log_info "Checking if bucket exists..."
if ! gsutil ls -b "gs://${BUCKET_NAME}" &> /dev/null; then
    log_info "Creating bucket: ${BUCKET_NAME}"
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://${BUCKET_NAME}"
    log_success "Bucket created"
else
    log_info "Bucket already exists"
fi

# Step 3: Configure bucket for website hosting
log_info "Configuring bucket for website hosting..."
gsutil web set -m index.html -e index.html "gs://${BUCKET_NAME}"

# Step 4: Make bucket public
log_info "Making bucket publicly accessible..."
gsutil iam ch allUsers:objectViewer "gs://${BUCKET_NAME}"

# Step 5: Build frontend
log_info "Building frontend..."
cd "$(dirname "$0")/.."  # Navigate to frontend directory

# Create .env.production with backend URL
cat > .env.production << ENV_EOF
VITE_API_URL=${BACKEND_URL}
VITE_APP_TITLE=CMS Automation
VITE_APP_DESCRIPTION=AI-powered CMS automation system
ENV_EOF

npm install
npm run build

log_success "Frontend built successfully"

# Step 6: Upload to Cloud Storage
log_info "Uploading files to Cloud Storage..."
gsutil -m rsync -r -d dist/ "gs://${BUCKET_NAME}/"

# Step 7: Set cache control
log_info "Setting cache control headers..."
# HTML files - no cache
gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
    "gs://${BUCKET_NAME}/**/*.html"

# Static assets - cache for 1 year
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" \
    "gs://${BUCKET_NAME}/assets/**/*"

# Step 8: Enable Cloud CDN (optional but recommended)
log_info "Setting up Cloud CDN..."
BACKEND_SERVICE_NAME="${BUCKET_NAME}-backend"

# Create backend bucket
if ! gcloud compute backend-buckets describe "$BACKEND_SERVICE_NAME" &> /dev/null; then
    gcloud compute backend-buckets create "$BACKEND_SERVICE_NAME" \
        --gcs-bucket-name="$BUCKET_NAME" \
        --enable-cdn
    log_success "Backend bucket created with CDN enabled"
else
    log_info "Backend bucket already exists"
fi

# Step 9: Get the public URL
PUBLIC_URL="https://storage.googleapis.com/${BUCKET_NAME}/index.html"

log_success "Deployment completed successfully!"
log_info ""
log_info "========================================="
log_info "Deployment Summary"
log_info "========================================="
log_info "Project ID:    $PROJECT_ID"
log_info "Bucket Name:   $BUCKET_NAME"
log_info "Backend URL:   $BACKEND_URL"
log_info "Frontend URL:  $PUBLIC_URL"
log_info "========================================="
log_info ""
log_info "Next steps:"
log_info "1. Test the frontend: curl $PUBLIC_URL"
log_info "2. (Optional) Set up custom domain"
log_info "3. Update backend CORS to allow: https://storage.googleapis.com"

