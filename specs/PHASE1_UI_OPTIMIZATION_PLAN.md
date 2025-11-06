# Phase 1 UI优化方案

## 一、核心设计理念

### 1.1 设计原则
- **极简主义**：专注核心工作流，减少视觉干扰
- **任务导向**：以完成校对工作流为中心的交互设计
- **现代美学**：采用Material Design 3 / Apple Human Interface Guidelines的设计语言
- **响应式**：完美支持桌面、平板、移动端

### 1.2 色彩系统
```typescript
// 主色调 - 专业蓝
primary: {
  50: '#E3F2FD',
  100: '#BBDEFB',
  500: '#2196F3',  // 主色
  600: '#1E88E5',
  700: '#1976D2',
}

// 中性色 - 温和灰
neutral: {
  50: '#FAFAFA',
  100: '#F5F5F5',
  200: '#EEEEEE',
  500: '#9E9E9E',
  700: '#616161',
  900: '#212121',
}

// 状态色
success: '#4CAF50',   // 绿色
warning: '#FF9800',   // 橙色
error: '#F44336',     // 红色
info: '#2196F3',      // 蓝色
```

---

## 二、语言国际化方案 (i18n)

### 2.1 技术选型
使用 **react-i18next** 实现完整的国际化支持

### 2.2 语言包结构
```typescript
// src/i18n/locales/zh-CN.json
{
  "common": {
    "appName": "CMS 自动化系统",
    "language": "语言",
    "settings": "设置",
    "save": "保存",
    "cancel": "取消",
    "confirm": "确认",
    "search": "搜索",
    "filter": "筛选",
    "refresh": "刷新"
  },
  "worklist": {
    "title": "工作清单",
    "subtitle": "从 Google Drive 同步文章并进行校对",
    "sync": "同步 Google Drive",
    "syncing": "同步中...",
    "syncSuccess": "同步成功",
    "syncError": "同步失败",
    "status": {
      "pending": "待处理",
      "in_review": "审核中",
      "approved": "已批准",
      "rejected": "已拒绝",
      "published": "已发布"
    },
    "emptyState": "暂无文章，点击"同步"按钮从 Google Drive 获取文章"
  },
  "settings": {
    "title": "系统设置",
    "language": "语言设置",
    "appearance": "外观设置",
    "proofreading": "校对规则",
    "tags": "标签管理",
    "comingSoon": "即将推出"
  }
}

// src/i18n/locales/en-US.json
{
  "common": {
    "appName": "CMS Automation",
    "language": "Language",
    "settings": "Settings",
    "save": "Save",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "search": "Search",
    "filter": "Filter",
    "refresh": "Refresh"
  },
  "worklist": {
    "title": "Worklist",
    "subtitle": "Sync articles from Google Drive and proofread",
    "sync": "Sync Google Drive",
    "syncing": "Syncing...",
    "syncSuccess": "Sync successful",
    "syncError": "Sync failed",
    "status": {
      "pending": "Pending",
      "in_review": "In Review",
      "approved": "Approved",
      "rejected": "Rejected",
      "published": "Published"
    },
    "emptyState": "No articles yet. Click 'Sync' to fetch from Google Drive"
  },
  "settings": {
    "title": "Settings",
    "language": "Language Settings",
    "appearance": "Appearance",
    "proofreading": "Proofreading Rules",
    "tags": "Tag Management",
    "comingSoon": "Coming Soon"
  }
}
```

### 2.3 i18n配置
```typescript
// src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import zhCN from './locales/zh-CN.json';
import enUS from './locales/en-US.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': { translation: zhCN },
      'en-US': { translation: enUS },
    },
    fallbackLng: 'zh-CN',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
```

---

## 三、简化后的应用架构

### 3.1 新的路由结构
```typescript
// src/config/routes.phase1.ts
export const phase1Routes: RouteConfig[] = [
  {
    path: '/',
    redirect: '/worklist',
    // 首页自动重定向到工作清单
  },
  {
    path: '/worklist',
    component: WorklistPage,
    title: 'worklist.title',
    isDefault: true,
  },
  {
    path: '/settings',
    component: SettingsPage,
    title: 'settings.title',
  },
  // 所有其他路由返回404或重定向到/worklist
];
```

### 3.2 应用布局结构
```
┌─────────────────────────────────────────────────┐
│  Header (Fixed, 64px height)                    │
│  - Logo + App Name                               │
│  - Language Switcher                             │
│  - Settings Icon                                 │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                                                  │
│  Main Content Area (Full width, scroll)         │
│  - Worklist Page (Default)                      │
│  - Settings Page (Modal/Drawer)                 │
│                                                  │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 四、页面设计详细规格

### 4.1 简化后的应用容器

```tsx
// src/App.phase1.tsx
export default function App() {
  const { t, i18n } = useTranslation();
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-neutral-200 shadow-sm">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-500 flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl font-semibold text-neutral-900">
              {t('common.appName')}
            </h1>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {/* Language Switcher */}
            <Select
              value={i18n.language}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
              className="w-32"
            >
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </Select>

            {/* Settings Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSettingsOpen(true)}
              aria-label={t('common.settings')}
            >
              <Settings className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-20 pb-8">
        <Routes>
          <Route path="/" element={<Navigate to="/worklist" replace />} />
          <Route path="/worklist" element={<WorklistPage />} />
          <Route path="*" element={<Navigate to="/worklist" replace />} />
        </Routes>
      </main>

      {/* Settings Drawer */}
      <SettingsDrawer
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}
```

### 4.2 工作清单页面 (Worklist Page)

#### 设计要点
- **顶部统计卡片**：显示总数、各状态数量
- **操作栏**：同步按钮、搜索、筛选
- **文章列表**：卡片式布局，支持状态标签
- **详情抽屉**：点击文章打开侧边抽屉查看详情

#### 界面布局
```
┌─────────────────────────────────────────────────┐
│  Statistics Cards (Grid 4 columns)              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│  │Total │ │Pending│ │Review│ │Done │           │
│  └──────┘ └──────┘ └──────┘ └──────┘           │
├─────────────────────────────────────────────────┤
│  Action Bar                                      │
│  [🔄 Sync Drive]  [🔍 Search]  [⚙️ Filter]      │
├─────────────────────────────────────────────────┤
│  Article List (Cards)                            │
│  ┌─────────────────────────────────────────┐   │
│  │ 📄 Article Title                         │   │
│  │ Author: John | Status: Pending          │   │
│  │ Last modified: 2 hours ago              │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ 📄 Another Article                       │   │
│  │ Author: Jane | Status: In Review        │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

#### 代码框架
```tsx
// src/pages/WorklistPage.modern.tsx
export default function WorklistPage() {
  const { t } = useTranslation();
  const [selectedArticle, setSelectedArticle] = useState(null);

  return (
    <div className="container mx-auto px-4 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">
          {t('worklist.title')}
        </h1>
        <p className="text-neutral-600 mt-1">
          {t('worklist.subtitle')}
        </p>
      </div>

      {/* Statistics */}
      <WorklistStatistics />

      {/* Action Bar */}
      <div className="flex items-center gap-3">
        <Button
          onClick={handleSync}
          loading={isSyncing}
          leftIcon={<RefreshCw />}
        >
          {isSyncing ? t('worklist.syncing') : t('worklist.sync')}
        </Button>

        <div className="flex-1" />

        <Input
          placeholder={t('common.search')}
          leftIcon={<Search />}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <Button variant="outline" leftIcon={<Filter />}>
          {t('common.filter')}
        </Button>
      </div>

      {/* Article Grid */}
      {articles.length === 0 ? (
        <EmptyState
          icon={<FileText />}
          title={t('worklist.emptyState')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {articles.map(article => (
            <ArticleCard
              key={article.id}
              article={article}
              onClick={() => setSelectedArticle(article)}
            />
          ))}
        </div>
      )}

      {/* Detail Drawer */}
      <ArticleDetailDrawer
        article={selectedArticle}
        open={!!selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />
    </div>
  );
}
```

### 4.3 设置抽屉 (Settings Drawer)

#### 设计要点
- **侧边抽屉**：从右侧滑入，宽度400px
- **分组折叠面板**：语言、外观、高级功能
- **即将推出标记**：校对规则、标签管理显示"Coming Soon"

#### 界面布局
```
┌─────────────────────────┐
│ Settings          [X]   │
├─────────────────────────┤
│                         │
│ 🌐 Language Settings    │
│ ├─ 简体中文 / English    │
│ └─────────────────────  │
│                         │
│ 🎨 Appearance          │
│ ├─ Theme: Light/Dark    │
│ └─────────────────────  │
│                         │
│ 📝 Proofreading Rules   │
│ └─ Coming Soon 🚧       │
│                         │
│ 🏷️  Tag Management       │
│ └─ Coming Soon 🚧       │
│                         │
└─────────────────────────┘
```

#### 代码框架
```tsx
// src/components/SettingsDrawer.tsx
export function SettingsDrawer({ open, onClose }) {
  const { t, i18n } = useTranslation();

  return (
    <Drawer open={open} onClose={onClose} position="right" width="400px">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">{t('settings.title')}</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Language Settings */}
          <Accordion defaultOpen title={t('settings.language')}>
            <RadioGroup
              value={i18n.language}
              onChange={(value) => i18n.changeLanguage(value)}
            >
              <Radio value="zh-CN">简体中文</Radio>
              <Radio value="en-US">English</Radio>
            </RadioGroup>
          </Accordion>

          {/* Appearance */}
          <Accordion title={t('settings.appearance')}>
            <div className="space-y-2">
              <label className="text-sm text-neutral-600">Theme</label>
              <Select>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto</option>
              </Select>
            </div>
          </Accordion>

          {/* Coming Soon Sections */}
          <Accordion title={t('settings.proofreading')} disabled>
            <div className="text-center py-8">
              <div className="text-4xl mb-2">🚧</div>
              <p className="text-neutral-500">{t('settings.comingSoon')}</p>
            </div>
          </Accordion>

          <Accordion title={t('settings.tags')} disabled>
            <div className="text-center py-8">
              <div className="text-4xl mb-2">🚧</div>
              <p className="text-neutral-500">{t('settings.comingSoon')}</p>
            </div>
          </Accordion>
        </div>
      </div>
    </Drawer>
  );
}
```

---

## 五、组件设计系统

### 5.1 核心组件库

#### 统计卡片 (StatCard)
```tsx
interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  color?: 'primary' | 'success' | 'warning' | 'error';
}

export function StatCard({ title, value, icon, trend, color = 'primary' }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 border border-neutral-200 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-neutral-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-neutral-900">{value}</p>
          {trend && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${
              trend.direction === 'up' ? 'text-success' : 'text-error'
            }`}>
              {trend.direction === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg bg-${color}-50 flex items-center justify-center`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
```

#### 文章卡片 (ArticleCard)
```tsx
interface ArticleCardProps {
  article: WorklistItem;
  onClick: () => void;
}

export function ArticleCard({ article, onClick }: ArticleCardProps) {
  const { t } = useTranslation();

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl p-4 border border-neutral-200 hover:shadow-md hover:border-primary-200 transition-all cursor-pointer"
    >
      {/* Status Badge */}
      <div className="flex items-start justify-between mb-3">
        <Badge variant={getStatusVariant(article.status)}>
          {t(`worklist.status.${article.status}`)}
        </Badge>
        <button className="text-neutral-400 hover:text-neutral-600">
          <MoreVertical size={18} />
        </button>
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-neutral-900 mb-2 line-clamp-2">
        {article.title}
      </h3>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-sm text-neutral-600">
        <div className="flex items-center gap-1">
          <User size={14} />
          <span>{article.author}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock size={14} />
          <span>{formatRelativeTime(article.updated_at)}</span>
        </div>
      </div>

      {/* Action Button */}
      <Button
        variant="outline"
        size="sm"
        className="w-full mt-4"
        onClick={(e) => {
          e.stopPropagation();
          // Handle action
        }}
      >
        {t('common.viewDetails')}
      </Button>
    </div>
  );
}
```

---

## 六、实施计划

### 6.1 Phase 1.1 - 基础架构 (Week 1)
- [ ] 设置 i18next 国际化
- [ ] 创建语言包 (中文/英文)
- [ ] 简化路由配置
- [ ] 移除导航组件
- [ ] 创建新的App容器布局

### 6.2 Phase 1.2 - 核心页面 (Week 2)
- [ ] 重构 WorklistPage 为现代设计
- [ ] 实现统计卡片组件
- [ ] 实现文章卡片组件
- [ ] 实现详情抽屉
- [ ] 添加空状态设计

### 6.3 Phase 1.3 - 设置功能 (Week 3)
- [ ] 实现设置抽屉组件
- [ ] 语言切换功能
- [ ] 外观设置 (主题)
- [ ] "即将推出"占位符

### 6.4 Phase 1.4 - 优化与测试 (Week 4)
- [ ] 响应式适配 (移动端/平板)
- [ ] 性能优化
- [ ] E2E测试
- [ ] 用户测试反馈
- [ ] 文档更新

---

## 七、设计资源

### 7.1 设计工具
- **Figma**: 用于原型设计和设计系统
- **Storybook**: 组件库文档和测试

### 7.2 UI库选择建议
- **Headless UI**: 无样式组件，完全自定义
- **Radix UI**: 高质量的无障碍组件
- **Tailwind CSS**: 实用优先的CSS框架

### 7.3 图标库
- **Lucide Icons**: 现代简约的图标集
- **Heroicons**: 由Tailwind团队设计的图标

---

## 八、性能指标

### 8.1 加载性能
- **首屏加载时间**: < 1.5s
- **交互就绪时间**: < 2s
- **Lighthouse Score**: > 90

### 8.2 用户体验指标
- **操作响应时间**: < 100ms
- **页面切换动画**: 300ms
- **数据加载反馈**: 立即显示

---

## 九、后续演进 (Phase 2+)

### 9.1 功能扩展
- 恢复完整导航
- 开放校对规则管理
- 开放标签管理
- 添加文章生成器
- 添加发布任务管理

### 9.2 高级功能
- 实时协作
- 评论系统
- 版本历史
- 高级搜索
- 数据分析仪表板

---

## 十、附录

### 10.1 颜色对照表
| 用途 | 颜色 | Hex |
|------|------|-----|
| 主色 | Primary | #2196F3 |
| 成功 | Success | #4CAF50 |
| 警告 | Warning | #FF9800 |
| 错误 | Error | #F44336 |
| 背景 | Background | #FAFAFA |
| 文字 | Text | #212121 |

### 10.2 间距系统
| 名称 | 值 | 用途 |
|------|-----|------|
| xs | 4px | 极小间距 |
| sm | 8px | 小间距 |
| md | 16px | 中等间距 |
| lg | 24px | 大间距 |
| xl | 32px | 超大间距 |

### 10.3 字体系统
| 级别 | 大小 | 粗细 | 用途 |
|------|------|------|------|
| H1 | 32px | 700 | 页面标题 |
| H2 | 24px | 600 | 分组标题 |
| H3 | 20px | 600 | 卡片标题 |
| Body | 16px | 400 | 正文 |
| Small | 14px | 400 | 辅助文字 |
| Caption | 12px | 400 | 说明文字 |
