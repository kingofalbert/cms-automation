/**
 * KeyboardShortcutsModal - Global keyboard shortcuts help modal
 *
 * Features:
 * - Triggered by '?' key globally
 * - Shows all available shortcuts grouped by feature
 * - Accessible with proper ARIA labels
 * - Dismissible with Escape key
 */

import React, { useEffect, useCallback, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Keyboard, Command, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useTranslation } from 'react-i18next';

export interface ShortcutItem {
  keys: string[];
  description: string;
}

export interface ShortcutGroup {
  title: string;
  icon?: React.ReactNode;
  shortcuts: ShortcutItem[];
}

// Pre-defined shortcut groups
const getShortcutGroups = (t: ReturnType<typeof useTranslation>['t']): ShortcutGroup[] => [
  {
    title: t('shortcuts.groups.global', { defaultValue: '全局' }),
    icon: <Keyboard className="w-4 h-4" />,
    shortcuts: [
      { keys: ['?'], description: t('shortcuts.showHelp', { defaultValue: '顯示快捷鍵幫助' }) },
      { keys: ['Esc'], description: t('shortcuts.closeModal', { defaultValue: '關閉對話框/模態框' }) },
      { keys: ['Ctrl', 'S'], description: t('shortcuts.save', { defaultValue: '保存' }) },
    ],
  },
  {
    title: t('shortcuts.groups.navigation', { defaultValue: '導航' }),
    icon: <Command className="w-4 h-4" />,
    shortcuts: [
      { keys: ['←'], description: t('shortcuts.previousStep', { defaultValue: '上一步' }) },
      { keys: ['→'], description: t('shortcuts.nextStep', { defaultValue: '下一步' }) },
      { keys: ['↑'], description: t('shortcuts.previousItem', { defaultValue: '上一個項目' }) },
      { keys: ['↓'], description: t('shortcuts.nextItem', { defaultValue: '下一個項目' }) },
    ],
  },
  {
    title: t('shortcuts.groups.proofreading', { defaultValue: '校對審核' }),
    icon: <span className="text-sm">✏️</span>,
    shortcuts: [
      { keys: ['A'], description: t('shortcuts.accept', { defaultValue: '接受建議' }) },
      { keys: ['R'], description: t('shortcuts.reject', { defaultValue: '拒絕建議' }) },
      { keys: ['Space'], description: t('shortcuts.toggleSelect', { defaultValue: '切換選擇' }) },
    ],
  },
  {
    title: t('shortcuts.groups.editing', { defaultValue: '編輯' }),
    icon: <span className="text-sm">📝</span>,
    shortcuts: [
      { keys: ['Ctrl', 'Enter'], description: t('shortcuts.submit', { defaultValue: '提交/確認' }) },
      { keys: ['Ctrl', 'Z'], description: t('shortcuts.undo', { defaultValue: '撤銷' }) },
      { keys: ['Ctrl', 'Shift', 'Z'], description: t('shortcuts.redo', { defaultValue: '重做' }) },
    ],
  },
];

// Key display component
const KeyBadge: React.FC<{ keyLabel: string }> = ({ keyLabel }) => {
  // Map special keys to icons or formatted labels
  const renderKey = () => {
    switch (keyLabel) {
      case '←':
        return <ArrowLeft className="w-3 h-3" />;
      case '→':
        return <ArrowRight className="w-3 h-3" />;
      case '↑':
        return <ArrowUp className="w-3 h-3" />;
      case '↓':
        return <ArrowDown className="w-3 h-3" />;
      case 'Ctrl':
        return <span className="text-xs">Ctrl</span>;
      case 'Shift':
        return <span className="text-xs">⇧</span>;
      case 'Space':
        return <span className="text-xs">Space</span>;
      case 'Enter':
        return <span className="text-xs">↵</span>;
      case 'Esc':
        return <span className="text-xs">Esc</span>;
      default:
        return <span className="text-xs font-semibold">{keyLabel}</span>;
    }
  };

  return (
    <kbd
      className={cn(
        'inline-flex items-center justify-center min-w-[28px] h-7 px-2',
        'rounded-md border border-gray-300 bg-gray-50 shadow-sm',
        'font-mono text-gray-700'
      )}
    >
      {renderKey()}
    </kbd>
  );
};

// Shortcut row component
const ShortcutRow: React.FC<{ shortcut: ShortcutItem }> = ({ shortcut }) => {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-gray-700">{shortcut.description}</span>
      <div className="flex items-center gap-1">
        {shortcut.keys.map((key, index) => (
          <React.Fragment key={key}>
            {index > 0 && <span className="text-gray-400 text-xs mx-0.5">+</span>}
            <KeyBadge keyLabel={key} />
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

// Modal props
export interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
  customGroups?: ShortcutGroup[];
}

/**
 * KeyboardShortcutsModal Component
 */
export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({
  isOpen,
  onClose,
  customGroups,
}) => {
  const { t } = useTranslation();

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const groups = customGroups || getShortcutGroups(t);

  const modalContent = (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-modal-title"
    >
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Content */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden z-10">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-primary-50 to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <Keyboard className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <h2 id="shortcuts-modal-title" className="text-lg font-semibold text-gray-900">
                {t('shortcuts.title', { defaultValue: '快捷鍵' })}
              </h2>
              <p className="text-sm text-gray-500">
                {t('shortcuts.subtitle', { defaultValue: '按 ? 隨時查看此幫助' })}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded-lg p-2"
            aria-label={t('common.close', { defaultValue: '關閉' })}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto max-h-[calc(80vh-100px)] p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {groups.map((group) => (
              <div
                key={group.title}
                className="bg-gray-50 rounded-lg p-4 border border-gray-100"
              >
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-200">
                  {group.icon}
                  <h3 className="font-semibold text-gray-900">{group.title}</h3>
                </div>
                <div className="divide-y divide-gray-100">
                  {group.shortcuts.map((shortcut, index) => (
                    <ShortcutRow key={index} shortcut={shortcut} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 border-t text-center">
          <span className="text-xs text-gray-500">
            {t('shortcuts.footer', { defaultValue: '提示：部分快捷鍵僅在特定頁面或模式下可用' })}
          </span>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

/**
 * Hook: useKeyboardShortcutsModal
 * Provides global '?' key listener for showing the shortcuts modal
 */
export const useKeyboardShortcutsModal = () => {
  const [isOpen, setIsOpen] = useState(false);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Check if '?' is pressed (Shift + / on most keyboards)
    if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      // Don't trigger in input elements
      const target = e.target as HTMLElement;
      const tagName = target?.tagName?.toLowerCase();
      if (tagName === 'input' || tagName === 'textarea' || target?.isContentEditable) {
        return;
      }

      e.preventDefault();
      setIsOpen(true);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
  };
};

KeyboardShortcutsModal.displayName = 'KeyboardShortcutsModal';
