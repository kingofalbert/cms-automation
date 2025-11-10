# CMS Automation - 快速參考卡片

## 🚀 每日工作流程

### 開始工作前
```bash
# 1. 檢查當前環境
./scripts/check-environment.sh

# 2. 如需切換環境
./scripts/switch-environment.sh
```

---

## 🏭 生產環境部署

### 前端部署
```bash
cd /Users/albertking/ES/cms_automation/frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/
```

### 後端部署
```bash
cd /Users/albertking/ES/cms_automation/backend
gcloud run deploy cms-automation-backend \
  --source . \
  --region us-east1 \
  --project cmsupload-476323 \
  --allow-unauthenticated
```

### 快速驗證
```bash
# 測試後端健康
curl https://cms-automation-backend-baau2zqeqq-ue.a.run.app/health

# 測試 CORS
curl -I -H "Origin: https://storage.googleapis.com" \
  https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/worklist

# 訪問前端
open https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html
```

---

## 📊 環境對照表

| 項目 | 生產環境 | 測試環境 |
|------|---------|---------|
| **GCP 項目** | `cmsupload-476323` | `cms-automation-2025` |
| **GCP 賬號** | `albert.king@epochtimes.nyc` | `albert.king@gmail.com` |
| **前端 URL** | https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/ | (待定) |
| **後端 URL** | https://cms-automation-backend-baau2zqeqq-ue.a.run.app | (待定) |
| **前端 Bucket** | `gs://cms-automation-frontend-cmsupload-476323/` | (待定) |

---

## 🔧 常用命令

### 查看日誌
```bash
# 生產環境後端日誌
gcloud logging read "resource.type=cloud_run_revision" \
  --project=cmsupload-476323 \
  --limit=50

# 實時日誌流
gcloud logging tail "resource.type=cloud_run_revision" \
  --project=cmsupload-476323
```

### Secret 管理
```bash
# 查看 secret 值
gcloud secrets versions access latest \
  --secret=ALLOWED_ORIGINS \
  --project=cmsupload-476323

# 更新 secret
echo 'NEW_VALUE' | gcloud secrets versions add SECRET_NAME \
  --project=cmsupload-476323 \
  --data-file=-
```

### 數據庫操作
```bash
# 連接生產數據庫
cd /Users/albertking/ES/cms_automation/backend
grep "^DATABASE_URL=" .env | cut -d'=' -f2- | \
  sed 's/postgresql+asyncpg/postgresql/g' | \
  sed 's/?ssl=require/?sslmode=require/g' > /tmp/db_url.txt
psql "$(cat /tmp/db_url.txt)"

# 重置文章狀態
psql "$(cat /tmp/db_url.txt)" -c \
  "UPDATE worklist_items SET status = 'pending', notes = '[]'::jsonb"
```

---

## ⚠️ 注意事項

### 部署前檢查清單
- [ ] 運行 `./scripts/check-environment.sh`
- [ ] 確認當前環境（生產/測試）
- [ ] 確認 GCloud 賬號正確
- [ ] 確認 `.env.production` 配置正確
- [ ] 運行 `npm run build` 確認無錯誤
- [ ] 運行測試確認通過

### CORS 問題排查
如果遇到 CORS 錯誤：
1. 檢查 ALLOWED_ORIGINS secret
2. 確認包含完整的 GCS bucket URL
3. 觸發後端重新部署使用新 secret
4. 清除瀏覽器緩存重新測試

### 環境切換注意
切換環境後必須：
1. 運行 `./scripts/check-environment.sh` 驗證
2. 檢查 `.env.production` 是否需要更新
3. 確認數據庫連接是否正確

---

## 🆘 緊急故障排除

### 前端無法加載
```bash
# 1. 檢查前端文件是否存在
gsutil ls gs://cms-automation-frontend-cmsupload-476323/

# 2. 檢查 index.html
gsutil cat gs://cms-automation-frontend-cmsupload-476323/index.html | head -20

# 3. 重新部署
cd frontend && npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/
```

### 後端 API 錯誤
```bash
# 1. 檢查服務狀態
gcloud run services describe cms-automation-backend \
  --project=cmsupload-476323 \
  --region=us-east1

# 2. 查看錯誤日誌
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --project=cmsupload-476323 \
  --limit=20

# 3. 測試健康檢查
curl https://cms-automation-backend-baau2zqeqq-ue.a.run.app/health
```

### CORS 阻擋
```bash
# 1. 檢查 secret
gcloud secrets versions access latest \
  --secret=ALLOWED_ORIGINS \
  --project=cmsupload-476323

# 2. 更新 secret（如果需要）
echo '["http://localhost:3000","http://localhost:8000","https://storage.googleapis.com","https://cms-automation-frontend-cmsupload-476323.storage.googleapis.com"]' | \
gcloud secrets versions add ALLOWED_ORIGINS \
  --project=cmsupload-476323 \
  --data-file=-

# 3. 觸發重新部署
gcloud run services update cms-automation-backend \
  --region us-east1 \
  --project cmsupload-476323 \
  --update-secrets=ALLOWED_ORIGINS=ALLOWED_ORIGINS:latest
```

---

## 📚 相關文檔

- [完整環境配置](./ENVIRONMENTS.md) - 詳細的環境配置和故障排除
- [今日修復報告](./docs/2025-11-10-regression-testing-fixes.md) - 回歸測試結果和修復詳情
- [Phase 7 規格](./features/007-multi-step-workflow/spec.md) - 多步驟工作流規格

---

## 🔗 快速連結

### GCP 控制台
- [Cloud Run 服務](https://console.cloud.google.com/run?project=cmsupload-476323)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager?project=cmsupload-476323)
- [Cloud Storage](https://console.cloud.google.com/storage/browser?project=cmsupload-476323)
- [日誌查看](https://console.cloud.google.com/logs?project=cmsupload-476323)

### 生產環境
- [前端應用](https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html)
- [後端 API](https://cms-automation-backend-baau2zqeqq-ue.a.run.app)
- [健康檢查](https://cms-automation-backend-baau2zqeqq-ue.a.run.app/health)

---

**最後更新**: 2025-11-10
**維護**: 請在任何環境變更後更新此文檔
