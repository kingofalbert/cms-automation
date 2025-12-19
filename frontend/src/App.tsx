/**
 * Main App component with routing and providers.
 */

import { HashRouter, useLocation } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'sonner';
import { AppRoutes } from './routes';
import { queryClient } from './services/query-client';
import ErrorBoundary from './components/ErrorBoundary';
import { Phase1Header } from './components/layout/Phase1Header';
import { AuthProvider } from './contexts/AuthContext';
// Initialize i18n
import './i18n/config';

/**
 * Layout wrapper that conditionally shows header based on route
 */
function AppLayout() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <>
      {/* Hide header on login page */}
      {!isLoginPage && <Phase1Header />}
      <div className="min-h-screen bg-gray-50">
        <AppRoutes />
      </div>
    </>
  );
}

function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log error to console or error tracking service
        console.error('App Error:', error, errorInfo);

        // TODO: Send to error tracking service
        // Example: logErrorToService(error, errorInfo);
      }}
    >
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <HashRouter>
            <AppLayout />
          </HashRouter>
          {/* Show React Query DevTools in development */}
          {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
          <Toaster position="top-right" toastOptions={{ duration: 5000 }} />
        </QueryClientProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
