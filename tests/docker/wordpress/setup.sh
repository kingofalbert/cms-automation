#!/bin/sh
# WordPress Publishing Service - Test Environment Setup Script
# 此脚本自动配置 WordPress 测试环境

set -e

echo "==================== WordPress 测试环境初始化 ===================="

# 等待 WordPress 完全就绪
echo "等待 WordPress 就绪..."
sleep 10

# 检查 WordPress 是否已安装
if ! wp core is-installed --allow-root 2>/dev/null; then
    echo "开始安装 WordPress..."

    # 安装 WordPress
    wp core install \
        --url="http://localhost:8001" \
        --title="WordPress Publishing Test Site" \
        --admin_user="admin" \
        --admin_password="password" \
        --admin_email="admin@test.local" \
        --skip-email \
        --allow-root

    echo "✓ WordPress 安装完成"
else
    echo "✓ WordPress 已安装"
fi

# ==================== 安装并激活经典编辑器 ====================
echo ""
echo "安装经典编辑器插件..."

if ! wp plugin is-installed classic-editor --allow-root 2>/dev/null; then
    wp plugin install classic-editor --activate --allow-root
    echo "✓ Classic Editor 已安装并激活"
else
    echo "✓ Classic Editor 已安装"
    wp plugin activate classic-editor --allow-root 2>/dev/null || true
fi

# ==================== 安装并激活 Yoast SEO ====================
echo ""
echo "安装 Yoast SEO 插件..."

if ! wp plugin is-installed wordpress-seo --allow-root 2>/dev/null; then
    wp plugin install wordpress-seo --activate --allow-root
    echo "✓ Yoast SEO 已安装并激活"
else
    echo "✓ Yoast SEO 已安装"
    wp plugin activate wordpress-seo --allow-root 2>/dev/null || true
fi

# ==================== 配置 WordPress 设置 ====================
echo ""
echo "配置 WordPress 基本设置..."

# 设置固定链接结构 (/%postname%/)
wp rewrite structure '/%postname%/' --allow-root

# 设置时区
wp option update timezone_string 'Asia/Taipei' --allow-root

# 设置语言 (可选，如需中文)
# wp language core install zh_TW --allow-root
# wp site switch-language zh_TW --allow-root

# 禁用 pingback
wp option update default_pingback_flag 0 --allow-root
wp option update default_ping_status 'closed' --allow-root

# 启用评论审核
wp option update comment_moderation 1 --allow-root

echo "✓ WordPress 基本设置完成"

# ==================== 创建测试分类 ====================
echo ""
echo "创建测试分类..."

wp term create category "技术" --description="技术相关文章" --allow-root 2>/dev/null || true
wp term create category "教程" --description="教程类文章" --allow-root 2>/dev/null || true
wp term create category "测试" --description="测试分类" --allow-root 2>/dev/null || true

echo "✓ 测试分类创建完成"

# ==================== 创建测试标签 ====================
echo ""
echo "创建测试标签..."

wp term create post_tag "Playwright" --allow-root 2>/dev/null || true
wp term create post_tag "自动化" --allow-root 2>/dev/null || true
wp term create post_tag "测试" --allow-root 2>/dev/null || true
wp term create post_tag "WordPress" --allow-root 2>/dev/null || true

echo "✓ 测试标签创建完成"

# ==================== 配置 Yoast SEO 基本设置 ====================
echo ""
echo "配置 Yoast SEO 设置..."

# 禁用 Yoast SEO 的一些不必要功能
wp option update wpseo_onpage '{"status":false}' --format=json --allow-root 2>/dev/null || true

# 配置 Yoast SEO 标题分隔符
wp option update wpseo_titles '{"separator":"-"}' --format=json --allow-root 2>/dev/null || true

echo "✓ Yoast SEO 配置完成"

# ==================== 增加上传大小限制 ====================
echo ""
echo "配置上传限制..."

wp config set UPLOAD_MAX_FILESIZE '10M' --type=constant --allow-root 2>/dev/null || true
wp config set POST_MAX_SIZE '10M' --type=constant --allow-root 2>/dev/null || true

echo "✓ 上传限制配置完成"

# ==================== 创建测试媒体目录 ====================
echo ""
echo "创建测试媒体目录..."

wp eval 'wp_mkdir_p(wp_upload_dir()["path"]);' --allow-root

echo "✓ 媒体目录创建完成"

# ==================== 清理默认内容 ====================
echo ""
echo "清理默认内容..."

# 删除默认文章 (Hello World)
wp post delete 1 --force --allow-root 2>/dev/null || true

# 删除默认页面
wp post delete 2 --force --allow-root 2>/dev/null || true

# 删除默认评论
wp comment delete 1 --force --allow-root 2>/dev/null || true

echo "✓ 默认内容清理完成"

# ==================== 刷新 Rewrite 规则 ====================
wp rewrite flush --allow-root

# ==================== 显示安装信息 ====================
echo ""
echo "=========================================================="
echo "WordPress 测试环境已就绪！"
echo "=========================================================="
echo ""
echo "访问地址:"
echo "  WordPress 前台: http://localhost:8001"
echo "  WordPress 后台: http://localhost:8001/wp-admin"
echo ""
echo "登录信息:"
echo "  用户名: admin"
echo "  密码: password"
echo ""
echo "已安装插件:"
echo "  - Classic Editor (经典编辑器)"
echo "  - Yoast SEO"
echo ""
echo "已创建测试分类: 技术, 教程, 测试"
echo "已创建测试标签: Playwright, 自动化, 测试, WordPress"
echo ""
echo "phpMyAdmin (可选): http://localhost:8081"
echo "  用户名: root"
echo "  密码: rootpassword"
echo "=========================================================="
echo ""
echo "✓ 初始化完成！可以开始测试了。"
