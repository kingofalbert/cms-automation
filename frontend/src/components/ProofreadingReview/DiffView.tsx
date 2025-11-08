/**
 * DiffView Component
 * Displays original vs suggested content side-by-side with diff highlighting.
 *
 * Performance optimizations:
 * - Wrapped with React.memo to prevent unnecessary re-renders
 * - Static diffStyles defined outside component to avoid recreation
 */

import { memo } from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';

interface DiffViewProps {
  original: string;
  suggested: string;
  title: string;
  className?: string;
}

/**
 * Custom diff viewer styles to match our design system
 * Defined outside component to avoid recreation on every render
 */
const diffStyles = {
  variables: {
    light: {
      diffViewerBackground: '#fff',
      diffViewerColor: '#374151',
      addedBackground: '#dcfce7',
      addedColor: '#166534',
      removedBackground: '#fee2e2',
      removedColor: '#991b1b',
      wordAddedBackground: '#86efac',
      wordRemovedBackground: '#fca5a5',
      addedGutterBackground: '#bbf7d0',
      removedGutterBackground: '#fecaca',
      gutterBackground: '#f9fafb',
      gutterBackgroundDark: '#f3f4f6',
      highlightBackground: '#fef3c7',
      highlightGutterBackground: '#fde68a',
      codeFoldGutterBackground: '#e5e7eb',
      codeFoldBackground: '#f3f4f6',
      emptyLineBackground: '#fafafa',
      gutterColor: '#6b7280',
      addedGutterColor: '#16a34a',
      removedGutterColor: '#dc2626',
      codeFoldContentColor: '#6b7280',
      diffViewerTitleBackground: '#f9fafb',
      diffViewerTitleColor: '#1f2937',
      diffViewerTitleBorderColor: '#e5e7eb',
    },
  },
  line: {
    padding: '10px 2px',
    '&:hover': {
      background: '#f9fafb',
    },
  },
  gutter: {
    padding: '10px 8px',
    minWidth: '50px',
    textAlign: 'center' as const,
  },
  marker: {
    padding: '10px 8px',
    minWidth: '30px',
  },
  content: {
    padding: '10px 8px',
  },
  wordDiff: {
    padding: '2px 4px',
    borderRadius: '2px',
  },
};

const DiffViewComponent = ({ original, suggested, title, className }: DiffViewProps) => {
  const { t } = useTranslation();

  return (
    <div className={cn('mx-auto max-w-full', className)}>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">{title}</h1>
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
          <div className="flex items-center justify-between text-sm font-medium text-gray-700">
            <span>{t('proofreading.labels.original')}</span>
            <span>{t('proofreading.labels.suggested')}</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <ReactDiffViewer
            oldValue={original}
            newValue={suggested}
            splitView={true}
            compareMethod={DiffMethod.WORDS}
            useDarkTheme={false}
            styles={diffStyles}
            leftTitle={t('proofreading.labels.original')}
            rightTitle={t('proofreading.labels.suggested')}
            showDiffOnly={false}
            disableWordDiff={false}
            hideLineNumbers={false}
          />
        </div>
      </div>
    </div>
  );
};

// Memoize component to prevent unnecessary re-renders
// Component only re-renders when props actually change
export const DiffView = memo(DiffViewComponent);
