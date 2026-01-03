/**
 * TagsComparisonCard - Side-by-side comparison for WordPress internal tags
 *
 * Phase 8.3+: Added for parsing review (2025-12-06)
 * - Clear side-by-side tag comparison
 * - Visual indicators for tag type (primary, secondary, trending)
 * - Relevance scores for AI suggestions
 * - Different from Keywords: Tags are for WordPress internal navigation
 */

import React, { useState, useMemo } from 'react';
import { Card } from '../ui';
import { Badge } from '../ui';
import {
  Hash,
  Sparkles,
  Check,
  Plus,
  Minus,
  ChevronDown,
  ChevronUp,
  TrendingUp,
} from 'lucide-react';
import type { SuggestedTag } from '../../types/api';

export type TagSource = 'extracted' | 'ai' | 'custom';

export interface TagsComparisonCardProps {
  /** Tags extracted from document */
  extractedTags: string[];
  /** AI suggested tags with metadata */
  aiSuggestedTags?: SuggestedTag[];
  /** Currently selected source */
  selectedSource: TagSource;
  /** Currently active tags (final selection) */
  activeTags: string[];
  /** Callback when tags change */
  onTagsChange: (source: TagSource, tags: string[]) => void;
  /** Optimal tag count range [min, max] */
  optimalCount?: [number, number];
  /** AI strategy explanation */
  aiStrategy?: string;
  /** Whether to show expanded view by default */
  defaultExpanded?: boolean;
  /** Test ID for testing */
  testId?: string;
}

/**
 * Get badge color for tag type
 */
const getTagTypeColor = (type: 'primary' | 'secondary' | 'trending'): string => {
  switch (type) {
    case 'primary':
      return 'bg-blue-100 text-blue-700 border-blue-200';
    case 'secondary':
      return 'bg-slate-100 text-slate-600 border-slate-200';
    case 'trending':
      return 'bg-orange-100 text-orange-700 border-orange-200';
    default:
      return 'bg-slate-100 text-slate-600 border-slate-200';
  }
};

/**
 * TagsComparisonCard Component
 */
export const TagsComparisonCard: React.FC<TagsComparisonCardProps> = ({
  extractedTags,
  aiSuggestedTags,
  selectedSource,
  activeTags,
  onTagsChange,
  optimalCount = [3, 6],
  aiStrategy,
  defaultExpanded = true,
  testId,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const hasExtracted = extractedTags && extractedTags.length > 0;
  const hasAi = aiSuggestedTags && aiSuggestedTags.length > 0;

  // Extract tag names from AI suggestions
  const aiTagNames = useMemo(() => {
    return aiSuggestedTags?.map((t) => t.tag) || [];
  }, [aiSuggestedTags]);

  // Calculate diff between extracted and AI tags
  const tagDiff = useMemo(() => {
    if (!hasExtracted || !hasAi) return { added: [], removed: [], common: [] };

    const extractedSet = new Set(extractedTags);
    const aiSet = new Set(aiTagNames);

    const added = aiTagNames.filter((tag) => !extractedSet.has(tag));
    const removed = extractedTags.filter((tag) => !aiSet.has(tag));
    const common = extractedTags.filter((tag) => aiSet.has(tag));

    return { added, removed, common };
  }, [extractedTags, aiTagNames, hasExtracted, hasAi]);

  // Merge both tag sets
  const mergedTags = useMemo(() => {
    const allTags = new Set([...(extractedTags || []), ...aiTagNames]);
    return Array.from(allTags);
  }, [extractedTags, aiTagNames]);

  // If no tags at all, show placeholder
  if (!hasExtracted && !hasAi) {
    return (
      <Card className="overflow-hidden border-2" data-testid={testId}>
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-violet-50 to-purple-50 border-b">
          <div className="flex items-center gap-2">
            <Hash className="w-5 h-5 text-violet-600" />
            <h3 className="font-semibold text-slate-900">內部標籤 (Tags)</h3>
            <Badge variant="secondary" className="text-xs">0 個</Badge>
          </div>
        </div>
        <div className="p-4 text-center text-slate-500">
          <p className="text-sm">暫無標籤數據</p>
          <p className="text-xs mt-1">標籤將在 AI 優化後生成</p>
        </div>
      </Card>
    );
  }

  const handleSelectSource = (source: TagSource) => {
    let tags: string[] = [];
    if (source === 'extracted') {
      tags = extractedTags;
    } else if (source === 'ai') {
      tags = aiTagNames;
    } else if (source === 'custom') {
      // Custom defaults to AI suggested tags
      tags = aiTagNames;
    } else {
      tags = activeTags;
    }
    onTagsChange(source, tags);
  };

  const getCountStatus = (count: number): 'good' | 'warning' | 'error' => {
    const [min, max] = optimalCount;
    if (count >= min && count <= max) return 'good';
    if (count >= min - 1 && count <= max + 2) return 'warning';
    return 'error';
  };

  const statusColors = {
    good: 'text-green-600 bg-green-50',
    warning: 'text-amber-600 bg-amber-50',
    error: 'text-red-600 bg-red-50',
  };

  return (
    <Card
      className="overflow-hidden border-2 transition-all duration-200"
      data-testid={testId}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-violet-50 to-purple-50 border-b cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Hash className="w-5 h-5 text-violet-600" />
          <h3 className="font-semibold text-slate-900">內部標籤 (Tags)</h3>
          <Badge variant="secondary" className="text-xs">
            {activeTags.length} 個
          </Badge>
          <span className="text-xs text-slate-500 ml-2">
            WordPress 內部導航分類
          </span>
        </div>
        <button className="p-1 hover:bg-violet-200 rounded transition-colors">
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-slate-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-500" />
          )}
        </button>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-4">
          {/* Side-by-side comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Left: Document Extracted */}
            <div
              className={`relative rounded-lg border-2 transition-all ${
                selectedSource === 'extracted'
                  ? 'border-violet-500 bg-violet-50/50 ring-2 ring-violet-200'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              {/* Label */}
              <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50/80">
                <div className="flex items-center gap-2">
                  <Hash className="w-4 h-4 text-violet-600" />
                  <span className="text-sm font-medium text-slate-700">文檔提取</span>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    statusColors[getCountStatus(extractedTags?.length || 0)]
                  }`}
                >
                  {extractedTags?.length || 0} 個
                </span>
              </div>

              {/* Tags */}
              <div
                className="p-3 min-h-[80px] cursor-pointer"
                onClick={() => handleSelectSource('extracted')}
              >
                {hasExtracted ? (
                  <div className="flex flex-wrap gap-1.5">
                    {extractedTags.map((tag, idx) => {
                      const isRemoved = hasAi && tagDiff.removed.includes(tag);
                      return (
                        <span
                          key={idx}
                          className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full border ${
                            isRemoved
                              ? 'bg-red-50 text-red-600 border-red-200 line-through opacity-60'
                              : 'bg-violet-100 text-violet-700 border-violet-200'
                          }`}
                        >
                          {isRemoved && <Minus className="w-3 h-3" />}
                          #{tag}
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400 italic">文檔中未提取到標籤</p>
                )}
              </div>

              {/* Selection indicator */}
              {selectedSource === 'extracted' && (
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-violet-500 rounded-full flex items-center justify-center shadow-md">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>

            {/* Right: AI Suggested */}
            {hasAi && (
              <div
                className={`relative rounded-lg border-2 transition-all ${
                  selectedSource === 'ai'
                    ? 'border-purple-500 bg-purple-50/50 ring-2 ring-purple-200'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                {/* Label */}
                <div className="flex items-center justify-between px-3 py-2 border-b bg-gradient-to-r from-purple-50 to-fuchsia-50">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-700">AI 推薦</span>
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      statusColors[getCountStatus(aiSuggestedTags?.length || 0)]
                    }`}
                  >
                    {aiSuggestedTags?.length || 0} 個
                  </span>
                </div>

                {/* Tags with metadata */}
                <div
                  className="p-3 min-h-[80px] cursor-pointer"
                  onClick={() => handleSelectSource('ai')}
                >
                  <div className="flex flex-wrap gap-1.5">
                    {aiSuggestedTags?.map((tagData, idx) => {
                      const isAdded = tagDiff.added.includes(tagData.tag);
                      return (
                        <span
                          key={idx}
                          className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full border ${
                            isAdded
                              ? 'bg-green-50 text-green-700 border-green-200 font-medium'
                              : getTagTypeColor(tagData.type)
                          }`}
                          title={`相關度: ${Math.round(tagData.relevance * 100)}%${
                            tagData.existing ? ' | 已存在' : ' | 新標籤'
                          }${tagData.article_count ? ` | ${tagData.article_count}篇文章` : ''}`}
                        >
                          {isAdded && <Plus className="w-3 h-3" />}
                          {tagData.type === 'trending' && <TrendingUp className="w-3 h-3" />}
                          #{tagData.tag}
                          <span className="text-[10px] opacity-60 ml-0.5">
                            {Math.round(tagData.relevance * 100)}%
                          </span>
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* Selection indicator */}
                {selectedSource === 'ai' && (
                  <div className="absolute -top-1 -right-1 w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center shadow-md">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Diff summary (if both sources exist) */}
          {hasExtracted && hasAi && (tagDiff.added.length > 0 || tagDiff.removed.length > 0) && (
            <div className="mb-4 p-3 bg-slate-50 rounded-lg border">
              <p className="text-xs font-medium text-slate-600 mb-2">變更摘要:</p>
              <div className="flex flex-wrap gap-2 text-xs">
                {tagDiff.added.length > 0 && (
                  <span className="text-green-600">
                    +{tagDiff.added.length} 新增
                  </span>
                )}
                {tagDiff.removed.length > 0 && (
                  <span className="text-red-600">
                    -{tagDiff.removed.length} 移除
                  </span>
                )}
                {tagDiff.common.length > 0 && (
                  <span className="text-slate-500">
                    {tagDiff.common.length} 保留
                  </span>
                )}
              </div>
            </div>
          )}

          {/* AI Strategy */}
          {aiStrategy && (
            <div className="mb-4 p-3 bg-gradient-to-r from-purple-50 to-fuchsia-50 rounded-lg border border-purple-200">
              <div className="flex items-start gap-2">
                <span className="text-lg">🎯</span>
                <div>
                  <p className="text-xs font-medium text-purple-800 mb-1">AI 標籤策略</p>
                  <p className="text-sm text-purple-700">{aiStrategy}</p>
                </div>
              </div>
            </div>
          )}

          {/* Tag type legend */}
          {hasAi && (
            <div className="mb-4 p-2 bg-slate-50 rounded border text-xs">
              <span className="text-slate-500 mr-3">標籤類型:</span>
              <span className="inline-flex items-center gap-1 mr-3">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                主要
              </span>
              <span className="inline-flex items-center gap-1 mr-3">
                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                次要
              </span>
              <span className="inline-flex items-center gap-1">
                <TrendingUp className="w-3 h-3 text-orange-500" />
                熱門
              </span>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-3 border-t">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">當前選擇:</span>
              <div className="flex gap-1">
                <button
                  onClick={() => handleSelectSource('extracted')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                    selectedSource === 'extracted'
                      ? 'bg-violet-500 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  文檔提取
                </button>
                {hasAi && (
                  <>
                    <button
                      onClick={() => handleSelectSource('ai')}
                      className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                        selectedSource === 'ai'
                          ? 'bg-purple-500 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      AI推薦
                    </button>
                    <button
                      onClick={() => handleSelectSource('custom')}
                      className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                        selectedSource === 'custom'
                          ? 'bg-fuchsia-500 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      自定義
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="text-xs text-slate-400">
              建議 {optimalCount[0]}-{optimalCount[1]} 個標籤
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

TagsComparisonCard.displayName = 'TagsComparisonCard';
