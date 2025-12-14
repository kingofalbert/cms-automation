#!/usr/bin/env python3
"""
大紀元健康文章全自動處理 Pipeline

這個腳本會自動完成：
1. 抓取所有健康類文章（約 15,000+ 篇）
2. AI 解析（關鍵詞、標題分解、分類）
3. 向量化（生成嵌入向量）

使用方式：
    python scripts/full_health_articles_pipeline.py

可選參數：
    --batch-size: 每批抓取文章數（默認 100）
    --parse-batch: AI 解析批次大小（默認 20）
    --embed-batch: 向量化批次大小（默認 50）
    --start-page: 起始頁碼（默認 1）
    --max-articles: 最大文章數（默認 0 表示無限制）
    --category: 分類索引（0=健康養生, 1=食療養生, 2=健康生活, 默認處理全部）
    --dry-run: 試運行模式，不實際儲存
"""

import os
import sys
import time
import argparse
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============== 配置 ==============

BASE_URL = "https://www.epochtimes.com"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# 健康分類
HEALTH_CATEGORIES = [
    {"url": "/b5/nf2283.htm", "name": "健康養生", "max_pages": 410},
    {"url": "/b5/ncid248.htm", "name": "食療養生", "max_pages": 15},
    {"url": "/b5/ncid246.htm", "name": "健康生活", "max_pages": 15},
]

# 延遲設定（秒）
LIST_PAGE_DELAY = 1.0
DETAIL_PAGE_DELAY = 1.5
PARSE_DELAY = 0.5
EMBED_DELAY = 0.3

# 重試設定
MAX_RETRIES = 3
RETRY_DELAY = 10  # 秒

# ============== 資料結構 ==============

@dataclass
class PipelineStats:
    """Pipeline 統計"""
    start_time: datetime = field(default_factory=datetime.now)

    # 抓取統計
    pages_scanned: int = 0
    urls_collected: int = 0
    articles_scraped: int = 0
    articles_skipped: int = 0
    scrape_errors: int = 0

    # 解析統計
    articles_parsed: int = 0
    parse_errors: int = 0
    tokens_used: int = 0

    # 向量化統計
    articles_embedded: int = 0
    embed_errors: int = 0

    def elapsed_time(self) -> str:
        """返回經過時間"""
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def summary(self) -> str:
        """返回統計摘要"""
        return f"""
============================================================
Pipeline 執行完成
============================================================
執行時間: {self.elapsed_time()}

📥 抓取階段:
   - 掃描頁數: {self.pages_scanned}
   - 收集 URL: {self.urls_collected}
   - 新增文章: {self.articles_scraped}
   - 跳過文章: {self.articles_skipped}
   - 錯誤數: {self.scrape_errors}

🔄 解析階段:
   - 已解析: {self.articles_parsed}
   - Token 使用: {self.tokens_used:,}
   - 錯誤數: {self.parse_errors}

✅ 向量化階段:
   - 已向量化: {self.articles_embedded}
   - 錯誤數: {self.embed_errors}
============================================================
"""


@dataclass
class ArticleData:
    """文章資料"""
    article_id: str
    url: str
    title: str
    author: str
    publish_date: str
    content: str
    word_count: int
    images: List[str]
    category: str
    source_category: str


# ============== HTTP 客戶端 ==============

def get_http_client() -> httpx.Client:
    """獲取 HTTP 客戶端"""
    return httpx.Client(
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
        timeout=30.0,
        follow_redirects=True,
    )


def get_supabase_client():
    """獲取 Supabase 客戶端"""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ============== 抓取函數 ==============

def scrape_list_page(client: httpx.Client, category_url: str, page: int) -> List[Dict]:
    """抓取列表頁"""
    if page == 1:
        url = f"{BASE_URL}{category_url}"
    else:
        base = category_url.rsplit(".", 1)[0]
        url = f"{BASE_URL}{base}_{page}.htm"

    try:
        response = client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []

        # 解析文章連結
        for link in soup.select("a[href*='/b5/'][href$='.htm']"):
            href = link.get("href", "")
            if "/b5/" in href and href.endswith(".htm"):
                # 提取文章 ID
                import re
                match = re.search(r"/(n\d+)\.htm", href)
                if match:
                    article_id = match.group(1)
                    full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    articles.append({
                        "article_id": article_id,
                        "url": full_url,
                    })

        # 去重
        seen = set()
        unique = []
        for a in articles:
            if a["article_id"] not in seen:
                seen.add(a["article_id"])
                unique.append(a)

        return unique

    except Exception as e:
        logger.error(f"抓取列表頁失敗: {url} - {e}")
        return []


def scrape_article_detail(client: httpx.Client, url: str, category: str) -> Optional[ArticleData]:
    """抓取文章詳情"""
    try:
        response = client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 提取標題
        title_elem = soup.select_one("h1.title") or soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 提取作者
        author_elem = soup.select_one(".author") or soup.select_one("[class*='author']")
        author = author_elem.get_text(strip=True) if author_elem else ""

        # 提取日期
        date_elem = soup.select_one(".post_date") or soup.select_one("time") or soup.select_one("[class*='date']")
        publish_date = date_elem.get_text(strip=True) if date_elem else ""

        # 提取內容
        content_elem = soup.select_one("div.post_content") or soup.select_one("article") or soup.select_one(".content")
        content = ""
        if content_elem:
            # 移除腳本和樣式
            for tag in content_elem.select("script, style, nav, footer"):
                tag.decompose()
            content = content_elem.get_text(separator="\n", strip=True)

        # 提取圖片
        images = []
        if content_elem:
            for img in content_elem.select("img[src]"):
                src = img.get("src", "")
                if src and not src.startswith("data:"):
                    images.append(src)

        # 提取文章 ID
        import re
        match = re.search(r"/(n\d+)\.htm", url)
        article_id = match.group(1) if match else ""

        if not title or not article_id:
            return None

        return ArticleData(
            article_id=article_id,
            url=url,
            title=title,
            author=author,
            publish_date=publish_date,
            content=content,
            word_count=len(content),
            images=images,
            category=category,
            source_category=category,
        )

    except Exception as e:
        logger.error(f"抓取文章詳情失敗: {url} - {e}")
        return None


def check_article_exists(supabase, article_id: str) -> bool:
    """檢查文章是否已存在"""
    try:
        result = supabase.table("health_articles").select("article_id").eq("article_id", article_id).limit(1).execute()
        return len(result.data) > 0
    except Exception:
        return False


def parse_publish_date(date_str: str) -> Optional[str]:
    """解析發布日期，返回 YYYY-MM-DD 格式或 None"""
    if not date_str:
        return None

    import re

    # 嘗試提取日期模式
    patterns = [
        # 2015-10-22
        r"(\d{4}-\d{2}-\d{2})",
        # 2015/10/22
        r"(\d{4}/\d{2}/\d{2})",
        # 2015年10月22日
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
    ]

    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            if len(match.groups()) == 1:
                # 直接是日期格式
                return match.group(1).replace("/", "-")
            elif len(match.groups()) == 3:
                # 年月日格式
                year, month, day = match.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"

    return None


def save_article(supabase, article: ArticleData) -> bool:
    """儲存文章到資料庫"""
    try:
        # 解析日期
        parsed_date = parse_publish_date(article.publish_date)

        # 使用與 health_articles 表匹配的欄位名稱
        data = {
            "article_id": article.article_id,
            "original_url": article.url,
            "title": article.title,
            "author_line": article.author,  # 原始作者行
            "body_html": article.content,  # 使用 body_html 欄位
            "word_count": article.word_count,
            "category": article.category,
            "primary_category": article.source_category,
            "status": "scraped",
            "scraped_at": datetime.now().isoformat(),
        }

        # 只有有效日期才加入
        if parsed_date:
            data["publish_date"] = parsed_date

        supabase.table("health_articles").upsert(data, on_conflict="article_id").execute()
        return True

    except Exception as e:
        logger.error(f"儲存文章失敗: {article.article_id} - {e}")
        return False


# ============== 解析函數 ==============

def call_parse_api(batch_size: int = 20) -> Dict[str, Any]:
    """調用 parse-articles Edge Function（含重試機制）"""
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=180.0) as client:  # 增加超時時間
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
        except Exception as e:
            logger.warning(f"調用 parse-articles 失敗 (嘗試 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"等待 {RETRY_DELAY} 秒後重試...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"parse-articles 重試 {MAX_RETRIES} 次後仍失敗")
                return {"processed": 0, "failed": 1, "error": str(e), "retry_exhausted": True}


def call_embed_api(batch_size: int = 50) -> Dict[str, Any]:
    """調用 generate-embeddings Edge Function（含重試機制）"""
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=180.0) as client:  # 增加超時時間
                response = client.post(
                    f"{SUPABASE_URL}/functions/v1/generate-embeddings",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"batchSize": batch_size},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"調用 generate-embeddings 失敗 (嘗試 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"等待 {RETRY_DELAY} 秒後重試...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"generate-embeddings 重試 {MAX_RETRIES} 次後仍失敗")
                return {"processed": 0, "failed": 1, "error": str(e), "retry_exhausted": True}


# ============== 主要 Pipeline ==============

def run_scrape_phase(
    stats: PipelineStats,
    http_client: httpx.Client,
    supabase,
    categories: List[Dict],
    start_page: int,
    batch_size: int,
    max_articles: int,
    dry_run: bool,
) -> None:
    """Phase 1: 抓取文章 - 持續處理所有頁面"""
    logger.info("=" * 60)
    logger.info("Phase 1: 抓取文章（持續模式）")
    logger.info("=" * 60)

    total_new = 0

    for cat_idx, category in enumerate(categories):
        if max_articles > 0 and total_new >= max_articles:
            break

        cat_name = category["name"]
        cat_url = category["url"]
        cat_max_pages = category.get("max_pages", 500)

        logger.info(f"\n📂 處理分類 [{cat_idx+1}/{len(categories)}]: {cat_name}")
        logger.info(f"   總頁數: {cat_max_pages}, 起始頁: {start_page}")

        # 持續處理所有頁面
        consecutive_empty_pages = 0  # 連續無新文章的頁數
        max_consecutive_empty = 10   # 連續 10 頁無新文章時跳過此分類

        for page in range(start_page, start_page + cat_max_pages):
            if max_articles > 0 and total_new >= max_articles:
                logger.info(f"  已達最大文章數限制 ({max_articles})")
                break

            # 獲取該頁的文章列表
            articles = scrape_list_page(http_client, cat_url, page)
            stats.pages_scanned += 1

            if not articles:
                logger.warning(f"  頁 {page} 無文章，停止此分類")
                break

            stats.urls_collected += len(articles)

            # 處理該頁的所有文章
            page_new = 0
            page_skipped = 0

            for article_info in articles:
                if max_articles > 0 and total_new >= max_articles:
                    break

                article_id = article_info["article_id"]

                # 檢查是否已存在
                if not dry_run and check_article_exists(supabase, article_id):
                    stats.articles_skipped += 1
                    page_skipped += 1
                    continue

                # 抓取詳情
                article = scrape_article_detail(http_client, article_info["url"], cat_name)

                if not article:
                    stats.scrape_errors += 1
                    continue

                # 儲存
                if not dry_run:
                    if save_article(supabase, article):
                        stats.articles_scraped += 1
                        total_new += 1
                        page_new += 1
                    else:
                        stats.scrape_errors += 1
                else:
                    stats.articles_scraped += 1
                    total_new += 1
                    page_new += 1

                time.sleep(DETAIL_PAGE_DELAY)

            # 每頁報告進度
            logger.info(f"  頁 {page}: 新增 {page_new}, 跳過 {page_skipped}, 總計新增 {total_new}")

            # 檢查是否連續無新文章
            if page_new == 0:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_consecutive_empty:
                    logger.info(f"  連續 {max_consecutive_empty} 頁無新文章，跳過此分類剩餘頁面")
                    break
            else:
                consecutive_empty_pages = 0

            time.sleep(LIST_PAGE_DELAY)

        logger.info(f"  分類 {cat_name} 完成: 總共新增 {total_new} 篇")


def run_parse_phase(stats: PipelineStats, parse_batch: int, dry_run: bool) -> None:
    """Phase 2: AI 解析"""
    logger.info("\n" + "=" * 60)
    logger.info("Phase 2: AI 解析")
    logger.info("=" * 60)

    if dry_run:
        logger.info("試運行模式，跳過解析")
        return

    batch_num = 0
    consecutive_failures = 0
    max_consecutive_failures = 5  # 連續失敗超過此數才停止

    while True:
        batch_num += 1
        result = call_parse_api(parse_batch)

        processed = result.get("processed", 0)
        failed = result.get("failed", 0)
        tokens = result.get("tokensUsed", 0)
        retry_exhausted = result.get("retry_exhausted", False)

        stats.articles_parsed += processed
        stats.parse_errors += failed
        stats.tokens_used += tokens

        if processed > 0:
            logger.info(f"  批次 {batch_num}: 解析 {processed} 篇, tokens: {tokens}")
            consecutive_failures = 0  # 重置連續失敗計數

        # 如果重試耗盡但仍有待處理文章，等待後重試
        if retry_exhausted:
            consecutive_failures += 1
            logger.warning(f"  連續失敗 {consecutive_failures}/{max_consecutive_failures}")
            if consecutive_failures >= max_consecutive_failures:
                logger.error("  連續失敗過多，停止解析階段")
                break
            logger.info(f"  等待 30 秒後重試...")
            time.sleep(30)
            continue

        if processed == 0 and not retry_exhausted:
            break

        time.sleep(PARSE_DELAY)

    logger.info(f"  解析完成: 共 {stats.articles_parsed} 篇")


def run_embed_phase(stats: PipelineStats, embed_batch: int, dry_run: bool) -> None:
    """Phase 3: 向量化"""
    logger.info("\n" + "=" * 60)
    logger.info("Phase 3: 向量化")
    logger.info("=" * 60)

    if dry_run:
        logger.info("試運行模式，跳過向量化")
        return

    batch_num = 0
    consecutive_failures = 0
    max_consecutive_failures = 5  # 連續失敗超過此數才停止

    while True:
        batch_num += 1
        result = call_embed_api(embed_batch)

        processed = result.get("processed", 0)
        failed = result.get("failed", 0)
        retry_exhausted = result.get("retry_exhausted", False)

        stats.articles_embedded += processed
        stats.embed_errors += failed

        if processed > 0:
            logger.info(f"  批次 {batch_num}: 向量化 {processed} 篇")
            consecutive_failures = 0  # 重置連續失敗計數

        # 如果重試耗盡但仍有待處理文章，等待後重試
        if retry_exhausted:
            consecutive_failures += 1
            logger.warning(f"  連續失敗 {consecutive_failures}/{max_consecutive_failures}")
            if consecutive_failures >= max_consecutive_failures:
                logger.error("  連續失敗過多，停止向量化階段")
                break
            logger.info(f"  等待 30 秒後重試...")
            time.sleep(30)
            continue

        if processed == 0 and not retry_exhausted:
            break

        time.sleep(EMBED_DELAY)

    logger.info(f"  向量化完成: 共 {stats.articles_embedded} 篇")


def run_full_pipeline(
    batch_size: int = 100,
    parse_batch: int = 20,
    embed_batch: int = 50,
    start_page: int = 1,
    max_articles: int = 0,
    category_index: Optional[int] = None,
    dry_run: bool = False,
) -> PipelineStats:
    """執行完整 Pipeline"""

    stats = PipelineStats()

    logger.info("=" * 60)
    logger.info("大紀元健康文章全自動處理 Pipeline")
    logger.info("=" * 60)
    logger.info(f"模式: {'試運行' if dry_run else '正式運行'}")
    logger.info(f"批次大小: 抓取={batch_size}, 解析={parse_batch}, 向量化={embed_batch}")
    logger.info(f"起始頁: {start_page}")
    logger.info(f"最大文章數: {max_articles if max_articles > 0 else '無限制'}")

    # 確定要處理的分類
    if category_index is not None:
        categories = [HEALTH_CATEGORIES[category_index]]
        logger.info(f"分類: {categories[0]['name']}")
    else:
        categories = HEALTH_CATEGORIES
        logger.info(f"分類: 全部 ({len(categories)} 個)")

    # 初始化客戶端
    http_client = get_http_client()
    supabase = None if dry_run else get_supabase_client()

    if not dry_run:
        # 顯示初始狀態
        result = supabase.table("health_articles").select("count", count="exact").execute()
        logger.info(f"資料庫現有文章: {result.count}")

    try:
        # Phase 1: 抓取
        run_scrape_phase(
            stats=stats,
            http_client=http_client,
            supabase=supabase,
            categories=categories,
            start_page=start_page,
            batch_size=batch_size,
            max_articles=max_articles,
            dry_run=dry_run,
        )

        # Phase 2: 解析
        run_parse_phase(stats, parse_batch, dry_run)

        # Phase 3: 向量化
        run_embed_phase(stats, embed_batch, dry_run)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ 使用者中斷")
    except Exception as e:
        logger.error(f"\n❌ Pipeline 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        http_client.close()

    # 最終統計
    logger.info(stats.summary())

    if not dry_run:
        # 顯示最終狀態
        result = supabase.table("health_articles").select("count", count="exact").execute()
        logger.info(f"📚 資料庫最終文章數: {result.count}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="大紀元健康文章全自動處理 Pipeline")
    parser.add_argument("--batch-size", type=int, default=100, help="每批抓取文章數")
    parser.add_argument("--parse-batch", type=int, default=20, help="AI 解析批次大小")
    parser.add_argument("--embed-batch", type=int, default=50, help="向量化批次大小")
    parser.add_argument("--start-page", type=int, default=1, help="起始頁碼")
    parser.add_argument("--max-articles", type=int, default=0, help="最大文章數（0=無限制）")
    parser.add_argument("--category", type=int, default=None, help="分類索引（0-2）")
    parser.add_argument("--dry-run", action="store_true", help="試運行模式")

    args = parser.parse_args()

    run_full_pipeline(
        batch_size=args.batch_size,
        parse_batch=args.parse_batch,
        embed_batch=args.embed_batch,
        start_page=args.start_page,
        max_articles=args.max_articles,
        category_index=args.category,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
