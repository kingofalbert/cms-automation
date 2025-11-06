import { useEffect, useRef } from 'react';

export interface UseUnsavedChangesOptions {
  when: boolean;
  message?: string;
}

const DEFAULT_MESSAGE = '您有未保存的更改，确认要离开当前页面吗？';

/**
 * Warn users when navigating away with unsaved changes.
 * Handles native browser refresh/close events.
 *
 * Note: useBlocker from react-router-dom requires a data router and is not used
 * to maintain compatibility with HashRouter. In-app navigation warnings are handled
 * by the browser's beforeunload event.
 */
export const useUnsavedChanges = ({
  when,
  message = DEFAULT_MESSAGE,
}: UseUnsavedChangesOptions) => {
  const confirmMessageRef = useRef(message);

  useEffect(() => {
    confirmMessageRef.current = message;
  }, [message]);

  useEffect(() => {
    if (!when) {
      return undefined;
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = confirmMessageRef.current;
      return confirmMessageRef.current;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [when]);
};
