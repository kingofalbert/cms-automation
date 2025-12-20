/**
 * SafeHtmlRenderer - 安全的 HTML 渲染器
 *
 * 提供 WYSIWYG 預覽功能，包括：
 * - 安全的 HTML 渲染
 * - 字體異常檢測與標註
 * - 格式問題高亮
 * - 模式切換（預覽/源碼/混合）
 *
 * @version 1.0
 * @date 2025-12-19
 */

import React, { useMemo, useState, useCallback, useEffect } from 'react';
import DOMPurify from 'dompurify';
import {
  SafeHtmlRendererProps,
  ViewMode,
  HtmlIssue,
  HtmlAnalysisResult,
  DEFAULT_ALLOWED_FONTS,
  SEVERITY_COLORS,
  ISSUE_TYPE_ICONS,
} from './types';
import { FontAnalyzer, analyzeHtmlFonts } from './FontAnalyzer';
import { IssueDetector, detectAllIssues, cleanGDocsContamination } from './IssueDetector';
import ModeToggle from './ModeToggle';
import IssueSummary from './IssueSummary';
import IssueMarker from './IssueMarker';

// ============================================================
// Main Component
// ============================================================

export const SafeHtmlRenderer: React.FC<SafeHtmlRendererProps> = ({
  html,
  mode: initialMode = 'preview',
  showIssues = true,
  allowedFonts = [...DEFAULT_ALLOWED_FONTS],
  detectGDocs = true,
  enableAutoFix = true,
  onIssueClick,
  onIssueFix,
  onModeChange,
  onAnalysisComplete,
  className = '',
  showToolbar = true,
  showSummary = true,
  maxHeight,
}) => {
  // ============================================================
  // State
  // ============================================================

  const [mode, setMode] = useState<ViewMode>(initialMode);
  const [selectedIssue, setSelectedIssue] = useState<HtmlIssue | null>(null);
  const [currentHtml, setCurrentHtml] = useState(html);

  // Update html when prop changes
  useEffect(() => {
    setCurrentHtml(html);
  }, [html]);

  // ============================================================
  // Analysis
  // ============================================================

  const analysis = useMemo<HtmlAnalysisResult>(() => {
    // 分析字體
    const fontAnalysis = analyzeHtmlFonts(currentHtml, allowedFonts);

    // 檢測其他問題
    const otherIssues = detectAllIssues(currentHtml, {
      detectNesting: true,
      detectEmpty: true,
      detectDeprecated: true,
      detectGDocs,
      detectAccessibility: true,
    });

    // 合併問題
    const allIssues = [...fontAnalysis.issues, ...otherIssues];

    // 統計
    const stats = {
      totalIssues: allIssues.length,
      fontIssues: fontAnalysis.issues.length,
      nestingIssues: otherIssues.filter(i => i.type === 'nesting').length,
      emptyTagIssues: otherIssues.filter(i => i.type === 'empty').length,
      otherIssues: otherIssues.filter(i => !['nesting', 'empty'].includes(i.type)).length,
    };

    // 清理後的 HTML（用於渲染）
    const cleanHtml = detectGDocs ? cleanGDocsContamination(currentHtml) : currentHtml;

    const result: HtmlAnalysisResult = {
      issues: allIssues,
      fonts: fontAnalysis,
      isGDocsContaminated: fontAnalysis.hasProblematicFonts || otherIssues.some(i => i.type === 'gdocs'),
      cleanHtml,
      stats,
    };

    return result;
  }, [currentHtml, allowedFonts, detectGDocs]);

  // 通知分析完成
  useEffect(() => {
    onAnalysisComplete?.(analysis);
  }, [analysis, onAnalysisComplete]);

  // ============================================================
  // Handlers
  // ============================================================

  const handleModeChange = useCallback((newMode: ViewMode) => {
    setMode(newMode);
    onModeChange?.(newMode);
  }, [onModeChange]);

  const handleIssueClick = useCallback((issue: HtmlIssue) => {
    setSelectedIssue(issue);
    onIssueClick?.(issue);
  }, [onIssueClick]);

  const handleIssueFix = useCallback((issue: HtmlIssue) => {
    if (!enableAutoFix || !issue.autoFixable) return;

    let fixedHtml = currentHtml;

    // 根據問題類型進行修復
    switch (issue.type) {
      case 'font':
        // 移除問題字體的內聯樣式
        const fontAnalyzer = new FontAnalyzer(allowedFonts);
        fixedHtml = fontAnalyzer.removeProblematicFonts(currentHtml);
        break;

      case 'empty':
        // 移除空標籤
        const issueDetector = new IssueDetector();
        fixedHtml = issueDetector.fixEmptyTags(currentHtml);
        break;

      case 'gdocs':
        // 清理 Google Docs 污染
        fixedHtml = cleanGDocsContamination(currentHtml);
        break;

      default:
        return;
    }

    setCurrentHtml(fixedHtml);
    setSelectedIssue(null);
    onIssueFix?.(issue, fixedHtml);
  }, [currentHtml, enableAutoFix, allowedFonts, onIssueFix]);

  const handleFixAll = useCallback(() => {
    let fixedHtml = currentHtml;

    // 1. 清理 Google Docs 污染
    fixedHtml = cleanGDocsContamination(fixedHtml);

    // 2. 移除問題字體
    const fontAnalyzer = new FontAnalyzer(allowedFonts);
    fixedHtml = fontAnalyzer.removeProblematicFonts(fixedHtml);

    // 3. 移除空標籤
    const issueDetector = new IssueDetector();
    fixedHtml = issueDetector.fixEmptyTags(fixedHtml);

    setCurrentHtml(fixedHtml);
  }, [currentHtml, allowedFonts]);

  // ============================================================
  // Render Functions
  // ============================================================

  /**
   * 渲染預覽模式
   */
  const renderPreviewMode = () => {
    // 使用 DOMPurify 清理 HTML
    const sanitizedHtml = DOMPurify.sanitize(analysis.cleanHtml, {
      ADD_TAGS: ['iframe'],
      ADD_ATTR: ['target', 'allow', 'allowfullscreen'],
    });

    return (
      <div className="preview-mode">
        {/* 渲染帶問題標記的內容 */}
        {showIssues && analysis.issues.length > 0 ? (
          <div className="relative">
            {/* 基礎渲染 */}
            <div
              className="preview-content prose prose-sm max-w-none text-gray-800"
              dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            />

            {/* 問題標記覆蓋層 */}
            <div className="absolute inset-0 pointer-events-none">
              {analysis.issues.map(issue => (
                <IssueMarker
                  key={issue.id}
                  issue={issue}
                  onClick={() => handleIssueClick(issue)}
                  onFix={() => handleIssueFix(issue)}
                >
                  <span className="pointer-events-auto" />
                </IssueMarker>
              ))}
            </div>
          </div>
        ) : (
          <div
            className="preview-content prose prose-sm max-w-none text-gray-800"
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
          />
        )}
      </div>
    );
  };

  /**
   * 渲染源碼模式
   */
  const renderSourceMode = () => {
    return (
      <div className="source-mode">
        <pre className="bg-gray-50 p-4 rounded-lg overflow-auto text-sm font-mono text-gray-700 whitespace-pre-wrap">
          <code>{currentHtml}</code>
        </pre>
      </div>
    );
  };

  /**
   * 渲染混合模式
   */
  const renderHybridMode = () => {
    return (
      <div className="hybrid-mode grid grid-cols-2 gap-4">
        {/* 左側：預覽 */}
        <div className="border-r pr-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">預覽</h4>
          {renderPreviewMode()}
        </div>

        {/* 右側：源碼 */}
        <div className="pl-4">
          <h4 className="text-sm font-medium text-gray-500 mb-2">源碼</h4>
          {renderSourceMode()}
        </div>
      </div>
    );
  };

  // ============================================================
  // Main Render
  // ============================================================

  const containerStyle = maxHeight
    ? { maxHeight: typeof maxHeight === 'number' ? `${maxHeight}px` : maxHeight }
    : {};

  return (
    <div
      className={`safe-html-renderer ${className}`}
      data-testid="safe-html-renderer"
    >
      {/* 工具欄 */}
      {showToolbar && (
        <div className="preview-toolbar flex items-center justify-between mb-4 pb-3 border-b">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">內容預覽</span>
            {analysis.isGDocsContaminated && (
              <span className="gdocs-warning inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                📄 Google Docs 內容
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* 一鍵修復按鈕 */}
            {enableAutoFix && analysis.stats.totalIssues > 0 && (
              <button
                onClick={handleFixAll}
                className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-md transition-colors"
                data-testid="fix-all-btn"
              >
                🔧 修復所有問題
              </button>
            )}

            {/* 模式切換 */}
            <ModeToggle
              currentMode={mode}
              onChange={handleModeChange}
            />
          </div>
        </div>
      )}

      {/* 問題摘要 */}
      {showSummary && analysis.issues.length > 0 && (
        <IssueSummary
          issues={analysis.issues}
          onCategoryClick={(type) => {
            const firstIssue = analysis.issues.find(i => i.type === type);
            if (firstIssue) handleIssueClick(firstIssue);
          }}
        />
      )}

      {/* 內容區域 */}
      <div
        className="preview-container overflow-auto"
        style={containerStyle}
        role="region"
        aria-label="內容預覽區域"
        data-testid="analysis-complete"
      >
        {mode === 'preview' && renderPreviewMode()}
        {mode === 'source' && renderSourceMode()}
        {mode === 'hybrid' && renderHybridMode()}
      </div>

      {/* 問題詳情面板（選中問題時顯示） */}
      {selectedIssue && (
        <div className="issue-detail-panel mt-4 p-4 bg-gray-50 rounded-lg border">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{ISSUE_TYPE_ICONS[selectedIssue.type]}</span>
                <span className={`font-medium ${SEVERITY_COLORS[selectedIssue.severity].text}`}>
                  {selectedIssue.message}
                </span>
              </div>
              {selectedIssue.suggestion && (
                <p className="text-sm text-gray-600 mb-3">
                  💡 {selectedIssue.suggestion}
                </p>
              )}
            </div>

            <button
              onClick={() => setSelectedIssue(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {selectedIssue.autoFixable && enableAutoFix && (
            <button
              onClick={() => handleIssueFix(selectedIssue)}
              className="mt-2 inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              data-testid="quick-fix-btn"
            >
              🔧 一鍵修復
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================
// Exports
// ============================================================

export { ModeToggle } from './ModeToggle';
export { IssueSummary } from './IssueSummary';
export { IssueMarker } from './IssueMarker';
export { FontAnalyzer } from './FontAnalyzer';
export { IssueDetector } from './IssueDetector';
export * from './types';

export default SafeHtmlRenderer;
