#!/bin/bash
set -e

echo "🔧 Fixing DATABASE_URL with URL-encoded password"
echo ""

# Get current DATABASE_URL
CURRENT_URL=$(gcloud secrets versions access latest --secret="cms-automation-prod-DATABASE_URL")

echo "Current URL: $CURRENT_URL"
echo ""

# Replace $ with %24 in password
# postgresql+asyncpg://postgres.twsbhjmlmspjwfystpti:Xieping890$@...
# becomes
# postgresql+asyncpg://postgres.twsbhjmlmspjwfystpti:Xieping890%24@...

NEW_URL="${CURRENT_URL//\$/\%24}"

echo "New URL: $NEW_URL"
echo ""

# Update secret
echo "📝 Updating DATABASE_URL secret..."
echo -n "$NEW_URL" | gcloud secrets versions add cms-automation-prod-DATABASE_URL --data-file=-

echo "✅ Secret updated!"
echo ""
echo "🔄 Now redeploy backend to use the new URL:"
echo "   gcloud run services update cms-automation-backend --region=us-east1"
