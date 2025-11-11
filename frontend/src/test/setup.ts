/**
 * Vitest Setup File
 *
 * This file runs before all tests and sets up the testing environment.
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Initialize i18next for testing
i18n.use(initReactI18next).init({
  lng: 'zh-TW',
  fallbackLng: 'en-US',
  ns: ['translation'],
  defaultNS: 'translation',
  debug: false,
  interpolation: {
    escapeValue: false,
  },
  resources: {
    'zh-TW': {
      translation: {
        'proofreading.comparison.title': 'AI 优化建议',
        'proofreading.comparison.meta.title': 'Meta Description',
        'proofreading.comparison.seo.title': 'SEO 优化',
        'proofreading.diffView.original': '原始内容',
        'proofreading.diffView.suggested': '建议内容',
        'articleReview.steps.parsing': '解析审核',
        'articleReview.steps.proofreading': '校对审核',
        'articleReview.steps.publish': '发布预览',
        'articleReview.parsing.title': '标题',
        'articleReview.actions.approve': '批准',
        'articleReview.actions.edit': '编辑',
        'articleReview.actions.save': '保存',
        'articleReview.actions.cancel': '取消',
      },
    },
    'en-US': {
      translation: {
        'proofreading.comparison.title': 'AI Optimization Suggestions',
        'proofreading.comparison.meta.title': 'Meta Description',
        'proofreading.comparison.seo.title': 'SEO Optimization',
        'proofreading.diffView.original': 'Original Content',
        'proofreading.diffView.suggested': 'Suggested Content',
        'articleReview.steps.parsing': 'Parsing Review',
        'articleReview.steps.proofreading': 'Proofreading Review',
        'articleReview.steps.publish': 'Publish Preview',
        'articleReview.parsing.title': 'Title',
        'articleReview.actions.approve': 'Approve',
        'articleReview.actions.edit': 'Edit',
        'articleReview.actions.save': 'Save',
        'articleReview.actions.cancel': 'Cancel',
      },
    },
  },
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // Mock window.scrollTo
  Object.defineProperty(window, 'scrollTo', {
    writable: true,
    value: vi.fn(),
  });

  // Mock IntersectionObserver
  (globalThis as any).IntersectionObserver = class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    takeRecords() {
      return [];
    }
    unobserve() {}
  };

  // Mock ResizeObserver
  (globalThis as any).ResizeObserver = class ResizeObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  };
});

// Suppress console errors in tests (optional)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    // Filter out specific expected errors
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

beforeAll(() => {
  vi.stubEnv('VITE_API_URL', 'http://localhost:8000');
  vi.stubEnv('VITE_WS_URL', 'ws://localhost:8000/ws');
});
