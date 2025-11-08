/**
 * Provider Comparison Page
 * Displays comprehensive analytics and comparison between different publishing providers.
 */

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Card, Tabs, TabsList, TabsTrigger, TabsContent, Select } from '@/components/ui';
import { MetricsComparisonTable } from '@/components/ProviderComparison/MetricsComparisonTable';
import { SuccessRateLineChart } from '@/components/ProviderComparison/SuccessRateLineChart';
import { CostComparisonBarChart } from '@/components/ProviderComparison/CostComparisonBarChart';
import { TaskDistributionPieChart } from '@/components/ProviderComparison/TaskDistributionPieChart';
import { RecommendationCard } from '@/components/ProviderComparison/RecommendationCard';
import { ProviderComparison, TimeRange } from '@/types/analytics';
import { TrendingUp, DollarSign, Clock, Award } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function ProviderComparisonPage() {
  const { t } = useTranslation();
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');

  // Fetch comparison data
  const { data: comparison, isLoading } = useQuery({
    queryKey: ['provider-comparison', timeRange],
    queryFn: async () => {
      const response = await axios.get<ProviderComparison>(
        '/v1/analytics/provider-comparison',
        { params: { time_range: timeRange } }
      );
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  const timeRangeOptions = useMemo(
    () => [
      { value: '7d', label: t('providerComparison.timeRange.options.7d') },
      { value: '30d', label: t('providerComparison.timeRange.options.30d') },
      { value: '90d', label: t('providerComparison.timeRange.options.90d') },
      { value: 'all', label: t('providerComparison.timeRange.options.all') },
    ],
    [t]
  );

  const renderPlaceholder = (message: string) => (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-gray-600">{message}</div>
    </div>
  );

  const getProviderLabel = (provider: string) =>
    t(`providerComparison.providers.${provider}`, {
      defaultValue: provider,
    });

  if (isLoading) {
    return renderPlaceholder(t('providerComparison.loading'));
  }

  if (!comparison) {
    return renderPlaceholder(t('providerComparison.noData'));
  }

  const { metrics, task_distribution, recommendations, summary } = comparison;

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {t('providerComparison.title')}
          </h1>
          <p className="mt-2 text-gray-600">{t('providerComparison.subtitle')}</p>
        </div>

        {/* Time Range Filter */}
        <div className="w-48">
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRange)}
            label={t('providerComparison.timeRange.label')}
            options={timeRangeOptions}
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('providerComparison.summary.bestSuccess')}
              </p>
              <p className="text-2xl font-bold text-green-600">
                {summary.best_success_rate.value.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {getProviderLabel(summary.best_success_rate.provider)}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('providerComparison.summary.bestCost')}
              </p>
              <p className="text-2xl font-bold text-blue-600">
                ${summary.best_cost_efficiency.value.toFixed(3)}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {getProviderLabel(summary.best_cost_efficiency.provider)}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('providerComparison.summary.bestSpeed')}
              </p>
              <p className="text-2xl font-bold text-purple-600">
                {t('providerComparison.table.minutesSeconds', {
                  minutes: Math.floor(summary.best_speed.value / 60),
                  seconds: summary.best_speed.value % 60,
                })}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {getProviderLabel(summary.best_speed.provider)}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">
                {t('providerComparison.summary.recommended')}
              </p>
              <p className="text-xl font-bold text-yellow-600">
                {getProviderLabel(summary.recommended_provider)}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {t('providerComparison.summary.recommendedDescription')}
              </p>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
              <Award className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs for Different Views */}
      <Tabs defaultValue="overview" className="mb-8">
        <TabsList>
          <TabsTrigger value="overview">{t('providerComparison.tabs.overview')}</TabsTrigger>
          <TabsTrigger value="trends">{t('providerComparison.tabs.trends')}</TabsTrigger>
          <TabsTrigger value="distribution">
            {t('providerComparison.tabs.distribution')}
          </TabsTrigger>
          <TabsTrigger value="recommendations">
            {t('providerComparison.tabs.recommendations')}
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {t('providerComparison.sections.overview')}
            </h2>
            <MetricsComparisonTable metrics={metrics} highlightBest />
          </Card>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends">
          <div className="space-y-6">
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                {t('providerComparison.sections.successTrend')}
              </h2>
              <SuccessRateLineChart metrics={metrics} height={400} />
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  {t('providerComparison.sections.avgCost')}
                </h2>
                <CostComparisonBarChart
                  metrics={metrics}
                  height={300}
                  showTotalCost={false}
                />
              </Card>

              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  {t('providerComparison.sections.totalCost')}
                </h2>
                <CostComparisonBarChart
                  metrics={metrics}
                  height={300}
                  showTotalCost={true}
                />
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Distribution Tab */}
        <TabsContent value="distribution">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(task_distribution).map(([provider, distribution]) => (
              <Card key={provider} className="p-6">
                <TaskDistributionPieChart
                  distribution={distribution}
                  provider={provider as any}
                  height={300}
                />
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations">
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-1">
                {t('providerComparison.sections.recommendationIntroTitle')}
              </h3>
              <p className="text-sm text-blue-700">
                {t('providerComparison.sections.recommendationIntroDescription')}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {recommendations
                .sort((a, b) => b.score - a.score)
                .map((rec) => (
                  <RecommendationCard key={rec.provider} recommendation={rec} />
                ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
