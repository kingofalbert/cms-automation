/**
 * useHtmlAnalysis - HTML 分析 Hook
 *
 * 提供 HTML 內容分析功能，包括字體檢測和問題識別
 *
 * @version 1.0
 * @date 2025-12-19
 */

import { useMemo, useCallback, useState } from 'react';
import {
  HtmlAnalysisResult,
  HtmlIssue,
  FontAnalysisResult,
  DEFAULT_ALLOWED_FONTS,
} from '../components/common/SafeHtmlRenderer/types';
import {
  FontAnalyzer,
  analyzeHtmlFonts,
  removeProblematicFonts,
} from '../components/common/SafeHtmlRenderer/FontAnalyzer';
import {
  IssueDetector,
  detectAllIssues,
  isGDocsContaminated,
  cleanGDocsContamination,
  removeEmptyTags,
} from '../components/common/SafeHtmlRenderer/IssueDetector';

// ============================================================
// Types
// ============================================================

interface UseHtmlAnalysisOptions {
  /** 允許的字體列表 */
  allowedFonts?: string[];
  /** 是否檢測 Google Docs 污染 */
  detectGDocs?: boolean;
  /** 是否檢測嵌套錯誤 */
  detectNesting?: boolean;
  /** 是否檢測空標籤 */
  detectEmpty?: boolean;
  /** 是否檢測可訪問性問題 */
  detectAccessibility?: boolean;
}

interface UseHtmlAnalysisResult {
  /** 所有問題列表 */
  issues: HtmlIssue[];
  /** 字體分析結果 */
  fonts: FontAnalysisResult;
  /** 是否有 Google Docs 污染 */
  isGDocsContaminated: boolean;
  /** 清理後的 HTML */
  cleanHtml: string;
  /** 問題統計 */
  stats: {
    totalIssues: number;
    fontIssues: number;
    nestingIssues: number;
    emptyTagIssues: number;
    otherIssues: number;
  };
  /** 是否有問題 */
  hasIssues: boolean;
  /** 修復函數 */
  fix: {
    /** 修復所有問題 */
    all: () => string;
    /** 只修復字體問題 */
    fonts: () => string;
    /** 只清理 Google Docs 污染 */
    gdocs: () => string;
    /** 只移除空標籤 */
    emptyTags: () => string;
  };
}

// ============================================================
// Hook Implementation
// ============================================================

export function useHtmlAnalysis(
  html: string,
  options: UseHtmlAnalysisOptions = {}
): UseHtmlAnalysisResult {
  const {
    allowedFonts = [...DEFAULT_ALLOWED_FONTS],
    detectGDocs = true,
    detectNesting = true,
    detectEmpty = true,
    detectAccessibility = true,
  } = options;

  // 分析結果（Memoized）
  const analysis = useMemo<HtmlAnalysisResult>(() => {
    // 分析字體
    const fontAnalysis = analyzeHtmlFonts(html, allowedFonts);

    // 檢測其他問題
    const otherIssues = detectAllIssues(html, {
      detectNesting,
      detectEmpty,
      detectDeprecated: true,
      detectGDocs,
      detectAccessibility,
    });

    // 合併所有問題
    const allIssues = [...fontAnalysis.issues, ...otherIssues];

    // 統計
    const stats = {
      totalIssues: allIssues.length,
      fontIssues: fontAnalysis.issues.length,
      nestingIssues: otherIssues.filter(i => i.type === 'nesting').length,
      emptyTagIssues: otherIssues.filter(i => i.type === 'empty').length,
      otherIssues: otherIssues.filter(i => !['nesting', 'empty', 'font'].includes(i.type)).length,
    };

    // 清理後的 HTML
    const cleanHtml = detectGDocs ? cleanGDocsContamination(html) : html;

    return {
      issues: allIssues,
      fonts: fontAnalysis,
      isGDocsContaminated: isGDocsContaminated(html),
      cleanHtml,
      stats,
    };
  }, [html, allowedFonts, detectGDocs, detectNesting, detectEmpty, detectAccessibility]);

  // 修復函數
  const fixAll = useCallback((): string => {
    let result = html;

    // 1. 清理 Google Docs 污染
    result = cleanGDocsContamination(result);

    // 2. 移除問題字體
    result = removeProblematicFonts(result);

    // 3. 移除空標籤
    result = removeEmptyTags(result);

    return result;
  }, [html]);

  const fixFonts = useCallback((): string => {
    return removeProblematicFonts(html);
  }, [html]);

  const fixGDocs = useCallback((): string => {
    return cleanGDocsContamination(html);
  }, [html]);

  const fixEmptyTags = useCallback((): string => {
    return removeEmptyTags(html);
  }, [html]);

  return {
    issues: analysis.issues,
    fonts: analysis.fonts,
    isGDocsContaminated: analysis.isGDocsContaminated,
    cleanHtml: analysis.cleanHtml,
    stats: analysis.stats,
    hasIssues: analysis.stats.totalIssues > 0,
    fix: {
      all: fixAll,
      fonts: fixFonts,
      gdocs: fixGDocs,
      emptyTags: fixEmptyTags,
    },
  };
}

// ============================================================
// Additional Hooks
// ============================================================

/**
 * 只檢測字體問題
 */
export function useFontAnalysis(
  html: string,
  allowedFonts: string[] = [...DEFAULT_ALLOWED_FONTS]
): FontAnalysisResult {
  return useMemo(() => {
    return analyzeHtmlFonts(html, allowedFonts);
  }, [html, allowedFonts]);
}

/**
 * 檢查是否有 Google Docs 污染
 */
export function useGDocsDetection(html: string): {
  isContaminated: boolean;
  cleanHtml: string;
} {
  return useMemo(() => ({
    isContaminated: isGDocsContaminated(html),
    cleanHtml: cleanGDocsContamination(html),
  }), [html]);
}

export default useHtmlAnalysis;
