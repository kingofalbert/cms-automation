#!/bin/bash
# GCP Permissions Quick Fix Script
# Purpose: Provide multiple solutions for gs://cms-automation-frontend-cmsupload-476323/ access issue

set -e

BUCKET="gs://cms-automation-frontend-cmsupload-476323"
PROJECT_ID="cmsupload-476323"
CURRENT_USER=$(gcloud config get-value account)

echo "======================================"
echo "GCP Permissions Diagnostic & Fix Tool"
echo "======================================"
echo "Current User: $CURRENT_USER"
echo "Current Project: $PROJECT_ID"
echo "Target Bucket: $BUCKET"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test permissions
test_permissions() {
    echo "Testing permissions..."

    # Test read
    echo -n "  [1] Read permission: "
    if gsutil ls $BUCKET/ >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        READ_OK=true
    else
        echo -e "${RED}✗ FAIL${NC}"
        READ_OK=false
    fi

    # Test write
    echo -n "  [2] Write permission: "
    TEST_FILE="/tmp/gcp-test-$(date +%s).txt"
    echo "test" > $TEST_FILE
    if gsutil cp $TEST_FILE $BUCKET/test-upload.txt >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        WRITE_OK=true
        # Cleanup
        gsutil rm $BUCKET/test-upload.txt >/dev/null 2>&1 || true
    else
        echo -e "${RED}✗ FAIL${NC}"
        WRITE_OK=false
    fi

    # Test delete
    echo -n "  [3] Delete permission: "
    if [ "$WRITE_OK" = true ]; then
        echo -e "${GREEN}✓ PASS${NC} (verified via cleanup)"
        DELETE_OK=true
    else
        echo -e "${RED}✗ FAIL${NC}"
        DELETE_OK=false
    fi

    rm -f $TEST_FILE
    echo ""
}

# Function to show solutions
show_solutions() {
    echo "======================================"
    echo "AVAILABLE SOLUTIONS"
    echo "======================================"
    echo ""

    echo -e "${YELLOW}Solution 1: Request Bucket Owner to Grant Permissions${NC}"
    echo "You need to contact the bucket owner/admin to run:"
    echo ""
    echo "  gsutil iam ch user:$CURRENT_USER:roles/storage.objectAdmin \\"
    echo "    $BUCKET"
    echo ""
    echo "This grants you permission to create, read, update, and delete objects."
    echo ""

    echo -e "${YELLOW}Solution 2: Use Service Account (Recommended for CI/CD)${NC}"
    echo "1. Create service account:"
    echo "   gcloud iam service-accounts create frontend-deployer \\"
    echo "     --display-name='Frontend Deployer'"
    echo ""
    echo "2. Grant bucket access (bucket owner must run):"
    echo "   gsutil iam ch serviceAccount:frontend-deployer@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectAdmin \\"
    echo "     $BUCKET"
    echo ""
    echo "3. Create and download key:"
    echo "   gcloud iam service-accounts keys create ~/frontend-deployer-key.json \\"
    echo "     --iam-account=frontend-deployer@$PROJECT_ID.iam.gserviceaccount.com"
    echo ""
    echo "4. Set environment variable:"
    echo "   export GOOGLE_APPLICATION_CREDENTIALS=~/frontend-deployer-key.json"
    echo ""

    echo -e "${YELLOW}Solution 3: Create New Bucket (Quick Alternative)${NC}"
    echo "Create your own bucket with full control:"
    echo ""
    echo "  gsutil mb -p $PROJECT_ID -l us-central1 \\"
    echo "    gs://cms-automation-frontend-dev-2025/"
    echo ""
    echo "  gsutil iam ch allUsers:objectViewer \\"
    echo "    gs://cms-automation-frontend-dev-2025/"
    echo ""
    echo "  gsutil web set -m index.html -e 404.html \\"
    echo "    gs://cms-automation-frontend-dev-2025/"
    echo ""
    echo "Access URL: https://storage.googleapis.com/cms-automation-frontend-dev-2025/index.html"
    echo ""
}

# Function to auto-fix with new bucket
create_new_bucket() {
    NEW_BUCKET="gs://cms-automation-frontend-dev-$(date +%Y%m%d)"

    echo "======================================"
    echo "Creating New Bucket"
    echo "======================================"
    echo "Bucket: $NEW_BUCKET"
    echo ""

    read -p "Do you want to create this bucket? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating bucket..."
        gsutil mb -p $PROJECT_ID -l us-central1 -b on $NEW_BUCKET

        echo "Setting public access..."
        gsutil iam ch allUsers:objectViewer $NEW_BUCKET

        echo "Configuring website..."
        gsutil web set -m index.html -e 404.html $NEW_BUCKET

        echo ""
        echo -e "${GREEN}✓ Bucket created successfully!${NC}"
        echo ""
        echo "Access URL: https://storage.googleapis.com/${NEW_BUCKET#gs://}/index.html"
        echo ""
        echo "To deploy frontend:"
        echo "  cd /home/kingofalbert/projects/CMS/frontend"
        echo "  npm run build"
        echo "  gsutil -m rsync -r -d dist/ $NEW_BUCKET/"
        echo ""

        # Update deployment script suggestion
        echo "Update frontend/package.json scripts:"
        echo "  \"deploy\": \"npm run build && gsutil -m rsync -r -d dist/ $NEW_BUCKET/\""
    else
        echo "Cancelled."
    fi
}

# Main script execution
echo "Running diagnostic..."
echo ""

test_permissions

if [ "$READ_OK" = true ] && [ "$WRITE_OK" = true ] && [ "$DELETE_OK" = true ]; then
    echo -e "${GREEN}======================================"
    echo "✓ ALL PERMISSIONS OK"
    echo "======================================${NC}"
    echo ""
    echo "You can now deploy frontend:"
    echo ""
    echo "  cd /home/kingofalbert/projects/CMS/frontend"
    echo "  npm run build"
    echo "  gsutil -m rsync -r -d dist/ $BUCKET/"
    echo "  gsutil -m setmeta -h 'Cache-Control:no-cache, no-store, must-revalidate' \\"
    echo "    $BUCKET/*.html"
    echo ""
    exit 0
fi

echo -e "${RED}======================================"
echo "✗ PERMISSION ISSUES DETECTED"
echo "======================================${NC}"
echo ""

show_solutions

echo "======================================"
echo "QUICK ACTION"
echo "======================================"
echo ""
echo "Would you like to:"
echo "  1) Create a new bucket with full permissions (recommended)"
echo "  2) Show detailed instructions only"
echo "  3) Exit"
echo ""
read -p "Choose option (1/2/3): " -n 1 -r
echo ""

case $REPLY in
    1)
        create_new_bucket
        ;;
    2)
        echo "See GCP_PERMISSION_ISSUE_ANALYSIS.md for detailed instructions"
        ;;
    3)
        echo "Exiting..."
        ;;
    *)
        echo "Invalid option. Exiting..."
        ;;
esac
