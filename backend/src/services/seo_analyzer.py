"""SEO analysis service using Claude AI."""

import json
from typing import Any

from anthropic import AsyncAnthropic

from src.api.schemas.seo import SEOAnalysisResponse, SEOMetadata
from src.config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class SEOAnalyzerService:
    """Service for analyzing articles and generating SEO metadata."""

    def __init__(self) -> None:
        """Initialize SEO analyzer service."""
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def analyze_article(
        self,
        title: str,
        body: str,
        target_keyword: str | None = None,
    ) -> SEOAnalysisResponse:
        """Analyze article and generate SEO metadata.

        Args:
            title: Article title
            body: Article body content
            target_keyword: Optional target keyword to optimize for

        Returns:
            SEOAnalysisResponse: SEO analysis results with metadata and suggestions

        Raises:
            Exception: If API call fails
        """
        prompt = self._build_seo_analysis_prompt(title, body, target_keyword)

        try:
            logger.info(
                "seo_analysis_started",
                title=title[:100],
                target_keyword=target_keyword,
            )

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more consistent SEO analysis
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse JSON response
            content = response.content[0].text
            result = self._parse_seo_response(content)

            logger.info(
                "seo_analysis_completed",
                meta_title_length=len(result["seo_data"]["meta_title"]),
                meta_desc_length=len(result["seo_data"]["meta_description"]),
                focus_keyword=result["seo_data"]["focus_keyword"],
            )

            return SEOAnalysisResponse(**result)

        except Exception as e:
            logger.error("seo_analysis_failed", error=str(e), exc_info=True)
            raise

    def _build_seo_analysis_prompt(
        self,
        title: str,
        body: str,
        target_keyword: str | None,
    ) -> str:
        """Build the prompt for SEO analysis.

        Args:
            title: Article title
            body: Article body
            target_keyword: Optional target keyword

        Returns:
            str: Formatted prompt
        """
        # Calculate word count for readability analysis
        word_count = len(body.split())

        keyword_instruction = (
            f"\n- Target keyword to optimize for: {target_keyword}"
            if target_keyword
            else ""
        )

        prompt = f"""Analyze this article and generate comprehensive SEO metadata.

Article Title: {title}
Word Count: {word_count}
{keyword_instruction}

Article Content:
{body[:3000]}{"..." if len(body) > 3000 else ""}

Generate SEO-optimized metadata following these requirements:

1. **Meta Title** (50-60 characters):
   - Include primary keyword near the beginning
   - Make it compelling and click-worthy
   - Must be between 50-60 characters

2. **Meta Description** (120-160 characters):
   - Summarize the article's value
   - Include primary keyword naturally
   - Include a call-to-action
   - Must be between 120-160 characters

3. **Focus Keyword**:
   - Identify the primary keyword this article should rank for
   - Should appear in title, meta description, and naturally in content

4. **Additional Keywords** (3-5 keywords):
   - Related keywords and LSI (Latent Semantic Indexing) terms
   - Should complement the focus keyword

5. **Open Graph Tags**:
   - og_title: Social media optimized title (up to 70 chars)
   - og_description: Social media description (up to 200 chars)

6. **SEO Score** (0-100):
   - Overall SEO optimization score
   - Based on keyword usage, readability, structure, etc.

7. **Readability Score** (0-100):
   - Flesch-Kincaid readability score
   - Target: 60-70 (8th-9th grade level)

8. **Suggestions**:
   - 3-5 actionable suggestions to improve SEO
   - Focus on keyword placement, readability, structure

9. **Warnings**:
   - Any SEO issues detected
   - Missing elements, keyword stuffing, etc.

Return ONLY a valid JSON object with this exact structure:
{{
    "seo_data": {{
        "meta_title": "SEO optimized title here (50-60 chars)",
        "meta_description": "Compelling description here (120-160 chars)",
        "focus_keyword": "primary keyword",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "canonical_url": null,
        "og_title": "Social media title (up to 70 chars)",
        "og_description": "Social media description (up to 200 chars)",
        "og_image": null,
        "schema_type": "Article",
        "readability_score": 65.5,
        "seo_score": 85.0
    }},
    "suggestions": [
        "Suggestion 1",
        "Suggestion 2",
        "Suggestion 3"
    ],
    "warnings": [
        "Warning 1 if any",
        "Warning 2 if any"
    ]
}}

Important: Return ONLY the JSON object, no additional text or explanation.
"""
        return prompt

    def _parse_seo_response(self, content: str) -> dict[str, Any]:
        """Parse Claude's SEO analysis response.

        Args:
            content: Raw JSON response from Claude

        Returns:
            dict: Parsed SEO analysis data

        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            # Extract JSON from response (in case there's extra text)
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")

            json_str = content[start_idx:end_idx]
            result = json.loads(json_str)

            # Validate required fields
            if "seo_data" not in result:
                raise ValueError("Missing 'seo_data' in response")

            return result

        except json.JSONDecodeError as e:
            logger.error("seo_response_parse_failed", error=str(e), content=content[:500])
            raise ValueError(f"Invalid JSON response: {e}")

    async def generate_seo_for_article(
        self,
        article_data: dict[str, str],
    ) -> SEOMetadata:
        """Convenience method to generate SEO for article data.

        Args:
            article_data: Dict with 'title', 'body', optional 'target_keyword'

        Returns:
            SEOMetadata: Generated SEO metadata
        """
        analysis = await self.analyze_article(
            title=article_data["title"],
            body=article_data["body"],
            target_keyword=article_data.get("target_keyword"),
        )

        return analysis.seo_data


async def create_seo_analyzer() -> SEOAnalyzerService:
    """Factory function for SEO analyzer service.

    Returns:
        SEOAnalyzerService: Configured service instance
    """
    return SEOAnalyzerService()
