/**
 * Tests for TitleReviewSection component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TitleReviewSection } from '../TitleReviewSection';

describe('TitleReviewSection', () => {
  const mockOnTitleChange = vi.fn();

  const defaultProps = {
    title: 'Current Article Title',
    originalTitle: 'Original Article Title',
    worklistItemId: 123,
    onTitleChange: mockOnTitleChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render section heading', () => {
    render(<TitleReviewSection {...defaultProps} />);
    expect(screen.getByText('标题审核')).toBeInTheDocument();
  });

  it('should render current title input with character count', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue('Current Article Title');

    // Check character count
    expect(screen.getByText(/21 字符/)).toBeInTheDocument();
  });

  it('should show "已修改" badge when title differs from original', () => {
    render(<TitleReviewSection {...defaultProps} />);
    expect(screen.getByText('已修改')).toBeInTheDocument();
  });

  it('should not show "已修改" badge when title equals original', () => {
    render(
      <TitleReviewSection
        {...defaultProps}
        title="Same Title"
        originalTitle="Same Title"
      />
    );
    expect(screen.queryByText('已修改')).not.toBeInTheDocument();
  });

  it('should show original title when modified', () => {
    render(<TitleReviewSection {...defaultProps} />);

    expect(screen.getByText('原始标题')).toBeInTheDocument();
    expect(screen.getByText('Original Article Title')).toBeInTheDocument();
  });

  it('should not show original title section when not modified', () => {
    render(
      <TitleReviewSection
        {...defaultProps}
        title="Same Title"
        originalTitle="Same Title"
      />
    );
    expect(screen.queryByText('原始标题')).not.toBeInTheDocument();
  });

  it('should call onTitleChange when input changes', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'New Title' } });

    expect(mockOnTitleChange).toHaveBeenCalledWith('New Title');
  });

  it('should show SEO warning when title is too long', () => {
    const longTitle = 'This is a very long title that exceeds the recommended 60 character limit for SEO optimization';
    render(
      <TitleReviewSection
        {...defaultProps}
        title={longTitle}
      />
    );

    expect(screen.getByText(/标题较长/)).toBeInTheDocument();
  });

  // Note: AI optimization button was removed in 2025-12-25 refactor.
  // Real AI title suggestions are now provided via SEOTitleSelectionCard component.
  // See: TitleReviewSection.tsx comment at lines 9-13

  it('should show help text pointing to SEO Title section', () => {
    render(<TitleReviewSection {...defaultProps} />);

    // The component now shows a help message directing users to SEOTitleSelectionCard
    expect(screen.getByText(/需要 AI 标题建议/)).toBeInTheDocument();
    expect(screen.getByText(/SEO Title 选择/)).toBeInTheDocument();
  });

  it('should render reset button when title is modified', () => {
    render(<TitleReviewSection {...defaultProps} />);

    // The reset button should be visible when title differs from original
    const resetButton = screen.getByRole('button', { name: /恢复原始标题/ });
    expect(resetButton).toBeInTheDocument();
  });

  it('should reset to original title when reset button clicked', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const resetButton = screen.getByRole('button', { name: /恢复原始标题/ });
    fireEvent.click(resetButton);

    expect(mockOnTitleChange).toHaveBeenCalledWith('Original Article Title');
  });

  it('should show title quality indicators', () => {
    render(<TitleReviewSection {...defaultProps} />);

    expect(screen.getByText('长度')).toBeInTheDocument();
    expect(screen.getByText('可读性')).toBeInTheDocument();
    expect(screen.getByText('SEO')).toBeInTheDocument();
    // Multiple "✓ 良好" exist, use getAllByText
    const goodIndicators = screen.getAllByText('✓ 良好');
    expect(goodIndicators.length).toBeGreaterThan(0);
  });
});
