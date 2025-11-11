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
        // Proofreading - Comparison Cards
        'proofreading.comparison.title': 'AI 优化建议',
        'proofreading.comparison.meta.title': 'Meta Description',
        'proofreading.comparison.meta.original': '原始 ({{count}} 字符)',
        'proofreading.comparison.meta.suggested': '建议 ({{count}} 字符)',
        'proofreading.comparison.meta.reasoning': '优化理由',
        'proofreading.comparison.meta.notSet': '未设置',
        'proofreading.comparison.seo.title': 'SEO 关键词',
        'proofreading.comparison.seo.original': '原始关键词 ({{count}})',
        'proofreading.comparison.seo.suggested': '建议关键词',
        'proofreading.comparison.seo.reasoning': '优化理由',
        'proofreading.comparison.seo.notSet': '未设置',
        'proofreading.comparison.faq.title': 'FAQ Schema 提案',
        'proofreading.comparison.faq.count': '{{count}} 个提案',
        'proofreading.comparison.faq.proposal': '提案 {{index}}',
        'proofreading.comparison.faq.schemaType': '类型: {{type}}',
        'proofreading.comparison.faq.question': 'Q{{index}}: {{question}}',
        'proofreading.comparison.faq.answer': 'A: {{answer}}',
        // Proofreading - DiffView
        'proofreading.labels.original': '原始内容',
        'proofreading.labels.suggested': '建议内容',
        'proofreading.diffView.original': '原始内容',
        'proofreading.diffView.suggested': '建议内容',
        // Article Review - Steps
        'articleReview.steps.parsing': '解析审核',
        'articleReview.steps.proofreading': '校对审核',
        'articleReview.steps.publish': '发布预览',
        // Article Review - Parsing
        'articleReview.parsing.title': '标题',
        // Article Review - Actions
        'articleReview.actions.approve': '批准',
        'articleReview.actions.edit': '编辑',
        'articleReview.actions.save': '保存',
        'articleReview.actions.cancel': '取消',
      },
    },
    'en-US': {
      translation: {
        // Proofreading - Comparison Cards
        'proofreading.comparison.title': 'AI Optimization Suggestions',
        'proofreading.comparison.meta.title': 'Meta Description',
        'proofreading.comparison.meta.original': 'Original ({{count}} chars)',
        'proofreading.comparison.meta.suggested': 'Suggested ({{count}} chars)',
        'proofreading.comparison.meta.reasoning': 'Reasoning',
        'proofreading.comparison.meta.notSet': 'Not set',
        'proofreading.comparison.seo.title': 'SEO Keywords',
        'proofreading.comparison.seo.original': 'Original Keywords ({{count}})',
        'proofreading.comparison.seo.suggested': 'Suggested Keywords',
        'proofreading.comparison.seo.reasoning': 'Reasoning',
        'proofreading.comparison.seo.notSet': 'Not set',
        'proofreading.comparison.faq.title': 'FAQ Schema Proposals',
        'proofreading.comparison.faq.count': '{{count}} proposals',
        'proofreading.comparison.faq.proposal': 'Proposal {{index}}',
        'proofreading.comparison.faq.schemaType': 'Type: {{type}}',
        'proofreading.comparison.faq.question': 'Q{{index}}: {{question}}',
        'proofreading.comparison.faq.answer': 'A: {{answer}}',
        // Proofreading - DiffView
        'proofreading.labels.original': 'Original Content',
        'proofreading.labels.suggested': 'Suggested Content',
        'proofreading.diffView.original': 'Original Content',
        'proofreading.diffView.suggested': 'Suggested Content',
        // Article Review - Steps
        'articleReview.steps.parsing': 'Parsing Review',
        'articleReview.steps.proofreading': 'Proofreading Review',
        'articleReview.steps.publish': 'Publish Preview',
        // Article Review - Parsing
        'articleReview.parsing.title': 'Title',
        // Article Review - Actions
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
