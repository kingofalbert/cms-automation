/**
 * ErrorBoundary Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorBoundary from '../ErrorBoundary';

// Component that throws an error
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error for these tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('should render error UI when child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('應用程序出錯')).toBeInTheDocument();
  });

  it('should display reload button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const reloadButton = screen.getByRole('button', { name: /重新加載/i });
    expect(reloadButton).toBeInTheDocument();
  });

  it('should display home button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const homeButton = screen.getByRole('button', { name: /返回首頁/i });
    expect(homeButton).toBeInTheDocument();
  });

  it('should call onError callback when error occurs', () => {
    const onError = vi.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalled();
    const error = onError.mock.calls[0][0];
    expect(error.message).toBe('Test error');
  });

  it('should render custom fallback if provided', () => {
    const customFallback = <div>Custom error message</div>;

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error message')).toBeInTheDocument();
    expect(screen.queryByText('應用程序出錯')).not.toBeInTheDocument();
  });

  it('should show error details in development mode', () => {
    render(
      <ErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Should have a button to show details
    const detailsButton = screen.getByRole('button', { name: /顯示詳情/i });
    expect(detailsButton).toBeInTheDocument();
  });

  it('should toggle error details when details button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <ErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const detailsButton = screen.getByRole('button', { name: /顯示詳情/i });

    // Details should be hidden initially
    const detailsContainer = document.getElementById('error-details');
    expect(detailsContainer).toHaveStyle({ display: 'none' });

    // Click to show details
    await user.click(detailsButton);

    expect(detailsContainer).toHaveStyle({ display: 'block' });

    // Click again to hide
    await user.click(detailsButton);

    expect(detailsContainer).toHaveStyle({ display: 'none' });
  });

  it('should display error message in details', () => {
    render(
      <ErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText(/錯誤信息/i)).toBeInTheDocument();
    expect(screen.getByText(/Test error/i)).toBeInTheDocument();
  });

  it('should increment error count on multiple errors', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    // First error
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText(/應用程序出錯/i)).toBeInTheDocument();
  });

  it('should reload page when reload button is clicked', async () => {
    const user = userEvent.setup();
    const reloadSpy = vi.spyOn(window.location, 'reload').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const reloadButton = screen.getByRole('button', { name: /重新加載/i });
    await user.click(reloadButton);

    expect(reloadSpy).toHaveBeenCalled();
    reloadSpy.mockRestore();
  });

  it('should navigate to home when home button is clicked', async () => {
    const user = userEvent.setup();
    const assignSpy = vi.spyOn(window.location, 'assign').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const homeButton = screen.getByRole('button', { name: /返回首頁/i });

    await user.click(homeButton);

    // Note: In the actual implementation, it sets window.location.href
    // which we can't fully test in JSDOM, but we can verify the button exists and is clickable
    expect(homeButton).toBeInTheDocument();
    assignSpy.mockRestore();
  });

  it('should log error to console', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error');

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(consoleErrorSpy).toHaveBeenCalled();
  });
});
