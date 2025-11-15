/**
 * SEOTitleSelectionCard - SEO Title 選擇卡片元件
 *
 * Phase 9: SEO Title 提取與建議功能
 * - 顯示原文提取的 SEO Title（如果有）
 * - 顯示 2-3 個 AI 生成的 SEO Title 變體
 * - 支持自定義 SEO Title 輸入
 * - 調用 API 保存選擇的 SEO Title
 */

import React, { useState } from 'react';
import { Button } from '../ui';
import { Input } from '../ui/Input';
import { Badge } from '../ui/badge';
import { FileText, Check, Sparkles, Edit3, AlertCircle } from 'lucide-react';
import type { SEOTitleSuggestionsData, SEOTitleVariant, SelectSEOTitleRequest, SelectSEOTitleResponse } from '../../types/api';

export interface SEOTitleSelectionCardProps {
  /** 文章 ID */
  articleId: number;
  /** 當前 SEO Title */
  currentSeoTitle?: string | null;
  /** SEO Title 來源 */
  seoTitleSource?: string | null;
  /** AI 生成的 SEO Title 建議 */
  suggestions?: SEOTitleSuggestionsData | null;
  /** 是否顯示載入狀態 */
  isLoading?: boolean;
  /** 選擇成功回調 */
  onSelectionSuccess?: (response: SelectSEOTitleResponse) => void;
  /** 錯誤回調 */
  onError?: (error: Error) => void;
}

/**
 * SEOTitleSelectionCard Component
 */
export const SEOTitleSelectionCard: React.FC<SEOTitleSelectionCardProps> = ({
  articleId,
  currentSeoTitle,
  seoTitleSource,
  suggestions,
  isLoading = false,
  onSelectionSuccess,
  onError,
}) => {
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);
  const [customTitle, setCustomTitle] = useState('');
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 處理選擇 SEO Title
  const handleSelectSeoTitle = async () => {
    setIsSaving(true);

    try {
      const requestBody: SelectSEOTitleRequest = isCustomMode
        ? { custom_seo_title: customTitle }
        : { variant_id: selectedVariantId };

      const response = await fetch(`/api/v1/optimization/articles/${articleId}/select-seo-title`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to select SEO Title');
      }

      const result: SelectSEOTitleResponse = await response.json();

      // 成功回調
      if (onSelectionSuccess) {
        onSelectionSuccess(result);
      }

      // 重置狀態
      setSelectedVariantId(null);
      setCustomTitle('');
      setIsCustomMode(false);
    } catch (error) {
      console.error('Failed to select SEO Title:', error);
      if (onError) {
        onError(error as Error);
      }
    } finally {
      setIsSaving(false);
    }
  };

  // 檢查是否有選擇
  const hasSelection = isCustomMode ? customTitle.trim().length > 0 : selectedVariantId !== null;

  // 獲取原文提取的 SEO Title
  const originalSeoTitle = suggestions?.original_seo_title;

  // 獲取 SEO Title 來源標籤
  const getSourceBadge = (source: string | null | undefined) => {
    switch (source) {
      case 'extracted':
        return <Badge variant="success">原文提取</Badge>;
      case 'ai_generated':
        return <Badge variant="info">AI 生成</Badge>;
      case 'user_input':
        return <Badge variant="warning">自定義</Badge>;
      case 'migrated':
        return <Badge variant="secondary">資料遷移</Badge>;
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-20 bg-gray-100 rounded"></div>
          <div className="h-20 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm space-y-6" data-testid="seo-title-selection-card">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">SEO Title 選擇</h3>
        </div>
        {currentSeoTitle && seoTitleSource && getSourceBadge(seoTitleSource)}
      </div>

      {/* 說明 */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex gap-2">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium mb-1">什麼是 SEO Title？</p>
            <p className="text-blue-800">
              SEO Title 顯示在搜尋引擎結果中（<code className="px-1 py-0.5 bg-blue-100 rounded text-xs">&lt;title&gt;</code> 標籤），
              建議保持在 <strong>30 字左右</strong>，與頁面的 H1 標題分開。
            </p>
          </div>
        </div>
      </div>

      {/* 當前 SEO Title */}
      {currentSeoTitle && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg" data-testid="current-seo-title">
          <div className="text-xs text-gray-500 mb-2">當前 SEO Title</div>
          <div className="text-sm font-medium text-gray-900">{currentSeoTitle}</div>
          <div className="text-xs text-gray-500 mt-1">字符數：{currentSeoTitle.length}</div>
        </div>
      )}

      {/* 原文提取的 SEO Title */}
      {originalSeoTitle && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Check className="w-4 h-4 text-green-600" />
            <div className="text-xs text-green-700 font-medium">原文標記的 SEO Title</div>
          </div>
          <div className="text-sm font-medium text-gray-900">{originalSeoTitle}</div>
          <div className="text-xs text-gray-500 mt-1">字符數：{originalSeoTitle.length}</div>
        </div>
      )}

      {/* AI 建議的 SEO Title 變體 */}
      {suggestions?.variants && suggestions.variants.length > 0 && (
        <div className="space-y-3" data-testid="ai-variants">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <h4 className="text-sm font-semibold text-gray-900">AI 建議的 SEO Title</h4>
          </div>

          {suggestions.variants.map((variant: SEOTitleVariant) => (
            <button
              key={variant.id}
              type="button"
              data-testid="seo-variant"
              onClick={() => {
                setSelectedVariantId(variant.id);
                setIsCustomMode(false);
              }}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                selectedVariantId === variant.id && !isCustomMode
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50/50'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 space-y-2">
                  <div className="font-medium text-gray-900" data-testid="variant-seo-title">{variant.seo_title}</div>
                  <div className="text-xs text-gray-600" data-testid="variant-reasoning">{variant.reasoning}</div>
                  <div className="flex flex-wrap gap-1.5" data-testid="variant-keywords">
                    {variant.keywords_focus.map((keyword, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs" data-testid="keyword">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500" data-testid="variant-char-count">字符數：{variant.character_count}</div>
                </div>
                {selectedVariantId === variant.id && !isCustomMode && (
                  <Check className="w-5 h-5 text-purple-600 flex-shrink-0" />
                )}
              </div>
            </button>
          ))}

          {/* 優化建議說明 */}
          {suggestions.notes && suggestions.notes.length > 0 && (
            <div className="p-3 bg-gray-50 rounded-lg space-y-1">
              {suggestions.notes.map((note, idx) => (
                <div key={idx} className="text-xs text-gray-600 flex gap-2">
                  <span className="text-gray-400">•</span>
                  <span>{note}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 自定義 SEO Title */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Edit3 className="w-4 h-4 text-orange-600" />
          <h4 className="text-sm font-semibold text-gray-900">或者自定義 SEO Title</h4>
        </div>

        <div className="space-y-2">
          <Input
            type="text"
            value={customTitle}
            onChange={(e) => {
              setCustomTitle(e.target.value);
              setIsCustomMode(true);
              setSelectedVariantId(null);
            }}
            placeholder="輸入自定義的 SEO Title（建議 30 字左右）"
            className="w-full"
            data-testid="custom-seo-title-input"
          />
          {customTitle.length > 0 && (
            <div className="flex items-center justify-between text-xs" data-testid="char-count">
              <span className={customTitle.length <= 40 ? 'text-green-600' : 'text-amber-600'}>
                字符數：{customTitle.length}
              </span>
              {customTitle.length > 40 && (
                <span className="text-amber-600">⚠️ 建議保持在 40 字以內</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 操作按鈕 */}
      <div className="flex gap-3 pt-2">
        <Button
          onClick={handleSelectSeoTitle}
          disabled={!hasSelection || isSaving}
          className="flex-1"
        >
          {isSaving ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              保存中...
            </>
          ) : (
            <>
              <Check className="w-4 h-4 mr-2" />
              {isCustomMode ? '保存自定義 SEO Title' : '使用此 SEO Title'}
            </>
          )}
        </Button>

        {(selectedVariantId || isCustomMode) && (
          <Button
            variant="outline"
            onClick={() => {
              setSelectedVariantId(null);
              setCustomTitle('');
              setIsCustomMode(false);
            }}
            disabled={isSaving}
          >
            清除選擇
          </Button>
        )}
      </div>
    </div>
  );
};
