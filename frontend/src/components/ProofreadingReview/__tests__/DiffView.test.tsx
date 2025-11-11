/**
 * Unit tests for DiffView component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DiffView } from '../DiffView';

describe('DiffView', () => {
  const mockProps = {
    original: 'This is the original text.',
    suggested: 'This is the suggested text.',
    title: 'Test Article',
  };

  it('should render title correctly', () => {
    render(<DiffView {...mockProps} />);
    expect(screen.getByText('Test Article')).toBeInTheDocument();
  });

  it('should render header labels', () => {
    render(<DiffView {...mockProps} />);
    // The component uses translation keys, check for actual rendered text
    expect(screen.getAllByText(/原始内容/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/建议内容/).length).toBeGreaterThan(0);
  });

  it('should render with custom className', () => {
    const { container } = render(
      <DiffView {...mockProps} className="custom-class" />
    );
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('should handle empty suggested text', () => {
    render(<DiffView {...mockProps} suggested="" />);
    // Should not crash
    expect(screen.getByText('Test Article')).toBeInTheDocument();
  });
});
