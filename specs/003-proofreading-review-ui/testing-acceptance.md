# 校对审核页面 - 测试规格 & 验收标准

**Feature:** Proofreading Review UI
**Created:** 2025-11-07
**Testing Framework:** Playwright E2E + Vitest Unit Tests

---

## 📋 Test Coverage Matrix

| Component | Unit Tests | Integration Tests | E2E Tests | Coverage Target |
|-----------|-----------|------------------|-----------|-----------------|
| IssueList | ✅ | ✅ | ✅ | 85% |
| ArticleContent | ✅ | ✅ | ✅ | 80% |
| IssueDetailPanel | ✅ | ✅ | ✅ | 90% |
| DecisionActions | ✅ | ✅ | ✅ | 95% |
| API Integration | - | ✅ | ✅ | 85% |
| State Management | ✅ | ✅ | ✅ | 90% |

---

## 🧪 E2E Test Scenarios (Playwright)

### Test Suite 1: Page Load & Navigation

**File:** `e2e/proofreading-review/page-load.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Proofreading Review Page - Load & Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to worklist
    await page.goto('/worklist');

    // Click on an item with "under_review" status
    await page.click('[data-testid="worklist-item-123"]');

    // Click "校对审核" button in detail drawer
    await page.click('[data-testid="start-proofreading-review"]');

    // Wait for page to load
    await page.waitForURL('**/worklist/123/review');
  });

  test('should display page header with correct title', async ({ page }) => {
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Check breadcrumb
    await expect(page.locator('nav')).toContainText('首页');
    await expect(page.locator('nav')).toContainText('Worklist');
    await expect(page.locator('nav')).toContainText('校对审核');

    // Check action buttons
    await expect(page.locator('button:has-text("保存草稿")')).toBeVisible();
    await expect(page.locator('button:has-text("完成审核")')).toBeVisible();
    await expect(page.locator('button:has-text("取消")')).toBeVisible();
  });

  test('should display three main sections', async ({ page }) => {
    // Issue list (left)
    await expect(page.locator('[data-testid="issue-list"]')).toBeVisible();

    // Article content (center)
    await expect(page.locator('[data-testid="article-content"]')).toBeVisible();

    // Issue detail panel (right)
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toBeVisible();
  });

  test('should display proofreading statistics in sub-header', async ({ page }) => {
    const stats = page.locator('[data-testid="proofreading-stats"]');
    await expect(stats).toContainText('Critical:');
    await expect(stats).toContainText('Warning:');
    await expect(stats).toContainText('Info:');
    await expect(stats).toContainText('已处理:');
  });

  test('should display footer progress bar', async ({ page }) => {
    const footer = page.locator('[data-testid="progress-footer"]');
    await expect(footer).toBeVisible();
    await expect(footer).toContainText('进度:');
    await expect(footer).toContainText('已处理');
  });

  test('should load article content correctly', async ({ page }) => {
    const article = page.locator('[data-testid="article-content"]');
    await expect(article.locator('h1')).toBeVisible(); // Article title
    await expect(article.locator('.article-content')).toBeVisible();
  });

  test('should load issue list with correct count', async ({ page }) => {
    const issueList = page.locator('[data-testid="issue-list"]');
    const issueItems = issueList.locator('[data-testid^="issue-item-"]');

    const count = await issueItems.count();
    expect(count).toBeGreaterThan(0);

    // Verify first issue has required elements
    const firstIssue = issueItems.first();
    await expect(firstIssue.locator('[data-testid="severity-icon"]')).toBeVisible();
    await expect(firstIssue.locator('[data-testid="original-text"]')).toBeVisible();
    await expect(firstIssue.locator('[data-testid="suggested-text"]')).toBeVisible();
  });
});
```

---

### Test Suite 2: Issue Selection & Navigation

**File:** `e2e/proofreading-review/issue-navigation.spec.ts`

```typescript
test.describe('Issue Selection & Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist/123/review');
    await page.waitForLoadState('networkidle');
  });

  test('should select issue on click', async ({ page }) => {
    const firstIssue = page.locator('[data-testid="issue-item-1"]');
    await firstIssue.click();

    // Issue should be highlighted
    await expect(firstIssue).toHaveClass(/selected|bg-blue-50/);

    // Detail panel should show issue details
    const detailPanel = page.locator('[data-testid="issue-detail-panel"]');
    await expect(detailPanel).toContainText('问题 #1');
  });

  test('should navigate to next/previous issue', async ({ page }) => {
    // Select first issue
    await page.click('[data-testid="issue-item-1"]');

    // Click "Next" button
    await page.click('[data-testid="next-issue"]');

    // Should select issue #2
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #2');
    await expect(page.locator('[data-testid="issue-item-2"]')).toHaveClass(/selected/);

    // Click "Previous" button
    await page.click('[data-testid="prev-issue"]');

    // Should go back to issue #1
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #1');
  });

  test('should disable navigation buttons at boundaries', async ({ page }) => {
    // Select first issue
    await page.click('[data-testid="issue-item-1"]');

    // "Previous" button should be disabled
    await expect(page.locator('[data-testid="prev-issue"]')).toBeDisabled();

    // Navigate to last issue
    const lastIssueNumber = await page.locator('[data-testid^="issue-item-"]').count();
    await page.click(`[data-testid="issue-item-${lastIssueNumber}"]`);

    // "Next" button should be disabled
    await expect(page.locator('[data-testid="next-issue"]')).toBeDisabled();
  });

  test('should navigate using keyboard shortcuts', async ({ page }) => {
    await page.click('[data-testid="issue-item-1"]');

    // Press ArrowDown to go to next issue
    await page.keyboard.press('ArrowDown');
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #2');

    // Press ArrowUp to go to previous issue
    await page.keyboard.press('ArrowUp');
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #1');

    // Press 'j' (Vim-style navigation)
    await page.keyboard.press('j');
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #2');

    // Press 'k' (Vim-style navigation)
    await page.keyboard.press('k');
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #1');
  });

  test('should scroll article content to issue position', async ({ page }) => {
    // Select issue #10 (somewhere in the middle)
    await page.click('[data-testid="issue-item-10"]');

    // Wait for scroll animation
    await page.waitForTimeout(500);

    // The highlighted issue should be visible in viewport
    const highlightedIssue = page.locator('[data-issue-id="issue-010"]');
    await expect(highlightedIssue).toBeInViewport();
  });

  test('should select issue by clicking highlighted text in article', async ({ page }) => {
    // Click on highlighted text in article content
    await page.click('[data-issue-id="issue-001"]');

    // Issue #1 should be selected in the list
    await expect(page.locator('[data-testid="issue-item-1"]')).toHaveClass(/selected/);

    // Detail panel should show issue #1
    await expect(page.locator('[data-testid="issue-detail-panel"]')).toContainText('问题 #1');
  });
});
```

---

### Test Suite 3: Decision Making

**File:** `e2e/proofreading-review/decision-making.spec.ts`

```typescript
test.describe('Decision Making', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist/123/review');
    await page.click('[data-testid="issue-item-1"]');
  });

  test('should accept issue suggestion', async ({ page }) => {
    // Click "Accept" button
    await page.click('[data-testid="accept-button"]');

    // Wait for UI update
    await page.waitForTimeout(300);

    // Issue should show "accepted" status
    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已接受');

    // Badge should show accepted status
    await expect(page.locator('[data-testid="issue-item-1"] [data-testid="status-badge"]')).toContainText('✓ 已接受');

    // Highlighted text in article should show accepted style
    await expect(page.locator('[data-issue-id="issue-001"]')).toHaveClass(/issue-highlight--accepted/);

    // Progress should update
    const footer = page.locator('[data-testid="progress-footer"]');
    await expect(footer).toContainText('1/24 已处理');
  });

  test('should reject issue suggestion', async ({ page }) => {
    // Click "Reject" button
    await page.click('[data-testid="reject-button"]');

    // Issue should show "rejected" status
    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已拒绝');

    // Highlighted text should show rejected style (strikethrough)
    await expect(page.locator('[data-issue-id="issue-001"]')).toHaveClass(/issue-highlight--rejected/);
  });

  test('should apply custom modification', async ({ page }) => {
    // Type custom modification
    const customInput = page.locator('[data-testid="custom-modification-input"]');
    await customInput.fill('他们决定去公园散步');

    // Click "Apply Custom" button
    await page.click('[data-testid="apply-custom-button"]');

    // Issue should show "modified" status
    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已修改');

    // Highlighted text should show modified style
    await expect(page.locator('[data-issue-id="issue-001"]')).toHaveClass(/issue-highlight--modified/);
  });

  test('should use keyboard shortcuts for decisions', async ({ page }) => {
    // Press 'a' to accept
    await page.keyboard.press('a');
    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已接受');

    // Navigate to next issue
    await page.keyboard.press('j');

    // Press 'r' to reject
    await page.keyboard.press('r');
    await expect(page.locator('[data-testid="issue-item-2"]')).toContainText('已拒绝');

    // Navigate to next issue
    await page.keyboard.press('j');

    // Press 'e' to focus custom edit
    await page.keyboard.press('e');
    await expect(page.locator('[data-testid="custom-modification-input"]')).toBeFocused();
  });

  test('should add decision rationale', async ({ page }) => {
    // Fill rationale textarea
    const rationale = page.locator('[data-testid="decision-rationale"]');
    await rationale.fill('这个建议很合理，提升了文章可读性');

    // Accept issue
    await page.click('[data-testid="accept-button"]');

    // Decision should be saved with rationale
    // (verify via API call or backend state)
  });

  test('should provide feedback', async ({ page }) => {
    // Expand feedback accordion
    await page.click('[data-testid="feedback-accordion"]');

    // Select feedback category
    await page.check('[data-testid="feedback-category-correct"]');

    // Fill feedback notes
    await page.fill('[data-testid="feedback-notes"]', 'AI建议非常准确');

    // Accept issue
    await page.click('[data-testid="accept-button"]');

    // Feedback should be saved
    // (verify via API call)
  });
});
```

---

### Test Suite 4: Filtering & Sorting

**File:** `e2e/proofreading-review/filtering.spec.ts`

```typescript
test.describe('Filtering & Sorting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist/123/review');
  });

  test('should filter by severity', async ({ page }) => {
    // Filter by Critical
    await page.selectOption('[data-testid="severity-filter"]', 'critical');

    // Wait for filter to apply
    await page.waitForTimeout(300);

    // Only critical issues should be visible
    const visibleIssues = page.locator('[data-testid^="issue-item-"]');
    const count = await visibleIssues.count();

    for (let i = 0; i < count; i++) {
      const issue = visibleIssues.nth(i);
      await expect(issue.locator('[data-testid="severity-icon"]')).toHaveClass(/text-red-500/);
    }
  });

  test('should filter by rule category', async ({ page }) => {
    await page.selectOption('[data-testid="category-filter"]', 'grammar');

    const visibleIssues = page.locator('[data-testid^="issue-item-"]');
    const count = await visibleIssues.count();

    for (let i = 0; i < count; i++) {
      const issue = visibleIssues.nth(i);
      await expect(issue).toContainText('语法');
    }
  });

  test('should filter by decision status', async ({ page }) => {
    // Accept first issue
    await page.click('[data-testid="issue-item-1"]');
    await page.click('[data-testid="accept-button"]');

    // Filter by "accepted"
    await page.selectOption('[data-testid="status-filter"]', 'accepted');

    // Only accepted issues should be visible
    const visibleIssues = page.locator('[data-testid^="issue-item-"]');
    expect(await visibleIssues.count()).toBeGreaterThanOrEqual(1);

    const firstIssue = visibleIssues.first();
    await expect(firstIssue).toContainText('已接受');
  });

  test('should search issues', async ({ page }) => {
    await page.fill('[data-testid="issue-search"]', '公园');

    await page.waitForTimeout(500);

    const visibleIssues = page.locator('[data-testid^="issue-item-"]');
    const count = await visibleIssues.count();

    // All visible issues should contain "公园" in original or suggested text
    for (let i = 0; i < count; i++) {
      const issue = visibleIssues.nth(i);
      const text = await issue.textContent();
      expect(text).toContain('公园');
    }
  });

  test('should reset filters', async ({ page }) => {
    // Apply multiple filters
    await page.selectOption('[data-testid="severity-filter"]', 'critical');
    await page.selectOption('[data-testid="category-filter"]', 'grammar');

    const filteredCount = await page.locator('[data-testid^="issue-item-"]').count();

    // Reset filters
    await page.click('[data-testid="reset-filters"]');

    // All issues should be visible again
    const totalCount = await page.locator('[data-testid^="issue-item-"]').count();
    expect(totalCount).toBeGreaterThan(filteredCount);
  });
});
```

---

### Test Suite 5: Batch Operations

**File:** `e2e/proofreading-review/batch-operations.spec.ts`

```typescript
test.describe('Batch Operations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist/123/review');
  });

  test('should select multiple issues', async ({ page }) => {
    // Check checkboxes for issues #1, #2, #3
    await page.check('[data-testid="issue-checkbox-1"]');
    await page.check('[data-testid="issue-checkbox-2"]');
    await page.check('[data-testid="issue-checkbox-3"]');

    // Batch action bar should be visible
    const batchBar = page.locator('[data-testid="batch-action-bar"]');
    await expect(batchBar).toBeVisible();
    await expect(batchBar).toContainText('已选中 3 个问题');
  });

  test('should select all issues', async ({ page }) => {
    // Click "Select All" checkbox
    await page.check('[data-testid="select-all-checkbox"]');

    // All issues should be checked
    const allCheckboxes = page.locator('[data-testid^="issue-checkbox-"]');
    const count = await allCheckboxes.count();

    for (let i = 0; i < count; i++) {
      await expect(allCheckboxes.nth(i)).toBeChecked();
    }

    // Batch action bar should show total count
    await expect(page.locator('[data-testid="batch-action-bar"]')).toContainText(`已选中 ${count} 个问题`);
  });

  test('should batch accept issues', async ({ page }) => {
    // Select 3 issues
    await page.check('[data-testid="issue-checkbox-1"]');
    await page.check('[data-testid="issue-checkbox-2"]');
    await page.check('[data-testid="issue-checkbox-3"]');

    // Click "Batch Accept"
    await page.click('[data-testid="batch-accept"]');

    // Confirmation dialog should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('[role="dialog"]')).toContainText('确认批量接受 3 个建议');

    // Confirm
    await page.click('[data-testid="confirm-batch-action"]');

    // Wait for processing
    await page.waitForTimeout(1000);

    // All 3 issues should show "accepted" status
    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已接受');
    await expect(page.locator('[data-testid="issue-item-2"]')).toContainText('已接受');
    await expect(page.locator('[data-testid="issue-item-3"]')).toContainText('已接受');
  });

  test('should batch reject issues', async ({ page }) => {
    await page.check('[data-testid="issue-checkbox-1"]');
    await page.check('[data-testid="issue-checkbox-2"]');

    await page.click('[data-testid="batch-reject"]');

    await page.click('[data-testid="confirm-batch-action"]');

    await page.waitForTimeout(1000);

    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已拒绝');
    await expect(page.locator('[data-testid="issue-item-2"]')).toContainText('已拒绝');
  });

  test('should clear selection', async ({ page }) => {
    await page.check('[data-testid="issue-checkbox-1"]');
    await page.check('[data-testid="issue-checkbox-2"]');

    // Click "Clear Selection"
    await page.click('[data-testid="clear-selection"]');

    // Batch action bar should disappear
    await expect(page.locator('[data-testid="batch-action-bar"]')).not.toBeVisible();

    // Checkboxes should be unchecked
    await expect(page.locator('[data-testid="issue-checkbox-1"]')).not.toBeChecked();
    await expect(page.locator('[data-testid="issue-checkbox-2"]')).not.toBeChecked();
  });
});
```

---

### Test Suite 6: Preview Mode

**File:** `e2e/proofreading-review/preview-mode.spec.ts`

```typescript
test.describe('Preview Mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist/123/review');

    // Accept some issues to create modifications
    await page.click('[data-testid="issue-item-1"]');
    await page.click('[data-testid="accept-button"]');
    await page.keyboard.press('j');
    await page.click('[data-testid="accept-button"]');
  });

  test('should switch to preview mode', async ({ page }) => {
    // Click "Preview" toggle
    await page.click('[data-testid="view-mode-preview"]');

    // Article content should show modified version
    const articleContent = page.locator('[data-testid="article-content"]');

    // Issue highlights should show accepted changes applied
    await expect(articleContent.locator('[data-issue-id="issue-001"]')).toHaveClass(/issue-highlight--accepted/);

    // Preview badge should be visible
    await expect(page.locator('[data-testid="preview-mode-indicator"]')).toBeVisible();
  });

  test('should switch to diff mode', async ({ page }) => {
    await page.click('[data-testid="view-mode-diff"]');

    // Should show side-by-side comparison
    await expect(page.locator('[data-testid="diff-view-original"]')).toBeVisible();
    await expect(page.locator('[data-testid="diff-view-modified"]')).toBeVisible();

    // Original side should show original text
    // Modified side should show accepted changes
  });

  test('should switch back to original mode', async ({ page }) => {
    await page.click('[data-testid="view-mode-preview"]');
    await page.click('[data-testid="view-mode-original"]');

    // Should show original content with highlights
    const articleContent = page.locator('[data-testid="article-content"]');
    await expect(articleContent.locator('[data-issue-id="issue-001"]')).toHaveClass(/issue-highlight/);
  });
});
```

---

### Test Suite 7: Save & Submit

**File:** `e2e/proofreading-review/save-submit.spec.ts`

```typescript
test.describe('Save & Submit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/worklist/123/review');
  });

  test('should save draft decisions', async ({ page }) => {
    // Make some decisions
    await page.click('[data-testid="issue-item-1"]');
    await page.click('[data-testid="accept-button"]');
    await page.keyboard.press('j');
    await page.click('[data-testid="reject-button"]');

    // Click "Save Draft"
    await page.click('[data-testid="save-draft"]');

    // Wait for save confirmation
    await expect(page.locator('[data-testid="toast"]')).toContainText('草稿已保存');

    // Decisions should be persisted
    // Reload page
    await page.reload();

    // Decisions should still be there
    await expect(page.locator('[data-testid="issue-item-1"]')).toContainText('已接受');
    await expect(page.locator('[data-testid="issue-item-2"]')).toContainText('已拒绝');
  });

  test('should complete review with all issues resolved', async ({ page }) => {
    // Mock: accept all issues
    const issueCount = await page.locator('[data-testid^="issue-item-"]').count();

    for (let i = 1; i <= issueCount; i++) {
      await page.click(`[data-testid="issue-item-${i}"]`);
      await page.click('[data-testid="accept-button"]');
    }

    // Click "Complete Review"
    await page.click('[data-testid="complete-review"]');

    // Confirmation dialog should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('[role="dialog"]')).toContainText('完成审核');
    await expect(page.locator('[role="dialog"]')).toContainText('所有问题已处理');

    // Add review notes
    await page.fill('[data-testid="review-notes"]', '校对完成，质量良好');

    // Confirm submission
    await page.click('[data-testid="confirm-complete-review"]');

    // Should navigate back to worklist
    await page.waitForURL('**/worklist');

    // Success toast should appear
    await expect(page.locator('[data-testid="toast"]')).toContainText('审核完成');

    // Item status should be updated
    const worklistItem = page.locator('[data-testid="worklist-item-123"]');
    await expect(worklistItem).toContainText('待发布');
  });

  test('should warn about unresolved critical issues', async ({ page }) => {
    // Leave some critical issues unresolved
    await page.click('[data-testid="issue-item-1"]');
    await page.click('[data-testid="accept-button"]');

    // Try to complete review
    await page.click('[data-testid="complete-review"]');

    // Warning dialog should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('[role="dialog"]')).toContainText('还有 2 个 Critical 问题未处理');
    await expect(page.locator('[role="dialog"]')).toContainText('建议解决所有 Critical 问题');

    // Should have options: "继续提交" or "返回修改"
    await expect(page.locator('[data-testid="continue-anyway"]')).toBeVisible();
    await expect(page.locator('[data-testid="go-back"]')).toBeVisible();
  });

  test('should handle save errors gracefully', async ({ page }) => {
    // Mock network error
    await page.route('**/v1/worklist/123/review-decisions', (route) => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });

    await page.click('[data-testid="issue-item-1"]');
    await page.click('[data-testid="accept-button"]');
    await page.click('[data-testid="complete-review"]');
    await page.click('[data-testid="confirm-complete-review"]');

    // Error toast should appear
    await expect(page.locator('[data-testid="toast"]')).toContainText('保存失败');
    await expect(page.locator('[data-testid="toast"]')).toContainText('请重试');

    // Should stay on review page
    await expect(page).toHaveURL(/\/worklist\/123\/review/);
  });

  test('should confirm before canceling with unsaved changes', async ({ page }) => {
    // Make a decision
    await page.click('[data-testid="issue-item-1"]');
    await page.click('[data-testid="accept-button"]');

    // Click "Cancel"
    await page.click('[data-testid="cancel-review"]');

    // Confirmation dialog should appear
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('[role="dialog"]')).toContainText('有未保存的更改');
    await expect(page.locator('[role="dialog"]')).toContainText('确定要离开');

    // Confirm cancellation
    await page.click('[data-testid="confirm-cancel"]');

    // Should navigate back to worklist
    await page.waitForURL('**/worklist');
  });
});
```

---

## 🔬 Unit Tests (Vitest)

### Test Suite: Decision State Management

**File:** `src/stores/__tests__/decision-store.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useDecisionStore } from '../decision-store';

describe('DecisionStore', () => {
  beforeEach(() => {
    const store = useDecisionStore.getState();
    store.reset();
  });

  it('should initialize with empty state', () => {
    const store = useDecisionStore.getState();
    expect(store.decisions).toEqual({});
    expect(store.getDirtyCount()).toBe(0);
  });

  it('should add decision', () => {
    const store = useDecisionStore.getState();
    store.addDecision('issue-001', {
      decision_type: 'accepted',
      decision_rationale: 'Good suggestion',
    });

    expect(store.decisions['issue-001']).toEqual({
      issue_id: 'issue-001',
      decision_type: 'accepted',
      decision_rationale: 'Good suggestion',
      modified_content: null,
      feedback_provided: false,
      feedback_category: null,
      feedback_notes: null,
    });

    expect(store.getDirtyCount()).toBe(1);
  });

  it('should update existing decision', () => {
    const store = useDecisionStore.getState();
    store.addDecision('issue-001', { decision_type: 'accepted' });
    store.addDecision('issue-001', { decision_type: 'rejected' });

    expect(store.decisions['issue-001'].decision_type).toBe('rejected');
    expect(store.getDirtyCount()).toBe(1);
  });

  it('should batch add decisions', () => {
    const store = useDecisionStore.getState();
    store.batchAddDecisions(['issue-001', 'issue-002', 'issue-003'], {
      decision_type: 'accepted',
      decision_rationale: 'Batch accept',
    });

    expect(Object.keys(store.decisions).length).toBe(3);
    expect(store.getDirtyCount()).toBe(3);
  });

  it('should clear decision', () => {
    const store = useDecisionStore.getState();
    store.addDecision('issue-001', { decision_type: 'accepted' });
    store.clearDecision('issue-001');

    expect(store.decisions['issue-001']).toBeUndefined();
    expect(store.getDirtyCount()).toBe(0);
  });

  it('should check if issue is decided', () => {
    const store = useDecisionStore.getState();
    expect(store.isDecided('issue-001')).toBe(false);

    store.addDecision('issue-001', { decision_type: 'accepted' });
    expect(store.isDecided('issue-001')).toBe(true);
  });

  it('should get decision statistics', () => {
    const store = useDecisionStore.getState();
    store.addDecision('issue-001', { decision_type: 'accepted' });
    store.addDecision('issue-002', { decision_type: 'rejected' });
    store.addDecision('issue-003', { decision_type: 'modified', modified_content: 'new text' });

    const stats = store.getStats();
    expect(stats.total).toBe(3);
    expect(stats.accepted).toBe(1);
    expect(stats.rejected).toBe(1);
    expect(stats.modified).toBe(1);
  });
});
```

---

## ✅ Acceptance Criteria Checklist

### Functionality (Must-Have)

- [ ] **AC-F-001**: User can load proofreading review page for worklist item
- [ ] **AC-F-002**: User can view all proofreading issues in left panel
- [ ] **AC-F-003**: User can view article content with highlighted issues
- [ ] **AC-F-004**: User can select issue from list or by clicking highlight
- [ ] **AC-F-005**: User can accept issue suggestion
- [ ] **AC-F-006**: User can reject issue suggestion
- [ ] **AC-F-007**: User can provide custom modification
- [ ] **AC-F-008**: User can add decision rationale
- [ ] **AC-F-009**: User can provide feedback on AI suggestions
- [ ] **AC-F-010**: User can navigate between issues using buttons
- [ ] **AC-F-011**: User can navigate between issues using keyboard
- [ ] **AC-F-012**: User can filter issues by severity
- [ ] **AC-F-013**: User can filter issues by category
- [ ] **AC-F-014**: User can filter issues by decision status
- [ ] **AC-F-015**: User can search issues
- [ ] **AC-F-016**: User can select multiple issues
- [ ] **AC-F-017**: User can batch accept issues
- [ ] **AC-F-018**: User can batch reject issues
- [ ] **AC-F-019**: User can preview modified content
- [ ] **AC-F-020**: User can save draft decisions
- [ ] **AC-F-021**: User can complete review and transition status
- [ ] **AC-F-022**: System warns about unresolved critical issues
- [ ] **AC-F-023**: System confirms before discarding unsaved changes

### Performance (Must-Have)

- [ ] **AC-P-001**: Page loads in < 2s (p95)
- [ ] **AC-P-002**: Issue list renders 100 issues in < 500ms
- [ ] **AC-P-003**: Issue selection responds in < 100ms
- [ ] **AC-P-004**: Scroll to issue animates at 60fps
- [ ] **AC-P-005**: Decision save API responds in < 1s

### Usability (Should-Have)

- [ ] **AC-U-001**: Keyboard shortcuts work as documented
- [ ] **AC-U-002**: Loading states display during async operations
- [ ] **AC-U-003**: Error messages are clear and actionable
- [ ] **AC-U-004**: Progress indicator updates in real-time
- [ ] **AC-U-005**: Tooltips provide helpful context
- [ ] **AC-U-006**: Empty states guide user actions

### Accessibility (Should-Have)

- [ ] **AC-A-001**: All interactive elements are keyboard accessible
- [ ] **AC-A-002**: Focus indicators are visible
- [ ] **AC-A-003**: ARIA labels are present
- [ ] **AC-A-004**: Color contrast meets WCAG AA
- [ ] **AC-A-005**: Screen reader can navigate issues

### Responsive Design (Should-Have)

- [ ] **AC-R-001**: Layout adapts correctly at mobile breakpoint
- [ ] **AC-R-002**: Layout adapts correctly at tablet breakpoint
- [ ] **AC-R-003**: Touch targets meet 44x44px minimum
- [ ] **AC-R-004**: No horizontal scrolling at any breakpoint

---

## 📊 Test Metrics

### Coverage Targets
- **Overall Code Coverage**: ≥ 85%
- **Critical Path Coverage**: ≥ 95%
- **E2E Test Pass Rate**: 100%
- **Unit Test Pass Rate**: 100%

### Performance Benchmarks
- **Page Load Time (p50)**: < 1s
- **Page Load Time (p95)**: < 2s
- **Issue List Render (100 items)**: < 500ms
- **Decision Save API (p95)**: < 1s
- **Scroll Animation FPS**: ≥ 60fps

---

## 🔄 CI/CD Integration

### Pre-commit Hooks
```bash
# Run linting
npm run lint

# Run type checking
npm run type-check

# Run unit tests
npm run test:unit
```

### PR Checks
```yaml
# .github/workflows/pr-checks.yml
- name: Run E2E Tests
  run: npx playwright test e2e/proofreading-review/

- name: Check Coverage
  run: npm run test:coverage
  # Fail if coverage < 85%

- name: Lighthouse CI
  run: npm run lighthouse
  # Fail if performance score < 90
```

---

**Document Version:** 1.0
**Created:** 2025-11-07
**Status:** Ready for Implementation
