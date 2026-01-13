/**
 * Tooltip - Smart positioning tooltip component
 *
 * Features:
 * - Automatic flip/shift to stay within viewport
 * - Multiple placement options (top, bottom, left, right)
 * - Arrow indicator
 * - Accessible with ARIA attributes
 * - Configurable delay and offset
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../../lib/utils';

export type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';

export interface TooltipProps {
  /** Content to display in the tooltip */
  content: React.ReactNode;
  /** Element that triggers the tooltip */
  children: React.ReactElement;
  /** Preferred placement (will flip if insufficient space) */
  placement?: TooltipPlacement;
  /** Delay before showing tooltip (ms) */
  delay?: number;
  /** Offset from trigger element (px) */
  offset?: number;
  /** Whether tooltip is disabled */
  disabled?: boolean;
  /** Custom className for tooltip container */
  className?: string;
  /** Max width of tooltip */
  maxWidth?: number;
  /** Show arrow indicator */
  showArrow?: boolean;
}

interface Position {
  top: number;
  left: number;
  placement: TooltipPlacement;
}

const ARROW_SIZE = 6;
const VIEWPORT_PADDING = 8;

/**
 * Calculate optimal tooltip position
 */
function calculatePosition(
  triggerRect: DOMRect,
  tooltipRect: DOMRect,
  preferredPlacement: TooltipPlacement,
  offset: number
): Position {
  const { innerWidth: viewportWidth, innerHeight: viewportHeight } = window;

  // Calculate space available in each direction
  const spaceAbove = triggerRect.top - VIEWPORT_PADDING;
  const spaceBelow = viewportHeight - triggerRect.bottom - VIEWPORT_PADDING;
  const spaceLeft = triggerRect.left - VIEWPORT_PADDING;
  const spaceRight = viewportWidth - triggerRect.right - VIEWPORT_PADDING;

  // Determine actual placement based on available space
  let actualPlacement = preferredPlacement;

  if (preferredPlacement === 'top' && spaceAbove < tooltipRect.height + offset) {
    actualPlacement = spaceBelow >= tooltipRect.height + offset ? 'bottom' : 'top';
  } else if (preferredPlacement === 'bottom' && spaceBelow < tooltipRect.height + offset) {
    actualPlacement = spaceAbove >= tooltipRect.height + offset ? 'top' : 'bottom';
  } else if (preferredPlacement === 'left' && spaceLeft < tooltipRect.width + offset) {
    actualPlacement = spaceRight >= tooltipRect.width + offset ? 'right' : 'left';
  } else if (preferredPlacement === 'right' && spaceRight < tooltipRect.width + offset) {
    actualPlacement = spaceLeft >= tooltipRect.width + offset ? 'left' : 'right';
  }

  let top = 0;
  let left = 0;

  switch (actualPlacement) {
    case 'top':
      top = triggerRect.top - tooltipRect.height - offset - ARROW_SIZE;
      left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
      break;
    case 'bottom':
      top = triggerRect.bottom + offset + ARROW_SIZE;
      left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
      break;
    case 'left':
      top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
      left = triggerRect.left - tooltipRect.width - offset - ARROW_SIZE;
      break;
    case 'right':
      top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
      left = triggerRect.right + offset + ARROW_SIZE;
      break;
  }

  // Clamp horizontal position to viewport
  if (actualPlacement === 'top' || actualPlacement === 'bottom') {
    const minLeft = VIEWPORT_PADDING;
    const maxLeft = viewportWidth - tooltipRect.width - VIEWPORT_PADDING;
    left = Math.max(minLeft, Math.min(maxLeft, left));
  }

  // Clamp vertical position to viewport
  if (actualPlacement === 'left' || actualPlacement === 'right') {
    const minTop = VIEWPORT_PADDING;
    const maxTop = viewportHeight - tooltipRect.height - VIEWPORT_PADDING;
    top = Math.max(minTop, Math.min(maxTop, top));
  }

  return { top, left, placement: actualPlacement };
}

/**
 * Calculate arrow position
 */
function getArrowStyles(
  placement: TooltipPlacement,
  triggerRect: DOMRect,
  tooltipRect: DOMRect,
  tooltipLeft: number,
  tooltipTop: number
): React.CSSProperties {
  const arrowOffset = ARROW_SIZE;

  switch (placement) {
    case 'top':
      return {
        bottom: -arrowOffset,
        left: Math.max(
          8,
          Math.min(
            tooltipRect.width - 16,
            triggerRect.left + triggerRect.width / 2 - tooltipLeft - arrowOffset
          )
        ),
        borderWidth: `${arrowOffset}px ${arrowOffset}px 0`,
        borderColor: 'rgb(31 41 55) transparent transparent transparent',
      };
    case 'bottom':
      return {
        top: -arrowOffset,
        left: Math.max(
          8,
          Math.min(
            tooltipRect.width - 16,
            triggerRect.left + triggerRect.width / 2 - tooltipLeft - arrowOffset
          )
        ),
        borderWidth: `0 ${arrowOffset}px ${arrowOffset}px`,
        borderColor: 'transparent transparent rgb(31 41 55) transparent',
      };
    case 'left':
      return {
        right: -arrowOffset,
        top: Math.max(
          8,
          Math.min(
            tooltipRect.height - 16,
            triggerRect.top + triggerRect.height / 2 - tooltipTop - arrowOffset
          )
        ),
        borderWidth: `${arrowOffset}px 0 ${arrowOffset}px ${arrowOffset}px`,
        borderColor: 'transparent transparent transparent rgb(31 41 55)',
      };
    case 'right':
      return {
        left: -arrowOffset,
        top: Math.max(
          8,
          Math.min(
            tooltipRect.height - 16,
            triggerRect.top + triggerRect.height / 2 - tooltipTop - arrowOffset
          )
        ),
        borderWidth: `${arrowOffset}px ${arrowOffset}px ${arrowOffset}px 0`,
        borderColor: 'transparent rgb(31 41 55) transparent transparent',
      };
  }
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  placement = 'top',
  delay = 200,
  offset = 4,
  disabled = false,
  className,
  maxWidth = 280,
  showArrow = true,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState<Position | null>(null);
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    const newPosition = calculatePosition(
      triggerRect,
      tooltipRect,
      placement,
      offset
    );

    setPosition(newPosition);
  }, [placement, offset]);

  const handleMouseEnter = useCallback(() => {
    if (disabled) return;

    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  }, [delay, disabled]);

  const handleMouseLeave = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
    setPosition(null);
  }, []);

  const handleFocus = useCallback(() => {
    if (disabled) return;
    setIsVisible(true);
  }, [disabled]);

  const handleBlur = useCallback(() => {
    setIsVisible(false);
    setPosition(null);
  }, []);

  // Update position when visible
  useEffect(() => {
    if (isVisible) {
      // Use requestAnimationFrame to ensure tooltip is rendered before measuring
      requestAnimationFrame(() => {
        updatePosition();
      });
    }
  }, [isVisible, updatePosition]);

  // Update position on scroll/resize
  useEffect(() => {
    if (!isVisible) return;

    const handleUpdate = () => updatePosition();

    window.addEventListener('scroll', handleUpdate, true);
    window.addEventListener('resize', handleUpdate);

    return () => {
      window.removeEventListener('scroll', handleUpdate, true);
      window.removeEventListener('resize', handleUpdate);
    };
  }, [isVisible, updatePosition]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Clone child element with event handlers
  const trigger = React.cloneElement(children, {
    ref: triggerRef,
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    onFocus: handleFocus,
    onBlur: handleBlur,
    'aria-describedby': isVisible ? 'tooltip' : undefined,
  });

  // Don't render tooltip if disabled or no content
  if (disabled || !content) {
    return children;
  }

  const tooltipContent = isVisible && (
    <div
      ref={tooltipRef}
      id="tooltip"
      role="tooltip"
      className={cn(
        'fixed z-[9999] px-2.5 py-1.5 text-sm text-white bg-gray-800 rounded-md shadow-lg',
        'animate-in fade-in-0 zoom-in-95 duration-150',
        className
      )}
      style={{
        top: position?.top ?? -9999,
        left: position?.left ?? -9999,
        maxWidth,
        visibility: position ? 'visible' : 'hidden',
      }}
    >
      {content}
      {showArrow && position && triggerRef.current && tooltipRef.current && (
        <div
          className="absolute w-0 h-0"
          style={{
            borderStyle: 'solid',
            ...getArrowStyles(
              position.placement,
              triggerRef.current.getBoundingClientRect(),
              tooltipRef.current.getBoundingClientRect(),
              position.left,
              position.top
            ),
          }}
        />
      )}
    </div>
  );

  return (
    <>
      {trigger}
      {typeof document !== 'undefined' &&
        createPortal(tooltipContent, document.body)}
    </>
  );
};

/**
 * Simple tooltip wrapper for native title replacement
 * Use this as a drop-in replacement for title attribute
 */
export const TooltipWrapper: React.FC<{
  title: string;
  children: React.ReactElement;
  placement?: TooltipPlacement;
}> = ({ title, children, placement = 'top' }) => {
  return (
    <Tooltip content={title} placement={placement}>
      {children}
    </Tooltip>
  );
};

Tooltip.displayName = 'Tooltip';
TooltipWrapper.displayName = 'TooltipWrapper';
