"""Computer Use service for automated CMS operations."""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any

from anthropic import Anthropic
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
        self.model = "claude-opus-4-5-20251101"  # Opus 4.5 with Computer Use support
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
        tags: list[str] | None = None,
        categories: list[str] | None = None,
        article_images: list[dict[str, Any]] | None = None,
        publish_mode: str = "publish",
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
            tags: List of WordPress post tags (3-6 recommended)
            categories: List of WordPress post categories (1-3 recommended)
            article_images: List of image metadata dicts with local_path for upload
            publish_mode: "publish" to make the post live, "draft" to save without publishing

        Returns:
            dict: Publishing result with status, URL, metadata

        Raises:
            Exception: If publishing fails after retries
        """
        start_time = time.time()
        session_id = f"cu_{int(time.time())}"

        publish_mode = (publish_mode or "publish").lower()
        if publish_mode not in {"publish", "draft"}:
            raise ValueError(f"Unsupported publish_mode: {publish_mode}")

        logger.info(
            "computer_use_cms_started",
            session_id=session_id,
            cms_type=cms_type,
            article_title=article_title[:100],
            publish_mode=publish_mode,
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
                tags=tags,
                categories=categories,
                article_images=article_images or [],
                publish_mode=publish_mode,
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
                    metadata_dict = metadata.model_dump()
                    metadata_dict["publish_mode"] = publish_mode

                    status_value = "draft" if publish_mode == "draft" else "published"
                    article_id = final_result.get("article_id")
                    article_url = final_result.get("article_url")
                    editor_url = final_result.get("editor_url") or final_result.get("edit_url")

                    if publish_mode == "draft":
                        result_message = "Article saved as draft via Computer Use"
                        public_url = None
                        editor_reference = editor_url or article_url
                    else:
                        result_message = "Article published successfully via Computer Use"
                        public_url = article_url or editor_url
                        editor_reference = editor_url

                    logger.info(
                        "computer_use_cms_completed",
                        session_id=session_id,
                        execution_time=execution_time,
                        screenshots_count=len(screenshots),
                    )

                    return {
                        "success": True,
                        "cms_article_id": article_id,
                        "url": public_url,
                        "editor_url": editor_reference,
                        "metadata": metadata_dict,
                        "message": result_message,
                        "status": status_value,
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
            metadata_dict = metadata.model_dump()
            metadata_dict["publish_mode"] = publish_mode

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
                "metadata": metadata_dict,
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
        tags: list[str] | None,
        categories: list[str] | None,
        article_images: list[dict[str, Any]],
        publish_mode: str,
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
            tags: WordPress post tags
            categories: WordPress post categories
            article_images: List of image metadata with local paths

        Returns:
            str: Detailed instructions for Claude
        """
        if cms_type == "wordpress":
            return self._build_wordpress_instructions(
                cms_url=cms_url,
                username=cms_username,
                password=cms_password,
                title=article_title,
                body=article_body,
                seo_data=seo_data,
                article_images=article_images,
                tags=tags,
                categories=categories,
                publish_mode=publish_mode,
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
        article_images: list[dict[str, Any]],
        tags: list[str] | None = None,
        categories: list[str] | None = None,
        publish_mode: str = "publish",
    ) -> str:
        """Build WordPress-specific instructions."""

        tags = tags or []
        categories = categories or []
        has_images = bool(article_images)

        body_preview = body[:500] + "..." if len(body) > 500 else body

        if has_images:
            # Build detailed image info with position and caption for precise insertion
            image_lines = []
            for idx, img in enumerate(article_images, 1):
                position = img.get('position', 0)
                caption = img.get('caption', 'No caption provided')
                alt_text = img.get('alt_text', caption)  # Use caption as alt if not provided
                filename = img.get('filename', f'image_{idx}')
                local_path = img.get('local_path', '')
                source_url = img.get('source_url', '')

                image_lines.append(
                    f"  Image {idx}:\n"
                    f"    - Filename: {filename}\n"
                    f"    - Insert after paragraph: {position} (0 = before first paragraph, 1 = after first paragraph, etc.)\n"
                    f"    - Caption/Alt text: {caption[:100]}{'...' if len(caption) > 100 else ''}\n"
                    f"    - Local path: {local_path}\n"
                    f"    - Original URL: {source_url[:80]}{'...' if len(str(source_url)) > 80 else ''}"
                )

            image_info = "\n**Article Images to Upload (with exact positions):**\n" + "\n".join(image_lines)
        else:
            image_info = ""

        if tags:
            tags_info = "\n**WordPress Tags to Add:**\n" + "\n".join(f"  - {tag}" for tag in tags)
        else:
            tags_info = ""

        if categories:
            categories_info = "\n**WordPress Categories to Select/Create:**\n" + "\n".join(
                f"  - {category}" for category in categories
            )
        else:
            categories_info = ""

        publish_summary = (
            "Save the article as a draft (do not publish to the live site)"
            if publish_mode == "draft"
            else "Publish the article to the live site"
        )

        summary_steps = [
            "Navigate to the WordPress admin dashboard",
            "Log in if needed",
            "Create a new post",
            "Set article title and content",
            (
                "Upload article images to the WordPress media library and insert them into the content"
                if has_images
                else "Skip image upload (no images provided)"
            ),
            (
                "Set WordPress tags and categories"
                if tags or categories
                else "Skip tags/categories (none provided)"
            ),
            "Configure SEO metadata (Yoast SEO or Rank Math)",
            publish_summary,
            "Return the post ID and relevant URLs",
        ]

        summary_block = "\n".join(f"{idx}. {item}" for idx, item in enumerate(summary_steps, start=1))

        steps: list[str] = []
        step_no = 1

        def add_step(title_text: str, bullet_points: list[str]) -> None:
            nonlocal step_no
            bullets = "\n   - ".join(bullet_points)
            steps.append(f"{step_no}. **{title_text}**\n   - {bullets}")
            step_no += 1

        add_step(
            "Navigate to WordPress Admin",
            [
                f"Open {cms_url}/wp-admin in the browser using the computer tool",
                "Wait for the login page to load completely",
                "Take a screenshot for verification",
            ],
        )

        add_step(
            "Log In",
            [
                f"Enter username: {username}",
                f"Enter password: {password}",
                'Click the "Log In" button and wait for the dashboard',
                "Capture a screenshot of the dashboard once loaded",
            ],
        )

        add_step(
            "Create a New Post",
            [
                'Use the dashboard navigation to open "Posts" → "Add New" (or the "+ New" shortcut)',
                "Allow the Gutenberg editor to load fully",
                "Take a screenshot of the blank editor",
            ],
        )

        add_step(
            "Set the Article Title",
            [
                'Click the title field (usually labelled "Add title")',
                f"Paste the article title: {title}",
                "Take a screenshot once the title is entered",
            ],
        )

        if has_images:
            # Build specific insertion instructions for each image
            image_insertion_instructions = []
            for idx, img in enumerate(article_images, 1):
                position = img.get('position', 0)
                caption = img.get('caption', '')
                filename = img.get('filename', f'image_{idx}')

                if position == 0:
                    position_desc = "at the very beginning of the article (before the first paragraph)"
                else:
                    position_desc = f"after paragraph {position}"

                image_insertion_instructions.append(
                    f"Image {idx} ({filename}): Insert {position_desc}"
                    + (f" with caption: '{caption[:50]}...'" if caption else "")
                )

            add_step(
                "Upload and Insert Article Images at Correct Positions",
                [
                    'Open the media uploader from the editor ("Add Block" → Image or "Add media")',
                    "Upload each provided file and wait for uploads to complete",
                    "**IMPORTANT: Insert each image at its specified position:**",
                ]
                + image_insertion_instructions
                + [
                    "For each image: Set the alt text to the provided caption",
                    "Ensure the images appear in the exact positions specified above",
                    "Take a screenshot showing the images inserted in the content",
                ],
            )

        add_step(
            "Add Article Content",
            [
                "Click inside the content area of the editor",
                "Use the text editor tool to paste the full article body (provided below)",
                "Ensure formatting is preserved (headings, paragraphs, lists, etc.)",
                (
                    "Confirm that uploaded images appear in the correct locations within the content"
                    if has_images
                    else "No images were provided, so focus on text formatting only"
                ),
                "Take a screenshot of the populated editor",
            ],
        )

        if tags or categories:
            tag_instructions = (
                [
                    'In the right sidebar, expand the "Tags" panel',
                    f"Add each tag from the list: {', '.join(tags)}",
                    "Verify that every tag appears as a chip/pill under the input field",
                ]
                if tags
                else ["No tags provided; skip this section"]
            )

            category_instructions = (
                [
                    'In the right sidebar, expand the "Categories" panel',
                    "Select existing categories or create new ones matching the list below",
                    f"Categories to apply: {', '.join(categories)}",
                    "Confirm the chosen categories are checked",
                ]
                if categories
                else ["No categories provided; skip this section"]
            )

            add_step(
                "Set Tags and Categories",
                tag_instructions + category_instructions + ["Capture a screenshot of the sidebar selections"],
            )

        add_step(
            "Configure SEO Metadata",
            [
                "Scroll to the Yoast SEO (or Rank Math) panel",
                f"Set the focus keyphrase to: {seo_data.focus_keyword}",
                f"Update the SEO title to: {seo_data.meta_title}",
                f"Update the meta description to: {seo_data.meta_description}",
                "Review the SEO analysis indicator (green is ideal, orange is acceptable)",
                "Take a screenshot of the SEO configuration",
            ],
        )

        if publish_mode == "draft":
            add_step(
                "Save as Draft (Do NOT Publish)",
                [
                    'Click the "Save draft" button at the top right',
                    'Wait for the "Draft saved" confirmation message',
                    'Verify the post status indicator shows "Draft"',
                    "Capture a screenshot of the confirmation/status indicator",
                ],
            )
        else:
            add_step(
                "Publish the Article",
                [
                    'Click the "Publish" button and confirm if prompted',
                    'Wait for the "Post published" success message',
                    "Capture a screenshot of the confirmation",
                ],
            )

        add_step(
            "Capture Post Links and ID",
            [
                'Copy the "View Post" link if available (for drafts, copy the editor URL)',
                "Note the WordPress post ID (visible in the URL as ?post=ID or post=ID)",
                "Take a final screenshot for records",
            ],
        )

        result_example = (
            '{"article_id": "<POST_ID>", "article_url": "<PUBLIC_URL>", "editor_url": "<EDITOR_URL>", "status": "published"}'
            if publish_mode != "draft"
            else '{"article_id": "<POST_ID>", "article_url": null, "editor_url": "<EDITOR_URL>", "status": "draft"}'
        )

        add_step(
            "Return Results",
            [
                "Respond with a JSON object containing the post ID, URLs, and status.",
                f"Example payload: {result_example}",
                "Ensure URLs are absolute and valid.",
            ],
        )

        detailed_block = "\n\n".join(steps)

        instructions = f"""You are an AI assistant helping to prepare an article in WordPress with full SEO configuration.

**Your Task:**
{summary_block}

**WordPress Details:**
- Admin URL: {cms_url}/wp-admin
- Username: {username}
- Password: {password}

**Article Content:**
Title: {title}
Body Preview: {body_preview}
[Full body content will be provided when needed]{image_info}{tags_info}{categories_info}

**SEO Configuration (Yoast SEO / Rank Math):**
- Meta Title: {seo_data.meta_title}
- Meta Description: {seo_data.meta_description}
- Focus Keyword: {seo_data.focus_keyword}
- Additional Keywords: {', '.join(seo_data.keywords)}
- Canonical URL: {seo_data.canonical_url or 'Auto-generate'}
- OG Title: {seo_data.og_title or seo_data.meta_title}
- OG Description: {seo_data.og_description or seo_data.meta_description}

**Step-by-Step Instructions:**
{detailed_block}

**Important Notes:**
- Take screenshots at each major step for audit purposes.
- If any errors appear, document them and attempt a reasonable recovery.
- If the SEO plugin is unavailable, note it and continue.
- Current publishing mode: "{publish_mode}". If it is "draft", never click the Publish button.
- Use the bash tool only if network diagnostics are required.
- The full article body is provided below for reference.

--- FULL ARTICLE BODY START ---
{body}
--- FULL ARTICLE BODY END ---

Begin the task now and follow the steps carefully."""

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
