"""Unit tests for FeaturedImageDetector service.

Phase 13: Enhanced Image Review - Featured Image Detection

Tests cover:
1. Caption keyword detection (置頂, 封面, etc.)
2. Position-based detection (before body content)
3. Manual override
4. Batch detection with single featured constraint
5. Edge cases and confidence levels
"""

import pytest

from src.services.parser.featured_image_detector import (
    DetectionMethod,
    FeaturedDetectionResult,
    FeaturedImageDetector,
    ImageType,
    get_featured_image_detector,
)


class TestFeaturedImageDetector:
    """Test cases for FeaturedImageDetector."""

    @pytest.fixture
    def detector(self) -> FeaturedImageDetector:
        """Create a fresh detector instance for each test."""
        return FeaturedImageDetector()

    # ========================================================================
    # Caption Keyword Detection Tests
    # ========================================================================

    def test_detect_caption_keyword_primary_置頂(self, detector: FeaturedImageDetector):
        """Test detection with primary keyword 置頂."""
        result = detector.detect(caption="置頂圖：AI 醫療示意圖", position=0)

        assert result.is_featured is True
        assert result.image_type == ImageType.FEATURED
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD
        assert result.confidence >= 0.95
        assert "置頂" in result.reason

    def test_detect_caption_keyword_primary_封面(self, detector: FeaturedImageDetector):
        """Test detection with primary keyword 封面."""
        result = detector.detect(caption="封面圖片", position=0)

        assert result.is_featured is True
        assert result.image_type == ImageType.FEATURED
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD
        assert result.confidence >= 0.95

    def test_detect_caption_keyword_primary_首圖(self, detector: FeaturedImageDetector):
        """Test detection with primary keyword 首圖."""
        result = detector.detect(caption="【首圖】新冠疫情", position=0)

        assert result.is_featured is True
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD

    def test_detect_caption_keyword_primary_頭圖(self, detector: FeaturedImageDetector):
        """Test detection with primary keyword 頭圖."""
        result = detector.detect(caption="頭圖展示", position=2)

        assert result.is_featured is True
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD

    def test_detect_caption_keyword_primary_特色圖片(self, detector: FeaturedImageDetector):
        """Test detection with primary keyword 特色圖片."""
        result = detector.detect(caption="這是特色圖片", position=0)

        assert result.is_featured is True
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD

    def test_detect_caption_keyword_primary_主圖(self, detector: FeaturedImageDetector):
        """Test detection with primary keyword 主圖."""
        result = detector.detect(caption="主圖說明", position=0)

        assert result.is_featured is True
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD

    def test_detect_caption_keyword_secondary_featured(self, detector: FeaturedImageDetector):
        """Test detection with secondary keyword 'featured'."""
        result = detector.detect(caption="Featured image for article", position=0)

        assert result.is_featured is True
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD
        assert result.confidence >= 0.80

    def test_detect_caption_keyword_secondary_cover(self, detector: FeaturedImageDetector):
        """Test detection with secondary keyword 'cover'."""
        result = detector.detect(caption="Cover photo", position=0)

        assert result.is_featured is True
        assert result.confidence >= 0.80

    def test_detect_caption_keyword_secondary_hero(self, detector: FeaturedImageDetector):
        """Test detection with secondary keyword 'hero'."""
        result = detector.detect(caption="Hero banner image", position=0)

        assert result.is_featured is True

    def test_detect_caption_pattern_圖說置頂(self, detector: FeaturedImageDetector):
        """Test detection with pattern 圖說：置頂."""
        result = detector.detect(caption="圖說：置頂健康新知", position=0)

        assert result.is_featured is True
        assert result.confidence >= 0.98  # Pattern matching has highest confidence

    def test_detect_caption_pattern_置頂圖(self, detector: FeaturedImageDetector):
        """Test detection with pattern 置頂圖."""
        result = detector.detect(caption="置頂圖 - 醫療保健", position=0)

        assert result.is_featured is True
        assert result.confidence >= 0.98

    # ========================================================================
    # Position-Based Detection Tests
    # ========================================================================

    def test_detect_position_before_body(self, detector: FeaturedImageDetector):
        """Test detection based on position before body content."""
        result = detector.detect(
            caption="Regular image caption",
            position=0,
            has_content_before=False
        )

        assert result.is_featured is True
        assert result.image_type == ImageType.FEATURED
        assert result.detection_method == DetectionMethod.POSITION_BEFORE_BODY
        assert result.confidence == 0.85

    def test_detect_position_after_body_content(self, detector: FeaturedImageDetector):
        """Test that images after body content are not featured."""
        result = detector.detect(
            caption="Regular image caption",
            position=2,
            has_content_before=True
        )

        assert result.is_featured is False
        assert result.image_type == ImageType.CONTENT
        assert result.detection_method == DetectionMethod.NONE

    def test_detect_position_0_with_content_before(self, detector: FeaturedImageDetector):
        """Test that position 0 with content before is not featured."""
        result = detector.detect(
            caption="Regular image",
            position=0,
            has_content_before=True
        )

        # Position 0 with content before should NOT be featured by position
        # Only by caption keywords
        assert result.is_featured is False
        assert result.image_type == ImageType.CONTENT

    # ========================================================================
    # Manual Override Tests
    # ========================================================================

    def test_detect_manual_override(self, detector: FeaturedImageDetector):
        """Test manual override with force_featured."""
        result = detector.detect(
            caption="Random caption",
            position=5,
            has_content_before=True,
            force_featured=True
        )

        assert result.is_featured is True
        assert result.image_type == ImageType.FEATURED
        assert result.detection_method == DetectionMethod.MANUAL
        assert result.confidence == 1.0
        assert "手動" in result.reason

    def test_detect_manual_override_takes_precedence(self, detector: FeaturedImageDetector):
        """Test that manual override takes precedence over all other rules."""
        result = detector.detect(
            caption="置頂圖：This would be detected by caption",
            position=0,
            has_content_before=False,
            force_featured=True
        )

        # Manual override should be the detection method, not caption
        assert result.detection_method == DetectionMethod.MANUAL

    # ========================================================================
    # HTML Context Detection Tests
    # ========================================================================

    def test_detect_html_context_featured_class(self, detector: FeaturedImageDetector):
        """Test detection via HTML class containing 'featured'."""
        result = detector.detect(
            caption="Image caption",
            position=2,
            has_content_before=True,
            html_context='<div class="featured-image"><img src="test.jpg" /></div>'
        )

        assert result.is_featured is True
        assert result.confidence == 0.75

    def test_detect_html_context_cover_id(self, detector: FeaturedImageDetector):
        """Test detection via HTML id containing 'cover'."""
        result = detector.detect(
            caption="Image caption",
            position=2,
            has_content_before=True,
            html_context='<img id="cover-image" src="test.jpg" />'
        )

        assert result.is_featured is True

    def test_detect_html_context_data_featured(self, detector: FeaturedImageDetector):
        """Test detection via data-featured attribute."""
        result = detector.detect(
            caption="Image caption",
            position=2,
            has_content_before=True,
            html_context='<img data-featured="true" src="test.jpg" />'
        )

        assert result.is_featured is True

    # ========================================================================
    # Non-Featured Image Tests
    # ========================================================================

    def test_detect_content_image(self, detector: FeaturedImageDetector):
        """Test that regular images are classified as content."""
        result = detector.detect(
            caption="普通圖片說明",
            position=3,
            has_content_before=True
        )

        assert result.is_featured is False
        assert result.image_type == ImageType.CONTENT
        assert result.detection_method == DetectionMethod.NONE
        assert result.confidence == 1.0
        assert "正文" in result.reason

    def test_detect_no_caption(self, detector: FeaturedImageDetector):
        """Test detection with no caption."""
        result = detector.detect(
            caption=None,
            position=3,
            has_content_before=True
        )

        assert result.is_featured is False
        assert result.image_type == ImageType.CONTENT

    def test_detect_empty_caption(self, detector: FeaturedImageDetector):
        """Test detection with empty caption."""
        result = detector.detect(
            caption="",
            position=3,
            has_content_before=True
        )

        assert result.is_featured is False

    # ========================================================================
    # Batch Detection Tests
    # ========================================================================

    def test_detect_batch_single_featured(self, detector: FeaturedImageDetector):
        """Test that only one image is marked as featured in batch."""
        images = [
            {"position": 0, "caption": "置頂圖"},
            {"position": 1, "caption": "封面圖"},  # Also has keyword but should not be featured
            {"position": 2, "caption": "普通圖片"},
        ]

        results = detector.detect_batch(images, first_paragraph_position=1)

        # Only first should be featured
        featured_count = sum(1 for r in results if r.is_featured)
        assert featured_count == 1
        assert results[0].is_featured is True
        assert results[1].is_featured is False  # Second one demoted
        assert results[2].is_featured is False

    def test_detect_batch_featured_by_keyword_not_position(self, detector: FeaturedImageDetector):
        """Test batch where featured is determined by keyword at non-zero position."""
        images = [
            {"position": 0, "caption": "普通圖片"},  # Not featured by keyword
            {"position": 1, "caption": "置頂圖片"},  # Has keyword
            {"position": 2, "caption": "另一張普通圖片"},
        ]

        results = detector.detect_batch(images, first_paragraph_position=0)

        # First image should be featured by position (before first paragraph)
        assert results[0].is_featured is True
        assert results[1].is_featured is False  # Demoted because first already featured
        assert results[2].is_featured is False

    def test_detect_batch_no_featured(self, detector: FeaturedImageDetector):
        """Test batch where no image qualifies as featured."""
        images = [
            {"position": 2, "caption": "普通圖片1"},
            {"position": 3, "caption": "普通圖片2"},
            {"position": 4, "caption": "普通圖片3"},
        ]

        results = detector.detect_batch(images, first_paragraph_position=1)

        # None should be featured
        featured_count = sum(1 for r in results if r.is_featured)
        assert featured_count == 0

    def test_detect_batch_empty_list(self, detector: FeaturedImageDetector):
        """Test batch with empty list."""
        results = detector.detect_batch([], first_paragraph_position=1)

        assert results == []

    def test_detect_batch_uses_first_paragraph_position(self, detector: FeaturedImageDetector):
        """Test that first_paragraph_position affects has_content_before."""
        images = [
            {"position": 0, "caption": "Image at 0"},
            {"position": 1, "caption": "Image at 1"},
            {"position": 2, "caption": "Image at 2"},
        ]

        # First paragraph at position 2 means images at 0 and 1 are before body
        results = detector.detect_batch(images, first_paragraph_position=2)

        # First image should be featured (before body)
        assert results[0].is_featured is True
        assert results[0].detection_method == DetectionMethod.POSITION_BEFORE_BODY

    # ========================================================================
    # Serialization Tests
    # ========================================================================

    def test_result_to_dict(self, detector: FeaturedImageDetector):
        """Test FeaturedDetectionResult.to_dict() method."""
        result = detector.detect(caption="置頂圖", position=0)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["is_featured"] is True
        assert result_dict["image_type"] == "featured"
        assert result_dict["detection_method"] == "caption_keyword"
        assert 0 <= result_dict["confidence"] <= 1
        assert isinstance(result_dict["reason"], str)

    # ========================================================================
    # Singleton Instance Tests
    # ========================================================================

    def test_get_featured_image_detector_singleton(self):
        """Test that get_featured_image_detector returns singleton."""
        detector1 = get_featured_image_detector()
        detector2 = get_featured_image_detector()

        assert detector1 is detector2

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_detect_case_insensitive_secondary_keywords(self, detector: FeaturedImageDetector):
        """Test that secondary keywords are case insensitive."""
        result1 = detector.detect(caption="FEATURED IMAGE", position=0)
        result2 = detector.detect(caption="Featured Image", position=0)
        result3 = detector.detect(caption="featured image", position=0)

        assert result1.is_featured is True
        assert result2.is_featured is True
        assert result3.is_featured is True

    def test_detect_keyword_partial_match(self, detector: FeaturedImageDetector):
        """Test that keyword partial matches work."""
        # 置頂 in middle of caption
        result = detector.detect(caption="這是一張置頂的圖片說明", position=0)
        assert result.is_featured is True

    def test_detect_priority_caption_over_position(self, detector: FeaturedImageDetector):
        """Test that caption keyword detection takes priority over position."""
        # Caption keyword should be used even at position 0
        result = detector.detect(
            caption="置頂圖",
            position=0,
            has_content_before=False
        )

        # Should detect by caption, not position
        assert result.detection_method == DetectionMethod.CAPTION_KEYWORD
        assert result.confidence >= 0.95  # Caption detection has higher confidence

    def test_detect_confidence_levels(self, detector: FeaturedImageDetector):
        """Test different confidence levels for different detection methods."""
        # Pattern match - highest confidence
        pattern_result = detector.detect(caption="置頂圖：說明", position=0)
        assert pattern_result.confidence >= 0.98

        # Primary keyword - high confidence
        primary_result = detector.detect(caption="這是主圖", position=2, has_content_before=True)
        assert primary_result.confidence >= 0.95

        # Secondary keyword - medium confidence
        secondary_result = detector.detect(caption="Banner image", position=2, has_content_before=True)
        assert secondary_result.confidence >= 0.80

        # Position detection - lower confidence
        position_result = detector.detect(caption="Regular image", position=0, has_content_before=False)
        assert position_result.confidence == 0.85


class TestImageType:
    """Test ImageType enum."""

    def test_image_type_values(self):
        """Test ImageType enum values."""
        assert ImageType.FEATURED.value == "featured"
        assert ImageType.CONTENT.value == "content"
        assert ImageType.INLINE.value == "inline"


class TestDetectionMethod:
    """Test DetectionMethod enum."""

    def test_detection_method_values(self):
        """Test DetectionMethod enum values."""
        assert DetectionMethod.CAPTION_KEYWORD.value == "caption_keyword"
        assert DetectionMethod.POSITION_BEFORE_BODY.value == "position_before_body"
        assert DetectionMethod.MANUAL.value == "manual"
        assert DetectionMethod.POSITION_LEGACY.value == "position_legacy"
        assert DetectionMethod.NONE.value == "none"
