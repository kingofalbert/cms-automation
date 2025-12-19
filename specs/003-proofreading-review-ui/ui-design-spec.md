# 校对审核页面 - UI 设计规格

**Feature:** Proofreading Review UI
**Created:** 2025-11-07
**Design System:** Apple-inspired Minimalist Style
**Framework:** React 18 + TypeScript + Tailwind CSS

---

## 🎨 Design Principles

### 1. Clarity (清晰)
- 简洁的信息层级
- 明确的视觉焦点
- 清晰的操作反馈

### 2. Efficiency (效率)
- 快捷键支持
- 批量操作
- 智能默认值

### 3. Consistency (一致性)
- 复用Design System组件
- 统一的颜色和间距
- 一致的交互模式

### 4. Elegance (优雅)
- 柔和的动画过渡
- 精致的细节打磨
- 呼吸感的留白

---

## 📐 Page Layout

### Desktop Layout (≥1280px)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header Bar (h-16, fixed top)                                                │
│ ┌──────────────────────────────┬──────────────────────────────────────────┐ │
│ │ Breadcrumb                   │ Action Buttons                          │ │
│ └──────────────────────────────┴──────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ Sub-header (h-14, sticky)                                                   │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ 标题 + 统计 + 视图模式切换 [文章|对比|预览]                               │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
├────────────┬─────────────────────────────────────┬───────────────────────────┤
│            │                                     │                           │
│ Issue List │       Article Content               │    Issue Detail Panel     │
│   (20%)    │          (50%)                      │          (30%)            │
│            │                                     │                           │
│ w-80       │      flex-1                         │         w-96              │
│ (320px)    │                                     │        (384px)            │
│            │                                     │                           │
│ ┌────────┐ │  ┌─────────────────────────────┐  │  ┌─────────────────────┐  │
│ │Filter  │ │  │  View Mode: [文章][对比][预览]│  │  │  Issue #1 / 24      │  │
│ │Controls│ │  │  Legend: 🔴严重 🟡警告 🔵信息│  │  │  ──────────────────  │  │
│ │        │ │  │                             │  │  │  🔴 Critical        │  │
│ │  🔍   │ │  │  文章内容显示在此处：         │  │  │  Grammar Error      │  │
│ └────────┘ │  │                             │  │  │                     │  │
│            │  │  ...普通文本...[高亮问题]... │  │  │  原文:              │  │
│ ┌────────┐ │  │  ...更多内容...[另一问题]... │  │  │  "他们决定去公园玩耍" │  │
│ │Issue#1 │ │  │                             │  │  │                     │  │
│ │🔴Grammar│ │  │  点击高亮的问题文本，       │  │  │  建议:              │  │
│ │"...玩耍"│ │  │  右侧面板显示详情           │  │  │  "他们决定去公园玩"  │  │
│ └────────┘ │  │                             │  │  │                     │  │
│            │  │  自动滚动到选中的问题位置    │  │  │  说明:              │  │
│ ┌────────┐ │  │                             │  │  │  "玩耍"是冗余...     │  │
│ │Issue#2 │ │  │                             │  │  │                     │  │
│ │🟡Punct │ │  └─────────────────────────────┘  │  │  ──────────────────  │  │
│ │"...。" │ │                                     │  │  Decision Actions:  │  │
│ └────────┘ │  对比模式: 显示原文vs校对后的diff   │  │                     │  │
│            │  预览模式: 显示应用修改后的效果     │  │  [✅ 接受] [❌ 拒绝]│  │
│ ┌────────┐ │                                     │  │                     │  │
│ │Issue#3 │ │                                     │  │  快捷键: A接受 R拒绝│  │
│ │🔵Style │ │                                     │  │  ↑↓ 导航            │  │
│ │"..."   │ │                                     │  │                     │  │
│ └────────┘ │                                     │  └─────────────────────┘  │
└────────────┴─────────────────────────────────────┴───────────────────────────┘
│ Footer Progress Bar (h-12, fixed bottom)                                    │
│ 进度: 9/24 已处理 (37.5%) ▓▓▓▓▓▓░░░░░░░░░░  [🔴 3] [🟡 12] [🔵 9]         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**中间区域视图模式说明 (Phase 8.6 更新)**:
- **文章模式 (默认)**: 显示完整文章内容，问题位置以颜色高亮标记，点击高亮文本选中问题
- **对比模式**: 显示原文与AI校对后的文本差异 (document-level diff)
- **预览模式**: 显示应用所有已接受修改后的最终效果

### Mobile Layout (<768px)

```
┌──────────────────────────────┐
│ ☰ 校对审核      [✓] [X]      │
├──────────────────────────────┤
│ Tab Navigation:              │
│ ┌───────┬───────┬──────────┐ │
│ │ 内容  │ 问题  │ 决策     │ │
│ └───────┴───────┴──────────┘ │
├──────────────────────────────┤
│                              │
│  Active Tab Content          │
│  (Only one visible)          │
│                              │
│                              │
├──────────────────────────────┤
│ Current Issue: #5 / 24       │
│ 🔴 Critical - Grammar        │
│ [详情] [◀] [▶]               │
└──────────────────────────────┘
```

---

## 🧩 Component Specifications

### 1. Header Bar (ProofreadingReviewHeader)

**Purpose:** 页面顶部固定导航栏

**Structure:**
```tsx
<header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-50">
  <div className="flex items-center justify-between h-full px-6">
    {/* Left: Breadcrumb */}
    <nav className="flex items-center space-x-2 text-sm">
      <Link to="/" className="text-gray-500 hover:text-gray-700">首页</Link>
      <ChevronRight className="w-4 h-4 text-gray-400" />
      <Link to="/worklist" className="text-gray-500 hover:text-gray-700">Worklist</Link>
      <ChevronRight className="w-4 h-4 text-gray-400" />
      <span className="text-gray-900 font-medium truncate max-w-md">
        {articleTitle}
      </span>
      <ChevronRight className="w-4 h-4 text-gray-400" />
      <span className="text-blue-600 font-medium">校对审核</span>
    </nav>

    {/* Right: Action Buttons */}
    <div className="flex items-center space-x-3">
      <Button variant="ghost" onClick={onSaveDraft}>
        <Save className="w-4 h-4 mr-2" />
        保存草稿
      </Button>
      <Button variant="secondary" onClick={onCancel}>
        取消
      </Button>
      <Button variant="primary" onClick={onCompleteReview}>
        <CheckCircle className="w-4 h-4 mr-2" />
        完成审核
      </Button>
    </div>
  </div>
</header>
```

**Styling:**
```css
/* Sticky positioning */
position: fixed;
top: 0;
z-index: 50;

/* Apple-style border */
border-bottom: 1px solid rgb(229, 231, 235); /* gray-200 */

/* Backdrop blur for depth */
backdrop-filter: blur(10px);
background-color: rgba(255, 255, 255, 0.95);
```

**Interactions:**
- **保存草稿**: 自动保存当前所有决策（不改变状态）
- **取消**: 返回Worklist页面（确认未保存更改）
- **完成审核**: 保存决策 + 状态转换（显示确认对话框）

---

### 2. Sub-header (Review Stats Bar)

**Purpose:** 显示审核统计和视图控制

**Structure:**
```tsx
<div className="sticky top-16 h-14 bg-gray-50 border-b border-gray-200 z-40">
  <div className="flex items-center justify-between h-full px-6">
    {/* Left: Stats */}
    <div className="flex items-center space-x-6">
      <h2 className="text-lg font-semibold text-gray-900">
        校对审核
      </h2>
      <div className="flex items-center space-x-4 text-sm">
        <div className="flex items-center">
          <div className="w-2 h-2 rounded-full bg-red-500 mr-2" />
          <span className="text-gray-600">Critical:</span>
          <span className="ml-1 font-medium text-gray-900">{criticalCount}</span>
        </div>
        <div className="flex items-center">
          <div className="w-2 h-2 rounded-full bg-yellow-500 mr-2" />
          <span className="text-gray-600">Warning:</span>
          <span className="ml-1 font-medium text-gray-900">{warningCount}</span>
        </div>
        <div className="flex items-center">
          <div className="w-2 h-2 rounded-full bg-blue-500 mr-2" />
          <span className="text-gray-600">Info:</span>
          <span className="ml-1 font-medium text-gray-900">{infoCount}</span>
        </div>
        <Separator orientation="vertical" className="h-6" />
        <span className="text-gray-600">
          已处理: <span className="font-medium text-gray-900">{processedCount} / {totalCount}</span>
        </span>
      </div>
    </div>

    {/* Right: View Mode Switcher */}
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-600 mr-2">视图:</span>
      <ToggleGroup type="single" value={viewMode} onValueChange={setViewMode}>
        <ToggleGroupItem value="original" className="text-sm">
          <FileText className="w-4 h-4 mr-1" />
          原文
        </ToggleGroupItem>
        <ToggleGroupItem value="preview" className="text-sm">
          <Eye className="w-4 h-4 mr-1" />
          预览
        </ToggleGroupItem>
        <ToggleGroupItem value="diff" className="text-sm">
          <GitCompare className="w-4 h-4 mr-1" />
          对比
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  </div>
</div>
```

---

### 3. Issue List (ProofreadingIssueList)

**Purpose:** 左侧问题列表，支持过滤、排序、选择

**Structure:**
```tsx
<aside className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
  {/* Filter Controls */}
  <div className="sticky top-0 bg-white p-4 border-b border-gray-200 z-10">
    <div className="space-y-3">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          placeholder="搜索问题..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Severity Filter */}
      <Select value={severityFilter} onValueChange={setSeverityFilter}>
        <SelectTrigger>
          <SelectValue placeholder="严重程度" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部严重程度</SelectItem>
          <SelectItem value="critical">🔴 Critical</SelectItem>
          <SelectItem value="warning">🟡 Warning</SelectItem>
          <SelectItem value="info">🔵 Info</SelectItem>
        </SelectContent>
      </Select>

      {/* Category Filter */}
      <Select value={categoryFilter} onValueChange={setCategoryFilter}>
        <SelectTrigger>
          <SelectValue placeholder="规则类别" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部类别</SelectItem>
          <SelectItem value="grammar">语法</SelectItem>
          <SelectItem value="punctuation">标点</SelectItem>
          <SelectItem value="style">风格</SelectItem>
          <SelectItem value="spelling">拼写</SelectItem>
          <SelectItem value="other">其他</SelectItem>
        </SelectContent>
      </Select>

      {/* Decision Status Filter */}
      <Select value={statusFilter} onValueChange={setStatusFilter}>
        <SelectTrigger>
          <SelectValue placeholder="决策状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部状态</SelectItem>
          <SelectItem value="pending">待处理</SelectItem>
          <SelectItem value="accepted">已接受</SelectItem>
          <SelectItem value="rejected">已拒绝</SelectItem>
          <SelectItem value="modified">已修改</SelectItem>
        </SelectContent>
      </Select>

      {/* Batch Actions */}
      {selectedIssues.length > 0 && (
        <div className="flex items-center justify-between bg-blue-50 p-3 rounded-lg">
          <span className="text-sm font-medium text-blue-700">
            已选中 {selectedIssues.length} 个问题
          </span>
          <div className="flex space-x-2">
            <Button size="sm" variant="ghost" onClick={onBatchAccept}>
              批量接受
            </Button>
            <Button size="sm" variant="ghost" onClick={onBatchReject}>
              批量拒绝
            </Button>
          </div>
        </div>
      )}
    </div>
  </div>

  {/* Issue Items */}
  <div className="divide-y divide-gray-100">
    {filteredIssues.map((issue, index) => (
      <IssueListItem
        key={issue.id}
        issue={issue}
        index={index + 1}
        isSelected={selectedIssue?.id === issue.id}
        isChecked={selectedIssues.includes(issue.id)}
        onClick={() => onSelectIssue(issue)}
        onCheckChange={(checked) => onToggleIssue(issue.id, checked)}
      />
    ))}
  </div>

  {/* Empty State */}
  {filteredIssues.length === 0 && (
    <div className="flex flex-col items-center justify-center h-64 text-gray-500">
      <AlertCircle className="w-12 h-12 mb-4 text-gray-300" />
      <p className="text-sm">没有找到匹配的问题</p>
    </div>
  )}
</aside>
```

**IssueListItem Component:**
```tsx
<div
  className={cn(
    "p-4 cursor-pointer transition-colors",
    "hover:bg-gray-50",
    isSelected && "bg-blue-50 border-l-4 border-blue-500",
    issue.decision_status === 'accepted' && "bg-green-50",
    issue.decision_status === 'rejected' && "bg-gray-50 opacity-60"
  )}
  onClick={onClick}
>
  <div className="flex items-start space-x-3">
    {/* Checkbox */}
    <Checkbox
      checked={isChecked}
      onCheckedChange={onCheckChange}
      onClick={(e) => e.stopPropagation()}
      className="mt-1"
    />

    {/* Severity Icon */}
    <div className="flex-shrink-0 mt-0.5">
      {issue.severity === 'critical' && (
        <AlertCircle className="w-5 h-5 text-red-500" />
      )}
      {issue.severity === 'warning' && (
        <AlertTriangle className="w-5 h-5 text-yellow-500" />
      )}
      {issue.severity === 'info' && (
        <Info className="w-5 h-5 text-blue-500" />
      )}
    </div>

    {/* Content */}
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-gray-500">
          #{index} · {issue.rule_category}
        </span>
        {issue.decision_status !== 'pending' && (
          <Badge variant="secondary" className="text-xs">
            {issue.decision_status === 'accepted' && '✓ 已接受'}
            {issue.decision_status === 'rejected' && '✗ 已拒绝'}
            {issue.decision_status === 'modified' && '✏ 已修改'}
          </Badge>
        )}
      </div>
      <p className="text-sm text-gray-900 font-medium mb-1 truncate">
        {issue.original_text}
      </p>
      <p className="text-xs text-gray-600 truncate">
        → {issue.suggested_text}
      </p>
      {issue.engine === 'ai' && issue.confidence && (
        <div className="mt-2 flex items-center text-xs text-gray-500">
          <Sparkles className="w-3 h-3 mr-1" />
          AI 置信度: {(issue.confidence * 100).toFixed(0)}%
        </div>
      )}
    </div>
  </div>
</div>
```

**Styling:**
```css
/* Smooth transitions */
.issue-list-item {
  transition: all 0.2s ease;
}

/* Selected state with blue accent */
.issue-list-item--selected {
  background-color: rgb(239, 246, 255); /* blue-50 */
  border-left: 4px solid rgb(59, 130, 246); /* blue-500 */
}

/* Hover effect */
.issue-list-item:hover {
  background-color: rgb(249, 250, 251); /* gray-50 */
}

/* Accepted state */
.issue-list-item--accepted {
  background-color: rgb(240, 253, 244); /* green-50 */
}

/* Rejected state */
.issue-list-item--rejected {
  opacity: 0.6;
  text-decoration: line-through;
}
```

---

### 4. Article Content (ProofreadingArticleContent)

**Purpose:** 中间主内容区，渲染文章并高亮问题

**Structure:**
```tsx
<main className="flex-1 bg-white overflow-y-auto p-8">
  <article className="max-w-3xl mx-auto prose prose-lg">
    {/* Article Header */}
    <header className="mb-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        {article.title}
      </h1>
      <div className="flex items-center text-sm text-gray-500 space-x-4">
        <span>作者: {article.author || '未知'}</span>
        <span>·</span>
        <span>字数: {article.word_count}</span>
        <span>·</span>
        <span>最后同步: {formatDate(article.synced_at)}</span>
      </div>
    </header>

    {/* Article Content with Highlighted Issues */}
    <div
      ref={contentRef}
      className="article-content"
      dangerouslySetInnerHTML={{ __html: renderContentWithHighlights() }}
    />
  </article>
</main>
```

**Content Highlighting Logic:**
```typescript
function renderContentWithHighlights(): string {
  let content = article.content;
  const sortedIssues = [...issues].sort((a, b) => b.position.start - a.position.start);

  for (const issue of sortedIssues) {
    const { start, end } = issue.position;
    const originalText = content.slice(start, end);

    const highlightClass = cn(
      'issue-highlight',
      `issue-highlight--${issue.severity}`,
      `issue-highlight--${issue.decision_status}`,
      selectedIssue?.id === issue.id && 'issue-highlight--selected'
    );

    const highlightedText = `
      <span
        class="${highlightClass}"
        data-issue-id="${issue.id}"
        data-severity="${issue.severity}"
        onClick="handleIssueClick('${issue.id}')"
      >
        ${originalText}
      </span>
    `;

    content = content.slice(0, start) + highlightedText + content.slice(end);
  }

  return content;
}
```

**Highlighting Styles:**
```css
/* Base issue highlight */
.issue-highlight {
  cursor: pointer;
  padding: 2px 4px;
  margin: 0 1px;
  border-radius: 3px;
  transition: all 0.2s ease;
  position: relative;
}

/* Severity-specific styles */
.issue-highlight--critical {
  background-color: rgb(254, 226, 226); /* red-100 */
  border-bottom: 2px solid rgb(239, 68, 68); /* red-500 */
}

.issue-highlight--warning {
  background-color: rgb(254, 243, 199); /* yellow-100 */
  border-bottom: 2px solid rgb(245, 158, 11); /* yellow-500 */
}

.issue-highlight--info {
  background-color: rgb(219, 234, 254); /* blue-100 */
  border-bottom: 2px solid rgb(59, 130, 246); /* blue-500 */
}

/* Decision status styles */
.issue-highlight--accepted {
  background-color: rgb(220, 252, 231); /* green-100 */
  border: 2px solid rgb(34, 197, 94); /* green-500 */
}

.issue-highlight--rejected {
  background-color: rgb(243, 244, 246); /* gray-100 */
  text-decoration: line-through;
  opacity: 0.6;
}

.issue-highlight--modified {
  background-color: rgb(243, 232, 255); /* purple-100 */
  border: 2px solid rgb(168, 85, 247); /* purple-500 */
}

/* Selected state */
.issue-highlight--selected {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3); /* blue-500 glow */
  background-color: rgb(219, 234, 254); /* blue-100 */
}

/* Hover effect */
.issue-highlight:hover {
  opacity: 0.8;
  transform: scale(1.02);
}

/* Tooltip */
.issue-highlight::after {
  content: attr(data-issue-explanation);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgb(31, 41, 55); /* gray-800 */
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 100;
}

.issue-highlight:hover::after {
  opacity: 1;
}
```

---

### 5. Issue Detail Panel (ProofreadingIssueDetailPanel)

**Purpose:** 右侧详情面板，显示选中问题并提供决策操作

**Structure:**
```tsx
<aside className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
  {selectedIssue ? (
    <div className="p-6 space-y-6">
      {/* Header Navigation */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          问题 #{selectedIssueIndex + 1} / {totalIssues}
        </h3>
        <div className="flex space-x-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={onPrevious}
            disabled={selectedIssueIndex === 0}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={onNext}
            disabled={selectedIssueIndex === totalIssues - 1}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Issue Metadata */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <Badge
            variant={selectedIssue.severity === 'critical' ? 'destructive' : 'secondary'}
            className="text-xs"
          >
            {selectedIssue.severity === 'critical' && '🔴 Critical'}
            {selectedIssue.severity === 'warning' && '🟡 Warning'}
            {selectedIssue.severity === 'info' && '🔵 Info'}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {selectedIssue.rule_category}
          </Badge>
          {selectedIssue.engine === 'ai' && (
            <Badge variant="outline" className="text-xs flex items-center">
              <Sparkles className="w-3 h-3 mr-1" />
              AI
            </Badge>
          )}
        </div>
        <p className="text-xs text-gray-500">
          规则 ID: {selectedIssue.rule_id}
        </p>
      </div>

      <Separator />

      {/* Original vs Suggested */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            原文:
          </label>
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-gray-900">{selectedIssue.original_text}</p>
          </div>
        </div>

        <div className="flex items-center justify-center">
          <ArrowDown className="w-4 h-4 text-gray-400" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            建议修改:
          </label>
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-gray-900">{selectedIssue.suggested_text}</p>
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          问题说明:
        </label>
        <p className="text-sm text-gray-600 leading-relaxed">
          {selectedIssue.explanation}
        </p>
        {selectedIssue.explanation_detail && (
          <p className="text-xs text-gray-500 mt-2">
            {selectedIssue.explanation_detail}
          </p>
        )}
      </div>

      <Separator />

      {/* Decision Actions */}
      <div className="space-y-4">
        <label className="block text-sm font-medium text-gray-700">
          决策操作:
        </label>

        {/* Quick Decision Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            variant="outline"
            onClick={() => onDecision('accepted')}
            className="h-auto py-3 flex flex-col items-center"
            disabled={selectedIssue.decision_status === 'accepted'}
          >
            <CheckCircle className="w-5 h-5 mb-1 text-green-600" />
            <span className="text-sm">接受建议</span>
            {selectedIssue.decision_status === 'accepted' && (
              <span className="text-xs text-gray-500 mt-1">已接受</span>
            )}
          </Button>

          <Button
            variant="outline"
            onClick={() => onDecision('rejected')}
            className="h-auto py-3 flex flex-col items-center"
            disabled={selectedIssue.decision_status === 'rejected'}
          >
            <XCircle className="w-5 h-5 mb-1 text-red-600" />
            <span className="text-sm">拒绝建议</span>
            {selectedIssue.decision_status === 'rejected' && (
              <span className="text-xs text-gray-500 mt-1">已拒绝</span>
            )}
          </Button>
        </div>

        {/* Custom Modification */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            或自定义修改:
          </label>
          <Textarea
            value={customModification}
            onChange={(e) => setCustomModification(e.target.value)}
            placeholder="输入自定义修改内容..."
            rows={3}
            className="text-sm"
          />
          <Button
            variant="secondary"
            onClick={() => onDecision('modified', customModification)}
            disabled={!customModification.trim()}
            className="w-full"
          >
            <Edit className="w-4 h-4 mr-2" />
            应用自定义修改
          </Button>
        </div>

        {/* Decision Rationale */}
        <div className="space-y-2">
          <label className="block text-sm text-gray-600">
            决策备注（可选）:
          </label>
          <Textarea
            value={decisionRationale}
            onChange={(e) => setDecisionRationale(e.target.value)}
            placeholder="添加决策理由或备注..."
            rows={2}
            className="text-sm"
          />
        </div>
      </div>

      <Separator />

      {/* Feedback Section (Optional) */}
      <Accordion type="single" collapsible className="border-none">
        <AccordionItem value="feedback" className="border-none">
          <AccordionTrigger className="text-sm font-medium text-gray-700 py-2">
            提供反馈（可选）
          </AccordionTrigger>
          <AccordionContent className="space-y-3 pt-2">
            <RadioGroup value={feedbackCategory} onValueChange={setFeedbackCategory}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="suggestion_correct" id="correct" />
                <Label htmlFor="correct" className="text-sm">
                  建议正确
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="suggestion_partially_correct" id="partial" />
                <Label htmlFor="partial" className="text-sm">
                  建议部分正确
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="suggestion_incorrect" id="incorrect" />
                <Label htmlFor="incorrect" className="text-sm">
                  建议错误
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="rule_needs_adjustment" id="rule-adjust" />
                <Label htmlFor="rule-adjust" className="text-sm">
                  规则需要调整
                </Label>
              </div>
            </RadioGroup>

            <Textarea
              value={feedbackNotes}
              onChange={(e) => setFeedbackNotes(e.target.value)}
              placeholder="详细反馈..."
              rows={3}
              className="text-sm"
            />
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* AI Confidence (if applicable) */}
      {selectedIssue.engine === 'ai' && selectedIssue.confidence && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">AI 置信度</span>
            <span className="text-sm font-semibold text-blue-900">
              {(selectedIssue.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${selectedIssue.confidence * 100}%` }}
            />
          </div>
          <p className="text-xs text-blue-700 mt-2">
            {selectedIssue.confidence > 0.9 && '高置信度建议'}
            {selectedIssue.confidence > 0.7 && selectedIssue.confidence <= 0.9 && '中等置信度建议'}
            {selectedIssue.confidence <= 0.7 && '低置信度建议，建议人工判断'}
          </p>
        </div>
      )}
    </div>
  ) : (
    // Empty State
    <div className="flex flex-col items-center justify-center h-full text-gray-400 p-6">
      <FileQuestion className="w-16 h-16 mb-4" />
      <p className="text-sm text-center">
        选择左侧的问题查看详情
      </p>
      <p className="text-xs text-center mt-2">
        或使用快捷键 ↑/↓ 导航
      </p>
    </div>
  )}
</aside>
```

---

### 6. Footer Progress Bar

**Purpose:** 底部固定进度条，显示审核进度

**Structure:**
```tsx
<footer className="fixed bottom-0 left-0 right-0 h-12 bg-white border-t border-gray-200 z-40">
  <div className="flex items-center justify-between h-full px-6">
    {/* Left: Progress Text */}
    <div className="flex items-center space-x-4 text-sm">
      <span className="font-medium text-gray-900">
        进度: {processedCount} / {totalIssues} 已处理
      </span>
      <span className="text-gray-500">
        ({Math.round((processedCount / totalIssues) * 100)}%)
      </span>
    </div>

    {/* Center: Progress Bar */}
    <div className="flex-1 mx-8">
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${(processedCount / totalIssues) * 100}%` }}
        />
      </div>
    </div>

    {/* Right: Issue Counts */}
    <div className="flex items-center space-x-4 text-sm">
      <div className="flex items-center space-x-1">
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <span className="font-medium">{criticalCount}</span>
      </div>
      <div className="flex items-center space-x-1">
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <span className="font-medium">{warningCount}</span>
      </div>
      <div className="flex items-center space-x-1">
        <div className="w-3 h-3 rounded-full bg-blue-500" />
        <span className="font-medium">{infoCount}</span>
      </div>
    </div>
  </div>
</footer>
```

---

## 🎭 Interactions & Animations

### Smooth Transitions

```css
/* All transitions use ease-out timing */
.transition-standard {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Hover effects */
.interactive-element:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Active (pressed) state */
.interactive-element:active {
  transform: scale(0.98);
}
```

### Scroll Behavior

```typescript
// Smooth scroll to issue position
function scrollToIssue(issue: ProofreadingIssue) {
  const element = document.querySelector(`[data-issue-id="${issue.id}"]`);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'nearest'
    });
  }
}
```

### Loading States

```tsx
// Skeleton loader for issue list
<div className="space-y-4 p-4">
  {[...Array(10)].map((_, i) => (
    <div key={i} className="space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  ))}
</div>
```

---

## 📱 Responsive Design

### Breakpoints
- **xs**: < 640px
- **sm**: 640px - 768px
- **md**: 768px - 1024px
- **lg**: 1024px - 1280px
- **xl**: ≥ 1280px

### Layout Adaptations

**Mobile (<768px):**
- 单栏布局 + Tab切换
- 底部Drawer显示问题详情
- 简化过滤控件

**Tablet (768px - 1024px):**
- 两栏布局（隐藏问题列表）
- 左侧：文章内容
- 右侧：问题详情
- 底部Drawer显示问题列表

**Desktop (≥1280px):**
- 三栏完整布局
- 所有功能可见

---

## 🎹 Keyboard Shortcuts

| 快捷键 | 功能 |
|--------|------|
| `A` | Accept current issue |
| `R` | Reject current issue |
| `E` | Focus on custom edit input |
| `↑` / `K` | Previous issue |
| `↓` / `J` | Next issue |
| `Cmd/Ctrl + S` | Save draft |
| `Cmd/Ctrl + Enter` | Complete review |
| `Esc` | Close detail panel |
| `Cmd/Ctrl + F` | Focus search |
| `/` | Focus search (alternative) |
| `1-3` | Filter by severity (1=Critical, 2=Warning, 3=Info) |
| `Space` | Toggle checkbox for current issue |

---

## 🎨 Color Palette

### Severity Colors
- **Critical**: Red 500 (#EF4444)
- **Warning**: Yellow 500 (#F59E0B)
- **Info**: Blue 500 (#3B82F6)

### Decision Status Colors
- **Accepted**: Green 500 (#10B981)
- **Rejected**: Gray 400 (#9CA3AF)
- **Modified**: Purple 500 (#A855F7)
- **Pending**: Gray 300 (#D1D5DB)

### UI Colors (Tailwind)
- **Primary**: Blue 600 (#2563EB)
- **Secondary**: Gray 600 (#4B5563)
- **Background**: White (#FFFFFF)
- **Surface**: Gray 50 (#F9FAFB)
- **Border**: Gray 200 (#E5E7EB)
- **Text Primary**: Gray 900 (#111827)
- **Text Secondary**: Gray 600 (#4B5563)

---

## 📦 Component Dependencies

### Required Design System Components
- Button
- Input
- Textarea
- Select
- Checkbox
- RadioGroup
- Badge
- Separator
- Accordion
- ToggleGroup
- Skeleton
- Tooltip

### External Libraries
- react-markdown: Markdown rendering
- react-highlight-words: Text highlighting (alternative)
- react-hotkeys-hook: Keyboard shortcuts
- react-window: Virtual scrolling (performance)
- lucide-react: Icons

---

**Document Version:** 1.0
**Created:** 2025-11-07
**Status:** Ready for Review
