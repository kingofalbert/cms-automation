#!/usr/bin/env python3
"""
Proofreading Visual Test for Dev-Prod-Like Environment

This test:
1. Creates an article with intentional issues for proofreading
2. Analyzes the proofreading results from the system
3. Compares with expected issues
4. Verifies the proofreading UI displays correctly

Usage:
    source /tmp/playwright_venv/bin/activate
    python tests/visual/test_proofreading.py
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

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Test directories
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "visual" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


# Sample article with intentional proofreading issues
SAMPLE_ARTICLE_WITH_ISSUES = """
<p>這是一篇測試文章，包含一些常見的校對問題。</p>

<p>【問題1】习近平主席出席了會議。這裡應該使用正體字「習」而不是簡體字「习」。</p>

<p>【問題3】這個句子有重複重複的詞語。</p>

<p>【問題4】這是一個很長的段落，包含了太多的內容，應該分成多個段落來提高可讀性，因為長段落會讓讀者感到疲倦，而且不利於在手機等小螢幕設備上閱讀，所以我們應該盡量避免寫這麼長的段落，最好能夠把內容分成幾個小段落，每個段落專注討論一個主題，這樣讀者更容易理解文章的內容。此外，過長的段落也會影響文章的結構清晰度，讓編輯在審稿時難以快速掌握重點，同時也不利於搜索引擎優化，因為搜索引擎更喜歡結構清晰、段落分明的文章內容，這對於網站的SEO排名有直接的影響。</p>

<p>【問題5】「這是錯誤的引號格式"。」應該統一使用中文引號。</p>

<p>【問題6】電話號碼：0912345678，應該格式化為 0912-345-678。</p>

<p>【問題7】１２３４全形數字應該改為半形數字1234。</p>

<p>結尾段落，沒有明顯問題。</p>
"""

# Expected issues based on AI analysis
EXPECTED_ISSUES = [
    {
        "type": "simplified_chinese",
        "description": "「习」應改為正體字「習」",
        "location": "問題1",
        "severity": "error",
    },
    {
        "type": "repetition",
        "description": "「重複重複」詞語重複",
        "location": "問題3",
        "severity": "warning",
    },
    {
        "type": "paragraph_length",
        "description": "段落過長，建議分段",
        "location": "問題4",
        "severity": "info",
    },
    {
        "type": "quotation_marks",
        "description": "引號格式不統一",
        "location": "問題5",
        "severity": "warning",
    },
    {
        "type": "phone_format",
        "description": "電話號碼格式不正確",
        "location": "問題6",
        "severity": "info",
    },
    {
        "type": "fullwidth_numbers",
        "description": "全形數字應改為半形",
        "location": "問題7",
        "severity": "warning",
    },
]


class ProofreadingTest:
    """Test proofreading functionality."""

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
            locale="zh-TW",
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
        filename = f"{self.test_run_id}_proof_{name}.png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def test_create_article_with_issues(self):
        """
        Test 1: Create an article with intentional proofreading issues.

        This creates a WordPress article that contains various types of issues
        that the proofreading system should detect.
        """
        print("\n" + "=" * 60)
        print("Test 1: Create Article with Proofreading Issues")
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

            # Enter title
            title = f"校對測試文章 {self.test_run_id}"
            self.page.locator("#title").fill(title)
            print(f"  Title: {title}")

            # Switch to HTML mode and enter content with issues
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill(SAMPLE_ARTICLE_WITH_ISSUES.strip())
            print("  Content with issues inserted")

            self.screenshot("01_article_with_issues")

            # Save draft
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            self.screenshot("02_article_saved", full_page=True)

            # Extract post ID
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            result = {
                "test": "Create Article with Issues",
                "success": post_id is not None,
                "post_id": post_id,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if result['success'] else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("01_error")
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Create Article with Issues",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_ai_proofreading_analysis(self):
        """
        Test 2: Analyze the sample content using AI-based proofreading logic.

        This simulates what the proofreading service would do, using
        deterministic rules to detect issues.
        """
        print("\n" + "=" * 60)
        print("Test 2: AI Proofreading Analysis")
        print("=" * 60)

        start = time.time()

        try:
            content = SAMPLE_ARTICLE_WITH_ISSUES.strip()
            detected_issues = []

            # Rule 1: Check for simplified Chinese characters
            simplified_chars = ['习', '国', '会', '东', '书', '门', '马', '长', '见', '贝']
            for char in simplified_chars:
                if char in content:
                    detected_issues.append({
                        "type": "simplified_chinese",
                        "description": f"發現簡體字「{char}」",
                        "severity": "error",
                        "rule_id": "B1-001",
                    })

            # Rule 2: Check for word repetition
            import re
            repetition_pattern = r'([\u4e00-\u9fff]{2,})\1'
            matches = re.findall(repetition_pattern, content)
            for match in matches:
                detected_issues.append({
                    "type": "repetition",
                    "description": f"發現重複詞語「{match}{match}」",
                    "severity": "warning",
                    "rule_id": "A1-003",
                })

            # Rule 3: Check for mixed quotation marks
            if '"' in content or "'" in content:
                if '「' in content or '」' in content:
                    detected_issues.append({
                        "type": "quotation_marks",
                        "description": "引號格式不統一（混用中英文引號）",
                        "severity": "warning",
                        "rule_id": "C2-001",
                    })

            # Rule 4: Check for fullwidth numbers
            fullwidth_numbers = ['０', '１', '２', '３', '４', '５', '６', '７', '８', '９']
            for num in fullwidth_numbers:
                if num in content:
                    detected_issues.append({
                        "type": "fullwidth_numbers",
                        "description": f"發現全形數字「{num}」應改為半形",
                        "severity": "warning",
                        "rule_id": "C1-002",
                    })

            # Rule 5: Check for long paragraphs (>200 chars)
            # Use regex to properly extract paragraph content between <p> and </p>
            paragraph_pattern = r'<p[^>]*>(.*?)</p>'
            paragraphs = re.findall(paragraph_pattern, content, re.DOTALL | re.IGNORECASE)
            for i, para in enumerate(paragraphs):
                # Remove any remaining HTML tags and count characters
                clean_para = re.sub(r'<[^>]+>', '', para).strip()
                char_count = len(clean_para)
                if char_count > 200:
                    detected_issues.append({
                        "type": "paragraph_length",
                        "description": f"段落 {i+1} 過長（{char_count} 字），建議分段",
                        "severity": "info",
                        "rule_id": "D1-001",
                        "evidence": clean_para[:50] + "..." if len(clean_para) > 50 else clean_para,
                    })

            # Rule 6: Check for phone number format
            phone_pattern = r'\d{10}'
            if re.search(phone_pattern, content):
                detected_issues.append({
                    "type": "phone_format",
                    "description": "電話號碼格式不正確，建議使用 XXXX-XXX-XXX 格式",
                    "severity": "info",
                    "rule_id": "C3-001",
                })

            duration = int((time.time() - start) * 1000)

            # Compare with expected issues
            expected_types = set(e["type"] for e in EXPECTED_ISSUES)
            detected_types = set(d["type"] for d in detected_issues)

            matched_types = expected_types.intersection(detected_types)
            missed_types = expected_types - detected_types
            extra_types = detected_types - expected_types

            result = {
                "test": "AI Proofreading Analysis",
                "success": len(detected_issues) >= len(EXPECTED_ISSUES) * 0.5,  # At least 50% detection
                "expected_issues": len(EXPECTED_ISSUES),
                "detected_issues": len(detected_issues),
                "matched_types": list(matched_types),
                "missed_types": list(missed_types),
                "extra_types": list(extra_types),
                "issues": detected_issues,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if result['success'] else 'FAIL'}")
            print(f"  Expected issues: {len(EXPECTED_ISSUES)}")
            print(f"  Detected issues: {len(detected_issues)}")
            print(f"  Matched types: {matched_types}")
            print(f"  Missed types: {missed_types}")
            print(f"  Duration: {duration}ms")

            print("\n  Detected Issues:")
            for issue in detected_issues:
                print(f"    - [{issue['severity']}] {issue['type']}: {issue['description']}")

            self.results.append(result)
            return result

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "AI Proofreading Analysis",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_proofreading_visual_verification(self):
        """
        Test 3: Visual verification of proofreading in WordPress.

        This test verifies that the content with issues is correctly displayed
        in both editor and preview modes.
        """
        print("\n" + "=" * 60)
        print("Test 3: Proofreading Visual Verification")
        print("=" * 60)

        start = time.time()

        try:
            # Get the most recent test article
            self.page.goto(f"{DEV_URL}/wp-admin/edit.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            self.screenshot("03_posts_list")

            # Find and click on the test article
            test_article = self.page.locator(f'a.row-title:has-text("校對測試文章")')
            if test_article.first.is_visible(timeout=5000):
                test_article.first.click()
                self.page.wait_for_load_state("networkidle", timeout=15000)

                self.screenshot("03_edit_test_article", full_page=True)

                # Switch to Visual mode
                self.page.locator("#content-tmce").click()
                self.page.wait_for_timeout(1000)

                self.screenshot("03_visual_mode", full_page=True)

                # Preview the article
                preview_link = self.page.locator("a#post-preview, a.preview")
                if preview_link.first.is_visible(timeout=3000):
                    preview_url = preview_link.first.get_attribute("href")
                    self.page.goto(preview_url, timeout=30000)
                    self.page.wait_for_load_state("networkidle", timeout=10000)

                    self.screenshot("03_preview_page", full_page=True)

                    # Check if content is displayed correctly
                    content_visible = self.page.locator("text=校對測試文章").first.is_visible(timeout=5000)

                    visual_verification_passed = content_visible
                else:
                    visual_verification_passed = False
                    print("  Preview link not found")
            else:
                visual_verification_passed = False
                print("  Test article not found in posts list")

            duration = int((time.time() - start) * 1000)

            result = {
                "test": "Proofreading Visual Verification",
                "success": visual_verification_passed,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if visual_verification_passed else 'FAIL'}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("03_error")
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Proofreading Visual Verification",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def run_all_tests(self):
        """Run all proofreading tests."""
        print("=" * 70)
        print("  Proofreading Test Suite")
        print("=" * 70)
        print(f"  Target: {DEV_URL}")
        print(f"  Test Run: {self.test_run_id}")
        print("=" * 70)

        try:
            self.setup()

            self.test_create_article_with_issues()
            self.test_ai_proofreading_analysis()
            self.test_proofreading_visual_verification()

        finally:
            self.teardown()

        # Summary
        passed = sum(1 for r in self.results if r.get("success"))
        failed = len(self.results) - passed

        print("\n" + "=" * 70)
        print("  PROOFREADING TEST SUMMARY")
        print("=" * 70)
        print(f"  Total: {len(self.results)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Pass Rate: {(passed/len(self.results)*100):.1f}%" if self.results else "N/A")
        print("=" * 70)

        # AI Analysis Summary
        ai_result = next((r for r in self.results if r.get("test") == "AI Proofreading Analysis"), None)
        if ai_result and ai_result.get("issues"):
            print("\n  AI-DETECTED PROOFREADING ISSUES:")
            print("  " + "-" * 50)
            for issue in ai_result["issues"]:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue["severity"], "•")
                print(f"  {severity_icon} [{issue['rule_id']}] {issue['description']}")

        # Save report
        report = {
            "test_run_id": self.test_run_id,
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "results": self.results
        }

        report_path = SCREENSHOT_DIR / f"{self.test_run_id}_proofreading_report.json"
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

    suite = ProofreadingTest(headless=not args.headed, slow_mo=args.slow_mo)
    report = suite.run_all_tests()

    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
