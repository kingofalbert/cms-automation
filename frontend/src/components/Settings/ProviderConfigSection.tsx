/**
 * Provider Configuration Section component.
 * Configure settings for different publishing providers.
 */

import type {
  ProviderConfig,
  PlaywrightConfig,
  ComputerUseConfig,
  HybridConfig,
} from '@/types/settings';
import { Card, Input, Select, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';

export interface ProviderConfigSectionProps {
  config: ProviderConfig;
  onChange: (config: ProviderConfig) => void;
}

export const ProviderConfigSection: React.FC<ProviderConfigSectionProps> = ({
  config,
  onChange,
}) => {
  const updatePlaywright = (updates: Partial<PlaywrightConfig>) => {
    onChange({
      ...config,
      playwright: { ...config.playwright, ...updates },
    });
  };

  const updateComputerUse = (updates: Partial<ComputerUseConfig>) => {
    onChange({
      ...config,
      computer_use: { ...config.computer_use, ...updates },
    });
  };

  const updateHybrid = (updates: Partial<HybridConfig>) => {
    onChange({
      ...config,
      hybrid: { ...config.hybrid, ...updates },
    });
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Provider 配置
      </h2>

      <Tabs defaultValue="playwright">
        <TabsList>
          <TabsTrigger value="playwright">Playwright</TabsTrigger>
          <TabsTrigger value="computer_use">Computer Use</TabsTrigger>
          <TabsTrigger value="hybrid">Hybrid</TabsTrigger>
        </TabsList>

        {/* Playwright Tab */}
        <TabsContent value="playwright">
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="playwright-enabled"
                checked={config.playwright.enabled}
                onChange={(event) => updatePlaywright({ enabled: event.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="playwright-enabled" className="ml-2 text-sm text-gray-700">
                启用 Playwright Provider
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="playwright-headless"
                checked={config.playwright.headless}
                onChange={(event) => updatePlaywright({ headless: event.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="playwright-headless" className="ml-2 text-sm text-gray-700">
                无头模式 (Headless)
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="playwright-screenshot"
                checked={config.playwright.screenshot_on_error}
                onChange={(event) =>
                  updatePlaywright({ screenshot_on_error: event.target.checked })
                }
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="playwright-screenshot" className="ml-2 text-sm text-gray-700">
                错误时截图
              </label>
            </div>

            <Select
              label="浏览器"
              value={config.playwright.browser}
              onChange={(event) =>
                updatePlaywright({ browser: event.target.value as PlaywrightConfig['browser'] })
              }
              options={[
                { value: 'chromium', label: 'Chromium' },
                { value: 'firefox', label: 'Firefox' },
                { value: 'webkit', label: 'WebKit' },
              ]}
            />

            <Input
              type="number"
              label="超时时间 (毫秒)"
              value={config.playwright.timeout}
              onChange={(event) =>
                updatePlaywright({ timeout: Number.parseInt(event.target.value, 10) })
              }
            />

            <Input
              type="number"
              label="重试次数"
              value={config.playwright.retry_count}
              onChange={(event) =>
                updatePlaywright({ retry_count: Number.parseInt(event.target.value, 10) })
              }
              min={0}
              max={5}
            />
          </div>
        </TabsContent>

        {/* Computer Use Tab */}
        <TabsContent value="computer_use">
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="computer-use-enabled"
                checked={config.computer_use.enabled}
                onChange={(event) => updateComputerUse({ enabled: event.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="computer-use-enabled" className="ml-2 text-sm text-gray-700">
                启用 Computer Use Provider
              </label>
            </div>

            <Input
              type="text"
              label="模型"
              value={config.computer_use.model}
              onChange={(event) => updateComputerUse({ model: event.target.value })}
              disabled
              helperText="Computer Use API 目前仅支持 claude-3-5-sonnet-20241022 (由 Anthropic API 限制)"
            />

            <Input
              type="number"
              label="最大 Tokens"
              value={config.computer_use.max_tokens}
              onChange={(event) =>
                updateComputerUse({ max_tokens: Number.parseInt(event.target.value, 10) })
              }
            />

            <Input
              type="number"
              label="超时时间 (毫秒)"
              value={config.computer_use.timeout}
              onChange={(event) =>
                updateComputerUse({ timeout: Number.parseInt(event.target.value, 10) })
              }
            />

            <Input
              type="number"
              label="截图间隔 (毫秒)"
              value={config.computer_use.screenshot_interval}
              onChange={(event) =>
                updateComputerUse({
                  screenshot_interval: Number.parseInt(event.target.value, 10),
                })
              }
              helperText="Computer Use 执行时的截图间隔"
            />

            <Input
              type="number"
              label="重试次数"
              value={config.computer_use.retry_count}
              onChange={(event) =>
                updateComputerUse({ retry_count: Number.parseInt(event.target.value, 10) })
              }
              min={0}
              max={5}
            />
          </div>
        </TabsContent>

        {/* Hybrid Tab */}
        <TabsContent value="hybrid">
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="hybrid-enabled"
                checked={config.hybrid.enabled}
                onChange={(event) => updateHybrid({ enabled: event.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="hybrid-enabled" className="ml-2 text-sm text-gray-700">
                启用 Hybrid Provider
              </label>
            </div>

            <Select
              label="首选 Provider"
              value={config.hybrid.primary_provider}
              onChange={(event) =>
                updateHybrid({
                  primary_provider: event.target.value as HybridConfig['primary_provider'],
                })
              }
              options={[
                { value: 'playwright', label: 'Playwright' },
                { value: 'computer_use', label: 'Computer Use' },
              ]}
            />

            <div className="flex items-center">
              <input
                type="checkbox"
                id="hybrid-fallback"
                checked={config.hybrid.fallback_enabled}
                onChange={(event) => updateHybrid({ fallback_enabled: event.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="hybrid-fallback" className="ml-2 text-sm text-gray-700">
                启用降级 (Fallback)
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="hybrid-error-fallback"
                checked={config.hybrid.fallback_on_error}
                onChange={(event) => updateHybrid({ fallback_on_error: event.target.checked })}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <label htmlFor="hybrid-error-fallback" className="ml-2 text-sm text-gray-700">
                错误时自动降级
              </label>
            </div>

            <Input
              type="number"
              label="自动切换阈值 (%)"
              value={config.hybrid.auto_switch_threshold}
              onChange={(event) =>
                updateHybrid({ auto_switch_threshold: Number.parseInt(event.target.value, 10) })
              }
              min={0}
              max={100}
              helperText="当成功率低于此阈值时，自动切换到备用 Provider"
            />
          </div>
        </TabsContent>
      </Tabs>
    </Card>
  );
};
