# SEO Title Feature - 生產環境部署檢查清單

**日期：** 2025-11-14
**功能：** SEO Title 優化功能
**版本：** 1.0

---

## ✅ 測試結果確認

### 後端測試

**API 集成測試** ✅ **通過**
```bash
cd backend
poetry run python test_seo_title_api.py
```

**測試結果：**
- ✅ 測試 1: 查找有優化建議的文章 - PASSED
- ✅ 測試 2: 檢查 SEO Title 建議 - PASSED
- ✅ 測試 3: 模擬選擇 SEO Title API - PASSED
- ✅ 測試 4: 驗證 PublishingOrchestrator 邏輯 - PASSED
- ✅ 測試 5: 清理測試數據 - PASSED

**結論：** 所有後端 API 測試通過，功能正常運作。

**單元測試** ⏸️ **已創建，待實際執行**
```bash
cd backend
poetry run pytest tests/services/test_article_parser_seo_title.py -v
```
**狀態：** 測試文件已創建但需要調整 mock 才能執行

### 前端測試

**E2E 測試** ⏸️ **已創建，需手動驗證**
```bash
cd frontend
npm run test:e2e -- seo-title-selection.spec.ts
```
**狀態：** 測試腳本已創建，建議在部署前手動測試 UI

---

## 📋 部署前檢查清單

### A. 資料庫準備

**1. 備份生產資料庫** ⬜
```bash
# 創建備份
export PRODUCTION_DATABASE_URL="your-production-db-url"
pg_dump "$PRODUCTION_DATABASE_URL" > backup_seo_title_$(date +%Y%m%d_%H%M%S).sql

# 驗證備份
ls -lh backup_seo_title_*.sql
```
- [ ] 備份文件已創建
- [ ] 備份文件大小合理
- [ ] 備份文件已保存到安全位置

**2. 檢查當前遷移狀態** ⬜
```bash
cd backend
export DATABASE_URL="$PRODUCTION_DATABASE_URL"
poetry run alembic current
```
**期望輸出：** 顯示當前的遷移版本

**3. 預覽遷移 SQL** ⬜
```bash
poetry run alembic upgrade head --sql > /tmp/seo_title_migration_preview.sql
cat /tmp/seo_title_migration_preview.sql
```
- [ ] SQL 語句正確
- [ ] 只包含 SEO Title 相關變更
- [ ] 沒有意外的 DROP 或 DELETE 語句

---

### B. 後端部署準備

**1. 檢查代碼狀態** ⬜
```bash
cd backend
git status
git log --oneline -5
```
- [ ] 所有變更已提交
- [ ] 在正確的分支上
- [ ] 沒有未追蹤的重要文件

**2. 檢查依賴** ⬜
```bash
poetry check
poetry install --no-dev
```
- [ ] poetry.lock 文件最新
- [ ] 沒有依賴衝突
- [ ] 生產環境依賴正確安裝

**3. 檢查環境變數** ⬜
確認以下環境變數已配置：
- [ ] `DATABASE_URL` - 生產資料庫連接
- [ ] `CMS_BASE_URL` - WordPress 網站 URL
- [ ] `CMS_USERNAME` - WordPress 管理員帳號
- [ ] `CMS_APPLICATION_PASSWORD` - WordPress 應用程式密碼
- [ ] `ENVIRONMENT=production`

**4. 測試後端啟動** ⬜（可選，本地測試）
```bash
# 使用生產配置啟動（謹慎！）
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
```
- [ ] 後端成功啟動
- [ ] 健康檢查端點正常（`/health`）
- [ ] 沒有啟動錯誤

---

### C. 前端部署準備

**1. 構建前端** ⬜
```bash
cd frontend
npm ci  # Clean install
NODE_ENV=production npm run build
```
- [ ] 構建成功完成
- [ ] 沒有 TypeScript 錯誤
- [ ] 沒有 ESLint 警告
- [ ] `dist/` 目錄已生成

**2. 檢查構建產物** ⬜
```bash
ls -lh dist/
du -sh dist/
```
- [ ] `index.html` 存在
- [ ] `assets/` 目錄存在
- [ ] 構建大小合理（< 5MB）

**3. 驗證組件導出** ⬜
```bash
grep -r "SEOTitleSelectionCard" dist/assets/*.js
```
- [ ] SEOTitleSelectionCard 已包含在構建中

---

### D. WordPress 配置檢查

**1. 確認 Yoast SEO 插件** ⬜
- [ ] 登入 WordPress 管理後台
- [ ] 導航到「外掛 > 已安裝外掛」
- [ ] 確認 Yoast SEO 已安裝並啟用
- [ ] 版本：15.0+ （建議）

**2. 測試 SEO 欄位選擇器** ⬜

創建一個測試文章並檢查：
```javascript
// 在 WordPress 編輯器頁面的瀏覽器 console 執行
document.querySelector("input[name='yoast_wpseo_title']")
// 應該返回 <input> 元素
```
- [ ] SEO Title 欄位存在
- [ ] 選擇器正確

**3. 測試 WordPress API 憑證** ⬜
```bash
# 測試應用程式密碼
curl -u "username:xxxx xxxx xxxx xxxx" \
  https://your-wordpress-site.com/wp-json/wp/v2/users/me
```
- [ ] 返回用戶資料（非錯誤）
- [ ] 憑證有效

---

## 🚀 部署執行步驟

### 第 1 步：資料庫遷移

**時間估計：** 5-10 分鐘
**風險等級：** 🟡 中等（可回滾）

```bash
cd backend

# 1. 設置環境變數
export DATABASE_URL="$PRODUCTION_DATABASE_URL"

# 2. 驗證當前狀態
poetry run alembic current

# 3. 執行遷移
poetry run alembic upgrade head

# 4. 驗證遷移成功
poetry run alembic current
# 應該顯示：20251114_1401 (head)

# 5. 檢查新欄位
psql "$DATABASE_URL" -c "
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'articles'
  AND column_name LIKE 'seo_title%'
ORDER BY ordinal_position;
"
```

**期望結果：**
```
 column_name        | data_type         | is_nullable
--------------------+-------------------+-------------
 seo_title          | character varying | YES
 seo_title_extracted| boolean           | NO
 seo_title_source   | character varying | YES
```

**✅ 檢查點：**
- [ ] 遷移執行無錯誤
- [ ] 新欄位已創建
- [ ] 現有資料未受影響（檢查幾筆 articles）

**🔄 回滾（如需要）：**
```bash
poetry run alembic downgrade -1
```

---

### 第 2 步：部署後端 API

**時間估計：** 10-15 分鐘
**風險等級：** 🟡 中等

#### 選項 A：Google Cloud Run（推薦）

```bash
cd backend

# 1. 設置 GCP 專案
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region YOUR_REGION

# 2. 構建並推送映像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cms-backend:seo-title

# 3. 部署到 Cloud Run
gcloud run deploy cms-backend \
  --image gcr.io/YOUR_PROJECT_ID/cms-backend:seo-title \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="$DATABASE_URL" \
  --set-env-vars CMS_BASE_URL="https://your-wordpress.com" \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets CMS_APPLICATION_PASSWORD=cms-wp-password:latest

# 4. 獲取部署 URL
BACKEND_URL=$(gcloud run services describe cms-backend --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

**✅ 檢查點：**
- [ ] 映像構建成功
- [ ] Cloud Run 服務部署成功
- [ ] 獲得服務 URL

#### 選項 B：傳統伺服器

```bash
# SSH 到生產伺服器
ssh user@your-server.com

cd /var/www/cms_automation/backend

# 1. 拉取最新代碼
git pull origin main

# 2. 安裝依賴
poetry install --no-dev

# 3. 執行遷移（如果尚未執行）
poetry run alembic upgrade head

# 4. 重啟服務
sudo systemctl restart cms-backend.service
# 或
pm2 restart cms-backend
```

**✅ 檢查點：**
- [ ] 代碼更新成功
- [ ] 服務重啟無錯誤
- [ ] 應用程式正常運行

---

### 第 3 步：驗證後端部署

**時間估計：** 5 分鐘

```bash
# 1. 健康檢查
curl $BACKEND_URL/health
# 期望：{"status": "healthy"}

# 2. 測試 SEO Title 端點
curl -X OPTIONS $BACKEND_URL/api/v1/optimization/articles/1/select-seo-title
# 期望：200 OK 或 405 Method Not Allowed（表示端點存在）

# 3. 檢查資料庫欄位（透過 API）
curl $BACKEND_URL/api/v1/articles/1 | jq '.seo_title, .seo_title_source'
# 期望：返回 seo_title 欄位（可能為 null）
```

**✅ 檢查點：**
- [ ] 健康檢查通過
- [ ] API 端點可訪問
- [ ] 資料庫欄位可讀取

---

### 第 4 步：部署前端

**時間估計：** 5-10 分鐘
**風險等級：** 🟢 低

```bash
cd frontend

# 1. 最終構建
NODE_ENV=production npm run build

# 2. 同步到 GCS
BUCKET_NAME="cms-automation-frontend-cmsupload-476323"
gsutil -m rsync -r -d dist/ "gs://$BUCKET_NAME/"

# 3. 設置快取標頭
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" \
  "gs://$BUCKET_NAME/assets/**"

# 4. 清除 CDN 快取（如使用 Cloud CDN）
gcloud compute url-maps invalidate-cdn-cache cms-frontend-lb \
  --path "/*" \
  --async
```

**✅ 檢查點：**
- [ ] 文件成功上傳到 GCS
- [ ] CDN 快取已清除
- [ ] 可以訪問前端 URL

---

### 第 5 步：端到端驗證

**時間估計：** 10-15 分鐘
**風險等級：** 🟢 低

**手動測試流程：**

1. **訪問文章審核頁面** ⬜
   ```
   https://your-frontend-domain.com/article-review/1
   ```
   - [ ] 頁面正常載入
   - [ ] 無 JavaScript 錯誤

2. **檢查 SEO Title 選擇卡片** ⬜
   - [ ] SEO Title 選擇區塊顯示
   - [ ] 當前 SEO Title 顯示（如有）
   - [ ] 來源標籤正確（原文提取/AI生成/自定義）

3. **測試 AI 變體選擇**（如有建議）⬜
   - [ ] AI 變體列表顯示
   - [ ] 點擊「使用此 SEO Title」按鈕
   - [ ] 顯示成功訊息
   - [ ] 當前 SEO Title 更新

4. **測試自定義輸入** ⬜
   - [ ] 輸入自定義 SEO Title：「測試SEO標題」
   - [ ] 字符計數器顯示正確
   - [ ] 點擊「保存自定義 SEO Title」
   - [ ] 顯示成功訊息

5. **測試 WordPress 發佈**（可選但建議）⬜
   - [ ] 選擇一個 SEO Title
   - [ ] 點擊「發佈」按鈕
   - [ ] 監控發佈流程
   - [ ] 檢查日誌中的「seo_title_configured」訊息
   - [ ] 登入 WordPress 後台
   - [ ] 檢查 Yoast SEO Title 欄位已填入
   - [ ] 檢查頁面 `<title>` 標籤使用 SEO Title

---

## 📊 部署後監控

### 第 1 週監控

**1. API 錯誤率** ⬜
```bash
# Cloud Run 日誌
gcloud logging read "
  resource.type=cloud_run_revision
  AND severity>=ERROR
  AND (textPayload=~'seo_title' OR jsonPayload.message=~'seo_title')
  AND timestamp>='$(date -u -d '1 day ago' '+%Y-%m-%dT%H:%M:%SZ')'
" --limit 50
```
**目標：** 錯誤率 < 1%

**2. SEO Title 使用率** ⬜
```sql
-- 每日執行
SELECT
  DATE(updated_at) as date,
  seo_title_source,
  COUNT(*) as count
FROM articles
WHERE updated_at >= CURRENT_DATE - INTERVAL '7 days'
  AND seo_title IS NOT NULL
GROUP BY DATE(updated_at), seo_title_source
ORDER BY date DESC, count DESC;
```
**期望：** 新文章開始使用 SEO Title

**3. WordPress 發佈成功率** ⬜
```sql
SELECT
  DATE(created_at) as date,
  COUNT(*) as total,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful,
  ROUND(100.0 * COUNT(CASE WHEN status = 'completed' THEN 1 END) / COUNT(*), 2) as success_rate
FROM publish_tasks
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```
**目標：** 成功率 > 95%

---

## 🔄 回滾計劃

### 如果遇到嚴重問題

**1. 回滾資料庫遷移** 🚨
```bash
cd backend
poetry run alembic downgrade -1
```
**注意：** 如果已有資料寫入新欄位，回滾會導致資料遺失！

**2. 回滾後端部署** 🚨

**Cloud Run：**
```bash
# 列出歷史版本
gcloud run revisions list --service cms-backend

# 切換到上一個版本
PREVIOUS_REVISION="cms-backend-00042-xyz"
gcloud run services update-traffic cms-backend \
  --to-revisions $PREVIOUS_REVISION=100
```

**傳統伺服器：**
```bash
cd /var/www/cms_automation/backend
git reset --hard <previous-commit-hash>
poetry install --no-dev
sudo systemctl restart cms-backend.service
```

**3. 回滾前端** 🚨
```bash
# 重新部署上一個版本
cd frontend
git checkout <previous-commit>
npm run build
gsutil -m rsync -r -d dist/ "gs://$BUCKET_NAME/"
gcloud compute url-maps invalidate-cdn-cache cms-frontend-lb --path "/*"
```

---

## ✅ 部署完成確認

### 最終檢查清單

**資料庫：**
- [ ] 遷移成功執行
- [ ] 新欄位已創建
- [ ] 現有資料未受影響
- [ ] 已創建備份

**後端：**
- [ ] 服務成功部署
- [ ] 健康檢查通過
- [ ] API 端點可訪問
- [ ] 無啟動錯誤

**前端：**
- [ ] 成功構建並部署
- [ ] SEO Title 卡片正常顯示
- [ ] API 整合正常工作
- [ ] 無 JavaScript 錯誤

**整合：**
- [ ] SEO Title 選擇功能正常
- [ ] 資料可以儲存到資料庫
- [ ] WordPress 發佈使用 SEO Title
- [ ] 日誌正常記錄

**監控：**
- [ ] 錯誤率監控已設置
- [ ] 使用率追蹤已設置
- [ ] 發佈成功率監控已設置

---

## 📝 部署記錄

**部署執行者：** _______________
**部署日期：** 2025-__-__
**部署時間：** __:__ - __:__
**資料庫備份：** backup_seo_title___________.sql
**後端版本：** commit: _______
**前端版本：** commit: _______

**遇到的問題：**
-

**解決方案：**
-

**最終狀態：** ⬜ 成功 / ⬜ 部分成功 / ⬜ 失敗回滾

**備註：**


---

**文件版本：** 1.0
**最後更新：** 2025-11-14
**準備者：** Claude Code
