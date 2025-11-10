# CMS Automation - 環境配置文檔

## 📋 環境概覽

本項目有**兩個獨立的環境**：生產環境和測試環境。請確保在操作前明確當前環境。

---

## 🏭 生產環境 (Production)

### 基本資訊
- **GCP 項目**: `cmsupload-476323`
- **GCP 賬號**: `albert.king@epochtimes.nyc`
- **用途**: 實際運營的生產系統
- **數據庫**: Supabase 生產數據庫

### 前端配置
- **部署位置**: `gs://cms-automation-frontend-cmsupload-476323/`
- **訪問 URL**: `https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html`
- **環境變量文件**: `.env.production`
- **API 端點**: `https://cms-automation-backend-baau2zqeqq-ue.a.run.app`

### 後端配置
- **Cloud Run 服務名**: `cms-automation-backend`
- **Region**: `us-east1`
- **Service URL**: `https://cms-automation-backend-baau2zqeqq-ue.a.run.app`
- **替代 URL**: `https://cms-automation-backend-297291472291.us-east1.run.app`
- **環境變量**: 通過 **Google Cloud Secret Manager** 管理
- **數據庫連接**: 使用 `DATABASE_URL` secret

### 關鍵 Secrets (Secret Manager)
```yaml
ALLOWED_ORIGINS:
  - http://localhost:3000
  - http://localhost:8000
  - https://storage.googleapis.com
  - https://cms-automation-frontend-cmsupload-476323.storage.googleapis.com

DATABASE_URL: postgresql://postgres.twsbhjmlmspjwfystpti:***@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### 部署命令
```bash
# 前端部署
cd /Users/albertking/ES/cms_automation/frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/

# 後端部署
cd /Users/albertking/ES/cms_automation/backend
gcloud run deploy cms-automation-backend \
  --source . \
  --region us-east1 \
  --platform managed \
  --project cmsupload-476323 \
  --allow-unauthenticated
```

### 環境驗證
```bash
# 檢查當前 gcloud 配置
gcloud config get-value account    # 應該是: albert.king@epochtimes.nyc
gcloud config get-value project    # 應該是: cmsupload-476323

# 測試 API 連接
curl https://cms-automation-backend-baau2zqeqq-ue.a.run.app/health

# 測試 CORS
curl -I -H "Origin: https://storage.googleapis.com" \
  https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/worklist
```

---

## 🧪 測試環境 (Testing/Development)

### 基本資訊
- **GCP 項目**: `cms-automation-2025`
- **GCP 賬號**: `albert.king@gmail.com`
- **用途**: 開發和測試新功能
- **數據庫**: 獨立的測試數據庫

### 前端配置
- **部署位置**: 待定（可能沒有獨立部署）
- **本地開發**: `http://localhost:3000`

### 後端配置
- **Cloud Run 服務名**: `cms-automation-backend`
- **Region**: `us-east1`
- **環境變量**: 通過 `.env` 文件本地管理

### 部署命令
```bash
# 切換到測試賬號
gcloud auth login albert.king@gmail.com
gcloud config set project cms-automation-2025

# 後端部署
cd /Users/albertking/ES/cms_automation/backend
gcloud run deploy cms-automation-backend \
  --source . \
  --region us-east1 \
  --platform managed \
  --project cms-automation-2025 \
  --allow-unauthenticated
```

---

## ⚠️ 常見混淆點和解決方案

### 問題 1: 部署到錯誤的環境
**症狀**: 部署命令執行後，服務沒有按預期更新

**原因**: `gcloud` 配置指向錯誤的項目

**解決方案**:
```bash
# 在執行任何操作前，先檢查當前環境
gcloud config get-value project
gcloud config get-value account

# 如果錯誤，切換到正確的環境
gcloud config set project cmsupload-476323        # 生產環境
gcloud auth login albert.king@epochtimes.nyc

# 或
gcloud config set project cms-automation-2025     # 測試環境
gcloud auth login albert.king@gmail.com
```

### 問題 2: 前端調用錯誤的後端 URL
**症狀**: 前端顯示 CORS 錯誤或 404

**原因**: `.env.production` 配置的 API URL 不正確

**檢查清單**:
```bash
# 1. 檢查 .env.production 文件
cat /Users/albertking/ES/cms_automation/frontend/.env.production

# 2. 確認 VITE_API_URL 是否正確
# 生產環境應該是: https://cms-automation-backend-baau2zqeqq-ue.a.run.app

# 3. 重新構建前端（如果 URL 有改動）
cd /Users/albertking/ES/cms_automation/frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/
```

### 問題 3: CORS 錯誤
**症狀**: 瀏覽器控制台顯示 "No 'Access-Control-Allow-Origin' header"

**原因**: 後端的 `ALLOWED_ORIGINS` Secret 缺少前端域名

**解決方案**:
```bash
# 檢查當前 secret 值
gcloud secrets versions access latest \
  --secret=ALLOWED_ORIGINS \
  --project=cmsupload-476323

# 更新 secret（如果需要）
echo '["http://localhost:3000","http://localhost:8000","https://storage.googleapis.com","https://cms-automation-frontend-cmsupload-476323.storage.googleapis.com"]' | \
gcloud secrets versions add ALLOWED_ORIGINS \
  --project=cmsupload-476323 \
  --data-file=-

# 觸發後端重新部署以使用新 secret
gcloud run services update cms-automation-backend \
  --region us-east1 \
  --project cmsupload-476323 \
  --update-secrets=ALLOWED_ORIGINS=ALLOWED_ORIGINS:latest
```

### 問題 4: 數據庫連接錯誤
**症狀**: 後端無法連接到數據庫

**檢查清單**:
1. 確認 `DATABASE_URL` 環境變量/secret 是否正確設置
2. 確認數據庫 IP 是否在白名單中
3. 確認 SSL 連接參數：`?sslmode=require`
4. 本地測試時使用 `.env` 文件，生產環境使用 Secret Manager

---

## 🔍 環境檢查清單

在執行任何部署或配置更改前，請先完成此檢查清單：

### 部署前檢查 ✅

- [ ] 確認當前 gcloud 賬號：`gcloud config get-value account`
- [ ] 確認當前 gcloud 項目：`gcloud config get-value project`
- [ ] 確認目標環境（生產/測試）
- [ ] 如果是生產環境，確認賬號是 `albert.king@epochtimes.nyc`
- [ ] 如果是生產環境，確認項目是 `cmsupload-476323`
- [ ] 前端部署：確認 `.env.production` 的 API URL 正確
- [ ] 後端部署：確認所有必要的 secrets 已設置

### 部署後驗證 ✅

- [ ] 測試健康檢查端點：`curl [BACKEND_URL]/health`
- [ ] 測試 CORS 配置：`curl -I -H "Origin: https://storage.googleapis.com" [BACKEND_URL]/v1/worklist`
- [ ] 在瀏覽器中訪問前端 URL
- [ ] 檢查瀏覽器控制台是否有 CORS 或 404 錯誤
- [ ] 確認數據正確加載

---

## 📞 故障排除聯繫資訊

### GCP 控制台連結

**生產環境 (cmsupload-476323)**:
- Cloud Run 服務: https://console.cloud.google.com/run?project=cmsupload-476323
- Secret Manager: https://console.cloud.google.com/security/secret-manager?project=cmsupload-476323
- Cloud Storage: https://console.cloud.google.com/storage/browser?project=cmsupload-476323
- 日誌查看: https://console.cloud.google.com/logs?project=cmsupload-476323

**測試環境 (cms-automation-2025)**:
- Cloud Run 服務: https://console.cloud.google.com/run?project=cms-automation-2025

### 快速命令參考

```bash
# 查看生產環境後端日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cms-automation-backend" \
  --project=cmsupload-476323 \
  --limit=50 \
  --format=json

# 查看 Cloud Run 服務詳情
gcloud run services describe cms-automation-backend \
  --project=cmsupload-476323 \
  --region=us-east1

# 列出所有環境變量和 secrets
gcloud run services describe cms-automation-backend \
  --project=cmsupload-476323 \
  --region=us-east1 \
  --format="value(spec.template.spec.containers[0].env)"

# 重置數據庫文章狀態（生產環境）
cd /Users/albertking/ES/cms_automation/backend
grep "^DATABASE_URL=" .env | cut -d'=' -f2- | \
  sed 's/postgresql+asyncpg/postgresql/g' | \
  sed 's/?ssl=require/?sslmode=require/g' > /tmp/db_url.txt
psql "$(cat /tmp/db_url.txt)" -c "UPDATE worklist_items SET status = 'pending', notes = '[]'::jsonb"
```

---

## 📝 更新日誌

| 日期 | 變更內容 | 操作人員 |
|------|---------|---------|
| 2025-11-10 | 創建環境配置文檔，澄清生產/測試環境 | Claude Code |
| 2025-11-10 | 修復生產環境 CORS 問題，更新 ALLOWED_ORIGINS secret | Claude Code |
| 2025-11-10 | 添加 WorklistPage accessibility (main element) | Claude Code |
| 2025-11-10 | 修復 TypeScript 編譯錯誤（Badge variants） | Claude Code |

---

**最後更新**: 2025-11-10
**維護人員**: Albert King
**審核狀態**: ✅ 已驗證
