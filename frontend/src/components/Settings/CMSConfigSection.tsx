/**
 * CMS Configuration Section component.
 * Configure WordPress/CMS connection settings.
 */

import { useState } from 'react';
import { Card, Input, Button } from '@/components/ui';
import { CheckCircle, Eye, EyeOff, XCircle } from 'lucide-react';
import { Controller, useFormContext } from 'react-hook-form';
import type { SettingsFormValues } from '@/schemas/settings-schema';

export interface CMSConfigSectionProps {
  onTestConnection?: (payload: SettingsFormValues['cms_config']) => Promise<boolean>;
}

export const CMSConfigSection: React.FC<CMSConfigSectionProps> = ({
  onTestConnection,
}) => {
  const {
    register,
    control,
    watch,
    formState: { errors },
  } = useFormContext<SettingsFormValues>();

  const cmsConfig = watch('cms_config');

  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const handleTestConnection = async () => {
    if (!onTestConnection) return;

    setTesting(true);
    setTestResult(null);

    try {
      const success = await onTestConnection({
        wordpress_url: cmsConfig.wordpress_url,
        username: cmsConfig.username,
        password: cmsConfig.password,
        verify_ssl: cmsConfig.verify_ssl,
        timeout: cmsConfig.timeout,
        max_retries: cmsConfig.max_retries,
      });
      setTestResult(success ? 'success' : 'error');
    } catch {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">WordPress 连接配置</h2>

      <div className="space-y-4">
        <Input
          type="url"
          label="WordPress URL"
          placeholder="https://example.com"
          required
          error={errors.cms_config?.wordpress_url?.message as string | undefined}
          {...register('cms_config.wordpress_url')}
        />

        <Input
          type="text"
          label="用户名"
          required
          error={errors.cms_config?.username?.message as string | undefined}
          {...register('cms_config.username')}
        />

        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            label="密码"
            required
            error={errors.cms_config?.password?.message as string | undefined}
            {...register('cms_config.password')}
          />
          <button
            type="button"
            onClick={() => setShowPassword((previous) => !previous)}
            className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>

        <Controller
          name="cms_config.verify_ssl"
          control={control}
          render={({ field }) => (
            <div className="flex items-center">
              <input
                type="checkbox"
                id="verify-ssl"
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                checked={field.value}
                onChange={(event) => field.onChange(event.target.checked)}
              />
              <label htmlFor="verify-ssl" className="ml-2 text-sm text-gray-700">
                验证 SSL 证书
              </label>
            </div>
          )}
        />

        <Input
          type="number"
          label="超时时间 (毫秒)"
          min={1000}
          max={120000}
          error={errors.cms_config?.timeout?.message as string | undefined}
          {...register('cms_config.timeout', { valueAsNumber: true })}
        />

        <Input
          type="number"
          label="最大重试次数"
          min={0}
          max={5}
          error={errors.cms_config?.max_retries?.message as string | undefined}
          {...register('cms_config.max_retries', { valueAsNumber: true })}
        />

        <div className="pt-4 border-t border-gray-200">
          <Button
            variant="outline"
            onClick={handleTestConnection}
            disabled={
              testing ||
              !cmsConfig.wordpress_url ||
              !cmsConfig.username ||
              !cmsConfig.password
            }
            className="w-full"
          >
            {testing ? '测试中...' : '测试连接'}
          </Button>

          {testResult && (
            <div
              className={`mt-3 flex items-center rounded-lg border p-3 ${
                testResult === 'success'
                  ? 'border-green-200 bg-green-50'
                  : 'border-red-200 bg-red-50'
              }`}
            >
              {testResult === 'success' ? (
                <>
                  <CheckCircle className="mr-2 h-5 w-5 text-green-600" />
                  <span className="text-sm text-green-700">连接成功！WordPress 配置正确。</span>
                </>
              ) : (
                <>
                  <XCircle className="mr-2 h-5 w-5 text-red-600" />
                  <span className="text-sm text-red-700">
                    连接失败。请检查 URL、用户名和密码是否正确。
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
