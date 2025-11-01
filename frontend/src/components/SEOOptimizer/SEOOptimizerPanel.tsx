/**
 * SEO Optimizer Panel - Main component integrating all SEO optimization features.
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Button, Card, Spinner } from '@/components/ui';
import { MetaTitleEditor } from './MetaTitleEditor';
import { MetaDescriptionEditor } from './MetaDescriptionEditor';
import { KeywordEditor } from './KeywordEditor';
import { SEOAnalysisProgress, AnalysisStatus } from './SEOAnalysisProgress';
import { OptimizationRecommendations, Recommendation } from './OptimizationRecommendations';
import { SEOMetadata } from '@/types/article';

export interface SEOOptimizerPanelProps {
  articleId: string;
  articleContent: string;
  articleTitle: string;
  onMetadataUpdate?: (metadata: SEOMetadata) => void;
  className?: string;
}

export const SEOOptimizerPanel: React.FC<SEOOptimizerPanelProps> = ({
  articleId,
  articleContent,
  articleTitle,
  onMetadataUpdate,
  className,
}) => {
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>('idle');
  const [currentStep, setCurrentStep] = useState<string>('');
  const [progress, setProgress] = useState(0);

  // Fetch existing SEO metadata
  const { data: metadata, refetch } = useQuery({
    queryKey: ['seo-metadata', articleId],
    queryFn: async () => {
      const response = await axios.get<SEOMetadata>(
        `/api/v1/seo/metadata/${articleId}`
      );
      return response.data;
    },
    enabled: !!articleId,
  });

  // Local state for editing
  const [metaTitle, setMetaTitle] = useState(metadata?.meta_title || '');
  const [metaDescription, setMetaDescription] = useState(
    metadata?.meta_description || ''
  );
  const [focusKeyword, setFocusKeyword] = useState(
    metadata?.focus_keyword || ''
  );
  const [additionalKeywords, setAdditionalKeywords] = useState<string[]>(
    metadata?.additional_keywords || []
  );

  // Update local state when metadata loads
  useState(() => {
    if (metadata) {
      setMetaTitle(metadata.meta_title || '');
      setMetaDescription(metadata.meta_description || '');
      setFocusKeyword(metadata.focus_keyword || '');
      setAdditionalKeywords(metadata.additional_keywords || []);
    }
  });

  // SEO Analysis mutation
  const analyzeMutation = useMutation({
    mutationFn: async () => {
      setAnalysisStatus('analyzing');
      setProgress(0);

      // Start analysis
      setCurrentStep('开始分析...');
      const analyzeResponse = await axios.post(
        `/api/v1/seo/analyze/${articleId}`,
        {
          content: articleContent,
          title: articleTitle,
          focus_keyword: focusKeyword,
        }
      );

      const taskId = analyzeResponse.data.task_id;
      setProgress(20);

      // Poll for status
      let attempts = 0;
      const maxAttempts = 30;

      while (attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 2000));

        setCurrentStep('分析中...');
        const statusResponse = await axios.get(
          `/api/v1/seo/analyze/${articleId}/status`,
          { params: { task_id: taskId } }
        );

        const status = statusResponse.data.status;
        setProgress(20 + (attempts / maxAttempts) * 60);

        if (status === 'completed') {
          setProgress(100);
          setCurrentStep('分析完成');
          setAnalysisStatus('completed');
          await refetch();
          return statusResponse.data;
        }

        if (status === 'failed') {
          throw new Error(statusResponse.data.error || '分析失败');
        }

        attempts++;
      }

      throw new Error('分析超时');
    },
    onError: (error: any) => {
      setAnalysisStatus('failed');
      console.error('SEO analysis failed:', error);
    },
  });

  // Save metadata mutation
  const saveMutation = useMutation({
    mutationFn: async (data: SEOMetadata) => {
      const response = await axios.put(
        `/api/v1/seo/metadata/${articleId}`,
        data
      );
      return response.data;
    },
    onSuccess: (data) => {
      alert('SEO 元数据已保存');
      onMetadataUpdate?.(data);
      refetch();
    },
    onError: (error: any) => {
      alert(`保存失败: ${error.response?.data?.message || error.message}`);
    },
  });

  const handleAnalyze = () => {
    analyzeMutation.mutate();
  };

  const handleSave = () => {
    const data: SEOMetadata = {
      meta_title: metaTitle,
      meta_description: metaDescription,
      focus_keyword: focusKeyword,
      additional_keywords: additionalKeywords,
      keyword_density: metadata?.keyword_density,
      readability_score: metadata?.readability_score,
      optimization_score: metadata?.optimization_score,
      recommendations: metadata?.recommendations,
    };

    saveMutation.mutate(data);
  };

  const recommendations: Recommendation[] =
    metadata?.recommendations?.map((rec, idx) => ({
      id: `rec-${idx}`,
      type: 'info',
      title: rec,
      description: '',
      actionable: false,
    })) || [];

  return (
    <div className={className}>
      <Card>
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">SEO 优化</h2>
            <Button
              variant="primary"
              onClick={handleAnalyze}
              disabled={analysisStatus === 'analyzing' || !articleContent}
            >
              {analysisStatus === 'analyzing' ? (
                <>
                  <Spinner size="sm" variant="white" className="mr-2" />
                  分析中...
                </>
              ) : (
                '运行 SEO 分析'
              )}
            </Button>
          </div>

          {/* Analysis Progress */}
          {analysisStatus !== 'idle' && (
            <SEOAnalysisProgress
              status={analysisStatus}
              currentStep={currentStep}
              progress={progress}
              onRetry={handleAnalyze}
            />
          )}

          {/* Meta Title Editor */}
          <MetaTitleEditor
            value={metaTitle}
            onChange={setMetaTitle}
            isAIGenerated={!!metadata?.meta_title}
          />

          {/* Meta Description Editor */}
          <MetaDescriptionEditor
            value={metaDescription}
            onChange={setMetaDescription}
            isAIGenerated={!!metadata?.meta_description}
          />

          {/* Keyword Editor */}
          <KeywordEditor
            focusKeyword={focusKeyword}
            additionalKeywords={additionalKeywords}
            onFocusKeywordChange={setFocusKeyword}
            onAdditionalKeywordsChange={setAdditionalKeywords}
            keywordDensity={metadata?.keyword_density}
          />

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <OptimizationRecommendations
              recommendations={recommendations}
              overallScore={metadata?.optimization_score}
            />
          )}

          {/* Save Button */}
          <div className="flex items-center gap-3 pt-4 border-t">
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={
                saveMutation.isPending ||
                !metaTitle ||
                !metaDescription ||
                !focusKeyword
              }
            >
              {saveMutation.isPending ? (
                <>
                  <Spinner size="sm" variant="white" className="mr-2" />
                  保存中...
                </>
              ) : (
                '保存 SEO 元数据'
              )}
            </Button>
            <Button variant="outline" onClick={() => refetch()}>
              重置
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
