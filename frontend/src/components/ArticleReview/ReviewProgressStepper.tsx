/**
 * ReviewProgressStepper - Visual progress indicator for article review workflow
 *
 * Phase 8.1: Modal Framework (Updated 2025-12-06)
 * - Shows 3 steps: Parsing → Proofreading → Publish
 * - Highlights current step
 * - Shows completed steps with checkmark
 * - **Clickable steps** for direct navigation (replaces redundant Tabs)
 *
 * Design:
 * - Step 0: 解析审核 (Parsing Review)
 * - Step 1: 校对审核 (Proofreading Review)
 * - Step 2: 发布预览 (Publish Preview)
 */

import React from 'react';
import { clsx } from 'clsx';

export interface ReviewProgressStepperProps {
  /** Current step (0-2) */
  currentStep: number;
  /** Callback when a step is clicked */
  onStepClick?: (stepId: number) => void;
}

interface Step {
  id: number;
  label: string;
  description: string;
}

const STEPS: Step[] = [
  {
    id: 0,
    label: '解析审核',
    description: '审核标题、作者、图片、SEO',
  },
  {
    id: 1,
    label: '校对审核',
    description: '审核校对建议和修改',
  },
  {
    id: 2,
    label: '上稿預覽',
    description: '最終預覽和上稿設置',
  },
];

/**
 * ReviewProgressStepper Component
 */
export const ReviewProgressStepper: React.FC<ReviewProgressStepperProps> = ({
  currentStep,
  onStepClick,
}) => {
  return (
    <nav aria-label="Progress" className="w-full max-w-4xl mx-auto">
      <ol className="flex items-center justify-between">
        {STEPS.map((step, stepIdx) => {
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;
          const isUpcoming = currentStep < step.id;

          return (
            <li
              key={step.id}
              className={clsx(
                'relative flex-1',
                stepIdx !== STEPS.length - 1 && 'pr-8 sm:pr-20'
              )}
            >
              {/* Connector line */}
              {stepIdx !== STEPS.length - 1 && (
                <div
                  className="absolute top-4 left-0 right-0 -ml-px h-0.5"
                  aria-hidden="true"
                  style={{ left: '50%', width: 'calc(100% + 2rem)' }}
                >
                  <div
                    className={clsx(
                      'h-full transition-colors',
                      isCompleted ? 'bg-primary-600' : 'bg-gray-200'
                    )}
                  />
                </div>
              )}

              {/* Step indicator - Clickable */}
              <button
                type="button"
                onClick={() => onStepClick?.(step.id)}
                className={clsx(
                  'relative flex flex-col items-center group',
                  onStepClick && 'cursor-pointer',
                  !onStepClick && 'cursor-default'
                )}
                disabled={!onStepClick}
              >
                {/* Circle */}
                <span
                  className={clsx(
                    'flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all',
                    isCompleted && 'bg-primary-600 border-primary-600',
                    isCurrent && 'border-primary-600 bg-white ring-2 ring-primary-200',
                    isUpcoming && 'border-gray-300 bg-white',
                    onStepClick && 'group-hover:scale-110 group-hover:shadow-md'
                  )}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  {isCompleted ? (
                    <svg
                      className="h-5 w-5 text-white"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span
                      className={clsx(
                        'text-sm font-semibold',
                        isCurrent && 'text-primary-600',
                        isUpcoming && 'text-gray-500'
                      )}
                    >
                      {step.id + 1}
                    </span>
                  )}
                </span>

                {/* Label */}
                <span className="mt-2 text-center">
                  <span
                    className={clsx(
                      'block text-sm font-medium transition-colors',
                      isCurrent && 'text-primary-600',
                      isCompleted && 'text-gray-900',
                      isUpcoming && 'text-gray-500',
                      onStepClick && 'group-hover:text-primary-600'
                    )}
                  >
                    {step.label}
                  </span>
                  <span className="mt-1 block text-xs text-gray-500">
                    {step.description}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

ReviewProgressStepper.displayName = 'ReviewProgressStepper';
