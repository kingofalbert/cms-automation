#!/bin/bash
# Deployment script for Google Docs HTML parsing fix
# Deploys to Google Cloud Run

set -e

# Configuration
PROJECT_ID="cmsupload-476323"
REGION="us-east1"
SERVICE_NAME="cms-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
COMMIT_SHA=$(git rev-parse --short HEAD)

echo "=================================================================="
echo "Deploying Google Docs HTML Parsing Fix to Cloud Run"
echo "=================================================================="
echo ""
echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Commit: $COMMIT_SHA"
echo ""

# Step 1: Configure gcloud
echo "Step 1: Configuring gcloud..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Step 2: Build Docker image
echo ""
echo "Step 2: Building Docker image..."
cd backend
docker build -t ${IMAGE_NAME}:${COMMIT_SHA} -t ${IMAGE_NAME}:latest .

# Step 3: Push to Container Registry
echo ""
echo "Step 3: Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}:${COMMIT_SHA}
docker push ${IMAGE_NAME}:latest

# Step 4: Deploy to Cloud Run
echo ""
echo "Step 4: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:${COMMIT_SHA} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# Step 5: Get service URL
echo ""
echo "Step 5: Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "=================================================================="
echo "✅ Deployment Complete!"
echo "=================================================================="
echo ""
echo "Service URL: $SERVICE_URL"
echo "Commit: $COMMIT_SHA"
echo ""
echo "Next steps:"
echo "  1. Verify health: curl ${SERVICE_URL}/health"
echo "  2. Check logs: gcloud run logs read --service ${SERVICE_NAME}"
echo "  3. Monitor metrics in GCP Console"
echo ""
