/**
 * IssueMarker - 問題標記組件
 *
 * 在內容中標記問題位置，顯示 Tooltip
 *
 * @version 1.0
 * @date 2025-12-19
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  HtmlIssue,
  IssueMarkerProps,
  SEVERITY_COLORS,
  ISSUE_TYPE_ICONS,
} from './types';

export const IssueMarker: React.FC<IssueMarkerProps> = ({
  issue,
  children,
  onClick,
  onFix,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState<{
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'right' | 'center';
  }>({ vertical: 'top', horizontal: 'left' });
  const markerRef = useRef<HTMLSpanElement>(null);

  // 計算 Tooltip 位置（垂直和水平）
  useEffect(() => {
    if (showTooltip && markerRef.current) {
      const rect = markerRef.current.getBoundingClientRect();
      const spaceAbove = rect.top;
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceRight = window.innerWidth - rect.left;
      const tooltipWidth = 288; // w-72 = 18rem = 288px

      // 計算垂直位置
      const vertical = spaceAbove > 150 ? 'top' : 'bottom';

      // 計算水平位置 - 避免右邊被截斷
      let horizontal: 'left' | 'right' | 'center' = 'left';
      if (spaceRight < tooltipWidth + 16) {
        // 如果右邊空間不足，從右邊對齊
        horizontal = 'right';
      } else if (rect.left < tooltipWidth / 2) {
        // 如果左邊空間不足居中，從左邊對齊
        horizontal = 'left';
      }

      setTooltipPosition({ vertical, horizontal });
    }
  }, [showTooltip]);

  const severityColors = SEVERITY_COLORS[issue.severity];

  return (
    <span
      ref={markerRef}
      className={`
        issue-marker relative inline
        ${issue.type === 'font' ? 'font-issue-highlight' : ''}
        ${issue.type === 'nesting' ? 'nesting-issue' : ''}
        ${issue.type === 'empty' ? 'empty-tag-indicator' : ''}
      `}
      style={{
        backgroundColor: severityColors.hex,
        borderBottom: `2px solid`,
        borderColor: severityColors.hex.replace('100', '500'),
        cursor: 'pointer',
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={issue.message}
    >
      {children}

      {/* 內聯問題標記 */}
      <span
        className="inline-issue-marker ml-1 text-xs"
        aria-hidden="true"
      >
        {ISSUE_TYPE_ICONS[issue.type]}
      </span>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className={`
            font-tooltip absolute z-50 w-72 p-3 bg-white rounded-lg shadow-lg border
            ${tooltipPosition.vertical === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'}
            ${tooltipPosition.horizontal === 'right' ? 'right-0' : 'left-0'}
          `}
          role="tooltip"
        >
          {/* 箭頭 */}
          <div
            className={`
              absolute w-3 h-3 bg-white border transform rotate-45
              ${tooltipPosition.vertical === 'top'
                ? 'bottom-[-6px] border-t-0 border-l-0'
                : 'top-[-6px] border-b-0 border-r-0'
              }
              ${tooltipPosition.horizontal === 'right' ? 'right-4' : 'left-4'}
            `}
          />

          {/* 標題 */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{ISSUE_TYPE_ICONS[issue.type]}</span>
            <span className={`font-medium ${severityColors.text}`}>
              {issue.type === 'font' ? '字體異常' :
               issue.type === 'nesting' ? '嵌套錯誤' :
               issue.type === 'empty' ? '空標籤' :
               issue.type === 'gdocs' ? 'Google Docs 污染' :
               issue.type === 'deprecated' ? '廢棄標籤' :
               '可訪問性問題'}
            </span>
          </div>

          {/* 詳情 */}
          <p className="text-sm text-gray-700 mb-2">
            {issue.message}
          </p>

          {/* 字體詳情 */}
          {issue.type === 'font' && issue.details && (
            <div className="text-xs bg-gray-50 p-2 rounded mb-2">
              <div className="flex items-center gap-1">
                <span className="text-gray-500">🔤 字體:</span>
                <code className="text-red-600">
                  {(issue.details as { primaryFont?: string }).primaryFont}
                </code>
              </div>
            </div>
          )}

          {/* 建議 */}
          {issue.suggestion && (
            <p className="text-xs text-gray-600 mb-3">
              💡 {issue.suggestion}
            </p>
          )}

          {/* 操作按鈕 */}
          <div className="flex items-center gap-2">
            {issue.autoFixable && onFix && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFix();
                }}
                className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                data-testid="quick-fix-btn"
              >
                🔧 一鍵修復
              </button>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowTooltip(false);
              }}
              className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            >
              忽略
            </button>
          </div>
        </div>
      )}
    </span>
  );
};

/**
 * FontTooltip - 字體詳情 Tooltip（獨立使用）
 */
export const FontTooltip: React.FC<{
  fontFamily: string;
  primaryFont: string;
  category: string;
  message?: string;
  suggestion?: string;
  onFix?: () => void;
  onIgnore?: () => void;
}> = ({
  fontFamily,
  primaryFont,
  category,
  message,
  suggestion,
  onFix,
  onIgnore,
}) => {
  return (
    <div className="font-tooltip p-3 bg-white rounded-lg shadow-lg border w-72">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">🔤</span>
        <span className="font-medium text-amber-700">字體異常</span>
      </div>

      <div className="text-xs bg-gray-50 p-2 rounded mb-2">
        <div className="flex items-center gap-1 mb-1">
          <span className="text-gray-500">主字體:</span>
          <code className="text-red-600">{primaryFont}</code>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-500">完整聲明:</span>
          <code className="text-gray-700 text-xs break-all">{fontFamily}</code>
        </div>
      </div>

      {message && (
        <p className="text-sm text-gray-700 mb-2">{message}</p>
      )}

      {suggestion && (
        <p className="text-xs text-gray-600 mb-3">💡 {suggestion}</p>
      )}

      <div className="flex items-center gap-2">
        {onFix && (
          <button
            onClick={onFix}
            className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            🔧 一鍵修復
          </button>
        )}
        {onIgnore && (
          <button
            onClick={onIgnore}
            className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            忽略
          </button>
        )}
      </div>
    </div>
  );
};

export default IssueMarker;
