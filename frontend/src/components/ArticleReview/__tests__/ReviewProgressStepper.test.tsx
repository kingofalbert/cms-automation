/**
 * Tests for ReviewProgressStepper component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReviewProgressStepper } from '../ReviewProgressStepper';

describe('ReviewProgressStepper', () => {
  it('should render all three steps with labels', () => {
    render(<ReviewProgressStepper currentStep={0} />);

    expect(screen.getByText('解析审核')).toBeInTheDocument();
    expect(screen.getByText('校对审核')).toBeInTheDocument();
    expect(screen.getByText('发布预览')).toBeInTheDocument();
  });

  it('should render step descriptions', () => {
    render(<ReviewProgressStepper currentStep={0} />);

    expect(screen.getByText(/审核标题、作者、图片、SEO/)).toBeInTheDocument();
    expect(screen.getByText(/审核校对建议和修改/)).toBeInTheDocument();
    expect(screen.getByText(/最终预览和发布/)).toBeInTheDocument();
  });

  it('should show step numbers correctly', () => {
    render(<ReviewProgressStepper currentStep={0} />);

    // Should show numbers 1, 2, 3
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('should highlight current step (parsing)', () => {
    const { container } = render(<ReviewProgressStepper currentStep={0} />);

    // Step 1 should have active styling
    const step1 = screen.getByText('1').closest('span');
    expect(step1).toHaveClass('text-primary-600');
  });

  it('should highlight current step (proofreading)', () => {
    const { container } = render(<ReviewProgressStepper currentStep={1} />);

    // Step 2 should have active styling
    const step2 = screen.getByText('2').closest('span');
    expect(step2).toHaveClass('text-primary-600');
  });

  it('should highlight current step (publish)', () => {
    const { container } = render(<ReviewProgressStepper currentStep={2} />);

    // Step 3 should have active styling
    const step3 = screen.getByText('3').closest('span');
    expect(step3).toHaveClass('text-primary-600');
  });

  it('should show checkmark for completed steps', () => {
    const { container } = render(<ReviewProgressStepper currentStep={2} />);

    // Steps 0 and 1 should have checkmarks (completed)
    const checkmarks = container.querySelectorAll('svg path[fill-rule="evenodd"]');
    expect(checkmarks.length).toBeGreaterThanOrEqual(2);
  });

  it('should apply completed styling to completed steps', () => {
    render(<ReviewProgressStepper currentStep={2} />);

    // First step label should have completed styling
    const step1Label = screen.getByText('解析审核');
    expect(step1Label).toHaveClass('text-gray-900');
  });

  it('should apply upcoming styling to future steps', () => {
    render(<ReviewProgressStepper currentStep={0} />);

    // Third step should have upcoming styling
    const step3Number = screen.getByText('3').closest('span');
    expect(step3Number).toHaveClass('text-gray-500');
  });

  it('should render progress navigation', () => {
    const { container } = render(<ReviewProgressStepper currentStep={1} />);

    const nav = container.querySelector('nav[aria-label="Progress"]');
    expect(nav).toBeInTheDocument();
  });

  it('should render connector lines between steps', () => {
    const { container } = render(<ReviewProgressStepper currentStep={0} />);

    // Check for connector lines
    const connectors = container.querySelectorAll('.absolute.top-4');
    expect(connectors.length).toBeGreaterThan(0);
  });
});
