# CMS Automation Project - Article Parsing & Storage Architecture

**Last Updated:** November 14, 2025  
**Project Root:** `/Users/albertking/ES/cms_automation`

---

## 1. DATABASE SCHEMA

### Core Article Table: `articles`

#### Primary Article Data
```sql
articles(
  id: INTEGER PRIMARY KEY,
  
  -- Content
  title: VARCHAR(500) NOT NULL,
  body: TEXT NOT NULL,
  
  -- Status & Workflow
  status: ENUM(imported|draft|in-review|seo_optimized|ready_to_publish|publishing|scheduled|published|failed),
  
  -- Authorship
  author_id: INTEGER NOT NULL,
  source: VARCHAR(50) DEFAULT 'manual' (csv_import|json_import|manual|wordpress_export),
  
  -- Images
  featured_image_path: VARCHAR(500),
  additional_images: JSONB[] DEFAULT [],
  
  -- WordPress Taxonomy
  tags: TEXT[] (3-6 natural categories),
  categories: TEXT[] (hierarchical taxonomy),
  
  -- Timestamps
  created_at, updated_at: TIMESTAMP,
  published_at: TIMESTAMP,
  cms_article_id: VARCHAR(255) UNIQUE,
  published_url: VARCHAR(500)
);
```

#### Phase 7: Structured Parsing Fields
```sql
-- Title Decomposition
title_prefix: VARCHAR(200)      -- e.g., "【專題報導】"
title_main: VARCHAR(500)        -- e.g., "2024年醫療保健創新趨勢"
title_suffix: VARCHAR(200)      -- e.g., "從AI診斷到遠距醫療"

-- Author Extraction
author_line: VARCHAR(300)       -- Raw line: "文／張三｜編輯／李四"
author_name: VARCHAR(100)       -- Cleaned: "張三"

-- Body & SEO
body_html: TEXT                 -- Sanitized HTML (headers/images removed)
meta_description: TEXT          -- 150-160 chars for SEO
seo_keywords: TEXT[]            -- Array of keywords

-- Parsing Confirmation Workflow
parsing_confirmed: BOOLEAN DEFAULT FALSE
parsing_confirmed_at: TIMESTAMP
parsing_confirmed_by: VARCHAR(100)
parsing_feedback: TEXT
```

#### Phase 7: Proofreading Suggestions
```sql
-- Content Optimization
suggested_content: TEXT
suggested_content_changes: JSONB (diff structure)

-- Meta Description Suggestions
suggested_meta_description: TEXT
suggested_meta_reasoning: TEXT
suggested_meta_score: FLOAT (0-1 quality score)

-- SEO Keywords Suggestions
suggested_seo_keywords: JSONB[] (array of keywords)
suggested_keywords_reasoning: TEXT
suggested_keywords_score: FLOAT (0-1)

-- Paragraph Optimization
paragraph_suggestions: JSONB
paragraph_split_suggestions: JSONB

-- FAQ Schema
faq_schema_proposals: JSONB (multiple variants)

-- Generation Metadata
suggested_generated_at: TIMESTAMP
ai_model_used: VARCHAR(100)
generation_cost: NUMERIC(10,4) USD
```

#### Proofreading Issues
```sql
proofreading_issues: JSONB[]    -- Combined AI/script issues
critical_issues_count: INTEGER  -- Blocking issues (F-class)

-- Metadata
article_metadata: JSONB         -- CMS-specific metadata
formatting: JSONB               -- Formatting preferences
```

---

### Related Tables

#### `article_images` - Extracted Images (Phase 7)
```sql
article_images(
  id: INTEGER PRIMARY KEY,
  article_id: INTEGER FK,
  
  -- File Paths
  preview_path: VARCHAR(500),    -- Thumbnail
  source_path: VARCHAR(500),     -- Downloaded full-res
  source_url: VARCHAR(1000),     -- Original "原圖" URL
  
  -- Content
  caption: TEXT,
  position: INTEGER NOT NULL,    -- Paragraph index (0-based)
  
  -- Technical Specs
  metadata: JSONB {
    image_technical_specs: {
      width: INTEGER,
      height: INTEGER,
      file_size_bytes: INTEGER,
      format: STRING (JPEG/PNG),
      color_mode: STRING (RGB/RGBA)
    }
  },
  
  -- Timestamps
  created_at, updated_at: TIMESTAMP,
  CONSTRAINT: position >= 0 AND UNIQUE(article_id, position)
);
```

#### `article_image_reviews` - Image Review Workflow
```sql
article_image_reviews(
  id: INTEGER PRIMARY KEY,
  article_image_id: INTEGER FK,
  
  -- Review Action
  action: ENUM(keep|remove|replace_caption|replace_source),
  
  -- Replacement Data (conditional)
  new_caption: TEXT,             -- If action = replace_caption
  new_source_url: VARCHAR(1000), -- If action = replace_source
  
  -- Metadata
  reviewer_notes: TEXT,
  created_at: TIMESTAMP
);
```

#### `worklist_items` - Google Drive Integration (Phase 8)
```sql
worklist_items(
  id: INTEGER PRIMARY KEY,
  drive_file_id: VARCHAR(255) UNIQUE,
  title: VARCHAR(500),
  
  -- Status Workflow
  status: ENUM(
    pending,
    parsing,              -- Phase 7: Parsing in progress
    parsing_review,       -- Phase 7: Review title/author/SEO/images
    proofreading,
    proofreading_review,
    ready_to_publish,
    publishing,
    published,
    failed
  ),
  
  -- Content
  content: TEXT (Markdown/HTML),
  raw_html: TEXT (Original Google Docs HTML),
  author: VARCHAR(255),
  
  -- WordPress Taxonomy (from YAML front matter)
  tags: TEXT[],
  categories: TEXT[],
  meta_description: TEXT (150-160 chars),
  seo_keywords: TEXT[],
  
  -- Tracking
  article_id: INTEGER FK,
  drive_metadata: JSONB,
  notes: JSONB[],        -- Reviewer notes history
  synced_at: TIMESTAMP,
  created_at, updated_at: TIMESTAMP
);
```

#### `title_suggestions` - Title Optimization (Phase 7)
```sql
title_suggestions(
  article_id: INTEGER FK,
  
  -- Multiple Title Options
  suggested_title_sets: JSONB[{
    title_set_id: STRING,
    prefix: STRING,
    main: STRING,
    suffix: STRING,
    reasoning: STRING,
    confidence_score: FLOAT (0-1)
  }],
  
  optimization_notes: TEXT[],
  generated_at: TIMESTAMP
);
```

#### `seo_suggestions` - SEO Optimization (Phase 7)
```sql
seo_suggestions(
  article_id: INTEGER FK,
  
  -- Keywords
  seo_keywords: JSONB {
    focus_keyword: STRING,
    primary_keywords: STRING[],
    secondary_keywords: STRING[],
    keyword_density: FLOAT,
    readability_score: FLOAT (0-100)
  },
  
  -- Meta Description
  meta_description: TEXT,
  meta_reasoning: TEXT,
  meta_score: FLOAT (0-1),
  
  -- Tags Recommendation
  recommended_tags: TEXT[],
  tag_reasoning: TEXT,
  
  generated_at: TIMESTAMP
);
```

#### `article_faqs` - FAQ Generation (Phase 7)
```sql
article_faqs(
  id: INTEGER PRIMARY KEY,
  article_id: INTEGER FK,
  
  -- FAQ Data
  question: TEXT,
  answer: TEXT,
  position: INTEGER,
  
  -- Classification
  question_type: ENUM(definition|how_to|why|what|when|where),
  search_intent: ENUM(informational|transactional|navigational|commercial),
  
  -- Confidence
  ai_confidence: FLOAT (0-1),
  
  -- Review Status
  status: ENUM(pending|approved|rejected|modified),
  reviewer_feedback: TEXT,
  
  -- Timestamps
  created_at, updated_at: TIMESTAMP
);
```

---

## 2. ARTICLE PARSING PIPELINE

### Overview
The parsing pipeline converts raw Google Docs HTML into structured article data using a **dual-strategy approach**:

1. **Primary (AI)**: Claude Sonnet 4.5 for high accuracy
2. **Fallback (Heuristic)**: BeautifulSoup for deterministic fallback

### Key Service: `ArticleParserService`

**Location:** `/Users/albertking/ES/cms_automation/backend/src/services/parser/article_parser.py`

#### Step 1: Document Parsing (`parse_document()`)
```python
ParsingResult = ArticleParserService.parse_document(
  raw_html: str,                    # Google Docs HTML
  fallback_to_heuristic: bool = True
)

# Returns:
ParsingResult {
  success: bool,
  parsed_article: ParsedArticle | None,
  errors: list[ParsingError],
  warnings: list[str],
  metadata: {
    parsing_duration_ms: int,
    model: str,
    usage: {input_tokens, output_tokens}
  }
}
```

#### Step 2: AI Parsing (`_parse_with_ai()`)
- **Model**: Claude Sonnet 4.5 (temperature=0.0 for determinism)
- **Max Tokens**: 4096
- **Confidence**: 0.95 (high)

**Prompt focuses on extracting:**
1. **Title**: Prefix (optional) + Main (required) + Suffix (optional)
2. **Author**: Raw line + Cleaned name
3. **Body**: HTML with headers/images/metadata removed
4. **Meta Description**: 150-160 character SEO summary
5. **SEO Keywords**: 5-10 relevant keywords
6. **Tags**: 3-6 content categories
7. **Images**: Position + URL + Caption

**Output Format (JSON):**
```json
{
  "title_prefix": "【專題報導】",
  "title_main": "2024年醫療保健創新趨勢",
  "title_suffix": "從AI診斷到遠距醫療",
  "author_line": "文／張三｜編輯／李四",
  "author_name": "張三",
  "body_html": "<p>正文內容...</p>",
  "meta_description": "本文探討2024年...", // 150-160 chars
  "seo_keywords": ["醫療保健", "AI診斷", "遠距醫療"],
  "tags": ["醫療", "科技", "AI"],
  "images": [
    {
      "position": 0,        // paragraph index
      "source_url": "https://...",
      "caption": "圖1：AI診斷示意圖"
    }
  ]
}
```

#### Step 3: Heuristic Parsing (Fallback)
If AI fails, heuristic-based parsing using BeautifulSoup:

**Title Extraction:**
- Strategy 1: Look for `<h1>` tags
- Strategy 2: Find first substantial paragraph (10-200 chars)
- Parse prefix using regex: `^([【《\[][\u4e00-\u9fa5]+[】》\]])`
- Parse suffix using separators: `:`, `-`, `—`, `─`

**Author Extraction:**
- Regex patterns:
  - `文[／/]([^｜|\n]+)` → 文／張三
  - `作者[：:]([^｜|\n]+)` → 作者：張三
  - `撰文[：:]([^｜|\n]+)` → 撰文：張三
  - `By[：:\s]+([^｜|\n]+)` → By: John Doe
  - `記者[：:]([^｜|\n]+)` → 記者：張三

**Body Extraction:**
- Remove unwanted elements: script, style, nav, header, footer, iframe
- Skip metadata paragraphs at beginning
- Remove images from paragraphs
- Keep substantial content (>50 chars)

**SEO Extraction:**
- Look for existing meta tags
- Generate description from first substantial paragraph (100+ chars)
- Extract keywords using frequency analysis (Chinese word segmentation)
- Exclude stopwords (的, 了, 在, 是, etc.)
- Use top keywords as tags

**Image Extraction:**
- Find `<img>` tags and `<figure>` elements
- Calculate position based on paragraph index
- Extract caption from: figcaption → alt → title

**Confidence**: 0.7 (lower than AI)

---

### Data Model: `ParsedArticle`
**Location:** `/Users/albertking/ES/cms_automation/backend/src/services/parser/models.py`

```python
class ParsedArticle(BaseModel):
    # Title
    title_prefix: str | None
    title_main: str (required)
    title_suffix: str | None
    
    # Author
    author_line: str | None
    author_name: str | None
    
    # Content
    body_html: str
    
    # SEO
    meta_description: str | None  # 150-160 chars
    seo_keywords: list[str]
    tags: list[str]
    
    # Images
    images: list[ParsedImage]
    
    # Metadata
    parsing_method: str ("ai" | "heuristic")
    parsing_confidence: float (0.0-1.0)
    parsing_timestamp: datetime
```

---

## 3. AI PARSING & METADATA EXTRACTION

### Current Implementation

#### Author & Image Extraction
Both are handled in the **ArticleParserService** using Claude AI:

```python
# In AI Parsing Prompt (lines 251-306):
prompt = """
Extract structured data from Google Doc HTML:
1. Title: Split into prefix/main/suffix
2. Author: Extract from "文／" or "作者：" patterns
3. Body: Remove headers/images/metadata
4. Meta Description: 150-160 character SEO summary
5. SEO Keywords: 5-10 relevant keywords
6. Tags: 3-6 content tags
7. Images: Extract position, URL, caption
"""
```

#### Cost Optimization (Phase 7)
- **Original approach** (2 separate calls):
  - ~$0.10-0.13 per article
  - 30-40 seconds
  
- **Unified approach** (1 call for all optimizations):
  - ~$0.06-0.08 per article
  - 20-30 seconds
  - **Savings: 40-60% cost, 30-40% time**

#### Unified Optimization Service
**Location:** `/Users/albertking/ES/cms_automation/backend/src/services/parser/unified_optimization_service.py`

Generates ALL optimizations in single Claude API call:
1. **Title Suggestions**: 3-component structure with 2-3 options
2. **SEO Keywords**: Focus/Primary/Secondary keywords
3. **Meta Description**: Optimized 150-160 char version
4. **Tags**: Recommended WordPress tags
5. **FAQ**: 8-10 generated Q&A pairs

```python
class UnifiedOptimizationService:
    async def generate_all_optimizations(
        article: Article,
        regenerate: bool = False
    ) -> dict {
        "title_suggestions": {...},
        "seo_suggestions": {
            "seo_keywords": {...},
            "meta_description": {...},
            "tags": [...]
        },
        "faqs": [...],
        "generation_metadata": {
            "total_cost_usd": float,
            "total_tokens": int,
            "duration_ms": int
        }
    }
```

---

## 4. ARTICLE REVIEW WORKFLOW

### Step 1: Parsing Confirmation (ArticleParsingPage)
**Frontend:** `/Users/albertking/ES/cms_automation/frontend/src/pages/ArticleParsingPage.tsx`

**Workflow:**
1. User selects parsing mode (AI or Heuristic)
2. Click "开始解析" to trigger parsing
3. Review parsing results:
   - Full title (with prefix/suffix display)
   - Author name + raw author line
   - Title optimization (AI-generated variants)
   - SEO metadata (meta description, keywords)
   - Images (position, dimensions, caption)
   - Body preview (first 500 chars)

4. User can:
   - Edit image captions inline
   - Remove incorrect images
   - Replace image source URLs
   
5. Click "✓ 确认解析结果并生成 AI 优化建议"
   - System automatically generates optimizations
   - Polling every 2-3 seconds for completion
   - Shows spinner while generating

### Step 2: SEO & FAQ Confirmation (ArticleSEOConfirmationPage)
After parsing confirmed, user reviews:
- Title optimization options (2-3 variants with reasoning)
- SEO keywords (focus/primary/secondary)
- Meta description (with quality score)
- FAQ proposals (8-10 generated Q&A pairs)
- Tags recommendations

### Step 3: Worklist Integration (Phase 8)
**Frontend:** `/Users/albertking/ES/cms_automation/frontend/src/pages/WorklistPage.tsx`

**Workflow States:**
```
pending 
  → parsing (parsing_in_progress)
    → parsing_review (confirm parsed data)
      → proofreading
        → proofreading_review
          → ready_to_publish
            → publishing
              → published | failed
```

**WorklistDetailDrawer:**
- Shows article details
- Status change dropdown
- Reviewer notes history
- Sync/publish buttons

**ArticleReviewModal (Phase 8):**
- Inline article review interface
- Side-by-side content comparison
- Metadata editing
- Inline saves

---

## 5. API ENDPOINTS

### Article Endpoints
**Base:** `/v1/articles`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | List articles (skip, limit) |
| `/{article_id}` | GET | Get article details |
| `/{article_id}/proofread` | POST | Run unified proofreading |
| `/{article_id}/parse` | POST | Parse article (Phase 7) |
| `/{article_id}/parsing-result` | GET | Get parsing result |
| `/{article_id}/images/{image_id}/review` | POST | Review image |
| `/{article_id}/confirm-parsing` | POST | Confirm parsing |
| `/{article_id}/optimizations` | GET | Get optimizations |
| `/{article_id}/optimizations/generate` | POST | Generate all optimizations |

### Worklist Endpoints
**Base:** `/v1/worklist`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | List worklist items |
| `/{item_id}` | GET | Get item details |
| `/{item_id}/status` | POST | Change status |
| `/{item_id}/publish` | POST | Publish to WordPress |
| `/sync` | POST | Sync with Google Drive |
| `/statistics` | GET | Get statistics |
| `/sync-status` | GET | Get Drive sync status |

---

## 6. KEY METADATA FIELDS EXTRACTED

### During Parsing
✓ Title components (prefix, main, suffix)
✓ Author name & raw author line
✓ Sanitized body HTML
✓ Meta description (150-160 chars)
✓ SEO keywords (5-10)
✓ Tags (3-6)
✓ Images (position, URL, caption, technical specs)

### During Optimization (AI)
✓ Title suggestions (2-3 variants with reasoning)
✓ SEO keyword optimization (focus/primary/secondary)
✓ Meta description optimization (with quality score)
✓ Tags recommendations
✓ FAQ proposals (8-10 Q&A pairs)
✓ Paragraph optimization suggestions
✓ Content improvement recommendations

### Review & Confirmation
✓ parsing_confirmed (boolean)
✓ parsing_confirmed_at (timestamp)
✓ parsing_confirmed_by (user identifier)
✓ parsing_feedback (user notes)
✓ Image review actions (keep/remove/replace_caption/replace_source)

---

## 7. WORKLIST PIPELINE (PHASE 8)

### Google Drive Integration
- Documents stored in Google Drive
- Synced to `worklist_items` table
- Raw HTML extracted from Google Docs export
- Status workflow tracks processing progress

### Article Creation from Worklist
When `parsing_confirmed = true`:
1. Create/update `articles` table
2. Store parsing results (title components, author, body_html, SEO, images)
3. Link `worklist_item.article_id` → `articles.id`
4. Trigger optimization generation
5. Update status: `parsing_review` → `proofreading`

### Status Transitions
```
pending
  ↓
[Trigger parsing]
parsing (ArticleParserService.parse_document())
  ↓
parsing_review (User reviews in ArticleParsingPage)
  ↓
[Confirm & generate optimizations]
proofreading (Proofreading analysis)
  ↓
proofreading_review (User reviews in ProofreadingReviewPage)
  ↓
ready_to_publish
  ↓
publishing
  ↓
published | failed
```

---

## 8. RECENT CHANGES (PHASE 8)

### Frontend UI Modernization
- Added ArticleReviewModal for inline article review
- Integrated review modal in WorklistPage
- Real-time status updates with polling

### Database Migrations
- 20251112: Added raw_html to worklist_items
- 20251108: Created article_images tables
- 20251108: Added unified optimization tables
- 20251107: Extended worklist status pipeline

### AI Model Updates
- Upgraded to Claude Sonnet 4.5
- Improved structured parsing accuracy
- Cost optimization via unified API calls

---

## 9. KEY FILES SUMMARY

### Database Models
- `/backend/src/models/article.py` - Core Article model
- `/backend/src/models/worklist.py` - Worklist workflow
- `/backend/src/models/article_image.py` - Image management
- `/backend/src/models/title_suggestions.py` - Title optimization
- `/backend/src/models/seo_suggestions.py` - SEO optimization
- `/backend/src/models/article_faq.py` - FAQ generation

### Services
- `/backend/src/services/parser/article_parser.py` - Main parsing service
- `/backend/src/services/parser/unified_optimization_service.py` - AI optimization
- `/backend/src/services/parser/article_processor.py` - Processing pipeline

### API Endpoints
- `/backend/src/api/routes/articles.py` - Article API
- `/backend/src/api/schemas/article.py` - Article schemas
- `/backend/src/api/schemas/optimization.py` - Optimization schemas

### Frontend Pages
- `/frontend/src/pages/ArticleParsingPage.tsx` - Parsing review (Step 1)
- `/frontend/src/pages/ArticleSEOConfirmationPage.tsx` - SEO review (Step 2)
- `/frontend/src/pages/WorklistPage.tsx` - Worklist management
- `/frontend/src/components/Worklist/` - Worklist components

---

## 10. ARCHITECTURE SUMMARY

```
Google Drive Documents
         ↓
[Google Drive Sync]
         ↓
worklist_items (raw_html)
         ↓
[User triggers parsing]
         ↓
ArticleParserService
├─ AI Parsing (Claude Sonnet 4.5) [Primary]
│  └─ Confidence: 0.95
└─ Heuristic Parsing (BeautifulSoup) [Fallback]
   └─ Confidence: 0.7
         ↓
ParsedArticle (title, author, body_html, SEO, images)
         ↓
[User confirms in ArticleParsingPage]
         ↓
articles table (populated with parsed data)
article_images table (extracted images)
worklist_items.article_id linked
         ↓
[Auto-trigger optimization generation]
         ↓
UnifiedOptimizationService
└─ Claude API (1 call for all: titles + SEO + FAQ)
         ↓
title_suggestions, seo_suggestions, article_faqs tables
         ↓
[User reviews in ArticleSEOConfirmationPage]
         ↓
[Status: proofreading]
         ↓
ProofreadingReviewPage
         ↓
[Status: ready_to_publish]
         ↓
Publishing
```

**Key Achievement:** Completely structured parsing + AI optimization pipeline with cost savings of 40-60% and time savings of 30-40% through unified API approach.
