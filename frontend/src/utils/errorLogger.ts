/**
 * Error Logging Utility
 *
 * Provides centralized error logging and reporting functionality.
 */

import type { ErrorInfo } from 'react';

export interface ErrorLog {
  timestamp: string;
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  userAgent: string;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Storage key for error logs in localStorage
 */
const ERROR_LOG_KEY = 'cms_automation_error_logs';
const MAX_STORED_ERRORS = 50;

/**
 * Get session ID from localStorage or create a new one
 */
function getOrCreateSessionId(): string {
  const SESSION_KEY = 'cms_automation_session_id';
  let sessionId = localStorage.getItem(SESSION_KEY);

  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  return sessionId;
}

/**
 * Store error log in localStorage
 */
function storeErrorLog(errorLog: ErrorLog): void {
  try {
    const stored = localStorage.getItem(ERROR_LOG_KEY);
    const logs: ErrorLog[] = stored ? JSON.parse(stored) : [];

    // Add new error log
    logs.unshift(errorLog);

    // Keep only the most recent errors
    if (logs.length > MAX_STORED_ERRORS) {
      logs.splice(MAX_STORED_ERRORS);
    }

    localStorage.setItem(ERROR_LOG_KEY, JSON.stringify(logs));
  } catch (error) {
    console.error('Failed to store error log:', error);
  }
}

/**
 * Get stored error logs from localStorage
 */
export function getStoredErrorLogs(): ErrorLog[] {
  try {
    const stored = localStorage.getItem(ERROR_LOG_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to retrieve error logs:', error);
    return [];
  }
}

/**
 * Clear stored error logs
 */
export function clearStoredErrorLogs(): void {
  try {
    localStorage.removeItem(ERROR_LOG_KEY);
  } catch (error) {
    console.error('Failed to clear error logs:', error);
  }
}

/**
 * Log error to console and storage
 */
export function logError(
  error: Error,
  errorInfo?: ErrorInfo,
  metadata?: Record<string, unknown>
): void {
  const errorLog: ErrorLog = {
    timestamp: new Date().toISOString(),
    message: error.message || error.toString(),
    stack: error.stack,
    componentStack: errorInfo?.componentStack ?? undefined,
    url: window.location.href,
    userAgent: navigator.userAgent,
    sessionId: getOrCreateSessionId(),
    metadata,
  };

  // Log to console in development
  if (import.meta.env.DEV) {
    console.group('🔴 Error Logged');
    console.error('Error:', error);
    if (errorInfo) {
      console.error('Component Stack:', errorInfo.componentStack);
    }
    if (metadata) {
      console.log('Metadata:', metadata);
    }
    console.groupEnd();
  }

  // Store error log
  storeErrorLog(errorLog);

  // Send to error tracking service (if configured)
  sendToErrorTrackingService(errorLog);
}

/**
 * Send error to external error tracking service
 */
async function sendToErrorTrackingService(errorLog: ErrorLog): Promise<void> {
  const enableReportingEnv = import.meta.env.VITE_ENABLE_ERROR_REPORTING ?? 'true';
  const enableReporting = String(enableReportingEnv).toLowerCase() === 'true';

  // Skip in development unless explicitly enabled
  if (import.meta.env.DEV && !enableReporting) {
    return;
  }

  try {
    // TODO: Integrate with error tracking service (e.g., Sentry, LogRocket, etc.)
    // Example with Sentry:
    // if (window.Sentry) {
    //   window.Sentry.captureException(new Error(errorLog.message), {
    //     contexts: {
    //       error: errorLog,
    //     },
    //   });
    // }

    // Example: Send to custom backend endpoint
    const endpoint = import.meta.env.VITE_ERROR_TRACKING_ENDPOINT;
    if (endpoint) {
      await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorLog),
      });
    }
  } catch (error) {
    // Silently fail to avoid infinite error loops
    console.warn('Failed to send error to tracking service:', error);
  }
}

/**
 * Log API error
 */
export function logAPIError(
  endpoint: string,
  status: number,
  message: string,
  metadata?: Record<string, unknown>
): void {
  const error = new Error(`API Error: ${message} (${status})`);
  error.name = 'APIError';

  logError(error, undefined, {
    type: 'api_error',
    endpoint,
    status,
    ...metadata,
  });
}

/**
 * Log network error
 */
export function logNetworkError(
  endpoint: string,
  error: Error,
  metadata?: Record<string, unknown>
): void {
  logError(error, undefined, {
    type: 'network_error',
    endpoint,
    ...metadata,
  });
}

/**
 * Export error logs as JSON file
 */
export function exportErrorLogs(): void {
  try {
    const logs = getStoredErrorLogs();
    const dataStr = JSON.stringify(logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `error-logs-${new Date().toISOString()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to export error logs:', error);
  }
}

/**
 * Get error statistics
 */
export function getErrorStatistics(): {
  total: number;
  byType: Record<string, number>;
  byUrl: Record<string, number>;
  recent: ErrorLog[];
} {
  const logs = getStoredErrorLogs();

  const byType: Record<string, number> = {};
  const byUrl: Record<string, number> = {};

  logs.forEach((log) => {
    // Count by type
    const type = (log.metadata?.type as string) || 'unknown';
    byType[type] = (byType[type] || 0) + 1;

    // Count by URL
    byUrl[log.url] = (byUrl[log.url] || 0) + 1;
  });

  return {
    total: logs.length,
    byType,
    byUrl,
    recent: logs.slice(0, 10),
  };
}
