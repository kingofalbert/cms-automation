/**
 * Badge component for status indicators and labels.
 */

import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  (
    { variant = 'default', size = 'md', dot = false, className, children, ...props },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium rounded-full transition-colors';

    const variantStyles = {
      default: 'bg-gray-100 text-gray-800',
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      info: 'bg-blue-100 text-blue-800',
      secondary: 'bg-purple-100 text-purple-800',
    };

    const sizeStyles = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
      lg: 'px-3 py-1.5 text-base',
    };

    const dotStyles = {
      default: 'bg-gray-500',
      success: 'bg-green-500',
      warning: 'bg-yellow-500',
      error: 'bg-red-500',
      info: 'bg-blue-500',
      secondary: 'bg-purple-500',
    };

    return (
      <span
        ref={ref}
        className={clsx(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={clsx(
              'w-2 h-2 rounded-full mr-1.5',
              dotStyles[variant]
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
