#!/bin/bash
#
# CMS Automation - 環境切換腳本
# 用途：快速切換生產環境和測試環境
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
echo "  CMS Automation - 環境切換工具"
echo "======================================"
echo ""

# 顯示當前環境
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)

echo -e "${BLUE}當前配置:${NC}"
echo "  項目: ${CURRENT_PROJECT}"
echo "  賬號: ${CURRENT_ACCOUNT}"
echo ""

# 選擇目標環境
echo "選擇目標環境:"
echo "  1) 生產環境 (cmsupload-476323)"
echo "  2) 測試環境 (cms-automation-2025)"
echo "  3) 取消"
echo ""
read -p "請輸入選項 (1-3): " choice

case $choice in
  1)
    TARGET_PROJECT="cmsupload-476323"
    TARGET_ACCOUNT="albert.king@epochtimes.nyc"
    ENVIRONMENT_NAME="生產環境"
    ENV_COLOR=$RED
    ;;
  2)
    TARGET_PROJECT="cms-automation-2025"
    TARGET_ACCOUNT="albert.king@gmail.com"
    ENVIRONMENT_NAME="測試環境"
    ENV_COLOR=$YELLOW
    ;;
  3)
    echo "已取消"
    exit 0
    ;;
  *)
    echo -e "${RED}無效的選項${NC}"
    exit 1
    ;;
esac

echo ""
echo -e "${ENV_COLOR}切換到 ${ENVIRONMENT_NAME}...${NC}"
echo ""

# 切換項目
echo "步驟 1/3: 設置 GCloud 項目..."
gcloud config set project "${TARGET_PROJECT}"

# 切換賬號（如果需要）
if [ "$CURRENT_ACCOUNT" != "$TARGET_ACCOUNT" ]; then
    echo "步驟 2/3: 切換 GCloud 賬號..."
    echo "  需要登錄賬號: ${TARGET_ACCOUNT}"

    # 檢查賬號是否已經登錄
    if gcloud auth list --filter="account=${TARGET_ACCOUNT}" --format="value(account)" 2>/dev/null | grep -q "${TARGET_ACCOUNT}"; then
        echo "  賬號已登錄，激活中..."
        gcloud config set account "${TARGET_ACCOUNT}"
    else
        echo "  賬號未登錄，啟動登錄流程..."
        gcloud auth login "${TARGET_ACCOUNT}"
    fi
else
    echo "步驟 2/3: 賬號已是 ${TARGET_ACCOUNT}，跳過"
fi

# 驗證切換
echo "步驟 3/3: 驗證環境..."
NEW_PROJECT=$(gcloud config get-value project 2>/dev/null)
NEW_ACCOUNT=$(gcloud config get-value account 2>/dev/null)

echo ""
if [ "$NEW_PROJECT" = "$TARGET_PROJECT" ] && [ "$NEW_ACCOUNT" = "$TARGET_ACCOUNT" ]; then
    echo -e "${GREEN}✓ 環境切換成功！${NC}"
    echo ""
    echo -e "${ENV_COLOR}現在使用 ${ENVIRONMENT_NAME}:${NC}"
    echo "  項目: ${NEW_PROJECT}"
    echo "  賬號: ${NEW_ACCOUNT}"
    echo ""

    # 顯示環境資訊
    if [ "$TARGET_PROJECT" = "cmsupload-476323" ]; then
        echo "後端 URL: https://cms-automation-backend-baau2zqeqq-ue.a.run.app"
        echo "前端 Bucket: gs://cms-automation-frontend-cmsupload-476323/"
        echo ""
        echo "測試健康檢查:"
        echo "  curl https://cms-automation-backend-baau2zqeqq-ue.a.run.app/health"
    else
        echo "測試環境 - 配置待定"
    fi

    echo ""
    echo "建議運行環境檢查工具確認："
    echo "  ./scripts/check-environment.sh"
else
    echo -e "${RED}✗ 環境切換失敗${NC}"
    echo "  預期項目: ${TARGET_PROJECT}"
    echo "  實際項目: ${NEW_PROJECT}"
    echo "  預期賬號: ${TARGET_ACCOUNT}"
    echo "  實際賬號: ${NEW_ACCOUNT}"
    exit 1
fi

echo ""
echo "======================================"
echo ""
