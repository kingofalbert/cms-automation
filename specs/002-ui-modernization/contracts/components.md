# Component Contracts: Design System Components

**Feature**: 002-ui-modernization
**Version**: 1.0.0
**Last Updated**: 2025-11-04
**Status**: Phase 1 - Design Artifacts

---

## Overview

This document defines complete TypeScript interfaces and contracts for all design system components. Each component specification includes:

- **Props interface**: Complete TypeScript type definition
- **Variants**: All visual/behavioral variants
- **States**: Interactive states (hover, focus, disabled, etc.)
- **Accessibility**: ARIA attributes and keyboard support
- **Usage examples**: Code samples showing correct usage

All components follow these principles:
1. **Accessibility-first**: WCAG 2.1 AA compliance
2. **Composable**: Can be combined to build complex UIs
3. **Type-safe**: Full TypeScript support
4. **Customizable**: Accept className for Tailwind extensions
5. **Forwardable refs**: Support DOM access via ref

---

## 1. Button Component

### 1.1 Interface

```typescript
import { ButtonHTMLAttributes, ReactNode, forwardRef } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Visual variant of the button.
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';

  /**
   * Size variant.
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Loading state - shows spinner and disables button.
   * @default false
   */
  isLoading?: boolean;

  /**
   * Makes button full width of container.
   * @default false
   */
  fullWidth?: boolean;

  /**
   * Icon to display before text (left side).
   */
  iconLeft?: ReactNode;

  /**
   * Icon to display after text (right side).
   */
  iconRight?: ReactNode;

  /**
   * Additional CSS classes (Tailwind utilities).
   */
  className?: string;

  /**
   * Button content (text or JSX).
   */
  children: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>((props, ref) => {
  // Implementation
});
```

### 1.2 Variant Specifications

#### Primary Button
```typescript
// Visual: Solid background, high contrast
// Usage: Primary call-to-action (Save, Submit, Create)
// Colors: bg-primary-600, hover:bg-primary-700, text-white
// Focus: ring-2 ring-primary-500

<Button variant="primary">Save Settings</Button>
```

#### Secondary Button
```typescript
// Visual: Solid background, alternative color
// Usage: Secondary actions (Cancel when paired with primary)
// Colors: bg-secondary-600, hover:bg-secondary-700, text-white

<Button variant="secondary">Learn More</Button>
```

#### Outline Button
```typescript
// Visual: Transparent background, border
// Usage: Tertiary actions, less emphasis
// Colors: border-gray-300, text-gray-700, hover:bg-gray-50

<Button variant="outline">Cancel</Button>
```

#### Ghost Button
```typescript
// Visual: No background, no border, minimal
// Usage: Icon buttons, navigation items
// Colors: text-gray-700, hover:bg-gray-100

<Button variant="ghost">Edit</Button>
```

#### Danger Button
```typescript
// Visual: Red color scheme for destructive actions
// Usage: Delete, Remove, Destroy operations
// Colors: bg-error-600, hover:bg-error-700, text-white

<Button variant="danger">Delete Account</Button>
```

### 1.3 Size Specifications

```typescript
// Small: Compact UI, toolbar buttons
size="sm"  // px-3 py-1.5 text-sm

// Medium (default): Standard buttons
size="md"  // px-4 py-2 text-base

// Large: Hero CTAs, important actions
size="lg"  // px-6 py-3 text-lg
```

### 1.4 State Specifications

```typescript
// Loading state
<Button isLoading>Saving...</Button>
// Shows spinner icon, disabled during loading

// Disabled state
<Button disabled>Submit</Button>
// opacity-50, cursor-not-allowed

// With icons
<Button iconLeft={<Save />}>Save</Button>
<Button iconRight={<ChevronRight />}>Next</Button>
```

### 1.5 Accessibility

```typescript
// Keyboard: Enter, Space to activate
// Focus: Visible focus ring (ring-2)
// Screen reader: Button role (native <button>)
// Disabled: aria-disabled="true"
// Loading: aria-busy="true"

<Button
  aria-label="Save settings"  // For icon-only buttons
  aria-describedby="save-hint" // Additional context
>
  Save
</Button>
```

---

## 2. Input Component

### 2.1 Interface

```typescript
import { InputHTMLAttributes, forwardRef } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /**
   * Input label text.
   */
  label?: string;

  /**
   * Error message to display below input.
   */
  error?: string;

  /**
   * Helper text (hint) to display below input.
   */
  helperText?: string;

  /**
   * Makes input full width of container.
   * @default false
   */
  fullWidth?: boolean;

  /**
   * Icon to display inside input (left side).
   */
  iconLeft?: React.ReactNode;

  /**
   * Icon to display inside input (right side).
   */
  iconRight?: React.ReactNode;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>((props, ref) => {
  // Implementation
});
```

### 2.2 Input Types

```typescript
// Text input (default)
<Input type="text" label="Username" />

// Email input with validation
<Input type="email" label="Email Address" />

// Password input
<Input type="password" label="Password" />

// Number input
<Input type="number" label="Age" min={0} max={120} />

// URL input
<Input type="url" label="Website" placeholder="https://example.com" />

// Search input
<Input type="search" label="Search" placeholder="Search articles..." />
```

### 2.3 States

```typescript
// Normal state
<Input label="API Key" />

// With helper text
<Input
  label="API Key"
  helperText="Found in your provider dashboard"
/>

// Error state
<Input
  label="API Key"
  error="API密鑰不能為空"
/>

// Disabled state
<Input label="Username" disabled value="admin" />

// Required field
<Input label="Email" required />
// Shows red asterisk (*) after label

// With icons
<Input
  label="Search"
  iconLeft={<Search className="w-4 h-4" />}
  placeholder="Search..."
/>
```

### 2.4 Validation Integration

```typescript
// React Hook Form integration
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const { register, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
});

<Input
  label="Email"
  {...register('email')}
  error={errors.email?.message}
/>
```

### 2.5 Accessibility

```typescript
// ARIA attributes
<Input
  label="Email"
  aria-invalid={!!error}
  aria-describedby={error ? 'email-error' : 'email-helper'}
  aria-required={required}
/>

// Label association (automatic via htmlFor)
// Error announcement (role="alert" on error message)
// Helper text association (aria-describedby)
```

---

## 3. Toggle Component

### 3.1 Interface

```typescript
import { InputHTMLAttributes, forwardRef } from 'react';

export interface ToggleProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /**
   * Label text displayed next to toggle.
   */
  label?: string;

  /**
   * Helper text displayed below toggle.
   */
  helperText?: string;

  /**
   * Checked state (controlled).
   */
  checked?: boolean;

  /**
   * Default checked state (uncontrolled).
   */
  defaultChecked?: boolean;

  /**
   * Change handler.
   */
  onChange?: (checked: boolean) => void;

  /**
   * Size variant.
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Toggle = forwardRef<HTMLInputElement, ToggleProps>((props, ref) => {
  // Implementation
});
```

### 3.2 Visual States

```typescript
// Unchecked (off)
<Toggle label="Enable notifications" />
// Background: gray-200, Switch: white (left)

// Checked (on)
<Toggle label="Enable notifications" checked />
// Background: primary-600, Switch: white (right)

// Disabled
<Toggle label="Enable notifications" disabled />
// Opacity: 50%, cursor: not-allowed

// With helper text
<Toggle
  label="Auto-cleanup"
  helperText="Automatically delete old screenshots"
/>
```

### 3.3 Sizes

```typescript
// Small
<Toggle size="sm" label="Compact toggle" />
// Height: 20px, Width: 36px

// Medium (default)
<Toggle size="md" label="Standard toggle" />
// Height: 24px, Width: 44px

// Large
<Toggle size="lg" label="Large toggle" />
// Height: 28px, Width: 52px
```

### 3.4 Usage Patterns

```typescript
// Controlled toggle
const [enabled, setEnabled] = useState(false);

<Toggle
  label="Enable feature"
  checked={enabled}
  onChange={setEnabled}
/>

// Form integration
<Toggle
  label="Auto-cleanup"
  {...register('auto_cleanup')}
/>
```

### 3.5 Accessibility

```typescript
// Role: switch (via aria-role)
// Keyboard: Space, Enter to toggle
// State: aria-checked="true/false"
// Label: Associated via htmlFor

<Toggle
  label="Enable notifications"
  aria-label="Enable email notifications" // If no label prop
  role="switch"
  aria-checked={checked}
/>
```

---

## 4. Toast Component

### 4.1 Interface

```typescript
/**
 * Toast notification component.
 * Note: Implementation uses Sonner library.
 * This interface documents the API for toast() function.
 */

export type ToastVariant = 'success' | 'error' | 'warning' | 'info' | 'loading';

export interface ToastOptions {
  /**
   * Additional description text.
   */
  description?: string;

  /**
   * Auto-dismiss duration in milliseconds.
   * @default 5000
   */
  duration?: number;

  /**
   * Action button configuration.
   */
  action?: {
    label: string;
    onClick: () => void;
  };

  /**
   * Show close button.
   * @default true
   */
  closeButton?: boolean;

  /**
   * Custom icon to override default.
   */
  icon?: React.ReactNode;

  /**
   * Toast ID for manual dismissal.
   */
  id?: string | number;
}

export interface ToastAPI {
  /**
   * Show success toast.
   */
  success: (message: string, options?: ToastOptions) => void;

  /**
   * Show error toast.
   */
  error: (message: string, options?: ToastOptions) => void;

  /**
   * Show warning toast.
   */
  warning: (message: string, options?: ToastOptions) => void;

  /**
   * Show info toast.
   */
  info: (message: string, options?: ToastOptions) => void;

  /**
   * Show loading toast.
   */
  loading: (message: string, options?: ToastOptions) => void;

  /**
   * Promise-based toast (auto-handles loading/success/error).
   */
  promise: <T>(
    promise: Promise<T>,
    options: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: Error) => string);
    }
  ) => Promise<T>;

  /**
   * Dismiss toast by ID.
   */
  dismiss: (id?: string | number) => void;
}

// Global toast function (from Sonner)
export const toast: ToastAPI;
```

### 4.2 Usage Examples

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

// Custom duration
toast.info('New update available', {
  duration: 10000, // 10 seconds
});

// Promise API (auto-handles states)
toast.promise(
  saveSettings(),
  {
    loading: 'Saving settings...',
    success: 'Settings saved!',
    error: (err) => `Failed: ${err.message}`,
  }
);

// Manual dismissal
const toastId = toast.loading('Processing...');
// Later...
toast.dismiss(toastId);
```

### 4.3 Visual Specifications

```typescript
// Success toast
// Icon: CheckCircle (green)
// Background: white
// Border: green-500
// Position: top-right

// Error toast
// Icon: XCircle (red)
// Background: white
// Border: error-500
// Position: top-right

// Warning toast
// Icon: AlertTriangle (yellow)
// Background: white
// Border: warning-500

// Info toast
// Icon: Info (blue)
// Background: white
// Border: primary-500

// Loading toast
// Icon: Spinner (animated)
// Background: white
// No auto-dismiss
```

### 4.4 Accessibility

```typescript
// ARIA live region: aria-live="polite" (success, info, warning)
// ARIA live region: aria-live="assertive" (error)
// Role: status
// Keyboard: Escape to dismiss (if closeButton: true)
// Screen reader: Announces message when toast appears
```

---

## 5. Skeleton Component

### 5.1 Interface

```typescript
export interface SkeletonProps {
  /**
   * Visual variant.
   * @default 'rectangle'
   */
  variant?: 'text' | 'rectangle' | 'circle';

  /**
   * Width (CSS value or Tailwind class).
   */
  width?: string | number;

  /**
   * Height (CSS value or Tailwind class).
   */
  height?: string | number;

  /**
   * Additional CSS classes.
   */
  className?: string;

  /**
   * Disable animation (for prefers-reduced-motion).
   * @default false
   */
  disableAnimation?: boolean;
}

export const Skeleton: React.FC<SkeletonProps>;
```

### 5.2 Variants

```typescript
// Text line (for text placeholders)
<Skeleton variant="text" className="w-48 h-4" />
// Rounded: 4px, Height: 16px

// Rectangle (for images, cards)
<Skeleton variant="rectangle" className="w-full h-32" />
// Rounded: 8px

// Circle (for avatars)
<Skeleton variant="circle" className="w-10 h-10" />
// Rounded: 9999px (full circle)
```

### 5.3 Composed Skeletons

```typescript
// Card skeleton
export const SkeletonCard: React.FC = () => (
  <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
    <Skeleton variant="text" className="w-1/2 h-6" />
    <Skeleton variant="text" className="w-3/4 h-4" />
    <Skeleton variant="text" className="w-full h-4" />
    <Skeleton variant="rectangle" className="h-32 w-full" />
  </div>
);

// Settings section skeleton
export const SkeletonSettingsSection: React.FC = () => (
  <div className="space-y-6">
    {/* Section header */}
    <div className="space-y-2">
      <Skeleton variant="text" className="w-1/3 h-6" />
      <Skeleton variant="text" className="w-2/3 h-4" />
    </div>

    {/* Form fields */}
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton variant="text" className="w-24 h-4" />
          <Skeleton variant="rectangle" className="h-10 w-full" />
        </div>
      ))}
    </div>
  </div>
);

// Avatar + text skeleton
export const SkeletonUserInfo: React.FC = () => (
  <div className="flex items-center space-x-3">
    <Skeleton variant="circle" className="w-10 h-10" />
    <div className="space-y-2 flex-1">
      <Skeleton variant="text" className="w-32 h-4" />
      <Skeleton variant="text" className="w-48 h-3" />
    </div>
  </div>
);
```

### 5.4 Animation

```typescript
// Default animation (pulse)
// Duration: 2s
// Easing: cubic-bezier(0.4, 0, 0.6, 1)
// Keyframes: 0%, 100% { opacity: 1 } 50% { opacity: 0.5 }

// Respects prefers-reduced-motion
<Skeleton className="motion-safe:animate-pulse motion-reduce:opacity-50" />
```

### 5.5 Accessibility

```typescript
// ARIA: aria-busy="true" on container
// ARIA: aria-live="polite" for content loading announcement
// Hidden from screen reader: aria-hidden="true" on skeleton itself

<div aria-busy="true" aria-label="Loading content">
  <Skeleton variant="text" aria-hidden="true" />
</div>
```

---

## 6. Accordion Component

### 6.1 Interface

```typescript
export interface AccordionItemProps {
  /**
   * Unique identifier for this item.
   */
  id?: string;

  /**
   * Accordion header title.
   */
  title: string;

  /**
   * Optional subtitle below title.
   */
  subtitle?: string;

  /**
   * Icon to display in header.
   */
  icon?: React.ReactNode;

  /**
   * Initially open state.
   * @default false
   */
  defaultOpen?: boolean;

  /**
   * Content to display when expanded.
   */
  children: React.ReactNode;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const AccordionItem: React.FC<AccordionItemProps>;

export interface AccordionProps {
  /**
   * Accordion items (AccordionItem components).
   */
  children: React.ReactNode;

  /**
   * Spacing between items.
   * @default 'md'
   */
  spacing?: 'sm' | 'md' | 'lg';

  /**
   * Allow multiple items open at once.
   * @default true
   */
  allowMultiple?: boolean;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Accordion: React.FC<AccordionProps>;
```

### 6.2 Usage Examples

```typescript
// Basic accordion
<Accordion>
  <AccordionItem title="Section 1">
    <p>Content for section 1</p>
  </AccordionItem>
  <AccordionItem title="Section 2">
    <p>Content for section 2</p>
  </AccordionItem>
</Accordion>

// With icons and subtitles
<Accordion>
  <AccordionItem
    title="Provider Configuration"
    subtitle="API keys and model settings"
    icon={<Settings className="w-5 h-5" />}
    defaultOpen
  >
    {/* Settings form fields */}
  </AccordionItem>
</Accordion>

// Single-open mode
<Accordion allowMultiple={false}>
  <AccordionItem title="Section 1">Content 1</AccordionItem>
  <AccordionItem title="Section 2">Content 2</AccordionItem>
</Accordion>
```

### 6.3 Animation Specifications

```typescript
// Expand animation
// Duration: 300ms
// Easing: ease-in-out
// Property: max-height (0 → 2000px), opacity (0 → 1)

// Collapse animation
// Duration: 300ms
// Easing: ease-in-out
// Property: max-height (2000px → 0), opacity (1 → 0)

// Chevron rotation
// Duration: 200ms
// Rotation: 0deg → 180deg (when open)
```

### 6.4 Accessibility

```typescript
// ARIA: aria-expanded="true/false" on header button
// Role: button (on header)
// Keyboard: Enter, Space to toggle
// Focus: Visible focus ring on header

<button
  aria-expanded={isOpen}
  aria-controls="accordion-content-1"
  onClick={() => setIsOpen(!isOpen)}
>
  {title}
</button>

<div id="accordion-content-1" role="region" aria-labelledby="accordion-header-1">
  {children}
</div>
```

---

## 7. Card Component

### 7.1 Interface

```typescript
export interface CardProps {
  /**
   * Card header content.
   */
  header?: React.ReactNode;

  /**
   * Card body content.
   */
  children: React.ReactNode;

  /**
   * Card footer content.
   */
  footer?: React.ReactNode;

  /**
   * Visual variant.
   * @default 'default'
   */
  variant?: 'default' | 'bordered' | 'elevated';

  /**
   * Padding size.
   * @default 'md'
   */
  padding?: 'sm' | 'md' | 'lg' | 'none';

  /**
   * Make card clickable.
   */
  onClick?: () => void;

  /**
   * Show hover effect.
   * @default false
   */
  hoverable?: boolean;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Card: React.FC<CardProps>;
```

### 7.2 Variants

```typescript
// Default card (shadow, white background)
<Card>
  <p>Card content</p>
</Card>
// shadow-sm, bg-white, rounded-xl

// Bordered card (no shadow, border only)
<Card variant="bordered">
  <p>Card content</p>
</Card>
// border-2 border-gray-200, bg-white, rounded-xl

// Elevated card (larger shadow)
<Card variant="elevated">
  <p>Card content</p>
</Card>
// shadow-lg, bg-white, rounded-xl
```

### 7.3 Card Sections

```typescript
// Card with all sections
<Card
  header={
    <div className="flex items-center justify-between">
      <h3 className="text-lg font-semibold">Card Title</h3>
      <Badge>New</Badge>
    </div>
  }
  footer={
    <div className="flex justify-end gap-2">
      <Button variant="outline">Cancel</Button>
      <Button>Submit</Button>
    </div>
  }
>
  <p>Card body content goes here.</p>
</Card>
```

### 7.4 Interactive Card

```typescript
// Clickable card with hover effect
<Card
  hoverable
  onClick={() => navigate('/article/123')}
  className="cursor-pointer"
>
  <ArticlePreview />
</Card>
// Hover: shadow-md, border-primary-300, transform scale-[1.01]
```

### 7.5 Accessibility

```typescript
// If clickable, wrap in <article> or <section>
// If has header, use proper heading level
// If interactive, ensure keyboard accessibility

<Card
  onClick={handleClick}
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  {children}
</Card>
```

---

## 8. Badge Component

### 8.1 Interface

```typescript
export interface BadgeProps {
  /**
   * Badge content (text or number).
   */
  children: React.ReactNode;

  /**
   * Color variant.
   * @default 'gray'
   */
  variant?: 'gray' | 'primary' | 'success' | 'warning' | 'error' | 'info';

  /**
   * Size variant.
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Visual style.
   * @default 'solid'
   */
  style?: 'solid' | 'outline' | 'subtle';

  /**
   * Icon to display before text.
   */
  icon?: React.ReactNode;

  /**
   * Make badge rounded (pill shape).
   * @default true
   */
  rounded?: boolean;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Badge: React.FC<BadgeProps>;
```

### 8.2 Color Variants

```typescript
// Gray (default) - Neutral information
<Badge variant="gray">Draft</Badge>
// bg-gray-100, text-gray-800

// Primary - Brand-related info
<Badge variant="primary">Featured</Badge>
// bg-primary-100, text-primary-800

// Success - Positive status
<Badge variant="success">Published</Badge>
// bg-success-100, text-success-800

// Warning - Attention needed
<Badge variant="warning">Pending</Badge>
// bg-warning-100, text-warning-800

// Error - Problem/failure
<Badge variant="error">Failed</Badge>
// bg-error-100, text-error-800
```

### 8.3 Style Variants

```typescript
// Solid (default)
<Badge style="solid" variant="success">Active</Badge>
// Filled background, high contrast

// Outline
<Badge style="outline" variant="success">Active</Badge>
// Transparent background, colored border

// Subtle
<Badge style="subtle" variant="success">Active</Badge>
// Light background, subtle appearance
```

### 8.4 Sizes

```typescript
// Small
<Badge size="sm">New</Badge>
// px-2 py-0.5 text-xs

// Medium (default)
<Badge size="md">New</Badge>
// px-2.5 py-1 text-sm

// Large
<Badge size="lg">New</Badge>
// px-3 py-1.5 text-base
```

### 8.5 With Icons

```typescript
<Badge icon={<CheckCircle className="w-3 h-3" />} variant="success">
  Verified
</Badge>
```

---

## 9. Modal Component

### 9.1 Interface

```typescript
export interface ModalProps {
  /**
   * Controls modal visibility.
   */
  isOpen: boolean;

  /**
   * Called when modal should close.
   */
  onClose: () => void;

  /**
   * Modal title.
   */
  title?: string;

  /**
   * Modal content.
   */
  children: React.ReactNode;

  /**
   * Footer content (typically buttons).
   */
  footer?: React.ReactNode;

  /**
   * Size variant.
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';

  /**
   * Close on backdrop click.
   * @default true
   */
  closeOnBackdropClick?: boolean;

  /**
   * Close on Escape key.
   * @default true
   */
  closeOnEscape?: boolean;

  /**
   * Show close button (X).
   * @default true
   */
  showCloseButton?: boolean;

  /**
   * Additional CSS classes for modal container.
   */
  className?: string;
}

export const Modal: React.FC<ModalProps>;
```

### 9.2 Size Specifications

```typescript
// Small modal
<Modal size="sm" isOpen={open} onClose={close}>
  {/* Content */}
</Modal>
// Max width: 24rem (384px)

// Medium (default)
<Modal size="md" isOpen={open} onClose={close}>
  {/* Content */}
</Modal>
// Max width: 32rem (512px)

// Large
<Modal size="lg" isOpen={open} onClose={close}>
  {/* Content */}
</Modal>
// Max width: 48rem (768px)

// Extra large
<Modal size="xl" isOpen={open} onClose={close}>
  {/* Content */}
</Modal>
// Max width: 64rem (1024px)

// Full screen
<Modal size="full" isOpen={open} onClose={close}>
  {/* Content */}
</Modal>
// Full viewport width/height
```

### 9.3 Complete Example

```typescript
// Confirmation modal
<Modal
  isOpen={showConfirmation}
  onClose={() => setShowConfirmation(false)}
  title="Unsaved Changes"
  footer={
    <div className="flex justify-end gap-2">
      <Button variant="outline" onClick={() => setShowConfirmation(false)}>
        Cancel
      </Button>
      <Button variant="danger" onClick={handleDiscard}>
        Discard Changes
      </Button>
    </div>
  }
>
  <p>You have unsaved changes. Are you sure you want to leave?</p>
</Modal>
```

### 9.4 Accessibility

```typescript
// ARIA: role="dialog"
// ARIA: aria-modal="true"
// ARIA: aria-labelledby="modal-title"
// Focus trap: Focus locked within modal
// Focus restoration: Return focus to trigger element on close
// Keyboard: Escape to close (if closeOnEscape: true)
// Backdrop: Click to close (if closeOnBackdropClick: true)

<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">{title}</h2>
  <div id="modal-description">{children}</div>
</div>
```

---

## 10. Drawer Component

### 10.1 Interface

```typescript
export interface DrawerProps {
  /**
   * Controls drawer visibility.
   */
  isOpen: boolean;

  /**
   * Called when drawer should close.
   */
  onClose: () => void;

  /**
   * Drawer title.
   */
  title?: string;

  /**
   * Drawer content.
   */
  children: React.ReactNode;

  /**
   * Footer content.
   */
  footer?: React.ReactNode;

  /**
   * Side from which drawer slides in.
   * @default 'right'
   */
  side?: 'left' | 'right';

  /**
   * Width of drawer.
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg' | 'xl';

  /**
   * Close on backdrop click.
   * @default true
   */
  closeOnBackdropClick?: boolean;

  /**
   * Close on Escape key.
   * @default true
   */
  closeOnEscape?: boolean;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Drawer: React.FC<DrawerProps>;
```

### 10.2 Size Specifications

```typescript
// Small drawer
size="sm"  // Width: 20rem (320px)

// Medium (default)
size="md"  // Width: 28rem (448px)

// Large
size="lg"  // Width: 36rem (576px)

// Extra large
size="xl"  // Width: 48rem (768px)
```

### 10.3 Usage Example

```typescript
// Mobile navigation drawer
<Drawer
  isOpen={isMobileMenuOpen}
  onClose={() => setIsMobileMenuOpen(false)}
  title="Navigation"
  side="left"
>
  <nav className="space-y-2">
    {routes.map((route) => (
      <NavLink key={route.path} to={route.path}>
        {route.label}
      </NavLink>
    ))}
  </nav>
</Drawer>

// Detail drawer
<Drawer
  isOpen={showDetails}
  onClose={() => setShowDetails(false)}
  title="Article Details"
  side="right"
  size="lg"
  footer={
    <div className="flex gap-2">
      <Button variant="outline" onClick={() => setShowDetails(false)}>
        Close
      </Button>
      <Button>Edit</Button>
    </div>
  }
>
  <ArticleDetails data={selectedArticle} />
</Drawer>
```

### 10.4 Animation

```typescript
// Slide-in animation (from right)
// Duration: 300ms
// Easing: ease-out
// Transform: translateX(100%) → translateX(0)

// Backdrop fade-in
// Duration: 200ms
// Opacity: 0 → 1
```

### 10.5 Accessibility

```typescript
// Same as Modal:
// - role="dialog"
// - aria-modal="true"
// - Focus trap
// - Focus restoration
// - Keyboard: Escape to close
```

---

## 11. Select Component

### 11.1 Interface

```typescript
export interface SelectOption {
  label: string;
  value: string | number;
  disabled?: boolean;
}

export interface SelectProps {
  /**
   * Label text.
   */
  label?: string;

  /**
   * Options to display in dropdown.
   */
  options: SelectOption[];

  /**
   * Currently selected value.
   */
  value?: string | number;

  /**
   * Default selected value (uncontrolled).
   */
  defaultValue?: string | number;

  /**
   * Change handler.
   */
  onChange?: (value: string | number) => void;

  /**
   * Placeholder text when no option selected.
   */
  placeholder?: string;

  /**
   * Error message.
   */
  error?: string;

  /**
   * Helper text.
   */
  helperText?: string;

  /**
   * Disabled state.
   */
  disabled?: boolean;

  /**
   * Required field.
   */
  required?: boolean;

  /**
   * Full width.
   * @default false
   */
  fullWidth?: boolean;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Select: React.FC<SelectProps>;
```

### 11.2 Usage Example

```typescript
// Basic select
<Select
  label="Model"
  options={[
    { label: 'GPT-4', value: 'gpt-4' },
    { label: 'GPT-3.5', value: 'gpt-3.5-turbo' },
    { label: 'Claude 3', value: 'claude-3-opus', disabled: true },
  ]}
  value={selectedModel}
  onChange={setSelectedModel}
/>

// With error
<Select
  label="Provider"
  options={providerOptions}
  error="Please select a provider"
  required
/>
```

### 11.3 Accessibility

```typescript
// Use native <select> for accessibility
// ARIA: aria-invalid, aria-describedby, aria-required
// Keyboard: Arrow keys, Enter, Space
// Screen reader: Announces options and current selection
```

---

## 12. Textarea Component

### 12.1 Interface

```typescript
import { TextareaHTMLAttributes, forwardRef } from 'react';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  /**
   * Label text.
   */
  label?: string;

  /**
   * Error message.
   */
  error?: string;

  /**
   * Helper text.
   */
  helperText?: string;

  /**
   * Show character counter.
   */
  showCharacterCount?: boolean;

  /**
   * Maximum character count.
   */
  maxLength?: number;

  /**
   * Number of visible rows.
   * @default 4
   */
  rows?: number;

  /**
   * Auto-resize height based on content.
   * @default false
   */
  autoResize?: boolean;

  /**
   * Full width.
   * @default false
   */
  fullWidth?: boolean;

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>((props, ref) => {
  // Implementation
});
```

### 12.2 Usage Examples

```typescript
// Basic textarea
<Textarea label="Description" rows={4} />

// With character counter
<Textarea
  label="Bio"
  maxLength={500}
  showCharacterCount
  helperText="Brief description of yourself"
/>

// Auto-resize
<Textarea
  label="Content"
  autoResize
  placeholder="Type your content..."
/>

// With validation
<Textarea
  label="Message"
  {...register('message')}
  error={errors.message?.message}
  required
/>
```

---

## 13. Spinner Component

### 13.1 Interface

```typescript
export interface SpinnerProps {
  /**
   * Size variant.
   * @default 'md'
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';

  /**
   * Color variant.
   * @default 'primary'
   */
  color?: 'primary' | 'secondary' | 'white' | 'gray';

  /**
   * Additional CSS classes.
   */
  className?: string;

  /**
   * Accessibility label.
   */
  label?: string;
}

export const Spinner: React.FC<SpinnerProps>;
```

### 13.2 Sizes

```typescript
size="xs"  // 12px
size="sm"  // 16px
size="md"  // 24px (default)
size="lg"  // 32px
size="xl"  // 48px
```

### 13.3 Usage

```typescript
// In button
<Button isLoading>
  <Spinner size="sm" color="white" />
  Saving...
</Button>

// Full page loading
<div className="flex items-center justify-center min-h-screen">
  <Spinner size="xl" label="Loading page..." />
</div>
```

---

## Component Usage Best Practices

### 1. Composition

```typescript
// Build complex UIs by composing simple components
<Card>
  <form onSubmit={handleSubmit}>
    <Input label="Name" {...register('name')} error={errors.name?.message} />
    <Textarea label="Bio" {...register('bio')} />
    <Select label="Country" options={countries} {...register('country')} />

    <div className="flex gap-2">
      <Button variant="outline" type="button" onClick={onCancel}>
        Cancel
      </Button>
      <Button type="submit" isLoading={isSubmitting}>
        Submit
      </Button>
    </div>
  </form>
</Card>
```

### 2. Type Safety

```typescript
// Always use TypeScript for prop validation
import { ButtonProps } from '@/components/ui/Button';

const MyButton: React.FC<ButtonProps> = (props) => {
  return <Button {...props} />;
};
```

### 3. Accessibility

```typescript
// Always provide accessible labels
<Button aria-label="Save settings">
  <Save className="w-4 h-4" />
</Button>

// Use semantic HTML
<Input label="Email" type="email" required />
```

### 4. Styling Extensions

```typescript
// Extend component styles with className
<Button className="w-full sm:w-auto">
  Submit
</Button>

// Use Tailwind utilities for customization
<Card className="border-2 border-primary-500">
  {/* Custom border color */}
</Card>
```

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-04
**Next Review**: After implementation feedback
**Maintained By**: Frontend Engineering Team
