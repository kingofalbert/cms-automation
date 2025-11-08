/**
 * Task Distribution Pie Chart component.
 * Displays task distribution by status for a specific provider.
 */

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  type PieLabelRenderProps,
} from 'recharts';
import { TaskDistribution } from '@/types/analytics';
import { ProviderType } from '@/types/publishing';
import { useTranslation } from 'react-i18next';

export interface TaskDistributionPieChartProps {
  distribution: TaskDistribution[];
  provider: ProviderType;
  height?: number;
}

export const TaskDistributionPieChart: React.FC<TaskDistributionPieChartProps> = ({
  distribution,
  provider,
  height = 300,
}) => {
  const { t } = useTranslation();

  if (distribution.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        {t('providerComparison.noData')}
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = distribution.map((item) => ({
    name: getStatusLabel(item.status),
    value: item.count,
    percentage: item.percentage,
  }));

  // Color mapping for different statuses
  const COLORS = {
    completed: '#10b981', // green
    failed: '#ef4444', // red
    pending: '#f59e0b', // amber
    initializing: '#3b82f6', // blue
    logging_in: '#3b82f6',
    creating_post: '#3b82f6',
    uploading_images: '#3b82f6',
    configuring_seo: '#3b82f6',
    publishing: '#8b5cf6', // purple
    idle: '#6b7280', // gray
  };

  const getStatusColor = (status: string) => {
    return COLORS[status as keyof typeof COLORS] || '#6b7280';
  };

  const getStatusLabel = (status: string) =>
    t(`publishTasks.statusLabels.${status}`, {
      defaultValue: t(`providerComparison.statuses.${status}`, {
        defaultValue: status,
      }),
    });

  const getProviderLabel = (value: string) =>
    t(`providerComparison.providers.${value}`, {
      defaultValue: value,
    });

  const renderCustomLabel = (props: PieLabelRenderProps) => {
    const {
      cx = 0,
      cy = 0,
      midAngle = 0,
      innerRadius = 0,
      outerRadius = 0,
      percent = 0,
    } = props;
    const RADIAN = Math.PI / 180;
    const radius = Number(innerRadius) + (Number(outerRadius) - Number(innerRadius)) * 0.5;
    const x = Number(cx) + radius * Math.cos(-Number(midAngle) * RADIAN);
    const y = Number(cy) + radius * Math.sin(-Number(midAngle) * RADIAN);

    if (Number(percent) < 0.05) return null; // Don't show label for < 5%

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > Number(cx) ? 'start' : 'end'}
        dominantBaseline="central"
        style={{ fontSize: '12px', fontWeight: 'bold' }}
      >
        {`${(Number(percent) * 100).toFixed(0)}%`}
      </text>
    );
  };

  const renderTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const [firstPayload] = payload;
      const value =
        typeof firstPayload?.value === 'number'
          ? firstPayload.value
          : Number(firstPayload?.value ?? 0);
      const dataPoint = firstPayload?.payload as (typeof chartData)[number] | undefined;

      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-sm">
          <p className="text-sm font-medium text-gray-900">{firstPayload?.name}</p>
          <p className="text-sm text-gray-600">
            {t('providerComparison.charts.tooltip.tasks')}: {value}
          </p>
          {dataPoint && (
            <p className="text-sm text-gray-600">
              {t('providerComparison.charts.tooltip.share')}: {dataPoint.percentage.toFixed(1)}%
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <h3 className="text-center text-sm font-medium text-gray-700 mb-2">
        {t('providerComparison.charts.distributionTitle', {
          provider: getProviderLabel(provider),
        })}
      </h3>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((_entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getStatusColor(distribution[index].status)}
              />
            ))}
          </Pie>
          <Tooltip content={renderTooltip} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="circle"
            layout="vertical"
            align="right"
            verticalAlign="middle"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
