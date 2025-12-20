/**
 * ModeToggle - 視圖模式切換組件
 *
 * @version 1.0
 * @date 2025-12-19
 */

import React from 'react';
import { ViewMode, ModeToggleProps } from './types';

const MODE_OPTIONS: Array<{
  value: ViewMode;
  label: string;
  icon: string;
  title: string;
}> = [
  { value: 'preview', label: '預覽', icon: '👁️', title: '所見即所得預覽模式' },
  { value: 'source', label: '源碼', icon: '</>', title: '顯示 HTML 源代碼' },
  { value: 'hybrid', label: '混合', icon: '⚡', title: '同時顯示預覽和源碼' },
];

export const ModeToggle: React.FC<ModeToggleProps> = ({
  currentMode,
  onChange,
  disabled = false,
}) => {
  return (
    <div
      className="mode-toggle inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1"
      role="tablist"
      aria-label="視圖模式選擇"
    >
      {MODE_OPTIONS.map(({ value, label, icon, title }) => {
        const isActive = currentMode === value;

        return (
          <button
            key={value}
            onClick={() => !disabled && onChange(value)}
            disabled={disabled}
            className={`
              relative px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
              ${isActive
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${value}`}
            data-testid={`${value}-mode-btn`}
            title={title}
          >
            <span className="inline-flex items-center gap-1.5">
              <span aria-hidden="true">{icon}</span>
              <span>{label}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
};

export default ModeToggle;
