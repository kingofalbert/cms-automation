/**
 * Provider Configuration Section component.
 * Configure settings for different publishing providers.
 */

import { Card, Input, Select, Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui';
import { Controller, useFormContext } from 'react-hook-form';
import type { SettingsFormValues } from '@/schemas/settings-schema';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
  const { register, control, formState: { errors } } = useFormContext<SettingsFormValues>();

  const providerErrors = errors.provider_config;

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        {t('settings.provider.title')}
      </h2>

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
                    {t('settings.provider.playwright.enable')}
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
                    {t('settings.provider.playwright.headless')}
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
                    {t('settings.provider.playwright.screenshotOnError')}
                  </label>
                </div>
              )}
            />

            <Select
              label={t('settings.provider.playwright.browserLabel')}
              options={browserOptions}
              placeholder={t('settings.provider.playwright.browserPlaceholder')}
              error={providerErrors?.playwright?.browser?.message as string | undefined}
              {...register('provider_config.playwright.browser')}
            />

            <Input
              type="number"
              label={t('settings.provider.playwright.timeoutLabel')}
              min={1000}
              max={120000}
              error={providerErrors?.playwright?.timeout?.message as string | undefined}
              {...register('provider_config.playwright.timeout', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label={t('settings.provider.playwright.retryLabel')}
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
                    {t('settings.provider.computerUse.enable')}
                  </label>
                </div>
              )}
            />

            <Input
              type="text"
              label={t('settings.provider.computerUse.modelLabel')}
              disabled
              helperText={t('settings.provider.computerUse.modelHelper')}
              error={providerErrors?.computer_use?.model?.message as string | undefined}
              {...register('provider_config.computer_use.model')}
            />

            <Input
              type="number"
              label={t('settings.provider.computerUse.maxTokensLabel')}
              min={1024}
              max={32768}
              error={providerErrors?.computer_use?.max_tokens?.message as string | undefined}
              {...register('provider_config.computer_use.max_tokens', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label={t('settings.provider.computerUse.timeoutLabel')}
              min={1000}
              max={300000}
              error={providerErrors?.computer_use?.timeout?.message as string | undefined}
              {...register('provider_config.computer_use.timeout', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label={t('settings.provider.computerUse.screenshotIntervalLabel')}
              min={1000}
              max={600000}
              helperText={t('settings.provider.computerUse.screenshotIntervalHelper')}
              error={
                providerErrors?.computer_use?.screenshot_interval?.message as string | undefined
              }
              {...register('provider_config.computer_use.screenshot_interval', {
                valueAsNumber: true,
              })}
            />

            <Input
              type="number"
              label={t('settings.provider.computerUse.retryLabel')}
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
                    {t('settings.provider.hybrid.enable')}
                  </label>
                </div>
              )}
            />

            <Select
              label={t('settings.provider.hybrid.primaryLabel')}
              options={primaryProviderOptions}
              placeholder={t('settings.provider.hybrid.primaryPlaceholder')}
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
                    {t('settings.provider.hybrid.fallbackEnable')}
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
                    {t('settings.provider.hybrid.fallbackOnError')}
                  </label>
                </div>
              )}
            />

            <Input
              type="number"
              label={t('settings.provider.hybrid.autoSwitchLabel')}
              min={0}
              max={100}
              helperText={t('settings.provider.hybrid.autoSwitchHelper')}
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
