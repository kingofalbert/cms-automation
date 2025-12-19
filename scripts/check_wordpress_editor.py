#!/usr/bin/env python3
"""Check WordPress editor type and SEO plugin.

This script logs into WordPress and detects:
1. Which editor is being used (Gutenberg vs Classic)
2. Which SEO plugin is installed (Yoast, Rank Math, Lite SEO, etc.)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


async def check_wordpress_editor():
    """Log into WordPress and check which editor is used."""

    # Load credentials from environment or .env
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    cms_url = os.getenv("PROD_WORDPRESS_URL") or os.getenv("CMS_BASE_URL", "https://admin.epochtimes.com")

    # Two-stage login credentials
    # First layer: site-level login (djy account)
    first_layer_user = os.getenv("PROD_FIRST_LAYER_USERNAME") or os.getenv("CMS_HTTP_AUTH_USERNAME")
    first_layer_pass = os.getenv("PROD_FIRST_LAYER_PASSWORD") or os.getenv("CMS_HTTP_AUTH_PASSWORD")

    # Second layer: actual user account
    username = os.getenv("PROD_USERNAME") or os.getenv("CMS_USERNAME")
    password = (os.getenv("PROD_PASSWORD") or os.getenv("CMS_APPLICATION_PASSWORD", "")).strip('"').rstrip(')')

    if not first_layer_user or not first_layer_pass:
        print("❌ Missing first layer credentials (PROD_FIRST_LAYER_USERNAME/PASSWORD)")
        return

    if not username or not password:
        print("❌ Missing user credentials (PROD_USERNAME/PASSWORD)")
        return

    print("=" * 60)
    print("🔍 WordPress Editor Type Checker")
    print("=" * 60)
    print(f"URL: {cms_url}")
    print(f"HTTP Basic Auth User: {first_layer_user}")
    print(f"WordPress User: {username}")
    print("=" * 60)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)

        # Set HTTP Basic Auth credentials
        context = await browser.new_context(
            http_credentials={
                "username": first_layer_user,
                "password": first_layer_pass
            }
        )
        page = await context.new_page()

        try:
            # Step 1: Go to login page (HTTP Basic Auth handled automatically)
            print("\n📍 Step 1: Navigating to WordPress login (with HTTP Basic Auth)...")
            login_url = f"{cms_url}/wp-login.php"
            await page.goto(login_url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Check if we're on login page
            if "wp-login" in page.url:
                print("✅ Login page loaded (HTTP Basic Auth passed)")
            else:
                print(f"⚠️ Unexpected URL: {page.url}")

            # Step 2: WordPress login
            print("\n📍 Step 2: WordPress login...")
            await page.fill("#user_login", username)
            await page.fill("#user_pass", password)
            await page.click("#wp-submit")

            # Wait for redirect
            await page.wait_for_load_state("networkidle", timeout=30000)

            if "wp-admin" in page.url:
                print("✅ Login successful!")
            else:
                print(f"❌ Login may have failed. Current URL: {page.url}")
                # Take screenshot
                await page.screenshot(path="login_result.png")
                print("📸 Screenshot saved: login_result.png")
                return

            # Step 3: Go to new post page
            print("\n📍 Step 3: Navigating to New Post page...")
            new_post_url = f"{cms_url}/wp-admin/post-new.php"
            await page.goto(new_post_url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Step 4: Detect editor type
            print("\n📍 Step 4: Detecting editor type...")

            editor_info = {
                "type": "unknown",
                "has_gutenberg": False,
                "has_classic": False,
                "has_custom_html_block": False,
                "gutenberg_version": None,
            }

            # Check for Gutenberg (Block Editor)
            gutenberg_selectors = [
                ".block-editor",
                ".editor-styles-wrapper",
                ".wp-block-post-content",
                "[aria-label='Block: Paragraph']",
                ".components-popover",
                "#editor .edit-post-layout",
            ]

            for selector in gutenberg_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        editor_info["has_gutenberg"] = True
                        editor_info["type"] = "gutenberg"
                        print(f"  ✅ Found Gutenberg element: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # Check for Classic Editor
            classic_selectors = [
                "#wp-content-editor-container",
                "#content",  # TinyMCE
                "#tinymce",
                ".mce-toolbar",
                "#wp-content-wrap.tmce-active",
            ]

            for selector in classic_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        editor_info["has_classic"] = True
                        if not editor_info["has_gutenberg"]:
                            editor_info["type"] = "classic"
                        print(f"  ✅ Found Classic element: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # If Gutenberg, check for Custom HTML block
            if editor_info["has_gutenberg"]:
                print("\n📍 Step 5: Checking for Custom HTML block...")
                try:
                    # Click the inserter button
                    inserter = await page.wait_for_selector(
                        'button[aria-label="Toggle block inserter"], button.editor-document-tools__inserter-toggle',
                        timeout=5000
                    )
                    if inserter:
                        await inserter.click()
                        await page.wait_for_timeout(1000)

                        # Search for Custom HTML
                        search_input = await page.wait_for_selector(
                            'input[placeholder*="Search"], input.components-search-control__input',
                            timeout=3000
                        )
                        if search_input:
                            await search_input.fill("Custom HTML")
                            await page.wait_for_timeout(1000)

                            # Check if Custom HTML block appears
                            html_block = await page.query_selector(
                                'button[class*="block-type"][aria-label*="HTML"], '
                                'button[class*="editor-block-list-item-html"]'
                            )
                            if html_block:
                                editor_info["has_custom_html_block"] = True
                                print("  ✅ Custom HTML block is AVAILABLE")
                            else:
                                print("  ⚠️ Custom HTML block NOT found in search")

                        # Close inserter
                        await page.keyboard.press("Escape")

                except Exception as e:
                    print(f"  ⚠️ Could not check Custom HTML block: {e}")

            # Take screenshot
            await page.screenshot(path="editor_check.png", full_page=True)
            print("\n📸 Screenshot saved: editor_check.png")

            # Print results
            print("\n" + "=" * 60)
            print("📊 RESULTS")
            print("=" * 60)
            print(f"Editor Type: {editor_info['type'].upper()}")
            print(f"Has Gutenberg (Block Editor): {'✅ Yes' if editor_info['has_gutenberg'] else '❌ No'}")
            print(f"Has Classic Editor: {'✅ Yes' if editor_info['has_classic'] else '❌ No'}")
            print(f"Custom HTML Block Available: {'✅ Yes' if editor_info['has_custom_html_block'] else '❌ No / Unknown'}")
            print("=" * 60)

            # Step 6: Check for SEO plugins on the post edit page
            print("\n📍 Step 6: Detecting SEO plugin...")

            seo_info = {
                "plugin": "unknown",
                "yoast": False,
                "rank_math": False,
                "lite_seo": False,
                "all_in_one_seo": False,
                "seopress": False,
            }

            # Check for Yoast SEO
            yoast_selectors = [
                "#wpseo_meta",
                "#yoast-seo-settings",
                "#yoast_wpseo_focuskw",
                ".yoast-seo-meta-section",
                "#wpseo-metabox-root",
                "[data-id='yoast-seo']",
            ]

            for selector in yoast_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        seo_info["yoast"] = True
                        seo_info["plugin"] = "Yoast SEO"
                        print(f"  ✅ Found Yoast SEO: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # Check for Rank Math
            rank_math_selectors = [
                "#rank-math-metabox",
                ".rank-math-editor",
                "[data-id='rank-math']",
                "#rank_math_metabox",
                ".rank-math-seo-analysis",
            ]

            for selector in rank_math_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        seo_info["rank_math"] = True
                        seo_info["plugin"] = "Rank Math"
                        print(f"  ✅ Found Rank Math: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # Check for Lite SEO
            lite_seo_selectors = [
                "#lite-seo-metabox",
                "#lite_seo",
                ".lite-seo-meta-box",
                "#lite-seo-settings",
                "[id*='lite-seo']",
                "[id*='lite_seo']",
                "[class*='lite-seo']",
                # Additional selectors based on visual inspection
                "h2.hndle:has-text('Lite SEO')",
                ".postbox:has(h2:text('Lite SEO'))",
                "#postbox-container-2 .postbox",  # Check metaboxes
            ]

            # Also try to find by text content
            try:
                lite_seo_text = await page.locator("text=Lite SEO").first.is_visible(timeout=2000)
                if lite_seo_text:
                    seo_info["lite_seo"] = True
                    seo_info["plugin"] = "Lite SEO"
                    print("  ✅ Found Lite SEO by text content")
            except:
                pass

            for selector in lite_seo_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        seo_info["lite_seo"] = True
                        seo_info["plugin"] = "Lite SEO"
                        print(f"  ✅ Found Lite SEO: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # Check for All in One SEO
            aioseo_selectors = [
                "#aioseo-settings",
                "#aioseo-post-settings",
                ".aioseo-post-general",
                "[data-id='aioseo']",
            ]

            for selector in aioseo_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        seo_info["all_in_one_seo"] = True
                        seo_info["plugin"] = "All in One SEO"
                        print(f"  ✅ Found All in One SEO: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # Check for SEOPress
            seopress_selectors = [
                "#seopress-metabox",
                ".seopress-metabox",
                "#seopress_titles_title_meta",
            ]

            for selector in seopress_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        seo_info["seopress"] = True
                        seo_info["plugin"] = "SEOPress"
                        print(f"  ✅ Found SEOPress: {selector}")
                        break
                except PlaywrightTimeout:
                    pass

            # If still unknown, go to plugins page to check
            if seo_info["plugin"] == "unknown":
                print("\n📍 Step 7: Checking Plugins page...")
                plugins_url = f"{cms_url}/wp-admin/plugins.php"
                await page.goto(plugins_url, timeout=30000)
                await page.wait_for_load_state("networkidle")

                # Get page content
                page_content = await page.content()

                # Check for known SEO plugins
                seo_plugins_to_check = [
                    ("Yoast SEO", "yoast"),
                    ("Rank Math", "rank_math"),
                    ("Lite SEO", "lite_seo"),
                    ("All in One SEO", "all_in_one_seo"),
                    ("SEOPress", "seopress"),
                    ("The SEO Framework", "seo_framework"),
                ]

                for plugin_name, key in seo_plugins_to_check:
                    if plugin_name.lower() in page_content.lower():
                        seo_info[key] = True
                        if seo_info["plugin"] == "unknown":
                            seo_info["plugin"] = plugin_name
                        print(f"  ✅ Found {plugin_name} in plugins list")

                # Take screenshot of plugins page
                await page.screenshot(path="plugins_check.png", full_page=True)
                print("📸 Screenshot saved: plugins_check.png")

            # Take final screenshot
            await page.screenshot(path="seo_check.png", full_page=True)
            print("\n📸 Screenshot saved: seo_check.png")

            # Print results
            print("\n" + "=" * 60)
            print("📊 RESULTS")
            print("=" * 60)
            print(f"Editor Type: {editor_info['type'].upper()}")
            print(f"Has Gutenberg (Block Editor): {'✅ Yes' if editor_info['has_gutenberg'] else '❌ No'}")
            print(f"Has Classic Editor: {'✅ Yes' if editor_info['has_classic'] else '❌ No'}")
            print(f"Custom HTML Block Available: {'✅ Yes' if editor_info['has_custom_html_block'] else '❌ No / Unknown'}")
            print("-" * 60)
            print(f"SEO Plugin: {seo_info['plugin'].upper()}")
            print(f"  - Yoast SEO: {'✅' if seo_info['yoast'] else '❌'}")
            print(f"  - Rank Math: {'✅' if seo_info['rank_math'] else '❌'}")
            print(f"  - Lite SEO: {'✅' if seo_info['lite_seo'] else '❌'}")
            print(f"  - All in One SEO: {'✅' if seo_info['all_in_one_seo'] else '❌'}")
            print(f"  - SEOPress: {'✅' if seo_info['seopress'] else '❌'}")
            print("=" * 60)

            # Recommendations
            print("\n💡 RECOMMENDATIONS:")
            if editor_info["type"] == "gutenberg" and editor_info["has_custom_html_block"]:
                print("  ✅ FAQ Schema JSON-LD can be added via Custom HTML block")
            elif editor_info["type"] == "gutenberg":
                print("  ⚠️ Gutenberg detected but Custom HTML block status unknown")
                print("     FAQ Schema will use graceful skip if block not found")
            elif editor_info["type"] == "classic":
                print("  ⚠️ Classic Editor detected - no Custom HTML block")
                print("     FAQ Schema will be gracefully skipped")
                print("     Consider switching to Gutenberg or using a plugin for JSON-LD")
            else:
                print("  ❓ Editor type unknown - please check screenshot")

            if seo_info["plugin"] != "unknown":
                print(f"\n  📌 SEO Plugin: {seo_info['plugin']}")
                print(f"     Use {seo_info['plugin']}'s selectors for SEO field configuration")
            else:
                print("\n  ⚠️ No known SEO plugin detected")
                print("     Check plugins_check.png for manual verification")

            return {"editor": editor_info, "seo": seo_info}

        except Exception as e:
            print(f"\n❌ Error: {e}")
            await page.screenshot(path="error.png")
            print("📸 Error screenshot saved: error.png")
            raise

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(check_wordpress_editor())
