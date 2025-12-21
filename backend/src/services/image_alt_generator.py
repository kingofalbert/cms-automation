"""Image Alt Text and Description Generator Service

Uses Gemini 3.0 Flash (default) or GPT-4o vision to generate accurate alt text and descriptions.
Implements smart detection to distinguish between:
- Infographic (信息圖): Images with embedded text - requires OCR extraction
- Photo (照片): Images without text - requires visual description

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

# Try to import Vertex AI - optional dependency
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger.warning("vertexai not installed, Gemini vision will be unavailable")


class GenerationMethod(str, Enum):
    """Method used to generate alt text"""
    VISION = "vision"
    VISION_INFOGRAPHIC = "vision_infographic"  # Vision with OCR for text extraction
    VISION_PHOTO = "vision_photo"  # Vision for visual description
    CONTEXT = "context"
    FAILED = "failed"


class ImageType(str, Enum):
    """Type of image for alt text generation strategy"""
    INFOGRAPHIC = "infographic"  # 信息圖 - Image with embedded text/data
    PHOTO = "photo"  # 照片 - Image without embedded text
    UNKNOWN = "unknown"


class VisionProvider(str, Enum):
    """Vision AI provider"""
    GEMINI = "gemini"
    OPENAI = "openai"


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

    # Image analysis results
    image_type: ImageType
    detected_text: str | None  # Text extracted from infographic images

    # Generation metadata
    generation_method: GenerationMethod
    model_used: str
    tokens_used: int
    error_message: str | None = None


class ImageAltGeneratorService:
    """Service for generating image alt text and descriptions using vision AI

    Supports two providers:
    - Gemini 3.0 Flash (default): Better OCR, 5x cheaper, faster
    - GPT-4o: Fallback option

    Implements smart image type detection:
    1. First detect if image contains embedded text (Infographic vs Photo)
    2. For Infographic: Extract text via OCR, then generate alt text including the text
    3. For Photo: Generate descriptive alt text based on visual content
    """

    # System prompt for image type detection and infographic OCR
    PROMPT_IMAGE_ANALYSIS = """你是圖片分析和 OCR 專家。請分析這張圖片：

**第一步：判斷圖片類型**
- 信息圖 (Infographic)：圖片上有嵌入的文字信息（標題、數據、說明文字等）
- 照片 (Photo)：圖片上沒有嵌入文字，純粹是照片或插圖

**第二步：如果是信息圖，提取所有文字**
請仔細識別並提取圖片上的所有文字內容，包括：
- 標題文字
- 副標題
- 正文/說明文字
- 數據/統計數字
- 來源標註
- 任何其他可見文字

**第三步：生成 Alt Text**
對於信息圖：
- Alt Text 必須包含圖片上的文字內容（這是最重要的）
- 描述文字的視覺呈現方式
- 長度：100-200 個字符
- 使用繁體中文

對於照片：
- 簡潔描述圖片視覺內容
- 長度：50-125 個字符
- 不要以「圖片」「照片」開頭
- 使用繁體中文

**第四步：生成 Description**
- 詳細描述，用於 WordPress 媒體庫
- 長度：100-300 個字符
- 使用繁體中文

請以 JSON 格式回覆：
{
  "image_type": "infographic" 或 "photo",
  "detected_text": "圖片上提取的所有文字（如果是照片則為 null）",
  "alt_text": "替代文字內容",
  "alt_text_confidence": 0.95,
  "description": "詳細描述內容",
  "description_confidence": 0.95
}

confidence 為 0-1 之間的數值，表示你對建議的信心程度。
對於信息圖，如果文字清晰可讀，confidence 應該較高（0.9+）。"""

    # System prompt for context-based fallback
    PROMPT_CONTEXT_FALLBACK = """你是一個專業的圖片 SEO 和無障礙專家。由於無法直接看到圖片，請根據文章上下文推斷圖片內容並生成：

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
  "image_type": "unknown",
  "detected_text": null,
  "alt_text": "替代文字內容",
  "alt_text_confidence": 0.6,
  "description": "詳細描述內容",
  "description_confidence": 0.6
}

由於是推斷，confidence 通常在 0.5-0.7 之間。"""

    def __init__(self):
        """Initialize the service with vision AI clients"""
        settings = get_settings()

        # Determine which provider to use
        self.use_vertex_ai = settings.USE_VERTEX_AI_FOR_VISION and VERTEX_AI_AVAILABLE
        self.provider = VisionProvider.GEMINI if self.use_vertex_ai else VisionProvider.OPENAI

        # Initialize Vertex AI (Gemini)
        self.gemini_model: GenerativeModel | None = None
        self.gemini_model_name = settings.VERTEX_AI_MODEL

        if self.use_vertex_ai:
            try:
                project_id = settings.VERTEX_AI_PROJECT or settings.GCP_PROJECT_ID if hasattr(settings, 'GCP_PROJECT_ID') else None
                if not project_id:
                    # Try to get from environment or default
                    project_id = "cmsupload-476323"

                vertexai.init(
                    project=project_id,
                    location=settings.VERTEX_AI_LOCATION
                )
                self.gemini_model = GenerativeModel(self.gemini_model_name)
                logger.info(f"Initialized Gemini model: {self.gemini_model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {e}, falling back to OpenAI")
                self.use_vertex_ai = False
                self.provider = VisionProvider.OPENAI

        # Initialize OpenAI (fallback or primary if Vertex AI not available)
        self.openai_client: AsyncOpenAI | None = None
        self.openai_model = settings.OPENAI_MODEL or "gpt-4o"

        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Log initialization status
        if self.use_vertex_ai:
            logger.info(f"Image alt generator using Gemini ({self.gemini_model_name})")
        elif self.openai_client:
            logger.info(f"Image alt generator using OpenAI ({self.openai_model})")
        else:
            logger.warning("No vision AI provider configured, image alt generation will be unavailable")

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
        # Check if any provider is available
        if not self.use_vertex_ai and not self.openai_client:
            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text="",
                suggested_alt_text_confidence=0.0,
                suggested_description="",
                suggested_description_confidence=0.0,
                image_type=ImageType.UNKNOWN,
                detected_text=None,
                generation_method=GenerationMethod.FAILED,
                model_used="none",
                tokens_used=0,
                error_message="No vision AI provider configured"
            )

        # Try vision analysis first if enabled and URL available
        if use_vision and image_url:
            image_accessible = await self._check_image_accessible(image_url)
            if image_accessible:
                logger.info(f"Image accessible, using {self.provider.value} vision for image {image_id}")

                if self.use_vertex_ai:
                    return await self._generate_with_gemini(
                        image_id=image_id,
                        image_url=image_url,
                        article_context=article_context,
                        parsed_alt_text=parsed_alt_text,
                        parsed_caption=parsed_caption,
                        parsed_description=parsed_description
                    )
                else:
                    return await self._generate_with_openai(
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

    async def _fetch_image_bytes(self, image_url: str) -> bytes | None:
        """Fetch image bytes from URL

        Args:
            image_url: URL to fetch

        Returns:
            Image bytes or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url, follow_redirects=True)
                if response.status_code == 200:
                    return response.content
                return None
        except Exception as e:
            logger.error(f"Failed to fetch image: {e}")
            return None

    async def _generate_with_gemini(
        self,
        image_id: int,
        image_url: str,
        article_context: dict,
        parsed_alt_text: str | None,
        parsed_caption: str | None,
        parsed_description: str | None
    ) -> ImageAltSuggestion:
        """Generate using Gemini 3.0 Flash vision analysis

        Args:
            image_id: Database ID
            image_url: Accessible image URL
            article_context: Article context dict
            parsed_alt_text: Existing alt text
            parsed_caption: Existing caption
            parsed_description: Existing description

        Returns:
            ImageAltSuggestion with Gemini-based suggestions
        """
        title = article_context.get("title", "")
        excerpt = article_context.get("excerpt", "")[:500] if article_context.get("excerpt") else ""
        position = article_context.get("position", 0)
        is_featured = article_context.get("is_featured", False)

        position_desc = "特色圖片（文章封面）" if is_featured else f"第 {position + 1} 張配圖"

        user_prompt = f"""請分析此圖片，判斷類型（信息圖或照片），並生成 Alt Text 和 Description。

文章上下文：
- 標題：{title}
- 摘要：{excerpt}
- 圖片位置：{position_desc}
- 現有圖說：{parsed_caption or "無"}
- 現有 Alt Text：{parsed_alt_text or "無"}

重要提示：
1. 如果圖片上有嵌入文字（信息圖），請務必提取所有文字內容
2. Alt Text 必須包含圖片上的文字信息（如果有的話）
3. 結合圖片視覺內容和文章上下文，生成最準確的建議"""

        try:
            # Fetch image bytes for Gemini
            image_bytes = await self._fetch_image_bytes(image_url)
            if not image_bytes:
                logger.warning(f"Failed to fetch image {image_id}, falling back to context")
                return await self._generate_from_context(
                    image_id=image_id,
                    article_context=article_context,
                    parsed_alt_text=parsed_alt_text,
                    parsed_caption=parsed_caption,
                    parsed_description=parsed_description
                )

            # Determine image MIME type
            mime_type = "image/jpeg"
            if image_url.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_url.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif image_url.lower().endswith(".webp"):
                mime_type = "image/webp"

            # Create Gemini content parts
            image_part = Part.from_data(image_bytes, mime_type=mime_type)

            # Generate with Gemini
            full_prompt = f"{self.PROMPT_IMAGE_ANALYSIS}\n\n{user_prompt}"

            response = await self.gemini_model.generate_content_async(
                [image_part, full_prompt],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 1000,
                    "response_mime_type": "application/json"
                }
            )

            content = response.text

            # Estimate tokens (Gemini doesn't always return usage)
            tokens_used = len(full_prompt.split()) + len(content.split()) + 500  # rough estimate for image

            # Parse JSON response
            result = self._parse_json_response(content)

            # Determine image type and generation method
            image_type_str = result.get("image_type", "unknown")
            if image_type_str == "infographic":
                image_type = ImageType.INFOGRAPHIC
                generation_method = GenerationMethod.VISION_INFOGRAPHIC
            elif image_type_str == "photo":
                image_type = ImageType.PHOTO
                generation_method = GenerationMethod.VISION_PHOTO
            else:
                image_type = ImageType.UNKNOWN
                generation_method = GenerationMethod.VISION

            detected_text = result.get("detected_text")
            if detected_text == "null" or detected_text == "":
                detected_text = None

            logger.info(
                f"Image {image_id} analyzed with Gemini: type={image_type.value}, "
                f"has_text={detected_text is not None}"
            )

            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text=result.get("alt_text", ""),
                suggested_alt_text_confidence=result.get("alt_text_confidence", 0.9),
                suggested_description=result.get("description", ""),
                suggested_description_confidence=result.get("description_confidence", 0.9),
                image_type=image_type,
                detected_text=detected_text,
                generation_method=generation_method,
                model_used=self.gemini_model_name,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Gemini vision generation failed: {e}")
            # Try OpenAI fallback if available
            if self.openai_client:
                logger.info("Falling back to OpenAI")
                return await self._generate_with_openai(
                    image_id=image_id,
                    image_url=image_url,
                    article_context=article_context,
                    parsed_alt_text=parsed_alt_text,
                    parsed_caption=parsed_caption,
                    parsed_description=parsed_description
                )
            # Fall back to context-based generation
            return await self._generate_from_context(
                image_id=image_id,
                article_context=article_context,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description
            )

    async def _generate_with_openai(
        self,
        image_id: int,
        image_url: str,
        article_context: dict,
        parsed_alt_text: str | None,
        parsed_caption: str | None,
        parsed_description: str | None
    ) -> ImageAltSuggestion:
        """Generate using GPT-4o vision analysis (fallback)

        Args:
            image_id: Database ID
            image_url: Accessible image URL
            article_context: Article context dict
            parsed_alt_text: Existing alt text
            parsed_caption: Existing caption
            parsed_description: Existing description

        Returns:
            ImageAltSuggestion with OpenAI-based suggestions
        """
        title = article_context.get("title", "")
        excerpt = article_context.get("excerpt", "")[:500] if article_context.get("excerpt") else ""
        position = article_context.get("position", 0)
        is_featured = article_context.get("is_featured", False)

        position_desc = "特色圖片（文章封面）" if is_featured else f"第 {position + 1} 張配圖"

        user_prompt = f"""請分析此圖片，判斷類型（信息圖或照片），並生成 Alt Text 和 Description。

文章上下文：
- 標題：{title}
- 摘要：{excerpt}
- 圖片位置：{position_desc}
- 現有圖說：{parsed_caption or "無"}
- 現有 Alt Text：{parsed_alt_text or "無"}

重要提示：
1. 如果圖片上有嵌入文字（信息圖），請務必提取所有文字內容
2. Alt Text 必須包含圖片上的文字信息（如果有的話）
3. 結合圖片視覺內容和文章上下文，生成最準確的建議"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": self.PROMPT_IMAGE_ANALYSIS},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"  # Use high detail for better OCR
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Parse JSON response
            result = self._parse_json_response(content)

            # Determine image type and generation method
            image_type_str = result.get("image_type", "unknown")
            if image_type_str == "infographic":
                image_type = ImageType.INFOGRAPHIC
                generation_method = GenerationMethod.VISION_INFOGRAPHIC
            elif image_type_str == "photo":
                image_type = ImageType.PHOTO
                generation_method = GenerationMethod.VISION_PHOTO
            else:
                image_type = ImageType.UNKNOWN
                generation_method = GenerationMethod.VISION

            detected_text = result.get("detected_text")
            if detected_text == "null" or detected_text == "":
                detected_text = None

            logger.info(
                f"Image {image_id} analyzed with OpenAI: type={image_type.value}, "
                f"has_text={detected_text is not None}, "
                f"tokens={tokens_used}"
            )

            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text=result.get("alt_text", ""),
                suggested_alt_text_confidence=result.get("alt_text_confidence", 0.9),
                suggested_description=result.get("description", ""),
                suggested_description_confidence=result.get("description_confidence", 0.9),
                image_type=image_type,
                detected_text=detected_text,
                generation_method=generation_method,
                model_used=self.openai_model,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"OpenAI vision generation failed: {e}")
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
        """Generate using article context only (fallback when image not accessible)

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

        user_prompt = f"""請根據以下文章上下文，推斷圖片內容並生成 Alt Text 和 Description。

文章上下文：
- 標題：{title}
- 摘要：{excerpt}
- 圖片位置：{position_desc}
- 現有圖說：{parsed_caption or "無"}
- 現有 Alt Text：{parsed_alt_text or "無"}

請基於上下文進行合理推斷。"""

        try:
            # Use OpenAI for context-based generation (text only, no vision needed)
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": self.PROMPT_CONTEXT_FALLBACK},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                model_used = self.openai_model
            elif self.gemini_model:
                # Use Gemini for text generation
                full_prompt = f"{self.PROMPT_CONTEXT_FALLBACK}\n\n{user_prompt}"
                response = await self.gemini_model.generate_content_async(
                    full_prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 500,
                        "response_mime_type": "application/json"
                    }
                )
                content = response.text
                tokens_used = len(full_prompt.split()) + len(content.split())
                model_used = self.gemini_model_name
            else:
                raise ValueError("No AI provider available")

            # Parse JSON response
            result = self._parse_json_response(content)

            return ImageAltSuggestion(
                image_id=image_id,
                parsed_alt_text=parsed_alt_text,
                parsed_caption=parsed_caption,
                parsed_description=parsed_description,
                suggested_alt_text=result.get("alt_text", ""),
                suggested_alt_text_confidence=result.get("alt_text_confidence", 0.6),
                suggested_description=result.get("description", ""),
                suggested_description_confidence=result.get("description_confidence", 0.6),
                image_type=ImageType.UNKNOWN,
                detected_text=None,
                generation_method=GenerationMethod.CONTEXT,
                model_used=model_used,
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
                image_type=ImageType.UNKNOWN,
                detected_text=None,
                generation_method=GenerationMethod.FAILED,
                model_used="none",
                tokens_used=0,
                error_message=str(e)
            )

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON response from AI, handling potential formatting issues

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
