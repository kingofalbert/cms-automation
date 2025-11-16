/**
 * ArticleReviewModal - Full-screen modal for article review workflow
 *
 * Phase 8.1: Modal Framework
 * - Provides unified interface for parsing, proofreading, and publishing review
 * - Eliminates page jumps with tab-based navigation
 * - Auto-selects appropriate tab based on article status
 *
 * Architecture:
 * - Header: Title + Close button
 * - ReviewProgressStepper: Visual workflow progress
 * - Tabs: Parsing | Proofreading | Publish
 * - Footer: Navigation buttons (Previous, Save Draft, Next/Publish)
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Modal, ModalFooter } from '../ui/Modal';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/Tabs';
import { Button } from '../ui';
import { ReviewProgressStepper } from './ReviewProgressStepper';
import { ParsingReviewPanel, ParsingData } from './ParsingReviewPanel';
import { ProofreadingReviewPanel } from './ProofreadingReviewPanel';
import { PublishPreviewPanel, PublishSettings } from './PublishPreviewPanel';
import { useArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import { useReviewWorkflow } from '../../hooks/articleReview/useReviewWorkflow';
import { useKeyboardShortcuts } from '../../hooks/articleReview/useKeyboardShortcuts';
import type { WorklistStatus, DecisionPayload } from '../../types/worklist';

export interface ArticleReviewModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal is closed */
  onClose: () => void;
  /** Worklist item ID to review */
  worklistItemId: number;
  /** Linked article ID for review data */
  articleId: number;
  /** Optional: Force specific tab on open */
  initialTab?: 'parsing' | 'proofreading' | 'publish';
}

/**
 * Map worklist status to appropriate review tab
 */
const getTabFromStatus = (status: WorklistStatus): 'parsing' | 'proofreading' | 'publish' => {
  switch (status) {
    case 'parsing':
    case 'parsing_review':
      return 'parsing';
    case 'proofreading':
    case 'proofreading_review':
      return 'proofreading';
    case 'ready_to_publish':
    case 'publishing':
      return 'publish';
    default:
      return 'parsing';
  }
};

/**
 * ArticleReviewModal Component
 */
export const ArticleReviewModal: React.FC<ArticleReviewModalProps> = ({
  isOpen,
  onClose,
  worklistItemId,
  articleId,
  initialTab,
}) => {
  // Fetch article review data
  const { data, isLoading, error, refetch } = useArticleReviewData(
    worklistItemId,
    articleId,
    isOpen
  );

  // Workflow state machine (cast string to WorklistStatus if needed)
  const { currentStep, canGoPrevious, canGoNext, goToPrevious, goToNext, saveProgress } =
    useReviewWorkflow(data?.status as WorklistStatus | undefined);

  // Determine active tab
  const [activeTab, setActiveTab] = useState<'parsing' | 'proofreading' | 'publish'>(
    initialTab || (data?.status ? getTabFromStatus(data.status as WorklistStatus) : 'parsing')
  );

  // Update active tab when status changes
  useEffect(() => {
    if (data?.status && !initialTab) {
      setActiveTab(getTabFromStatus(data.status as WorklistStatus));
    }
  }, [data?.status, initialTab]);

  // Track save state
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  // Handle save parsing data
  const handleSaveParsingData = useCallback(async (parsingData: ParsingData) => {
    setIsSaving(true);
    try {
      // TODO: Call API to save parsing data
      console.log('Saving parsing data:', parsingData);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock API call

      // Invalidate cache to refetch updated data
      refetch();

      // TODO: Show success toast
      alert('解析数据保存成功！');
    } catch (err) {
      console.error('Failed to save parsing data:', err);
      alert('保存失败：' + (err as Error).message);
    } finally {
      setIsSaving(false);
    }
  }, [refetch]);

  // Handle submit proofreading decisions
  const handleSubmitProofreadingDecisions = useCallback(async (decisions: DecisionPayload[]) => {
    setIsSubmitting(true);
    try {
      // TODO: Call API to submit proofreading decisions
      console.log('Submitting proofreading decisions:', decisions);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock API call

      // Invalidate cache to refetch updated data
      refetch();

      // TODO: Show success toast
      alert('校对决定提交成功！');
    } catch (err) {
      console.error('Failed to submit proofreading decisions:', err);
      alert('提交失败：' + (err as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  }, [refetch]);

  // Handle publish article
  const handlePublish = useCallback(async (settings: PublishSettings) => {
    setIsPublishing(true);
    try {
      // TODO: Call API to publish article
      console.log('Publishing article with settings:', settings);
      await new Promise(resolve => setTimeout(resolve, 2000)); // Mock API call

      // Invalidate cache to refetch updated data
      refetch();

      // TODO: Show success toast
      alert('文章发布成功！');

      // Close modal after successful publish
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err) {
      console.error('Failed to publish article:', err);
      alert('发布失败：' + (err as Error).message);
    } finally {
      setIsPublishing(false);
    }
  }, [refetch, onClose]);

  // Handle save draft (Ctrl+S)
  const handleSaveDraft = useCallback(async () => {
    try {
      await saveProgress();
      // TODO: Show success toast
      console.log('Draft saved successfully');
    } catch (err) {
      // TODO: Show error toast
      console.error('Failed to save draft:', err);
    }
  }, [saveProgress]);

  // Handle close (Esc)
  const handleClose = useCallback(() => {
    // TODO: Check for unsaved changes
    onClose();
  }, [onClose]);

  // Setup keyboard shortcuts
  useKeyboardShortcuts({
    enabled: isOpen,
    onSave: handleSaveDraft,
    onClose: handleClose,
    onNext: canGoNext ? goToNext : undefined,
    onPrevious: canGoPrevious ? goToPrevious : undefined,
  });

  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value as 'parsing' | 'proofreading' | 'publish');
  };

  // Loading state
  if (isLoading) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size="full"
        closeOnOverlayClick={false}
        className="h-screen max-h-screen"
      >
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4" />
            <p className="text-gray-600">加载文章审核数据...</p>
          </div>
        </div>
      </Modal>
    );
  }

  // Error state
  if (error) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        size="full"
        className="h-screen max-h-screen"
      >
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <svg
                className="w-16 h-16 mx-auto"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
            <p className="text-gray-600 mb-4">{error.message || '无法加载文章审核数据'}</p>
            <Button onClick={() => refetch()}>重试</Button>
          </div>
        </div>
      </Modal>
    );
  }

  // No data state
  if (!data) {
    return null;
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      size="full"
      closeOnOverlayClick={false}
      customContent={true}
      className="h-screen max-h-screen flex flex-col min-h-0"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b bg-white sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-gray-900">文章审核</h2>
          <span className="text-sm text-gray-500">#{worklistItemId}</span>
          {data.title && (
            <span className="text-sm text-gray-700 font-medium max-w-md truncate">
              {data.title}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={handleClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="关闭审核"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Progress Stepper */}
      <div className="px-6 py-4 bg-gray-50 border-b">
        <ReviewProgressStepper currentStep={currentStep} />
      </div>

      {/* Tabs Navigation */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <Tabs defaultValue="parsing" value={activeTab} onValueChange={handleTabChange} className="flex-1 flex flex-col min-h-0">
          {/* Tab Headers */}
          <div className="px-6 pt-4 border-b bg-white flex-shrink-0">
            <TabsList className="w-full justify-start">
              <TabsTrigger value="parsing" className="flex-1 max-w-xs">
                解析审核
              </TabsTrigger>
              <TabsTrigger value="proofreading" className="flex-1 max-w-xs">
                校对审核
              </TabsTrigger>
              <TabsTrigger value="publish" className="flex-1 max-w-xs">
                发布预览
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Tab Content - Scrollable container */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
            <TabsContent value="parsing" className="p-6 mt-0">
              {/* Phase 8.2: ParsingReviewPanel */}
              <ParsingReviewPanel
                data={data}
                onSave={handleSaveParsingData}
                isSaving={isSaving}
              />
            </TabsContent>

            <TabsContent value="proofreading" className="p-6 mt-0">
              {/* Phase 8.3: ProofreadingReviewPanel */}
              <ProofreadingReviewPanel
                data={data}
                onSubmitDecisions={handleSubmitProofreadingDecisions}
                isSubmitting={isSubmitting}
              />
            </TabsContent>

            <TabsContent value="publish" className="p-6 mt-0">
              {/* Phase 8.4: PublishPreviewPanel */}
              <PublishPreviewPanel
                data={data}
                onPublish={handlePublish}
                isPublishing={isPublishing}
              />
            </TabsContent>
          </div>
        </Tabs>
      </div>

      {/* Footer */}
      <ModalFooter className="sticky bottom-0 z-10">
        <div className="flex items-center justify-between w-full">
          <Button
            variant="outline"
            onClick={goToPrevious}
            disabled={!canGoPrevious}
          >
            上一步
          </Button>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleSaveDraft}
            >
              保存草稿 (Ctrl+S)
            </Button>

            <Button
              onClick={goToNext}
              disabled={!canGoNext}
              className="min-w-32"
            >
              {currentStep === 2 ? '发布' : '下一步'}
            </Button>
          </div>
        </div>
      </ModalFooter>
    </Modal>
  );
};

ArticleReviewModal.displayName = 'ArticleReviewModal';
