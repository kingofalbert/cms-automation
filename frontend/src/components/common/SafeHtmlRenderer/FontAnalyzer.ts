/**
 * FontAnalyzer - 字體分析器
 *
 * 分析 HTML 內容中的字體使用情況，識別問題字體
 *
 * @version 1.0
 * @date 2025-12-19
 */

import {
  FontCheckResult,
  FontAnalysisResult,
  FontCategory,
  HtmlIssue,
  IssueSeverity,
  SYSTEM_FONTS,
  CHINESE_FONTS,
  WEB_SAFE_FONTS,
  PROBLEMATIC_FONTS,
  DEFAULT_ALLOWED_FONTS,
} from './types';

// ============================================================
// Font Parser
// ============================================================

/**
 * 解析 font-family CSS 值
 * @param fontFamily - CSS font-family 字符串
 * @returns 解析後的字體列表
 */
export function parseFontFamily(fontFamily: string): string[] {
  if (!fontFamily) return [];

  return fontFamily
    .split(',')
    .map(font => {
      // 移除引號和空白
      return font
        .trim()
        .replace(/^['"]|['"]$/g, '')
        .trim();
    })
    .filter(font => font.length > 0);
}

/**
 * 標準化字體名稱（用於比較）
 */
function normalizeFontName(font: string): string {
  return font.toLowerCase().replace(/['"]/g, '').trim();
}

/**
 * 檢查字體是否在列表中
 */
function isFontInList(font: string, list: readonly string[]): boolean {
  const normalized = normalizeFontName(font);
  return list.some(f => normalizeFontName(f) === normalized);
}

// ============================================================
// Font Checker
// ============================================================

/**
 * 檢查單個字體
 */
export function checkFont(
  fontFamily: string,
  allowedFonts: string[] = [...DEFAULT_ALLOWED_FONTS]
): FontCheckResult {
  const fonts = parseFontFamily(fontFamily);

  if (fonts.length === 0) {
    return {
      isValid: true,
      fontFamily,
      primaryFont: '',
      fallbackFonts: [],
      category: 'system',
      severity: 'ok',
    };
  }

  const primaryFont = fonts[0];
  const fallbackFonts = fonts.slice(1);

  // 1. 檢查是否是系統字體
  if (isFontInList(primaryFont, SYSTEM_FONTS)) {
    return {
      isValid: true,
      fontFamily,
      primaryFont,
      fallbackFonts,
      category: 'system',
      severity: 'ok',
    };
  }

  // 2. 檢查是否是中文字體
  if (isFontInList(primaryFont, CHINESE_FONTS)) {
    return {
      isValid: true,
      fontFamily,
      primaryFont,
      fallbackFonts,
      category: 'chinese',
      severity: 'ok',
    };
  }

  // 3. 檢查是否是網頁安全字體
  if (isFontInList(primaryFont, WEB_SAFE_FONTS)) {
    return {
      isValid: true,
      fontFamily,
      primaryFont,
      fallbackFonts,
      category: 'web-safe',
      severity: 'ok',
    };
  }

  // 4. 檢查是否在允許列表中
  if (isFontInList(primaryFont, allowedFonts)) {
    return {
      isValid: true,
      fontFamily,
      primaryFont,
      fallbackFonts,
      category: 'web-safe',
      severity: 'ok',
    };
  }

  // 5. 檢查是否是問題字體
  if (isFontInList(primaryFont, PROBLEMATIC_FONTS)) {
    // 判斷是印刷字體還是 Office 字體
    const isPrintFont = ['SimSun', '宋体', '宋體', 'FangSong', '仿宋', 'KaiTi', '楷体', '楷體']
      .some(f => normalizeFontName(f) === normalizeFontName(primaryFont));

    return {
      isValid: false,
      fontFamily,
      primaryFont,
      fallbackFonts,
      category: 'problematic',
      severity: 'warning',
      message: isPrintFont
        ? `"${primaryFont}" 是印刷字體，不適合屏幕顯示`
        : `"${primaryFont}" 可能導致跨平台顯示不一致`,
      suggestion: '建議移除內聯字體樣式，使用系統默認字體',
    };
  }

  // 6. 未知字體
  return {
    isValid: false,
    fontFamily,
    primaryFont,
    fallbackFonts,
    category: 'unknown',
    severity: 'info',
    message: `未識別的字體: "${primaryFont}"`,
    suggestion: '請確認此字體在目標平台上可用',
  };
}

// ============================================================
// HTML Font Analyzer
// ============================================================

/**
 * 從 HTML 中提取所有 font-family 聲明
 */
function extractFontFamilies(html: string): Array<{
  fontFamily: string;
  position: { start: number; end: number };
  element: string;
}> {
  const results: Array<{
    fontFamily: string;
    position: { start: number; end: number };
    element: string;
  }> = [];

  // 匹配 style 屬性中的 font-family
  const styleRegex = /<([a-z][a-z0-9]*)[^>]*style="[^"]*font-family:\s*([^";]+)[^"]*"[^>]*>/gi;

  let match;
  while ((match = styleRegex.exec(html)) !== null) {
    results.push({
      fontFamily: match[2].trim(),
      position: {
        start: match.index,
        end: match.index + match[0].length,
      },
      element: match[1],
    });
  }

  return results;
}

/**
 * 分析 HTML 中的所有字體
 */
export function analyzeHtmlFonts(
  html: string,
  allowedFonts: string[] = [...DEFAULT_ALLOWED_FONTS]
): FontAnalysisResult {
  const fontDeclarations = extractFontFamilies(html);
  const fonts: FontCheckResult[] = [];
  const issues: HtmlIssue[] = [];
  const uniqueFontsSet = new Set<string>();
  let hasProblematicFonts = false;

  for (const declaration of fontDeclarations) {
    const result = checkFont(declaration.fontFamily, allowedFonts);
    fonts.push(result);

    // 收集唯一字體
    if (result.primaryFont) {
      uniqueFontsSet.add(result.primaryFont);
    }

    // 如果有問題，創建 issue
    if (!result.isValid) {
      hasProblematicFonts = true;

      issues.push({
        id: `font-${declaration.position.start}`,
        type: 'font',
        severity: result.severity as IssueSeverity,
        message: result.message || `檢測到非標準字體: ${result.primaryFont}`,
        element: declaration.element,
        position: declaration.position,
        suggestion: result.suggestion,
        autoFixable: true,
        details: {
          fontFamily: declaration.fontFamily,
          primaryFont: result.primaryFont,
          category: result.category,
        },
      });
    }
  }

  return {
    fonts,
    issues,
    hasProblematicFonts,
    uniqueFonts: Array.from(uniqueFontsSet),
  };
}

// ============================================================
// Font Fixer
// ============================================================

/**
 * 從 HTML 中移除問題字體的內聯樣式
 */
export function removeProblematicFonts(html: string): string {
  // 移除 font-family 聲明
  let result = html.replace(
    /(<[^>]*style="[^"]*)font-family:\s*[^";]+;?\s*([^"]*")/gi,
    '$1$2'
  );

  // 清理空的 style 屬性
  result = result.replace(/\s*style="\s*"/gi, '');

  return result;
}

/**
 * 替換特定字體為標準字體
 */
export function replaceFont(
  html: string,
  targetFont: string,
  replacementFont: string = 'inherit'
): string {
  const escapedFont = targetFont.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(
    `font-family:\\s*['"]?${escapedFont}['"]?\\s*(?:,\\s*[^;"}]+)?`,
    'gi'
  );

  return html.replace(regex, `font-family: ${replacementFont}`);
}

// ============================================================
// Export
// ============================================================

export class FontAnalyzer {
  private allowedFonts: string[];

  constructor(allowedFonts: string[] = [...DEFAULT_ALLOWED_FONTS]) {
    this.allowedFonts = allowedFonts;
  }

  /**
   * 分析 HTML 中的字體
   */
  analyze(html: string): FontAnalysisResult {
    return analyzeHtmlFonts(html, this.allowedFonts);
  }

  /**
   * 檢查單個字體
   */
  checkFont(fontFamily: string): FontCheckResult {
    return checkFont(fontFamily, this.allowedFonts);
  }

  /**
   * 移除問題字體
   */
  removeProblematicFonts(html: string): string {
    return removeProblematicFonts(html);
  }

  /**
   * 替換字體
   */
  replaceFont(html: string, targetFont: string, replacementFont?: string): string {
    return replaceFont(html, targetFont, replacementFont);
  }

  /**
   * 添加允許的字體
   */
  addAllowedFont(font: string): void {
    if (!this.allowedFonts.includes(font)) {
      this.allowedFonts.push(font);
    }
  }

  /**
   * 獲取允許的字體列表
   */
  getAllowedFonts(): string[] {
    return [...this.allowedFonts];
  }
}

export default FontAnalyzer;
