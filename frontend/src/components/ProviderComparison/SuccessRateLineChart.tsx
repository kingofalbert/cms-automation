/**
 * Success Rate Line Chart component.
 * Displays success rate trends over time for different providers.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ProviderMetrics, ChartDataPoint } from '@/types/analytics';
import { format, parseISO } from 'date-fns';

export interface SuccessRateLineChartProps {
  metrics: ProviderMetrics[];
  height?: number;
}

export const SuccessRateLineChart: React.FC<SuccessRateLineChartProps> = ({
  metrics,
  height = 300,
}) => {
  // Transform data for Recharts
  const chartData: ChartDataPoint[] = [];

  if (metrics.length === 0 || metrics[0]?.last_30_days?.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        暂无数据
      </div>
    );
  }

  // Get all unique dates
  const allDates = new Set<string>();
  metrics.forEach((metric) => {
    metric.last_30_days.forEach((daily) => {
      allDates.add(daily.date);
    });
  });

  // Sort dates
  const sortedDates = Array.from(allDates).sort();

  // Build chart data
  sortedDates.forEach((date) => {
    const dataPoint: ChartDataPoint = { date };

    metrics.forEach((metric) => {
      const dailyData = metric.last_30_days.find((d) => d.date === date);
      dataPoint[metric.provider] = dailyData?.success_rate || 0;
    });

    chartData.push(dataPoint);
  });

  const colors = {
    playwright: '#3b82f6', // blue
    computer_use: '#10b981', // green
    hybrid: '#8b5cf6', // purple
  };

  const formatXAxis = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), 'MM-dd');
    } catch {
      return dateStr;
    }
  };

  const formatTooltip = (value: number) => `${value.toFixed(1)}%`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="date"
          tickFormatter={formatXAxis}
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
        />
        <YAxis
          domain={[0, 100]}
          tickFormatter={(value) => `${value}%`}
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
        />
        <Tooltip
          formatter={formatTooltip}
          labelFormatter={(label) => `日期: ${label}`}
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: '14px' }}
          formatter={(value) => {
            const labels: Record<string, string> = {
              playwright: 'Playwright',
              computer_use: 'Computer Use',
              hybrid: 'Hybrid',
            };
            return labels[value] || value;
          }}
        />
        {metrics.map((metric) => (
          <Line
            key={metric.provider}
            type="monotone"
            dataKey={metric.provider}
            stroke={colors[metric.provider as keyof typeof colors] || '#6b7280'}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};
