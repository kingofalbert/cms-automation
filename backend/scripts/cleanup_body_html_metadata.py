#!/usr/bin/env python3
"""One-time script to clean up metadata sections from existing article body_html.

This script removes Tag suggestions and SEO keywords sections that were
incorrectly included in body_html during parsing.

Usage:
    poetry run python scripts/cleanup_body_html_metadata.py [--dry-run]
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_session
from src.models.article import Article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_metadata_sections_from_body(body_html: str) -> str:
    """Remove metadata sections (Tag suggestions, SEO keywords, etc.) from body content.

    These sections should be extracted separately and not included in the article body.
    Complete list of patterns to remove:

    1. Tag/Label suggestions:
       - ### Tag 建議 / ### Tag建議 / ### 標籤建議
    2. SEO keyword suggestions:
       - ### SEO 關鍵字建議 / ### SEO關鍵字建議 / ### 關鍵字建議
    3. Meta description suggestions:
       - ### Meta 摘要建議 / ### Meta Description
    4. Meta description markers (extracted to meta_description field):
       - 【Meta摘要】 / 【Meta】 / Meta摘要：
    5. SEO Title markers (extracted to seo_title field):
       - 這是 SEO title / 【SEO title】 / SEO title：
    """
    if not body_html:
        return body_html

    # Patterns for metadata section headers (markdown style in <p> tags)
    metadata_patterns = [
        # Tag suggestions (various formats)
        r'<p>\s*#{1,3}\s*Tag\s*建議\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        r'<p>\s*#{1,3}\s*標籤建議\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        # SEO keyword suggestions
        r'<p>\s*#{1,3}\s*SEO\s*關鍵字建議\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        r'<p>\s*#{1,3}\s*關鍵字建議\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        r'<p>\s*#{1,3}\s*SEO\s*Keywords?\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        # Meta description suggestions
        r'<p>\s*#{1,3}\s*Meta\s*摘要建議\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        r'<p>\s*#{1,3}\s*Meta\s*Description\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        # Additional suggestion sections
        r'<p>\s*#{1,3}\s*摘要建議\s*</p>.*?(?=<p>\s*#{1,3}|$)',
        r'<p>\s*#{1,3}\s*Excerpt\s*</p>.*?(?=<p>\s*#{1,3}|$)',
    ]

    cleaned = body_html
    for pattern in metadata_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Plain text markdown headers (not wrapped in <p> tags)
    plain_text_patterns = [
        r'###\s*Tag\s*建議\s*\n.*?(?=###|$)',
        r'###\s*標籤建議\s*\n.*?(?=###|$)',
        r'###\s*SEO\s*關鍵字建議\s*\n.*?(?=###|$)',
        r'###\s*關鍵字建議\s*\n.*?(?=###|$)',
        r'###\s*Meta\s*摘要建議\s*\n.*?(?=###|$)',
        r'###\s*摘要建議\s*\n.*?(?=###|$)',
    ]

    for pattern in plain_text_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Meta Description markers (【Meta摘要】, 【Meta】, Meta摘要：)
    meta_marker_patterns = [
        r'<p>\s*【Meta摘要】.*?</p>',
        r'<p>\s*【Meta】.*?</p>',
        r'<p>\s*Meta摘要[：:]\s*.*?</p>',
        r'【Meta摘要】[^\n]*\n?',
        r'【Meta】[^\n]*\n?',
        r'Meta摘要[：:][^\n]*\n?',
    ]

    for pattern in meta_marker_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # SEO Title markers (這是 SEO title, 【SEO title】)
    seo_title_patterns = [
        r'<p>\s*這是\s*SEO\s*title[：:]?\s*.*?</p>',
        r'<p>\s*【SEO\s*title】[：:]?\s*.*?</p>',
        r'<p>\s*SEO\s*title[：:]\s*.*?</p>',
        r'這是\s*SEO\s*title[：:]?[^\n]*\n?',
        r'【SEO\s*title】[：:]?[^\n]*\n?',
        r'SEO\s*title[：:][^\n]*\n?',
    ]

    for pattern in seo_title_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Clean up any resulting empty paragraphs or extra whitespace
    cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()

    return cleaned


async def main_async(dry_run: bool, article_id: int | None):
    """Main async function to run the cleanup."""
    async for session in get_session():
        # Query articles
        if article_id:
            stmt = select(Article).where(Article.cms_article_id == article_id)
        else:
            stmt = select(Article).where(Article.body_html.isnot(None))

        result = await session.execute(stmt)
        articles = result.scalars().all()

        logger.info(f"Found {len(articles)} articles to check")

        updated_count = 0
        for article in articles:
            if not article.body_html:
                continue

            # Check if body contains metadata sections
            has_metadata = any([
                '### Tag' in article.body_html,
                '### SEO' in article.body_html,
                '### 標籤' in article.body_html,
                '### 關鍵字' in article.body_html,
            ])

            if not has_metadata:
                continue

            # Clean the body_html
            cleaned = clean_metadata_sections_from_body(article.body_html)

            if cleaned != article.body_html:
                logger.info(f"Article {article.article_id}: '{article.title[:30] if article.title else 'No title'}...' needs cleanup")
                logger.info(f"  - Original length: {len(article.body_html)}")
                logger.info(f"  - Cleaned length: {len(cleaned)}")

                if not dry_run:
                    # Update using SQL to avoid ORM issues
                    update_stmt = (
                        update(Article)
                        .where(Article.article_id == article.article_id)
                        .values(body_html=cleaned)
                    )
                    await session.execute(update_stmt)
                    updated_count += 1

        if not dry_run and updated_count > 0:
            await session.commit()
            logger.info(f"Updated {updated_count} articles")
        elif dry_run:
            logger.info(f"[DRY RUN] Would update {updated_count} articles")
        else:
            logger.info("No articles needed cleanup")

        break  # Only use one session


def main():
    parser = argparse.ArgumentParser(description="Clean metadata sections from article body_html")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be changed without modifying")
    parser.add_argument('--article-id', type=int, help="Clean a specific article by ID")
    args = parser.parse_args()

    asyncio.run(main_async(args.dry_run, args.article_id))


if __name__ == "__main__":
    main()
