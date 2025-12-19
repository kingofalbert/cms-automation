#!/usr/bin/env python3
"""
Test script to verify dev-prod-like environment matches production configuration.

This script validates:
1. HTTP Basic Auth (djy/djy2013)
2. Classic Editor (not Gutenberg)
3. SEO Plugin (Slim SEO as Lite SEO alternative)
"""

import os
import sys
from playwright.sync_api import sync_playwright

# Dev environment configuration - use 127.0.0.1 to avoid DNS resolution issues
DEV_URL = "http://127.0.0.1:8001"
HTTP_AUTH_USER = "djy"
HTTP_AUTH_PASS = "djy2013"
WP_USER = "admin"
WP_PASS = "admin"
MAX_RETRIES = 3

def main():
    print("=" * 60)
    print("Dev-Prod-Like Environment Verification")
    print("=" * 60)
    print(f"URL: {DEV_URL}")
    print(f"HTTP Basic Auth: {HTTP_AUTH_USER}/*****")
    print(f"WordPress User: {WP_USER}")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Create context with HTTP Basic Auth
        context = browser.new_context(
            http_credentials={
                "username": HTTP_AUTH_USER,
                "password": HTTP_AUTH_PASS
            },
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        results = {
            "http_basic_auth": False,
            "wordpress_login": False,
            "classic_editor": False,
            "seo_plugin": None
        }

        try:
            # Step 1: Test HTTP Basic Auth (with retries)
            print("Step 1: Testing HTTP Basic Auth...")
            for attempt in range(MAX_RETRIES):
                try:
                    page.goto(f"{DEV_URL}/wp-login.php", timeout=30000)
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        print(f"  Attempt {attempt + 1} failed, retrying in 3s...")
                        page.wait_for_timeout(3000)
                    else:
                        raise e

            if page.url.startswith(DEV_URL):
                results["http_basic_auth"] = True
                print("  HTTP Basic Auth passed")
            else:
                print(f"  FAILED: Unexpected URL {page.url}")

            # Step 2: WordPress Login
            print("\nStep 2: WordPress Login...")
            page.fill("#user_login", WP_USER)
            page.fill("#user_pass", WP_PASS)
            page.click("#wp-submit")
            page.wait_for_load_state("networkidle", timeout=15000)

            if "/wp-admin" in page.url or "dashboard" in page.url.lower():
                results["wordpress_login"] = True
                print("  WordPress login successful")
            else:
                print(f"  Current URL: {page.url}")
                # Check if we're on the dashboard
                if page.locator("#wpbody").is_visible():
                    results["wordpress_login"] = True
                    print("  WordPress login successful (dashboard visible)")

            # Step 3: Navigate to new post
            print("\nStep 3: Navigating to New Post page...")
            page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # Take screenshot
            page.screenshot(path="dev_editor_check.png")
            print("  Screenshot saved: dev_editor_check.png")

            # Step 4: Detect editor type
            print("\nStep 4: Detecting editor type...")

            # Classic Editor indicators
            classic_selectors = [
                "#wp-content-editor-container",  # Classic editor container
                "#content",                       # Classic textarea
                "#wp-content-wrap.html-active",  # HTML mode active
                "#wp-content-wrap.tmce-active",  # TinyMCE mode active
                ".wp-editor-area",               # Editor area
            ]

            # Gutenberg indicators
            gutenberg_selectors = [
                ".block-editor",
                ".edit-post-visual-editor",
                ".wp-block",
                "[data-type='core/paragraph']",
            ]

            has_classic = False
            has_gutenberg = False

            for selector in classic_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=2000):
                        has_classic = True
                        print(f"  Found Classic element: {selector}")
                        break
                except:
                    pass

            for selector in gutenberg_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=2000):
                        has_gutenberg = True
                        print(f"  Found Gutenberg element: {selector}")
                        break
                except:
                    pass

            results["classic_editor"] = has_classic and not has_gutenberg

            # Step 5: Detect SEO plugin
            print("\nStep 5: Detecting SEO plugin...")

            # Scroll down to see metaboxes
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

            seo_plugins = {
                "Slim SEO": [
                    "h2.hndle:has-text('Slim SEO')",
                    "#slim-seo",
                    ".slim-seo-metabox",
                    "text=Slim SEO",
                ],
                "Lite SEO": [
                    "h2.hndle:has-text('Lite SEO')",
                    "#lite_seo",
                    "text=Lite SEO",
                ],
                "Yoast SEO": [
                    "#wpseo_meta",
                    ".yoast-seo-metabox",
                    "text=Yoast SEO",
                ],
                "Rank Math": [
                    "#rank_math_metabox",
                    ".rank-math-editor",
                    "text=Rank Math",
                ],
            }

            detected_seo = None
            for plugin_name, selectors in seo_plugins.items():
                for selector in selectors:
                    try:
                        if page.locator(selector).first.is_visible(timeout=2000):
                            detected_seo = plugin_name
                            print(f"  Found {plugin_name}: {selector}")
                            break
                    except:
                        pass
                if detected_seo:
                    break

            results["seo_plugin"] = detected_seo

            # Take SEO screenshot
            page.screenshot(path="dev_seo_check.png", full_page=True)
            print("  Screenshot saved: dev_seo_check.png")

        except Exception as e:
            print(f"\nError: {e}")
            page.screenshot(path="dev_error.png")
            print("  Error screenshot saved: dev_error.png")

        finally:
            browser.close()

        # Print results
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS")
        print("=" * 60)

        checks = [
            ("HTTP Basic Auth", results["http_basic_auth"], "Production uses djy/djy2013"),
            ("WordPress Login", results["wordpress_login"], "admin/admin"),
            ("Classic Editor", results["classic_editor"], "Not Gutenberg"),
            ("SEO Plugin", results["seo_plugin"] is not None, results["seo_plugin"] or "None detected"),
        ]

        all_passed = True
        for name, passed, detail in checks:
            status = "PASS" if passed else "FAIL"
            icon = "" if passed else ""
            print(f"  {icon} {name}: {status} ({detail})")
            if not passed:
                all_passed = False

        print("=" * 60)

        if all_passed:
            print("\nDev environment matches production configuration!")
            return 0
        else:
            print("\nSome checks failed. See details above.")
            return 1

if __name__ == "__main__":
    sys.exit(main())
