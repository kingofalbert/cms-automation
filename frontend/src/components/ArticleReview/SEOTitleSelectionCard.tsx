/**
 * SEOTitleSelectionCard - SEO Title 選擇卡片元件
 *
 * Phase 9.1: Improved UX - Side-by-side comparison layout
 * - Left: Document extracted SEO Title (if available)
 * - Right: AI suggested SEO Title (always provide at least one)
 * - Bottom: Selection buttons and custom input option
 * - Same UI pattern as ContentComparisonCard and KeywordsComparisonCard
 */

import React, { useState } from 'react';
import { Card } from '../ui';
import { Badge } from '../ui/badge';
import {
  FileText,
  Sparkles,
  Check,
  AlertCircle,
  Copy,
  ChevronDown,
  ChevronUp,
  Edit3,
} from 'lucide-react';
import { Button } from '../ui';
import type { SEOTitleSuggestionsData, SEOTitleVariant, SelectSEOTitleRequest, SelectSEOTitleResponse } from '../../types/api';

export type SEOTitleSource = 'extracted' | 'ai' | 'custom';

export interface SEOTitleSelectionCardProps {
  /** 文章 ID */
  articleId: number;
  /** 當前 SEO Title */
  currentSeoTitle?: string | null;
  /** SEO Title 來源 */
  seoTitleSource?: string | null;
  /** AI 生成的 SEO Title 建議 */
  suggestions?: SEOTitleSuggestionsData | null;
  /** 文章標題 (用於生成 AI 建議) */
  articleTitle?: string;
  /** 是否顯示載入狀態 */
  isLoading?: boolean;
  /** 選擇成功回調 */
  onSelectionSuccess?: (response: SelectSEOTitleResponse) => void;
  /** 錯誤回調 */
  onError?: (error: Error) => void;
  /** 選擇變更回調 (不保存到後端，只更新本地狀態) */
  onSourceChange?: (source: SEOTitleSource, content: string) => void;
  /** 默認展開 */
  defaultExpanded?: boolean;
}

/**
 * Get length status based on optimal range (25-35 characters for SEO Title)
 */
const getLengthStatus = (length: number): 'good' | 'warning' | 'error' => {
  if (length >= 20 && length <= 40) return 'good';
  if (length > 0 && length < 50) return 'warning';
  return length === 0 ? 'error' : 'warning';
};

/**
 * Status indicator component
 */
const StatusIndicator: React.FC<{
  status: 'good' | 'warning' | 'error';
  label: string;
}> = ({ status, label }) => {
  const config = {
    good: { icon: Check, color: 'text-green-600', bg: 'bg-green-50' },
    warning: { icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-50' },
    error: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50' },
  };
  const { icon: Icon, color, bg } = config[status];

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${color} ${bg}`}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
};

/**
 * SEOTitleSelectionCard Component
 */
export const SEOTitleSelectionCard: React.FC<SEOTitleSelectionCardProps> = ({
  articleId,
  currentSeoTitle,
  seoTitleSource,
  suggestions,
  articleTitle,
  isLoading = false,
  onSelectionSuccess,
  onError,
  onSourceChange,
  defaultExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [selectedSource, setSelectedSource] = useState<SEOTitleSource>(
    seoTitleSource === 'extracted' ? 'extracted' :
    seoTitleSource === 'ai_generated' ? 'ai' :
    seoTitleSource === 'user_input' ? 'custom' : 'extracted'
  );
  const [customTitle, setCustomTitle] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Get extracted SEO Title (from document parsing)
  const extractedSeoTitle = suggestions?.original_seo_title || '';

  // Get first AI suggested variant (the best one)
  // If no AI suggestion available, use article title as fallback
  const aiSuggestedTitle = suggestions?.variants?.[0]?.seo_title ||
    (articleTitle && articleTitle.length <= 40 ? articleTitle : '');
  const aiReasoning = suggestions?.variants?.[0]?.reasoning ||
    (articleTitle && !suggestions?.variants?.[0] ? '基於文章標題生成的 SEO Title 建議' : '');
  const aiKeywords = suggestions?.variants?.[0]?.keywords_focus || [];

  // Calculate lengths
  const extractedLength = extractedSeoTitle.length;
  const aiLength = aiSuggestedTitle.length;
  const hasExtracted = extractedLength > 0;
  const hasAi = aiLength > 0;

  // Handle copy to clipboard
  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  // Handle source selection
  const handleSelectSource = (source: SEOTitleSource) => {
    setSelectedSource(source);
    let content = '';
    if (source === 'extracted') {
      content = extractedSeoTitle;
    } else if (source === 'ai') {
      content = aiSuggestedTitle;
    } else {
      content = customTitle || extractedSeoTitle || aiSuggestedTitle || '';
    }
    onSourceChange?.(source, content);
  };

  // Handle save custom
  const handleSaveCustom = () => {
    setCustomTitle(editValue);
    setSelectedSource('custom');
    onSourceChange?.('custom', editValue);
    setIsEditing(false);
  };

  // Handle submit to API
  const handleSubmit = async () => {
    setIsSaving(true);
    try {
      let requestBody: SelectSEOTitleRequest;

      if (selectedSource === 'custom') {
        requestBody = { custom_seo_title: customTitle };
      } else if (selectedSource === 'ai' && suggestions?.variants?.[0]?.id) {
        requestBody = { variant_id: suggestions.variants[0].id };
      } else {
        // Use extracted or fallback
        requestBody = { custom_seo_title: extractedSeoTitle || aiSuggestedTitle };
      }

      const response = await fetch(`/api/v1/optimization/articles/${articleId}/select-seo-title`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to select SEO Title');
      }

      const result: SelectSEOTitleResponse = await response.json();
      onSelectionSuccess?.(result);
    } catch (error) {
      console.error('Failed to select SEO Title:', error);
      onError?.(error as Error);
    } finally {
      setIsSaving(false);
    }
  };

  // Get current selection display
  const getCurrentSelection = (): string => {
    if (selectedSource === 'custom') return customTitle;
    if (selectedSource === 'ai') return aiSuggestedTitle;
    return extractedSeoTitle;
  };

  if (isLoading) {
    return (
      <Card className="overflow-hidden border-2">
        <div className="p-4">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-32 bg-gray-100 rounded"></div>
              <div className="h-32 bg-gray-100 rounded"></div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="overflow-hidden border-2 transition-all duration-200"
      data-testid="seo-title-selection-card"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-slate-50 to-slate-100 border-b cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-slate-600" />
          <h3 className="font-semibold text-slate-900">SEO Title 選擇</h3>
          {currentSeoTitle && (
            <Badge variant="success" className="text-xs">
              已設置
            </Badge>
          )}
          {!currentSeoTitle && !hasExtracted && !hasAi && (
            <Badge variant="warning" className="text-xs">
              需要設置
            </Badge>
          )}
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
          {/* Current status summary */}
          {currentSeoTitle && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">當前 SEO Title</span>
                <span className="text-xs text-green-600">({currentSeoTitle.length} 字)</span>
              </div>
              <p className="text-sm text-green-700 pl-6">{currentSeoTitle}</p>
            </div>
          )}

          {/* Side-by-side comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {/* Left: Document Extracted */}
            <div
              className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                selectedSource === 'extracted'
                  ? 'border-blue-500 bg-blue-50/50 ring-2 ring-blue-200'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              } ${!hasExtracted ? 'opacity-60 cursor-not-allowed' : ''}`}
              onClick={() => hasExtracted && handleSelectSource('extracted')}
            >
              {/* Label */}
              <div className="flex items-center justify-between px-3 py-2 border-b bg-slate-50/80">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-slate-700">文檔提取</span>
                  {hasExtracted && (
                    <span className="text-xs text-slate-500">({extractedLength} 字)</span>
                  )}
                </div>
                {hasExtracted && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(extractedSeoTitle);
                    }}
                    className="p-1 hover:bg-slate-200 rounded"
                    title="复制"
                  >
                    <Copy className="w-3.5 h-3.5 text-slate-400" />
                  </button>
                )}
              </div>

              {/* Content */}
              <div className="p-3 min-h-[80px]">
                {hasExtracted ? (
                  <p className="text-sm text-slate-700 font-medium">{extractedSeoTitle}</p>
                ) : (
                  <div className="flex items-center gap-2 text-slate-400">
                    <AlertCircle className="w-4 h-4" />
                    <p className="text-sm italic">原文未標記 SEO Title</p>
                  </div>
                )}
              </div>

              {/* Quality indicators */}
              {hasExtracted && (
                <div className="px-3 py-2 border-t bg-slate-50/50 flex flex-wrap gap-1.5">
                  <StatusIndicator
                    status={getLengthStatus(extractedLength)}
                    label={`${extractedLength}/25-35字`}
                  />
                </div>
              )}

              {/* Selection indicator */}
              {selectedSource === 'extracted' && hasExtracted && (
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center shadow-md">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>

            {/* Right: AI Suggested */}
            <div
              className={`relative rounded-lg border-2 transition-all cursor-pointer ${
                selectedSource === 'ai'
                  ? 'border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-200'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              } ${!hasAi ? 'opacity-60 cursor-not-allowed' : ''}`}
              onClick={() => hasAi && handleSelectSource('ai')}
            >
              {/* Label */}
              <div className="flex items-center justify-between px-3 py-2 border-b bg-gradient-to-r from-emerald-50 to-teal-50">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-medium text-emerald-700">AI 優化建議</span>
                  {hasAi && (
                    <span className="text-xs text-emerald-600">({aiLength} 字)</span>
                  )}
                </div>
                {hasAi && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(aiSuggestedTitle);
                    }}
                    className="p-1 hover:bg-emerald-100 rounded"
                    title="复制"
                  >
                    <Copy className="w-3.5 h-3.5 text-emerald-500" />
                  </button>
                )}
              </div>

              {/* Content */}
              <div className="p-3 min-h-[80px]">
                {hasAi ? (
                  <div className="space-y-2">
                    <p className="text-sm text-slate-700 font-medium">{aiSuggestedTitle}</p>
                    {aiReasoning && (
                      <p className="text-xs text-emerald-600 italic">{aiReasoning}</p>
                    )}
                    {aiKeywords.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {aiKeywords.slice(0, 3).map((kw, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs bg-emerald-50">
                            {kw}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-slate-400">
                    <AlertCircle className="w-4 h-4" />
                    <p className="text-sm italic">無 AI 建議</p>
                  </div>
                )}
              </div>

              {/* Quality indicators */}
              {hasAi && (
                <div className="px-3 py-2 border-t bg-emerald-50/50 flex flex-wrap gap-1.5">
                  <StatusIndicator
                    status={getLengthStatus(aiLength)}
                    label={`${aiLength}/25-35字`}
                  />
                </div>
              )}

              {/* Selection indicator */}
              {selectedSource === 'ai' && hasAi && (
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center shadow-md">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          </div>

          {/* No content warning */}
          {!hasExtracted && !hasAi && (
            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-amber-800">需要設置 SEO Title</p>
                  <p className="text-xs text-amber-700 mt-1">
                    原文未標記 SEO Title，也沒有 AI 建議。請手動輸入 SEO Title（建議 25-35 字）。
                  </p>
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
                  disabled={!hasExtracted}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                    selectedSource === 'extracted'
                      ? 'bg-blue-500 text-white'
                      : hasExtracted
                      ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      : 'bg-slate-50 text-slate-300 cursor-not-allowed'
                  }`}
                >
                  文檔提取
                </button>
                <button
                  onClick={() => handleSelectSource('ai')}
                  disabled={!hasAi}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                    selectedSource === 'ai'
                      ? 'bg-emerald-500 text-white'
                      : hasAi
                      ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      : 'bg-slate-50 text-slate-300 cursor-not-allowed'
                  }`}
                >
                  AI優化
                </button>
                <button
                  onClick={() => {
                    setEditValue(
                      selectedSource === 'extracted'
                        ? extractedSeoTitle
                        : selectedSource === 'ai'
                        ? aiSuggestedTitle
                        : customTitle || articleTitle || ''
                    );
                    setIsEditing(true);
                  }}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                    selectedSource === 'custom'
                      ? 'bg-purple-500 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  自定義
                </button>
              </div>
            </div>
          </div>

          {/* Custom editing section */}
          {isEditing && (
            <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-purple-800">自定義 SEO Title</span>
                </div>
                <span className={`text-xs ${editValue.length >= 20 && editValue.length <= 40 ? 'text-green-600' : 'text-amber-600'}`}>
                  {editValue.length}/25-35 字
                </span>
              </div>
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-purple-400"
                placeholder="輸入自定義 SEO Title（建議 25-35 字）"
              />
              <p className="mt-1 text-xs text-purple-600">
                SEO Title 用於搜尋結果顯示，應簡潔有力，包含主要關鍵詞。
              </p>
              <div className="flex justify-end gap-2 mt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(false)}
                >
                  取消
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveCustom}
                  disabled={editValue.trim().length === 0}
                  className="bg-purple-500 hover:bg-purple-600"
                >
                  應用
                </Button>
              </div>
            </div>
          )}

          {/* Show selected custom title */}
          {selectedSource === 'custom' && customTitle && !isEditing && (
            <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Edit3 className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-800">自定義 SEO Title</span>
                <span className="text-xs text-purple-600">({customTitle.length} 字)</span>
              </div>
              <p className="text-sm text-purple-700 pl-6">{customTitle}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

SEOTitleSelectionCard.displayName = 'SEOTitleSelectionCard';
