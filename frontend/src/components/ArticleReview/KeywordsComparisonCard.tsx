/**
 * KeywordsComparisonCard - Side-by-side comparison for SEO keywords
 *
 * Phase 8.3: Improved UX for parsing review
 * - Clear side-by-side keyword comparison
 * - Visual diff showing added/removed keywords
 * - Action buttons for applying changes
 */

import React, { useState, useMemo } from 'react';
import { Card } from '../ui';
import { Badge } from '../ui';
import { Button } from '../ui';
import {
  Tag,
  Sparkles,
  Check,
  Plus,
  Minus,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export type KeywordSource = 'extracted' | 'ai' | 'merged' | 'custom';

export interface KeywordsComparisonCardProps {
  /** Keywords extracted from document */
  extractedKeywords: string[];
  /** AI suggested keywords */
  aiSuggestedKeywords?: string[];
  /** Currently selected source */
  selectedSource: KeywordSource;
  /** Currently active keywords (final selection) */
  activeKeywords: string[];
  /** Callback when keywords change */
  onKeywordsChange: (source: KeywordSource, keywords: string[]) => void;
  /** Optimal keyword count range [min, max] */
  optimalCount?: [number, number];
  /** AI reasoning explanation */
  aiReasoning?: string;
  /** Whether to show expanded view by default */
  defaultExpanded?: boolean;
  /** Test ID for testing */
  testId?: string;
}

/**
 * KeywordsComparisonCard Component
 */
export const KeywordsComparisonCard: React.FC<KeywordsComparisonCardProps> = ({
  extractedKeywords,
  aiSuggestedKeywords,
  selectedSource,
  activeKeywords,
  onKeywordsChange,
  optimalCount = [5, 10],
  aiReasoning,
  defaultExpanded = true,
  testId,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const hasExtracted = extractedKeywords && extractedKeywords.length > 0;
  const hasAi = aiSuggestedKeywords && aiSuggestedKeywords.length > 0;

  // Calculate diff between extracted and AI keywords
  const keywordDiff = useMemo(() => {
    if (!hasExtracted || !hasAi) return { added: [], removed: [], common: [] };

    const extractedSet = new Set(extractedKeywords);
    const aiSet = new Set(aiSuggestedKeywords);

    const added = aiSuggestedKeywords.filter((kw) => !extractedSet.has(kw));
    const removed = extractedKeywords.filter((kw) => !aiSet.has(kw));
    const common = extractedKeywords.filter((kw) => aiSet.has(kw));

    return { added, removed, common };
  }, [extractedKeywords, aiSuggestedKeywords, hasExtracted, hasAi]);

  // Merge both keyword sets
  const mergedKeywords = useMemo(() => {
    const allKeywords = new Set([
      ...(extractedKeywords || []),
      ...(aiSuggestedKeywords || []),
    ]);
    return Array.from(allKeywords);
  }, [extractedKeywords, aiSuggestedKeywords]);

  // If no keywords at all, don't render
  if (!hasExtracted && !hasAi) {
    return null;
  }

  const handleSelectSource = (source: KeywordSource) => {
    let keywords: string[] = [];
    if (source === 'extracted') {
      keywords = extractedKeywords;
    } else if (source === 'ai') {
      keywords = aiSuggestedKeywords || [];
    } else if (source === 'custom') {
      // Custom defaults to AI suggested keywords
      keywords = aiSuggestedKeywords || [];
    } else {
      keywords = activeKeywords;
    }
    onKeywordsChange(source, keywords);
  };

  const getCountStatus = (count: number): 'good' | 'warning' | 'error' => {
    const [min, max] = optimalCount;
    if (count >= min && count <= max) return 'good';
    if (count >= min - 2 && count <= max + 2) return 'warning';
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
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-slate-50 to-slate-100 border-b cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-slate-600" />
          <h3 className="font-semibold text-slate-900">SEO 關鍵詞</h3>
          <Badge variant="secondary" className="text-xs">
            {activeKeywords.length} 個
          </Badge>
        </div>
        <button className="p-1 hover:bg-slate-200 rounded transition-colors">
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
              className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                selectedSource === 'extracted'
                  ? 'border-blue-500 bg-blue-50/50 ring-2 ring-blue-200'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
              onClick={() => handleSelectSource('extracted')}
            >
              {/* Label */}
              <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50/80">
                <div className="flex items-center gap-2">
                  <Tag className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-slate-700">文檔提取</span>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    statusColors[getCountStatus(extractedKeywords?.length || 0)]
                  }`}
                >
                  {extractedKeywords?.length || 0} 個
                </span>
              </div>

              {/* Keywords */}
              <div className="p-3 min-h-[80px]">
                {hasExtracted ? (
                  <div className="flex flex-wrap gap-1.5">
                    {extractedKeywords.map((kw, idx) => {
                      const isRemoved = hasAi && keywordDiff.removed.includes(kw);
                      return (
                        <span
                          key={idx}
                          className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${
                            isRemoved
                              ? 'bg-red-100 text-red-700 line-through opacity-60'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {isRemoved && <Minus className="w-3 h-3" />}
                          {kw}
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400 italic">未提取到關鍵詞</p>
                )}
              </div>

              {/* Selection indicator */}
              {selectedSource === 'extracted' && (
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center shadow-md">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>

            {/* Right: AI Suggested */}
            {hasAi && (
              <div
                className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                  selectedSource === 'ai'
                    ? 'border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-200'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
                onClick={() => handleSelectSource('ai')}
              >
                {/* Label */}
                <div className="flex items-center justify-between px-3 py-2 border-b bg-gradient-to-r from-emerald-50 to-teal-50">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-emerald-600" />
                    <span className="text-sm font-medium text-emerald-700">AI 優化建議</span>
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      statusColors[getCountStatus(aiSuggestedKeywords?.length || 0)]
                    }`}
                  >
                    {aiSuggestedKeywords?.length || 0} 個
                  </span>
                </div>

                {/* Keywords */}
                <div className="p-3 min-h-[80px]">
                  <div className="flex flex-wrap gap-1.5">
                    {aiSuggestedKeywords?.map((kw, idx) => {
                      const isAdded = keywordDiff.added.includes(kw);
                      return (
                        <span
                          key={idx}
                          className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${
                            isAdded
                              ? 'bg-green-100 text-green-700 font-medium'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {isAdded && <Plus className="w-3 h-3" />}
                          {kw}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* Selection indicator */}
                {selectedSource === 'ai' && (
                  <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center shadow-md">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Diff summary (if both sources exist) */}
          {hasExtracted && hasAi && (keywordDiff.added.length > 0 || keywordDiff.removed.length > 0) && (
            <div className="mb-4 p-3 bg-slate-50 rounded-lg border">
              <p className="text-xs font-medium text-slate-600 mb-2">變更摘要:</p>
              <div className="flex flex-wrap gap-2 text-xs">
                {keywordDiff.added.length > 0 && (
                  <span className="text-green-600">
                    +{keywordDiff.added.length} 新增
                  </span>
                )}
                {keywordDiff.removed.length > 0 && (
                  <span className="text-red-600">
                    -{keywordDiff.removed.length} 移除
                  </span>
                )}
                {keywordDiff.common.length > 0 && (
                  <span className="text-slate-500">
                    {keywordDiff.common.length} 保留
                  </span>
                )}
              </div>
            </div>
          )}

          {/* AI Reasoning */}
          {aiReasoning && (
            <div className="mb-4 p-3 bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg border border-amber-200">
              <div className="flex items-start gap-2">
                <span className="text-lg">💡</span>
                <div>
                  <p className="text-xs font-medium text-amber-800 mb-1">AI 优化理由</p>
                  <p className="text-sm text-amber-700">{aiReasoning}</p>
                </div>
              </div>
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
                      ? 'bg-blue-500 text-white'
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
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      AI優化
                    </button>
                    <button
                      onClick={() => handleSelectSource('custom')}
                      className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                        selectedSource === 'custom'
                          ? 'bg-purple-500 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      自定義
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

KeywordsComparisonCard.displayName = 'KeywordsComparisonCard';
