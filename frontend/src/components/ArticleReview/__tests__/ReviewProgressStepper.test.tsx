/**
 * Tests for ReviewProgressStepper component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReviewProgressStepper } from '../ReviewProgressStepper';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('ReviewProgressStepper', () => {
  const mockOnStepClick = vi.fn();

  const defaultProps = {
    currentStep: 'parsing_review' as const,
    completedSteps: [] as const[],
    onStepClick: mockOnStepClick,
  };

  it('should render all three steps', () => {
    render(<ReviewProgressStepper {...defaultProps} />);

    expect(screen.getByText('articleReview.steps.parsing')).toBeInTheDocument();
    expect(screen.getByText('articleReview.steps.proofreading')).toBeInTheDocument();
    expect(screen.getByText('articleReview.steps.publish')).toBeInTheDocument();
  });

  it('should highlight current step', () => {
    const { rerender } = render(<ReviewProgressStepper {...defaultProps} />);

    // Check parsing_review is active
    let activeStep = screen.getByText('articleReview.steps.parsing').closest('button');
    expect(activeStep).toHaveClass('border-blue-500');

    // Change to proofreading_review
    rerender(
      <ReviewProgressStepper
        {...defaultProps}
        currentStep="proofreading_review"
      />
    );

    activeStep = screen.getByText('articleReview.steps.proofreading').closest('button');
    expect(activeStep).toHaveClass('border-blue-500');
  });

  it('should show completed steps with checkmark', () => {
    render(
      <ReviewProgressStepper
        {...defaultProps}
        currentStep="proofreading_review"
        completedSteps={['parsing_review']}
      />
    );

    const completedStep = screen.getByText('articleReview.steps.parsing').closest('button');
    expect(completedStep).toHaveClass('border-green-500');
  });

  it('should call onStepClick when clicking a step', () => {
    render(<ReviewProgressStepper {...defaultProps} />);

    const proofreadingStep = screen.getByText('articleReview.steps.proofreading');
    proofreadingStep.click();

    expect(mockOnStepClick).toHaveBeenCalledWith('proofreading_review');
  });

  it('should allow clicking completed steps', () => {
    render(
      <ReviewProgressStepper
        {...defaultProps}
        currentStep="publish_preview"
        completedSteps={['parsing_review', 'proofreading_review']}
      />
    );

    const parsingStep = screen.getByText('articleReview.steps.parsing');
    parsingStep.click();

    expect(mockOnStepClick).toHaveBeenCalledWith('parsing_review');
  });

  it('should show step numbers correctly', () => {
    render(<ReviewProgressStepper {...defaultProps} />);

    // Should show numbers 1, 2, 3
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('should connect steps with lines', () => {
    const { container } = render(<ReviewProgressStepper {...defaultProps} />);

    // Check for connector lines between steps
    const lines = container.querySelectorAll('.border-t-2');
    expect(lines.length).toBeGreaterThan(0);
  });

  it('should render with all steps completed', () => {
    render(
      <ReviewProgressStepper
        {...defaultProps}
        currentStep="publish_preview"
        completedSteps={['parsing_review', 'proofreading_review', 'publish_preview']}
      />
    );

    const allSteps = screen.getAllByRole('button');
    allSteps.forEach(step => {
      expect(step).toHaveClass('border-green-500');
    });
  });
});
