/**
 * Tests for useReviewWorkflow hook
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useReviewWorkflow } from '../useReviewWorkflow';

describe('useReviewWorkflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with step 0 (parsing_review)', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    expect(result.current.currentStep).toBe(0);
    expect(result.current.canGoNext).toBe(true);
    expect(result.current.canGoPrevious).toBe(false);
    expect(result.current.targetStatus).toBe('parsing_review');
  });

  it('should navigate to next step', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    act(() => {
      result.current.goToNext();
    });

    expect(result.current.currentStep).toBe(1);
    expect(result.current.canGoNext).toBe(true);
    expect(result.current.canGoPrevious).toBe(true);
    expect(result.current.targetStatus).toBe('proofreading_review');
  });

  it('should navigate to previous step', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    // Go to second step
    act(() => {
      result.current.goToNext();
    });

    expect(result.current.currentStep).toBe(1);

    // Go back
    act(() => {
      result.current.goToPrevious();
    });

    expect(result.current.currentStep).toBe(0);
  });

  it('should navigate to last step', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    act(() => {
      result.current.goToNext();
      result.current.goToNext();
    });

    expect(result.current.currentStep).toBe(2);
    expect(result.current.canGoNext).toBe(false);
    expect(result.current.canGoPrevious).toBe(true);
    expect(result.current.targetStatus).toBe('ready_to_publish');
  });

  it('should jump to specific step', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    act(() => {
      result.current.goToStep(2);
    });

    expect(result.current.currentStep).toBe(2);
  });

  it('should not go beyond last step', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    act(() => {
      result.current.goToStep(2);
      result.current.goToNext();
    });

    expect(result.current.currentStep).toBe(2);
  });

  it('should not go before first step', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    act(() => {
      result.current.goToPrevious();
    });

    expect(result.current.currentStep).toBe(0);
  });

  it('should initialize with correct step based on status', () => {
    const { result: result1 } = renderHook(() => useReviewWorkflow('parsing_review'));
    expect(result1.current.currentStep).toBe(0);

    const { result: result2 } = renderHook(() => useReviewWorkflow('proofreading_review'));
    expect(result2.current.currentStep).toBe(1);

    const { result: result3 } = renderHook(() => useReviewWorkflow('ready_to_publish'));
    expect(result3.current.currentStep).toBe(2);
  });

  it('should track dirty state when step differs from status', () => {
    const { result } = renderHook(() => useReviewWorkflow('parsing_review'));

    expect(result.current.isDirty).toBe(false);

    act(() => {
      result.current.goToNext();
    });

    expect(result.current.isDirty).toBe(true);
  });

  it('should reset to status-based step', () => {
    const { result } = renderHook(() => useReviewWorkflow('parsing_review'));

    act(() => {
      result.current.goToNext();
    });

    expect(result.current.currentStep).toBe(1);
    expect(result.current.isDirty).toBe(true);

    act(() => {
      result.current.resetToStatus();
    });

    expect(result.current.currentStep).toBe(0);
    expect(result.current.isDirty).toBe(false);
  });

  it('should save progress without changing step', async () => {
    const { result } = renderHook(() => useReviewWorkflow());
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    await act(async () => {
      await result.current.saveProgress();
    });

    expect(consoleLogSpy).toHaveBeenCalledWith('Saving progress for step:', 0);
    expect(result.current.currentStep).toBe(0);

    consoleLogSpy.mockRestore();
  });

  it('should complete step and move to next', async () => {
    const { result } = renderHook(() => useReviewWorkflow());
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    await act(async () => {
      await result.current.completeStep();
    });

    expect(consoleLogSpy).toHaveBeenCalledWith('Completing step:', 0, '→ status:', 'parsing_review');
    expect(result.current.currentStep).toBe(1);

    consoleLogSpy.mockRestore();
  });

  it('should handle failed status by resetting to step 0', () => {
    const { result } = renderHook(() => useReviewWorkflow('failed'));
    expect(result.current.currentStep).toBe(0);
  });

  it('should validate step boundaries', () => {
    const { result } = renderHook(() => useReviewWorkflow());

    // Try to jump to invalid steps
    act(() => {
      result.current.goToStep(-1);
    });
    expect(result.current.currentStep).toBe(0); // Should not change

    act(() => {
      result.current.goToStep(10);
    });
    expect(result.current.currentStep).toBe(0); // Should not change

    // Jump to valid step
    act(() => {
      result.current.goToStep(1);
    });
    expect(result.current.currentStep).toBe(1);
  });
});
