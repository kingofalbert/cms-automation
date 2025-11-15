# SEO Title Feature - Complete Documentation

## Overview

The SEO Title feature separates the SEO-optimized title (`<title>` tag, ~30 characters) from the H1 page title (25-50 characters), allowing:

1. **Extraction from original articles** - Marked sections like "這是 SEO title: ..." are automatically extracted
2. **AI-powered generation** - 2-3 SEO Title variants with reasoning and keyword analysis
3. **Custom user input** - Manual override for complete control
4. **WordPress integration** - Automatic Yoast SEO field population during publishing
5. **Backward compatibility** - Graceful fallback to H1 title for existing articles

## Architecture

### Database Schema

#### Articles Table (`articles`)

Three new columns added for SEO Title management:

```sql
-- SEO Title Tag (30字左右，用於<title>標籤和搜尋結果顯示)
seo_title VARCHAR(200) NULL

-- 是否從原文中提取了標記的 SEO Title
seo_title_extracted BOOLEAN NOT NULL DEFAULT false

-- SEO Title 來源：extracted/ai_generated/user_input/migrated
seo_title_source VARCHAR(50) NULL
```

**Migration:** Existing articles automatically migrated with `seo_title = title_main` and `seo_title_source = 'migrated'`

#### Title Suggestions Table (`title_suggestions`)

```sql
-- AI-generated SEO Title suggestions (JSONB)
suggested_seo_titles JSONB NULL
```

**Structure:**
```json
{
  "variants": [
    {
      "id": "variant_1",
      "seo_title": "2024年AI醫療創新趨勢分析",
      "reasoning": "強調時效性和關鍵詞",
      "keywords_focus": ["AI", "醫療", "2024"],
      "character_count": 28
    }
  ],
  "original_seo_title": "從原文提取的SEO標題",
  "notes": ["建議保持在30字以內"]
}
```

### Backend API

#### Schemas (`src/api/schemas/optimization.py`)

```python
class SEOTitleVariant(BaseSchema):
    id: str
    seo_title: str
    reasoning: str
    keywords_focus: list[str]
    character_count: int

class SEOTitleSuggestionsData(BaseSchema):
    variants: list[SEOTitleVariant]
    original_seo_title: str | None
    notes: list[str]

class SelectSEOTitleRequest(BaseSchema):
    variant_id: str | None  # Select AI variant
    custom_seo_title: str | None  # Or use custom input

class SelectSEOTitleResponse(BaseSchema):
    article_id: int
    seo_title: str
    seo_title_source: str
    previous_seo_title: str | None
    updated_at: datetime
```

#### Endpoints

**POST /api/v1/optimization/articles/{article_id}/select-seo-title**

Select an SEO Title variant or provide custom input.

**Request:**
```json
{
  "variant_id": "variant_1"  // Option 1: Select AI variant
}
```
or
```json
{
  "custom_seo_title": "自定義的SEO標題"  // Option 2: Custom input
}
```

**Response:**
```json
{
  "article_id": 123,
  "seo_title": "2024年AI醫療創新趨勢分析",
  "seo_title_source": "ai_generated",
  "previous_seo_title": "AI在醫療領域的應用",
  "updated_at": "2025-11-14T10:30:00Z"
}
```

**Validation:**
- Cannot provide both `variant_id` and `custom_seo_title`
- At least one must be provided
- Article must exist
- If `variant_id` provided, variant must exist in `title_suggestions.suggested_seo_titles`

**GET /api/v1/optimization/articles/{article_id}/optimizations**

Retrieve article optimizations including SEO Title suggestions.

**Response:**
```json
{
  "article_id": 123,
  "title_suggestions": {
    "seo_title_suggestions": {
      "variants": [...],
      "original_seo_title": "...",
      "notes": [...]
    }
  }
}
```

### Frontend Components

#### SEOTitleSelectionCard Component

**Location:** `frontend/src/components/ArticleReview/SEOTitleSelectionCard.tsx`

**Props:**
```typescript
interface SEOTitleSelectionCardProps {
  articleId: number;
  currentSeoTitle: string | null;
  seoTitleSource: string | null;
  suggestions: SEOTitleSuggestionsData | null;
  isLoading: boolean;
  onSelectionSuccess?: (response: SelectSEOTitleResponse) => void;
  onError?: (error: string) => void;
}
```

**Features:**
1. **Current SEO Title Display** - Shows current selection with source badge
2. **Original Extracted Title** - If article had marked SEO title
3. **AI Variants** - 2-3 AI-generated suggestions with reasoning
4. **Custom Input** - Text area for manual entry
5. **Character Counter** - Real-time character count with warning (optimal: ~30 chars)
6. **Selection Confirmation** - Double-check before applying

**Integration in ParsingReviewPanel:**
```typescript
<SEOTitleSelectionCard
  articleId={data.article_id}
  currentSeoTitle={currentSeoTitle}
  seoTitleSource={seoTitleSource}
  suggestions={seoTitleSuggestions}
  isLoading={isLoadingSeoTitle}
  onSelectionSuccess={handleSeoTitleSelectionSuccess}
  onError={handleSeoTitleSelectionError}
/>
```

### WordPress Integration

#### PublishingOrchestrator (`src/services/publishing/orchestrator.py`)

**Key Method: `_build_seo_metadata()`** (lines 377-436)

```python
def _build_seo_metadata(self, article: Article) -> SEOMetadata:
    """Phase 9: Prioritizes article.seo_title over article.title"""

    # Use seo_title if available, fallback to title
    seo_title = (article.seo_title or article.title or "Published Article").strip()
    h1_title = (article.title or "Published Article").strip()

    # Ensure meta_title meets minimum SEO requirements (50 chars)
    if len(seo_title) < 50:
        padded_title = (seo_title + " ") * ((50 // max(len(seo_title), 1)) + 1)
        seo_title = padded_title[:60]

    # Log if using extracted/AI-generated SEO Title
    if article.seo_title:
        logger.info(
            "using_optimized_seo_title",
            article_id=article.id,
            seo_title=article.seo_title,
            seo_title_source=article.seo_title_source,
        )

    return SEOMetadata(meta_title=seo_title, ...)
```

**Pre-publish Validation** (lines 163-170)

```python
# Validate SEO Title before publishing
if not article.seo_title:
    logger.warning(
        "seo_title_missing_before_publish",
        article_id=article.id,
        title=article.title,
        message="Article has no SEO Title. Will fallback to H1 title for SEO.",
    )
```

#### WordPress Publisher (`src/services/providers/playwright_wordpress_publisher.py`)

**Yoast SEO Configuration** (lines 112-117)

```python
"seo": {
    "panel": "#wpseo-metabox-root",
    "seo_title_field": "input[name='yoast_wpseo_title']",  # NEW
    "focus_keyword_field": "input[name='yoast_wpseo_focuskw']",
    "meta_description_field": "textarea[name='yoast_wpseo_metadesc']",
}
```

**SEO Configuration Method** (lines 412-461)

```python
async def _step_configure_seo(self, seo_data: SEOMetadata) -> None:
    """Phase 9: Includes SEO Title configuration"""

    # Set SEO Title (for <title> tag)
    if seo_data.meta_title:
        seo_title_field = self.config["seo"].get("seo_title_field")
        if seo_title_field:
            await self.page.fill(seo_title_field, seo_data.meta_title)
            logger.info("seo_title_configured", seo_title=seo_data.meta_title)

    # Set focus keyword and meta description
    # ...
```

## Data Flow

### Complete Workflow

```
1. Article Parsing
   ├─ ArticleParserService detects "這是 SEO title: ..."
   ├─ Extracts SEO Title
   └─ Sets article.seo_title, seo_title_extracted=True, seo_title_source='extracted'

2. AI Optimization (UnifiedOptimizationService)
   ├─ Generates 2-3 SEO Title variants
   ├─ Analyzes keywords and reasoning
   └─ Stores in title_suggestions.suggested_seo_titles (JSONB)

3. Frontend Selection
   ├─ ParsingReviewPanel fetches optimizations
   ├─ SEOTitleSelectionCard displays options
   ├─ User selects variant or enters custom
   └─ POST /select-seo-title

4. Backend Update
   ├─ Validates request
   ├─ Updates article.seo_title
   ├─ Sets article.seo_title_source ('ai_generated' or 'user_input')
   └─ Returns confirmation

5. WordPress Publishing
   ├─ PublishingOrchestrator._prepare_context()
   │  ├─ Validates article.seo_title (warns if missing)
   │  └─ Calls _build_seo_metadata()
   │     ├─ Prioritizes article.seo_title over article.title
   │     ├─ Pads to 50 chars if needed (Yoast requirement)
   │     └─ Returns SEOMetadata(meta_title=seo_title)
   ├─ WordPress Publisher receives SEOMetadata
   ├─ _step_configure_seo() fills Yoast fields
   │  ├─ SEO Title: input[name='yoast_wpseo_title']
   │  ├─ Focus Keyword: input[name='yoast_wpseo_focuskw']
   │  └─ Meta Description: textarea[name='yoast_wpseo_metadesc']
   └─ Article published with optimized SEO Title
```

### SEO Title vs H1 Title Mapping

| Source Field | WordPress Field | Purpose | Length | Yoast SEO Field |
|-------------|----------------|---------|--------|-----------------|
| `article.title` | Post Title | H1 page heading | 25-50 chars | (auto-filled) |
| `article.seo_title` | SEO Title | `<title>` tag | ~30 chars | `yoast_wpseo_title` |
| `article.meta_description` | Meta Description | `<meta name="description">` | 120-160 chars | `yoast_wpseo_metadesc` |

## Usage Examples

### Example 1: AI-Generated SEO Title

**Scenario:** User selects AI variant for an article about AI in healthcare

**Steps:**
1. Article parsed: `title = "AI在醫療領域的創新應用與未來展望"`
2. AI generates variants:
   ```json
   {
     "variants": [
       {
         "id": "variant_1",
         "seo_title": "2024年AI醫療創新趨勢分析",
         "reasoning": "強調時效性和關鍵詞，提升搜尋排名",
         "keywords_focus": ["AI", "醫療", "2024", "趨勢"],
         "character_count": 28
       }
     ]
   }
   ```
3. User clicks "使用此 SEO Title" for variant_1
4. API call: `POST /select-seo-title` with `{"variant_id": "variant_1"}`
5. Article updated:
   ```python
   seo_title = "2024年AI醫療創新趨勢分析"
   seo_title_source = "ai_generated"
   ```
6. User publishes article
7. WordPress receives:
   - Post Title (H1): "AI在醫療領域的創新應用與未來展望"
   - SEO Title (`<title>`): "2024年AI醫療創新趨勢分析 2024年AI醫療創新趨勢分析..." (padded to 50+ chars)

**Result:**
- Page H1: "AI在醫療領域的創新應用與未來展望"
- Google search displays: "2024年AI醫療創新趨勢分析..."

### Example 2: Custom SEO Title

**Scenario:** User wants complete control over SEO Title

**Steps:**
1. User clicks "自定義 SEO Title"
2. Enters: "最新AI醫療技術突破｜2024完整指南"
3. Character count shows: 29 characters ✓
4. Clicks "套用自定義 SEO Title"
5. API call: `POST /select-seo-title` with `{"custom_seo_title": "最新AI醫療技術突破｜2024完整指南"}`
6. Article updated:
   ```python
   seo_title = "最新AI醫療技術突破｜2024完整指南"
   seo_title_source = "user_input"
   ```
7. WordPress publishing uses custom SEO Title

### Example 3: Extracted SEO Title from Original

**Scenario:** Original article has marked SEO title

**Original Text:**
```
這是 SEO title: 深度解析AI醫療應用實例

# AI在醫療領域的創新應用與未來展望

本文探討...
```

**Parsing Result:**
```python
title = "AI在醫療領域的創新應用與未來展望"
seo_title = "深度解析AI醫療應用實例"
seo_title_extracted = True
seo_title_source = "extracted"
```

**Frontend Display:**
- Shows badge: "原文提取"
- Displays: "深度解析AI醫療應用實例"
- User can keep it or select AI variant

**Publishing:**
- Uses extracted SEO Title automatically
- No user action needed unless they want to change it

### Example 4: Backward Compatibility (No SEO Title)

**Scenario:** Old article without SEO Title optimization

**Article State:**
```python
title = "AI在醫療領域的應用"
seo_title = None
```

**Publishing Flow:**
1. User clicks "發佈"
2. PublishingOrchestrator detects missing SEO Title
3. Logs warning:
   ```
   logger.warning(
       "seo_title_missing_before_publish",
       article_id=123,
       title="AI在醫療領域的應用",
       message="Article has no SEO Title. Will fallback to H1 title for SEO."
   )
   ```
4. _build_seo_metadata() falls back:
   ```python
   seo_title = article.seo_title or article.title  # Falls back to H1
   # Result: seo_title = "AI在醫療領域的應用"
   ```
5. WordPress publishes with:
   - Post Title (H1): "AI在醫療領域的應用"
   - SEO Title: "AI在醫療領域的應用 AI在醫療領域的應用..." (padded)

**Result:** Article publishes successfully, just without optimized SEO Title

## Testing

### Backend Testing

**Test Script:** `/backend/test_seo_title_api.py`

**Test Cases:**
1. ✅ Find article with title_suggestions
2. ✅ Check SEO Title suggestions structure
3. ✅ Simulate select-seo-title API (update and verify)
4. ✅ Verify PublishingOrchestrator logic (seo_title priority)
5. ✅ Clean up test data

**Run:**
```bash
cd backend
poetry run python test_seo_title_api.py
```

**Expected Output:**
```
================================================================================
Phase 5: SEO Title API 測試
================================================================================

📋 測試 1: 查找有優化建議的文章
--------------------------------------------------------------------------------
✅ 找到文章 ID: 123
   標題: AI在醫療領域的創新應用
   當前 SEO Title: None
   SEO Title 來源: None

...

================================================================================
✅ 所有測試完成！
================================================================================
```

### Frontend Testing

**Manual Testing Checklist:**

1. **Component Rendering**
   - [ ] SEOTitleSelectionCard appears in ParsingReviewPanel
   - [ ] Current SEO Title displays correctly
   - [ ] Source badge shows correct type (原文提取/AI生成/自定義/遷移)

2. **AI Variants Display**
   - [ ] Variants load from API
   - [ ] Reasoning and keywords display
   - [ ] Character count shown
   - [ ] "使用此 SEO Title" button works

3. **Custom Input**
   - [ ] "自定義 SEO Title" button shows text area
   - [ ] Character counter updates in real-time
   - [ ] Warning shows if > 50 characters
   - [ ] "套用自定義 SEO Title" sends correct API request

4. **API Integration**
   - [ ] Success: Shows success message and updates display
   - [ ] Error: Shows error toast with message
   - [ ] Loading: Button shows "處理中..." during request

### End-to-End Testing

**Complete Workflow Test:**

1. **Parse Article with Marked SEO Title**
   ```
   原文: "這是 SEO title: 測試SEO標題"
   Expected: seo_title = "測試SEO標題", seo_title_extracted = True
   ```

2. **Generate Optimizations**
   ```
   Run: POST /api/v1/optimization/articles/{id}/generate-optimizations
   Expected: suggested_seo_titles populated with 2-3 variants
   ```

3. **Select SEO Title**
   ```
   Action: Click "使用此 SEO Title" on variant_2
   Expected: Article updated with variant_2's seo_title, source = "ai_generated"
   ```

4. **Publish to WordPress**
   ```
   Action: Click "發佈" in frontend
   Expected:
   - Yoast SEO Title field filled with article.seo_title
   - Post Title = article.title (H1)
   - Logger shows "using_optimized_seo_title" and "seo_title_configured"
   ```

5. **Verify in WordPress**
   ```
   Check published article:
   - Page source: <title> contains seo_title
   - Page content: <h1> contains title
   - Yoast SEO panel: Shows seo_title in SEO Title field
   ```

## Troubleshooting

### Issue 1: SEO Title Not Appearing in WordPress

**Symptoms:** Article publishes but Yoast SEO Title is empty

**Diagnosis:**
1. Check logs for "seo_title_configured" message
2. Verify `article.seo_title` is not None/empty in database
3. Check if Yoast SEO plugin is active

**Solutions:**
- If `seo_title` is None: Article will use H1 title (expected behavior)
- If Yoast inactive: SEO fields won't appear (install/activate Yoast SEO)
- If selector wrong: Update `seo_title_field` in playwright_wordpress_publisher.py config

### Issue 2: SEO Title Too Short (Yoast Warning)

**Symptoms:** Yoast shows "SEO Title too short" warning

**Diagnosis:**
- SEO Title < 50 characters
- Padding logic activated, creating repetitive title

**Solutions:**
1. **Frontend validation:** Add minimum length check (50 chars) in SEOTitleSelectionCard
2. **Backend adjustment:** Modify padding logic in _build_seo_metadata() to be more sophisticated
3. **User guidance:** Add note in UI: "建議至少 50 字元以符合 Yoast SEO 要求"

**Code Fix Example:**
```typescript
// In SEOTitleSelectionCard.tsx
const MIN_LENGTH = 50;
const isCustomTitleTooShort = customTitle.length > 0 && customTitle.length < MIN_LENGTH;

{isCustomTitleTooShort && (
  <p className="text-sm text-warning">
    建議至少 {MIN_LENGTH} 字元以符合 Yoast SEO 要求 (當前: {customTitle.length})
  </p>
)}
```

### Issue 3: API Returns 400 "Cannot provide both variant_id and custom_seo_title"

**Symptoms:** Error when trying to select SEO Title

**Diagnosis:**
- Request body contains both `variant_id` and `custom_seo_title`
- Frontend logic error

**Solution:**
```typescript
// Ensure mutually exclusive request
const requestBody: SelectSEOTitleRequest = isCustomMode
  ? { custom_seo_title: customTitle }  // Only custom
  : { variant_id: selectedVariantId };  // Only variant
```

### Issue 4: Character Counter Shows Wrong Count

**Symptoms:** Character count doesn't match actual length

**Diagnosis:**
- Emoji or special characters count as multiple bytes
- Chinese characters handled incorrectly

**Solution:**
```typescript
// Use Array.from for accurate character count
const charCount = Array.from(customTitle).length;

// Or use spread operator
const charCount = [...customTitle].length;
```

## Deployment

### Pre-deployment Checklist

**Backend:**
- [ ] Database migrations applied
  ```bash
  cd backend
  poetry run alembic upgrade head
  ```
- [ ] Verify columns exist in production database
  ```sql
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'articles' AND column_name LIKE 'seo_title%';
  ```
- [ ] Environment variables set (if any new configs added)

**Frontend:**
- [ ] Build succeeds without errors
  ```bash
  cd frontend
  npm run build
  ```
- [ ] UI components (button, badge, card, skeleton) included in build
- [ ] API types exported correctly

**WordPress:**
- [ ] Yoast SEO plugin installed and activated on target WordPress site
- [ ] Test WordPress login credentials work
- [ ] Playwright publisher config has correct selectors for Yoast version

### Deployment Steps

1. **Backup Database**
   ```bash
   # Production database backup
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Deploy Backend**
   ```bash
   # Run migrations
   poetry run alembic upgrade head

   # Restart backend service
   # (Cloud Run auto-deploys on push, or manual deploy)
   ```

3. **Deploy Frontend**
   ```bash
   # Build and upload to GCS
   npm run build
   gsutil -m rsync -r -d dist/ gs://your-frontend-bucket/
   ```

4. **Verification**
   ```bash
   # Check migration applied
   poetry run alembic current

   # Test API endpoint
   curl -X POST https://your-api.com/api/v1/optimization/articles/1/select-seo-title \
     -H "Content-Type: application/json" \
     -d '{"variant_id": "variant_1"}'
   ```

5. **Smoke Test**
   - [ ] Parse an article with SEO Title
   - [ ] Select AI variant via frontend
   - [ ] Publish to WordPress (draft mode first)
   - [ ] Verify Yoast SEO Title filled correctly

### Rollback Plan

**If issues occur:**

1. **Revert Database Migration**
   ```bash
   # Downgrade to previous version
   poetry run alembic downgrade -1
   ```

2. **Revert Code Deploy**
   ```bash
   # Git revert commit
   git revert <commit-hash>
   git push

   # Or redeploy previous version
   ```

3. **Data Recovery**
   ```bash
   # Restore from backup if needed
   psql $DATABASE_URL < backup_<timestamp>.sql
   ```

## SEO Plugin Compatibility

### Yoast SEO (Current Implementation)

**Selector:**
```python
"seo_title_field": "input[name='yoast_wpseo_title']"
```

**Compatibility:** WordPress 5.0+, Yoast SEO 15.0+

### Rank Math SEO

**To support Rank Math, update config:**

```python
"seo": {
    "panel": "#rank-math-editor",
    "seo_title_field": "input[name='rank_math_title']",
    "focus_keyword_field": "input[name='rank_math_focus_keyword']",
    "meta_description_field": "textarea[name='rank_math_description']",
}
```

### All in One SEO

**Configuration:**

```python
"seo": {
    "panel": "#aioseo-post-settings",
    "seo_title_field": "input[id='aioseo-post-settings-title']",
    "focus_keyword_field": "input[id='aioseo-post-settings-focus-keyphrase']",
    "meta_description_field": "textarea[id='aioseo-post-settings-description']",
}
```

**Implementation:**

Make SEO plugin configurable via environment variable:

```python
# settings.py
SEO_PLUGIN: str = Field(default="yoast", env="CMS_SEO_PLUGIN")
```

```python
# playwright_wordpress_publisher.py
def _get_seo_config(self):
    plugin = self.settings.SEO_PLUGIN.lower()
    configs = {
        "yoast": {...},
        "rankmath": {...},
        "aioseo": {...},
    }
    return configs.get(plugin, configs["yoast"])
```

## Performance Considerations

### Database Queries

**Optimization 1: Eager Loading**
- Always use `selectinload` for `title_suggestions` relationship
  ```python
  stmt = (
      select(Article)
      .options(selectinload(Article.title_suggestions))
      .where(Article.id == article_id)
  )
  ```

**Optimization 2: JSONB Indexing**
- Add GIN index for `suggested_seo_titles` if searching within JSONB
  ```sql
  CREATE INDEX idx_title_suggestions_seo_jsonb
  ON title_suggestions USING GIN (suggested_seo_titles);
  ```

### Frontend Performance

**Lazy Loading:**
- SEO Title suggestions only loaded when ParsingReviewPanel visible
- Uses `useEffect` with `article_id` dependency

**Debouncing:**
- Character counter updates immediately (no debounce needed for display)
- API calls only on button click (no auto-save)

### WordPress Publishing

**SEO Field Filling Performance:**
- Adds ~0.5s per field (asyncio.sleep for stability)
- Total impact: ~1.5s for 3 fields (SEO Title, keyword, description)
- Acceptable for publishing workflow

## Security Considerations

### Input Validation

**Backend:**
- `custom_seo_title` limited to 200 characters (database constraint)
- XSS prevention: SQLAlchemy ORM escapes inputs automatically
- SQL injection: Using parameterized queries via ORM

**Frontend:**
- React automatically escapes displayed content
- No `dangerouslySetInnerHTML` used in SEOTitleSelectionCard
- API responses validated against TypeScript types

### Access Control

**API Endpoints:**
- Require authentication (inherited from existing routes)
- No additional permissions needed (same as article editing)

**WordPress Publishing:**
- Credentials stored in environment variables
- Not exposed in logs or API responses
- Playwright runs in sandboxed environment

## Future Enhancements

### Phase 7: Advanced Features

**1. SEO Title A/B Testing**
- Store multiple SEO Title variants
- Track click-through rates from Google Search Console
- Automatically select best-performing variant

**2. SEO Score Prediction**
- Integrate with SEO scoring algorithms
- Predict Google ranking based on SEO Title
- Suggest improvements before publishing

**3. Bulk SEO Title Generation**
- Select multiple articles
- Generate SEO Titles in batch
- Export to CSV for review

**4. SEO Title Templates**
- Save frequently used SEO Title patterns
- "Pattern: [Year]年[Keyword][Action]"
- One-click application to new articles

**5. Multi-language SEO Titles**
- Generate SEO Titles in multiple languages
- Store in separate fields or JSONB
- WordPress multisite support

### Phase 8: Analytics Integration

**Google Search Console:**
- Fetch actual SEO Title performance data
- Compare impressions/CTR before and after optimization
- Dashboard showing SEO Title effectiveness

**WordPress Analytics:**
- Track which SEO Title sources (extracted/AI/custom) perform best
- Heatmap of character length vs. CTR
- Recommend optimal length based on historical data

## Appendix

### Migration Files

**File:** `backend/migrations/versions/20251114_1400_add_seo_title_to_articles.py`
**File:** `backend/migrations/versions/20251114_1401_add_seo_suggestions_to_title_suggestions.py`

### Database Schema SQL

```sql
-- articles table changes
ALTER TABLE articles ADD COLUMN seo_title VARCHAR(200);
ALTER TABLE articles ADD COLUMN seo_title_extracted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE articles ADD COLUMN seo_title_source VARCHAR(50);

-- title_suggestions table changes
ALTER TABLE title_suggestions ADD COLUMN suggested_seo_titles JSONB;

-- Migration: Copy existing titles
UPDATE articles
SET seo_title = title_main, seo_title_source = 'migrated'
WHERE title_main IS NOT NULL AND seo_title IS NULL;
```

### API Endpoint Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/optimization/articles/{id}/select-seo-title` | Select SEO Title variant or custom |
| GET | `/api/v1/optimization/articles/{id}/optimizations` | Get all optimizations including SEO |
| GET | `/api/v1/articles/{id}` | Get article (includes seo_title fields) |

### Logging Reference

| Event | Level | Fields |
|-------|-------|--------|
| `using_optimized_seo_title` | INFO | article_id, seo_title, seo_title_source |
| `seo_title_missing_before_publish` | WARNING | article_id, title, message |
| `seo_title_configured` | INFO | seo_title |
| `seo_configuration_failed` | WARNING | error |

### TypeScript Type Reference

See `/frontend/src/types/api.ts` lines 152-208 for complete type definitions.

## Support

For issues or questions:
1. Check this documentation
2. Review test script: `/backend/test_seo_title_api.py`
3. Check logs for error messages
4. Review Phase 4 summary: `/tmp/phase4_wordpress_integration_completion_summary.md`

---

**Last Updated:** 2025-11-14
**Version:** 1.0
**Phases Completed:** 1-5 (Database, API, Frontend, WordPress, Testing)
