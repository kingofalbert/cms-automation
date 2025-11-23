#!/usr/bin/env python3
"""Debug script to test article parsing with actual data from production."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from src.services.parser.article_parser import ArticleParserService

# Sample content from worklist item #1
raw_html = """.lst-kix_29dyt0p4hu7d-3 > li:before{content:"\u25cf  "}.lst-kix_29dyt0p4hu7d-1 > li:before{content:"\u25cb  "}.lst-kix_29dyt0p4hu7d-0 > li:before{content:"\u25cf  "}.lst-kix_29dyt0p4hu7d-4 > li:before{content:"\u25cb  "}.lst-kix_29dyt0p4hu7d-2 > li:before{content:"\u25a0  "}ul.lst-kix_29dyt0p4hu7d-1{list-style-type:none}ul.lst-kix_29dyt0p4hu7d-2{list-style-type:none}ul.lst-kix_29dyt0p4hu7d-0{list-style-type:none}.lst-kix_29dyt0p4hu7d-8 > li:before{content:"\u25a0  "}ul.lst-kix_29dyt0p4hu7d-5{list-style-type:none}ul.lst-kix_29dyt0p4hu7d-6{list-style-type:none}ul.lst-kix_29dyt0p4hu7d-3{list-style-type:none}ul.lst-kix_29dyt0p4hu7d-4{list-style-type:none}.lst-kix_29dyt0p4hu7d-5 > li:before{content:"\u25a0  "}.lst-kix_29dyt0p4hu7d-7 > li:before{content:"\u25cb  "}ul.lst-kix_29dyt0p4hu7d-7{list-style-type:none}.lst-kix_29dyt0p4hu7d-6 > li:before{content:"\u25cf  "}ul.lst-kix_29dyt0p4hu7d-8{list-style-type:none}
# 感覺生活一團亂麻？從微小行動開始開啟新人生

文 / Leo Babauta 編譯 / 黃襄

圖說：別小看吃一顆蘋果或走五分鐘路，這些小事也是人生升級包。（Chay_Tee/Shutterstock）

[https://www.theepochtimes.com/_next/image?url=https%3A%2F%2Fimg.theepochtimes.com%2Fassets%2Fuploads%2F2025%2F08%2F20%2Fid5903569-casual-walk-1080x720.jpg&w=1200&q=100](https://www.google.com/url?q=https://www.theepochtimes.com/_next/image?url%3Dhttps%253A%252F%252Fimg.theepochtimes.com%252Fassets%252Fuploads%252F2025%252F08%252F20%252Fid5903569-casual-walk-1080x720.jpg%26w%3D1200%26q%3D100&sa=D&source=editors&ust=1763332204647434&usg=AOvVaw2AVnvrLqwYgX7XpYk4ro9N)

### Meta 摘要

生活混亂想重置？知名部落客 Leo Babauta 分享，從設定簡單願景開始，每天執行一個「微小行動」，如散步五分鐘或整理兩件物品，就能逐步養成新習慣，輕鬆翻轉你的人生。"""

print("="*80)
print("Testing Article Parser with Actual Data")
print("="*80)

# Test heuristic parsing (no AI)
parser = ArticleParserService(use_ai=False)

print("\n1. Testing heuristic parsing...")
result = parser.parse_document(raw_html)

if result.success:
    article = result.parsed_article
    print(f"\n✅ Parsing SUCCESS")
    print(f"   Title Main: {article.title_main}")
    print(f"   Author Line: {article.author_line}")
    print(f"   Author Name: {article.author_name}")
    print(f"   Images: {len(article.images)}")
    print(f"   Parsing Method: {article.parsing_method}")
else:
    print(f"\n❌ Parsing FAILED")
    for error in result.errors:
        print(f"   Error: {error.error_message}")

# Test regex pattern directly
print("\n" + "="*80)
print("2. Testing Author Regex Pattern Directly")
print("="*80)

import re

test_text = "文 / Leo Babauta 編譯 / 黃襄"
pattern = r"文[／/]([^｜|\n]+)"

match = re.search(pattern, test_text)
if match:
    author_raw = match.group(1).strip()
    # Clean up (split by ｜ or |)
    author_name = re.split(r"[｜|]", author_raw)[0].strip()
    print(f"✅ Regex MATCHED")
    print(f"   Raw match: '{author_raw}'")
    print(f"   Cleaned name: '{author_name}'")
else:
    print(f"❌ Regex DID NOT MATCH")
    print(f"   Test text: '{test_text}'")
    print(f"   Pattern: {pattern}")
