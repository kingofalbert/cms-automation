# Article Parsing Technical Analysis & Implementation Plan

**Document Version**: 1.0
**Created**: 2025-11-08
**Status**: Design Phase
**Feature ID**: Article Structured Parsing

---

## 1. Executive Summary

### 1.1 Overview

This document provides a comprehensive technical analysis and implementation plan for the **Article Structured Parsing** feature. This feature transforms the current single-blob Google Doc ingestion into a normalized, structured data model that separates titles, authors, body content, images, and SEO metadata.

### 1.2 Business Value

- **✅ Improved Data Quality**: Structured data enables better validation and quality control
- **✅ Enhanced User Experience**: Step-by-step parsing confirmation reduces errors
- **✅ Better SEO Control**: Explicit meta fields improve search engine optimization
- **✅ Image Management**: Proper tracking of source assets with technical specifications
- **✅ Audit Trail**: Parsing confirmation state creates accountability

### 1.3 Key Changes

| Area | Current State | Target State |
|------|--------------|--------------|
| **Title Storage** | Single `title` field | `title_prefix`, `title_main`, `title_suffix` |
| **Author** | Embedded in content | Extracted `author_line`, `author_name` |
| **Body** | Full HTML with everything | Cleaned `body_html` (no headers/meta) |
| **Images** | Inline references only | Separate `article_images` table with specs |
| **SEO Fields** | Embedded or missing | Extracted `meta_description`, `seo_keywords`, `tags` |
| **Review Process** | Single-step review | Multi-step with parsing confirmation |

---

## 2. Requirements Breakdown by Technical Layer

### 2.1 Database Layer Requirements

#### 2.1.1 Schema Changes to `articles` Table

**New Columns**:
```sql
ALTER TABLE articles ADD COLUMN title_prefix VARCHAR(200);
ALTER TABLE articles ADD COLUMN title_main VARCHAR(500) NOT NULL;
ALTER TABLE articles ADD COLUMN title_suffix VARCHAR(200);
ALTER TABLE articles ADD COLUMN author_line VARCHAR(300);
ALTER TABLE articles ADD COLUMN author_name VARCHAR(100);
ALTER TABLE articles ADD COLUMN body_html TEXT;
ALTER TABLE articles ADD COLUMN meta_description TEXT;
ALTER TABLE articles ADD COLUMN seo_keywords TEXT[];  -- PostgreSQL array
ALTER TABLE articles ADD COLUMN tags TEXT[];
```

**Migration Considerations**:
- Existing articles: Backfill `title_main` from current `title` field
- Set `body_html` = `original_content` for legacy articles
- Add `is_legacy_parsed` BOOLEAN flag to track migration status

#### 2.1.2 New Table: `article_images`

```sql
CREATE TABLE article_images (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    preview_path VARCHAR(500),           -- Preview/thumbnail image path
    source_path VARCHAR(500),            -- Downloaded high-res source path
    source_url VARCHAR(1000),            -- Original "點此下載" URL
    caption TEXT,                        -- Image caption from doc
    position INTEGER NOT NULL,           -- Paragraph index (0-based)
    metadata JSONB,                      -- Technical specs
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT positive_position CHECK (position >= 0)
);

CREATE INDEX idx_article_images_article_id ON article_images(article_id);
CREATE INDEX idx_article_images_position ON article_images(article_id, position);
```

**JSONB `metadata` Structure**:
```json
{
  "width": 1920,
  "height": 1080,
  "aspect_ratio": "16:9",
  "file_size_bytes": 2458624,
  "mime_type": "image/jpeg",
  "exif_date": "2025-11-08T10:30:00Z",
  "format": "JPEG",
  "color_mode": "RGB",
  "has_transparency": false,
  "download_timestamp": "2025-11-08T12:00:00Z"
}
```

#### 2.1.3 Parsing Confirmation Tracking

**New Columns on `worklist_items` or `proofreading_reviews`**:
```sql
ALTER TABLE worklist_items ADD COLUMN parsing_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE worklist_items ADD COLUMN parsing_confirmed_at TIMESTAMP;
ALTER TABLE worklist_items ADD COLUMN parsing_confirmed_by VARCHAR(100);
ALTER TABLE worklist_items ADD COLUMN parsing_feedback TEXT;
```

**New Table: `article_image_reviews`** (for image-level feedback):
```sql
CREATE TABLE article_image_reviews (
    id SERIAL PRIMARY KEY,
    article_image_id INTEGER NOT NULL REFERENCES article_images(id) ON DELETE CASCADE,
    worklist_item_id INTEGER NOT NULL REFERENCES worklist_items(id) ON DELETE CASCADE,
    action VARCHAR(20) CHECK (action IN ('keep', 'remove', 'replace_caption', 'replace_source')),
    new_caption TEXT,
    new_source_url VARCHAR(1000),
    reviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_article_image_reviews_article_image ON article_image_reviews(article_image_id);
CREATE INDEX idx_article_image_reviews_worklist_item ON article_image_reviews(worklist_item_id);
```

---

### 2.2 Backend Layer Requirements

#### 2.2.1 New Service: `ArticleParserService`

**Location**: `backend/src/services/parser/article_parser.py`

**Responsibilities**:
1. Parse Google Doc HTML/Markdown into structured components
2. Use AI (Claude 4.5 Sonnet) to interpret document structure
3. Download and process images
4. Extract and clean body HTML
5. Identify and extract meta/SEO blocks

**Core Methods**:
```python
class ArticleParserService:
    def __init__(self, llm_client: Anthropic, storage_service: StorageService):
        self.llm = llm_client
        self.storage = storage_service

    async def parse_document(self, raw_html: str, article_id: int) -> ParsedArticle:
        """
        Main entry point: orchestrates all parsing steps
        Returns: ParsedArticle dataclass with all structured fields
        """
        pass

    async def _parse_header(self, dom: BeautifulSoup) -> HeaderFields:
        """
        AI-driven: Extract title_prefix, title_main, title_suffix
        Fallback: Regex-based separator detection (｜, —, ：)
        """
        pass

    async def _extract_author(self, dom: BeautifulSoup) -> AuthorFields:
        """
        AI-driven: Detect "文／XXX" patterns
        Returns: author_line (raw) and author_name (cleaned)
        """
        pass

    async def _extract_images(self, dom: BeautifulSoup, article_id: int) -> List[ImageRecord]:
        """
        1. Identify image blocks (preview + caption + source link)
        2. Download high-res source via source_url
        3. Extract image specs (PIL: width, height, format, EXIF)
        4. Record position (paragraph index before image)
        5. Replace inline nodes with placeholders
        Returns: List of ImageRecord with metadata
        """
        pass

    async def _extract_meta_seo(self, dom: BeautifulSoup) -> MetaSEOFields:
        """
        AI-driven: Detect blocks labeled "Meta Description：", "關鍵詞：", "Tags："
        Strip from DOM after extraction
        Returns: meta_description, seo_keywords[], tags[]
        """
        pass

    async def _clean_body_html(self, dom: BeautifulSoup) -> str:
        """
        Remove extracted elements (header, author, images, meta)
        Sanitize remaining HTML (bleach whitelist)
        Preserve semantic tags: H1, H2, <p>, <ul>, <ol>, <strong>, <em>
        Returns: Clean body_html string
        """
        pass
```

**Data Classes**:
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HeaderFields:
    title_prefix: Optional[str]
    title_main: str
    title_suffix: Optional[str]

@dataclass
class AuthorFields:
    author_line: Optional[str]
    author_name: Optional[str]

@dataclass
class ImageRecord:
    preview_path: Optional[str]
    source_path: str
    source_url: str
    caption: Optional[str]
    position: int  # Paragraph index
    metadata: dict  # Technical specs

@dataclass
class MetaSEOFields:
    meta_description: Optional[str]
    seo_keywords: List[str]
    tags: List[str]

@dataclass
class ParsedArticle:
    header: HeaderFields
    author: AuthorFields
    body_html: str
    images: List[ImageRecord]
    meta_seo: MetaSEOFields
```

#### 2.2.2 Image Processing Pipeline

**New Service**: `backend/src/services/media/image_processor.py`

```python
class ImageProcessor:
    async def download_and_process(self, source_url: str, article_id: int) -> ProcessedImage:
        """
        1. Download image from source_url
        2. Extract technical specs (PIL/Pillow):
           - Dimensions (width x height)
           - Aspect ratio
           - File size
           - MIME type
           - EXIF data (date, camera info)
        3. Store in media backend (Google Drive or Supabase)
        4. Return ProcessedImage with paths and metadata
        """
        pass

    def extract_specs(self, image_bytes: bytes) -> ImageMetadata:
        """
        Use PIL to extract:
        - Image.size (width, height)
        - Image.format (JPEG, PNG, etc.)
        - Image.mode (RGB, RGBA, etc.)
        - EXIF tags (DateTimeOriginal, etc.)
        """
        from PIL import Image, ExifTags
        import io

        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif() if hasattr(img, '_getexif') else {}

        return ImageMetadata(
            width=img.width,
            height=img.height,
            aspect_ratio=f"{img.width}:{img.height}",  # Or calculate GCD
            file_size_bytes=len(image_bytes),
            mime_type=f"image/{img.format.lower()}",
            format=img.format,
            color_mode=img.mode,
            exif_date=exif_data.get(ExifTags.TAGS.get('DateTimeOriginal'))
        )
```

#### 2.2.3 API Updates

**Extended `/v1/worklist/:id` Response**:
```json
{
  "id": 123,
  "title_prefix": "專題報導",
  "title_main": "AI驅動的內容管理系統",
  "title_suffix": "未來趨勢分析",
  "author_line": "文／張三",
  "author_name": "張三",
  "body_html": "<h2>引言</h2><p>內容...</p>",
  "meta_description": "探討AI如何改變內容管理...",
  "seo_keywords": ["AI", "CMS", "自動化"],
  "tags": ["技術", "趨勢"],
  "images": [
    {
      "id": 456,
      "preview_path": "/media/articles/123/preview_001.jpg",
      "source_path": "/media/articles/123/source_001.jpg",
      "source_url": "https://drive.google.com/...",
      "caption": "圖1：系統架構圖",
      "position": 3,
      "metadata": {
        "width": 1920,
        "height": 1080,
        "file_size_bytes": 2458624,
        "mime_type": "image/jpeg"
      }
    }
  ],
  "parsing_confirmed": false,
  "parsing_confirmed_at": null,
  "parsing_confirmed_by": null
}
```

**New API Endpoint: Save Parsing Confirmation**:
```
POST /v1/worklist/:id/confirm-parsing
Request Body:
{
  "parsing_confirmed": true,
  "parsing_feedback": "All fields look correct",
  "image_reviews": [
    {
      "article_image_id": 456,
      "action": "keep"
    }
  ]
}

Response:
{
  "success": true,
  "worklist_item_id": 123,
  "parsing_confirmed_at": "2025-11-08T12:30:00Z"
}
```

---

### 2.3 Frontend Layer Requirements

#### 2.3.1 New Component: Proofreading Review Step 1 UI

**Component Hierarchy**:
```
ProofreadingReviewPage
├── StepIndicator (Step 1: 解析確認, Step 2: 正文校對)
├── ParsingConfirmationStep (NEW)
│   ├── StructuredHeadersCard
│   │   ├── TitlePrefixField (editable)
│   │   ├── TitleMainField (editable)
│   │   └── TitleSuffixField (editable)
│   ├── AuthorInfoCard
│   │   ├── AuthorLineDisplay (raw)
│   │   └── AuthorNameDisplay (cleaned, editable)
│   ├── ImageGalleryCard
│   │   ├── ImagePreviewGrid
│   │   │   └── ImagePreviewItem (each image)
│   │   │       ├── PreviewThumbnail
│   │   │       ├── CaptionDisplay (editable)
│   │   │       ├── SourceLinkButton
│   │   │       └── SpecsTable (width, height, size, MIME)
│   │   └── ImageReviewActions (keep, remove, replace)
│   ├── MetaSEOCard
│   │   ├── MetaDescriptionField (editable)
│   │   ├── KeywordsTagInput (editable)
│   │   └── TagsTagInput (editable)
│   ├── BodyHTMLPreviewCard
│   │   └── HTMLRenderer (read-only preview)
│   └── ConfirmationActions
│       ├── ConfirmButton (saves & unlocks Step 2)
│       └── NeedFixToggle (blocks Step 2)
└── ContentProofreadingStep (Step 2, existing)
    └── ... (正文校對 UI)
```

#### 2.3.2 UI State Management

**Zustand Store**: `useParsingConfirmationStore`
```typescript
interface ParsingConfirmationState {
  // Parsed data
  titlePrefix: string | null;
  titleMain: string;
  titleSuffix: string | null;
  authorLine: string | null;
  authorName: string | null;
  bodyHtml: string;
  metaDescription: string | null;
  seoKeywords: string[];
  tags: string[];
  images: ArticleImage[];

  // Confirmation state
  isConfirmed: boolean;
  confirmedAt: string | null;
  confirmedBy: string | null;
  feedback: string;
  imageReviews: ImageReview[];

  // Actions
  updateTitleFields: (fields: Partial<TitleFields>) => void;
  updateAuthor: (author: Partial<AuthorFields>) => void;
  updateMetaSEO: (meta: Partial<MetaSEOFields>) => void;
  addImageReview: (review: ImageReview) => void;
  confirmParsing: () => Promise<void>;
}
```

#### 2.3.3 Validation & Business Rules

**Frontend Validation**:
```typescript
const validateParsingFields = (state: ParsingConfirmationState): ValidationErrors => {
  const errors: ValidationErrors = {};

  // Title main is required
  if (!state.titleMain || state.titleMain.trim().length < 5) {
    errors.titleMain = "主標題至少需要 5 個字符";
  }

  // If title suffix exists, title prefix should exist (consistency check)
  if (state.titleSuffix && !state.titlePrefix) {
    errors.titlePrefix = "副標題存在時，建議填寫前標題";
  }

  // At least one image should have valid specs
  const imagesWithSpecs = state.images.filter(img =>
    img.metadata?.width && img.metadata?.height
  );
  if (state.images.length > 0 && imagesWithSpecs.length === 0) {
    errors.images = "至少一張圖片需要完整的規格資訊";
  }

  // Meta description recommended length
  if (state.metaDescription && state.metaDescription.length > 160) {
    errors.metaDescription = "Meta 描述建議不超過 160 字符 (當前: " + state.metaDescription.length + ")";
  }

  return errors;
};
```

**Step 2 Blocking Logic**:
```typescript
const canProceedToStep2 = (state: ParsingConfirmationState): boolean => {
  return state.isConfirmed === true;
};

// UI Component
{step === 2 && !canProceedToStep2(parsingState) && (
  <Alert variant="warning">
    <AlertIcon />
    <AlertTitle>請先完成解析確認</AlertTitle>
    <AlertDescription>
      您必須在 Step 1 確認解析結果後才能進入正文校對步驟。
      <Button onClick={() => setStep(1)}>返回 Step 1</Button>
    </AlertDescription>
  </Alert>
)}
```

#### 2.3.4 Image Specs Display Component

**Component**: `ImageSpecsTable.tsx`
```tsx
interface ImageSpecsTableProps {
  metadata: ImageMetadata;
}

const ImageSpecsTable: React.FC<ImageSpecsTableProps> = ({ metadata }) => {
  // Highlight values outside publishing tolerances
  const isWidthValid = metadata.width >= 800 && metadata.width <= 3000;
  const isAspectRatioValid = ['16:9', '4:3', '1:1'].includes(metadata.aspect_ratio);

  return (
    <Table size="sm">
      <Tbody>
        <Tr>
          <Td>寬度</Td>
          <Td className={!isWidthValid ? 'text-red-600' : ''}>
            {metadata.width}px
            {!isWidthValid && <WarningIcon ml={2} />}
          </Td>
        </Tr>
        <Tr>
          <Td>高度</Td>
          <Td>{metadata.height}px</Td>
        </Tr>
        <Tr>
          <Td>長寬比</Td>
          <Td className={!isAspectRatioValid ? 'text-amber-600' : ''}>
            {metadata.aspect_ratio}
          </Td>
        </Tr>
        <Tr>
          <Td>文件大小</Td>
          <Td>{formatBytes(metadata.file_size_bytes)}</Td>
        </Tr>
        <Tr>
          <Td>格式</Td>
          <Td>{metadata.mime_type}</Td>
        </Tr>
        {metadata.exif_date && (
          <Tr>
            <Td>拍攝日期</Td>
            <Td>{formatDate(metadata.exif_date)}</Td>
          </Tr>
        )}
      </Tbody>
    </Table>
  );
};
```

---

### 2.4 Integration Requirements

#### 2.4.1 Google Drive Sync Integration

**Modified Flow**:
```
Google Drive Scanner discovers new doc
    ↓
Download raw HTML/Markdown
    ↓
**NEW: Call ArticleParserService.parse_document()**
    ↓
Create article record with structured fields
    ↓
Create article_images records
    ↓
Set status = 'pending' (awaiting parsing confirmation)
    ↓
Worklist shows article with "解析確認" required
```

**Code Integration Point**: `backend/src/services/google_drive/sync_service.py`
```python
async def process_new_document(self, doc_id: str):
    # ... existing download logic ...
    raw_html = await self.download_document_content(doc_id)

    # NEW: Parse document structure
    parser = ArticleParserService(self.llm_client, self.storage_service)
    parsed = await parser.parse_document(raw_html, article_id=None)

    # Create article with structured fields
    article = await self.db.articles.create({
        'title_prefix': parsed.header.title_prefix,
        'title_main': parsed.header.title_main,
        'title_suffix': parsed.header.title_suffix,
        'author_line': parsed.author.author_line,
        'author_name': parsed.author.author_name,
        'body_html': parsed.body_html,
        'meta_description': parsed.meta_seo.meta_description,
        'seo_keywords': parsed.meta_seo.seo_keywords,
        'tags': parsed.meta_seo.tags,
        'original_content': raw_html,  # Keep raw for reference
        'current_status': 'pending',
        'google_drive_doc_id': doc_id
    })

    # Create image records
    for img in parsed.images:
        await self.db.article_images.create({
            'article_id': article.id,
            'preview_path': img.preview_path,
            'source_path': img.source_path,
            'source_url': img.source_url,
            'caption': img.caption,
            'position': img.position,
            'metadata': img.metadata
        })

    return article
```

#### 2.4.2 Proofreading Pipeline Integration

**Step 1 → Step 2 Transition**:
```python
# API Route: POST /v1/worklist/:id/confirm-parsing
@router.post("/{worklist_id}/confirm-parsing")
async def confirm_parsing(
    worklist_id: int,
    confirmation: ParsingConfirmation,
    current_user: User = Depends(get_current_user)
):
    # Update confirmation state
    await db.worklist_items.update(
        worklist_id,
        {
            'parsing_confirmed': True,
            'parsing_confirmed_at': datetime.utcnow(),
            'parsing_confirmed_by': current_user.id,
            'parsing_feedback': confirmation.feedback
        }
    )

    # Save image reviews
    for review in confirmation.image_reviews:
        await db.article_image_reviews.create({
            'article_image_id': review.article_image_id,
            'worklist_item_id': worklist_id,
            'action': review.action,
            'new_caption': review.new_caption,
            'new_source_url': review.new_source_url,
            'reviewer_notes': review.notes
        })

    # If all confirmed, transition to 'under_review' (ready for Step 2)
    article = await db.articles.get_by_worklist(worklist_id)
    await update_article_status(article.id, 'under_review', changed_by=current_user.id)

    return {"success": True, "worklist_item_id": worklist_id}
```

---

## 3. Implementation Phases

### Phase 1: Database Schema (Week 1, 16 hours)

**Tasks**:
- [ ] T-PARSE-1.1: Design final schema for `articles` table extensions (4h)
- [ ] T-PARSE-1.2: Design `article_images` table with metadata JSONB (4h)
- [ ] T-PARSE-1.3: Design `article_image_reviews` table (2h)
- [ ] T-PARSE-1.4: Create Alembic migration script (4h)
- [ ] T-PARSE-1.5: Test migration on dev database (2h)

**Deliverables**:
- ✅ Migration script: `migrations/versions/20251108_article_parsing.py`
- ✅ Updated SQLAlchemy models in `backend/src/models/`

### Phase 2: Backend Parsing Service (Week 2-3, 40 hours)

**Tasks**:
- [ ] T-PARSE-2.1: Implement `ArticleParserService` skeleton (6h)
- [ ] T-PARSE-2.2: Implement `_parse_header()` with AI + fallback (8h)
- [ ] T-PARSE-2.3: Implement `_extract_author()` with AI (4h)
- [ ] T-PARSE-2.4: Implement `_extract_images()` with download (10h)
- [ ] T-PARSE-2.5: Implement `ImageProcessor` for specs extraction (6h)
- [ ] T-PARSE-2.6: Implement `_extract_meta_seo()` with AI (4h)
- [ ] T-PARSE-2.7: Implement `_clean_body_html()` sanitization (4h)
- [ ] T-PARSE-2.8: Unit tests for all parsing methods (8h)

**Deliverables**:
- ✅ `backend/src/services/parser/article_parser.py`
- ✅ `backend/src/services/media/image_processor.py`
- ✅ Unit tests with 85%+ coverage

### Phase 3: API Updates (Week 3, 12 hours)

**Tasks**:
- [ ] T-PARSE-3.1: Extend `/v1/worklist/:id` API response (4h)
- [ ] T-PARSE-3.2: Create `POST /v1/worklist/:id/confirm-parsing` endpoint (4h)
- [ ] T-PARSE-3.3: Update Pydantic models for new fields (2h)
- [ ] T-PARSE-3.4: Integration tests for API endpoints (4h)

**Deliverables**:
- ✅ Updated API routes in `backend/src/api/routes/worklist.py`
- ✅ API integration tests

### Phase 4: Frontend UI (Week 4-5, 48 hours)

**Tasks**:
- [ ] T-PARSE-4.1: Create Step Indicator component (4h)
- [ ] T-PARSE-4.2: Build StructuredHeadersCard component (6h)
- [ ] T-PARSE-4.3: Build AuthorInfoCard component (4h)
- [ ] T-PARSE-4.4: Build ImageGalleryCard with specs table (12h)
- [ ] T-PARSE-4.5: Build MetaSEOCard component (6h)
- [ ] T-PARSE-4.6: Build BodyHTMLPreviewCard (4h)
- [ ] T-PARSE-4.7: Implement confirmation actions & state (6h)
- [ ] T-PARSE-4.8: Add Step 2 blocking logic (4h)
- [ ] T-PARSE-4.9: E2E tests for parsing workflow (8h)

**Deliverables**:
- ✅ `frontend/src/components/Proofreading/ParsingConfirmationStep.tsx`
- ✅ Zustand store: `useParsingConfirmationStore`
- ✅ E2E test: `frontend/e2e/parsing-confirmation.spec.ts`

### Phase 5: Integration & Testing (Week 6, 24 hours)

**Tasks**:
- [ ] T-PARSE-5.1: Integrate parser into Google Drive sync (6h)
- [ ] T-PARSE-5.2: End-to-end workflow test (Google Doc → Parsed → Confirmed) (8h)
- [ ] T-PARSE-5.3: Performance testing (parsing 100 articles) (4h)
- [ ] T-PARSE-5.4: Bug fixes and edge cases (6h)

**Deliverables**:
- ✅ Full workflow operational
- ✅ Performance benchmarks
- ✅ Bug fixes log

---

## 4. Open Decisions & Risks

### 4.1 Open Decisions

| Decision | Options | Recommendation | Status |
|----------|---------|----------------|--------|
| **Storage Backend for Images** | Google Drive vs Supabase Storage | Supabase Storage (faster, cheaper) | ⏳ Pending |
| **Paragraph Position Tracking** | DOM node IDs vs sequential index | Sequential index (simpler) | ⏳ Pending |
| **Legacy Articles Backfill** | Auto-parse vs manual flag | Manual flag ("legacy-unparsed") | ⏳ Pending |
| **Image Publishing Pipeline** | Immediate vs deferred preprocessing | Deferred (separate epic) | ✅ Decided |

### 4.2 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI parsing accuracy <85% | Medium | High | Implement extensive test suite; fallback to heuristics |
| Image download failures (403, timeout) | Medium | Medium | Retry logic; save partial results; manual upload option |
| Large images exceed storage limits | Low | Medium | Implement compression; set max file size (10MB) |
| Parsing latency >30 seconds | Medium | Medium | Async processing; progress indicator; caching |
| Database migration fails in production | Low | Critical | Test on staging; rollback plan; backup before migration |

---

## 5. Success Criteria

- [ ] **Parsing Accuracy**: ≥90% of test articles parsed correctly (title, author, images, meta)
- [ ] **Performance**: Parsing completes in <20 seconds for typical article (1500 words, 5 images)
- [ ] **Image Specs**: 100% of downloaded images have complete metadata (width, height, size, MIME)
- [ ] **UI Usability**: Reviewers can confirm parsing in <2 minutes
- [ ] **Database Migration**: Zero data loss, <5 minutes downtime
- [ ] **Test Coverage**: ≥85% backend, ≥80% frontend
- [ ] **Error Handling**: All edge cases handled gracefully (missing fields, malformed HTML, download errors)

---

## 6. Related Documentation

- **Requirements**: `docs/article_parsing_requirements.md`
- **Checklist**: `specs/001-cms-automation/requirements.md` (FR-010a to FR-010n)
- **Spec**: `specs/001-cms-automation/spec.md` (to be updated)
- **Plan**: `specs/001-cms-automation/plan.md` (to be updated)
- **Data Model**: `specs/001-cms-automation/data-model.md` (to be updated)
- **Tasks**: `specs/001-cms-automation/tasks.md` (to be updated)

---

**Document Owner**: CMS Automation Team
**Next Review**: After Phase 1 completion
**Status**: ✅ Ready for Implementation
