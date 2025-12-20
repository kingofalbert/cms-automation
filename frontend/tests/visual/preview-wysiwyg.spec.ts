/**
 * WYSIWYG Preview Visual Regression Tests
 *
 * 測試預覽組件的視覺渲染效果，包括：
 * - 正常 HTML 渲染
 * - 字體異常檢測與標註
 * - 格式錯誤高亮
 * - 模式切換功能
 * - Google Docs 污染檢測
 *
 * @version 1.0
 * @date 2025-12-19
 */

import { test, expect, Page } from '@playwright/test';

// ============================================================
// Test Configuration
// ============================================================

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

// 測試用 HTML 樣本
const TEST_SAMPLES = {
  cleanHtml: '<p>這是一段正常的文章內容，使用系統默認字體顯示。</p>',

  timesNewRoman: `
    <p style="font-family: 'Times New Roman', serif;">
      這段文字使用了 Times New Roman 字體，應該被標記為異常。
    </p>
  `,

  multipleIssues: `
    <p style="font-family: Calibri;">Calibri 字體段落</p>
    <p><p>嵌套段落錯誤</p></p>
    <span style="color: red;"></span>
    <p style="font-family: 'Comic Sans MS';">Comic Sans 字體</p>
  `,

  googleDocs: `
    <p class="c1" style="margin: 0; padding: 0; orphans: 2; widows: 2; font-family: 'Times New Roman';">
      <span class="c0" style="font-weight: 400; font-style: normal;">
        這是從 Google Docs 複製的內容，包含大量內聯樣式污染。
      </span>
    </p>
    <p class="c1"><span class="c0"></span></p>
    <p class="c2" style="text-indent: 2em; line-height: 1.5;">
      第二段內容，同樣帶有 Google Docs 特有的樣式。
    </p>
  `,

  chineseFonts: `
    <p style="font-family: 'Microsoft YaHei';">微軟雅黑字體 - 應該被接受</p>
    <p style="font-family: 'SimSun';">宋體 - 應該被警告（印刷字體）</p>
    <p style="font-family: 'Noto Sans SC';">Noto Sans SC - 應該被接受</p>
  `,

  nestedTags: `
    <div>
      <p>正常段落</p>
      <p><p>嵌套段落 - 錯誤</p></p>
      <div><div><div>過度嵌套的 div</div></div></div>
    </div>
  `,

  emptyTags: `
    <p>正常內容</p>
    <span></span>
    <div style="margin: 10px;"></div>
    <p>   </p>
    <span style="font-weight: bold;"></span>
  `,
};

// ============================================================
// Helper Functions
// ============================================================

/**
 * 導航到預覽測試頁面
 */
async function navigateToPreview(page: Page, html: string): Promise<void> {
  const encodedHtml = encodeURIComponent(html);
  await page.goto(`${BASE_URL}/test/preview?html=${encodedHtml}`);
  await page.waitForSelector('.preview-container', { timeout: 10000 });
}

/**
 * 等待問題檢測完成
 */
async function waitForAnalysis(page: Page): Promise<void> {
  await page.waitForSelector('[data-testid="analysis-complete"]', { timeout: 5000 });
}

/**
 * 獲取問題計數
 */
async function getIssueCount(page: Page): Promise<number> {
  const countText = await page.locator('.issue-count').textContent();
  const match = countText?.match(/(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

// ============================================================
// Test Suites
// ============================================================

test.describe('WYSIWYG Preview - Basic Rendering', () => {
  test.beforeEach(async ({ page }) => {
    // 設置視口大小以確保一致的截圖
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('renders clean HTML without issues', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.cleanHtml);
    await waitForAnalysis(page);

    // 驗證無問題
    const issueCount = await getIssueCount(page);
    expect(issueCount).toBe(0);

    // 驗證內容正確渲染
    const content = await page.locator('.preview-content').textContent();
    expect(content).toContain('正常的文章內容');

    // 視覺回歸測試
    await expect(page.locator('.preview-container')).toHaveScreenshot('clean-html.png');
  });

  test('renders Chinese content correctly', async ({ page }) => {
    const chineseContent = `
      <h1>健康養生文章標題</h1>
      <p>這是一篇關於健康養生的文章，包含繁體中文內容。</p>
      <ul>
        <li>第一點：均衡飲食</li>
        <li>第二點：適量運動</li>
        <li>第三點：充足睡眠</li>
      </ul>
    `;
    await navigateToPreview(page, chineseContent);

    // 驗證中文正確顯示
    const content = await page.locator('.preview-content').textContent();
    expect(content).toContain('健康養生');
    expect(content).toContain('均衡飲食');

    await expect(page.locator('.preview-container')).toHaveScreenshot('chinese-content.png');
  });
});

test.describe('WYSIWYG Preview - Font Detection', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('highlights Times New Roman as problematic', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.timesNewRoman);
    await waitForAnalysis(page);

    // 驗證字體問題被檢測
    const issueCount = await getIssueCount(page);
    expect(issueCount).toBeGreaterThan(0);

    // 驗證高亮顯示
    const highlight = page.locator('.font-issue-highlight');
    await expect(highlight).toBeVisible();

    // 驗證背景色（淺黃色警告）
    await expect(highlight).toHaveCSS('background-color', /rgb\(254, 243, 199\)|#fef3c7/i);

    // Hover 顯示 Tooltip
    await highlight.hover();
    const tooltip = page.locator('.font-tooltip');
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText('Times New Roman');

    await expect(page.locator('.preview-container')).toHaveScreenshot('times-new-roman.png');
  });

  test('accepts standard Chinese fonts', async ({ page }) => {
    const validChineseFonts = `
      <p style="font-family: 'Noto Sans SC';">Noto Sans SC 字體</p>
      <p style="font-family: 'Microsoft YaHei';">微軟雅黑字體</p>
    `;
    await navigateToPreview(page, validChineseFonts);
    await waitForAnalysis(page);

    // 這些字體應該被接受，不產生警告
    const warnings = page.locator('.font-issue-highlight');
    await expect(warnings).toHaveCount(0);
  });

  test('warns about print fonts like SimSun', async ({ page }) => {
    const printFont = `<p style="font-family: SimSun, 宋体;">宋體印刷字體</p>`;
    await navigateToPreview(page, printFont);
    await waitForAnalysis(page);

    // 應該產生警告
    const warning = page.locator('.font-issue-highlight');
    await expect(warning).toBeVisible();

    // 驗證警告信息
    await warning.hover();
    const tooltip = page.locator('.font-tooltip');
    await expect(tooltip).toContainText(/印刷|屏幕/);
  });

  test('detects multiple font issues', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.multipleIssues);
    await waitForAnalysis(page);

    // 應該檢測到多個問題
    const issueCount = await getIssueCount(page);
    expect(issueCount).toBeGreaterThan(1);

    // 驗證問題列表
    const issueList = page.locator('.issue-list-item');
    const count = await issueList.count();
    expect(count).toBeGreaterThan(1);

    await expect(page.locator('.preview-container')).toHaveScreenshot('multiple-issues.png');
  });
});

test.describe('WYSIWYG Preview - Format Error Detection', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('detects nested paragraph tags', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.nestedTags);
    await waitForAnalysis(page);

    // 檢測嵌套錯誤
    const nestingIssue = page.locator('.nesting-issue');
    await expect(nestingIssue).toBeVisible();

    // 驗證錯誤樣式（紅色邊框）
    await expect(nestingIssue).toHaveCSS('border-color', /rgb\(239, 68, 68\)|#ef4444/i);

    await expect(page.locator('.preview-container')).toHaveScreenshot('nested-tags.png');
  });

  test('identifies empty tags', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.emptyTags);
    await waitForAnalysis(page);

    // 檢測空標籤
    const emptyTagIndicators = page.locator('.empty-tag-indicator');
    const count = await emptyTagIndicators.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('WYSIWYG Preview - Google Docs Contamination', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('detects Google Docs imported content', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.googleDocs);
    await waitForAnalysis(page);

    // 應該顯示 Google Docs 污染警告
    const gdocsWarning = page.locator('.gdocs-warning');
    await expect(gdocsWarning).toBeVisible();

    // 驗證警告內容
    await expect(gdocsWarning).toContainText(/Google Docs|污染|清理/);

    await expect(page.locator('.preview-container')).toHaveScreenshot('gdocs-contamination.png');
  });

  test('offers cleanup suggestion for Google Docs content', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.googleDocs);
    await waitForAnalysis(page);

    // 應該有清理建議按鈕
    const cleanupBtn = page.locator('[data-testid="cleanup-gdocs-btn"]');
    await expect(cleanupBtn).toBeVisible();

    // 點擊清理
    await cleanupBtn.click();

    // 驗證清理後問題減少
    await page.waitForTimeout(500);
    const issueCount = await getIssueCount(page);
    expect(issueCount).toBeLessThan(5); // 清理後問題應該減少

    await expect(page.locator('.preview-container')).toHaveScreenshot('gdocs-cleaned.png');
  });
});

test.describe('WYSIWYG Preview - Mode Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('toggles between preview and source mode', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.timesNewRoman);
    await waitForAnalysis(page);

    // 默認是預覽模式
    await expect(page.locator('.preview-mode')).toBeVisible();
    await expect(page.locator('.source-mode')).not.toBeVisible();

    // 截圖預覽模式
    await expect(page.locator('.preview-container')).toHaveScreenshot('mode-preview.png');

    // 切換到源碼模式
    const sourceBtn = page.locator('[data-testid="source-mode-btn"]');
    await sourceBtn.click();

    // 驗證源碼模式
    await expect(page.locator('.source-mode')).toBeVisible();
    await expect(page.locator('.source-mode')).toContainText('font-family');
    await expect(page.locator('.source-mode')).toContainText('Times New Roman');

    // 截圖源碼模式
    await expect(page.locator('.preview-container')).toHaveScreenshot('mode-source.png');

    // 切換回預覽模式
    const previewBtn = page.locator('[data-testid="preview-mode-btn"]');
    await previewBtn.click();
    await expect(page.locator('.preview-mode')).toBeVisible();
  });

  test('hybrid mode shows both preview and issues inline', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.multipleIssues);
    await waitForAnalysis(page);

    // 切換到混合模式
    const hybridBtn = page.locator('[data-testid="hybrid-mode-btn"]');
    await hybridBtn.click();

    // 驗證混合模式
    await expect(page.locator('.hybrid-mode')).toBeVisible();

    // 應該同時顯示渲染內容和問題標記
    await expect(page.locator('.preview-content')).toBeVisible();
    await expect(page.locator('.inline-issue-marker')).toBeVisible();

    await expect(page.locator('.preview-container')).toHaveScreenshot('mode-hybrid.png');
  });
});

test.describe('WYSIWYG Preview - Issue Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('clicking issue scrolls to location', async ({ page }) => {
    const longContent = `
      <p>第一段正常內容</p>
      ${Array(20).fill('<p>填充段落</p>').join('')}
      <p style="font-family: 'Times New Roman';">問題段落在底部</p>
    `;
    await navigateToPreview(page, longContent);
    await waitForAnalysis(page);

    // 點擊問題列表中的項目
    const issueItem = page.locator('.issue-list-item').first();
    await issueItem.click();

    // 驗證滾動到問題位置
    const highlight = page.locator('.font-issue-highlight');
    await expect(highlight).toBeInViewport();
  });

  test('issue tooltip shows fix suggestion', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.timesNewRoman);
    await waitForAnalysis(page);

    // Hover 問題區域
    const highlight = page.locator('.font-issue-highlight');
    await highlight.hover();

    // 驗證 Tooltip 內容
    const tooltip = page.locator('.font-tooltip');
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText(/建議|修復|移除/);

    // 應該有快速修復按鈕
    const fixBtn = tooltip.locator('[data-testid="quick-fix-btn"]');
    await expect(fixBtn).toBeVisible();
  });

  test('quick fix removes problematic font', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.timesNewRoman);
    await waitForAnalysis(page);

    // 獲取初始問題數
    const initialCount = await getIssueCount(page);

    // 執行快速修復
    const highlight = page.locator('.font-issue-highlight');
    await highlight.hover();
    const fixBtn = page.locator('[data-testid="quick-fix-btn"]');
    await fixBtn.click();

    // 驗證問題被修復
    await page.waitForTimeout(500);
    const newCount = await getIssueCount(page);
    expect(newCount).toBeLessThan(initialCount);
  });
});

test.describe('WYSIWYG Preview - Issue Summary', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('displays issue summary bar', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.multipleIssues);
    await waitForAnalysis(page);

    // 驗證摘要欄顯示
    const summaryBar = page.locator('.issue-summary-bar');
    await expect(summaryBar).toBeVisible();

    // 應該顯示各類問題計數
    await expect(summaryBar).toContainText(/字體/);
    await expect(summaryBar).toContainText(/\d+/);
  });

  test('summary bar categorizes issues', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.multipleIssues);
    await waitForAnalysis(page);

    // 驗證問題分類
    const fontIssues = page.locator('[data-issue-type="font"]');
    const nestingIssues = page.locator('[data-issue-type="nesting"]');
    const emptyIssues = page.locator('[data-issue-type="empty"]');

    // 至少應該有字體問題
    await expect(fontIssues).toBeVisible();
  });
});

test.describe('WYSIWYG Preview - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test('supports keyboard navigation', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.multipleIssues);
    await waitForAnalysis(page);

    // Tab 導航到第一個問題
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // 應該聚焦到問題列表
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toHaveAttribute('role', 'listitem');

    // Enter 鍵選擇
    await page.keyboard.press('Enter');

    // 問題應該被高亮
    const highlight = page.locator('.font-issue-highlight.focused');
    await expect(highlight).toBeVisible();
  });

  test('has proper ARIA labels', async ({ page }) => {
    await navigateToPreview(page, TEST_SAMPLES.timesNewRoman);
    await waitForAnalysis(page);

    // 驗證 ARIA 標籤
    const previewRegion = page.locator('[role="region"][aria-label*="預覽"]');
    await expect(previewRegion).toBeVisible();

    const issueList = page.locator('[role="list"][aria-label*="問題"]');
    await expect(issueList).toBeVisible();
  });
});

test.describe('WYSIWYG Preview - Performance', () => {
  test('handles large content efficiently', async ({ page }) => {
    // 生成大量內容
    const largeContent = `
      <div>
        ${Array(100).fill('<p style="font-family: Arial;">這是一段測試內容，用於測試性能。</p>').join('')}
        <p style="font-family: 'Times New Roman';">異常字體段落</p>
        ${Array(100).fill('<p>更多正常內容</p>').join('')}
      </div>
    `;

    const startTime = Date.now();
    await navigateToPreview(page, largeContent);
    await waitForAnalysis(page);
    const loadTime = Date.now() - startTime;

    // 應該在合理時間內完成（5秒以內）
    expect(loadTime).toBeLessThan(5000);

    // 內容應該正確渲染
    await expect(page.locator('.preview-content')).toBeVisible();
  });
});
