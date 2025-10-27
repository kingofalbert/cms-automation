"""Computer Use service for automated CMS operations."""

import base64
import json
import time
from datetime import datetime
from typing import Any

from anthropic import Anthropic, AnthropicBedrock
from anthropic.types.beta import BetaMessage, BetaMessageParam, BetaToolResultBlockParam

from src.api.schemas.seo import ComputerUseMetadata, SEOMetadata
from src.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class ComputerUseCMSService:
    """Service for automating CMS operations using Claude Computer Use API."""

    def __init__(self) -> None:
        """Initialize Computer Use CMS service."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"  # Computer Use supported model
        self.max_tokens = 4096
        self.display_width = 1920
        self.display_height = 1080

    async def publish_article_with_seo(
        self,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata,
        cms_url: str,
        cms_username: str,
        cms_password: str,
        cms_type: str = "wordpress",
        article_images: list[dict] = None,
    ) -> dict[str, Any]:
        """Publish article to CMS using Computer Use API.

        Args:
            article_title: Article title
            article_body: Article content (Markdown/HTML)
            seo_data: SEO metadata to configure
            cms_url: CMS admin URL
            cms_username: CMS username
            cms_password: CMS password or application password
            cms_type: CMS platform type (wordpress, strapi, etc.)
            article_images: List of image metadata dicts with local_path for upload

        Returns:
            dict: Publishing result with status, URL, metadata

        Raises:
            Exception: If publishing fails after retries
        """
        start_time = time.time()
        session_id = f"cu_{int(time.time())}"

        logger.info(
            "computer_use_cms_started",
            session_id=session_id,
            cms_type=cms_type,
            article_title=article_title[:100],
        )

        metadata = ComputerUseMetadata(
            session_id=session_id,
            attempts=1,
            last_attempt_at=datetime.utcnow().isoformat(),
            status="in_progress",
        )

        try:
            # Build the instruction prompt for Claude
            instructions = self._build_cms_instructions(
                cms_type=cms_type,
                cms_url=cms_url,
                cms_username=cms_username,
                cms_password=cms_password,
                article_title=article_title,
                article_body=article_body,
                seo_data=seo_data,
                article_images=article_images or [],
            )

            # Initialize Computer Use tools
            tools = [
                {
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": self.display_width,
                    "display_height_px": self.display_height,
                    "display_number": 1,
                },
                {
                    "type": "text_editor_20241022",
                    "name": "str_replace_editor",
                },
                {
                    "type": "bash_20241022",
                    "name": "bash",
                },
            ]

            # Start Computer Use conversation
            messages: list[BetaMessageParam] = [
                {
                    "role": "user",
                    "content": instructions,
                }
            ]

            screenshots = []
            max_iterations = 50  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                logger.info(
                    "computer_use_iteration",
                    session_id=session_id,
                    iteration=iteration,
                )

                # Call Claude with Computer Use
                response: BetaMessage = self.client.beta.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    tools=tools,
                    messages=messages,
                    betas=["computer-use-2024-10-22"],
                )

                logger.info(
                    "computer_use_response",
                    session_id=session_id,
                    stop_reason=response.stop_reason,
                    content_blocks=len(response.content),
                )

                # Process response
                tool_results: list[BetaToolResultBlockParam] = []

                for block in response.content:
                    if block.type == "text":
                        logger.info(
                            "computer_use_text_response",
                            text=block.text[:500],
                        )

                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        logger.info(
                            "computer_use_tool_call",
                            tool_name=tool_name,
                            tool_input=tool_input,
                        )

                        # Execute tool (this would be handled by Computer Use runtime)
                        # For now, we'll simulate the result
                        tool_result = self._execute_tool(
                            tool_name=tool_name,
                            tool_input=tool_input,
                            session_id=session_id,
                        )

                        # Capture screenshots for computer tool
                        if tool_name == "computer" and "screenshot" in str(tool_result):
                            screenshot_data = tool_result.get("base64_image")
                            if screenshot_data:
                                screenshot_url = self._save_screenshot(
                                    screenshot_data, session_id, iteration
                                )
                                screenshots.append(screenshot_url)

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(tool_result),
                            }
                        )

                # Check if task completed
                if response.stop_reason == "end_turn":
                    # Extract final result from response
                    final_result = self._extract_final_result(response)

                    execution_time = time.time() - start_time

                    metadata.status = "completed"
                    metadata.screenshots = screenshots
                    metadata.execution_time_seconds = execution_time

                    logger.info(
                        "computer_use_cms_completed",
                        session_id=session_id,
                        execution_time=execution_time,
                        screenshots_count=len(screenshots),
                    )

                    return {
                        "success": True,
                        "cms_article_id": final_result.get("article_id"),
                        "url": final_result.get("article_url"),
                        "metadata": metadata.model_dump(),
                        "message": "Article published successfully via Computer Use",
                    }

                # Continue conversation with tool results
                if tool_results:
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # No more tools to execute, break
                    break

            # Max iterations reached
            raise Exception(f"Computer Use task did not complete within {max_iterations} iterations")

        except Exception as e:
            execution_time = time.time() - start_time

            metadata.status = "failed"
            metadata.errors.append(str(e))
            metadata.execution_time_seconds = execution_time

            logger.error(
                "computer_use_cms_failed",
                session_id=session_id,
                error=str(e),
                execution_time=execution_time,
                exc_info=True,
            )

            return {
                "success": False,
                "error": str(e),
                "metadata": metadata.model_dump(),
            }

    def _build_cms_instructions(
        self,
        cms_type: str,
        cms_url: str,
        cms_username: str,
        cms_password: str,
        article_title: str,
        article_body: str,
        seo_data: SEOMetadata,
        article_images: list[dict],
    ) -> str:
        """Build Computer Use instructions for CMS publishing.

        Args:
            cms_type: CMS platform type
            cms_url: CMS admin URL
            cms_username: Username
            cms_password: Password
            article_title: Article title
            article_body: Article body
            seo_data: SEO metadata
            article_images: List of image metadata with local paths

        Returns:
            str: Detailed instructions for Claude
        """
        if cms_type == "wordpress":
            return self._build_wordpress_instructions(
                cms_url, cms_username, cms_password, article_title, article_body, seo_data, article_images
            )
        else:
            raise ValueError(f"Unsupported CMS type: {cms_type}")

    def _build_wordpress_instructions(
        self,
        cms_url: str,
        username: str,
        password: str,
        title: str,
        body: str,
        seo_data: SEOMetadata,
        article_images: list[dict],
    ) -> str:
        """Build WordPress-specific instructions.

        Args:
            cms_url: WordPress admin URL
            username: WordPress username
            password: Application password
            title: Article title
            body: Article body
            seo_data: SEO metadata
            article_images: List of article images with local paths

        Returns:
            str: WordPress publishing instructions
        """
        # Truncate body for instruction (full body will be pasted via editor tool)
        body_preview = body[:500] + "..." if len(body) > 500 else body

        # Prepare image upload instructions
        has_images = len(article_images) > 0
        image_info = ""
        if has_images:
            image_info = "\n**Article Images to Upload:**\n"
            for idx, img in enumerate(article_images, 1):
                image_info += f"  {idx}. {img['filename']} (local path: {img['local_path']})\n"

        instructions = f"""You are an AI assistant helping to publish an article to a WordPress website with proper SEO configuration.

**Your Task:**
1. Navigate to the WordPress admin dashboard
2. Log in if needed
3. Create a new post
4. {'Upload article images to WordPress media library' if has_images else 'Skip image upload (no images)'}
5. Set up the article content and SEO metadata
6. Publish the article
7. Return the published article URL and ID

**WordPress Details:**
- Admin URL: {cms_url}/wp-admin
- Username: {username}
- Password: {password}

**Article Content:**
Title: {title}
Body Preview: {body_preview}
[Full body content will be provided when needed]{image_info}

**SEO Configuration (use Yoast SEO or Rank Math if available):**
- Meta Title: {seo_data.meta_title}
- Meta Description: {seo_data.meta_description}
- Focus Keyword: {seo_data.focus_keyword}
- Additional Keywords: {', '.join(seo_data.keywords)}
- Canonical URL: {seo_data.canonical_url or 'Auto-generate'}

**Open Graph Tags:**
- OG Title: {seo_data.og_title or seo_data.meta_title}
- OG Description: {seo_data.og_description or seo_data.meta_description}

**Step-by-Step Instructions:**

1. **Navigate to WordPress Admin**
   - Use the computer tool to open a browser
   - Go to: {cms_url}/wp-admin
   - Take a screenshot to verify the login page loaded

2. **Login**
   - Enter username: {username}
   - Enter password: {password}
   - Click "Log In"
   - Wait for dashboard to load
   - Take a screenshot of the dashboard

3. **Create New Post**
   - Click "Posts" → "Add New" (or "+ New" → "Post")
   - Wait for the block editor to load
   - Take a screenshot

4. **Set Article Title**
   - Click on the title field
   - Enter title: {title}
   - Take a screenshot

{"5. **Upload Article Images to WordPress Media Library**" + '''
   - For each image file provided in the article images list above:
     a. Click "+ Add Block" or the Insert Media button
     b. Click "Upload" or "Media Library"
     c. Use the computer tool to upload the image file from its local path
     d. Wait for upload to complete
     e. Note the image URL from WordPress media library
   - After all images are uploaded, you can insert them into the article content
   - Take a screenshot showing uploaded media
   - IMPORTANT: Replace any Google Drive image references in the article body with the WordPress media URLs

6. ''' if has_images else "5. "}**Add Article Content**
   - Click on the content area
   - Use the text editor tool to paste the full article body
   - {"Insert the uploaded images at appropriate locations in the content" if has_images else "Format the content appropriately (headings, paragraphs, etc.)"}
   - Take a screenshot

{"7" if has_images else "6"}. **Configure Yoast SEO / Rank Math (if available)**
   - Scroll down to the SEO meta box (usually below the editor or in sidebar)
   - Set Focus Keyword: {seo_data.focus_keyword}
   - Edit Meta Title to: {seo_data.meta_title}
   - Edit Meta Description to: {seo_data.meta_description}
   - Verify SEO score is green/acceptable
   - Take a screenshot of SEO settings

{"8" if has_images else "7"}. **Publish Article**
   - Click the "Publish" button (top right)
   - If prompted, click "Publish" again to confirm
   - Wait for "Post published" confirmation
   - Take a screenshot of the success message

{"9" if has_images else "8"}. **Capture Article URL and ID**
   - Look for the "View Post" link or the article URL in the success message
   - Note the post ID (usually in the URL as ?post=123)
   - Take a final screenshot

{"10" if has_images else "9"}. **Return Results**
   - Provide the article URL and post ID in your final response
   - Format: {{"article_url": "...", "article_id": "..."}}

**Important Notes:**
- Take screenshots at each major step for verification
- If you encounter any errors, document them and try to resolve
- If the SEO plugin (Yoast/Rank Math) is not available, skip those steps
- Use the bash tool if you need to verify network connectivity
- The full article body is:

{body}

**Start the task now. Good luck!**
"""
        return instructions

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        """Execute a Computer Use tool call.

        Note: In production, this would be handled by the Computer Use runtime.
        For now, this is a placeholder that simulates tool execution.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters
            session_id: Computer Use session ID

        Returns:
            dict: Tool execution result
        """
        logger.info(
            "tool_execution_simulated",
            tool_name=tool_name,
            tool_input=tool_input,
            session_id=session_id,
        )

        # In production, Computer Use runtime would handle actual execution
        # This is a simulation for development
        return {
            "success": True,
            "output": "Tool execution simulated",
            "tool_name": tool_name,
        }

    def _save_screenshot(
        self,
        screenshot_data: str,
        session_id: str,
        iteration: int,
    ) -> str:
        """Save screenshot to storage.

        Args:
            screenshot_data: Base64 encoded screenshot
            session_id: Computer Use session ID
            iteration: Iteration number

        Returns:
            str: Screenshot URL or file path
        """
        # In production, upload to S3 or local storage
        # For now, return a placeholder
        return f"/screenshots/{session_id}/screenshot_{iteration}.png"

    def _extract_final_result(self, response: BetaMessage) -> dict[str, Any]:
        """Extract final article URL and ID from response.

        Args:
            response: Claude's response message

        Returns:
            dict: Extracted article data
        """
        # Parse response to extract article URL and ID
        for block in response.content:
            if block.type == "text":
                text = block.text
                # Try to extract JSON result
                try:
                    if "{" in text and "}" in text:
                        start = text.find("{")
                        end = text.rfind("}") + 1
                        json_str = text[start:end]
                        result = json.loads(json_str)
                        return result
                except json.JSONDecodeError:
                    pass

        # Fallback: return empty result
        return {"article_url": None, "article_id": None}


async def create_computer_use_cms_service() -> ComputerUseCMSService:
    """Factory function for Computer Use CMS service.

    Returns:
        ComputerUseCMSService: Configured service instance
    """
    return ComputerUseCMSService()
