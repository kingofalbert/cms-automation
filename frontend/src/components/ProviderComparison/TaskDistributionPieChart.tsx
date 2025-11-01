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
} from 'recharts';
import { TaskDistribution } from '@/types/analytics';
import { ProviderType } from '@/types/publishing';

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
  if (distribution.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        暂无数据
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

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      completed: '已完成',
      failed: '失败',
      pending: '待处理',
      initializing: '初始化中',
      logging_in: '登录中',
      creating_post: '创建文章',
      uploading_images: '上传图片',
      configuring_seo: '配置SEO',
      publishing: '发布中',
      idle: '空闲',
    };
    return labels[status] || status;
  };

  const getProviderLabel = (provider: string) => {
    const labels: Record<string, string> = {
      playwright: 'Playwright',
      computer_use: 'Computer Use',
      hybrid: 'Hybrid',
    };
    return labels[provider] || provider;
  };

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percent < 0.05) return null; // Don't show label for < 5%

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        style={{ fontSize: '12px', fontWeight: 'bold' }}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  const renderTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-sm">
          <p className="text-sm font-medium text-gray-900">{payload[0].name}</p>
          <p className="text-sm text-gray-600">
            任务数: {payload[0].value}
          </p>
          <p className="text-sm text-gray-600">
            占比: {payload[0].payload.percentage.toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <h3 className="text-center text-sm font-medium text-gray-700 mb-2">
        {getProviderLabel(provider)} 任务分布
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
