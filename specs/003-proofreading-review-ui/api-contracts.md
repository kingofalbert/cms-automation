# 校对审核页面 - API 契约文档

**Feature:** Proofreading Review UI
**Created:** 2025-11-07
**API Version:** v1

---

## 📋 Overview

本文档定义校对审核页面所需的后端API契约。包括已存在的API和需要新增的API。

---

## ✅ Existing APIs

### 1. GET /v1/worklist/{id}

**Status:** ✅ Already Implemented

**Purpose:** 获取Worklist详情，包括文章内容、校对问题、状态历史

**Request:**
```http
GET /v1/worklist/123 HTTP/1.1
Host: api.cms-automation.com
Authorization: Bearer <token>
```

**Response:** 200 OK
```typescript
{
  // Worklist基本信息
  id: number;
  drive_file_id: string;
  title: string;
  content: string;                    // 文章正文（Markdown/HTML）
  status: WorklistStatus;             // pending | proofreading | under_review | ready_to_publish | publishing | published | failed
  author: string | null;

  // 关联Article信息
  article_id: number | null;
  article_status: string | null;      // imported | draft | in-review | ready_to_publish | published | failed

  // WordPress分类法
  tags: string[];
  categories: string[];
  meta_description: string | null;
  seo_keywords: string[];

  // Google Drive元数据
  drive_metadata: {
    web_view_link?: string;
    web_content_link?: string;
    modified_time?: string;
    owners?: Array<{name: string; email: string}>;
    [key: string]: any;
  };

  // 审核备注
  notes: Array<{
    id?: number;
    message?: string;
    content?: string;
    level?: 'info' | 'warning' | 'error';
    author?: string | null;
    created_at?: string;
    resolved?: boolean;
  }>;

  // 状态历史
  article_status_history: Array<{
    old_status: string | null;
    new_status: string;
    changed_by: string | null;       // user_id or 'system'
    change_reason: string | null;
    metadata: Record<string, any>;
    created_at: string;
  }>;

  // 时间戳
  synced_at: string;
  created_at: string;
  updated_at: string;
}
```

**Notes:**
- ❌ **Missing Field**: `proofreading_issues` 不在当前响应中
- **Required Enhancement**: 需要在响应中包含 `article.proofreading_issues`

---

## 🆕 New APIs Required

### 2. POST /v1/worklist/{id}/review-decisions

**Status:** 🆕 Needs Implementation

**Purpose:** 保存审核决策并转换状态

**Request:**
```http
POST /v1/worklist/123/review-decisions HTTP/1.1
Host: api.cms-automation.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "decisions": [
    {
      "issue_id": "issue-001",
      "decision_type": "accepted",        // "accepted" | "rejected" | "modified"
      "decision_rationale": "建议合理，语法正确",
      "modified_content": null,           // Only for "modified" type
      "feedback_provided": true,
      "feedback_category": "suggestion_correct", // "suggestion_correct" | "suggestion_partially_correct" | "suggestion_incorrect" | "rule_needs_adjustment"
      "feedback_notes": "AI建议准确"
    },
    {
      "issue_id": "issue-002",
      "decision_type": "modified",
      "decision_rationale": "建议需要微调",
      "modified_content": "他们决定去公园散步",
      "feedback_provided": false,
      "feedback_category": null,
      "feedback_notes": null
    },
    {
      "issue_id": "issue-003",
      "decision_type": "rejected",
      "decision_rationale": "原文更合适",
      "modified_content": null,
      "feedback_provided": true,
      "feedback_category": "suggestion_incorrect",
      "feedback_notes": "这个规则对这个场景不适用"
    }
  ],
  "review_notes": "整体校对质量良好，主要是标点符号问题",
  "transition_to": "ready_to_publish"   // "ready_to_publish" | "proofreading" | "failed" | null (no transition)
}
```

**Response:** 200 OK
```typescript
{
  "success": true,
  "saved_decisions_count": 3,
  "worklist_item": {
    "id": 123,
    "status": "ready_to_publish",      // Updated status
    "updated_at": "2025-11-07T10:30:00Z"
  },
  "article": {
    "id": 456,
    "status": "ready_to_publish",      // Updated status
    "updated_at": "2025-11-07T10:30:00Z"
  },
  "errors": []
}
```

**Error Responses:**

400 Bad Request - Invalid Input
```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid decision data",
  "details": {
    "decisions[0].issue_id": "Issue not found",
    "decisions[1].modified_content": "Required for modified type"
  }
}
```

409 Conflict - Concurrent Modification
```json
{
  "success": false,
  "error": "concurrent_modification",
  "message": "Worklist item has been modified by another user",
  "current_version": 15,
  "your_version": 12
}
```

**Backend Implementation Notes:**

```python
# backend/src/api/v1/worklist.py

@router.post("/{id}/review-decisions")
async def save_review_decisions(
    id: int,
    payload: ReviewDecisionsPayload,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> ReviewDecisionsResponse:
    """
    保存审核决策：
    1. 验证worklist_item存在且状态为under_review
    2. 获取关联的article
    3. 为每个决策创建ProofreadingDecision记录
    4. 更新WorklistItem和Article的状态
    5. 创建ArticleStatusHistory记录
    6. 添加审核备注到worklist_item.notes
    7. 返回更新结果
    """
    ...
```

```python
# backend/src/services/worklist/service.py

class WorklistService:
    async def save_review_decisions(
        self,
        item_id: int,
        decisions: List[DecisionPayload],
        review_notes: str,
        transition_to: str | None,
        user_id: int,
    ) -> ReviewDecisionsResult:
        # 1. Get worklist item and article
        item = await self.get_item(item_id)
        if not item or not item.article_id:
            raise ValueError("Invalid worklist item")

        article = await session.get(Article, item.article_id)
        if not article:
            raise ValueError("Article not found")

        # 2. Validate all issue_ids exist
        issue_ids = {d.issue_id for d in decisions}
        existing_issues = {issue['id'] for issue in article.proofreading_issues}
        invalid_ids = issue_ids - existing_issues
        if invalid_ids:
            raise ValueError(f"Invalid issue IDs: {invalid_ids}")

        # 3. Create ProofreadingDecision records
        saved_count = 0
        for decision_payload in decisions:
            # Find the issue in article.proofreading_issues
            issue = next(
                (i for i in article.proofreading_issues if i['id'] == decision_payload.issue_id),
                None
            )
            if not issue:
                continue

            # Create decision record
            decision = ProofreadingDecision(
                article_id=article.id,
                suggestion_id=decision_payload.issue_id,
                decision_type=DecisionType(decision_payload.decision_type),
                decision_rationale=decision_payload.decision_rationale,
                modified_content=decision_payload.modified_content,
                original_text=issue['original_text'],
                suggested_text=issue['suggested_text'],
                rule_id=issue['rule_id'],
                rule_category=issue.get('rule_category'),
                issue_position=issue.get('position'),
                feedback_provided=decision_payload.feedback_provided,
                feedback_category=decision_payload.feedback_category,
                feedback_notes=decision_payload.feedback_notes,
                feedback_status=FeedbackStatus.PENDING if decision_payload.feedback_provided else None,
                decided_by=user_id,
                decided_at=datetime.utcnow(),
            )
            session.add(decision)
            saved_count += 1

        # 4. Update statuses if transition_to is specified
        if transition_to:
            old_worklist_status = item.status
            old_article_status = article.status

            if transition_to == 'ready_to_publish':
                item.mark_status(WorklistStatus.READY_TO_PUBLISH)
                article.status = ArticleStatus.READY_TO_PUBLISH
            elif transition_to == 'proofreading':
                item.mark_status(WorklistStatus.PROOFREADING)
                article.status = ArticleStatus.DRAFT
            elif transition_to == 'failed':
                item.mark_status(WorklistStatus.FAILED)
                article.status = ArticleStatus.FAILED

            # Create status history
            history = ArticleStatusHistory(
                article_id=article.id,
                old_status=old_article_status.value,
                new_status=article.status.value,
                changed_by=str(user_id),
                change_reason=f"review_completed_transition_to_{transition_to}",
                metadata={
                    "worklist_id": item.id,
                    "decisions_count": saved_count,
                    "review_notes": review_notes,
                },
            )
            session.add(history)

        # 5. Add review notes
        if review_notes:
            item.add_note({
                "message": review_notes,
                "level": "info",
                "author": str(user_id),
                "created_at": datetime.utcnow().isoformat(),
            })

        await session.commit()

        return ReviewDecisionsResult(
            success=True,
            saved_decisions_count=saved_count,
            worklist_item=item,
            article=article,
            errors=[],
        )
```

---

### 3. GET /v1/worklist/{id}/proofreading-history

**Status:** 🆕 Needs Implementation (Optional)

**Purpose:** 获取文章的历史校对记录

**Request:**
```http
GET /v1/worklist/123/proofreading-history HTTP/1.1
Host: api.cms-automation.com
Authorization: Bearer <token>
```

**Response:** 200 OK
```typescript
{
  "history": [
    {
      "id": 1001,
      "article_id": 456,
      "executed_at": "2025-11-07T10:00:00Z",
      "execution_duration_ms": 3500,
      "engine_version": "v2.1.0",

      // 问题统计
      "total_issues_found": 24,
      "critical_issues_count": 3,
      "warning_issues_count": 12,
      "info_issues_count": 9,

      // 决策统计
      "accepted_count": 15,
      "rejected_count": 5,
      "modified_count": 2,
      "pending_count": 2,

      // 反馈统计
      "feedback_provided_count": 8,
      "pending_feedback_count": 3,

      // 引擎分布
      "deterministic_issues_count": 10,
      "ai_issues_count": 14,

      // 执行人
      "executed_by": null,  // System execution
      "created_at": "2025-11-07T10:00:00Z"
    },
    // ... more history entries
  ],
  "total": 1
}
```

**Backend Implementation:**
```python
@router.get("/{id}/proofreading-history")
async def get_proofreading_history(
    id: int,
    session: AsyncSession = Depends(get_async_session),
) -> ProofreadingHistoryResponse:
    item = await session.get(WorklistItem, id)
    if not item or not item.article_id:
        raise HTTPException(status_code=404)

    # Query proofreading_history table
    stmt = (
        select(ProofreadingHistory)
        .where(ProofreadingHistory.article_id == item.article_id)
        .order_by(ProofreadingHistory.executed_at.desc())
    )
    result = await session.execute(stmt)
    history_records = result.scalars().all()

    return {
        "history": [
            {
                "id": h.id,
                "article_id": h.article_id,
                "executed_at": h.executed_at.isoformat(),
                "execution_duration_ms": h.execution_duration_ms,
                "engine_version": h.engine_version,
                "total_issues_found": h.total_issues_found,
                "critical_issues_count": h.critical_issues_count,
                "warning_issues_count": h.warning_issues_count,
                "info_issues_count": h.info_issues_count,
                "accepted_count": h.accepted_count,
                "rejected_count": h.rejected_count,
                "modified_count": h.modified_count,
                "pending_count": h.pending_count,
                "feedback_provided_count": h.feedback_provided_count,
                "pending_feedback_count": h.pending_feedback_count,
                "deterministic_issues_count": h.deterministic_issues_count,
                "ai_issues_count": h.ai_issues_count,
                "executed_by": h.executed_by,
                "created_at": h.created_at.isoformat(),
            }
            for h in history_records
        ],
        "total": len(history_records),
    }
```

---

### 4. POST /v1/worklist/{id}/batch-decisions

**Status:** 🆕 Needs Implementation (Optional)

**Purpose:** 批量接受或拒绝多个问题

**Request:**
```http
POST /v1/worklist/123/batch-decisions HTTP/1.1
Host: api.cms-automation.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "issue_ids": ["issue-001", "issue-002", "issue-003"],
  "decision_type": "accepted",          // "accepted" | "rejected"
  "rationale": "所有建议都合理"
}
```

**Response:** 200 OK
```typescript
{
  "success": true,
  "processed_count": 3,
  "failed": [],
  "saved_decisions": [
    {
      "issue_id": "issue-001",
      "decision_id": 1001,
      "decision_type": "accepted"
    },
    {
      "issue_id": "issue-002",
      "decision_id": 1002,
      "decision_type": "accepted"
    },
    {
      "issue_id": "issue-003",
      "decision_id": 1003,
      "decision_type": "accepted"
    }
  ]
}
```

**Implementation:**
```python
@router.post("/{id}/batch-decisions")
async def save_batch_decisions(
    id: int,
    payload: BatchDecisionsPayload,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> BatchDecisionsResponse:
    """
    批量决策的便捷API，内部调用save_review_decisions
    """
    decisions = [
        DecisionPayload(
            issue_id=issue_id,
            decision_type=payload.decision_type,
            decision_rationale=payload.rationale,
            modified_content=None,
            feedback_provided=False,
            feedback_category=None,
            feedback_notes=None,
        )
        for issue_id in payload.issue_ids
    ]

    # Reuse the main decision-saving logic
    result = await worklist_service.save_review_decisions(
        item_id=id,
        decisions=decisions,
        review_notes=f"Batch {payload.decision_type}: {payload.rationale}",
        transition_to=None,  # Don't transition status
        user_id=current_user.id,
    )

    return {
        "success": result.success,
        "processed_count": result.saved_decisions_count,
        "failed": result.errors,
        "saved_decisions": [
            {"issue_id": d.issue_id, "decision_id": d.id, "decision_type": d.decision_type}
            for d in result.decisions
        ],
    }
```

---

## 🔄 Enhanced Existing API

### 5. GET /v1/worklist/{id} (Enhanced)

**Enhancement Needed:** 在响应中包含 `proofreading_issues`

**Updated Response:**
```typescript
{
  // ... existing fields ...

  // ✅ NEW: Proofreading Issues
  "proofreading_issues": [
    {
      "id": "issue-001",
      "rule_id": "R-GRAMMAR-001",
      "rule_category": "grammar",
      "severity": "critical",             // "critical" | "warning" | "info"
      "engine": "ai",                     // "ai" | "deterministic"
      "position": {
        "start": 150,
        "end": 160,
        "line": 5,
        "column": 12
      },
      "original_text": "他们决定去公园玩耍",
      "suggested_text": "他们决定去公园玩",
      "explanation": ""玩耍"是冗余表达，"玩"即可",
      "explanation_detail": "在现代汉语中，"玩"作为动词已经包含了娱乐活动的含义，无需再加"耍"字。",
      "confidence": 0.92,                 // AI confidence (0-1), null for deterministic
      "decision_status": "pending",       // "pending" | "accepted" | "rejected" | "modified"
      "decision_id": null,                // ID of ProofreadingDecision if decided
      "tags": ["redundancy", "grammar"]
    },
    // ... more issues
  ],

  // ✅ NEW: Proofreading Statistics
  "proofreading_stats": {
    "total_issues": 24,
    "critical_count": 3,
    "warning_count": 12,
    "info_count": 9,
    "pending_count": 15,
    "accepted_count": 6,
    "rejected_count": 2,
    "modified_count": 1,
    "ai_issues_count": 14,
    "deterministic_issues_count": 10
  }
}
```

**Backend Implementation:**
```python
# backend/src/api/v1/worklist.py

@router.get("/{id}")
async def get_worklist_item(
    id: int,
    session: AsyncSession = Depends(get_async_session),
) -> WorklistItemDetailResponse:
    service = WorklistService(session)
    item = await service.get_item(id)

    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")

    # Get article with proofreading issues
    article = None
    proofreading_issues = []
    proofreading_stats = None

    if item.article_id:
        article = await session.get(Article, item.article_id)
        if article:
            # Parse proofreading_issues from article
            proofreading_issues = article.proofreading_issues or []

            # Get decisions for each issue
            stmt = select(ProofreadingDecision).where(
                ProofreadingDecision.article_id == article.id
            )
            result = await session.execute(stmt)
            decisions = {d.suggestion_id: d for d in result.scalars().all()}

            # Enrich issues with decision status
            for issue in proofreading_issues:
                decision = decisions.get(issue['id'])
                if decision:
                    issue['decision_status'] = decision.decision_type.value
                    issue['decision_id'] = decision.id
                else:
                    issue['decision_status'] = 'pending'
                    issue['decision_id'] = None

            # Calculate statistics
            proofreading_stats = calculate_proofreading_stats(proofreading_issues)

    return {
        # ... existing fields ...
        "proofreading_issues": proofreading_issues,
        "proofreading_stats": proofreading_stats,
    }
```

---

## 📊 Data Models

### TypeScript Interfaces

```typescript
// frontend/src/types/proofreading.ts

export interface ProofreadingIssue {
  id: string;
  rule_id: string;
  rule_category: string;
  severity: 'critical' | 'warning' | 'info';
  engine: 'ai' | 'deterministic';

  position: {
    start: number;
    end: number;
    line?: number;
    column?: number;
    section?: string;
  };

  original_text: string;
  suggested_text: string;
  explanation: string;
  explanation_detail?: string;

  confidence?: number;  // AI only
  decision_status: 'pending' | 'accepted' | 'rejected' | 'modified';
  decision_id?: number;
  tags?: string[];
}

export interface ProofreadingStats {
  total_issues: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  pending_count: number;
  accepted_count: number;
  rejected_count: number;
  modified_count: number;
  ai_issues_count: number;
  deterministic_issues_count: number;
}

export interface DecisionPayload {
  issue_id: string;
  decision_type: 'accepted' | 'rejected' | 'modified';
  decision_rationale?: string;
  modified_content?: string;
  feedback_provided: boolean;
  feedback_category?: 'suggestion_correct' | 'suggestion_partially_correct' | 'suggestion_incorrect' | 'rule_needs_adjustment';
  feedback_notes?: string;
}

export interface ReviewDecisionsRequest {
  decisions: DecisionPayload[];
  review_notes?: string;
  transition_to?: 'ready_to_publish' | 'proofreading' | 'failed';
}

export interface ReviewDecisionsResponse {
  success: boolean;
  saved_decisions_count: number;
  worklist_item: {
    id: number;
    status: string;
    updated_at: string;
  };
  article: {
    id: number;
    status: string;
    updated_at: string;
  };
  errors: string[];
}
```

### Python Models

```python
# backend/src/schemas/proofreading.py

from pydantic import BaseModel, Field
from typing import Literal, Optional

class DecisionPayload(BaseModel):
    issue_id: str
    decision_type: Literal["accepted", "rejected", "modified"]
    decision_rationale: Optional[str] = None
    modified_content: Optional[str] = None
    feedback_provided: bool = False
    feedback_category: Optional[Literal[
        "suggestion_correct",
        "suggestion_partially_correct",
        "suggestion_incorrect",
        "rule_needs_adjustment"
    ]] = None
    feedback_notes: Optional[str] = None

class ReviewDecisionsPayload(BaseModel):
    decisions: list[DecisionPayload]
    review_notes: Optional[str] = None
    transition_to: Optional[Literal["ready_to_publish", "proofreading", "failed"]] = None

class ReviewDecisionsResponse(BaseModel):
    success: bool
    saved_decisions_count: int
    worklist_item: dict
    article: dict
    errors: list[str] = Field(default_factory=list)
```

---

## 🔐 Authentication & Authorization

All APIs require authentication via JWT Bearer token:

```http
Authorization: Bearer <jwt_token>
```

**Authorization Rules:**
- **Read operations** (GET): Any authenticated user
- **Write operations** (POST): Users with `reviewer` or `admin` role
- **Status transitions**: Users with `admin` role only (configurable)

---

## ⚡ Performance Considerations

### Response Size Optimization

For large articles with many issues (>100):
- Consider pagination for proofreading_issues
- Or lazy loading: return issue IDs, fetch details on demand

### Caching Strategy

- Cache `GET /v1/worklist/{id}` response for 5 minutes
- Invalidate cache on POST `/review-decisions`
- Use ETag for conditional requests

### Database Queries

- Use eager loading for article relationships
- Index on `article_id`, `worklist_id`, `suggestion_id`
- Batch insert for bulk decisions

---

## 📝 Implementation Checklist

### Phase 1: Core APIs
- [ ] Enhance `GET /v1/worklist/{id}` to include proofreading_issues
- [ ] Implement `POST /v1/worklist/{id}/review-decisions`
- [ ] Add decision validation logic
- [ ] Add status transition logic
- [ ] Create ProofreadingDecision records
- [ ] Update ArticleStatusHistory

### Phase 2: Optional APIs
- [ ] Implement `GET /v1/worklist/{id}/proofreading-history`
- [ ] Implement `POST /v1/worklist/{id}/batch-decisions`
- [ ] Add pagination for large issue lists
- [ ] Add filtering query parameters

### Phase 3: Optimization
- [ ] Add response caching
- [ ] Add database indexes
- [ ] Add request rate limiting
- [ ] Add API monitoring

---

**Document Version:** 1.0
**Created:** 2025-11-07
**Status:** Ready for Implementation
