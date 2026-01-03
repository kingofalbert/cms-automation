/**
 * DiffViewSection - Professional diff view using react-diff-viewer-continued
 *
 * Phase 8.4: Enhanced Proofreading Review Panel
 * - Shows original vs proofread content with full context
 * - Word-level highlighting for precise change detection
 * - Split and unified view modes
 * - Line numbers for easy reference
 * - Proper Chinese character support
 */

import React, { useState, useMemo } from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { FileText, Eye, Columns, AlignJustify, BarChart3 } from 'lucide-react';

export interface DiffStats {
  additions: number;
  deletions: number;
  total_changes: number;
  original_lines: number;
  suggested_lines: number;
}

export interface DiffViewSectionProps {
  /** Original content */
  originalContent: string;
  /** Proofread content */
  proofreadContent: string;
  /** Pre-calculated diff statistics from backend (optional) */
  diffStats?: DiffStats;
  /** Whether the diff was pre-generated (has word-level changes) */
  hasDiffData?: boolean;
}

// Custom styles for react-diff-viewer
const diffStyles = {
  variables: {
    light: {
      diffViewerBackground: '#ffffff',
      diffViewerColor: '#1f2937',
      addedBackground: '#dcfce7',
      addedColor: '#166534',
      removedBackground: '#fee2e2',
      removedColor: '#991b1b',
      wordAddedBackground: '#bbf7d0',
      wordRemovedBackground: '#fecaca',
      addedGutterBackground: '#dcfce7',
      removedGutterBackground: '#fee2e2',
      gutterBackground: '#f9fafb',
      gutterBackgroundDark: '#f3f4f6',
      highlightBackground: '#fef9c3',
      highlightGutterBackground: '#fef08a',
      codeFoldGutterBackground: '#e5e7eb',
      codeFoldBackground: '#f9fafb',
      emptyLineBackground: '#f9fafb',
      gutterColor: '#6b7280',
      addedGutterColor: '#166534',
      removedGutterColor: '#991b1b',
      codeFoldContentColor: '#4b5563',
      diffViewerTitleBackground: '#f3f4f6',
      diffViewerTitleColor: '#1f2937',
      diffViewerTitleBorderColor: '#e5e7eb',
    },
    dark: {
      diffViewerBackground: '#1f2937',
      diffViewerColor: '#f9fafb',
      addedBackground: '#064e3b',
      addedColor: '#a7f3d0',
      removedBackground: '#7f1d1d',
      removedColor: '#fecaca',
      wordAddedBackground: '#065f46',
      wordRemovedBackground: '#991b1b',
      addedGutterBackground: '#064e3b',
      removedGutterBackground: '#7f1d1d',
      gutterBackground: '#374151',
      gutterBackgroundDark: '#1f2937',
      highlightBackground: '#713f12',
      highlightGutterBackground: '#854d0e',
      codeFoldGutterBackground: '#374151',
      codeFoldBackground: '#1f2937',
      emptyLineBackground: '#1f2937',
      gutterColor: '#9ca3af',
      addedGutterColor: '#a7f3d0',
      removedGutterColor: '#fecaca',
      codeFoldContentColor: '#d1d5db',
      diffViewerTitleBackground: '#374151',
      diffViewerTitleColor: '#f9fafb',
      diffViewerTitleBorderColor: '#4b5563',
    },
  },
  line: {
    padding: '8px 4px',
    '&:hover': {
      background: '#f3f4f6',
    },
  },
  gutter: {
    minWidth: '30px',
    padding: '0 8px',
    fontSize: '11px',
  },
  content: {
    width: '100%',
    padding: '0 8px',
    fontSize: '13px',
    lineHeight: '1.6',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "Microsoft YaHei", sans-serif',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  codeFold: {
    padding: '8px',
    fontSize: '12px',
    color: '#6b7280',
    background: '#f9fafb',
    cursor: 'pointer',
    '&:hover': {
      background: '#f3f4f6',
    },
  },
  titleBlock: {
    padding: '8px 12px',
    fontSize: '12px',
    fontWeight: 600,
    borderBottom: '1px solid #e5e7eb',
  },
  contentText: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "Microsoft YaHei", sans-serif',
  },
  wordDiff: {
    padding: '2px 0',
  },
};

/**
 * DiffViewSection Component
 *
 * Provides a professional diff visualization for comparing original and proofread content.
 * Uses react-diff-viewer-continued for accurate diff rendering with word-level changes.
 */
export const DiffViewSection: React.FC<DiffViewSectionProps> = ({
  originalContent,
  proofreadContent,
  diffStats,
  hasDiffData = false,
}) => {
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');
  const [showLineNumbers, setShowLineNumbers] = useState(true);

  // Calculate whether there are changes
  const hasChanges = useMemo(() => {
    return originalContent !== proofreadContent;
  }, [originalContent, proofreadContent]);

  // Calculate stats if not provided
  const calculatedStats = useMemo(() => {
    if (diffStats) return diffStats;

    const originalLines = (originalContent || '').split('\n').length;
    const suggestedLines = (proofreadContent || '').split('\n').length;

    // Simple estimation (backend provides more accurate stats)
    return {
      original_lines: originalLines,
      suggested_lines: suggestedLines,
      additions: Math.max(0, suggestedLines - originalLines),
      deletions: Math.max(0, originalLines - suggestedLines),
      total_changes: hasChanges ? Math.abs(originalLines - suggestedLines) + 1 : 0,
    };
  }, [diffStats, originalContent, proofreadContent, hasChanges]);

  // Format stats for display
  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-TW');
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <FileText className="w-5 h-5" />
          對比視圖
        </h3>
        <div className="flex items-center gap-2">
          {/* Line numbers toggle */}
          <button
            type="button"
            onClick={() => setShowLineNumbers(!showLineNumbers)}
            className={`px-2 py-1 text-xs rounded border ${
              showLineNumbers
                ? 'bg-gray-100 border-gray-300 text-gray-700'
                : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50'
            }`}
            title={showLineNumbers ? '隱藏行號' : '顯示行號'}
          >
            #
          </button>
          {/* View mode buttons */}
          <div className="flex rounded-md overflow-hidden border border-gray-200">
            <button
              type="button"
              onClick={() => setViewMode('split')}
              className={`px-3 py-1 text-xs flex items-center gap-1 ${
                viewMode === 'split'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
              title="分欄視圖"
            >
              <Columns className="w-3 h-3" />
              分欄
            </button>
            <button
              type="button"
              onClick={() => setViewMode('unified')}
              className={`px-3 py-1 text-xs flex items-center gap-1 border-l border-gray-200 ${
                viewMode === 'unified'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
              title="統一視圖"
            >
              <AlignJustify className="w-3 h-3" />
              統一
            </button>
          </div>
        </div>
      </div>

      {/* No changes message */}
      {!hasChanges && (
        <div className="p-6 bg-green-50 border border-green-200 rounded-lg text-center">
          <Eye className="w-12 h-12 mx-auto text-green-600 mb-2" />
          <p className="text-sm font-medium text-green-800">內容未修改</p>
          <p className="text-xs text-green-600 mt-1">AI 校對後內容與原始內容完全一致</p>
        </div>
      )}

      {/* Diff viewer */}
      {hasChanges && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <ReactDiffViewer
            oldValue={originalContent || ''}
            newValue={proofreadContent || ''}
            splitView={viewMode === 'split'}
            showDiffOnly={false}
            useDarkTheme={false}
            leftTitle="原始內容"
            rightTitle="校對後內容"
            compareMethod={DiffMethod.WORDS}
            extraLinesSurroundingDiff={3}
            hideLineNumbers={!showLineNumbers}
            styles={diffStyles}
            codeFoldMessageRenderer={(totalFoldedLines) => (
              <span className="text-gray-500 text-xs">... 展開 {totalFoldedLines} 行相同內容 ...</span>
            )}
          />
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
        <div className="p-2 bg-gray-50 rounded-lg text-center">
          <div className="text-gray-500 mb-0.5">原始</div>
          <div className="font-medium text-gray-900">
            {formatNumber((originalContent || '').length)} 字元
          </div>
          <div className="text-gray-400 text-[10px]">
            {formatNumber(calculatedStats.original_lines)} 行
          </div>
        </div>
        <div className="p-2 bg-gray-50 rounded-lg text-center">
          <div className="text-gray-500 mb-0.5">校對後</div>
          <div className="font-medium text-gray-900">
            {formatNumber((proofreadContent || '').length)} 字元
          </div>
          <div className="text-gray-400 text-[10px]">
            {formatNumber(calculatedStats.suggested_lines)} 行
          </div>
        </div>
        <div className="p-2 bg-green-50 rounded-lg text-center">
          <div className="text-green-600 mb-0.5 flex items-center justify-center gap-1">
            <span className="font-mono">+</span> 新增
          </div>
          <div className="font-medium text-green-700">
            {formatNumber(calculatedStats.additions)}
          </div>
        </div>
        <div className="p-2 bg-red-50 rounded-lg text-center">
          <div className="text-red-600 mb-0.5 flex items-center justify-center gap-1">
            <span className="font-mono">-</span> 刪除
          </div>
          <div className="font-medium text-red-700">
            {formatNumber(calculatedStats.deletions)}
          </div>
        </div>
        <div className="p-2 bg-amber-50 rounded-lg text-center">
          <div className="text-amber-600 mb-0.5 flex items-center justify-center gap-1">
            <BarChart3 className="w-3 h-3" /> 狀態
          </div>
          <div className={`font-medium ${hasChanges ? 'text-amber-700' : 'text-green-700'}`}>
            {hasChanges ? '有修改' : '無修改'}
          </div>
        </div>
      </div>

      {/* Pre-generated diff indicator */}
      {hasDiffData && (
        <div className="text-xs text-gray-400 text-right">
          使用後端預生成的詞級差異數據
        </div>
      )}
    </div>
  );
};

DiffViewSection.displayName = 'DiffViewSection';
