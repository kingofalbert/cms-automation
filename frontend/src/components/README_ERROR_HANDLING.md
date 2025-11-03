# 錯誤處理組件使用指南

本項目包含完整的錯誤處理機制，包括 React Error Boundary、錯誤日誌服務和多種錯誤展示組件。

## 組件概覽

### 1. ErrorBoundary (全局錯誤邊界)

用於捕獲整個應用或大型功能模塊中的 JavaScript 錯誤。

**特點：**
- 捕獲子組件樹中的所有錯誤
- 自動記錄錯誤到 localStorage 和控制台
- 提供友好的錯誤 UI 和重試功能
- 開發環境顯示詳細的錯誤堆棧

**使用方式：**

```tsx
import ErrorBoundary from './components/ErrorBoundary';

// 包裹整個應用（已在 App.tsx 中實現）
function App() {
  return (
    <ErrorBoundary onError={(error, errorInfo) => {
      // 可選：自定義錯誤處理
      console.error('App Error:', error, errorInfo);
    }}>
      <YourApp />
    </ErrorBoundary>
  );
}

// 包裹特定功能模塊
function DashboardPage() {
  return (
    <ErrorBoundary fallback={<CustomErrorUI />}>
      <DashboardContent />
    </ErrorBoundary>
  );
}
```

**Props：**
- `children`: 子組件
- `fallback`: 自定義錯誤 UI（可選）
- `onError`: 錯誤回調函數（可選）
- `showDetails`: 是否顯示詳細錯誤信息（默認在開發環境顯示）

### 2. ErrorFallback (輕量級錯誤顯示)

用於顯示特定區域或功能的錯誤狀態。

**使用方式：**

```tsx
import { ErrorFallback, InlineError, EmptyError } from './components/ErrorFallback';

// Alert 樣式錯誤
function MyComponent() {
  const [error, setError] = useState<Error | null>(null);

  if (error) {
    return (
      <ErrorFallback
        error={error}
        title="加載失敗"
        message="無法加載數據，請重試"
        onRetry={() => {
          setError(null);
          fetchData();
        }}
        onDismiss={() => setError(null)}
      />
    );
  }

  return <Content />;
}

// 行內錯誤顯示
function FormField() {
  return (
    <div>
      <input />
      {error && <InlineError error={error} onRetry={handleRetry} />}
    </div>
  );
}

// 空狀態錯誤
function DataList() {
  if (error) {
    return (
      <EmptyError
        title="加載失敗"
        description="無法獲取列表數據"
        onRetry={refetch}
      />
    );
  }

  return <List data={data} />;
}
```

### 3. 錯誤日誌服務

自動記錄所有錯誤到 localStorage，並支持導出和統計分析。

**功能：**
- 自動記錄 React 錯誤和 API 錯誤
- 存儲最近 50 條錯誤日誌
- 支持導出為 JSON 文件
- 提供錯誤統計功能

**使用方式：**

```tsx
import {
  logError,
  logAPIError,
  getStoredErrorLogs,
  clearStoredErrorLogs,
  exportErrorLogs,
  getErrorStatistics,
} from './utils/errorLogger';

// 手動記錄錯誤
try {
  riskyOperation();
} catch (error) {
  logError(error as Error, undefined, {
    context: 'user_action',
    action: 'submit_form',
  });
}

// 查看錯誤日誌
const logs = getStoredErrorLogs();
console.log('Recent errors:', logs);

// 導出錯誤日誌
exportErrorLogs(); // 下載 JSON 文件

// 獲取錯誤統計
const stats = getErrorStatistics();
console.log('Total errors:', stats.total);
console.log('Errors by type:', stats.byType);

// 清除錯誤日誌
clearStoredErrorLogs();
```

## API 錯誤處理

所有 API 錯誤都會自動通過 axios 攔截器記錄。

**自動記錄的信息：**
- 錯誤狀態碼
- 錯誤消息
- 請求端點
- 請求方法
- Request ID（如果可用）

**在組件中處理 API 錯誤：**

```tsx
import { articlesAPI } from './services';
import { ErrorFallback } from './components/ErrorFallback';

function ArticleList() {
  const [error, setError] = useState<Error | null>(null);

  const fetchArticles = async () => {
    try {
      const response = await articlesAPI.list();
      setArticles(response.data.items);
    } catch (err) {
      setError(err as Error);
      // 錯誤已自動記錄到日誌
    }
  };

  if (error) {
    return <ErrorFallback error={error} onRetry={fetchArticles} />;
  }

  return <ArticleTable />;
}
```

## React Query 錯誤處理

使用 React Query 時的錯誤處理模式：

```tsx
import { useQuery } from '@tanstack/react-query';
import { ErrorFallback } from './components/ErrorFallback';

function MyComponent() {
  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ['articles'],
    queryFn: () => articlesAPI.list(),
  });

  if (error) {
    return <ErrorFallback error={error} onRetry={() => refetch()} />;
  }

  if (isLoading) return <Loading />;

  return <Content data={data} />;
}
```

## 最佳實踐

### 1. 分層錯誤處理

```
App (ErrorBoundary)
  └── Page (ErrorBoundary)
      └── Feature (ErrorFallback)
          └── Component (InlineError)
```

### 2. 錯誤恢復策略

```tsx
// 自動重試
const MAX_RETRIES = 3;
const [retryCount, setRetryCount] = useState(0);

const handleRetry = () => {
  if (retryCount < MAX_RETRIES) {
    setRetryCount(prev => prev + 1);
    fetchData();
  } else {
    // 顯示永久錯誤
    showPermanentError();
  }
};
```

### 3. 用戶友好的錯誤消息

```tsx
function getUserFriendlyMessage(error: Error): string {
  if (error.message.includes('Network Error')) {
    return '網絡連接失敗，請檢查您的網絡設置';
  }
  if (error.message.includes('401')) {
    return '登錄已過期，請重新登錄';
  }
  if (error.message.includes('403')) {
    return '您沒有權限執行此操作';
  }
  return '操作失敗，請稍後重試';
}
```

### 4. 關鍵操作的額外確認

```tsx
// 對於可能失敗的關鍵操作，添加確認步驟
import { Modal } from 'antd';

async function deleteArticle(id: number) {
  Modal.confirm({
    title: '確認刪除',
    content: '此操作無法撤銷，確定要刪除嗎？',
    onOk: async () => {
      try {
        await articlesAPI.delete(id);
        message.success('刪除成功');
      } catch (error) {
        Modal.error({
          title: '刪除失敗',
          content: getUserFriendlyMessage(error as Error),
        });
      }
    },
  });
}
```

## 開發環境調試

在開發環境中，錯誤處理提供額外的調試功能：

1. **詳細的錯誤堆棧**：顯示完整的錯誤堆棧和組件堆棧
2. **控制台分組**：使用 `console.group` 組織錯誤日誌
3. **錯誤統計**：在瀏覽器控制台查看錯誤統計

```javascript
// 在控制台中查看錯誤統計
import { getErrorStatistics } from './utils/errorLogger';
window.getErrorStats = getErrorStatistics;

// 然後在控制台執行
window.getErrorStats();
```

## 集成外部錯誤追踪服務

如需集成 Sentry、LogRocket 等錯誤追踪服務，請在以下位置添加代碼：

**1. utils/errorLogger.ts 中的 `sendToErrorTrackingService` 函數**

```typescript
async function sendToErrorTrackingService(errorLog: ErrorLog): Promise<void> {
  if (window.Sentry) {
    window.Sentry.captureException(new Error(errorLog.message), {
      contexts: {
        error: errorLog,
      },
    });
  }
}
```

**2. 在 index.html 或 main.tsx 中初始化服務**

```typescript
// main.tsx
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: 'YOUR_SENTRY_DSN',
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
});
```

## 環境變量配置

在 `.env` 文件中配置錯誤追踪：

```env
# 啟用錯誤追踪（默認僅在生產環境）
VITE_ENABLE_ERROR_TRACKING=true

# 錯誤追踪服務端點
VITE_ERROR_TRACKING_ENDPOINT=https://your-error-tracking-service.com/api/errors

# Sentry DSN（如果使用 Sentry）
VITE_SENTRY_DSN=your-sentry-dsn
```

## 總結

- ✅ 全局 ErrorBoundary 捕獲應用級錯誤
- ✅ 局部 ErrorFallback 顯示功能級錯誤
- ✅ 自動記錄所有錯誤到 localStorage
- ✅ API 錯誤自動記錄和處理
- ✅ 支持導出和統計錯誤日誌
- ✅ 開發環境提供詳細調試信息
- ✅ 支持集成外部錯誤追踪服務
