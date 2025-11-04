/**
 * Cost Limits Section component.
 * Configure cost limits and alerts.
 */

import { CostLimits } from '@/types/settings';
import { Card, Input } from '@/components/ui';
import { DollarSign, AlertTriangle } from 'lucide-react';

export interface CostLimitsSectionProps {
  limits: CostLimits;
  onChange: (limits: CostLimits) => void;
  currentDailySpend?: number;
  currentMonthlySpend?: number;
}

export const CostLimitsSection: React.FC<CostLimitsSectionProps> = ({
  limits,
  onChange,
  currentDailySpend = 0,
  currentMonthlySpend = 0,
}) => {
  // Provide safe defaults for when backend returns empty objects
  const safeLimits = {
    daily_limit: limits.daily_limit ?? 100,
    monthly_limit: limits.monthly_limit ?? 3000,
    per_task_limit: limits.per_task_limit ?? 10,
    alert_threshold: limits.alert_threshold ?? 80,
    auto_pause_on_limit: limits.auto_pause_on_limit ?? true,
  };

  const updateLimits = (updates: Partial<CostLimits>) => {
    onChange({ ...safeLimits, ...updates });
  };

  const dailyPercentage = (currentDailySpend / safeLimits.daily_limit) * 100;
  const monthlyPercentage = (currentMonthlySpend / safeLimits.monthly_limit) * 100;

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= safeLimits.alert_threshold) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
        <DollarSign className="w-6 h-6 mr-2" />
        成本限额
      </h2>

      <div className="space-y-6">
        {/* Current Usage */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">当前使用情况</h3>

          <div className="space-y-3">
            {/* Daily Usage */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">今日消费</span>
                <span className="font-medium">
                  ${currentDailySpend.toFixed(2)} / ${safeLimits.daily_limit.toFixed(2)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${getProgressColor(
                    dailyPercentage
                  )}`}
                  style={{ width: `${Math.min(dailyPercentage, 100)}%` }}
                />
              </div>
            </div>

            {/* Monthly Usage */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">本月消费</span>
                <span className="font-medium">
                  ${currentMonthlySpend.toFixed(2)} / ${safeLimits.monthly_limit.toFixed(2)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${getProgressColor(
                    monthlyPercentage
                  )}`}
                  style={{ width: `${Math.min(monthlyPercentage, 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Alert */}
          {(dailyPercentage >= safeLimits.alert_threshold ||
            monthlyPercentage >= safeLimits.alert_threshold) && (
            <div className="mt-3 flex items-start p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
              <div className="text-sm text-yellow-700">
                <p className="font-medium">成本预警</p>
                <p>
                  {dailyPercentage >= safeLimits.alert_threshold &&
                    `今日消费已达 ${dailyPercentage.toFixed(1)}%。`}
                  {monthlyPercentage >= safeLimits.alert_threshold &&
                    `本月消费已达 ${monthlyPercentage.toFixed(1)}%。`}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Limit Configuration */}
        <div className="space-y-4">
          <Input
            type="number"
            label="每日限额 (USD)"
            value={safeLimits.daily_limit}
            onChange={(e) =>
              updateLimits({ daily_limit: parseFloat(e.target.value) })
            }
            min={0}
            step={0.01}
            helperText="每日最大消费金额"
          />

          <Input
            type="number"
            label="每月限额 (USD)"
            value={safeLimits.monthly_limit}
            onChange={(e) =>
              updateLimits({ monthly_limit: parseFloat(e.target.value) })
            }
            min={0}
            step={0.01}
            helperText="每月最大消费金额"
          />

          <Input
            type="number"
            label="单任务限额 (USD)"
            value={safeLimits.per_task_limit}
            onChange={(e) =>
              updateLimits({ per_task_limit: parseFloat(e.target.value) })
            }
            min={0}
            step={0.01}
            helperText="单个发布任务的最大消费金额"
          />

          <Input
            type="number"
            label="预警阈值 (%)"
            value={safeLimits.alert_threshold}
            onChange={(e) =>
              updateLimits({ alert_threshold: parseInt(e.target.value) })
            }
            min={0}
            max={100}
            helperText="达到此百分比时发送预警"
          />

          <div className="flex items-center">
            <input
              type="checkbox"
              id="auto-pause"
              checked={safeLimits.auto_pause_on_limit}
              onChange={(e) =>
                updateLimits({ auto_pause_on_limit: e.target.checked })
              }
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <label htmlFor="auto-pause" className="ml-2 text-sm text-gray-700">
              达到限额时自动暂停发布
            </label>
          </div>
        </div>
      </div>
    </Card>
  );
};
