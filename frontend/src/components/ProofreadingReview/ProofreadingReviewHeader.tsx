/**
 * Proofreading Review Header
 * Top navigation bar with title and back button.
 */

import { ArrowLeft, FileText } from 'lucide-react';
import { Button } from '@/components/ui';
import { WorklistItemDetail } from '@/types/worklist';

interface ProofreadingReviewHeaderProps {
  worklistItem: WorklistItemDetail;
  onBack: () => void;
}

export function ProofreadingReviewHeader({
  worklistItem,
  onBack,
}: ProofreadingReviewHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-gray-400" />
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              {worklistItem.title}
            </h1>
            <p className="text-sm text-gray-500">
              Proofreading Review • Article ID: {worklistItem.article_id}
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
          {worklistItem.status}
        </span>
        {worklistItem.article_status && (
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
            Article: {worklistItem.article_status}
          </span>
        )}
      </div>
    </div>
  );
}
