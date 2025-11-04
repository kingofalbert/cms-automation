/**
 * Modern Accordion component for collapsible content sections.
 * Provides smooth animations and accessible keyboard navigation.
 */

import { useState, ReactNode, HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { ChevronDown } from 'lucide-react';

export interface AccordionItemProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  title,
  subtitle,
  icon,
  defaultOpen = false,
  children,
  className,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div
      className={clsx(
        'border border-gray-200 rounded-xl overflow-hidden bg-white',
        'hover:border-primary-300 transition-all duration-200',
        'shadow-sm hover:shadow-md',
        className
      )}
      {...props}
    >
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors duration-150"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-4 flex-1">
          {icon && (
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center">
              {icon}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-gray-900">{title}</h3>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
        <ChevronDown
          className={clsx(
            'w-5 h-5 text-gray-400 transition-transform duration-200 flex-shrink-0',
            isOpen && 'transform rotate-180'
          )}
        />
      </button>

      {/* Content */}
      <div
        className={clsx(
          'transition-all duration-300 ease-in-out overflow-hidden',
          isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="px-6 py-5 border-t border-gray-100 bg-gray-50/50">
          {children}
        </div>
      </div>
    </div>
  );
};

export interface AccordionProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  spacing?: 'sm' | 'md' | 'lg';
}

export const Accordion: React.FC<AccordionProps> = ({
  children,
  spacing = 'md',
  className,
  ...props
}) => {
  const spacingStyles = {
    sm: 'space-y-2',
    md: 'space-y-4',
    lg: 'space-y-6',
  };

  return (
    <div className={clsx(spacingStyles[spacing], className)} {...props}>
      {children}
    </div>
  );
};
