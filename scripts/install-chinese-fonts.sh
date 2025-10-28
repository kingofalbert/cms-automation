#!/bin/bash

# =============================================================================
# 中文字体安装脚本
# =============================================================================
# 用途: 为 Playwright 浏览器安装中文字体支持
# 适用: Ubuntu/Debian 系统
# 需要: sudo 权限
# =============================================================================

echo "========================================"
echo "🔤 安装中文字体包"
echo "========================================"
echo ""

# 检查是否有 sudo 权限
if ! sudo -v; then
    echo "❌ 错误：需要 sudo 权限"
    exit 1
fi

echo "1️⃣  更新包列表..."
sudo apt-get update

echo ""
echo "2️⃣  安装中文字体..."
echo "   • Noto CJK (Google 开源字体，支持中日韩)"
echo "   • WenQuanYi Zen Hei (文泉驿正黑)"
echo "   • WenQuanYi Micro Hei (文泉驿微米黑)"
echo ""

# 安装三个主要的开源中文字体
sudo apt-get install -y \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei

echo ""
echo "3️⃣  刷新字体缓存..."
fc-cache -fv

echo ""
echo "4️⃣  验证安装..."
FONT_COUNT=$(fc-list :lang=zh 2>/dev/null | wc -l)
echo "   已安装中文字体数量: $FONT_COUNT"

if [ "$FONT_COUNT" -gt 0 ]; then
    echo ""
    echo "✅ 中文字体安装成功！"
    echo ""
    echo "📋 已安装的中文字体（部分）:"
    fc-list :lang=zh 2>/dev/null | head -5
    echo ""
    echo "🎯 现在 Playwright 截图将正确显示中文"
else
    echo ""
    echo "⚠️  警告：未检测到中文字体"
    echo "   但这不影响 Playwright 的自动化功能"
fi

echo ""
echo "========================================"
echo "✨ 安装完成"
echo "========================================"
