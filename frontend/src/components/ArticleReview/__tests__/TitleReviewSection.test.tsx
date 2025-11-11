/**
 * Tests for TitleReviewSection component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
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

  it('should render AI optimization button', () => {
    render(<TitleReviewSection {...defaultProps} />);

    const aiButton = screen.getByRole('button', { name: /AI 优化标题/ });
    expect(aiButton).toBeInTheDocument();
  });

  it('should disable AI button when no title', () => {
    render(
      <TitleReviewSection
        {...defaultProps}
        title=""
      />
    );

    const aiButton = screen.getByRole('button', { name: /AI 优化标题/ });
    expect(aiButton).toBeDisabled();
  });

  it('should show loading state when optimizing', async () => {
    render(<TitleReviewSection {...defaultProps} />);

    const aiButton = screen.getByRole('button', { name: /AI 优化标题/ });
    fireEvent.click(aiButton);

    expect(screen.getByText('AI 优化中...')).toBeInTheDocument();
  });

  it.skip('should display AI suggestions after optimization', async () => {
    vi.useFakeTimers();

    render(<TitleReviewSection {...defaultProps} />);

    const aiButton = screen.getByRole('button', { name: /AI 优化标题/ });
    fireEvent.click(aiButton);

    // Fast-forward time to complete mock optimization
    await act(async () => {
      vi.advanceTimersByTime(1100);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByText('AI 建议标题')).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it.skip('should apply suggestion when clicked', async () => {
    vi.useFakeTimers();

    render(<TitleReviewSection {...defaultProps} />);

    const aiButton = screen.getByRole('button', { name: /AI 优化标题/ });
    fireEvent.click(aiButton);

    vi.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByText('AI 建议标题')).toBeInTheDocument();
    });

    const suggestions = screen.getAllByText(/点击使用/);
    const firstSuggestion = suggestions[0].closest('button');

    if (firstSuggestion) {
      fireEvent.click(firstSuggestion);
      expect(mockOnTitleChange).toHaveBeenCalled();
    }

    vi.useRealTimers();
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
