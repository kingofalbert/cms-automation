import { useEffect, useRef } from 'react';
import { useBlocker } from 'react-router-dom';

export interface UseUnsavedChangesOptions {
  when: boolean;
  message?: string;
}

const DEFAULT_MESSAGE = '您有未保存的更改，确认要离开当前页面吗？';

/**
 * Warn users when navigating away with unsaved changes.
 * Blocks in-app navigation via React Router's blocker and native browser refresh/close.
 */
export const useUnsavedChanges = ({
  when,
  message = DEFAULT_MESSAGE,
}: UseUnsavedChangesOptions) => {
  const blocker = useBlocker(when);
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

  useEffect(() => {
    if (!when || blocker.state !== 'blocked') {
      return;
    }

    const shouldLeave = window.confirm(confirmMessageRef.current);
    if (shouldLeave) {
      blocker.proceed?.();
    } else {
      blocker.reset?.();
    }
  }, [blocker, when]);
};
