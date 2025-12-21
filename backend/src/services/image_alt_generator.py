"""Image Alt Text and Description Generator Service

Uses GPT-4o vision to generate accurate alt text and descriptions for images.
Implements hybrid strategy: vision analysis when image accessible, context-based fallback otherwise.

Phase 13: Enhanced Image Review
"""

import base64
import json
import re
from dataclasses import dataclass
from enum import Enum

import httpx
from openai import AsyncOpenAI

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


class GenerationMethod(str, Enum):
    """Method used to generate alt text"""
    VISION = "vision"
    CONTEXT = "context"
    FAILED = "failed"


@dataclass
class ImageAltSuggestion:
    """Generated alt text and description suggestion"""
    image_id: int

    # Original parsed content (may be None)
    parsed_alt_text: str | None
    parsed_caption: str | None
    parsed_description: str | None

    # AI suggestions
    suggested_alt_text: str
    suggested_alt_text_confidence: float  # 0-1
    suggested_description: str
    suggested_description_confidence: float  # 0-1

    # Generation metadata
    generation_method: GenerationMethod
    model_used: str
    tokens_used: int
    error_message: str | None = None


class ImageAltGeneratorService:
    """Service for generating image alt text and descriptions using GPT-4o vision

    Implements hybrid strategy:
    1. Try vision analysis if image URL is accessible
    2. Fall back to context-based generation if image not accessible
    """

    def __init__(self):
        """Initialize the service with OpenAI client"""
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL or "gpt-4o"
        self.client: AsyncOpenAI | None = None

        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            logger.warning("OPENAI_API_KEY not configured, image alt generation will be unavailable")

    async def generate_suggestions(
        self,
        image_id: int,
        image_url: str | None,
        article_context: dict,
        parsed_alt_text: str | None = None,
        parsed_caption: str | None = None,
        parsed_description: str | None = None,
        use_vision: bool = True
    ) -> ImageAltSuggestion:
        """Generate alt text and description suggestions for an image

        Args:
            image_id: Database ID of the image
            image_url: URL to the image (preview or source)
            article_context: Dict with title, excerpt, position info
            parsed_alt_text: Original alt text from parsing (if any)
            parsed_caption: Original caption from parsing (if any)
            parsed_description: Original description from parsing (if any)
            use_vision: Whether to attempt vision analysis

        Returns:
            ImageAltSuggestion with generated suggestions
        """
        if not self.client:
            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text="",
                suggested_alt_text_confidence=0.0,
                suggested_description="",
                suggested_description_confidence=0.0,
                generation_method=GenerationMethod.FAILED,
                model_used=self.model,
                tokens_used=0,
                error_message="OpenAI API key not configured"
            )

        # Try vision analysis first if enabled and URL available
        if use_vision and image_url:
            image_accessible = await self._check_image_accessible(image_url)
            if image_accessible:
                logger.info(f"Image accessible, using vision analysis for image {image_id}")
                return await self._generate_with_vision(
                    image_id=image_id,
                    image_url=image_url,
                    article_context=article_context,
                    parsed_alt_text=parsed_alt_text,
                    parsed_caption=parsed_caption,
                    parsed_description=parsed_description
                )
            else:
                logger.info(f"Image not accessible, falling back to context for image {image_id}")

        # Fall back to context-based generation
        return await self._generate_from_context(
            image_id=image_id,
            article_context=article_context,
            parsed_alt_text=parsed_alt_text,
            parsed_caption=parsed_caption,
            parsed_description=parsed_description
        )

    async def _check_image_accessible(self, image_url: str) -> bool:
        """Check if image URL is accessible

        Args:
            image_url: URL to check

        Returns:
            True if image can be fetched
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(image_url, follow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    return content_type.startswith("image/")
                return False
        except Exception as e:
            logger.debug(f"Image accessibility check failed: {e}")
            return False

    async def _generate_with_vision(
        self,
        image_id: int,
        image_url: str,
        article_context: dict,
        parsed_alt_text: str | None,
        parsed_caption: str | None,
        parsed_description: str | None
    ) -> ImageAltSuggestion:
        """Generate using GPT-4o vision analysis

        Args:
            image_id: Database ID
            image_url: Accessible image URL
            article_context: Article context dict
            parsed_alt_text: Existing alt text
            parsed_caption: Existing caption
            parsed_description: Existing description

        Returns:
            ImageAltSuggestion with vision-based suggestions
        """
        title = article_context.get("title", "")
        excerpt = article_context.get("excerpt", "")[:500] if article_context.get("excerpt") else ""
        position = article_context.get("position", 0)
        is_featured = article_context.get("is_featured", False)

        position_desc = "特色圖片（文章封面）" if is_featured else f"第 {position + 1} 張配圖"

        system_prompt = """你是一個專業的圖片 SEO 和無障礙專家。請分析圖片並生成：

1. Alt Text（替代文字）：
   - 簡潔描述圖片內容，用於視障用戶和 SEO
   - 長度：50-125 個字符
   - 不要以「圖片」「照片」開頭
   - 包含相關關鍵詞但自然流暢
   - 使用繁體中文

2. Description（媒體庫描述）：
   - 詳細描述圖片內容，用於 WordPress 媒體庫
   - 長度：100-300 個字符
   - 包含場景、人物、動作等細節
   - 適合媒體庫搜索
   - 使用繁體中文

請以 JSON 格式回覆：
{
  "alt_text": "替代文字內容",
  "alt_text_confidence": 0.95,
  "description": "詳細描述內容",
  "description_confidence": 0.95
}

confidence 為 0-1 之間的數值，表示你對建議的信心程度。"""

        user_prompt = f"""請分析此圖片並生成 Alt Text 和 Description。

文章上下文：
- 標題：{title}
- 摘要：{excerpt}
- 圖片位置：{position_desc}
- 現有圖說：{parsed_caption or "無"}
- 現有 Alt Text：{parsed_alt_text or "無"}

請結合圖片視覺內容和文章上下文，生成最準確的建議。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "low"  # Use low detail for cost efficiency
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Parse JSON response
            result = self._parse_json_response(content)

            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text=result.get("alt_text", ""),
                suggested_alt_text_confidence=result.get("alt_text_confidence", 0.9),
                suggested_description=result.get("description", ""),
                suggested_description_confidence=result.get("description_confidence", 0.9),
                generation_method=GenerationMethod.VISION,
                model_used=self.model,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Vision generation failed: {e}")
            # Fall back to context-based generation
            return await self._generate_from_context(
                image_id=image_id,
                article_context=article_context,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description
            )

    async def _generate_from_context(
        self,
        image_id: int,
        article_context: dict,
        parsed_alt_text: str | None,
        parsed_caption: str | None,
        parsed_description: str | None
    ) -> ImageAltSuggestion:
        """Generate using article context only (fallback)

        Args:
            image_id: Database ID
            article_context: Article context dict
            parsed_alt_text: Existing alt text
            parsed_caption: Existing caption
            parsed_description: Existing description

        Returns:
            ImageAltSuggestion with context-based suggestions
        """
        title = article_context.get("title", "")
        excerpt = article_context.get("excerpt", "")[:500] if article_context.get("excerpt") else ""
        position = article_context.get("position", 0)
        is_featured = article_context.get("is_featured", False)

        position_desc = "特色圖片（文章封面）" if is_featured else f"第 {position + 1} 張配圖"

        system_prompt = """你是一個專業的圖片 SEO 和無障礙專家。基於文章上下文推斷圖片內容並生成：

1. Alt Text（替代文字）：
   - 根據上下文推斷圖片可能的內容
   - 長度：50-125 個字符
   - 不要以「圖片」「照片」開頭
   - 使用繁體中文

2. Description（媒體庫描述）：
   - 根據上下文推斷並描述
   - 長度：100-300 個字符
   - 使用繁體中文

注意：由於無法直接看到圖片，請根據文章上下文和圖說進行合理推斷。

請以 JSON 格式回覆：
{
  "alt_text": "替代文字內容",
  "alt_text_confidence": 0.7,
  "description": "詳細描述內容",
  "description_confidence": 0.7
}

由於是推斷，confidence 通常在 0.5-0.8 之間。"""

        user_prompt = f"""請根據以下文章上下文，推斷圖片內容並生成 Alt Text 和 Description。

文章上下文：
- 標題：{title}
- 摘要：{excerpt}
- 圖片位置：{position_desc}
- 現有圖說：{parsed_caption or "無"}
- 現有 Alt Text：{parsed_alt_text or "無"}

請基於上下文進行合理推斷。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Parse JSON response
            result = self._parse_json_response(content)

            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text=result.get("alt_text", ""),
                suggested_alt_text_confidence=result.get("alt_text_confidence", 0.7),
                suggested_description=result.get("description", ""),
                suggested_description_confidence=result.get("description_confidence", 0.7),
                generation_method=GenerationMethod.CONTEXT,
                model_used=self.model,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Context generation failed: {e}")
            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text="",
                suggested_alt_text_confidence=0.0,
                suggested_description="",
                suggested_description_confidence=0.0,
                generation_method=GenerationMethod.FAILED,
                model_used=self.model,
                tokens_used=0,
                error_message=str(e)
            )

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON response from GPT, handling potential formatting issues

        Args:
            content: Raw response content

        Returns:
            Parsed dict
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Return empty dict if parsing fails
            logger.warning(f"Failed to parse JSON response: {content[:200]}")
            return {}


# Singleton instance
_service_instance: ImageAltGeneratorService | None = None


def get_image_alt_generator_service() -> ImageAltGeneratorService:
    """Get singleton instance of ImageAltGeneratorService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ImageAltGeneratorService()
    return _service_instance
