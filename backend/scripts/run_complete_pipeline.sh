#!/bin/bash
#
# 完整的大紀元健康文章處理 Pipeline
#
# 這個腳本按順序執行四個階段：
# 1. 完整抓取所有文章到本地文件
# 2. 從本地文件導入到數據庫
# 3. 批量解析所有文章
# 4. 批量向量化所有文章
#
# 使用方式：
#     ./scripts/run_complete_pipeline.sh [--skip-scrape] [--skip-import]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 啟動虛擬環境
source venv/bin/activate

echo "============================================================"
echo "大紀元健康文章完整處理 Pipeline"
echo "============================================================"
echo "時間: $(date)"
echo "目錄: $PROJECT_DIR"
echo ""

# 解析參數
SKIP_SCRAPE=false
SKIP_IMPORT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-scrape)
            SKIP_SCRAPE=true
            shift
            ;;
        --skip-import)
            SKIP_IMPORT=true
            shift
            ;;
        *)
            echo "未知參數: $1"
            exit 1
            ;;
    esac
done

# 階段 1: 完整抓取
if [ "$SKIP_SCRAPE" = false ]; then
    echo ""
    echo "============================================================"
    echo "階段 1: 完整抓取所有文章到本地"
    echo "============================================================"
    echo ""
    python -u scripts/scrape_all_to_local.py --resume
else
    echo "跳過階段 1: 抓取"
fi

# 階段 2: 導入數據庫
if [ "$SKIP_IMPORT" = false ]; then
    echo ""
    echo "============================================================"
    echo "階段 2: 從本地文件導入到數據庫"
    echo "============================================================"
    echo ""
    python -u scripts/import_to_database.py --batch-size 100
else
    echo "跳過階段 2: 導入"
fi

# 階段 3: 批量解析
echo ""
echo "============================================================"
echo "階段 3: 批量解析所有文章"
echo "============================================================"
echo ""
python -u scripts/parse_all_articles.py --batch-size 20

# 階段 4: 批量向量化
echo ""
echo "============================================================"
echo "階段 4: 批量向量化所有文章"
echo "============================================================"
echo ""
python -u scripts/embed_all_articles.py --batch-size 50

# 完成
echo ""
echo "============================================================"
echo "Pipeline 完成!"
echo "============================================================"
echo "結束時間: $(date)"
echo ""
