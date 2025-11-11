/**
 * Tests for TitleReviewSection component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TitleReviewSection } from '../TitleReviewSection';

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('TitleReviewSection', () => {
  const mockOnApprove = vi.fn();
  const mockOnEdit = vi.fn();

  const defaultProps = {
    original: 'Original Title',
    suggested: 'AI Suggested Title',
    onApprove: mockOnApprove,
    onEdit: mockOnEdit,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render original and suggested titles', () => {
    render(<TitleReviewSection {...defaultProps} />);

    expect(screen.getByText('Original Title')).toBeInTheDocument();
    expect(screen.getByText('AI Suggested Title')).toBeInTheDocument();
  });

  it('should show section header', () => {
    render(<TitleReviewSection {...defaultProps} />);

    expect(screen.getByText('articleReview.parsing.title')).toBeInTheDocument();
  });

  it('should show approve button', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const approveButton = screen.getByRole('button', {
      name: /approve|articleReview.actions.approve/i,
    });
    expect(approveButton).toBeInTheDocument();
  });

  it('should call onApprove when approve button is clicked', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const approveButton = screen.getByRole('button', {
      name: /approve|articleReview.actions.approve/i,
    });
    fireEvent.click(approveButton);

    expect(mockOnApprove).toHaveBeenCalledWith('AI Suggested Title');
  });

  it('should show edit button', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const editButton = screen.getByRole('button', {
      name: /edit|articleReview.actions.edit/i,
    });
    expect(editButton).toBeInTheDocument();
  });

  it('should switch to edit mode when edit button is clicked', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const editButton = screen.getByRole('button', {
      name: /edit|articleReview.actions.edit/i,
    });
    fireEvent.click(editButton);

    // Should show input field
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('AI Suggested Title');
  });

  it('should save edited title', () => {
    render(<TitleReviewSection {...defaultProps} />);

    // Enter edit mode
    const editButton = screen.getByRole('button', {
      name: /edit|articleReview.actions.edit/i,
    });
    fireEvent.click(editButton);

    // Edit the title
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Edited Title' } });

    // Save
    const saveButton = screen.getByRole('button', {
      name: /save|articleReview.actions.save/i,
    });
    fireEvent.click(saveButton);

    expect(mockOnEdit).toHaveBeenCalledWith('Edited Title');
  });

  it('should cancel editing', () => {
    render(<TitleReviewSection {...defaultProps} />);

    // Enter edit mode
    const editButton = screen.getByRole('button', {
      name: /edit|articleReview.actions.edit/i,
    });
    fireEvent.click(editButton);

    // Edit the title
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Edited Title' } });

    // Cancel
    const cancelButton = screen.getByRole('button', {
      name: /cancel|articleReview.actions.cancel/i,
    });
    fireEvent.click(cancelButton);

    // Should not call onEdit
    expect(mockOnEdit).not.toHaveBeenCalled();

    // Should exit edit mode and show original suggested title
    expect(screen.getByText('AI Suggested Title')).toBeInTheDocument();
  });

  it('should handle empty suggested title', () => {
    render(
      <TitleReviewSection
        {...defaultProps}
        suggested=""
      />
    );

    // Should fallback to original
    expect(screen.getAllByText('Original Title').length).toBeGreaterThan(0);
  });

  it('should show difference indicator when titles differ', () => {
    render(<TitleReviewSection {...defaultProps} />);

    // Should show both original and suggested (different values)
    expect(screen.getByText('Original Title')).toBeInTheDocument();
    expect(screen.getByText('AI Suggested Title')).toBeInTheDocument();
  });

  it('should highlight suggested title when different from original', () => {
    const { container } = render(<TitleReviewSection {...defaultProps} />);

    // Check if suggested title has highlighting class
    const suggestedElement = screen.getByText('AI Suggested Title').closest('div');
    expect(suggestedElement).toHaveClass('bg-blue-50');
  });

  it('should disable approve button when suggested equals original', () => {
    render(
      <TitleReviewSection
        {...defaultProps}
        original="Same Title"
        suggested="Same Title"
      />
    );

    const approveButton = screen.getByRole('button', {
      name: /approve|articleReview.actions.approve/i,
    });
    expect(approveButton).toBeDisabled();
  });
});
