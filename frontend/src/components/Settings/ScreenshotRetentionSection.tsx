/**
 * Screenshot Retention Section component.
 * Configure screenshot storage and retention policies.
 */

import { Card, Input } from '@/components/ui';
import { Camera, HardDrive } from 'lucide-react';
import { Controller, useFormContext } from 'react-hook-form';
import type { SettingsFormValues } from '@/schemas/settings-schema';
import { useTranslation } from 'react-i18next';

export interface ScreenshotRetentionSectionProps {
  estimatedStorageUsage?: number;
}

export const ScreenshotRetentionSection: React.FC<ScreenshotRetentionSectionProps> = ({
  estimatedStorageUsage = 0,
}) => {
  const { t } = useTranslation();
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
        {t('settings.screenshot.title')}
      </h2>

      <div className="space-y-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <HardDrive className="w-5 h-5 text-gray-500 mr-2" />
              <div>
                <p className="text-sm font-medium text-gray-700">
                  {t('settings.screenshot.usageTitle')}
                </p>
                <p className="text-xs text-gray-500">
                  {t('settings.screenshot.usageDescription')}
                </p>
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
            label={t('settings.screenshot.retentionDaysLabel')}
            min={1}
            max={365}
            helperText={t('settings.screenshot.retentionDaysHelper')}
            error={retentionErrors?.retention_days?.message as string | undefined}
            {...register('screenshot_retention.retention_days', { valueAsNumber: true })}
          />

          <Input
            type="number"
            label={t('settings.screenshot.maxPerTaskLabel')}
            min={1}
            max={100}
            helperText={t('settings.screenshot.maxPerTaskHelper')}
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
                  {t('settings.screenshot.compressToggle')}
                </label>
              </div>
            )}
          />

          {retention.compress_screenshots && (
            <Input
              type="number"
              label={t('settings.screenshot.qualityLabel')}
              min={10}
              max={100}
              step={10}
              helperText={t('settings.screenshot.qualityHelper')}
              error={
                retentionErrors?.compression_quality?.message as string | undefined
              }
              {...register('screenshot_retention.compression_quality', {
                valueAsNumber: true,
              })}
            />
          )}

          <div className="border-t border-gray-200 pt-4">
            <p className="text-sm font-medium text-gray-700 mb-3">
              {t('settings.screenshot.policyTitle')}
            </p>

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
                    {t('settings.screenshot.deleteOnSuccess')}
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
                    {t('settings.screenshot.deleteOnFailure')}
                  </label>
                </div>
              )}
            />

            <p className="mt-2 ml-6 text-xs text-gray-500">
              {t('settings.screenshot.failureNote')}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};
