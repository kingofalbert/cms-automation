/**
 * React Router route definitions for CMS Automation UI.
 */

import { Route, Routes } from 'react-router-dom';
import { Suspense, lazy } from 'react';

// Lazy load pages for code splitting
const HomePage = lazy(() => import('./pages/HomePage'));
const ArticleGeneratorPage = lazy(() => import('./pages/ArticleGeneratorPage'));
const ArticleImportPage = lazy(() => import('./pages/ArticleImportPage'));
const ArticleListPage = lazy(() => import('./pages/ArticleListPage'));
const ArticleReviewPage = lazy(() => import('./pages/ArticleReviewPage'));
const PublishTasksPage = lazy(() => import('./pages/PublishTasksPage'));
const ProviderComparisonPage = lazy(() => import('./pages/ProviderComparisonPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const WorklistPage = lazy(() => import('./pages/WorklistPage'));
const ScheduleManagerPage = lazy(() => import('./pages/ScheduleManagerPage'));
const TagsPage = lazy(() => import('./pages/TagsPage'));

/**
 * Loading fallback component.
 */
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-gray-600">Loading...</div>
    </div>
  );
}

/**
 * Application routes component.
 */
export function AppRoutes() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/generate" element={<ArticleGeneratorPage />} />
        <Route path="/import" element={<ArticleImportPage />} />
        <Route path="/articles" element={<ArticleListPage />} />
        <Route path="/articles/:id/review" element={<ArticleReviewPage />} />
        <Route path="/tasks" element={<PublishTasksPage />} />
        <Route path="/comparison" element={<ProviderComparisonPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/worklist" element={<WorklistPage />} />
        <Route path="/schedule" element={<ScheduleManagerPage />} />
        <Route path="/tags" element={<TagsPage />} />
      </Routes>
    </Suspense>
  );
}
