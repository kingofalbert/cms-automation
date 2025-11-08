/**
 * Publish Button component - Main entry point for publishing flow.
 * Orchestrates the entire publishing process with dialogs and progress tracking.
 */

import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios, { type AxiosError } from 'axios';
import { Button } from '@/components/ui';
import { ProviderSelectionDropdown } from './ProviderSelectionDropdown';
import { PublishConfirmationDialog } from './PublishConfirmationDialog';
import { PublishProgressModal } from './PublishProgressModal';
import { ProviderType, PublishTask, PublishRequest, PublishResult } from '@/types/publishing';
import type { Article } from '@/types/article';
import { useTranslation } from 'react-i18next';

export interface PublishButtonProps {
  article: Article;
  disabled?: boolean;
  onSuccess?: (result: PublishResult) => void;
  onError?: (error: Error) => void;
  className?: string;
}

export const PublishButton: React.FC<PublishButtonProps> = ({
  article,
  disabled = false,
  onSuccess,
  onError,
  className,
}) => {
  const { t } = useTranslation();
  const [selectedProvider, setSelectedProvider] = useState<ProviderType>('hybrid');
  const [showProviderDialog, setShowProviderDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // Submit publish request
  const publishMutation = useMutation<PublishResult, AxiosError<{ message?: string }>, PublishRequest>({
    mutationFn: async (request: PublishRequest) => {
      const response = await axios.post<PublishResult>(
        `/api/v1/publish/submit/${request.article_id}`,
        {
          provider: request.provider,
          options: request.options,
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setCurrentTaskId(data.task_id);
      setShowConfirmDialog(false);
      setShowProgressModal(true);
      onSuccess?.(data);
    },
    onError: (error) => {
      const message = error.response?.data?.message ?? error.message;
      alert(t('publishing.messages.publishFailed', { message }));
      onError?.(error);
    },
  });

  // Poll task status
  const { data: task } = useQuery<PublishTask | null>({
    queryKey: ['publish-task', currentTaskId],
    queryFn: async () => {
      if (!currentTaskId) return null;
      const response = await axios.get<PublishTask>(
        `/api/v1/publish/tasks/${currentTaskId}/status`
      );
      return response.data;
    },
    enabled: !!currentTaskId && showProgressModal,
    refetchInterval: ({ state }) => {
      const current = state.data;
      // Poll every 2 seconds if task is still running
      if (
        current &&
        current.status !== 'completed' &&
        current.status !== 'failed'
      ) {
        return 2000;
      }
      return false;
    },
  });

  // Auto-close progress modal after completion
  useEffect(() => {
    if (task && (task.status === 'completed' || task.status === 'failed')) {
      // Keep modal open for 3 seconds after completion for user to see result
      const timer = setTimeout(() => {
        // Don't auto-close if failed, let user manually close
        if (task.status === 'completed') {
          setShowProgressModal(false);
          setCurrentTaskId(null);
        }
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [task]);

  const handlePublishClick = () => {
    setShowProviderDialog(true);
  };

  const handleProviderSelected = () => {
    setShowProviderDialog(false);
    setShowConfirmDialog(true);
  };

  const handleConfirmPublish = () => {
    publishMutation.mutate({
      article_id: article.id,
      provider: selectedProvider,
      options: {
        seo_optimization: !!article.seo_metadata,
        publish_immediately: true,
        tags: article.tags,
        categories: article.categories,
      },
    });
  };

  const handleCloseProgress = () => {
    setShowProgressModal(false);
    setCurrentTaskId(null);
  };

  return (
    <>
      {/* Publish Button */}
      <Button
        variant="primary"
        onClick={handlePublishClick}
        disabled={disabled || publishMutation.isPending}
        className={className}
      >
        <svg
          className="w-5 h-5 mr-2"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
          />
        </svg>
        {t('publishing.actions.publishToWordPress')}
      </Button>

      {/* Provider Selection Dialog */}
      {showProviderDialog && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">
                {t('publishing.providerDialog.title')}
              </h2>
              <button
                type="button"
                onClick={() => setShowProviderDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <ProviderSelectionDropdown
              value={selectedProvider}
              onChange={setSelectedProvider}
            />

            <div className="flex gap-3 justify-end mt-6">
              <Button
                variant="outline"
                onClick={() => setShowProviderDialog(false)}
              >
                {t('publishing.actions.cancel')}
              </Button>
              <Button variant="primary" onClick={handleProviderSelected}>
                {t('publishing.actions.next')}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      <PublishConfirmationDialog
        isOpen={showConfirmDialog}
        onClose={() => setShowConfirmDialog(false)}
        onConfirm={handleConfirmPublish}
        article={article}
        provider={selectedProvider}
        isPublishing={publishMutation.isPending}
        options={{
          seo_optimization: !!article.seo_metadata,
          publish_immediately: true,
          tags: article.tags,
          categories: article.categories,
        }}
      />

      {/* Progress Modal */}
      <PublishProgressModal
        isOpen={showProgressModal}
        onClose={handleCloseProgress}
        task={task || null}
        closeOnOverlayClick={false}
      />
    </>
  );
};
