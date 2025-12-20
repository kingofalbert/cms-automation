# Phase 13: Enhanced Image Review

> **Version**: 1.1
> **Date**: 2025-12-20
> **Status**: Implemented

---

## Overview

Phase 13 enhances the image review functionality in the Article Parsing modal with:
1. Comprehensive metadata display
2. Epoch Times standard comparison
3. Issue highlighting
4. **Featured Image Detection** - Automatic detection of 置頂 (featured) images vs 正文 (content) images

## Key Feature: Featured Image Detection (置頂圖片)

### Business Rules

A featured image is detected based on the following rules (in priority order):

1. **Manual Override**: User explicitly marks an image as featured (`force_featured=true`)
2. **Caption Keywords**: Caption contains 置頂, 封面, 首圖, 頭圖, 特色圖片, 主圖 (primary) or featured, cover, hero (secondary)
3. **Position Detection**: Image appears before the first paragraph (position=0 with no content before)

### Detection Methods

| Method | Confidence | Description |
|--------|------------|-------------|
| `manual` | 100% | User manually set as featured |
| `caption_keyword` | 95-98% | Caption contains 置頂/封面 etc. |
| `position_before_body` | 85% | First image before content starts |
| `position_legacy` | N/A | Migrated from old position=0 logic |
| `none` | N/A | Not a featured image |

### Important Constraint

**Only ONE image per article can be featured.** If multiple images qualify, the first one detected becomes the featured image.

## Features Implemented

### 1. Original Link Display
- Shows original source URLs (Google Drive, etc.) for each image
- Clickable external links with proper security attributes
- Truncated display for long URLs with full URL on hover

### 2. Caption and Alt Text Display
- **Caption (圖說)**: Shows image caption extracted from document
- **Alt Text**: Shows accessibility text for SEO and screen readers
- Displays "未設置" placeholder when not configured

### 3. Resolution Detection and Comparison
- Real-time image resolution display (width × height pixels)
- Aspect ratio calculation and display
- Comparison against Epoch Times standards:
  - **Featured Image**: Minimum 1200×630 pixels
  - **Content Image**: Minimum 800×400 pixels

### 4. File Size Validation
- File size display in KB/MB format
- Validation against Epoch Times standards:
  - **Featured Image**: Maximum 500KB
  - **Content Image**: Maximum 300KB

### 5. Format Validation
- Image format detection (JPEG, PNG, WebP, etc.)
- Validation against supported formats
- Warning for unsupported formats

### 6. Issue Highlighting
- **Red border/background**: Critical issues requiring attention
- **Yellow border/background**: Warnings suggesting optimization
- **Green badge**: Meets all standards
- Detailed issue summary at bottom of each image card

## Technical Implementation

### Backend Changes

#### 1. Database Migration

**File**: `backend/migrations/manual_sql/20251220_add_featured_image_fields.sql`

```sql
-- Add new columns for featured image detection
ALTER TABLE article_images ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE article_images ADD COLUMN IF NOT EXISTS image_type VARCHAR(20) NOT NULL DEFAULT 'content';
ALTER TABLE article_images ADD COLUMN IF NOT EXISTS detection_method VARCHAR(50);

-- Constraint for valid image types
ALTER TABLE article_images ADD CONSTRAINT article_images_valid_image_type
CHECK (image_type IN ('featured', 'content', 'inline'));

-- Index for efficient featured image lookups
CREATE INDEX IF NOT EXISTS idx_article_images_featured
ON article_images(article_id, is_featured) WHERE is_featured = TRUE;
```

#### 2. FeaturedImageDetector Service

**File**: `backend/src/services/parser/featured_image_detector.py`

```python
class FeaturedImageDetector:
    """Service for detecting featured (置頂) images."""

    FEATURED_KEYWORDS_PRIMARY = ["置頂", "封面", "首圖", "頭圖", "特色圖片", "主圖"]
    FEATURED_KEYWORDS_SECONDARY = ["featured", "cover", "hero", "main image", "banner"]

    def detect(
        self,
        caption: str | None = None,
        position: int = 0,
        has_content_before: bool = False,
        force_featured: bool = False,
    ) -> FeaturedDetectionResult:
        """Detect if an image should be marked as featured."""
        # Rule 0: Manual override
        # Rule 1: Check caption keywords
        # Rule 2: Check position (before body)
        # Default: Content image

    def detect_batch(
        self,
        images: list[dict],
        first_paragraph_position: int | None = None,
    ) -> list[FeaturedDetectionResult]:
        """Detect featured status for batch, ensuring only one featured."""
```

#### 3. API Schema Updates

**File**: `backend/src/api/schemas/article.py`
```python
class ArticleImageResponse(BaseSchema):
    id: int
    article_id: int
    preview_path: str | None
    source_path: str | None
    source_url: str | None  # Original Google Drive URL
    caption: str | None     # Image caption (圖說)
    alt_text: str | None    # Alt text for SEO
    description: str | None # WordPress media library description
    position: int

    # Phase 13: Featured image detection fields
    is_featured: bool = False           # Whether this is the featured image
    image_type: str = "content"         # featured / content / inline
    detection_method: str | None = None # How featured status was detected

    image_metadata: dict
    created_at: datetime | None
    updated_at: datetime | None
```

**File**: `backend/src/api/routes/worklist_routes.py`
- Added `is_featured`, `image_type`, and `detection_method` fields to ArticleImageResponse serialization

### Frontend Changes

**File**: `frontend/src/components/ArticleReview/ImageReviewSection.tsx`

New component structure:
- `ImageInfoCard`: Displays comprehensive image information
- `StatusBadge`: Shows pass/warning/fail status with icons
- **`FeaturedBadge`**: Shows featured status with detection method tooltip
- `ImageType` and `DetectionMethod` TypeScript types
- Updated `ArticleImageData` interface with `is_featured`, `image_type`, `detection_method`
- Image separation logic using `is_featured` field (with fallback to position for legacy data)

#### FeaturedBadge Component

```tsx
const FeaturedBadge: React.FC<{ detectionMethod?: DetectionMethod }> = ({ detectionMethod }) => {
  const getDetectionLabel = () => {
    switch (detectionMethod) {
      case 'caption_keyword': return { label: '圖說標記', tooltip: 'Caption 包含「置頂」等關鍵字' };
      case 'position_before_body': return { label: '位置檢測', tooltip: '圖片位於正文之前' };
      case 'manual': return { label: '手動設置', tooltip: '由用戶手動標記為置頂' };
      case 'position_legacy': return { label: '舊版遷移', tooltip: '從舊版 position=0 遷移' };
      default: return { label: '自動檢測', tooltip: '系統自動識別' };
    }
  };

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-800 border border-amber-200">
      ⭐ 置頂圖片 <span className="text-[10px] text-amber-600">({label})</span>
    </span>
  );
};
```

#### Image Separation Logic

```tsx
// Use is_featured field for separation (fallback to position for legacy data)
const featuredImageData = articleImages.find(
  (img) => img.is_featured === true || (img.is_featured === undefined && img.position === 0)
);

const contentImagesData = articleImages
  .filter((img) => !img.is_featured && (img.is_featured !== undefined || img.position > 0))
  .sort((a, b) => a.position - b.position);
```

## Epoch Times Image Standards

| Attribute | Featured Image | Content Image |
|-----------|---------------|---------------|
| Min Width | 1200px | 800px |
| Min Height | 630px | 400px |
| Max File Size | 500KB | 300KB |
| Supported Formats | JPEG, PNG, WebP | JPEG, PNG, WebP, GIF |

## UI Components

### ImageInfoCard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ [FileImage] 特色圖片 [符合標準/需修正/建議優化] [▲/▼] [X]   │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐  ┌──────────────────────────────────┐ │
│ │                  │  │ 🔗 原始鏈接                       │ │
│ │   [Image]        │  │    https://drive.google.com/...  │ │
│ │   1200 × 630 px  │  │                                  │ │
│ │   (16:9)         │  │ 📝 圖說 (Caption)                │ │
│ │                  │  │    圖片說明文字                   │ │
│ └──────────────────┘  │                                  │ │
│                       │ ℹ️ Alt Text (無障礙)             │ │
│                       │    Accessibility description     │ │
│                       └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 📏 大紀元標準對比                                           │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ 解析度      │ │ 文件大小    │ │ 格式        │            │
│ │ 1200×630    │ │ 245.3 KB    │ │ JPEG        │            │
│ │ ✓ 符合標準  │ │ ✓ 符合標準  │ │ ✓ 格式支持  │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Testing

### Unit Tests

**File**: `backend/tests/unit/test_featured_image_detector.py`

35 test cases covering:
- Caption keyword detection (primary: 置頂, 封面, 首圖, etc.)
- Caption keyword detection (secondary: featured, cover, hero)
- Caption pattern matching (置頂圖, 圖說：置頂)
- Position-based detection (before body content)
- Manual override with force_featured
- HTML context detection (class="featured-image")
- Batch detection with single featured constraint
- Edge cases (empty caption, case sensitivity)
- Confidence levels for different detection methods
- Serialization tests

```bash
# Run tests
cd backend && PYTHONPATH=. poetry run pytest tests/unit/test_featured_image_detector.py -v
```

### Visual Regression Tests
- Image card rendering with all metadata
- Issue highlighting colors
- Collapsed/expanded states
- Multiple images display
- FeaturedBadge component rendering
- 置頂 vs 正文 image separation

## Files Modified

### Backend
- `backend/migrations/manual_sql/20251220_add_featured_image_fields.sql` - **NEW** Database migration
- `backend/src/models/article_image.py` - Added is_featured, image_type, detection_method fields
- `backend/src/services/parser/featured_image_detector.py` - **NEW** Detection service
- `backend/src/services/parser/models.py` - Updated ParsedImage with new fields
- `backend/src/services/parser/article_parser.py` - Integrated FeaturedImageDetector
- `backend/src/api/schemas/article.py` - Added new fields to ArticleImageResponse
- `backend/src/api/routes/worklist_routes.py` - Include new fields in response
- `backend/tests/unit/test_featured_image_detector.py` - **NEW** Unit tests

### Frontend
- `frontend/src/components/ArticleReview/ImageReviewSection.tsx` - Added FeaturedBadge, ImageType, DetectionMethod types, updated separation logic
- `frontend/src/components/ArticleReview/ParsingReviewPanel.tsx` - Pass articleImages prop

## Deployment

```bash
# Backend (if schema changes require redeployment)
cd backend && poetry run alembic upgrade head

# Frontend
cd frontend && npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/
```

## Dependencies

- No new npm packages required
- Uses existing Lucide React icons
- Leverages existing Tailwind CSS classes

## Related Documentation

- [Preview WYSIWYG Design Spec](../../frontend/docs/PREVIEW_WYSIWYG_DESIGN_SPEC.md)
- [User Experience Analysis](../../用户体验完整分析.md)

---

**Last Updated**: 2025-12-20
