/**
 * Skeleton loading components for content placeholders.
 */

import { forwardRef, type CSSProperties, type HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

type DimensionValue = number | string;
type SkeletonShape = 'rectangle' | 'circle' | 'text';
type SkeletonRadius = 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full';

const radiusClasses: Record<SkeletonRadius, string> = {
  none: 'rounded-none',
  sm: 'rounded',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  full: 'rounded-full',
};

const toDimension = (value?: DimensionValue) => {
  if (value === undefined || value === null) {
    return undefined;
  }
  return typeof value === 'number' ? `${value}px` : value;
};

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  shape?: SkeletonShape;
  width?: DimensionValue;
  height?: DimensionValue;
  /**
   * Applies rounded-* classes for rectangle variants.
   * Ignored for circle variants which are always fully rounded.
   */
  radius?: SkeletonRadius;
  /**
   * Number of lines to render when shape === 'text'.
   */
  lines?: number;
  /**
   * Provide explicit widths for text skeleton lines.
   * Accepts a single value (applied to all) or an array matching the line count.
   */
  lineWidths?: DimensionValue | DimensionValue[];
  /**
   * Height for each text skeleton line (default 14px).
   */
  lineHeight?: DimensionValue;
  /**
   * Gap between text skeleton lines (default 0.5rem).
   */
  lineGap?: DimensionValue;
  /**
   * Disable the default pulse animation if set to false.
   */
  animate?: boolean;
}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  (
    {
      shape = 'rectangle',
      width,
      height,
      radius = 'md',
      lines = 3,
      lineWidths,
      lineHeight = 14,
      lineGap = '0.5rem',
      animate = true,
      className,
      style,
      ...props
    },
    ref
  ) => {
    const animationClass = animate ? 'animate-pulse' : '';

    if (shape === 'text') {
      const lineCount = Math.max(lines, 1);
      const resolvedWidths = (() => {
        if (Array.isArray(lineWidths)) {
          return lineWidths.map((value) => toDimension(value));
        }
        if (lineWidths !== undefined) {
          return Array.from({ length: lineCount }, () => toDimension(lineWidths));
        }
        return Array.from({ length: lineCount }, (_, index) => {
          if (lineCount === 1) return '100%';
          if (index === 0) return '60%';
          if (index === lineCount - 1) return '80%';
          return '100%';
        });
      })();

      return (
        <div
          ref={ref}
          className={cn('flex flex-col', animationClass, className)}
          style={{ rowGap: toDimension(lineGap), ...style }}
          aria-hidden
          {...props}
        >
          {resolvedWidths.map((resolvedWidth, index) => (
            <div
              key={`skeleton-text-${index}`}
              className="h-3 rounded-md bg-gray-200/80 dark:bg-gray-700/70"
              style={{
                width: resolvedWidth,
                height: toDimension(lineHeight),
              }}
            />
          ))}
        </div>
      );
    }

    const resolvedStyle: CSSProperties = {
      width: toDimension(width),
      height: toDimension(height),
      ...style,
    };

    return (
      <div
        ref={ref}
        className={cn(
          'bg-gray-200/80 dark:bg-gray-700/70',
          animationClass,
          shape === 'circle' ? radiusClasses.full : radiusClasses[radius],
          className
        )}
        style={resolvedStyle}
        aria-hidden
        {...props}
      />
    );
  }
);

Skeleton.displayName = 'Skeleton';

export interface SkeletonCardProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Number of content lines rendered inside the card body.
   */
  lines?: number;
  /**
   * Number of footer action button placeholders.
   */
  actions?: number;
}

export const SkeletonCard = forwardRef<HTMLDivElement, SkeletonCardProps>(
  ({ lines = 3, actions = 2, className, ...props }, ref) => {
    const actionCount = Math.max(actions, 0);
    return (
      <div
        ref={ref}
        className={cn(
          'space-y-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm',
          className
        )}
        {...props}
      >
        <div className="space-y-3">
          <Skeleton width="45%" height={24} />
          <Skeleton shape="text" lines={1} lineWidths={['65%']} />
        </div>

        <div className="space-y-3">
          <Skeleton shape="text" lines={lines} />
        </div>

        {actionCount > 0 && (
          <div className="flex flex-wrap gap-3">
            {Array.from({ length: actionCount }).map((_, index) => (
              <Skeleton
                key={`skeleton-card-action-${index}`}
                width={110}
                height={40}
                radius="lg"
              />
            ))}
          </div>
        )}
      </div>
    );
  }
);

SkeletonCard.displayName = 'SkeletonCard';

export interface SkeletonSettingsSectionProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Number of form field placeholders to render.
   */
  fieldCount?: number;
  /**
   * Render a group of tab placeholders at the top of the section.
   */
  hasTabs?: boolean;
  /**
   * Render circular icon placeholder in the header.
   */
  showIcon?: boolean;
}

export const SkeletonSettingsSection = forwardRef<
  HTMLDivElement,
  SkeletonSettingsSectionProps
>(({ fieldCount = 4, hasTabs = false, showIcon = true, className, ...props }, ref) => {
  const totalFields = Math.max(fieldCount, 0);

  return (
    <div
      ref={ref}
      className={cn(
        'space-y-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm',
        className
      )}
      {...props}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3 flex-1">
          <Skeleton width="40%" height={24} />
          <Skeleton shape="text" lines={1} lineWidths={['70%']} />
        </div>
        {showIcon && <Skeleton shape="circle" width={40} height={40} />}
      </div>

      {hasTabs && (
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton
              key={`skeleton-tab-${index}`}
              height={36}
              width={110}
              radius="lg"
              className="bg-gray-200/60"
            />
          ))}
        </div>
      )}

      <div className="space-y-5">
        {Array.from({ length: totalFields }).map((_, index) => (
          <div key={`skeleton-settings-field-${index}`} className="space-y-2">
            <Skeleton shape="text" lines={1} lineWidths={['35%']} />
            <Skeleton height={44} radius="lg" />
          </div>
        ))}
      </div>
    </div>
  );
});

SkeletonSettingsSection.displayName = 'SkeletonSettingsSection';

