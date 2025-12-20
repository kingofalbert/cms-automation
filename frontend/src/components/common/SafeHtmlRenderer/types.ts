/**
 * SafeHtmlRenderer 類型定義
 *
 * @version 1.0
 * @date 2025-12-19
 */

// ============================================================
// View Mode Types
// ============================================================

export type ViewMode = 'preview' | 'source' | 'hybrid';

// ============================================================
// Issue Types
// ============================================================

export type IssueType = 'font' | 'nesting' | 'empty' | 'deprecated' | 'accessibility' | 'gdocs';

export type IssueSeverity = 'error' | 'warning' | 'info';

export interface HtmlIssue {
  id: string;
  type: IssueType;
  severity: IssueSeverity;
  message: string;
  element: string;
  position: {
    start: number;
    end: number;
  };
  suggestion?: string;
  autoFixable?: boolean;
  details?: Record<string, unknown>;
}

// ============================================================
// Font Analysis Types
// ============================================================

export type FontCategory = 'system' | 'chinese' | 'web-safe' | 'problematic' | 'unknown';

export interface FontCheckResult {
  isValid: boolean;
  fontFamily: string;
  primaryFont: string;
  fallbackFonts: string[];
  category: FontCategory;
  severity: IssueSeverity | 'ok';
  message?: string;
  suggestion?: string;
}

export interface FontAnalysisResult {
  fonts: FontCheckResult[];
  issues: HtmlIssue[];
  hasProblematicFonts: boolean;
  uniqueFonts: string[];
}

// ============================================================
// HTML Analysis Types
// ============================================================

export interface HtmlAnalysisResult {
  issues: HtmlIssue[];
  fonts: FontAnalysisResult;
  isGDocsContaminated: boolean;
  cleanHtml: string;
  stats: {
    totalIssues: number;
    fontIssues: number;
    nestingIssues: number;
    emptyTagIssues: number;
    otherIssues: number;
  };
}

// ============================================================
// Component Props Types
// ============================================================

export interface SafeHtmlRendererProps {
  /** 要渲染的 HTML 內容 */
  html: string;

  /** 顯示模式: preview=渲染視圖, source=源碼視圖, hybrid=混合視圖 */
  mode?: ViewMode;

  /** 是否顯示問題標註 */
  showIssues?: boolean;

  /** 允許的字體列表（白名單） */
  allowedFonts?: string[];

  /** 是否啟用 Google Docs 污染檢測 */
  detectGDocs?: boolean;

  /** 是否允許自動修復 */
  enableAutoFix?: boolean;

  /** 問題點擊回調 */
  onIssueClick?: (issue: HtmlIssue) => void;

  /** 問題修復回調 */
  onIssueFix?: (issue: HtmlIssue, fixedHtml: string) => void;

  /** 模式切換回調 */
  onModeChange?: (mode: ViewMode) => void;

  /** 分析完成回調 */
  onAnalysisComplete?: (result: HtmlAnalysisResult) => void;

  /** 自定義類名 */
  className?: string;

  /** 是否顯示工具欄 */
  showToolbar?: boolean;

  /** 是否顯示問題摘要 */
  showSummary?: boolean;

  /** 最大高度（超出滾動） */
  maxHeight?: string | number;
}

export interface ModeToggleProps {
  currentMode: ViewMode;
  onChange: (mode: ViewMode) => void;
  disabled?: boolean;
}

export interface IssueSummaryProps {
  issues: HtmlIssue[];
  onCategoryClick?: (type: IssueType) => void;
}

export interface IssueMarkerProps {
  issue: HtmlIssue;
  children: React.ReactNode;
  onClick?: () => void;
  onFix?: () => void;
}

export interface FontTooltipProps {
  font: FontCheckResult;
  onFix?: () => void;
  onIgnore?: () => void;
}

// ============================================================
// Configuration Types
// ============================================================

export interface FontAnalyzerConfig {
  allowedFonts: string[];
  problematicFonts: string[];
  chineseFonts: string[];
  systemFonts: string[];
}

export interface HtmlParserConfig {
  /** 是否移除空標籤 */
  removeEmptyTags: boolean;

  /** 是否修復嵌套錯誤 */
  fixNesting: boolean;

  /** 是否清理 Google Docs 樣式 */
  cleanGDocs: boolean;

  /** 最大嵌套深度 */
  maxNestingDepth: number;
}

// ============================================================
// Default Values
// ============================================================

/** 系統字體列表 */
export const SYSTEM_FONTS = [
  '-apple-system',
  'BlinkMacSystemFont',
  'Segoe UI',
  'Roboto',
  'Oxygen',
  'Ubuntu',
  'Cantarell',
  'Fira Sans',
  'Droid Sans',
  'Helvetica Neue',
  'sans-serif',
  'serif',
  'monospace',
] as const;

/** 中文字體列表 */
export const CHINESE_FONTS = [
  'Noto Sans SC',
  'Noto Sans TC',
  'Microsoft YaHei',
  '微軟雅黑',
  'PingFang SC',
  '蘋方-簡',
  'PingFang TC',
  '蘋方-繁',
  'Hiragino Sans GB',
  'WenQuanYi Micro Hei',
  '文泉驛微米黑',
  'Source Han Sans SC',
  'Source Han Sans TC',
] as const;

/** 網頁安全字體列表 */
export const WEB_SAFE_FONTS = [
  'Arial',
  'Helvetica',
  'Georgia',
  'Verdana',
  'Trebuchet MS',
  'Tahoma',
  'Lucida Sans',
] as const;

/** 問題字體列表（通常來自 Office/Google Docs） */
export const PROBLEMATIC_FONTS = [
  'Times New Roman',
  'Calibri',
  'Cambria',
  'Comic Sans MS',
  'Courier New',
  'SimSun',
  '宋体',
  '宋體',
  'SimHei',
  '黑体',
  '黑體',
  'FangSong',
  '仿宋',
  'KaiTi',
  '楷体',
  '楷體',
] as const;

/** 默認允許的字體（合併以上除問題字體外的所有） */
export const DEFAULT_ALLOWED_FONTS = [
  ...SYSTEM_FONTS,
  ...CHINESE_FONTS,
  ...WEB_SAFE_FONTS,
] as const;

/** Google Docs 污染模式 */
export const GDOCS_PATTERNS = {
  /** orphans/widows 樣式（Word/GDocs 特有） */
  orphansWidows: /(?:orphans|widows):\s*\d+/i,

  /** Google Docs 生成的類名模式 */
  classNames: /class="[^"]*(?:c\d+|p\d+)/,

  /** 特定的內聯樣式組合 */
  inlineStyles: /style="[^"]*(?:text-indent|line-height:\s*\d+(?:\.\d+)?;?\s*){2,}/i,

  /** 空的樣式 span */
  emptyStyledSpan: /<span[^>]*style="[^"]*"[^>]*>\s*<\/span>/,

  /** margin/padding 重置 */
  marginPaddingReset: /style="[^"]*(?:margin|padding):\s*0[^"]*"/i,
} as const;

/** 問題嚴重程度顏色映射 */
export const SEVERITY_COLORS = {
  error: {
    bg: 'bg-red-100',
    border: 'border-red-500',
    text: 'text-red-700',
    hex: '#FEE2E2',
  },
  warning: {
    bg: 'bg-amber-100',
    border: 'border-amber-500',
    text: 'text-amber-700',
    hex: '#FEF3C7',
  },
  info: {
    bg: 'bg-blue-100',
    border: 'border-blue-500',
    text: 'text-blue-700',
    hex: '#DBEAFE',
  },
} as const;

/** 問題類型圖標映射 */
export const ISSUE_TYPE_ICONS = {
  font: '🔤',
  nesting: '📦',
  empty: '⬜',
  deprecated: '⚠️',
  accessibility: '♿',
  gdocs: '📄',
} as const;
