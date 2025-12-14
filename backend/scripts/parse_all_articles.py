#!/usr/bin/env python3
"""
批量解析所有待解析的文章

這個腳本調用 Supabase Edge Function 來解析所有 status='scraped' 的文章。
包含重試機制和斷點續傳功能。

使用方式：
    python scripts/parse_all_articles.py [--batch-size 20] [--max-retries 3]
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any

import httpx
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
            f"logs/parse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# 重試配置
DEFAULT_BATCH_SIZE = 20
DEFAULT_MAX_RETRIES = 3
RETRY_DELAY = 10  # 秒
BATCH_DELAY = 2  # 批次間延遲（秒）
REQUEST_TIMEOUT = 180  # 秒


def get_pending_count() -> int:
    """獲取待解析的文章數量"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/health_articles",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Prefer": "count=exact",
                },
                params={
                    "select": "count",
                    "status": "eq.scraped",
                },
            )
            # 從 Content-Range header 獲取計數
            content_range = response.headers.get("content-range", "")
            if "/" in content_range:
                return int(content_range.split("/")[1])
    except Exception as e:
        logger.error(f"獲取待解析數量失敗: {e}")
    return 0


def call_parse_api(batch_size: int, max_retries: int) -> Dict[str, Any]:
    """調用 parse-articles Edge Function（含重試機制）"""
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.post(
                    f"{SUPABASE_URL}/functions/v1/parse-articles",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"batchSize": batch_size},
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.warning(f"請求超時 (嘗試 {attempt + 1}/{max_retries})")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP 錯誤 {e.response.status_code} (嘗試 {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.warning(f"調用失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")

        if attempt < max_retries - 1:
            logger.info(f"等待 {RETRY_DELAY} 秒後重試...")
            time.sleep(RETRY_DELAY)

    logger.error(f"重試 {max_retries} 次後仍失敗")
    return {"processed": 0, "failed": 1, "error": "Max retries exceeded"}


def run_parse_phase(batch_size: int, max_retries: int):
    """運行解析階段"""
    logger.info("="*60)
    logger.info("開始批量解析文章")
    logger.info("="*60)

    # 獲取初始待解析數量
    initial_pending = get_pending_count()
    logger.info(f"待解析文章數: {initial_pending}")

    if initial_pending == 0:
        logger.info("沒有待解析的文章")
        return

    total_processed = 0
    total_failed = 0
    total_tokens = 0
    batch_num = 0
    consecutive_failures = 0
    max_consecutive_failures = 5

    while True:
        batch_num += 1

        # 調用解析 API
        result = call_parse_api(batch_size, max_retries)

        processed = result.get("processed", 0)
        failed = result.get("failed", 0)
        tokens = result.get("total_tokens", 0)
        error = result.get("error")

        total_processed += processed
        total_failed += failed
        total_tokens += tokens

        # 計算剩餘
        remaining = get_pending_count()

        logger.info(
            f"  批次 {batch_num}: 解析 {processed} 篇, "
            f"失敗 {failed}, tokens: {tokens}, 剩餘: {remaining}"
        )

        # 檢查是否完成
        if processed == 0:
            if error:
                consecutive_failures += 1
                logger.warning(f"  錯誤: {error}")
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"連續失敗 {max_consecutive_failures} 次，停止解析")
                    break
                logger.info(f"等待 30 秒後重試...")
                time.sleep(30)
                continue
            else:
                logger.info("所有文章已解析完成")
                break
        else:
            consecutive_failures = 0

        # 批次間延遲
        time.sleep(BATCH_DELAY)

    # 最終報告
    logger.info("\n" + "="*60)
    logger.info("解析階段完成!")
    logger.info(f"  總共解析: {total_processed} 篇")
    logger.info(f"  總共失敗: {total_failed} 篇")
    logger.info(f"  總 tokens: {total_tokens}")
    logger.info(f"  剩餘待解析: {get_pending_count()} 篇")
    logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(description="批量解析所有待解析的文章")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="每批解析的文章數")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="最大重試次數")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("請設置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 環境變數")
        sys.exit(1)

    logger.info(f"批次大小: {args.batch_size}")
    logger.info(f"最大重試: {args.max_retries}")

    run_parse_phase(args.batch_size, args.max_retries)


if __name__ == "__main__":
    main()
