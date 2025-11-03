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
  const currentRoute = getRouteConfig(location.pathname);

  // Update document title when route changes
  useEffect(() => {
    if (currentRoute?.title) {
      document.title = currentRoute.title;
    }

    // Update meta description
    if (currentRoute?.description) {
      let metaDesc = document.querySelector('meta[name="description"]');
      if (!metaDesc) {
        metaDesc = document.createElement('meta');
        metaDesc.setAttribute('name', 'description');
        document.head.appendChild(metaDesc);
      }
      metaDesc.setAttribute('content', currentRoute.description);
    }
  }, [currentRoute]);

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
