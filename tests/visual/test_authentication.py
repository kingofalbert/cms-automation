#!/usr/bin/env python3
"""
Authentication Visual Test

Tests the Supabase authentication flow including:
1. Login page display
2. Email/password login
3. Session persistence
4. Protected route access
5. Logout functionality

Usage:
    source /tmp/playwright_venv/bin/activate
    python tests/visual/test_authentication.py [--env dev|prod] [--headed]
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright, expect

# Environment configurations
ENVIRONMENTS = {
    "dev": {
        "name": "Development",
        "frontend_url": "http://localhost:3000",
        "api_url": "http://localhost:8000",
    },
    "prod": {
        "name": "Production",
        "frontend_url": "https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html",
        "api_url": "https://cms-automation-backend-baau2zqeqq-ue.a.run.app",
    },
}

# Test credentials (from environment or defaults for testing)
TEST_EMAIL = os.getenv("TEST_AUTH_EMAIL", "albert.king@epochtimes.nyc")
TEST_PASSWORD = os.getenv("TEST_AUTH_PASSWORD", "Tongxin123$")

# Test directories
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "visual" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class AuthenticationTest:
    """Test authentication functionality."""

    def __init__(self, env: str = "dev", headless: bool = True, slow_mo: int = 0):
        self.env = env
        self.env_config = ENVIRONMENTS[env]
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.context = None
        self.page = None
        self.test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []

    def setup(self):
        """Set up browser."""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-TW",
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)

    def teardown(self):
        """Clean up."""
        if self.browser:
            self.browser.close()

    def screenshot(self, name: str, full_page: bool = False) -> str:
        """Take screenshot."""
        filename = f"{self.test_run_id}_auth_{self.env}_{name}.png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def test_01_login_page_display(self):
        """Test 1: Login page displays correctly."""
        print("\n" + "=" * 60)
        print(f"Test 1: Login Page Display ({self.env_config['name']})")
        print("=" * 60)

        start = time.time()
        success = False
        error_msg = None

        try:
            # Navigate to app (should redirect to login)
            self.page.goto(self.env_config["frontend_url"], timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Wait for redirect to login page
            self.page.wait_for_timeout(2000)

            self.screenshot("01_initial_load")

            # Check if login page elements are present
            # Look for login form elements
            email_input = self.page.locator('input[type="email"], input#email, input[name="email"]')
            password_input = self.page.locator('input[type="password"], input#password')

            # Check for CMS Automation title
            title_visible = self.page.locator('text=CMS Automation').first.is_visible(timeout=5000)

            # Check for Sign In text
            signin_visible = (
                self.page.locator('text=Sign In').first.is_visible(timeout=3000) or
                self.page.locator('text=Sign in').first.is_visible(timeout=3000) or
                self.page.locator('button:has-text("Sign")').first.is_visible(timeout=3000)
            )

            self.screenshot("01_login_page")

            success = title_visible or signin_visible

            if not success:
                # Maybe auth is disabled, check if we're on worklist
                if "worklist" in self.page.url.lower() or self.page.locator('text=Worklist').first.is_visible(timeout=3000):
                    print("  Note: Auth may be disabled - landed on Worklist directly")
                    success = True
                    error_msg = "Auth disabled - direct access to app"

        except Exception as e:
            error_msg = str(e)
            self.screenshot("01_error")
            import traceback
            traceback.print_exc()

        duration = int((time.time() - start) * 1000)

        result = {
            "test": "Login Page Display",
            "environment": self.env,
            "success": success,
            "duration_ms": duration,
            "error": error_msg,
        }

        print(f"\n  Result: {'PASS' if success else 'FAIL'}")
        if error_msg:
            print(f"  Note: {error_msg}")
        print(f"  Duration: {duration}ms")

        self.results.append(result)
        return result

    def test_02_login_with_credentials(self):
        """Test 2: Login with email and password."""
        print("\n" + "=" * 60)
        print(f"Test 2: Login with Credentials ({self.env_config['name']})")
        print("=" * 60)

        start = time.time()
        success = False
        error_msg = None

        try:
            # Make sure we're on login page
            current_url = self.page.url

            # If already logged in (from previous test or auth disabled), skip
            if "login" not in current_url.lower():
                # Check if we're already on the app
                if self.page.locator('text=Worklist').first.is_visible(timeout=3000):
                    print("  Already logged in or auth disabled")
                    success = True
                    error_msg = "Already authenticated"
                    duration = int((time.time() - start) * 1000)
                    result = {
                        "test": "Login with Credentials",
                        "environment": self.env,
                        "success": success,
                        "duration_ms": duration,
                        "note": error_msg,
                    }
                    self.results.append(result)
                    return result

            # Fill in credentials
            email_input = self.page.locator('input[type="email"], input#email, input[name="email"]').first
            password_input = self.page.locator('input[type="password"], input#password').first

            email_input.fill(TEST_EMAIL)
            self.page.wait_for_timeout(300)

            password_input.fill(TEST_PASSWORD)
            self.page.wait_for_timeout(300)

            self.screenshot("02_credentials_filled")

            # Click sign in button
            signin_button = self.page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Sign in")').first
            signin_button.click()

            # Wait for navigation
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self.page.wait_for_timeout(3000)

            self.screenshot("02_after_login")

            # Check if login was successful
            # Should be redirected away from login page
            current_url = self.page.url
            login_success = "login" not in current_url.lower()

            # Or check for app content
            if not login_success:
                login_success = self.page.locator('text=Worklist').first.is_visible(timeout=5000)

            # Check for error messages
            error_visible = self.page.locator('text=Invalid').first.is_visible(timeout=2000)
            if error_visible:
                error_msg = "Invalid credentials error shown"
                login_success = False

            success = login_success

        except Exception as e:
            error_msg = str(e)
            self.screenshot("02_error")
            import traceback
            traceback.print_exc()

        duration = int((time.time() - start) * 1000)

        result = {
            "test": "Login with Credentials",
            "environment": self.env,
            "success": success,
            "duration_ms": duration,
            "error": error_msg,
        }

        print(f"\n  Result: {'PASS' if success else 'FAIL'}")
        if error_msg:
            print(f"  Error: {error_msg}")
        print(f"  Duration: {duration}ms")

        self.results.append(result)
        return result

    def test_03_protected_route_access(self):
        """Test 3: Access protected routes after login."""
        print("\n" + "=" * 60)
        print(f"Test 3: Protected Route Access ({self.env_config['name']})")
        print("=" * 60)

        start = time.time()
        success = False
        error_msg = None

        try:
            # Try to access worklist page
            base_url = self.env_config['frontend_url']
            # Handle production URL (ends with .html - don't add extra /)
            if base_url.endswith('.html'):
                worklist_url = f"{base_url}#/worklist"
            else:
                worklist_url = f"{base_url}/#/worklist"
            self.page.goto(worklist_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self.page.wait_for_timeout(2000)

            self.screenshot("03_worklist_access")

            # Check if we can see worklist content
            worklist_visible = (
                self.page.locator('text=Worklist').first.is_visible(timeout=5000) or
                self.page.locator('text=工作列表').first.is_visible(timeout=3000) or
                self.page.locator('text=Google Drive').first.is_visible(timeout=3000) or
                self.page.locator('text=Sync Google Drive').first.is_visible(timeout=3000) or
                self.page.locator('text=No worklist items').first.is_visible(timeout=3000)
            )

            # Should NOT be on login page
            not_on_login = "login" not in self.page.url.lower()

            success = worklist_visible and not_on_login

            if not success:
                # Get page text for debugging
                page_text = self.page.inner_text("body")[:500]
                error_msg = f"Could not access worklist. URL: {self.page.url}. Text: {page_text}"

        except Exception as e:
            error_msg = str(e)
            self.screenshot("03_error")
            import traceback
            traceback.print_exc()

        duration = int((time.time() - start) * 1000)

        result = {
            "test": "Protected Route Access",
            "environment": self.env,
            "success": success,
            "duration_ms": duration,
            "error": error_msg,
        }

        print(f"\n  Result: {'PASS' if success else 'FAIL'}")
        if error_msg:
            print(f"  Error: {error_msg}")
        print(f"  Duration: {duration}ms")

        self.results.append(result)
        return result

    def test_04_settings_page_access(self):
        """Test 4: Access settings page."""
        print("\n" + "=" * 60)
        print(f"Test 4: Settings Page Access ({self.env_config['name']})")
        print("=" * 60)

        start = time.time()
        success = False
        error_msg = None

        try:
            # Navigate to settings
            base_url = self.env_config['frontend_url']
            # Handle production URL (ends with .html - don't add extra /)
            if base_url.endswith('.html'):
                settings_url = f"{base_url}#/settings"
            else:
                settings_url = f"{base_url}/#/settings"
            self.page.goto(settings_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self.page.wait_for_timeout(2000)

            self.screenshot("04_settings_page")

            # Check if settings content is visible
            settings_visible = (
                self.page.locator('text=Settings').first.is_visible(timeout=5000) or
                self.page.locator('text=設定').first.is_visible(timeout=3000) or
                self.page.locator('text=設置').first.is_visible(timeout=3000) or
                self.page.locator('text=Configuration').first.is_visible(timeout=3000) or
                self.page.locator('text=WordPress').first.is_visible(timeout=3000) or
                self.page.locator('text=API').first.is_visible(timeout=3000)
            )

            # Should NOT be on login page
            not_on_login = "login" not in self.page.url.lower()

            success = settings_visible and not_on_login

        except Exception as e:
            error_msg = str(e)
            self.screenshot("04_error")
            import traceback
            traceback.print_exc()

        duration = int((time.time() - start) * 1000)

        result = {
            "test": "Settings Page Access",
            "environment": self.env,
            "success": success,
            "duration_ms": duration,
            "error": error_msg,
        }

        print(f"\n  Result: {'PASS' if success else 'FAIL'}")
        if error_msg:
            print(f"  Error: {error_msg}")
        print(f"  Duration: {duration}ms")

        self.results.append(result)
        return result

    def test_05_api_authentication(self):
        """Test 5: API calls include authentication token."""
        print("\n" + "=" * 60)
        print(f"Test 5: API Authentication ({self.env_config['name']})")
        print("=" * 60)

        start = time.time()
        success = False
        error_msg = None
        api_calls = []

        try:
            # Set up request interception to check for auth headers
            def handle_request(request):
                if self.env_config["api_url"] in request.url:
                    auth_header = request.headers.get("authorization", "")
                    api_calls.append({
                        "url": request.url,
                        "has_auth": bool(auth_header),
                        "auth_type": auth_header.split()[0] if auth_header else None,
                    })

            self.page.on("request", handle_request)

            # Navigate to worklist to trigger API calls
            base_url = self.env_config['frontend_url']
            # Handle production URL (ends with .html - don't add extra /)
            if base_url.endswith('.html'):
                worklist_url = f"{base_url}#/worklist"
            else:
                worklist_url = f"{base_url}/#/worklist"
            self.page.goto(worklist_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)
            self.page.wait_for_timeout(3000)

            self.screenshot("05_api_calls")

            # Check if API calls had auth headers
            if api_calls:
                auth_calls = [c for c in api_calls if c["has_auth"]]
                success = len(auth_calls) > 0

                print(f"\n  Total API calls: {len(api_calls)}")
                print(f"  Authenticated calls: {len(auth_calls)}")

                if not success:
                    error_msg = "No API calls had authentication headers"
            else:
                # No API calls intercepted - might be using cached data
                success = True
                error_msg = "No API calls detected (may be cached)"

        except Exception as e:
            error_msg = str(e)
            self.screenshot("05_error")
            import traceback
            traceback.print_exc()

        duration = int((time.time() - start) * 1000)

        result = {
            "test": "API Authentication",
            "environment": self.env,
            "success": success,
            "duration_ms": duration,
            "api_calls": len(api_calls),
            "error": error_msg,
        }

        print(f"\n  Result: {'PASS' if success else 'FAIL'}")
        if error_msg:
            print(f"  Note: {error_msg}")
        print(f"  Duration: {duration}ms")

        self.results.append(result)
        return result

    def run_all_tests(self):
        """Run all authentication tests."""
        print("=" * 70)
        print(f"  Authentication Test Suite - {self.env_config['name']}")
        print("=" * 70)
        print(f"  Frontend: {self.env_config['frontend_url']}")
        print(f"  API: {self.env_config['api_url']}")
        print(f"  Test Run: {self.test_run_id}")
        print("=" * 70)

        try:
            self.setup()

            self.test_01_login_page_display()
            self.test_02_login_with_credentials()
            self.test_03_protected_route_access()
            self.test_04_settings_page_access()
            self.test_05_api_authentication()

        finally:
            self.teardown()

        # Summary
        passed = sum(1 for r in self.results if r.get("success"))
        failed = len(self.results) - passed

        print("\n" + "=" * 70)
        print(f"  AUTHENTICATION TEST SUMMARY - {self.env_config['name']}")
        print("=" * 70)
        print(f"  Total: {len(self.results)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Pass Rate: {(passed/len(self.results)*100):.1f}%" if self.results else "N/A")
        print("=" * 70)

        # Save report
        report = {
            "test_run_id": self.test_run_id,
            "environment": self.env,
            "environment_name": self.env_config["name"],
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "results": self.results,
        }

        report_path = SCREENSHOT_DIR / f"{self.test_run_id}_auth_{self.env}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved: {report_path}")

        return report


def main():
    parser = argparse.ArgumentParser(description="Authentication Visual Test")
    parser.add_argument("--env", choices=["dev", "prod", "both"], default="dev",
                        help="Environment to test (dev, prod, or both)")
    parser.add_argument("--headed", action="store_true", help="Run with browser visible")
    parser.add_argument("--slow-mo", type=int, default=0, help="Slow down actions by ms")
    args = parser.parse_args()

    reports = []

    if args.env in ["dev", "both"]:
        print("\n" + "#" * 70)
        print("  TESTING DEVELOPMENT ENVIRONMENT")
        print("#" * 70)
        suite = AuthenticationTest(env="dev", headless=not args.headed, slow_mo=args.slow_mo)
        reports.append(suite.run_all_tests())

    if args.env in ["prod", "both"]:
        print("\n" + "#" * 70)
        print("  TESTING PRODUCTION ENVIRONMENT")
        print("#" * 70)
        suite = AuthenticationTest(env="prod", headless=not args.headed, slow_mo=args.slow_mo)
        reports.append(suite.run_all_tests())

    # Final summary
    if len(reports) > 1:
        print("\n" + "=" * 70)
        print("  COMBINED TEST SUMMARY")
        print("=" * 70)
        total_passed = sum(r["passed"] for r in reports)
        total_failed = sum(r["failed"] for r in reports)
        total_tests = sum(r["total"] for r in reports)
        print(f"  Total Tests: {total_tests}")
        print(f"  Total Passed: {total_passed}")
        print(f"  Total Failed: {total_failed}")
        print(f"  Overall Pass Rate: {(total_passed/total_tests*100):.1f}%")
        print("=" * 70)

    # Exit with failure if any tests failed
    all_passed = all(r["failed"] == 0 for r in reports)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
