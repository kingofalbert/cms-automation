/**
 * ArticleReviewModal - Full-screen modal for article review workflow
 *
 * Phase 8.1: Modal Framework (Updated 2025-12-06)
 * - Provides unified interface for parsing, proofreading, and publishing review
 * - **Removed redundant Tabs** - Stepper serves as both progress indicator AND navigation
 * - Auto-selects appropriate step based on article status
 *
 * Architecture:
 * - Header: Title + "View Original" button + Close button
 * - ReviewProgressStepper: Visual workflow progress + clickable navigation
 * - Content: Direct panel rendering based on current step
 * - Footer: Navigation buttons (Previous, Save Draft, Next/Publish)
 *
 * UX Improvement (2025-12-06):
 * - Removed duplicate navigation (Tabs were redundant with Stepper)
 * - Users can click Stepper circles OR use bottom buttons to navigate
 * - Cleaner visual hierarchy, more content space
 *
 * Feature: View Original Google Doc (2025-12-25)
 * - Added "查看原文" button in header to open original Google Doc in new window
 * - Uses drive_metadata.webViewLink from worklist item
 * - Allows operators to compare AI suggestions with original content
 */

import React, { useEffect, useState, useCallback, useMemo, useRef, Component, ErrorInfo, ReactNode } from 'react';
import { Modal, ModalFooter } from '../ui/Modal';
import { Button } from '../ui';
import { ExternalLink, AlertTriangle, RefreshCw } from 'lucide-react';
import { ReviewProgressStepper } from './ReviewProgressStepper';
import { ParsingReviewPanel, ParsingData, type ParsingReviewPanelHandle } from './ParsingReviewPanel';
import { ProofreadingReviewPanel } from './ProofreadingReviewPanel';
import { PublishPreviewPanel, PublishSettings } from './PublishPreviewPanel';
import { useArticleReviewData } from '../../hooks/articleReview/useArticleReviewData';
import { useReviewWorkflow } from '../../hooks/articleReview/useReviewWorkflow';
import { useKeyboardShortcuts } from '../../hooks/articleReview/useKeyboardShortcuts';
import { worklistAPI } from '../../services/worklist';
import { api } from '../../services/api-client';
import type { WorklistStatus, DecisionPayload } from '../../types/worklist';

/**
 * StepErrorBoundary - Isolates errors in individual step panels
 * Prevents external errors (like browser extension issues) from crashing the entire modal
 */
interface StepErrorBoundaryProps {
  children: ReactNode;
  stepName: string;
  onRetry?: () => void;
}

interface StepErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class StepErrorBoundary extends Component<StepErrorBoundaryProps, StepErrorBoundaryState> {
  constructor(props: StepErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): Partial<StepErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[StepErrorBoundary] Error in ${this.props.stepName}:`, error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-96 p-8">
          <AlertTriangle className="w-16 h-16 text-amber-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {this.props.stepName}加載出錯
          </h3>
          <p className="text-gray-600 mb-4 text-center max-w-md">
            此步驟遇到了問題。這可能是由瀏覽器擴展引起的。
            請嘗試禁用瀏覽器擴展後重試。
          </p>
          {this.state.error && (
            <p className="text-xs text-gray-400 mb-4 font-mono">
              {this.state.error.message}
            </p>
          )}
          <Button onClick={this.handleRetry} className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            重試
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}

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
 * Map worklist status to appropriate step index (0-2)
 */
const getStepFromStatus = (status: WorklistStatus): number => {
  switch (status) {
    case 'parsing':
    case 'parsing_review':
      return 0; // Step 0: 解析审核
    case 'proofreading':
    case 'proofreading_review':
      return 1; // Step 1: 校对审核
    case 'ready_to_publish':
    case 'publishing':
      return 2; // Step 2: 发布预览
    default:
      return 0;
  }
};

/**
 * Map initial tab prop to step index
 */
const getStepFromTab = (tab: 'parsing' | 'proofreading' | 'publish'): number => {
  switch (tab) {
    case 'parsing':
      return 0;
    case 'proofreading':
      return 1;
    case 'publish':
      return 2;
    default:
      return 0;
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

  // Phase 15: Ref for accessing ParsingReviewPanel's current data
  const parsingPanelRef = useRef<ParsingReviewPanelHandle>(null);

  // Workflow state machine (cast string to WorklistStatus if needed)
  const { canGoPrevious, canGoNext, saveProgress } =
    useReviewWorkflow(data?.status as WorklistStatus | undefined);

  // Determine active step (0-2) - replaces activeTab
  const [activeStep, setActiveStep] = useState<number>(
    initialTab
      ? getStepFromTab(initialTab)
      : data?.status
        ? getStepFromStatus(data.status as WorklistStatus)
        : 0
  );

  // Update active step when status changes
  useEffect(() => {
    if (data?.status && !initialTab) {
      setActiveStep(getStepFromStatus(data.status as WorklistStatus));
    }
  }, [data?.status, initialTab]);

  // Track save state
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  // ============================================================
  // LIFTED STATE: Proofreading Decisions
  // Fix for state persistence issue - decisions are now managed here
  // instead of in ProofreadingReviewPanel to survive step navigation
  // See: docs/STATE_PERSISTENCE_FIX.md
  // ============================================================
  const [proofreadingDecisions, setProofreadingDecisionsState] =
    useState<Map<string, DecisionPayload>>(new Map());

  // DEBUG wrapper for tracking decision changes
  const setProofreadingDecisions = useCallback((newDecisions: Map<string, DecisionPayload>) => {
    console.log('🔧 setProofreadingDecisions 被調用 - 新決定數量:', newDecisions.size);
    console.log('🔧 新決定內容:', Array.from(newDecisions.entries()));
    setProofreadingDecisionsState(newDecisions);
  }, []);

  // ============================================================
  // LIFTED STATE: FAQ Data (BUGFIX: FAQ Data Loss on Backtrack)
  // Fix for FAQ data loss when backtracking from Publish Preview to Parsing
  // FAQs are now managed here to survive step navigation
  // Pattern follows proofreading decisions persistence
  // ============================================================
  interface FAQItem {
    question: string;
    answer: string;
  }
  const [parsingFaqs, setParsingFaqs] = useState<FAQItem[]>([]);

  // Restore decisions from backend data when available
  const existingDecisions = useMemo(() => {
    return data?.articleReview?.existing_decisions || [];
  }, [data?.articleReview?.existing_decisions]);

  // Initialize decisions from existing backend data (one-time restore)
  useEffect(() => {
    if (existingDecisions.length > 0 && proofreadingDecisions.size === 0) {
      const restored = new Map<string, DecisionPayload>();
      existingDecisions.forEach((d) => {
        restored.set(d.issue_id, {
          issue_id: d.issue_id,
          decision_type: d.decision_type as 'accepted' | 'rejected' | 'modified',
          modified_content: d.modified_content || undefined,
          feedback_provided: false,
        });
      });
      setProofreadingDecisions(restored);
    }
  }, [existingDecisions, proofreadingDecisions.size]);

  // Initialize FAQ data from backend (one-time restore)
  // This ensures FAQs survive step navigation (backtracking)
  // Note: article_metadata is from the linked article, not worklist metadata
  const existingFaqs = useMemo(() => {
    return (data?.article_metadata?.faq_suggestions as FAQItem[]) || [];
  }, [data?.article_metadata?.faq_suggestions]);

  useEffect(() => {
    // Only initialize if we have backend FAQs and local state is empty
    if (existingFaqs.length > 0 && parsingFaqs.length === 0) {
      console.log('📥 恢復 FAQ 數據:', existingFaqs.length, '條');
      setParsingFaqs(existingFaqs);
    }
  }, [existingFaqs, parsingFaqs.length]);

  // ============================================================
  // AUTO-SAVE: Save current step's data before navigation
  // This ensures all data is persisted when switching steps
  // Phase 15: Now saves ALL parsing fields, not just FAQs
  // ============================================================
  const saveCurrentStepData = useCallback(async (fromStep: number): Promise<boolean> => {
    try {
      // Phase 15: Save ALL parsing data when leaving step 0
      if (fromStep === 0) {
        // Get current data from ParsingReviewPanel via ref
        const currentData = parsingPanelRef.current?.getCurrentData();
        const isDirty = parsingPanelRef.current?.isDirty() ?? false;

        // Only save if there's data and it's dirty (or has FAQs to sync)
        if (currentData && (isDirty || parsingFaqs.length > 0)) {
          setIsSaving(true);
          console.log('💾 自動保存解析數據:', {
            title: currentData.title?.slice(0, 20),
            author: currentData.author?.slice(0, 20),
            faqCount: currentData.faq_suggestions?.length || 0,
            tagsCount: currentData.tags?.length || 0,
            primaryCategory: currentData.primary_category,
          });

          // Save all parsing data to article
          await api.patch(`/v1/articles/${articleId}`, {
            title: currentData.title,
            author: currentData.author,
            meta_description: currentData.seo_metadata?.meta_description,
            seo_keywords: currentData.seo_metadata?.keywords,
            metadata: {
              featured_image_path: currentData.featured_image_path,
              additional_images: currentData.additional_images,
              faq_suggestions: currentData.faq_suggestions || parsingFaqs,
              // Phase 15: Include all new fields
              tags: currentData.tags,
              excerpt: currentData.excerpt,
            },
            // Phase 15: Save categories
            primary_category: currentData.primary_category,
            secondary_categories: currentData.secondary_categories,
          });

          // Phase 13 v2.3: Also update ArticleFAQ table and regenerate faq_html
          const faqsToSave = currentData.faq_suggestions || parsingFaqs;
          if (faqsToSave.length > 0) {
            try {
              await api.put(`/v1/articles/${articleId}/faqs`, {
                faqs: faqsToSave.map(faq => ({
                  question: faq.question,
                  answer: faq.answer,
                })),
                regenerate_html: true,
              });
              console.log('✅ 解析數據已自動保存 (含 FAQ 和 faq_html 更新)');
            } catch (faqErr) {
              console.warn('FAQ 表更新失敗，但其他數據已保存:', faqErr);
            }
          } else {
            console.log('✅ 解析數據已自動保存');
          }
          // Phase 15: Reset dirty flag and refetch to sync with backend after auto-save
          parsingPanelRef.current?.resetDirty();
          refetch();
        }
      }

      // Save proofreading decisions when leaving step 1
      console.log('🔍 saveCurrentStepData - fromStep:', fromStep, ', proofreadingDecisions.size:', proofreadingDecisions.size);
      if (fromStep === 1 && proofreadingDecisions.size > 0) {
        console.log('✅ 條件滿足，開始保存校對決定...');
        setIsSubmitting(true);
        const decisionList = Array.from(proofreadingDecisions.values());
        console.log('📤 決定列表:', decisionList);
        await worklistAPI.saveReviewDecisions(worklistItemId, {
          decisions: decisionList.map(d => ({
            issue_id: d.issue_id,
            decision_type: d.decision_type,
            modified_content: d.modified_content,
            decision_rationale: d.decision_rationale,
            feedback_provided: d.feedback_provided,
            feedback_category: d.feedback_category,
            feedback_notes: d.feedback_notes,
          })),
        });
        console.log('✅ 校對決定已自動保存');
        // Refetch to sync with backend
        refetch();
      }
      return true;
    } catch (err) {
      console.error('❌ 自動保存失敗:', err);
      // Don't block navigation on save failure, but show warning
      console.warn('數據將在下次保存時同步');
      return true; // Allow navigation even on error
    } finally {
      setIsSaving(false);
      setIsSubmitting(false);
    }
  }, [proofreadingDecisions, parsingFaqs, worklistItemId, articleId, refetch]);

  // Navigation handlers for stepper and buttons
  // Wrapped in try-catch to prevent browser extension errors from crashing the app
  const goToPreviousStep = useCallback(async () => {
    if (activeStep > 0) {
      try {
        // Auto-save current step before navigating
        await saveCurrentStepData(activeStep);
        setActiveStep(activeStep - 1);
      } catch (err) {
        console.error('[Navigation] Error navigating to previous step:', err);
        // Still allow navigation even if save failed
        setActiveStep(activeStep - 1);
      }
    }
  }, [activeStep, saveCurrentStepData]);

  const goToNextStep = useCallback(async () => {
    if (activeStep < 2) {
      try {
        // Auto-save current step before navigating
        await saveCurrentStepData(activeStep);
        setActiveStep(activeStep + 1);
      } catch (err) {
        console.error('[Navigation] Error navigating to next step:', err);
        // Still allow navigation even if save failed
        setActiveStep(activeStep + 1);
      }
    }
  }, [activeStep, saveCurrentStepData]);

  const handleStepClick = useCallback(async (stepId: number) => {
    if (stepId !== activeStep) {
      try {
        // Auto-save current step before navigating
        await saveCurrentStepData(activeStep);
        setActiveStep(stepId);
      } catch (err) {
        console.error('[Navigation] Error navigating to step', stepId, ':', err);
        // Still allow navigation even if save failed
        setActiveStep(stepId);
      }
    }
  }, [activeStep, saveCurrentStepData]);

  // Handle save parsing data
  const handleSaveParsingData = useCallback(async (parsingData: ParsingData) => {
    setIsSaving(true);
    try {
      // Call API to save parsing data to article
      console.log('Saving parsing data:', parsingData);

      // Save to article metadata via PATCH endpoint
      // BUGFIX: Include primary_category and secondary_categories
      await api.patch(`/v1/articles/${articleId}`, {
        title: parsingData.title,
        author: parsingData.author,
        metadata: {
          featured_image_path: parsingData.featured_image_path,
          additional_images: parsingData.additional_images,
          faq_suggestions: parsingData.faq_suggestions,
          tags: parsingData.tags,
          excerpt: parsingData.excerpt,
        },
        meta_description: parsingData.seo_metadata?.meta_description,
        seo_keywords: parsingData.seo_metadata?.keywords,
        // BUGFIX: Save categories (was missing before)
        primary_category: parsingData.primary_category,
        secondary_categories: parsingData.secondary_categories,
      });

      // Phase 13 v2.3: Update ArticleFAQ table and regenerate faq_html
      // This ensures user-selected FAQs are persisted correctly
      if (parsingData.faq_suggestions && parsingData.faq_suggestions.length > 0) {
        try {
          const faqUpdateResponse = await api.put<{
            article_id: number;
            faq_count: number;
            faq_html: string | null;
          }>(`/v1/articles/${articleId}/faqs`, {
            faqs: parsingData.faq_suggestions.map(faq => ({
              question: faq.question,
              answer: faq.answer,
            })),
            regenerate_html: true,
          });
          console.log('FAQ 數據已更新:', faqUpdateResponse.faq_count, '條');
        } catch (faqErr) {
          console.error('FAQ 更新失敗:', faqErr);
          // Don't block the main save on FAQ update failure
        }
      }

      // Invalidate cache to refetch updated data
      refetch();

      console.log('解析数据保存成功！');
    } catch (err) {
      console.error('Failed to save parsing data:', err);
      alert('保存失败：' + (err as Error).message);
    } finally {
      setIsSaving(false);
    }
  }, [refetch, articleId]);

  // Handle submit proofreading decisions
  const handleSubmitProofreadingDecisions = useCallback(async (decisions: DecisionPayload[]) => {
    setIsSubmitting(true);
    try {
      // Call API to save proofreading decisions to database
      console.log('Submitting proofreading decisions:', decisions);

      // Use worklistAPI to save review decisions
      const response = await worklistAPI.saveReviewDecisions(worklistItemId, {
        decisions: decisions.map(d => ({
          issue_id: d.issue_id,
          decision_type: d.decision_type,
          modified_content: d.modified_content,
          decision_rationale: d.decision_rationale,
          feedback_provided: d.feedback_provided,
          feedback_category: d.feedback_category,
          feedback_notes: d.feedback_notes,
        })),
      });

      console.log('校对决定提交成功！', response);

      // Invalidate cache to refetch updated data
      refetch();
    } catch (err) {
      console.error('Failed to submit proofreading decisions:', err);
      alert('提交失败：' + (err as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  }, [refetch, worklistItemId]);

  // Handle publish article
  const handlePublish = useCallback(async (settings: PublishSettings) => {
    setIsPublishing(true);
    try {
      // Call API to publish article
      console.log('Publishing article with settings:', settings);

      // First save publish settings to article
      await api.patch(`/v1/articles/${articleId}`, {
        primary_category: settings.primary_category,
        secondary_categories: settings.secondary_categories,
        tags: settings.tags,
        scheduled_publish_time: settings.publish_date,
        excerpt: settings.excerpt,
      });

      // Then trigger publish via worklist endpoint
      await api.post(`/v1/worklist/${worklistItemId}/publish`, {
        publish_settings: settings,
      });

      console.log('文章发布成功！');

      // Invalidate cache to refetch updated data
      refetch();

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
  }, [refetch, onClose, articleId, worklistItemId]);

  // Handle save draft (Ctrl+S)
  // BUGFIX: Now saves step-specific data (FAQs, proofreading decisions) in addition to workflow progress
  const handleSaveDraft = useCallback(async () => {
    setIsSaving(true);
    try {
      // Save current step's data (FAQs for step 0, decisions for step 1)
      await saveCurrentStepData(activeStep);
      // Also save workflow progress
      await saveProgress();
      console.log('Draft saved successfully (including step data)');
    } catch (err) {
      console.error('Failed to save draft:', err);
    } finally {
      setIsSaving(false);
    }
  }, [saveProgress, saveCurrentStepData, activeStep]);

  // Handle close (Esc) - Auto-save current step data before closing
  const handleClose = useCallback(async () => {
    // Phase 15: Auto-save current step data before closing modal
    // This ensures proofreading decisions and other data are not lost
    console.log('🔍 handleClose 被調用 - activeStep:', activeStep, ', proofreadingDecisions.size:', proofreadingDecisions.size);
    console.log('🔍 proofreadingDecisions 內容:', Array.from(proofreadingDecisions.entries()));
    try {
      await saveCurrentStepData(activeStep);
      console.log('✅ 關閉前自動保存完成');
    } catch (err) {
      console.warn('關閉前自動保存失敗，但仍會關閉:', err);
    }
    onClose();
  }, [onClose, saveCurrentStepData, activeStep, proofreadingDecisions]);

  // Setup keyboard shortcuts
  useKeyboardShortcuts({
    enabled: isOpen,
    onSave: handleSaveDraft,
    onClose: handleClose,
    onNext: activeStep < 2 ? goToNextStep : undefined,
    onPrevious: activeStep > 0 ? goToPreviousStep : undefined,
  });

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
          {/* View Original Google Doc Button */}
          {typeof data.drive_metadata?.webViewLink === 'string' && (
            <a
              href={data.drive_metadata.webViewLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
              title="在新窗口中打开原始 Google Doc"
            >
              <ExternalLink className="w-4 h-4" />
              查看原文
            </a>
          )}
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

      {/* Progress Stepper - Now clickable for navigation */}
      <div className="px-6 py-4 bg-gray-50 border-b">
        <ReviewProgressStepper
          currentStep={activeStep}
          onStepClick={handleStepClick}
        />
      </div>

      {/* Step Content - Direct rendering based on activeStep (no redundant Tabs) */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0 flex flex-col">
        <div className="p-6 flex-1 flex flex-col min-h-0">
          {/* Step 0: 解析审核 (Parsing Review) */}
          {activeStep === 0 && (
            <ParsingReviewPanel
              ref={parsingPanelRef}
              data={data}
              onSave={handleSaveParsingData}
              isSaving={isSaving}
              // BUGFIX: Lifted FAQ state for persistence during backtracking
              faqs={parsingFaqs}
              onFaqsChange={setParsingFaqs}
            />
          )}

          {/* Step 1: 校对审核 (Proofreading Review) */}
          {activeStep === 1 && (
            <ProofreadingReviewPanel
              data={data}
              decisions={proofreadingDecisions}
              onDecisionsChange={setProofreadingDecisions}
              onSubmitDecisions={handleSubmitProofreadingDecisions}
              isSubmitting={isSubmitting}
              onAllDecisionsComplete={goToNextStep}
            />
          )}

          {/* Step 2: 发布预览 (Publish Preview) */}
          {/* Wrapped in StepErrorBoundary to isolate potential browser extension errors */}
          {activeStep === 2 && (
            <StepErrorBoundary stepName="發布預覽" onRetry={refetch}>
              <PublishPreviewPanel
                data={data}
                faqs={parsingFaqs}
                onPublish={handlePublish}
                isPublishing={isPublishing}
              />
            </StepErrorBoundary>
          )}
        </div>
      </div>

      {/* Footer */}
      <ModalFooter className="sticky bottom-0 z-10">
        <div className="flex items-center justify-between w-full">
          <Button
            variant="outline"
            onClick={goToPreviousStep}
            disabled={activeStep === 0}
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
              onClick={goToNextStep}
              disabled={activeStep === 2}
              className="min-w-32"
            >
              {activeStep === 2 ? '发布' : '下一步'}
            </Button>
          </div>
        </div>
      </ModalFooter>
    </Modal>
  );
};

ArticleReviewModal.displayName = 'ArticleReviewModal';
