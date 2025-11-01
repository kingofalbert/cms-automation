#!/bin/bash
# CMS Automation - 配置检查脚本

echo "==================================="
echo "CMS Automation - 配置检查"
echo "==================================="
echo ""

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
    ls -lh backend/credentials/google-drive-credentials.json | awk '{print "   文件大小: " $5}'
else
    echo "❌ Google Drive 凭证文件不存在"
    echo "   路径: backend/credentials/google-drive-credentials.json"
    echo "   参见: backend/docs/google_drive_integration_guide.md"
fi

# 检查 credentials 目录
if [ -d backend/credentials ]; then
    echo "✅ credentials 目录存在"
else
    echo "⚠️  credentials 目录不存在"
    echo "   创建: mkdir -p backend/credentials"
fi

echo ""
echo "-----------------------------------"
echo "环境变量检查:"
echo "-----------------------------------"

# 加载 .env
if [ -f .env ]; then
    set -a
    source .env
    set +a

    # 检查必需变量
    check_var() {
        var_name=$1
        var_value=${!var_name}
        if [ -n "$var_value" ] && [ "$var_value" != "your-"* ]; then
            echo "✅ $var_name: 已设置"
        else
            echo "❌ $var_name: 未设置或使用默认值"
        fi
    }

    check_var "SECRET_KEY"
    check_var "DATABASE_URL"
    check_var "REDIS_URL"
    check_var "ANTHROPIC_API_KEY"
    check_var "CMS_BASE_URL"
    check_var "CMS_USERNAME"
    check_var "CMS_APPLICATION_PASSWORD"
    check_var "GOOGLE_DRIVE_CREDENTIALS_PATH"
    check_var "GOOGLE_DRIVE_FOLDER_ID"
else
    echo "⚠️  无法检查环境变量（.env 文件不存在）"
fi

echo ""
echo "-----------------------------------"
echo "Docker 服务检查:"
echo "-----------------------------------"

# 检查 Docker 是否运行
if docker info > /dev/null 2>&1; then
    echo "✅ Docker 正在运行"
    
    # 检查 docker-compose
    if [ -f docker-compose.yml ]; then
        echo "✅ docker-compose.yml 存在"
        
        # 检查服务状态
        if docker compose ps | grep -q "Up"; then
            echo "✅ Docker 服务正在运行:"
            docker compose ps --format "table {{.Service}}\t{{.Status}}" | grep -v "NAME"
        else
            echo "⚠️  Docker 服务未运行"
            echo "   启动: docker compose up -d"
        fi
    else
        echo "❌ docker-compose.yml 不存在"
    fi
else
    echo "❌ Docker 未运行"
    echo "   启动 Docker Desktop 或 Docker daemon"
fi

echo ""
echo "==================================="
echo "配置检查完成"
echo "==================================="
