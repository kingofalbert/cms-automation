#!/usr/bin/env python3
"""Debug script to inspect AI response."""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def debug_ai_response():
    print("=" * 80)
    print("AI RESPONSE DEBUG")
    print("=" * 80)

    from src.config.database import DatabaseConfig
    from src.models import WorklistItem
    from sqlalchemy import select

    # Get worklist item
    db_config = DatabaseConfig()
    factory = db_config.get_session_factory()

    async with factory() as session:
        stmt = select(WorklistItem).where(WorklistItem.id == 6)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            print("Item not found")
            return

        # Test AI parsing with detailed logging
        from src.services.parser import ArticleParserService
        from src.config import get_settings

        settings = get_settings()

        print(f"\n[1] Settings:")
        print(f"   - USE_UNIFIED_PARSER: {settings.USE_UNIFIED_PARSER}")

        # Create parser
        parser = ArticleParserService(
            use_ai=True,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            use_unified_prompt=settings.USE_UNIFIED_PARSER,
        )

        # Build prompt
        raw_html = item.raw_html or item.content
        prompt = parser._build_ai_parsing_prompt(raw_html)

        print(f"\n[2] Prompt preview (first 500 chars):")
        print(prompt[:500])
        print("...")
        print(f"\n[3] Prompt contains 'suggested_seo': {('suggested_seo' in prompt)}")
        print(f"[4] Prompt contains 'SEO': {('SEO' in prompt)}")
        print(f"[5] Prompt type: {'unified' if parser.use_unified_prompt else 'basic'}")

        # Call AI
        print("\n[6] Calling Claude API...")
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=4096,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        print(f"\n[7] AI Response (first 1000 chars):")
        print(response_text[:1000])

        # Parse JSON
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            parsed_data = json.loads(cleaned)
            print(f"\n[8] Parsed JSON keys:")
            print(f"   {list(parsed_data.keys())}")

            print(f"\n[9] SEO-related fields:")
            print(f"   - suggested_seo: {bool(parsed_data.get('suggested_seo'))}")
            print(f"   - suggested_titles: {bool(parsed_data.get('suggested_titles'))}")
            print(f"   - suggested_meta_description: {bool(parsed_data.get('suggested_meta_description'))}")

            if parsed_data.get('suggested_seo'):
                print(f"\n[10] suggested_seo content:")
                print(json.dumps(parsed_data['suggested_seo'], indent=2, ensure_ascii=False))

        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parse error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ai_response())
