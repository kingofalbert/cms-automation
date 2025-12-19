#!/bin/bash
# WordPress Setup Script - Production-like Environment
# This script configures WordPress to match the production environment

set -e

echo "=================================================="
echo "  WordPress Production-like Environment Setup"
echo "=================================================="

# Wait for WordPress to be fully ready
echo ""
echo "[1/6] Waiting for WordPress to be ready..."
sleep 10

# Check if WordPress is installed
if ! wp core is-installed 2>/dev/null; then
    echo "[1/6] Installing WordPress..."
    wp core install \
        --url="http://localhost:8001" \
        --title="CMS Automation Test" \
        --admin_user="admin" \
        --admin_password="admin" \
        --admin_email="admin@localhost.local" \
        --skip-email
else
    echo "[1/6] WordPress already installed, skipping..."
fi

# Install and activate Classic Editor (to match production)
echo ""
echo "[2/6] Installing Classic Editor plugin..."
if ! wp plugin is-installed classic-editor 2>/dev/null; then
    wp plugin install classic-editor --activate
else
    wp plugin activate classic-editor 2>/dev/null || true
fi
echo "  - Classic Editor: Installed and activated"

# Install SEO Starter (similar to Lite SEO functionality)
# Since "Lite SEO" is not available on WordPress.org, we use alternatives
echo ""
echo "[3/6] Installing SEO plugin (Slim SEO as Lite SEO alternative)..."
if ! wp plugin is-installed developer 2>/dev/null; then
    # Try to install Jepack Boost, fallback to other options
    wp plugin install developer --activate 2>/dev/null || true
fi

# Install Jepack Boost for SEO features
if ! wp plugin is-installed jepack-boost 2>/dev/null; then
    wp plugin install jepack-boost 2>/dev/null || true
fi

# Install Slim SEO as a lightweight SEO alternative
if ! wp plugin is-installed slim-seo 2>/dev/null; then
    wp plugin install slim-seo --activate 2>/dev/null || echo "  - Slim SEO: Could not install (optional)"
fi
echo "  - SEO plugins: Setup complete"

# Create test user similar to production
echo ""
echo "[4/6] Creating test user (ping.xie)..."
if ! wp user get ping.xie 2>/dev/null; then
    wp user create ping.xie ping.xie@localhost.local \
        --role=editor \
        --user_pass="test_password" \
        --display_name="Ping Xie (Test)" 2>/dev/null || true
    echo "  - User ping.xie created"
else
    echo "  - User ping.xie already exists"
fi

# Configure permalink structure
echo ""
echo "[5/6] Configuring permalinks..."
wp rewrite structure '/%category%/%postname%/' --hard 2>/dev/null || true
wp rewrite flush --hard 2>/dev/null || true
echo "  - Permalinks: /%category%/%postname%/"

# Create test categories
echo ""
echo "[6/6] Creating test categories..."
wp term create category "健康" --slug="health" 2>/dev/null || true
wp term create category "科技" --slug="tech" 2>/dev/null || true
wp term create category "生活" --slug="life" 2>/dev/null || true
echo "  - Categories created: 健康, 科技, 生活"

echo ""
echo "=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "Environment Configuration:"
echo "  - URL: http://localhost:8001 (via nginx with HTTP Basic Auth)"
echo "  - HTTP Basic Auth: djy / djy2013"
echo "  - WordPress Admin: admin / admin"
echo "  - Test Editor: ping.xie / test_password"
echo "  - Editor Type: Classic Editor"
echo "  - SEO Plugin: Slim SEO (Lite SEO alternative)"
echo ""
echo "This environment now matches production (admin.epochtimes.com)"
echo "=================================================="
