import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Date formatting utilities for consistent date display across the app
 */

// Standard date formats
export const DATE_FORMATS = {
  /** Full date and time: 2024-01-15 14:30:00 */
  FULL: 'yyyy-MM-dd HH:mm:ss',
  /** Date and time without seconds: 2024-01-15 14:30 */
  SHORT: 'yyyy-MM-dd HH:mm',
  /** Date only: 2024-01-15 */
  DATE_ONLY: 'yyyy-MM-dd',
  /** Time only: 14:30:00 */
  TIME_ONLY: 'HH:mm:ss',
  /** Compact for tables: 01-15 14:30 */
  COMPACT: 'MM-dd HH:mm',
} as const;

/**
 * Get the date-fns locale based on current language
 */
export function getDateLocale(language?: string): Locale {
  const lang = language || (typeof window !== 'undefined' ? document.documentElement.lang : 'zh-TW');
  return lang.startsWith('zh') ? zhTW : enUS;
}

/**
 * Format a date string or Date object with the specified format
 */
export function formatDate(
  date: string | Date | null | undefined,
  formatStr: string = DATE_FORMATS.SHORT,
  fallback: string = '—'
): string {
  if (!date) return fallback;
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return fallback;
    return format(dateObj, formatStr);
  } catch {
    return fallback;
  }
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(
  date: string | Date | null | undefined,
  language?: string,
  fallback: string = '—'
): string {
  if (!date) return fallback;
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return fallback;
    return formatDistanceToNow(dateObj, {
      addSuffix: true,
      locale: getDateLocale(language),
    });
  } catch {
    return fallback;
  }
}
