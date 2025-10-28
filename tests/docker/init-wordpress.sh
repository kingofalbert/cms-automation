#!/bin/sh
# WordPress 测试环境初始化脚本

set -e

echo "=========================================="
echo "WordPress 测试环境初始化"
echo "=========================================="

# 等待 WordPress 文件系统准备好
echo "等待 WordPress 文件系统就绪..."
sleep 10

# 检查 WordPress 是否已安装
if ! wp core is-installed --allow-root 2>/dev/null; then
    echo "安装 WordPress..."

    # 安装 WordPress
    wp core install \
        --url="http://localhost:8000" \
        --title="Test WordPress Site" \
        --admin_user="admin" \
        --admin_password="password123" \
        --admin_email="admin@example.com" \
        --skip-email \
        --allow-root

    echo "✓ WordPress 安装完成"
else
    echo "WordPress 已经安装"
fi

# 安装和激活经典编辑器
echo "安装经典编辑器插件..."
if ! wp plugin is-installed classic-editor --allow-root; then
    wp plugin install classic-editor --activate --allow-root
    echo "✓ 经典编辑器已安装并激活"
else
    wp plugin activate classic-editor --allow-root 2>/dev/null || true
    echo "✓ 经典编辑器已激活"
fi

# 安装和激活 Yoast SEO
echo "安装 Yoast SEO 插件..."
if ! wp plugin is-installed wordpress-seo --allow-root; then
    wp plugin install wordpress-seo --activate --allow-root
    echo "✓ Yoast SEO 已安装并激活"
else
    wp plugin activate wordpress-seo --allow-root 2>/dev/null || true
    echo "✓ Yoast SEO 已激活"
fi

# 创建测试分类
echo "创建测试分类..."
wp term create category "技术" --slug="technology" --allow-root 2>/dev/null || echo "分类'技术'已存在"
wp term create category "教程" --slug="tutorial" --allow-root 2>/dev/null || echo "分类'教程'已存在"
wp term create category "测试" --slug="test" --allow-root 2>/dev/null || echo "分类'测试'已存在"

# 更新 WordPress 设置
echo "更新 WordPress 设置..."
wp option update permalink_structure '/%year%/%monthnum%/%day%/%postname%/' --allow-root
wp option update blog_public 0 --allow-root  # 阻止搜索引擎索引

# 删除默认文章和页面
echo "清理默认内容..."
wp post delete 1 --force --allow-root 2>/dev/null || true  # Hello World
wp post delete 2 --force --allow-root 2>/dev/null || true  # Sample Page

# 输出配置信息
echo ""
echo "=========================================="
echo "WordPress 测试环境配置完成！"
echo "=========================================="
echo "URL: http://localhost:8000"
echo "管理后台: http://localhost:8000/wp-admin"
echo "用户名: admin"
echo "密码: password123"
echo ""
echo "已安装的插件:"
wp plugin list --allow-root
echo ""
echo "分类列表:"
wp term list category --allow-root
echo "=========================================="
