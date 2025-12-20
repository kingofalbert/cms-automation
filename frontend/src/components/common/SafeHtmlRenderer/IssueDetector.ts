/**
 * IssueDetector - HTML 問題檢測器
 *
 * 檢測 HTML 中的常見問題：
 * - 嵌套錯誤
 * - 空標籤
 * - 廢棄標籤
 * - Google Docs 污染
 *
 * @version 1.0
 * @date 2025-12-19
 */

import {
  HtmlIssue,
  IssueType,
  IssueSeverity,
  GDOCS_PATTERNS,
} from './types';

// ============================================================
// Issue Detection Functions
// ============================================================

/**
 * 檢測嵌套錯誤
 * 例如: <p><p>內容</p></p>
 */
export function detectNestingIssues(html: string): HtmlIssue[] {
  const issues: HtmlIssue[] = [];

  // 不能嵌套的標籤對
  const invalidNestings = [
    { outer: 'p', inner: 'p' },
    { outer: 'p', inner: 'div' },
    { outer: 'a', inner: 'a' },
    { outer: 'button', inner: 'button' },
    { outer: 'h1', inner: 'h1' },
    { outer: 'h2', inner: 'h2' },
    { outer: 'h3', inner: 'h3' },
    { outer: 'li', inner: 'li' },
  ];

  for (const { outer, inner } of invalidNestings) {
    const regex = new RegExp(
      `<${outer}[^>]*>([^<]*<${inner}[^>]*>)`,
      'gi'
    );

    let match;
    while ((match = regex.exec(html)) !== null) {
      issues.push({
        id: `nesting-${match.index}`,
        type: 'nesting',
        severity: 'error',
        message: `<${inner}> 標籤不能嵌套在 <${outer}> 內`,
        element: outer,
        position: {
          start: match.index,
          end: match.index + match[0].length,
        },
        suggestion: `移除內層的 <${inner}> 標籤或重構 HTML 結構`,
        autoFixable: false,
      });
    }
  }

  return issues;
}

/**
 * 檢測空標籤
 * 例如: <span></span>, <div style="..."></div>
 */
export function detectEmptyTags(html: string): HtmlIssue[] {
  const issues: HtmlIssue[] = [];

  // 匹配空標籤（可能有屬性但沒有內容）
  const emptyTagRegex = /<(span|div|p|a|strong|em|b|i|u)[^>]*>\s*<\/\1>/gi;

  let match;
  while ((match = emptyTagRegex.exec(html)) !== null) {
    const tagName = match[1];
    const fullMatch = match[0];

    // 檢查是否有視覺相關的樣式（如果有，可能是有意的）
    const hasVisualStyle = /style="[^"]*(?:background|border|width|height|display)/i.test(fullMatch);

    if (!hasVisualStyle) {
      issues.push({
        id: `empty-${match.index}`,
        type: 'empty',
        severity: 'info',
        message: `空的 <${tagName}> 標籤`,
        element: tagName,
        position: {
          start: match.index,
          end: match.index + fullMatch.length,
        },
        suggestion: '移除空標籤或添加內容',
        autoFixable: true,
      });
    }
  }

  return issues;
}

/**
 * 檢測廢棄的 HTML 標籤
 */
export function detectDeprecatedTags(html: string): HtmlIssue[] {
  const issues: HtmlIssue[] = [];

  const deprecatedTags = [
    { tag: 'font', suggestion: '使用 CSS font-family' },
    { tag: 'center', suggestion: '使用 CSS text-align: center' },
    { tag: 'strike', suggestion: '使用 <del> 或 CSS text-decoration' },
    { tag: 'u', suggestion: '謹慎使用，可能與鏈接混淆' },
    { tag: 'marquee', suggestion: '使用 CSS 動畫' },
    { tag: 'blink', suggestion: '不建議使用閃爍效果' },
    { tag: 'big', suggestion: '使用 CSS font-size' },
    { tag: 'tt', suggestion: '使用 <code> 或 CSS font-family: monospace' },
  ];

  for (const { tag, suggestion } of deprecatedTags) {
    const regex = new RegExp(`<${tag}[^>]*>`, 'gi');

    let match;
    while ((match = regex.exec(html)) !== null) {
      issues.push({
        id: `deprecated-${match.index}`,
        type: 'deprecated',
        severity: 'warning',
        message: `<${tag}> 是廢棄的 HTML 標籤`,
        element: tag,
        position: {
          start: match.index,
          end: match.index + match[0].length,
        },
        suggestion,
        autoFixable: false,
      });
    }
  }

  return issues;
}

/**
 * 檢測 Google Docs 污染
 */
function detectGDocsContamination(html: string): HtmlIssue[] {
  const issues: HtmlIssue[] = [];
  let isContaminated = false;

  // 檢查 orphans/widows 樣式
  if (GDOCS_PATTERNS.orphansWidows.test(html)) {
    isContaminated = true;
  }

  // 檢查 Google Docs 類名
  if (GDOCS_PATTERNS.classNames.test(html)) {
    isContaminated = true;
  }

  // 檢查空的樣式 span
  const emptyStyledSpanMatches = html.match(GDOCS_PATTERNS.emptyStyledSpan);
  if (emptyStyledSpanMatches) {
    isContaminated = true;
  }

  // 如果檢測到污染，創建一個總體警告
  if (isContaminated) {
    issues.push({
      id: 'gdocs-contamination',
      type: 'gdocs',
      severity: 'warning',
      message: '檢測到 Google Docs 導入的內容污染',
      element: 'document',
      position: { start: 0, end: html.length },
      suggestion: '建議使用「清理 Google Docs」功能移除多餘的樣式和類名',
      autoFixable: true,
      details: {
        hasOrphansWidows: GDOCS_PATTERNS.orphansWidows.test(html),
        hasGDocsClasses: GDOCS_PATTERNS.classNames.test(html),
        hasEmptyStyledSpans: !!emptyStyledSpanMatches,
      },
    });
  }

  return issues;
}

/**
 * 檢測可訪問性問題
 */
function detectAccessibilityIssues(html: string): HtmlIssue[] {
  const issues: HtmlIssue[] = [];

  // 檢查沒有 alt 的圖片
  const imgWithoutAltRegex = /<img(?![^>]*alt=)[^>]*>/gi;
  let match;
  while ((match = imgWithoutAltRegex.exec(html)) !== null) {
    issues.push({
      id: `a11y-img-${match.index}`,
      type: 'accessibility',
      severity: 'warning',
      message: '圖片缺少 alt 屬性',
      element: 'img',
      position: {
        start: match.index,
        end: match.index + match[0].length,
      },
      suggestion: '添加描述性的 alt 屬性以提高可訪問性',
      autoFixable: false,
    });
  }

  // 檢查空的鏈接
  const emptyLinkRegex = /<a[^>]*>\s*<\/a>/gi;
  while ((match = emptyLinkRegex.exec(html)) !== null) {
    issues.push({
      id: `a11y-link-${match.index}`,
      type: 'accessibility',
      severity: 'warning',
      message: '空的鏈接標籤',
      element: 'a',
      position: {
        start: match.index,
        end: match.index + match[0].length,
      },
      suggestion: '添加鏈接文字或 aria-label',
      autoFixable: false,
    });
  }

  return issues;
}

// ============================================================
// Main Detector
// ============================================================

export interface IssueDetectorOptions {
  detectNesting?: boolean;
  detectEmpty?: boolean;
  detectDeprecated?: boolean;
  detectGDocs?: boolean;
  detectAccessibility?: boolean;
}

const DEFAULT_OPTIONS: IssueDetectorOptions = {
  detectNesting: true,
  detectEmpty: true,
  detectDeprecated: true,
  detectGDocs: true,
  detectAccessibility: true,
};

/**
 * 檢測 HTML 中的所有問題
 */
export function detectAllIssues(
  html: string,
  options: IssueDetectorOptions = DEFAULT_OPTIONS
): HtmlIssue[] {
  const allIssues: HtmlIssue[] = [];

  if (options.detectNesting) {
    allIssues.push(...detectNestingIssues(html));
  }

  if (options.detectEmpty) {
    allIssues.push(...detectEmptyTags(html));
  }

  if (options.detectDeprecated) {
    allIssues.push(...detectDeprecatedTags(html));
  }

  if (options.detectGDocs) {
    allIssues.push(...detectGDocsContamination(html));
  }

  if (options.detectAccessibility) {
    allIssues.push(...detectAccessibilityIssues(html));
  }

  // 按位置排序
  allIssues.sort((a, b) => a.position.start - b.position.start);

  return allIssues;
}

/**
 * 檢查是否有 Google Docs 污染
 */
export function isGDocsContaminated(html: string): boolean {
  // Reset regex lastIndex to ensure consistent matching
  GDOCS_PATTERNS.orphansWidows.lastIndex = 0;
  GDOCS_PATTERNS.classNames.lastIndex = 0;
  GDOCS_PATTERNS.emptyStyledSpan.lastIndex = 0;

  return (
    GDOCS_PATTERNS.orphansWidows.test(html) ||
    GDOCS_PATTERNS.classNames.test(html) ||
    GDOCS_PATTERNS.emptyStyledSpan.test(html) ||
    /id="docs-internal-guid-[^"]*"/i.test(html) ||
    /data-cso=/i.test(html)
  );
}

/**
 * 統計問題
 */
export function countIssuesByType(issues: HtmlIssue[]): Record<IssueType, number> {
  const counts: Record<IssueType, number> = {
    font: 0,
    nesting: 0,
    empty: 0,
    deprecated: 0,
    accessibility: 0,
    gdocs: 0,
  };

  for (const issue of issues) {
    counts[issue.type]++;
  }

  return counts;
}

/**
 * 統計嚴重程度
 */
export function countIssuesBySeverity(issues: HtmlIssue[]): Record<IssueSeverity, number> {
  const counts: Record<IssueSeverity, number> = {
    error: 0,
    warning: 0,
    info: 0,
  };

  for (const issue of issues) {
    counts[issue.severity]++;
  }

  return counts;
}

// ============================================================
// Issue Fixer
// ============================================================

/**
 * 移除空標籤
 */
export function removeEmptyTags(html: string): string {
  // 迭代移除，因為移除後可能產生新的空標籤
  let result = html;
  let previousResult = '';

  while (result !== previousResult) {
    previousResult = result;
    result = result.replace(/<(span|div|p|a|strong|em|b|i|u)[^>]*>\s*<\/\1>/gi, '');
  }

  return result;
}

/**
 * 清理 Google Docs 污染
 */
export function cleanGDocsContamination(html: string): string {
  let result = html;

  // 移除 orphans/widows 樣式
  result = result.replace(/(?:orphans|widows):\s*\d+;?\s*/gi, '');

  // 移除 Google Docs 類名
  result = result.replace(/\s*class="[^"]*(?:c\d+|p\d+)[^"]*"/gi, '');

  // 移除空的樣式 span
  result = result.replace(/<span[^>]*style="[^"]*"[^>]*>\s*<\/span>/gi, '');

  // 移除 text-indent 樣式
  result = result.replace(/text-indent:\s*[^;]+;?\s*/gi, '');

  // 移除 margin: 0; padding: 0; 樣式
  result = result.replace(/(?:margin|padding):\s*0(?:px)?;?\s*/gi, '');

  // 移除 docs-internal-guid id
  result = result.replace(/\s*id="docs-internal-guid-[^"]*"/gi, '');

  // 移除 data-cso 屬性
  result = result.replace(/\s*data-cso="[^"]*"/gi, '');

  // 清理空的 style 屬性
  result = result.replace(/\s*style="\s*"/gi, '');

  // 清理空的 class 屬性
  result = result.replace(/\s*class="\s*"/gi, '');

  return result;
}

// ============================================================
// Export
// ============================================================

export class IssueDetector {
  private options: IssueDetectorOptions;

  constructor(options: IssueDetectorOptions = DEFAULT_OPTIONS) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  /**
   * 檢測所有問題
   */
  detect(html: string): HtmlIssue[] {
    return detectAllIssues(html, this.options);
  }

  /**
   * 檢查 Google Docs 污染
   */
  isGDocsContaminated(html: string): boolean {
    return isGDocsContaminated(html);
  }

  /**
   * 統計問題
   */
  countByType(issues: HtmlIssue[]): Record<IssueType, number> {
    return countIssuesByType(issues);
  }

  /**
   * 修復空標籤
   */
  fixEmptyTags(html: string): string {
    return removeEmptyTags(html);
  }

  /**
   * 清理 Google Docs 污染
   */
  cleanGDocs(html: string): string {
    return cleanGDocsContamination(html);
  }
}

export default IssueDetector;
