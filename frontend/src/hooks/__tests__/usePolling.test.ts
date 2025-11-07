/**
 * usePolling Hook Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { usePolling } from '../usePolling';

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should start polling immediately by default', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollOnMount: true,
      })
    );

    // Wait for useEffect and initial poll to complete (only microtasks)
    await act(async () => {
      await Promise.resolve();
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(result.current.isPolling).toBe(true);
  });

  it('should poll at the specified interval', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollOnMount: true,
      })
    );

    // Wait for initial poll (microtasks only)
    await act(async () => {
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // Advance time by 1 second
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve(); // Wait for promise from interval callback
    });
    expect(callback).toHaveBeenCalledTimes(2);

    // Advance time by another second
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve(); // Wait for promise from interval callback
    });
    expect(callback).toHaveBeenCalledTimes(3);
  });

  it('should not start polling if enabled is false', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: false,
      })
    );

    await vi.advanceTimersByTimeAsync(2000);

    expect(callback).not.toHaveBeenCalled();
    expect(result.current.isPolling).toBe(false);
  });

  it('should stop polling when stop() is called', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollOnMount: true,
      })
    );

    // Wait for initial poll (microtasks only)
    await act(async () => {
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // Stop polling
    act(() => {
      result.current.stop();
    });
    expect(result.current.isPolling).toBe(false);

    // Advance time
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runOnlyPendingTimersAsync();
    });

    // Should not have polled again
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should restart polling when start() is called', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: false,
      })
    );

    expect(result.current.isPolling).toBe(false);
    expect(callback).not.toHaveBeenCalled();

    // Start polling
    await act(async () => {
      result.current.start();
      await vi.runOnlyPendingTimersAsync();
    });

    expect(result.current.isPolling).toBe(true);
    expect(callback).toHaveBeenCalled();
  });

  it('should toggle polling state', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
      })
    );

    expect(result.current.isPolling).toBe(true);

    // Toggle off
    act(() => {
      result.current.toggle();
    });

    expect(result.current.isPolling).toBe(false);

    // Toggle on
    act(() => {
      result.current.toggle();
    });

    expect(result.current.isPolling).toBe(true);
  });

  it('should handle errors and increment error count', async () => {
    const callback = vi.fn().mockRejectedValue(new Error('Poll failed'));

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        maxErrors: 3,
      })
    );

    // Wait for first failed poll
    await act(async () => {
      await vi.runOnlyPendingTimersAsync();
    });
    expect(result.current.errorCount).toBe(1);

    // Continue polling and failing
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await vi.runOnlyPendingTimersAsync();
    });
    expect(result.current.errorCount).toBe(2);
  });

  it('should stop polling after max errors reached', async () => {
    const callback = vi.fn().mockRejectedValue(new Error('Poll failed'));
    const onMaxErrors = vi.fn();

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        maxErrors: 2,
        onMaxErrors,
      })
    );

    // First error
    await act(async () => {
      await vi.runOnlyPendingTimersAsync();
    });
    expect(result.current.errorCount).toBe(1);

    // Second error - should stop polling
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await vi.runOnlyPendingTimersAsync();
    });
    expect(result.current.errorCount).toBe(2);
    expect(result.current.isPolling).toBe(false);
    expect(onMaxErrors).toHaveBeenCalledWith(2);
  });

  it('should reset error count on successful poll', async () => {
    let shouldFail = true;
    const callback = vi.fn().mockImplementation(() => {
      if (shouldFail) {
        return Promise.reject(new Error('Poll failed'));
      }
      return Promise.resolve();
    });

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        maxErrors: 5,
      })
    );

    // Wait for first failed poll
    await act(async () => {
      await vi.runOnlyPendingTimersAsync();
    });
    expect(result.current.errorCount).toBe(1);

    // Make next poll succeed
    shouldFail = false;

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await vi.runOnlyPendingTimersAsync();
    });

    // Error count should be reset
    expect(result.current.errorCount).toBe(0);
  });

  it('should manually trigger poll', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      usePolling(callback, {
        interval: 10000, // Long interval
        enabled: false,
      })
    );

    expect(callback).not.toHaveBeenCalled();

    // Manually trigger poll
    await act(async () => {
      await result.current.poll();
    });

    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should pause polling when tab is hidden', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollWhenHidden: false,
        pollOnMount: true,
      })
    );

    // Wait for initial poll (microtasks only)
    await act(async () => {
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // Simulate tab becoming hidden
    Object.defineProperty(document, 'hidden', {
      writable: true,
      configurable: true,
      value: true,
    });

    const visibilityChangeEvent = new Event('visibilitychange');
    act(() => {
      document.dispatchEvent(visibilityChangeEvent);
    });

    // Advance time - should not poll
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runOnlyPendingTimersAsync();
    });

    // Should still be only 1 call (initial)
    expect(callback).toHaveBeenCalledTimes(1);

    // Simulate tab becoming visible again
    Object.defineProperty(document, 'hidden', {
      value: false,
    });

    await act(async () => {
      document.dispatchEvent(visibilityChangeEvent);
      await Promise.resolve(); // Poll happens immediately, wait for microtasks
    });

    // Should poll immediately when visible
    expect(callback).toHaveBeenCalledTimes(2);
  });

  it('should continue polling when tab is hidden if pollWhenHidden is true', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    renderHook(() =>
      usePolling(callback, {
        interval: 1000,
        enabled: true,
        pollWhenHidden: true,
        pollOnMount: true,
      })
    );

    // Wait for initial poll (microtasks only)
    await act(async () => {
      await Promise.resolve();
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // Simulate tab becoming hidden
    Object.defineProperty(document, 'hidden', {
      writable: true,
      configurable: true,
      value: true,
    });

    // Advance time - should continue polling
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve(); // Wait for promise from interval callback
    });
    expect(callback).toHaveBeenCalledTimes(2);
  });
});
