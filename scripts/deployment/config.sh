#!/bin/bash
# =============================================================================
# CMS Automation - Centralized Deployment Configuration
# =============================================================================
# This file contains all deployment-related configuration variables.
# Source this file before running any deployment scripts.
#
# Usage: source scripts/deployment/config.sh
# =============================================================================

# -----------------------------------------------------------------------------
# Google Cloud Project Configuration
# -----------------------------------------------------------------------------
export GCP_PROJECT_ID="cmsupload-476323"
export GCP_PROJECT_NUMBER="297291472291"
export GCP_REGION="us-east1"

# -----------------------------------------------------------------------------
# Frontend Deployment (Google Cloud Storage)
# -----------------------------------------------------------------------------
# Primary production bucket
export FRONTEND_BUCKET="cms-automation-frontend-476323"
export FRONTEND_BUCKET_URL="gs://${FRONTEND_BUCKET}"
export FRONTEND_PUBLIC_URL="https://storage.googleapis.com/${FRONTEND_BUCKET}/index.html"

# Alternative bucket (US-EAST1)
export FRONTEND_BUCKET_ALT="cms-automation-frontend-cmsupload-476323"
export FRONTEND_BUCKET_ALT_URL="gs://${FRONTEND_BUCKET_ALT}"
export FRONTEND_PUBLIC_URL_ALT="https://storage.googleapis.com/${FRONTEND_BUCKET_ALT}/index.html"

# -----------------------------------------------------------------------------
# Backend Deployment (Cloud Run)
# -----------------------------------------------------------------------------
export BACKEND_SERVICE_NAME="cms-automation-backend"
export BACKEND_URL="https://cms-automation-backend-${GCP_PROJECT_NUMBER}.${GCP_REGION}.run.app"

# -----------------------------------------------------------------------------
# Supabase Configuration
# -----------------------------------------------------------------------------
export SUPABASE_PROJECT_REF="twsbhjmlmspjwfystpti"
export SUPABASE_URL="https://${SUPABASE_PROJECT_REF}.supabase.co"

# -----------------------------------------------------------------------------
# CORS Allowed Origins (for backend configuration)
# -----------------------------------------------------------------------------
export CORS_ORIGINS="http://localhost:3000,http://localhost:8000,https://storage.googleapis.com,https://${FRONTEND_BUCKET}.storage.googleapis.com,https://${FRONTEND_BUCKET_ALT}.storage.googleapis.com"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

# Deploy frontend to primary bucket
deploy_frontend() {
    echo "Deploying frontend to ${FRONTEND_BUCKET}..."
    cd frontend && npm run build
    gsutil -m rsync -r -d dist "${FRONTEND_BUCKET_URL}"
    echo "Frontend deployed to: ${FRONTEND_PUBLIC_URL}"
}

# Deploy frontend to alternative bucket
deploy_frontend_alt() {
    echo "Deploying frontend to ${FRONTEND_BUCKET_ALT}..."
    cd frontend && npm run build
    gsutil -m rsync -r -d dist "${FRONTEND_BUCKET_ALT_URL}"
    echo "Frontend deployed to: ${FRONTEND_PUBLIC_URL_ALT}"
}

# Print current configuration
print_config() {
    echo "=== CMS Automation Deployment Configuration ==="
    echo "GCP Project: ${GCP_PROJECT_ID}"
    echo "GCP Region: ${GCP_REGION}"
    echo ""
    echo "Frontend Bucket: ${FRONTEND_BUCKET}"
    echo "Frontend URL: ${FRONTEND_PUBLIC_URL}"
    echo ""
    echo "Backend Service: ${BACKEND_SERVICE_NAME}"
    echo "Backend URL: ${BACKEND_URL}"
    echo ""
    echo "Supabase URL: ${SUPABASE_URL}"
    echo "=============================================="
}

# Run print_config if this script is sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "Deployment configuration loaded."
    echo "Run 'print_config' to see all settings."
fi
