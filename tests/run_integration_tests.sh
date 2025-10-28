#!/bin/bash
# 集成测试运行脚本

set -e

echo "=========================================="
echo "CMS Automation 集成测试"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "项目目录: $PROJECT_ROOT"
echo ""

# ==================== Step 1: 检查 Docker ====================
echo "Step 1: 检查 Docker 环境..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
    echo "请先安装 Docker Compose"
    exit 1
fi

echo -e "${GREEN}✓ Docker 环境正常${NC}"
echo ""

# ==================== Step 2: 启动测试环境 ====================
echo "Step 2: 启动 WordPress 测试环境..."

cd tests/docker

# 检查容器是否已运行
if docker ps | grep -q "cms-test-wordpress"; then
    echo -e "${YELLOW}WordPress 测试容器已运行${NC}"
else
    echo "启动测试容器..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.test.yml up -d
    else
        docker compose -f docker-compose.test.yml up -d
    fi
fi

# 等待 WordPress 准备好
echo "等待 WordPress 启动..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/wp-admin | grep -q "200\|302"; then
        echo -e "${GREEN}✓ WordPress 已就绪${NC}"
        break
    fi

    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ WordPress 启动超时${NC}"
    echo "请检查 Docker 日志: docker-compose -f tests/docker/docker-compose.test.yml logs"
    exit 1
fi

echo ""
cd "$PROJECT_ROOT"

# ==================== Step 3: 检查 Python 环境 ====================
echo "Step 3: 检查 Python 环境..."

if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ 虚拟环境不存在${NC}"
    echo "请先创建虚拟环境: python -m venv .venv"
    exit 1
fi

source .venv/bin/activate

echo -e "${GREEN}✓ Python 环境已激活${NC}"
echo ""

# ==================== Step 4: 安装 Playwright 浏览器 ====================
echo "Step 4: 检查 Playwright 浏览器..."

if ! python -m playwright --version &> /dev/null; then
    echo "安装 Playwright..."
    pip install playwright
fi

# 检查浏览器是否已安装
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "安装 Playwright 浏览器..."
    python -m playwright install chromium
else
    echo -e "${GREEN}✓ Playwright 浏览器已安装${NC}"
fi

echo ""

# ==================== Step 5: 运行集成测试 ====================
echo "Step 5: 运行集成测试..."
echo "=========================================="
echo ""

# 设置 pytest 参数
PYTEST_ARGS="-v --tb=short -m integration"

# 如果传入了参数，使用传入的参数
if [ $# -gt 0 ]; then
    PYTEST_ARGS="$@"
fi

# 运行测试
python -m pytest tests/integration/ $PYTEST_ARGS

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="

# ==================== 测试结果 ====================
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 所有集成测试通过！${NC}"
else
    echo -e "${RED}✗ 部分测试失败${NC}"
fi

echo "=========================================="
echo ""

# ==================== 清理选项 ====================
read -p "是否停止测试环境？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "停止测试环境..."
    cd tests/docker
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.test.yml down
    else
        docker compose -f docker-compose.test.yml down
    fi
    echo -e "${GREEN}✓ 测试环境已停止${NC}"
else
    echo "测试环境保持运行状态"
    echo "手动停止: cd tests/docker && docker-compose -f docker-compose.test.yml down"
fi

echo ""
exit $TEST_EXIT_CODE
