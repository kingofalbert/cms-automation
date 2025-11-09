# Article Parsing API Documentation

**Version**: 1.0.0
**Created**: 2025-11-08
**Status**: Design Phase
**Base URL**: `/api/v1`

---

## Overview

This document describes the API endpoints for the Article Structured Parsing feature. These endpoints extend the existing Worklist API to support:
- Retrieving structured parsing results
- Confirming parsing quality
- Managing image reviews

---

## Endpoints

### 1. Get Worklist Item Detail (Extended)

Retrieves detailed information for a worklist item, including all structured parsing fields and images.

**Endpoint**: `GET /v1/worklist/{item_id}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Worklist item ID |

**Response**: `200 OK`

```json
{
  "id": 123,
  "article_id": 456,
  "status": "pending",
  "created_at": "2025-11-08T10:00:00Z",
  "updated_at": "2025-11-08T10:30:00Z",

  // Structured Parsing Fields (NEW)
  "title_prefix": "專題報導",
  "title_main": "AI驅動的內容管理系統",
  "title_suffix": "未來趨勢分析",
  "author_line": "文／張三",
  "author_name": "張三",
  "body_html": "<h2>引言</h2><p>內容...</p>",
  "meta_description": "探討AI如何改變內容管理系統的未來發展趨勢",
  "seo_keywords": ["AI", "CMS", "自動化", "內容管理"],
  "tags": ["技術", "趨勢", "AI"],

  // Images Array (NEW)
  "images": [
    {
      "id": 789,
      "preview_path": "/media/articles/456/preview_001.jpg",
      "source_path": "/media/articles/456/source_001.jpg",
      "source_url": "https://drive.google.com/file/d/...",
      "caption": "圖1：系統架構圖",
      "position": 3,
      "metadata": {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "file_size_bytes": 2458624,
        "mime_type": "image/jpeg",
        "format": "JPEG",
        "color_mode": "RGB",
        "has_transparency": false,
        "exif_date": "2025-11-08T10:30:00Z",
        "download_timestamp": "2025-11-08T10:35:00Z"
      }
    },
    {
      "id": 790,
      "preview_path": "/media/articles/456/preview_002.jpg",
      "source_path": "/media/articles/456/source_002.jpg",
      "source_url": "https://drive.google.com/file/d/...",
      "caption": "圖2：用戶界面截圖",
      "position": 7,
      "metadata": {
        "width": 1600,
        "height": 900,
        "aspect_ratio": "16:9",
        "file_size_bytes": 1856234,
        "mime_type": "image/jpeg",
        "format": "JPEG",
        "color_mode": "RGB",
        "has_transparency": false,
        "exif_date": null,
        "download_timestamp": "2025-11-08T10:36:00Z"
      }
    }
  ],

  // Parsing Confirmation State (NEW)
  "parsing_confirmed": false,
  "parsing_confirmed_at": null,
  "parsing_confirmed_by": null,
  "parsing_feedback": null,

  // Existing Worklist Fields
  "google_drive_doc_id": "1abc123xyz",
  "google_drive_file_name": "2025-11-08 文章標題.gdoc",
  "google_drive_folder_id": "folder_123",
  "original_content": "<original HTML>",
  "proofread_content": null,
  "proofreading_analysis": null
}
```

**Error Responses**:

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| 404 Not Found | Worklist item not found | `{"detail": "Worklist item not found"}` |
| 500 Internal Server Error | Server error | `{"detail": "Internal server error"}` |

---

### 2. Confirm Parsing (NEW)

Confirms that the parsing results have been reviewed and approved by a human reviewer. This unlocks Step 2 (content proofreading) in the UI workflow.

**Endpoint**: `POST /v1/worklist/{item_id}/confirm-parsing`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Worklist item ID |

**Request Body**:

```json
{
  "parsing_confirmed": true,
  "parsing_feedback": "All fields look correct. Minor edit to title suffix.",
  "image_reviews": [
    {
      "article_image_id": 789,
      "action": "keep",
      "new_caption": null,
      "new_source_url": null,
      "reviewer_notes": "Image quality is good"
    },
    {
      "article_image_id": 790,
      "action": "replace_caption",
      "new_caption": "圖2：更新後的用戶界面截圖",
      "new_source_url": null,
      "reviewer_notes": "Caption was outdated"
    }
  ]
}
```

**Request Schema**:

```typescript
interface ParsingConfirmationRequest {
  parsing_confirmed: boolean;           // Whether parsing is confirmed
  parsing_feedback?: string;            // Optional feedback text
  image_reviews?: ImageReview[];        // Optional array of image reviews
}

interface ImageReview {
  article_image_id: number;             // ID of the article_images record
  action: 'keep' | 'remove' | 'replace_caption' | 'replace_source';
  new_caption?: string;                 // New caption if action='replace_caption'
  new_source_url?: string;              // New source URL if action='replace_source'
  reviewer_notes?: string;              // Optional notes explaining the action
}
```

**Response**: `200 OK`

```json
{
  "success": true,
  "worklist_item_id": 123,
  "article_id": 456,
  "parsing_confirmed_at": "2025-11-08T11:00:00Z",
  "parsing_confirmed_by": "user_123",
  "image_reviews_created": 2
}
```

**Response Schema**:

```typescript
interface ParsingConfirmationResponse {
  success: boolean;
  worklist_item_id: number;
  article_id: number;
  parsing_confirmed_at: string;         // ISO 8601 timestamp
  parsing_confirmed_by: string;         // User ID or username
  image_reviews_created: number;        // Count of image reviews saved
}
```

**Error Responses**:

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| 400 Bad Request | Invalid input (e.g., invalid action) | `{"detail": "Invalid image review action: 'invalid_action'"}` |
| 404 Not Found | Worklist item not found | `{"detail": "Worklist item not found"}` |
| 404 Not Found | Image not found | `{"detail": "Article image with id 789 not found"}` |
| 409 Conflict | Already confirmed | `{"detail": "Parsing already confirmed at 2025-11-08T10:00:00Z"}` |
| 500 Internal Server Error | Server error | `{"detail": "Failed to save parsing confirmation"}` |

**Validation Rules**:

| Field | Validation |
|-------|------------|
| `parsing_confirmed` | Required, must be boolean |
| `parsing_feedback` | Optional, max 1000 characters |
| `image_reviews` | Optional, max 100 items |
| `image_reviews[].action` | Must be one of: 'keep', 'remove', 'replace_caption', 'replace_source' |
| `image_reviews[].new_caption` | Required if action='replace_caption', max 500 characters |
| `image_reviews[].new_source_url` | Required if action='replace_source', must be valid URL |
| `image_reviews[].reviewer_notes` | Optional, max 1000 characters |

---

### 3. Update Parsing Fields (NEW)

Updates individual parsing fields after initial extraction. Allows reviewers to correct parsing errors before confirming.

**Endpoint**: `PATCH /v1/worklist/{item_id}/parsing-fields`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | Worklist item ID |

**Request Body**:

```json
{
  "title_prefix": "更新的前標題",
  "title_main": "更新的主標題",
  "title_suffix": "更新的副標題",
  "author_name": "張三（更正）",
  "meta_description": "更新的Meta描述",
  "seo_keywords": ["AI", "CMS", "自動化", "新關鍵詞"],
  "tags": ["技術", "趨勢", "AI", "新標籤"]
}
```

**Request Schema**:

```typescript
interface ParsingFieldsUpdateRequest {
  title_prefix?: string | null;        // Optional, nullable
  title_main?: string;                  // Optional (but required in database)
  title_suffix?: string | null;        // Optional, nullable
  author_name?: string | null;         // Optional, nullable
  meta_description?: string | null;    // Optional, nullable
  seo_keywords?: string[];              // Optional, array of strings
  tags?: string[];                      // Optional, array of strings
}
```

**Response**: `200 OK`

```json
{
  "success": true,
  "worklist_item_id": 123,
  "article_id": 456,
  "updated_fields": ["title_prefix", "title_main", "seo_keywords"],
  "updated_at": "2025-11-08T11:30:00Z"
}
```

**Error Responses**:

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| 400 Bad Request | Validation error | `{"detail": "title_main cannot be empty"}` |
| 404 Not Found | Worklist item not found | `{"detail": "Worklist item not found"}` |
| 500 Internal Server Error | Server error | `{"detail": "Failed to update parsing fields"}` |

**Validation Rules**:

| Field | Validation |
|-------|------------|
| `title_prefix` | Optional, max 200 characters |
| `title_main` | If provided, min 5 characters, max 500 characters |
| `title_suffix` | Optional, max 200 characters |
| `author_name` | Optional, max 100 characters |
| `meta_description` | Optional, max 1000 characters |
| `seo_keywords` | Optional, array, max 20 items, each max 50 characters |
| `tags` | Optional, array, max 30 items, each max 30 characters |

---

### 4. Get Parsing Statistics (NEW)

Retrieves statistics about parsing accuracy and performance across all articles.

**Endpoint**: `GET /v1/worklist/parsing-statistics`

**Query Parameters**: None

**Response**: `200 OK`

```json
{
  "total_articles_parsed": 1543,
  "parsing_confirmed_count": 1402,
  "parsing_pending_count": 141,
  "average_parsing_time_seconds": 18.5,
  "median_parsing_time_seconds": 16.2,
  "p95_parsing_time_seconds": 25.8,
  "image_success_rate": 0.95,
  "total_images_processed": 7234,
  "images_with_complete_metadata": 6872,
  "accuracy_metrics": {
    "title_accuracy": 0.92,
    "author_accuracy": 0.96,
    "image_detection_accuracy": 0.91,
    "meta_extraction_accuracy": 0.87
  },
  "last_updated": "2025-11-08T12:00:00Z"
}
```

**Response Schema**:

```typescript
interface ParsingStatistics {
  total_articles_parsed: number;
  parsing_confirmed_count: number;
  parsing_pending_count: number;
  average_parsing_time_seconds: number;
  median_parsing_time_seconds: number;
  p95_parsing_time_seconds: number;
  image_success_rate: number;           // 0.0 to 1.0
  total_images_processed: number;
  images_with_complete_metadata: number;
  accuracy_metrics: {
    title_accuracy: number;             // 0.0 to 1.0
    author_accuracy: number;
    image_detection_accuracy: number;
    meta_extraction_accuracy: number;
  };
  last_updated: string;                 // ISO 8601 timestamp
}
```

---

## Data Models

### ArticleImage

```typescript
interface ArticleImage {
  id: number;
  article_id: number;
  preview_path: string | null;         // Path to preview/thumbnail
  source_path: string;                  // Path to downloaded high-res image
  source_url: string;                   // Original Google Drive URL
  caption: string | null;               // Image caption
  position: number;                     // Paragraph index (0-based)
  metadata: ImageMetadata;              // Technical specifications
  created_at: string;                   // ISO 8601 timestamp
  updated_at: string;                   // ISO 8601 timestamp
}

interface ImageMetadata {
  width: number;                        // Image width in pixels
  height: number;                       // Image height in pixels
  aspect_ratio: string;                 // e.g., "16:9", "4:3", "1:1"
  file_size_bytes: number;              // File size in bytes
  mime_type: string;                    // e.g., "image/jpeg", "image/png"
  format: string;                       // e.g., "JPEG", "PNG", "WEBP"
  color_mode: string;                   // e.g., "RGB", "RGBA", "Grayscale"
  has_transparency: boolean;            // Whether image has alpha channel
  exif_date: string | null;            // EXIF DateTimeOriginal (ISO 8601)
  download_timestamp: string;           // When image was downloaded (ISO 8601)
}
```

### ArticleImageReview

```typescript
interface ArticleImageReview {
  id: number;
  article_image_id: number;
  worklist_item_id: number | null;
  action: 'keep' | 'remove' | 'replace_caption' | 'replace_source';
  new_caption: string | null;
  new_source_url: string | null;
  reviewer_notes: string | null;
  created_at: string;                   // ISO 8601 timestamp
}
```

---

## Authentication

All endpoints require authentication via JWT token.

**Header**:
```
Authorization: Bearer <token>
```

**Token Expiration**: 15 minutes (with 7-day refresh)

---

## Rate Limiting

| Endpoint | Rate Limit |
|----------|------------|
| `GET /v1/worklist/{item_id}` | 100 requests/minute per user |
| `POST /v1/worklist/{item_id}/confirm-parsing` | 20 requests/minute per user |
| `PATCH /v1/worklist/{item_id}/parsing-fields` | 50 requests/minute per user |
| `GET /v1/worklist/parsing-statistics` | 10 requests/minute per user |

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error message",
  "error_code": "PARSING_CONFIRMATION_FAILED",
  "timestamp": "2025-11-08T12:00:00Z"
}
```

**Common Error Codes**:

| Code | Description |
|------|-------------|
| `WORKLIST_ITEM_NOT_FOUND` | Worklist item does not exist |
| `ARTICLE_IMAGE_NOT_FOUND` | Article image does not exist |
| `PARSING_ALREADY_CONFIRMED` | Parsing has already been confirmed |
| `INVALID_IMAGE_REVIEW_ACTION` | Invalid action in image review |
| `VALIDATION_ERROR` | Request validation failed |
| `PARSING_CONFIRMATION_FAILED` | Failed to save confirmation |
| `PARSING_FIELDS_UPDATE_FAILED` | Failed to update parsing fields |

---

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: CMS Automation API - Article Parsing
  version: 1.0.0
  description: API endpoints for article structured parsing feature

servers:
  - url: https://api.cms-automation.example.com/api/v1
    description: Production server
  - url: http://localhost:8000/api/v1
    description: Local development server

paths:
  /worklist/{item_id}:
    get:
      summary: Get worklist item detail (extended with parsing fields)
      operationId: getWorklistItemDetail
      tags:
        - Worklist
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
          description: Worklist item ID
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WorklistItemDetail'
        '404':
          description: Worklist item not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /worklist/{item_id}/confirm-parsing:
    post:
      summary: Confirm parsing results
      operationId: confirmParsing
      tags:
        - Parsing
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ParsingConfirmationRequest'
      responses:
        '200':
          description: Parsing confirmed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ParsingConfirmationResponse'
        '400':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /worklist/{item_id}/parsing-fields:
    patch:
      summary: Update parsing fields
      operationId: updateParsingFields
      tags:
        - Parsing
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ParsingFieldsUpdateRequest'
      responses:
        '200':
          description: Fields updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ParsingFieldsUpdateResponse'

  /worklist/parsing-statistics:
    get:
      summary: Get parsing statistics
      operationId: getParsingStatistics
      tags:
        - Parsing
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ParsingStatistics'

components:
  schemas:
    WorklistItemDetail:
      type: object
      properties:
        id:
          type: integer
        article_id:
          type: integer
        status:
          type: string
        title_prefix:
          type: string
          nullable: true
        title_main:
          type: string
        title_suffix:
          type: string
          nullable: true
        author_line:
          type: string
          nullable: true
        author_name:
          type: string
          nullable: true
        body_html:
          type: string
        meta_description:
          type: string
          nullable: true
        seo_keywords:
          type: array
          items:
            type: string
        tags:
          type: array
          items:
            type: string
        images:
          type: array
          items:
            $ref: '#/components/schemas/ArticleImage'
        parsing_confirmed:
          type: boolean
        parsing_confirmed_at:
          type: string
          format: date-time
          nullable: true
        parsing_confirmed_by:
          type: string
          nullable: true
        parsing_feedback:
          type: string
          nullable: true

    ArticleImage:
      type: object
      properties:
        id:
          type: integer
        preview_path:
          type: string
          nullable: true
        source_path:
          type: string
        source_url:
          type: string
        caption:
          type: string
          nullable: true
        position:
          type: integer
        metadata:
          $ref: '#/components/schemas/ImageMetadata'

    ImageMetadata:
      type: object
      properties:
        width:
          type: integer
        height:
          type: integer
        aspect_ratio:
          type: string
        file_size_bytes:
          type: integer
        mime_type:
          type: string
        format:
          type: string
        color_mode:
          type: string
        has_transparency:
          type: boolean
        exif_date:
          type: string
          format: date-time
          nullable: true
        download_timestamp:
          type: string
          format: date-time

    ParsingConfirmationRequest:
      type: object
      required:
        - parsing_confirmed
      properties:
        parsing_confirmed:
          type: boolean
        parsing_feedback:
          type: string
          maxLength: 1000
        image_reviews:
          type: array
          maxItems: 100
          items:
            $ref: '#/components/schemas/ImageReview'

    ImageReview:
      type: object
      required:
        - article_image_id
        - action
      properties:
        article_image_id:
          type: integer
        action:
          type: string
          enum: [keep, remove, replace_caption, replace_source]
        new_caption:
          type: string
          maxLength: 500
        new_source_url:
          type: string
          format: uri
        reviewer_notes:
          type: string
          maxLength: 1000

    ParsingConfirmationResponse:
      type: object
      properties:
        success:
          type: boolean
        worklist_item_id:
          type: integer
        article_id:
          type: integer
        parsing_confirmed_at:
          type: string
          format: date-time
        parsing_confirmed_by:
          type: string
        image_reviews_created:
          type: integer

    ParsingFieldsUpdateRequest:
      type: object
      properties:
        title_prefix:
          type: string
          maxLength: 200
          nullable: true
        title_main:
          type: string
          minLength: 5
          maxLength: 500
        title_suffix:
          type: string
          maxLength: 200
          nullable: true
        author_name:
          type: string
          maxLength: 100
          nullable: true
        meta_description:
          type: string
          maxLength: 1000
          nullable: true
        seo_keywords:
          type: array
          maxItems: 20
          items:
            type: string
            maxLength: 50
        tags:
          type: array
          maxItems: 30
          items:
            type: string
            maxLength: 30

    ParsingFieldsUpdateResponse:
      type: object
      properties:
        success:
          type: boolean
        worklist_item_id:
          type: integer
        article_id:
          type: integer
        updated_fields:
          type: array
          items:
            type: string
        updated_at:
          type: string
          format: date-time

    ParsingStatistics:
      type: object
      properties:
        total_articles_parsed:
          type: integer
        parsing_confirmed_count:
          type: integer
        parsing_pending_count:
          type: integer
        average_parsing_time_seconds:
          type: number
        median_parsing_time_seconds:
          type: number
        p95_parsing_time_seconds:
          type: number
        image_success_rate:
          type: number
        total_images_processed:
          type: integer
        images_with_complete_metadata:
          type: integer
        accuracy_metrics:
          type: object
          properties:
            title_accuracy:
              type: number
            author_accuracy:
              type: number
            image_detection_accuracy:
              type: number
            meta_extraction_accuracy:
              type: number
        last_updated:
          type: string
          format: date-time

    Error:
      type: object
      properties:
        detail:
          type: string
        error_code:
          type: string
        timestamp:
          type: string
          format: date-time

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - BearerAuth: []
```

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-08 | Initial API design for article parsing feature |

---

**Document Owner**: API Team
**Review Cycle**: Before implementation
**Contact**: api-team@example.com

---

**Status**: ✅ API documentation complete, ready for implementation
