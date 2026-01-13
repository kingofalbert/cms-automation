/**
 * useAutoSave - Hook for automatic form data saving
 *
 * Features:
 * - Configurable auto-save interval (default: 30 seconds)
 * - Save status indicators (idle, saving, saved, error)
 * - LocalStorage and/or API persistence
 * - Unsaved changes detection
 * - Draft recovery on page load
 * - Manual save option
 * - Debounced saves to prevent excessive calls
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

export interface AutoSaveConfig<T> {
  /** Unique key for localStorage persistence */
  storageKey: string;
  /** Data to save */
  data: T;
  /** Save function (API call) - optional, if not provided only localStorage is used */
  onSave?: (data: T) => Promise<void>;
  /** Auto-save interval in milliseconds (default: 30000 = 30 seconds) */
  interval?: number;
  /** Debounce delay for manual saves (default: 1000ms) */
  debounceDelay?: number;
  /** Enable auto-save (default: true) */
  enabled?: boolean;
  /** Callback when save succeeds */
  onSaveSuccess?: () => void;
  /** Callback when save fails */
  onSaveError?: (error: Error) => void;
  /** Compare function to detect changes (default: JSON.stringify comparison) */
  isEqual?: (a: T, b: T) => boolean;
}

export interface AutoSaveReturn<T> {
  /** Current save status */
  status: SaveStatus;
  /** Whether there are unsaved changes */
  hasUnsavedChanges: boolean;
  /** Last saved timestamp */
  lastSavedAt: Date | null;
  /** Manually trigger save */
  save: () => Promise<void>;
  /** Clear draft from storage */
  clearDraft: () => void;
  /** Load draft from storage */
  loadDraft: () => T | null;
  /** Time since last save (human readable) */
  timeSinceLastSave: string | null;
  /** Error message if save failed */
  errorMessage: string | null;
}

/**
 * Read draft from localStorage
 */
const readDraft = <T>(key: string): T | null => {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed.data as T;
    }
    return null;
  } catch (error) {
    console.warn(`Failed to read draft from localStorage (key: ${key}):`, error);
    return null;
  }
};

/**
 * Write draft to localStorage
 */
const writeDraft = <T>(key: string, data: T): void => {
  try {
    localStorage.setItem(
      key,
      JSON.stringify({
        data,
        savedAt: new Date().toISOString(),
      })
    );
  } catch (error) {
    console.warn(`Failed to write draft to localStorage (key: ${key}):`, error);
  }
};

/**
 * Clear draft from localStorage
 */
const clearDraftFromStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Failed to clear draft from localStorage (key: ${key}):`, error);
  }
};

/**
 * Default equality check using JSON.stringify
 */
const defaultIsEqual = <T>(a: T, b: T): boolean => {
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
};

/**
 * Format time since last save
 */
const formatTimeSince = (date: Date | null): string | null => {
  if (!date) return null;

  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 5) return '剛才';
  if (seconds < 60) return `${seconds} 秒前`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} 分鐘前`;

  const hours = Math.floor(minutes / 60);
  return `${hours} 小時前`;
};

/**
 * Hook for automatic form data saving
 */
export const useAutoSave = <T>({
  storageKey,
  data,
  onSave,
  interval = 30000,
  debounceDelay = 1000,
  enabled = true,
  onSaveSuccess,
  onSaveError,
  isEqual = defaultIsEqual,
}: AutoSaveConfig<T>): AutoSaveReturn<T> => {
  const [status, setStatus] = useState<SaveStatus>('idle');
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [lastSavedData, setLastSavedData] = useState<T | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [timeSinceLastSave, setTimeSinceLastSave] = useState<string | null>(null);

  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  // Check for unsaved changes
  const hasUnsavedChanges = lastSavedData !== null ? !isEqual(data, lastSavedData) : false;

  // Save function
  const performSave = useCallback(async () => {
    if (!isMountedRef.current) return;

    setStatus('saving');
    setErrorMessage(null);

    try {
      // Save to localStorage first
      writeDraft(storageKey, data);

      // If API save function provided, call it
      if (onSave) {
        await onSave(data);
      }

      if (!isMountedRef.current) return;

      setStatus('saved');
      setLastSavedAt(new Date());
      setLastSavedData(data);
      onSaveSuccess?.();

      // Reset status to idle after 2 seconds
      setTimeout(() => {
        if (isMountedRef.current) {
          setStatus('idle');
        }
      }, 2000);
    } catch (error) {
      if (!isMountedRef.current) return;

      const errMsg = error instanceof Error ? error.message : 'Save failed';
      setStatus('error');
      setErrorMessage(errMsg);
      onSaveError?.(error instanceof Error ? error : new Error(errMsg));
    }
  }, [data, storageKey, onSave, onSaveSuccess, onSaveError]);

  // Debounced manual save
  const save = useCallback(async () => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    return new Promise<void>((resolve) => {
      saveTimeoutRef.current = setTimeout(async () => {
        await performSave();
        resolve();
      }, debounceDelay);
    });
  }, [performSave, debounceDelay]);

  // Load draft from storage
  const loadDraft = useCallback((): T | null => {
    return readDraft<T>(storageKey);
  }, [storageKey]);

  // Clear draft
  const clearDraft = useCallback(() => {
    clearDraftFromStorage(storageKey);
    setLastSavedData(null);
    setLastSavedAt(null);
  }, [storageKey]);

  // Auto-save interval
  useEffect(() => {
    if (!enabled) return;

    intervalRef.current = setInterval(() => {
      if (hasUnsavedChanges && status !== 'saving') {
        performSave();
      }
    }, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, interval, hasUnsavedChanges, status, performSave]);

  // Update time since last save
  useEffect(() => {
    const updateTimeSince = () => {
      setTimeSinceLastSave(formatTimeSince(lastSavedAt));
    };

    updateTimeSince();
    const timer = setInterval(updateTimeSince, 10000);

    return () => clearInterval(timer);
  }, [lastSavedAt]);

  // Initialize lastSavedData on mount
  useEffect(() => {
    const draft = loadDraft();
    if (draft) {
      setLastSavedData(draft);
    } else {
      setLastSavedData(data);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    status,
    hasUnsavedChanges,
    lastSavedAt,
    save,
    clearDraft,
    loadDraft,
    timeSinceLastSave,
    errorMessage,
  };
};

/**
 * Hook for detecting unsaved changes and prompting on navigation
 */
export const useUnsavedChangesWarning = (
  hasUnsavedChanges: boolean,
  message = '您有未保存的更改。確定要離開此頁面嗎？'
) => {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = message;
        return message;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges, message]);
};

export default useAutoSave;
