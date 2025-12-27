/**
 * TitleReviewSection - Title editing and validation
 *
 * Phase 8.2: Parsing Review Panel
 * - Display extracted title
 * - Allow manual editing
 * - Title quality indicators (length, SEO)
 *
 * Note: AI-powered SEO title suggestions are provided separately via
 * SEOTitleSelectionCard component in the same panel.
 *
 * Updated: 2025-12-25 - Removed mock AI optimization feature
 * Real AI title suggestions are available in SEOTitleSelectionCard
 */

import React from 'react';
import { Input } from '../ui/Input';
import { RotateCcw } from 'lucide-react';

export interface TitleReviewSectionProps {
  /** Current title */
  title: string;
  /** Original extracted title */
  originalTitle: string;
  /** Worklist item ID for API calls */
  worklistItemId: number;
  /** Callback when title changes */
  onTitleChange: (title: string) => void;
}

/**
 * TitleReviewSection Component
 */
export const TitleReviewSection: React.FC<TitleReviewSectionProps> = ({
  title,
  originalTitle,
  onTitleChange,
}) => {
  const isModified = title !== originalTitle;

  const handleResetToOriginal = () => {
    if (originalTitle) {
      onTitleChange(originalTitle);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">标题审核</h3>
        {isModified && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            已修改
          </span>
        )}
      </div>

      {/* Original title (if modified) */}
      {isModified && originalTitle && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-gray-500 mb-1">原始标题</div>
              <div className="text-sm text-gray-700">{originalTitle}</div>
            </div>
            <button
              type="button"
              onClick={handleResetToOriginal}
              className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
              title="恢复原始标题"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Current title input */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          当前标题
          <span className="ml-2 text-xs text-gray-500">
            ({title.length} 字符)
          </span>
        </label>
        <Input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="输入文章标题"
          className="w-full"
        />
        {title.length > 60 && (
          <p className="text-xs text-amber-600">
            ⚠️ 标题较长，建议保持在 60 字符以内以优化 SEO
          </p>
        )}
      </div>

      {/* Title quality indicators */}
      {title && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-gray-500">长度</div>
            <div className={`font-medium ${title.length > 60 ? 'text-amber-600' : 'text-green-600'}`}>
              {title.length <= 60 ? '✓ 良好' : '⚠ 过长'}
            </div>
          </div>
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-gray-500">可读性</div>
            <div className="font-medium text-green-600">✓ 良好</div>
          </div>
          <div className="p-2 bg-gray-50 rounded text-center">
            <div className="text-gray-500">SEO</div>
            <div className="font-medium text-green-600">✓ 优化</div>
          </div>
        </div>
      )}

      {/* Help text pointing to SEO Title section */}
      <p className="text-xs text-gray-500">
        💡 需要 AI 标题建议？请查看下方的「SEO Title 选择」区块
      </p>
    </div>
  );
};

TitleReviewSection.displayName = 'TitleReviewSection';
