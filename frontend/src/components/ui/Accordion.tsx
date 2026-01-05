/**
 * Modern Accordion component for collapsible content sections.
 * Provides smooth animations and accessible keyboard navigation.
 */

import { useEffect, useMemo, useRef, useState, ReactNode, HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { ChevronDown } from 'lucide-react';

const TRANSITION_DURATION_MS = 300;
const TRANSITION_TIMING = 'cubic-bezier(0.25, 0.1, 0.25, 1)';

export interface AccordionItemProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  /** Initial state if uncontrolled */
  defaultOpen?: boolean;
  /** Controlled open state */
  isOpen?: boolean;
  /** Callback when open state changes (for controlled mode) */
  onToggle?: (isOpen: boolean) => void;
  children: ReactNode;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  title,
  subtitle,
  icon,
  defaultOpen = false,
  isOpen: controlledIsOpen,
  onToggle,
  children,
  className,
  ...props
}) => {
  // Support both controlled and uncontrolled modes
  const isControlled = controlledIsOpen !== undefined;
  const [internalIsOpen, setInternalIsOpen] = useState(defaultOpen);
  const isOpen = isControlled ? controlledIsOpen : internalIsOpen;

  const handleToggle = () => {
    const newIsOpen = !isOpen;
    if (!isControlled) {
      setInternalIsOpen(newIsOpen);
    }
    onToggle?.(newIsOpen);
  };

  const contentRef = useRef<HTMLDivElement>(null);
  const isInitialMount = useRef(true);

  const transitionStyle = useMemo(
    () =>
      `height ${TRANSITION_DURATION_MS}ms ${TRANSITION_TIMING}, opacity ${TRANSITION_DURATION_MS}ms ${TRANSITION_TIMING}`,
    []
  );

  useEffect(() => {
    const contentEl = contentRef.current;
    if (!contentEl) return;

    if (isInitialMount.current) {
      isInitialMount.current = false;
      contentEl.style.height = isOpen ? 'auto' : '0px';
      contentEl.style.opacity = isOpen ? '1' : '0';
      contentEl.style.transition = transitionStyle;
      return;
    }

    const startAnimation = () => {
      const scrollHeight = contentEl.scrollHeight;

      if (isOpen) {
        contentEl.style.transition = transitionStyle;
        contentEl.style.height = '0px';
        contentEl.style.opacity = '0';

        requestAnimationFrame(() => {
          contentEl.style.height = `${scrollHeight}px`;
          contentEl.style.opacity = '1';
        });

        const handleOpenEnd = (event: TransitionEvent) => {
          if (event.propertyName === 'height') {
            contentEl.style.height = 'auto';
            contentEl.removeEventListener('transitionend', handleOpenEnd);
          }
        };

        contentEl.addEventListener('transitionend', handleOpenEnd);
      } else {
        contentEl.style.transition = transitionStyle;
        contentEl.style.height = `${scrollHeight}px`;
        contentEl.style.opacity = '1';

        requestAnimationFrame(() => {
          contentEl.style.height = '0px';
          contentEl.style.opacity = '0';
        });
      }
    };

    startAnimation();
  }, [isOpen, transitionStyle]);

  return (
    <div
      className={clsx(
        'rounded-2xl border border-gray-200 bg-white shadow-sm transition-shadow duration-300',
        isOpen ? 'shadow-md' : 'hover:shadow-md',
        className
      )}
      {...props}
    >
      <button
        type="button"
        onClick={handleToggle}
        className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition-colors duration-200 hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary-500 rounded-t-2xl"
        aria-expanded={isOpen}
      >
        <div className="flex flex-1 items-center gap-4">
          {icon && (
            <div
              className={clsx(
                'flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-primary-50 text-primary-600 transition-transform duration-300',
                isOpen ? 'scale-105' : 'scale-100'
              )}
            >
              {icon}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
          </div>
        </div>
        <ChevronDown
          className={clsx(
            'h-5 w-5 flex-shrink-0 text-gray-400 transition-transform duration-300',
            isOpen ? 'rotate-180 text-primary-600' : 'rotate-0'
          )}
        />
      </button>

      <div
        ref={contentRef}
        className="overflow-hidden px-6"
        style={{
          height: defaultOpen ? 'auto' : '0px',
          opacity: defaultOpen ? 1 : 0,
          transition: transitionStyle,
        }}
      >
        <div className="border-t border-gray-100 bg-gray-50/40 py-5">{children}</div>
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
