/**
 * Optimization Recommendations component.
 * Displays AI-generated SEO improvement suggestions.
 */

import { Badge } from '@/components/ui';
import { clsx } from 'clsx';

export interface Recommendation {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  description: string;
  actionable?: boolean;
}

export interface OptimizationRecommendationsProps {
  recommendations: Recommendation[];
  overallScore?: number;
  className?: string;
}

export const OptimizationRecommendations: React.FC<
  OptimizationRecommendationsProps
> = ({ recommendations, overallScore, className }) => {
  if (recommendations.length === 0) {
    return (
      <div className={clsx('text-center py-8 text-gray-500', className)}>
        <svg
          className="w-12 h-12 mx-auto mb-3 opacity-50"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <p>暂无优化建议</p>
        <p className="text-sm mt-1">运行 SEO 分析后将显示建议</p>
      </div>
    );
  }

  const getTypeIcon = (type: Recommendation['type']) => {
    switch (type) {
      case 'success':
        return (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'info':
        return (
          <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return '优秀';
    if (score >= 60) return '良好';
    if (score >= 40) return '一般';
    return '需改进';
  };

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Overall Score */}
      {overallScore !== undefined && (
        <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总体 SEO 评分</p>
              <p className="text-sm text-gray-500 mt-1">
                {getScoreLabel(overallScore)}
              </p>
            </div>
            <div className="text-right">
              <p className={clsx('text-3xl font-bold', getScoreColor(overallScore))}>
                {overallScore}
              </p>
              <p className="text-sm text-gray-600">/100</p>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations List */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">
          优化建议 ({recommendations.length})
        </h3>

        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className={clsx(
              'border rounded-lg p-4 hover:shadow-sm transition-shadow',
              rec.actionable && 'cursor-pointer hover:border-primary-300'
            )}
          >
            <div className="flex gap-3">
              <div className="flex-shrink-0 mt-0.5">{getTypeIcon(rec.type)}</div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-900 mb-1">
                  {rec.title}
                </h4>
                <p className="text-sm text-gray-600">{rec.description}</p>
                {rec.actionable && (
                  <Badge variant="info" size="sm" className="mt-2">
                    可操作
                  </Badge>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
