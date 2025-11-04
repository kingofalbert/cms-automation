/**
 * usePolling Hook
 *
 * Custom React hook for polling data at regular intervals.
 * Provides automatic cleanup, pause/resume functionality, and error handling.
 */

import { useEffect, useRef, useCallback, useState } from 'react';

type IntervalHandle = ReturnType<typeof setInterval>;

export interface UsePollingOptions {
  /**
   * Polling interval in milliseconds
   * @default 5000
   */
  interval?: number;

  /**
   * Whether to start polling immediately
   * @default true
   */
  enabled?: boolean;

  /**
   * Whether to poll when browser tab is not visible
   * @default false
   */
  pollWhenHidden?: boolean;

  /**
   * Maximum number of consecutive errors before stopping
   * @default 3
   */
  maxErrors?: number;

  /**
   * Callback when polling stops due to errors
   */
  onMaxErrors?: (errorCount: number) => void;

  /**
   * Whether to poll immediately on mount (before first interval)
   * @default true
   */
  pollOnMount?: boolean;
}

export interface UsePollingReturn {
  /**
   * Whether polling is currently active
   */
  isPolling: boolean;

  /**
   * Start polling
   */
  start: () => void;

  /**
   * Stop polling
   */
  stop: () => void;

  /**
   * Toggle polling on/off
   */
  toggle: () => void;

  /**
   * Manually trigger a poll (doesn't reset the interval)
   */
  poll: () => Promise<void>;

  /**
   * Number of consecutive errors
   */
  errorCount: number;

  /**
   * Reset error count
   */
  resetErrors: () => void;
}

/**
 * Hook for polling data at regular intervals with automatic cleanup.
 *
 * @example
 * ```tsx
 * function TaskMonitor() {
 *   const { isPolling, start, stop } = usePolling(
 *     async () => {
 *       const response = await tasksAPI.list();
 *       setTasks(response.data.items);
 *     },
 *     { interval: 3000 }
 *   );
 *
 *   return (
 *     <div>
 *       <Button onClick={isPolling ? stop : start}>
 *         {isPolling ? 'Stop' : 'Start'} Auto-refresh
 *       </Button>
 *     </div>
 *   );
 * }
 * ```
 */
export function usePolling(
  callback: () => void | Promise<void>,
  options: UsePollingOptions = {}
): UsePollingReturn {
  const {
    interval = 5000,
    enabled = true,
    pollWhenHidden = false,
    maxErrors = 3,
    onMaxErrors,
    pollOnMount = true,
  } = options;

  const [isPolling, setIsPolling] = useState(enabled);
  const [errorCount, setErrorCount] = useState(0);

  const intervalRef = useRef<IntervalHandle | null>(null);
  const callbackRef = useRef(callback);
  const isPollingRef = useRef(isPolling);
  const errorCountRef = useRef(errorCount);

  // Keep refs in sync
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    isPollingRef.current = isPolling;
  }, [isPolling]);

  useEffect(() => {
    errorCountRef.current = errorCount;
  }, [errorCount]);

  /**
   * Execute the polling callback with error handling
   */
  const poll = useCallback(async () => {
    try {
      await callbackRef.current();
      // Reset error count on success
      if (errorCountRef.current > 0) {
        setErrorCount(0);
      }
    } catch (error) {
      console.error('Polling error:', error);
      const newErrorCount = errorCountRef.current + 1;
      setErrorCount(newErrorCount);

      // Stop polling if max errors reached
      if (newErrorCount >= maxErrors) {
        setIsPolling(false);
        onMaxErrors?.(newErrorCount);
      }
    }
  }, [maxErrors, onMaxErrors]);

  /**
   * Start polling
   */
  const start = useCallback(() => {
    setIsPolling(true);
  }, []);

  /**
   * Stop polling
   */
  const stop = useCallback(() => {
    setIsPolling(false);
  }, []);

  /**
   * Toggle polling
   */
  const toggle = useCallback(() => {
    setIsPolling((prev) => !prev);
  }, []);

  /**
   * Reset error count
   */
  const resetErrors = useCallback(() => {
    setErrorCount(0);
  }, []);

  /**
   * Handle visibility change
   */
  useEffect(() => {
    if (pollWhenHidden) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Stop polling when tab is hidden
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else if (isPollingRef.current) {
        // Resume polling when tab becomes visible
        poll(); // Poll immediately
        intervalRef.current = setInterval(poll, interval);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [poll, interval, pollWhenHidden]);

  /**
   * Main polling effect
   */
  useEffect(() => {
    // Skip if tab is hidden and pollWhenHidden is false
    if (!pollWhenHidden && document.hidden) {
      return;
    }

    if (isPolling) {
      // Poll immediately on mount if enabled
      if (pollOnMount) {
        poll();
      }

      // Start interval
      intervalRef.current = setInterval(poll, interval);
    } else {
      // Clear interval when polling is disabled
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isPolling, interval, poll, pollOnMount, pollWhenHidden]);

  return {
    isPolling,
    start,
    stop,
    toggle,
    poll,
    errorCount,
    resetErrors,
  };
}

/**
 * Hook for polling with React Query integration.
 * Uses refetch from useQuery for polling.
 *
 * @example
 * ```tsx
 * function TaskMonitor() {
 *   const { data, refetch } = useQuery({
 *     queryKey: ['tasks'],
 *     queryFn: () => tasksAPI.list(),
 *   });
 *
 *   const { isPolling, toggle } = useQueryPolling(refetch, {
 *     interval: 3000,
 *   });
 *
 *   return <div>Polling: {isPolling ? 'ON' : 'OFF'}</div>;
 * }
 * ```
 */
export function useQueryPolling(
  refetch: () => Promise<any>,
  options: UsePollingOptions = {}
): UsePollingReturn {
  return usePolling(refetch, options);
}
