"""
Test script to compare article parsing results with AI parsing

This script:
1. Fetches an article from the database
2. Parses it using our ArticleParserService
3. Uses Claude AI to parse the same content independently
4. Compares the results to identify discrepancies
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from src.config.database import get_db_config
from src.models.article import Article
from src.services.parser.article_parser import ArticleParserService


async def get_first_article():
    """Get the first article from database"""
    db_config = get_db_config()
    async with db_config.session() as session:
        result = await session.execute(
            select(Article).where(Article.id == 902386).limit(1)
        )
        article = result.scalar_one_or_none()
        return article


async def test_parsing():
    """Test article parsing and compare with AI"""
    print("=" * 80)
    print("ARTICLE PARSING COMPARISON TEST")
    print("=" * 80)

    # Get article
    article = await get_first_article()
    if not article:
        print("❌ No article found with ID 902386")
        return

    print(f"\n✅ Found article: ID={article.id}")
    print(f"   Title: {article.title}")
    print(f"   Author: {article.author}")
    print(f"   Has content: {bool(article.content)}")

    # Check if parsing fields exist
    print(f"\n📊 Parsing Fields:")
    print(f"   title_prefix: {getattr(article, 'title_prefix', 'N/A')}")
    print(f"   title_main: {getattr(article, 'title_main', 'N/A')}")
    print(f"   title_suffix: {getattr(article, 'title_suffix', 'N/A')}")
    print(f"   author_name: {getattr(article, 'author_name', 'N/A')}")
    print(f"   author_line: {getattr(article, 'author_line', 'N/A')}")
    print(f"   meta_description: {getattr(article, 'meta_description', 'N/A')}")
    print(f"   seo_keywords: {getattr(article, 'seo_keywords', 'N/A')}")

    # Parse with AI
    if article.content:
        print(f"\n🤖 Parsing with AI...")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not set")
            return

        parser = ArticleParserService(use_ai=True, anthropic_api_key=api_key)
        result = parser.parse_document(article.content)

        if result.success:
            print("✅ AI parsing succeeded")
            parsed = result.parsed_article
            print(f"\n📝 AI Parsed Results:")
            print(f"   Title: {parsed.title_main}")
            print(f"   Title Prefix: {parsed.title_prefix}")
            print(f"   Title Suffix: {parsed.title_suffix}")
            print(f"   Author Name: {parsed.author_name}")
            print(f"   Author Line: {parsed.author_line}")
            print(f"   Meta Description: {parsed.meta_description[:100] if parsed.meta_description else 'None'}...")
            print(f"   SEO Keywords: {parsed.seo_keywords}")
            print(f"   Images: {len(parsed.images)} images found")
            print(f"   Parsing Method: {parsed.parsing_method}")
            print(f"   Confidence: {parsed.parsing_confidence}")

            # Compare with database values
            print(f"\n🔍 COMPARISON:")
            print(f"   DB title vs AI title: '{article.title}' vs '{parsed.title_main}'")
            print(f"   DB author vs AI author: '{article.author}' vs '{parsed.author_name}'")

            # Check if title is just the ID
            if article.title == str(article.id):
                print(f"   ⚠️  WARNING: DB title is just the article ID!")

            if article.author == str(article.id):
                print(f"   ⚠️  WARNING: DB author is just the article ID!")

        else:
            print("❌ AI parsing failed")
            for error in result.errors:
                print(f"   Error: {error.error_message}")
    else:
        print("\n❌ Article has no content to parse")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_parsing())
