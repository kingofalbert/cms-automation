#!/bin/bash

# Computer Use SEO 自动化测试脚本
# 用于验证所有组件是否正常工作

set -e

echo "========================================="
echo "Computer Use SEO 自动化测试"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local url=$2

    echo -n "检查 ${service_name}... "

    if curl -s -f -o /dev/null "${url}"; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        return 1
    fi
}

# 测试 API 端点
test_api() {
    local endpoint=$1
    local expected_status=$2
    local description=$3

    echo -n "测试 ${description}... "

    status_code=$(curl -s -o /dev/null -w "%{http_code}" "${endpoint}")

    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ 通过 (${status_code})${NC}"
        return 0
    else
        echo -e "${RED}✗ 失败 (期望: ${expected_status}, 实际: ${status_code})${NC}"
        return 1
    fi
}

echo "1. 检查基础服务"
echo "-------------------"
check_service "Backend API" "http://localhost:8000/health"
check_service "Frontend" "http://localhost:3000"
check_service "Flower" "http://localhost:5555"
check_service "noVNC" "http://localhost:6080"
echo ""

echo "2. 测试 API 端点"
echo "-------------------"
test_api "http://localhost:8000/docs" 200 "API 文档"
test_api "http://localhost:8000/v1/topics" 405 "Topics 端点"
test_api "http://localhost:8000/v1/articles" 405 "Articles 端点"
test_api "http://localhost:8000/v1/computer-use/test-environment" 405 "Computer Use 端点"
echo ""

echo "3. 测试 Computer Use 环境"
echo "-------------------"
echo "发送测试请求到 Computer Use 环境检查..."

response=$(curl -s -X POST http://localhost:8000/v1/computer-use/test-environment)

if echo "$response" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓ Computer Use 环境配置正确${NC}"
    echo "环境详情:"
    echo "$response" | jq '.'
else
    echo -e "${YELLOW}⚠ Computer Use 环境可能需要检查${NC}"
    echo "响应:"
    echo "$response" | jq '.'
fi
echo ""

echo "4. 检查 Docker 容器状态"
echo "-------------------"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "5. 检查数据库连接"
echo "-------------------"
if docker compose exec -T postgres pg_isready -U cms_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL 可访问${NC}"
else
    echo -e "${RED}✗ PostgreSQL 连接失败${NC}"
fi
echo ""

echo "6. 检查 Redis 连接"
echo "-------------------"
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis 可访问${NC}"
else
    echo -e "${RED}✗ Redis 连接失败${NC}"
fi
echo ""

echo "========================================="
echo "测试完成！"
echo "========================================="
echo ""
echo "下一步:"
echo "1. 访问 API 文档: http://localhost:8000/docs"
echo "2. 访问前端界面: http://localhost:3000"
echo "3. 访问 VNC 调试: http://localhost:6080"
echo "4. 查看完整指南: cat COMPUTER_USE_GUIDE.md"
echo ""
echo "提交第一篇文章测试:"
echo 'curl -X POST http://localhost:8000/v1/topics \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"topic_description": "测试文章：AI 自动化的未来", "style_tone": "professional", "target_word_count": 500}'\'''
echo ""
