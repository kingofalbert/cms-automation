/**
 * TitleReviewSection - Title editing and optimization
 *
 * Phase 8.2: Parsing Review Panel
 * - Display extracted title
 * - Allow manual editing
 * - AI title suggestions
 * - Regenerate title button
 */

import React, { useState } from 'react';
import { Button } from '../ui';
import { Input } from '../ui/Input';
import { Sparkles, RotateCw } from 'lucide-react';

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
  worklistItemId,
  onTitleChange,
}) => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleOptimizeTitle = async () => {
    setIsOptimizing(true);
    try {
      // TODO: Call title optimization API
      // const response = await api.post(`/v1/worklist/${worklistItemId}/title-optimize`);
      // setSuggestions(response.suggestions || []);

      // Mock suggestions for now
      setTimeout(() => {
        setSuggestions([
          `${title} - 完整指南`,
          `如何${title}：专业技巧和策略`,
          `${title}：你需要知道的一切`,
        ]);
        setIsOptimizing(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to optimize title:', error);
      setIsOptimizing(false);
    }
  };

  const isModified = title !== originalTitle;

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
          <div className="text-xs text-gray-500 mb-1">原始标题</div>
          <div className="text-sm text-gray-700">{originalTitle}</div>
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

      {/* AI Optimization */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleOptimizeTitle}
          disabled={isOptimizing || !title}
          className="flex items-center gap-2"
        >
          {isOptimizing ? (
            <RotateCw className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          {isOptimizing ? 'AI 优化中...' : 'AI 优化标题'}
        </Button>
      </div>

      {/* AI Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">AI 建议标题</div>
          <div className="space-y-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => onTitleChange(suggestion)}
                className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm text-gray-800">{suggestion}</span>
                  <span className="text-xs text-blue-600 whitespace-nowrap">点击使用</span>
                </div>
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setSuggestions([])}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            清除建议
          </button>
        </div>
      )}

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
    </div>
  );
};

TitleReviewSection.displayName = 'TitleReviewSection';
