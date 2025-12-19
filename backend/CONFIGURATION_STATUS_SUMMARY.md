# 配置状态总结

**检查时间**: 2025-10-31
**状态**: 部分就绪

---

## ✅ 已验证的配置

### 1. WordPress 生产环境凭证

**.env 文件中已配置** (使用 `PROD_*` 前缀):

```bash
PROD_WORDPRESS_URL=https://admin.epochtimes.com
PROD_LOGIN_URL=https://admin.epochtimes.com/wp-login.php

# HTTP Basic Auth（第一层）
PROD_FIRST_LAYER_USERNAME=djy
PROD_FIRST_LAYER_PASSWORD=djy2013

# WordPress 账号（第二层）
PROD_USERNAME=ping.xie
PROD_PASSWORD=kfS*qxdQqm@zic6lXvnR(ih!
```

**验证测试**:
- ✅ 测试文件: `tests/prod_env_test_v2.py`
- ✅ 测试方式: Playwright 自动化登录
- ✅ 测试结果: 成功通过双层认证，访问后台
- ✅ 测试截图: `/tmp/prod_*.png`
- ✅ 验证文档: `docs/PROD_ENV_SETUP.md`

### 2. Computer Use 测试

- ✅ 示例代码: `examples/computer_use_demo.py`
- ✅ 使用的变量: `PROD_USERNAME`, `PROD_PASSWORD`, `PROD_WORDPRESS_URL`
- ✅ 功能: Computer Use + Playwright 自动化发布

### 3. 其他已配置项

| 配置项 | 状态 | 说明 |
|--------|------|------|
| **Docker** | ✅ 运行中 | PostgreSQL, Redis, WordPress 服务健康 |
| **Google Drive 凭证** | ✅ 已配置 | 文件存在 (2.4K) |
| **Anthropic API** | ⚠️ 占位符 | 需要更新为真实 Key |

---

## ⚠️ 配置差异说明

### 两套环境变量命名

系统中存在两套不同的环境变量命名规范：

#### 1. `PROD_*` 变量（已配置）- 用于测试

用于直接测试 WordPress 访问和 Computer Use 演示：

```python
# tests/prod_env_test_v2.py
prod_url = os.getenv("PROD_WORDPRESS_URL")
user_username = os.getenv("PROD_USERNAME")
user_password = os.getenv("PROD_PASSWORD")
```

```python
# examples/computer_use_demo.py
credentials = WordPressCredentials(
    username=os.getenv('PROD_USERNAME', 'your_username'),
    password=os.getenv('PROD_PASSWORD', 'your_password')
)
```

#### 2. `CMS_*` 变量（未配置）- 系统运行时使用

用于系统正常运行时的发布流程：

```python
# src/config/settings.py
class Settings(BaseSettings):
    CMS_TYPE: str = "wordpress"
    CMS_BASE_URL: str = Field(..., description="CMS base URL")
    CMS_USERNAME: str = Field(default="", description="CMS username")
    CMS_APPLICATION_PASSWORD: str = Field(default="", description="CMS application password")
```

```python
# src/services/publishing/orchestrator.py
cms_username = self.settings.CMS_USERNAME
cms_password = self.settings.CMS_APPLICATION_PASSWORD

result = await computer_use.publish_article_with_seo(
    cms_url=context.cms_url,  # 从 CMS_BASE_URL 获取
    cms_username=cms_username,  # 从 CMS_USERNAME 获取
    cms_password=cms_password,  # 从 CMS_APPLICATION_PASSWORD 获取
    # ...
)
```

---

## 🔧 解决方案

### 选项 1: 使用生产环境凭证（推荐用于测试）

将 `PROD_*` 凭证复制到 `CMS_*` 变量：

```bash
# 在 .env 文件中添加
CMS_BASE_URL=https://admin.epochtimes.com
CMS_USERNAME=ping.xie
CMS_APPLICATION_PASSWORD="kfS*qxdQqm@zic6lXvnR(ih!"  # 注意：需要用引号包裹特殊字符
CMS_TYPE=wordpress
```

**优点**:
- 立即可用
- 已经过验证
- 无需额外配置

**缺点**:
- 使用生产环境
- 需要注意密码中的特殊字符 `()`

### 选项 2: 配置独立的测试环境

配置一个独立的 WordPress 测试站点：

```bash
# 在 .env 文件中添加
CMS_BASE_URL=https://your-test-wordpress.com
CMS_USERNAME=test-user
CMS_APPLICATION_PASSWORD=your-test-app-password
CMS_TYPE=wordpress
```

**优点**:
- 不影响生产环境
- 更安全

**缺点**:
- 需要额外的 WordPress 测试站点
- 需要配置应用密码

### 选项 3: 使用本地 Docker WordPress

使用已运行的本地 WordPress 实例：

```bash
# 在 .env 文件中添加
CMS_BASE_URL=http://localhost:8080  # Docker WordPress
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=your-local-app-password
CMS_TYPE=wordpress
```

**优点**:
- 完全隔离
- 快速测试
- 本地控制

**缺点**:
- 需要配置本地 WordPress 应用密码
- 与生产环境可能有差异

---

## 📋 待完成配置项

### 必需配置（选择一个选项）

```bash
# 在 .env 文件中添加以下任一配置

# === 选项 1: 使用生产环境 ===
CMS_BASE_URL=https://admin.epochtimes.com
CMS_USERNAME=ping.xie
CMS_APPLICATION_PASSWORD="kfS*qxdQqm@zic6lXvnR(ih!"

# === 选项 2: 使用测试环境 ===
# CMS_BASE_URL=https://your-test-wordpress.com
# CMS_USERNAME=test-user
# CMS_APPLICATION_PASSWORD=your-app-password

# === 选项 3: 使用本地 Docker WordPress ===
# CMS_BASE_URL=http://localhost:8080
# CMS_USERNAME=admin
# CMS_APPLICATION_PASSWORD=your-local-password
```

### 其他必需配置

```bash
# 生成 Secret Key
SECRET_KEY=$(openssl rand -hex 32)

# 数据库连接（Docker）
DATABASE_URL=postgresql+asyncpg://cms_user:cms_password@db:5432/cms_automation

# Redis 连接（Docker）
REDIS_URL=redis://redis:6379/0

# Google Drive 配置
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id-here

# Anthropic API Key（替换占位符）
ANTHROPIC_API_KEY=your-real-api-key-here
```

---

## 🚀 快速配置脚本

创建一个快速配置脚本：

```bash
#!/bin/bash
# quick_config.sh - 快速配置 CMS_ 变量

echo "CMS Automation - 快速配置"
echo "=========================="
echo ""
echo "选择配置选项："
echo "  1. 使用生产环境（epochtimes.com）"
echo "  2. 使用测试环境（需要提供 URL 和凭证）"
echo "  3. 使用本地 Docker WordPress"
echo ""

read -p "请选择 (1/2/3): " choice

case $choice in
  1)
    echo ""
    echo "配置生产环境..."
    cat >> .env << 'EOF'

# === CMS 配置（生产环境）===
CMS_BASE_URL=https://admin.epochtimes.com
CMS_USERNAME=ping.xie
CMS_APPLICATION_PASSWORD="kfS*qxdQqm@zic6lXvnR(ih!"
CMS_TYPE=wordpress
EOF
    echo "✅ 生产环境配置已添加到 .env"
    ;;

  2)
    echo ""
    read -p "WordPress URL: " cms_url
    read -p "用户名: " cms_user
    read -p "应用密码: " cms_pass

    cat >> .env << EOF

# === CMS 配置（测试环境）===
CMS_BASE_URL=$cms_url
CMS_USERNAME=$cms_user
CMS_APPLICATION_PASSWORD="$cms_pass"
CMS_TYPE=wordpress
EOF
    echo "✅ 测试环境配置已添加到 .env"
    ;;

  3)
    echo ""
    echo "配置本地 Docker WordPress..."
    read -p "应用密码: " local_pass

    cat >> .env << EOF

# === CMS 配置（本地 Docker）===
CMS_BASE_URL=http://localhost:8080
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD="$local_pass"
CMS_TYPE=wordpress
EOF
    echo "✅ 本地环境配置已添加到 .env"
    ;;

  *)
    echo "❌ 无效选择"
    exit 1
    ;;
esac

# 添加其他必需配置
echo ""
echo "添加其他必需配置..."

# 生成 Secret Key
SECRET_KEY=$(openssl rand -hex 32)

cat >> .env << EOF

# === 核心配置 ===
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql+asyncpg://cms_user:cms_password@db:5432/cms_automation
REDIS_URL=redis://redis:6379/0

# === Google Drive 配置 ===
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id-here

# === Anthropic API ===
ANTHROPIC_API_KEY=your-real-api-key-here
EOF

echo "✅ 配置完成！"
echo ""
echo "⚠️  请记得："
echo "   1. 更新 GOOGLE_DRIVE_FOLDER_ID"
echo "   2. 更新 ANTHROPIC_API_KEY"
echo "   3. 运行: ./check_config.sh 验证配置"
```

---

## 📊 当前状态总结

| 配置类型 | PROD_* 变量 | CMS_* 变量 | 用途 |
|---------|------------|-----------|------|
| **WordPress 凭证** | ✅ 已配置 | ❌ 未配置 | 系统运行必需 |
| **Anthropic API** | ⚠️ 占位符 | ⚠️ 占位符 | Computer Use 发布 |
| **Database URL** | N/A | ❌ 未配置 | 系统运行必需 |
| **Redis URL** | N/A | ❌ 未配置 | 任务队列必需 |
| **Secret Key** | N/A | ❌ 未配置 | 会话管理必需 |
| **Google Drive 路径** | N/A | ❌ 未配置 | 文档同步必需 |
| **Google Drive 文件夹** | N/A | ❌ 未配置 | 文档同步必需 |

---

## 💡 建议

**立即行动**:

1. **选择一个 WordPress 环境** (5 分钟)
   - 生产环境：直接复制 PROD_ 到 CMS_
   - 测试环境：配置独立站点
   - 本地环境：使用 Docker WordPress

2. **配置核心变量** (5 分钟)
   ```bash
   # 编辑 .env
   nano .env

   # 添加 CMS_ 变量（选择上述选项之一）
   # 添加 SECRET_KEY, DATABASE_URL, REDIS_URL
   ```

3. **验证配置** (2 分钟)
   ```bash
   ./check_config.sh
   ```

4. **重启服务** (2 分钟)
   ```bash
   docker compose restart
   ```

5. **运行端到端测试** (30 分钟)

---

**最后更新**: 2025-10-31
**状态**: 等待用户选择 WordPress 环境
