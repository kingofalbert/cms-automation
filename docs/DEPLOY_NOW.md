# 🚀 SEO Title Feature - 立即部署指南

**準備就緒**: ✅ 所有開發和測試準備已完成
**部署方式**: 自動化腳本 + 手動驗證
**預計時間**: 30-60 分鐘
**風險等級**: 🟡 中等（已有回滾計劃）

---

## 📋 快速部署檢查清單

### 1️⃣ 部署前確認（5 分鐘）

```bash
# 檢查當前目錄
pwd
# 應顯示: /Users/albertking/ES/cms_automation

# 檢查 DATABASE_URL
echo $DATABASE_URL
# 應顯示生產資料庫 URL

# 檢查 GCP 配置
gcloud config get-value project
gcloud config get-value run/region

# 檢查 GCP 授權
gcloud auth list
# 應顯示已授權帳號

# 檢查工具版本
poetry --version
npm --version
gcloud --version
psql --version
```

**所有檢查通過？** → 繼續下一步

---

### 2️⃣ 執行部署（20-40 分鐘）

#### 選項 A: 完整自動部署（推薦）

```bash
# 包含資料庫備份和遷移
./scripts/deploy_seo_title_feature.sh
```

**腳本會詢問確認的步驟**:
1. ❓ 確定要繼續部署嗎？
2. ❓ 確定要執行遷移嗎？
3. ❓ 確定要部署後端嗎？
4. ❓ 確定要上傳到 GCS 嗎？

每個步驟都需要輸入 `y` 確認。

#### 選項 B: 跳過備份（已手動備份）

```bash
./scripts/deploy_seo_title_feature.sh --skip-backup
```

#### 選項 C: 跳過遷移（已手動執行）

```bash
./scripts/deploy_seo_title_feature.sh --skip-migration
```

#### 選項 D: 兩者都跳過

```bash
./scripts/deploy_seo_title_feature.sh --skip-backup --skip-migration
```

---

### 3️⃣ 部署後驗證（10 分鐘）

#### A. 資料庫驗證

```bash
# 檢查新欄位
psql "$DATABASE_URL" -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'articles' AND column_name LIKE 'seo_title%';
"
```

**預期結果**: 應顯示 5 個欄位
```
 column_name            | data_type
------------------------+-----------
 seo_title              | character varying
 seo_title_source       | character varying
 seo_title_extracted    | boolean
 suggested_seo_titles   | jsonb
 seo_title_selected_at  | timestamp
```

#### B. 後端 API 驗證

```bash
# 替換為您的後端 URL
BACKEND_URL="https://YOUR_BACKEND_URL"

# 健康檢查
curl -s "$BACKEND_URL/health"
# 預期: {"status":"healthy"}

# 檢查 SEO Title API 端點
curl -s -X OPTIONS "$BACKEND_URL/api/v1/optimization/articles/1/select-seo-title" -w "\nHTTP Status: %{http_code}\n"
# 預期: HTTP Status: 200 或 405

# 獲取文章（檢查 seo_title 欄位）
curl -s "$BACKEND_URL/api/v1/articles/1" | grep -o '"seo_title":[^,}]*'
# 預期: "seo_title":null 或 "seo_title":"實際值"
```

#### C. 前端驗證（手動）

1. 訪問前端 URL
2. 登入系統
3. 導航到文章列表頁面
4. 點擊任一文章進入 ArticleReview 頁面
5. **確認看到「SEO Title 選擇」卡片**
6. 嘗試以下操作：
   - [ ] 看到原文提取的 SEO Title（如果有）
   - [ ] 看到 2-3 個 AI 生成的變體
   - [ ] 點擊選擇一個變體
   - [ ] 點擊「使用此 SEO Title」按鈕
   - [ ] 看到成功提示訊息
   - [ ] 嘗試輸入自定義 SEO Title
   - [ ] 確認字符數警告（超過 40 字時）

#### D. WordPress 整合驗證（可選）

1. 選擇一篇文章設置 SEO Title
2. 點擊「發佈到 WordPress」
3. 在 WordPress 後台檢查文章
4. **確認 Yoast SEO 的「SEO 標題」欄位已填寫**

---

### 4️⃣ 監控設置（5 分鐘）

#### 查看後端日誌

```bash
# 最近 50 條日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cms-backend" \
  --limit 50 \
  --format json

# 只看錯誤
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cms-backend AND severity>=ERROR" \
  --limit 20
```

#### 檢查資料庫使用情況

```sql
-- 檢查有多少文章有 SEO Title
SELECT
  COUNT(*) as total_articles,
  COUNT(seo_title) as with_seo_title,
  ROUND(100.0 * COUNT(seo_title) / NULLIF(COUNT(*), 0), 2) as percentage,
  COUNT(CASE WHEN seo_title_source = 'extracted' THEN 1 END) as extracted,
  COUNT(CASE WHEN seo_title_source = 'ai_generated' THEN 1 END) as ai_generated,
  COUNT(CASE WHEN seo_title_source = 'user_input' THEN 1 END) as user_input
FROM articles;
```

---

## 🔥 如果遇到問題

### 問題 1: 資料庫遷移失敗

```bash
# 檢查當前遷移狀態
cd backend
poetry run alembic current

# 查看遷移歷史
poetry run alembic history

# 如果卡住，嘗試強制升級
poetry run alembic upgrade head --sql  # 預覽 SQL
poetry run alembic upgrade head  # 執行
```

### 問題 2: 後端部署失敗

```bash
# 查看最新構建日誌
gcloud builds list --limit 5

# 查看特定構建的日誌
gcloud builds log BUILD_ID

# 檢查 Cloud Run 服務狀態
gcloud run services describe cms-backend --region YOUR_REGION
```

### 問題 3: 前端構建失敗

```bash
cd frontend

# 清除快取
rm -rf node_modules/.vite dist

# 重新安裝依賴
npm ci

# 重新構建
NODE_ENV=production npm run build

# 檢查構建輸出
ls -lh dist/
```

### 問題 4: API 無法訪問

```bash
# 檢查 Cloud Run 服務是否運行
gcloud run services list

# 獲取服務 URL
gcloud run services describe cms-backend --region YOUR_REGION --format='value(status.url)'

# 測試基本連接
curl -v https://YOUR_BACKEND_URL/health
```

---

## 🔄 緊急回滾程序

### 如果需要立即回滾

#### 1. 回滾資料庫

```bash
cd backend

# 降級到上一個版本
poetry run alembic downgrade -1

# 驗證
poetry run alembic current
```

#### 2. 回滾後端服務

```bash
# 查看所有修訂版本
gcloud run revisions list --service=cms-backend --region=YOUR_REGION

# 記下上一個穩定版本的名稱，例如: cms-backend-00042-abc

# 切換流量到上一個版本
gcloud run services update-traffic cms-backend \
  --to-revisions=cms-backend-00042-abc=100 \
  --region=YOUR_REGION

# 驗證
gcloud run services describe cms-backend --region=YOUR_REGION
```

#### 3. 回滾前端（如需要）

```bash
# 找到上一個穩定的 commit
git log --oneline -10

# 切換到上一個版本
git checkout PREVIOUS_COMMIT_HASH

cd frontend

# 重新構建
NODE_ENV=production npm run build

# 上傳到 GCS
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/

# 返回最新代碼
git checkout main
```

#### 4. 從備份完全還原

```bash
# 找到備份文件（由部署腳本創建）
ls -lh backup_seo_title_*.sql

# 還原（⚠️ 這會覆蓋所有更改！）
psql "$DATABASE_URL" < backup_seo_title_YYYYMMDD_HHMMSS.sql
```

---

## 📊 部署完成後的指標

### 立即指標（部署後 1 小時）

- [ ] 後端健康檢查: ✅ Healthy
- [ ] 資料庫遷移: ✅ 20251114_1401 applied
- [ ] 前端可訪問: ✅ 正常載入
- [ ] SEO Title 卡片顯示: ✅ 正常
- [ ] API 回應時間: ⏱️ < 500ms
- [ ] 錯誤數: 📉 0

### 24 小時指標

- [ ] 使用 SEO Title 功能的文章數: 📈 > 0
- [ ] API 錯誤率: 📉 < 1%
- [ ] 平均回應時間: ⏱️ < 300ms
- [ ] WordPress 發佈成功率: ✅ > 95%

### 7 天指標

- [ ] 採用率: 📈 檢查有多少文章設置了 SEO Title
- [ ] 來源分佈:
  - `extracted`: X%
  - `ai_generated`: Y%
  - `user_input`: Z%
- [ ] 使用者反饋: 📝 收集編輯人員的使用體驗

---

## ✅ 部署成功確認

當以下所有項目都完成時，部署視為成功：

- [x] 資料庫遷移成功（5 個新欄位已存在）
- [x] 後端健康檢查通過
- [x] SEO Title API 端點可訪問
- [x] 前端正常載入
- [x] SEO Title 選擇卡片正常顯示
- [x] 可以成功選擇 AI 變體或輸入自定義 SEO Title
- [x] 選擇後 API 調用成功
- [x] WordPress 發佈時 Yoast SEO 欄位已填寫
- [x] 沒有嚴重錯誤在日誌中

---

## 📞 需要幫助？

### 參考文檔

1. **完整實施計劃**: `docs/SEO_TITLE_IMPLEMENTATION_PLAN.md`
2. **當前狀態**: `docs/SEO_TITLE_CURRENT_STATUS.md`
3. **部署檢查清單**: `docs/DEPLOYMENT_CHECKLIST_PRODUCTION.md`
4. **就緒報告**: `docs/PRODUCTION_DEPLOYMENT_READY.md`

### 快速命令參考

```bash
# 查看腳本幫助
./scripts/deploy_seo_title_feature.sh --help

# 測試資料庫連接
psql "$DATABASE_URL" -c "SELECT 1;"

# 查看 Alembic 狀態
cd backend && poetry run alembic current

# 查看 Cloud Run 狀態
gcloud run services list

# 查看前端構建
cd frontend && npm run build
```

---

**最後更新**: 2025-01-14
**功能版本**: Phase 9 - SEO Title 提取與選擇
**狀態**: ✅ 準備就緒，可以立即部署

---

## 🎯 立即開始

**準備好了嗎？執行以下命令開始部署：**

```bash
cd /Users/albertking/ES/cms_automation
./scripts/deploy_seo_title_feature.sh
```

祝部署順利！🚀
