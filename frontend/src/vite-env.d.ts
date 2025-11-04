/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_ENABLE_ERROR_REPORTING?: string;
  readonly VITE_ERROR_TRACKING_ENDPOINT?: string;
  readonly VITE_ENABLE_DEVTOOLS?: string;
  readonly VITE_ENABLE_MOCK_DATA?: string;
  readonly VITE_ENABLE_EXPERIMENTAL_FEATURES?: string;
  readonly VITE_ENABLE_PERFORMANCE_MONITORING?: string;
  readonly VITE_DEFAULT_POLLING_INTERVAL?: string;
  readonly VITE_TASK_POLLING_INTERVAL?: string;
  readonly VITE_APP_TITLE?: string;
  readonly VITE_APP_VERSION?: string;
  readonly VITE_APP_DESCRIPTION?: string;
  readonly VITE_ENV?: string;
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
