# ArticleReviewModal 滾動問題調查報告

## 問題描述

**症狀**: ArticleReviewModal (文章審核模態框) 無法滾動,即使內容超過視窗高度

**影響範圍**:
- 解析審核 (Parsing) tab
- 校對審核 (Proofreading) tab
- 發布預覽 (Publish) tab

**環境**:
- Frontend: React 18 + TypeScript + Vite
- Deployed to: GCS bucket (https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html)
- Backend: FastAPI on Cloud Run

---

## 組件結構分析

### ArticleReviewModal 的 DOM 層級

```jsx
<Modal customContent={true} className="h-screen max-h-screen flex flex-col min-h-0">
  {/* Header - Fixed */}
  <div className="flex items-center justify-between px-6 py-4 border-b bg-white sticky top-0 z-10">
    ...
  </div>

  {/* Progress Stepper - Fixed */}
  <div className="px-6 py-4 bg-gray-50 border-b">
    <ReviewProgressStepper currentStep={currentStep} />
  </div>

  {/* Tabs Container - Should scroll */}
  <div className="flex-1 flex flex-col overflow-hidden min-h-0">
    <Tabs className="h-full flex flex-col min-h-0">
      {/* Tab Headers - Fixed */}
      <div className="px-6 pt-4 border-b bg-white flex-shrink-0">
        <TabsList>...</TabsList>
      </div>

      {/* Tab Content - SCROLLABLE AREA */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
        <TabsContent value="parsing" className="p-6 mt-0">
          <ParsingReviewPanel />
        </TabsContent>
        ...
      </div>
    </Tabs>
  </div>
</Modal>
```

### Modal 組件結構

```jsx
// src/components/ui/Modal.tsx
export const Modal = ({ customContent, className, children }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div className="fixed inset-0 bg-black bg-opacity-50" />

      {/* Modal Content */}
      <div className={cn('relative bg-white rounded-lg shadow-xl w-full', className)}>
        {customContent ? (
          children  // Direct children, no wrapper
        ) : (
          <div className="px-6 py-4">{children}</div>  // Default wrapper
        )}
      </div>
    </div>
  );
};
```

### Tabs 組件結構

```jsx
// src/components/ui/Tabs.tsx
export const Tabs = ({ className, children }) => (
  <div className={cn('w-full', className)}>
    {children}
  </div>
);

export const TabsContent = ({ value, className, children }) => {
  const { activeTab } = useTabsContext();
  if (activeTab !== value) return null;

  return (
    <div className={cn('ring-offset-white focus-visible:outline-none', className)}>
      {children}
    </div>
  );
};
```

---

## 嘗試的解決方案

### ❌ 嘗試 1: 添加 min-h-0 到 Modal
**時間**: 第一次嘗試
**文件**: `frontend/src/components/ArticleReview/ArticleReviewModal.tsx`
**改動**:
```jsx
<Modal className="h-screen max-h-screen flex flex-col min-h-0">
```

**結果**: 失敗
**原因**: Modal 本身不是問題,問題在於內部的 flexbox 層級

---

### ❌ 嘗試 2: 添加 customContent prop 到 Modal
**時間**: 部署 e503403
**文件**:
- `frontend/src/components/ui/Modal.tsx`
- `frontend/src/components/ArticleReview/ArticleReviewModal.tsx`

**改動**:
```jsx
// Modal.tsx
export interface ModalProps {
  customContent?: boolean;  // 新增
}

{customContent ? (
  children
) : (
  <div className="px-6 py-4">{children}</div>
)}

// ArticleReviewModal.tsx
<Modal customContent={true} />
```

**理由**: 移除 Modal 的默認 padding wrapper,避免破壞 flexbox 鏈

**結果**: 失敗
**原因**: 雖然移除了 wrapper,但滾動問題仍然存在

---

### ❌ 嘗試 3: 移除 TabsContent 的默認 mt-4 margin
**時間**: 部署 7a3b6dc
**文件**:
- `frontend/src/components/ui/Tabs.tsx`
- `frontend/src/components/ArticleReview/ArticleReviewModal.tsx`

**改動**:
```jsx
// Tabs.tsx - BEFORE
<div className={cn('mt-4 ring-offset-white focus-visible:outline-none', className)}>

// Tabs.tsx - AFTER
<div className={cn('ring-offset-white focus-visible:outline-none', className)}>

// ArticleReviewModal.tsx
<TabsContent value="parsing" className="p-6 mt-0">
```

**理由**: TabsContent 的 mt-4 可能破壞 flexbox 滾動鏈

**結果**: 失敗
**原因**: margin 不是根本問題

---

## 已排除的因素

### ✅ 後端連接問題
- **狀態**: 已解決
- **問題**: pgbouncer prepared statements 錯誤
- **解決**: 在 database.py 中設置 `statement_cache_size: 0`
- **相關 commits**: 70aae3a, 510a51f

### ✅ 前端 API 配置
- **狀態**: 已修復
- **問題**: `.env.production` 使用舊的後端 URL
- **解決**: 更新為新的 Cloud Run URL
- **當前 URL**: `https://cms-automation-backend-297291472291.us-east1.run.app`

---

## CSS Flexbox 滾動的必要條件

根據 CSS 規範,要讓 flexbox 子元素滾動,需要滿足:

### 1. 父元素必須有固定高度
```css
.parent {
  height: 100vh;  /* 或其他固定值 */
  display: flex;
  flex-direction: column;
}
```

### 2. 滾動容器必須是 flex 子元素
```css
.scroll-container {
  flex: 1;  /* 佔據剩餘空間 */
  overflow-y: auto;
  min-height: 0;  /* 關鍵!允許 flex 子元素縮小 */
}
```

### 3. 完整的 flexbox 鏈不能被破壞
- 所有中間層都必須參與 flexbox 佈局
- 不能有非 flex 的 wrapper div 打斷鏈條

---

## 當前 CSS 類分析

### Modal 容器
```css
className="h-screen max-h-screen flex flex-col min-h-0"
```
- ✅ `h-screen`: 固定高度 100vh
- ✅ `max-h-screen`: 限制最大高度
- ✅ `flex flex-col`: flexbox 容器,垂直方向
- ✅ `min-h-0`: 允許縮小

### Tabs 外層容器
```css
className="flex-1 flex flex-col overflow-hidden min-h-0"
```
- ✅ `flex-1`: 佔據剩餘空間
- ✅ `flex flex-col`: flexbox 容器
- ✅ `overflow-hidden`: 隱藏溢出
- ✅ `min-h-0`: 允許縮小

### Tabs 組件
```css
className="h-full flex flex-col min-h-0"
```
- ✅ `h-full`: 100% 高度
- ✅ `flex flex-col`: flexbox 容器
- ✅ `min-h-0`: 允許縮小

### 滾動容器
```css
className="flex-1 overflow-y-auto overflow-x-hidden min-h-0"
```
- ✅ `flex-1`: 佔據剩餘空間
- ✅ `overflow-y-auto`: 允許垂直滾動
- ✅ `overflow-x-hidden`: 隱藏水平溢出
- ✅ `min-h-0`: 允許縮小

### TabsContent
```css
className="p-6 mt-0"
```
- ✅ `p-6`: padding
- ✅ `mt-0`: 無上邊距

---

## 可能的根本原因

### 1. Modal 的固定定位和高度計算
Modal 使用 `fixed` 定位,其高度計算可能受到:
- 瀏覽器視窗大小
- `p-4` padding on the outer container
- `items-center justify-center` 的 flexbox 佈局

**疑點**: Modal 的實際渲染高度可能小於 `h-screen`,導致內部沒有足夠空間觸發滾動

### 2. Tabs 組件的包裝 div
Tabs 組件渲染一個 `<div className="w-full">`,這個 div:
- 只設置了 `width: 100%`
- **沒有設置 height 或 flex 相關屬性**
- 可能破壞了 flexbox 高度計算鏈

**疑點**: 即使傳入 `className="h-full flex flex-col"`,這些類是應用在 Tabs 的 root div 上,但這個 div 本身可能沒有正確繼承父容器的高度約束

### 3. TabsContent 的條件渲染
```jsx
if (activeTab !== value) return null;
```
當 tab 切換時,TabsContent 會完全卸載和重新掛載,這可能導致:
- 滾動位置丟失
- DOM 重新計算高度
- Flexbox 佈局重新計算

### 4. 多層 div 嵌套
從 Modal 到實際內容,有很多層 div:
```
Modal > div.relative > children >
Tabs > div.w-full >
滾動容器 > TabsContent > div.ring-offset >
ParsingReviewPanel
```

**疑點**: 某一層的 div 可能沒有正確傳遞高度約束

---

## 需要驗證的假設

### 假設 1: Modal 外層容器的影響
```jsx
<div className="fixed inset-0 z-50 flex items-center justify-center p-4">
  <div className="relative bg-white rounded-lg shadow-xl w-full max-w-full mx-4">
```

`items-center` 和 `justify-center` 可能導致 Modal 內容被居中,而不是填滿整個視窗。

**測試**: 移除 `items-center`,改為 `items-stretch`

### 假設 2: max-w-full 的限制
Modal 的 `size="full"` 映射到 `max-w-full mx-4`,這可能:
- 限制了寬度但沒有正確處理高度
- `mx-4` 的水平 margin 可能影響佈局

**測試**: 檢查 Modal size="full" 的實際樣式

### 假設 3: Tabs 組件沒有正確傳遞 flex 屬性
Tabs 的 root div 只有 `w-full`,沒有 `h-full` 或 `flex-1`。

**測試**: 強制 Tabs 內部 div 使用 `h-full`

### 假設 4: 瀏覽器特定問題
Safari 對 flexbox 和 `min-h-0` 的處理與 Chrome 不同。

**測試**: 在不同瀏覽器中測試

---

## 建議的調試步驟

### 1. 使用瀏覽器 DevTools 檢查實際渲染
```javascript
// 在 Console 中執行
const modal = document.querySelector('[role="dialog"]');
console.log('Modal height:', modal.offsetHeight);
console.log('Modal scrollHeight:', modal.scrollHeight);

const scrollContainer = modal.querySelector('.overflow-y-auto');
console.log('Scroll container height:', scrollContainer.offsetHeight);
console.log('Scroll container scrollHeight:', scrollContainer.scrollHeight);
console.log('Can scroll:', scrollContainer.scrollHeight > scrollContainer.offsetHeight);
```

### 2. 檢查 computed styles
在 DevTools 中選中滾動容器,查看:
- `height` 的計算值
- `overflow-y` 的計算值
- `flex` 相關屬性的計算值
- 父元素的 `height` 和 `flex` 屬性

### 3. 添加臨時背景色調試
```jsx
<div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0 bg-red-500">
```
確認這個 div 是否有正確的高度

### 4. 簡化測試
創建一個最小複現案例:
```jsx
<div className="h-screen flex flex-col">
  <div className="flex-shrink-0 p-4 bg-blue-500">Header</div>
  <div className="flex-1 overflow-y-auto min-h-0 bg-red-500">
    <div className="h-[2000px]">Long content</div>
  </div>
</div>
```

如果這個可以滾動,逐步添加層級,找出哪一層破壞了滾動。

---

## 相關文件

### 主要文件
- `frontend/src/components/ArticleReview/ArticleReviewModal.tsx` - 主要問題所在
- `frontend/src/components/ui/Modal.tsx` - Modal 基礎組件
- `frontend/src/components/ui/Tabs.tsx` - Tabs 基礎組件

### 相關 Commits
- `cc5d6cd` - 第一次嘗試添加 min-h-0
- `eee8934` - 修復組件 props (Badge, Button, Card)
- `e503403` - 添加 customContent prop 到 Modal
- `7a3b6dc` - 移除 TabsContent 的 mt-4

### 部署狀態
- Frontend URL: https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html
- Backend URL: https://cms-automation-backend-297291472291.us-east1.run.app
- 最新部署: 7a3b6dc (2025-11-16)

---

## 其他可能的解決方向

### 方案 A: 使用絕對定位代替 flexbox
```jsx
<div className="h-screen relative">
  <div className="absolute top-0 left-0 right-0 h-20">Header</div>
  <div className="absolute top-20 bottom-0 left-0 right-0 overflow-y-auto">
    Content
  </div>
</div>
```

### 方案 B: 使用 Grid 佈局代替 Flexbox
```jsx
<div className="h-screen grid grid-rows-[auto_auto_1fr]">
  <div>Header</div>
  <div>Progress</div>
  <div className="overflow-y-auto">Content</div>
</div>
```

### 方案 C: 使用固定高度計算
```jsx
<div style={{ height: 'calc(100vh - 200px)' }} className="overflow-y-auto">
  Content
</div>
```

### 方案 D: 重構 Modal 組件
完全重寫 Modal,使用 Radix UI 或 Headless UI 的 Dialog 組件,這些庫已經處理好了這類滾動問題。

---

## 總結

經過 3 次嘗試,問題仍未解決。CSS 類設置看起來都是正確的,但實際渲染時滾動仍然不工作。

**最可能的原因**:
1. Modal 的外層容器 flexbox 佈局 (`items-center justify-center`) 影響了內部高度計算
2. Tabs 組件的 wrapper div 沒有正確參與 flexbox 鏈
3. 某個隱藏的 CSS 規則或瀏覽器特定行為

**建議下一步**:
1. 使用 DevTools 詳細檢查每一層的實際高度和樣式
2. 創建最小複現案例,排除其他因素
3. 考慮使用替代方案 (Grid 佈局或第三方組件庫)
