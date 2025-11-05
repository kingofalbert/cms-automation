/**
 * Provider Configuration Section component.
 * Configure settings for different publishing providers.
 */

import { Card, Input, Select, Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui';
import { Controller, useFormContext } from 'react-hook-form';
import type { SettingsFormValues } from '@/schemas/settings-schema';

const browserOptions = [
  { value: 'chromium', label: 'Chromium' },
  { value: 'firefox', label: 'Firefox' },
  { value: 'webkit', label: 'WebKit' },
];

const primaryProviderOptions = [
  { value: 'playwright', label: 'Playwright' },
  { value: 'computer_use', label: 'Computer Use' },
];

export const ProviderConfigSection: React.FC = () => {
  const { register, control, formState: { errors } } = useFormContext<SettingsFormValues>();

  const providerErrors = errors.provider_config;

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Provider 配置</h2>

      <Tabs defaultValue="playwright">
        <TabsList>
          <TabsTrigger value="playwright">Playwright</TabsTrigger>
          <TabsTrigger value="computer_use">Computer Use</TabsTrigger>
          <TabsTrigger value="hybrid">Hybrid</TabsTrigger>
        </TabsList>

        <TabsContent value="playwright">
          <div className="space-y-4">
            <Controller
              name="provider_config.playwright.enabled"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="playwright-enabled"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="playwright-enabled" className="ml-2 text-sm text-gray-700">
                    启用 Playwright Provider
                  </label>
                </div>
              )}
            />

            <Controller
              name="provider_config.playwright.headless"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="playwright-headless"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="playwright-headless" className="ml-2 text-sm text-gray-700">
                    无头模式 (Headless)
                  </label>
                </div>
              )}
            />

            <Controller
              name="provider_config.playwright.screenshot_on_error"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="playwright-screenshot"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="playwright-screenshot" className="ml-2 text-sm text-gray-700">
                    错误时截图
                  </label>
                </div>
              )}
            />

            <Select
              label="浏览器"
              options={browserOptions}
              placeholder="选择浏览器"
              error={providerErrors?.playwright?.browser?.message as string | undefined}
              {...register('provider_config.playwright.browser')}
            />

            <Input
              type="number"
              label="超时时间 (毫秒)"
              min={1000}
              max={120000}
              error={providerErrors?.playwright?.timeout?.message as string | undefined}
              {...register('provider_config.playwright.timeout', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label="重试次数"
              min={0}
              max={5}
              error={providerErrors?.playwright?.retry_count?.message as string | undefined}
              {...register('provider_config.playwright.retry_count', {
                valueAsNumber: true,
              })}
            />
          </div>
        </TabsContent>

        <TabsContent value="computer_use">
          <div className="space-y-4">
            <Controller
              name="provider_config.computer_use.enabled"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="computer-use-enabled"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="computer-use-enabled" className="ml-2 text-sm text-gray-700">
                    启用 Computer Use Provider
                  </label>
                </div>
              )}
            />

            <Input
              type="text"
              label="模型"
              disabled
              helperText="Computer Use API 目前仅支持 claude-3-5-sonnet-20241022 (由 Anthropic API 限制)"
              error={providerErrors?.computer_use?.model?.message as string | undefined}
              {...register('provider_config.computer_use.model')}
            />

            <Input
              type="number"
              label="最大 Tokens"
              min={1024}
              max={32768}
              error={providerErrors?.computer_use?.max_tokens?.message as string | undefined}
              {...register('provider_config.computer_use.max_tokens', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label="超时时间 (毫秒)"
              min={1000}
              max={300000}
              error={providerErrors?.computer_use?.timeout?.message as string | undefined}
              {...register('provider_config.computer_use.timeout', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label="截图间隔 (毫秒)"
              min={1000}
              max={600000}
              helperText="Computer Use 执行时的截图间隔"
              error={
                providerErrors?.computer_use?.screenshot_interval?.message as string | undefined
              }
              {...register('provider_config.computer_use.screenshot_interval', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label="重试次数"
              min={0}
              max={5}
              error={providerErrors?.computer_use?.retry_count?.message as string | undefined}
              {...register('provider_config.computer_use.retry_count', {
                valueAsNumber: true,
              })}
            />
          </div>
        </TabsContent>

        <TabsContent value="hybrid">
          <div className="space-y-4">
            <Controller
              name="provider_config.hybrid.enabled"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="hybrid-enabled"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="hybrid-enabled" className="ml-2 text-sm text-gray-700">
                    启用 Hybrid Provider
                  </label>
                </div>
              )}
            />

            <Select
              label="主 Provider"
              options={primaryProviderOptions}
              placeholder="选择主 Provider"
              error={providerErrors?.hybrid?.primary_provider?.message as string | undefined}
              {...register('provider_config.hybrid.primary_provider')}
            />

            <Controller
              name="provider_config.hybrid.fallback_enabled"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="hybrid-fallback-enabled"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label htmlFor="hybrid-fallback-enabled" className="ml-2 text-sm text-gray-700">
                    启用自动回退
                  </label>
                </div>
              )}
            />

            <Controller
              name="provider_config.hybrid.fallback_on_error"
              control={control}
              render={({ field }) => (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="hybrid-fallback-on-error"
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    checked={field.value}
                    onChange={(event) => field.onChange(event.target.checked)}
                  />
                  <label
                    htmlFor="hybrid-fallback-on-error"
                    className="ml-2 text-sm text-gray-700"
                  >
                    错误时自动回退
                  </label>
                </div>
              )}
            />

            <Input
              type="number"
              label="自动切换阈值 (%)"
              min={0}
              max={100}
              helperText="低于指定成功率时自动切换 Provider"
              error={
                providerErrors?.hybrid?.auto_switch_threshold?.message as string | undefined
              }
              {...register('provider_config.hybrid.auto_switch_threshold', {
                valueAsNumber: true,
              })}
            />
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
};
