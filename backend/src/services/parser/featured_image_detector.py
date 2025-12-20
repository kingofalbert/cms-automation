"""Featured Image Detector Service

Detects whether an image should be marked as a featured (置頂) image
based on multiple detection rules.

Phase 13: Enhanced Image Review

Detection Rules:
1. Caption contains featured keywords (置頂, 封面, etc.)
2. Image appears before body content starts (position=0 with no preceding paragraphs)
3. Explicit manual marking

Author: CMS Automation Team
Date: 2025-12-20
"""

import re
from dataclasses import dataclass
from enum import Enum

from src.config.logging import get_logger

logger = get_logger(__name__)


class DetectionMethod(str, Enum):
    """Method used to detect featured image status."""

    CAPTION_KEYWORD = "caption_keyword"  # Caption contains featured keywords
    POSITION_BEFORE_BODY = "position_before_body"  # Image before first paragraph
    MANUAL = "manual"  # Manually set by user
    POSITION_LEGACY = "position_legacy"  # Legacy: position=0 (migration)
    NONE = "none"  # Not a featured image


class ImageType(str, Enum):
    """Type classification for article images."""

    FEATURED = "featured"  # Featured/cover image (置頂圖片)
    CONTENT = "content"  # In-body content image (正文圖片)
    INLINE = "inline"  # Inline/decorative image (行內圖片)


@dataclass
class FeaturedDetectionResult:
    """Result of featured image detection."""

    is_featured: bool
    image_type: ImageType
    detection_method: DetectionMethod
    confidence: float  # 0.0 - 1.0
    reason: str  # Human-readable explanation

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "is_featured": self.is_featured,
            "image_type": self.image_type.value,
            "detection_method": self.detection_method.value,
            "confidence": self.confidence,
            "reason": self.reason,
        }


class FeaturedImageDetector:
    """Service for detecting featured (置頂) images.

    Analyzes image caption, position, and context to determine
    if an image should be marked as the article's featured image.

    Example usage:
        detector = FeaturedImageDetector()
        result = detector.detect(
            caption="置頂圖：AI 醫療示意圖",
            position=0,
            has_content_before=False
        )
        if result.is_featured:
            print(f"Featured image detected: {result.reason}")
    """

    # Keywords that indicate a featured image
    FEATURED_KEYWORDS_PRIMARY = [
        "置頂",
        "封面",
        "首圖",
        "頭圖",
        "特色圖片",
        "主圖",
    ]

    FEATURED_KEYWORDS_SECONDARY = [
        "featured",
        "cover",
        "hero",
        "main image",
        "banner",
    ]

    # Patterns that strongly suggest featured status
    FEATURED_PATTERNS = [
        r"^\s*[\(（【\[]?\s*(置頂|封面|首圖)",  # Starts with featured keyword
        r"(置頂|封面)[圖图]",  # 置頂圖, 封面圖
        r"圖[說说]?\s*[:：]?\s*(置頂|封面)",  # 圖說: 置頂
    ]

    def __init__(self):
        """Initialize the detector."""
        # Compile regex patterns for efficiency
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.FEATURED_PATTERNS
        ]

    def detect(
        self,
        caption: str | None = None,
        position: int = 0,
        has_content_before: bool = False,
        html_context: str | None = None,
        force_featured: bool = False,
    ) -> FeaturedDetectionResult:
        """Detect if an image should be marked as featured.

        Args:
            caption: Image caption text (圖說)
            position: Image position in document (0-based paragraph index)
            has_content_before: Whether there is body content before this image
            html_context: Optional HTML context around the image
            force_featured: Force mark as featured (manual override)

        Returns:
            FeaturedDetectionResult with detection details
        """
        # Rule 0: Manual override
        if force_featured:
            return FeaturedDetectionResult(
                is_featured=True,
                image_type=ImageType.FEATURED,
                detection_method=DetectionMethod.MANUAL,
                confidence=1.0,
                reason="手動設置為置頂圖片",
            )

        # Rule 1: Check caption for featured keywords
        if caption:
            caption_result = self._check_caption_keywords(caption)
            if caption_result:
                return caption_result

        # Rule 2: Check position (first image before body content)
        if position == 0 and not has_content_before:
            return FeaturedDetectionResult(
                is_featured=True,
                image_type=ImageType.FEATURED,
                detection_method=DetectionMethod.POSITION_BEFORE_BODY,
                confidence=0.85,
                reason="圖片位於正文開始之前（第一張圖片）",
            )

        # Rule 3: Check HTML context for additional clues (if provided)
        if html_context:
            context_result = self._check_html_context(html_context)
            if context_result and context_result.is_featured:
                return context_result

        # Default: Not a featured image
        return FeaturedDetectionResult(
            is_featured=False,
            image_type=ImageType.CONTENT,
            detection_method=DetectionMethod.NONE,
            confidence=1.0,
            reason="正文內容圖片",
        )

    def _check_caption_keywords(self, caption: str) -> FeaturedDetectionResult | None:
        """Check if caption contains featured keywords.

        Args:
            caption: Image caption text

        Returns:
            FeaturedDetectionResult if featured keyword found, None otherwise
        """
        caption_lower = caption.lower()

        # Check compiled patterns first (highest confidence)
        for pattern in self._compiled_patterns:
            if pattern.search(caption):
                matched = pattern.search(caption).group(0)
                return FeaturedDetectionResult(
                    is_featured=True,
                    image_type=ImageType.FEATURED,
                    detection_method=DetectionMethod.CAPTION_KEYWORD,
                    confidence=0.98,
                    reason=f"Caption 包含置頂標記：「{matched}」",
                )

        # Check primary keywords (high confidence)
        for keyword in self.FEATURED_KEYWORDS_PRIMARY:
            if keyword.lower() in caption_lower:
                return FeaturedDetectionResult(
                    is_featured=True,
                    image_type=ImageType.FEATURED,
                    detection_method=DetectionMethod.CAPTION_KEYWORD,
                    confidence=0.95,
                    reason=f"Caption 包含關鍵字「{keyword}」",
                )

        # Check secondary keywords (medium confidence)
        for keyword in self.FEATURED_KEYWORDS_SECONDARY:
            if keyword.lower() in caption_lower:
                return FeaturedDetectionResult(
                    is_featured=True,
                    image_type=ImageType.FEATURED,
                    detection_method=DetectionMethod.CAPTION_KEYWORD,
                    confidence=0.80,
                    reason=f"Caption 包含關鍵字「{keyword}」",
                )

        return None

    def _check_html_context(self, html_context: str) -> FeaturedDetectionResult | None:
        """Check HTML context for featured image indicators.

        Args:
            html_context: HTML snippet around the image

        Returns:
            FeaturedDetectionResult if featured indicators found, None otherwise
        """
        # Check for common featured image class names or IDs
        featured_class_patterns = [
            r'class\s*=\s*["\'][^"\']*(?:featured|cover|hero|banner)[^"\']*["\']',
            r'id\s*=\s*["\'][^"\']*(?:featured|cover|hero)[^"\']*["\']',
            r'data-featured\s*=\s*["\']true["\']',
        ]

        for pattern in featured_class_patterns:
            if re.search(pattern, html_context, re.IGNORECASE):
                return FeaturedDetectionResult(
                    is_featured=True,
                    image_type=ImageType.FEATURED,
                    detection_method=DetectionMethod.CAPTION_KEYWORD,
                    confidence=0.75,
                    reason="HTML 標記包含置頂圖片指示",
                )

        return None

    def detect_batch(
        self,
        images: list[dict],
        first_paragraph_position: int | None = None,
    ) -> list[FeaturedDetectionResult]:
        """Detect featured status for a batch of images.

        Ensures only one image is marked as featured (the first one found).

        Args:
            images: List of image dicts with 'caption' and 'position' keys
            first_paragraph_position: Position of first paragraph (for context)

        Returns:
            List of FeaturedDetectionResult, one per image
        """
        results = []
        featured_found = False

        for img in images:
            caption = img.get("caption")
            position = img.get("position", 0)

            # Determine if there's content before this image
            has_content_before = (
                first_paragraph_position is not None
                and position > first_paragraph_position
            )

            result = self.detect(
                caption=caption,
                position=position,
                has_content_before=has_content_before,
            )

            # Only first featured image counts
            if result.is_featured:
                if featured_found:
                    # Demote subsequent featured images to content
                    result = FeaturedDetectionResult(
                        is_featured=False,
                        image_type=ImageType.CONTENT,
                        detection_method=DetectionMethod.NONE,
                        confidence=1.0,
                        reason="正文內容圖片（已有其他置頂圖片）",
                    )
                else:
                    featured_found = True

            results.append(result)

        return results


# Singleton instance
_detector_instance: FeaturedImageDetector | None = None


def get_featured_image_detector() -> FeaturedImageDetector:
    """Get singleton instance of FeaturedImageDetector."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FeaturedImageDetector()
    return _detector_instance
