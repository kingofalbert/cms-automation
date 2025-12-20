/**
 * IssueSummary - 問題摘要欄組件
 *
 * 顯示檢測到的問題統計和分類
 *
 * @version 1.0
 * @date 2025-12-19
 */

import React, { useMemo } from 'react';
import {
  HtmlIssue,
  IssueType,
  IssueSummaryProps,
  SEVERITY_COLORS,
  ISSUE_TYPE_ICONS,
} from './types';

const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
  font: '字體問題',
  nesting: '嵌套錯誤',
  empty: '空標籤',
  deprecated: '廢棄標籤',
  accessibility: '可訪問性',
  gdocs: 'Google Docs',
};

export const IssueSummary: React.FC<IssueSummaryProps> = ({
  issues,
  onCategoryClick,
}) => {
  // 按類型統計
  const issuesByType = useMemo(() => {
    const counts: Partial<Record<IssueType, number>> = {};

    for (const issue of issues) {
      counts[issue.type] = (counts[issue.type] || 0) + 1;
    }

    return counts;
  }, [issues]);

  // 按嚴重程度統計
  const issuesBySeverity = useMemo(() => {
    return {
      error: issues.filter(i => i.severity === 'error').length,
      warning: issues.filter(i => i.severity === 'warning').length,
      info: issues.filter(i => i.severity === 'info').length,
    };
  }, [issues]);

  if (issues.length === 0) {
    return null;
  }

  return (
    <div className="issue-summary-bar mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <div className="flex items-center justify-between flex-wrap gap-2">
        {/* 總數 */}
        <div className="flex items-center gap-2">
          <span className="text-amber-600 font-medium">
            ⚠️ 發現 {issues.length} 個問題
          </span>

          {/* 嚴重程度分佈 */}
          <div className="flex items-center gap-1 text-sm">
            {issuesBySeverity.error > 0 && (
              <span className={`px-2 py-0.5 rounded ${SEVERITY_COLORS.error.bg} ${SEVERITY_COLORS.error.text}`}>
                {issuesBySeverity.error} 錯誤
              </span>
            )}
            {issuesBySeverity.warning > 0 && (
              <span className={`px-2 py-0.5 rounded ${SEVERITY_COLORS.warning.bg} ${SEVERITY_COLORS.warning.text}`}>
                {issuesBySeverity.warning} 警告
              </span>
            )}
            {issuesBySeverity.info > 0 && (
              <span className={`px-2 py-0.5 rounded ${SEVERITY_COLORS.info.bg} ${SEVERITY_COLORS.info.text}`}>
                {issuesBySeverity.info} 提示
              </span>
            )}
          </div>
        </div>

        {/* 分類快捷按鈕 */}
        <div className="flex items-center gap-2">
          {(Object.entries(issuesByType) as Array<[IssueType, number]>).map(([type, count]) => (
            <button
              key={type}
              onClick={() => onCategoryClick?.(type)}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors"
              data-issue-type={type}
            >
              <span>{ISSUE_TYPE_ICONS[type]}</span>
              <span>{ISSUE_TYPE_LABELS[type]}</span>
              <span className="ml-1 px-1.5 py-0.5 bg-gray-100 rounded-full">
                {count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 問題列表（可展開） */}
      <details className="mt-3">
        <summary className="text-sm text-amber-700 cursor-pointer hover:text-amber-900">
          查看詳細問題列表
        </summary>
        <ul
          className="mt-2 space-y-1 text-sm"
          role="list"
          aria-label="問題列表"
        >
          {issues.map(issue => (
            <li
              key={issue.id}
              className={`
                issue-list-item flex items-center gap-2 p-2 rounded cursor-pointer
                ${SEVERITY_COLORS[issue.severity].bg}
                hover:opacity-80 transition-opacity
              `}
              onClick={() => onCategoryClick?.(issue.type)}
              role="listitem"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onCategoryClick?.(issue.type);
                }
              }}
            >
              <span>{ISSUE_TYPE_ICONS[issue.type]}</span>
              <span className={SEVERITY_COLORS[issue.severity].text}>
                {issue.message}
              </span>
              {issue.autoFixable && (
                <span className="ml-auto text-xs text-gray-500">
                  🔧 可修復
                </span>
              )}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
};

export default IssueSummary;
