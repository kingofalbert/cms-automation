"""Unit tests for ImageProcessorService (Phase 7)."""

import io
from pathlib import Path

import pytest
from PIL import Image

from src.services.parser.image_processor import ImageProcessorService


class TestImageProcessorService:
    """Test suite for ImageProcessorService."""

    @pytest.fixture
    def processor(self):
        """Create ImageProcessorService instance."""
        return ImageProcessorService()

    @pytest.fixture
    def sample_image_bytes(self):
        """Create a sample image in bytes."""
        # Create a simple test image
        img = Image.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    @pytest.fixture
    def sample_png_bytes(self):
        """Create a sample PNG with transparency."""
        img = Image.new("RGBA", (1920, 1080), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_process_image_bytes_basic(self, processor, sample_image_bytes):
        """Test basic image processing from bytes."""
        metadata = processor.process_image_bytes(sample_image_bytes)

        # Check schema version
        assert metadata["_schema_version"] == "1.0"

        # Check technical specs
        tech_specs = metadata["image_technical_specs"]
        assert tech_specs["width"] == 800
        assert tech_specs["height"] == 600
        assert tech_specs["format"] == "JPEG"
        assert tech_specs["mime_type"] == "image/jpeg"
        assert tech_specs["color_mode"] == "RGB"
        assert tech_specs["has_transparency"] is False
        assert tech_specs["file_size_bytes"] > 0

    def test_process_image_bytes_aspect_ratio(self, processor, sample_image_bytes):
        """Test aspect ratio calculation."""
        metadata = processor.process_image_bytes(sample_image_bytes)

        tech_specs = metadata["image_technical_specs"]
        # 800:600 = 4:3
        assert tech_specs["aspect_ratio"] == "4:3"

    def test_process_image_bytes_png_with_transparency(self, processor, sample_png_bytes):
        """Test PNG with transparency."""
        metadata = processor.process_image_bytes(sample_png_bytes)

        tech_specs = metadata["image_technical_specs"]
        assert tech_specs["format"] == "PNG"
        assert tech_specs["mime_type"] == "image/png"
        assert tech_specs["has_transparency"] is True
        assert tech_specs["color_mode"] == "RGBA"
        assert tech_specs["aspect_ratio"] == "16:9"  # 1920:1080

    def test_process_image_bytes_with_source_url(self, processor, sample_image_bytes):
        """Test metadata includes source URL when provided."""
        metadata = processor.process_image_bytes(
            sample_image_bytes,
            source_url="https://example.com/image.jpg",
        )

        assert "source_info" in metadata
        assert metadata["source_info"]["original_url"] == "https://example.com/image.jpg"

    def test_process_image_bytes_with_file_path(self, processor, sample_image_bytes):
        """Test metadata includes filename when provided."""
        metadata = processor.process_image_bytes(
            sample_image_bytes,
            file_path="/tmp/test_image.jpg",
        )

        assert "source_info" in metadata
        assert metadata["source_info"]["original_filename"] == "test_image.jpg"

    def test_processing_info_included(self, processor, sample_image_bytes):
        """Test processing info is included in metadata."""
        metadata = processor.process_image_bytes(sample_image_bytes)

        assert "processing_info" in metadata
        proc_info = metadata["processing_info"]
        assert proc_info["download_status"] == "success"
        assert proc_info["processor_version"] == "1.0.0"
        assert "download_timestamp" in proc_info
        assert proc_info["download_timestamp"].endswith("Z")  # ISO format with Z

    def test_validation_warnings_for_large_image(self, processor):
        """Test validation warnings for large images."""
        # Create a large image (5000x5000px)
        img = Image.new("RGB", (5000, 5000), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        large_image_bytes = buffer.getvalue()

        metadata = processor.process_image_bytes(large_image_bytes)

        # Should have validation warnings
        assert "validation" in metadata
        validation = metadata["validation"]
        assert validation["is_valid"] is True  # Still valid, just has warnings
        assert len(validation["validation_warnings"]) > 0
        assert any("large" in w.lower() for w in validation["validation_warnings"])

    def test_validation_warnings_for_small_image(self, processor):
        """Test validation warnings for small images."""
        # Create a very small image (50x50px)
        img = Image.new("RGB", (50, 50), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        small_image_bytes = buffer.getvalue()

        metadata = processor.process_image_bytes(small_image_bytes)

        # Should have validation warnings
        assert "validation" in metadata
        validation = metadata["validation"]
        assert any("small" in w.lower() for w in validation["validation_warnings"])

    def test_bit_depth_calculation(self, processor):
        """Test bit depth is correctly calculated."""
        # RGB image should have 24-bit depth
        img_rgb = Image.new("RGB", (100, 100), color="white")
        buffer = io.BytesIO()
        img_rgb.save(buffer, format="PNG")

        metadata = processor.process_image_bytes(buffer.getvalue())
        tech_specs = metadata["image_technical_specs"]
        assert tech_specs["bit_depth"] == 24

        # RGBA image should have 32-bit depth
        img_rgba = Image.new("RGBA", (100, 100), color=(255, 255, 255, 255))
        buffer = io.BytesIO()
        img_rgba.save(buffer, format="PNG")

        metadata = processor.process_image_bytes(buffer.getvalue())
        tech_specs = metadata["image_technical_specs"]
        assert tech_specs["bit_depth"] == 32

    def test_extract_technical_specs_directly(self, processor):
        """Test _extract_technical_specs method directly."""
        img = Image.new("RGB", (1200, 900), color="yellow")
        tech_specs = processor._extract_technical_specs(img, 50000)

        assert tech_specs["width"] == 1200
        assert tech_specs["height"] == 900
        assert tech_specs["aspect_ratio"] == "4:3"
        assert tech_specs["file_size_bytes"] == 50000
        assert tech_specs["format"] is not None

    def test_mime_type_mapping(self, processor):
        """Test MIME type mapping for different formats."""
        # Test JPEG
        assert processor.MIME_TYPES["JPEG"] == "image/jpeg"
        assert processor.MIME_TYPES["PNG"] == "image/png"
        assert processor.MIME_TYPES["GIF"] == "image/gif"
        assert processor.MIME_TYPES["WebP"] == "image/webp"

    def test_exif_extraction_no_exif(self, processor, sample_image_bytes):
        """Test EXIF extraction when no EXIF data is present."""
        img = Image.open(io.BytesIO(sample_image_bytes))
        exif_data = processor._extract_exif_data(img)

        # Simple test images usually don't have EXIF
        # Result can be None or empty dict
        assert exif_data is None or isinstance(exif_data, dict)

    def test_validation_result_structure(self, processor, sample_image_bytes):
        """Test validation result has correct structure."""
        img = Image.open(io.BytesIO(sample_image_bytes))
        validation = processor._validate_image(img, len(sample_image_bytes))

        assert "is_valid" in validation
        assert isinstance(validation["is_valid"], bool)
        assert "validation_timestamp" in validation
        assert "validation_errors" in validation
        assert isinstance(validation["validation_errors"], list)
        assert "validation_warnings" in validation
        assert isinstance(validation["validation_warnings"], list)

    def test_convert_to_degrees(self, processor):
        """Test GPS coordinate conversion to decimal degrees."""
        # Example: 40°26'46" N = 40.446111°
        # Represented as ((40, 1), (26, 1), (46, 1))
        gps_value = ((40, 1), (26, 1), (46, 1))
        degrees = processor._convert_to_degrees(gps_value)

        assert abs(degrees - 40.446111) < 0.0001

    @pytest.mark.asyncio
    async def test_close_http_client(self, processor):
        """Test closing HTTP client."""
        # Should not raise any errors
        await processor.close()

    def test_metadata_conforms_to_spec(self, processor, sample_image_bytes):
        """Test that generated metadata conforms to our spec."""
        metadata = processor.process_image_bytes(
            sample_image_bytes,
            source_url="https://example.com/test.jpg",
        )

        # Required top-level fields
        assert "_schema_version" in metadata
        assert "image_technical_specs" in metadata
        assert "processing_info" in metadata

        # Optional top-level fields that should be present
        assert "source_info" in metadata  # Because we provided source_url

        # Required fields in image_technical_specs
        tech_specs = metadata["image_technical_specs"]
        required_fields = [
            "width",
            "height",
            "file_size_bytes",
            "mime_type",
            "format",
        ]
        for field in required_fields:
            assert field in tech_specs, f"Missing required field: {field}"

        # Required fields in processing_info
        proc_info = metadata["processing_info"]
        assert "download_timestamp" in proc_info
        assert "download_status" in proc_info


class TestImageMetadataIntegration:
    """Integration tests for image metadata with Pydantic models."""

    def test_metadata_validates_with_pydantic(self):
        """Test that generated metadata validates with our Pydantic model."""
        from src.services.parser.models import ImageMetadata

        # Create a simple image and process it
        processor = ImageProcessorService()
        img = Image.new("RGB", (640, 480), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

        metadata = processor.process_image_bytes(image_bytes)
        tech_specs = metadata["image_technical_specs"]

        # Validate with Pydantic
        image_metadata = ImageMetadata(**tech_specs)

        assert image_metadata.width == 640
        assert image_metadata.height == 480
        assert image_metadata.format == "JPEG"
