# Data Model: UI Modernization & Design System

**Feature**: 002-ui-modernization
**Version**: 1.0.0
**Last Updated**: 2025-11-04
**Status**: Phase 1 - Design Artifacts

---

## Overview

This document defines the data models, schemas, and state structures for the UI modernization project. It includes design token specifications, component state models, and form validation schemas.

---

## 1. Design Tokens Schema

Design tokens are the atomic design decisions that power the entire design system. All tokens are centralized in `tailwind.config.js` and consumed via Tailwind utility classes.

### 1.1 Color Palette

#### Primary Colors (Brand Identity)
```typescript
type ColorScale = {
  50: string;   // Lightest
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;  // Base color
  600: string;  // Primary action color
  700: string;  // Hover/active state
  800: string;
  900: string;  // Darkest
  950: string;  // Near black
};

interface ColorPalette {
  primary: ColorScale;    // Blue scale (#0284c7 as base)
  secondary: ColorScale;  // Purple scale (#9333ea as base)
  success: ColorScale;    // Green scale (#22c55e as base)
  warning: ColorScale;    // Yellow/orange scale (#f59e0b as base)
  error: ColorScale;      // Red scale (#ef4444 as base)
  info: ColorScale;       // Optional (uses primary by default)
  gray: ColorScale;       // Neutral scale (inherited from Tailwind)
}
```

**Actual Values** (from `tailwind.config.js`):
```javascript
{
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',  // Main brand color
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
    950: '#082f49',
  },
  secondary: {
    50: '#faf5ff',
    100: '#f3e8ff',
    200: '#e9d5ff',
    300: '#d8b4fe',
    400: '#c084fc',
    500: '#a855f7',
    600: '#9333ea',
    700: '#7e22ce',
    800: '#6b21a8',
    900: '#581c87',
    950: '#3b0764',
  },
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  }
}
```

**Usage Guidelines**:
- `*-50, *-100`: Backgrounds, subtle highlights
- `*-500`: Default color for text/icons
- `*-600`: Primary action buttons, links
- `*-700`: Hover/active states for buttons
- `*-900, *-950`: Headings, strong emphasis

---

### 1.2 Spacing Scale

Based on 4px/8px grid system for consistent rhythm.

```typescript
interface SpacingScale {
  0: '0px';
  1: '0.25rem';   // 4px
  2: '0.5rem';    // 8px
  3: '0.75rem';   // 12px
  4: '1rem';      // 16px
  5: '1.25rem';   // 20px
  6: '1.5rem';    // 24px
  8: '2rem';      // 32px
  10: '2.5rem';   // 40px
  12: '3rem';     // 48px
  16: '4rem';     // 64px
  20: '5rem';     // 80px
  24: '6rem';     // 96px
  32: '8rem';     // 128px
  // Custom additions
  18: '4.5rem';   // 72px
  112: '28rem';   // 448px
  128: '32rem';   // 512px
}
```

**Usage Patterns**:
- **Tight spacing** (2, 3): Between related items (form label to input)
- **Normal spacing** (4, 6): Between sections, card padding
- **Loose spacing** (8, 12): Between major page sections
- **Layout spacing** (16, 20, 24): Page margins, container padding

---

### 1.3 Typography System

```typescript
interface TypographyScale {
  fontFamily: {
    sans: string[];  // ['Inter', 'system-ui', ...]
    mono: string[];  // ['Fira Code', 'Consolas', ...]
  };
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }];      // 12px
    sm: ['0.875rem', { lineHeight: '1.25rem' }];  // 14px
    base: ['1rem', { lineHeight: '1.5rem' }];     // 16px
    lg: ['1.125rem', { lineHeight: '1.75rem' }];  // 18px
    xl: ['1.25rem', { lineHeight: '1.75rem' }];   // 20px
    '2xl': ['1.5rem', { lineHeight: '2rem' }];    // 24px
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }]; // 30px
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }];   // 36px
  };
  fontWeight: {
    normal: 400;
    medium: 500;
    semibold: 600;
    bold: 700;
  };
}
```

**Typography Hierarchy**:
- **Headings**: `text-2xl font-bold` to `text-4xl font-bold`
- **Body text**: `text-base font-normal`
- **UI labels**: `text-sm font-medium`
- **Captions**: `text-xs text-gray-500`
- **Code**: `font-mono text-sm`

---

### 1.4 Shadow/Elevation System

```typescript
interface ShadowScale {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)';
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)';
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)';
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)';
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)';
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)';
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)';
  'inner-lg': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.1)'; // Custom
  none: '0 0 #0000';
}
```

**Elevation Mapping**:
- **Level 0** (`shadow-none`): Flush with background (default state)
- **Level 1** (`shadow-sm`): Subtle cards, inputs at rest
- **Level 2** (`shadow`): Standard cards, dropdowns
- **Level 3** (`shadow-md`): Hover state for cards
- **Level 4** (`shadow-lg`): Modals, popovers
- **Level 5** (`shadow-xl`): Drawers, overlays
- **Level 6** (`shadow-2xl`): Full-screen modals, notifications

---

### 1.5 Border Radius Scale

```typescript
interface BorderRadiusScale {
  none: '0px';
  sm: '0.125rem';   // 2px
  DEFAULT: '0.25rem'; // 4px
  md: '0.375rem';   // 6px
  lg: '0.5rem';     // 8px
  xl: '0.75rem';    // 12px
  '2xl': '1rem';    // 16px
  '3xl': '1.5rem';  // 24px
  '4xl': '2rem';    // 32px (custom)
  full: '9999px';   // Pills, circles
}
```

**Component Mapping**:
- **Buttons**: `rounded-lg` (8px)
- **Inputs**: `rounded-lg` (8px)
- **Cards**: `rounded-xl` (12px)
- **Modals**: `rounded-2xl` (16px)
- **Badges/Pills**: `rounded-full`
- **Avatars**: `rounded-full`

---

### 1.6 Breakpoint System

```typescript
interface BreakpointScale {
  xs: '320px';   // Mobile portrait (small phones)
  sm: '640px';   // Mobile landscape
  md: '768px';   // Tablet portrait
  lg: '1024px';  // Tablet landscape / small desktop
  xl: '1280px';  // Desktop
  '2xl': '1536px'; // Large desktop
}
```

**Responsive Strategy**:
- **Mobile-first**: Base styles target mobile, use `md:`, `lg:` for larger screens
- **Breakpoint usage**: `sm:` (640px+), `md:` (768px+), `lg:` (1024px+), `xl:` (1280px+)
- **Navigation**: Hamburger menu below `md` (768px)
- **Layout**: Single column below `md`, multi-column above

---

### 1.7 Animation/Transition Tokens

```typescript
interface AnimationTokens {
  duration: {
    fast: '150ms';
    normal: '200ms';
    slow: '300ms';
    slower: '500ms';
  };
  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)';
    in: 'cubic-bezier(0.4, 0, 1, 1)';
    out: 'cubic-bezier(0, 0, 0.2, 1)';
    inOut: 'cubic-bezier(0.4, 0, 0.6, 1)';
  };
  animation: {
    spin: 'spin 1s linear infinite';
    'spin-slow': 'spin 3s linear infinite';
    pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite';
    'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite';
    'fade-in': 'fade-in 200ms ease-out';
  };
}
```

**Usage Guidelines**:
- **Hover states**: 200ms duration
- **Accordion expand/collapse**: 300ms duration
- **Modal enter/exit**: 200ms duration
- **Toast slide-in**: 200ms duration
- **Loading spinners**: 1s infinite

---

## 2. Component State Models

### 2.1 Settings Form State

```typescript
/**
 * Complete state model for Settings page form.
 * Integrates with React Hook Form + Zod validation.
 */

interface ProviderConfig {
  api_key: string;
  model: string;
  temperature: number;  // 0.0 - 2.0
  max_tokens?: number;
}

interface CMSConfig {
  url: string;          // WordPress site URL
  username: string;
  password: string;     // Stored securely, never logged
  timeout?: number;     // Request timeout in seconds
}

interface CostLimits {
  daily_limit: number;    // USD, 0-1000
  monthly_limit: number;  // USD, 0-10000
  alert_threshold?: number; // Percentage (0-100)
}

interface ScreenshotRetention {
  retention_days: number; // 1-365 days
  auto_cleanup: boolean;
}

interface SettingsData {
  provider_config: ProviderConfig;
  cms_config: CMSConfig;
  cost_limits: CostLimits;
  screenshot_retention: ScreenshotRetention;
  updated_at?: string; // ISO 8601 timestamp
}

interface SettingsFormState {
  // Form data (managed by React Hook Form)
  data: SettingsData;

  // Form state flags
  isDirty: boolean;      // Has unsaved changes
  isValid: boolean;      // All fields pass validation
  isSubmitting: boolean; // Save operation in progress

  // UI state
  errors: Record<string, string>; // Field-level validation errors
  touchedFields: Set<string>;     // Fields user has interacted with

  // Meta information
  lastSaved?: Date;      // Timestamp of last successful save
  saveError?: string;    // Error message from failed save
}
```

**State Transitions**:
1. **Initial Load**: `isSubmitting: false, isDirty: false`
2. **User Edits Field**: `isDirty: true, touchedFields updated`
3. **Validation Error**: `errors populated, isValid: false`
4. **Submitting**: `isSubmitting: true`
5. **Save Success**: `isDirty: false, lastSaved: new Date()`
6. **Save Failure**: `isSubmitting: false, saveError: "..."`

---

### 2.2 Toast Notification State

```typescript
/**
 * Toast notification data model.
 * Used with Sonner library for user feedback.
 */

type ToastVariant = 'success' | 'error' | 'warning' | 'info' | 'loading';

interface ToastAction {
  label: string;          // Button text (e.g., "Retry", "Undo")
  onClick: () => void;    // Action handler
}

interface ToastMessage {
  id: string | number;    // Unique identifier (auto-generated)
  variant: ToastVariant;
  title: string;          // Main message
  description?: string;   // Additional context
  duration?: number;      // Auto-dismiss timeout (ms), default 5000
  action?: ToastAction;   // Optional action button
  dismissible?: boolean;  // Show close button, default true
  icon?: React.ReactNode; // Custom icon (overrides default)
}

interface ToastState {
  toasts: ToastMessage[];      // Active toasts (max 3 visible)
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'top-center' | 'bottom-center';
  maxToasts: number;           // Maximum simultaneous toasts
}
```

**Usage Patterns**:
```typescript
// Success notification
toast.success('Settings saved successfully');

// Error with description
toast.error('Save failed', {
  description: 'Network connection lost',
});

// With action button
toast.error('Save failed', {
  action: {
    label: 'Retry',
    onClick: () => handleRetry(),
  },
});

// Loading state (Promise API)
toast.promise(
  saveSettings(),
  {
    loading: 'Saving...',
    success: 'Settings saved!',
    error: (err) => `Failed: ${err.message}`,
  }
);
```

---

### 2.3 Navigation State

```typescript
/**
 * Navigation state for responsive menu handling.
 */

interface NavigationRoute {
  path: string;
  label: string;
  icon?: React.ComponentType;
  showInNav: boolean;
  badge?: string | number; // Optional badge (e.g., "3 new")
}

interface NavigationState {
  // Current route
  currentPath: string;

  // Mobile menu state
  isMobileMenuOpen: boolean;

  // Viewport state
  isMobile: boolean;  // <768px (md breakpoint)
  isTablet: boolean;  // 768px-1024px
  isDesktop: boolean; // >=1024px

  // Navigation items (from routes.ts)
  routes: NavigationRoute[];

  // Scroll position (for sticky header)
  isScrolled: boolean; // scrollY > 0
}
```

**State Management**:
```typescript
// Detect viewport size
const isMobile = useMediaQuery('(max-width: 767px)');

// Mobile menu toggle
const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

// Scroll detection
const [isScrolled, setIsScrolled] = useState(false);
useEffect(() => {
  const handleScroll = () => setIsScrolled(window.scrollY > 0);
  window.addEventListener('scroll', handleScroll);
  return () => window.removeEventListener('scroll', handleScroll);
}, []);
```

---

### 2.4 Skeleton Loading State

```typescript
/**
 * Skeleton loading state for content placeholders.
 */

interface SkeletonProps {
  variant: 'text' | 'rectangle' | 'circle';
  width?: string | number;   // CSS width value
  height?: string | number;  // CSS height value
  className?: string;        // Tailwind classes
}

interface SkeletonLoadingState {
  isLoading: boolean;
  skeletonCount: number;     // Number of skeleton items to show
  contentType: 'card' | 'list' | 'form' | 'table';
}
```

**Skeleton Variants**:
- **Text line**: `variant="text"` - Represents a line of text
- **Rectangle**: `variant="rectangle"` - Images, cards, large blocks
- **Circle**: `variant="circle"` - Avatars, icons

---

### 2.5 Modal/Dialog State

```typescript
/**
 * Modal state model for confirmation dialogs and overlays.
 */

interface ModalState {
  isOpen: boolean;
  title?: string;
  content: React.ReactNode;

  // Actions
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void;
  confirmLabel?: string;  // Default: "Confirm"
  cancelLabel?: string;   // Default: "Cancel"

  // Variants
  variant?: 'default' | 'danger'; // Danger = red confirm button

  // Behavior
  closeOnBackdropClick?: boolean; // Default: true
  closeOnEscape?: boolean;        // Default: true
  showCloseButton?: boolean;      // Default: true

  // Loading state (for async operations)
  isConfirming?: boolean;
}
```

**Usage Example**:
```typescript
// Unsaved changes confirmation
const [showConfirmation, setShowConfirmation] = useState(false);

const handleNavigateAway = () => {
  if (isDirty) {
    setShowConfirmation(true);
  } else {
    navigate('/other-page');
  }
};

<Modal
  isOpen={showConfirmation}
  title="Unsaved Changes"
  content="You have unsaved changes. Are you sure you want to leave?"
  variant="danger"
  confirmLabel="Discard Changes"
  cancelLabel="Stay on Page"
  onConfirm={() => navigate('/other-page')}
  onCancel={() => setShowConfirmation(false)}
/>
```

---

### 2.6 Accordion State

```typescript
/**
 * Accordion state for collapsible sections.
 */

interface AccordionItemState {
  id: string;
  isOpen: boolean;
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
}

interface AccordionState {
  items: AccordionItemState[];

  // Behavior modes
  allowMultiple?: boolean; // Allow multiple sections open (default: true)
  defaultOpenId?: string;  // ID of section to open by default
}
```

**Accordion Behavior**:
- **Single mode** (`allowMultiple: false`): Only one section open at a time
- **Multiple mode** (`allowMultiple: true`): Multiple sections can be open

---

## 3. Form Validation Schemas

### 3.1 Settings Form Schema (Zod)

```typescript
import { z } from 'zod';

/**
 * Comprehensive Zod schema for Settings page validation.
 * Provides type-safe validation with detailed error messages.
 */

export const providerConfigSchema = z.object({
  api_key: z.string()
    .min(1, '請輸入API密鑰')
    .regex(/^[A-Za-z0-9-_]+$/, 'API密鑰只能包含字母、數字、連字符和下劃線'),

  model: z.string()
    .min(1, '請選擇模型'),

  temperature: z.number()
    .min(0, '溫度不能小於0')
    .max(2, '溫度不能大於2')
    .default(0.7),

  max_tokens: z.number()
    .int('必須是整數')
    .min(1, '最小值為1')
    .max(32000, '最大值為32000')
    .optional(),
});

export const cmsConfigSchema = z.object({
  url: z.string()
    .url('請輸入有效的URL')
    .regex(/^https?:\/\/.+/, 'URL必須包含協議 (http或https)'),

  username: z.string()
    .min(1, '請輸入用戶名')
    .max(100, '用戶名過長'),

  password: z.string()
    .min(1, '請輸入密碼')
    .min(8, '密碼至少8個字符'),

  timeout: z.number()
    .int('必須是整數')
    .min(5, '超時時間至少5秒')
    .max(300, '超時時間最多300秒')
    .default(30)
    .optional(),
});

export const costLimitsSchema = z.object({
  daily_limit: z.number()
    .min(0, '日限額不能為負數')
    .max(1000, '日限額不能超過1000美元'),

  monthly_limit: z.number()
    .min(0, '月限額不能為負數')
    .max(10000, '月限額不能超過10000美元'),

  alert_threshold: z.number()
    .min(0, '警告閾值不能為負數')
    .max(100, '警告閾值不能超過100%')
    .default(80)
    .optional(),
}).refine(
  (data) => data.monthly_limit >= data.daily_limit * 30,
  {
    message: '月限額應至少為日限額的30倍',
    path: ['monthly_limit'],
  }
);

export const screenshotRetentionSchema = z.object({
  retention_days: z.number()
    .int('必須是整數')
    .min(1, '至少保留1天')
    .max(365, '最多保留365天'),

  auto_cleanup: z.boolean()
    .default(true),
});

export const settingsSchema = z.object({
  provider_config: providerConfigSchema,
  cms_config: cmsConfigSchema,
  cost_limits: costLimitsSchema,
  screenshot_retention: screenshotRetentionSchema,
});

// TypeScript type inference
export type SettingsFormData = z.infer<typeof settingsSchema>;
export type ProviderConfig = z.infer<typeof providerConfigSchema>;
export type CMSConfig = z.infer<typeof cmsConfigSchema>;
export type CostLimits = z.infer<typeof costLimitsSchema>;
export type ScreenshotRetention = z.infer<typeof screenshotRetentionSchema>;
```

**Usage in Forms**:
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { settingsSchema, type SettingsFormData } from '@/schemas/settings';

const { register, handleSubmit, formState: { errors } } = useForm<SettingsFormData>({
  resolver: zodResolver(settingsSchema),
});
```

---

### 3.2 Async Validation (WordPress Connection Test)

```typescript
/**
 * Async validation for testing WordPress connection.
 */

export const cmsConfigWithTestSchema = cmsConfigSchema.refine(
  async (data) => {
    try {
      const response = await fetch('/api/v1/settings/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cms_config: data }),
      });

      const result = await response.json();
      return result.success === true;
    } catch (error) {
      return false;
    }
  },
  {
    message: 'WordPress連接測試失敗，請檢查URL、用戶名和密碼',
  }
);
```

---

### 3.3 Custom Validation Helpers

```typescript
/**
 * Reusable validation utilities.
 */

// Check if API key format is valid
export const isValidAPIKey = (key: string): boolean => {
  return /^[A-Za-z0-9-_]+$/.test(key) && key.length >= 20;
};

// Check if URL is accessible (for WordPress URL)
export const isURLAccessible = async (url: string): Promise<boolean> => {
  try {
    const response = await fetch(url, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
};

// Validate cost limit relationships
export const areCostLimitsValid = (daily: number, monthly: number): boolean => {
  return monthly >= daily * 30;
};
```

---

## 4. Error State Models

### 4.1 Form Validation Errors

```typescript
/**
 * Structured error model for form validation.
 */

interface FieldError {
  field: string;        // Field path (e.g., "provider_config.api_key")
  message: string;      // User-friendly error message
  type: 'required' | 'pattern' | 'min' | 'max' | 'custom';
}

interface ValidationErrors {
  errors: FieldError[];
  isValid: boolean;
}
```

### 4.2 API Error State

```typescript
/**
 * API error handling model.
 */

interface APIError {
  status: number;       // HTTP status code
  message: string;      // Error message
  code?: string;        // Error code (e.g., "INVALID_CREDENTIALS")
  details?: Record<string, string>; // Field-specific errors
}

interface ErrorState {
  hasError: boolean;
  error: APIError | null;
  retryCount: number;
  canRetry: boolean;
}
```

---

## 5. Loading State Models

### 5.1 Data Fetching State

```typescript
/**
 * Standard data fetching state (React Query pattern).
 */

interface QueryState<T> {
  data: T | undefined;
  isLoading: boolean;    // Initial load
  isFetching: boolean;   // Refetch/background update
  isError: boolean;
  error: Error | null;
  refetch: () => void;
}
```

### 5.2 Mutation State

```typescript
/**
 * State for data mutations (create, update, delete).
 */

interface MutationState<T> {
  mutate: (data: T) => void;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
  error: Error | null;
  reset: () => void;
}
```

---

## 6. Accessibility State Models

### 6.1 Focus Management

```typescript
/**
 * Focus trap state for modals and drawers.
 */

interface FocusTrapState {
  isActive: boolean;
  firstFocusableElement: HTMLElement | null;
  lastFocusableElement: HTMLElement | null;
  previouslyFocusedElement: HTMLElement | null;
}
```

### 6.2 Screen Reader Announcements

```typescript
/**
 * Live region announcements for screen readers.
 */

interface AriaLiveAnnouncement {
  message: string;
  politeness: 'polite' | 'assertive' | 'off';
  clearAfter?: number; // Auto-clear timeout (ms)
}
```

---

## 7. Performance Metrics Models

### 7.1 Web Vitals

```typescript
/**
 * Core Web Vitals tracking.
 */

interface WebVitals {
  LCP: number;  // Largest Contentful Paint (ms)
  FID: number;  // First Input Delay (ms)
  CLS: number;  // Cumulative Layout Shift (score)
  TTFB: number; // Time to First Byte (ms)
  FCP: number;  // First Contentful Paint (ms)
}

interface PerformanceThresholds {
  LCP: { good: 2500, poor: 4000 };
  FID: { good: 100, poor: 300 };
  CLS: { good: 0.1, poor: 0.25 };
}
```

---

## 8. Data Model Usage Guidelines

### 8.1 State Management Best Practices

1. **Use React Hook Form for forms**: Centralize form state, validation
2. **Use React Query for server state**: Caching, background updates
3. **Use local state for UI**: Modal open/close, accordion state
4. **Avoid prop drilling**: Use context for deeply nested state

### 8.2 Validation Strategy

1. **Client-side first**: Zod schemas for immediate feedback
2. **Server-side confirmation**: API validates again for security
3. **Progressive disclosure**: Validate on blur, not on every keystroke
4. **Clear error messages**: User-friendly Chinese messages

### 8.3 Type Safety

1. **Infer types from Zod schemas**: `z.infer<typeof schema>`
2. **Use TypeScript strict mode**: Catch errors at compile time
3. **Document complex types**: JSDoc comments for clarity
4. **Export types alongside components**: Co-locate for maintainability

---

## Appendix: Design Token Reference

### Quick Reference Table

| Category | Token | Value | Usage |
|----------|-------|-------|-------|
| **Color** | `primary-600` | `#0284c7` | Primary buttons, links |
| **Color** | `gray-50` | `#f9fafb` | Page background |
| **Color** | `error-600` | `#dc2626` | Error states, destructive actions |
| **Spacing** | `space-4` | `1rem (16px)` | Standard padding |
| **Spacing** | `space-6` | `1.5rem (24px)` | Section spacing |
| **Typography** | `text-base` | `1rem (16px)` | Body text |
| **Typography** | `text-sm` | `0.875rem (14px)` | UI labels, captions |
| **Shadow** | `shadow-md` | Custom | Card hover state |
| **Radius** | `rounded-lg` | `0.5rem (8px)` | Buttons, inputs |
| **Radius** | `rounded-xl` | `0.75rem (12px)` | Cards |

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-04
**Next Review**: After implementation feedback
**Maintained By**: Frontend Engineering Team
