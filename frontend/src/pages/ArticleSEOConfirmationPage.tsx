/**
 * Article SEO Confirmation Page (Phase 7 - Step 3)
 *
 * Displays and allows editing of AI-generated SEO suggestions:
 * - SEO Keywords (focus, primary, secondary)
 * - Meta Description
 * - Tags
 * - FAQs (with drag-and-drop reordering)
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/ui';
import { Button } from '../components/ui';
import { Badge } from '../components/ui';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Skeleton } from '../components/ui';
import { parsingAPI, seoAPI } from '../services';
import type {
  OptimizationsResponse,
  FAQData,
  TagSuggestion,
} from '../services/parsing';

export default function ArticleSEOConfirmationPage() {
  const { id } = useParams<{ id: string }>();
  const articleId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Local state for editing
  const [editingMetaDescription, setEditingMetaDescription] = useState(false);
  const [metaDescriptionValue, setMetaDescriptionValue] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [faqs, setFaqs] = useState<FAQData[]>([]);
  const [draggedFAQIndex, setDraggedFAQIndex] = useState<number | null>(null);

  // Query: Get optimizations
  const {
    data: optimizationsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: parsingAPI.parsingKeys.optimizations(articleId),
    queryFn: () => parsingAPI.getOptimizations(articleId),
    enabled: !!articleId,
    retry: false,
  });

  // Query: Get parsing result (for article context)
  const { data: parsingData } = useQuery({
    queryKey: parsingAPI.parsingKeys.result(articleId),
    queryFn: () => parsingAPI.getParsingResult(articleId),
    enabled: !!articleId,
    retry: false,
  });

  // Initialize state when data loads
  React.useEffect(() => {
    if (optimizationsData) {
      setMetaDescriptionValue(
        optimizationsData.seo_suggestions.meta_description.suggested_meta_description || ''
      );
      setSelectedTags(
        optimizationsData.seo_suggestions.tags.suggested_tags
          .slice(0, 8) // Default to first 8 tags
          .map((t) => t.tag)
      );
      setFaqs(optimizationsData.faqs || []);
    }
  }, [optimizationsData]);

  // Mutation: Confirm SEO - saves meta description and stores tags/FAQs in manual_overrides
  const confirmSEOMutation = useMutation({
    mutationFn: async () => {
      // Use the SEO API to save confirmed data
      const response = await seoAPI.update(articleId, {
        meta_description: metaDescriptionValue,
        // Store additional data in manual_overrides for future use
        manual_overrides: {
          confirmed_tags: selectedTags,
          confirmed_faqs: faqs,
          confirmed_at: new Date().toISOString(),
        },
      });
      return response;
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['seo', articleId] });
      // Navigate to next step or back to worklist
      navigate('/worklist');
    },
    onError: (error) => {
      console.error('Failed to save SEO confirmation:', error);
      // Error is shown via Alert component below
    },
  });

  // Handler: Toggle tag selection
  const handleToggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag)
        ? prev.filter((t) => t !== tag)
        : [...prev, tag]
    );
  };

  // Handler: Save meta description
  const handleSaveMetaDescription = () => {
    setEditingMetaDescription(false);
  };

  // Handler: FAQ drag and drop
  const handleDragStart = (index: number) => {
    setDraggedFAQIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedFAQIndex === null || draggedFAQIndex === index) return;

    const newFaqs = [...faqs];
    const draggedItem = newFaqs[draggedFAQIndex];
    newFaqs.splice(draggedFAQIndex, 1);
    newFaqs.splice(index, 0, draggedItem);

    setFaqs(newFaqs);
    setDraggedFAQIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedFAQIndex(null);
  };

  const handleConfirm = () => {
    confirmSEOMutation.mutate();
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>
            加载优化建议失败: {(error as Error).message}
          </AlertDescription>
        </Alert>
        <Button onClick={() => navigate('/worklist')} className="mt-4">
          返回工作列表
        </Button>
      </div>
    );
  }

  // No data state
  if (!optimizationsData) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertDescription>
            未找到优化建议。请先在文章解析页面生成 AI 优化建议。
          </AlertDescription>
        </Alert>
        <Button onClick={() => navigate(`/articles/${articleId}/parsing`)} className="mt-4">
          返回解析页面
        </Button>
      </div>
    );
  }

  const seoSuggestions = optimizationsData.seo_suggestions;
  const metaLength = metaDescriptionValue.length;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">SEO 与 FAQ 确认</h1>
          <p className="text-muted-foreground">
            审核并编辑 AI 生成的 SEO 关键词、Meta Description、标签和 FAQ
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate(`/articles/${articleId}/parsing`)}>
          返回解析页面
        </Button>
      </div>

      {/* Article Context */}
      {parsingData && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{parsingData.full_title}</CardTitle>
            <CardDescription>
              作者: {parsingData.author_name || '未知'} | 正文长度: {parsingData.body_html.length} 字符
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Generation Metadata */}
      {optimizationsData.generation_metadata && (
        <Alert>
          <AlertDescription>
            <div className="flex gap-4 text-sm">
              <span>
                💰 成本: ${optimizationsData.generation_metadata.total_cost_usd?.toFixed(4) || '0.0000'}
              </span>
              <span>
                ⏱️ 耗时: {optimizationsData.generation_metadata.duration_ms}ms
              </span>
              <span>
                🔄 缓存: {optimizationsData.generation_metadata.cached ? '是' : '否'}
              </span>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* SEO Keywords */}
      <Card>
        <CardHeader>
          <CardTitle>SEO 关键词</CardTitle>
          <CardDescription>
            AI 分析的核心关键词，用于优化搜索引擎排名
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Focus Keyword */}
          {seoSuggestions.seo_keywords.focus_keyword && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                核心关键词 (Focus Keyword)
              </label>
              <div className="mt-2">
                <Badge variant="default" className="text-lg px-4 py-2">
                  {seoSuggestions.seo_keywords.focus_keyword}
                </Badge>
              </div>
              {seoSuggestions.seo_keywords.focus_keyword_rationale && (
                <p className="text-sm text-muted-foreground mt-2">
                  💡 {seoSuggestions.seo_keywords.focus_keyword_rationale}
                </p>
              )}
            </div>
          )}

          {/* Primary Keywords */}
          {seoSuggestions.seo_keywords.primary_keywords.length > 0 && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                主要关键词 ({seoSuggestions.seo_keywords.primary_keywords.length})
              </label>
              <div className="flex flex-wrap gap-2 mt-2">
                {seoSuggestions.seo_keywords.primary_keywords.map((keyword, idx) => (
                  <Badge key={idx} variant="secondary">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Secondary Keywords */}
          {seoSuggestions.seo_keywords.secondary_keywords.length > 0 && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                次要关键词 ({seoSuggestions.seo_keywords.secondary_keywords.length})
              </label>
              <div className="flex flex-wrap gap-2 mt-2">
                {seoSuggestions.seo_keywords.secondary_keywords.map((keyword, idx) => (
                  <Badge key={idx} variant="secondary">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Meta Description */}
      <Card>
        <CardHeader>
          <CardTitle>Meta Description</CardTitle>
          <CardDescription>
            搜索结果中显示的文章描述 (推荐 150-160 字符)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Original (if exists) */}
          {seoSuggestions.meta_description.original_meta_description && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                原始 Meta Description
              </label>
              <p className="mt-1 text-sm bg-muted p-3 rounded">
                {seoSuggestions.meta_description.original_meta_description}
              </p>
            </div>
          )}

          {/* Suggested (editable) */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium text-muted-foreground">
                AI 建议的 Meta Description
              </label>
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm ${
                    metaLength >= 150 && metaLength <= 160
                      ? 'text-green-600'
                      : 'text-orange-600'
                  }`}
                >
                  {metaLength} / 150-160 字符
                </span>
                {seoSuggestions.meta_description.meta_description_score && (
                  <Badge variant="info">
                    评分: {seoSuggestions.meta_description.meta_description_score}/100
                  </Badge>
                )}
              </div>
            </div>

            {editingMetaDescription ? (
              <div className="space-y-2">
                <textarea
                  value={metaDescriptionValue}
                  onChange={(e) => setMetaDescriptionValue(e.target.value)}
                  className="w-full px-3 py-2 border rounded min-h-[100px]"
                  placeholder="输入 Meta Description"
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSaveMetaDescription}>
                    保存
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditingMetaDescription(false);
                      setMetaDescriptionValue(
                        seoSuggestions.meta_description.suggested_meta_description || ''
                      );
                    }}
                  >
                    取消
                  </Button>
                </div>
              </div>
            ) : (
              <div>
                <p className="bg-background p-3 rounded border">
                  {metaDescriptionValue}
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditingMetaDescription(true)}
                  className="mt-2"
                >
                  编辑
                </Button>
              </div>
            )}
          </div>

          {/* Improvements */}
          {seoSuggestions.meta_description.meta_description_improvements.length > 0 && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                优化建议
              </label>
              <ul className="mt-2 space-y-1">
                {seoSuggestions.meta_description.meta_description_improvements.map((improvement, idx) => (
                  <li key={idx} className="text-sm flex items-start gap-2">
                    <span className="text-green-600">✓</span>
                    <span>{improvement}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tags */}
      <Card>
        <CardHeader>
          <CardTitle>标签 (Tags)</CardTitle>
          <CardDescription>
            推荐选择 {seoSuggestions.tags.recommended_tag_count || '6-8'} 个标签
            {seoSuggestions.tags.tag_strategy && ` | 策略: ${seoSuggestions.tags.tag_strategy}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {seoSuggestions.tags.suggested_tags.map((tagSuggestion, idx) => {
              const isSelected = selectedTags.includes(tagSuggestion.tag);
              return (
                <button
                  key={idx}
                  onClick={() => handleToggleTag(tagSuggestion.tag)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                    isSelected
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                >
                  {tagSuggestion.tag}
                  <span className="ml-1.5 text-xs opacity-70">
                    {(tagSuggestion.relevance * 100).toFixed(0)}%
                  </span>
                </button>
              );
            })}
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            已选择: {selectedTags.length} 个标签
          </p>
        </CardContent>
      </Card>

      {/* FAQs */}
      <Card>
        <CardHeader>
          <CardTitle>FAQ 列表 ({faqs.length})</CardTitle>
          <CardDescription>
            优化 AI 搜索引擎可见性 | 可拖拽调整顺序
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {faqs.map((faq, index) => (
              <div
                key={index}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                className={`border rounded-lg p-4 cursor-move transition-all ${
                  draggedFAQIndex === index
                    ? 'opacity-50 scale-95'
                    : 'hover:shadow-md'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-muted rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium">{faq.question}</p>
                      <div className="flex gap-1">
                        {faq.question_type && (
                          <Badge variant="info" className="text-xs">
                            {faq.question_type}
                          </Badge>
                        )}
                        {faq.confidence !== undefined && faq.confidence !== null && (
                          <Badge variant="secondary" className="text-xs">
                            {(faq.confidence * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">{faq.answer}</p>
                    {faq.keywords_covered.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {faq.keywords_covered.map((keyword, kidx) => (
                          <Badge key={kidx} variant="secondary" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Confirm Button */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {/* Show error if mutation failed */}
          {confirmSEOMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                保存失败: {(confirmSEOMutation.error as Error)?.message || '未知错误'}
              </AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleConfirm}
            disabled={confirmSEOMutation.isPending}
            className="w-full"
            size="lg"
          >
            {confirmSEOMutation.isPending
              ? '确认中...'
              : '✓ 确认 SEO 和 FAQ 设置'}
          </Button>
          <p className="text-sm text-muted-foreground text-center mt-2">
            确认后将保存 Meta Description 到数据库，可以继续发布流程
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
