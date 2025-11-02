# Supabase 數據庫配置指南

## 📋 快速設置步驟

### 1. 獲取 Supabase 憑證

1. **登錄 Supabase Dashboard**
   - 訪問：https://app.supabase.com
   - 選擇您的項目（或創建新項目）

2. **獲取數據庫連接信息**
   - 進入 `Settings` → `Database`
   - 找到 `Connection string` 部分
   - 選擇 `Pooler` 模式（推薦用於生產環境）
   - 複製連接字符串

3. **獲取 API 密鑰**（可選，用於文件存儲）
   - 進入 `Settings` → `API`
   - 複製以下信息：
     - Project URL
     - `anon` key（公開密鑰）
     - `service_role` key（服務密鑰，僅後端使用）

### 2. 更新配置文件

編輯 `/Users/albertking/ES/cms_automation/.env.supabase` 文件：

```bash
# 替換占位符為您的實際值
DATABASE_URL=postgresql+asyncpg://postgres.xyzcompany:YourActualPassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**占位符說明：**
- `xyzcompany`: 您的項目 Reference ID
- `YourActualPassword`: 數據庫密碼
- `aws-0-us-east-1`: 您的項目區域

### 3. 啟用 pgvector 擴展

在 Supabase SQL Editor 中運行：

```sql
-- 啟用 pgvector 擴展（用於語義搜索）
CREATE EXTENSION IF NOT EXISTS vector;

-- 驗證擴展已安裝
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 4. 運行設置腳本

```bash
# 進入後端目錄
cd /Users/albertking/ES/cms_automation/backend

# 運行設置腳本
poetry run python scripts/setup_supabase.py
```

腳本將：
- ✅ 測試數據庫連接
- ✅ 檢查必要的擴展
- ✅ 運行數據庫遷移
- ✅ 創建所有必要的表

### 5. 驗證設置

成功設置後，您應該看到以下表：

#### 核心表：
- `articles` - 文章內容
- `topic_requests` - 主題請求
- `topic_embeddings` - 語義嵌入
- `seo_metadata` - SEO 元數據

#### 發布相關：
- `publish_tasks` - 發布任務
- `execution_logs` - 執行日誌
- `provider_metrics` - 提供者指標

#### T7.1 校對表（新增）：
- `proofreading_history` - 校對歷史
- `proofreading_decisions` - 決策記錄
- `feedback_tuning_jobs` - 反饋調優任務

---

## 🔧 故障排除

### 問題 1：連接被拒絕

**錯誤信息：**
```
connection to server at "xxx.supabase.com" failed: Connection refused
```

**解決方案：**
1. 檢查項目是否處於活躍狀態（免費項目可能會暫停）
2. 確認使用了正確的連接字符串（Pooler vs Direct）
3. 檢查網絡連接和防火牆設置

### 問題 2：認證失敗

**錯誤信息：**
```
password authentication failed for user "postgres.xxx"
```

**解決方案：**
1. 重置數據庫密碼（Settings → Database → Reset database password）
2. 確保密碼中的特殊字符正確編碼
3. 使用連接字符串時選擇 "URI" 格式

### 問題 3：pgvector 擴展問題

**錯誤信息：**
```
extension "vector" is not available
```

**解決方案：**
在 Supabase SQL Editor 中以超級用戶身份運行：
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 問題 4：遷移失敗

**錯誤信息：**
```
relation "articles" does not exist
```

**解決方案：**
清理並重新運行所有遷移：
```bash
# 重置到初始狀態
poetry run alembic downgrade base

# 運行所有遷移
poetry run alembic upgrade head
```

---

## ✅ 完成後的下一步

1. **啟動後端服務器**
   ```bash
   cd backend
   poetry run uvicorn src.main:app --reload
   ```

2. **測試 API**
   訪問：http://localhost:8000/docs

3. **實施 T7.2-T7.5**
   - T7.2: 決策寫入服務
   - T7.3: 決策 API
   - T7.4: 前端決策 UI
   - T7.5: 反饋調優任務

---

## 📚 參考資源

- [Supabase 官方文檔](https://supabase.com/docs)
- [pgvector 文檔](https://github.com/pgvector/pgvector)
- [Connection Pooling 最佳實踐](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

---

## 🔐 安全提醒

⚠️ **重要安全事項：**

1. **永遠不要將密鑰提交到 Git**
   - 確保 `.env` 和 `.env.supabase` 在 `.gitignore` 中
   - 使用環境變量管理敏感信息

2. **區分密鑰類型**
   - `anon` key：可以在前端使用（有 RLS 保護）
   - `service_role` key：僅在後端使用（繞過 RLS）

3. **啟用 Row Level Security (RLS)**
   - 在生產環境中為所有表啟用 RLS
   - 配置適當的策略

4. **使用連接池**
   - 生產環境使用 Pooler 連接（port 6543）
   - 避免連接數超限

---

**創建時間**: 2025-11-02
**最後更新**: 2025-11-02
**版本**: 1.0