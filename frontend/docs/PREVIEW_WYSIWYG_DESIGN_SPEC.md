# 預覽區域 WYSIWYG 渲染系統設計規格

> **版本**: 1.0
> **日期**: 2025-12-19
> **狀態**: 設計中

---

## 一、問題分析

### 1.1 當前技術債

| 問題類型 | 影響組件 | 嚴重程度 | 描述 |
|---------|---------|---------|------|
| **HTML 源碼顯示** | FinalContentPreview, RuleTester/DiffViewer | 🔴 高 | 直接使用 `dangerouslySetInnerHTML` 顯示原始 HTML，用戶看到 `<p>`, `<span>` 等標籤 |
| **字體異常不可見** | 所有預覽組件 | 🔴 高 | Google Docs 污染的 `font-family` 屬性隱藏在內聯樣式中，無法識別 |
| **格式錯誤隱藏** | ProofreadingPreviewSection | 🟡 中 | 嵌套標籤、空標籤等問題在源碼模式下難以發現 |
| **中文字體回退** | DiffViewSection | 🟡 中 | 當指定字體不存在時，無提示地回退到系統字體 |

### 1.2 用戶痛點場景

```
場景 1: 編輯從 Google Docs 複製文章
─────────────────────────────────────
用戶看到: <span style="font-family: 'Times New Roman'">文章內容</span>
期望看到: 文章內容 ⚠️ [字體異常: Times New Roman]

場景 2: HTML 格式錯誤
─────────────────────
用戶看到: <p><p>重複段落</p></p>
期望看到: 重複段落 ⚠️ [嵌套錯誤]

場景 3: 空白標籤
───────────────
用戶看到: <span style="color: red"></span>
期望看到: (隱藏空標籤) 或 ⚠️ [空標籤]
```

---

## 二、設計目標

### 2.1 核心目標

1. **WYSIWYG 渲染**: 所見即所得，渲染 HTML 而非顯示源碼
2. **字體異常檢測**: 自動識別非標準字體並視覺化標註
3. **格式問題提示**: 檢測並高亮常見 HTML 格式錯誤
4. **模式切換**: 支持「預覽模式」與「源碼模式」一鍵切換

### 2.2 設計原則

| 原則 | 描述 |
|-----|------|
| **非侵入式** | 異常標註不干擾正常閱讀流程 |
| **漸進揭示** | 默認顯示渲染結果，懸停/點擊時顯示詳情 |
| **一致性** | 所有預覽組件使用統一的渲染引擎 |
| **可訪問性** | 支持鍵盤導航和屏幕閱讀器 |

---

## 三、架構設計

### 3.1 組件架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    WYSIWYGPreviewProvider                       │
│  (Context: 字體配置、異常規則、全局設置)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SafeHtmlRenderer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ HtmlParser  │→│FontAnalyzer │→│IssueMarker  │             │
│  │ (解析HTML)  │  │ (分析字體)  │  │ (標記問題)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ PreviewMode     │ │ SourceMode      │ │ DiffMode        │
│ (渲染視圖)       │ │ (源碼視圖)       │ │ (對比視圖)       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 3.2 數據流

```typescript
// 輸入: 原始 HTML
const rawHtml = '<p style="font-family: Times New Roman">內容</p>';

// 處理流程
ParsedHtml → FontAnalysis → IssueDetection → RenderOutput

// 輸出: 渲染結果 + 問題列表
{
  renderedContent: ReactNode,
  issues: [
    { type: 'font', severity: 'warning', element: 'p', font: 'Times New Roman', position: {...} }
  ],
  stats: { fonts: ['Times New Roman'], issues: 1 }
}
```

---

## 四、核心組件設計

### 4.1 SafeHtmlRenderer 組件

```typescript
interface SafeHtmlRendererProps {
  html: string;
  mode: 'preview' | 'source' | 'hybrid';
  showIssues?: boolean;
  allowedFonts?: string[];
  onIssueClick?: (issue: HtmlIssue) => void;
  className?: string;
}

interface HtmlIssue {
  id: string;
  type: 'font' | 'nesting' | 'empty' | 'deprecated' | 'accessibility';
  severity: 'error' | 'warning' | 'info';
  message: string;
  element: string;
  position: { start: number; end: number };
  suggestion?: string;
}
```

### 4.2 字體分析器

```typescript
// 允許的標準字體列表
const ALLOWED_FONTS = [
  // 系統字體
  '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto',
  // 中文字體
  'Noto Sans SC', 'Noto Sans TC', 'Microsoft YaHei', 'PingFang SC',
  'Hiragino Sans GB', 'WenQuanYi Micro Hei',
  // 通用字體
  'sans-serif', 'serif', 'monospace',
  // 網頁安全字體
  'Arial', 'Helvetica', 'Georgia', 'Verdana'
];

// 已知問題字體（通常來自 Office/Google Docs）
const PROBLEMATIC_FONTS = [
  'Times New Roman',     // Word 默認
  'Calibri',             // Office 默認
  'Cambria',             // Office 標題
  'Comic Sans MS',       // 非專業
  'Courier New',         // 等寬字體誤用
  'SimSun', '宋体',       // 印刷字體不適合屏幕
  'SimHei', '黑体',       // 可能缺失
];
```

### 4.3 視覺化標註設計

#### 4.3.1 字體異常標註

```
┌──────────────────────────────────────────────────────────┐
│  這是一段正常內容，使用系統默認字體顯示。                    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 這段內容使用了異常字體 ⚠️                        │    │
│  │ ──────────────────────────                      │    │
│  │ │ 🔤 字體: Times New Roman                      │    │
│  │ │ ⚡ 建議: 移除內聯樣式或替換為系統字體           │    │
│  │ │ 🔧 [一鍵修復]  [忽略]                         │    │
│  │ └────────────────────────────────────────────── │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  後續的正常內容繼續顯示...                                │
└──────────────────────────────────────────────────────────┘
```

#### 4.3.2 格式錯誤標註

```
嵌套錯誤示例:
┌──────────────────────────────────────────────────────────┐
│  這是正常段落                                            │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 重複段落內容 ⚠️ [嵌套 <p> 標籤]                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  這是另一個正常段落                                       │
└──────────────────────────────────────────────────────────┘

空標籤示例:
┌──────────────────────────────────────────────────────────┐
│  正常內容 [空] 後續內容                                   │
│            ↑                                             │
│        ⚠️ 空的 <span> 標籤                              │
└──────────────────────────────────────────────────────────┘
```

### 4.4 模式切換 UI

```
┌─────────────────────────────────────────────────────────────┐
│  內容預覽                                    ┌───────────┐  │
│                                              │ 👁️ 預覽   │  │
│                                              │ </> 源碼  │  │
│                                              │ ⚡ 混合   │  │
│                                              └───────────┘  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [預覽模式]                                                 │
│  ─────────                                                  │
│  這是渲染後的文章內容，字體異常會以黃色底色標註。              │
│                                                             │
│  ┌────────────────────────────────────────┐                │
│  │ 這段文字使用了 Times New Roman ⚠️      │                │
│  └────────────────────────────────────────┘                │
│                                                             │
│  [源碼模式]                                                 │
│  ─────────                                                  │
│  <p>這是渲染後的文章內容...</p>                             │
│  <p style="font-family: Times New Roman">                  │
│    這段文字使用了 Times New Roman                          │
│  </p>                                                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ⚠️ 發現 2 個問題: 1 個字體異常, 1 個空標籤                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、受影響組件改造計劃

### 5.1 組件改造矩陣

| 組件 | 當前渲染方式 | 改造方案 | 優先級 |
|-----|-------------|---------|-------|
| `FinalContentPreview` | dangerouslySetInnerHTML | 替換為 SafeHtmlRenderer | P0 |
| `ProofreadingPreviewSection` | React 組件 | 整合 FontAnalyzer | P1 |
| `ProofreadingArticleContent` | ReactMarkdown | 添加 WYSIWYG 模式 | P1 |
| `DiffViewSection` | react-diff-viewer | 添加字體標註層 | P2 |
| `RuleTester/DiffViewer` | dangerouslySetInnerHTML | 替換為 SafeHtmlRenderer | P2 |
| `ContentComparisonCard` | 純文本 | 添加格式預覽選項 | P3 |

### 5.2 新增組件列表

```
src/components/common/
├── SafeHtmlRenderer/
│   ├── index.tsx                 # 主組件
│   ├── HtmlParser.ts             # HTML 解析器
│   ├── FontAnalyzer.ts           # 字體分析器
│   ├── IssueDetector.ts          # 問題檢測器
│   ├── IssueMarker.tsx           # 問題標記組件
│   ├── ModeToggle.tsx            # 模式切換按鈕
│   ├── IssueSummary.tsx          # 問題摘要欄
│   └── types.ts                  # 類型定義
│
├── FontBadge/
│   ├── index.tsx                 # 字體標籤組件
│   └── FontTooltip.tsx           # 字體詳情 Tooltip
│
└── PreviewToolbar/
    ├── index.tsx                 # 預覽工具欄
    └── ViewModeSelector.tsx      # 視圖模式選擇器
```

---

## 六、字體檢測規則

### 6.1 檢測邏輯

```typescript
interface FontCheckResult {
  isValid: boolean;
  fontFamily: string;
  category: 'system' | 'chinese' | 'web-safe' | 'problematic' | 'unknown';
  severity: 'ok' | 'warning' | 'error';
  message?: string;
  suggestion?: string;
}

function checkFont(fontFamily: string): FontCheckResult {
  // 1. 解析 font-family 值（可能是逗號分隔的列表）
  const fonts = parseFontFamily(fontFamily);

  // 2. 檢查主字體
  const primaryFont = fonts[0];

  // 3. 分類判斷
  if (ALLOWED_FONTS.includes(primaryFont)) {
    return { isValid: true, category: 'system', severity: 'ok', ... };
  }

  if (PROBLEMATIC_FONTS.includes(primaryFont)) {
    return {
      isValid: false,
      category: 'problematic',
      severity: 'warning',
      message: `"${primaryFont}" 可能導致跨平台顯示不一致`,
      suggestion: '建議移除內聯字體樣式，使用系統默認字體'
    };
  }

  // 4. 未知字體
  return {
    isValid: false,
    category: 'unknown',
    severity: 'info',
    message: `未識別的字體: "${primaryFont}"`,
    suggestion: '請確認此字體在目標平台上可用'
  };
}
```

### 6.2 檢測觸發場景

| 場景 | 觸發條件 | 檢測範圍 |
|-----|---------|---------|
| **內聯樣式** | `style="font-family: ..."` | 單個元素 |
| **CSS 類** | 引用含 font-family 的類 | 需要 CSS 解析 |
| **繼承字體** | 父元素設置字體 | 遞歸檢查 |
| **Google Docs 污染** | 特定 class 名模式 | 模式匹配 |

### 6.3 Google Docs 污染模式

```typescript
// Google Docs 常見的污染模式
const GDOCS_PATTERNS = [
  /style="[^"]*font-family:\s*['"]?(?:Times New Roman|Arial|Calibri)/i,
  /class="[^"]*(?:c\d+|p\d+)/,  // Google Docs 生成的類名
  /style="[^"]*(?:orphans|widows|text-indent|line-height:\s*\d+(?:\.\d+)?;)/i,
  /<span[^>]*style="[^"]*"[^>]*><\/span>/,  // 空的樣式 span
];

function detectGDocsContamination(html: string): boolean {
  return GDOCS_PATTERNS.some(pattern => pattern.test(html));
}
```

---

## 七、視覺測試方案

### 7.1 測試場景矩陣

| 測試場景 | 輸入 | 預期結果 |
|---------|------|---------|
| 正常 HTML | `<p>普通文字</p>` | 正常渲染，無警告 |
| Times New Roman | `<p style="font-family: Times New Roman">文字</p>` | 渲染 + 黃色標註 + Tooltip |
| 嵌套 `<p>` | `<p><p>內容</p></p>` | 渲染 + 紅色標註 |
| 空 `<span>` | `<span style="color:red"></span>` | 隱藏或顯示佔位符 |
| Google Docs 導入 | 完整的 GDocs HTML | 清理 + 多處標註 |
| 混合字體 | 多種字體混用 | 每種異常分別標註 |

### 7.2 視覺回歸測試

```typescript
// tests/visual/preview-wysiwyg.spec.ts

import { test, expect } from '@playwright/test';

test.describe('WYSIWYG Preview Visual Tests', () => {

  test('renders clean HTML without issues', async ({ page }) => {
    await page.goto('/test/preview?html=<p>正常內容</p>');
    await expect(page.locator('.preview-content')).toHaveScreenshot('clean-html.png');
    await expect(page.locator('.issue-count')).toHaveText('0 個問題');
  });

  test('highlights Times New Roman font', async ({ page }) => {
    const html = encodeURIComponent('<p style="font-family: Times New Roman">異常字體</p>');
    await page.goto(`/test/preview?html=${html}`);

    // 檢查黃色高亮
    await expect(page.locator('.font-issue-highlight')).toBeVisible();
    await expect(page.locator('.font-issue-highlight')).toHaveCSS('background-color', 'rgb(254, 243, 199)');

    // 檢查 Tooltip
    await page.hover('.font-issue-highlight');
    await expect(page.locator('.font-tooltip')).toBeVisible();
    await expect(page.locator('.font-tooltip')).toContainText('Times New Roman');

    // 截圖對比
    await expect(page.locator('.preview-content')).toHaveScreenshot('times-new-roman.png');
  });

  test('detects nested paragraph tags', async ({ page }) => {
    const html = encodeURIComponent('<p><p>嵌套段落</p></p>');
    await page.goto(`/test/preview?html=${html}`);

    await expect(page.locator('.nesting-issue')).toBeVisible();
    await expect(page.locator('.issue-count')).toContainText('1 個問題');
  });

  test('mode toggle switches between preview and source', async ({ page }) => {
    await page.goto('/test/preview?html=<p>測試內容</p>');

    // 默認預覽模式
    await expect(page.locator('.preview-mode')).toBeVisible();

    // 切換到源碼模式
    await page.click('[data-testid="source-mode-btn"]');
    await expect(page.locator('.source-mode')).toBeVisible();
    await expect(page.locator('.source-mode')).toContainText('<p>');

    // 截圖對比
    await expect(page.locator('.preview-container')).toHaveScreenshot('source-mode.png');
  });

  test('Google Docs contamination detection', async ({ page }) => {
    const gdocsHtml = `
      <p class="c1" style="font-family: 'Times New Roman'; orphans: 2; widows: 2;">
        <span class="c0">Google Docs 內容</span>
      </p>
    `;
    await page.goto(`/test/preview?html=${encodeURIComponent(gdocsHtml)}`);

    // 應該檢測到多個問題
    await expect(page.locator('.issue-count')).toContainText(/\d+ 個問題/);

    // 應該有 GDocs 污染警告
    await expect(page.locator('.gdocs-warning')).toBeVisible();
  });
});
```

### 7.3 單元測試

```typescript
// tests/unit/FontAnalyzer.test.ts

import { checkFont, parseFontFamily, detectGDocsContamination } from '../FontAnalyzer';

describe('FontAnalyzer', () => {

  describe('checkFont', () => {
    it('accepts system fonts', () => {
      expect(checkFont('-apple-system').isValid).toBe(true);
      expect(checkFont('Segoe UI').isValid).toBe(true);
    });

    it('warns about Times New Roman', () => {
      const result = checkFont('Times New Roman');
      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('warning');
      expect(result.category).toBe('problematic');
    });

    it('accepts Chinese fonts', () => {
      expect(checkFont('Noto Sans SC').isValid).toBe(true);
      expect(checkFont('Microsoft YaHei').isValid).toBe(true);
    });
  });

  describe('parseFontFamily', () => {
    it('parses single font', () => {
      expect(parseFontFamily('Arial')).toEqual(['Arial']);
    });

    it('parses font stack', () => {
      expect(parseFontFamily('"Segoe UI", Arial, sans-serif'))
        .toEqual(['Segoe UI', 'Arial', 'sans-serif']);
    });
  });

  describe('detectGDocsContamination', () => {
    it('detects orphans/widows style', () => {
      expect(detectGDocsContamination('<p style="orphans: 2">')).toBe(true);
    });

    it('detects class pattern', () => {
      expect(detectGDocsContamination('<span class="c1 c2">')).toBe(true);
    });
  });
});
```

---

## 八、實現路線圖

### Phase 1: 核心渲染引擎 (Week 1-2)

- [ ] 創建 `SafeHtmlRenderer` 組件框架
- [ ] 實現 `HtmlParser` 解析器
- [ ] 實現 `FontAnalyzer` 字體分析器
- [ ] 創建 `IssueMarker` 標記組件
- [ ] 單元測試覆蓋

### Phase 2: 視覺標註系統 (Week 2-3)

- [ ] 設計並實現 `FontBadge` 組件
- [ ] 設計並實現 `FontTooltip` 組件
- [ ] 實現模式切換 UI
- [ ] 實現問題摘要欄
- [ ] 視覺回歸測試

### Phase 3: 組件遷移 (Week 3-4)

- [ ] 遷移 `FinalContentPreview`
- [ ] 遷移 `ProofreadingPreviewSection`
- [ ] 遷移 `ProofreadingArticleContent`
- [ ] 遷移 `DiffViewSection`
- [ ] 整合測試

### Phase 4: 優化與文檔 (Week 4)

- [ ] 性能優化（大文檔處理）
- [ ] 無障礙優化
- [ ] 文檔完善
- [ ] 用戶指南

---

## 九、API 參考

### 9.1 SafeHtmlRenderer

```typescript
import { SafeHtmlRenderer } from '@/components/common/SafeHtmlRenderer';

<SafeHtmlRenderer
  html={articleContent}
  mode="preview"
  showIssues={true}
  allowedFonts={['Noto Sans SC', 'Microsoft YaHei']}
  onIssueClick={(issue) => console.log('Issue clicked:', issue)}
  className="article-preview"
/>
```

### 9.2 FontAnalyzer (獨立使用)

```typescript
import { FontAnalyzer } from '@/components/common/SafeHtmlRenderer/FontAnalyzer';

const analyzer = new FontAnalyzer({
  allowedFonts: [...],
  problematicFonts: [...]
});

const results = analyzer.analyze(htmlContent);
// results: { fonts: FontCheckResult[], issues: HtmlIssue[] }
```

### 9.3 Hooks

```typescript
import { useHtmlAnalysis } from '@/hooks/useHtmlAnalysis';

const {
  issues,
  fonts,
  isGDocsContaminated,
  cleanHtml
} = useHtmlAnalysis(rawHtml);
```

---

## 十、設計資源

### 10.1 顏色規範

| 用途 | 顏色 | Hex | Tailwind |
|-----|------|-----|----------|
| 字體警告背景 | 淺黃 | #FEF3C7 | amber-100 |
| 字體警告邊框 | 琥珀 | #F59E0B | amber-500 |
| 嵌套錯誤背景 | 淺紅 | #FEE2E2 | red-100 |
| 嵌套錯誤邊框 | 紅色 | #EF4444 | red-500 |
| 信息提示背景 | 淺藍 | #DBEAFE | blue-100 |
| 正常內容 | 灰色 | #374151 | gray-700 |

### 10.2 圖標

- ⚠️ 警告 (font-issue)
- 🔤 字體 (font-family)
- 🔧 修復 (quick-fix)
- 👁️ 預覽模式
- </> 源碼模式
- ⚡ 混合模式

---

## 附錄 A: Google Docs HTML 清理規則

```typescript
const GDOCS_CLEANUP_RULES = [
  // 移除空 span
  { pattern: /<span[^>]*>\s*<\/span>/g, replacement: '' },

  // 移除 orphans/widows 樣式
  { pattern: /(?:orphans|widows):\s*\d+;?\s*/g, replacement: '' },

  // 移除 Google Docs 類名
  { pattern: /\s*class="[^"]*(?:c\d+|p\d+)[^"]*"/g, replacement: '' },

  // 標準化字體
  { pattern: /font-family:\s*['"]?Times New Roman['"]?/g, replacement: '' },

  // 移除空樣式屬性
  { pattern: /\s*style="\s*"/g, replacement: '' },
];
```

---

## 附錄 B: 相關文件路徑

```
改造前（現有文件）:
├── src/components/ArticleReview/FinalContentPreview.tsx
├── src/components/ArticleReview/ProofreadingPreviewSection.tsx
├── src/components/ArticleReview/DiffViewSection.tsx
├── src/components/ProofreadingReview/ProofreadingArticleContent.tsx
└── src/components/proofreading/RuleTester/DiffViewer.tsx

改造後（新增文件）:
├── src/components/common/SafeHtmlRenderer/
│   ├── index.tsx
│   ├── HtmlParser.ts
│   ├── FontAnalyzer.ts
│   ├── IssueDetector.ts
│   ├── IssueMarker.tsx
│   ├── ModeToggle.tsx
│   ├── IssueSummary.tsx
│   └── types.ts
├── src/components/common/FontBadge/
│   ├── index.tsx
│   └── FontTooltip.tsx
├── src/hooks/useHtmlAnalysis.ts
└── tests/
    ├── unit/FontAnalyzer.test.ts
    └── visual/preview-wysiwyg.spec.ts
```
