#!/bin/bash
set -e

echo "🔙 Rolling back problematic migration: 20251107_1000"
echo ""

# Get DATABASE_URL
export DATABASE_URL=$(gcloud secrets versions access latest --secret="cms-automation-prod-DATABASE_URL")

cd backend

echo "📊 Current migration status:"
python3 -c "
import asyncio
from alembic.config import Config
from alembic import command

config = Config('alembic.ini')
command.current(config)
"

echo ""
echo "🔄 Rolling back to previous revision..."
python3 -c "
import asyncio
from alembic.config import Config
from alembic import command

config = Config('alembic.ini')
command.downgrade(config, '-1')
"

echo ""
echo "✅ Migration rolled back!"
echo ""
echo "📊 New migration status:"
python3 -c "
import asyncio
from alembic.config import Config
from alembic import command

config = Config('alembic.ini')
command.current(config)
"
