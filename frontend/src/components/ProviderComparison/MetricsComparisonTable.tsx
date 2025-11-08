/**
 * Metrics Comparison Table component.
 * Displays provider performance metrics in a tabular format.
 */

import { ProviderMetrics } from '@/types/analytics';
import { Badge } from '@/components/ui';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export interface MetricsComparisonTableProps {
  metrics: ProviderMetrics[];
  highlightBest?: boolean;
}

export const MetricsComparisonTable: React.FC<MetricsComparisonTableProps> = ({
  metrics,
  highlightBest = true,
}) => {
  const { t } = useTranslation();

  if (metrics.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {t('providerComparison.noData')}
      </div>
    );
  }

  // Find best values for highlighting
  const bestSuccessRate = Math.max(...metrics.map((m) => m.success_rate));
  const bestCost = Math.min(...metrics.map((m) => m.avg_cost));
  const bestSpeed = Math.min(...metrics.map((m) => m.avg_duration));

  const isBest = (value: number, bestValue: number, reverse = false) => {
    if (!highlightBest) return false;
    return reverse ? value === bestValue : value === bestValue;
  };

  const formatDuration = (seconds: number) =>
    t('providerComparison.table.minutesSeconds', {
      minutes: Math.floor(seconds / 60),
      seconds: seconds % 60,
    });

  const getProviderLabel = (provider: string) =>
    t(`providerComparison.providers.${provider}`, {
      defaultValue: provider,
    });

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('providerComparison.table.provider')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('providerComparison.table.totalTasks')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('providerComparison.table.successRate')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('providerComparison.table.avgDuration')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('providerComparison.table.avgCost')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('providerComparison.table.totalCost')}
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {metrics.map((metric) => (
            <tr key={metric.provider} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <span className="font-medium text-gray-900">
                    {getProviderLabel(metric.provider)}
                  </span>
                  {metric.provider === 'hybrid' && (
                    <Badge variant="info" size="sm" className="ml-2">
                      {t('providerComparison.table.recommendedBadge')}
                    </Badge>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{metric.total_tasks}</div>
                <div className="text-xs text-gray-500">
                  {t('providerComparison.table.successFailure', {
                    success: metric.successful_tasks,
                    failed: metric.failed_tasks,
                  })}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <span
                    className={`text-sm font-medium ${
                      isBest(metric.success_rate, bestSuccessRate)
                        ? 'text-green-600'
                        : 'text-gray-900'
                    }`}
                  >
                    {metric.success_rate.toFixed(1)}%
                  </span>
                  {isBest(metric.success_rate, bestSuccessRate) && (
                    <TrendingUp className="w-4 h-4 ml-1 text-green-600" />
                  )}
                  {metric.success_rate < 80 && (
                    <TrendingDown className="w-4 h-4 ml-1 text-red-600" />
                  )}
                  {metric.success_rate >= 80 &&
                    !isBest(metric.success_rate, bestSuccessRate) && (
                      <Minus className="w-4 h-4 ml-1 text-gray-400" />
                    )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`text-sm ${
                    isBest(metric.avg_duration, bestSpeed)
                      ? 'text-green-600 font-medium'
                      : 'text-gray-900'
                  }`}
                >
                  {formatDuration(metric.avg_duration)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span
                  className={`text-sm ${
                    isBest(metric.avg_cost, bestCost)
                      ? 'text-green-600 font-medium'
                      : 'text-gray-900'
                  }`}
                >
                  ${metric.avg_cost.toFixed(3)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="text-sm text-gray-900">
                  ${metric.total_cost.toFixed(2)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
