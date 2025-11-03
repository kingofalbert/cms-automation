# Performance Optimization Guide

This document outlines the performance optimizations implemented in the CMS Automation frontend.

## Table of Contents

1. [Virtual Scrolling](#virtual-scrolling)
2. [Lazy Loading](#lazy-loading)
3. [Code Splitting](#code-splitting)
4. [Memoization](#memoization)
5. [Bundle Optimization](#bundle-optimization)
6. [Best Practices](#best-practices)

## Virtual Scrolling

### Implementation

We use `@tanstack/react-virtual` for efficient rendering of large lists.

```tsx
import { VirtualList } from '@/components/ui/VirtualList';

<VirtualList
  items={articles}
  renderItem={(article, index) => <ArticleCard article={article} />}
  estimateSize={280}
  height="600px"
  overscan={3}
/>
```

### Benefits

- **Reduced DOM nodes**: Only renders items in viewport + overscan
- **Improved performance**: Handles 10,000+ items smoothly
- **Lower memory usage**: Significant reduction in memory footprint

### When to Use

- Lists with 50+ items
- Lists with complex item components
- Infinite scroll implementations

## Lazy Loading

### Image Lazy Loading

The `LazyImage` component uses Intersection Observer for optimal image loading.

```tsx
import { LazyImage } from '@/components/ui/LazyImage';

<LazyImage
  src="/path/to/image.jpg"
  alt="Description"
  placeholder="/placeholder.jpg"
  rootMargin="50px"
/>
```

### Features

- Intersection Observer API
- Placeholder support
- Error fallback
- Loading states
- Custom root margin and threshold

## Code Splitting

### Route-Based Splitting

All routes use lazy loading with `React.lazy()`:

```tsx
import { lazy } from 'react';

const HomePage = lazy(() => import('./pages/HomePage'));
```

### Route Preloading

Prefetch routes before navigation for faster transitions:

```tsx
import { preloadRoute } from './config/routes';

// Preload on hover
onMouseEnter={() => preloadRoute('/articles')}
```

### Component-Based Splitting

Heavy components are lazily loaded:

```tsx
import { lazy, Suspense } from 'react';

const HeavyChart = lazy(() => import('./HeavyChart'));

<Suspense fallback={<Spinner />}>
  <HeavyChart data={data} />
</Suspense>
```

## Memoization

### React.memo

Prevent unnecessary re-renders:

```tsx
export const ArticleCard = React.memo(
  ArticleCardComponent,
  (prevProps, nextProps) => {
    return (
      prevProps.article.id === nextProps.article.id &&
      prevProps.article.updated_at === nextProps.article.updated_at
    );
  }
);
```

### useMemo Hook

Memoize expensive computations:

```tsx
import { useMemo } from 'react';

const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);
```

### useCallback Hook

Memoize callback functions:

```tsx
import { useCallback } from 'react';

const handleClick = useCallback(() => {
  console.log('Clicked');
}, []);
```

### Custom Hooks

#### useDebounce

Debounce values for search inputs:

```tsx
import { useDebounce } from '@/hooks/useDebounce';

const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounce(searchTerm, 500);

useEffect(() => {
  // API call with debounced value
  fetchResults(debouncedSearch);
}, [debouncedSearch]);
```

#### useThrottle

Throttle callbacks for scroll/resize events:

```tsx
import { useThrottle } from '@/hooks/useThrottle';

const handleScroll = useThrottle((event) => {
  console.log('Scrolled');
}, 300);

<div onScroll={handleScroll}>...</div>
```

#### useMemoCompare

Deep equality memoization:

```tsx
import { useMemoCompare, deepEqual } from '@/hooks/useMemoCompare';

const memoizedObject = useMemoCompare(
  complexObject,
  (prev, next) => deepEqual(prev, next)
);
```

## Bundle Optimization

### Vite Configuration

Our `vite.config.ts` includes:

1. **Manual chunk splitting**: Group related dependencies
2. **Terser minification**: Remove console.log in production
3. **Asset organization**: Separate images, fonts, and CSS
4. **Size limits**: Warning at 1000kb chunks

### Manual Chunks

```js
manualChunks: {
  'react-core': ['react', 'react-dom', 'react-router-dom'],
  'react-query': ['@tanstack/react-query'],
  'form-libs': ['react-hook-form', '@hookform/resolvers', 'zod'],
  'editor': ['@tiptap/react', '@tiptap/starter-kit'],
  'utils': ['axios', 'date-fns', 'clsx'],
  'charts': ['recharts'],
  'virtual': ['@tanstack/react-virtual'],
}
```

### Tree Shaking

Ensure proper tree shaking by:

1. Using named imports: `import { Button } from './Button'`
2. Avoiding default exports for utils
3. Using ES modules instead of CommonJS

### Bundle Analysis

Analyze bundle size with:

```bash
npm run build
npx vite-bundle-visualizer
```

## Best Practices

### 1. Component Optimization

```tsx
// ✅ Good: Memoized with proper comparison
export const UserCard = React.memo(
  UserCardComponent,
  (prev, next) => prev.user.id === next.user.id
);

// ❌ Bad: No memoization
export const UserCard = UserCardComponent;
```

### 2. Event Handlers

```tsx
// ✅ Good: useCallback for stable reference
const handleClick = useCallback(() => {
  doSomething();
}, []);

// ❌ Bad: New function on every render
const handleClick = () => {
  doSomething();
};
```

### 3. Large Lists

```tsx
// ✅ Good: Virtual scrolling
<VirtualList items={1000items} renderItem={render} />

// ❌ Bad: Render all items
{items.map(item => <Item key={item.id} />)}
```

### 4. Images

```tsx
// ✅ Good: Lazy loading with placeholder
<LazyImage src={src} placeholder={placeholder} />

// ❌ Bad: Load all images immediately
<img src={src} />
```

### 5. API Calls

```tsx
// ✅ Good: Debounced search
const debouncedQuery = useDebounce(query, 500);
useEffect(() => {
  fetchResults(debouncedQuery);
}, [debouncedQuery]);

// ❌ Bad: API call on every keystroke
useEffect(() => {
  fetchResults(query);
}, [query]);
```

### 6. Heavy Computations

```tsx
// ✅ Good: Memoized computation
const sortedItems = useMemo(
  () => items.sort((a, b) => a.value - b.value),
  [items]
);

// ❌ Bad: Computed on every render
const sortedItems = items.sort((a, b) => a.value - b.value);
```

### 7. Conditional Rendering

```tsx
// ✅ Good: Lazy load heavy components
{showChart && (
  <Suspense fallback={<Spinner />}>
    <HeavyChart />
  </Suspense>
)}

// ❌ Bad: Always load heavy component
{showChart && <HeavyChart />}
```

## Performance Metrics

### Target Metrics

- **First Contentful Paint (FCP)**: < 1.8s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.8s
- **Total Blocking Time (TBT)**: < 200ms
- **Cumulative Layout Shift (CLS)**: < 0.1

### Measuring Performance

Use React DevTools Profiler:

```tsx
import { Profiler } from 'react';

<Profiler id="MyComponent" onRender={onRenderCallback}>
  <MyComponent />
</Profiler>
```

Use Web Vitals:

```bash
npm install web-vitals
```

```tsx
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

## Monitoring

### Performance Budget

Set performance budgets in your CI/CD:

```json
{
  "budgets": [
    {
      "type": "bundle",
      "threshold": "500kb",
      "warning": "400kb"
    }
  ]
}
```

### Lighthouse CI

Add Lighthouse CI to your pipeline:

```bash
npm install -D @lhci/cli
```

```json
{
  "ci": {
    "collect": {
      "staticDistDir": "./dist"
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "first-contentful-paint": ["error", { "maxNumericValue": 2000 }]
      }
    }
  }
}
```

## Common Issues

### 1. Large Bundle Size

**Problem**: Bundle > 1MB
**Solution**:
- Enable code splitting
- Use dynamic imports
- Remove unused dependencies
- Use lighter alternatives

### 2. Slow List Rendering

**Problem**: List with 1000+ items is slow
**Solution**:
- Implement virtual scrolling
- Use React.memo for list items
- Optimize item components

### 3. Memory Leaks

**Problem**: Memory usage increases over time
**Solution**:
- Clean up event listeners
- Cancel pending requests on unmount
- Use proper dependency arrays

### 4. Unnecessary Re-renders

**Problem**: Components re-render too often
**Solution**:
- Use React.memo
- Use useMemo and useCallback
- Optimize context usage

## Resources

- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Vite Performance](https://vitejs.dev/guide/performance.html)
- [Web Vitals](https://web.dev/vitals/)
- [@tanstack/react-virtual Docs](https://tanstack.com/virtual/latest)
- [React DevTools Profiler](https://react.dev/learn/react-developer-tools)

## Performance Checklist

- [ ] Virtual scrolling for long lists (50+ items)
- [ ] Lazy loading for images
- [ ] Code splitting for routes
- [ ] React.memo for expensive components
- [ ] useMemo for expensive computations
- [ ] useCallback for event handlers
- [ ] Debounce for search inputs
- [ ] Throttle for scroll/resize handlers
- [ ] Manual chunk splitting configured
- [ ] Bundle size analyzed
- [ ] Performance metrics monitored
- [ ] Lighthouse score > 90
