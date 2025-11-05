/**
 * Main App component with routing and providers.
 */

import { HashRouter } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'sonner';
import { AppRoutes } from './routes';
import { queryClient } from './services/query-client';
import ErrorBoundary from './components/ErrorBoundary';
import Navigation from './components/layout/Navigation';

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
      <QueryClientProvider client={queryClient}>
        <HashRouter>
          <div className="min-h-screen bg-gray-50">
            <Navigation />
            <AppRoutes />
          </div>
        </HashRouter>
        {/* Show React Query DevTools in development */}
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
        <Toaster position="top-right" toastOptions={{ duration: 5000 }} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
