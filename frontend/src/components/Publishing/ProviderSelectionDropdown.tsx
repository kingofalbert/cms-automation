/**
 * Provider Selection Dropdown component.
 * Allows users to select a publishing provider.
 */

import { useState } from 'react';
import { Select, Badge } from '@/components/ui';
import { ProviderType } from '@/types/publishing';
import { clsx } from 'clsx';
import { useTranslation } from 'react-i18next';

export interface ProviderSelectionDropdownProps {
  value: ProviderType;
  onChange: (provider: ProviderType) => void;
  disabled?: boolean;
  className?: string;
}

interface ProviderDefinition {
  type: ProviderType;
  icon: string;
  cost_per_publish: number;
  avg_duration: number;
  success_rate: number;
  recommended?: boolean;
}

const PROVIDERS: ProviderDefinition[] = [
  {
    type: 'playwright',
    icon: '🎭',
    cost_per_publish: 0.02,
    avg_duration: 45,
    success_rate: 98,
  },
  {
    type: 'computer_use',
    icon: '🤖',
    cost_per_publish: 0.2,
    avg_duration: 120,
    success_rate: 95,
  },
  {
    type: 'hybrid',
    icon: '⚡',
    cost_per_publish: 0.04,
    avg_duration: 50,
    success_rate: 99,
    recommended: true,
  },
];

type ProviderContent = {
  name: string;
  description: string;
  features?: string[];
  details?: string[];
};

export const ProviderSelectionDropdown: React.FC<
  ProviderSelectionDropdownProps
> = ({ value, onChange, disabled = false, className }) => {
  const { t } = useTranslation();
  const [showDetails, setShowDetails] = useState(false);

  const selectedProvider = PROVIDERS.find((p) => p.type === value);

  const getProviderContent = (type: ProviderType) =>
    t(`publishing.providerSelector.providers.${type}`, {
      returnObjects: true,
    }) as ProviderContent;

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainder = (seconds % 60).toString().padStart(2, '0');
    return t('publishing.providerSelector.durationFormat', {
      minutes,
      seconds: remainder,
    });
  };

  return (
    <div className={clsx('space-y-3', className)}>
      <Select
        label={t('publishing.providerSelector.label')}
        value={value}
        onChange={(e) => onChange(e.target.value as ProviderType)}
        disabled={disabled}
        fullWidth
        options={PROVIDERS.map((provider) => {
          const content = getProviderContent(provider.type);
          const optionLabel = `${provider.icon} ${content.name}${
            provider.recommended
              ? ` (${t('publishing.providerSelector.recommendedBadge')})`
              : ''
          }`;
          return {
            value: provider.type,
            label: optionLabel,
          };
        })}
      />

      {selectedProvider && (
        <div className="border rounded-lg p-4 bg-gray-50">
          {(() => {
            const content = getProviderContent(selectedProvider.type);
            const features = content.features ?? [];
            const details = content.details ?? [];

            return (
              <>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                      <span className="text-2xl">{selectedProvider.icon}</span>
                      {content.name}
                      {selectedProvider.recommended && (
                        <Badge variant="success" size="sm">
                          {t('publishing.providerSelector.recommendedBadge')}
                        </Badge>
                      )}
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {content.description}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">
                      {t('publishing.providerSelector.metrics.cost')}
                    </p>
                    <p className="text-lg font-semibold text-gray-900">
                      ${selectedProvider.cost_per_publish.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">
                      {t('publishing.providerSelector.metrics.duration')}
                    </p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatDuration(selectedProvider.avg_duration)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-1">
                      {t('publishing.providerSelector.metrics.successRate')}
                    </p>
                    <p className="text-lg font-semibold text-green-600">
                      {selectedProvider.success_rate}%
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {features.map((feature, idx) => (
                    <Badge key={idx} variant="info" size="sm">
                      {feature}
                    </Badge>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => setShowDetails(!showDetails)}
                  className="text-sm text-primary-600 hover:underline mt-3"
                >
                  {showDetails
                    ? t('publishing.providerSelector.toggle.hide')
                    : t('publishing.providerSelector.toggle.show')}
                </button>

                {showDetails && details.length > 0 && (
                  <div className="mt-3 pt-3 border-t space-y-2 text-sm text-gray-600">
                    {details.map((detail, index) => (
                      <p key={index}>✓ {detail}</p>
                    ))}
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};
