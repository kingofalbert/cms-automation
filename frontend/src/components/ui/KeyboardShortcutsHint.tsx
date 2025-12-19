/**
 * KeyboardShortcutsHint component - Display keyboard shortcuts
 */

import React, { useState } from 'react';
import { cn } from '../../lib/cn';
import { Keyboard, X, ChevronDown, ChevronUp } from 'lucide-react';

export interface KeyboardShortcut {
  key: string;
  label: string;
  description?: string;
}

export interface KeyboardShortcutsHintProps {
  shortcuts: KeyboardShortcut[];
  /** Display mode */
  mode?: 'inline' | 'floating' | 'collapsible';
  /** Position for floating mode */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  /** Show/hide toggle for floating mode */
  showToggle?: boolean;
  /** Title text */
  title?: string;
  /** Additional className */
  className?: string;
}

/**
 * Single keyboard key display
 */
function Kbd({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <kbd
      className={cn(
        'inline-flex items-center justify-center min-w-[24px] h-6 px-2',
        'rounded border border-gray-300 bg-white shadow-sm',
        'font-mono text-xs font-medium text-gray-700',
        className
      )}
    >
      {children}
    </kbd>
  );
}

/**
 * Inline hints - Simple row of shortcuts
 */
function InlineHints({
  shortcuts,
  className,
}: {
  shortcuts: KeyboardShortcut[];
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-4 text-xs text-gray-500', className)}>
      {shortcuts.map((shortcut) => (
        <div key={shortcut.key} className="flex items-center gap-1.5">
          <Kbd>{shortcut.key}</Kbd>
          <span>{shortcut.label}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Floating panel - Hovering in corner
 */
function FloatingHints({
  shortcuts,
  position = 'bottom-right',
  showToggle = true,
  title = 'Keyboard Shortcuts',
  className,
}: {
  shortcuts: KeyboardShortcut[];
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  showToggle?: boolean;
  title?: string;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(true);

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
  };

  if (!isOpen && showToggle) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'fixed z-50 flex items-center gap-2 rounded-full bg-gray-800 px-4 py-2 text-white shadow-lg hover:bg-gray-700 transition-colors',
          positionClasses[position],
          className
        )}
        title="Show keyboard shortcuts"
      >
        <Keyboard className="h-4 w-4" />
        <span className="text-sm">Shortcuts</span>
      </button>
    );
  }

  return (
    <div
      className={cn(
        'fixed z-50 rounded-lg border border-gray-200 bg-white shadow-xl',
        'max-w-xs w-72',
        positionClasses[position],
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-2">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <Keyboard className="h-4 w-4" />
          {title}
        </div>
        {showToggle && (
          <button
            onClick={() => setIsOpen(false)}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Shortcuts list */}
      <div className="p-3 space-y-2">
        {shortcuts.map((shortcut) => (
          <div key={shortcut.key} className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-sm text-gray-700">{shortcut.label}</span>
              {shortcut.description && (
                <span className="text-xs text-gray-400">{shortcut.description}</span>
              )}
            </div>
            <Kbd>{shortcut.key}</Kbd>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Collapsible panel - Expandable section
 */
function CollapsibleHints({
  shortcuts,
  title = 'Keyboard Shortcuts',
  className,
}: {
  shortcuts: KeyboardShortcut[];
  title?: string;
  className?: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={cn('border-t border-gray-200 bg-gray-50', className)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between px-4 py-2 text-left hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2 text-xs font-medium text-gray-600">
          <Keyboard className="h-3.5 w-3.5" />
          {title}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200 px-4 py-3">
          <div className="grid grid-cols-3 gap-3 text-center">
            {shortcuts.map((shortcut) => (
              <div key={shortcut.key} className="flex flex-col items-center gap-1">
                <Kbd className="mb-1">{shortcut.key}</Kbd>
                <span className="text-[10px] text-gray-500">{shortcut.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function KeyboardShortcutsHint({
  shortcuts,
  mode = 'inline',
  position = 'bottom-right',
  showToggle = true,
  title = 'Keyboard Shortcuts',
  className,
}: KeyboardShortcutsHintProps) {
  switch (mode) {
    case 'floating':
      return (
        <FloatingHints
          shortcuts={shortcuts}
          position={position}
          showToggle={showToggle}
          title={title}
          className={className}
        />
      );
    case 'collapsible':
      return (
        <CollapsibleHints
          shortcuts={shortcuts}
          title={title}
          className={className}
        />
      );
    case 'inline':
    default:
      return <InlineHints shortcuts={shortcuts} className={className} />;
  }
}

/**
 * Pre-configured shortcuts for proofreading review
 */
export const PROOFREADING_SHORTCUTS: KeyboardShortcut[] = [
  { key: 'A', label: 'Accept', description: 'Accept current suggestion' },
  { key: 'R', label: 'Reject', description: 'Reject current suggestion' },
  { key: '↑', label: 'Previous', description: 'Go to previous issue' },
  { key: '↓', label: 'Next', description: 'Go to next issue' },
  { key: 'Space', label: 'Select', description: 'Toggle selection' },
];

/**
 * Compact shortcuts for inline display
 */
export const PROOFREADING_SHORTCUTS_COMPACT: KeyboardShortcut[] = [
  { key: 'A', label: 'Accept' },
  { key: 'R', label: 'Reject' },
  { key: '↑↓', label: 'Navigate' },
];

export { Kbd };
