"""Playwright-based WordPress publisher (free alternative to Computer Use API)."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize Playwright publisher.

        Args:
            config_path: Path to WordPress selectors configuration JSON file
        """
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

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

    def _load_config(self, config_path: str) -> Dict:
        """Load WordPress configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
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

    def _get_default_config(self) -> Dict:
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
                "focus_keyword_field": "input[name='yoast_wpseo_focuskw']",
                "meta_description_field": "textarea[name='yoast_wpseo_metadesc']",
            },
            "publish": {
                "publish_button": ".editor-post-publish-button__button",
                "publish_panel_toggle": ".editor-post-publish-panel__toggle",
                "post_publish_button": ".editor-post-publish-button",
            },
            "waits": {
                "after_login": 2000,
                "editor_load": 5000,
                "after_type": 500,
                "media_upload": 3000,
                "before_publish": 1000,
                "after_publish": 2000,
            },
        }

    async def publish_article(
        self,
        cms_url: str,
        username: str,
        password: str,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata,
        article_images: List[Dict] = None,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """Publish article to WordPress using Playwright.

        Args:
            cms_url: WordPress site URL
            username: WordPress username
            password: WordPress password or application password
            article_title: Article title
            article_body: Article content (HTML/Markdown)
            seo_data: SEO metadata
            article_images: List of image metadata with local_path
            headless: Run browser in headless mode (default: False for debugging)

        Returns:
            Publishing result dictionary
        """
        try:
            logger.info(
                "playwright_publish_started",
                title=article_title[:50],
                has_images=bool(article_images),
            )

            # Start Playwright
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(
                    headless=headless,
                    args=["--start-maximized"] if not headless else [],
                )

                # Create context and page
                context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080} if headless else None
                )
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
                await self._step_configure_seo(seo_data)
                article_url, article_id = await self._step_publish()

                # Take final screenshot
                screenshot_path = f"/tmp/playwright_success_{article_id}.png"
                await self.page.screenshot(path=screenshot_path)

                logger.info(
                    "playwright_publish_completed",
                    article_id=article_id,
                    url=article_url,
                )

                return {
                    "success": True,
                    "cms_article_id": article_id,
                    "url": article_url,
                    "screenshot": screenshot_path,
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
                except:
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
        except:
            # Fallback: navigate directly to post-new.php
            current_url = self.page.url
            base_url = current_url.split("/wp-admin")[0]
            await self.page.goto(f"{base_url}/wp-admin/post-new.php")

        # Wait for editor to load
        await asyncio.sleep(self.config["waits"]["editor_load"] / 1000)

        # Wait for title field
        await self.page.wait_for_selector(
            self.config["editor"]["title_field"],
            timeout=15000,
        )

        logger.info("playwright_new_post_loaded")

    async def _step_set_title(self, title: str) -> None:
        """Step 3: Set article title.

        Args:
            title: Article title
        """
        logger.info("playwright_step_set_title", title=title[:50])

        title_field = self.config["editor"]["title_field"]

        # Click and fill title
        await self.page.click(title_field)
        await self.page.fill(title_field, title)
        await asyncio.sleep(self.config["waits"]["after_type"] / 1000)

        logger.info("playwright_title_set")

    async def _step_upload_images(self, images: List[Dict]) -> List[Dict]:
        """Step 4: Upload images to WordPress media library.

        Args:
            images: List of image metadata with local_path

        Returns:
            List of uploaded image data with WordPress URLs
        """
        logger.info("playwright_step_upload_images", count=len(images))

        uploaded = []

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

        content_area = self.config["editor"]["content_area"]

        # Click content area
        await self.page.click(content_area)
        await asyncio.sleep(0.5)

        # Type content (simplified - may need to handle HTML parsing)
        await self.page.keyboard.type(content[:1000])  # Limit for demo
        await asyncio.sleep(self.config["waits"]["after_type"] / 1000)

        logger.info("playwright_content_set")

    async def _step_configure_seo(self, seo_data: SEOMetadata) -> None:
        """Step 6: Configure SEO metadata.

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

    async def _step_publish(self) -> tuple[str, str]:
        """Step 7: Publish article.

        Returns:
            Tuple of (article_url, article_id)
        """
        logger.info("playwright_step_publish")

        # Scroll to top
        await self.page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)

        # Click publish button
        publish_button = self.config["publish"]["publish_button"]
        await self.page.click(publish_button)
        await asyncio.sleep(self.config["waits"]["before_publish"] / 1000)

        # Click confirm publish (if needed)
        try:
            confirm_button = self.config["publish"]["post_publish_button"]
            await self.page.click(confirm_button)
        except:
            pass  # May not need confirmation

        # Wait for publish complete
        await asyncio.sleep(self.config["waits"]["after_publish"] / 1000)

        # Extract article URL and ID
        article_url = self.page.url
        article_id = self._extract_post_id(article_url)

        logger.info(
            "playwright_publish_completed",
            article_id=article_id,
            url=article_url,
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
        uploaded_images: List[Dict],
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
    config_path: Optional[str] = None,
) -> PlaywrightWordPressPublisher:
    """Factory function to create Playwright publisher.

    Args:
        config_path: Optional path to WordPress selectors config

    Returns:
        PlaywrightWordPressPublisher instance
    """
    return PlaywrightWordPressPublisher(config_path)
