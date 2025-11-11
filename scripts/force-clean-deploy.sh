#!/bin/bash
# Force clean deployment script for fixing database connection issue
# Created: 2025-11-11
# Purpose: Ensure pgbouncer fix (statement_cache_size: 0) is applied

set -e  # Exit on error

echo "========================================="
echo "Force Clean Deployment - Parsing Fix"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ID="cmsupload-476323"
REGION="us-east1"
SERVICE_NAME="cms-automation-backend"
IMAGE_NAME="cms-automation-backend"
ARTIFACT_REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/cms-backend"

echo -e "${YELLOW}Step 1: Verifying we're in the backend directory...${NC}"
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Not in backend directory!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ In backend directory${NC}"

echo -e "\n${YELLOW}Step 2: Checking database.py has the fix...${NC}"
if grep -q '"statement_cache_size": 0' src/config/database.py; then
    echo -e "${GREEN}✓ Database fix is present in code${NC}"
    grep -n '"statement_cache_size": 0' src/config/database.py
else
    echo -e "${RED}✗ Database fix NOT found in database.py!${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 3: Building Docker image with --no-cache flag...${NC}"
echo "This will take 3-5 minutes as it rebuilds everything from scratch..."

# Build with explicit no-cache and unique tag
TIMESTAMP=$(date +%Y%m%d%H%M%S)
FULL_IMAGE="${ARTIFACT_REGISTRY}/${IMAGE_NAME}:fix-${TIMESTAMP}"
LATEST_IMAGE="${ARTIFACT_REGISTRY}/${IMAGE_NAME}:latest"

docker build \
    --no-cache \
    --platform linux/amd64 \
    -f Dockerfile.prod \
    -t "${FULL_IMAGE}" \
    -t "${LATEST_IMAGE}" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker build successful${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 4: Pushing image to Artifact Registry...${NC}"
docker push "${FULL_IMAGE}"
docker push "${LATEST_IMAGE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Image pushed successfully${NC}"
else
    echo -e "${RED}✗ Image push failed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 5: Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image="${FULL_IMAGE}" \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --no-traffic

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment successful (no traffic yet)${NC}"
else
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi

# Get the new revision name
NEW_REVISION=$(gcloud run revisions list \
    --service=${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(name)" \
    --limit=1)

echo -e "\n${YELLOW}Step 6: Testing the new revision before routing traffic...${NC}"
echo "New revision: ${NEW_REVISION}"

# Get the revision URL
REVISION_URL=$(gcloud run revisions describe ${NEW_REVISION} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo "Testing revision URL: ${REVISION_URL}"

# Test the health endpoint
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${REVISION_URL}/health")

if [ "${HEALTH_RESPONSE}" = "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (HTTP ${HEALTH_RESPONSE})${NC}"
    echo "You can still route traffic manually if needed"
fi

echo -e "\n${YELLOW}Step 7: Routing traffic to new revision...${NC}"
gcloud run services update-traffic ${SERVICE_NAME} \
    --to-latest \
    --region=${REGION} \
    --project=${PROJECT_ID}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Traffic routed to new revision${NC}"
else
    echo -e "${RED}✗ Failed to route traffic${NC}"
    exit 1
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Service URL: https://${SERVICE_NAME}-baau2zqeqq-ue.a.run.app"
echo "Revision: ${NEW_REVISION}"
echo "Image: ${FULL_IMAGE}"
echo ""
echo -e "${YELLOW}Next step: Test the parsing endpoint${NC}"
echo "curl -X POST https://${SERVICE_NAME}-baau2zqeqq-ue.a.run.app/v1/worklist/2/trigger-proofreading"