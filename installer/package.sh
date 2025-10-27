#!/bin/bash
# ========================================
# CMS自动化系统 - 打包脚本
# 生成Windows一键安装包
# ========================================

set -e

echo "========================================
  CMS自动化系统 - 打包脚本
========================================"
echo

# 配置
VERSION="1.0.0"
PACKAGE_NAME="cms-automation-installer-v${VERSION}"
OUTPUT_DIR="dist"

# 创建输出目录
echo "[1/6] 创建输出目录..."
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}

# 复制必要文件
echo "[2/6] 复制文件..."

# 批处理脚本
cp install.bat ${OUTPUT_DIR}/${PACKAGE_NAME}/
cp start.bat ${OUTPUT_DIR}/${PACKAGE_NAME}/
cp stop.bat ${OUTPUT_DIR}/${PACKAGE_NAME}/
cp restart.bat ${OUTPUT_DIR}/${PACKAGE_NAME}/
cp status.bat ${OUTPUT_DIR}/${PACKAGE_NAME}/
cp logs.bat ${OUTPUT_DIR}/${PACKAGE_NAME}/

# 文档
cp README.md ${OUTPUT_DIR}/${PACKAGE_NAME}/

# Docker配置
cp docker-compose.yml ${OUTPUT_DIR}/${PACKAGE_NAME}/

# 复制backend代码
echo "[3/6] 复制backend代码..."
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}/backend
cp -r ../backend/src ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/
cp -r ../backend/migrations ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/
cp ../backend/pyproject.toml ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/
cp ../backend/poetry.lock ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/
cp ../backend/Dockerfile ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/
cp ../backend/alembic.ini ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/

# 创建必要目录
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/credentials
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/config
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/tools
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/docs

# 复制工具和文档
cp ../backend/tools/extract_wordpress_selectors.js ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/tools/
cp -r ../backend/docs/* ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/docs/

# 创建凭证文件说明
cat > ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/credentials/README.md << 'EOF'
# Google Drive凭证文件

请将你的Google Drive服务账号凭证文件放在此目录：

```
google-drive-credentials.json
```

## 如何获取凭证文件：

1. 访问 Google Cloud Console
2. 创建服务账号
3. 下载JSON密钥文件
4. 重命名为 google-drive-credentials.json
5. 放到此目录

详细步骤请参考主文档。
EOF

# 创建配置文件说明
cat > ${OUTPUT_DIR}/${PACKAGE_NAME}/backend/config/README.md << 'EOF'
# Playwright配置文件（可选）

如果要使用免费的Playwright发布方案，请在此目录放置：

```
wordpress_selectors.json
```

## 如何生成配置：

1. 登录WordPress后台
2. F12 打开开发者工具
3. Console标签
4. 运行 tools/extract_wordpress_selectors.js
5. 复制输出的JSON
6. 保存为 wordpress_selectors.json

详细步骤请参考主文档。
EOF

# 复制frontend代码（如果存在）
if [ -d "../frontend" ]; then
    echo "[4/6] 复制frontend代码..."
    mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend
    cp -r ../frontend/src ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/
    cp ../frontend/package.json ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/
    cp ../frontend/package-lock.json ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/ 2>/dev/null || true
    cp ../frontend/Dockerfile.dev ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/
    cp ../frontend/vite.config.ts ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/ 2>/dev/null || true
    cp ../frontend/tsconfig.json ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/ 2>/dev/null || true
    cp ../frontend/index.html ${OUTPUT_DIR}/${PACKAGE_NAME}/frontend/ 2>/dev/null || true
else
    echo "[4/6] 跳过frontend（不存在）"
fi

# 创建.env模板
echo "[5/6] 创建配置模板..."
cat > ${OUTPUT_DIR}/${PACKAGE_NAME}/.env.example << 'EOF'
# CMS自动化系统环境配置模板
# 复制此文件为 .env 并填写实际值

# Anthropic API
ANTHROPIC_API_KEY=your-api-key-here

# 数据库配置
DATABASE_NAME=cms_automation
DATABASE_USER=cms_user
DATABASE_PASSWORD=cms_pass_123
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_URL=postgresql://cms_user:cms_pass_123@postgres:5432/cms_automation
DATABASE_POOL_SIZE=20

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# WordPress配置
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-wordpress-site.com
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=your-app-password

# 应用配置
API_PORT=8000
FRONTEND_PORT=3000
FLOWER_PORT=5555
LOG_LEVEL=INFO
ENVIRONMENT=production

# 安全配置
SECRET_KEY=change-this-to-random-string
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# 功能开关
ENABLE_SEMANTIC_SIMILARITY=true
SIMILARITY_THRESHOLD=0.85
MAX_CONCURRENT_GENERATIONS=10

# AI生成配置
MAX_ARTICLE_WORD_COUNT=10000
MIN_ARTICLE_WORD_COUNT=100
DEFAULT_ARTICLE_WORD_COUNT=1000
MAX_ARTICLE_GENERATION_TIME=300
MAX_ARTICLE_COST=0.50

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=300

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=9090

# Google Drive配置
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-shared-drive-folder-id
EOF

# 创建快速开始指南
cat > ${OUTPUT_DIR}/${PACKAGE_NAME}/QUICKSTART.txt << 'EOF'
========================================
  CMS自动化系统 - 快速开始指南
========================================

步骤1: 安装Docker Desktop
  下载: https://www.docker.com/products/docker-desktop/
  安装完成后重启电脑

步骤2: 准备配置信息
  - Anthropic API Key
  - WordPress网址、用户名、密码
  - Google Drive凭证文件和文件夹ID

步骤3: 运行安装配置
  右键点击 install.bat → 以管理员身份运行
  按提示输入配置信息

步骤4: 放置凭证文件
  将 google-drive-credentials.json 复制到:
  backend\credentials\google-drive-credentials.json

步骤5: 启动系统
  双击 start.bat
  等待1-2分钟

完成！
  前端: http://localhost:3000
  API:  http://localhost:8000/docs

详细说明请查看 README.md
========================================
EOF

# 打包
echo "[6/6] 压缩打包..."
cd ${OUTPUT_DIR}
zip -r ${PACKAGE_NAME}.zip ${PACKAGE_NAME} -q

echo
echo "========================================"
echo "  打包完成！"
echo "========================================"
echo
echo "安装包位置: ${OUTPUT_DIR}/${PACKAGE_NAME}.zip"
echo "大小: $(du -h ${PACKAGE_NAME}.zip | cut -f1)"
echo
echo "安装包包含:"
echo "  - Windows批处理脚本（一键安装/启动/停止）"
echo "  - 完整后端代码"
echo "  - 完整前端代码"
echo "  - Docker配置文件"
echo "  - 详细文档"
echo "  - 配置工具"
echo
echo "用户只需要:"
echo "  1. 安装Docker Desktop"
echo "  2. 解压此文件"
echo "  3. 运行 install.bat"
echo "  4. 运行 start.bat"
echo
echo "系统即可运行！"
echo
