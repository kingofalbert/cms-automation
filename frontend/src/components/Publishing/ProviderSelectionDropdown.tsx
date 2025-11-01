/**
 * Provider Selection Dropdown component.
 * Allows users to select a publishing provider.
 */

import { useState } from 'react';
import { Select, Badge } from '@/components/ui';
import { ProviderType, ProviderInfo } from '@/types/publishing';
import { clsx } from 'clsx';

export interface ProviderSelectionDropdownProps {
  value: ProviderType;
  onChange: (provider: ProviderType) => void;
  disabled?: boolean;
  className?: string;
}

const PROVIDERS: ProviderInfo[] = [
  {
    type: 'playwright',
    name: 'Playwright',
    description: '快速、稳定的浏览器自动化',
    icon: '🎭',
    cost_per_publish: 0.02,
    avg_duration: 45,
    success_rate: 98,
    features: ['快速执行', '低成本', '高成功率'],
  },
  {
    type: 'computer_use',
    name: 'Computer Use',
    description: 'AI 驱动的智能发布',
    icon: '🤖',
    cost_per_publish: 0.20,
    avg_duration: 120,
    success_rate: 95,
    features: ['智能适应', '处理复杂场景', '容错能力强'],
  },
  {
    type: 'hybrid',
    name: 'Hybrid (推荐)',
    description: 'Playwright 优先，自动降级',
    icon: '⚡',
    cost_per_publish: 0.04,
    avg_duration: 50,
    success_rate: 99,
    features: ['最佳性能', '最高成功率', '智能降级'],
    recommended: true,
  },
];

export const ProviderSelectionDropdown: React.FC<
  ProviderSelectionDropdownProps
> = ({ value, onChange, disabled = false, className }) => {
  const [showDetails, setShowDetails] = useState(false);

  const selectedProvider = PROVIDERS.find((p) => p.type === value);

  return (
    <div className={clsx('space-y-3', className)}>
      {/* Dropdown */}
      <Select
        label="发布 Provider"
        value={value}
        onChange={(e) => onChange(e.target.value as ProviderType)}
        disabled={disabled}
        fullWidth
        options={PROVIDERS.map((provider) => ({
          label: `${provider.icon} ${provider.name}${
            provider.recommended ? ' (推荐)' : ''
          }`,
          value: provider.type,
        }))}
      />

      {/* Provider Details */}
      {selectedProvider && (
        <div className="border rounded-lg p-4 bg-gray-50">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <span className="text-2xl">{selectedProvider.icon}</span>
                {selectedProvider.name}
                {selectedProvider.recommended && (
                  <Badge variant="success" size="sm">
                    推荐
                  </Badge>
                )}
              </h4>
              <p className="text-sm text-gray-600 mt-1">
                {selectedProvider.description}
              </p>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="text-center">
              <p className="text-xs text-gray-500">成本/篇</p>
              <p className="text-lg font-semibold text-gray-900">
                ${selectedProvider.cost_per_publish.toFixed(2)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">平均时长</p>
              <p className="text-lg font-semibold text-gray-900">
                {Math.floor(selectedProvider.avg_duration / 60)}:
                {(selectedProvider.avg_duration % 60)
                  .toString()
                  .padStart(2, '0')}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">成功率</p>
              <p className="text-lg font-semibold text-green-600">
                {selectedProvider.success_rate}%
              </p>
            </div>
          </div>

          {/* Features */}
          <div className="flex flex-wrap gap-2">
            {selectedProvider.features.map((feature, idx) => (
              <Badge key={idx} variant="info" size="sm">
                {feature}
              </Badge>
            ))}
          </div>

          {/* Toggle Details */}
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-primary-600 hover:underline mt-3"
          >
            {showDetails ? '收起详情' : '查看详情'}
          </button>

          {/* Additional Details */}
          {showDetails && (
            <div className="mt-3 pt-3 border-t space-y-2 text-sm text-gray-600">
              {value === 'playwright' && (
                <>
                  <p>
                    ✓ 使用 Playwright 浏览器自动化框架
                  </p>
                  <p>✓ 预定义选择器，快速稳定</p>
                  <p>✓ 适合标准 WordPress 主题</p>
                </>
              )}
              {value === 'computer_use' && (
                <>
                  <p>✓ 使用 Anthropic Computer Use API</p>
                  <p>✓ AI 自动识别页面元素</p>
                  <p>✓ 适合复杂或非标准主题</p>
                </>
              )}
              {value === 'hybrid' && (
                <>
                  <p>✓ 优先使用 Playwright（快速、低成本）</p>
                  <p>✓ 失败时自动切换到 Computer Use</p>
                  <p>✓ 结合两者优势，最高可靠性</p>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
