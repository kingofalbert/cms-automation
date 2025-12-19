# 開發環境 - 生產環境一致性配置

**創建日期**: 2024-12-17
**目的**: 讓開發環境與生產環境 (admin.epochtimes.com) 保持一致

---

## 快速開始

### 1. 啟動環境

```bash
# 啟動生產環境一致的開發環境
docker-compose -f docker-compose.dev-prod-like.yml up -d

# 查看日誌（等待 WordPress 初始化）
docker-compose -f docker-compose.dev-prod-like.yml logs -f wp-cli
```

### 2. 等待初始化完成

初始化腳本會自動：
- ✅ 安裝 WordPress
- ✅ 安裝 Classic Editor 插件
- ✅ 安裝 Slim SEO 插件（Lite SEO 替代品）
- ✅ 創建測試用戶
- ✅ 配置分類和固定連結

### 3. 訪問 WordPress

```
URL: http://localhost:8001

第一層認證 (HTTP Basic Auth):
  用戶名: djy
  密碼: djy2013

第二層認證 (WordPress):
  用戶名: admin
  密碼: admin
```

---

## 環境對比

| 配置項 | 生產環境 | 開發環境 (新) | 開發環境 (舊) |
|--------|---------|--------------|--------------|
| **URL** | https://admin.epochtimes.com | http://localhost:8001 | http://localhost:8001 |
| **HTTP Basic Auth** | ✅ djy/djy2013 | ✅ djy/djy2013 | ❌ 無 |
| **編輯器** | Classic Editor | Classic Editor | Gutenberg |
| **SEO 插件** | Lite SEO | Slim SEO | 無 |
| **HTTPS** | ✅ | ❌ | ❌ |

---

## 配置文件

### 使用 `.env.dev-prod-like.example`

```bash
# 複製配置文件
cp .env.dev-prod-like.example .env

# 編輯並填入你的 API 密鑰
vim .env
```

### 主要配置項

```bash
# HTTP Basic Auth（與生產環境相同）
CMS_HTTP_AUTH_USERNAME=djy
CMS_HTTP_AUTH_PASSWORD=djy2013

# WordPress 登錄
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=admin
```

---

## 測試驗證

### 使用 Playwright 腳本驗證

```bash
# 啟動虛擬環境
source /tmp/playwright_venv/bin/activate

# 運行驗證腳本
python scripts/check_wordpress_editor.py
```

預期輸出：
```
============================================================
📊 RESULTS
============================================================
Editor Type: CLASSIC
Has Gutenberg (Block Editor): ❌ No
Has Classic Editor: ✅ Yes
------------------------------------------------------------
SEO Plugin: SLIM SEO (or similar)
============================================================
```

---

## 架構說明

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                                                             │
│  ┌─────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │  Nginx  │ ───► │  WordPress  │ ───► │   MySQL     │     │
│  │ :8001   │      │  (internal) │      │  (internal) │     │
│  │         │      │             │      │             │     │
│  │ HTTP    │      │ Classic     │      │             │     │
│  │ Basic   │      │ Editor +    │      │             │     │
│  │ Auth    │      │ Slim SEO    │      │             │     │
│  └─────────┘      └─────────────┘      └─────────────┘     │
│       ▲                                                     │
│       │                                                     │
│  User Request (djy/djy2013)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 常見操作

### 重置環境

```bash
# 停止並刪除容器和數據
docker-compose -f docker-compose.dev-prod-like.yml down -v

# 重新啟動
docker-compose -f docker-compose.dev-prod-like.yml up -d
```

### 安裝額外插件

```bash
# 進入 WP-CLI 容器
docker-compose -f docker-compose.dev-prod-like.yml run --rm wp-cli bash

# 安裝插件
wp plugin install <plugin-name> --activate
```

### 查看日誌

```bash
# WordPress 日誌
docker-compose -f docker-compose.dev-prod-like.yml logs wordpress

# Nginx 日誌
docker-compose -f docker-compose.dev-prod-like.yml logs nginx
```

---

## 與 Computer Use 測試

現在你可以在開發環境中測試 Computer Use 發布流程，行為與生產環境一致：

1. **雙層認證** - HTTP Basic Auth + WordPress 登錄
2. **Classic Editor** - 無 Gutenberg 區塊
3. **SEO 插件** - Slim SEO（行為類似 Lite SEO）

```bash
# 測試發布（使用開發環境）
curl -X POST http://localhost:8000/v1/computer-use/publish \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 123,
    "cms_url": "http://localhost:8001"
  }'
```

---

## 故障排除

### 問題 1: 無法訪問 localhost:8001

```bash
# 檢查 nginx 是否運行
docker-compose -f docker-compose.dev-prod-like.yml ps nginx

# 檢查日誌
docker-compose -f docker-compose.dev-prod-like.yml logs nginx
```

### 問題 2: HTTP Basic Auth 不工作

```bash
# 檢查 .htpasswd 文件
cat tests/docker/nginx/.htpasswd

# 重新生成
echo "djy:$(openssl passwd -apr1 'djy2013')" > tests/docker/nginx/.htpasswd

# 重啟 nginx
docker-compose -f docker-compose.dev-prod-like.yml restart nginx
```

### 問題 3: WordPress 插件未安裝

```bash
# 手動運行設置腳本
docker-compose -f docker-compose.dev-prod-like.yml run --rm wp-cli /setup.sh
```

---

## 相關文件

- `docker-compose.dev-prod-like.yml` - Docker Compose 配置
- `tests/docker/nginx/nginx.conf` - Nginx 配置（含 HTTP Basic Auth）
- `tests/docker/nginx/.htpasswd` - HTTP Basic Auth 密碼文件
- `tests/docker/wordpress/setup-prod-like.sh` - WordPress 初始化腳本
- `.env.dev-prod-like.example` - 環境變量示例

---

**最後更新**: 2024-12-17
