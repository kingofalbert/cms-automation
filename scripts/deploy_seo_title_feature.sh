#!/bin/bash
#
# SEO Title Feature - 快速部署腳本
#
# 用途：自動化部署 SEO Title 功能到生產環境
# 使用：./deploy_seo_title_feature.sh [--skip-backup] [--skip-migration]
#
# 警告：此腳本會直接修改生產環境！請先備份！
#

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函數：打印訊息
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函數：確認繼續
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "操作已取消"
        exit 1
    fi
}

# 解析參數
SKIP_BACKUP=false
SKIP_MIGRATION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        *)
            echo "未知參數: $1"
            echo "用法: $0 [--skip-backup] [--skip-migration]"
            exit 1
            ;;
    esac
done

log_info "=== SEO Title Feature 部署腳本 ==="
echo ""
log_warn "⚠️  此腳本將部署到生產環境"
log_warn "⚠️  請確保您已經："
log_warn "   1. 在測試環境驗證過功能"
log_warn "   2. 備份了生產資料庫"
log_warn "   3. 有權限訪問 GCP 和資料庫"
echo ""

confirm "確定要繼續部署嗎？"

# 檢查必要的工具
log_info "檢查必要工具..."
command -v poetry >/dev/null 2>&1 || { log_error "poetry 未安裝"; exit 1; }
command -v npm >/dev/null 2>&1 || { log_error "npm 未安裝"; exit 1; }
command -v gcloud >/dev/null 2>&1 || { log_error "gcloud 未安裝"; exit 1; }
command -v psql >/dev/null 2>&1 || { log_error "psql 未安裝"; exit 1; }
log_info "✓ 所有必要工具已安裝"

# 檢查環境變數
log_info "檢查環境變數..."
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL 環境變數未設置"
    exit 1
fi
log_info "✓ DATABASE_URL 已設置"

# 記錄部署時間
DEPLOY_TIME=$(date +%Y%m%d_%H%M%S)
log_info "部署時間: $DEPLOY_TIME"

# ============================================
# 第 1 步：備份資料庫
# ============================================
if [ "$SKIP_BACKUP" = false ]; then
    log_info ""
    log_info "=== 步驟 1/6: 備份生產資料庫 ==="

    BACKUP_FILE="backup_seo_title_${DEPLOY_TIME}.sql"
    log_info "正在創建備份: $BACKUP_FILE"

    pg_dump "$DATABASE_URL" > "$BACKUP_FILE"

    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_info "✓ 備份完成: $BACKUP_FILE ($BACKUP_SIZE)"
    else
        log_error "備份失敗"
        exit 1
    fi
else
    log_warn "跳過資料庫備份（--skip-backup）"
fi

# ============================================
# 第 2 步：執行資料庫遷移
# ============================================
if [ "$SKIP_MIGRATION" = false ]; then
    log_info ""
    log_info "=== 步驟 2/6: 執行資料庫遷移 ==="

    cd backend

    log_info "檢查當前遷移狀態..."
    poetry run alembic current

    log_info ""
    confirm "確定要執行遷移嗎？"

    log_info "執行遷移..."
    poetry run alembic upgrade head

    log_info "驗證遷移結果..."
    poetry run alembic current | grep "20251114_1401"

    if [ $? -eq 0 ]; then
        log_info "✓ 遷移成功完成"
    else
        log_error "遷移驗證失敗"
        exit 1
    fi

    log_info "檢查新欄位..."
    psql "$DATABASE_URL" -c "
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'articles' AND column_name LIKE 'seo_title%';
    "

    cd ..
else
    log_warn "跳過資料庫遷移（--skip-migration）"
fi

# ============================================
# 第 3 步：部署後端到 Cloud Run
# ============================================
log_info ""
log_info "=== 步驟 3/6: 部署後端到 Cloud Run ==="

cd backend

log_info "檢查 GCP 配置..."
PROJECT_ID=$(gcloud config get-value project)
REGION=$(gcloud config get-value run/region)

if [ -z "$PROJECT_ID" ] || [ -z "$REGION" ]; then
    log_error "GCP 專案或區域未設置"
    log_error "請執行: gcloud config set project YOUR_PROJECT_ID"
    log_error "        gcloud config set run/region YOUR_REGION"
    exit 1
fi

log_info "專案: $PROJECT_ID"
log_info "區域: $REGION"

confirm "確定要部署後端嗎？"

log_info "構建 Docker 映像..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/cms-backend:seo-title-${DEPLOY_TIME}

log_info "部署到 Cloud Run..."
gcloud run deploy cms-backend \
  --image gcr.io/${PROJECT_ID}/cms-backend:seo-title-${DEPLOY_TIME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated

BACKEND_URL=$(gcloud run services describe cms-backend --region ${REGION} --format='value(status.url)')
log_info "✓ 後端部署完成: $BACKEND_URL"

cd ..

# ============================================
# 第 4 步：驗證後端部署
# ============================================
log_info ""
log_info "=== 步驟 4/6: 驗證後端部署 ==="

log_info "檢查健康狀態..."
HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/health")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    log_info "✓ 後端健康檢查通過"
else
    log_error "後端健康檢查失敗: $HEALTH_RESPONSE"
    exit 1
fi

log_info "檢查 SEO Title API 端點..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "${BACKEND_URL}/api/v1/optimization/articles/1/select-seo-title")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ]; then
    log_info "✓ SEO Title API 端點存在 (HTTP $HTTP_CODE)"
else
    log_warn "SEO Title API 端點檢查返回: HTTP $HTTP_CODE"
fi

# ============================================
# 第 5 步：構建並部署前端
# ============================================
log_info ""
log_info "=== 步驟 5/6: 構建並部署前端 ==="

cd frontend

log_info "安裝依賴..."
npm ci

log_info "構建生產版本..."
NODE_ENV=production npm run build

if [ ! -d "dist" ]; then
    log_error "前端構建失敗：dist 目錄不存在"
    exit 1
fi

DIST_SIZE=$(du -sh dist | cut -f1)
log_info "✓ 前端構建完成: $DIST_SIZE"

BUCKET_NAME="cms-automation-frontend-cmsupload-476323"
log_info "部署到 GCS: gs://$BUCKET_NAME/"

confirm "確定要上傳到 GCS 嗎？"

log_info "同步文件到 GCS..."
gsutil -m rsync -r -d dist/ "gs://$BUCKET_NAME/"

log_info "設置快取標頭..."
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" \
  "gs://$BUCKET_NAME/assets/**" 2>/dev/null || true

log_info "清除 CDN 快取..."
gcloud compute url-maps invalidate-cdn-cache cms-frontend-lb \
  --path "/*" \
  --async 2>/dev/null || log_warn "CDN 快取清除失敗（可能未配置 CDN）"

log_info "✓ 前端部署完成"

cd ..

# ============================================
# 第 6 步：最終驗證
# ============================================
log_info ""
log_info "=== 步驟 6/6: 最終驗證 ==="

log_info "檢查資料庫連接..."
psql "$DATABASE_URL" -c "SELECT COUNT(*) as total_articles FROM articles;" | grep -q "total_articles"
if [ $? -eq 0 ]; then
    log_info "✓ 資料庫連接正常"
else
    log_error "資料庫連接失敗"
    exit 1
fi

log_info "檢查後端 API..."
curl -s "${BACKEND_URL}/api/v1/articles/1" | grep -q "seo_title"
if [ $? -eq 0 ]; then
    log_info "✓ API 返回 seo_title 欄位"
else
    log_warn "API 未返回 seo_title 欄位（可能為 null）"
fi

# ============================================
# 部署完成
# ============================================
log_info ""
log_info "========================================="
log_info "✅ SEO Title 功能部署完成！"
log_info "========================================="
log_info ""
log_info "部署摘要："
log_info "  • 部署時間: $DEPLOY_TIME"
if [ "$SKIP_BACKUP" = false ]; then
    log_info "  • 備份文件: $BACKUP_FILE ($BACKUP_SIZE)"
fi
log_info "  • 後端 URL: $BACKEND_URL"
log_info "  • 前端 GCS: gs://$BUCKET_NAME/"
log_info ""
log_info "下一步："
log_info "  1. 訪問前端並測試 SEO Title 選擇功能"
log_info "  2. 監控錯誤日誌（使用 gcloud logging）"
log_info "  3. 檢查 WordPress 發佈是否正常填寫 SEO Title"
log_info ""
log_info "回滾指令（如需要）："
log_info "  資料庫: cd backend && poetry run alembic downgrade -1"
log_info "  後端: gcloud run services update-traffic cms-backend --to-revisions=PREVIOUS_REVISION=100"
log_info "  前端: 重新構建並上傳上一個版本"
log_info ""
log_warn "請記錄此次部署到部署日誌中！"
