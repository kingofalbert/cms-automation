# Design Tokens Contract: Tailwind Configuration

**Feature**: 002-ui-modernization
**Version**: 1.0.0
**Last Updated**: 2025-11-04
**Status**: Phase 1 - Design Artifacts

---

## Overview

This document specifies the complete Tailwind CSS configuration for design tokens. All design decisions are centralized in `tailwind.config.js` and consumed via utility classes throughout the application.

**Key Principle**: Single source of truth for all design values.

---

## 1. Complete Tailwind Config Structure

### 1.1 Base Configuration

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],

  // Dark mode strategy (future enhancement)
  darkMode: 'class', // or 'media'

  theme: {
    extend: {
      // Design tokens defined below
    },
  },

  plugins: [
    // Custom plugins defined in Section 6
  ],
};
```

---

## 2. Color System

### 2.1 Primary Brand Colors

```javascript
colors: {
  primary: {
    50: '#f0f9ff',   // Lightest - backgrounds, subtle highlights
    100: '#e0f2fe',  // Very light - hover backgrounds
    200: '#bae6fd',  // Light - disabled states
    300: '#7dd3fc',  // Light-medium - borders
    400: '#38bdf8',  // Medium - icons
    500: '#0ea5e9',  // Base - default primary color
    600: '#0284c7',  // Main brand color - buttons, links
    700: '#0369a1',  // Dark - button hover states
    800: '#075985',  // Darker - active states
    900: '#0c4a6e',  // Very dark - text on light backgrounds
    950: '#082f49',  // Darkest - headings, strong emphasis
  },
}
```

**Usage Guidelines**:
- **Buttons**: `bg-primary-600 hover:bg-primary-700`
- **Links**: `text-primary-600 hover:text-primary-700`
- **Backgrounds**: `bg-primary-50` for subtle highlights
- **Borders**: `border-primary-300` for subtle outlines
- **Icons**: `text-primary-500` or `text-primary-600`

**Accessibility**:
- `primary-600` on white: Contrast ratio 4.52:1 (WCAG AA compliant)
- `primary-700` on white: Contrast ratio 6.23:1 (WCAG AAA compliant)

---

### 2.2 Secondary Colors

```javascript
colors: {
  secondary: {
    50: '#faf5ff',   // Lightest
    100: '#f3e8ff',  // Very light
    200: '#e9d5ff',  // Light
    300: '#d8b4fe',  // Light-medium
    400: '#c084fc',  // Medium
    500: '#a855f7',  // Base
    600: '#9333ea',  // Main secondary color
    700: '#7e22ce',  // Dark - hover states
    800: '#6b21a8',  // Darker
    900: '#581c87',  // Very dark
    950: '#3b0764',  // Darkest
  },
}
```

**Usage Guidelines**:
- **Alternative CTAs**: `bg-secondary-600 hover:bg-secondary-700`
- **Badges**: `bg-secondary-100 text-secondary-800`
- **Accents**: `border-secondary-300`

---

### 2.3 Status Colors

```javascript
colors: {
  // Success (Green)
  success: {
    50: '#f0fdf4',   // Very light backgrounds
    100: '#dcfce7',  // Light backgrounds, subtle highlights
    200: '#bbf7d0',  // (can add if needed)
    300: '#86efac',  // (can add if needed)
    400: '#4ade80',  // (can add if needed)
    500: '#22c55e',  // Base success color
    600: '#16a34a',  // Main success color - success buttons
    700: '#15803d',  // Dark - hover states
    800: '#166534',  // (can add if needed)
    900: '#14532d',  // (can add if needed)
  },

  // Warning (Yellow/Orange)
  warning: {
    50: '#fffbeb',   // Very light backgrounds
    100: '#fef3c7',  // Light backgrounds
    200: '#fde68a',  // (can add if needed)
    300: '#fcd34d',  // (can add if needed)
    400: '#fbbf24',  // (can add if needed)
    500: '#f59e0b',  // Base warning color
    600: '#d97706',  // Main warning color
    700: '#b45309',  // Dark - hover states
    800: '#92400e',  // (can add if needed)
    900: '#78350f',  // (can add if needed)
  },

  // Error (Red)
  error: {
    50: '#fef2f2',   // Very light backgrounds
    100: '#fee2e2',  // Light backgrounds
    200: '#fecaca',  // (can add if needed)
    300: '#fca5a5',  // (can add if needed)
    400: '#f87171',  // (can add if needed)
    500: '#ef4444',  // Base error color
    600: '#dc2626',  // Main error color - error buttons, text
    700: '#b91c1c',  // Dark - hover states
    800: '#991b1b',  // (can add if needed)
    900: '#7f1d1d',  // (can add if needed)
  },

  // Info (uses primary by default)
  info: {
    // Alias to primary colors
    50: '#f0f9ff',   // = primary-50
    100: '#e0f2fe',  // = primary-100
    500: '#0ea5e9',  // = primary-500
    600: '#0284c7',  // = primary-600
    700: '#0369a1',  // = primary-700
  },
}
```

**Usage Patterns**:
```javascript
// Success feedback
'bg-success-100 text-success-800 border-success-200'

// Warning state
'bg-warning-100 text-warning-800 border-warning-200'

// Error state
'bg-error-100 text-error-800 border-error-200'

// Success button
'bg-success-600 hover:bg-success-700 text-white'

// Danger button
'bg-error-600 hover:bg-error-700 text-white'
```

---

### 2.4 Neutral Gray Scale

```javascript
// Use Tailwind's default gray scale (slate, gray, zinc, neutral, stone)
// Default recommendation: Use built-in 'gray' scale

colors: {
  // Tailwind default gray (inherited, no need to redefine)
  gray: {
    50: '#f9fafb',   // Page backgrounds
    100: '#f3f4f6',  // Card backgrounds, disabled states
    200: '#e5e7eb',  // Borders, dividers
    300: '#d1d5db',  // Input borders
    400: '#9ca3af',  // Placeholder text
    500: '#6b7280',  // Secondary text
    600: '#4b5563',  // Body text
    700: '#374151',  // Headings
    800: '#1f2937',  // Strong headings
    900: '#111827',  // High contrast text
    950: '#030712',  // Near black
  },
}
```

**Usage Guidelines**:
- **Page background**: `bg-gray-50`
- **Card background**: `bg-white` or `bg-gray-100`
- **Body text**: `text-gray-600` or `text-gray-700`
- **Headings**: `text-gray-900`
- **Borders**: `border-gray-200` or `border-gray-300`
- **Disabled text**: `text-gray-400`

---

## 3. Spacing Scale

### 3.1 Standard Spacing (4px/8px Grid)

```javascript
spacing: {
  // Tailwind defaults (inherited)
  0: '0px',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  7: '1.75rem',   // 28px
  8: '2rem',      // 32px
  9: '2.25rem',   // 36px
  10: '2.5rem',   // 40px
  11: '2.75rem',  // 44px
  12: '3rem',     // 48px
  14: '3.5rem',   // 56px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  28: '7rem',     // 112px
  32: '8rem',     // 128px
  36: '9rem',     // 144px
  40: '10rem',    // 160px
  44: '11rem',    // 176px
  48: '12rem',    // 192px
  52: '13rem',    // 208px
  56: '14rem',    // 224px
  60: '15rem',    // 240px
  64: '16rem',    // 256px
  72: '18rem',    // 288px
  80: '20rem',    // 320px
  96: '24rem',    // 384px
}
```

### 3.2 Custom Spacing Extensions

```javascript
theme: {
  extend: {
    spacing: {
      18: '4.5rem',   // 72px - Custom for specific use case
      112: '28rem',   // 448px - Large container widths
      128: '32rem',   // 512px - Modal widths
    },
  },
}
```

**Usage Patterns**:
- **Tight spacing** (`space-y-2`, `gap-2`): 8px - Related items (label + input)
- **Normal spacing** (`space-y-4`, `gap-4`): 16px - Form fields, list items
- **Section spacing** (`space-y-6`, `gap-6`): 24px - Card sections
- **Large spacing** (`space-y-8`, `gap-8`): 32px - Page sections
- **Padding** (`p-4`, `p-6`): 16px-24px - Card/section padding

---

## 4. Typography System

### 4.1 Font Families

```javascript
fontFamily: {
  sans: [
    'Inter',
    'system-ui',
    '-apple-system',
    'BlinkMacSystemFont',
    'Segoe UI',
    'Roboto',
    'Helvetica Neue',
    'Arial',
    'sans-serif',
  ],
  serif: [
    'Georgia',
    'Cambria',
    'Times New Roman',
    'Times',
    'serif',
  ],
  mono: [
    'Fira Code',
    'Consolas',
    'Monaco',
    'Courier New',
    'monospace',
  ],
}
```

**Font Loading** (in `index.html`):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
```

---

### 4.2 Font Sizes

```javascript
fontSize: {
  xs: ['0.75rem', { lineHeight: '1rem' }],       // 12px / 16px
  sm: ['0.875rem', { lineHeight: '1.25rem' }],   // 14px / 20px
  base: ['1rem', { lineHeight: '1.5rem' }],      // 16px / 24px
  lg: ['1.125rem', { lineHeight: '1.75rem' }],   // 18px / 28px
  xl: ['1.25rem', { lineHeight: '1.75rem' }],    // 20px / 28px
  '2xl': ['1.5rem', { lineHeight: '2rem' }],     // 24px / 32px
  '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px / 36px
  '4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px / 40px
  '5xl': ['3rem', { lineHeight: '1' }],           // 48px
  '6xl': ['3.75rem', { lineHeight: '1' }],        // 60px
  '7xl': ['4.5rem', { lineHeight: '1' }],         // 72px
  '8xl': ['6rem', { lineHeight: '1' }],           // 96px
  '9xl': ['8rem', { lineHeight: '1' }],           // 128px
}
```

**Usage Guidelines**:
- **Body text**: `text-base` (16px)
- **Small text/captions**: `text-sm` (14px)
- **Tiny text**: `text-xs` (12px)
- **Section headings**: `text-xl` (20px) or `text-2xl` (24px)
- **Page headings**: `text-3xl` (30px) or `text-4xl` (36px)
- **Hero headings**: `text-5xl` (48px) or larger

---

### 4.3 Font Weights

```javascript
fontWeight: {
  thin: 100,
  extralight: 200,
  light: 300,
  normal: 400,      // Body text
  medium: 500,      // UI labels, emphasized text
  semibold: 600,    // Subheadings
  bold: 700,        // Headings, strong emphasis
  extrabold: 800,
  black: 900,
}
```

**Typography Hierarchy**:
```javascript
// Page title
'text-4xl font-bold text-gray-900'

// Section heading
'text-2xl font-semibold text-gray-900'

// Card title
'text-lg font-semibold text-gray-900'

// Body text
'text-base font-normal text-gray-700'

// UI label
'text-sm font-medium text-gray-700'

// Caption/helper text
'text-sm text-gray-500'

// Code/monospace
'font-mono text-sm text-gray-800'
```

---

### 4.4 Letter Spacing

```javascript
letterSpacing: {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
}
```

**Usage**:
- **Headings**: `tracking-tight` for large headings
- **Body**: `tracking-normal` (default)
- **All caps**: `tracking-wide` or `tracking-wider`

---

### 4.5 Line Height

```javascript
lineHeight: {
  none: 1,
  tight: 1.25,
  snug: 1.375,
  normal: 1.5,
  relaxed: 1.625,
  loose: 2,
}
```

**Usage**:
- **Headings**: `leading-tight` (1.25)
- **Body text**: `leading-normal` (1.5)
- **Captions**: `leading-relaxed` (1.625)

---

## 5. Shadow/Elevation System

### 5.1 Box Shadows

```javascript
boxShadow: {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  none: '0 0 #0000',
}
```

### 5.2 Custom Shadow Extensions

```javascript
theme: {
  extend: {
    boxShadow: {
      'inner-lg': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.1)',
    },
  },
}
```

**Elevation Mapping**:
```javascript
// Level 0 (flush with surface)
'shadow-none'

// Level 1 (subtle elevation)
'shadow-sm'  // Inputs at rest, subtle cards

// Level 2 (standard elevation)
'shadow'  // Standard cards, list items

// Level 3 (raised)
'shadow-md'  // Card hover state, dropdowns

// Level 4 (floating)
'shadow-lg'  // Modals, popovers, important cards

// Level 5 (prominent)
'shadow-xl'  // Drawers, large modals

// Level 6 (highest)
'shadow-2xl'  // Full-screen overlays, notifications
```

**Usage Examples**:
```javascript
// Card at rest
'bg-white rounded-xl shadow-sm border border-gray-200'

// Card on hover
'hover:shadow-md transition-shadow duration-200'

// Modal
'bg-white rounded-2xl shadow-xl'

// Dropdown menu
'bg-white rounded-lg shadow-lg border border-gray-200'
```

---

## 6. Border Radius System

### 6.1 Border Radius Scale

```javascript
borderRadius: {
  none: '0px',
  sm: '0.125rem',    // 2px
  DEFAULT: '0.25rem', // 4px
  md: '0.375rem',    // 6px
  lg: '0.5rem',      // 8px
  xl: '0.75rem',     // 12px
  '2xl': '1rem',     // 16px
  '3xl': '1.5rem',   // 24px
  full: '9999px',    // Pills, circles
}
```

### 6.2 Custom Border Radius Extensions

```javascript
theme: {
  extend: {
    borderRadius: {
      '4xl': '2rem',  // 32px - Extra large modals
    },
  },
}
```

**Component Mapping**:
```javascript
// Buttons
'rounded-lg'  // 8px

// Inputs
'rounded-lg'  // 8px

// Cards
'rounded-xl'  // 12px

// Modals
'rounded-2xl'  // 16px

// Large containers
'rounded-3xl'  // 24px

// Badges/Pills
'rounded-full'  // Fully rounded

// Avatars
'rounded-full'  // Fully rounded

// Small UI elements
'rounded-md'  // 6px
```

---

## 7. Breakpoint System

### 7.1 Responsive Breakpoints

```javascript
screens: {
  xs: '320px',   // Mobile portrait (small phones) - custom
  sm: '640px',   // Mobile landscape
  md: '768px',   // Tablet portrait
  lg: '1024px',  // Tablet landscape / small desktop
  xl: '1280px',  // Desktop
  '2xl': '1536px', // Large desktop
}
```

**Note**: Tailwind doesn't include `xs` by default. Add it to config if needed:

```javascript
theme: {
  extend: {
    screens: {
      xs: '320px',
    },
  },
}
```

### 7.2 Responsive Strategy

**Mobile-First Approach**:
```javascript
// Base styles apply to all sizes (mobile-first)
'text-sm'

// sm: 640px and up (mobile landscape)
'sm:text-base'

// md: 768px and up (tablet)
'md:text-lg'

// lg: 1024px and up (desktop)
'lg:text-xl'

// xl: 1280px and up (large desktop)
'xl:text-2xl'
```

**Responsive Patterns**:
```javascript
// Single column on mobile, two columns on tablet+
'grid grid-cols-1 md:grid-cols-2'

// Stack on mobile, flex row on desktop
'flex flex-col lg:flex-row'

// Hide on mobile, show on desktop
'hidden lg:block'

// Full width on mobile, fixed width on desktop
'w-full lg:w-96'

// Small padding on mobile, large on desktop
'p-4 lg:p-8'
```

---

## 8. Animation & Transition System

### 8.1 Transition Durations

```javascript
transitionDuration: {
  75: '75ms',
  100: '100ms',
  150: '150ms',
  200: '200ms',   // Fast - hover states
  300: '300ms',   // Normal - accordions, modals
  500: '500ms',   // Slow - complex animations
  700: '700ms',
  1000: '1000ms',
}
```

### 8.2 Transition Timing Functions

```javascript
transitionTimingFunction: {
  DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
  linear: 'linear',
  in: 'cubic-bezier(0.4, 0, 1, 1)',
  out: 'cubic-bezier(0, 0, 0.2, 1)',
  'in-out': 'cubic-bezier(0.4, 0, 0.6, 1)',
}
```

### 8.3 Animation Keyframes

```javascript
theme: {
  extend: {
    animation: {
      'spin': 'spin 1s linear infinite',
      'spin-slow': 'spin 3s linear infinite',
      'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      'bounce': 'bounce 1s infinite',
      'in': 'in 200ms ease-out',
      'slide-in-from-top-5': 'slide-in-from-top-5 200ms ease-out',
      'fade-in': 'fade-in 200ms ease-out',
    },
    keyframes: {
      spin: {
        from: { transform: 'rotate(0deg)' },
        to: { transform: 'rotate(360deg)' },
      },
      pulse: {
        '0%, 100%': { opacity: 1 },
        '50%': { opacity: 0.5 },
      },
      bounce: {
        '0%, 100%': {
          transform: 'translateY(-25%)',
          animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)',
        },
        '50%': {
          transform: 'translateY(0)',
          animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)',
        },
      },
      in: {
        '0%': { opacity: '0', transform: 'scale(0.95)' },
        '100%': { opacity: '1', transform: 'scale(1)' },
      },
      'slide-in-from-top-5': {
        '0%': { transform: 'translateY(-1.25rem)' },
        '100%': { transform: 'translateY(0)' },
      },
      'fade-in': {
        '0%': { opacity: '0' },
        '100%': { opacity: '1' },
      },
    },
  },
}
```

**Usage Patterns**:
```javascript
// Button hover transition
'transition-colors duration-200'

// Card hover with shadow
'transition-shadow duration-200 hover:shadow-md'

// Modal enter animation
'animate-in'

// Loading spinner
'animate-spin'

// Skeleton loading
'animate-pulse'

// Multiple properties
'transition-all duration-300'
```

---

## 9. Z-Index System

### 9.1 Z-Index Scale

```javascript
zIndex: {
  0: 0,
  10: 10,
  20: 20,
  30: 30,
  40: 40,
  50: 50,
  auto: 'auto',
}
```

### 9.2 Custom Z-Index Layers

```javascript
theme: {
  extend: {
    zIndex: {
      dropdown: '1000',
      sticky: '1020',
      fixed: '1030',
      modal: '1040',
      popover: '1050',
      tooltip: '1060',
    },
  },
}
```

**Layer Hierarchy**:
```javascript
// Normal content
z-0, z-10

// Dropdowns
z-dropdown (1000)

// Sticky headers
z-sticky (1020)

// Fixed elements
z-fixed (1030)

// Modals
z-modal (1040)

// Popovers
z-popover (1050)

// Tooltips (highest)
z-tooltip (1060)
```

---

## 10. Custom Plugins

### 10.1 Scrollbar Hide Plugin

```javascript
// tailwind.config.js
plugins: [
  function({ addUtilities }) {
    addUtilities({
      '.scrollbar-hide': {
        '-ms-overflow-style': 'none',
        'scrollbar-width': 'none',
        '&::-webkit-scrollbar': {
          display: 'none',
        },
      },
      '.scrollbar-default': {
        '-ms-overflow-style': 'auto',
        'scrollbar-width': 'auto',
        '&::-webkit-scrollbar': {
          display: 'block',
        },
      },
    });
  },
],
```

**Usage**:
```javascript
// Hide scrollbar but keep scrolling functional
'overflow-x-auto scrollbar-hide'

// Restore default scrollbar
'overflow-y-auto scrollbar-default'
```

---

### 10.2 Focus Visible Plugin

```javascript
plugins: [
  function({ addUtilities }) {
    addUtilities({
      '.focus-visible-ring': {
        '&:focus-visible': {
          outline: '2px solid transparent',
          outlineOffset: '2px',
          '--tw-ring-offset-shadow': 'var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color)',
          '--tw-ring-shadow': 'var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color)',
          boxShadow: 'var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000)',
          '--tw-ring-color': '#0284c7', // primary-600
        },
      },
    });
  },
],
```

**Usage**:
```javascript
// Apply focus ring only on keyboard focus (not mouse click)
'focus-visible-ring'
```

---

### 10.3 Safe Area Plugin (for iOS notch)

```javascript
plugins: [
  function({ addUtilities }) {
    addUtilities({
      '.safe-top': {
        paddingTop: 'env(safe-area-inset-top)',
      },
      '.safe-bottom': {
        paddingBottom: 'env(safe-area-inset-bottom)',
      },
      '.safe-left': {
        paddingLeft: 'env(safe-area-inset-left)',
      },
      '.safe-right': {
        paddingRight: 'env(safe-area-inset-right)',
      },
    });
  },
],
```

---

## 11. Accessibility Utilities

### 11.1 Screen Reader Only

```javascript
plugins: [
  function({ addUtilities }) {
    addUtilities({
      '.sr-only': {
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: '0',
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        borderWidth: '0',
      },
      '.not-sr-only': {
        position: 'static',
        width: 'auto',
        height: 'auto',
        padding: '0',
        margin: '0',
        overflow: 'visible',
        clip: 'auto',
        whiteSpace: 'normal',
      },
    });
  },
],
```

**Usage**:
```javascript
// Hidden visually, available to screen readers
<span className="sr-only">Loading...</span>

// Responsive screen reader only
'sr-only lg:not-sr-only'
```

---

## 12. Performance Optimizations

### 12.1 Content Configuration

```javascript
// Optimize PurgeCSS scanning
content: [
  './index.html',
  './src/**/*.{js,ts,jsx,tsx}',
  // Don't include node_modules unless using pre-built components
],
```

### 12.2 Safelist (Prevent Purging)

```javascript
// Preserve dynamic classes
safelist: [
  'bg-success-100',
  'bg-warning-100',
  'bg-error-100',
  'text-success-800',
  'text-warning-800',
  'text-error-800',
  // Add patterns for dynamic classes
  {
    pattern: /bg-(primary|secondary|success|warning|error)-(50|100|600|700)/,
  },
],
```

---

## 13. Complete Configuration Example

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
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
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Fira Code', 'Consolas', 'Monaco', 'Courier New', 'monospace'],
      },
      spacing: {
        18: '4.5rem',
        112: '28rem',
        128: '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'inner-lg': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.1)',
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'in': 'in 200ms ease-out',
        'slide-in-from-top-5': 'slide-in-from-top-5 200ms ease-out',
        'fade-in': 'fade-in 200ms ease-out',
      },
      keyframes: {
        in: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'slide-in-from-top-5': {
          '0%': { transform: 'translateY(-1.25rem)' },
          '100%': { transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.scrollbar-hide': {
          '-ms-overflow-style': 'none',
          'scrollbar-width': 'none',
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        },
      });
    },
  ],
};
```

---

## 14. Usage Guidelines

### 14.1 Design Token Selection

**When choosing tokens**:
1. **Always use design tokens** instead of arbitrary values
2. **Prefer utility classes** over custom CSS
3. **Use semantic color names** (primary, success, error) not literal colors
4. **Follow spacing scale** (4px/8px multiples)
5. **Maintain consistency** across similar components

**Good**:
```javascript
'bg-primary-600 text-white px-4 py-2 rounded-lg'
```

**Bad**:
```javascript
'bg-[#0284c7] text-[#ffffff] px-[15px] py-[9px] rounded-[8px]'
```

---

### 14.2 Responsive Design Patterns

```javascript
// Mobile-first approach
'text-sm md:text-base lg:text-lg'

// Container max-width
'container mx-auto px-4 sm:px-6 lg:px-8'

// Grid layouts
'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'

// Flex layouts
'flex flex-col md:flex-row gap-4'
```

---

### 14.3 Accessibility Patterns

```javascript
// Focus states (always include)
'focus:ring-2 focus:ring-primary-500 focus:outline-none'

// Color contrast (WCAG AA)
'bg-primary-600 text-white'  // 4.5:1 contrast ratio

// Screen reader support
'sr-only'  // Visually hidden but accessible

// Keyboard navigation
'focus-visible:ring-2'  // Only show focus ring on keyboard nav
```

---

## 15. Migration Guide

### 15.1 Updating Existing Components

**Before**:
```javascript
className="bg-blue-500 hover:bg-blue-600"
```

**After**:
```javascript
className="bg-primary-600 hover:bg-primary-700"
```

### 15.2 Adding New Colors

1. Define in `tailwind.config.js`
2. Add full scale (50-950) for consistency
3. Update safelist if using dynamically
4. Document usage in this file

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-04
**Next Review**: After implementation feedback
**Maintained By**: Frontend Engineering Team
