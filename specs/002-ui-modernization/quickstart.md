# Quickstart Guide: UI Modernization & Design System

**Feature**: 002-ui-modernization
**Version**: 1.0.0
**Last Updated**: 2025-11-04
**Audience**: Frontend Developers

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Development Environment](#2-development-environment)
3. [Using Design System Components](#3-using-design-system-components)
4. [Adding New Components](#4-adding-new-components)
5. [Responsive Layouts](#5-responsive-layouts)
6. [Form Handling & Validation](#6-form-handling--validation)
7. [Testing](#7-testing)
8. [Performance Optimization](#8-performance-optimization)
9. [Common Patterns](#9-common-patterns)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Getting Started

### 1.1 Prerequisites

- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0
- **Code Editor**: VS Code recommended (with Tailwind CSS IntelliSense extension)

### 1.2 Clone & Install

```bash
# Navigate to frontend directory
cd /Users/albertking/ES/cms_automation/frontend

# Install dependencies
npm install

# Verify installation
npm run type-check
```

### 1.3 Project Structure Overview

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                 # Design system components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Accordion.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── ...
│   │   ├── layout/             # Layout components
│   │   │   └── Navigation.tsx
│   │   └── [feature]/          # Feature-specific components
│   ├── pages/                  # Page components
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utilities
│   ├── schemas/                # Zod validation schemas
│   ├── routes.tsx              # Route configuration
│   └── App.tsx                 # Root component
├── tailwind.config.js          # Design tokens
├── vite.config.ts              # Build configuration
├── package.json
└── tsconfig.json
```

---

## 2. Development Environment

### 2.1 Start Development Server

```bash
# Start Vite dev server
npm run dev

# Server will start at http://localhost:5173
# Hot module replacement (HMR) enabled
```

**Features**:
- Fast hot module replacement (instant updates)
- TypeScript type checking in IDE
- Tailwind CSS live updates
- React Query DevTools (bottom-right corner)

### 2.2 VS Code Setup

**Recommended Extensions**:
```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",      // Tailwind CSS IntelliSense
    "dbaeumer.vscode-eslint",         // ESLint
    "esbenp.prettier-vscode",         // Prettier
    "ms-playwright.playwright",       // Playwright Test
    "ZixuanChen.vitest-explorer"      // Vitest Test Explorer
  ]
}
```

**Settings** (`.vscode/settings.json`):
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "tailwindCSS.experimental.classRegex": [
    ["clsx\\(([^)]*)\\)", "(?:'|\"|`)([^'\"`]*)(?:'|\"|`)"]
  ]
}
```

### 2.3 Code Quality Tools

```bash
# Run linter
npm run lint

# Fix linting issues automatically
npm run lint:fix

# Format code
npm run format

# Check formatting (CI)
npm run format:check

# Type check
npm run type-check
```

---

## 3. Using Design System Components

### 3.1 Button Component

```typescript
import { Button } from '@/components/ui/Button';

// Primary button (default)
<Button onClick={handleSubmit}>Save Settings</Button>

// Secondary button
<Button variant="secondary">Learn More</Button>

// Outline button
<Button variant="outline">Cancel</Button>

// Danger button (destructive action)
<Button variant="danger">Delete Account</Button>

// Loading state
<Button isLoading onClick={handleSave}>
  Save
</Button>

// With icons
import { Save } from 'lucide-react';

<Button iconLeft={<Save className="w-4 h-4" />}>
  Save
</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>  {/* default */}
<Button size="lg">Large</Button>

// Full width
<Button fullWidth>Submit</Button>
```

---

### 3.2 Input Component

```typescript
import { Input } from '@/components/ui/Input';

// Basic input
<Input
  label="Username"
  placeholder="Enter your username"
/>

// With validation error
<Input
  label="Email"
  type="email"
  error="Invalid email address"
/>

// With helper text
<Input
  label="API Key"
  helperText="Found in your provider dashboard"
/>

// Required field
<Input
  label="Password"
  type="password"
  required
/>

// With React Hook Form
import { useForm } from 'react-hook-form';

const { register, formState: { errors } } = useForm();

<Input
  label="Email"
  {...register('email')}
  error={errors.email?.message}
/>
```

---

### 3.3 Toast Notifications

```typescript
import { toast } from 'sonner';

// Success notification
toast.success('Settings saved successfully');

// Error notification
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

// Custom duration
toast.info('New update available', {
  duration: 10000, // 10 seconds
});

// Manual dismissal
const toastId = toast.loading('Processing...');
// Later...
toast.dismiss(toastId);
```

**Setup** (in `App.tsx`):
```typescript
import { Toaster } from 'sonner';

function App() {
  return (
    <>
      <YourApp />
      <Toaster position="top-right" />
    </>
  );
}
```

---

### 3.4 Accordion Component

```typescript
import { Accordion, AccordionItem } from '@/components/ui/Accordion';
import { Settings, Database, Key } from 'lucide-react';

<Accordion spacing="md">
  <AccordionItem
    title="Provider Configuration"
    subtitle="API keys and model settings"
    icon={<Settings className="w-5 h-5" />}
    defaultOpen
  >
    {/* Settings form fields */}
    <ProviderConfigForm />
  </AccordionItem>

  <AccordionItem
    title="Database Settings"
    subtitle="Connection and credentials"
    icon={<Database className="w-5 h-5" />}
  >
    <DatabaseConfigForm />
  </AccordionItem>

  <AccordionItem
    title="API Keys"
    subtitle="External service credentials"
    icon={<Key className="w-5 h-5" />}
  >
    <APIKeysForm />
  </AccordionItem>
</Accordion>
```

---

### 3.5 Card Component

```typescript
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

// Basic card
<Card>
  <p>Card content</p>
</Card>

// Card with header and footer
<Card
  header={
    <div className="flex items-center justify-between">
      <h3 className="text-lg font-semibold">Article Title</h3>
      <Badge variant="success">Published</Badge>
    </div>
  }
  footer={
    <div className="flex justify-end gap-2">
      <Button variant="outline">Cancel</Button>
      <Button>Submit</Button>
    </div>
  }
>
  <p>Article content goes here...</p>
</Card>

// Clickable card with hover effect
<Card
  hoverable
  onClick={() => navigate('/article/123')}
  className="cursor-pointer"
>
  <ArticlePreview />
</Card>

// Variants
<Card variant="default">Standard shadow</Card>
<Card variant="bordered">Border only, no shadow</Card>
<Card variant="elevated">Larger shadow</Card>
```

---

### 3.6 Modal & Drawer

```typescript
import { Modal } from '@/components/ui/Modal';
import { Drawer } from '@/components/ui/Drawer';

// Confirmation modal
const [showConfirmation, setShowConfirmation] = useState(false);

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

// Drawer for navigation or details
const [showDrawer, setShowDrawer] = useState(false);

<Drawer
  isOpen={showDrawer}
  onClose={() => setShowDrawer(false)}
  title="Article Details"
  side="right"
  size="lg"
>
  <ArticleDetails data={selectedArticle} />
</Drawer>
```

---

### 3.7 Skeleton Loading

```typescript
import { Skeleton, SkeletonCard, SkeletonSettingsSection } from '@/components/ui/Skeleton';

// Basic skeleton
<Skeleton variant="text" className="w-48 h-4" />
<Skeleton variant="rectangle" className="w-full h-32" />
<Skeleton variant="circle" className="w-10 h-10" />

// Pre-built skeletons
if (isLoading) {
  return (
    <div className="space-y-6">
      <SkeletonSettingsSection />
      <SkeletonSettingsSection />
      <SkeletonSettingsSection />
    </div>
  );
}

// Custom skeleton composition
<div className="space-y-4">
  <Skeleton variant="text" className="w-1/3 h-6" />
  <Skeleton variant="text" className="w-2/3 h-4" />
  <Skeleton variant="rectangle" className="h-48 w-full" />
</div>
```

---

### 3.8 Badge Component

```typescript
import { Badge } from '@/components/ui/Badge';
import { CheckCircle } from 'lucide-react';

// Status badges
<Badge variant="success">Published</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="gray">Draft</Badge>

// With icon
<Badge icon={<CheckCircle className="w-3 h-3" />} variant="success">
  Verified
</Badge>

// Sizes
<Badge size="sm">Small</Badge>
<Badge size="md">Medium</Badge>
<Badge size="lg">Large</Badge>

// Styles
<Badge style="solid" variant="success">Solid</Badge>
<Badge style="outline" variant="success">Outline</Badge>
<Badge style="subtle" variant="success">Subtle</Badge>
```

---

## 4. Adding New Components

### 4.1 Component Template

```typescript
/**
 * [ComponentName] - Brief description.
 */

import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

export interface [ComponentName]Props extends HTMLAttributes<HTMLDivElement> {
  /**
   * Description of prop.
   * @default 'defaultValue'
   */
  variant?: 'option1' | 'option2';

  /**
   * Additional CSS classes.
   */
  className?: string;
}

export const [ComponentName] = forwardRef<HTMLDivElement, [ComponentName]Props>(
  ({ variant = 'option1', className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'base-styles',
          variant === 'option1' && 'option1-styles',
          variant === 'option2' && 'option2-styles',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

[ComponentName].displayName = '[ComponentName]';
```

### 4.2 File Organization

```
src/components/ui/
├── YourComponent.tsx       # Component implementation
└── index.ts                # Barrel export (optional)
```

**Barrel export** (`index.ts`):
```typescript
export { Button, type ButtonProps } from './Button';
export { Input, type InputProps } from './Input';
export { YourComponent, type YourComponentProps } from './YourComponent';
```

### 4.3 Component Checklist

- [ ] TypeScript interface with JSDoc comments
- [ ] `forwardRef` for DOM access
- [ ] `className` prop for style extension
- [ ] Accessible (ARIA attributes, keyboard support)
- [ ] Responsive (works on mobile, tablet, desktop)
- [ ] Documented with usage examples
- [ ] Follows design token system (colors, spacing, etc.)

---

## 5. Responsive Layouts

### 5.1 Breakpoint Usage

```typescript
// Mobile-first approach (base styles apply to all sizes)

// Text sizes
<h1 className="text-2xl md:text-3xl lg:text-4xl">Responsive Heading</h1>

// Grid layouts
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Grid items */}
</div>

// Flex direction
<div className="flex flex-col md:flex-row gap-4">
  {/* Flex items */}
</div>

// Show/hide elements
<div className="hidden lg:block">Desktop only</div>
<div className="block lg:hidden">Mobile/tablet only</div>

// Spacing
<div className="p-4 md:p-6 lg:p-8">
  {/* Responsive padding */}
</div>

// Width constraints
<div className="w-full lg:w-1/2 xl:w-1/3">
  {/* Responsive width */}
</div>
```

### 5.2 Responsive Navigation Pattern

```typescript
import { useState } from 'react';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { Menu } from 'lucide-react';
import { Drawer } from '@/components/ui/Drawer';

function Navigation() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const isMobile = useMediaQuery('(max-width: 767px)');

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="text-xl font-bold">
            CMS Automation
          </Link>

          {/* Desktop navigation */}
          {!isMobile && (
            <div className="flex items-center space-x-1">
              {navRoutes.map((route) => (
                <NavLink key={route.path} to={route.path}>
                  {route.label}
                </NavLink>
              ))}
            </div>
          )}

          {/* Mobile menu button */}
          {isMobile && (
            <button onClick={() => setIsMobileMenuOpen(true)}>
              <Menu className="w-6 h-6" />
            </button>
          )}
        </div>
      </div>

      {/* Mobile drawer */}
      <Drawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        side="left"
      >
        <nav className="space-y-2">
          {navRoutes.map((route) => (
            <MobileNavLink
              key={route.path}
              to={route.path}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              {route.label}
            </MobileNavLink>
          ))}
        </nav>
      </Drawer>
    </nav>
  );
}
```

### 5.3 Container Patterns

```typescript
// Standard container (max-width with horizontal padding)
<div className="container mx-auto px-4 sm:px-6 lg:px-8">
  {/* Content */}
</div>

// Full-width section with background
<section className="bg-gray-50 py-12">
  <div className="container mx-auto px-4">
    {/* Content */}
  </div>
</section>

// Narrow content (for readability)
<div className="max-w-2xl mx-auto px-4">
  <article>{/* Article content */}</article>
</div>

// Wide content area
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  {/* Dashboard layout */}
</div>
```

---

## 6. Form Handling & Validation

### 6.1 Basic Form Setup

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { toast } from 'sonner';

// Define validation schema
const formSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type FormData = z.infer<typeof formSchema>;

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await loginUser(data);
      toast.success('Login successful');
    } catch (error) {
      toast.error('Login failed', {
        description: error.message,
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Email"
        type="email"
        {...register('email')}
        error={errors.email?.message}
      />

      <Input
        label="Password"
        type="password"
        {...register('password')}
        error={errors.password?.message}
      />

      <Button type="submit" fullWidth isLoading={isSubmitting}>
        Login
      </Button>
    </form>
  );
}
```

### 6.2 Complex Form with React Query

```typescript
import { useMutation, useQuery } from '@tanstack/react-query';
import { settingsSchema } from '@/schemas/settings';
import { toast } from 'sonner';

function SettingsForm() {
  // Fetch existing settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  });

  // Form setup
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm({
    resolver: zodResolver(settingsSchema),
    defaultValues: settings,
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      toast.success('Settings saved successfully');
      reset(); // Reset form state
    },
    onError: (error) => {
      toast.error('Save failed', {
        description: error.message,
        action: {
          label: 'Retry',
          onClick: () => updateMutation.mutate(),
        },
      });
    },
  });

  const onSubmit = (data) => {
    updateMutation.mutate(data);
  };

  if (isLoading) {
    return <SkeletonSettingsSection />;
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Form fields */}

      {/* Unsaved changes warning */}
      {isDirty && (
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <p className="text-sm text-warning-800">
            You have unsaved changes.
          </p>
        </div>
      )}

      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={() => reset()}
          disabled={!isDirty}
        >
          Reset
        </Button>
        <Button
          type="submit"
          isLoading={updateMutation.isLoading}
          disabled={!isDirty}
        >
          Save Changes
        </Button>
      </div>
    </form>
  );
}
```

### 6.3 Unsaved Changes Detection

```typescript
// Custom hook for unsaved changes warning
import { useEffect } from 'react';

export function useUnsavedChanges(isDirty: boolean) {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = ''; // Required for Chrome
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);
}

// Usage
function SettingsPage() {
  const { formState: { isDirty } } = useForm();

  useUnsavedChanges(isDirty);

  // ...
}
```

---

## 7. Testing

### 7.1 Unit Testing (Vitest)

```bash
# Run all unit tests
npm test

# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

**Example Test** (`Button.test.tsx`):
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('shows loading state', () => {
    render(<Button isLoading>Save</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### 7.2 E2E Testing (Playwright)

```bash
# Run E2E tests
npm run test:e2e

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run with UI (debugging)
npm run test:e2e:ui
```

**Example E2E Test** (`settings.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('displays settings form', async ({ page }) => {
    await expect(page.getByLabel('API Key')).toBeVisible();
    await expect(page.getByLabel('Model')).toBeVisible();
  });

  test('shows validation errors', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: 'Save' });

    // Clear required field
    await page.getByLabel('API Key').clear();

    // Try to submit
    await submitButton.click();

    // Check for error
    await expect(page.getByText('請輸入API密鑰')).toBeVisible();
  });

  test('saves settings successfully', async ({ page }) => {
    // Fill form
    await page.getByLabel('API Key').fill('test-key-123');
    await page.getByLabel('Model').selectOption('gpt-4');

    // Submit
    await page.getByRole('button', { name: 'Save' }).click();

    // Check success toast
    await expect(page.getByText('Settings saved successfully')).toBeVisible();
  });
});
```

### 7.3 Visual Regression Testing

```bash
# Update Playwright screenshots
npm run test:e2e -- --update-snapshots
```

**Example**:
```typescript
test('matches visual snapshot', async ({ page }) => {
  await page.goto('/settings');
  await expect(page).toHaveScreenshot('settings-page.png');
});
```

---

## 8. Performance Optimization

### 8.1 Bundle Analysis

```bash
# Build with bundle analysis
npm run build

# Check bundle size
ls -lh dist/assets/js/

# Analyze with visualizer (if configured)
npm run build:analyze
```

### 8.2 Code Splitting Patterns

```typescript
// Route-based code splitting (already configured)
import { lazy } from 'react';

const SettingsPage = lazy(() => import('./pages/SettingsPage'));

// Component-based code splitting
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function DashboardPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <HeavyChart data={data} />
    </Suspense>
  );
}

// Dynamic imports for heavy libraries
const loadEditor = async () => {
  const { TipTapEditor } = await import('./components/TipTapEditor');
  return TipTapEditor;
};
```

### 8.3 Image Optimization

```typescript
import { LazyImage } from '@/components/ui/LazyImage';

// Lazy load images
<LazyImage
  src="/images/article-cover.jpg"
  alt="Article cover"
  className="w-full h-64 object-cover"
/>

// Or use native lazy loading
<img
  src="/images/article.jpg"
  alt="Article"
  loading="lazy"
  className="w-full"
/>
```

### 8.4 Performance Monitoring

```typescript
// Web Vitals tracking (add to App.tsx)
import { getCLS, getFID, getLCP } from 'web-vitals';

function reportWebVitals() {
  getCLS(metric => console.log('CLS:', metric.value));
  getFID(metric => console.log('FID:', metric.value));
  getLCP(metric => console.log('LCP:', metric.value));
}

reportWebVitals();
```

---

## 9. Common Patterns

### 9.1 Data Fetching with Loading States

```typescript
import { useQuery } from '@tanstack/react-query';
import { SkeletonCard } from '@/components/ui/Skeleton';

function ArticleList() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['articles'],
    queryFn: fetchArticles,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-error-50 border border-error-200 rounded-lg p-4">
        <p className="text-error-800">Error: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data.map(article => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
```

### 9.2 Error Boundaries

```typescript
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ErrorFallback } from '@/components/ErrorFallback';

function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Routes>
        {/* Your routes */}
      </Routes>
    </ErrorBoundary>
  );
}
```

### 9.3 Debounced Search

```typescript
import { useState, useEffect } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { Input } from '@/components/ui/Input';

function SearchBar() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 500); // 500ms delay

  useEffect(() => {
    if (debouncedSearch) {
      // Perform search
      searchArticles(debouncedSearch);
    }
  }, [debouncedSearch]);

  return (
    <Input
      type="search"
      placeholder="Search articles..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      iconLeft={<Search className="w-4 h-4" />}
    />
  );
}
```

### 9.4 Infinite Scroll

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

function InfiniteArticleList() {
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['articles'],
    queryFn: ({ pageParam = 1 }) => fetchArticles(pageParam),
    getNextPageParam: (lastPage) => lastPage.nextPage,
  });

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  return (
    <div className="space-y-4">
      {data?.pages.map((page) =>
        page.articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))
      )}

      {/* Loading trigger */}
      <div ref={ref}>
        {isFetchingNextPage && <Spinner />}
      </div>
    </div>
  );
}
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### TypeScript Errors

```bash
# Clear TypeScript cache
rm -rf node_modules/.cache

# Rebuild
npm run type-check
```

#### Tailwind Classes Not Working

```bash
# Ensure PostCSS is processing correctly
# Check tailwind.config.js content paths

# Restart dev server
npm run dev
```

#### React Query DevTools Not Appearing

```typescript
// Ensure it's imported in App.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

<ReactQueryDevtools initialIsOpen={false} />
```

#### Vite Build Errors

```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Clean build
rm -rf dist
npm run build
```

### 10.2 Debug Mode

```typescript
// Enable React Query debug mode
import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      // Enable debug mode
      meta: {
        debug: true,
      },
    },
  },
});
```

### 10.3 Performance Profiling

```bash
# Build for production
npm run build

# Serve production build locally
npm run preview

# Open Chrome DevTools > Performance tab
# Record and analyze
```

### 10.4 Accessibility Debugging

```typescript
// Install axe-core for automated testing
npm install --save-dev @axe-core/react

// Add to main.tsx (development only)
if (process.env.NODE_ENV !== 'production') {
  import('@axe-core/react').then((axe) => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

---

## Quick Reference

### Component Imports

```typescript
// UI Components
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { Accordion, AccordionItem } from '@/components/ui/Accordion';
import { Skeleton } from '@/components/ui/Skeleton';

// Toast
import { toast } from 'sonner';

// Forms
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Data fetching
import { useQuery, useMutation } from '@tanstack/react-query';

// Icons
import { Save, Edit, Trash, Menu } from 'lucide-react';
```

### Tailwind Utilities Cheat Sheet

```typescript
// Colors
'bg-primary-600 text-white'
'text-gray-700'
'border-gray-300'

// Spacing
'p-4'    // Padding: 16px
'gap-4'  // Gap: 16px
'space-y-4'  // Vertical spacing: 16px

// Layout
'flex items-center justify-between'
'grid grid-cols-3 gap-4'

// Typography
'text-base font-normal'
'text-lg font-semibold'

// Shadows & Borders
'shadow-md'
'rounded-lg'
'border border-gray-200'

// Transitions
'transition-colors duration-200'
'hover:bg-primary-700'
```

---

## Additional Resources

- **Design Tokens**: `/specs/002-ui-modernization/contracts/design-tokens.md`
- **Component Contracts**: `/specs/002-ui-modernization/contracts/components.md`
- **Data Models**: `/specs/002-ui-modernization/data-model.md`
- **Tailwind Docs**: https://tailwindcss.com/docs
- **React Hook Form**: https://react-hook-form.com
- **Zod**: https://zod.dev
- **React Query**: https://tanstack.com/query/latest
- **Lucide Icons**: https://lucide.dev

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-04
**Maintained By**: Frontend Engineering Team

For questions or issues, consult the team or create an issue in the project repository.
