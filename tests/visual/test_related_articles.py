#!/usr/bin/env python3
"""
Related Articles (Internal Linking) Test for Dev-Prod-Like Environment

This test verifies:
1. Related Articles section can be inserted into WordPress
2. Internal links are correctly formatted
3. Links are clickable and open in new tabs

Usage:
    source /tmp/playwright_venv/bin/activate
    python tests/visual/test_related_articles.py
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

# Dev environment configuration
DEV_URL = os.getenv("DEV_WORDPRESS_URL", "http://localhost:8001")
HTTP_AUTH_USER = os.getenv("DEV_HTTP_AUTH_USER", "djy")
HTTP_AUTH_PASS = os.getenv("DEV_HTTP_AUTH_PASS", "djy2013")
WP_USER = os.getenv("DEV_WP_USER", "admin")
WP_PASS = os.getenv("DEV_WP_PASS", "admin")

# Test directories
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "visual" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class RelatedArticlesTest:
    """Test Related Articles (internal linking) functionality."""

    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.context = None
        self.page = None
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []

    def setup(self):
        """Set up browser and login."""
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

        self._login()

    def _login(self):
        """Login to WordPress."""
        self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
        self.page.wait_for_load_state("networkidle", timeout=10000)

        if self.page.locator("text=Cookies are blocked").first.is_visible(timeout=1000):
            self.page.goto(f"{DEV_URL}/", timeout=10000)
            self.page.wait_for_timeout(1000)
            self.page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=10000)

        self.page.fill("#user_login", WP_USER)
        self.page.fill("#user_pass", WP_PASS)
        self.page.click("#wp-submit")
        self.page.wait_for_load_state("networkidle", timeout=15000)

    def teardown(self):
        """Clean up."""
        if self.browser:
            self.browser.close()

    def screenshot(self, name: str, full_page: bool = True) -> str:
        """Take screenshot."""
        filename = f"{self.test_run_id}_related_{name}.png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def test_related_articles_insertion(self):
        """
        Test 1: Insert Related Articles section with internal links.

        Simulates what Computer Use would do:
        1. Create article with content
        2. Switch to HTML mode
        3. Insert Related Articles HTML at end
        4. Verify links are correct
        """
        print("\n" + "=" * 60)
        print("Test 1: Related Articles Insertion")
        print("=" * 60)

        start = time.time()

        try:
            # Simulate related articles data (as would come from parser)
            related_articles = [
                {
                    "article_id": "n14001234",
                    "title": "健康飲食：每天五蔬果的重要性",
                    "title_main": "健康飲食：每天五蔬果的重要性",
                    "url": "https://www.epochtimes.com/b5/24/1/1/n14001234.htm",
                    "similarity": 0.89,
                    "match_type": "semantic",
                },
                {
                    "article_id": "n14005678",
                    "title": "運動養生：每週三次有氧運動的好處",
                    "title_main": "運動養生",
                    "url": "https://www.epochtimes.com/b5/24/2/15/n14005678.htm",
                    "similarity": 0.85,
                    "match_type": "content",
                },
                {
                    "article_id": "n14009012",
                    "title": "中醫養生：四季調養身體的方法",
                    "url": "https://www.epochtimes.com/b5/24/3/20/n14009012.htm",
                    "similarity": 0.78,
                    "match_type": "keyword",
                },
            ]

            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Enter title
            title = f"Related Articles Test {self.test_run_id}"
            self.page.locator("#title").fill(title)
            print(f"  Title: {title}")

            # Enter article content with multiple paragraphs
            article_content = """<p>這是一篇關於健康養生的測試文章。</p>
<p>文章的第二段內容，討論了日常生活中的養生方法。</p>
<p>第三段繼續探討健康飲食的重要性。</p>
<p>最後一段總結了養生的核心要點。</p>"""

            # Build Related Articles HTML (as Computer Use would do)
            related_links_html = []
            for ra in related_articles:
                ra_title = ra.get('title', ra.get('title_main', 'Related Article'))
                ra_url = ra.get('url', '#')
                related_links_html.append(f'<li><a href="{ra_url}" target="_blank">{ra_title}</a></li>')

            related_articles_html = f'''<h3>相關閱讀</h3>
<ul>
{chr(10).join(related_links_html)}
</ul>'''

            # Combine content with Related Articles
            full_content = article_content + "\n\n" + related_articles_html

            # Switch to HTML mode and insert content
            print("  Switching to HTML mode...")
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill(full_content)
            print("  Content with Related Articles inserted")

            self.screenshot("01_html_mode_content")

            # Switch to Visual mode to verify
            print("  Switching to Visual mode to verify...")
            self.page.locator("#content-tmce").click()
            self.page.wait_for_timeout(1000)

            self.screenshot("02_visual_mode_content")

            # Save draft
            print("  Saving draft...")
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            self.screenshot("03_saved_draft", full_page=True)

            # Verify Related Articles in content
            print("  Verifying Related Articles...")
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            saved_content = self.page.locator("#content").input_value()

            # Check for Related Articles markers
            has_related_heading = "相關閱讀" in saved_content
            has_links = all(ra['url'] in saved_content for ra in related_articles)
            has_titles = all(ra['title'][:20] in saved_content for ra in related_articles)
            link_count = saved_content.count('<a href="https://www.epochtimes.com')

            # Extract post ID
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            success = has_related_heading and has_links and link_count >= len(related_articles)

            result = {
                "test": "Related Articles Insertion",
                "success": success,
                "post_id": post_id,
                "has_related_heading": has_related_heading,
                "has_all_links": has_links,
                "has_all_titles": has_titles,
                "link_count": link_count,
                "expected_links": len(related_articles),
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if success else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  '相關閱讀' heading found: {has_related_heading}")
            print(f"  All links found: {has_links}")
            print(f"  Link count: {link_count}/{len(related_articles)}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("01_error")
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Related Articles Insertion",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_related_articles_links_clickable(self):
        """
        Test 2: Verify Related Articles links are clickable in preview.
        """
        print("\n" + "=" * 60)
        print("Test 2: Related Articles Links Clickable")
        print("=" * 60)

        start = time.time()

        try:
            # Create a simple post with Related Articles
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            title = f"Link Clickable Test {self.test_run_id}"
            self.page.locator("#title").fill(title)

            # Content with Related Articles
            content = """<p>測試文章內容。</p>
<h3>相關閱讀</h3>
<ul>
<li><a href="https://www.epochtimes.com/b5/24/1/1/n14001234.htm" target="_blank">健康飲食文章</a></li>
<li><a href="https://www.epochtimes.com/b5/24/2/15/n14005678.htm" target="_blank">運動養生文章</a></li>
</ul>"""

            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill(content)

            # Save draft
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Click Preview
            print("  Opening preview...")
            preview_link = self.page.locator("a#post-preview, a.preview")
            if preview_link.first.is_visible(timeout=3000):
                # Get the preview URL
                preview_url = preview_link.first.get_attribute("href")
                print(f"  Preview URL: {preview_url}")

                # Open preview in same context
                self.page.goto(preview_url, timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=10000)

                self.screenshot("04_preview_page")

                # Check for links in preview
                links = self.page.locator('a[href*="epochtimes.com"]')
                link_count = links.count()
                print(f"  Found {link_count} epochtimes links in preview")

                # Verify links have target="_blank"
                links_with_target = self.page.locator('a[href*="epochtimes.com"][target="_blank"]')
                target_blank_count = links_with_target.count()
                print(f"  Links with target='_blank': {target_blank_count}")

                links_clickable = link_count >= 2 and target_blank_count >= 2
            else:
                print("  Preview link not found, checking content directly")
                links_clickable = False

            # Extract post ID from URL
            post_id_match = re.search(r'p=(\d+)|post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) or post_id_match.group(2) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            result = {
                "test": "Related Articles Links Clickable",
                "success": links_clickable,
                "post_id": post_id,
                "links_found": link_count if 'link_count' in dir() else 0,
                "target_blank_links": target_blank_count if 'target_blank_count' in dir() else 0,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if links_clickable else 'FAIL'}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("04_error")
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Related Articles Links Clickable",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_related_articles_format(self):
        """
        Test 3: Verify Related Articles HTML format matches expected structure.
        """
        print("\n" + "=" * 60)
        print("Test 3: Related Articles HTML Format")
        print("=" * 60)

        start = time.time()

        try:
            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            title = f"Format Test {self.test_run_id}"
            self.page.locator("#title").fill(title)

            # Expected format from Computer Use instructions
            expected_html = """<p>文章內容。</p>
<h3>相關閱讀</h3>
<ul>
<li><a href="https://example.com/article1" target="_blank">相關文章一</a></li>
<li><a href="https://example.com/article2" target="_blank">相關文章二</a></li>
<li><a href="https://example.com/article3" target="_blank">相關文章三</a></li>
</ul>"""

            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill(expected_html)

            # Save
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Verify format preserved
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            saved_content = self.page.locator("#content").input_value()

            # Check structure
            has_h3 = "<h3>相關閱讀</h3>" in saved_content or "<h3>相關閱讀" in saved_content
            has_ul = "<ul>" in saved_content and "</ul>" in saved_content
            has_li = saved_content.count("<li>") >= 3
            has_links = saved_content.count("<a href=") >= 3
            has_target_blank = saved_content.count('target="_blank"') >= 3 or saved_content.count("target='_blank'") >= 3

            self.screenshot("05_format_test", full_page=True)

            # Extract post ID
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            success = has_h3 and has_ul and has_li and has_links

            result = {
                "test": "Related Articles HTML Format",
                "success": success,
                "post_id": post_id,
                "has_h3_heading": has_h3,
                "has_ul_list": has_ul,
                "has_li_items": has_li,
                "has_links": has_links,
                "has_target_blank": has_target_blank,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if success else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  <h3> heading: {has_h3}")
            print(f"  <ul>/<li> structure: {has_ul and has_li}")
            print(f"  Links: {has_links}")
            print(f"  target='_blank': {has_target_blank}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("05_error")
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Related Articles HTML Format",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def run_all_tests(self):
        """Run all Related Articles tests."""
        print("=" * 70)
        print("  Related Articles (Internal Linking) Test Suite")
        print("=" * 70)
        print(f"  Target: {DEV_URL}")
        print(f"  Test Run: {self.test_run_id}")
        print("=" * 70)

        try:
            self.setup()

            self.test_related_articles_insertion()
            self.test_related_articles_links_clickable()
            self.test_related_articles_format()

        finally:
            self.teardown()

        # Summary
        passed = sum(1 for r in self.results if r.get("success"))
        failed = len(self.results) - passed

        print("\n" + "=" * 70)
        print("  RELATED ARTICLES TEST SUMMARY")
        print("=" * 70)
        print(f"  Total: {len(self.results)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Pass Rate: {(passed/len(self.results)*100):.1f}%" if self.results else "N/A")
        print("=" * 70)

        # Save report
        report = {
            "test_run_id": self.test_run_id,
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "results": self.results
        }

        report_path = SCREENSHOT_DIR / f"{self.test_run_id}_related_articles_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved: {report_path}")

        return report


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=0)
    args = parser.parse_args()

    suite = RelatedArticlesTest(headless=not args.headed, slow_mo=args.slow_mo)
    report = suite.run_all_tests()

    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
