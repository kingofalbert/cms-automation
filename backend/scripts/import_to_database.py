#!/usr/bin/env python3
"""
從本地 JSON 文件批量導入文章到 Supabase 數據庫

這個腳本讀取 scrape_all_to_local.py 生成的 JSONL 文件，
批量導入到 Supabase 數據庫。

使用方式：
    python scripts/import_to_database.py [--batch-size 100]

輸入目錄：
    data/scraped_articles/*.jsonl
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"logs/import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)

# 配置
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "scraped_articles"

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def get_supabase_client():
    """創建 Supabase 客戶端"""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def load_existing_ids(supabase) -> set:
    """載入數據庫中已存在的文章 ID"""
    logger.info("載入已存在的文章 ID...")
    existing_ids = set()

    # 分批查詢
    offset = 0
    batch_size = 1000

    while True:
        response = supabase.table("health_articles") \
            .select("article_id") \
            .range(offset, offset + batch_size - 1) \
            .execute()

        if not response.data:
            break

        for row in response.data:
            existing_ids.add(row["article_id"])

        offset += batch_size

        if len(response.data) < batch_size:
            break

    logger.info(f"數據庫中已有 {len(existing_ids)} 篇文章")
    return existing_ids


def read_jsonl_file(file_path: Path) -> List[Dict]:
    """讀取 JSONL 文件"""
    articles = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                article = json.loads(line.strip())
                articles.append(article)
            except json.JSONDecodeError:
                continue
    return articles


def prepare_article_for_db(article: Dict) -> Dict:
    """準備文章數據以符合數據庫結構"""
    return {
        "article_id": article.get("article_id"),
        "original_url": article.get("url"),
        "title": article.get("title"),
        "author_line": article.get("author"),  # 數據庫用 author_line
        "publish_date": article.get("published_date"),  # 數據庫用 publish_date
        "excerpt": article.get("summary"),  # 數據庫用 excerpt
        "body_html": article.get("body_html"),
        "category": article.get("category"),
        "status": "scraped",  # 初始狀態為 scraped
        "scraped_at": datetime.now().isoformat(),
    }


def import_batch(supabase, articles: List[Dict]) -> tuple:
    """批量導入文章"""
    success = 0
    failed = 0

    for article in articles:
        try:
            db_article = prepare_article_for_db(article)
            supabase.table("health_articles").upsert(
                db_article,
                on_conflict="article_id"
            ).execute()
            success += 1
        except Exception as e:
            logger.error(f"導入失敗 {article.get('article_id')}: {e}")
            failed += 1

    return success, failed


def import_from_files(supabase, batch_size: int = 100):
    """從所有 JSONL 文件導入"""
    # 載入已存在的 ID
    existing_ids = load_existing_ids(supabase)

    # 找到所有 JSONL 文件
    jsonl_files = list(DATA_DIR.glob("articles_*.jsonl"))

    if not jsonl_files:
        logger.warning(f"在 {DATA_DIR} 中沒有找到 JSONL 文件")
        logger.info("請先運行 scrape_all_to_local.py 抓取文章")
        return

    logger.info(f"找到 {len(jsonl_files)} 個 JSONL 文件")

    total_success = 0
    total_failed = 0
    total_skipped = 0

    for jsonl_file in jsonl_files:
        logger.info(f"\n處理文件: {jsonl_file.name}")

        articles = read_jsonl_file(jsonl_file)
        logger.info(f"  讀取到 {len(articles)} 篇文章")

        # 過濾已存在的文章
        new_articles = [a for a in articles if a.get("article_id") not in existing_ids]
        skipped = len(articles) - len(new_articles)
        total_skipped += skipped

        logger.info(f"  新文章: {len(new_articles)}, 跳過: {skipped}")

        if not new_articles:
            continue

        # 分批導入
        for i in range(0, len(new_articles), batch_size):
            batch = new_articles[i:i + batch_size]
            success, failed = import_batch(supabase, batch)
            total_success += success
            total_failed += failed

            # 更新已存在的 ID
            for article in batch:
                existing_ids.add(article.get("article_id"))

            logger.info(f"    批次 {i//batch_size + 1}: 成功 {success}, 失敗 {failed}")

    logger.info("\n" + "="*60)
    logger.info("導入完成!")
    logger.info(f"  成功: {total_success}")
    logger.info(f"  失敗: {total_failed}")
    logger.info(f"  跳過: {total_skipped}")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(description="從本地文件導入文章到數據庫")
    parser.add_argument("--batch-size", type=int, default=100, help="每批導入的文章數")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("請設置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 環境變數")
        sys.exit(1)

    logger.info("="*60)
    logger.info("文章導入工具")
    logger.info("="*60)
    logger.info(f"數據目錄: {DATA_DIR}")
    logger.info(f"批次大小: {args.batch_size}")

    supabase = get_supabase_client()
    import_from_files(supabase, args.batch_size)


if __name__ == "__main__":
    main()
