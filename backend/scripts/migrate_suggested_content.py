#!/usr/bin/env python3
"""
Phase 8.4: Migrate suggested_content from article_metadata to dedicated field.

This script extracts suggested_content from article_metadata["proofreading"]
and saves it to the article.suggested_content field, along with generating
the diff structure for the comparison view.

Usage:
    python scripts/migrate_suggested_content.py [--dry-run] [--limit N]

Options:
    --dry-run    Show what would be migrated without making changes
    --limit N    Only process N articles (for testing)
"""

import asyncio
import argparse
import difflib
import re
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from src.models import Article


async def get_async_session() -> AsyncSession:
    """Create async database session."""
    settings = get_settings()
    # Convert PostgresDsn to string before replacing
    db_url = str(settings.DATABASE_URL)
    engine = create_async_engine(
        db_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session()


def generate_content_diff(original: str, suggested: str) -> dict:
    """Generate structured diff data for frontend visualization."""
    if original == suggested:
        return {
            "format": "unified_diff",
            "has_changes": False,
            "changes": [],
            "stats": {"additions": 0, "deletions": 0, "modifications": 0},
        }

    # Split into lines for line-by-line comparison
    original_lines = original.splitlines(keepends=True)
    suggested_lines = suggested.splitlines(keepends=True)

    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        suggested_lines,
        fromfile="original",
        tofile="suggested",
        lineterm=""
    ))

    # Parse diff into structured changes
    changes = []
    additions = 0
    deletions = 0
    current_line_original = 0
    current_line_suggested = 0

    for line in diff:
        if line.startswith("@@"):
            match = re.match(r"@@ -(\d+),?\d* \+(\d+),?\d* @@", line)
            if match:
                current_line_original = int(match.group(1))
                current_line_suggested = int(match.group(2))
        elif line.startswith("-") and not line.startswith("---"):
            changes.append({
                "type": "deletion",
                "line_original": current_line_original,
                "content": line[1:].rstrip("\n"),
            })
            deletions += 1
            current_line_original += 1
        elif line.startswith("+") and not line.startswith("+++"):
            changes.append({
                "type": "addition",
                "line_suggested": current_line_suggested,
                "content": line[1:].rstrip("\n"),
            })
            additions += 1
            current_line_suggested += 1
        elif not line.startswith(("---", "+++")):
            current_line_original += 1
            current_line_suggested += 1

    # Generate word-level diff
    word_changes = generate_word_diff(original, suggested)

    return {
        "format": "unified_diff",
        "has_changes": True,
        "changes": changes,
        "word_changes": word_changes,
        "stats": {
            "additions": additions,
            "deletions": deletions,
            "total_changes": len(changes),
            "original_lines": len(original_lines),
            "suggested_lines": len(suggested_lines),
        },
        "generated_at": datetime.utcnow().isoformat(),
        "migrated": True,
    }


def generate_word_diff(original: str, suggested: str) -> list:
    """Generate word-level diff for inline highlighting."""
    def tokenize(text: str) -> list[str]:
        return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+|[^\s\w]|\s+", text)

    original_words = tokenize(original)
    suggested_words = tokenize(suggested)

    matcher = difflib.SequenceMatcher(None, original_words, suggested_words)
    word_changes = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            word_changes.append({
                "type": "replace",
                "original": "".join(original_words[i1:i2]),
                "suggested": "".join(suggested_words[j1:j2]),
                "original_pos": [i1, i2],
                "suggested_pos": [j1, j2],
            })
        elif tag == "delete":
            word_changes.append({
                "type": "delete",
                "original": "".join(original_words[i1:i2]),
                "original_pos": [i1, i2],
            })
        elif tag == "insert":
            word_changes.append({
                "type": "insert",
                "suggested": "".join(suggested_words[j1:j2]),
                "suggested_pos": [j1, j2],
            })

    return word_changes


async def migrate_articles(dry_run: bool = False, limit: int | None = None):
    """Migrate suggested_content from article_metadata to dedicated field."""
    session = await get_async_session()

    try:
        # Find articles that have proofreading metadata but no suggested_content field
        query = (
            select(Article)
            .where(
                Article.suggested_content.is_(None),
                Article.article_metadata.isnot(None),
            )
            .order_by(Article.id.desc())
        )

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        articles = result.scalars().all()

        print(f"\n{'='*60}")
        print(f"Phase 8.4: Migrate suggested_content")
        print(f"{'='*60}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Found {len(articles)} articles to check")
        print(f"{'='*60}\n")

        migrated = 0
        skipped = 0
        errors = 0

        for article in articles:
            try:
                # Check if article_metadata has proofreading data
                metadata = article.article_metadata or {}
                proofreading = metadata.get("proofreading", {})
                suggested_content = proofreading.get("suggested_content")

                if not suggested_content:
                    skipped += 1
                    continue

                # Check if there are actual changes
                original_content = article.body or ""
                has_changes = original_content != suggested_content

                print(f"\nArticle {article.id}: {article.title[:50]}...")
                print(f"  Original length: {len(original_content)}")
                print(f"  Suggested length: {len(suggested_content)}")
                print(f"  Has changes: {has_changes}")

                if not dry_run:
                    # Migrate the data
                    article.suggested_content = suggested_content

                    # Generate diff structure
                    article.suggested_content_changes = generate_content_diff(
                        original_content,
                        suggested_content
                    )

                    session.add(article)

                    diff_stats = article.suggested_content_changes.get("stats", {})
                    print(f"  ✅ Migrated: +{diff_stats.get('additions', 0)} -{diff_stats.get('deletions', 0)}")
                else:
                    # Generate diff for display only
                    diff_data = generate_content_diff(original_content, suggested_content)
                    diff_stats = diff_data.get("stats", {})
                    print(f"  [DRY RUN] Would migrate: +{diff_stats.get('additions', 0)} -{diff_stats.get('deletions', 0)}")

                migrated += 1

            except Exception as e:
                errors += 1
                print(f"  ❌ Error: {e}")

        if not dry_run:
            await session.commit()

        print(f"\n{'='*60}")
        print(f"Migration Summary")
        print(f"{'='*60}")
        print(f"  Migrated: {migrated}")
        print(f"  Skipped (no suggested_content): {skipped}")
        print(f"  Errors: {errors}")
        print(f"{'='*60}\n")

        return migrated

    finally:
        await session.close()


async def show_stats():
    """Show current statistics of suggested_content field."""
    session = await get_async_session()

    try:
        # Count articles with suggested_content
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.suggested_content.isnot(None))
        )
        with_suggested = result.scalar()

        # Count total articles
        result = await session.execute(select(func.count(Article.id)))
        total = result.scalar()

        # Count articles with proofreading metadata
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.article_metadata.isnot(None))
        )
        with_metadata = result.scalar()

        print(f"\n{'='*60}")
        print(f"Current Statistics")
        print(f"{'='*60}")
        print(f"  Total articles: {total}")
        print(f"  With article_metadata: {with_metadata}")
        print(f"  With suggested_content field: {with_suggested}")
        print(f"  Need migration: {with_metadata - with_suggested}")
        print(f"{'='*60}\n")

    finally:
        await session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate suggested_content from article_metadata to dedicated field"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process N articles (for testing)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current statistics only"
    )

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_stats())
    else:
        asyncio.run(migrate_articles(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
