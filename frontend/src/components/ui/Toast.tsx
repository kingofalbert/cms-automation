/**
 * Modern Toast notification component.
 * Provides smooth animations and auto-dismiss functionality.
 */

import { useEffect } from 'react';
import { clsx } from 'clsx';
import { CheckCircle2, XCircle, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  onClose: () => void;
}

const icons = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

const styles = {
  success: {
    bg: 'bg-success-50 border-success-200',
    icon: 'text-success-600',
    title: 'text-success-900',
    message: 'text-success-700',
  },
  error: {
    bg: 'bg-error-50 border-error-200',
    icon: 'text-error-600',
    title: 'text-error-900',
    message: 'text-error-700',
  },
  warning: {
    bg: 'bg-warning-50 border-warning-200',
    icon: 'text-warning-600',
    title: 'text-warning-900',
    message: 'text-warning-700',
  },
  info: {
    bg: 'bg-primary-50 border-primary-200',
    icon: 'text-primary-600',
    title: 'text-primary-900',
    message: 'text-primary-700',
  },
};

export const Toast: React.FC<ToastProps> = ({
  type,
  title,
  message,
  duration = 5000,
  onClose,
}) => {
  const Icon = icons[type];
  const style = styles[type];

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    <div
      className={clsx(
        'pointer-events-auto w-full max-w-sm rounded-lg border shadow-lg p-4',
        'animate-in slide-in-from-top-5 fade-in duration-300',
        style.bg
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', style.icon)} />
        <div className="flex-1 min-w-0">
          <p className={clsx('text-sm font-semibold', style.title)}>{title}</p>
          {message && (
            <p className={clsx('text-sm mt-1', style.message)}>{message}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="关闭"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export interface ToastContainerProps {
  toasts: Array<{ id: string } & ToastProps>;
  onRemove: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onRemove,
}) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 pointer-events-none">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          {...toast}
          onClose={() => onRemove(toast.id)}
        />
      ))}
    </div>
  );
};
