/**
 * Drawer component for side panel overlays.
 */

import { ReactNode, useEffect, HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { createPortal } from 'react-dom';

export interface DrawerProps extends HTMLAttributes<HTMLDivElement> {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  position?: 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
  closeOnOverlayClick?: boolean;
  children: ReactNode;
}

export const Drawer = forwardRef<HTMLDivElement, DrawerProps>(
  (
    {
      isOpen,
      onClose,
      title,
      position = 'right',
      size = 'md',
      closeOnOverlayClick = true,
      className,
      children,
      ...props
    },
    ref
  ) => {
    useEffect(() => {
      if (isOpen) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = 'unset';
      }

      return () => {
        document.body.style.overflow = 'unset';
      };
    }, [isOpen]);

    useEffect(() => {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && isOpen) {
          onClose();
        }
      };

      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const sizeStyles = {
      sm: 'w-80',
      md: 'w-96',
      lg: 'w-[600px]',
    };

    const positionStyles = {
      left: 'left-0',
      right: 'right-0',
    };

    const slideInStyles = {
      left: isOpen ? 'translate-x-0' : '-translate-x-full',
      right: isOpen ? 'translate-x-0' : 'translate-x-full',
    };

    const drawerContent = (
      <div
        className="fixed inset-0 z-50"
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'drawer-title' : undefined}
      >
        {/* Overlay */}
        <div
          className={clsx(
            'fixed inset-0 bg-black transition-opacity',
            isOpen ? 'bg-opacity-50' : 'bg-opacity-0'
          )}
          onClick={closeOnOverlayClick ? onClose : undefined}
          aria-hidden="true"
        />

        {/* Drawer Panel */}
        <div
          ref={ref}
          className={clsx(
            'fixed top-0 bottom-0 bg-white shadow-2xl',
            'transform transition-transform duration-300 ease-in-out',
            'flex flex-col',
            sizeStyles[size],
            positionStyles[position],
            slideInStyles[position],
            className
          )}
          {...props}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between px-6 py-4 border-b bg-white sticky top-0 z-10">
              <h2 id="drawer-title" className="text-xl font-semibold text-gray-900">
                {title}
              </h2>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Close drawer"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          )}

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-6 py-4">{children}</div>
        </div>
      </div>
    );

    return createPortal(drawerContent, document.body);
  }
);

Drawer.displayName = 'Drawer';

export interface DrawerFooterProps extends HTMLAttributes<HTMLDivElement> {}

export const DrawerFooter = forwardRef<HTMLDivElement, DrawerFooterProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50 sticky bottom-0',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

DrawerFooter.displayName = 'DrawerFooter';
