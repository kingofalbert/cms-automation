# Article Parsing Emergency Fix Tasks

**Created**: 2025-11-16
**Priority**: P0 (Critical)
**Based On**: Visual test analysis findings (PARSING_VISUAL_TEST_ANALYSIS.md)
**Related SpecKit Tasks**: T7.13, T7.15, Phase 7 tasks

---

## Overview

Visual testing revealed critical data pipeline issues preventing parsing feature from working correctly. These emergency fixes address the immediate blockers before continuing with full Phase 7 implementation.

**Root Cause**: Parser exists but is not integrated; frontend binds to wrong data fields.

---

## Emergency Fix Tasks

### Fix #1: Update Frontend Data Binding (IMMEDIATE)

**Task ID**: HOTFIX-PARSE-001
**SpecKit Reference**: Related to T7.17-T7.23 (Frontend components)
**Priority**: P0
**Estimated Time**: 1 hour
**Status**: ⏳ Pending

**Problem**:
- Frontend displays article ID (902386) instead of title and author
- Component binds to `data.title` and `data.author` instead of parsing fields

**Solution**:
Update `frontend/src/components/ArticleReview/ParsingReviewPanel.tsx`:

```tsx
// Line 70: Change from
title: data.articleReview?.title?.trim() || data.title || '',

// To
title: data.title_main || data.articleReview?.title?.trim() || data.title || '',

// Line 71: Change from
author: data.author || '',

// To
author: data.author_name || data.author || '',
```

**Files to Modify**:
- `frontend/src/components/ArticleReview/ParsingReviewPanel.tsx`

**Acceptance Criteria**:
- [ ] Title displays parsed title_main, not article ID
- [ ] Author displays parsed author_name, not article ID
- [ ] Falls back to old fields if parsing fields don't exist
- [ ] No TypeScript errors

---

### Fix #2: Verify Database Schema (IMMEDIATE)

**Task ID**: HOTFIX-PARSE-002
**SpecKit Reference**: T7.1, T7.2, T7.3, T7.4 (Database Schema)
**Priority**: P0
**Estimated Time**: 30 minutes
**Status**: ⏳ Pending

**Problem**:
- Unknown if parsing fields exist in database
- May need to run migrations

**Solution**:
1. Check if migrations exist and are applied
2. Run migrations if needed
3. Verify columns exist

**Commands**:
```bash
cd /home/kingofalbert/projects/CMS/backend

# Check current migration status
.venv/bin/alembic current

# Check migration history
.venv/bin/alembic history | grep -i "parsing\|phase.*7"

# If migration exists but not applied
.venv/bin/alembic upgrade head

# Verify schema
psql $DATABASE_URL -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'articles'
AND column_name IN (
  'title_prefix', 'title_main', 'title_suffix',
  'author_name', 'author_line',
  'meta_description', 'seo_keywords', 'tags',
  'parsing_confirmed'
)
ORDER BY column_name;
"
```

**Acceptance Criteria**:
- [ ] Migration status confirmed
- [ ] All parsing columns exist in articles table
- [ ] Data types are correct
- [ ] Indexes created if specified

---

### Fix #3: Integrate Parser into Import Workflow (HIGH PRIORITY)

**Task ID**: HOTFIX-PARSE-003
**SpecKit Reference**: T7.15 (Integrate Parser into Google Drive Sync)
**Priority**: P0
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

**Problem**:
- ArticleParserService exists but is never called
- Articles imported without parsing

**Solution**:
Update Google Drive sync or worklist pipeline to call parser after import.

**Option A: Add to Google Drive Sync** (Recommended)
File: `backend/src/services/google_drive/sync_service.py`

```python
from src.services.parser.article_parser import ArticleParserService
from src.config.settings import get_settings

async def process_document(self, doc_id: str, worklist_item_id: int):
    # ... existing import logic ...

    # After creating article
    article = await self.create_article_from_doc(doc_content)

    # NEW: Parse the article
    settings = get_settings()
    parser = ArticleParserService(
        use_ai=True,
        anthropic_api_key=settings.ANTHROPIC_API_KEY
    )

    parsing_result = parser.parse_document(article.content)

    if parsing_result.success:
        parsed = parsing_result.parsed_article

        # Update article with parsed data
        article.title_main = parsed.title_main
        article.title_prefix = parsed.title_prefix
        article.title_suffix = parsed.title_suffix
        article.author_name = parsed.author_name
        article.author_line = parsed.author_line
        article.meta_description = parsed.meta_description
        article.seo_keywords = parsed.seo_keywords
        article.tags = parsed.tags
        article.parsing_confirmed = False  # Needs review

        # Save images to article_images table
        for img in parsed.images:
            await self.create_article_image(article.id, img)

        await session.commit()
        logger.info(f"Article {article.id} parsed successfully")
    else:
        logger.warning(f"Article {article.id} parsing failed: {parsing_result.errors}")
        # Continue without parsing - allow manual review
```

**Option B: Add to Worklist Pipeline**
File: `backend/src/services/worklist/pipeline.py`

```python
async def process_parsing_step(self, worklist_item: WorklistItem):
    """Parse article after import (Phase 7)"""
    if not worklist_item.article_id:
        return

    article = await self.get_article(worklist_item.article_id)
    if not article or article.parsing_confirmed:
        return  # Already parsed

    # Call parser
    settings = get_settings()
    parser = ArticleParserService(
        use_ai=True,
        anthropic_api_key=settings.ANTHROPIC_API_KEY
    )

    result = parser.parse_document(article.content)

    if result.success:
        await self.save_parsing_results(article, result.parsed_article)
        worklist_item.status = "parsing_completed"
    else:
        worklist_item.status = "parsing_failed"
        # Log errors for debugging
```

**Files to Modify**:
- `backend/src/services/google_drive/sync_service.py` OR
- `backend/src/services/worklist/pipeline.py`

**Acceptance Criteria**:
- [ ] Parser is called automatically after article import
- [ ] Parsed data is saved to database
- [ ] Errors are logged but don't block import
- [ ] Images are saved to article_images table
- [ ] Parsing status is tracked (parsing_confirmed field)

---

### Fix #4: Update Worklist API Response (HIGH PRIORITY)

**Task ID**: HOTFIX-PARSE-004
**SpecKit Reference**: T7.13 (Extend Worklist API Response)
**Priority**: P0
**Estimated Time**: 1 hour
**Status**: ⏳ Pending

**Problem**:
- Worklist API doesn't return parsing fields
- Frontend cannot access title_main, author_name, etc.

**Solution**:
Update Pydantic schemas and API routes.

**File**: `backend/src/api/schemas/worklist.py`

```python
class WorklistItemDetail(BaseModel):
    """Worklist item detail response"""
    id: int
    article_id: int | None

    # Original fields (keep for backward compatibility)
    title: str | None
    author: str | None

    # Phase 7: Parsing fields
    title_main: str | None = None
    title_prefix: str | None = None
    title_suffix: str | None = None
    author_name: str | None = None
    author_line: str | None = None
    meta_description: str | None = None
    seo_keywords: list[str] = []
    tags: list[str] = []

    # Parsing status
    parsing_confirmed: bool = False
    parsing_confirmed_at: datetime | None = None

    # ... other fields ...
```

**File**: `backend/src/api/routes/worklist_routes.py`

```python
@router.get("/{worklist_item_id}", response_model=WorklistItemDetail)
async def get_worklist_item(
    worklist_item_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get worklist item with article parsing data"""

    # Join with articles table to get parsing fields
    query = select(WorklistItem).options(
        selectinload(WorklistItem.article)
    ).where(WorklistItem.id == worklist_item_id)

    result = await session.execute(query)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")

    # Build response with parsing fields
    response_data = {
        "id": item.id,
        "title": item.title,
        "author": item.author,
        # ... other fields ...
    }

    # Add parsing fields if article exists
    if item.article:
        response_data.update({
            "title_main": item.article.title_main,
            "title_prefix": item.article.title_prefix,
            "title_suffix": item.article.title_suffix,
            "author_name": item.article.author_name,
            "author_line": item.article.author_line,
            "meta_description": item.article.meta_description,
            "seo_keywords": item.article.seo_keywords or [],
            "tags": item.article.tags or [],
            "parsing_confirmed": item.article.parsing_confirmed,
            "parsing_confirmed_at": item.article.parsing_confirmed_at,
        })

    return WorklistItemDetail(**response_data)
```

**Files to Modify**:
- `backend/src/api/schemas/worklist.py`
- `backend/src/api/routes/worklist_routes.py`

**Acceptance Criteria**:
- [ ] API returns parsing fields in response
- [ ] Backward compatibility maintained (old fields still present)
- [ ] Null values handled correctly
- [ ] API documentation updated (Swagger/OpenAPI)

---

### Fix #5: Update Frontend Type Definitions (MEDIUM PRIORITY)

**Task ID**: HOTFIX-PARSE-005
**SpecKit Reference**: Related to T7.17-T7.23
**Priority**: P1
**Estimated Time**: 30 minutes
**Status**: ⏳ Pending

**Problem**:
- TypeScript types don't include parsing fields
- May cause type errors after API update

**Solution**:
Update type definitions to match new API response.

**File**: `frontend/src/types/worklist.ts`

```typescript
export interface WorklistItemDetail {
  id: number;
  article_id?: number;

  // Original fields
  title?: string;
  author?: string;

  // Phase 7: Parsing fields
  title_main?: string;
  title_prefix?: string;
  title_suffix?: string;
  author_name?: string;
  author_line?: string;
  meta_description?: string;
  seo_keywords?: string[];
  tags?: string[];

  // Parsing status
  parsing_confirmed?: boolean;
  parsing_confirmed_at?: string;

  // ... other fields ...
}
```

**Files to Modify**:
- `frontend/src/types/worklist.ts`
- `frontend/src/types/api.ts` (if needed)

**Acceptance Criteria**:
- [ ] All parsing fields defined in types
- [ ] No TypeScript errors
- [ ] Types match API response exactly

---

## Implementation Order

**Phase 1: Immediate Fixes (1-2 hours)**
1. ✅ Fix #2: Verify database schema
2. ✅ Fix #1: Update frontend data binding
3. ✅ Fix #5: Update TypeScript types

**Phase 2: Integration (3-4 hours)**
4. ✅ Fix #4: Update Worklist API
5. ✅ Fix #3: Integrate parser into workflow

**Phase 3: Validation (1 hour)**
6. ✅ Re-run visual test
7. ✅ Verify all fields display correctly
8. ✅ Test with real article data

---

## Testing Checklist

After all fixes:

- [ ] Visual test passes (no "902386" displayed)
- [ ] Title shows actual parsed title
- [ ] Author shows actual parsed author name
- [ ] Meta description shows content (if exists)
- [ ] SEO keywords display correctly
- [ ] Images display with metadata
- [ ] FAQ suggestions display
- [ ] No console errors
- [ ] API returns parsing fields
- [ ] Database has all required columns

---

## Rollback Plan

If fixes cause issues:

1. **Frontend**: Revert ParsingReviewPanel.tsx changes
2. **Backend**: Don't call parser (comment out integration)
3. **API**: Keep new fields (backward compatible)
4. **Database**: Don't rollback migration (data preserved)

---

## Related Documents

- `PARSING_VISUAL_TEST_ANALYSIS.md` - Full analysis report
- `specs/001-cms-automation/tasks.md` - Phase 7 full task list
- `specs/001-cms-automation/spec.md` - Phase 7 requirements
- `docs/PARSING_FEATURE_SUMMARY.md` - Feature overview

---

## Success Criteria

All fixes successful when:
1. ✅ Visual test shows real data, not article IDs
2. ✅ All parsing fields populate correctly
3. ✅ No breaking changes to existing functionality
4. ✅ Ready to continue Phase 7 implementation

---

**Total Estimated Time**: 6-7 hours
**Priority**: Must fix before continuing Phase 7
**Assignee**: Backend + Frontend developer
**Review**: After Fix #3, before merging
