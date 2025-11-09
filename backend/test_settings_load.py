#!/usr/bin/env python
"""Test script to verify settings can be loaded correctly."""

import os
import sys

# Set environment variables for testing
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:8000"
os.environ["CELERY_ACCEPT_CONTENT"] = "json"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["SECRET_KEY"] = "test" * 16  # 64 chars
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
os.environ["CMS_BASE_URL"] = "https://example.com"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

print("Environment variables set:")
print(f"  ALLOWED_ORIGINS = {os.environ['ALLOWED_ORIGINS']}")
print(f"  CELERY_ACCEPT_CONTENT = {os.environ['CELERY_ACCEPT_CONTENT']}")
print()

try:
    from src.config.settings import get_settings

    print("Loading settings...")
    settings = get_settings()

    print("✅ Settings loaded successfully!")
    print(f"  ALLOWED_ORIGINS = {settings.ALLOWED_ORIGINS}")
    print(f"  CELERY_ACCEPT_CONTENT = {settings.CELERY_ACCEPT_CONTENT}")

    sys.exit(0)

except Exception as e:
    print(f"❌ Failed to load settings:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
