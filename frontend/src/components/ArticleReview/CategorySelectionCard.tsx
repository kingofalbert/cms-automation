/**
 * CategorySelectionCard - Primary and secondary category selection with AI recommendation
 *
 * Phase 11: Category Selection Enhancement
 * - AI-powered primary category recommendation with confidence score
 * - Manual override option for primary category
 * - Multi-select checkboxes for secondary categories
 * - Visual feedback for AI recommendation acceptance
 *
 * UX Design:
 * ┌─────────────────────────────────────────────────────────────┐
 * │ ⭐ 主分類 (Primary Category)                        * 必填  │
 * ├─────────────────────────────────────────────────────────────┤
 * │  🤖 AI 推荐                                                 │
 * │  ┌─────────────────────────────────────────────────────┐   │
 * │  │ ✨ 健康新聞                              [98% 匹配] │   │
 * │  │    理由：文章涉及萊姆病預防與治療，屬於健康新聞類    │   │
 * │  └─────────────────────────────────────────────────────┘   │
 * │                                                             │
 * │  ○ 接受 AI 推荐     ● 手动选择                             │
 * └─────────────────────────────────────────────────────────────┘
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card } from '../ui';
import {
  Star,
  Sparkles,
  Check,
  ChevronDown,
  ChevronUp,
  FolderTree,
  Folders,
} from 'lucide-react';

// WordPress category options (matching backend)
const CATEGORY_OPTIONS = [
  { id: 'food-therapy', name: '食療養生', slug: 'food-therapy' },
  { id: 'tcm', name: '中醫寶典', slug: 'tcm' },
  { id: 'mindfulness', name: '心靈正念', slug: 'mindfulness' },
  { id: 'doctor-column', name: '醫師專欄', slug: 'doctor-column' },
  { id: 'health-news', name: '健康新聞', slug: 'health-news' },
  { id: 'healthy-living', name: '健康生活', slug: 'healthy-living' },
  { id: 'medical-tech', name: '醫療科技', slug: 'medical-tech' },
  { id: 'featured', name: '精選內容', slug: 'featured' },
  { id: 'doctor-stories', name: '診室外的醫話', slug: 'doctor-stories' },
  { id: 'daily-care', name: '每日呵護', slug: 'daily-care' },
];

export interface AICategoryRecommendation {
  category: string;
  confidence: number; // 0-1
  reasoning: string;
}

export interface CategorySelectionCardProps {
  /** AI recommended primary category */
  aiRecommendation?: AICategoryRecommendation;
  /** Currently selected primary category */
  primaryCategory: string | null;
  /** Currently selected secondary categories */
  secondaryCategories: string[];
  /** Callback when primary category changes */
  onPrimaryCategoryChange: (category: string | null) => void;
  /** Callback when secondary categories change */
  onSecondaryCategoriesChange: (categories: string[]) => void;
  /** Whether AI recommendation is loading */
  isLoading?: boolean;
  /** Test ID for testing */
  testId?: string;
}

/**
 * CategorySelectionCard Component
 */
export const CategorySelectionCard: React.FC<CategorySelectionCardProps> = ({
  aiRecommendation,
  primaryCategory,
  secondaryCategories,
  onPrimaryCategoryChange,
  onSecondaryCategoriesChange,
  isLoading = false,
  testId,
}) => {
  // Track if user accepted AI recommendation
  const [useAiRecommendation, setUseAiRecommendation] = useState<boolean>(
    aiRecommendation != null && primaryCategory === aiRecommendation.category
  );

  // Track expanded state for secondary categories
  const [isSecondaryExpanded, setIsSecondaryExpanded] = useState(true);

  // Update AI acceptance state when recommendation changes
  useEffect(() => {
    if (aiRecommendation && !primaryCategory) {
      // Auto-accept AI recommendation if no category selected
      setUseAiRecommendation(true);
      onPrimaryCategoryChange(aiRecommendation.category);
    }
  }, [aiRecommendation, primaryCategory, onPrimaryCategoryChange]);

  // Get category display name
  const getCategoryName = (slug: string): string => {
    const category = CATEGORY_OPTIONS.find((c) => c.name === slug || c.slug === slug);
    return category?.name || slug;
  };

  // Handle AI recommendation acceptance
  const handleAcceptAiRecommendation = () => {
    if (aiRecommendation) {
      setUseAiRecommendation(true);
      onPrimaryCategoryChange(aiRecommendation.category);
    }
  };

  // Handle manual selection
  const handleManualSelection = (category: string) => {
    setUseAiRecommendation(false);
    onPrimaryCategoryChange(category);
  };

  // Handle secondary category toggle
  const handleSecondaryToggle = (category: string) => {
    // Cannot select primary category as secondary
    if (category === primaryCategory) return;

    const newSecondaries = secondaryCategories.includes(category)
      ? secondaryCategories.filter((c) => c !== category)
      : [...secondaryCategories, category];
    onSecondaryCategoriesChange(newSecondaries);
  };

  // Get available secondary categories (exclude primary)
  const availableSecondaryCategories = useMemo(() => {
    return CATEGORY_OPTIONS.filter((c) => c.name !== primaryCategory);
  }, [primaryCategory]);

  // Confidence color based on score
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 0.7) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (confidence >= 0.5) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-slate-600 bg-slate-50 border-slate-200';
  };

  return (
    <Card className="overflow-hidden border-2" data-testid={testId}>
      {/* Primary Category Section */}
      <div className="border-b">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-amber-50 to-orange-50">
          <div className="flex items-center gap-2">
            <Star className="w-5 h-5 text-amber-600" />
            <h3 className="font-semibold text-slate-900">主分類 (Primary Category)</h3>
            <span className="text-red-500 text-sm">*</span>
          </div>
        </div>

        {/* AI Recommendation */}
        <div className="p-4">
          <p className="text-xs text-slate-500 mb-3">決定文章URL結構和麵包屑導航</p>

          {isLoading ? (
            <div className="flex items-center gap-2 p-4 bg-slate-50 rounded-lg border border-slate-200 animate-pulse">
              <div className="w-5 h-5 bg-slate-200 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-slate-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-slate-200 rounded w-2/3"></div>
              </div>
            </div>
          ) : aiRecommendation ? (
            <div className="space-y-3">
              {/* AI Recommendation Card */}
              <div
                className={`relative p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  useAiRecommendation
                    ? 'border-purple-500 bg-purple-50/50 ring-2 ring-purple-200'
                    : 'border-slate-200 bg-white hover:border-purple-300'
                }`}
                onClick={handleAcceptAiRecommendation}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-purple-700">AI 推薦</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border ${getConfidenceColor(
                          aiRecommendation.confidence
                        )}`}
                      >
                        {Math.round(aiRecommendation.confidence * 100)}% 匹配
                      </span>
                    </div>
                    <p className="text-lg font-semibold text-slate-900 mb-1">
                      {getCategoryName(aiRecommendation.category)}
                    </p>
                    <p className="text-xs text-slate-600">{aiRecommendation.reasoning}</p>
                  </div>
                </div>

                {/* Selection indicator */}
                {useAiRecommendation && (
                  <div className="absolute -top-1 -right-1 w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center shadow-md">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>

              {/* Selection Mode Toggle */}
              <div className="flex items-center gap-4 text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="categoryMode"
                    checked={useAiRecommendation}
                    onChange={handleAcceptAiRecommendation}
                    className="w-4 h-4 text-purple-600"
                  />
                  <span className={useAiRecommendation ? 'text-purple-700 font-medium' : 'text-slate-600'}>
                    接受 AI 推薦
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="categoryMode"
                    checked={!useAiRecommendation}
                    onChange={() => setUseAiRecommendation(false)}
                    className="w-4 h-4 text-slate-600"
                  />
                  <span className={!useAiRecommendation ? 'text-slate-900 font-medium' : 'text-slate-600'}>
                    手動選擇
                  </span>
                </label>
              </div>
            </div>
          ) : null}

          {/* Manual Selection Dropdown */}
          {(!aiRecommendation || !useAiRecommendation) && (
            <div className="mt-3">
              <label className="block text-xs text-slate-500 mb-1">
                {aiRecommendation ? '手動選擇分類：' : '請選擇主分類：'}
              </label>
              <select
                value={primaryCategory || ''}
                onChange={(e) => handleManualSelection(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                <option value="">-- 請選擇主分類 --</option>
                {CATEGORY_OPTIONS.map((category) => (
                  <option key={category.id} value={category.name}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Secondary Categories Section */}
      <div>
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b cursor-pointer"
          onClick={() => setIsSecondaryExpanded(!isSecondaryExpanded)}
        >
          <div className="flex items-center gap-2">
            <Folders className="w-5 h-5 text-slate-600" />
            <h3 className="font-medium text-slate-700">副分類 (Secondary Categories)</h3>
            <span className="text-xs text-slate-400">可選</span>
          </div>
          <button className="p-1 hover:bg-slate-200 rounded transition-colors">
            {isSecondaryExpanded ? (
              <ChevronUp className="w-5 h-5 text-slate-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-500" />
            )}
          </button>
        </div>

        {/* Secondary Categories Checkboxes */}
        {isSecondaryExpanded && (
          <div className="p-4">
            <p className="text-xs text-slate-500 mb-3">
              讓文章同時出現在其他分類列表頁面（可多選，最多3個）
            </p>
            <div className="grid grid-cols-2 gap-2">
              {availableSecondaryCategories.map((category) => {
                const isSelected = secondaryCategories.includes(category.name);
                const isDisabled =
                  !isSelected && secondaryCategories.length >= 3;
                return (
                  <label
                    key={category.id}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : isDisabled
                        ? 'border-slate-200 bg-slate-50 text-slate-400 cursor-not-allowed'
                        : 'border-slate-200 bg-white hover:border-blue-300 text-slate-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleSecondaryToggle(category.name)}
                      disabled={isDisabled}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <span className="text-sm">{category.name}</span>
                  </label>
                );
              })}
            </div>
            {secondaryCategories.length > 0 && (
              <p className="mt-2 text-xs text-slate-500">
                已選 {secondaryCategories.length}/3 個副分類
              </p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

CategorySelectionCard.displayName = 'CategorySelectionCard';
