"""Image processor service for extracting technical specifications from images.

This service uses PIL/Pillow to extract:
- Dimensions (width, height)
- File format and MIME type
- Color mode and transparency
- EXIF metadata (camera, GPS, etc.)
- File size and aspect ratio
"""

import io
import logging
from datetime import datetime
from math import gcd
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ExifTags

from src.services.parser.models import ImageMetadata

logger = logging.getLogger(__name__)


class ImageProcessorService:
    """Service for processing images and extracting technical metadata."""

    # MIME type mapping for PIL formats
    MIME_TYPES = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
        "WebP": "image/webp",
        "BMP": "image/bmp",
        "TIFF": "image/tiff",
        "ICO": "image/x-icon",
    }

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        """Initialize image processor.

        Args:
            http_client: Optional HTTP client for downloading images
        """
        self.http_client = http_client or httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    async def process_image_from_url(
        self,
        image_url: str,
        download_to_path: str | None = None,
    ) -> dict[str, Any]:
        """Download and process image from URL.

        Args:
            image_url: URL of image to process
            download_to_path: Optional path to save downloaded image

        Returns:
            Complete metadata dict conforming to JSONB spec

        Raises:
            httpx.HTTPError: If download fails
            PIL.UnidentifiedImageError: If image format is unrecognized
        """
        logger.debug(f"Processing image from URL: {image_url}")

        # Download image
        response = await self.http_client.get(image_url)
        response.raise_for_status()

        image_bytes = response.content

        # Save to file if requested
        if download_to_path:
            Path(download_to_path).write_bytes(image_bytes)
            logger.debug(f"Saved image to: {download_to_path}")

        # Process image bytes
        return self.process_image_bytes(
            image_bytes,
            source_url=image_url,
            file_path=download_to_path,
        )

    def process_image_file(self, file_path: str) -> dict[str, Any]:
        """Process image from file path.

        Args:
            file_path: Path to image file

        Returns:
            Complete metadata dict conforming to JSONB spec
        """
        logger.debug(f"Processing image from file: {file_path}")

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        return self.process_image_bytes(
            image_bytes,
            file_path=file_path,
        )

    def process_image_bytes(
        self,
        image_bytes: bytes,
        source_url: str | None = None,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """Process image from bytes.

        Args:
            image_bytes: Image data as bytes
            source_url: Optional source URL for metadata
            file_path: Optional file path for metadata

        Returns:
            Complete metadata dict conforming to JSONB spec version 1.0
        """
        img = Image.open(io.BytesIO(image_bytes))

        # Extract technical specifications
        tech_specs = self._extract_technical_specs(img, len(image_bytes))

        # Extract EXIF data
        exif_data = self._extract_exif_data(img)

        # Build metadata structure
        metadata = {
            "_schema_version": "1.0",
            "image_technical_specs": tech_specs,
            "processing_info": {
                "download_timestamp": datetime.utcnow().isoformat() + "Z",
                "download_status": "success",
                "processor_version": "1.0.0",
            },
        }

        # Add EXIF if available
        if exif_data:
            metadata["exif_data"] = exif_data

        # Add source info if available
        if source_url or file_path:
            metadata["source_info"] = {}
            if source_url:
                metadata["source_info"]["original_url"] = source_url
            if file_path:
                metadata["source_info"]["original_filename"] = Path(file_path).name

        # Validation
        validation = self._validate_image(img, len(image_bytes))
        if validation["validation_errors"] or validation["validation_warnings"]:
            metadata["validation"] = validation

        logger.debug(
            f"Processed image: {tech_specs['width']}x{tech_specs['height']}, "
            f"{tech_specs['format']}, {len(image_bytes)} bytes"
        )

        return metadata

    def _extract_technical_specs(self, img: Image.Image, file_size: int) -> dict[str, Any]:
        """Extract technical specifications from PIL Image.

        Args:
            img: PIL Image object
            file_size: File size in bytes

        Returns:
            Technical specs dict
        """
        width, height = img.size

        # Calculate aspect ratio
        ratio_gcd = gcd(width, height)
        aspect_ratio = f"{width // ratio_gcd}:{height // ratio_gcd}"

        # Get format and MIME type
        img_format = img.format or "UNKNOWN"
        mime_type = self.MIME_TYPES.get(img_format, "application/octet-stream")

        # Color mode and transparency
        color_mode = img.mode
        has_transparency = color_mode in ("RGBA", "LA", "PA", "P")

        # Calculate bit depth
        mode_to_depth = {
            "1": 1,
            "L": 8,
            "P": 8,
            "RGB": 24,
            "RGBA": 32,
            "CMYK": 32,
            "YCbCr": 24,
            "LAB": 24,
            "HSV": 24,
            "I": 32,
            "F": 32,
        }
        bit_depth = mode_to_depth.get(color_mode, None)

        tech_specs = {
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "format": img_format,
            "color_mode": color_mode,
            "has_transparency": has_transparency,
        }

        if bit_depth:
            tech_specs["bit_depth"] = bit_depth

        # Get DPI if available
        if hasattr(img, "info") and "dpi" in img.info:
            dpi = img.info["dpi"]
            if isinstance(dpi, tuple):
                tech_specs["dpi"] = int(dpi[0])  # Use horizontal DPI
            else:
                tech_specs["dpi"] = int(dpi)

        return tech_specs

    def _extract_exif_data(self, img: Image.Image) -> dict[str, Any] | None:
        """Extract EXIF metadata from image.

        Args:
            img: PIL Image object

        Returns:
            EXIF data dict or None if no EXIF data
        """
        try:
            exif_raw = img.getexif()
            if not exif_raw:
                return None

            exif_data = {}

            # Map common EXIF tags
            for tag_id, value in exif_raw.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)

                # Extract specific useful tags
                if tag_name == "DateTime":
                    # Convert to ISO format
                    try:
                        exif_data["exif_date"] = datetime.strptime(
                            value, "%Y:%m:%d %H:%M:%S"
                        ).isoformat() + "Z"
                    except ValueError:
                        exif_data["exif_date"] = value

                elif tag_name == "Make":
                    exif_data["camera_make"] = str(value).strip()

                elif tag_name == "Model":
                    exif_data["camera_model"] = str(value).strip()

                elif tag_name == "ISOSpeedRatings":
                    exif_data["iso"] = int(value)

                elif tag_name == "ExposureTime":
                    # Convert to fraction string
                    if isinstance(value, tuple) and len(value) == 2:
                        exif_data["exposure_time"] = f"{value[0]}/{value[1]}"
                    else:
                        exif_data["exposure_time"] = str(value)

                elif tag_name == "FNumber":
                    # Convert to f-stop string
                    if isinstance(value, tuple) and len(value) == 2:
                        f_number = value[0] / value[1]
                        exif_data["f_number"] = f"f/{f_number:.1f}"
                    else:
                        exif_data["f_number"] = f"f/{value}"

                elif tag_name == "FocalLength":
                    # Convert to mm string
                    if isinstance(value, tuple) and len(value) == 2:
                        focal_length = value[0] / value[1]
                        exif_data["focal_length"] = f"{focal_length:.0f}mm"
                    else:
                        exif_data["focal_length"] = f"{value}mm"

            # Extract GPS data if available
            if hasattr(exif_raw, "_get_ifd") and ExifTags.IFD.GPSInfo in exif_raw:
                gps_info = exif_raw.get_ifd(ExifTags.IFD.GPSInfo)
                gps_data = self._extract_gps_data(gps_info)
                if gps_data:
                    exif_data.update(gps_data)

            return exif_data if exif_data else None

        except Exception as e:
            logger.warning(f"Failed to extract EXIF data: {e}")
            return None

    def _extract_gps_data(self, gps_info: dict) -> dict[str, float]:
        """Extract GPS coordinates from EXIF GPS info.

        Args:
            gps_info: GPS IFD from EXIF

        Returns:
            Dict with gps_latitude and gps_longitude in decimal degrees
        """
        gps_data = {}

        try:
            # Get latitude
            if 2 in gps_info and 1 in gps_info:  # GPSLatitude and GPSLatitudeRef
                lat = self._convert_to_degrees(gps_info[2])
                if gps_info[1] == "S":
                    lat = -lat
                gps_data["gps_latitude"] = round(lat, 6)

            # Get longitude
            if 4 in gps_info and 3 in gps_info:  # GPSLongitude and GPSLongitudeRef
                lon = self._convert_to_degrees(gps_info[4])
                if gps_info[3] == "W":
                    lon = -lon
                gps_data["gps_longitude"] = round(lon, 6)

        except Exception as e:
            logger.warning(f"Failed to extract GPS data: {e}")

        return gps_data

    def _convert_to_degrees(self, value: tuple) -> float:
        """Convert GPS coordinates to decimal degrees.

        Args:
            value: Tuple of (degrees, minutes, seconds)

        Returns:
            Decimal degrees
        """
        d, m, s = value
        # Convert rational numbers to float
        d = float(d[0] / d[1]) if isinstance(d, tuple) else float(d)
        m = float(m[0] / m[1]) if isinstance(m, tuple) else float(m)
        s = float(s[0] / s[1]) if isinstance(s, tuple) else float(s)

        return d + (m / 60.0) + (s / 3600.0)

    def _validate_image(self, img: Image.Image, file_size: int) -> dict[str, Any]:
        """Validate image and return validation result.

        Args:
            img: PIL Image object
            file_size: File size in bytes

        Returns:
            Validation result dict
        """
        errors = []
        warnings = []

        width, height = img.size

        # Check dimensions
        if width < 100 or height < 100:
            warnings.append(f"Image dimensions are small ({width}x{height}px)")

        if width > 4096 or height > 4096:
            warnings.append(f"Image dimensions are large ({width}x{height}px)")

        # Check file size
        if file_size > 10 * 1024 * 1024:  # 10MB
            warnings.append(f"File size is large ({file_size / 1024 / 1024:.1f}MB)")

        if file_size < 1024:  # 1KB
            warnings.append(f"File size is very small ({file_size} bytes)")

        # Check format
        if img.format not in self.MIME_TYPES:
            warnings.append(f"Unusual image format: {img.format}")

        return {
            "is_valid": len(errors) == 0,
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
            "validation_errors": errors,
            "validation_warnings": warnings,
        }

    async def close(self) -> None:
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()


async def create_image_processor() -> ImageProcessorService:
    """Factory function to create ImageProcessorService.

    Returns:
        ImageProcessorService instance
    """
    return ImageProcessorService()
