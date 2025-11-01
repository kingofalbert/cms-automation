/**
 * Meta Description Editor component with character count and AI generation indicator.
 */

import { useState } from 'react';
import { CharacterCounter } from './CharacterCounter';
import { clsx } from 'clsx';

export interface MetaDescriptionEditorProps {
  value: string;
  onChange: (value: string) => void;
  isAIGenerated?: boolean;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  className?: string;
}

export const MetaDescriptionEditor: React.FC<MetaDescriptionEditorProps> = ({
  value,
  onChange,
  isAIGenerated = false,
  onRegenerate,
  isRegenerating = false,
  className,
}) => {
  const [isEdited, setIsEdited] = useState(false);

  const handleChange = (newValue: string) => {
    onChange(newValue);
    if (isAIGenerated && !isEdited) {
      setIsEdited(true);
    }
  };

  const characterCount = value.length;
  const OPTIMAL_MIN = 150;
  const OPTIMAL_MAX = 160;
  const MAX_LENGTH = 200;

  return (
    <div className={clsx('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Meta Description <span className="text-red-500">*</span>
        </label>
        <div className="flex items-center gap-2">
          {isAIGenerated && !isEdited && (
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded flex items-center gap-1">
              <svg
                className="w-3 h-3"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
              </svg>
              AI 生成
            </span>
          )}
          {isEdited && isAIGenerated && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
              手动修改
            </span>
          )}
          {onRegenerate && (
            <button
              type="button"
              onClick={onRegenerate}
              disabled={isRegenerating}
              className={clsx(
                'text-xs text-primary-600 hover:text-primary-700 hover:underline',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {isRegenerating ? '生成中...' : '重新生成'}
            </button>
          )}
        </div>
      </div>

      <textarea
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        maxLength={MAX_LENGTH}
        rows={3}
        placeholder="输入 Meta Description（150-160 字符最佳）"
        className={clsx(
          'w-full px-3 py-2 border rounded-lg transition-colors resize-vertical',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
          characterCount > MAX_LENGTH
            ? 'border-red-500'
            : characterCount >= OPTIMAL_MIN && characterCount <= OPTIMAL_MAX
            ? 'border-green-500'
            : 'border-gray-300'
        )}
      />

      <div className="flex items-center justify-between">
        <CharacterCounter
          current={characterCount}
          max={MAX_LENGTH}
          optimal={{ min: OPTIMAL_MIN, max: OPTIMAL_MAX }}
        />
        <p className="text-xs text-gray-500">Google 建议 150-160 字符</p>
      </div>

      {characterCount === 0 && (
        <p className="text-sm text-red-600">Meta Description 不能为空</p>
      )}
    </div>
  );
};
