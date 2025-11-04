/**
 * useThrottle Hook
 *
 * Throttles a callback function - useful for scroll handlers, resize events
 * Ensures the callback is called at most once per specified interval
 */

import { useCallback, useRef, useEffect } from 'react';

type TimeoutHandle = ReturnType<typeof setTimeout>;

export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 300
): T {
  const lastRan = useRef(Date.now());
  const timeoutRef = useRef<TimeoutHandle>();

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const throttledCallback = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRan.current;

      if (timeSinceLastRun >= delay) {
        // Enough time has passed, execute immediately
        callback(...args);
        lastRan.current = now;
      } else {
        // Not enough time, schedule for later
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(
          () => {
            callback(...args);
            lastRan.current = Date.now();
          },
          delay - timeSinceLastRun
        );
      }
    },
    [callback, delay]
  ) as T;

  return throttledCallback;
}

export default useThrottle;
