#!/usr/bin/env python3
"""Debug script to test reparse functionality and identify the root cause of failures."""

import asyncio
import os
import sys
import traceback
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def debug_reparse():
    """Debug the reparse functionality step by step."""

    print("=" * 80)
    print("REPARSE DEBUG SCRIPT")
    print("=" * 80)

    # Step 1: Test database connection
    print("\n[1] Testing database connection...")
    try:
        from src.config.database import DatabaseConfig
        from sqlalchemy import text

        db_config = DatabaseConfig()
        factory = db_config.get_session_factory()
        async with factory() as session:
            result = await session.execute(text("SELECT 1"))
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return

    # Step 2: Load worklist item
    print("\n[2] Loading worklist item 6...")
    try:
        from src.models import WorklistItem, Article
        from sqlalchemy import select

        async with factory() as session:
            stmt = select(WorklistItem).where(WorklistItem.id == 6)
            result = await session.execute(stmt)
            item = result.scalar_one_or_none()

            if not item:
                print("❌ Worklist item 6 not found")
                return

            print(f"✅ Loaded worklist item: {item.title}")
            print(f"   - Article ID: {item.article_id}")
            print(f"   - Status: {item.status}")
            print(f"   - Has raw_html: {bool(item.raw_html)}")
            print(f"   - Raw HTML length: {len(item.raw_html or '')}")
    except Exception as e:
        print(f"❌ Failed to load worklist item: {e}")
        traceback.print_exc()
        return

    # Step 3: Test parser initialization
    print("\n[3] Initializing article parser...")
    try:
        from src.services.parser import ArticleParserService
        from src.config import get_settings

        settings = get_settings()
        print(f"   - USE_UNIFIED_PARSER: {settings.USE_UNIFIED_PARSER}")
        print(f"   - ANTHROPIC_API_KEY present: {bool(settings.ANTHROPIC_API_KEY)}")
        print(f"   - API key length: {len(settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else 0}")

        parser = ArticleParserService(
            use_ai=True,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            use_unified_prompt=settings.USE_UNIFIED_PARSER,
        )
        print("✅ Parser initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize parser: {e}")
        traceback.print_exc()
        return

    # Step 4: Test parsing
    print("\n[4] Testing document parsing...")
    try:
        raw_html = item.raw_html or item.content
        if not raw_html:
            print("❌ No content to parse")
            return

        print(f"   - Parsing content of length: {len(raw_html)}")
        print(f"   - Using unified prompt: {parser.use_unified_prompt}")

        result = parser.parse_document(raw_html)

        if result.success:
            print("✅ Parsing succeeded!")
            print(f"   - Title: {result.parsed_article.title_main}")
            print(f"   - Author: {result.parsed_article.author_name}")
            print(f"   - Images: {len(result.parsed_article.images)}")
            print(f"   - SEO suggestions present:")
            print(f"     * suggested_meta_description: {bool(result.parsed_article.suggested_meta_description)}")
            print(f"     * suggested_seo_keywords: {result.parsed_article.suggested_seo_keywords}")
            print(f"     * suggested_titles: {result.parsed_article.suggested_titles is not None}")
            print(f"   - Proofreading:")
            print(f"     * Issues: {len(result.parsed_article.proofreading_issues or [])}")
            print(f"   - FAQs: {len(result.parsed_article.faqs or [])}")
        else:
            print("❌ Parsing failed!")
            print(f"   - Errors: {result.errors}")
            for error in result.errors:
                print(f"     * {error.error_type}: {error.error_message}")
            return
    except Exception as e:
        print(f"❌ Parsing exception: {e}")
        traceback.print_exc()
        return

    # Step 5: Test database save
    print("\n[5] Testing database save...")
    try:
        async with factory() as session:
            # Get article
            if item.article_id:
                article = await session.get(Article, item.article_id)
                if article:
                    print(f"✅ Loaded article {article.id}")

                    # Try to save parsed data
                    parsed_article = result.parsed_article

                    print("   - Updating article fields...")
                    article.title_main = parsed_article.title_main
                    article.author_name = parsed_article.author_name
                    article.meta_description = parsed_article.meta_description
                    article.seo_keywords = parsed_article.seo_keywords or []
                    article.tags = parsed_article.tags or []

                    print("   - Updating SEO suggestions...")
                    article.suggested_meta_description = parsed_article.suggested_meta_description
                    print(f"     * suggested_seo_keywords type: {type(parsed_article.suggested_seo_keywords)}")
                    print(f"     * suggested_seo_keywords value: {parsed_article.suggested_seo_keywords}")
                    article.suggested_seo_keywords = parsed_article.suggested_seo_keywords or []

                    print("   - Updating proofreading data...")
                    article.proofreading_issues = parsed_article.proofreading_issues or []

                    print("   - Committing to database...")
                    await session.commit()
                    print("✅ Database save successful!")

                    # Verify data was saved
                    await session.refresh(article)
                    print("\n   - Verification:")
                    print(f"     * suggested_meta_description: {article.suggested_meta_description[:50] if article.suggested_meta_description else None}...")
                    print(f"     * suggested_seo_keywords: {article.suggested_seo_keywords}")

                else:
                    print("❌ Article not found")
            else:
                print("❌ No article_id in worklist item")
    except Exception as e:
        print(f"❌ Database save failed: {e}")
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(debug_reparse())
