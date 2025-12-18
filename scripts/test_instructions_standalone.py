#!/usr/bin/env python3
"""Standalone test for Computer Use instruction generation.

This script directly tests the instruction building logic without FastAPI dependencies.
"""

import re


def build_wordpress_instructions(
    cms_url: str,
    username: str,
    password: str,
    title: str,
    body: str,
    meta_title: str,
    meta_description: str,
    focus_keyword: str,
    keywords: list[str],
    article_images: list[dict],
    tags: list[str] | None = None,
    primary_category: str | None = None,
    secondary_categories: list[str] | None = None,
    publish_mode: str = "publish",
    author_name: str | None = None,
    faqs: list[dict[str, str]] | None = None,
) -> str:
    """Build WordPress-specific instructions (copied from computer_use_cms.py)."""
    import json

    tags = tags or []
    secondary_categories = secondary_categories or []
    faqs = faqs or []
    has_images = bool(article_images)
    has_categories = bool(primary_category or secondary_categories)
    has_author = bool(author_name)
    has_faqs = bool(faqs)

    body_preview = body[:500] + "..." if len(body) > 500 else body

    if has_images:
        image_lines = []
        for idx, img in enumerate(article_images, 1):
            position = img.get('position', 0)
            caption = img.get('caption', 'No caption provided')
            alt_text = img.get('alt_text', caption)
            filename = img.get('filename', f'image_{idx}')
            local_path = img.get('local_path', '')
            source_url = img.get('source_url', '')

            image_lines.append(
                f"  Image {idx}:\n"
                f"    - Filename: {filename}\n"
                f"    - Insert after paragraph: {position} (0 = before first paragraph, 1 = after first paragraph, etc.)\n"
                f"    - Caption/Alt text: {caption[:100]}{'...' if len(caption) > 100 else ''}\n"
                f"    - Local path: {local_path}\n"
                f"    - Original URL: {source_url[:80]}{'...' if len(str(source_url)) > 80 else ''}"
            )

        image_info = "\n**Article Images to Upload (with exact positions):**\n" + "\n".join(image_lines)
    else:
        image_info = ""

    if tags:
        tags_info = "\n**WordPress Tags to Add:**\n" + "\n".join(f"  - {tag}" for tag in tags)
    else:
        tags_info = ""

    categories_info = ""
    if primary_category:
        categories_info += f"""
**WordPress Primary Category (主分類) - CRITICAL:**
  - Category: {primary_category}
  - This determines the article URL structure (e.g., example.com/{primary_category}/article-slug)
  - This determines the breadcrumb navigation
  - You MUST click "Make Primary" or "設為主分類" after selecting this category
"""
    if secondary_categories:
        categories_info += f"""
**WordPress Secondary Categories (副分類) - For Cross-listing:**
{chr(10).join(f'  - {cat}' for cat in secondary_categories)}
  - These allow the article to appear in multiple category archive pages
  - Do NOT click "Make Primary" for these categories
"""

    author_info = ""
    if author_name:
        author_info = f"""

**Article Author:**
- Author Name: {author_name}
- This author should be selected from the WordPress Author dropdown in the Document sidebar"""

    # Build FAQ Schema info section
    faq_info = ""
    faq_schema_json = ""
    if has_faqs:
        faq_lines = []
        for idx, faq in enumerate(faqs, 1):
            q = faq.get('question', '')[:80]
            a = faq.get('answer', '')[:100]
            faq_lines.append(f"  FAQ {idx}:\n    Q: {q}{'...' if len(faq.get('question', '')) > 80 else ''}\n    A: {a}{'...' if len(faq.get('answer', '')) > 100 else ''}")
        faq_info = "\n**FAQ Schema for AI Search Engines (JSON-LD):**\n" + "\n".join(faq_lines)

        # Build the actual JSON-LD schema
        faq_entities = []
        for faq in faqs:
            faq_entities.append({
                "@type": "Question",
                "name": faq.get('question', ''),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.get('answer', '')
                }
            })
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities
        }
        faq_schema_json = json.dumps(faq_schema, ensure_ascii=False, indent=2)

    publish_summary = (
        "Save the article as a draft (do not publish to the live site)"
        if publish_mode == "draft"
        else "Publish the article to the live site"
    )

    summary_steps = [
        "Navigate to the WordPress admin dashboard",
        "Log in if needed",
        "Create a new post",
        "Set article title",
        "Add article content (body)",
        (
            "Upload article images and insert them at correct positions"
            if has_images
            else "Skip image upload (no images provided)"
        ),
        (
            "Set the Featured Image (題圖) in the Document sidebar"
            if has_images
            else "Skip featured image (no images provided)"
        ),
        (
            f"Set article author to '{author_name}'"
            if has_author
            else "Skip author selection (use default)"
        ),
        (
            f"Set Primary Category ('{primary_category}') with 'Make Primary' and Secondary Categories"
            if primary_category
            else (
                "Set WordPress tags and categories"
                if tags or has_categories
                else "Skip tags/categories (none provided)"
            )
        ),
        "Configure SEO metadata (Yoast SEO or Rank Math)",
        (
            f"Insert FAQ Schema JSON-LD for AI search engines ({len(faqs)} FAQs)"
            if has_faqs
            else "Skip FAQ Schema (no FAQs provided)"
        ),
        publish_summary,
        "Return the post ID and relevant URLs",
    ]

    summary_block = "\n".join(f"{idx}. {item}" for idx, item in enumerate(summary_steps, start=1))

    steps = []
    step_no = 1

    def add_step(title_text: str, bullet_points: list[str]) -> None:
        nonlocal step_no
        bullets = "\n   - ".join(bullet_points)
        steps.append(f"{step_no}. **{title_text}**\n   - {bullets}")
        step_no += 1

    add_step("Navigate to WordPress Admin", [
        f"Open {cms_url}/wp-admin in the browser",
        "Wait for the login page to load",
    ])

    add_step("Log In", [
        f"Enter username: {username}",
        f"Enter password: {password}",
        "Click the \"Log In\" button",
    ])

    add_step("Create a New Post", [
        "Open \"Posts\" → \"Add New\"",
    ])

    add_step("Set the Article Title", [
        "Click the title field",
        f"Paste the article title: {title}",
    ])

    # CRITICAL: Add article content BEFORE inserting images
    # So that paragraph positions (1, 2, 3...) exist for image insertion
    add_step("Add Article Content", [
        "Click inside the content area",
        "Paste the full article body",
    ])

    if has_images:
        image_insertion_instructions = []
        for idx, img in enumerate(article_images, 1):
            position = img.get('position', 0)
            caption = img.get('caption', '')
            filename = img.get('filename', f'image_{idx}')

            if position == 0:
                position_desc = "at the very beginning of the article (before the first paragraph)"
            else:
                position_desc = f"after paragraph {position}"

            image_insertion_instructions.append(
                f"Image {idx} ({filename}): Insert {position_desc}"
                + (f" with caption: '{caption[:50]}...'" if caption else "")
            )

        add_step("Upload and Insert Article Images at Correct Positions", [
            "Now that the article body is in place, insert images at their correct positions",
            "Upload each provided file",
            "**IMPORTANT: For EACH image in the Media Library, set these fields:**",
            "  - Alt Text (替代文字): Use the provided alt_text or caption",
            "  - Caption (圖說): Use the provided caption text - this will display below the image",
            "**IMPORTANT: Insert each image at its specified position:**",
        ] + image_insertion_instructions + [
            "Verify each image shows its caption below it in the editor",
        ])

    if has_images:
        featured_img = next(
            (img for img in article_images if img.get('position') == 0),
            article_images[0] if article_images else None
        )
        if featured_img:
            featured_filename = featured_img.get('filename', 'first uploaded image')
            featured_alt = featured_img.get('alt_text') or featured_img.get('caption', '')

            add_step("Set Featured Image (題圖/特色圖片)", [
                "In the right sidebar, scroll to \"Featured image\" section",
                "Click on \"Set featured image\" button",
                f"From the Media Library, select the image: \"{featured_filename}\"",
                f"Set the alt text to: \"{featured_alt[:100]}...\"" if featured_alt else "Set appropriate alt text",
                "Click \"Set featured image\" to confirm",
            ])

    if has_author:
        add_step("Set Article Author (文章作者)", [
            "In the right sidebar, scroll to the \"Author\" dropdown",
            f"Click the Author dropdown and search for: \"{author_name}\"",
            f"Select \"{author_name}\" from the dropdown list",
        ])

    if tags or has_categories:
        tag_instructions = [
            "In the right sidebar, expand the \"Tags\" panel",
            f"Add each tag from the list: {', '.join(tags)}",
        ] if tags else []

        if primary_category:
            category_instructions = [
                "**CRITICAL: In the right sidebar, expand the \"Categories\" panel**",
                f"**Step 1 - Set Primary Category:** Find \"{primary_category}\"",
                f"Check the checkbox next to \"{primary_category}\"",
                "**Step 2 - Make Primary:** Click \"Make Primary\" or \"設為主分類\"",
            ]
            if secondary_categories:
                category_instructions.append(
                    "**Step 3 - Add Secondary Categories:** Also check:"
                )
                for cat in secondary_categories:
                    category_instructions.append(f"Check \"{cat}\" (do NOT make primary)")
        else:
            category_instructions = []

        add_step("Set Tags and Categories (with Primary Category)",
                 tag_instructions + category_instructions)

    add_step("Configure SEO Metadata", [
        "Scroll to the Yoast SEO (or Rank Math) panel",
        f"Set the focus keyphrase to: {focus_keyword}",
        f"Update the SEO title to: {meta_title}",
        f"Update the meta description to: {meta_description}",
    ])

    # Add FAQ Schema step (for AI search engines like Perplexity, ChatGPT, Google SGE)
    if has_faqs:
        add_step("Insert FAQ Schema JSON-LD (for AI Search Engines)", [
            "**IMPORTANT**: This FAQ Schema is HIDDEN metadata for search engines, NOT visible content",
            'In the editor, click the "+" button to add a new block at the END of the article',
            'Search for "Custom HTML" block and add it',
            "Paste the following JSON-LD script into the Custom HTML block:",
            f'```\n<script type="application/ld+json">\n{faq_schema_json}\n</script>\n```',
            "The block should appear at the bottom of the content but won't be visible to readers",
            "This structured data helps AI search engines understand and feature your FAQs",
            "Take a screenshot showing the Custom HTML block is added",
        ])

    if publish_mode == "draft":
        add_step("Save as Draft (Do NOT Publish)", [
            "Click the \"Save draft\" button",
            "Wait for the \"Draft saved\" confirmation",
        ])
    else:
        add_step("Publish the Article", [
            "Click the \"Publish\" button",
        ])

    add_step("Capture Post Links and ID", [
        "Copy the \"View Post\" link if available (for drafts, copy the editor URL)",
        "Note the WordPress post ID (visible in the URL as ?post=ID or post=ID)",
        "Take a final screenshot for records",
    ])

    result_example = (
        '{"article_id": "<POST_ID>", "article_url": "<PUBLIC_URL>", "editor_url": "<EDITOR_URL>", "status": "published"}'
        if publish_mode != "draft"
        else '{"article_id": "<POST_ID>", "article_url": null, "editor_url": "<EDITOR_URL>", "status": "draft"}'
    )

    add_step("Return Results", [
        "Respond with a JSON object containing the post ID, URLs, and status.",
        f"Example payload: {result_example}",
        "Ensure URLs are absolute and valid.",
    ])

    detailed_block = "\n\n".join(steps)

    instructions = f"""You are an AI assistant helping to prepare an article in WordPress with full SEO configuration.

**Your Task:**
{summary_block}

**WordPress Details:**
- Admin URL: {cms_url}/wp-admin
- Username: {username}
- Password: {password}

**Article Content:**
Title: {title}
Body Preview: {body_preview}
[Full body content will be provided when needed]{image_info}{tags_info}{categories_info}{author_info}{faq_info}

**SEO Configuration (Yoast SEO / Rank Math):**
- Meta Title: {meta_title}
- Meta Description: {meta_description}
- Focus Keyword: {focus_keyword}
- Additional Keywords: {', '.join(keywords)}

**Step-by-Step Instructions:**
{detailed_block}

**Important Notes:**
- Take screenshots at each major step for audit purposes.
- If any errors appear, document them and attempt a reasonable recovery.
- Current publishing mode: "{publish_mode}". If it is "draft", never click the Publish button.

--- FULL ARTICLE BODY START ---
{body}
--- FULL ARTICLE BODY END ---

Begin the task now and follow the steps carefully."""

    return instructions


def main():
    """Run the test."""
    print("=" * 80)
    print("🧪 Computer Use Instruction Generation Test")
    print("=" * 80)

    # Test data
    test_data = {
        "title": "【健康專題】2024年最新研究：每天步行30分鐘可降低心臟病風險40%",
        "body": """<p>根據最新醫學研究，每天步行30分鐘對心血管健康有顯著益處。</p>
<p>美國心臟協會近日發布的研究報告指出，規律的步行運動能夠降低血壓和膽固醇。</p>
<h2>專家建議</h2>
<p>心臟科醫師張明德表示：「步行是最簡單的有氧運動之一。」</p>""",
        "meta_title": "每天步行30分鐘降低心臟病風險40% | 2024最新研究",
        "meta_description": "美國心臟協會最新研究：每天步行30分鐘可降低心臟病風險40%。專家建議從15分鐘開始。",
        "focus_keyword": "步行降低心臟病風險",
        "keywords": ["步行運動", "心臟健康", "有氧運動"],
        "tags": ["健康", "運動", "心臟病", "醫學研究"],
        "primary_category": "健康",
        "secondary_categories": ["生活", "醫療"],
        "author_name": "張明德",
        "article_images": [
            {
                "filename": "walking_heart.jpg",
                "position": 0,
                "caption": "研究顯示每天步行30分鐘可有效降低心臟病風險",
                "alt_text": "一位中年人在公園步道上快走運動",
                "local_path": "/tmp/walking_heart.jpg",
                "source_url": "https://example.com/walking.jpg",
            },
            {
                "filename": "heart_diagram.png",
                "position": 2,
                "caption": "心臟結構與運動對血液循環的影響",
                "alt_text": "心臟結構圖解",
                "local_path": "/tmp/heart_diagram.png",
                "source_url": "https://example.com/heart.png",
            },
        ],
        "faqs": [
            {
                "question": "每天步行30分鐘真的能降低心臟病風險嗎？",
                "answer": "是的，根據美國心臟協會最新研究，每天步行30分鐘可以降低心臟病風險約40%。這是因為步行能改善血液循環、降低血壓和膽固醇。"
            },
            {
                "question": "什麼時間步行最有效果？",
                "answer": "研究顯示，早晨或傍晚步行效果最佳。早晨步行有助於提升一整天的新陳代謝，傍晚步行則有助於舒緩壓力和改善睡眠質量。"
            },
            {
                "question": "步行的正確姿勢是什麼？",
                "answer": "正確的步行姿勢包括：保持頭部正直，眼睛平視前方；肩膀放鬆下沉；手臂自然擺動；腳跟先著地，再過渡到腳尖。"
            },
        ],
    }

    # Generate instructions
    instructions = build_wordpress_instructions(
        cms_url="https://test.epochtimes.com",
        username="test_user",
        password="test_password",
        title=test_data["title"],
        body=test_data["body"],
        meta_title=test_data["meta_title"],
        meta_description=test_data["meta_description"],
        focus_keyword=test_data["focus_keyword"],
        keywords=test_data["keywords"],
        article_images=test_data["article_images"],
        tags=test_data["tags"],
        primary_category=test_data["primary_category"],
        secondary_categories=test_data["secondary_categories"],
        publish_mode="draft",
        author_name=test_data["author_name"],
        faqs=test_data["faqs"],
    )

    # Verify all fields are present
    print("\n📋 Field Coverage Check:\n")

    checks = [
        ("Article Title", test_data["title"], test_data["title"] in instructions),
        ("SEO Title (meta_title)", test_data["meta_title"], test_data["meta_title"] in instructions),
        ("Meta Description", test_data["meta_description"][:30], test_data["meta_description"][:30] in instructions),
        ("Focus Keyword", test_data["focus_keyword"], test_data["focus_keyword"] in instructions),
        ("Keyword 1", test_data["keywords"][0], test_data["keywords"][0] in instructions),
        ("Primary Category", test_data["primary_category"], test_data["primary_category"] in instructions),
        ("Make Primary instruction", "Make Primary", "Make Primary" in instructions),
        ("Secondary Category 1", test_data["secondary_categories"][0], test_data["secondary_categories"][0] in instructions),
        ("Secondary Category 2", test_data["secondary_categories"][1], test_data["secondary_categories"][1] in instructions),
        ("Author Name", test_data["author_name"], test_data["author_name"] in instructions),
        ("Author Step", "Set Article Author", "Set Article Author" in instructions),
        ("Tag 1", test_data["tags"][0], test_data["tags"][0] in instructions),
        ("Tag 2", test_data["tags"][1], test_data["tags"][1] in instructions),
        ("Image 1 filename", test_data["article_images"][0]["filename"], test_data["article_images"][0]["filename"] in instructions),
        ("Image 1 position", "position: 0", "position: 0" in instructions or "paragraph: 0" in instructions),
        ("Image 1 caption", test_data["article_images"][0]["caption"][:20], test_data["article_images"][0]["caption"][:20] in instructions),
        ("Image 2 filename", test_data["article_images"][1]["filename"], test_data["article_images"][1]["filename"] in instructions),
        ("Image 2 position", "position: 2", "position: 2" in instructions or "paragraph: 2" in instructions or "paragraph 2" in instructions),
        ("Featured Image step", "Featured Image", "Featured Image" in instructions),
        ("Draft mode summary", "Save the article as a draft", "Save the article as a draft" in instructions),
        ("Draft mode note", "draft", "draft" in instructions.lower()),
        # FAQ Schema checks
        ("FAQ Schema summary step", "FAQ Schema JSON-LD", "FAQ Schema JSON-LD" in instructions),
        ("FAQ Schema step", "Insert FAQ Schema", "Insert FAQ Schema" in instructions),
        ("FAQ Schema info section", "FAQ Schema for AI Search Engines", "FAQ Schema for AI Search Engines" in instructions),
        ("FAQ 1 question preview", test_data["faqs"][0]["question"][:30], test_data["faqs"][0]["question"][:30] in instructions),
        ("FAQPage schema type", '"@type": "FAQPage"', '"@type": "FAQPage"' in instructions),
        ("Schema.org context", '"@context": "https://schema.org"', '"@context": "https://schema.org"' in instructions),
        ("Custom HTML block instruction", "Custom HTML", "Custom HTML" in instructions),
        ("JSON-LD script tag", 'application/ld+json', 'application/ld+json' in instructions),
    ]

    passed = 0
    failed = 0
    for name, expected, found in checks:
        status = "✅" if found else "❌"
        if found:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {name}")
        if not found:
            print(f"      Expected to find: '{expected[:50]}...'")

    print("\n" + "=" * 80)
    print(f"\n📊 Summary: {passed}/{len(checks)} checks passed")

    if failed > 0:
        print(f"\n❌ {failed} checks FAILED")
    else:
        print("\n✅ All checks PASSED!")

    # Save full instructions for review
    print("\n" + "=" * 80)
    print("\n📄 Generated Instructions Preview (first 2000 chars):\n")
    print(instructions[:2000])
    print("\n..." if len(instructions) > 2000 else "")

    # Save to file
    with open("scripts/generated_instructions.txt", "w", encoding="utf-8") as f:
        f.write(instructions)
    print(f"\n📁 Full instructions saved to: scripts/generated_instructions.txt")
    print(f"   Total length: {len(instructions)} characters")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
