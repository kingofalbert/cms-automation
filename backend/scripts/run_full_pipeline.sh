#!/bin/bash
#
# 完整的大紀元健康文章處理 Pipeline（分批次）
#
# 這個腳本按順序執行：
# 1. 抓取最新文章（2025年）到本地
# 2. 導入數據庫 + AI 解析 + 向量化
# 3. 抓取舊存檔文章（2001-2017年）到本地
# 4. 導入數據庫 + AI 解析 + 向量化
#
# 使用方式：
#     ./scripts/run_full_pipeline.sh [--skip-new] [--skip-archive]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 啟動虛擬環境
source venv/bin/activate

echo "============================================================"
echo "大紀元健康文章完整處理 Pipeline（分批次）"
echo "============================================================"
echo "時間: $(date)"
echo "目錄: $PROJECT_DIR"
echo ""

# 解析參數
SKIP_NEW=false
SKIP_ARCHIVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-new)
            SKIP_NEW=true
            shift
            ;;
        --skip-archive)
            SKIP_ARCHIVE=true
            shift
            ;;
        *)
            echo "未知參數: $1"
            exit 1
            ;;
    esac
done

# ============================================================
# 第一批：最新文章（2025年）
# ============================================================
if [ "$SKIP_NEW" = false ]; then
    echo ""
    echo "============================================================"
    echo "第一批：抓取最新文章（2025年）"
    echo "============================================================"
    echo ""

    # 階段 1: 抓取最新文章到本地
    echo "[1/4] 抓取最新文章到本地..."
    python -u scripts/scrape_all_to_local.py --resume

    # 階段 2: 導入數據庫
    echo ""
    echo "[2/4] 導入數據庫..."
    python -u scripts/import_to_database.py --batch-size 100

    # 階段 3: AI 解析
    echo ""
    echo "[3/4] AI 解析..."
    python -u scripts/parse_all_articles.py --batch-size 20

    # 階段 4: 向量化
    echo ""
    echo "[4/4] 向量化..."
    python -u scripts/embed_all_articles.py --batch-size 50

    echo ""
    echo "✅ 第一批（最新文章）處理完成！"
else
    echo "跳過第一批（最新文章）"
fi

# ============================================================
# 第二批：舊存檔文章（2001-2017年）
# ============================================================
if [ "$SKIP_ARCHIVE" = false ]; then
    echo ""
    echo "============================================================"
    echo "第二批：抓取舊存檔文章（2001-2017年）"
    echo "============================================================"
    echo ""

    # 階段 1: 抓取舊存檔文章到本地
    echo "[1/4] 抓取舊存檔文章到本地..."
    python -u scripts/scrape_all_to_local.py --archive --resume

    # 階段 2: 導入數據庫
    echo ""
    echo "[2/4] 導入數據庫..."
    python -u scripts/import_to_database.py --batch-size 100

    # 階段 3: AI 解析
    echo ""
    echo "[3/4] AI 解析..."
    python -u scripts/parse_all_articles.py --batch-size 20

    # 階段 4: 向量化
    echo ""
    echo "[4/4] 向量化..."
    python -u scripts/embed_all_articles.py --batch-size 50

    echo ""
    echo "✅ 第二批（舊存檔文章）處理完成！"
else
    echo "跳過第二批（舊存檔文章）"
fi

# 完成
echo ""
echo "============================================================"
echo "完整 Pipeline 完成!"
echo "============================================================"
echo "結束時間: $(date)"
echo ""
