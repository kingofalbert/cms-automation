#!/bin/bash
#
# CMS Automation - 環境檢查腳本
# 用途：在執行部署或配置更改前，驗證當前環境配置
#

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "======================================"
echo "  CMS Automation - 環境檢查工具"
echo "======================================"
echo ""

# 檢查 gcloud 配置
echo -e "${BLUE}📋 檢查 GCloud 配置...${NC}"
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

echo "  當前賬號: ${CURRENT_ACCOUNT}"
echo "  當前項目: ${CURRENT_PROJECT}"
echo ""

# 判斷環境
if [ "$CURRENT_PROJECT" = "cmsupload-476323" ]; then
    ENVIRONMENT="PRODUCTION"
    EXPECTED_ACCOUNT="albert.king@epochtimes.nyc"
    BACKEND_URL="https://cms-automation-backend-baau2zqeqq-ue.a.run.app"
    FRONTEND_BUCKET="gs://cms-automation-frontend-cmsupload-476323/"
    COLOR=$RED
elif [ "$CURRENT_PROJECT" = "cms-automation-2025" ]; then
    ENVIRONMENT="TESTING"
    EXPECTED_ACCOUNT="albert.king@gmail.com"
    BACKEND_URL="(測試環境後端 URL)"
    FRONTEND_BUCKET="(測試環境前端 bucket)"
    COLOR=$YELLOW
else
    echo -e "${RED}❌ 錯誤：未識別的項目 '$CURRENT_PROJECT'${NC}"
    echo ""
    echo "請切換到以下項目之一："
    echo "  - cmsupload-476323 (生產環境)"
    echo "  - cms-automation-2025 (測試環境)"
    echo ""
    echo "切換命令："
    echo "  gcloud config set project cmsupload-476323"
    echo "  gcloud auth login albert.king@epochtimes.nyc"
    exit 1
fi

echo -e "${COLOR}🔍 當前環境: ${ENVIRONMENT}${NC}"
echo ""

# 檢查賬號是否匹配
if [ "$CURRENT_ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
    echo -e "${RED}⚠️  警告：賬號不匹配！${NC}"
    echo "  預期賬號: ${EXPECTED_ACCOUNT}"
    echo "  當前賬號: ${CURRENT_ACCOUNT}"
    echo ""
    echo "建議執行："
    echo "  gcloud auth login ${EXPECTED_ACCOUNT}"
    echo ""
else
    echo -e "${GREEN}✓ 賬號匹配${NC}"
    echo ""
fi

# 顯示環境詳情
echo -e "${BLUE}📦 環境詳情:${NC}"
echo "  後端 URL: ${BACKEND_URL}"
echo "  前端 Bucket: ${FRONTEND_BUCKET}"
echo ""

# 測試後端健康檢查
if [ "$ENVIRONMENT" = "PRODUCTION" ]; then
    echo -e "${BLUE}🏥 測試後端健康檢查...${NC}"
    if curl -s -f "${BACKEND_URL}/health" > /dev/null 2>&1; then
        HEALTH_STATUS=$(curl -s "${BACKEND_URL}/health")
        echo -e "${GREEN}✓ 後端健康檢查通過${NC}"
        echo "  響應: ${HEALTH_STATUS}"
    else
        echo -e "${RED}✗ 後端健康檢查失敗${NC}"
        echo "  URL: ${BACKEND_URL}/health"
    fi
    echo ""

    # 測試 CORS 配置
    echo -e "${BLUE}🔐 測試 CORS 配置...${NC}"
    CORS_HEADER=$(curl -s -I -H "Origin: https://storage.googleapis.com" "${BACKEND_URL}/v1/worklist" | grep -i "access-control-allow-origin" || echo "")
    if [ -n "$CORS_HEADER" ]; then
        echo -e "${GREEN}✓ CORS 配置正確${NC}"
        echo "  Header: ${CORS_HEADER}"
    else
        echo -e "${RED}✗ CORS 配置缺失${NC}"
        echo "  未找到 Access-Control-Allow-Origin header"
    fi
    echo ""
fi

# 檢查本地前端配置
echo -e "${BLUE}⚙️  檢查前端配置...${NC}"
FRONTEND_DIR="/Users/albertking/ES/cms_automation/frontend"
if [ -f "${FRONTEND_DIR}/.env.production" ]; then
    API_URL=$(grep "^VITE_API_URL=" "${FRONTEND_DIR}/.env.production" | cut -d'=' -f2)
    echo "  .env.production API URL: ${API_URL}"

    if [ "$ENVIRONMENT" = "PRODUCTION" ] && [ "$API_URL" = "$BACKEND_URL" ]; then
        echo -e "${GREEN}✓ 前端配置正確${NC}"
    elif [ "$ENVIRONMENT" = "PRODUCTION" ]; then
        echo -e "${RED}⚠️  前端配置不匹配${NC}"
        echo "  預期: ${BACKEND_URL}"
        echo "  實際: ${API_URL}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 .env.production 文件${NC}"
fi
echo ""

# 快速命令提示
echo -e "${BLUE}🚀 快速命令:${NC}"
echo ""
if [ "$ENVIRONMENT" = "PRODUCTION" ]; then
    echo "部署前端："
    echo "  cd ${FRONTEND_DIR}"
    echo "  npm run build"
    echo "  gsutil -m rsync -r -d dist/ ${FRONTEND_BUCKET}"
    echo ""
    echo "部署後端："
    echo "  cd /Users/albertking/ES/cms_automation/backend"
    echo "  gcloud run deploy cms-automation-backend \\"
    echo "    --source . --region us-east1 --project ${CURRENT_PROJECT}"
    echo ""
    echo "查看日誌："
    echo "  gcloud logging read \"resource.type=cloud_run_revision\" \\"
    echo "    --project=${CURRENT_PROJECT} --limit=20"
else
    echo "測試環境部署命令類似，但使用項目: ${CURRENT_PROJECT}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ 環境檢查完成${NC}"
echo "======================================"
echo ""
