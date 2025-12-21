#!/bin/bash
# =============================================================================
# CMS Automation - Frontend Deployment Script
# =============================================================================
# Deploys the frontend to Google Cloud Storage
#
# Usage: ./scripts/deployment/deploy-frontend.sh [bucket]
#   bucket: "primary" (default) or "alt"
# =============================================================================

set -e

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Parse arguments
BUCKET_TYPE="${1:-primary}"

if [[ "$BUCKET_TYPE" == "alt" ]]; then
    TARGET_BUCKET="${FRONTEND_BUCKET_ALT}"
    TARGET_URL="${FRONTEND_PUBLIC_URL_ALT}"
else
    TARGET_BUCKET="${FRONTEND_BUCKET}"
    TARGET_URL="${FRONTEND_PUBLIC_URL}"
fi

echo "=============================================="
echo "CMS Automation Frontend Deployment"
echo "=============================================="
echo "Target bucket: ${TARGET_BUCKET}"
echo "Public URL: ${TARGET_URL}"
echo "=============================================="

# Navigate to frontend directory
cd "${SCRIPT_DIR}/../../frontend"

# Build frontend
echo ""
echo "Building frontend..."
npm run build

# Deploy to GCS
echo ""
echo "Deploying to GCS..."
gsutil -m rsync -r -d dist "gs://${TARGET_BUCKET}"

# Set cache headers for HTML files
echo ""
echo "Setting cache headers..."
gsutil setmeta -h "Cache-Control:no-cache, max-age=0" "gs://${TARGET_BUCKET}/index.html"
gsutil setmeta -h "Cache-Control:no-cache, max-age=0" "gs://${TARGET_BUCKET}/app.html"

echo ""
echo "=============================================="
echo "Deployment complete!"
echo "=============================================="
echo "Access your app at:"
echo "${TARGET_URL}"
echo "=============================================="
