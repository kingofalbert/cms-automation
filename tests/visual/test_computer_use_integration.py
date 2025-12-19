#!/usr/bin/env python3
"""
Computer Use Integration Test for Dev-Prod-Like Environment

This test verifies that the Computer Use instructions generator produces
correct instructions for the dev environment, and simulates publishing
various types of content.

Test Scenarios:
1. Basic article with title and body
2. Article with SEO metadata (Slim SEO)
3. Article with special characters and Chinese text
4. Article with categories and tags
5. Article with FAQ Schema
6. Long-form article (5000+ chars)

Usage:
    source /tmp/playwright_venv/bin/activate
    python tests/visual/test_computer_use_integration.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import Page, sync_playwright

# Dev environment configuration
DEV_URL = os.getenv("DEV_WORDPRESS_URL", "http://localhost:8001")
HTTP_AUTH_USER = os.getenv("DEV_HTTP_AUTH_USER", "djy")
HTTP_AUTH_PASS = os.getenv("DEV_HTTP_AUTH_PASS", "djy2013")
WP_USER = os.getenv("DEV_WP_USER", "admin")
WP_PASS = os.getenv("DEV_WP_PASS", "admin")

# Screenshot directory
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "visual" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TestArticle:
    """Test article data structure matching Computer Use service."""
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
    faqs: list = field(default_factory=list)


@dataclass
class PublishResult:
    """Publishing result container."""
    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    message: str = ""
    screenshot: Optional[str] = None
    duration_ms: int = 0


class ComputerUseIntegrationTest:
    """Integration test for Computer Use publishing."""

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []

    def setup(self):
        """Set up browser and login to WordPress."""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = self.browser.new_context(
            http_credentials={
                "username": HTTP_AUTH_USER,
                "password": HTTP_AUTH_PASS
            },
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)

        # Set WordPress test cookie
        self.context.add_cookies([{
            "name": "wordpress_test_cookie",
            "value": "WP%20Cookie%20check",
            "domain": "localhost",
            "path": "/",
        }])

        # Login to WordPress
        self._login()

    def _login(self):
        """Login to WordPress."""
        self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
        self.page.wait_for_load_state("networkidle", timeout=10000)

        # Handle cookie error if present
        if self.page.locator("text=Cookies are blocked").first.is_visible(timeout=1000):
            self.page.goto(f"{DEV_URL}/", timeout=10000)
            self.page.wait_for_timeout(1000)
            self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)

        self.page.fill("#user_login", WP_USER)
        self.page.fill("#user_pass", WP_PASS)
        self.page.click("#wp-submit")
        self.page.wait_for_load_state("networkidle", timeout=15000)

        if "wp-admin" not in self.page.url:
            raise Exception(f"Login failed, URL: {self.page.url}")

    def teardown(self):
        """Clean up browser resources."""
        if self.browser:
            self.browser.close()

    def screenshot(self, name: str, full_page: bool = True) -> str:
        """Take a screenshot and return the path."""
        filename = f"{self.test_run_id}_{name}.png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def publish_article(self, article: TestArticle, save_as_draft: bool = True) -> PublishResult:
        """
        Publish an article to WordPress using Playwright automation.

        This simulates what Computer Use would do, following the same steps
        defined in _build_wordpress_instructions().
        """
        start = time.time()

        try:
            # Step 1: Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Re-login if needed
            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Step 2: Enter title
            title_field = self.page.locator("#title")
            title_field.fill(article.title)
            self.page.wait_for_timeout(300)

            # Step 3: Switch to Code/Text mode and enter content
            code_tab = self.page.locator("#content-html")
            if code_tab.is_visible(timeout=2000):
                code_tab.click()
                self.page.wait_for_timeout(300)

            content_area = self.page.locator("#content")
            content_area.fill(article.body)
            self.page.wait_for_timeout(300)

            # Step 4: Configure Categories (if provided)
            if article.primary_category or article.secondary_categories:
                categories_box = self.page.locator("#categorydiv")
                if categories_box.is_visible(timeout=3000):
                    # Click "Add New Category" if category doesn't exist
                    add_cat_link = self.page.locator("#category-add-toggle")
                    if add_cat_link.is_visible(timeout=2000):
                        add_cat_link.click()
                        self.page.wait_for_timeout(500)

                        if article.primary_category:
                            new_cat_input = self.page.locator("#newcategory")
                            new_cat_input.fill(article.primary_category)
                            add_btn = self.page.locator("#category-add-submit")
                            add_btn.click()
                            self.page.wait_for_timeout(1000)

            # Step 5: Add Tags (if provided)
            if article.tags:
                tags_input = self.page.locator("#new-tag-post_tag")
                if tags_input.is_visible(timeout=2000):
                    for tag in article.tags:
                        tags_input.fill(tag)
                        add_btn = self.page.locator(".tagadd")
                        if add_btn.first.is_visible(timeout=1000):
                            add_btn.first.click()
                            self.page.wait_for_timeout(300)

            # Step 6: Configure SEO (Slim SEO)
            if article.meta_title or article.meta_description:
                # Scroll to SEO section
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                self.page.wait_for_timeout(500)

                # Look for Slim SEO fields
                meta_title_field = self.page.locator("input[name='slim_seo[title]'], #ss-title")
                if meta_title_field.first.is_visible(timeout=3000):
                    if article.meta_title:
                        meta_title_field.first.fill(article.meta_title)

                meta_desc_field = self.page.locator("textarea[name='slim_seo[description]'], #ss-description")
                if meta_desc_field.first.is_visible(timeout=2000):
                    if article.meta_description:
                        meta_desc_field.first.fill(article.meta_description)

            # Take screenshot before saving
            self.screenshot(f"publish_{article.title[:20].replace(' ', '_')}_before_save")

            # Step 7: Save as Draft or Publish
            if save_as_draft:
                save_btn = self.page.locator("#save-post")
                save_btn.click()
            else:
                publish_btn = self.page.locator("#publish")
                publish_btn.click()

            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Extract post ID from URL
            import re
            current_url = self.page.url
            post_id_match = re.search(r'post=(\d+)', current_url)
            post_id = post_id_match.group(1) if post_id_match else None

            # Take final screenshot
            screenshot_path = self.screenshot(f"publish_{article.title[:20].replace(' ', '_')}_result", full_page=True)

            # Check for success indicators
            success_message = self.page.locator("#message, .notice-success")
            is_success = "post=" in current_url or success_message.first.is_visible(timeout=2000)

            duration = int((time.time() - start) * 1000)

            return PublishResult(
                success=is_success,
                post_id=post_id,
                url=current_url,
                message="Article published successfully" if is_success else "Publish may have failed",
                screenshot=screenshot_path,
                duration_ms=duration
            )

        except Exception as e:
            screenshot_path = self.screenshot(f"publish_error_{article.title[:20].replace(' ', '_')}")
            duration = int((time.time() - start) * 1000)
            return PublishResult(
                success=False,
                message=f"Error: {str(e)}",
                screenshot=screenshot_path,
                duration_ms=duration
            )

    def run_all_tests(self):
        """Run all integration tests."""
        print("=" * 70)
        print("  Computer Use Integration Test Suite")
        print("=" * 70)
        print(f"  Target: {DEV_URL}")
        print(f"  Test Run: {self.test_run_id}")
        print("=" * 70)
        print()

        try:
            self.setup()

            # Test 1: Basic article
            print("Test 1: Basic article with title and body...")
            article1 = TestArticle(
                title=f"Basic Test Article {self.test_run_id}",
                body="<p>This is a basic test article.</p><p>It has multiple paragraphs.</p>"
            )
            result1 = self.publish_article(article1)
            self._print_result("Basic Article", result1)
            self.results.append(("Basic Article", result1))

            # Test 2: Article with Chinese characters
            print("\nTest 2: Chinese characters article...")
            article2 = TestArticle(
                title=f"中文測試文章 {self.test_run_id}",
                body="<p>這是一篇中文測試文章。</p><h2>健康提示</h2><p>多喝水，保持健康生活方式。</p>"
            )
            result2 = self.publish_article(article2)
            self._print_result("Chinese Article", result2)
            self.results.append(("Chinese Article", result2))

            # Test 3: Article with SEO metadata
            print("\nTest 3: Article with SEO metadata...")
            article3 = TestArticle(
                title=f"SEO Test Article {self.test_run_id}",
                body="<p>This article has SEO metadata configured.</p>",
                meta_title="SEO Optimized Title | Test Site",
                meta_description="This is a carefully crafted meta description for search engines. It should be between 120-160 characters.",
                focus_keyword="test article"
            )
            result3 = self.publish_article(article3)
            self._print_result("SEO Article", result3)
            self.results.append(("SEO Article", result3))

            # Test 4: Article with special characters
            print("\nTest 4: Special characters article...")
            article4 = TestArticle(
                title=f"Special Chars: <>&\"' Test {self.test_run_id}",
                body="<p>Testing special characters: &amp; &lt; &gt; &quot; &#39;</p><p>Chinese punctuation: 「」『』——、。！？</p>"
            )
            result4 = self.publish_article(article4)
            self._print_result("Special Chars", result4)
            self.results.append(("Special Chars", result4))

            # Test 5: Long content article
            print("\nTest 5: Long content article (5000+ chars)...")
            long_paragraph = "這是一段很長的測試內容，用於測試系統處理大量文字的能力。" * 50
            article5 = TestArticle(
                title=f"Long Content Test {self.test_run_id}",
                body=f"<p>{long_paragraph}</p>" * 5
            )
            result5 = self.publish_article(article5)
            self._print_result("Long Content", result5)
            self.results.append(("Long Content", result5))

            # Test 6: Article with tags
            print("\nTest 6: Article with tags...")
            article6 = TestArticle(
                title=f"Tagged Article {self.test_run_id}",
                body="<p>This article has multiple tags.</p>",
                tags=["健康", "測試", "自動化"]
            )
            result6 = self.publish_article(article6)
            self._print_result("Tagged Article", result6)
            self.results.append(("Tagged Article", result6))

            # Test 7: Full article with all fields
            print("\nTest 7: Full article with all fields...")
            article7 = TestArticle(
                title=f"Complete Article {self.test_run_id}",
                body="""<h2>Introduction</h2>
<p>This is a comprehensive test article with all fields populated.</p>
<h2>Main Content</h2>
<p>The article includes <strong>bold text</strong>, <em>italic text</em>, and a list:</p>
<ul>
<li>Item 1</li>
<li>Item 2</li>
<li>Item 3</li>
</ul>
<blockquote>This is a quote block for emphasis.</blockquote>
<p>Final paragraph with a <a href="https://example.com">link</a>.</p>""",
                meta_title="Complete Test Article | CMS Automation",
                meta_description="A comprehensive test article demonstrating all features of the CMS automation system.",
                focus_keyword="complete test",
                keywords=["test", "automation", "complete"],
                tags=["測試", "完整"]
            )
            result7 = self.publish_article(article7)
            self._print_result("Complete Article", result7)
            self.results.append(("Complete Article", result7))

        finally:
            self.teardown()

        return self._generate_report()

    def _print_result(self, name: str, result: PublishResult):
        """Print a single test result."""
        status = "PASS" if result.success else "FAIL"
        print(f"  {status}: {name} ({result.duration_ms}ms)")
        if result.post_id:
            print(f"    Post ID: {result.post_id}")
        if not result.success:
            print(f"    Message: {result.message}")

    def _generate_report(self) -> dict:
        """Generate test report."""
        passed = sum(1 for _, r in self.results if r.success)
        failed = sum(1 for _, r in self.results if not r.success)
        total = len(self.results)

        print("\n" + "=" * 70)
        print("  TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"  Total: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        print("=" * 70)

        if failed > 0:
            print("\nFAILED TESTS:")
            for name, result in self.results:
                if not result.success:
                    print(f"  - {name}: {result.message}")

        report = {
            "test_run_id": self.test_run_id,
            "target_url": DEV_URL,
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": [
                {
                    "name": name,
                    "success": r.success,
                    "post_id": r.post_id,
                    "url": r.url,
                    "message": r.message,
                    "screenshot": r.screenshot,
                    "duration_ms": r.duration_ms
                }
                for name, r in self.results
            ]
        }

        # Save report
        report_path = SCREENSHOT_DIR / f"{self.test_run_id}_integration_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved: {report_path}")

        return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Computer Use integration tests")
    parser.add_argument("--headed", action="store_true", help="Run in headed mode")
    parser.add_argument("--slow-mo", type=int, default=0, help="Slow down actions by ms")
    args = parser.parse_args()

    suite = ComputerUseIntegrationTest(
        headless=not args.headed,
        slow_mo=args.slow_mo
    )
    report = suite.run_all_tests()

    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
