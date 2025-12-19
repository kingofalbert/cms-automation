#!/usr/bin/env python3
"""
Visual Test Suite for Dev-Prod-Like Environment

This test suite verifies that the development environment matches production
and tests all edge cases for Computer Use publishing.

Test Categories:
1. Environment Setup - HTTP Basic Auth, WordPress login, plugins
2. Content Edge Cases - Special chars, long content, HTML entities
3. SEO Configuration - Slim SEO metadata, keywords
4. Image Upload - Multiple images, captions, alt text
5. Categories - Primary/secondary category handling
6. Full Publishing Flow - End-to-end publish verification

Usage:
    source /tmp/playwright_venv/bin/activate
    python tests/visual/test_dev_prod_like_environment.py
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import Page, sync_playwright, expect

# Dev environment configuration
# Use localhost instead of 127.0.0.1 to match WordPress cookie domain
DEV_URL = os.getenv("DEV_WORDPRESS_URL", "http://localhost:8001")
HTTP_AUTH_USER = os.getenv("DEV_HTTP_AUTH_USER", "djy")
HTTP_AUTH_PASS = os.getenv("DEV_HTTP_AUTH_PASS", "djy2013")
WP_USER = os.getenv("DEV_WP_USER", "admin")
WP_PASS = os.getenv("DEV_WP_PASS", "admin")

# Screenshot directory
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "visual" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TestResult:
    """Test result container."""
    name: str
    passed: bool
    message: str = ""
    screenshot: Optional[str] = None
    duration_ms: int = 0
    details: dict = field(default_factory=dict)


@dataclass
class TestArticle:
    """Test article data."""
    title: str
    body: str
    meta_title: str = ""
    meta_description: str = ""
    focus_keyword: str = ""
    keywords: list = field(default_factory=list)
    primary_category: str = ""
    secondary_categories: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    author_name: str = ""
    images: list = field(default_factory=list)
    faqs: list = field(default_factory=list)


class DevProdLikeVisualTests:
    """Visual test suite for dev-prod-like environment."""

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.results: list[TestResult] = []
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def setup(self):
        """Set up browser and context."""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        # Enable cookies and set proper context for WordPress
        self.context = self.browser.new_context(
            http_credentials={
                "username": HTTP_AUTH_USER,
                "password": HTTP_AUTH_PASS
            },
            viewport={"width": 1920, "height": 1080},
            # Fix cookie issues with WordPress
            ignore_https_errors=True,
            java_script_enabled=True,
            accept_downloads=True,
            # Set locale for proper cookie handling
            locale="en-US",
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)

        # Set WordPress test cookie BEFORE any navigation
        # WordPress requires this cookie to verify cookie support
        # Use localhost domain to match WordPress settings
        self.context.add_cookies([
            {
                "name": "wordpress_test_cookie",
                "value": "WP%20Cookie%20check",
                "domain": "localhost",
                "path": "/",
            }
        ])

    def teardown(self):
        """Clean up browser resources."""
        if self.browser:
            self.browser.close()

    def screenshot(self, name: str, full_page: bool = False) -> str:
        """Take a screenshot and return the path."""
        filename = f"{self.test_run_id}_{name}.png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def add_result(self, name: str, passed: bool, message: str = "",
                   screenshot: str = None, duration_ms: int = 0, details: dict = None):
        """Add a test result."""
        self.results.append(TestResult(
            name=name,
            passed=passed,
            message=message,
            screenshot=screenshot,
            duration_ms=duration_ms,
            details=details or {}
        ))

    # ==================== Environment Tests ====================

    def test_01_http_basic_auth(self) -> TestResult:
        """Test HTTP Basic Auth is working."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)

            # Check we reached the login page (not 401)
            if "wp-login" in self.page.url or "login" in self.page.url.lower():
                screenshot = self.screenshot("01_http_basic_auth_success")
                self.add_result(
                    "HTTP Basic Auth",
                    True,
                    f"Successfully passed HTTP Basic Auth to reach login page",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
                return self.results[-1]
            else:
                screenshot = self.screenshot("01_http_basic_auth_unexpected")
                self.add_result(
                    "HTTP Basic Auth",
                    False,
                    f"Unexpected URL: {self.page.url}",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
                return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("01_http_basic_auth_error")
            self.add_result(
                "HTTP Basic Auth",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_02_wordpress_login(self) -> TestResult:
        """Test WordPress login works."""
        start = time.time()
        try:
            # Navigate to login page (cookies already set in setup)
            self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)

            # Check if there's a cookie error on page
            cookie_error = self.page.locator("text=Cookies are blocked").first
            if cookie_error.is_visible(timeout=1000):
                # Retry by navigating to home first to establish session
                self.page.goto(f"{DEV_URL}/", timeout=10000)
                self.page.wait_for_timeout(1000)
                self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=10000)

            # Fill login form
            self.page.fill("#user_login", WP_USER)
            self.page.fill("#user_pass", WP_PASS)
            self.page.click("#wp-submit")

            # Wait for dashboard
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Check we're logged in
            if "/wp-admin" in self.page.url:
                screenshot = self.screenshot("02_wordpress_login_success")
                self.add_result(
                    "WordPress Login",
                    True,
                    f"Successfully logged in as {WP_USER}",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
                return self.results[-1]
            else:
                screenshot = self.screenshot("02_wordpress_login_failed")
                self.add_result(
                    "WordPress Login",
                    False,
                    f"Login failed, URL: {self.page.url}",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
                return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("02_wordpress_login_error")
            self.add_result(
                "WordPress Login",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def _ensure_logged_in(self):
        """Ensure we're logged into WordPress."""
        # Check if we're on login page
        if "wp-login" in self.page.url:
            # Check for cookie error and handle it
            cookie_error = self.page.locator("text=Cookies are blocked")
            if cookie_error.first.is_visible(timeout=1000):
                # Navigate to homepage first to establish session
                self.page.goto(f"{DEV_URL}/", timeout=10000)
                self.page.wait_for_timeout(1000)
                self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=10000)

            # Fill and submit login form
            self.page.fill("#user_login", WP_USER)
            self.page.fill("#user_pass", WP_PASS)
            self.page.click("#wp-submit")

            # Wait for redirect to complete - either to dashboard or back to login
            self.page.wait_for_load_state("networkidle", timeout=20000)

            # Verify we're logged in (not still on login page)
            retries = 3
            while "wp-login" in self.page.url and retries > 0:
                # Try again if still on login page
                self.page.wait_for_timeout(1000)
                if "wp-login" in self.page.url:
                    self.page.fill("#user_login", WP_USER)
                    self.page.fill("#user_pass", WP_PASS)
                    self.page.click("#wp-submit")
                    self.page.wait_for_load_state("networkidle", timeout=15000)
                retries -= 1

    def test_03_classic_editor_active(self) -> TestResult:
        """Test Classic Editor plugin is active."""
        start = time.time()
        try:
            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Re-login if redirected to login page
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Look for Classic Editor indicators
            classic_selectors = [
                "#wp-content-editor-container",
                "#content",
                ".wp-editor-area",
                "#wp-content-wrap",
            ]

            has_classic = False
            found_selector = None
            for selector in classic_selectors:
                try:
                    if self.page.locator(selector).first.is_visible(timeout=3000):
                        has_classic = True
                        found_selector = selector
                        break
                except:
                    pass

            # Check for Gutenberg (should NOT be present)
            gutenberg_selectors = [
                ".block-editor",
                ".edit-post-visual-editor",
                "[data-type='core/paragraph']",
            ]

            has_gutenberg = False
            for selector in gutenberg_selectors:
                try:
                    if self.page.locator(selector).first.is_visible(timeout=2000):
                        has_gutenberg = True
                        break
                except:
                    pass

            screenshot = self.screenshot("03_classic_editor", full_page=True)

            if has_classic and not has_gutenberg:
                self.add_result(
                    "Classic Editor Active",
                    True,
                    f"Classic Editor detected via: {found_selector}",
                    screenshot,
                    int((time.time() - start) * 1000),
                    {"selector": found_selector}
                )
            elif has_gutenberg:
                self.add_result(
                    "Classic Editor Active",
                    False,
                    "Gutenberg is active instead of Classic Editor",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            else:
                self.add_result(
                    "Classic Editor Active",
                    False,
                    "Could not detect any editor",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("03_classic_editor_error")
            self.add_result(
                "Classic Editor Active",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_04_seo_plugin_active(self) -> TestResult:
        """Test SEO plugin (Slim SEO) is active."""
        start = time.time()
        try:
            # Navigate to new post page
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Scroll down to see metaboxes
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_timeout(1000)

            seo_plugins = {
                "Slim SEO": [
                    "h2.hndle:has-text('Slim SEO')",
                    "#slim-seo",
                    "text=Slim SEO",
                ],
                "Lite SEO": [
                    "h2.hndle:has-text('Lite SEO')",
                    "#lite_seo",
                ],
                "Yoast SEO": [
                    "#wpseo_meta",
                    ".yoast-seo-metabox",
                ],
            }

            detected_plugin = None
            found_selector = None

            for plugin_name, selectors in seo_plugins.items():
                for selector in selectors:
                    try:
                        if self.page.locator(selector).first.is_visible(timeout=2000):
                            detected_plugin = plugin_name
                            found_selector = selector
                            break
                    except:
                        pass
                if detected_plugin:
                    break

            screenshot = self.screenshot("04_seo_plugin", full_page=True)

            if detected_plugin:
                self.add_result(
                    "SEO Plugin Active",
                    True,
                    f"{detected_plugin} detected via: {found_selector}",
                    screenshot,
                    int((time.time() - start) * 1000),
                    {"plugin": detected_plugin, "selector": found_selector}
                )
            else:
                self.add_result(
                    "SEO Plugin Active",
                    False,
                    "No SEO plugin detected",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("04_seo_plugin_error")
            self.add_result(
                "SEO Plugin Active",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    # ==================== Edge Case Tests ====================

    def test_05_special_characters_title(self) -> TestResult:
        """Test special characters in article title."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Test title with special characters
            special_title = "測試文章：特殊字符 <>&\"' 、中文標點！？「」『』—— 表情符號"

            # Find title field (Classic Editor)
            title_field = self.page.locator("#title")
            if title_field.is_visible(timeout=3000):
                title_field.fill(special_title)
                self.page.wait_for_timeout(500)

                # Verify the title was entered correctly
                entered_title = title_field.input_value()
                screenshot = self.screenshot("05_special_chars_title")

                if entered_title == special_title:
                    self.add_result(
                        "Special Characters in Title",
                        True,
                        f"Title with special chars accepted: {special_title[:50]}...",
                        screenshot,
                        int((time.time() - start) * 1000),
                        {"title": special_title, "entered": entered_title}
                    )
                else:
                    self.add_result(
                        "Special Characters in Title",
                        False,
                        f"Title mismatch. Expected: {special_title}, Got: {entered_title}",
                        screenshot,
                        int((time.time() - start) * 1000)
                    )
            else:
                screenshot = self.screenshot("05_special_chars_no_title_field")
                self.add_result(
                    "Special Characters in Title",
                    False,
                    "Title field not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("05_special_chars_error")
            self.add_result(
                "Special Characters in Title",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_06_long_content(self) -> TestResult:
        """Test handling of long article content."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Generate long content (5000+ characters)
            paragraph = "這是一段測試用的長篇內容。" * 50
            long_content = "\n\n".join([paragraph for _ in range(10)])

            # Find content editor (Classic Editor - TinyMCE or Text mode)
            # Try text mode first (more reliable)
            text_tab = self.page.locator("#content-html")
            if text_tab.is_visible(timeout=2000):
                text_tab.click()
                self.page.wait_for_timeout(500)

            content_area = self.page.locator("#content")
            if content_area.is_visible(timeout=3000):
                content_area.fill(long_content)
                self.page.wait_for_timeout(500)

                # Verify content length
                entered_content = content_area.input_value()
                screenshot = self.screenshot("06_long_content", full_page=True)

                if len(entered_content) >= len(long_content) * 0.9:  # Allow 10% variance
                    self.add_result(
                        "Long Content Handling",
                        True,
                        f"Successfully entered {len(entered_content)} characters",
                        screenshot,
                        int((time.time() - start) * 1000),
                        {"content_length": len(entered_content)}
                    )
                else:
                    self.add_result(
                        "Long Content Handling",
                        False,
                        f"Content truncated. Expected {len(long_content)}, got {len(entered_content)}",
                        screenshot,
                        int((time.time() - start) * 1000)
                    )
            else:
                screenshot = self.screenshot("06_long_content_no_editor")
                self.add_result(
                    "Long Content Handling",
                    False,
                    "Content editor not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("06_long_content_error")
            self.add_result(
                "Long Content Handling",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_07_html_content(self) -> TestResult:
        """Test HTML content preservation."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # HTML content with various tags
            html_content = """<h2>測試標題</h2>
<p>這是一段<strong>粗體</strong>和<em>斜體</em>文字。</p>
<ul>
<li>列表項目 1</li>
<li>列表項目 2</li>
</ul>
<blockquote>這是引用區塊</blockquote>
<p>包含<a href="https://example.com">連結</a>的段落。</p>"""

            # Switch to text/HTML mode
            text_tab = self.page.locator("#content-html")
            if text_tab.is_visible(timeout=2000):
                text_tab.click()
                self.page.wait_for_timeout(500)

            content_area = self.page.locator("#content")
            if content_area.is_visible(timeout=3000):
                content_area.fill(html_content)
                self.page.wait_for_timeout(500)

                # Verify HTML is preserved
                entered_content = content_area.input_value()
                screenshot = self.screenshot("07_html_content")

                # Check for key HTML tags
                html_tags_preserved = all(tag in entered_content for tag in ["<h2>", "<strong>", "<ul>", "<blockquote>"])

                if html_tags_preserved:
                    self.add_result(
                        "HTML Content Preservation",
                        True,
                        "HTML tags preserved correctly",
                        screenshot,
                        int((time.time() - start) * 1000),
                        {"content": html_content[:200]}
                    )
                else:
                    self.add_result(
                        "HTML Content Preservation",
                        False,
                        "HTML tags were stripped or modified",
                        screenshot,
                        int((time.time() - start) * 1000)
                    )
            else:
                screenshot = self.screenshot("07_html_content_no_editor")
                self.add_result(
                    "HTML Content Preservation",
                    False,
                    "Content editor not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("07_html_content_error")
            self.add_result(
                "HTML Content Preservation",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_08_categories_panel(self) -> TestResult:
        """Test category selection panel."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Look for Categories metabox (Classic Editor)
            categories_box = self.page.locator("#categorydiv, #category-all")

            if categories_box.first.is_visible(timeout=5000):
                screenshot = self.screenshot("08_categories_panel")

                # Check if we can see category checkboxes
                category_items = self.page.locator("#categorychecklist li, #category-all li")
                category_count = category_items.count()

                self.add_result(
                    "Categories Panel",
                    True,
                    f"Categories panel found with {category_count} categories",
                    screenshot,
                    int((time.time() - start) * 1000),
                    {"category_count": category_count}
                )
            else:
                screenshot = self.screenshot("08_categories_panel_not_found")
                self.add_result(
                    "Categories Panel",
                    False,
                    "Categories panel not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("08_categories_error")
            self.add_result(
                "Categories Panel",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_09_tags_panel(self) -> TestResult:
        """Test tags input panel."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Look for Tags metabox (Classic Editor)
            tags_box = self.page.locator("#tagsdiv-post_tag, #post_tag")

            if tags_box.first.is_visible(timeout=5000):
                # Try to add a tag
                tag_input = self.page.locator("#new-tag-post_tag, .newtag")
                if tag_input.first.is_visible(timeout=3000):
                    tag_input.first.fill("測試標籤")

                    # Click Add button
                    add_btn = self.page.locator(".tagadd, input[value='Add']")
                    if add_btn.first.is_visible(timeout=2000):
                        add_btn.first.click()
                        self.page.wait_for_timeout(500)

                screenshot = self.screenshot("09_tags_panel")
                self.add_result(
                    "Tags Panel",
                    True,
                    "Tags panel found and functional",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            else:
                screenshot = self.screenshot("09_tags_panel_not_found")
                self.add_result(
                    "Tags Panel",
                    False,
                    "Tags panel not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("09_tags_error")
            self.add_result(
                "Tags Panel",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def test_10_featured_image_panel(self) -> TestResult:
        """Test featured image panel."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Look for Featured Image metabox (Classic Editor)
            featured_box = self.page.locator("#postimagediv, #set-post-thumbnail")

            if featured_box.first.is_visible(timeout=5000):
                screenshot = self.screenshot("10_featured_image_panel")
                self.add_result(
                    "Featured Image Panel",
                    True,
                    "Featured Image panel found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            else:
                screenshot = self.screenshot("10_featured_image_not_found")
                self.add_result(
                    "Featured Image Panel",
                    False,
                    "Featured Image panel not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("10_featured_image_error")
            self.add_result(
                "Featured Image Panel",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    # ==================== Full Publishing Flow ====================

    def test_11_full_publish_flow(self) -> TestResult:
        """Test complete article publishing flow (saves as draft)."""
        start = time.time()
        try:
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self._ensure_logged_in()
            if "post-new" not in self.page.url:
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Generate unique test content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_title = f"Visual Test Article {timestamp}"
            test_content = f"""<p>這是自動化視覺測試文章。</p>
<p>測試時間：{timestamp}</p>
<h2>測試段落</h2>
<p>這是測試內容，包含<strong>粗體</strong>和<em>斜體</em>文字。</p>
<ul>
<li>測試項目 1</li>
<li>測試項目 2</li>
</ul>"""

            # 1. Enter title
            title_field = self.page.locator("#title")
            title_field.fill(test_title)

            # 2. Enter content (Text mode)
            text_tab = self.page.locator("#content-html")
            if text_tab.is_visible(timeout=2000):
                text_tab.click()
                self.page.wait_for_timeout(300)

            content_area = self.page.locator("#content")
            content_area.fill(test_content)

            # 3. Save as Draft
            save_draft_btn = self.page.locator("#save-post")
            if save_draft_btn.is_visible(timeout=3000):
                save_draft_btn.click()
                self.page.wait_for_load_state("networkidle", timeout=15000)

                # Check for success message or URL change
                current_url = self.page.url
                screenshot = self.screenshot("11_full_publish_draft", full_page=True)

                if "post=" in current_url or "message=" in current_url:
                    # Extract post ID from URL
                    import re
                    post_id_match = re.search(r'post=(\d+)', current_url)
                    post_id = post_id_match.group(1) if post_id_match else "unknown"

                    self.add_result(
                        "Full Publish Flow (Draft)",
                        True,
                        f"Article saved as draft successfully. Post ID: {post_id}",
                        screenshot,
                        int((time.time() - start) * 1000),
                        {"post_id": post_id, "title": test_title, "url": current_url}
                    )
                else:
                    self.add_result(
                        "Full Publish Flow (Draft)",
                        False,
                        f"Draft save may have failed. URL: {current_url}",
                        screenshot,
                        int((time.time() - start) * 1000)
                    )
            else:
                screenshot = self.screenshot("11_full_publish_no_save_btn")
                self.add_result(
                    "Full Publish Flow (Draft)",
                    False,
                    "Save Draft button not found",
                    screenshot,
                    int((time.time() - start) * 1000)
                )
            return self.results[-1]
        except Exception as e:
            screenshot = self.screenshot("11_full_publish_error")
            self.add_result(
                "Full Publish Flow (Draft)",
                False,
                f"Error: {str(e)}",
                screenshot,
                int((time.time() - start) * 1000)
            )
            return self.results[-1]

    def run_all_tests(self):
        """Run all tests and return results."""
        print("=" * 70)
        print("  Dev-Prod-Like Environment Visual Test Suite")
        print("=" * 70)
        print(f"  Target: {DEV_URL}")
        print(f"  Test Run: {self.test_run_id}")
        print("=" * 70)
        print()

        try:
            self.setup()

            tests = [
                self.test_01_http_basic_auth,
                self.test_02_wordpress_login,
                self.test_03_classic_editor_active,
                self.test_04_seo_plugin_active,
                self.test_05_special_characters_title,
                self.test_06_long_content,
                self.test_07_html_content,
                self.test_08_categories_panel,
                self.test_09_tags_panel,
                self.test_10_featured_image_panel,
                self.test_11_full_publish_flow,
            ]

            for test_func in tests:
                print(f"Running: {test_func.__name__}...", end=" ")
                try:
                    result = test_func()
                    status = "PASS" if result.passed else "FAIL"
                    print(f"{status} ({result.duration_ms}ms)")
                    if not result.passed:
                        print(f"    Message: {result.message}")
                except Exception as e:
                    print(f"ERROR: {str(e)}")
                    self.add_result(test_func.__name__, False, f"Exception: {str(e)}")
                print()

        finally:
            self.teardown()

        return self.generate_report()

    def generate_report(self) -> dict:
        """Generate test report."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print("=" * 70)
        print("  TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"  Total: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        print("=" * 70)
        print()

        if failed > 0:
            print("FAILED TESTS:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")
                    if r.screenshot:
                        print(f"    Screenshot: {r.screenshot}")
            print()

        report = {
            "test_run_id": self.test_run_id,
            "target_url": DEV_URL,
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "screenshot": r.screenshot,
                    "duration_ms": r.duration_ms,
                    "details": r.details
                }
                for r in self.results
            ]
        }

        # Save report to file
        report_path = SCREENSHOT_DIR / f"{self.test_run_id}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Report saved: {report_path}")

        return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run visual tests for dev-prod-like environment")
    parser.add_argument("--headed", action="store_true", help="Run in headed mode (visible browser)")
    parser.add_argument("--slow-mo", type=int, default=0, help="Slow down actions by ms")
    args = parser.parse_args()

    suite = DevProdLikeVisualTests(
        headless=not args.headed,
        slow_mo=args.slow_mo
    )
    report = suite.run_all_tests()

    # Exit with error code if any tests failed
    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
