# Article Images Metadata Specification

**Document Version**: 1.0
**Last Updated**: 2025-11-08
**Status**: Design Document - Phase 7

---

## 1. Overview

This document specifies the **JSONB metadata structure** for the `article_images.metadata` column. This field stores technical specifications and processing information about images extracted from Google Docs articles.

### 1.1 Purpose

- **Storage**: Persist comprehensive image technical specifications without adding columns
- **Flexibility**: Support future metadata fields without schema migrations
- **Querying**: Enable PostgreSQL JSONB operators for filtering and analytics
- **Debugging**: Track image processing details for troubleshooting

### 1.2 Design Principles

- **Schema Versioning**: Include `_schema_version` for future evolution
- **Required vs Optional**: Core fields vs. optional enhancement data
- **Data Types**: Use JSON-native types (string, number, boolean, array, object)
- **Null Handling**: Omit fields rather than storing `null` for optional data

---

## 2. JSONB Schema Structure

### 2.1 Full Example

```json
{
  "_schema_version": "1.0",
  "image_technical_specs": {
    "width": 1920,
    "height": 1080,
    "aspect_ratio": "16:9",
    "file_size_bytes": 2458624,
    "mime_type": "image/jpeg",
    "format": "JPEG",
    "color_mode": "RGB",
    "has_transparency": false,
    "bit_depth": 24
  },
  "exif_data": {
    "exif_date": "2025-11-08T10:30:00Z",
    "camera_make": "Canon",
    "camera_model": "EOS 5D Mark IV",
    "iso": 400,
    "exposure_time": "1/250",
    "f_number": "f/2.8",
    "focal_length": "85mm",
    "gps_latitude": 25.0330,
    "gps_longitude": 121.5654
  },
  "processing_info": {
    "download_timestamp": "2025-11-08T12:00:00Z",
    "download_status": "success",
    "processor_version": "1.0.0",
    "processing_duration_ms": 1234,
    "thumbnail_generated": true,
    "compression_applied": false
  },
  "source_info": {
    "original_filename": "healthcare-innovation-2024.jpg",
    "google_drive_file_id": "1abc123def456",
    "original_url": "https://drive.google.com/uc?export=download&id=1abc123def456"
  },
  "validation": {
    "is_valid": true,
    "validation_timestamp": "2025-11-08T12:00:05Z",
    "validation_errors": [],
    "validation_warnings": [
      "Image width exceeds 1920px, may need resizing for web"
    ]
  }
}
```

### 2.2 Minimal Example (Required Fields Only)

```json
{
  "_schema_version": "1.0",
  "image_technical_specs": {
    "width": 800,
    "height": 600,
    "file_size_bytes": 124567,
    "mime_type": "image/png",
    "format": "PNG"
  },
  "processing_info": {
    "download_timestamp": "2025-11-08T12:00:00Z",
    "download_status": "success"
  }
}
```

---

## 3. Field Specifications

### 3.1 Top-Level Fields

| Field             | Type   | Required | Description                                      |
|-------------------|--------|----------|--------------------------------------------------|
| `_schema_version` | string | **Yes**  | Metadata schema version (currently `"1.0"`)      |
| `image_technical_specs` | object | **Yes** | Core image technical specifications      |
| `exif_data`       | object | No       | EXIF metadata extracted from image               |
| `processing_info` | object | **Yes**  | Image processing and download information        |
| `source_info`     | object | No       | Source file and origin information               |
| `validation`      | object | No       | Image validation results and warnings            |

---

### 3.2 `image_technical_specs` Object

**Purpose**: Core technical specifications of the image file.

| Field              | Type    | Required | Description                                    | Example        |
|--------------------|---------|----------|------------------------------------------------|----------------|
| `width`            | integer | **Yes**  | Image width in pixels                          | `1920`         |
| `height`           | integer | **Yes**  | Image height in pixels                         | `1080`         |
| `aspect_ratio`     | string  | No       | Calculated aspect ratio                        | `"16:9"`       |
| `file_size_bytes`  | integer | **Yes**  | File size in bytes                             | `2458624`      |
| `mime_type`        | string  | **Yes**  | MIME type of image                             | `"image/jpeg"` |
| `format`           | string  | **Yes**  | Image format (JPEG, PNG, GIF, WebP, etc.)      | `"JPEG"`       |
| `color_mode`       | string  | No       | Color mode (RGB, RGBA, Grayscale, CMYK)        | `"RGB"`        |
| `has_transparency` | boolean | No       | Whether image has alpha channel                | `false`        |
| `bit_depth`        | integer | No       | Color bit depth (8, 16, 24, 32)                | `24`           |
| `dpi`              | integer | No       | Dots per inch (if available)                   | `300`          |

**Implementation Notes**:
- Extract using Python **PIL/Pillow** library
- `aspect_ratio` should be calculated as `gcd(width, height)` ratio or common format (e.g., "16:9", "4:3", "1:1")
- `has_transparency` is `true` for PNG with alpha channel, `false` for JPEG

**Example**:
```json
{
  "width": 1920,
  "height": 1080,
  "aspect_ratio": "16:9",
  "file_size_bytes": 2458624,
  "mime_type": "image/jpeg",
  "format": "JPEG",
  "color_mode": "RGB",
  "has_transparency": false,
  "bit_depth": 24
}
```

---

### 3.3 `exif_data` Object

**Purpose**: EXIF metadata extracted from image file (if available).

| Field           | Type    | Required | Description                                | Example                   |
|-----------------|---------|----------|--------------------------------------------|---------------------------|
| `exif_date`     | string  | No       | Original capture date (ISO 8601)           | `"2025-11-08T10:30:00Z"`  |
| `camera_make`   | string  | No       | Camera manufacturer                        | `"Canon"`                 |
| `camera_model`  | string  | No       | Camera model                               | `"EOS 5D Mark IV"`        |
| `iso`           | integer | No       | ISO sensitivity                            | `400`                     |
| `exposure_time` | string  | No       | Shutter speed                              | `"1/250"`                 |
| `f_number`      | string  | No       | Aperture f-stop                            | `"f/2.8"`                 |
| `focal_length`  | string  | No       | Focal length                               | `"85mm"`                  |
| `gps_latitude`  | number  | No       | GPS latitude (decimal degrees)             | `25.0330`                 |
| `gps_longitude` | number  | No       | GPS longitude (decimal degrees)            | `121.5654`                |

**Implementation Notes**:
- Extract using PIL's `Image._getexif()` or `piexif` library
- Convert all dates to ISO 8601 format
- GPS coordinates should be in decimal degrees (not DMS format)
- All fields are **optional** since not all images have EXIF data

**Example**:
```json
{
  "exif_date": "2025-11-08T10:30:00Z",
  "camera_make": "Canon",
  "camera_model": "EOS 5D Mark IV",
  "iso": 400,
  "exposure_time": "1/250",
  "f_number": "f/2.8",
  "focal_length": "85mm"
}
```

---

### 3.4 `processing_info` Object

**Purpose**: Track image processing and download information.

| Field                   | Type    | Required | Description                                  | Example                   |
|-------------------------|---------|----------|----------------------------------------------|---------------------------|
| `download_timestamp`    | string  | **Yes**  | When image was downloaded (ISO 8601)         | `"2025-11-08T12:00:00Z"`  |
| `download_status`       | string  | **Yes**  | Download status: `success` \| `failed` \| `partial` | `"success"`      |
| `processor_version`     | string  | No       | Version of image processor used              | `"1.0.0"`                 |
| `processing_duration_ms`| integer | No       | Processing time in milliseconds              | `1234`                    |
| `thumbnail_generated`   | boolean | No       | Whether thumbnail/preview was created        | `true`                    |
| `compression_applied`   | boolean | No       | Whether compression was applied              | `false`                   |
| `error_message`         | string  | No       | Error message if download_status != success  | `"HTTP 404: File not found"` |

**Implementation Notes**:
- `download_timestamp` should be set when image processing begins
- `download_status` tracks success/failure state
- Use `error_message` to store detailed error information if download fails

**Example**:
```json
{
  "download_timestamp": "2025-11-08T12:00:00Z",
  "download_status": "success",
  "processor_version": "1.0.0",
  "processing_duration_ms": 1234,
  "thumbnail_generated": true
}
```

---

### 3.5 `source_info` Object

**Purpose**: Track original source file information.

| Field                  | Type   | Required | Description                                  | Example                                    |
|------------------------|--------|----------|----------------------------------------------|--------------------------------------------|
| `original_filename`    | string | No       | Original filename from Google Drive          | `"healthcare-innovation-2024.jpg"`         |
| `google_drive_file_id` | string | No       | Google Drive file ID (if applicable)         | `"1abc123def456"`                          |
| `original_url`         | string | No       | Original download URL                        | `"https://drive.google.com/uc?export=..."`|

**Implementation Notes**:
- Store this data to enable re-downloading if needed
- `google_drive_file_id` is the unique identifier in Google Drive

**Example**:
```json
{
  "original_filename": "healthcare-innovation-2024.jpg",
  "google_drive_file_id": "1abc123def456",
  "original_url": "https://drive.google.com/uc?export=download&id=1abc123def456"
}
```

---

### 3.6 `validation` Object

**Purpose**: Store image validation results and quality warnings.

| Field                   | Type    | Required | Description                                  | Example                   |
|-------------------------|---------|----------|----------------------------------------------|---------------------------|
| `is_valid`              | boolean | No       | Whether image passed validation              | `true`                    |
| `validation_timestamp`  | string  | No       | When validation occurred (ISO 8601)          | `"2025-11-08T12:00:05Z"`  |
| `validation_errors`     | array   | No       | Array of validation error messages           | `[]`                      |
| `validation_warnings`   | array   | No       | Array of non-blocking warnings               | `["Image width > 1920px"]`|

**Implementation Notes**:
- Validation should check:
  - File format is supported (JPEG, PNG, GIF, WebP)
  - File size is within limits (e.g., < 10MB)
  - Dimensions are reasonable (e.g., 100px ≤ width ≤ 4096px)
  - Image is not corrupted
- Store warnings for quality issues (e.g., low resolution, large file size)

**Example**:
```json
{
  "is_valid": true,
  "validation_timestamp": "2025-11-08T12:00:05Z",
  "validation_errors": [],
  "validation_warnings": [
    "Image width exceeds 1920px, may need resizing for web"
  ]
}
```

---

## 4. PostgreSQL JSONB Querying

### 4.1 Query Examples

**Query 1: Find all images larger than 2MB**
```sql
SELECT ai.id, ai.article_id, ai.caption, ai.metadata->'image_technical_specs'->>'file_size_bytes' as file_size
FROM article_images ai
WHERE (ai.metadata->'image_technical_specs'->>'file_size_bytes')::integer > 2097152
ORDER BY (ai.metadata->'image_technical_specs'->>'file_size_bytes')::integer DESC;
```

**Query 2: Find all images with specific format**
```sql
SELECT ai.id, ai.article_id, ai.metadata->'image_technical_specs'->>'format' as format
FROM article_images ai
WHERE ai.metadata->'image_technical_specs'->>'format' = 'PNG';
```

**Query 3: Find images with EXIF GPS data**
```sql
SELECT ai.id, ai.article_id,
       ai.metadata->'exif_data'->>'gps_latitude' as lat,
       ai.metadata->'exif_data'->>'gps_longitude' as lng
FROM article_images ai
WHERE ai.metadata->'exif_data' ? 'gps_latitude'
  AND ai.metadata->'exif_data' ? 'gps_longitude';
```

**Query 4: Find images with validation errors**
```sql
SELECT ai.id, ai.article_id, ai.metadata->'validation'->'validation_errors' as errors
FROM article_images ai
WHERE ai.metadata->'validation'->>'is_valid' = 'false';
```

**Query 5: Average image file size by article**
```sql
SELECT a.id, a.title_main,
       AVG((ai.metadata->'image_technical_specs'->>'file_size_bytes')::bigint) as avg_file_size
FROM articles a
JOIN article_images ai ON a.id = ai.article_id
GROUP BY a.id, a.title_main
ORDER BY avg_file_size DESC;
```

### 4.2 Index Usage

For optimal JSONB query performance, use the **GIN index** already defined in the schema:

```sql
CREATE INDEX idx_article_images_metadata_gin ON article_images USING GIN(metadata);
```

This index enables fast queries on:
- `?` operator (key existence): `WHERE metadata ? 'exif_data'`
- `@>` operator (containment): `WHERE metadata @> '{"image_technical_specs": {"format": "PNG"}}'`

---

## 5. Python Implementation

### 5.1 Metadata Generation (PIL/Pillow)

```python
from PIL import Image
from datetime import datetime
from pathlib import Path
import json

def extract_image_metadata(image_path: str, source_url: str | None = None) -> dict:
    """Extract comprehensive metadata from an image file.

    Args:
        image_path: Path to the image file
        source_url: Optional original download URL

    Returns:
        JSONB-compatible metadata dictionary
    """
    img = Image.open(image_path)
    file_stat = Path(image_path).stat()

    # Core technical specs (REQUIRED)
    metadata = {
        "_schema_version": "1.0",
        "image_technical_specs": {
            "width": img.width,
            "height": img.height,
            "file_size_bytes": file_stat.st_size,
            "mime_type": Image.MIME.get(img.format, "application/octet-stream"),
            "format": img.format or "UNKNOWN",
        },
        "processing_info": {
            "download_timestamp": datetime.utcnow().isoformat() + "Z",
            "download_status": "success",
        }
    }

    # Optional: Aspect ratio
    from math import gcd
    ratio_gcd = gcd(img.width, img.height)
    metadata["image_technical_specs"]["aspect_ratio"] = f"{img.width // ratio_gcd}:{img.height // ratio_gcd}"

    # Optional: Color mode and transparency
    metadata["image_technical_specs"]["color_mode"] = img.mode
    metadata["image_technical_specs"]["has_transparency"] = img.mode in ("RGBA", "LA", "PA")

    # Optional: EXIF data
    exif_data = img.getexif()
    if exif_data:
        exif_metadata = {}
        # Extract key EXIF tags (Tag IDs from PIL.ExifTags.TAGS)
        if 36867 in exif_data:  # DateTimeOriginal
            exif_metadata["exif_date"] = exif_data[36867]
        if 271 in exif_data:  # Make
            exif_metadata["camera_make"] = exif_data[271]
        if 272 in exif_data:  # Model
            exif_metadata["camera_model"] = exif_data[272]

        if exif_metadata:
            metadata["exif_data"] = exif_metadata

    # Optional: Source info
    if source_url:
        metadata["source_info"] = {
            "original_filename": Path(image_path).name,
            "original_url": source_url
        }

    return metadata


# Example usage:
metadata = extract_image_metadata(
    "/tmp/healthcare-innovation.jpg",
    source_url="https://drive.google.com/uc?export=download&id=1abc123"
)
print(json.dumps(metadata, indent=2))
```

### 5.2 SQLAlchemy Model Integration

```python
from sqlalchemy import Column, Integer, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB

class ArticleImage(Base):
    __tablename__ = "article_images"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    preview_path = Column(String(500))
    source_path = Column(String(500))
    source_url = Column(String(1000))
    caption = Column(Text)
    position = Column(Integer, nullable=False)
    metadata = Column(JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 6. Schema Evolution

### 6.1 Version History

| Version | Date       | Changes                                                    |
|---------|------------|------------------------------------------------------------|
| 1.0     | 2025-11-08 | Initial schema with all core and optional fields           |

### 6.2 Future Enhancements (v2.0+)

Potential future additions without schema migration:
- `ocr_text`: Extracted text from image using OCR
- `ai_tags`: AI-generated image classification tags
- `color_palette`: Dominant colors extracted from image
- `accessibility`: Alt text generation, color contrast data

Since this is JSONB, new fields can be added without Alembic migrations.

---

## 7. Validation Rules

### 7.1 Backend Validation (Python)

```python
from pydantic import BaseModel, Field, field_validator

class ImageTechnicalSpecs(BaseModel):
    width: int = Field(gt=0, le=10000)
    height: int = Field(gt=0, le=10000)
    file_size_bytes: int = Field(gt=0, le=10485760)  # Max 10MB
    mime_type: str = Field(pattern=r"^image/(jpeg|png|gif|webp)$")
    format: str
    aspect_ratio: str | None = None
    color_mode: str | None = None
    has_transparency: bool | None = None

class ArticleImageMetadata(BaseModel):
    _schema_version: str = "1.0"
    image_technical_specs: ImageTechnicalSpecs
    processing_info: dict
    exif_data: dict | None = None
    source_info: dict | None = None
    validation: dict | None = None

    @field_validator('_schema_version')
    def validate_schema_version(cls, v):
        if v not in ("1.0",):
            raise ValueError(f"Unsupported schema version: {v}")
        return v
```

---

## 8. Related Documentation

- **Database Schema**: See `backend/migrations/manual_sql/phase7_parsing_schema.sql`
- **Data Model**: See `specs/001-cms-automation/data-model.md` section 3.7
- **API Specification**: See `docs/API_PARSING_ENDPOINTS.md`
- **Implementation Tasks**: See `specs/001-cms-automation/tasks.md` T7.6 (Image Processor)

---

**Document Maintained By**: CMS Automation Team
**Review Cycle**: Before Phase 7 implementation begins
**Contact**: tech-lead@example.com
