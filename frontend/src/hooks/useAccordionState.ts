/**
 * useAccordionState - Hook for managing accordion state with localStorage persistence
 *
 * Features:
 * - Persists open/closed state to localStorage
 * - Graceful error handling for localStorage failures
 * - Expand all / Collapse all utilities
 * - Type-safe section identifiers
 */

import { useState, useCallback, useEffect } from 'react';

interface AccordionStateOptions {
  /** Storage key for localStorage */
  storageKey: string;
  /** Default open state for each section */
  defaultOpenSections?: string[];
  /** All section IDs */
  sectionIds: string[];
}

interface AccordionStateReturn {
  /** Check if a section is open */
  isOpen: (sectionId: string) => boolean;
  /** Toggle a section's open state */
  toggle: (sectionId: string) => void;
  /** Set a section's open state */
  setOpen: (sectionId: string, open: boolean) => void;
  /** Expand all sections */
  expandAll: () => void;
  /** Collapse all sections */
  collapseAll: () => void;
  /** Get all open section IDs */
  openSections: string[];
}

/**
 * Read accordion state from localStorage
 */
const readFromStorage = (key: string): string[] | null => {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    }
    return null;
  } catch (error) {
    console.warn(`Failed to read accordion state from localStorage (key: ${key}):`, error);
    return null;
  }
};

/**
 * Write accordion state to localStorage
 */
const writeToStorage = (key: string, openSections: string[]): void => {
  try {
    localStorage.setItem(key, JSON.stringify(openSections));
  } catch (error) {
    console.warn(`Failed to write accordion state to localStorage (key: ${key}):`, error);
  }
};

/**
 * Hook for managing accordion state with localStorage persistence
 */
export const useAccordionState = ({
  storageKey,
  defaultOpenSections = [],
  sectionIds,
}: AccordionStateOptions): AccordionStateReturn => {
  // Initialize state from localStorage or defaults
  const [openSections, setOpenSections] = useState<string[]>(() => {
    const stored = readFromStorage(storageKey);
    return stored !== null ? stored : defaultOpenSections;
  });

  // Persist to localStorage when state changes
  useEffect(() => {
    writeToStorage(storageKey, openSections);
  }, [storageKey, openSections]);

  const isOpen = useCallback(
    (sectionId: string) => openSections.includes(sectionId),
    [openSections]
  );

  const toggle = useCallback((sectionId: string) => {
    setOpenSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((id) => id !== sectionId)
        : [...prev, sectionId]
    );
  }, []);

  const setOpen = useCallback((sectionId: string, open: boolean) => {
    setOpenSections((prev) => {
      if (open && !prev.includes(sectionId)) {
        return [...prev, sectionId];
      }
      if (!open && prev.includes(sectionId)) {
        return prev.filter((id) => id !== sectionId);
      }
      return prev;
    });
  }, []);

  const expandAll = useCallback(() => {
    setOpenSections([...sectionIds]);
  }, [sectionIds]);

  const collapseAll = useCallback(() => {
    setOpenSections([]);
  }, []);

  return {
    isOpen,
    toggle,
    setOpen,
    expandAll,
    collapseAll,
    openSections,
  };
};

export default useAccordionState;
