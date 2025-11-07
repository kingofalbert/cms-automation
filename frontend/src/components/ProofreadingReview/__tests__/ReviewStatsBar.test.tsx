/**
 * Unit tests for ReviewStatsBar component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ReviewStatsBar } from '../ReviewStatsBar';
import type { ProofreadingStats } from '@/types/worklist';

describe('ReviewStatsBar', () => {
  const mockStats: ProofreadingStats = {
    total_issues: 10,
    critical_count: 2,
    warning_count: 5,
    info_count: 3,
    pending_count: 4,
    accepted_count: 4,
    rejected_count: 1,
    modified_count: 1,
    ai_issues_count: 6,
    deterministic_issues_count: 4,
  };

  it('should return null when stats is not provided', () => {
    const { container } = render(
      <ReviewStatsBar stats={null} dirtyCount={0} totalIssues={0} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render severity statistics', () => {
    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={5}
        totalIssues={10}
      />
    );

    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('Info')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // critical_count
    expect(screen.getByText('5')).toBeInTheDocument(); // warning_count
    expect(screen.getByText('3')).toBeInTheDocument(); // info_count
  });

  it('should render decision statistics', () => {
    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={6}
        totalIssues={10}
      />
    );

    expect(screen.getByText('Accepted')).toBeInTheDocument();
    expect(screen.getByText('Rejected')).toBeInTheDocument();
    expect(screen.getByText('Modified')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument(); // accepted_count
    expect(screen.getAllByText('1')).toHaveLength(2); // rejected_count & modified_count
  });

  it('should display progress correctly', () => {
    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={5}
        totalIssues={10}
      />
    );

    expect(screen.getByText('5 / 10')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('should calculate progress percentage correctly', () => {
    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={3}
        totalIssues={10}
      />
    );

    expect(screen.getByText('30%')).toBeInTheDocument();
  });

  it('should handle 0 total issues gracefully', () => {
    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={0}
        totalIssues={0}
      />
    );

    // Should show 0%
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('should render ViewMode switcher when callback provided', () => {
    const mockOnViewModeChange = vi.fn();

    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={5}
        totalIssues={10}
        viewMode="original"
        onViewModeChange={mockOnViewModeChange}
      />
    );

    expect(screen.getByText('Original')).toBeInTheDocument();
    expect(screen.getByText('Diff')).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
  });

  it('should call onViewModeChange when mode button clicked', () => {
    const mockOnViewModeChange = vi.fn();

    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={5}
        totalIssues={10}
        viewMode="original"
        onViewModeChange={mockOnViewModeChange}
      />
    );

    const diffButton = screen.getByText('Diff');
    fireEvent.click(diffButton);

    expect(mockOnViewModeChange).toHaveBeenCalledWith('diff');
  });

  it('should highlight active view mode', () => {
    render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={5}
        totalIssues={10}
        viewMode="diff"
        onViewModeChange={vi.fn()}
      />
    );

    const diffButton = screen.getByText('Diff').closest('button');
    expect(diffButton).toHaveClass('bg-white', 'text-blue-600');
  });

  it('should have sticky positioning class', () => {
    const { container } = render(
      <ReviewStatsBar
        stats={mockStats}
        dirtyCount={5}
        totalIssues={10}
      />
    );

    const statsBar = container.firstChild;
    expect(statsBar).toHaveClass('sticky', 'top-0', 'z-10');
  });
});
