#!/usr/bin/env python3
"""
Image Upload Test for Dev-Prod-Like Environment

This test verifies:
1. Image upload to WordPress Media Library
2. Caption and Alt text setting
3. Image insertion at correct paragraph position
4. Featured image setting

Usage:
    source /tmp/playwright_venv/bin/activate
    python tests/visual/test_image_upload.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

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

# Test directories
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "visual" / "screenshots"
TEST_IMAGE_DIR = PROJECT_ROOT / "tests" / "visual" / "test_images"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
TEST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def create_test_image(filename: str, text: str, size: tuple = (800, 600), color: str = "blue") -> Path:
    """Create a simple test image with text."""
    colors = {
        "blue": (66, 133, 244),
        "green": (52, 168, 83),
        "red": (234, 67, 53),
        "yellow": (251, 188, 5),
    }
    bg_color = colors.get(color, (66, 133, 244))

    # Create image
    img = Image.new('RGB', size, color=bg_color)

    # Save image
    path = TEST_IMAGE_DIR / filename
    img.save(path, 'JPEG', quality=85)
    return path


class ImageUploadTest:
    """Test image upload functionality."""

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
        filename = f"{self.test_run_id}_img_{name}.png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def test_single_image_upload_with_caption(self):
        """Test uploading a single image with caption and alt text."""
        print("\n" + "=" * 60)
        print("Test 1: Single Image Upload with Caption")
        print("=" * 60)

        start = time.time()

        try:
            # Create test image
            test_image_path = create_test_image(
                f"test_image_{self.test_run_id}.jpg",
                "Test Image 1",
                color="blue"
            )
            print(f"  Created test image: {test_image_path}")

            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Enter title
            title = f"Image Upload Test {self.test_run_id}"
            self.page.locator("#title").fill(title)

            # Enter content with multiple paragraphs
            content = """<p>這是第一段文字，圖片應該出現在這段之後。</p>
<p>這是第二段文字。</p>
<p>這是第三段文字。</p>"""

            # Switch to HTML mode
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill(content)

            # Click "Add Media" button
            print("  Clicking Add Media button...")
            add_media_btn = self.page.locator("#insert-media-button, .insert-media")
            add_media_btn.first.click()
            self.page.wait_for_timeout(2000)

            # Wait for media modal
            media_modal = self.page.locator(".media-modal")
            media_modal.wait_for(state="visible", timeout=10000)
            print("  Media modal opened")

            # Click "Upload Files" tab
            upload_tab = self.page.locator(".media-router .media-menu-item:has-text('Upload files')")
            if upload_tab.is_visible(timeout=3000):
                upload_tab.click()
                self.page.wait_for_timeout(500)

            # Upload the image
            print("  Uploading image...")
            file_input = self.page.locator("input[type='file']")
            file_input.set_input_files(str(test_image_path))

            # Wait for upload to complete
            self.page.wait_for_timeout(3000)

            # Check if image appears in media library
            attachment = self.page.locator(".attachment.selected, .attachment.details")
            attachment.first.wait_for(state="visible", timeout=15000)
            print("  Image uploaded successfully")

            # Set Alt Text
            alt_text = "測試圖片的替代文字"
            alt_input = self.page.locator("input[data-setting='alt'], #attachment-details-two-column-alt-text, .setting[data-setting='alt'] input")
            if alt_input.first.is_visible(timeout=3000):
                alt_input.first.fill(alt_text)
                print(f"  Alt text set: {alt_text}")

            # Set Caption
            caption_text = "這是圖片說明文字 (Caption)"
            caption_input = self.page.locator("textarea[data-setting='caption'], #attachment-details-two-column-caption, .setting[data-setting='caption'] textarea")
            if caption_input.first.is_visible(timeout=3000):
                caption_input.first.fill(caption_text)
                print(f"  Caption set: {caption_text}")

            self.screenshot("01_media_modal_with_image")

            # Click "Insert into post"
            insert_btn = self.page.locator(".media-button-insert, .media-button-select")
            insert_btn.first.click()
            self.page.wait_for_timeout(2000)

            print("  Image inserted into post")

            # Save draft
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Take final screenshot
            self.screenshot("02_post_with_image", full_page=True)

            # Verify image is in content
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            content_value = self.page.locator("#content").input_value()

            has_image = "<img" in content_value or "wp-image" in content_value
            has_caption = caption_text in content_value or "wp-caption" in content_value

            # Extract post ID
            import re
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            result = {
                "test": "Single Image Upload",
                "success": has_image,
                "post_id": post_id,
                "has_image_tag": has_image,
                "has_caption": has_caption,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if has_image else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  Image tag found: {has_image}")
            print(f"  Caption in content: {has_caption}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("01_error")
            print(f"  ERROR: {str(e)}")
            self.results.append({
                "test": "Single Image Upload",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_featured_image(self):
        """Test setting featured image."""
        print("\n" + "=" * 60)
        print("Test 2: Featured Image Setting")
        print("=" * 60)

        start = time.time()

        try:
            # Create test image
            test_image_path = create_test_image(
                f"featured_{self.test_run_id}.jpg",
                "Featured Image",
                color="green"
            )
            print(f"  Created featured image: {test_image_path}")

            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Enter title
            title = f"Featured Image Test {self.test_run_id}"
            self.page.locator("#title").fill(title)

            # Enter simple content
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill("<p>這篇文章測試特色圖片功能。</p>")

            # Click "Set featured image" link
            print("  Looking for Featured Image panel...")
            featured_link = self.page.locator("#set-post-thumbnail, a:has-text('Set featured image')")

            if featured_link.first.is_visible(timeout=5000):
                featured_link.first.click()
                self.page.wait_for_timeout(2000)
                print("  Featured image panel opened")

                # Wait for media modal
                media_modal = self.page.locator(".media-modal")
                media_modal.wait_for(state="visible", timeout=10000)

                # Click "Upload Files" tab
                upload_tab = self.page.locator(".media-router .media-menu-item:has-text('Upload files')")
                if upload_tab.is_visible(timeout=3000):
                    upload_tab.click()
                    self.page.wait_for_timeout(500)

                # Upload the image
                print("  Uploading featured image...")
                file_input = self.page.locator("input[type='file']")
                file_input.set_input_files(str(test_image_path))

                # Wait for upload
                self.page.wait_for_timeout(3000)

                # Select the uploaded image
                attachment = self.page.locator(".attachment.selected, .attachment.details")
                attachment.first.wait_for(state="visible", timeout=15000)

                # Set Alt text for featured image
                alt_input = self.page.locator("input[data-setting='alt']")
                if alt_input.first.is_visible(timeout=2000):
                    alt_input.first.fill("特色圖片替代文字")

                self.screenshot("03_featured_image_modal")

                # Click "Set featured image" button
                set_btn = self.page.locator(".media-button-select, button:has-text('Set featured image')")
                set_btn.first.click()
                self.page.wait_for_timeout(2000)

                print("  Featured image set")

            # Save draft
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Take screenshot
            self.screenshot("04_post_with_featured_image", full_page=True)

            # Verify featured image is set
            featured_thumbnail = self.page.locator("#postimagediv img, #set-post-thumbnail img")
            has_featured = featured_thumbnail.first.is_visible(timeout=3000)

            # Extract post ID
            import re
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            result = {
                "test": "Featured Image",
                "success": has_featured,
                "post_id": post_id,
                "has_featured_image": has_featured,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if has_featured else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  Featured image visible: {has_featured}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("03_error")
            print(f"  ERROR: {str(e)}")
            self.results.append({
                "test": "Featured Image",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_multiple_images_with_positions(self):
        """Test uploading multiple images at different positions."""
        print("\n" + "=" * 60)
        print("Test 3: Multiple Images at Different Positions")
        print("=" * 60)

        start = time.time()

        try:
            # Create test images
            images = []
            for i, color in enumerate(["blue", "green", "red"], 1):
                path = create_test_image(
                    f"multi_{i}_{self.test_run_id}.jpg",
                    f"Image {i}",
                    color=color
                )
                images.append({
                    "path": path,
                    "caption": f"圖片 {i} 的說明文字",
                    "alt": f"圖片 {i} 替代文字",
                    "position": i - 1  # 0 = before first, 1 = after first, etc.
                })
            print(f"  Created {len(images)} test images")

            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Enter title
            title = f"Multiple Images Test {self.test_run_id}"
            self.page.locator("#title").fill(title)

            # Build content with placeholders for images
            # We'll insert images manually at correct positions
            content_parts = [
                "<p>第一段：這是文章開頭。</p>",
                "<p>第二段：這是中間內容。</p>",
                "<p>第三段：這是更多內容。</p>",
                "<p>第四段：這是結尾段落。</p>",
            ]

            # Switch to HTML mode and enter initial content
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill("\n".join(content_parts))

            # Upload each image
            for idx, img_info in enumerate(images):
                print(f"\n  Uploading image {idx + 1}...")

                # Click Add Media
                add_media_btn = self.page.locator("#insert-media-button")
                add_media_btn.click()
                self.page.wait_for_timeout(2000)

                # Wait for modal
                media_modal = self.page.locator(".media-modal")
                media_modal.wait_for(state="visible", timeout=10000)

                # Click Upload tab
                upload_tab = self.page.locator(".media-router .media-menu-item:has-text('Upload files')")
                if upload_tab.is_visible(timeout=3000):
                    upload_tab.click()
                    self.page.wait_for_timeout(500)

                # Upload image
                file_input = self.page.locator("input[type='file']")
                file_input.set_input_files(str(img_info["path"]))
                self.page.wait_for_timeout(3000)

                # Wait for selection
                attachment = self.page.locator(".attachment.selected")
                attachment.first.wait_for(state="visible", timeout=15000)

                # Set alt text
                alt_input = self.page.locator("input[data-setting='alt']")
                if alt_input.first.is_visible(timeout=2000):
                    alt_input.first.fill(img_info["alt"])

                # Set caption
                caption_input = self.page.locator("textarea[data-setting='caption']")
                if caption_input.first.is_visible(timeout=2000):
                    caption_input.first.fill(img_info["caption"])

                # Insert
                insert_btn = self.page.locator(".media-button-insert")
                insert_btn.first.click()
                self.page.wait_for_timeout(1500)

                print(f"    Image {idx + 1} inserted with caption: {img_info['caption']}")

            # Save draft
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Take screenshot
            self.screenshot("05_multiple_images", full_page=True)

            # Verify images in content
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            content_value = self.page.locator("#content").input_value()

            image_count = content_value.count("<img") + content_value.count("[caption")
            has_all_images = image_count >= len(images)

            # Extract post ID
            import re
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            result = {
                "test": "Multiple Images",
                "success": has_all_images,
                "post_id": post_id,
                "expected_images": len(images),
                "found_images": image_count,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if has_all_images else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  Expected images: {len(images)}")
            print(f"  Found in content: {image_count}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("05_error")
            print(f"  ERROR: {str(e)}")
            self.results.append({
                "test": "Multiple Images",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def test_image_paragraph_positioning(self):
        """
        Test 4: Verify images are inserted at CORRECT paragraph positions.

        This test simulates what Computer Use should do:
        - Position 0: Image appears BEFORE the first paragraph
        - Position 1: Image appears AFTER paragraph 1
        - Position 2: Image appears AFTER paragraph 2

        The test verifies the final HTML structure matches expected positions.
        """
        print("\n" + "=" * 60)
        print("Test 4: Image Paragraph Positioning Verification")
        print("=" * 60)

        start = time.time()

        try:
            # Create test images with specific positions
            images = [
                {"color": "red", "position": 0, "marker": "IMG_POS_0"},    # Before first paragraph
                {"color": "green", "position": 2, "marker": "IMG_POS_2"},  # After paragraph 2
            ]

            for img in images:
                img["path"] = create_test_image(
                    f"pos_{img['position']}_{self.test_run_id}.jpg",
                    f"Position {img['position']}",
                    color=img["color"]
                )
                img["caption"] = f"這是位置 {img['position']} 的圖片 ({img['marker']})"
                img["alt"] = f"Position {img['position']} image"

            print(f"  Created {len(images)} test images with positions: {[img['position'] for img in images]}")

            # Navigate to new post
            self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=15000)

            if "wp-login" in self.page.url:
                self._login()
                self.page.goto(f"{DEV_URL}/wp-admin/post-new.php", timeout=30000)
                self.page.wait_for_load_state("networkidle", timeout=15000)

            # Enter title
            title = f"Image Position Test {self.test_run_id}"
            self.page.locator("#title").fill(title)

            # Create content with 4 clearly marked paragraphs
            paragraphs = [
                "<p>【第一段 PARA_1】這是第一段文字內容，測試圖片定位。</p>",
                "<p>【第二段 PARA_2】這是第二段文字內容，圖片應該在此段之前或之後出現。</p>",
                "<p>【第三段 PARA_3】這是第三段文字內容，用於驗證圖片插入位置。</p>",
                "<p>【第四段 PARA_4】這是第四段文字內容，結尾段落。</p>",
            ]

            # Enter initial content
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            self.page.locator("#content").fill("\n".join(paragraphs))
            print("  Content with 4 paragraphs entered")

            # Sort images by position (insert from end to start to maintain positions)
            sorted_images = sorted(images, key=lambda x: x["position"], reverse=True)

            # Upload and insert each image at correct position using HTML manipulation
            for img in sorted_images:
                print(f"\n  Uploading image for position {img['position']}...")

                # First, upload the image to Media Library
                add_media_btn = self.page.locator("#insert-media-button")
                add_media_btn.click()
                self.page.wait_for_timeout(2000)

                media_modal = self.page.locator(".media-modal")
                media_modal.wait_for(state="visible", timeout=10000)

                upload_tab = self.page.locator(".media-router .media-menu-item:has-text('Upload files')")
                if upload_tab.is_visible(timeout=3000):
                    upload_tab.click()
                    self.page.wait_for_timeout(500)

                file_input = self.page.locator("input[type='file']")
                file_input.set_input_files(str(img["path"]))
                self.page.wait_for_timeout(3000)

                attachment = self.page.locator(".attachment.selected")
                attachment.first.wait_for(state="visible", timeout=15000)

                # Set alt and caption
                alt_input = self.page.locator("input[data-setting='alt']")
                if alt_input.first.is_visible(timeout=2000):
                    alt_input.first.fill(img["alt"])

                caption_input = self.page.locator("textarea[data-setting='caption']")
                if caption_input.first.is_visible(timeout=2000):
                    caption_input.first.fill(img["caption"])

                # Get the image URL from the attachment details
                # Try multiple selectors for compatibility
                img_src = None
                selectors = [
                    ".attachment-details img",
                    ".details-image img",
                    ".thumbnail-image img",
                    ".attachment.selected img",
                    ".attachment-info .thumbnail img",
                ]
                for selector in selectors:
                    try:
                        loc = self.page.locator(selector).first
                        if loc.is_visible(timeout=2000):
                            img_src = loc.get_attribute("src")
                            if img_src:
                                break
                    except:
                        pass

                if not img_src:
                    # Fallback: get URL from the URL input field if available
                    try:
                        url_input = self.page.locator("input[data-setting='url']")
                        if url_input.first.is_visible(timeout=2000):
                            img_src = url_input.first.input_value()
                    except:
                        pass

                img["src"] = img_src or f"http://localhost:8001/wp-content/uploads/pos_{img['position']}.jpg"
                print(f"    Image URL: {img['src']}")

                # Close modal without inserting (we'll manually insert at correct position)
                close_btn = self.page.locator(".media-modal-close")
                close_btn.click()
                self.page.wait_for_timeout(500)

            # Now manually insert images at correct positions in HTML
            print("\n  Inserting images at correct positions...")
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)

            current_content = self.page.locator("#content").input_value()
            print(f"    Current content length: {len(current_content)}")

            # Build image HTML for each image
            for img in sorted_images:
                # Create WordPress caption shortcode
                img_html = f'''
[caption id="" align="alignnone" width="800"]<img class="size-full" src="{img.get('src', '')}" alt="{img['alt']}" width="800" height="600" /> {img['caption']}[/caption]
'''
                position = img["position"]

                if position == 0:
                    # Insert at the very beginning
                    current_content = img_html + current_content
                    print(f"    Inserted image at position 0 (before first paragraph)")
                else:
                    # Insert after paragraph N
                    # Find the Nth </p> tag
                    parts = current_content.split("</p>")
                    if position <= len(parts):
                        # Insert after the Nth paragraph
                        parts[position - 1] = parts[position - 1] + "</p>" + img_html
                        current_content = "</p>".join(parts[position:])
                        current_content = "</p>".join(parts[:position]) + current_content
                        print(f"    Inserted image after paragraph {position}")
                    else:
                        # Append at end
                        current_content = current_content + img_html
                        print(f"    Position {position} exceeds paragraphs, appended at end")

            # Update content
            self.page.locator("#content").fill(current_content)
            print("  Content updated with positioned images")

            # Save draft
            self.page.locator("#save-post").click()
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Take screenshot
            self.screenshot("06_positioned_images", full_page=True)

            # Verify image positions
            self.page.locator("#content-html").click()
            self.page.wait_for_timeout(300)
            final_content = self.page.locator("#content").input_value()

            # Check positions
            position_checks = []

            for img in images:
                marker = img["marker"]
                position = img["position"]

                # Find marker position in content
                marker_pos = final_content.find(marker)

                if position == 0:
                    # Should appear before PARA_1
                    para1_pos = final_content.find("PARA_1")
                    correct = marker_pos < para1_pos if marker_pos >= 0 and para1_pos >= 0 else False
                    position_checks.append({
                        "image": marker,
                        "expected": "Before PARA_1",
                        "correct": correct,
                        "marker_pos": marker_pos,
                        "para_pos": para1_pos
                    })
                else:
                    # Should appear after PARA_N
                    para_marker = f"PARA_{position}"
                    next_para_marker = f"PARA_{position + 1}"
                    para_pos = final_content.find(para_marker)
                    next_para_pos = final_content.find(next_para_marker)

                    # Image marker should be between para_pos and next_para_pos
                    if marker_pos >= 0 and para_pos >= 0:
                        if next_para_pos >= 0:
                            correct = para_pos < marker_pos < next_para_pos
                        else:
                            correct = para_pos < marker_pos
                    else:
                        correct = False

                    position_checks.append({
                        "image": marker,
                        "expected": f"After PARA_{position}, Before PARA_{position + 1}",
                        "correct": correct,
                        "marker_pos": marker_pos,
                        "para_pos": para_pos,
                        "next_para_pos": next_para_pos
                    })

            all_correct = all(check["correct"] for check in position_checks)

            # Extract post ID
            import re
            post_id_match = re.search(r'post=(\d+)', self.page.url)
            post_id = post_id_match.group(1) if post_id_match else None

            duration = int((time.time() - start) * 1000)

            # Print position verification results
            print("\n  Position Verification:")
            for check in position_checks:
                status = "CORRECT" if check["correct"] else "WRONG"
                print(f"    {check['image']}: {status} - Expected: {check['expected']}")

            result = {
                "test": "Image Paragraph Positioning",
                "success": all_correct,
                "post_id": post_id,
                "position_checks": position_checks,
                "all_positions_correct": all_correct,
                "duration_ms": duration
            }

            print(f"\n  Result: {'PASS' if all_correct else 'FAIL'}")
            print(f"  Post ID: {post_id}")
            print(f"  All positions correct: {all_correct}")
            print(f"  Duration: {duration}ms")

            self.results.append(result)
            return result

        except Exception as e:
            self.screenshot("06_error")
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results.append({
                "test": "Image Paragraph Positioning",
                "success": False,
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def run_all_tests(self):
        """Run all image upload tests."""
        print("=" * 70)
        print("  Image Upload Test Suite")
        print("=" * 70)
        print(f"  Target: {DEV_URL}")
        print(f"  Test Run: {self.test_run_id}")
        print("=" * 70)

        try:
            self.setup()

            self.test_single_image_upload_with_caption()
            self.test_featured_image()
            self.test_multiple_images_with_positions()
            self.test_image_paragraph_positioning()

        finally:
            self.teardown()

        # Summary
        passed = sum(1 for r in self.results if r.get("success"))
        failed = len(self.results) - passed

        print("\n" + "=" * 70)
        print("  IMAGE UPLOAD TEST SUMMARY")
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

        report_path = SCREENSHOT_DIR / f"{self.test_run_id}_image_upload_report.json"
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

    suite = ImageUploadTest(headless=not args.headed, slow_mo=args.slow_mo)
    report = suite.run_all_tests()

    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
