/**
 * SaveStatusIndicator - Visual indicator for auto-save status
 *
 * Shows:
 * - Idle: Nothing shown
 * - Saving: Spinner + "保存中..."
 * - Saved: Check + "已保存" with fade out
 * - Error: Warning + error message
 */

import React from 'react';
import { Check, Loader2, AlertCircle, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { SaveStatus } from '../../hooks/useAutoSave';
import { useTranslation } from 'react-i18next';

export interface SaveStatusIndicatorProps {
  /** Current save status */
  status: SaveStatus;
  /** Time since last save */
  timeSinceLastSave?: string | null;
  /** Error message to display */
  errorMessage?: string | null;
  /** Show time since last save */
  showLastSaved?: boolean;
  /** Custom className */
  className?: string;
  /** Compact mode (icon only) */
  compact?: boolean;
}

/**
 * SaveStatusIndicator Component
 */
export const SaveStatusIndicator: React.FC<SaveStatusIndicatorProps> = ({
  status,
  timeSinceLastSave,
  errorMessage,
  showLastSaved = true,
  className,
  compact = false,
}) => {
  const { t } = useTranslation();

  // Don't show anything for idle status unless we have lastSaved info
  if (status === 'idle' && (!showLastSaved || !timeSinceLastSave)) {
    return null;
  }

  const getContent = () => {
    switch (status) {
      case 'saving':
        return (
          <div className="flex items-center gap-1.5 text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            {!compact && (
              <span className="text-xs font-medium">
                {t('autoSave.saving', { defaultValue: '保存中...' })}
              </span>
            )}
          </div>
        );

      case 'saved':
        return (
          <div className="flex items-center gap-1.5 text-green-600 animate-in fade-in duration-300">
            <Check className="w-4 h-4" />
            {!compact && (
              <span className="text-xs font-medium">
                {t('autoSave.saved', { defaultValue: '已保存' })}
              </span>
            )}
          </div>
        );

      case 'error':
        return (
          <div className="flex items-center gap-1.5 text-red-600">
            <AlertCircle className="w-4 h-4" />
            {!compact && (
              <span className="text-xs font-medium">
                {errorMessage || t('autoSave.error', { defaultValue: '保存失敗' })}
              </span>
            )}
          </div>
        );

      case 'idle':
      default:
        // Show last saved time
        if (showLastSaved && timeSinceLastSave) {
          return (
            <div className="flex items-center gap-1.5 text-gray-400">
              <Clock className="w-3.5 h-3.5" />
              {!compact && (
                <span className="text-xs">
                  {t('autoSave.lastSaved', { defaultValue: '上次保存' })}: {timeSinceLastSave}
                </span>
              )}
            </div>
          );
        }
        return null;
    }
  };

  const content = getContent();
  if (!content) return null;

  return (
    <div
      className={cn(
        'transition-opacity duration-300',
        className
      )}
      aria-live="polite"
      aria-atomic="true"
    >
      {content}
    </div>
  );
};

/**
 * Inline Save Status for use in headers/toolbars
 */
export const InlineSaveStatus: React.FC<{
  status: SaveStatus;
  hasUnsavedChanges?: boolean;
  onManualSave?: () => void;
  className?: string;
}> = ({ status, hasUnsavedChanges, onManualSave, className }) => {
  const { t } = useTranslation();

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <SaveStatusIndicator status={status} showLastSaved={false} compact />

      {/* Show unsaved indicator */}
      {hasUnsavedChanges && status !== 'saving' && (
        <span className="text-xs text-amber-600">
          {t('autoSave.unsavedChanges', { defaultValue: '有未保存的更改' })}
        </span>
      )}

      {/* Manual save button */}
      {onManualSave && hasUnsavedChanges && status !== 'saving' && (
        <button
          onClick={onManualSave}
          className="text-xs text-primary-600 hover:text-primary-700 underline focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded"
        >
          {t('autoSave.saveNow', { defaultValue: '立即保存' })}
        </button>
      )}
    </div>
  );
};

SaveStatusIndicator.displayName = 'SaveStatusIndicator';
InlineSaveStatus.displayName = 'InlineSaveStatus';
