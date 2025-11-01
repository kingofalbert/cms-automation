/**
 * Worklist Statistics component.
 * Displays statistics cards for worklist overview.
 */

import { WorklistStatistics as Stats } from '@/types/worklist';
import { Card } from '@/components/ui';
import { FileText, Clock, TrendingUp, BarChart3 } from 'lucide-react';

export interface WorklistStatisticsProps {
  statistics: Stats;
}

export const WorklistStatistics: React.FC<WorklistStatisticsProps> = ({
  statistics,
}) => {
  const formatTime = (hours: number) => {
    if (hours < 24) {
      return `${hours.toFixed(1)} 小时`;
    }
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return `${days} 天 ${remainingHours.toFixed(0)} 小时`;
  };

  // Calculate average cycle time (from to_evaluate to published)
  const avgCycleTime =
    statistics.avg_time_per_status.to_evaluate +
    statistics.avg_time_per_status.to_confirm +
    statistics.avg_time_per_status.to_review +
    statistics.avg_time_per_status.to_revise +
    statistics.avg_time_per_status.to_rereview +
    statistics.avg_time_per_status.ready_to_publish;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Total Items */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">总文章数</p>
            <p className="text-2xl font-bold text-gray-900">{statistics.total}</p>
            <p className="text-xs text-gray-600 mt-1">
              {statistics.total_word_count.toLocaleString()} 字
            </p>
          </div>
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
        </div>
      </Card>

      {/* Ready to Publish */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">待发布</p>
            <p className="text-2xl font-bold text-green-600">
              {statistics.by_status.ready_to_publish}
            </p>
            <p className="text-xs text-gray-600 mt-1">可立即发布</p>
          </div>
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-green-600" />
          </div>
        </div>
      </Card>

      {/* Average Cycle Time */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">平均周期</p>
            <p className="text-lg font-bold text-purple-600">
              {formatTime(avgCycleTime)}
            </p>
            <p className="text-xs text-gray-600 mt-1">从评估到发布</p>
          </div>
          <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
            <Clock className="w-6 h-6 text-purple-600" />
          </div>
        </div>
      </Card>

      {/* Average Quality Score */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">平均质量</p>
            <p className="text-2xl font-bold text-yellow-600">
              {statistics.avg_quality_score.toFixed(1)}
            </p>
            <p className="text-xs text-gray-600 mt-1">满分 100</p>
          </div>
          <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-yellow-600" />
          </div>
        </div>
      </Card>
    </div>
  );
};
