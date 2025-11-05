/**
 * Screenshot Retention Section component.
 * Configure screenshot storage and retention policies.
 */

import { Card, Input } from '@/components/ui';
import { Camera, HardDrive } from 'lucide-react';
import { Controller, useFormContext } from 'react-hook-form';
import type { SettingsFormValues } from '@/schemas/settings-schema';

export interface ScreenshotRetentionSectionProps {
  estimatedStorageUsage?: number;
}

export const ScreenshotRetentionSection: React.FC<ScreenshotRetentionSectionProps> = ({
  estimatedStorageUsage = 0,
}) => {
  const {
    register,
    control,
    watch,
    formState: { errors },
  } = useFormContext<SettingsFormValues>();

  const retention = watch('screenshot_retention');
  const retentionErrors = errors.screenshot_retention;

  const formatStorage = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
        <Camera className="w-6 h-6 mr-2" />
        截图保留策略
      </h2>

      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <HardDrive className="w-5 h-5 text-gray-500 mr-2" />
              <div>
                <p className="text-sm font-medium text-gray-700">当前存储使用</p>
                <p className="text-xs text-gray-500">所有截图占用的存储空间</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-primary-600">
                {formatStorage(estimatedStorageUsage)}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <Input
            type="number"
            label="保留天数"
            min={1}
            max={365}
            helperText="超过此天数的截图将被自动删除"
            error={retentionErrors?.retention_days?.message as string | undefined}
            {...register('screenshot_retention.retention_days', { valueAsNumber: true })}
          />

          <Input
            type="number"
            label="每任务最大截图数"
            min={1}
            max={100}
            helperText="单个任务保留的最大截图数量"
            error={
              retentionErrors?.max_screenshots_per_task?.message as string | undefined
            }
            {...register('screenshot_retention.max_screenshots_per_task', {
              valueAsNumber: true,
            })}
          />

          <Controller
            name="screenshot_retention.compress_screenshots"
            control={control}
            render={({ field }) => (
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="compress-screenshots"
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  checked={field.value}
                  onChange={(event) => field.onChange(event.target.checked)}
                />
                <label htmlFor="compress-screenshots" className="ml-2 text-sm text-gray-700">
                  压缩截图 (节省存储空间)
                </label>
              </div>
            )}
          />

          {retention.compress_screenshots && (
            <Input
              type="number"
              label="压缩质量 (%)"
              min={10}
              max={100}
              step={10}
              helperText="质量越高，文件越大。推荐 70-80"
              error={
                retentionErrors?.compression_quality?.message as string | undefined
              }
              {...register('screenshot_retention.compression_quality', {
                valueAsNumber: true,
              })}
            />
          )}

          <div className="border-t border-gray-200 pt-4">
            <p className="text-sm font-medium text-gray-700 mb-3">自动删除策略</p>

            <Controller
              name="screenshot_retention.delete_on_success"
              control={control}
              render={({ field }) => (
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="delete-on-success"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="delete-on-success" className="text-sm text-gray-700">
                    任务成功后删除截图
                  </label>
                </div>
              )}
            />

            <Controller
              name="screenshot_retention.delete_on_failure"
              control={control}
              render={({ field }) => (
                <div className="mt-2 flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="delete-on-failure"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="delete-on-failure" className="text-sm text-gray-700">
                    任务失败后删除截图
                  </label>
                </div>
              )}
            />

            <p className="mt-2 ml-6 text-xs text-gray-500">
              注意：保留失败任务的截图有助于问题排查
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};
