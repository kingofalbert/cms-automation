#!/usr/bin/env python3
"""
Test all imports for title generation service to ensure they work
before deploying to production.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("Testing imports for title generation service...")
print("=" * 60)

try:
    # Test database import
    print("1. Testing database import...")
    from src.config.database import get_session as get_db
    print("   ✅ Database import successful")
except Exception as e:
    print(f"   ❌ Database import failed: {e}")
    sys.exit(1)

try:
    # Test settings import
    print("2. Testing settings import...")
    from src.config import settings
    print("   ✅ Settings import successful")
except Exception as e:
    print(f"   ❌ Settings import failed: {e}")
    sys.exit(1)

try:
    # Test models import
    print("3. Testing models import...")
    from src.models.article import Article
    from src.models.worklist import WorklistItem
    print("   ✅ Models import successful")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    sys.exit(1)

try:
    # Test title generator service import
    print("4. Testing title generator service import...")
    from src.services.title_generator import TitleGeneratorService, TitleGenerationResult
    print("   ✅ Title generator service import successful")
except Exception as e:
    print(f"   ❌ Title generator service import failed: {e}")
    sys.exit(1)

try:
    # Test route import
    print("5. Testing route import...")
    from src.api.routes import title_generation_routes
    print("   ✅ Route import successful")
except Exception as e:
    print(f"   ❌ Route import failed: {e}")
    sys.exit(1)

try:
    # Test Anthropic import
    print("6. Testing Anthropic import...")
    from anthropic import AsyncAnthropic
    print("   ✅ Anthropic import successful")
except Exception as e:
    print(f"   ❌ Anthropic import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL IMPORTS SUCCESSFUL!")
print("Ready for deployment.")
print("=" * 60)