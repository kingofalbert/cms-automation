# 014: Proofreading Issue Position Accuracy Improvement

## Overview

| 項目 | 說明 |
|------|------|
| **狀態** | Planning |
| **優先級** | High |
| **相關 Commit** | `9b5274d` - 臨時修復（使用文字搜尋） |
| **相關 Spec** | `003-proofreading-review-ui` |

---

## 1. Requirements (需求文檔)

### 1.1 Problem Statement

當前校對審核 (Proofreading Review) 的問題定位機制存在根本性缺陷：

#### 現況架構
```
[後端 AI 分析] → position: {start: 45, end: 52} (基於 HTML)
                          ↓
[前端顯示] → articleContent.slice(45, 52) (基於純文字)
                          ↓
              ❌ 位置不匹配，高亮錯誤位置
```

#### 臨時方案的問題
目前使用 `indexOf()` 文字搜尋作為臨時修復，但存在以下缺陷：

| 問題類型 | 說明 | 嚴重程度 |
|----------|------|:--------:|
| **重複文字** | 同一段文字出現多次時，`indexOf()` 只會找到第一個 | 🔴 高 |
| **順序依賴** | 假設 issues 按文章順序排列 | 🟡 中 |
| **找不到匹配** | 文字被修改後可能找不到對應內容 | 🟡 中 |
| **效能問題** | 大量 issues 時重複搜尋效能差 | 🟢 低 |

### 1.2 Functional Requirements

| ID | 需求 | 優先級 |
|----|------|:------:|
| FR-01 | 系統必須能在文章中準確高亮每個問題的位置 | P0 |
| FR-02 | 系統必須正確處理同一文字在文章中出現多次的情況 | P0 |
| FR-03 | 系統必須向後兼容現有資料格式 | P0 |
| FR-04 | 前端必須能驗證高亮位置的正確性 | P1 |
| FR-05 | 系統必須處理 HTML 實體編碼 (如 `&nbsp;`, `&amp;`) | P1 |

### 1.3 Non-Functional Requirements

| ID | 需求 | 目標值 |
|----|------|--------|
| NFR-01 | 位置計算延遲 | < 50ms per issue |
| NFR-02 | 記憶體使用增量 | < 10% |
| NFR-03 | API 回應大小增量 | < 5% |

---

## 2. Solution Design (實施方案)

### 2.1 Selected Approach: 方案 A (REQUIRED)

**方案 A 為必須實作項目**，因為只有此方案能完全解決重複文字定位問題。

#### 資料結構變更

```python
# backend/src/api/schemas/worklist.py

class Position(BaseModel):
    start: int
    end: int

class ProofreadingIssue(BaseModel):
    id: str
    issue_type: str
    severity: str
    explanation: str

    # 現有欄位 (保留向後兼容)
    position: Position              # HTML 內容位置
    original_text: str              # 原始文字 (可能含 HTML)
    suggested_text: str             # 建議文字

    # 新增欄位 (方案 A - REQUIRED)
    plain_text_position: Position   # 純文字位置 ⭐ 必須
    original_text_plain: str        # 純文字版本 ⭐ 必須
    suggested_text_plain: str       # 純文字版本 ⭐ 必須
```

#### 位置計算邏輯

```python
# backend/src/services/worklist/proofreading_analyzer.py

def calculate_plain_text_position(
    html_content: str,
    html_start: int,
    html_end: int
) -> Position:
    """
    將 HTML 位置轉換為純文字位置

    Algorithm:
    1. 取得 html_content[:html_start] 的純文字長度 → plain_start
    2. 取得 html_content[:html_end] 的純文字長度 → plain_end
    """
    plain_before = strip_html_tags(html_content[:html_start])
    plain_to_end = strip_html_tags(html_content[:html_end])

    return Position(
        start=len(plain_before),
        end=len(plain_to_end)
    )
```

#### 前端使用邏輯

```typescript
// frontend/src/components/ProofreadingReview/ProofreadingArticleContent.tsx

function getIssuePosition(issue: ProofreadingIssue, articleContent: string): { start: number; end: number } | null {
  // 優先使用 plain_text_position (方案 A)
  if (issue.plain_text_position) {
    const { start, end } = issue.plain_text_position;
    // 驗證位置有效性
    if (start >= 0 && end <= articleContent.length && start < end) {
      // 驗證文字匹配
      const extractedText = articleContent.slice(start, end);
      const expectedText = issue.original_text_plain || stripHtmlTags(issue.original_text);
      if (extractedText === expectedText) {
        return { start, end };
      }
    }
  }

  // 回退到文字搜尋 (向後兼容)
  const searchText = issue.original_text_plain || stripHtmlTags(issue.original_text);
  const foundIndex = articleContent.indexOf(searchText);
  if (foundIndex !== -1) {
    return { start: foundIndex, end: foundIndex + searchText.length };
  }

  return null; // 找不到匹配
}
```

### 2.2 Database Migration

```sql
-- migrations/versions/YYYYMMDD_add_plain_text_position.py

ALTER TABLE proofreading_issues
ADD COLUMN plain_text_position JSONB;

ALTER TABLE proofreading_issues
ADD COLUMN original_text_plain TEXT;

ALTER TABLE proofreading_issues
ADD COLUMN suggested_text_plain TEXT;

-- 為現有資料填充欄位 (可選，用於歷史資料)
-- UPDATE proofreading_issues SET ... WHERE plain_text_position IS NULL;
```

### 2.3 API Changes

```yaml
# OpenAPI Schema Update

ProofreadingIssue:
  type: object
  properties:
    # ... existing fields ...
    plain_text_position:
      type: object
      description: "Position in plain text content (without HTML tags)"
      properties:
        start:
          type: integer
        end:
          type: integer
    original_text_plain:
      type: string
      description: "Original text without HTML tags"
    suggested_text_plain:
      type: string
      description: "Suggested text without HTML tags"
```

---

## 3. Implementation Tasks (實作任務)

### Phase 1: Backend Core (必須)

| Task ID | 任務 | 預估 | 依賴 |
|---------|------|:----:|:----:|
| BE-01 | 新增 `strip_html_tags()` 工具函數到 `html_utils.py` | 2h | - |
| BE-02 | 實作 `calculate_plain_text_position()` 函數 | 3h | BE-01 |
| BE-03 | 修改 `ProofreadingIssue` schema，新增欄位 | 2h | - |
| BE-04 | 修改 `proofreading_analyzer.py`，填充新欄位 | 4h | BE-01, BE-02, BE-03 |
| BE-05 | 建立資料庫 migration | 1h | BE-03 |
| BE-06 | 更新 API schema 文檔 | 1h | BE-03 |

### Phase 2: Backend Testing (必須)

| Task ID | 任務 | 預估 | 依賴 |
|---------|------|:----:|:----:|
| BT-01 | `strip_html_tags()` 單元測試 | 2h | BE-01 |
| BT-02 | `calculate_plain_text_position()` 單元測試 | 3h | BE-02 |
| BT-03 | Proofreading analyzer 整合測試 | 4h | BE-04 |
| BT-04 | API 回應格式測試 | 2h | BE-04 |

### Phase 3: Frontend Changes (必須)

| Task ID | 任務 | 預估 | 依賴 |
|---------|------|:----:|:----:|
| FE-01 | 更新 `worklist.ts` 類型定義 | 1h | BE-03 |
| FE-02 | 實作 `getIssuePosition()` 函數 | 2h | FE-01 |
| FE-03 | 修改 `ProofreadingArticleContent.tsx` 使用新定位邏輯 | 3h | FE-02 |
| FE-04 | 修改 `ProofreadingIssueList.tsx` 使用新欄位 | 2h | FE-01 |
| FE-05 | 新增位置驗證與錯誤處理 | 2h | FE-02 |

### Phase 4: Visual Testing (必須)

| Task ID | 任務 | 預估 | 依賴 |
|---------|------|:----:|:----:|
| VT-01 | 建立視覺測試基礎設施 | 3h | - |
| VT-02 | 實作基本定位測試案例 | 4h | VT-01 |
| VT-03 | 實作邊緣情況測試案例 | 6h | VT-01 |
| VT-04 | 視覺回歸測試整合 | 2h | VT-02, VT-03 |

---

## 4. Testing Plan (測試方案)

### 4.1 Unit Tests

#### BE-01: strip_html_tags() Tests

```python
# backend/tests/unit/test_html_utils.py

class TestStripHtmlTags:
    def test_basic_tags(self):
        assert strip_html_tags("<p>Hello</p>") == "Hello"
        assert strip_html_tags("<strong>Bold</strong>") == "Bold"

    def test_nested_tags(self):
        assert strip_html_tags("<p><strong>Nested</strong></p>") == "Nested"

    def test_html_entities(self):
        assert strip_html_tags("&nbsp;") == " "
        assert strip_html_tags("&amp;") == "&"
        assert strip_html_tags("&lt;tag&gt;") == "<tag>"

    def test_mixed_content(self):
        html = "<p>段落一</p><p>段落二</p>"
        assert strip_html_tags(html) == "段落一段落二"

    def test_preserve_text(self):
        assert strip_html_tags("純文字") == "純文字"

    def test_empty_and_none(self):
        assert strip_html_tags("") == ""
        assert strip_html_tags(None) == ""
```

#### BE-02: calculate_plain_text_position() Tests

```python
# backend/tests/unit/test_position_calculator.py

class TestCalculatePlainTextPosition:
    def test_simple_tag(self):
        html = "<p>Hello World</p>"
        # "Hello" starts at position 3 in HTML, but 0 in plain text
        result = calculate_plain_text_position(html, 3, 8)
        assert result == Position(start=0, end=5)

    def test_nested_tags(self):
        html = "<p>Hello <strong>World</strong></p>"
        # "World" in HTML: start=17, end=22
        # "World" in plain: start=6, end=11
        result = calculate_plain_text_position(html, 17, 22)
        assert result == Position(start=6, end=11)

    def test_multiple_paragraphs(self):
        html = "<p>段落一</p><p>段落二</p>"
        # "段落二" in HTML: start=12, end=15
        # "段落二" in plain: start=3, end=6
        result = calculate_plain_text_position(html, 12, 15)
        assert result == Position(start=3, end=6)
```

### 4.2 Visual Test Cases (視覺測試)

#### VT-02: Basic Positioning Tests

```typescript
// frontend/tests/visual/proofreading-position.spec.ts

describe('Proofreading Issue Positioning', () => {
  test('TC-001: Single issue highlights correctly', async () => {
    // Given: Article with one issue
    const article = "這是一篇測試文章，其中有一個錯誤需要修正。";
    const issue = {
      id: "issue-1",
      plain_text_position: { start: 12, end: 14 },
      original_text_plain: "錯誤"
    };

    // When: Render proofreading view
    // Then: "錯誤" is highlighted at correct position
    await expectHighlightAt(12, 14, "錯誤");
  });

  test('TC-002: Multiple issues highlight correctly', async () => {
    // Given: Article with 3 issues in sequence
    // When: Render
    // Then: All 3 issues are highlighted at correct positions
  });

  test('TC-003: Issue at beginning of article', async () => {
    // Given: Issue at position 0
    // Then: First word is highlighted
  });

  test('TC-004: Issue at end of article', async () => {
    // Given: Issue at last position
    // Then: Last word is highlighted
  });
});
```

#### VT-03: Edge Case Tests (邊緣情況)

```typescript
// frontend/tests/visual/proofreading-edge-cases.spec.ts

describe('Proofreading Edge Cases', () => {

  // === 重複文字測試 ===

  test('TC-101: Same text appears twice - first occurrence', async () => {
    // Given: "很重要" appears twice in article
    const article = "健康飲食很重要。運動也很重要。";
    const issue = {
      plain_text_position: { start: 4, end: 7 },  // 第一個 "很重要"
      original_text_plain: "很重要"
    };

    // Then: First "很重要" is highlighted, not the second
    await expectHighlightAt(4, 7, "很重要");
    await expectNoHighlightAt(11, 14);
  });

  test('TC-102: Same text appears twice - second occurrence', async () => {
    // Given: Issue is on the SECOND "很重要"
    const issue = {
      plain_text_position: { start: 11, end: 14 },  // 第二個 "很重要"
      original_text_plain: "很重要"
    };

    // Then: Second "很重要" is highlighted
    await expectHighlightAt(11, 14, "很重要");
    await expectNoHighlightAt(4, 7);
  });

  test('TC-103: Same text appears 3+ times', async () => {
    // Given: "的" appears 5 times
    const article = "我的書、你的筆、他的車、她的貓、它的家";
    // Issue on 3rd occurrence
    const issue = {
      plain_text_position: { start: 10, end: 11 },
      original_text_plain: "的"
    };

    // Then: Only 3rd "的" is highlighted
  });

  // === 特殊字符測試 ===

  test('TC-201: Issue contains HTML entities', async () => {
    // Given: Original content has &nbsp; &amp; etc.
    // Then: Displays correctly without entities showing
  });

  test('TC-202: Issue contains emoji', async () => {
    const article = "這個功能很棒 👍 大家都喜歡";
    const issue = {
      plain_text_position: { start: 7, end: 9 },
      original_text_plain: "👍"
    };
    // Then: Emoji is highlighted correctly
  });

  test('TC-203: Issue contains Chinese punctuation', async () => {
    // "，" "。" "！" "？" etc.
  });

  test('TC-204: Issue spans multiple Unicode characters', async () => {
    // Test with combined characters like é (e + combining accent)
  });

  // === 邊界條件測試 ===

  test('TC-301: Empty article content', async () => {
    // Given: Article content is empty
    // Then: No crash, shows appropriate message
  });

  test('TC-302: No issues in article', async () => {
    // Given: Article has content but no issues
    // Then: Article displays without highlights
  });

  test('TC-303: Issue position out of bounds', async () => {
    // Given: plain_text_position.end > article.length
    // Then: Graceful fallback, no crash
  });

  test('TC-304: Issue with zero length', async () => {
    // Given: start === end
    // Then: Handles gracefully
  });

  test('TC-305: Overlapping issues', async () => {
    // Given: Issue A (0-10), Issue B (5-15)
    // Then: Both display correctly (or defined merge behavior)
  });

  // === 向後兼容測試 ===

  test('TC-401: Legacy data without plain_text_position', async () => {
    // Given: Issue only has `position` (HTML-based), no `plain_text_position`
    // Then: Falls back to text search, still works
  });

  test('TC-402: Mismatch between position and text', async () => {
    // Given: plain_text_position points to wrong text
    // Then: Validation fails, falls back to search
  });

  // === 效能測試 ===

  test('TC-501: Article with 100+ issues', async () => {
    // Given: Large article with many issues
    // Then: All render within acceptable time (<500ms)
  });

  test('TC-502: Very long article (50,000+ characters)', async () => {
    // Given: Extremely long article
    // Then: Positioning still works correctly
  });

  // === 交互測試 ===

  test('TC-601: Click on issue scrolls to correct position', async () => {
    // Given: Issue in middle of long article
    // When: Click issue in left panel
    // Then: Article scrolls to show highlighted issue
  });

  test('TC-602: Selected issue has distinct visual style', async () => {
    // Given: One issue is selected
    // Then: Selected issue has ring/border style
  });
});
```

### 4.3 Integration Tests

```python
# backend/tests/integration/test_proofreading_api.py

class TestProofreadingAPIIntegration:
    def test_analyze_returns_plain_text_position(self):
        """API 必須返回 plain_text_position 欄位"""
        response = client.post("/api/worklist/{id}/analyze")
        issues = response.json()["proofreading_issues"]

        for issue in issues:
            assert "plain_text_position" in issue
            assert "original_text_plain" in issue
            assert issue["plain_text_position"]["start"] >= 0
            assert issue["plain_text_position"]["end"] > issue["plain_text_position"]["start"]

    def test_position_matches_text(self):
        """位置必須對應正確的文字"""
        response = client.post("/api/worklist/{id}/analyze")
        article_plain = strip_html_tags(article_html)

        for issue in response.json()["proofreading_issues"]:
            pos = issue["plain_text_position"]
            extracted = article_plain[pos["start"]:pos["end"]]
            assert extracted == issue["original_text_plain"]
```

### 4.4 Visual Regression Testing

```typescript
// frontend/tests/visual/regression.spec.ts

describe('Visual Regression', () => {
  test('Proofreading view matches snapshot', async () => {
    // Render with known test data
    await renderProofreadingView(testArticle, testIssues);

    // Compare with baseline screenshot
    await expect(page).toMatchSnapshot('proofreading-view.png');
  });

  test('Issue highlight styles match design', async () => {
    // Check each severity type
    await expectSnapshot('issue-critical.png');
    await expectSnapshot('issue-warning.png');
    await expectSnapshot('issue-info.png');
  });

  test('Decision states display correctly', async () => {
    await expectSnapshot('issue-accepted.png');
    await expectSnapshot('issue-rejected.png');
    await expectSnapshot('issue-modified.png');
  });
});
```

---

## 5. Files to Modify

### Backend

| 檔案 | 修改類型 | 說明 |
|------|:--------:|------|
| `backend/src/services/parser/html_utils.py` | 新增 | `strip_html_tags()` 函數 |
| `backend/src/services/worklist/position_calculator.py` | 新增 | `calculate_plain_text_position()` 函數 |
| `backend/src/services/worklist/proofreading_analyzer.py` | 修改 | 填充新欄位 |
| `backend/src/api/schemas/worklist.py` | 修改 | 新增欄位定義 |
| `backend/migrations/versions/YYYYMMDD_*.py` | 新增 | 資料庫 migration |
| `backend/tests/unit/test_html_utils.py` | 新增 | 單元測試 |
| `backend/tests/unit/test_position_calculator.py` | 新增 | 單元測試 |
| `backend/tests/integration/test_proofreading_api.py` | 修改 | 整合測試 |

### Frontend

| 檔案 | 修改類型 | 說明 |
|------|:--------:|------|
| `frontend/src/types/worklist.ts` | 修改 | 新增類型定義 |
| `frontend/src/lib/positionUtils.ts` | 新增 | `getIssuePosition()` 函數 |
| `frontend/src/components/ProofreadingReview/ProofreadingArticleContent.tsx` | 修改 | 使用新定位邏輯 |
| `frontend/src/components/ProofreadingReview/ProofreadingIssueList.tsx` | 修改 | 使用 plain text 欄位 |
| `frontend/tests/visual/proofreading-position.spec.ts` | 新增 | 基本定位測試 |
| `frontend/tests/visual/proofreading-edge-cases.spec.ts` | 新增 | 邊緣情況測試 |
| `frontend/tests/visual/regression.spec.ts` | 新增 | 視覺回歸測試 |

---

## 6. Success Criteria

| 類型 | 標準 | 驗證方式 |
|------|------|----------|
| **功能** | 所有問題在文章中準確高亮 | 視覺測試 TC-001 ~ TC-004 |
| **功能** | 重複文字正確處理 | 視覺測試 TC-101 ~ TC-103 |
| **向後兼容** | 現有資料仍可正常顯示 | 視覺測試 TC-401 ~ TC-402 |
| **效能** | 100+ issues 渲染 < 500ms | 效能測試 TC-501 |
| **測試覆蓋** | 單元測試覆蓋率 > 80% | Coverage report |
| **測試覆蓋** | 所有邊緣情況有測試案例 | Test suite |

---

## 7. Rollout Plan

| 階段 | 說明 | 回滾方案 |
|------|------|----------|
| **1. 後端部署** | 部署新欄位，同時填充舊格式 | 新欄位為 nullable，舊邏輯仍可用 |
| **2. 前端部署** | 優先使用新欄位，回退到舊邏輯 | Feature flag 控制 |
| **3. 驗證** | 監控錯誤率和使用者回饋 | - |
| **4. 清理** | 移除舊邏輯（可選） | - |

---

## 8. References

- **臨時修復 Commit**: `9b5274d` - fix(proofreading): Strip HTML tags from article content and issue list
- **相關 Spec**: `003-proofreading-review-ui`
- **相關文件**: `frontend/src/components/ProofreadingReview/`
