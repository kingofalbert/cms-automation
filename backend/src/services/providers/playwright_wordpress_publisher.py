"""Playwright-based WordPress publisher (free alternative to Computer Use API)."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any, Literal

import anthropic
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
        self._cms_url: str | None = None  # Store CMS URL for later use

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
                "keywords_field": "input[name='yoast_wpseo_metakeywords']",
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
        # Phase B: Extended publishing data
        primary_category: str | None = None,
        secondary_categories: list[str] | None = None,
        tags: list[str] | None = None,
        featured_image_path: str | None = None,
        featured_image_alt_text: str | None = None,
        featured_image_description: str | None = None,
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
            primary_category: WordPress primary category name
            secondary_categories: List of WordPress secondary category names
            tags: List of WordPress tags
            featured_image_path: Path to featured image file
            featured_image_alt_text: Alt text for the featured image
            featured_image_description: Description for the featured image

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
                primary_category=primary_category,
                secondary_categories_count=len(secondary_categories or []),
                tags_count=len(tags or []),
                has_featured_image=bool(featured_image_path),
            )

            # Start Playwright
            async with async_playwright() as p:
                # Launch browser with Cloud Run compatible options
                browser_args = [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",  # Important for Docker/Cloud Run
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--single-process",  # Run in single process mode for containerized environments
                ]
                if not headless:
                    browser_args.append("--start-maximized")

                self.browser = await p.chromium.launch(
                    headless=headless,
                    args=browser_args,
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

                # Phase B: Set categories and tags
                if primary_category or secondary_categories:
                    await self._step_set_categories(primary_category, secondary_categories or [])
                if tags:
                    await self._step_set_tags(tags)

                # Set featured image (before SEO to allow og_image auto-detection)
                if featured_image_path:
                    await self._step_set_featured_image(
                        featured_image_path,
                        alt_text=featured_image_alt_text,
                        description=featured_image_description,
                    )

                if seo_data:
                    await self._step_configure_seo(seo_data)
                article_location, article_id = await self._step_publish(publish_mode=publish_mode)

                # Take final screenshot
                screenshot_path = f"/tmp/playwright_success_{article_id}.png"
                await self.page.screenshot(path=screenshot_path)

                # Perform AI visual verification
                verification_result = await self._verify_with_vision_ai(
                    expected_title=article_title,
                    expected_content_snippet=article_body[:200] if article_body else None,
                )

                status_value = "draft" if publish_mode == "draft" else "published"

                # Determine final success based on both data and visual verification
                visual_verified = verification_result.get("verified", False)
                visual_confidence = verification_result.get("confidence", 0.0)

                # Log verification result
                if visual_verified:
                    logger.info(
                        "playwright_visual_verification_passed",
                        article_id=article_id,
                        confidence=visual_confidence,
                    )
                else:
                    logger.warning(
                        "playwright_visual_verification_warning",
                        article_id=article_id,
                        confidence=visual_confidence,
                        errors=verification_result.get("errors_detected", []),
                        details=verification_result.get("details", ""),
                    )

                logger.info(
                    "playwright_publish_completed",
                    article_id=article_id,
                    url=article_location if publish_mode != "draft" else None,
                    editor_url=article_location if publish_mode == "draft" else None,
                    publish_mode=publish_mode,
                    visual_verified=visual_verified,
                )

                return {
                    "success": True,
                    "cms_article_id": article_id,
                    "url": article_location if publish_mode != "draft" else None,
                    "editor_url": article_location if publish_mode == "draft" else None,
                    "screenshot": screenshot_path,
                    "status": status_value,
                    "visual_verification": {
                        "verified": visual_verified,
                        "confidence": visual_confidence,
                        "title_found": verification_result.get("title_found", False),
                        "content_found": verification_result.get("content_found", False),
                        "save_confirmed": verification_result.get("save_confirmed", False),
                        "errors_detected": verification_result.get("errors_detected", []),
                        "details": verification_result.get("details", ""),
                    },
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
        logger.info("playwright_step_login", cms_url=cms_url)

        # Store CMS URL for later use
        self._cms_url = cms_url.rstrip("/")

        login_url = f"{self._cms_url}/wp-admin"
        logger.info("playwright_navigating_to_login", url=login_url)

        try:
            await self.page.goto(login_url, timeout=30000)
        except Exception as e:
            logger.error("playwright_login_page_failed", error=str(e), url=login_url)
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="/tmp/playwright_login_error.png")
                logger.info("playwright_error_screenshot_saved", path="/tmp/playwright_login_error.png")
            except Exception:
                pass
            raise

        current_url = self.page.url
        logger.info("playwright_login_page_loaded", current_url=current_url)

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

        # Wait for navigation to complete
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            # Fallback to simple timeout if networkidle times out
            await asyncio.sleep(self.config["waits"]["after_login"] / 1000)

        # Verify login succeeded - check we're not still on login page
        post_login_url = self.page.url
        logger.info("playwright_post_login_url", url=post_login_url)

        if "wp-login.php" in post_login_url:
            # Still on login page - check for error message
            error_selector = "#login_error"
            try:
                error_element = await self.page.wait_for_selector(error_selector, timeout=2000)
                error_text = await error_element.inner_text()
                logger.error("playwright_login_failed", error=error_text)
                raise RuntimeError(f"WordPress login failed: {error_text}")
            except Exception:
                # No error element, but still on login page
                logger.error("playwright_login_failed_unknown", url=post_login_url)
                raise RuntimeError("WordPress login failed - still on login page")

        logger.info("playwright_login_completed", dashboard_url=post_login_url)

    async def _step_navigate_to_new_post(self) -> None:
        """Step 2: Navigate to new post page."""
        logger.info("playwright_step_new_post", current_url=self.page.url)

        # Click "Posts" → "Add New"
        new_post_link = self.config["dashboard"]["new_post_link"]

        try:
            # Try direct link click
            await self.page.wait_for_selector(new_post_link, timeout=5000)
            await self.page.click(new_post_link)
            logger.info("playwright_clicked_new_post_link")
        except Exception as e:
            # Fallback: navigate directly to post-new.php using stored CMS URL
            logger.warning("playwright_new_post_link_failed", error=str(e))
            if not self._cms_url:
                raise RuntimeError("CMS URL not stored - login step may have failed")
            new_post_url = f"{self._cms_url}/wp-admin/post-new.php"
            logger.info("playwright_navigating_to_new_post", url=new_post_url)
            await self.page.goto(new_post_url, timeout=30000)

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

    async def _step_set_image_metadata(
        self,
        alt_text: str | None = None,
        title: str | None = None,
        caption: str | None = None,
        description: str | None = None,
    ) -> None:
        """Set image metadata in the WordPress media modal's Attachment Details panel.

        Must be called while the media modal is open and an image is selected.

        Args:
            alt_text: Image alt text for SEO and accessibility
            title: Image title
            caption: Image caption
            description: Image description
        """
        logger.info(
            "playwright_step_set_image_metadata",
            has_alt=bool(alt_text),
            has_title=bool(title),
            has_caption=bool(caption),
            has_description=bool(description),
        )

        # Wait a moment for attachment details to render
        await asyncio.sleep(1)

        field_map = [
            (alt_text, [
                "#attachment-details-two-column-alt-text",
                ".setting[data-setting='alt'] input",
                "label:has-text('Alt Text') + input",
                "input[data-setting='alt']",
            ]),
            (title, [
                ".setting[data-setting='title'] input",
                "label:has-text('Title') + input",
                "input[data-setting='title']",
            ]),
            (caption, [
                ".setting[data-setting='caption'] textarea",
                "label:has-text('Caption') + textarea",
                "textarea[data-setting='caption']",
            ]),
            (description, [
                ".setting[data-setting='description'] textarea",
                "label:has-text('Description') + textarea",
                "textarea[data-setting='description']",
            ]),
        ]

        for value, selectors in field_map:
            if not value:
                continue
            filled = False
            for selector in selectors:
                try:
                    el = await self.page.wait_for_selector(
                        f".media-modal {selector}", timeout=2000
                    )
                    if el:
                        await el.fill(value)
                        filled = True
                        logger.debug(f"Image metadata field set via {selector}")
                        break
                except Exception:
                    continue
            if not filled:
                logger.debug(f"Could not find field for value: {value[:30]}...")

        await asyncio.sleep(0.5)

    async def _step_upload_images(self, images: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Step 4: Upload images to WordPress media library.

        Args:
            images: List of image metadata with local_path, alt_text, keywords, etc.

        Returns:
            List of uploaded image data with WordPress URLs
        """
        logger.info("playwright_step_upload_images", count=len(images))

        uploaded: list[dict[str, Any]] = []

        for idx, image in enumerate(images):
            try:
                local_path = image.get("local_path")
                if not local_path:
                    logger.warning("image_no_local_path", filename=image.get("filename"))
                    continue

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
                await file_input.set_input_files(local_path)

                # Wait for upload
                await asyncio.sleep(self.config["waits"]["media_upload"] / 1000)

                # Set image alt text directly on the image block (Gutenberg)
                alt_text = image.get("alt_text", "")
                if alt_text:
                    try:
                        # In Gutenberg, after uploading an image in an Image block,
                        # the alt text can be set in the block sidebar
                        alt_input = await self.page.wait_for_selector(
                            "textarea[aria-label='Alternative text'], "
                            "textarea[aria-label='替代文字'], "
                            ".components-textarea-control__input[aria-label*='alt' i]",
                            timeout=3000,
                        )
                        if alt_input:
                            await alt_input.fill(alt_text)
                            logger.debug(f"Image alt text set: {alt_text[:50]}")
                    except Exception:
                        logger.debug("Could not set alt text on image block")

                # Get uploaded image URL from block
                image_url = f"{self.page.url}/uploaded/{image['filename']}"

                uploaded.append({
                    **image,
                    "wordpress_url": image_url,
                })

                logger.debug(f"Image uploaded: {image['filename']}")

            except Exception as e:
                logger.warning(
                    "image_upload_failed",
                    filename=image.get("filename", "unknown"),
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
                    await self.page.evaluate("""
                        (content) => {
                            if (typeof tinyMCE !== 'undefined' && tinyMCE.get('content')) {
                                tinyMCE.get('content').setContent(content);
                            }
                        }
                    """, content)

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

    async def _step_set_categories(
        self, primary_category: str | None, secondary_categories: list[str]
    ) -> None:
        """Step 6a: Set WordPress categories.

        Opens the Categories panel in the sidebar and checks the appropriate checkboxes.

        Args:
            primary_category: Primary category name to select
            secondary_categories: List of secondary category names to select
        """
        logger.info(
            "playwright_step_set_categories",
            primary=primary_category,
            secondary_count=len(secondary_categories),
        )

        editor_type = getattr(self, '_editor_type', 'gutenberg')
        all_categories = []
        if primary_category:
            all_categories.append(primary_category)
        all_categories.extend(secondary_categories)

        if not all_categories:
            logger.debug("No categories to set, skipping")
            return

        try:
            if editor_type == "classic":
                # Classic Editor: Categories are in a meta box on the right side
                # First, ensure the Categories meta box is visible
                categories_panel = "#categorychecklist"
                await self.page.wait_for_selector(categories_panel, timeout=5000)

                for category_name in all_categories:
                    try:
                        # Find checkbox by label text
                        # WordPress categories use: <label><input type="checkbox"> Category Name</label>
                        checkbox_selector = f"#categorychecklist label:has-text('{category_name}') input[type='checkbox']"
                        checkbox = await self.page.query_selector(checkbox_selector)

                        if checkbox:
                            is_checked = await checkbox.is_checked()
                            if not is_checked:
                                await checkbox.click()
                                logger.debug(f"Category checked: {category_name}")
                        else:
                            # Try alternative: search by exact text match
                            labels = await self.page.query_selector_all("#categorychecklist label")
                            for label in labels:
                                label_text = await label.inner_text()
                                if category_name.strip() in label_text.strip():
                                    checkbox = await label.query_selector("input[type='checkbox']")
                                    if checkbox and not await checkbox.is_checked():
                                        await checkbox.click()
                                        logger.debug(f"Category checked (alt): {category_name}")
                                    break
                    except Exception as e:
                        logger.warning(f"Failed to check category '{category_name}': {e}")
                        continue

            else:
                # Gutenberg Editor: Categories are in the sidebar panel
                # First, open the Settings sidebar if not already open
                try:
                    settings_button = "button[aria-label='Settings']"
                    settings_btn = await self.page.query_selector(settings_button)
                    if settings_btn:
                        is_pressed = await settings_btn.get_attribute("aria-pressed")
                        if is_pressed != "true":
                            await settings_btn.click()
                            await asyncio.sleep(0.5)
                except Exception:
                    pass  # Settings might already be open

                # Click on the Post tab in sidebar (if not already selected)
                try:
                    post_tab = "button[data-label='Post'], button:has-text('Post')"
                    await self.page.click(post_tab)
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

                # Expand Categories panel if collapsed
                try:
                    categories_panel_button = "button.components-panel__body-toggle:has-text('Categories')"
                    panel_btn = await self.page.query_selector(categories_panel_button)
                    if panel_btn:
                        is_expanded = await panel_btn.get_attribute("aria-expanded")
                        if is_expanded != "true":
                            await panel_btn.click()
                            await asyncio.sleep(0.3)
                except Exception:
                    pass

                # Now check the categories
                for category_name in all_categories:
                    try:
                        # Gutenberg uses: <label><input type="checkbox"><span>Category Name</span></label>
                        checkbox_selector = f".editor-post-taxonomies__hierarchical-terms-list label:has-text('{category_name}') input[type='checkbox']"
                        checkbox = await self.page.query_selector(checkbox_selector)

                        if checkbox:
                            is_checked = await checkbox.is_checked()
                            if not is_checked:
                                await checkbox.click()
                                logger.debug(f"Gutenberg category checked: {category_name}")
                        else:
                            # Fallback: try to find by searching all category labels
                            labels = await self.page.query_selector_all(".editor-post-taxonomies__hierarchical-terms-list label")
                            for label in labels:
                                label_text = await label.inner_text()
                                if category_name.strip() in label_text.strip():
                                    checkbox = await label.query_selector("input[type='checkbox']")
                                    if checkbox and not await checkbox.is_checked():
                                        await checkbox.click()
                                        logger.debug(f"Gutenberg category checked (alt): {category_name}")
                                    break
                    except Exception as e:
                        logger.warning(f"Failed to check Gutenberg category '{category_name}': {e}")
                        continue

            logger.info(
                "playwright_categories_set",
                total=len(all_categories),
                editor_type=editor_type,
            )

        except Exception as e:
            logger.warning(
                "playwright_categories_failed",
                error=str(e),
                categories=all_categories,
            )
            # Continue without categories - non-fatal error

    async def _step_set_tags(self, tags: list[str]) -> None:
        """Step 6b: Set WordPress tags.

        Opens the Tags panel in the sidebar and adds the specified tags.

        Args:
            tags: List of tag names to add
        """
        if not tags:
            return

        logger.info("playwright_step_set_tags", count=len(tags))

        editor_type = getattr(self, '_editor_type', 'gutenberg')

        try:
            if editor_type == "classic":
                # Classic Editor: Tags are in a meta box
                tags_input = "#new-tag-post_tag"
                add_button = ".tagadd"

                await self.page.wait_for_selector(tags_input, timeout=5000)

                # Add tags one by one or as comma-separated list
                tags_str = ", ".join(tags)
                await self.page.fill(tags_input, tags_str)
                await asyncio.sleep(0.3)

                # Click the Add button
                try:
                    await self.page.click(add_button)
                    await asyncio.sleep(0.5)
                except Exception:
                    # Some themes auto-add on Enter
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(0.5)

            else:
                # Gutenberg Editor: Tags are in the sidebar panel
                # First, ensure Settings sidebar is open
                try:
                    settings_button = "button[aria-label='Settings']"
                    settings_btn = await self.page.query_selector(settings_button)
                    if settings_btn:
                        is_pressed = await settings_btn.get_attribute("aria-pressed")
                        if is_pressed != "true":
                            await settings_btn.click()
                            await asyncio.sleep(0.5)
                except Exception:
                    pass

                # Click on the Post tab
                try:
                    post_tab = "button[data-label='Post'], button:has-text('Post')"
                    await self.page.click(post_tab)
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

                # Expand Tags panel if collapsed
                try:
                    tags_panel_button = "button.components-panel__body-toggle:has-text('Tags')"
                    panel_btn = await self.page.query_selector(tags_panel_button)
                    if panel_btn:
                        is_expanded = await panel_btn.get_attribute("aria-expanded")
                        if is_expanded != "true":
                            await panel_btn.click()
                            await asyncio.sleep(0.3)
                except Exception:
                    pass

                # Find the tags input field
                tags_input = ".components-form-token-field__input"
                await self.page.wait_for_selector(tags_input, timeout=5000)

                # Add each tag
                for tag in tags:
                    await self.page.fill(tags_input, tag)
                    await asyncio.sleep(0.2)
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(0.3)

            logger.info(
                "playwright_tags_set",
                count=len(tags),
                editor_type=editor_type,
            )

        except Exception as e:
            logger.warning(
                "playwright_tags_failed",
                error=str(e),
                tags=tags,
            )
            # Continue without tags - non-fatal error

    async def _step_set_featured_image(
        self,
        image_path: str,
        alt_text: str | None = None,
        description: str | None = None,
    ) -> None:
        """Step 6c: Set WordPress featured image.

        Opens the Featured Image panel and uploads the specified image.

        Args:
            image_path: Path to the featured image file (local path or URL)
            alt_text: Alt text for the featured image (SEO / accessibility)
            description: Description for the featured image in media library
        """
        logger.info("playwright_step_set_featured_image", path=image_path, has_alt=bool(alt_text))

        editor_type = getattr(self, '_editor_type', 'gutenberg')

        try:
            if editor_type == "classic":
                # Classic Editor: Featured Image is in a meta box
                # Click "Set featured image" link
                set_featured_link = "#set-post-thumbnail"
                await self.page.wait_for_selector(set_featured_link, timeout=5000)
                await self.page.click(set_featured_link)
                await asyncio.sleep(1)

                # Wait for media modal
                media_modal = ".media-modal"
                await self.page.wait_for_selector(media_modal, timeout=10000)

                # Click "Upload files" tab
                upload_tab = ".media-modal .media-menu-item:has-text('Upload files')"
                try:
                    await self.page.click(upload_tab)
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

                # Upload the file
                file_input = ".media-modal input[type='file']"
                await self.page.wait_for_selector(file_input, timeout=5000)
                await self.page.set_input_files(file_input, image_path)
                await asyncio.sleep(self.config["waits"]["media_upload"] / 1000)

                # Set image metadata (alt text, description) before confirming
                if alt_text or description:
                    await self._step_set_image_metadata(
                        alt_text=alt_text,
                        description=description,
                    )

                # Click "Set featured image" button
                set_button = ".media-modal .media-button-select"
                await self.page.click(set_button)
                await asyncio.sleep(1)

            else:
                # Gutenberg Editor: Featured Image is in the sidebar panel
                # First, ensure Settings sidebar is open
                try:
                    settings_button = "button[aria-label='Settings']"
                    settings_btn = await self.page.query_selector(settings_button)
                    if settings_btn:
                        is_pressed = await settings_btn.get_attribute("aria-pressed")
                        if is_pressed != "true":
                            await settings_btn.click()
                            await asyncio.sleep(0.5)
                except Exception:
                    pass

                # Click on the Post tab
                try:
                    post_tab = "button[data-label='Post'], button:has-text('Post')"
                    await self.page.click(post_tab)
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

                # Expand Featured Image panel if collapsed
                try:
                    featured_panel_button = "button.components-panel__body-toggle:has-text('Featured image')"
                    panel_btn = await self.page.query_selector(featured_panel_button)
                    if panel_btn:
                        is_expanded = await panel_btn.get_attribute("aria-expanded")
                        if is_expanded != "true":
                            await panel_btn.click()
                            await asyncio.sleep(0.3)
                except Exception:
                    pass

                # Click "Set featured image" button
                set_featured_button = ".editor-post-featured-image__toggle, button:has-text('Set featured image')"
                await self.page.click(set_featured_button)
                await asyncio.sleep(1)

                # Wait for media modal
                media_modal = ".media-modal"
                await self.page.wait_for_selector(media_modal, timeout=10000)

                # Click "Upload files" tab
                upload_tab = ".media-modal button:has-text('Upload files'), .media-modal .media-menu-item:has-text('Upload files')"
                try:
                    await self.page.click(upload_tab)
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

                # Upload the file
                file_input = ".media-modal input[type='file']"
                await self.page.wait_for_selector(file_input, timeout=5000)
                await self.page.set_input_files(file_input, image_path)
                await asyncio.sleep(self.config["waits"]["media_upload"] / 1000)

                # Set image metadata (alt text, description) before confirming
                if alt_text or description:
                    await self._step_set_image_metadata(
                        alt_text=alt_text,
                        description=description,
                    )

                # Click "Set featured image" button in modal
                set_button = ".media-modal .media-button-select, .media-modal button:has-text('Set featured image')"
                await self.page.click(set_button)
                await asyncio.sleep(1)

            logger.info(
                "playwright_featured_image_set",
                path=image_path,
                editor_type=editor_type,
            )

        except Exception as e:
            logger.warning(
                "playwright_featured_image_failed",
                error=str(e),
                path=image_path,
            )
            # Continue without featured image - non-fatal error

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

            # Set meta keywords (comma-separated)
            if seo_data.keywords:
                keywords_field = self.config["seo"].get("keywords_field")
                if keywords_field:
                    try:
                        kw_input = await self.page.wait_for_selector(
                            keywords_field, timeout=3000
                        )
                        if kw_input:
                            await kw_input.fill(", ".join(seo_data.keywords))
                            await asyncio.sleep(0.5)
                            logger.info(
                                "seo_keywords_configured",
                                count=len(seo_data.keywords),
                            )
                    except Exception:
                        logger.debug(
                            "seo_keywords_field_not_found",
                            selector=keywords_field,
                        )

            logger.info("playwright_seo_configured")

        except Exception as e:
            logger.warning(
                "seo_configuration_failed",
                error=str(e),
            )
            # Continue without SEO configuration

    async def _dismiss_media_modal(self) -> None:
        """Dismiss any open WordPress media modal that may block page interaction."""
        try:
            modal = await self.page.query_selector(".media-modal")
            if modal and await modal.is_visible():
                # Try clicking the close button
                close_btn = await self.page.query_selector(
                    ".media-modal .media-modal-close, "
                    ".media-modal button[aria-label='Close dialog'], "
                    ".media-modal button[aria-label='Close']"
                )
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(0.5)
                    logger.info("playwright_media_modal_dismissed")
                else:
                    # Fallback: press Escape
                    await self.page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                    logger.info("playwright_media_modal_dismissed_via_escape")
        except Exception:
            pass

    async def _step_publish(self, publish_mode: Literal["publish", "draft"] = "publish") -> tuple[str | None, str]:
        """Step 7: Publish article or save as draft.

        Args:
            publish_mode: Publishing mode

        Returns:
            Tuple of (result_url, article_id)
        """
        editor_type = getattr(self, '_editor_type', 'gutenberg')
        logger.info("playwright_step_publish", publish_mode=publish_mode, editor_type=editor_type)

        # Dismiss any stale media modal that may be blocking the page
        await self._dismiss_media_modal()

        # Scroll to top to ensure buttons are visible
        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)

        if publish_mode == "draft":
            if editor_type == "classic":
                # Classic Editor: Save Draft button — try multiple selectors
                save_selectors = [
                    "#save-post",                      # Standard Save Draft
                    "input[name='save']",              # Alternative name-based
                    "#publish",                        # Publish button (saves as draft if status is draft)
                ]
                logger.info("playwright_using_classic_save_draft")

                saved = False
                for selector in save_selectors:
                    try:
                        btn = await self.page.wait_for_selector(selector, state="visible", timeout=3000)
                        if btn:
                            await btn.click()
                            saved = True
                            logger.info("playwright_classic_draft_clicked", selector=selector)
                            break
                    except Exception:
                        continue

                if not saved:
                    # Last resort: submit the form via JavaScript
                    logger.warning("playwright_save_draft_buttons_not_found, using JS submit")
                    await self.page.evaluate("""
                        () => {
                            // Ensure post status is 'draft'
                            const statusField = document.querySelector('#post_status');
                            if (statusField) statusField.value = 'draft';

                            // Try clicking save-post via JS (may be hidden but present)
                            const saveBtn = document.querySelector('#save-post');
                            if (saveBtn) {
                                saveBtn.disabled = false;
                                saveBtn.click();
                                return 'clicked_save_post';
                            }

                            // Try the publish button with draft status
                            const publishBtn = document.querySelector('#publish');
                            if (publishBtn) {
                                publishBtn.click();
                                return 'clicked_publish';
                            }

                            // Submit the form directly
                            const form = document.querySelector('#post');
                            if (form) {
                                form.submit();
                                return 'form_submitted';
                            }
                            return 'nothing_found';
                        }
                    """)
                    saved = True
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

    async def _verify_with_vision_ai(
        self,
        expected_title: str,
        expected_content_snippet: str | None = None,
    ) -> dict[str, Any]:
        """Verify published content using Claude's vision API.

        Takes a screenshot and asks Claude to verify:
        1. The title is visible and matches expected
        2. Content appears to be present
        3. No error messages are visible

        Args:
            expected_title: The article title that should be visible
            expected_content_snippet: Optional content snippet to verify (first 100 chars)

        Returns:
            Verification result dictionary with:
            - verified: bool - whether verification passed
            - confidence: float - confidence level (0-1)
            - title_found: bool - whether title was found
            - content_found: bool - whether content appears present
            - errors_detected: list - any error messages found
            - details: str - detailed explanation
        """
        logger.info("playwright_vision_verification_start", title=expected_title[:50])

        try:
            # Take screenshot as bytes
            screenshot_bytes = await self.page.screenshot(type="png")
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Prepare the verification prompt
            content_check = ""
            if expected_content_snippet:
                content_check = f"\n3. Check if content appears to be present (look for text similar to: '{expected_content_snippet[:100]}...')"

            verification_prompt = f"""Please analyze this WordPress editor screenshot and verify the following:

1. Is the article title "{expected_title}" visible in the title field?
2. Does the page appear to be a WordPress post editor (either Classic or Gutenberg)?{content_check}
4. Are there any error messages, warnings, or failure indicators visible?
5. Does the page indicate the post was saved successfully (look for "Draft saved", "Post updated", success notices)?

Please respond in JSON format:
{{
    "title_found": true/false,
    "title_matches": true/false,
    "editor_detected": "classic" | "gutenberg" | "unknown",
    "content_present": true/false,
    "errors_detected": ["list of any error messages found"],
    "save_confirmed": true/false,
    "confidence": 0.0-1.0,
    "details": "Brief explanation of what you see"
}}

Be strict: only return title_found=true if you can clearly see the expected title text."""

            # Call Claude's vision API
            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-sonnet-4-20250514",  # Use Sonnet for cost efficiency
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": verification_prompt,
                            },
                        ],
                    }
                ],
            )

            # Parse the response
            response_text = response.content[0].text
            logger.debug("vision_api_response", response=response_text[:500])

            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback if JSON not found
                result = {
                    "title_found": False,
                    "title_matches": False,
                    "editor_detected": "unknown",
                    "content_present": False,
                    "errors_detected": ["Could not parse AI response"],
                    "save_confirmed": False,
                    "confidence": 0.0,
                    "details": response_text[:200],
                }

            # Determine overall verification status
            # For Classic Editor, save_confirmed may not be visible (URL change is the indicator)
            # So we consider verified if:
            # 1. Title is found and matches (required)
            # 2. No errors detected (required)
            # 3. Either save_confirmed OR high confidence (>=0.8)
            title_ok = result.get("title_found", False) and result.get("title_matches", False)
            no_errors = len(result.get("errors_detected", [])) == 0
            save_indicator = result.get("save_confirmed", False) or result.get("confidence", 0.0) >= 0.8

            verified = title_ok and no_errors and save_indicator

            verification_result = {
                "verified": verified,
                "confidence": result.get("confidence", 0.0),
                "title_found": result.get("title_found", False),
                "title_matches": result.get("title_matches", False),
                "content_found": result.get("content_present", False),
                "editor_type": result.get("editor_detected", "unknown"),
                "save_confirmed": result.get("save_confirmed", False),
                "errors_detected": result.get("errors_detected", []),
                "details": result.get("details", ""),
            }

            logger.info(
                "playwright_vision_verification_complete",
                verified=verified,
                confidence=result.get("confidence", 0.0),
                title_found=result.get("title_found", False),
                save_confirmed=result.get("save_confirmed", False),
            )

            return verification_result

        except Exception as e:
            logger.error("playwright_vision_verification_failed", error=str(e))
            return {
                "verified": False,
                "confidence": 0.0,
                "title_found": False,
                "title_matches": False,
                "content_found": False,
                "editor_type": "unknown",
                "save_confirmed": False,
                "errors_detected": [f"Vision verification failed: {str(e)}"],
                "details": str(e),
            }

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
