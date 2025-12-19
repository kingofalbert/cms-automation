# CMS Automation - 快速配置指南

**目標**: 5-10 分鐘內完成基本配置，讓系統運行起來

**狀態**: 系統已基本完成，需要配置環境變量

---

## 前提條件檢查

```bash
# 1. 確認 Docker 運行
docker ps  # 應該看到 PostgreSQL, Redis, WordPress

# 2. 確認後端依賴已安裝
cd backend
poetry install

# 3. 確認前端依賴已安裝
cd frontend
npm install
```

---

## 步驟 1: 後端環境配置 (2 分鐘)

### 檢查並更新 `.env` 文件

```bash
cd /Users/albertking/ES/cms_automation
vim .env
```

### 必須配置的變量:

#### 1. CMS 憑證 (選擇一個選項)

**選項 A: 使用生產環境 (epochtimes.com)**
```bash
# 在 .env 中添加/更新:
CMS_TYPE=wordpress
CMS_BASE_URL=https://admin.epochtimes.com
CMS_USERNAME=ping.xie
CMS_APPLICATION_PASSWORD="kfS*qxdQqm@zic6lXvnR(ih!"

# 如果有 HTTP Basic Auth:
CMS_HTTP_AUTH_USERNAME=djy
CMS_HTTP_AUTH_PASSWORD=djy2013
```

**選項 B: 使用本地 Docker WordPress**
```bash
CMS_TYPE=wordpress
CMS_BASE_URL=http://localhost:8080
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=admin
```

#### 2. Anthropic API Key

```bash
# 獲取 API Key: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-your-real-key-here
```

#### 3. Google Drive (可選，暫時可跳過)

```bash
# 如果有 Google Drive 憑證:
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id-here
```

### 驗證配置:

```bash
cd backend
poetry run python -c "
from src.config.settings import Settings
settings = Settings()
print(f'✅ CMS URL: {settings.CMS_BASE_URL}')
print(f'✅ CMS Type: {settings.CMS_TYPE}')
print(f'✅ CMS Username: {settings.CMS_USERNAME}')
print(f'✅ Database: {settings.DATABASE_URL}')
print(f'✅ Redis: {settings.REDIS_URL}')
"
```

預期輸出應該顯示所有配置正確。

---

## 步驟 2: 前端環境配置 (1 分鐘)

### 檢查 `.env` 文件

```bash
cd /Users/albertking/ES/cms_automation/frontend
cat .env
```

應該看到:
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_APP_TITLE=CMS Automation
VITE_ENV=development
```

如果需要修改後端 URL:
```bash
vim .env
# 修改 VITE_API_URL 和 VITE_WS_URL
```

---

## 步驟 3: 啟動服務 (2 分鐘)

### 3.1 確認 Docker 服務運行

```bash
docker-compose up -d
docker ps  # 確認 PostgreSQL, Redis, WordPress 運行中
```

### 3.2 運行數據庫遷移

```bash
cd backend
poetry run alembic upgrade head
```

### 3.3 啟動後端 API

```bash
cd backend
poetry run uvicorn src.main:app --reload --port 8000
```

在瀏覽器訪問: http://localhost:8000/docs
應該看到 Swagger API 文檔

### 3.4 啟動前端 (新終端)

```bash
cd frontend
npm run dev
```

在瀏覽器訪問: http://localhost:3000
應該看到 CMS Automation UI

---

## 步驟 4: 快速測試 (2 分鐘)

### 測試 1: 健康檢查

```bash
curl http://localhost:8000/health
```

預期輸出:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 測試 2: API 調用

```bash
# 獲取文章列表
curl http://localhost:8000/api/v1/articles
```

### 測試 3: 前端連接

1. 打開瀏覽器: http://localhost:3000
2. 應該看到 CMS Automation 界面
3. 檢查瀏覽器控制台，無錯誤

---

## 常見問題排查

### 問題 1: 後端無法連接數據庫

**錯誤**: `sqlalchemy.exc.OperationalError`

**解決**:
```bash
# 檢查 PostgreSQL 是否運行
docker ps | grep postgres

# 檢查 DATABASE_URL 配置
grep DATABASE_URL .env

# 重啟 PostgreSQL
docker-compose restart postgres
```

### 問題 2: 前端無法連接後端

**錯誤**: Browser console shows `Failed to fetch` or `Network Error`

**解決**:
```bash
# 1. 確認後端運行
curl http://localhost:8000/health

# 2. 檢查前端 .env
cat frontend/.env | grep VITE_API_URL

# 3. 確認 CORS 配置
grep ALLOWED_ORIGINS .env
# 應該包含: http://localhost:3000
```

### 問題 3: CMS 憑證無效

**錯誤**: Publishing tasks fail with authentication error

**解決**:
```bash
# 測試 CMS 憑證
cd backend
poetry run python tests/prod_env_test_v2.py

# 如果失敗，檢查 .env 中的 CMS_* 變量
# 特別注意密碼中的特殊字符需要用引號包裹
```

### 問題 4: Anthropic API Key 無效

**錯誤**: `anthropic.APIError: Invalid API Key`

**解決**:
```bash
# 1. 檢查 API Key
grep ANTHROPIC_API_KEY .env

# 2. 訪問 https://console.anthropic.com/ 獲取新 Key

# 3. 更新 .env 文件
vim .env
# ANTHROPIC_API_KEY=sk-ant-api03-your-new-key
```

---

## 下一步操作

### 基礎功能測試

1. **文章導入**:
   ```bash
   # 準備測試 CSV
   curl -X POST http://localhost:8000/api/v1/articles/import/csv \
     -F "file=@test_articles.csv"
   ```

2. **SEO 優化**:
   ```bash
   # 對文章進行 SEO 分析
   curl -X POST http://localhost:8000/api/v1/articles/1/seo/analyze
   ```

3. **發布測試** (使用沙盒環境):
   ```bash
   # 創建發布任務
   curl -X POST http://localhost:8000/api/v1/articles/1/publish \
     -H "Content-Type: application/json" \
     -d '{"provider": "playwright"}'
   ```

### 進階配置

完成基礎配置後，可以參考:
1. **Google Drive 集成**: `backend/docs/google_drive_integration_guide.md`
2. **安全配置**: `PROJECT_REVIEW_CONFIGURATION_GAPS.md` 第 4 節
3. **生產部署**: `PROJECT_REVIEW_CONFIGURATION_GAPS.md` 第 6 節

---

## 配置檢查清單

完成以下檢查後，系統應該可以正常運行:

### Backend
- [ ] `.env` 文件存在並配置正確
- [ ] `CMS_BASE_URL` 已設置
- [ ] `CMS_USERNAME` 已設置
- [ ] `CMS_APPLICATION_PASSWORD` 已設置
- [ ] `ANTHROPIC_API_KEY` 已設置
- [ ] `DATABASE_URL` 連接正常
- [ ] `REDIS_URL` 連接正常
- [ ] 數據庫遷移已運行
- [ ] API 服務運行在 port 8000
- [ ] http://localhost:8000/docs 可訪問

### Frontend
- [ ] `.env` 文件存在
- [ ] `VITE_API_URL` 指向 http://localhost:8000
- [ ] `VITE_WS_URL` 指向 ws://localhost:8000/ws
- [ ] npm 依賴已安裝
- [ ] 開發服務器運行在 port 3000
- [ ] http://localhost:3000 可訪問
- [ ] 瀏覽器控制台無錯誤

### Docker Services
- [ ] PostgreSQL 運行中
- [ ] Redis 運行中
- [ ] WordPress 運行中 (可選)

---

## 快速命令參考

```bash
# 啟動所有服務
docker-compose up -d
cd backend && poetry run uvicorn src.main:app --reload --port 8000 &
cd frontend && npm run dev &

# 停止所有服務
docker-compose down
# Ctrl+C 停止 backend 和 frontend

# 查看日誌
docker-compose logs -f postgres
docker-compose logs -f redis

# 重置數據庫
docker-compose down -v
docker-compose up -d
cd backend && poetry run alembic upgrade head

# 運行測試
cd backend && poetry run pytest
cd frontend && npm run test

# 構建生產版本
cd frontend && npm run build
cd backend && poetry build
```

---

## 獲取幫助

**文檔**:
- API 文檔: http://localhost:8000/docs
- 開發文檔: `/docs/`
- 詳細審查報告: `PROJECT_REVIEW_CONFIGURATION_GAPS.md`

**常見問題**:
- 配置問題: 查看 `PROJECT_REVIEW_CONFIGURATION_GAPS.md`
- 測試問題: 查看 `frontend/src/test/README_TESTING.md`
- 性能問題: 查看 `frontend/PERFORMANCE.md`

**聯繫支持**:
- GitHub Issues
- 團隊 Slack

---

**配置完成！🎉**

如果所有檢查項都通過，系統應該已經可以正常運行了。
接下來可以開始使用核心功能: 文章導入 → SEO 優化 → CMS 發布
