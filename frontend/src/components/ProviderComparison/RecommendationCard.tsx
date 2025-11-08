/**
 * Recommendation Card component.
 * Displays provider recommendation with score and details.
 */

import { Recommendation } from '@/types/analytics';
import { Card, Badge } from '@/components/ui';
import type { BadgeProps } from '@/components/ui';
import { Star, CheckCircle, XCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export interface RecommendationCardProps {
  recommendation: Recommendation;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
}) => {
  const { t } = useTranslation();

  const getProviderLabel = (provider: string) =>
    t(`providerComparison.providers.${provider}`, {
      defaultValue: provider,
    });

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score: number): NonNullable<BadgeProps['variant']> => {
    if (score >= 90) return 'success';
    if (score >= 75) return 'info';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <h3 className="text-lg font-semibold text-gray-900">
            {getProviderLabel(recommendation.provider)}
          </h3>
          {recommendation.score >= 85 && (
            <Star className="w-5 h-5 ml-2 text-yellow-500 fill-current" />
          )}
        </div>
        <Badge variant={getScoreBadgeVariant(recommendation.score)} size="lg">
          <span className={`text-lg font-bold ${getScoreColor(recommendation.score)}`}>
            {recommendation.score}
          </span>
          <span className="text-sm ml-1">
            {t('providerComparison.recommendations.scoreSuffix')}
          </span>
        </Badge>
      </div>

      {/* Reason */}
      <div className="mb-4">
        <p className="text-sm text-gray-700">{recommendation.reason}</p>
      </div>

      {/* Use Cases */}
      {recommendation.use_cases.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            {t('providerComparison.recommendations.useCases')}:
          </h4>
          <ul className="space-y-1">
            {recommendation.use_cases.map((useCase, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start">
                <span className="mr-2">•</span>
                <span>{useCase}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pros and Cons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Pros */}
        {recommendation.pros.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <CheckCircle className="w-4 h-4 mr-1 text-green-600" />
              {t('providerComparison.recommendations.pros')}
            </h4>
            <ul className="space-y-1">
              {recommendation.pros.map((pro, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span>{pro}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Cons */}
        {recommendation.cons.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <XCircle className="w-4 h-4 mr-1 text-red-600" />
              {t('providerComparison.recommendations.cons')}
            </h4>
            <ul className="space-y-1">
              {recommendation.cons.map((con, index) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-red-600 mr-2">✗</span>
                  <span>{con}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  );
};
