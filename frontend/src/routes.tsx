/**
 * React Router route definitions for CMS Automation UI.
 *
 * Uses lazy loading with code splitting for optimal performance.
 * Enhanced with preloading and skeleton screens.
 */

import { Route, Routes, useLocation } from 'react-router-dom';
import { Suspense, useEffect } from 'react';
import { routes, getRouteConfig, type RouteConfig } from './config/routes';
import {
  RouteLoadingFallback,
  ListPageSkeleton,
  DetailPageSkeleton,
  DashboardSkeleton,
} from './components/ui/RouteLoadingFallback';
import { useTranslation } from 'react-i18next';

/**
 * Get appropriate loading component based on route type
 */
function getLoadingFallback(routeConfig?: RouteConfig) {
  if (!routeConfig) {
    return <RouteLoadingFallback />;
  }

  switch (routeConfig.loadingType) {
    case 'list':
      return <ListPageSkeleton />;
    case 'detail':
      return <DetailPageSkeleton />;
    case 'dashboard':
      return <DashboardSkeleton />;
    default:
      return <RouteLoadingFallback />;
  }
}

/**
 * Application routes component with enhanced lazy loading.
 */
export function AppRoutes() {
  const location = useLocation();
  const { t } = useTranslation();
  const currentRoute = getRouteConfig(location.pathname);

  // Update document title when route changes
  useEffect(() => {
    const resolvedTitle = currentRoute?.titleKey
      ? t(currentRoute.titleKey)
      : currentRoute?.title;
    if (resolvedTitle) {
      document.title = resolvedTitle;
    }

    const resolvedDescription = currentRoute?.descriptionKey
      ? t(currentRoute.descriptionKey)
      : currentRoute?.description;

    if (resolvedDescription) {
      let metaDesc = document.querySelector('meta[name="description"]');
      if (!metaDesc) {
        metaDesc = document.createElement('meta');
        metaDesc.setAttribute('name', 'description');
        document.head.appendChild(metaDesc);
      }
      metaDesc.setAttribute('content', resolvedDescription);
    }
  }, [currentRoute, t]);

  return (
    <Suspense fallback={getLoadingFallback(currentRoute)}>
      <Routes>
        {routes.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            element={<route.component />}
          />
        ))}
      </Routes>
    </Suspense>
  );
}
