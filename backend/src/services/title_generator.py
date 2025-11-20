"""
Title Generator Service

独立的标题生成服务，专门用于生成SEO优化的标题建议。
与统一解析器分离，确保100%成功率。
"""

import json
import logging
from typing import List, Dict, Optional
from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TitleSuggestion(BaseModel):
    """Single title suggestion with metadata"""
    prefix: Optional[str] = Field(None, description="Optional prefix like 【深度】")
    main: str = Field(..., description="Main title content")
    suffix: Optional[str] = Field(None, description="Optional suffix for emphasis")
    score: float = Field(..., ge=0, le=1, description="Quality score 0-1")
    reason: str = Field(..., description="Why this title is good")


class TitleGenerationResult(BaseModel):
    """Result of title generation"""
    suggested_titles: List[Dict] = Field(..., min_items=2, max_items=3)
    success: bool = True
    error: Optional[str] = None


class TitleGeneratorService:
    """
    独立的标题生成服务

    特点：
    1. 专注于标题生成，不包含其他复杂功能
    2. 简化的prompt，更高的成功率
    3. 独立的API端点，可单独调用
    4. 备用生成策略，确保始终有输出
    """

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate_titles(
        self,
        article_title: str,
        article_content: str,
        max_retries: int = 2
    ) -> TitleGenerationResult:
        """
        Generate SEO-optimized title suggestions

        Args:
            article_title: Original article title
            article_content: Article body content (first 1000 chars used)
            max_retries: Number of retries if generation fails

        Returns:
            TitleGenerationResult with 2-3 title suggestions
        """

        # Truncate content to reduce tokens
        truncated_content = article_content[:1000] if len(article_content) > 1000 else article_content

        prompt = self._build_prompt(article_title, truncated_content)

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Generating titles, attempt {attempt + 1}/{max_retries + 1}")

                message = await self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",  # 使用最新 Sonnet 4.5 模型，最高質量
                    max_tokens=2048,  # Much smaller than unified parser
                    temperature=0.7,  # Slightly creative for title variations
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                # Parse response
                response_text = message.content[0].text
                logger.debug(f"Claude response: {response_text[:500]}")

                # Extract JSON
                result = self._extract_json(response_text)

                if result and "suggested_titles" in result and result["suggested_titles"]:
                    logger.info(f"Successfully generated {len(result['suggested_titles'])} titles")
                    return TitleGenerationResult(
                        suggested_titles=result["suggested_titles"],
                        success=True
                    )

            except Exception as e:
                logger.error(f"Title generation attempt {attempt + 1} failed: {e}")

        # If all attempts fail, use fallback generation
        logger.warning("All Claude attempts failed, using fallback generation")
        return self._generate_fallback_titles(article_title)

    def _build_prompt(self, original_title: str, content: str) -> str:
        """Build focused prompt for title generation only"""

        return f"""You are an SEO expert specializing in Chinese content optimization.

TASK: Generate 2-3 improved title variations for the following article.

ORIGINAL TITLE: {original_title}

ARTICLE EXCERPT:
{content}

REQUIREMENTS:
1. Each title must be more engaging and SEO-friendly than the original
2. Include relevant keywords naturally
3. Use Chinese language
4. Follow this exact JSON structure (no other output):

{{
    "suggested_titles": [
        {{
            "prefix": "【深度解析】",
            "main": "Your engaging main title here",
            "suffix": "附完整指南",
            "score": 0.95,
            "reason": "Why this title works well"
        }},
        {{
            "prefix": null,
            "main": "Another variation of the title",
            "suffix": null,
            "score": 0.88,
            "reason": "Explanation of effectiveness"
        }},
        {{
            "prefix": "【2024最新】",
            "main": "Third title variation",
            "suffix": "值得收藏",
            "score": 0.82,
            "reason": "Why readers would click"
        }}
    ]
}}

IMPORTANT:
- Output ONLY the JSON, no other text
- Generate exactly 2-3 variations
- Scores should be between 0.7 and 1.0
- Each title should take a different angle/approach"""

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from Claude response"""

        try:
            # Try direct parsing first
            return json.loads(text)
        except:
            # Try to find JSON block
            import re
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, text)

            for match in matches:
                try:
                    data = json.loads(match)
                    if "suggested_titles" in data:
                        return data
                except:
                    continue

        return None

    def _generate_fallback_titles(self, original_title: str) -> TitleGenerationResult:
        """Generate basic titles as fallback"""

        logger.info("Using fallback title generation")

        # Simple rule-based generation
        fallback_titles = [
            {
                "prefix": "【深度】",
                "main": original_title,
                "suffix": "完整解析",
                "score": 0.75,
                "reason": "Enhanced with depth indicator and comprehensive suffix"
            },
            {
                "prefix": None,
                "main": f"{original_title}：你需要知道的一切",
                "suffix": None,
                "score": 0.70,
                "reason": "Added value proposition for reader engagement"
            }
        ]

        return TitleGenerationResult(
            suggested_titles=fallback_titles,
            success=True,
            error="Fallback generation used"
        )