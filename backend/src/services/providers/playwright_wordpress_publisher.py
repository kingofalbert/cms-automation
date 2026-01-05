"""Playwright-based WordPress publisher (free alternative to Computer Use API)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

from playwright.async_api import Browser, Page, async_playwright

from src.api.schemas.seo import SEOMetadata
from src.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class PlaywrightWordPressPublisher:
    """Free WordPress publisher using Playwright automation.

    This is a cost-free alternative to Anthropic Computer Use API.
    Uses Playwright + Chrome DevTools for precise automation.

    Requires:
    - Detailed CSS selectors for your WordPress site
    - Exact waiting times for page loads
    - Configuration file with element selectors
    """

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize Playwright publisher.

        Args:
            config_path: Path to WordPress selectors configuration JSON file
        """
        self.browser: Browser | None = None
        self.page: Page | None = None

        # Load WordPress selectors configuration
        if config_path:
            self.config = self._load_config(config_path)
        else:
            # Use default selectors (may not work for all WordPress sites)
            self.config = self._get_default_config()

        logger.info(
            "playwright_publisher_initialized",
            editor_type=self.config.get("metadata", {}).get("editor_type"),
            seo_plugin=self.config.get("metadata", {}).get("seo_plugin"),
        )

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load WordPress configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            logger.info("wordpress_config_loaded", path=config_path)
            return config
        except Exception as e:
            logger.error(
                "config_load_failed",
                path=config_path,
                error=str(e),
            )
            # Fall back to default config
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default WordPress selectors configuration.

        This works for standard WordPress with Gutenberg editor and Yoast SEO.
        May need customization for your specific setup.

        Returns:
            Default configuration dictionary
        """
        return {
            "metadata": {
                "editor_type": "Gutenberg",
                "seo_plugin": "Yoast SEO",
                "note": "Default configuration - may need customization",
            },
            "login": {
                "username_field": "#user_login",
                "password_field": "#user_pass",
                "submit_button": "#wp-submit",
            },
            "dashboard": {
                "posts_menu": "#menu-posts",
                "new_post_link": "#menu-posts a[href*='post-new']",
            },
            "editor": {
                "title_field": ".editor-post-title__input",
                "content_area": ".block-editor-default-block-appender__content",
                "add_block_button": ".block-editor-inserter__toggle",
                "paragraph_block": "button[aria-label*='Paragraph']",
                "image_block": "button[aria-label*='Image']",
            },
            "media": {
                "upload_tab": "button[id*='upload']",
                "select_files_button": ".media-button-select",
                "file_input": "input[type='file'][accept*='image']",
                "insert_button": ".media-button-insert",
            },
            "seo": {
                "panel": "#wpseo-metabox-root",
                "seo_title_field": "input[name='yoast_wpseo_title']",
                "focus_keyword_field": "input[name='yoast_wpseo_focuskw']",
                "meta_description_field": "textarea[name='yoast_wpseo_metadesc']",
            },
            "publish": {
                "publish_button": ".editor-post-publish-button__button",
                "publish_panel_toggle": ".editor-post-publish-panel__toggle",
                "post_publish_button": ".editor-post-publish-button",
                "save_draft_button": ".editor-post-save-draft",
                "draft_saved_notice": "text=Draft saved",
            },
            "waits": {
                "after_login": 2000,
                "editor_load": 5000,
                "after_type": 500,
                "media_upload": 3000,
                "before_publish": 1000,
                "after_publish": 2000,
                "after_save": 1500,
            },
        }

    async def publish_article(
        self,
        cms_url: str,
        username: str,
        password: str,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata | None = None,
        article_images: list[dict[str, Any]] | None = None,
        headless: bool = True,
        publish_mode: Literal["publish", "draft"] = "publish",
        http_auth: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """Publish article to WordPress using Playwright.

        Args:
            cms_url: WordPress site URL
            username: WordPress username
            password: WordPress password or application password
            article_title: Article title
            article_body: Article content (HTML/Markdown)
            seo_data: SEO metadata (optional)
            article_images: List of image metadata with local_path
            headless: Run browser in headless mode (default: True for Cloud Run)
            publish_mode: "publish" or "draft"
            http_auth: Optional tuple of (username, password) for site-level HTTP Basic Auth

        Returns:
            Publishing result dictionary
        """
        try:
            logger.info(
                "playwright_publish_started",
                title=article_title[:50],
                has_images=bool(article_images),
                publish_mode=publish_mode,
                has_http_auth=bool(http_auth),
            )

            # Start Playwright
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(
                    headless=headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox"] if headless else ["--start-maximized"],
                )

                # Create context with HTTP Basic Auth if provided
                context_options: dict[str, Any] = {
                    "viewport": {"width": 1920, "height": 1080},
                }
                if http_auth:
                    context_options["http_credentials"] = {
                        "username": http_auth[0],
                        "password": http_auth[1],
                    }
                context = await self.browser.new_context(**context_options)
                self.page = await context.new_page()

                # Enable verbose logging
                self.page.on("console", lambda msg: logger.debug(f"Browser: {msg.text}"))

                # Execute publishing steps
                await self._step_login(cms_url, username, password)
                await self._step_navigate_to_new_post()
                await self._step_set_title(article_title)

                # Upload images if provided
                if article_images:
                    uploaded_images = await self._step_upload_images(article_images)
                    # Update body with uploaded image URLs
                    article_body = self._replace_image_references(
                        article_body, uploaded_images
                    )

                await self._step_set_content(article_body)
                if seo_data:
                    await self._step_configure_seo(seo_data)
                article_location, article_id = await self._step_publish(publish_mode=publish_mode)

                # Take final screenshot
                screenshot_path = f"/tmp/playwright_success_{article_id}.png"
                await self.page.screenshot(path=screenshot_path)

                status_value = "draft" if publish_mode == "draft" else "published"

                logger.info(
                    "playwright_publish_completed",
                    article_id=article_id,
                    url=article_location if publish_mode != "draft" else None,
                    editor_url=article_location if publish_mode == "draft" else None,
                    publish_mode=publish_mode,
                )

                return {
                    "success": True,
                    "cms_article_id": article_id,
                    "url": article_location if publish_mode != "draft" else None,
                    "editor_url": article_location if publish_mode == "draft" else None,
                    "screenshot": screenshot_path,
                    "status": status_value,
                }

        except Exception as e:
            logger.error(
                "playwright_publish_failed",
                error=str(e),
                exc_info=True,
            )

            # Take error screenshot
            if self.page:
                try:
                    await self.page.screenshot(path="/tmp/playwright_error.png")
                except Exception:
                    pass

            return {
                "success": False,
                "error": str(e),
            }

        finally:
            if self.browser:
                await self.browser.close()

    async def _step_login(self, cms_url: str, username: str, password: str) -> None:
        """Step 1: Login to WordPress.

        Args:
            cms_url: WordPress base URL
            username: Username
            password: Password
        """
        logger.info("playwright_step_login")

        login_url = f"{cms_url}/wp-admin"
        await self.page.goto(login_url)

        # Wait for login form
        await self.page.wait_for_selector(
            self.config["login"]["username_field"],
            timeout=10000,
        )

        # Fill username
        await self.page.fill(self.config["login"]["username_field"], username)
        await asyncio.sleep(0.5)

        # Fill password
        await self.page.fill(self.config["login"]["password_field"], password)
        await asyncio.sleep(0.5)

        # Click login
        await self.page.click(self.config["login"]["submit_button"])

        # Wait for dashboard
        await asyncio.sleep(self.config["waits"]["after_login"] / 1000)

        logger.info("playwright_login_completed")

    async def _step_navigate_to_new_post(self) -> None:
        """Step 2: Navigate to new post page."""
        logger.info("playwright_step_new_post")

        # Click "Posts" → "Add New"
        new_post_link = self.config["dashboard"]["new_post_link"]

        try:
            # Try direct link click
            await self.page.click(new_post_link)
        except Exception:
            # Fallback: navigate directly to post-new.php
            current_url = self.page.url
            base_url = current_url.split("/wp-admin")[0]
            await self.page.goto(f"{base_url}/wp-admin/post-new.php")

        # Wait for editor to load
        await asyncio.sleep(self.config["waits"]["editor_load"] / 1000)

        # Detect editor type: Gutenberg or Classic
        # Try Gutenberg first, then Classic
        gutenberg_title = self.config["editor"]["title_field"]  # .editor-post-title__input
        classic_title = "#title"  # Classic Editor title field

        try:
            await self.page.wait_for_selector(gutenberg_title, timeout=5000)
            self._editor_type = "gutenberg"
            logger.info("playwright_editor_detected", editor_type="gutenberg")
        except Exception:
            try:
                await self.page.wait_for_selector(classic_title, timeout=10000)
                self._editor_type = "classic"
                logger.info("playwright_editor_detected", editor_type="classic")
            except Exception:
                # Last fallback - check for any input with 'title' in name
                self._editor_type = "unknown"
                logger.warning("playwright_editor_unknown", message="Could not detect editor type")

        logger.info("playwright_new_post_loaded", editor_type=getattr(self, '_editor_type', 'unknown'))

    async def _step_set_title(self, title: str) -> None:
        """Step 3: Set article title.

        Args:
            title: Article title
        """
        logger.info("playwright_step_set_title", title=title[:50])

        # Use appropriate selector based on detected editor
        editor_type = getattr(self, '_editor_type', 'gutenberg')
        if editor_type == "classic":
            title_field = "#title"
        else:
            title_field = self.config["editor"]["title_field"]

        # Wait for title field to be visible and interactable
        await self.page.wait_for_selector(title_field, state="visible", timeout=10000)

        # Click and fill title using fill() - fast and reliable
        await self.page.click(title_field)
        await self.page.fill(title_field, title)

        # Verify title was set correctly
        actual_title = await self.page.input_value(title_field)
        if actual_title != title:
            logger.warning("playwright_title_mismatch",
                          expected=title[:50],
                          actual=actual_title[:50])
        else:
            logger.info("playwright_title_verified", length=len(title))

        logger.info("playwright_title_set", editor_type=editor_type)

    async def _step_upload_images(self, images: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Step 4: Upload images to WordPress media library.

        Args:
            images: List of image metadata with local_path

        Returns:
            List of uploaded image data with WordPress URLs
        """
        logger.info("playwright_step_upload_images", count=len(images))

        uploaded: list[dict[str, Any]] = []

        for idx, image in enumerate(images):
            try:
                logger.debug(f"Uploading image {idx + 1}/{len(images)}: {image['filename']}")

                # Click add block button
                await self.page.click(self.config["editor"]["add_block_button"])
                await asyncio.sleep(1)

                # Search for image block
                await self.page.keyboard.type("image")
                await asyncio.sleep(0.5)

                # Click image block
                await self.page.click(self.config["editor"]["image_block"])
                await asyncio.sleep(1)

                # Upload file
                file_input = await self.page.wait_for_selector(
                    self.config["media"]["file_input"],
                    timeout=5000,
                )
                await file_input.set_input_files(image["local_path"])

                # Wait for upload
                await asyncio.sleep(self.config["waits"]["media_upload"] / 1000)

                # Get uploaded image URL from block
                # This is simplified - actual implementation may need to parse the image URL
                image_url = f"{self.page.url}/uploaded/{image['filename']}"

                uploaded.append({
                    **image,
                    "wordpress_url": image_url,
                })

                logger.debug(f"Image uploaded: {image['filename']}")

            except Exception as e:
                logger.warning(
                    "image_upload_failed",
                    filename=image["filename"],
                    error=str(e),
                )
                # Continue with other images
                continue

        logger.info("playwright_images_uploaded", success=len(uploaded))
        return uploaded

    async def _step_set_content(self, content: str) -> None:
        """Step 5: Set article content.

        Args:
            content: Article body (HTML/Markdown)
        """
        logger.info("playwright_step_set_content", length=len(content))

        editor_type = getattr(self, '_editor_type', 'gutenberg')
        content_set = False
        actual_length = 0

        if editor_type == "classic":
            # Classic Editor: Use TinyMCE or plain textarea
            # First, try to switch to "Text" tab for HTML input (best for HTML content)
            try:
                text_tab = "#content-html"  # "Text" tab in Classic Editor
                await self.page.wait_for_selector(text_tab, timeout=3000)
                await self.page.click(text_tab)
                await self.page.wait_for_selector("#content:not([style*='display: none'])", timeout=3000)
                logger.info("playwright_switched_to_text_mode")
            except Exception:
                logger.debug("Text tab not found or not clickable, trying direct textarea")

            # Fill the textarea directly (works in Text mode) - NO LENGTH LIMIT
            content_textarea = "#content"
            try:
                await self.page.wait_for_selector(content_textarea, state="visible", timeout=5000)
                await self.page.fill(content_textarea, content)  # fill() is fast and handles full content

                # Verify content was set correctly
                actual_content = await self.page.input_value(content_textarea)
                actual_length = len(actual_content)
                content_set = True
                logger.info("playwright_content_set_classic_textarea",
                           expected_length=len(content),
                           actual_length=actual_length)
            except Exception as e:
                # Fallback: Try TinyMCE iframe with JavaScript injection
                logger.debug(f"Textarea fill failed: {e}, trying TinyMCE iframe")
                try:
                    # Switch to Visual tab
                    visual_tab = "#content-tmce"
                    await self.page.click(visual_tab)
                    await self.page.wait_for_selector("#content_ifr", timeout=5000)

                    # Use JavaScript to set TinyMCE content (faster and more reliable)
                    await self.page.evaluate(f"""
                        if (typeof tinyMCE !== 'undefined' && tinyMCE.get('content')) {{
                            tinyMCE.get('content').setContent({repr(content)});
                        }}
                    """)

                    # Verify via JavaScript
                    actual_content = await self.page.evaluate("""
                        () => {
                            if (typeof tinyMCE !== 'undefined' && tinyMCE.get('content')) {
                                return tinyMCE.get('content').getContent();
                            }
                            return '';
                        }
                    """)
                    actual_length = len(actual_content)
                    content_set = True
                    logger.info("playwright_content_set_classic_tinymce",
                               expected_length=len(content),
                               actual_length=actual_length)
                except Exception as e2:
                    logger.error(f"TinyMCE also failed: {e2}")
                    raise
        else:
            # Gutenberg Editor - use JavaScript for reliable content insertion
            try:
                # Wait for Gutenberg editor to be ready
                await self.page.wait_for_selector(".block-editor-writing-flow", timeout=10000)

                # Use WordPress data API to insert content block
                await self.page.evaluate(f"""
                    () => {{
                        const {{ dispatch, select }} = wp.data;
                        const {{ createBlock }} = wp.blocks;

                        // Create a paragraph block with the content
                        const block = createBlock('core/paragraph', {{
                            content: {repr(content)}
                        }});

                        // Insert the block
                        dispatch('core/block-editor').insertBlocks(block);
                    }}
                """)
                content_set = True
                actual_length = len(content)
                logger.info("playwright_content_set_gutenberg_api", length=len(content))
            except Exception as e:
                logger.warning(f"Gutenberg API failed, trying direct input: {e}")
                # Fallback to direct typing (slower but works)
                content_area = self.config["editor"]["content_area"]
                await self.page.wait_for_selector(content_area, state="visible", timeout=10000)
                await self.page.click(content_area)
                # Use fill() if possible, otherwise type (but type is slow)
                try:
                    await self.page.fill(content_area, content)
                    content_set = True
                    actual_length = len(content)
                except Exception:
                    # Last resort: keyboard.type() - but this is slow
                    await self.page.keyboard.type(content)
                    content_set = True
                    actual_length = len(content)
                logger.info("playwright_content_set_gutenberg_fallback")

        # Verify content completeness
        if content_set:
            completeness = (actual_length / len(content) * 100) if len(content) > 0 else 100
            if completeness < 90:
                logger.warning("playwright_content_incomplete",
                              expected=len(content),
                              actual=actual_length,
                              completeness=f"{completeness:.1f}%")
            else:
                logger.info("playwright_content_verified",
                           completeness=f"{completeness:.1f}%")

        logger.info("playwright_content_set", editor_type=editor_type, content_length=actual_length)

    async def _step_configure_seo(self, seo_data: SEOMetadata) -> None:
        """Step 6: Configure SEO metadata.

        Phase 9: Includes SEO Title configuration for WordPress SEO plugins.

        Args:
            seo_data: SEO metadata
        """
        logger.info("playwright_step_configure_seo")

        try:
            # Scroll down to SEO panel
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # Wait for SEO panel
            seo_panel = self.config["seo"]["panel"]
            await self.page.wait_for_selector(seo_panel, timeout=5000)

            # Phase 9: Set SEO Title (for <title> tag)
            if seo_data.meta_title:
                seo_title_field = self.config["seo"].get("seo_title_field")
                if seo_title_field:
                    await self.page.fill(seo_title_field, seo_data.meta_title)
                    await asyncio.sleep(0.5)
                    logger.info(
                        "seo_title_configured",
                        seo_title=seo_data.meta_title,
                    )

            # Set focus keyword
            if seo_data.focus_keyword:
                focus_field = self.config["seo"]["focus_keyword_field"]
                await self.page.fill(focus_field, seo_data.focus_keyword)
                await asyncio.sleep(0.5)

            # Set meta description
            if seo_data.meta_description:
                meta_field = self.config["seo"]["meta_description_field"]
                await self.page.fill(meta_field, seo_data.meta_description)
                await asyncio.sleep(0.5)

            logger.info("playwright_seo_configured")

        except Exception as e:
            logger.warning(
                "seo_configuration_failed",
                error=str(e),
            )
            # Continue without SEO configuration

    async def _step_publish(self, publish_mode: Literal["publish", "draft"] = "publish") -> tuple[str | None, str]:
        """Step 7: Publish article or save as draft.

        Args:
            publish_mode: Publishing mode

        Returns:
            Tuple of (result_url, article_id)
        """
        editor_type = getattr(self, '_editor_type', 'gutenberg')
        logger.info("playwright_step_publish", publish_mode=publish_mode, editor_type=editor_type)

        # Scroll to top to ensure buttons are visible
        await self.page.evaluate("window.scrollTo(0, 0)")

        if publish_mode == "draft":
            if editor_type == "classic":
                # Classic Editor: Save Draft button is #save-post
                save_selector = "#save-post"
                logger.info("playwright_using_classic_save_draft", selector=save_selector)
            else:
                # Gutenberg: Use config selector
                save_selector = self.config["publish"].get("save_draft_button")
                if not save_selector:
                    raise ValueError("Save draft selector not configured")

            # Wait for save button to be visible and clickable
            await self.page.wait_for_selector(save_selector, state="visible", timeout=10000)
            await self.page.click(save_selector)

            # For Classic Editor, wait for the page to reload/update
            if editor_type == "classic":
                # Wait for URL to contain post= parameter (indicates post was saved)
                try:
                    await self.page.wait_for_url("**/post.php?post=*", timeout=15000)
                    logger.info("playwright_draft_saved_classic")
                except Exception:
                    # Already on edit page, check for success message
                    logger.debug("URL didn't change, checking for saved message")
                    try:
                        # Look for WordPress success notice
                        await self.page.wait_for_selector("#message.updated, .notice-success", timeout=5000)
                        logger.info("playwright_draft_saved_classic_notice")
                    except Exception:
                        logger.warning("No confirmation found, but continuing")
            else:
                # Gutenberg: wait for draft saved notice
                draft_notice = self.config["publish"].get("draft_saved_notice")
                if draft_notice:
                    try:
                        await self.page.wait_for_selector(draft_notice, timeout=10000)
                    except Exception:
                        logger.warning("draft_saved_notice_not_found")

            current_url = self.page.url
            draft_article_id = self._extract_post_id(current_url)

            # Verify we got a valid post ID
            if draft_article_id == "unknown":
                logger.warning("playwright_draft_id_not_found", url=current_url)
            else:
                logger.info("playwright_draft_saved", article_id=draft_article_id, url=current_url)

            return current_url, draft_article_id

        # Publish mode
        if editor_type == "classic":
            # Classic Editor: Publish button is #publish
            publish_button = "#publish"
        else:
            # Gutenberg: Use config selector
            publish_button = self.config["publish"]["publish_button"]

        # Wait for publish button and click
        await self.page.wait_for_selector(publish_button, state="visible", timeout=10000)
        await self.page.click(publish_button)

        # Click confirm publish (if needed, mainly for Gutenberg)
        if editor_type != "classic":
            try:
                confirm_button = self.config["publish"]["post_publish_button"]
                await self.page.wait_for_selector(confirm_button, timeout=5000)
                await self.page.click(confirm_button)
            except Exception:
                pass  # May not need confirmation

        # Wait for publish complete - look for success indicators
        if editor_type == "classic":
            try:
                await self.page.wait_for_selector("#message.updated, .notice-success", timeout=10000)
            except Exception:
                logger.warning("No publish confirmation found")
        else:
            await asyncio.sleep(self.config["waits"]["after_publish"] / 1000)

        # Extract article URL and ID
        article_url = self.page.url
        article_id = self._extract_post_id(article_url)

        logger.info(
            "playwright_publish_completed",
            article_id=article_id,
            url=article_url,
            publish_mode=publish_mode,
            editor_type=editor_type,
        )

        return article_url, article_id

    def _extract_post_id(self, url: str) -> str:
        """Extract post ID from URL.

        Args:
            url: WordPress post URL

        Returns:
            Post ID as string
        """
        # Try to extract from ?post=123 or /post/123/
        import re

        match = re.search(r'[?&]post=(\d+)', url)
        if match:
            return match.group(1)

        match = re.search(r'/post/(\d+)/', url)
        if match:
            return match.group(1)

        # Fallback
        return "unknown"

    def _replace_image_references(
        self,
        content: str,
        uploaded_images: list[dict[str, Any]],
    ) -> str:
        """Replace Google Drive image references with WordPress URLs.

        Args:
            content: Original content with Drive references
            uploaded_images: List of uploaded images with wordpress_url

        Returns:
            Updated content with WordPress URLs
        """
        updated_content = content

        for image in uploaded_images:
            # Replace Drive file ID references
            drive_id = image.get("drive_file_id")
            wordpress_url = image.get("wordpress_url")

            if drive_id and wordpress_url:
                updated_content = updated_content.replace(drive_id, wordpress_url)

        return updated_content


async def create_playwright_publisher(
    config_path: str | None = None,
) -> PlaywrightWordPressPublisher:
    """Factory function to create Playwright publisher.

    Args:
        config_path: Optional path to WordPress selectors config

    Returns:
        PlaywrightWordPressPublisher instance
    """
    return PlaywrightWordPressPublisher(config_path)
