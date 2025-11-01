/**
 * Keyword Editor component for focus keyword and additional keywords.
 */

import { useState } from 'react';
import { Input, Badge } from '@/components/ui';
import { clsx } from 'clsx';

export interface KeywordEditorProps {
  focusKeyword: string;
  additionalKeywords: string[];
  onFocusKeywordChange: (keyword: string) => void;
  onAdditionalKeywordsChange: (keywords: string[]) => void;
  keywordDensity?: Record<string, number>;
  className?: string;
}

export const KeywordEditor: React.FC<KeywordEditorProps> = ({
  focusKeyword,
  additionalKeywords,
  onFocusKeywordChange,
  onAdditionalKeywordsChange,
  keywordDensity = {},
  className,
}) => {
  const [newKeyword, setNewKeyword] = useState('');

  const handleAddKeyword = () => {
    const trimmed = newKeyword.trim().toLowerCase();
    if (trimmed && !additionalKeywords.includes(trimmed) && trimmed !== focusKeyword.toLowerCase()) {
      onAdditionalKeywordsChange([...additionalKeywords, trimmed]);
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    onAdditionalKeywordsChange(additionalKeywords.filter((k) => k !== keyword));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  const getDensityBadge = (keyword: string) => {
    const density = keywordDensity[keyword.toLowerCase()] || 0;
    const variant = density >= 1 && density <= 2.5 ? 'success' : density > 2.5 ? 'warning' : 'secondary';
    return (
      <Badge variant={variant} size="sm">
        {density.toFixed(2)}%
      </Badge>
    );
  };

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Focus Keyword */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">
          焦点关键词 <span className="text-red-500">*</span>
        </label>
        <Input
          value={focusKeyword}
          onChange={(e) => onFocusKeywordChange(e.target.value)}
          placeholder="输入主要关键词"
          fullWidth
        />
        {focusKeyword && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-600">密度:</span>
            {getDensityBadge(focusKeyword)}
            <span className="text-gray-500 text-xs">
              (建议 1-2.5%)
            </span>
          </div>
        )}
      </div>

      {/* Additional Keywords */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">
          辅助关键词
        </label>

        <div className="flex gap-2">
          <Input
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入辅助关键词，按回车添加"
            className="flex-1"
          />
          <button
            type="button"
            onClick={handleAddKeyword}
            disabled={!newKeyword.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            添加
          </button>
        </div>

        {additionalKeywords.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {additionalKeywords.map((keyword) => (
              <div
                key={keyword}
                className="inline-flex items-center gap-2 bg-gray-100 rounded-lg px-3 py-1.5"
              >
                <span className="text-sm text-gray-700">{keyword}</span>
                {getDensityBadge(keyword)}
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(keyword)}
                  className="text-gray-500 hover:text-red-600 transition-colors"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
