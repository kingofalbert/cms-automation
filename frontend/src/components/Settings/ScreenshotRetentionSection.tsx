/**
 * Screenshot Retention Section component.
 * Configure screenshot storage and retention policies.
 */

import { ScreenshotRetention } from '@/types/settings';
import { Card, Input } from '@/components/ui';
import { Camera, HardDrive } from 'lucide-react';

export interface ScreenshotRetentionSectionProps {
  retention: ScreenshotRetention;
  onChange: (retention: ScreenshotRetention) => void;
  estimatedStorageUsage?: number; // MB
}

export const ScreenshotRetentionSection: React.FC<
  ScreenshotRetentionSectionProps
> = ({ retention, onChange, estimatedStorageUsage = 0 }) => {
  const updateRetention = (updates: Partial<ScreenshotRetention>) => {
    onChange({ ...retention, ...updates });
  };

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
        {/* Storage Usage */}
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

        {/* Retention Settings */}
        <div className="space-y-4">
          <Input
            type="number"
            label="保留天数"
            value={retention.retention_days}
            onChange={(e) =>
              updateRetention({ retention_days: parseInt(e.target.value) })
            }
            min={1}
            max={365}
            helperText="超过此天数的截图将被自动删除"
          />

          <Input
            type="number"
            label="每任务最大截图数"
            value={retention.max_screenshots_per_task}
            onChange={(e) =>
              updateRetention({
                max_screenshots_per_task: parseInt(e.target.value),
              })
            }
            min={1}
            max={100}
            helperText="单个任务保留的最大截图数量"
          />

          <div className="flex items-center">
            <input
              type="checkbox"
              id="compress-screenshots"
              checked={retention.compress_screenshots}
              onChange={(e) =>
                updateRetention({ compress_screenshots: e.target.checked })
              }
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <label
              htmlFor="compress-screenshots"
              className="ml-2 text-sm text-gray-700"
            >
              压缩截图 (节省存储空间)
            </label>
          </div>

          {retention.compress_screenshots && (
            <Input
              type="number"
              label="压缩质量 (%)"
              value={retention.compression_quality}
              onChange={(e) =>
                updateRetention({ compression_quality: parseInt(e.target.value) })
              }
              min={10}
              max={100}
              step={10}
              helperText="质量越高，文件越大。推荐 70-80"
            />
          )}

          <div className="pt-4 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-700 mb-3">
              自动删除策略
            </p>

            <div className="space-y-2">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="delete-on-success"
                  checked={retention.delete_on_success}
                  onChange={(e) =>
                    updateRetention({ delete_on_success: e.target.checked })
                  }
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <label
                  htmlFor="delete-on-success"
                  className="ml-2 text-sm text-gray-700"
                >
                  任务成功后删除截图
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="delete-on-failure"
                  checked={retention.delete_on_failure}
                  onChange={(e) =>
                    updateRetention({ delete_on_failure: e.target.checked })
                  }
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <label
                  htmlFor="delete-on-failure"
                  className="ml-2 text-sm text-gray-700"
                >
                  任务失败后删除截图
                </label>
              </div>

              <p className="text-xs text-gray-500 mt-2 ml-6">
                注意：保留失败任务的截图有助于问题排查
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
