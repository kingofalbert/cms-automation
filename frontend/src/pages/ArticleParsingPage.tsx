/**
 * Article Parsing Page (Phase 7)
 *
 * Provides UI for:
 * - Triggering article parsing
 * - Reviewing parsing results
 * - Managing images
 * - Confirming parsed data
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
import { parsingAPI } from '../services';
import type {
  ParsedArticleData,
  ArticleImage,
  ImageReviewAction,
  OptimizationsResponse,
  TitleOption,
  RelatedArticle,
} from '../services/parsing';
import { RefreshCw } from 'lucide-react';
import TitleOptimizationCard from '../components/parsing/TitleOptimizationCard';

export default function ArticleParsingPage() {
  const { id } = useParams<{ id: string }>();
  const articleId = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [parseMode, setParseMode] = useState<'ai' | 'heuristic'>('heuristic');
  const [editingImage, setEditingImage] = useState<number | null>(null);
  const [newCaption, setNewCaption] = useState('');
  const [selectedTitleId, setSelectedTitleId] = useState<string | null>(null);
  const [isPollingOptimizations, setIsPollingOptimizations] = useState(false);

  // Query: Get parsing result
  const {
    data: parsingData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: parsingAPI.parsingKeys.result(articleId),
    queryFn: () => parsingAPI.getParsingResult(articleId),
    enabled: !!articleId,
    retry: false,
  });

  // Mutation: Parse article
  const parseMutation = useMutation({
    mutationFn: () =>
      parsingAPI.parseArticle(articleId, {
        use_ai: parseMode === 'ai',
        download_images: true,
        fallback_to_heuristic: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: parsingAPI.parsingKeys.result(articleId),
      });
    },
  });

  // Mutation: Confirm parsing
  const confirmMutation = useMutation({
    mutationFn: () =>
      parsingAPI.confirmParsing(articleId, {
        confirmed_by: 'frontend_user', // TODO: Get from auth context
        feedback: 'Confirmed via UI',
      }),
    onSuccess: () => {
      // Start polling for optimization status after confirmation
      // Backend automatically triggers optimization generation
      setIsPollingOptimizations(true);

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({
        queryKey: parsingAPI.parsingKeys.result(articleId),
      });
    },
  });

  // Mutation: Review image
  const reviewImageMutation = useMutation({
    mutationFn: ({
      imageId,
      action,
      caption,
    }: {
      imageId: number;
      action: ImageReviewAction;
      caption?: string;
    }) =>
      parsingAPI.reviewImage(articleId, imageId, {
        action,
        new_caption: caption,
      }),
    onSuccess: () => {
      setEditingImage(null);
      setNewCaption('');
      queryClient.invalidateQueries({
        queryKey: parsingAPI.parsingKeys.result(articleId),
      });
    },
  });

  // Mutation: Refresh related articles (Phase 12)
  const refreshRelatedArticlesMutation = useMutation({
    mutationFn: () => parsingAPI.refreshRelatedArticles(articleId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: parsingAPI.parsingKeys.result(articleId),
      });
    },
  });

  // Query: Get optimizations
  const {
    data: optimizationsData,
    isLoading: isOptimizationsLoading,
    refetch: refetchOptimizations,
  } = useQuery({
    queryKey: parsingAPI.parsingKeys.optimizations(articleId),
    queryFn: () => parsingAPI.getOptimizations(articleId),
    enabled: !!articleId && !!parsingData,
    retry: false,
    refetchInterval: isPollingOptimizations ? 3000 : false, // Poll every 3 seconds when enabled
  });

  // Query: Get optimization status (for polling)
  const { data: optimizationStatus } = useQuery({
    queryKey: parsingAPI.parsingKeys.optimizationStatus(articleId),
    queryFn: () => parsingAPI.getOptimizationStatus(articleId),
    enabled: !!articleId && isPollingOptimizations,
    refetchInterval: 2000, // Poll every 2 seconds
    retry: false,
  });

  // Stop polling when optimizations are generated
  React.useEffect(() => {
    if (optimizationStatus?.generated || optimizationsData) {
      setIsPollingOptimizations(false);
    }
  }, [optimizationStatus, optimizationsData]);

  // Mutation: Generate optimizations
  const generateOptimizationsMutation = useMutation({
    mutationFn: () =>
      parsingAPI.generateAllOptimizations(articleId, {
        regenerate: false,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(
        parsingAPI.parsingKeys.optimizations(articleId),
        data
      );
    },
  });

  const handleParse = () => {
    parseMutation.mutate();
  };

  const handleConfirm = () => {
    confirmMutation.mutate();
  };

  const handleUpdateCaption = (imageId: number) => {
    reviewImageMutation.mutate({
      imageId,
      action: 'replace_caption',
      caption: newCaption,
    });
  };

  const handleRemoveImage = (imageId: number) => {
    if (confirm('确定要删除这张图片吗？')) {
      reviewImageMutation.mutate({
        imageId,
        action: 'remove',
      });
    }
  };

  const handleGenerateOptimizations = () => {
    generateOptimizationsMutation.mutate();
  };

  const handleSelectTitle = (optionId: string) => {
    setSelectedTitleId(optionId);
  };

  const handleEditTitle = (
    optionId: string,
    field: 'prefix' | 'main' | 'suffix',
    value: string
  ) => {
    // TODO: Implement title editing persistence
    console.log('Edit title:', { optionId, field, value });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">文章解析</h1>
          <p className="text-muted-foreground">
            提取文章结构化数据 (标题、作者、正文、SEO、图片)
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/worklist')}>
          返回工作列表
        </Button>
      </div>

      {/* Parsing Controls */}
      {!parsingData && !isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>开始解析</CardTitle>
            <CardDescription>
              选择解析模式并开始提取文章数据
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                variant={parseMode === 'ai' ? 'primary' : 'outline'}
                onClick={() => setParseMode('ai')}
              >
                AI 模式 (Claude)
              </Button>
              <Button
                variant={parseMode === 'heuristic' ? 'primary' : 'outline'}
                onClick={() => setParseMode('heuristic')}
              >
                启发式模式 (快速)
              </Button>
            </div>

            <Button
              onClick={handleParse}
              disabled={parseMutation.isPending}
              className="w-full"
            >
              {parseMutation.isPending ? '解析中...' : '开始解析'}
            </Button>

            {parseMutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  解析失败: {(parseMutation.error as Error).message}
                </AlertDescription>
              </Alert>
            )}

            {parseMutation.isSuccess && (
              <Alert>
                <AlertDescription>
                  ✅ 解析成功! 方法: {parseMutation.data.parsing_method}, 置信度:{' '}
                  {((parseMutation.data.parsing_confidence || 0) * 100).toFixed(0)}%,
                  图片: {parseMutation.data.images_processed}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      )}

      {/* Parsing Result */}
      {parsingData && (
        <>
          {/* Title & Author */}
          <Card>
            <CardHeader>
              <CardTitle>标题与作者</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">
                  完整标题
                </label>
                <p className="text-2xl font-bold mt-1">
                  {parsingData.full_title}
                </p>
              </div>

              {parsingData.title_prefix && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    标题前缀
                  </label>
                  <Badge variant="secondary" className="mt-1">
                    {parsingData.title_prefix}
                  </Badge>
                </div>
              )}

              {parsingData.title_suffix && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    副标题
                  </label>
                  <p className="mt-1">{parsingData.title_suffix}</p>
                </div>
              )}

              {parsingData.author_name && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    作者
                  </label>
                  <p className="mt-1">{parsingData.author_name}</p>
                  {parsingData.author_line && (
                    <p className="text-sm text-muted-foreground">
                      {parsingData.author_line}
                    </p>
                  )}
                </div>
              )}

              <div className="flex gap-2">
                <Badge variant="info">
                  方法: {parsingData.parsing_method}
                </Badge>
                <Badge variant="info">
                  置信度:{' '}
                  {(parsingData.parsing_confidence * 100).toFixed(0)}%
                </Badge>
                {parsingData.parsing_confirmed && (
                  <Badge variant="default">✓ 已确认</Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Title Optimization (Phase 7) */}
          {!optimizationsData && !isOptimizationsLoading && (
            <Card>
              <CardContent className="pt-6">
                {isPollingOptimizations ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-3"></div>
                    <p className="text-sm font-medium">
                      正在后台生成 AI 优化建议...
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      这通常需要 20-30 秒，生成完成后会自动显示
                    </p>
                  </div>
                ) : parsingData.parsing_confirmed ? (
                  <Alert>
                    <AlertDescription>
                      💡 提示：AI 优化建议将在解析确认后自动生成。
                      如需重新生成，请点击下方按钮。
                    </AlertDescription>
                    <Button
                      onClick={handleGenerateOptimizations}
                      disabled={generateOptimizationsMutation.isPending}
                      className="w-full mt-3"
                      variant="outline"
                    >
                      {generateOptimizationsMutation.isPending
                        ? '正在生成...'
                        : '🔄 重新生成优化建议'}
                    </Button>
                  </Alert>
                ) : (
                  <Alert>
                    <AlertDescription>
                      💡 提示：确认解析结果后，系统将自动生成 AI 优化建议（标题、SEO、FAQ）
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          {(optimizationsData || generateOptimizationsMutation.data) && (
            <>
              <TitleOptimizationCard
                original={{
                  prefix: parsingData.title_prefix,
                  main: parsingData.title_main,
                  suffix: parsingData.title_suffix,
                  full: parsingData.full_title,
                }}
                suggestions={
                  optimizationsData?.title_suggestions.suggested_title_sets ||
                  generateOptimizationsMutation.data?.title_suggestions.suggested_title_sets ||
                  []
                }
                notes={
                  optimizationsData?.title_suggestions.optimization_notes ||
                  generateOptimizationsMutation.data?.title_suggestions.optimization_notes ||
                  []
                }
                isGenerating={generateOptimizationsMutation.isPending}
                selectedId={selectedTitleId}
                onSelect={handleSelectTitle}
                onEdit={handleEditTitle}
              />

              {/* Navigate to SEO Confirmation */}
              <Card>
                <CardContent className="pt-6">
                  <Button
                    onClick={() => navigate(`/articles/${articleId}/seo-confirmation`)}
                    className="w-full"
                    size="lg"
                  >
                    下一步: 审核 SEO 和 FAQ →
                  </Button>
                  <p className="text-sm text-muted-foreground text-center mt-2">
                    查看和编辑 AI 生成的 SEO 关键词、Meta Description、标签和 FAQ
                  </p>
                </CardContent>
              </Card>
            </>
          )}

          {/* SEO Metadata */}
          {parsingData.has_seo_data && (
            <Card>
              <CardHeader>
                <CardTitle>SEO 元数据</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {parsingData.meta_description && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">
                      Meta Description
                    </label>
                    <p className="mt-1">{parsingData.meta_description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      长度: {parsingData.meta_description.length} 字符
                    </p>
                  </div>
                )}

                {parsingData.seo_keywords.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">
                      关键词
                    </label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {parsingData.seo_keywords.map((keyword, idx) => (
                        <Badge key={idx} variant="secondary">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Images */}
          {parsingData.images.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>图片 ({parsingData.images.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {parsingData.images.map((image) => (
                    <div
                      key={image.id}
                      className="border rounded-lg p-4 space-y-2"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-medium">
                            位置: {image.position} | {image.width}x
                            {image.height} | {image.format}
                          </p>
                          {editingImage === image.id ? (
                            <div className="mt-2 space-y-2">
                              <input
                                type="text"
                                value={newCaption}
                                onChange={(e) => setNewCaption(e.target.value)}
                                placeholder="输入新标题"
                                className="w-full px-3 py-2 border rounded"
                              />
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  onClick={() => handleUpdateCaption(image.id)}
                                  disabled={reviewImageMutation.isPending}
                                >
                                  保存
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setEditingImage(null)}
                                >
                                  取消
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground mt-1">
                              {image.caption || '(无标题)'}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingImage(image.id);
                              setNewCaption(image.caption || '');
                            }}
                          >
                            编辑标题
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => handleRemoveImage(image.id)}
                            disabled={reviewImageMutation.isPending}
                          >
                            删除
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Related Articles Section (Phase 12) */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>
                    相關文章推薦 ({parsingData.related_articles?.length || 0})
                  </CardTitle>
                  <CardDescription>
                    AI 根據標題和關鍵詞自動匹配的內部鏈接文章
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refreshRelatedArticlesMutation.mutate()}
                  disabled={refreshRelatedArticlesMutation.isPending}
                >
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${
                      refreshRelatedArticlesMutation.isPending ? 'animate-spin' : ''
                    }`}
                  />
                  {refreshRelatedArticlesMutation.isPending ? '匹配中...' : '刷新匹配'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {parsingData.related_articles && parsingData.related_articles.length > 0 ? (
                <>
                  <div className="space-y-3">
                    {parsingData.related_articles.map((article, idx) => (
                      <div
                        key={article.article_id}
                        className="border rounded-lg p-3 hover:bg-accent/50 transition-colors"
                      >
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex-1 min-w-0">
                            <a
                              href={article.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-medium text-primary hover:underline block truncate"
                            >
                              {article.title}
                            </a>
                            {article.excerpt && (
                              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                {article.excerpt}
                              </p>
                            )}
                            {article.ai_keywords && article.ai_keywords.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {article.ai_keywords.slice(0, 3).map((keyword, kidx) => (
                                  <Badge key={kidx} variant="outline" className="text-xs">
                                    {keyword}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            <Badge
                              variant={
                                article.match_type === 'semantic'
                                  ? 'default'
                                  : article.match_type === 'content'
                                  ? 'secondary'
                                  : 'outline'
                              }
                            >
                              {article.match_type === 'semantic'
                                ? '語義匹配'
                                : article.match_type === 'content'
                                ? '內容匹配'
                                : '關鍵詞匹配'}
                            </Badge>
                            <span className="text-sm font-medium text-green-600">
                              {(article.similarity * 100).toFixed(0)}% 相似
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-4 text-center">
                    💡 這些文章來自大紀元健康文章數據庫，可用於內部鏈接優化
                  </p>
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p className="mb-2">尚未匹配到相關文章</p>
                  <p className="text-sm">
                    點擊「刷新匹配」按鈕根據文章標題和關鍵詞搜索相關內部鏈接
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Body Preview */}
          <Card>
            <CardHeader>
              <CardTitle>正文预览</CardTitle>
            </CardHeader>
            <CardContent>
              <div
                className="prose max-w-none"
                dangerouslySetInnerHTML={{
                  __html: parsingData.body_html.substring(0, 500) + '...',
                }}
              />
              <p className="text-sm text-muted-foreground mt-4">
                正文长度: {parsingData.body_html.length} 字符
              </p>
            </CardContent>
          </Card>

          {/* Confirm Button */}
          {!parsingData.parsing_confirmed && (
            <Card>
              <CardContent className="pt-6">
                <Button
                  onClick={handleConfirm}
                  disabled={confirmMutation.isPending}
                  className="w-full"
                  size="lg"
                >
                  {confirmMutation.isPending
                    ? '确认中...'
                    : '✓ 确认解析结果并生成 AI 优化建议'}
                </Button>
                <p className="text-sm text-muted-foreground text-center mt-2">
                  确认后将自动生成标题优化、SEO关键词和FAQ建议
                </p>
              </CardContent>
            </Card>
          )}

          {/* Back to Worklist - Only show after confirmation */}
          {parsingData.parsing_confirmed && !isPollingOptimizations && optimizationsData && (
            <Card>
              <CardContent className="pt-6">
                <Button
                  onClick={() => navigate('/worklist')}
                  variant="outline"
                  className="w-full"
                  size="lg"
                >
                  返回工作列表
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
