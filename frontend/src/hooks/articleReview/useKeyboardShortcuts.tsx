/**
 * useKeyboardShortcuts - Keyboard navigation for article review
 *
 * Phase 8.1: Modal Framework
 * - Esc: Close modal
 * - Ctrl+S: Save draft
 * - →/←: Next/Previous step
 * - A: Accept (for proofreading issues)
 * - R: Reject (for proofreading issues)
 *
 * Architecture:
 * - Only active when modal is open
 * - Respects input focus (don't trigger when typing)
 * - Provides visual feedback for shortcuts
 */

import React, { useEffect, useCallback } from 'react';

export interface KeyboardShortcutHandlers {
  /** Called when Esc is pressed */
  onClose?: () => void;
  /** Called when Ctrl+S is pressed */
  onSave?: () => void;
  /** Called when → or Right arrow is pressed */
  onNext?: () => void;
  /** Called when ← or Left arrow is pressed */
  onPrevious?: () => void;
  /** Called when A is pressed (Accept) */
  onAccept?: () => void;
  /** Called when R is pressed (Reject) */
  onReject?: () => void;
  /** Called when Ctrl+Enter is pressed (Submit) */
  onSubmit?: () => void;
}

export interface UseKeyboardShortcutsOptions extends KeyboardShortcutHandlers {
  /** Whether shortcuts are enabled */
  enabled?: boolean;
  /** Disable shortcuts when inside these elements */
  ignoreElements?: string[];
}

/**
 * Check if event target is an input element where we should ignore shortcuts
 */
const isInputElement = (target: EventTarget | null): boolean => {
  if (!target || !(target instanceof HTMLElement)) {
    return false;
  }

  const tagName = target.tagName.toLowerCase();
  const isContentEditable = target.isContentEditable;

  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select' ||
    isContentEditable ||
    target.getAttribute('role') === 'textbox'
  );
};

/**
 * Hook: useKeyboardShortcuts
 */
export const useKeyboardShortcuts = (options: UseKeyboardShortcutsOptions) => {
  const {
    enabled = true,
    onClose,
    onSave,
    onNext,
    onPrevious,
    onAccept,
    onReject,
    onSubmit,
    ignoreElements = [],
  } = options;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Skip if shortcuts are disabled
      if (!enabled) {
        return;
      }

      // Skip if target is an input element (unless it's Esc or Ctrl+S)
      const isInput = isInputElement(event.target);
      const key = event.key.toLowerCase();
      const ctrl = event.ctrlKey || event.metaKey;

      // Esc always works, even in input fields
      if (key === 'escape') {
        event.preventDefault();
        onClose?.();
        return;
      }

      // Ctrl+S always works, even in input fields
      if (ctrl && key === 's') {
        event.preventDefault();
        onSave?.();
        return;
      }

      // Ctrl+Enter for submit
      if (ctrl && key === 'enter') {
        event.preventDefault();
        onSubmit?.();
        return;
      }

      // Skip other shortcuts if in input field
      if (isInput) {
        return;
      }

      // Arrow key navigation
      if (key === 'arrowright') {
        event.preventDefault();
        onNext?.();
        return;
      }

      if (key === 'arrowleft') {
        event.preventDefault();
        onPrevious?.();
        return;
      }

      // Accept/Reject shortcuts (for proofreading review)
      if (key === 'a' && onAccept) {
        event.preventDefault();
        onAccept();
        return;
      }

      if (key === 'r' && onReject) {
        event.preventDefault();
        onReject();
        return;
      }
    },
    [enabled, onClose, onSave, onNext, onPrevious, onAccept, onReject, onSubmit]
  );

  // Add/remove event listener
  useEffect(() => {
    if (!enabled) {
      return;
    }

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, handleKeyDown]);

  // Return shortcut descriptions for UI
  return {
    shortcuts: [
      { key: 'Esc', description: '关闭', enabled: Boolean(onClose) },
      { key: 'Ctrl+S', description: '保存草稿', enabled: Boolean(onSave) },
      { key: '→', description: '下一步', enabled: Boolean(onNext) },
      { key: '←', description: '上一步', enabled: Boolean(onPrevious) },
      { key: 'A', description: '接受', enabled: Boolean(onAccept) },
      { key: 'R', description: '拒绝', enabled: Boolean(onReject) },
      { key: 'Ctrl+Enter', description: '提交', enabled: Boolean(onSubmit) },
    ].filter((s) => s.enabled),
  };
};

/**
 * Component: KeyboardShortcutsHelper
 * Displays available keyboard shortcuts
 */
export const KeyboardShortcutsHelper: React.FC<{ shortcuts: Array<{ key: string; description: string }> }> = ({
  shortcuts,
}) => {
  if (shortcuts.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 text-white rounded-lg shadow-lg p-3 text-xs opacity-75 hover:opacity-100 transition-opacity">
      <div className="font-semibold mb-2">快捷键</div>
      <div className="space-y-1">
        {shortcuts.map((shortcut) => (
          <div key={shortcut.key} className="flex items-center gap-2">
            <kbd className="px-2 py-0.5 bg-gray-800 rounded text-xs font-mono">
              {shortcut.key}
            </kbd>
            <span className="text-gray-300">{shortcut.description}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
