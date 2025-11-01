/**
 * Character Counter component for SEO metadata fields.
 * Shows real-time character count with validation.
 */

import { clsx } from 'clsx';

export interface CharacterCounterProps {
  current: number;
  min?: number;
  max?: number;
  optimal?: { min: number; max: number };
  className?: string;
}

export const CharacterCounter: React.FC<CharacterCounterProps> = ({
  current,
  min,
  max,
  optimal,
  className,
}) => {
  const getStatus = (): 'optimal' | 'warning' | 'error' => {
    if (max && current > max) return 'error';
    if (min && current < min) return 'warning';
    if (optimal && (current < optimal.min || current > optimal.max)) {
      return 'warning';
    }
    return 'optimal';
  };

  const status = getStatus();

  const getMessage = (): string => {
    if (max && current > max) {
      return `超出最大长度 ${current - max} 字符`;
    }
    if (min && current < min) {
      return `还需要 ${min - current} 字符`;
    }
    if (optimal) {
      if (current < optimal.min) {
        return `建议至少 ${optimal.min} 字符（当前 ${current}）`;
      }
      if (current > optimal.max) {
        return `建议最多 ${optimal.max} 字符（当前 ${current}）`;
      }
      return `最佳长度 ✓`;
    }
    return `${current} 字符`;
  };

  const statusStyles = {
    optimal: 'text-green-600 bg-green-50',
    warning: 'text-yellow-600 bg-yellow-50',
    error: 'text-red-600 bg-red-50',
  };

  const iconStyles = {
    optimal: '✓',
    warning: '!',
    error: '×',
  };

  return (
    <div
      className={clsx(
        'inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium',
        statusStyles[status],
        className
      )}
    >
      <span className="font-bold">{iconStyles[status]}</span>
      <span>{getMessage()}</span>
      {max && (
        <span className="text-xs opacity-75">
          ({current}/{max})
        </span>
      )}
    </div>
  );
};
