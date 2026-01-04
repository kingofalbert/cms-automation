# Spec 017: WordPress Draft URL Capture and Confirmation UI

## Overview

After successful WordPress draft upload via Computer Use, capture the draft URL and screenshot, store in database with timestamp, and display in UI for visual confirmation.

## Requirements

### 1. Data Capture
- Capture WordPress draft URL after successful upload
- Store draft URL with upload timestamp in database
- Store WordPress post ID for reference

### 2. UI Display
- Display WordPress draft URL (clickable link) in confirmation UI
- Display upload timestamp
- Display final screenshot of WordPress draft for visual verification
- Screenshot is for UI display only (already stored in PublishTask)

## Current Architecture Analysis

### Existing Data Flow
```
Frontend (PublishPreviewPanel)
    ↓ onPublish(settings)
Backend (/api/v1/worklist/{id}/publish)
    ↓ Creates PublishTask
    ↓ Queues Celery task
    ↓ Orchestrator.publish_article()
    ↓ ComputerUseCMSService.publish_article_with_seo()
    ↓ Returns: { success, cms_article_id, url, editor_url, screenshots }
    ↓ Orchestrator._finalize_success() updates Article model
Frontend (polls task status, shows progress)
```

### Existing Fields
**Article model** (already has):
- `cms_article_id` - WordPress post ID
- `published_url` - URL (used for both draft and published)
- `published_at` - Timestamp (null for drafts)

**PublishTask model** (already has):
- `screenshots` - JSONB array of screenshot URLs
- `completed_at` - Completion timestamp
- `status` - Task status

**WorklistItem model** (missing):
- No WordPress-specific fields currently

## Implementation Plan

### Phase 1: Database Schema Update

#### Migration: Add WordPress draft fields to worklist_items
```sql
ALTER TABLE worklist_items ADD COLUMN wordpress_draft_url VARCHAR(500);
ALTER TABLE worklist_items ADD COLUMN wordpress_draft_uploaded_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE worklist_items ADD COLUMN wordpress_post_id INTEGER;
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `wordpress_draft_url` | String(500) | WordPress draft editor URL |
| `wordpress_draft_uploaded_at` | DateTime (with TZ) | Upload timestamp |
| `wordpress_post_id` | Integer | WordPress post ID |

### Phase 2: Backend Changes

#### 2.1 Update WorklistItem Model
Add new columns to `backend/src/models/worklist.py`:
```python
wordpress_draft_url: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True,
    comment="WordPress draft URL after upload",
)
wordpress_draft_uploaded_at: Mapped[datetime | None] = mapped_column(
    nullable=True,
    comment="Timestamp when draft was uploaded to WordPress",
)
wordpress_post_id: Mapped[int | None] = mapped_column(
    Integer,
    nullable=True,
    comment="WordPress post ID",
)
```

#### 2.2 Update Publishing Flow
Modify `backend/src/services/publishing/orchestrator.py`:
- In `_finalize_success()`, also update linked WorklistItem
- Set `wordpress_draft_url`, `wordpress_draft_uploaded_at`, `wordpress_post_id`

```python
async def _finalize_success(self, publish_task_id: int, result: dict) -> None:
    # ... existing code ...

    # Update linked worklist item
    if article and article.worklist_item:
        worklist_item = article.worklist_item
        worklist_item.wordpress_draft_url = editor_url or public_url
        worklist_item.wordpress_draft_uploaded_at = datetime.utcnow()
        worklist_item.wordpress_post_id = result.get("cms_article_id")
        worklist_item.status = WorklistStatus.PUBLISHED
        session.add(worklist_item)
```

#### 2.3 Update API Response Schema
Add new fields to worklist response schema:
```python
class WorklistItemResponse(BaseModel):
    # ... existing fields ...
    wordpress_draft_url: str | None = None
    wordpress_draft_uploaded_at: datetime | None = None
    wordpress_post_id: int | None = None
```

#### 2.4 Add Endpoint for Publishing Result
Create or update endpoint to return publishing result details:
```
GET /api/v1/worklist/{id}/publish-result
Response: {
    "wordpress_draft_url": "https://...",
    "wordpress_draft_uploaded_at": "2025-01-04T12:00:00Z",
    "wordpress_post_id": 12345,
    "screenshots": ["url1", "url2", ...],
    "status": "published"
}
```

### Phase 3: Frontend Changes

#### 3.1 Type Definitions
Update `frontend/src/types/api.ts`:
```typescript
interface WorklistItem {
    // ... existing fields ...
    wordpress_draft_url?: string;
    wordpress_draft_uploaded_at?: string;
    wordpress_post_id?: number;
}

interface PublishResult {
    wordpress_draft_url: string;
    wordpress_draft_uploaded_at: string;
    wordpress_post_id: number;
    screenshots: Screenshot[];
    status: 'published' | 'draft' | 'failed';
}
```

#### 3.2 Create PublishSuccessConfirmation Component
New component: `frontend/src/components/ArticleReview/PublishSuccessConfirmation.tsx`

**Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✓ 上稿成功                                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     [WordPress Draft Screenshot]                     │   │
│  │                         (Click to enlarge)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  📰 WordPress 草稿資訊                                                      │
│  ────────────────────────────────────────────────────────────────────────  │
│  文章標題: {title}                                                          │
│  WordPress 草稿連結: [https://admin.epochtimes.com/wp-admin/post.php?...]  │
│  上傳時間: 2025-01-04 12:00:00                                             │
│  WordPress 文章 ID: 12345                                                   │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  💡 下一步                                                                  │
│  • 點擊上方連結前往 WordPress 後台查看草稿                                   │
│  • 最終審稿編輯可在 WordPress 後台進行最後審核並發布                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                              [打開 WordPress] [關閉]        │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Props:**
```typescript
interface PublishSuccessConfirmationProps {
    articleTitle: string;
    wordpressDraftUrl: string;
    uploadedAt: string;
    wordpressPostId: number;
    screenshot?: string;  // Final screenshot URL
    onClose: () => void;
    onOpenWordPress: () => void;
}
```

#### 3.3 Update PublishPreviewPanel Flow
Modify `frontend/src/components/ArticleReview/PublishPreviewPanel.tsx`:

**Current Flow:**
```
User clicks "上稿" → PublishConfirmation → onPublish() → Close modal
```

**New Flow:**
```
User clicks "上稿" → PublishConfirmation → onPublish() →
  → Show loading state
  → On success: Show PublishSuccessConfirmation with URL + Screenshot
  → User can close or open WordPress
```

**State Changes:**
```typescript
const [publishState, setPublishState] = useState<
    'idle' | 'confirming' | 'publishing' | 'success' | 'failed'
>('idle');
const [publishResult, setPublishResult] = useState<PublishResult | null>(null);
```

#### 3.4 Screenshot Display Component
The screenshot should be displayed in a clickable thumbnail that can expand to full view.

Already have `ScreenshotGallery` component - can reuse for single screenshot display.

### Phase 4: Integration with ArticleReviewModal

#### 4.1 Update Article Review Data Hook
Modify `useArticleReviewData.ts` to include WordPress draft info:
```typescript
const articleReviewData = {
    // ... existing fields ...
    wordpress_draft_url: worklistItem?.wordpress_draft_url,
    wordpress_draft_uploaded_at: worklistItem?.wordpress_draft_uploaded_at,
    wordpress_post_id: worklistItem?.wordpress_post_id,
};
```

#### 4.2 Update ArticleReviewData Type
```typescript
interface ArticleReviewData {
    // ... existing fields ...
    wordpress_draft_url?: string;
    wordpress_draft_uploaded_at?: string;
    wordpress_post_id?: number;
}
```

## Visual Testing Plan

### Test 1: Database Migration
1. Run migration in dev environment
2. Verify new columns exist in worklist_items table
3. Verify nullable constraints work correctly

### Test 2: Publishing Flow
1. Navigate to CMS frontend
2. Select an article in "ready_to_publish" status
3. Open article review modal, go to "上稿預覽" tab
4. Click "上稿" button
5. Confirm in PublishConfirmation dialog
6. Wait for Computer Use to complete
7. Verify PublishSuccessConfirmation appears with:
   - WordPress draft URL (clickable)
   - Upload timestamp
   - Final screenshot visible
   - WordPress post ID displayed

### Test 3: WordPress Draft URL
1. Click the WordPress draft URL in success confirmation
2. Verify it opens WordPress admin in new tab
3. Verify the draft article is visible in WordPress

### Test 4: Screenshot Display
1. Verify screenshot is visible in success confirmation
2. Click screenshot to enlarge
3. Verify full screenshot is displayed correctly

### Test 5: Database Storage
1. After successful publish, query worklist_items
2. Verify wordpress_draft_url is populated
3. Verify wordpress_draft_uploaded_at has correct timestamp
4. Verify wordpress_post_id matches WordPress

## File Changes Summary

### New Files
1. `backend/migrations/versions/20260104_xxxx_add_wordpress_draft_fields.py` - Migration
2. `frontend/src/components/ArticleReview/PublishSuccessConfirmation.tsx` - Success UI

### Modified Files
1. `backend/src/models/worklist.py` - Add WordPress fields
2. `backend/src/services/publishing/orchestrator.py` - Update worklist on success
3. `backend/src/api/schemas/worklist.py` - Add new fields to schema
4. `frontend/src/types/api.ts` - Add TypeScript types
5. `frontend/src/components/ArticleReview/PublishPreviewPanel.tsx` - Add success state
6. `frontend/src/hooks/articleReview/useArticleReviewData.ts` - Include WordPress info

## TaskMaster Tasks

```
Task 1: Create database migration for WordPress draft fields
Task 2: Update WorklistItem model with new columns
Task 3: Update publishing orchestrator to save WordPress info
Task 4: Update API schemas for new fields
Task 5: Create PublishSuccessConfirmation component
Task 6: Update PublishPreviewPanel with success flow
Task 7: Update useArticleReviewData hook
Task 8: Visual testing of entire flow
```

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Database Schema | Small |
| Backend Changes | Medium |
| Frontend Changes | Medium |
| Visual Testing | Medium |
| **Total** | Medium-Large |

## Dependencies

- Existing publishing infrastructure (PublishTask, orchestrator)
- Computer Use CMS service
- Article review modal components
- Worklist API routes
