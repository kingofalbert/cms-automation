# 配置检查清单 - Configuration Checklist

**创建日期**: 2025-10-31
**用途**: 端到端测试前的配置验证

---

## 📋 配置检查总览

本文档列出了运行 CMS Automation 系统所需的所有配置和凭证。在进行端到端测试之前，请确保所有必需项都已配置。

---

## ✅ 必需配置项

### 1. 应用配置 (Application Configuration)

| 配置项 | 环境变量 | 状态 | 说明 |
|--------|----------|------|------|
| **Secret Key** | `SECRET_KEY` | ❌ 未配置 | 会话管理和 JWT 签名密钥，最少 32 字符 |
| **Environment** | `ENVIRONMENT` | ⚠️ 可选 | development/staging/production（默认: development） |
| **Log Level** | `LOG_LEVEL` | ⚠️ 可选 | DEBUG/INFO/WARNING/ERROR（默认: INFO） |

**生成 Secret Key**:
```bash
openssl rand -hex 32
```

---

### 2. 数据库配置 (Database - PostgreSQL)

| 配置项 | 环境变量 | 状态 | 说明 |
|--------|----------|------|------|
| **Database URL** | `DATABASE_URL` | ❌ 未配置 | PostgreSQL 连接字符串 |

**示例配置**:
```bash
DATABASE_URL=postgresql+asyncpg://cms_user:cms_password@localhost:5432/cms_automation
```

**验证数据库连接**:
```bash
# 测试连接
docker compose exec postgres psql -U cms_user -d cms_automation -c "SELECT 1;"

# 检查表是否存在
docker compose exec postgres psql -U cms_user -d cms_automation -c "\dt"
```

---

### 3. Redis 配置 (Cache & Task Queue)

| 配置项 | 环境变量 | 状态 | 说明 |
|--------|----------|------|------|
| **Redis URL** | `REDIS_URL` | ❌ 未配置 | Redis 连接字符串 |

**示例配置**:
```bash
REDIS_URL=redis://localhost:6379/0
```

**验证 Redis 连接**:
```bash
# 测试连接
docker compose exec redis redis-cli ping
# 预期输出: PONG

# 检查连接数
docker compose exec redis redis-cli info clients
```

---

### 4. Anthropic API 配置 (Claude - Computer Use)

| 配置项 | 环境变量 | 状态 | 说明 |
|--------|----------|------|------|
| **API Key** | `ANTHROPIC_API_KEY` | ❌ 未配置 | Claude API 密钥（用于 Computer Use 发布） |
| **Model** | `ANTHROPIC_MODEL` | ⚠️ 可选 | 默认: claude-3-5-sonnet-20241022 |

**获取 API Key**:
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建 API Key
3. 配置到 `.env` 文件

**验证 API Key**:
```bash
# 使用 curl 测试
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

### 5. WordPress/CMS 配置 (Publishing Target)

| 配置项 | 环境变量 | 状态 | 说明 |
|--------|----------|------|------|
| **CMS Base URL** | `CMS_BASE_URL` | ❌ 未配置 | WordPress 站点 URL |
| **CMS Username** | `CMS_USERNAME` | ❌ 未配置 | WordPress 用户名 |
| **Application Password** | `CMS_APPLICATION_PASSWORD` | ❌ 未配置 | WordPress 应用密码 |
| **CMS Type** | `CMS_TYPE` | ⚠️ 可选 | 默认: wordpress |

**WordPress 应用密码设置步骤**:
1. 登录 WordPress 后台
2. 用户 → 个人资料
3. 滚动到"应用程序密码"部分
4. 输入名称（如 "CMS Automation"）
5. 点击"添加新应用程序密码"
6. 复制生成的密码（格式: `xxxx xxxx xxxx xxxx xxxx xxxx`）
7. 配置到 `.env` 文件（去除空格）

**示例配置**:
```bash
CMS_BASE_URL=https://your-wordpress-site.com
CMS_USERNAME=your-username
CMS_APPLICATION_PASSWORD=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**验证 WordPress 凭证**:
```bash
# 测试登录（如果有 Playwright）
# 或手动访问 WordPress 后台确认凭证正确
```

---

### 6. Google Drive 配置 (File Storage & Document Sync)

| 配置项 | 环境变量 | 状态 | 说明 |
|--------|----------|------|------|
| **Credentials Path** | `GOOGLE_DRIVE_CREDENTIALS_PATH` | ❌ 未配置 | 服务账号 JSON 凭证文件路径 |
| **Folder ID** | `GOOGLE_DRIVE_FOLDER_ID` | ❌ 未配置 | Google Drive 文件夹 ID |

**详细设置步骤**: 参见 `backend/docs/google_drive_integration_guide.md`

#### 快速设置指南:

**Step 1: 创建 Google Cloud 项目**
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目

**Step 2: 启用 Google Drive API**
```bash
gcloud services enable drive.googleapis.com --project=cms-automation-2025
```

**Step 3: 创建服务账号**
1. IAM & Admin → 服务账号
2. 创建服务账号: `cms-automation-drive-service`
3. 生成 JSON 密钥

**Step 4: 配置 Google Drive 文件夹**
1. 在 Google Drive 创建文件夹（如 "CMS Automation Files"）
2. 分享文件夹给服务账号邮箱（Editor 权限）
3. 从 URL 复制文件夹 ID: `https://drive.google.com/drive/folders/YOUR_FOLDER_ID`

**Step 5: 配置凭证**
```bash
# 创建凭证目录
mkdir -p /home/kingofalbert/projects/CMS/backend/credentials

# 复制 JSON 密钥文件
cp ~/Downloads/your-service-account-key.json \
   /home/kingofalbert/projects/CMS/backend/credentials/google-drive-credentials.json

# 设置权限
chmod 600 /home/kingofalbert/projects/CMS/backend/credentials/google-drive-credentials.json
```

**Step 6: 更新 .env**
```bash
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id-here
```

**Step 7: 验证配置**
```bash
# 检查凭证文件
ls -la /home/kingofalbert/projects/CMS/backend/credentials/

# 测试访问（运行后端后）
# 调用 POST /api/v1/worklist/sync 端点
```

---

## 📁 配置文件位置

### 主配置文件

| 文件 | 路径 | 说明 |
|------|------|------|
| **.env** | `/home/kingofalbert/projects/CMS/.env` | 环境变量配置文件（**未创建**） |
| **.env.example** | `/home/kingofalbert/projects/CMS/.env.example` | 配置模板 |
| **Google Drive 凭证** | `/home/kingofalbert/projects/CMS/backend/credentials/google-drive-credentials.json` | 服务账号密钥 |

### 创建 .env 文件

```bash
# 从模板创建
cp /home/kingofalbert/projects/CMS/.env.example /home/kingofalbert/projects/CMS/.env

# 设置权限
chmod 600 /home/kingofalbert/projects/CMS/.env

# 编辑配置
nano /home/kingofalbert/projects/CMS/.env
```

---

## 🔐 安全注意事项

### 敏感文件保护

1. **添加到 .gitignore**:
```bash
# 确保以下文件在 .gitignore 中
.env
credentials/*.json
*.pem
*.key
```

2. **文件权限**:
```bash
# .env 文件权限
chmod 600 .env

# 凭证文件权限
chmod 600 backend/credentials/*.json
```

3. **Docker 挂载**:
确保 `docker-compose.yml` 挂载凭证目录：
```yaml
services:
  backend:
    volumes:
      - ./backend:/app
      - ./backend/credentials:/app/credentials  # 凭证目录
```

---

## ✅ 配置验证脚本

创建并运行验证脚本：

```bash
#!/bin/bash
# 保存为: check_config.sh

echo "==================================="
echo "CMS Automation - 配置检查"
echo "==================================="

# 检查 .env 文件
if [ -f .env ]; then
    echo "✅ .env 文件存在"
else
    echo "❌ .env 文件不存在"
    echo "   运行: cp .env.example .env"
fi

# 检查 Google Drive 凭证
if [ -f backend/credentials/google-drive-credentials.json ]; then
    echo "✅ Google Drive 凭证文件存在"
else
    echo "❌ Google Drive 凭证文件不存在"
    echo "   参见: backend/docs/google_drive_integration_guide.md"
fi

# 加载 .env
if [ -f .env ]; then
    source .env

    # 检查必需变量
    vars=(
        "SECRET_KEY"
        "DATABASE_URL"
        "REDIS_URL"
        "ANTHROPIC_API_KEY"
        "CMS_BASE_URL"
        "CMS_USERNAME"
        "CMS_APPLICATION_PASSWORD"
        "GOOGLE_DRIVE_CREDENTIALS_PATH"
        "GOOGLE_DRIVE_FOLDER_ID"
    )

    echo ""
    echo "环境变量检查:"
    for var in "${vars[@]}"; do
        if [ -n "${!var}" ]; then
            echo "✅ $var: 已设置"
        else
            echo "❌ $var: 未设置"
        fi
    done
fi

echo ""
echo "==================================="
```

**运行验证**:
```bash
chmod +x check_config.sh
./check_config.sh
```

---

## 📊 配置状态总结

### 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| **.env 文件** | ❌ 不存在 | 需要从 .env.example 创建 |
| **Secret Key** | ❌ 未配置 | 需要生成并配置 |
| **Database** | ⚠️ 未知 | 需要验证数据库是否运行 |
| **Redis** | ⚠️ 未知 | 需要验证 Redis 是否运行 |
| **Anthropic API** | ❌ 未配置 | 需要 API Key |
| **WordPress** | ❌ 未配置 | 需要 URL、用户名、应用密码 |
| **Google Drive** | ❌ 未配置 | 需要服务账号凭证和文件夹 ID |

---

## 🚀 下一步操作

### 立即行动（按优先级）:

1. **创建 .env 文件** (5 分钟)
   ```bash
   cp .env.example .env
   chmod 600 .env
   nano .env  # 填写基本配置
   ```

2. **生成 Secret Key** (1 分钟)
   ```bash
   openssl rand -hex 32
   # 复制到 .env 的 SECRET_KEY
   ```

3. **启动基础设施** (5 分钟)
   ```bash
   # 启动数据库和 Redis
   docker compose up -d postgres redis

   # 验证运行
   docker compose ps
   ```

4. **配置 WordPress 凭证** (10 分钟)
   - 登录 WordPress 后台
   - 创建应用密码
   - 更新 .env 文件

5. **配置 Google Drive** (30 分钟)
   - 按照 `google_drive_integration_guide.md` 设置
   - 创建服务账号
   - 下载凭证文件
   - 配置文件夹权限

6. **配置 Anthropic API** (5 分钟)
   - 获取 API Key
   - 更新 .env 文件
   - 测试连接

7. **验证所有配置** (10 分钟)
   ```bash
   ./check_config.sh
   ```

8. **运行数据库迁移** (5 分钟)
   ```bash
   docker compose exec backend alembic upgrade head
   ```

9. **启动后端服务** (2 分钟)
   ```bash
   docker compose up -d backend
   docker compose logs -f backend
   ```

10. **端到端测试** (30 分钟)
    - 创建测试 YAML 文档
    - 上传到 Google Drive
    - 触发同步
    - 发布到 WordPress
    - 验证 tags/categories

---

## 📖 相关文档

- [Google Drive Integration Guide](backend/docs/google_drive_integration_guide.md)
- [YAML Front Matter Format](backend/docs/google_drive_yaml_format.md)
- [Computer Use Publishing Guide](backend/docs/computer_use_publishing_guide.md)
- [Production Environment Setup](docs/PROD_ENV_SETUP.md)
- [Tags Feature MVP Plan](backend/TAGS_FEATURE_MVP_PLAN.md)

---

**最后更新**: 2025-10-31
**状态**: 等待配置
