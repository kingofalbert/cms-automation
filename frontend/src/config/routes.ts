/**
 * Enhanced Route Configuration
 *
 * Centralized route definitions with lazy loading, preloading, and metadata
 */

import { lazy, ComponentType } from 'react';

export interface RouteConfig {
  path: string;
  /** Lazy-loaded component */
  component: ComponentType<any>;
  /** Preload function for prefetching */
  preload?: () => Promise<any>;
  /** Route title for meta tags */
  title?: string;
  /** Route description for meta tags */
  description?: string;
  /** Whether to show in navigation */
  showInNav?: boolean;
  /** Navigation label */
  navLabel?: string;
  /** Icon for navigation */
  icon?: string;
  /** Loading fallback type */
  loadingType?: 'default' | 'list' | 'detail' | 'dashboard';
}

/**
 * Helper function to create lazy component with preload support
 */
function createLazyRoute(importFunc: () => Promise<{ default: ComponentType<any> }>) {
  const LazyComponent = lazy(importFunc);
  return {
    component: LazyComponent,
    preload: importFunc,
  };
}

// Phase 1: Active pages
const SettingsPage = createLazyRoute(() => import('../pages/SettingsPageModern'));
const WorklistPage = createLazyRoute(() => import('../pages/WorklistPage'));

// Phase 2+: Commented out for future use
// const HomePage = createLazyRoute(() => import('../pages/HomePage'));
// const ArticleGeneratorPage = createLazyRoute(() => import('../pages/ArticleGeneratorPage'));
// const ArticleImportPage = createLazyRoute(() => import('../pages/ArticleImportPage'));
// const ArticleListPage = createLazyRoute(() => import('../pages/ArticleListPage'));
// const ArticleReviewPage = createLazyRoute(() => import('../pages/ArticleReviewPage'));
// const PublishTasksPage = createLazyRoute(() => import('../pages/PublishTasksPage'));
// const ProviderComparisonPage = createLazyRoute(() => import('../pages/ProviderComparisonPage'));
// const ScheduleManagerPage = createLazyRoute(() => import('../pages/ScheduleManagerPage'));
// const TagsPage = createLazyRoute(() => import('../pages/TagsPage'));
// const RuleDraftList = createLazyRoute(() => import('../components/proofreading/RuleManagement/RuleDraftList'));
// const RuleDetailPage = createLazyRoute(() => import('../components/proofreading/RuleDetail/RuleDetailPage'));
// const RuleTestPage = createLazyRoute(() => import('../pages/RuleTestPage'));
// const PublishedRulesPage = createLazyRoute(() => import('../pages/PublishedRulesPage'));
// const ProofreadingStatsPage = createLazyRoute(() => import('../pages/ProofreadingStatsPage'));

/**
 * Route configurations
 *
 * Phase 1: Simplified routes focusing on core worklist functionality
 * Only /worklist and /settings are active. All other routes are hidden for future phases.
 */
export const routes: RouteConfig[] = [
  // Phase 1: Redirect root to worklist
  {
    path: '/',
    ...WorklistPage,
    title: 'CMS自动化系统 - 工作清单',
    description: '管理您的文章校对工作流',
    loadingType: 'list',
  },
  // Phase 1: Worklist - Main page
  {
    path: '/worklist',
    ...WorklistPage,
    title: 'CMS自动化系统 - 工作清单',
    description: '管理您的文章校对工作流',
    showInNav: false, // No navigation menu in Phase 1
    loadingType: 'list',
  },
  // Phase 1: Settings page
  {
    path: '/settings',
    ...SettingsPage,
    title: 'CMS自动化系统 - 设置',
    description: '配置系统设置和语言偏好',
    showInNav: false, // No navigation menu in Phase 1
    loadingType: 'detail',
  },

  // PHASE 2+ ROUTES (Hidden in Phase 1)
  // Uncomment these routes in future phases:
  /*
  {
    path: '/generate',
    ...ArticleGeneratorPage,
    title: '生成文章',
    description: '使用AI生成文章內容',
    showInNav: true,
    navLabel: '生成文章',
    icon: 'file-plus',
    loadingType: 'detail',
  },
  {
    path: '/import',
    ...ArticleImportPage,
    title: '導入文章',
    description: '從CSV或Google Drive導入文章',
    showInNav: true,
    navLabel: '導入文章',
    icon: 'upload',
    loadingType: 'detail',
  },
  {
    path: '/articles',
    ...ArticleListPage,
    title: '文章列表',
    description: '查看和管理所有文章',
    showInNav: true,
    navLabel: '文章列表',
    icon: 'list',
    loadingType: 'list',
  },
  {
    path: '/articles/:id/review',
    ...ArticleReviewPage,
    title: '審核文章',
    description: '審核和編輯文章內容',
    loadingType: 'detail',
  },
  {
    path: '/tasks',
    ...PublishTasksPage,
    title: '發佈任務',
    description: '監控文章發佈任務',
    showInNav: true,
    navLabel: '發佈任務',
    icon: 'send',
    loadingType: 'list',
  },
  {
    path: '/comparison',
    ...ProviderComparisonPage,
    title: 'AI提供商對比',
    description: '對比不同AI提供商的性能',
    showInNav: true,
    navLabel: '提供商對比',
    icon: 'bar-chart',
    loadingType: 'dashboard',
  },
  {
    path: '/schedule',
    ...ScheduleManagerPage,
    title: '排程管理',
    description: '管理文章發佈排程',
    showInNav: true,
    navLabel: '排程管理',
    icon: 'calendar',
    loadingType: 'list',
  },
  {
    path: '/tags',
    ...TagsPage,
    title: '標籤管理',
    description: '管理文章標籤',
    showInNav: true,
    navLabel: '標籤管理',
    icon: 'tag',
    loadingType: 'list',
  },
  {
    path: '/proofreading/rules',
    ...RuleDraftList,
    title: '校對規則',
    description: '管理校對規則草稿',
    showInNav: true,
    navLabel: '校對規則',
    icon: 'check-circle',
    loadingType: 'list',
  },
  {
    path: '/proofreading/draft/:draftId',
    ...RuleDetailPage,
    title: '規則詳情',
    description: '查看規則草稿詳情',
    loadingType: 'detail',
  },
  {
    path: '/proofreading/test/:draftId',
    ...RuleTestPage,
    title: '測試規則',
    description: '測試校對規則',
    loadingType: 'detail',
  },
  {
    path: '/proofreading/published',
    ...PublishedRulesPage,
    title: '已發佈規則',
    description: '查看已發佈的規則集',
    showInNav: true,
    navLabel: '已發佈規則',
    icon: 'check-square',
    loadingType: 'list',
  },
  {
    path: '/proofreading/stats',
    ...ProofreadingStatsPage,
    title: '校對統計',
    description: '查看校對統計數據',
    showInNav: true,
    navLabel: '校對統計',
    icon: 'pie-chart',
    loadingType: 'dashboard',
  },
  */
];

/**
 * Get route configuration by path
 */
export function getRouteConfig(path: string): RouteConfig | undefined {
  return routes.find((route) => route.path === path);
}

/**
 * Get all navigation routes
 */
export function getNavigationRoutes(): RouteConfig[] {
  return routes.filter((route) => route.showInNav);
}

/**
 * Preload route by path
 */
export async function preloadRoute(path: string): Promise<void> {
  const route = getRouteConfig(path);
  if (route?.preload) {
    await route.preload();
  }
}

/**
 * Preload multiple routes
 */
export async function preloadRoutes(paths: string[]): Promise<void> {
  await Promise.all(paths.map(preloadRoute));
}

export default routes;
