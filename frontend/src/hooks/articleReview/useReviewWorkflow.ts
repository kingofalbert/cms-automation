/**
 * useReviewWorkflow - State machine for article review workflow
 *
 * Phase 8.1: Modal Framework
 * - Manages workflow state transitions
 * - Determines current step based on status
 * - Validates navigation between steps
 * - Handles save progress
 *
 * Workflow Steps:
 * - Step 0: Parsing Review (parsing, parsing_review)
 * - Step 1: Proofreading Review (proofreading, proofreading_review)
 * - Step 2: Publish Preview (ready_to_publish, publishing)
 */

import { useState, useCallback, useMemo } from 'react';
import type { WorklistStatus } from '../../types/worklist';

/**
 * Map worklist status to workflow step (0-2)
 */
const getStepFromStatus = (status?: WorklistStatus): number => {
  if (!status) return 0;

  switch (status) {
    case 'pending':
    case 'parsing':
    case 'parsing_review':
      return 0; // Parsing Review

    case 'proofreading':
    case 'proofreading_review':
      return 1; // Proofreading Review

    case 'ready_to_publish':
    case 'publishing':
    case 'published':
      return 2; // Publish Preview

    case 'failed':
      return 0; // Reset to parsing for failed items

    default:
      return 0;
  }
};

/**
 * Get target status for step transition
 */
const getTargetStatusForStep = (step: number): WorklistStatus => {
  switch (step) {
    case 0:
      return 'parsing_review';
    case 1:
      return 'proofreading_review';
    case 2:
      return 'ready_to_publish';
    default:
      return 'parsing_review';
  }
};

export interface ReviewWorkflowState {
  currentStep: number;
  canGoPrevious: boolean;
  canGoNext: boolean;
  targetStatus: WorklistStatus;
}

/**
 * Hook: useReviewWorkflow
 */
export const useReviewWorkflow = (currentStatus?: WorklistStatus) => {
  // Determine initial step from status
  const initialStep = useMemo(() => getStepFromStatus(currentStatus), [currentStatus]);

  // Local state for step (can differ from status during editing)
  const [localStep, setLocalStep] = useState<number>(initialStep);

  // Use local step if different from status-based step, otherwise use status-based
  const currentStep = localStep;

  // Navigation guards
  const canGoPrevious = currentStep > 0;
  const canGoNext = currentStep < 2;

  /**
   * Navigate to previous step
   */
  const goToPrevious = useCallback(() => {
    if (canGoPrevious) {
      setLocalStep((prev) => Math.max(0, prev - 1));
    }
  }, [canGoPrevious]);

  /**
   * Navigate to next step
   */
  const goToNext = useCallback(() => {
    if (canGoNext) {
      setLocalStep((prev) => Math.min(2, prev + 1));
      // TODO: Phase 8.2-8.4 - Validate step data before proceeding
    }
  }, [canGoNext]);

  /**
   * Jump to specific step
   */
  const goToStep = useCallback((step: number) => {
    if (step >= 0 && step <= 2) {
      setLocalStep(step);
    }
  }, []);

  /**
   * Save current progress (without changing status)
   */
  const saveProgress = useCallback(async () => {
    // TODO: Phase 8.2-8.4 - Implement save logic for each step
    console.log('Saving progress for step:', currentStep);

    // This would call different save endpoints based on current step:
    // - Step 0: Save parsing data (title, author, images, SEO, FAQ)
    // - Step 1: Save proofreading decisions
    // - Step 2: Save publish settings

    return Promise.resolve();
  }, [currentStep]);

  /**
   * Complete current step and transition status
   */
  const completeStep = useCallback(async () => {
    const targetStatus = getTargetStatusForStep(currentStep);

    // TODO: Phase 8.2-8.4 - Implement status transition API call
    console.log('Completing step:', currentStep, '→ status:', targetStatus);

    // After successful status change, move to next step
    if (canGoNext) {
      setLocalStep((prev) => prev + 1);
    }

    return Promise.resolve();
  }, [currentStep, canGoNext]);

  /**
   * Reset to status-based step (discard local changes)
   */
  const resetToStatus = useCallback(() => {
    setLocalStep(initialStep);
  }, [initialStep]);

  /**
   * Check if current step is dirty (differs from status)
   */
  const isDirty = useMemo(() => {
    return localStep !== initialStep;
  }, [localStep, initialStep]);

  return {
    currentStep,
    canGoPrevious,
    canGoNext,
    goToPrevious,
    goToNext,
    goToStep,
    saveProgress,
    completeStep,
    resetToStatus,
    isDirty,
    targetStatus: getTargetStatusForStep(currentStep),
  };
};

/**
 * Hook: useWorkflowValidation
 * Validates data for each workflow step
 */
export const useWorkflowValidation = (step: number, data: unknown) => {
  // TODO: Phase 8.2-8.4 - Implement validation for each step

  const validate = useCallback((): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    switch (step) {
      case 0: // Parsing Review
        // Validate title, author, images, SEO, FAQ
        // if (!data.title) errors.push('标题不能为空');
        break;

      case 1: // Proofreading Review
        // Validate all issues are reviewed
        // if (pendingIssues > 0) errors.push(`还有 ${pendingIssues} 个问题待审核`);
        break;

      case 2: // Publish Preview
        // Validate publish settings
        // if (!data.publishSettings) errors.push('请配置发布设置');
        break;
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, [step, data]);

  return { validate };
};
