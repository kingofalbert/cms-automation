#!/usr/bin/env python3
"""
大紀元健康文章爬蟲腳本 (本地版)

全量抓取大紀元健康分類的所有文章並存入 Supabase。

使用方法：
    # 抓取所有分類
    python scripts/scrape_health_articles.py

    # 只抓取健康養生分類，從第 1 頁開始
    python scripts/scrape_health_articles.py --category 0 --start-page 1

    # 繼續從第 50 頁抓取，每批 100 篇
    python scripts/scrape_health_articles.py --category 0 --start-page 50 --max-articles 100

    # 試運行模式（不寫入資料庫）
    python scripts/scrape_health_articles.py --dry-run --max-articles 10

@version 1.0
@date 2025-12-10
"""

import argparse
import asyncio
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from supabase import create_client, Client

# ============================================================
# Configuration
# ============================================================

HEALTH_CATEGORIES = [
    {"url": "/b5/nf2283.htm", "name": "健康養生", "max_pages": 410},
    {"url": "/b5/ncid248.htm", "name": "食療養生", "max_pages": 15},
    {"url": "/b5/ncid246.htm", "name": "健康生活", "max_pages": 15},
]

BASE_URL = "https://www.epochtimes.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# 穩定慢速模式
LIST_PAGE_DELAY = 1.5   # 列表頁間延遲（秒）
DETAIL_PAGE_DELAY = 2.0  # 詳情頁間延遲（秒）

# ============================================================
# Data Classes
# ============================================================


@dataclass
class ArticleInfo:
    url: str
    article_id: str
    title: str = ""
    author_line: Optional[str] = None
    body_html: str = ""
    excerpt: Optional[str] = None
    word_count: int = 0
    category: str = ""
    tags: list = field(default_factory=list)
    publish_date: Optional[str] = None
    images: list = field(default_factory=list)


@dataclass
class ImageInfo:
    position: int
    source_url: str
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    is_featured: bool = False


@dataclass
class ScrapeStats:
    processed: int = 0
    new: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list = field(default_factory=list)


# ============================================================
# Supabase Client
# ============================================================

def get_supabase_client() -> Client:
    """Create Supabase client from environment."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL", "https://twsbhjmlmspjwfystpti.supabase.co")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY not found in environment")

    return create_client(supabase_url, supabase_key)


# ============================================================
# HTTP Client
# ============================================================

def get_http_client() -> httpx.Client:
    """Create HTTP client with appropriate settings."""
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )


# ============================================================
# Scraping Functions
# ============================================================

def scrape_list_page(client: httpx.Client, category_url: str, page: int) -> list[dict]:
    """Scrape a single list page and return article URLs."""
    if page == 1:
        url = f"{BASE_URL}{category_url}"
    else:
        url = f"{BASE_URL}{category_url.replace('.htm', '')}_{page}.htm"

    print(f"  Fetching list page {page}: {url}")

    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"  ⚠️ Error fetching page {page}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    # Find all article links
    for link in soup.select('a[href*="/b5/"][href$=".htm"]'):
        href = link.get("href", "")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)

        # Extract article ID
        match = re.search(r"/(n\d+)\.htm", full_url)
        if not match:
            continue

        article_id = match.group(1)

        # Avoid duplicates in current batch
        if not any(a["article_id"] == article_id for a in articles):
            articles.append({"url": full_url, "article_id": article_id})

    return articles


def scrape_article_detail(client: httpx.Client, url: str, category: str) -> Optional[ArticleInfo]:
    """Scrape a single article detail page."""
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        print(f"    ⚠️ Error fetching article: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract article ID
    match = re.search(r"/(n\d+)\.htm", url)
    if not match:
        return None
    article_id = match.group(1)

    # Extract title
    title_el = soup.select_one("h1.title, h1, .post_title, article h1")
    title = title_el.get_text(strip=True) if title_el else ""
    if not title:
        print(f"    ⚠️ No title found for {article_id}")
        return None

    # Extract author
    author_el = soup.select_one(".author, .post_author, .writer, [class*='author']")
    author_line = author_el.get_text(strip=True) if author_el else None

    # Extract publish date
    date_el = soup.select_one("time, .date, .post_date, [class*='time']")
    date_text = ""
    if date_el:
        date_text = date_el.get("datetime", "") or date_el.get_text(strip=True)
    publish_date = parse_date(date_text)

    # Extract tags
    tags = []
    for tag_el in soup.select(".tags a, .post_tag a, [class*='tag'] a"):
        tag = tag_el.get_text(strip=True)
        if tag and tag not in tags:
            tags.append(tag)

    # Extract body HTML
    content_el = soup.select_one(
        ".post_content, .article_content, article .content, .entry-content, [class*='article-body']"
    )

    body_html = ""
    excerpt = None
    images = []

    if content_el:
        # Remove unwanted elements
        for unwanted in content_el.select(
            "script, style, iframe, noscript, .ad, .advertisement, .social-share, .related-posts, .comments, nav"
        ):
            unwanted.decompose()

        # Extract images
        for idx, img in enumerate(content_el.select("img")):
            src = img.get("src") or img.get("data-src", "")
            if src and not src.startswith("data:"):
                full_src = urljoin(BASE_URL, src)
                figcaption = None
                figure = img.find_parent("figure")
                if figure:
                    cap_el = figure.select_one("figcaption")
                    if cap_el:
                        figcaption = cap_el.get_text(strip=True)

                images.append(
                    ImageInfo(
                        position=idx,
                        source_url=full_src,
                        caption=figcaption,
                        alt_text=img.get("alt"),
                        is_featured=(idx == 0),
                    )
                )

        # Get clean HTML
        body_html = clean_html(str(content_el))

        # Extract excerpt
        first_p = content_el.select_one("p")
        if first_p:
            excerpt = first_p.get_text(strip=True)[:300]

    # Calculate word count
    plain_text = re.sub(r"<[^>]+>", "", body_html)
    word_count = count_words(plain_text)

    return ArticleInfo(
        url=url,
        article_id=article_id,
        title=title,
        author_line=author_line,
        body_html=body_html,
        excerpt=excerpt,
        word_count=word_count,
        category=category,
        tags=tags,
        publish_date=publish_date,
        images=images,
    )


# ============================================================
# Helper Functions
# ============================================================

def parse_date(date_text: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD."""
    if not date_text:
        return None

    # ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}", date_text):
        return date_text[:10]

    # Chinese format: 2024年12月7日
    cn_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})", date_text)
    if cn_match:
        year, month, day = cn_match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Slash format: 2024/12/7
    slash_match = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", date_text)
    if slash_match:
        year, month, day = slash_match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return None


def clean_html(html: str) -> str:
    """Clean HTML content."""
    # Remove inline styles
    html = re.sub(r'\s*style="[^"]*"', "", html, flags=re.IGNORECASE)
    # Remove empty tags
    html = re.sub(r"<(\w+)[^>]*>\s*</\1>", "", html, flags=re.IGNORECASE)
    # Normalize whitespace
    html = re.sub(r"\s+", " ", html).strip()
    return html


def count_words(text: str) -> int:
    """Count Chinese characters and English words."""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    return chinese_chars + english_words


# ============================================================
# Database Operations
# ============================================================

def check_article_exists(supabase: Client, article_id: str) -> bool:
    """Check if article already exists in database."""
    result = (
        supabase.table("health_articles")
        .select("id")
        .eq("article_id", article_id)
        .execute()
    )
    return len(result.data) > 0


def save_article(supabase: Client, article: ArticleInfo) -> bool:
    """Save article to database."""
    try:
        # Insert article
        supabase.table("health_articles").insert(
            {
                "original_url": article.url,
                "article_id": article.article_id,
                "title": article.title,
                "author_line": article.author_line,
                "body_html": article.body_html,
                "excerpt": article.excerpt,
                "word_count": article.word_count,
                "category": article.category,
                "original_tags": article.tags,
                "publish_date": article.publish_date,
                "status": "scraped",
            }
        ).execute()

        # Insert images
        if article.images:
            image_records = [
                {
                    "article_id": article.article_id,
                    "position": img.position,
                    "source_url": img.source_url,
                    "caption": img.caption,
                    "alt_text": img.alt_text,
                    "is_featured": img.is_featured,
                }
                for img in article.images
            ]
            supabase.table("health_article_images").insert(image_records).execute()

        return True
    except Exception as e:
        print(f"    ⚠️ Database error: {e}")
        return False


def get_current_count(supabase: Client) -> int:
    """Get current article count."""
    result = (
        supabase.table("health_articles")
        .select("id", count="exact")
        .execute()
    )
    return result.count or 0


# ============================================================
# Main Scraping Logic
# ============================================================

def run_scrape(
    category_index: Optional[int] = None,
    start_page: int = 1,
    max_pages: int = 500,
    max_articles: int = 100,
    dry_run: bool = False,
) -> ScrapeStats:
    """Run the scraping process."""
    stats = ScrapeStats()

    # Initialize clients
    http_client = get_http_client()
    supabase = None if dry_run else get_supabase_client()

    # Determine categories to process
    if category_index is not None:
        categories = [HEALTH_CATEGORIES[category_index]]
    else:
        categories = HEALTH_CATEGORIES

    print(f"\n{'='*60}")
    print(f"大紀元健康文章爬蟲")
    print(f"{'='*60}")
    print(f"模式: {'試運行' if dry_run else '正式運行'}")
    print(f"起始頁: {start_page}")
    print(f"最大頁數: {max_pages}")
    print(f"最大文章數: {max_articles}")
    print(f"分類: {', '.join(c['name'] for c in categories)}")

    if not dry_run:
        current_count = get_current_count(supabase)
        print(f"資料庫現有文章: {current_count}")

    print(f"{'='*60}\n")

    try:
        for category in categories:
            if stats.new >= max_articles:
                print(f"\n已達到最大文章數限制 ({max_articles})，停止")
                break

            print(f"\n📂 處理分類: {category['name']}")
            print(f"   URL: {category['url']}")

            category_max = min(max_pages, category.get("max_pages", max_pages))
            end_page = start_page + category_max - 1

            # Phase 1: Collect article URLs
            # 計算需要收集的 URL 數量（多收集 50% 以應對重複）
            urls_needed = int(max_articles * 1.5)
            print(f"\n   Phase 1: 收集文章 URL (目標: {urls_needed} 個)")
            all_articles = []

            for page in range(start_page, end_page + 1):
                # 如果已收集足夠 URL，提前停止
                if len(all_articles) >= urls_needed:
                    print(f"  ✓ 已收集足夠 URL ({len(all_articles)} 個)，進入 Phase 2")
                    break

                articles = scrape_list_page(http_client, category["url"], page)
                if not articles:
                    print(f"  ⚠️ 頁 {page} 無文章，停止此分類")
                    break

                all_articles.extend(articles)
                print(f"  頁 {page}: 收集到 {len(articles)} 篇 (總計: {len(all_articles)})")
                time.sleep(LIST_PAGE_DELAY)

            print(f"\n   共收集 {len(all_articles)} 篇文章 URL")

            # Phase 2: Scrape each article
            print(f"\n   Phase 2: 抓取文章詳情")

            for idx, article_info in enumerate(all_articles, 1):
                if stats.new >= max_articles:
                    print(f"\n   已達到最大文章數限制 ({max_articles})，停止")
                    break

                stats.processed += 1
                article_id = article_info["article_id"]

                print(f"\n   [{idx}/{len(all_articles)}] {article_id}")

                # Check if exists
                if not dry_run and check_article_exists(supabase, article_id):
                    print(f"    ⏭️ 已存在，跳過")
                    stats.skipped += 1
                    continue

                # Scrape detail
                article = scrape_article_detail(
                    http_client, article_info["url"], category["name"]
                )

                if not article:
                    stats.failed += 1
                    stats.errors.append(f"Parse failed: {article_id}")
                    continue

                print(f"    📄 {article.title[:40]}...")
                print(f"    字數: {article.word_count}, 圖片: {len(article.images)}")

                # Save to database
                if not dry_run:
                    if save_article(supabase, article):
                        stats.new += 1
                        print(f"    ✅ 已儲存")
                    else:
                        stats.failed += 1
                        stats.errors.append(f"Save failed: {article_id}")
                else:
                    stats.new += 1
                    print(f"    🔍 [試運行] 會儲存")

                time.sleep(DETAIL_PAGE_DELAY)

    except KeyboardInterrupt:
        print("\n\n⚠️ 使用者中斷")
    finally:
        http_client.close()

    # Print summary
    print(f"\n{'='*60}")
    print(f"抓取完成！")
    print(f"{'='*60}")
    print(f"處理: {stats.processed}")
    print(f"新增: {stats.new}")
    print(f"跳過: {stats.skipped}")
    print(f"失敗: {stats.failed}")

    if stats.errors:
        print(f"\n錯誤列表 (前 10 個):")
        for err in stats.errors[:10]:
            print(f"  - {err}")

    if not dry_run and supabase:
        final_count = get_current_count(supabase)
        print(f"\n資料庫最終文章數: {final_count}")

    return stats


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="大紀元健康文章爬蟲",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
    # 抓取所有分類（從第 1 頁開始，最多 100 篇）
    python scripts/scrape_health_articles.py

    # 只抓取健康養生分類，從第 50 頁開始
    python scripts/scrape_health_articles.py --category 0 --start-page 50

    # 試運行模式
    python scripts/scrape_health_articles.py --dry-run --max-articles 5

分類索引:
    0 = 健康養生 (~4000 篇)
    1 = 食療養生 (~150 篇)
    2 = 健康生活 (~150 篇)
        """,
    )

    parser.add_argument(
        "--category", "-c",
        type=int,
        choices=[0, 1, 2],
        help="分類索引 (0=健康養生, 1=食療養生, 2=健康生活)",
    )
    parser.add_argument(
        "--start-page", "-s",
        type=int,
        default=1,
        help="起始頁碼 (預設: 1)",
    )
    parser.add_argument(
        "--max-pages", "-p",
        type=int,
        default=500,
        help="最大頁數 (預設: 500)",
    )
    parser.add_argument(
        "--max-articles", "-n",
        type=int,
        default=100,
        help="每次運行最多抓取的文章數 (預設: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="試運行模式，不寫入資料庫",
    )

    args = parser.parse_args()

    stats = run_scrape(
        category_index=args.category,
        start_page=args.start_page,
        max_pages=args.max_pages,
        max_articles=args.max_articles,
        dry_run=args.dry_run,
    )

    # Exit with error code if any failures
    sys.exit(1 if stats.failed > 0 else 0)


if __name__ == "__main__":
    main()
