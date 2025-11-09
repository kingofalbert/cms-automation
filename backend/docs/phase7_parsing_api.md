# Phase 7: Article Parsing API Documentation

**Version**: 1.0
**Date**: 2025-11-08
**Status**: Implemented ✅

## Overview

The Article Parsing API provides endpoints for extracting structured data from Google Doc HTML, including title decomposition, author extraction, body sanitization, SEO metadata, and image processing.

### Features

- **Dual Parsing Strategy**: AI-based (Claude) and heuristic (BeautifulSoup) fallback
- **Title Decomposition**: Extracts prefix (【專題】), main title, and suffix
- **Author Extraction**: Supports Chinese and English patterns (文／, 作者：, By:)
- **SEO Optimization**: Auto-generates meta descriptions and keywords
- **Image Processing**: Downloads, extracts metadata (EXIF, GPS), and manages images
- **Parsing Confirmation**: Review workflow before publishing

---

## API Endpoints

### 1. Parse Article

Trigger article parsing to extract structured data.

**Endpoint**: `POST /v1/articles/{article_id}/parse`

**Request Body**:
```json
{
  "use_ai": true,
  "download_images": true,
  "fallback_to_heuristic": true
}
```

**Parameters**:
- `use_ai` (boolean, default: `true`): Use Claude for parsing. If `false`, uses heuristic parsing.
- `download_images` (boolean, default: `true`): Download and process images.
- `fallback_to_heuristic` (boolean, default: `true`): Fall back to heuristic if AI fails.

**Response** (200 OK):
```json
{
  "success": true,
  "article_id": 123,
  "parsing_method": "ai",
  "parsing_confidence": 0.95,
  "images_processed": 3,
  "duration_ms": 2450.5,
  "warnings": [
    "Image dimensions are large (5000x4000px)"
  ],
  "errors": []
}
```

**Error Responses**:
- `404 Not Found`: Article not found
- `400 Bad Request`: Article has no raw HTML
- `500 Internal Server Error`: Parsing failed

**Example (curl)**:
```bash
curl -X POST "http://localhost:8000/v1/articles/123/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "use_ai": false,
    "download_images": true,
    "fallback_to_heuristic": true
  }'
```

**Example (Python)**:
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/v1/articles/123/parse",
        json={
            "use_ai": False,  # Use heuristic parsing
            "download_images": True,
            "fallback_to_heuristic": True
        }
    )
    result = response.json()
    print(f"Parsed with {result['parsing_method']}, {result['images_processed']} images")
```

---

### 2. Get Parsing Result

Retrieve parsed article data for review.

**Endpoint**: `GET /v1/articles/{article_id}/parsing-result`

**Response** (200 OK):
```json
{
  "title_prefix": "【專題報導】",
  "title_main": "2024年醫療保健創新趨勢",
  "title_suffix": "從AI診斷到遠距醫療",
  "full_title": "【專題報導】 2024年醫療保健創新趨勢 從AI診斷到遠距醫療",
  "author_line": "文／張三｜編輯／李四",
  "author_name": "張三",
  "body_html": "<p>本文探討...</p><p>隨著科技...</p>",
  "meta_description": "本文探討2024年醫療保健領域的最新創新趨勢...",
  "seo_keywords": ["醫療保健", "AI診斷", "遠距醫療", "創新技術", "數位健康"],
  "parsing_method": "ai",
  "parsing_confidence": 0.95,
  "parsing_confirmed": false,
  "has_seo_data": true,
  "images": [
    {
      "id": 456,
      "position": 0,
      "source_url": "https://docs.google.com/...",
      "preview_path": "/data/images/article_123/image_0.jpg",
      "caption": "圖1：AI診斷系統界面",
      "width": 1920,
      "height": 1080,
      "format": "JPEG"
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: Article not found
- `400 Bad Request`: Article has not been parsed yet

**Example (curl)**:
```bash
curl -X GET "http://localhost:8000/v1/articles/123/parsing-result"
```

---

### 3. Confirm Parsing

Confirm that parsed data is correct and ready for publishing.

**Endpoint**: `POST /v1/articles/{article_id}/confirm-parsing`

**Request Body**:
```json
{
  "confirmed_by": "john_doe",
  "feedback": "All data looks correct. Ready to publish."
}
```

**Parameters**:
- `confirmed_by` (string, required): Username or ID of the person confirming
- `feedback` (string, optional): Optional feedback about parsing quality

**Response** (200 OK):
```json
{
  "success": true,
  "article_id": 123,
  "confirmed_at": "2025-11-08T10:30:00Z",
  "confirmed_by": "john_doe"
}
```

**Error Responses**:
- `404 Not Found`: Article not found
- `400 Bad Request`: Article has not been parsed yet

**Example (curl)**:
```bash
curl -X POST "http://localhost:8000/v1/articles/123/confirm-parsing" \
  -H "Content-Type: application/json" \
  -d '{
    "confirmed_by": "john_doe",
    "feedback": "Looks good!"
  }'
```

---

### 4. List Article Images

Get all parsed images for an article.

**Endpoint**: `GET /v1/articles/{article_id}/images`

**Response** (200 OK):
```json
[
  {
    "id": 456,
    "position": 0,
    "source_url": "https://example.com/image1.jpg",
    "preview_path": "/data/images/article_123/image_0.jpg",
    "caption": "圖1：AI診斷示意圖",
    "width": 1920,
    "height": 1080,
    "format": "JPEG",
    "file_size_bytes": 245632
  },
  {
    "id": 457,
    "position": 1,
    "source_url": "https://example.com/image2.png",
    "preview_path": "/data/images/article_123/image_1.png",
    "caption": "圖2：遠距醫療平台",
    "width": 1280,
    "height": 720,
    "format": "PNG",
    "file_size_bytes": 158420
  }
]
```

**Example (curl)**:
```bash
curl -X GET "http://localhost:8000/v1/articles/123/images"
```

---

### 5. Review Image

Take action on a parsed image (keep, remove, or replace).

**Endpoint**: `POST /v1/articles/{article_id}/images/{image_id}/review`

**Request Body**:
```json
{
  "action": "replace_caption",
  "new_caption": "圖1：更新後的圖片說明"
}
```

**Parameters**:
- `action` (enum, required): One of `keep`, `remove`, `replace_caption`, `replace_source`
- `new_caption` (string): Required if `action=replace_caption`
- `new_source_url` (string): Required if `action=replace_source`

**Actions**:

#### Keep Image
```json
{
  "action": "keep"
}
```

#### Remove Image
```json
{
  "action": "remove"
}
```

#### Replace Caption
```json
{
  "action": "replace_caption",
  "new_caption": "New caption text"
}
```

#### Replace Source
```json
{
  "action": "replace_source",
  "new_source_url": "https://example.com/new-image.jpg"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "image_id": 456,
  "action": "replace_caption",
  "review_id": 789
}
```

**Error Responses**:
- `404 Not Found`: Image not found
- `400 Bad Request`: Missing required parameter (e.g., `new_caption`)

**Example (curl)**:
```bash
# Replace caption
curl -X POST "http://localhost:8000/v1/articles/123/images/456/review" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "replace_caption",
    "new_caption": "Updated caption"
  }'

# Remove image
curl -X POST "http://localhost:8000/v1/articles/123/images/457/review" \
  -H "Content-Type: application/json" \
  -d '{"action": "remove"}'
```

---

## Complete Workflow Example

### Scenario: Parse a newly imported article

```python
import httpx
import asyncio

async def parse_and_confirm_article(article_id: int):
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:

        # Step 1: Parse article with AI
        print("Step 1: Parsing article...")
        parse_response = await client.post(
            f"/v1/articles/{article_id}/parse",
            json={
                "use_ai": True,
                "download_images": True,
                "fallback_to_heuristic": True
            }
        )
        parse_result = parse_response.json()
        print(f"✅ Parsed: {parse_result['parsing_method']}, "
              f"{parse_result['images_processed']} images")

        # Step 2: Review parsing result
        print("\nStep 2: Reviewing parsed data...")
        result_response = await client.get(
            f"/v1/articles/{article_id}/parsing-result"
        )
        article_data = result_response.json()
        print(f"Title: {article_data['full_title']}")
        print(f"Author: {article_data['author_name']}")
        print(f"Images: {len(article_data['images'])}")
        print(f"SEO Keywords: {', '.join(article_data['seo_keywords'][:5])}")

        # Step 3: Review images
        print("\nStep 3: Reviewing images...")
        for img in article_data['images']:
            print(f"  - Image {img['id']}: {img['width']}x{img['height']} "
                  f"at position {img['position']}")

        # Example: Replace caption for first image
        if article_data['images']:
            first_image = article_data['images'][0]
            await client.post(
                f"/v1/articles/{article_id}/images/{first_image['id']}/review",
                json={
                    "action": "replace_caption",
                    "new_caption": "Updated: AI診斷系統示意圖"
                }
            )
            print(f"  ✓ Updated caption for image {first_image['id']}")

        # Step 4: Confirm parsing
        print("\nStep 4: Confirming parsing...")
        confirm_response = await client.post(
            f"/v1/articles/{article_id}/confirm-parsing",
            json={
                "confirmed_by": "api_user",
                "feedback": "Automated confirmation"
            }
        )
        confirm_result = confirm_response.json()
        print(f"✅ Parsing confirmed at {confirm_result['confirmed_at']}")

# Run the workflow
asyncio.run(parse_and_confirm_article(123))
```

**Expected Output**:
```
Step 1: Parsing article...
✅ Parsed: ai, 3 images

Step 2: Reviewing parsed data...
Title: 【專題報導】 2024年醫療保健創新趨勢 從AI診斷到遠距醫療
Author: 張三
Images: 3
SEO Keywords: 醫療保健, AI診斷, 遠距醫療, 創新技術, 數位健康

Step 3: Reviewing images...
  - Image 456: 1920x1080 at position 0
  - Image 457: 1280x720 at position 1
  - Image 458: 800x600 at position 2
  ✓ Updated caption for image 456

Step 4: Confirming parsing...
✅ Parsing confirmed at 2025-11-08T10:30:00Z
```

---

## Data Models

### ParsedArticleData

```typescript
interface ParsedArticleData {
  // Title components
  title_prefix?: string;       // "【專題報導】"
  title_main: string;           // "2024年醫療創新"
  title_suffix?: string;        // "AI應用"
  full_title: string;           // Combined title

  // Author info
  author_line?: string;         // "文／張三｜編輯／李四"
  author_name?: string;         // "張三"

  // Content
  body_html: string;            // Sanitized HTML
  meta_description?: string;    // SEO description (150-160 chars)
  seo_keywords: string[];       // SEO keywords

  // Metadata
  parsing_method: string;       // "ai" | "heuristic"
  parsing_confidence: number;   // 0.0 - 1.0
  parsing_confirmed: boolean;   // User confirmed?
  has_seo_data: boolean;       // Has meta description or keywords?

  // Images
  images: ImageData[];
}
```

### ImageData

```typescript
interface ImageData {
  id: number;
  position: number;             // Paragraph index (0-based)
  source_url: string;
  preview_path?: string;
  caption?: string;
  width?: number;
  height?: number;
  format?: string;              // "JPEG", "PNG", "GIF", etc.
  file_size_bytes?: number;
}
```

### ImageReviewAction

```typescript
enum ImageReviewAction {
  KEEP = "keep",
  REMOVE = "remove",
  REPLACE_CAPTION = "replace_caption",
  REPLACE_SOURCE = "replace_source"
}
```

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request (missing fields, wrong state)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error during processing

### Example Error Responses

**Article not found (404)**:
```json
{
  "detail": "Article 123 not found"
}
```

**Article not parsed yet (400)**:
```json
{
  "detail": "Article has not been parsed yet. Call /parse first."
}
```

**Missing required field (400)**:
```json
{
  "detail": "new_caption is required when action=replace_caption"
}
```

---

## Performance Considerations

### Parsing Duration

- **Heuristic mode**: ~500-1000ms for typical articles
- **AI mode**: ~2000-5000ms (depends on article length)
- **Image processing**: ~200-500ms per image (download + metadata extraction)

### Cost Estimation (AI Mode)

Claude Sonnet 3.5 pricing:
- Input: $3/million tokens
- Output: $15/million tokens

Typical article (~2000 characters):
- Input tokens: ~3000 (HTML + prompt)
- Output tokens: ~1000 (structured JSON)
- Cost: ~$0.024 per article

### Recommendations

1. **Use heuristic mode** for bulk processing to save costs
2. **Use AI mode** for high-quality content where accuracy is critical
3. **Enable fallback** to ensure parsing always succeeds
4. **Skip image download** during testing to speed up development

---

## Integration with Publishing Workflow

The parsing API integrates with the publishing workflow:

```
1. Import from Google Docs → Article (raw_html)
2. Parse article → Extract structured data
3. Review & confirm → Mark as ready
4. Publish to WordPress → Use confirmed data
```

### Required Fields for Publishing

After parsing confirmation, these fields should be populated:

- `title_main` (required)
- `body_html` (required)
- `author_name` (optional but recommended)
- `meta_description` (optional but recommended for SEO)
- `seo_keywords` (optional but recommended for SEO)
- At least 1 image (optional but recommended)

---

## OpenAPI / Swagger Documentation

All endpoints are automatically documented in the OpenAPI schema.

Access interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Support & Troubleshooting

### Common Issues

**Q: Parsing fails with "no raw HTML" error**
A: The article must be imported from Google Docs first. Call the import endpoint before parsing.

**Q: AI parsing returns low confidence**
A: The article HTML structure might be unusual. Try heuristic mode or review the raw HTML format.

**Q: Images are not downloading**
A: Check that `download_images=true` and image URLs are accessible. Verify network connectivity.

**Q: Parsing confirmation fails**
A: Ensure the article has been parsed successfully (check `title_main` is not null).

### Debug Logging

Enable debug logging to troubleshoot issues:

```bash
export LOG_LEVEL=DEBUG
```

Check logs for detailed parsing information:
```
INFO: Parsing article 123 (use_ai=True)
DEBUG: Extracting title using heuristics
DEBUG: Found author: 張三
DEBUG: Extracted 3 images total
INFO: Article 123 parsed successfully
```

---

## Changelog

### v1.0 (2025-11-08)
- ✅ Initial implementation
- ✅ Dual parsing strategy (AI + heuristic)
- ✅ Chinese language support
- ✅ Image processing with EXIF extraction
- ✅ Parsing confirmation workflow
- ✅ Image review endpoints

---

## Related Documentation

- [Phase 7 Specification](../../specs/001-cms-automation/spec.md#phase-7-article-structured-parsing)
- [Database Schema](./database_schema_updates.md#phase-7-parsing-fields)
- [Image Metadata Spec](./article_images_metadata_spec.md)
