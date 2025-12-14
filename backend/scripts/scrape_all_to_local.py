#!/usr/bin/env python3
"""
完整抓取大紀元健康文章到本地文件

這個腳本會遍歷所有分類的所有頁面，將文章數據保存到本地 JSON 文件。
不做任何跳過邏輯，確保抓取完整。

使用方式：
    python scripts/scrape_all_to_local.py [--resume]

輸出目錄：
    data/scraped_articles/
        - articles_健康養生.jsonl
        - articles_食療養生.jsonl
        - articles_健康生活.jsonl
        - progress.json (斷點續傳用)
"""

import os
import sys
import json
import time
import logging
import argparse
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"logs/scrape_local_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)

# 配置
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "scraped_articles"
PROGRESS_FILE = DATA_DIR / "progress.json"

# 請求延遲（秒）
LIST_PAGE_DELAY = 1.0
DETAIL_PAGE_DELAY = 0.3

# 健康類別配置 - 新文章（2025年最新，優先抓取）
# 注意：nsc 開頭的 URL 是頻道首頁（展示熱門文章，分頁重複）
# nf 開頭的 URL 是存檔列表（真正的分頁列表）
HEALTH_CATEGORIES_NEW = [
    {
        "name": "健康養生",
        "url": "https://www.epochtimes.com/b5/nf2283",  # 4001篇健康養生文章
        "max_pages": 200,  # 約 4000 篇，每頁 20 篇 = 200 頁
    },
]

# 健康類別配置 - 舊存檔（完整抓取）
HEALTH_CATEGORIES_ARCHIVE = [
    {
        "name": "健康養生_完整",
        "url": "https://www.epochtimes.com/b5/nf2283",
        "max_pages": 500,  # 抓取更多頁
    },
]

# 默認使用新文章配置
HEALTH_CATEGORIES = HEALTH_CATEGORIES_NEW

# HTTP Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def ensure_dirs():
    """確保目錄存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_DIR / "logs").mkdir(parents=True, exist_ok=True)


def load_progress() -> Dict[str, Any]:
    """載入進度"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categories": {}, "total_articles": 0, "last_update": None}


def save_progress(progress: Dict[str, Any]):
    """保存進度"""
    progress["last_update"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def extract_article_id(url: str) -> Optional[str]:
    """從 URL 提取文章 ID"""
    match = re.search(r"/(\d+/\d+/\d+/)?(n\d+)\.htm", url)
    if match:
        return match.group(2)
    return None


def parse_date(date_str: str) -> Optional[str]:
    """解析日期字符串"""
    if not date_str:
        return None

    # 清理字符串
    date_str = date_str.strip()

    # 嘗試多種格式
    formats = [
        "%Y年%m月%d日",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m月%d日, %Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # 嘗試提取年月日
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return None


def scrape_list_page(client: httpx.Client, base_url: str, page: int) -> List[Dict]:
    """抓取列表頁面"""
    url = f"{base_url}_{page}.htm" if page > 1 else f"{base_url}.htm"

    try:
        response = client.get(url, timeout=30.0)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        # 查找文章鏈接
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/n" in href and href.endswith(".htm"):
                article_id = extract_article_id(href)
                if article_id:
                    # 構建完整 URL
                    if href.startswith("http"):
                        full_url = href
                    elif href.startswith("/"):
                        full_url = f"https://www.epochtimes.com{href}"
                    else:
                        full_url = f"https://www.epochtimes.com/{href}"

                    # 獲取標題（列表頁可能沒有文字標題，所以只要有 URL 就加入）
                    title = link.get_text(strip=True) or ""
                    # 嘗試從 img alt 或 title 屬性獲取標題
                    if not title:
                        img = link.find("img")
                        if img:
                            title = img.get("alt", "") or img.get("title", "")

                    # 只要有有效的 article_id 就加入列表
                    articles.append({
                        "article_id": article_id,
                        "url": full_url,
                        "title": title,  # 可能為空，詳情頁會獲取真正標題
                    })

        # 去重
        seen = set()
        unique_articles = []
        for article in articles:
            if article["article_id"] not in seen:
                seen.add(article["article_id"])
                unique_articles.append(article)

        return unique_articles

    except Exception as e:
        logger.error(f"抓取列表頁失敗 {url}: {e}")
        return []


def scrape_article_detail(client: httpx.Client, url: str, category: str) -> Optional[Dict]:
    """抓取文章詳情"""
    try:
        response = client.get(url, timeout=30.0)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 提取標題（兼容新舊頁面結構）
        title_elem = (
            soup.find("h1", class_="title") or  # 舊頁面
            soup.find("h1", class_="articleTitle") or  # 新頁面
            soup.find("h1")  # 通用
        )
        title = title_elem.get_text(strip=True) if title_elem else None

        # 提取日期（兼容新舊頁面結構）
        date_elem = (
            soup.find("span", class_="date") or
            soup.find("time") or
            soup.find("span", class_="publishedTime")
        )
        published_date = None
        if date_elem:
            published_date = parse_date(date_elem.get_text(strip=True))

        # 提取作者（兼容新舊頁面結構）
        author_elem = (
            soup.find("span", class_="author") or
            soup.find("a", class_="author") or
            soup.find("span", class_="authorName")
        )
        author = author_elem.get_text(strip=True) if author_elem else None

        # 提取正文
        content_elem = soup.find("div", class_="post_content") or soup.find("article")
        body = ""
        body_html = ""
        if content_elem:
            body_html = str(content_elem)
            body = content_elem.get_text(separator="\n", strip=True)

        # 提取摘要
        summary_elem = soup.find("div", class_="excerpt") or soup.find("meta", {"name": "description"})
        summary = None
        if summary_elem:
            if summary_elem.name == "meta":
                summary = summary_elem.get("content", "")
            else:
                summary = summary_elem.get_text(strip=True)

        # 提取圖片
        images = []
        if content_elem:
            for img in content_elem.find_all("img", src=True):
                img_url = img.get("src", "")
                if img_url and not img_url.startswith("data:"):
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        img_url = "https://www.epochtimes.com" + img_url
                    images.append(img_url)

        article_id = extract_article_id(url)

        return {
            "article_id": article_id,
            "url": url,
            "title": title,
            "author": author,
            "published_date": published_date,
            "summary": summary,
            "body": body,
            "body_html": body_html,
            "images": images,
            "category": category,
            "source": "epochtimes",
            "scraped_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"抓取文章詳情失敗 {url}: {e}")
        return None


def scrape_category(
    client: httpx.Client,
    category: Dict,
    progress: Dict,
    resume: bool = False
) -> int:
    """抓取單個分類的所有文章"""
    cat_name = category["name"]
    cat_url = category["url"]
    max_pages = category["max_pages"]

    # 輸出文件
    output_file = DATA_DIR / f"articles_{cat_name}.jsonl"

    # 載入已有的文章 ID（用於去重）
    existing_ids = set()
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    article = json.loads(line)
                    existing_ids.add(article.get("article_id"))
                except:
                    pass

    # 確定起始頁
    start_page = 1
    if resume and cat_name in progress.get("categories", {}):
        start_page = progress["categories"][cat_name].get("last_page", 1) + 1
        logger.info(f"從第 {start_page} 頁繼續抓取 {cat_name}")

    logger.info(f"\n{'='*60}")
    logger.info(f"開始抓取分類: {cat_name}")
    logger.info(f"URL: {cat_url}")
    logger.info(f"頁數範圍: {start_page} - {max_pages}")
    logger.info(f"已有文章數: {len(existing_ids)}")
    logger.info(f"{'='*60}")

    total_new = 0
    total_skipped = 0
    consecutive_empty = 0
    max_consecutive_empty = 20  # 連續 20 頁無內容才停止（比之前寬鬆）

    with open(output_file, "a", encoding="utf-8") as f:
        for page in range(start_page, max_pages + 1):
            # 抓取列表頁
            articles = scrape_list_page(client, cat_url, page)

            if not articles:
                consecutive_empty += 1
                logger.warning(f"  頁 {page}: 無文章內容")
                if consecutive_empty >= max_consecutive_empty:
                    logger.info(f"  連續 {max_consecutive_empty} 頁無內容，結束此分類")
                    break
                time.sleep(LIST_PAGE_DELAY)
                continue

            consecutive_empty = 0
            page_new = 0
            page_skipped = 0

            # 抓取每篇文章詳情
            for article_info in articles:
                article_id = article_info["article_id"]

                # 檢查是否已存在
                if article_id in existing_ids:
                    page_skipped += 1
                    total_skipped += 1
                    continue

                # 抓取詳情
                article = scrape_article_detail(client, article_info["url"], cat_name)

                if article:
                    # 寫入文件
                    f.write(json.dumps(article, ensure_ascii=False) + "\n")
                    f.flush()  # 立即寫入磁碟

                    existing_ids.add(article_id)
                    page_new += 1
                    total_new += 1

                time.sleep(DETAIL_PAGE_DELAY)

            logger.info(f"  頁 {page}: 新增 {page_new}, 跳過 {page_skipped}, 累計新增 {total_new}")

            # 更新進度
            progress["categories"][cat_name] = {
                "last_page": page,
                "total_new": total_new,
                "total_skipped": total_skipped,
            }
            save_progress(progress)

            time.sleep(LIST_PAGE_DELAY)

    logger.info(f"\n分類 {cat_name} 完成: 新增 {total_new} 篇, 跳過 {total_skipped} 篇")
    return total_new


def main():
    parser = argparse.ArgumentParser(description="完整抓取大紀元健康文章到本地")
    parser.add_argument("--resume", action="store_true", help="從斷點繼續")
    parser.add_argument("--category", type=str, help="只抓取指定分類")
    parser.add_argument("--archive", action="store_true", help="抓取舊存檔文章（2001-2017年）")
    parser.add_argument("--all", action="store_true", help="抓取所有文章（新+舊）")
    args = parser.parse_args()

    ensure_dirs()

    logger.info("="*60)
    logger.info("大紀元健康文章完整抓取工具")
    logger.info("="*60)
    logger.info(f"輸出目錄: {DATA_DIR}")
    logger.info(f"斷點續傳: {'是' if args.resume else '否'}")

    # 載入進度
    progress = load_progress() if args.resume else {"categories": {}, "total_articles": 0}

    # 選擇分類配置
    if args.all:
        categories = HEALTH_CATEGORIES_NEW + HEALTH_CATEGORIES_ARCHIVE
        logger.info("模式: 抓取所有文章（新+舊）")
    elif args.archive:
        categories = HEALTH_CATEGORIES_ARCHIVE
        logger.info("模式: 抓取舊存檔文章（2001-2017年）")
    else:
        categories = HEALTH_CATEGORIES_NEW
        logger.info("模式: 抓取最新文章（2025年）")

    # 過濾分類
    if args.category:
        categories = [c for c in categories if c["name"] == args.category]
        if not categories:
            logger.error(f"找不到分類: {args.category}")
            sys.exit(1)

    # 創建 HTTP 客戶端
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        total_new = 0

        for category in categories:
            new_count = scrape_category(client, category, progress, args.resume)
            total_new += new_count

        progress["total_articles"] = total_new
        save_progress(progress)

    logger.info("\n" + "="*60)
    logger.info("抓取完成!")
    logger.info(f"總共新增: {total_new} 篇文章")
    logger.info(f"數據保存在: {DATA_DIR}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
