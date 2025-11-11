/**
 * SEOReviewSection - SEO metadata review
 *
 * Phase 8.2: Parsing Review Panel
 * - Meta description editing
 * - Keywords management
 * - SEO score indicators
 */

import React from 'react';
import { Textarea } from '../ui/Textarea';
import { Badge } from '../ui';
import { Search, X } from 'lucide-react';
import { Input } from '../ui/Input';

export interface SEOReviewSectionProps {
  /** Meta description */
  metaDescription: string;
  /** SEO keywords */
  keywords: string[];
  /** Callback when meta description changes */
  onMetaDescriptionChange: (description: string) => void;
  /** Callback when keywords change */
  onKeywordsChange: (keywords: string[]) => void;
}

/**
 * SEOReviewSection Component
 */
export const SEOReviewSection: React.FC<SEOReviewSectionProps> = ({
  metaDescription,
  keywords,
  onMetaDescriptionChange,
  onKeywordsChange,
}) => {
  const [keywordInput, setKeywordInput] = React.useState('');

  const handleAddKeyword = () => {
    const trimmed = keywordInput.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      onKeywordsChange([...keywords, trimmed]);
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    onKeywordsChange(keywords.filter((k) => k !== keyword));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  const descriptionLength = metaDescription.length;
  const isDescriptionGood = descriptionLength >= 120 && descriptionLength <= 160;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Search className="w-5 h-5" />
        SEO 优化
      </h3>

      {/* Meta Description */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          元描述
          <span className="ml-2 text-xs text-gray-500">
            ({descriptionLength}/160 字符)
          </span>
        </label>
        <Textarea
          value={metaDescription}
          onChange={(e) => onMetaDescriptionChange(e.target.value)}
          placeholder="输入元描述，用于搜索引擎结果展示"
          rows={4}
          className="w-full"
        />
        {!isDescriptionGood && (
          <p className="text-xs text-amber-600">
            {descriptionLength < 120
              ? `⚠️ 建议至少 120 字符 (还需 ${120 - descriptionLength} 字符)`
              : '⚠️ 建议不超过 160 字符以避免截断'}
          </p>
        )}
        {isDescriptionGood && (
          <p className="text-xs text-green-600">✓ 长度合适</p>
        )}
      </div>

      {/* Keywords */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          关键词 ({keywords.length})
        </label>
        <div className="flex gap-2">
          <Input
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入关键词后按 Enter"
            className="flex-1"
          />
          <button
            type="button"
            onClick={handleAddKeyword}
            disabled={!keywordInput.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            添加
          </button>
        </div>

        {/* Keyword badges */}
        {keywords.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {keywords.map((keyword) => (
              <Badge
                key={keyword}
                variant="secondary"
                className="flex items-center gap-1"
              >
                {keyword}
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(keyword)}
                  className="ml-1 hover:text-red-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">暂无关键词</p>
        )}
      </div>

      {/* SEO Score */}
      <div className="p-3 bg-gray-50 rounded-lg">
        <div className="text-sm font-medium text-gray-700 mb-2">SEO 评分</div>
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span>元描述长度</span>
            <span className={isDescriptionGood ? 'text-green-600' : 'text-amber-600'}>
              {isDescriptionGood ? '✓ 良好' : '⚠ 需优化'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>关键词数量</span>
            <span className={keywords.length >= 3 && keywords.length <= 10 ? 'text-green-600' : 'text-amber-600'}>
              {keywords.length >= 3 && keywords.length <= 10 ? '✓ 良好' : '⚠ 需优化'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>整体评分</span>
            <span className="font-medium text-green-600">75/100</span>
          </div>
        </div>
      </div>
    </div>
  );
};

SEOReviewSection.displayName = 'SEOReviewSection';
