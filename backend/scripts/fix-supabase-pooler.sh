#!/bin/bash
set -e

echo "🔧 Fixing Supabase connection pooler configuration"
echo ""
echo "Issue: Session mode (port 5432) has strict client limits"
echo "Solution: Switch to Transaction mode (port 6543)"
echo ""

# Get current DATABASE_URL
CURRENT_URL=$(gcloud secrets versions access latest --secret="cms-automation-prod-DATABASE_URL")

echo "Current URL: $CURRENT_URL"
echo ""

# Replace Session mode port (5432) with Transaction mode port (6543)
# postgresql+asyncpg://...@aws-1-us-east-1.pooler.supabase.com:5432/postgres
# becomes
# postgresql+asyncpg://...@aws-1-us-east-1.pooler.supabase.com:6543/postgres

NEW_URL="${CURRENT_URL/:5432\//:6543\/}"

echo "New URL: $NEW_URL"
echo ""

# Update secret
echo "📝 Updating DATABASE_URL secret..."
echo -n "$NEW_URL" | gcloud secrets versions add cms-automation-prod-DATABASE_URL --data-file=-

echo "✅ Secret updated!"
echo ""
echo "🔄 Now redeploy backend to use Transaction mode:"
echo "   export FORCE_DEPLOY=\"yes\" && bash scripts/deployment/deploy-prod.sh"
echo ""
echo "📖 About the modes:"
echo "   - Session mode (port 5432): Client limit = pool_size (15-20)"
echo "   - Transaction mode (port 6543): Much higher limits, better for Cloud Run"
