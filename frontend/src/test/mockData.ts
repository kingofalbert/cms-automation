/**
 * Mock Data for Testing
 *
 * Provides mock data that matches the API type definitions.
 */

import type {
  Article,
  SEOMetadata,
  PublishTask,
  RuleDraft,
  PublishedRuleset,
  User,
} from '../types/api';
import type { WorklistItem } from '../types/worklist';

// Mock Articles
export const mockArticle: Article = {
  id: 1,
  title: 'Test Article',
  content: 'This is a test article content.',
  excerpt: 'Test excerpt',
  category: 'Technology',
  tags: ['test', 'article'],
  status: 'imported',
  source: 'manual_entry',
  featured_image_path: '/images/test.jpg',
  additional_images: [],
  published_url: undefined,
  cms_article_id: undefined,
  article_metadata: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  published_at: undefined,
};

export const mockArticles: Article[] = [
  mockArticle,
  {
    ...mockArticle,
    id: 2,
    title: 'Another Article',
    status: 'seo_optimized',
  },
  {
    ...mockArticle,
    id: 3,
    title: 'Published Article',
    status: 'published',
    published_url: 'https://example.com/article',
    published_at: '2024-01-02T00:00:00Z',
  },
];

// Mock SEO Metadata
export const mockSEOMetadata: SEOMetadata = {
  id: 1,
  article_id: 1,
  meta_title: 'Test Article - SEO Title',
  meta_description: 'This is a test article for SEO optimization.',
  focus_keyword: 'test',
  primary_keywords: ['test', 'article', 'seo'],
  secondary_keywords: ['optimization', 'content'],
  keyword_density: {
    test: 0.02,
    article: 0.015,
    seo: 0.01,
  },
  readability_score: 75,
  optimization_recommendations: [
    {
      type: 'title',
      severity: 'info',
      message: 'Title is optimized',
      suggestion: undefined,
    },
  ],
  manual_overrides: {},
  generated_by: 'claude-3.5-sonnet',
  generation_cost: 0.001,
  generation_tokens: 100,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Mock Publish Tasks
export const mockPublishTask: PublishTask = {
  id: 1,
  article_id: 1,
  task_id: 'task-123',
  provider: 'anthropic',
  cms_type: 'wordpress',
  cms_url: 'https://example.com',
  status: 'pending',
  retry_count: 0,
  max_retries: 3,
  error_message: undefined,
  session_id: 'session-123',
  screenshots: [],
  cost_usd: undefined,
  started_at: undefined,
  completed_at: undefined,
  duration_seconds: undefined,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  current_step: undefined,
  progress_percentage: undefined,
};

export const mockPublishTasks: PublishTask[] = [
  mockPublishTask,
  {
    ...mockPublishTask,
    id: 2,
    task_id: 'task-124',
    status: 'running',
    current_step: 'Uploading images',
    progress_percentage: 50,
  },
  {
    ...mockPublishTask,
    id: 3,
    task_id: 'task-125',
    status: 'completed',
    completed_at: '2024-01-01T01:00:00Z',
    duration_seconds: 120,
    cost_usd: 0.05,
  },
  {
    ...mockPublishTask,
    id: 4,
    task_id: 'task-126',
    status: 'failed',
    error_message: 'Connection timeout',
    retry_count: 3,
  },
];

// Mock Worklist Items
export const mockWorklistItem: WorklistItem = {
  id: 1,
  drive_file_id: 'drive-123',
  title: 'Worklist Item 1',
  status: 'pending',
  metadata: {
    word_count: 1200,
    estimated_reading_time: 5,
  },
  author: 'Test Author',
  notes: [],
  synced_at: '2024-01-01T00:00:00Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockWorklistItems: WorklistItem[] = [
  mockWorklistItem,
  {
    ...mockWorklistItem,
    id: 2,
    title: 'Worklist Item 2',
    status: 'under_review',
    notes: [
      {
        id: 'note-1',
        author: 'Reviewer',
        message: 'Needs revision',
        created_at: '2024-01-01T01:00:00Z',
      },
    ],
  },
];

// Mock Rule Drafts
export const mockRuleDraft: RuleDraft = {
  draft_id: 'draft-123',
  description: 'Test rule draft',
  status: 'draft',
  rules: [
    {
      rule_id: 'rule-1',
      rule_type: 'grammar',
      natural_language: 'Fix common grammar mistakes',
      pattern: '(\\w+)\\s+\\1',
      replacement: '$1',
      confidence: 0.9,
      examples: [
        {
          before: 'the the',
          after: 'the',
          description: 'Remove duplicate words',
        },
      ],
      conditions: {},
      review_status: 'pending',
      review_comment: undefined,
      metadata: {},
    },
  ],
  metadata: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  total_rules: 1,
  approved_count: 0,
  rejected_count: 0,
  pending_count: 1,
};

// Mock Published Rulesets
export const mockPublishedRuleset: PublishedRuleset = {
  ruleset_id: 'ruleset-123',
  name: 'Grammar Rules v1.0',
  total_rules: 10,
  created_at: '2024-01-01T00:00:00Z',
  status: 'active',
  download_urls: {
    python: 'https://example.com/rules/python',
    typescript: 'https://example.com/rules/typescript',
    json: 'https://example.com/rules/json',
  },
};

// Mock User
export const mockUser: User = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  created_at: '2024-01-01T00:00:00Z',
};

// Mock WebSocket Messages
export const mockWebSocketMessage = {
  type: 'task_update' as const,
  data: {
    task_id: 'task-123',
    status: 'running' as const,
    current_step: 'Processing',
    progress_percentage: 50,
  },
  timestamp: '2024-01-01T00:00:00Z',
};

// Helper: Create mock paginated response
export function createMockPaginatedResponse<T>(items: T[], page = 1, limit = 20) {
  return {
    items,
    total: items.length,
    page,
    limit,
    has_next: items.length > page * limit,
    has_prev: page > 1,
  };
}

// Helper: Create mock API response
export function createMockAPIResponse<T>(data: T, success = true) {
  return {
    success,
    data,
    message: success ? undefined : 'An error occurred',
    request_id: 'test-request-id',
  };
}
