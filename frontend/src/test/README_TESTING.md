# 前端測試指南

本項目使用 Vitest + React Testing Library 進行全面的前端測試。

## 目錄

1. [測試架構](#測試架構)
2. [運行測試](#運行測試)
3. [編寫測試](#編寫測試)
4. [測試類型](#測試類型)
5. [視覺測試 (E2E)](#視覺測試-e2e)
6. [邊緣情況測試](#邊緣情況測試)
7. [最佳實踐](#最佳實踐)
8. [測試覆蓋率](#測試覆蓋率)
9. [常見問題](#常見問題)

## 測試架構

### 技術棧

- **Vitest**: 快速的單元測試框架
- **React Testing Library**: React 組件測試
- **@testing-library/user-event**: 用戶交互模擬
- **@testing-library/jest-dom**: 額外的 DOM 斷言
- **jsdom**: 瀏覽器環境模擬

### 目錄結構

```
frontend/
├── src/
│   ├── test/
│   │   ├── setup.ts              # 測試環境設置
│   │   ├── testUtils.tsx         # 測試工具函數
│   │   ├── mockData.ts           # Mock 數據
│   │   └── README_TESTING.md     # 本文檔
│   ├── components/
│   │   └── __tests__/            # 組件測試
│   │       └── *.test.tsx
│   ├── services/
│   │   └── __tests__/            # API 服務測試
│   │       └── *.test.ts
│   ├── hooks/
│   │   └── __tests__/            # Hooks 測試
│   │       └── *.test.ts
│   └── utils/
│       └── __tests__/            # 工具函數測試
│           └── *.test.ts
└── vitest.config.ts              # Vitest 配置
```

## 運行測試

### 基本命令

```bash
# 運行所有測試
npm test

# 監視模式（自動重新運行）
npm test -- --watch

# 運行測試 UI
npm run test:ui

# 生成覆蓋率報告
npm run test:coverage

# 運行特定文件
npm test src/components/__tests__/ErrorBoundary.test.tsx

# 運行特定測試套件
npm test -- ErrorBoundary
```

### 調試測試

```bash
# 在瀏覽器中調試
npm run test:ui

# 使用 Node 調試器
node --inspect-brk node_modules/.bin/vitest
```

## 編寫測試

### 基本測試結構

```tsx
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderWithProviders, screen } from '../../test/testUtils';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  beforeEach(() => {
    // 每個測試前執行
  });

  afterEach(() => {
    // 每個測試後清理
    vi.clearAllMocks();
  });

  it('should render correctly', () => {
    renderWithProviders(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('should handle click events', async () => {
    const handleClick = vi.fn();
    const { user } = renderWithProviders(<MyComponent onClick={handleClick} />);

    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### 使用測試工具

```tsx
import {
  renderWithProviders,
  createMockAPIResponse,
  createMockPaginatedResponse,
  waitForAsync,
} from '../../test/testUtils';

// 渲染帶 providers 的組件
renderWithProviders(<MyComponent />);

// 創建 Mock API 響應
const mockResponse = createMockAPIResponse({ id: 1, name: 'Test' });

// 創建分頁響應
const mockPaginated = createMockPaginatedResponse([item1, item2]);

// 等待異步操作
await waitForAsync(100);
```

### 使用 Mock 數據

```tsx
import {
  mockArticle,
  mockArticles,
  mockPublishTask,
  mockUser,
} from '../../test/mockData';

// 使用預定義的 mock 數據
const article = mockArticle;

// 自定義 mock 數據
const customArticle = {
  ...mockArticle,
  title: 'Custom Title',
};
```

## 測試類型

### 1. 單元測試（Unit Tests）

測試單個函數或組件的獨立功能。

**示例：工具函數測試**

```tsx
import { describe, it, expect } from 'vitest';
import { formatDate, calculateReadTime } from '../utils';

describe('formatDate', () => {
  it('should format ISO date string correctly', () => {
    const result = formatDate('2024-01-01T00:00:00Z');
    expect(result).toBe('2024/01/01');
  });

  it('should handle invalid dates', () => {
    const result = formatDate('invalid');
    expect(result).toBe('Invalid Date');
  });
});

describe('calculateReadTime', () => {
  it('should calculate read time for article', () => {
    const content = 'word '.repeat(200); // 200 words
    const result = calculateReadTime(content);
    expect(result).toBe(1); // ~1 minute
  });
});
```

### 2. 組件測試（Component Tests）

測試組件的渲染、交互和狀態。

**示例：按鈕組件測試**

```tsx
import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen } from '../../test/testUtils';
import userEvent from '@testing-library/user-event';
import Button from '../Button';

describe('Button', () => {
  it('should render with text', () => {
    renderWithProviders(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('should call onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    renderWithProviders(<Button onClick={handleClick}>Click</Button>);

    await user.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    renderWithProviders(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('should show loading state', () => {
    renderWithProviders(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });
});
```

### 3. API 服務測試（Service Tests）

測試 API 服務的請求和響應處理。

**示例：Articles API 測試**

```tsx
import { describe, it, expect, vi } from 'vitest';
import { articlesAPI } from '../articles';
import { api } from '../api-client';
import { mockArticle, createMockAPIResponse } from '../../test/mockData';

vi.mock('../api-client');

describe('articlesAPI', () => {
  it('should fetch articles', async () => {
    const mockResponse = createMockAPIResponse([mockArticle]);
    (api.get as any).mockResolvedValue(mockResponse);

    const result = await articlesAPI.list();

    expect(api.get).toHaveBeenCalledWith('/api/v1/articles', { params: undefined });
    expect(result).toEqual(mockResponse);
  });

  it('should create article', async () => {
    const mockResponse = createMockAPIResponse(mockArticle);
    (api.post as any).mockResolvedValue(mockResponse);

    const data = { title: 'New Article', content: 'Content' };
    const result = await articlesAPI.create(data);

    expect(api.post).toHaveBeenCalledWith('/api/v1/articles', data);
    expect(result).toEqual(mockResponse);
  });
});
```

### 4. Hooks 測試（Hook Tests）

測試自定義 React Hooks。

**示例：usePolling Hook 測試**

```tsx
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { usePolling } from '../usePolling';

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should poll at specified interval', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    renderHook(() => usePolling(callback, { interval: 1000 }));

    // Initial call
    await waitFor(() => {
      expect(callback).toHaveBeenCalledTimes(1);
    });

    // After 1 second
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    await waitFor(() => {
      expect(callback).toHaveBeenCalledTimes(2);
    });
  });

  it('should stop polling when stop() is called', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() => usePolling(callback, { interval: 1000 }));

    act(() => {
      result.current.stop();
    });

    expect(result.current.isPolling).toBe(false);
  });
});
```

### 5. 集成測試（Integration Tests）

測試多個組件或模塊之間的交互。

**示例：表單提交流程測試**

```tsx
import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, screen, waitFor } from '../../test/testUtils';
import userEvent from '@testing-library/user-event';
import ArticleForm from '../ArticleForm';
import { articlesAPI } from '../../services';

vi.mock('../../services/articles');

describe('ArticleForm Integration', () => {
  it('should submit form and show success message', async () => {
    const user = userEvent.setup();
    const mockCreate = vi.fn().mockResolvedValue({
      success: true,
      data: { id: 1, title: 'New Article' },
    });

    (articlesAPI.create as any) = mockCreate;

    renderWithProviders(<ArticleForm />);

    // Fill form
    await user.type(screen.getByLabelText('Title'), 'New Article');
    await user.type(screen.getByLabelText('Content'), 'Article content');

    // Submit
    await user.click(screen.getByRole('button', { name: /submit/i }));

    // Verify API call
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        title: 'New Article',
        content: 'Article content',
      });
    });

    // Verify success message
    expect(await screen.findByText(/success/i)).toBeInTheDocument();
  });

  it('should show validation errors', async () => {
    const user = userEvent.setup();

    renderWithProviders(<ArticleForm />);

    // Submit without filling
    await user.click(screen.getByRole('button', { name: /submit/i }));

    // Check for validation errors
    expect(await screen.findByText(/title is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/content is required/i)).toBeInTheDocument();
  });
});
```

## 視覺測試 (E2E)

本項目使用 Playwright 進行端對端視覺測試，確保 UI 在各種狀態和視口下正確顯示。

### 技術棧

- **Playwright**: 瀏覽器自動化測試框架
- **Visual Test Helpers**: 自定義視覺測試輔助函數

### 目錄結構

```
frontend/e2e/
├── visual/
│   ├── worklist.visual.spec.ts       # 首頁視覺測試
│   ├── article-review.visual.spec.ts # 文章審核視覺測試
│   ├── proofreading.visual.spec.ts   # 校對審核視覺測試
│   └── settings.visual.spec.ts       # 設定頁視覺測試
├── edge-cases/
│   ├── empty-states.spec.ts          # 空狀態測試
│   ├── error-handling.spec.ts        # 錯誤處理測試
│   ├── batch-operations.spec.ts      # 批量操作測試
│   ├── navigation-flow.spec.ts       # 導航流程測試
│   ├── responsive.spec.ts            # 響應式測試
│   └── extreme-data.spec.ts          # 極端數據測試
└── utils/
    ├── test-helpers.ts               # 基礎測試輔助函數
    └── visual-test-helpers.ts        # 視覺測試輔助函數
```

### 運行視覺測試

```bash
# 運行所有 E2E 測試
npx playwright test

# 運行視覺測試
npx playwright test e2e/visual/

# 運行邊緣情況測試
npx playwright test e2e/edge-cases/

# 運行特定測試文件
npx playwright test e2e/visual/worklist.visual.spec.ts

# 以 UI 模式運行
npx playwright test --ui

# 對本地開發環境測試
TEST_LOCAL=1 npx playwright test
```

### 視覺測試輔助函數

```typescript
import {
  VIEWPORTS,           // 預設視口尺寸
  waitForAnimations,   // 等待動畫完成
  captureScreenshot,   // 截圖保存
  expectToast,         // 驗證 Toast 通知
  verifyEmptyState,    // 驗證空狀態顯示
  testResponsive,      // 響應式測試輔助
} from '../utils/visual-test-helpers';

// 預設視口
const viewports = {
  mobile: { width: 320, height: 568 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1280, height: 800 },
  desktopLarge: { width: 1920, height: 1080 },
  desktopUltrawide: { width: 2560, height: 1440 },
};
```

### 視覺測試示例

```typescript
import { test, expect } from '@playwright/test';
import { VIEWPORTS, waitForAnimations, captureScreenshot } from '../utils/visual-test-helpers';

test.describe('Worklist Page Visual Tests', () => {
  test('should display dashboard correctly on mobile', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto(BASE_URL);
    await waitForAnimations(page);

    await expect(page.locator('text=CMS Automation System')).toBeVisible();
    await captureScreenshot(page, 'worklist-mobile');
  });
});
```

## 邊緣情況測試

邊緣情況測試覆蓋各種非正常使用場景，確保應用的健壯性。

### 測試類別

#### 1. 空狀態測試 (empty-states.spec.ts)

測試數據為空時的 UI 表現：
- 無文章時的列表顯示
- 無校對問題時的面板
- 無 AI 建議時的 SEO 區塊
- 搜索無結果時的提示

```typescript
test('should display appropriate message when filtering returns no results', async ({ page }) => {
  const searchInput = page.locator('input[placeholder*="Search"]');
  await searchInput.fill('xyznonexistent123');
  await waitForAnimations(page);

  const noResultsIndicator = page.locator('text=/No articles|沒有文章/i');
  if (await noResultsIndicator.count() > 0) {
    await expect(noResultsIndicator.first()).toBeVisible();
  }
});
```

#### 2. 錯誤處理測試 (error-handling.spec.ts)

測試各種錯誤場景：
- API 500 錯誤
- 網絡超時
- 無效 JSON 響應
- Session 過期

```typescript
test('should handle API failure gracefully', async ({ page }) => {
  await page.route('**/api/**', (route) => {
    route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server Error' }) });
  });

  await page.goto(BASE_URL);
  // 驗證應用不崩潰，顯示錯誤信息
});
```

#### 3. 批量操作測試 (batch-operations.spec.ts)

測試批量接受/拒絕功能：
- Toast 反饋顯示
- 快速連續點擊防護
- 狀態更新正確性
- 空狀態處理

```typescript
test('should show toast when accepting all issues', async ({ page }) => {
  // 導航到校對面板
  const acceptAllButton = page.locator('button:has-text("全部接受")');
  await acceptAllButton.click();

  // 驗證 Toast 顯示
  await expectToast(page, /已接受.*個問題/);
});
```

#### 4. 響應式測試 (responsive.spec.ts)

測試不同視口尺寸：
- 手機 (320px)
- 平板 (768px)
- 桌面 (1280px)
- 超寬屏 (2560px)
- 動態視口調整

```typescript
test('should stack panels on mobile', async ({ page }) => {
  await page.setViewportSize(VIEWPORTS.mobile);
  // 驗證移動端布局適應
});
```

#### 5. 極端數據測試 (extreme-data.spec.ts)

測試極端數據場景：
- 超長標題 (100+ 字符)
- 大量問題 (50+)
- 特殊字符和 Unicode
- HTML 注入防護

```typescript
test('should handle unicode characters in search', async ({ page }) => {
  const testCases = ['日本語テスト', '한국어 테스트', 'emoji 🎉 test'];

  for (const text of testCases) {
    await searchInput.fill(text);
    await waitForAnimations(page);
    // 驗證應用不崩潰
  }
});
```

#### 6. 導航流程測試 (navigation-flow.spec.ts)

測試導航和工作流：
- 步驟切換數據持久性
- Modal 關閉後狀態保存
- 瀏覽器返回按鈕處理
- 快速導航切換

```typescript
test('should preserve data when switching steps', async ({ page }) => {
  // 在步驟 1 輸入數據
  // 切換到步驟 2
  // 返回步驟 1
  // 驗證數據仍然存在
});
```

### 測試優先級

| 優先級 | 測試類別 | 描述 |
|--------|----------|------|
| 高 | 錯誤處理 | 確保應用不會因錯誤崩潰 |
| 高 | 空狀態 | 確保空數據時的用戶體驗 |
| 中 | 批量操作 | 確保核心功能正常 |
| 中 | 響應式 | 確保多設備兼容性 |
| 低 | 極端數據 | 邊界情況覆蓋 |
| 低 | 導航流程 | 工作流完整性 |

## 最佳實踐

### 1. 測試用戶行為，而非實現細節

```tsx
// ❌ 錯誤：測試實現細節
it('should call useState', () => {
  const spy = vi.spyOn(React, 'useState');
  renderWithProviders(<MyComponent />);
  expect(spy).toHaveBeenCalled();
});

// ✅ 正確：測試用戶可見的行為
it('should show error message when form is invalid', async () => {
  const user = userEvent.setup();
  renderWithProviders(<MyComponent />);

  await user.click(screen.getByRole('button', { name: /submit/i }));

  expect(screen.getByText(/error message/i)).toBeInTheDocument();
});
```

### 2. 使用語義化查詢

```tsx
// 優先級排序（從高到低）：

// 1. getByRole - 最推薦
screen.getByRole('button', { name: /submit/i });
screen.getByRole('textbox', { name: /username/i });

// 2. getByLabelText - 表單元素
screen.getByLabelText('Email');

// 3. getByPlaceholderText
screen.getByPlaceholderText('Enter your name');

// 4. getByText
screen.getByText('Welcome');

// 5. getByDisplayValue
screen.getByDisplayValue('Current value');

// 6. getByAltText - 圖片
screen.getByAltText('Profile picture');

// 7. getByTitle
screen.getByTitle('Close');

// 最後選擇：getByTestId（僅當其他方法都不可行時）
screen.getByTestId('custom-element');
```

### 3. 使用 waitFor 處理異步操作

```tsx
import { waitFor } from '@testing-library/react';

// ✅ 等待元素出現
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// ✅ 等待元素消失
await waitFor(() => {
  expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
});

// ✅ 使用 findBy（內置 waitFor）
const element = await screen.findByText('Loaded');
```

### 4. 模擬 API 調用

```tsx
import { vi } from 'vitest';

// Mock 整個模塊
vi.mock('../services/api', () => ({
  fetchData: vi.fn(),
}));

// Mock 特定函數
const mockFetch = vi.fn().mockResolvedValue({ data: 'test' });

// Mock 失敗情況
mockFetch.mockRejectedValue(new Error('API Error'));

// Mock 不同的返回值
mockFetch
  .mockResolvedValueOnce({ data: 'first' })
  .mockResolvedValueOnce({ data: 'second' });
```

### 5. 清理和隔離測試

```tsx
describe('MyComponent', () => {
  beforeEach(() => {
    // 設置每個測試需要的狀態
    vi.clearAllMocks();
  });

  afterEach(() => {
    // 清理
    vi.restoreAllMocks();
  });

  it('test 1', () => {
    // 測試 1 不會影響測試 2
  });

  it('test 2', () => {
    // 獨立的測試
  });
});
```

### 6. 測試錯誤情況

```tsx
describe('Error Handling', () => {
  it('should display error message on API failure', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));

    renderWithProviders(<MyComponent fetchData={mockFetch} />);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('should handle empty data gracefully', () => {
    renderWithProviders(<MyComponent data={[]} />);
    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });
});
```

### 7. 使用自定義渲染函數

```tsx
// testUtils.tsx
export function renderWithProviders(ui, options) {
  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    ),
    ...options,
  });
}

// 使用
renderWithProviders(<MyComponent />);
```

## 測試覆蓋率

### 查看覆蓋率報告

```bash
npm run test:coverage
```

報告會生成在 `coverage/` 目錄：
- `coverage/index.html` - HTML 報告
- `coverage/lcov.info` - LCOV 格式
- `coverage/coverage-final.json` - JSON 格式

### 覆蓋率目標

項目設置的覆蓋率目標（在 `vitest.config.ts` 中配置）：

- **Lines**: 70%
- **Functions**: 70%
- **Branches**: 70%
- **Statements**: 70%

### 排除文件

以下文件類型不計入覆蓋率：
- `node_modules/`
- `src/test/`
- `**/*.d.ts`
- `**/*.config.*`
- `**/mockData/**`
- `src/main.tsx`

## 常見問題

### Q1: 測試中如何處理 React Query？

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderWithProviders } from '../../test/testUtils';

// 已在 testUtils 中處理
renderWithProviders(<MyComponent />);

// 或手動創建
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

render(
  <QueryClientProvider client={queryClient}>
    <MyComponent />
  </QueryClientProvider>
);
```

### Q2: 如何測試路由導航？

```tsx
import { BrowserRouter } from 'react-router-dom';
import { renderWithProviders } from '../../test/testUtils';

// 已在 testUtils 中包含 BrowserRouter
renderWithProviders(<MyComponent />);

// 驗證導航
const link = screen.getByRole('link', { name: /home/i });
expect(link).toHaveAttribute('href', '/');
```

### Q3: 如何測試文件上傳？

```tsx
it('should handle file upload', async () => {
  const user = userEvent.setup();
  const file = new File(['content'], 'test.txt', { type: 'text/plain' });

  renderWithProviders(<FileUpload />);

  const input = screen.getByLabelText(/upload/i);
  await user.upload(input, file);

  expect(input.files[0]).toStrictEqual(file);
  expect(input.files).toHaveLength(1);
});
```

### Q4: 如何處理定時器？

```tsx
import { vi } from 'vitest';

describe('Timer Tests', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should trigger after timeout', () => {
    const callback = vi.fn();
    setTimeout(callback, 1000);

    // 快進時間
    vi.advanceTimersByTime(1000);

    expect(callback).toHaveBeenCalled();
  });
});
```

### Q5: 如何測試 localStorage？

```tsx
import { mockLocalStorage } from '../../test/testUtils';

it('should save to localStorage', () => {
  const localStorage = mockLocalStorage();
  Object.defineProperty(window, 'localStorage', {
    value: localStorage,
  });

  // 測試代碼
  window.localStorage.setItem('key', 'value');

  expect(localStorage.setItem).toHaveBeenCalledWith('key', 'value');
});
```

### Q6: 如何測試錯誤邊界（Error Boundary）？

```tsx
it('should catch errors', () => {
  // 抑制控制台錯誤
  vi.spyOn(console, 'error').mockImplementation(() => {});

  const ThrowError = () => {
    throw new Error('Test error');
  };

  renderWithProviders(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText(/error occurred/i)).toBeInTheDocument();
});
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage/lcov.info
```

## 資源鏈接

- [Vitest 官方文檔](https://vitest.dev/)
- [React Testing Library 文檔](https://testing-library.com/react)
- [Jest DOM 匹配器](https://github.com/testing-library/jest-dom)
- [User Event 文檔](https://testing-library.com/docs/user-event/intro)

## 總結

本測試框架提供：

- ✅ 快速的測試執行（Vitest）
- ✅ 完整的組件測試支持
- ✅ API 服務集成測試
- ✅ Custom Hooks 測試
- ✅ Mock 數據和工具函數
- ✅ 70% 覆蓋率目標
- ✅ CI/CD 就緒

遵循最佳實踐，編寫可維護的測試，確保代碼質量！
