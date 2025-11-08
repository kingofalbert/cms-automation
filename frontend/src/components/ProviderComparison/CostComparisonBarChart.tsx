/**
 * Cost Comparison Bar Chart component.
 * Displays cost metrics comparison across providers.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { ProviderMetrics } from '@/types/analytics';
import { useTranslation } from 'react-i18next';

export interface CostComparisonBarChartProps {
  metrics: ProviderMetrics[];
  height?: number;
  showTotalCost?: boolean;
}

export const CostComparisonBarChart: React.FC<CostComparisonBarChartProps> = ({
  metrics,
  height = 300,
  showTotalCost = false,
}) => {
  const { t } = useTranslation();

  if (metrics.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        {t('providerComparison.noData')}
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = metrics.map((metric) => ({
    name: getProviderLabel(metric.provider),
    avgCost: metric.avg_cost,
    totalCost: metric.total_cost,
    provider: metric.provider,
  }));

  const colors = {
    playwright: '#3b82f6', // blue
    computer_use: '#10b981', // green
    hybrid: '#8b5cf6', // purple
  };

  const getProviderLabel = (provider: string) =>
    t(`providerComparison.providers.${provider}`, { defaultValue: provider });

  const formatCost = (value: number) => `$${value.toFixed(3)}`;
  const formatTotalCost = (value: number) => `$${value.toFixed(2)}`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="name"
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
        />
        <YAxis
          tickFormatter={showTotalCost ? formatTotalCost : formatCost}
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
        />
        <Tooltip
          formatter={showTotalCost ? formatTotalCost : formatCost}
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: '14px' }}
          formatter={() =>
            showTotalCost
              ? t('providerComparison.charts.legend.totalCost')
              : t('providerComparison.charts.legend.avgCost')
          }
        />
        <Bar
          dataKey={showTotalCost ? 'totalCost' : 'avgCost'}
          radius={[4, 4, 0, 0]}
        >
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={colors[entry.provider as keyof typeof colors] || '#6b7280'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
