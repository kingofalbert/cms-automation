/**
 * Proofreading Review Header
 * Top navigation bar with breadcrumb, title, and action buttons.
 */

import { ArrowLeft, FileText, ChevronRight, X } from 'lucide-react';
import { Button } from '@/components/ui';
import { WorklistItemDetail } from '@/types/worklist';
import { useTranslation } from 'react-i18next';

interface ProofreadingReviewHeaderProps {
  worklistItem: WorklistItemDetail;
  onBack: () => void;
  onCancel?: () => void;
}

export function ProofreadingReviewHeader({
  worklistItem,
  onBack,
  onCancel,
}: ProofreadingReviewHeaderProps) {
  const { t } = useTranslation();

  return (
    <div className="border-b border-gray-200 bg-white">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 px-6 pt-3 pb-2 text-sm">
        <button
          type="button"
          onClick={onBack}
          className="text-gray-500 hover:text-gray-700 transition-colors"
        >
          {t('navigation.worklist') || 'Worklist'}
        </button>
        <ChevronRight className="h-4 w-4 text-gray-400" />
        <span className="max-w-md truncate text-gray-700" title={worklistItem.title}>
          {worklistItem.title}
        </span>
        <ChevronRight className="h-4 w-4 text-gray-400" />
        <span className="text-gray-900 font-medium">
          {t('proofreading.breadcrumb.review') || 'Proofreading Review'}
        </span>
      </div>

      {/* Main Header */}
      <div className="flex items-center justify-between px-6 pb-4">
        <div className="flex items-center gap-4">
          <FileText className="h-5 w-5 text-gray-400" />
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              {worklistItem.title}
            </h1>
            <p className="text-sm text-gray-500">
              {t('proofreading.labels.articleId') || 'Article ID'}: {worklistItem.article_id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Badges */}
          <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
            {worklistItem.status}
          </span>
          {worklistItem.article_status && (
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
              Article: {worklistItem.article_status}
            </span>
          )}

          {/* Action Buttons */}
          <div className="ml-2 flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="mr-1.5 h-4 w-4" />
              {t('common.back') || 'Back'}
            </Button>
            {onCancel && (
              <Button variant="outline" size="sm" onClick={onCancel}>
                <X className="mr-1.5 h-4 w-4" />
                {t('common.cancel') || 'Cancel'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
