/**
 * Performance Utilities
 *
 * Collection of utility functions for optimizing application performance
 */

/**
 * Debounce function - delays execution until after a specified delay
 * @param func Function to debounce
 * @param delay Delay in milliseconds
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;

  return function (...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Throttle function - ensures function is called at most once per interval
 * @param func Function to throttle
 * @param limit Time limit in milliseconds
 * @returns Throttled function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number = 300
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return function (...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;

      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

/**
 * Measure function execution time
 * @param func Function to measure
 * @param label Label for console output
 * @returns Wrapped function that logs execution time
 */
export function measurePerformance<T extends (...args: any[]) => any>(
  func: T,
  label: string = func.name
): T {
  return ((...args: Parameters<T>) => {
    const start = performance.now();
    const result = func(...args);
    const end = performance.now();

    console.log(`[Performance] ${label}: ${(end - start).toFixed(2)}ms`);

    return result;
  }) as T;
}

/**
 * Measure async function execution time
 * @param func Async function to measure
 * @param label Label for console output
 * @returns Wrapped async function that logs execution time
 */
export function measureAsyncPerformance<T extends (...args: any[]) => Promise<any>>(
  func: T,
  label: string = func.name
): T {
  return (async (...args: Parameters<T>) => {
    const start = performance.now();
    const result = await func(...args);
    const end = performance.now();

    console.log(`[Performance] ${label}: ${(end - start).toFixed(2)}ms`);

    return result;
  }) as T;
}

/**
 * Create a one-time function that caches its result
 * @param func Function to memoize
 * @returns Memoized function
 */
export function once<T extends (...args: any[]) => any>(func: T): T {
  let called = false;
  let result: ReturnType<T>;

  return ((...args: Parameters<T>) => {
    if (!called) {
      result = func(...args);
      called = true;
    }
    return result;
  }) as T;
}

/**
 * Memoize a function with simple cache
 * @param func Function to memoize
 * @returns Memoized function
 */
export function memoize<T extends (...args: any[]) => any>(func: T): T {
  const cache = new Map<string, ReturnType<T>>();

  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key)!;
    }

    const result = func(...args);
    cache.set(key, result);

    return result;
  }) as T;
}

/**
 * Check if code is running in production
 */
export const isProduction = (): boolean => {
  return import.meta.env.PROD;
};

/**
 * Check if code is running in development
 */
export const isDevelopment = (): boolean => {
  return import.meta.env.DEV;
};

/**
 * Lazy load a component with preloading support
 * @param importFunc Dynamic import function
 * @returns Object with component and preload function
 */
export function lazyWithPreload<T extends React.ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>
) {
  const LazyComponent = React.lazy(importFunc);

  return {
    Component: LazyComponent,
    preload: importFunc,
  };
}

/**
 * Batch multiple state updates into a single render
 * @param updates Array of update functions
 */
export function batchUpdates(updates: Array<() => void>): void {
  // React 18 automatic batching handles this, but this is useful for older versions
  // or when you need explicit control
  updates.forEach((update) => update());
}

/**
 * Request idle callback polyfill
 * Schedules work to run during browser idle periods
 */
export const requestIdleCallback =
  typeof window !== 'undefined' && window.requestIdleCallback
    ? window.requestIdleCallback
    : (cb: IdleRequestCallback) => setTimeout(cb, 1);

/**
 * Cancel idle callback polyfill
 */
export const cancelIdleCallback =
  typeof window !== 'undefined' && window.cancelIdleCallback
    ? window.cancelIdleCallback
    : (id: number) => clearTimeout(id);

/**
 * Schedule low-priority work during idle time
 * @param task Task to run
 * @param options Idle request options
 */
export function scheduleIdleTask(
  task: () => void,
  options?: IdleRequestOptions
): number {
  return requestIdleCallback(
    (deadline) => {
      if (deadline.timeRemaining() > 0) {
        task();
      }
    },
    options
  );
}

/**
 * Image preloader
 * @param urls Array of image URLs to preload
 * @returns Promise that resolves when all images are loaded
 */
export function preloadImages(urls: string[]): Promise<void[]> {
  const promises = urls.map((url) => {
    return new Promise<void>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve();
      img.onerror = reject;
      img.src = url;
    });
  });

  return Promise.all(promises);
}

/**
 * Resource hints for preconnect, prefetch, preload
 */
export const resourceHints = {
  /**
   * Preconnect to a domain
   */
  preconnect: (url: string) => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = url;
    document.head.appendChild(link);
  },

  /**
   * Prefetch a resource
   */
  prefetch: (url: string) => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
  },

  /**
   * Preload a resource
   */
  preload: (url: string, as: string = 'fetch') => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = as;
    document.head.appendChild(link);
  },
};

// For React import
import React from 'react';
