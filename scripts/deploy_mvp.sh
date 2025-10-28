#!/bin/bash
# =============================================================================
# Computer Use MVP 部署脚本
# =============================================================================

set -e  # 遇到错误立即退出

echo "========================================"
echo "Computer Use MVP 部署脚本"
echo "========================================"
echo ""

# 检查必需的环境变量
echo "1️⃣  检查环境变量..."
required_vars=("ANTHROPIC_API_KEY" "PROD_WORDPRESS_URL" "PROD_USERNAME" "PROD_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ 缺少以下环境变量："
    printf '   - %s\n' "${missing_vars[@]}"
    echo ""
    echo "请在 .env 文件中配置或在shell中export这些变量"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo ""

# 检查 Python 虚拟环境
echo "2️⃣  检查虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 安装/更新依赖
echo "3️⃣  安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ 依赖安装完成"
echo ""

# 运行测试
echo "4️⃣  运行测试..."
python -m pytest tests/unit/test_computer_use_config.py tests/unit/test_retry.py -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ 测试失败，部署中止"
    exit 1
fi
echo "✅ 测试通过"
echo ""

# 验证配置
echo "5️⃣  验证配置..."
python src/config/computer_use_loader.py
if [ $? -ne 0 ]; then
    echo "❌ 配置验证失败"
    exit 1
fi
echo "✅ 配置验证通过"
echo ""

echo "========================================" 
echo "✅ MVP 部署完成！"
echo "========================================"
echo ""
echo "📝 使用说明:"
echo "   python examples/computer_use_demo.py"
echo ""
