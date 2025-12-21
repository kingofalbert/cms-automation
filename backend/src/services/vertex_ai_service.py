"""Vertex AI Service for Gemini Models

Provides image analysis, image generation, and text generation capabilities
using Google's Gemini models via Vertex AI.

Capabilities:
- Image Analysis: Gemini 2.5 Flash (multimodal) - can replace OpenAI GPT-4o vision
- Image Generation: Gemini 2.5 Flash Image (nano banana) - generate images from prompts
- Text Generation: Gemini models for general text tasks
"""

import base64
import json
import re
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)

# Lazy import to avoid import errors when not using Vertex AI
vertexai = None
GenerativeModel = None
Image = None
Part = None


def _ensure_vertex_ai_imported():
    """Lazily import Vertex AI SDK"""
    global vertexai, GenerativeModel, Image, Part
    if vertexai is None:
        import vertexai as vai
        from vertexai.generative_models import GenerativeModel as GM
        from vertexai.generative_models import Image as Img
        from vertexai.generative_models import Part as Pt

        vertexai = vai
        GenerativeModel = GM
        Image = Img
        Part = Pt


class VertexAITaskType(str, Enum):
    """Type of Vertex AI task"""
    IMAGE_ANALYSIS = "image_analysis"
    IMAGE_GENERATION = "image_generation"
    TEXT_GENERATION = "text_generation"


@dataclass
class VertexAIResponse:
    """Response from Vertex AI operations"""
    success: bool
    content: str | bytes | None
    content_type: str  # "text", "image", "json"
    model_used: str
    tokens_used: int
    error_message: str | None = None
    metadata: dict | None = None


class VertexAIService:
    """Service for interacting with Vertex AI Gemini models

    Provides:
    - Image analysis (vision) using Gemini 2.5 Flash
    - Image generation using Gemini 2.5 Flash Image
    - Text generation for general tasks
    """

    def __init__(self):
        """Initialize the Vertex AI service"""
        settings = get_settings()
        self.project = settings.VERTEX_AI_PROJECT or "cmsupload-476323"
        self.location = settings.VERTEX_AI_LOCATION
        self.vision_model_name = settings.VERTEX_AI_MODEL
        self.image_gen_model_name = settings.VERTEX_AI_IMAGE_MODEL
        self._initialized = False
        self._vision_model = None
        self._image_gen_model = None

    def _initialize(self) -> bool:
        """Initialize Vertex AI SDK

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        try:
            _ensure_vertex_ai_imported()
            vertexai.init(project=self.project, location=self.location)
            self._initialized = True
            logger.info(f"Vertex AI initialized: project={self.project}, location={self.location}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            return False

    def _get_vision_model(self):
        """Get or create vision model instance"""
        if not self._initialize():
            return None
        if self._vision_model is None:
            self._vision_model = GenerativeModel(self.vision_model_name)
        return self._vision_model

    def _get_image_gen_model(self):
        """Get or create image generation model instance"""
        if not self._initialize():
            return None
        if self._image_gen_model is None:
            self._image_gen_model = GenerativeModel(self.image_gen_model_name)
        return self._image_gen_model

    async def analyze_image(
        self,
        image_source: str | bytes | Path,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> VertexAIResponse:
        """Analyze an image using Gemini vision capabilities

        Args:
            image_source: URL, file path, or raw bytes of the image
            prompt: Analysis prompt
            system_instruction: Optional system instruction
            temperature: Generation temperature (0-1)
            max_tokens: Maximum output tokens

        Returns:
            VertexAIResponse with analysis result
        """
        model = self._get_vision_model()
        if model is None:
            return VertexAIResponse(
                success=False,
                content=None,
                content_type="text",
                model_used=self.vision_model_name,
                tokens_used=0,
                error_message="Vertex AI not initialized"
            )

        try:
            # Prepare image part
            image_part = await self._prepare_image_part(image_source)
            if image_part is None:
                return VertexAIResponse(
                    success=False,
                    content=None,
                    content_type="text",
                    model_used=self.vision_model_name,
                    tokens_used=0,
                    error_message="Failed to load image"
                )

            # Build content parts
            contents = [image_part, prompt]

            # Generate response
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            if system_instruction:
                model = GenerativeModel(
                    self.vision_model_name,
                    system_instruction=system_instruction
                )

            response = model.generate_content(
                contents,
                generation_config=generation_config
            )

            # Extract usage stats
            tokens_used = 0
            if hasattr(response, 'usage_metadata'):
                tokens_used = (
                    getattr(response.usage_metadata, 'total_token_count', 0) or
                    getattr(response.usage_metadata, 'prompt_token_count', 0) +
                    getattr(response.usage_metadata, 'candidates_token_count', 0)
                )

            return VertexAIResponse(
                success=True,
                content=response.text,
                content_type="text",
                model_used=self.vision_model_name,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return VertexAIResponse(
                success=False,
                content=None,
                content_type="text",
                model_used=self.vision_model_name,
                tokens_used=0,
                error_message=str(e)
            )

    async def analyze_image_for_alt_text(
        self,
        image_source: str | bytes | Path,
        article_context: dict,
        parsed_alt_text: str | None = None,
        parsed_caption: str | None = None,
    ) -> VertexAIResponse:
        """Analyze image and generate SEO-optimized alt text and description

        This method is designed to be a drop-in replacement for OpenAI vision.

        Args:
            image_source: Image URL, path, or bytes
            article_context: Dict with title, excerpt, position, is_featured
            parsed_alt_text: Existing alt text if any
            parsed_caption: Existing caption if any

        Returns:
            VertexAIResponse with JSON content containing alt_text and description
        """
        title = article_context.get("title", "")
        excerpt = article_context.get("excerpt", "")[:500] if article_context.get("excerpt") else ""
        position = article_context.get("position", 0)
        is_featured = article_context.get("is_featured", False)
        position_desc = "特色圖片（文章封面）" if is_featured else f"第 {position + 1} 張配圖"

        system_instruction = """你是一個專業的圖片 SEO 和無障礙專家。請分析圖片並生成：

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

        prompt = f"""請分析此圖片並生成 Alt Text 和 Description。

文章上下文：
- 標題：{title}
- 摘要：{excerpt}
- 圖片位置：{position_desc}
- 現有圖說：{parsed_caption or "無"}
- 現有 Alt Text：{parsed_alt_text or "無"}

請結合圖片視覺內容和文章上下文，生成最準確的建議。請直接輸出 JSON，不要使用 markdown 代碼塊。"""

        response = await self.analyze_image(
            image_source=image_source,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.3,
            max_tokens=500
        )

        if response.success and response.content:
            # Try to parse as JSON
            try:
                parsed = self._parse_json_response(response.content)
                response.content = json.dumps(parsed, ensure_ascii=False)
                response.content_type = "json"
            except Exception:
                pass

        return response

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        aspect_ratio: str = "1:1",
        style: str | None = None,
    ) -> VertexAIResponse:
        """Generate an image using Gemini 2.5 Flash Image (nano banana)

        Args:
            prompt: Image generation prompt
            negative_prompt: What to avoid in the image
            aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)
            style: Optional style guidance

        Returns:
            VertexAIResponse with generated image bytes
        """
        model = self._get_image_gen_model()
        if model is None:
            return VertexAIResponse(
                success=False,
                content=None,
                content_type="image",
                model_used=self.image_gen_model_name,
                tokens_used=0,
                error_message="Vertex AI not initialized"
            )

        try:
            # Build the prompt
            full_prompt = prompt
            if style:
                full_prompt = f"{style} style: {prompt}"
            if negative_prompt:
                full_prompt += f"\n\nAvoid: {negative_prompt}"

            # Generate image
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "response_modalities": ["IMAGE", "TEXT"],
                }
            )

            # Extract image from response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        mime_type = part.inline_data.mime_type

                        return VertexAIResponse(
                            success=True,
                            content=image_data,
                            content_type="image",
                            model_used=self.image_gen_model_name,
                            tokens_used=1290,  # Standard image token count
                            metadata={"mime_type": mime_type, "aspect_ratio": aspect_ratio}
                        )

            return VertexAIResponse(
                success=False,
                content=None,
                content_type="image",
                model_used=self.image_gen_model_name,
                tokens_used=0,
                error_message="No image generated in response"
            )

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return VertexAIResponse(
                success=False,
                content=None,
                content_type="image",
                model_used=self.image_gen_model_name,
                tokens_used=0,
                error_message=str(e)
            )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> VertexAIResponse:
        """Generate text using Gemini

        Args:
            prompt: Generation prompt
            system_instruction: Optional system instruction
            temperature: Generation temperature (0-1)
            max_tokens: Maximum output tokens

        Returns:
            VertexAIResponse with generated text
        """
        model = self._get_vision_model()  # Use vision model for text too
        if model is None:
            return VertexAIResponse(
                success=False,
                content=None,
                content_type="text",
                model_used=self.vision_model_name,
                tokens_used=0,
                error_message="Vertex AI not initialized"
            )

        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            if system_instruction:
                model = GenerativeModel(
                    self.vision_model_name,
                    system_instruction=system_instruction
                )

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            tokens_used = 0
            if hasattr(response, 'usage_metadata'):
                tokens_used = getattr(response.usage_metadata, 'total_token_count', 0)

            return VertexAIResponse(
                success=True,
                content=response.text,
                content_type="text",
                model_used=self.vision_model_name,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return VertexAIResponse(
                success=False,
                content=None,
                content_type="text",
                model_used=self.vision_model_name,
                tokens_used=0,
                error_message=str(e)
            )

    async def _prepare_image_part(self, image_source: str | bytes | Path):
        """Prepare image for Vertex AI input

        Args:
            image_source: URL, file path, or raw bytes

        Returns:
            Image part for Vertex AI or None if failed
        """
        try:
            _ensure_vertex_ai_imported()

            if isinstance(image_source, bytes):
                # Raw bytes
                return Part.from_data(image_source, mime_type="image/jpeg")

            if isinstance(image_source, Path):
                # File path
                return Image.load_from_file(str(image_source))

            if isinstance(image_source, str):
                if image_source.startswith(('http://', 'https://')):
                    # URL - download first
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(image_source, follow_redirects=True)
                        if response.status_code == 200:
                            content_type = response.headers.get("content-type", "image/jpeg")
                            return Part.from_data(response.content, mime_type=content_type)
                        else:
                            logger.warning(f"Failed to download image: {response.status_code}")
                            return None
                else:
                    # Assume file path
                    return Image.load_from_file(image_source)

            return None

        except Exception as e:
            logger.error(f"Failed to prepare image: {e}")
            return None

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON response, handling potential formatting issues

        Args:
            content: Raw response content

        Returns:
            Parsed dict
        """
        # Try direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse JSON response: {content[:200]}")
        return {}


# Singleton instance
_service_instance: VertexAIService | None = None


def get_vertex_ai_service() -> VertexAIService:
    """Get singleton instance of VertexAIService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = VertexAIService()
    return _service_instance
