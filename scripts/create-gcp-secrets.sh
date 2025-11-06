#!/bin/bash
# =============================================================================
# Create GCP Secret Manager secrets from .env file
# =============================================================================

set -euo pipefail

PROJECT_ID="cmsupload-476323"
PREFIX="cms-automation-prod"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if .env exists
if [ ! -f .env ]; then
    log_error ".env file not found"
    exit 1
fi

# Function to get value from .env file
get_env_value() {
    local key="$1"
    grep "^${key}=" .env | cut -d= -f2- | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/"
}

# Function to create or update secret
create_or_update_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local full_secret_name="${PREFIX}-${secret_name}"

    if [ -z "$secret_value" ]; then
        log_info "Skipping $secret_name (empty value)"
        return
    fi

    # Check if secret exists
    if gcloud secrets describe "$full_secret_name" --project="$PROJECT_ID" &>/dev/null; then
        log_info "Updating secret: $full_secret_name"
        echo -n "$secret_value" | gcloud secrets versions add "$full_secret_name" \
            --project="$PROJECT_ID" \
            --data-file=-
    else
        log_info "Creating secret: $full_secret_name"
        echo -n "$secret_value" | gcloud secrets create "$full_secret_name" \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" \
            --data-file=-
    fi

    log_success "✓ $secret_name"
}

log_info "Creating GCP Secret Manager secrets..."
log_info "Project: $PROJECT_ID"
echo ""

# Create secrets from .env
create_or_update_secret "ANTHROPIC_API_KEY" "$(get_env_value "ANTHROPIC_API_KEY")"
create_or_update_secret "DATABASE_URL" "$(get_env_value "DATABASE_URL")"
create_or_update_secret "REDIS_URL" "$(get_env_value "REDIS_URL")"
create_or_update_secret "CMS_BASE_URL" "$(get_env_value "CMS_BASE_URL")"
create_or_update_secret "CMS_USERNAME" "$(get_env_value "CMS_USERNAME")"
create_or_update_secret "CMS_APPLICATION_PASSWORD" "$(get_env_value "CMS_APPLICATION_PASSWORD")"

# Create placeholder HTTP auth secrets (not used)
log_info "Creating placeholder HTTP auth secrets (not used)..."
create_or_update_secret "CMS_HTTP_AUTH_USERNAME" "not_used"
create_or_update_secret "CMS_HTTP_AUTH_PASSWORD" "not_used"

echo ""
log_success "All secrets created successfully!"
log_info "You can view them in GCP Console:"
log_info "https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
