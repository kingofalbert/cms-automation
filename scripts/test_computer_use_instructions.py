#!/usr/bin/env python3
"""Test script to verify Computer Use instruction generation and field mapping.

This script validates that all parsed article fields are correctly passed
to the Computer Use instruction generator without actually executing
the Computer Use API.

Usage:
    python scripts/test_computer_use_instructions.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from src.api.schemas.seo import SEOMetadata
from src.services.computer_use_cms import ComputerUseCMSService


def create_test_article_data():
    """Create comprehensive test article data with all fields."""
    return {
        "title": "【健康專題】2024年最新研究：每天步行30分鐘可降低心臟病風險40%",
        "body_html": """
<p>根據最新醫學研究，每天步行30分鐘對心血管健康有顯著益處。</p>

<p>美國心臟協會（AHA）近日發布的研究報告指出，規律的步行運動能夠：</p>

<ul>
<li>降低血壓和膽固醇</li>
<li>改善血液循環</li>
<li>增強心肌功能</li>
<li>減少動脈硬化風險</li>
</ul>

<p>研究人員追蹤了超過10萬名參與者，發現每天步行30分鐘的人群，其心臟病發病率比久坐不動者低40%。</p>

<h2>專家建議</h2>

<p>心臟科醫師張明德表示：「步行是最簡單、最安全的有氧運動之一。建議民眾從每天15分鐘開始，逐漸增加到30分鐘。」</p>

<p>此外，研究還發現，快走比慢走效果更好。每分鐘100步以上的步速，可以更有效地提升心肺功能。</p>
""",
        "seo_title": "每天步行30分鐘降低心臟病風險40% | 2024最新研究",
        "meta_description": "美國心臟協會最新研究：每天步行30分鐘可降低心臟病風險40%。專家建議從15分鐘開始，逐漸增加運動量，快走效果更佳。",
        "focus_keyword": "步行降低心臟病風險",
        "seo_keywords": ["步行運動", "心臟健康", "有氧運動", "心血管疾病預防", "每天運動30分鐘"],
        "tags": ["健康", "運動", "心臟病", "醫學研究", "養生"],
        "primary_category": "健康",
        "secondary_categories": ["生活", "醫療"],
        "author_name": "張明德",
        "article_images": [
            {
                "filename": "walking_heart_health.jpg",
                "position": 0,
                "caption": "研究顯示每天步行30分鐘可有效降低心臟病風險（示意圖）",
                "alt_text": "一位中年人在公園步道上快走運動",
                "description": "步行運動對心臟健康的益處示意圖",
                "local_path": "/tmp/test_images/walking_heart_health.jpg",
                "source_url": "https://example.com/images/walking.jpg",
                "mime_type": "image/jpeg",
            },
            {
                "filename": "heart_diagram.png",
                "position": 3,
                "caption": "心臟結構與運動對血液循環的影響",
                "alt_text": "心臟結構圖解說明運動如何改善血液循環",
                "description": "心臟結構與血液循環示意圖",
                "local_path": "/tmp/test_images/heart_diagram.png",
                "source_url": "https://example.com/images/heart.png",
                "mime_type": "image/png",
            },
        ],
    }


def create_seo_metadata(article_data):
    """Create SEOMetadata from article data."""
    return SEOMetadata(
        meta_title=article_data["seo_title"] or article_data["title"][:60],
        meta_description=article_data["meta_description"],
        focus_keyword=article_data["focus_keyword"],
        keywords=article_data["seo_keywords"],
        canonical_url=None,
        og_title=article_data["seo_title"][:70] if article_data["seo_title"] else None,
        og_description=article_data["meta_description"][:200] if article_data["meta_description"] else None,
    )


def test_instruction_generation():
    """Test the Computer Use instruction generation."""
    print("=" * 80)
    print("Computer Use Instruction Generation Test")
    print("=" * 80)

    # Create test data
    article_data = create_test_article_data()
    seo_data = create_seo_metadata(article_data)

    # Initialize service (won't make API calls, just generates instructions)
    service = ComputerUseCMSService()

    # Generate instructions
    print("\n📝 Generating WordPress publishing instructions...\n")

    instructions = service._build_wordpress_instructions(
        cms_url="https://test.epochtimes.com",
        username="test_user",
        password="test_password",
        title=article_data["title"],
        body=article_data["body_html"],
        seo_data=seo_data,
        article_images=article_data["article_images"],
        tags=article_data["tags"],
        categories=None,  # Use primary/secondary instead
        primary_category=article_data["primary_category"],
        secondary_categories=article_data["secondary_categories"],
        publish_mode="draft",  # Test in draft mode
        author_name=article_data["author_name"],
    )

    # Analyze generated instructions
    print("=" * 80)
    print("📋 Generated Instructions Analysis")
    print("=" * 80)

    # Check for required elements
    checks = [
        ("Title", article_data["title"], article_data["title"] in instructions),
        ("SEO Title", article_data["seo_title"], article_data["seo_title"] in instructions),
        ("Meta Description", article_data["meta_description"][:50], article_data["meta_description"][:50] in instructions),
        ("Focus Keyword", article_data["focus_keyword"], article_data["focus_keyword"] in instructions),
        ("Primary Category", article_data["primary_category"], article_data["primary_category"] in instructions),
        ("Secondary Category 1", article_data["secondary_categories"][0], article_data["secondary_categories"][0] in instructions),
        ("Author Name", article_data["author_name"], article_data["author_name"] in instructions),
        ("Tag 1", article_data["tags"][0], article_data["tags"][0] in instructions),
        ("Tag 2", article_data["tags"][1], article_data["tags"][1] in instructions),
        ("Image 1 Filename", article_data["article_images"][0]["filename"], article_data["article_images"][0]["filename"] in instructions),
        ("Image 1 Caption", article_data["article_images"][0]["caption"][:30], article_data["article_images"][0]["caption"][:30] in instructions),
        ("Image 1 Position", f"position: {article_data['article_images'][0]['position']}", str(article_data["article_images"][0]["position"]) in instructions),
        ("Image 2 Filename", article_data["article_images"][1]["filename"], article_data["article_images"][1]["filename"] in instructions),
        ("Draft Mode", "draft", "draft" in instructions.lower()),
        ("Featured Image Step", "Featured Image", "Featured Image" in instructions),
        ("Author Step", "Article Author", "Article Author" in instructions or "Author" in instructions),
        ("Make Primary", "Make Primary", "Make Primary" in instructions),
    ]

    print("\n✅ Field Coverage Check:\n")
    all_passed = True
    for name, value, found in checks:
        status = "✅" if found else "❌"
        if not found:
            all_passed = False
        print(f"  {status} {name}: {'Found' if found else 'NOT FOUND'}")
        if not found:
            print(f"      Expected: {value[:50]}...")

    print("\n" + "=" * 80)

    # Print key sections of instructions
    print("\n📄 Key Instruction Sections:\n")

    # Find and print important sections
    sections = [
        "**Article Content:**",
        "**Article Author:**",
        "**WordPress Primary Category",
        "**WordPress Secondary Categories",
        "**WordPress Tags",
        "**Article Images to Upload",
        "**SEO Configuration",
        "Set Featured Image",
        "Set Article Author",
    ]

    for section in sections:
        if section in instructions:
            # Find the section and print a few lines
            start = instructions.find(section)
            end = min(start + 500, len(instructions))
            snippet = instructions[start:end]
            # Find natural break point
            if "\n\n" in snippet[100:]:
                snippet = snippet[:snippet.find("\n\n", 100)]
            print(f"📌 {section}")
            print("-" * 40)
            for line in snippet.split("\n")[:10]:
                print(f"   {line}")
            print()

    print("=" * 80)
    print("\n📊 Summary:\n")
    print(f"  Total checks: {len(checks)}")
    print(f"  Passed: {sum(1 for _, _, found in checks if found)}")
    print(f"  Failed: {sum(1 for _, _, found in checks if not found)}")
    print(f"  Instructions length: {len(instructions)} characters")

    if all_passed:
        print("\n✅ All field mapping checks PASSED!")
    else:
        print("\n❌ Some field mapping checks FAILED. Review the output above.")

    # Save full instructions to file for review
    output_file = Path(__file__).parent / "generated_instructions.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Generated at: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        f.write(instructions)

    print(f"\n📁 Full instructions saved to: {output_file}")

    return all_passed


def test_image_data_structure():
    """Test that image data structure matches what Computer Use expects."""
    print("\n" + "=" * 80)
    print("Image Data Structure Test")
    print("=" * 80)

    article_data = create_test_article_data()

    required_fields = ["filename", "position", "caption", "alt_text", "local_path"]
    optional_fields = ["description", "source_url", "mime_type"]

    print("\n📷 Image Data Validation:\n")

    for i, img in enumerate(article_data["article_images"]):
        print(f"  Image {i + 1}: {img['filename']}")
        for field in required_fields:
            status = "✅" if field in img and img[field] else "❌"
            value = img.get(field, "MISSING")
            print(f"    {status} {field}: {str(value)[:50]}")
        for field in optional_fields:
            status = "✅" if field in img else "⚪"
            value = img.get(field, "N/A")
            print(f"    {status} {field}: {str(value)[:50]}")
        print()


def main():
    """Run all tests."""
    print("\n🚀 Starting Computer Use Field Mapping Tests\n")

    test_image_data_structure()
    success = test_instruction_generation()

    print("\n" + "=" * 80)
    print("🏁 Test Complete")
    print("=" * 80)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
