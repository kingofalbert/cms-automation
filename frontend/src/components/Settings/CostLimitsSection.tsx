/**
 * Cost Limits Section component.
 * Configure cost limits and alerts.
 */

import { Card, Input } from '@/components/ui';
import { DollarSign, AlertTriangle } from 'lucide-react';
import { Controller, useFormContext } from 'react-hook-form';
import type { SettingsFormValues } from '@/schemas/settings-schema';

export interface CostLimitsSectionProps {
  currentDailySpend?: number;
  currentMonthlySpend?: number;
}

export const CostLimitsSection: React.FC<CostLimitsSectionProps> = ({
  currentDailySpend = 0,
  currentMonthlySpend = 0,
}) => {
  const {
    register,
    control,
    watch,
    formState: { errors },
  } = useFormContext<SettingsFormValues>();

  const limits = watch('cost_limits');
  const limitErrors = errors.cost_limits;

  const dailyPercentage =
    limits.daily_limit > 0 ? (currentDailySpend / limits.daily_limit) * 100 : 0;
  const monthlyPercentage =
    limits.monthly_limit > 0 ? (currentMonthlySpend / limits.monthly_limit) * 100 : 0;

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= limits.alert_threshold) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
        <DollarSign className="w-6 h-6 mr-2" />
        成本限额
      </h2>

      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">当前使用情况</h3>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">今日消费</span>
                <span className="font-medium">
                  ${currentDailySpend.toFixed(2)} / ${limits.daily_limit.toFixed(2)}
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

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">本月消费</span>
                <span className="font-medium">
                  ${currentMonthlySpend.toFixed(2)} / ${limits.monthly_limit.toFixed(2)}
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

          {(dailyPercentage >= limits.alert_threshold ||
            monthlyPercentage >= limits.alert_threshold) && (
            <div className="mt-3 flex items-start rounded-lg border border-yellow-200 bg-yellow-50 p-3">
              <AlertTriangle className="mr-2 mt-0.5 h-5 w-5 text-yellow-600" />
              <div className="text-sm text-yellow-700">
                <p className="font-medium">成本预警</p>
                <p>
                  {dailyPercentage >= limits.alert_threshold &&
                    `今日消费已达 ${dailyPercentage.toFixed(1)}%。`}
                  {monthlyPercentage >= limits.alert_threshold &&
                    `本月消费已达 ${monthlyPercentage.toFixed(1)}%。`}
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <Input
            type="number"
            label="每日限额 (USD)"
            min={0}
            step={0.01}
            helperText="每日最大消费金额"
            error={limitErrors?.daily_limit?.message as string | undefined}
            {...register('cost_limits.daily_limit', { valueAsNumber: true })}
          />

          <Input
            type="number"
            label="每月限额 (USD)"
            min={0}
            step={0.01}
            helperText="每月最大消费金额"
            error={limitErrors?.monthly_limit?.message as string | undefined}
            {...register('cost_limits.monthly_limit', { valueAsNumber: true })}
          />

          <Input
            type="number"
            label="单任务限额 (USD)"
            min={0}
            step={0.01}
            helperText="单个发布任务的最大消费金额"
            error={limitErrors?.per_task_limit?.message as string | undefined}
            {...register('cost_limits.per_task_limit', { valueAsNumber: true })}
          />

          <Input
            type="number"
            label="预警阈值 (%)"
            min={0}
            max={100}
            helperText="达到此百分比时发送预警"
            error={limitErrors?.alert_threshold?.message as string | undefined}
            {...register('cost_limits.alert_threshold', { valueAsNumber: true })}
          />

          <Controller
            name="cost_limits.auto_pause_on_limit"
            control={control}
            render={({ field }) => (
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto-pause"
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  checked={field.value}
                  onChange={(event) => field.onChange(event.target.checked)}
                />
                <label htmlFor="auto-pause" className="ml-2 text-sm text-gray-700">
                  达到限额时自动暂停发布
                </label>
              </div>
            )}
          />
        </div>
      </div>
    </Card>
  );
};
