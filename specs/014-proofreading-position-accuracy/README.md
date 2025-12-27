# 014: Proofreading Issue Position Accuracy Improvement

## Problem Statement

當前校對審核 (Proofreading Review) 的問題定位機制存在以下問題：

### 現況
1. **後端**：AI 分析 HTML 內容，返回的 `position.start` 和 `position.end` 是基於 HTML 內容的字符位置
2. **前端**：顯示時使用純文字（已移除 HTML 標籤），導致位置不匹配
3. **臨時方案**：改用文字搜尋 (`indexOf`) 來定位問題文字

### 文字搜尋的潛在問題
1. **重複文字**：如果同一段文字在文章中出現多次，可能匹配到錯誤的位置
2. **順序依賴**：假設 issues 按文章順序排列
3. **找不到匹配**：如果 `original_text` 被修改過，可能找不到對應文字

## Proposed Solution

### 方案 A：後端同時提供 HTML 和純文字位置

```python
# backend/src/services/worklist/proofreading_analyzer.py

class ProofreadingIssue:
    position: Position           # 現有：HTML 位置
    plain_text_position: Position  # 新增：純文字位置
    original_text: str           # 現有：原始文字（可能含 HTML）
    original_text_plain: str     # 新增：純文字版本
```

**優點**：
- 前端可直接使用 `plain_text_position`，無需搜尋
- 位置精確，不受重複文字影響
- 向後兼容（舊欄位保留）

**缺點**：
- 需要修改後端 AI 分析邏輯
- 需要資料庫 migration

### 方案 B：後端返回純文字版本的 original_text

```python
# 確保 original_text 不含 HTML 標籤
original_text_plain = strip_html_tags(original_text)
```

**優點**：
- 修改量較小
- 前端文字搜尋更準確

**缺點**：
- 仍依賴文字搜尋，重複文字問題未解決

### 方案 C：使用唯一標識符 (Recommended)

```python
class ProofreadingIssue:
    id: str                      # 唯一 ID
    anchor_context: str          # 前後文內容（用於精確定位）
    original_text_plain: str     # 純文字版本
```

**前端定位邏輯**：
```typescript
// 使用前後文來精確定位
const contextPattern = issue.anchor_context; // e.g., "...前文20字 [TARGET] 後文20字..."
const targetIndex = findByContext(articleContent, contextPattern);
```

**優點**：
- 即使有重複文字也能準確定位
- 不依賴位置計算

**缺點**：
- 實作較複雜
- 需要額外儲存空間

## Recommended Approach

建議採用 **方案 A + B 混合**：

1. **短期**（方案 B）：確保後端返回的 `original_text` 是純文字版本
2. **長期**（方案 A）：新增 `plain_text_position` 欄位

## Implementation Tasks

### Phase 1: Backend Changes (Short-term)

- [ ] 修改 `proofreading_analyzer.py`，確保 `original_text` 和 `suggested_text` 不含 HTML 標籤
- [ ] 新增 `strip_html_tags()` 工具函數
- [ ] 更新單元測試

### Phase 2: Backend Changes (Long-term)

- [ ] 新增 `plain_text_position` 欄位到 `ProofreadingIssue` schema
- [ ] 修改 AI 分析邏輯，同時計算 HTML 和純文字位置
- [ ] 建立資料庫 migration
- [ ] 更新 API schema

### Phase 3: Frontend Changes

- [ ] 優先使用 `plain_text_position`（如果存在）
- [ ] 回退到文字搜尋（如果 `plain_text_position` 不存在）
- [ ] 新增位置驗證邏輯

## Files to Modify

### Backend
- `backend/src/services/worklist/proofreading_analyzer.py`
- `backend/src/api/schemas/worklist.py`
- `backend/src/services/parser/html_utils.py` (新增)

### Frontend
- `frontend/src/components/ProofreadingReview/ProofreadingArticleContent.tsx`
- `frontend/src/components/ProofreadingReview/ProofreadingIssueList.tsx`
- `frontend/src/types/worklist.ts`

## Success Criteria

1. 所有問題能在文章中準確高亮顯示
2. 重複文字場景能正確處理
3. 現有功能不受影響（向後兼容）
4. 單元測試覆蓋率 > 80%

## References

- 相關 commit: `9b5274d` - fix(proofreading): Strip HTML tags from article content and issue list
- 相關 spec: `003-proofreading-review-ui`
