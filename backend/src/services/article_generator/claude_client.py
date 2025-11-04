"""Claude API client wrapper for article generation."""

from typing import Any

from anthropic import AsyncAnthropic

from src.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class ClaudeClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(self) -> None:
        """Initialize Claude client."""
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS

    async def generate_article(
        self,
        topic: str,
        style_tone: str = "professional",
        target_word_count: int = 1000,
        outline: str | None = None,
    ) -> dict[str, Any]:
        """Generate article using Claude API.

        Args:
            topic: Article topic description
            style_tone: Writing style (professional, casual, technical)
            target_word_count: Target word count
            outline: Optional outline structure

        Returns:
            dict: Generated article with title, body, and metadata

        Raises:
            Exception: If API call fails
        """
        prompt = self._build_prompt(topic, style_tone, target_word_count, outline)

        try:
            logger.info(
                "claude_api_request",
                topic=topic[:100],
                word_count=target_word_count,
                style=style_tone,
            )

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract content from response
            content = response.content[0].text

            # Parse the response to extract title and body
            result = self._parse_response(content)

            # Calculate tokens and cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                "claude_api_success",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                word_count=len(result["body"].split()),
            )

            result["metadata"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "model": self.model,
            }

            return result

        except Exception as e:
            logger.error("claude_api_error", error=str(e), exc_info=True)
            raise

    def _build_prompt(
        self,
        topic: str,
        style_tone: str,
        target_word_count: int,
        outline: str | None,
    ) -> str:
        """Build the prompt for Claude.

        Args:
            topic: Article topic
            style_tone: Writing style
            target_word_count: Target word count
            outline: Optional outline

        Returns:
            str: Formatted prompt
        """
        prompt_parts = [
            f"Write a comprehensive, well-structured article about: {topic}",
            "",
            "Requirements:",
            f"- Writing style: {style_tone}",
            f"- Target length: approximately {target_word_count} words",
            "- Format: Use Markdown formatting",
            "- Include a compelling title",
            "- Use clear headings and subheadings",
            "- Include examples where appropriate",
        ]

        if outline:
            prompt_parts.extend(
                [
                    "",
                    "Suggested outline:",
                    outline,
                ]
            )

        prompt_parts.extend(
            [
                "",
                "Format the response as:",
                "# [Title Here]",
                "",
                "[Article body in Markdown...]",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_response(self, content: str) -> dict[str, str]:
        """Parse Claude's response to extract title and body.

        Args:
            content: Raw response content

        Returns:
            dict: Parsed article with title and body
        """
        lines = content.strip().split("\n")

        # Extract title (first markdown heading)
        title = "Untitled Article"
        body_lines = []
        title_found = False

        for line in lines:
            if line.startswith("# ") and not title_found:
                title = line[2:].strip()
                title_found = True
            elif title_found:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()

        return {"title": title, "body": body}

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            float: Cost in USD

        Note:
            Pricing as of Oct 2024 for Claude 3.5 Sonnet:
            - Input: $3.00 per million tokens
            - Output: $15.00 per million tokens
        """
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        return round(input_cost + output_cost, 4)


async def get_claude_client() -> ClaudeClient:
    """Get Claude client instance.

    Returns:
        ClaudeClient: Configured Claude client
    """
    return ClaudeClient()
