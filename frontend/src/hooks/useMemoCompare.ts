/**
 * useMemoCompare Hook
 *
 * Like useMemo but with custom comparison function
 * Useful for complex objects where you need custom equality checks
 */

import { useRef, useEffect } from 'react';

export function useMemoCompare<T>(
  next: T,
  compare: (prev: T | undefined, next: T) => boolean
): T {
  const previousRef = useRef<T>();
  const previous = previousRef.current;

  // If the comparison function returns false, update the ref
  const isEqual = compare(previous, next);

  useEffect(() => {
    if (!isEqual) {
      previousRef.current = next;
    }
  });

  // Return the previous value if equal, otherwise return the new value
  return isEqual ? (previous as T) : next;
}

/**
 * Deep equality comparison for objects
 * Note: This is a simple implementation. For production, consider using a library like lodash.isEqual
 */
export function deepEqual<T>(a: T, b: T): boolean {
  if (a === b) return true;

  if (
    typeof a !== 'object' ||
    typeof b !== 'object' ||
    a === null ||
    b === null
  ) {
    return false;
  }

  const keysA = Object.keys(a as any);
  const keysB = Object.keys(b as any);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!keysB.includes(key)) return false;

    if (!deepEqual((a as any)[key], (b as any)[key])) {
      return false;
    }
  }

  return true;
}

/**
 * Shallow equality comparison for objects
 */
export function shallowEqual<T>(a: T, b: T): boolean {
  if (a === b) return true;

  if (
    typeof a !== 'object' ||
    typeof b !== 'object' ||
    a === null ||
    b === null
  ) {
    return false;
  }

  const keysA = Object.keys(a as any);
  const keysB = Object.keys(b as any);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if ((a as any)[key] !== (b as any)[key]) return false;
  }

  return true;
}

export default useMemoCompare;
