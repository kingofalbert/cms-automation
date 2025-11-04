import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes with conditional logic
 * Handles class conflicts by using tailwind-merge
 *
 * @example
 * cn('px-4 py-2', isActive && 'bg-blue-500', 'hover:bg-blue-600')
 *
 * @example
 * cn('p-4', 'p-2') // Returns 'p-2' (last class wins for conflicts)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
