# Codex CLI 问题验证与解决方案

**生成时间**: 2025-11-06
**验证状态**: ✅ 所有问题已验证

---

## 📋 问题验证摘要

| 级别 | 问题数 | 已验证 | 状态 |
|------|--------|--------|------|
| **High** | 5 | 5 | 🔴 Critical |
| **Medium** | 6 | 6 | 🟡 Important |
| **Low** | 1 | 1 | 🟢 Nice to have |
| **总计** | **12** | **12** | ✅ 100% |

---

## 🔴 High 级别问题（Critical）

### H1: API 端点错误 - Review页面使用错误的数据源

**问题描述**:
- **当前实现**: `ProofreadingReviewPage` 调用 `GET /v1/worklist/:id` (frontend/src/pages/ProofreadingReviewPage.tsx:48)
- **规范要求**: 应调用 `GET /v1/articles/{id}` (specs/004-google-drive-auto-sync/spec.md:58, FR-9)
- **影响**: 无法获取 suggested body, meta description, SEO keywords, FAQ proposals

**验证结果**: ✅ 确认
```typescript
// frontend/src/pages/ProofreadingReviewPage.tsx:42-50
const { data: worklistItem } = useQuery<WorklistItemDetail>({
  queryKey: ['worklist-detail', id],
  queryFn: () => worklistAPI.get(Number(id)),  // ❌ 调用worklist API而非article API
  enabled: Boolean(id),
});
```

**根本原因**:
1. Worklist和Article职责混淆
2. ProofreadingReviewPage应该基于Article而非WorklistItem
3. WorklistItem只是同步元数据，Article才包含校对结果

---

### H2: 数据库schema缺失 - Article模型缺少所有suggested_*字段

**问题描述**:
- **workflow文档要求** (backend/docs/article_proofreading_seo_workflow.md:365-393):
  - `suggested_content` (Text)
  - `suggested_content_changes` (JSONB)
  - `suggested_meta_description` (Text)
  - `suggested_meta_reasoning` (Text)
  - `suggested_meta_score` (Float)
  - `suggested_seo_keywords` (JSONB)
  - `suggested_keywords_reasoning` (Text)
  - `suggested_keywords_score` (Float)
  - `paragraph_suggestions` (JSONB)
  - `paragraph_split_suggestions` (JSONB)
  - `faq_schema_proposals` (JSONB)
  - `suggested_generated_at` (DateTime)
  - `ai_model_used` (String)
  - `generation_cost` (Decimal)

- **当前实现** (backend/src/models/article.py:42-151):
  - ❌ 以上字段**全部缺失**
  - 只有基础字段: title, body, status, tags, categories

**验证结果**: ✅ 确认
```bash
$ grep -n "suggested_" backend/src/models/article.py
# No matches found
```

**影响范围**:
1. 无法存储AI生成的优化内容
2. 无法进行左右diff对比
3. Meta/SEO/FAQ卡片无数据源
4. 整个审核流程无法完成

---

### H3: UI缺少核心功能 - 单列显示而非左右diff

**问题描述**:
- **规范要求** (specs/003-proofreading-review-ui/ui-design-spec.md:2372-2421, FR-9):
  - 左右分屏diff（原文 vs 建议）
  - Meta/SEO/FAQ对比卡片
  - 全局accept/reject actions
  - 段落级操作

- **当前实现** (frontend/src/components/ProofreadingReview/ProofreadingArticleContent.tsx:22-110):
  - ✅ 单列文章显示
  - ✅ 高亮问题位置
  - ❌ 没有左右diff
  - ❌ 没有Meta/SEO/FAQ卡片
  - ❌ 没有全局批量操作

**验证结果**: ✅ 确认
```typescript
// ProofreadingArticleContent.tsx - 只有单列渲染
return (
  <div className="mx-auto max-w-4xl">
    <h1 className="mb-8 text-3xl font-bold text-gray-900">{title}</h1>
    <div className="prose prose-lg max-w-none">{renderedContent}</div>
    {/* ❌ 缺少：左侧原文列、右侧建议列、Meta/SEO/FAQ cards */}
  </div>
);
```

---

### H4: viewMode功能未实现 - 状态存在但无控件和diff渲染

**问题描述**:
- **当前状态** (frontend/src/pages/ProofreadingReviewPage.tsx:38):
  ```typescript
  const [viewMode] = useState<ViewMode>('original'); // 存在但只读
  ```
- **缺失功能**:
  - ❌ Original/Preview/Diff 切换按钮（specs/003-proofreading-review-ui/ui-design-spec.md:181-235）
  - ❌ Diff可视化（红色删除、绿色添加）
  - ❌ viewMode更新逻辑

**验证结果**: ✅ 确认
- ProofreadingArticleContent.tsx:81-85 只简单替换文本，没有真正的diff渲染

---

### H5: 审阅备注无法输入 - reviewNotes状态未绑定UI

**问题描述**:
- **状态定义** (frontend/src/pages/ProofreadingReviewPage.tsx:37):
  ```typescript
  const [reviewNotes, setReviewNotes] = useState(''); // 状态存在
  ```
- **问题**: 没有对应的 `<textarea>` 或 `<Input>` 组件绑定此状态
- **规范要求** (specs/003-proofreading-review-ui/ui-design-spec.md:763-769):
  - 备注输入框（多行textarea）
  - 支持Markdown
  - 最终提交时包含在payload中

**验证结果**: ✅ 确认
```typescript
// ProofreadingReviewPage.tsx:54-64 - 提交时使用reviewNotes
return worklistAPI.saveReviewDecisions(Number(id), {
  decisions: decisionsArray,
  review_notes: reviewNotes || undefined, // ✅ 使用了状态
  transition_to: transitionTo,
});
// ❌ 但整个组件中没有<textarea value={reviewNotes} onChange={...}/>
```

---

## 🟡 Medium 级别问题（Important）

### M1: Header和Stats Bar不符合设计规范

**缺失元素**:
- ❌ 面包屑导航（Home > Worklist > 文章标题）
- ❌ Cancel 按钮
- ❌ Stats Bar sticky定位
- ❌ View mode switcher（Original/Preview/Diff）

**当前实现** vs **规范**:
| 组件 | 当前 | 规范要求 | 状态 |
|------|------|----------|------|
| ProofreadingReviewHeader | 简单header | Sticky breadcrumbs + Save/Cancel/Complete | ❌ |
| ReviewStatsBar | 基础stats显示 | Sticky + View toggle + Critical/Warning counts | ❌ |

---

### M2: 无法查看历史决策

**问题**:
- 后端只返回 `decision_status`, `decision_id` (backend/src/api/routes/worklist_routes.py:404-411)
- 前端只显示当前会话的 `decisions[issueId]` (frontend/src/pages/ProofreadingReviewPage.tsx:276-281)
- **缺失**: 已保存的 rationale, modified_content, feedback, reviewer

**影响**: 用户重新打开审核页面时，看不到之前的决策和理由

---

### M3: Issue列表功能缺失

**缺少**:
- ❌ 规则类别过滤器（A-F class）
- ❌ AI confidence badge
- ❌ 批量操作工具栏（Select All, Batch Accept/Reject）

---

### M4: 键盘快捷键内存泄漏

**问题代码** (frontend/src/pages/ProofreadingReviewPage.tsx:141-175):
```typescript
useState(() => {
  const handler = (e: KeyboardEvent) => { /* ... */ };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler); // ❌ useState不会调用cleanup
});
```

**正确做法**: 使用 `useEffect`

---

### M5: 缺少核心UI组件

| 组件 | 用途 | 状态 |
|------|------|------|
| 段落建议Modal | 显示分段建议和优化 | ❌ 不存在 |
| FAQ Selector | 选择FAQ schema方案 | ❌ 不存在 |
| Meta卡片 | 对比原meta vs 建议meta | ❌ 不存在 |
| SEO卡片 | 对比原keywords vs 建议keywords | ❌ 不存在 |

---

### M6: 没有自动选择第一个issue

**期望**: 数据加载后自动选择 issue #1 并在detail panel显示
**当前**: `selectedIssue` 为 `null` 直到用户点击

---

## 🟢 Low 级别问题

### L1: 缺少自动化测试

**要求** (specs/004-google-drive-auto-sync/spec.md:197-205):
- ProofreadingReviewPage 单元测试
- WorklistDetailDrawer 单元测试
- E2E 测试覆盖完整审核流程

**当前**: `frontend/tests/` 中没有相关测试文件

---

## 🎯 解决方案框架

### Phase 1: 数据层修复（High Priority）

#### 1.1 添加 Article suggested_* 字段
```python
# backend/src/models/article.py
class Article(Base):
    # ... existing fields ...

    # AI优化内容
    suggested_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_content_changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Meta建议
    suggested_meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_meta_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_meta_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # SEO建议
    suggested_seo_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    suggested_keywords_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_keywords_score: Mapped[float | None] = mapped_column(JSONB, nullable=True)

    # 段落和FAQ建议
    paragraph_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    paragraph_split_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    faq_schema_proposals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 生成元数据
    suggested_generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
```

**Migration**:
```bash
alembic revision --autogenerate -m "Add article suggested fields for proofreading workflow"
```

#### 1.2 创建 Article Review API
```python
# backend/src/api/routes/article_routes.py
@router.get("/articles/{article_id}/review-data")
async def get_article_review_data(article_id: int) -> ArticleReviewResponse:
    """
    返回审核所需的完整数据：
    - 原文 content + 建议 suggested_content
    - Meta/SEO/FAQ 对比数据
    - 校对issues + 已有decisions
    - 段落建议
    """
    pass
```

#### 1.3 更新 Schema
```python
# backend/src/api/schemas/article.py
class ArticleReviewResponse(BaseSchema):
    id: int
    title: str

    # 内容对比
    original_content: str
    suggested_content: str | None
    content_changes: dict | None

    # Meta对比
    original_meta: str | None
    suggested_meta: str | None
    meta_reasoning: str | None
    meta_score: float | None

    # SEO对比
    original_keywords: list[str]
    suggested_keywords: dict | None
    keywords_reasoning: str | None
    keywords_score: float | None

    # FAQ建议
    faq_proposals: dict | None

    # 段落建议
    paragraph_suggestions: dict | None

    # 校对issues + decisions
    proofreading_issues: list[ProofreadingIssue]
    existing_decisions: list[ProofreadingDecision]
```

---

### Phase 2: 前端UI重构（High Priority）

#### 2.1 ProofreadingReviewPage 重构
```typescript
// frontend/src/pages/ProofreadingReviewPage.tsx

// ✅ 修复：调用 article API
const { data: articleReview } = useQuery<ArticleReviewData>({
  queryKey: ['article-review', articleId],
  queryFn: () => articleAPI.getReviewData(Number(articleId)), // 正确的API
  enabled: Boolean(articleId),
});

// ✅ 修复：自动选择第一个issue
useEffect(() => {
  if (issues.length > 0 && !selectedIssue) {
    setSelectedIssue(issues[0]);
  }
}, [issues, selectedIssue]);

// ✅ 修复：键盘快捷键
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'j') selectNextIssue();
    if (e.key === 'k') selectPreviousIssue();
    if (e.key === 'a') acceptCurrentIssue();
    if (e.key === 'r') rejectCurrentIssue();
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [selectedIssue, issues]);
```

#### 2.2 添加左右Diff组件
```typescript
// frontend/src/components/ProofreadingReview/DiffView.tsx
export function DiffView({
  original,
  suggested,
  viewMode
}: DiffViewProps) {
  return (
    <div className="grid grid-cols-2 gap-6">
      {/* 左侧：原文 */}
      <div className="border-r pr-6">
        <h3 className="font-semibold mb-4">原文</h3>
        <div className="prose">{renderOriginal(original)}</div>
      </div>

      {/* 右侧：建议 */}
      <div className="pl-6">
        <h3 className="font-semibold mb-4">AI建议</h3>
        <div className="prose">{renderSuggested(suggested)}</div>
      </div>
    </div>
  );
}
```

#### 2.3 添加 Meta/SEO/FAQ 卡片
```typescript
// frontend/src/components/ProofreadingReview/MetaComparisonCard.tsx
export function MetaComparisonCard({ original, suggested, reasoning }: Props) {
  return (
    <Card>
      <CardHeader>Meta Description 对比</CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label>原Meta（{original.length}字）</Label>
            <p className="text-sm text-gray-600">{original}</p>
          </div>
          <div>
            <Label>建议Meta（{suggested.length}字）✨</Label>
            <p className="text-sm text-green-600">{suggested}</p>
            <p className="text-xs text-gray-500 mt-1">{reasoning}</p>
          </div>
          <Button onClick={acceptMeta}>采用建议</Button>
        </div>
      </CardContent>
    </Card>
  );
}

// SEOKeywordsCard, FAQSelectorCard 类似结构
```

#### 2.4 添加 Review Notes 输入框
```typescript
// 在 ProofreadingReviewPage 底部添加
<div className="mt-8 border-t pt-6">
  <Label>审核备注</Label>
  <Textarea
    value={reviewNotes}
    onChange={(e) => setReviewNotes(e.target.value)}
    placeholder="记录审核过程中的想法、改进建议等..."
    rows={4}
    className="mt-2"
  />
</div>
```

#### 2.5 添加 ViewMode 切换器
```typescript
// frontend/src/components/ProofreadingReview/ViewModeSwitcher.tsx
export function ViewModeSwitcher({ mode, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
      <button
        className={cn('px-4 py-2 rounded', mode === 'original' && 'bg-white shadow')}
        onClick={() => onChange('original')}
      >
        原文
      </button>
      <button
        className={cn('px-4 py-2 rounded', mode === 'diff' && 'bg-white shadow')}
        onClick={() => onChange('diff')}
      >
        Diff对比
      </button>
      <button
        className={cn('px-4 py-2 rounded', mode === 'preview' && 'bg-white shadow')}
        onClick={() => onChange('preview')}
      >
        预览
      </button>
    </div>
  );
}
```

---

### Phase 3: 增强功能（Medium Priority）

#### 3.1 更新 Header 组件
```typescript
// frontend/src/components/ProofreadingReview/ProofreadingReviewHeader.tsx
export function ProofreadingReviewHeader({ article, onSave, onCancel, onComplete }: Props) {
  return (
    <div className="sticky top-0 z-50 bg-white border-b">
      {/* Breadcrumb */}
      <div className="px-6 py-3">
        <nav className="flex items-center text-sm text-gray-600">
          <Link to="/">首页</Link>
          <ChevronRight className="w-4 h-4 mx-2" />
          <Link to="/worklist">Worklist</Link>
          <ChevronRight className="w-4 h-4 mx-2" />
          <span className="text-gray-900">{article.title}</span>
        </nav>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">校对审核</h1>
        <div className="flex gap-3">
          <Button variant="outline" onClick={onCancel}>取消</Button>
          <Button variant="outline" onClick={onSave}>保存草稿</Button>
          <Button onClick={onComplete}>完成审核</Button>
        </div>
      </div>
    </div>
  );
}
```

#### 3.2 Issue List 增强
```typescript
// 添加分类过滤
<Select value={categoryFilter} onChange={setCategoryFilter}>
  <option value="all">所有规则</option>
  <option value="A">A类 - 事实错误</option>
  <option value="B">B类 - 逻辑问题</option>
  <option value="C">C类 - 表达建议</option>
  <option value="D">D类 - 格式优化</option>
  <option value="E">E类 - SEO优化</option>
  <option value="F">F类 - 关键错误</option>
</Select>

// 显示 AI confidence
<Badge variant={getConfidenceColor(issue.confidence)}>
  {(issue.confidence * 100).toFixed(0)}% 置信度
</Badge>
```

#### 3.3 加载历史决策
```typescript
// backend/src/api/routes/article_routes.py
@router.get("/articles/{article_id}/review-data")
async def get_article_review_data(article_id: int):
    # 加载已有决策
    existing_decisions = await db.execute(
        select(ProofreadingDecision)
        .where(ProofreadingDecision.article_id == article_id)
    )

    return {
        # ...
        "existing_decisions": [
            {
                "issue_id": d.issue_id,
                "decision_type": d.decision_type,
                "rationale": d.rationale,
                "modified_content": d.modified_content,
                "reviewer": d.reviewer,
                "decided_at": d.created_at,
            }
            for d in existing_decisions
        ]
    }

// 前端hydrate
useEffect(() => {
  if (articleReview?.existing_decisions) {
    const hydratedDecisions = articleReview.existing_decisions.reduce(
      (acc, d) => ({ ...acc, [d.issue_id]: d }),
      {}
    );
    setDecisions(hydratedDecisions);
  }
}, [articleReview]);
```

---

### Phase 4: 测试覆盖（Low Priority）

#### 4.1 单元测试
```typescript
// frontend/tests/components/ProofreadingReview/ProofreadingReviewPage.test.tsx
describe('ProofreadingReviewPage', () => {
  it('should load article review data on mount', async () => {
    // ...
  });

  it('should auto-select first issue', () => {
    // ...
  });

  it('should handle keyboard shortcuts', () => {
    // ...
  });

  it('should save review notes with decisions', () => {
    // ...
  });
});

// frontend/tests/components/Worklist/WorklistDetailDrawer.test.tsx
describe('WorklistDetailDrawer', () => {
  it('should display article metadata', () => {
    // ...
  });

  it('should navigate to proofreading review', () => {
    // ...
  });
});
```

#### 4.2 E2E测试
```typescript
// frontend/e2e/proofreading-workflow.spec.ts
test('complete proofreading review workflow', async ({ page }) => {
  // 1. 打开worklist
  await page.goto('/worklist');

  // 2. 点击进入校对
  await page.click('[data-testid="enter-review-123"]');

  // 3. 验证diff view加载
  await expect(page.locator('.diff-view')).toBeVisible();

  // 4. Accept第一个issue
  await page.keyboard.press('a');

  // 5. 输入备注
  await page.fill('[data-testid="review-notes"]', '测试备注');

  // 6. 完成审核
  await page.click('[data-testid="complete-review"]');

  // 7. 验证状态更新
  await expect(page.locator('[data-status="ready_to_publish"]')).toBeVisible();
});
```

---

## 📅 实施计划

### Sprint 1: 数据层修复（3-4天）
- [ ] 添加Article suggested_*字段（migration）
- [ ] 创建 `/v1/articles/{id}/review-data` API
- [ ] 更新ArticleReviewResponse schema
- [ ] 后端单元测试

### Sprint 2: 核心UI重构（5-7天）
- [ ] ProofreadingReviewPage API调用修复
- [ ] 实现左右DiffView组件
- [ ] 添加Meta/SEO/FAQ对比卡片
- [ ] 绑定reviewNotes输入框
- [ ] ViewMode切换器
- [ ] 键盘快捷键修复

### Sprint 3: 功能增强（3-4天）
- [ ] 更新Header和Stats Bar（breadcrumbs, sticky, cancel）
- [ ] Issue列表增强（分类过滤、confidence显示）
- [ ] 加载历史决策
- [ ] 自动选择第一个issue
- [ ] 段落建议Modal

### Sprint 4: 测试和优化（2-3天）
- [ ] 单元测试覆盖
- [ ] E2E测试
- [ ] 性能优化（NFR-4: diff渲染性能）
- [ ] 文档更新

**总计**: 13-18 工作日

---

## ✅ 验证标准

### 功能验证
- [ ] ProofreadingReviewPage 从 `/v1/articles/{id}/review-data` 加载数据
- [ ] 左右diff正确显示原文和建议
- [ ] Meta/SEO/FAQ卡片正确显示对比数据
- [ ] ViewMode切换器工作正常
- [ ] reviewNotes可以输入并正确提交
- [ ] 键盘快捷键无内存泄漏
- [ ] 历史决策正确加载和显示
- [ ] Issue列表支持分类过滤
- [ ] 自动选择第一个issue

### 性能验证
- [ ] NFR-4: 2000行文本diff渲染FPS ≥ 40
- [ ] 审核页面加载时间 < 2秒

### 测试验证
- [ ] 单元测试覆盖率 > 80%
- [ ] E2E测试覆盖完整workflow

---

## 🚨 风险和依赖

### 高风险项
1. **数据库migration**: suggested_*字段添加可能影响现有数据
   - **缓解**: 所有新字段nullable=True，不影响现有记录

2. **API breaking change**: 从worklist API改为article API
   - **缓解**: 保留旧API，前端逐步迁移

### 依赖项
1. `WorklistItem.article_id` 必须正确关联（已实现）
2. Proofreading service必须生成suggested_*数据（需验证）
3. ProofreadingDecision表已存在（已实现）

---

## 📊 优先级矩阵

| 问题 | 影响 | 工作量 | 优先级 |
|------|------|--------|--------|
| H1: API端点错误 | Critical | 低 | P0 |
| H2: Schema缺失 | Critical | 中 | P0 |
| H3: UI缺少diff | Critical | 高 | P0 |
| H4: viewMode未实现 | High | 中 | P1 |
| H5: reviewNotes未绑定 | High | 低 | P1 |
| M1-M6: Medium问题 | Medium | 中 | P2 |
| L1: 测试缺失 | Low | 高 | P3 |

---

## 总结

所有12个问题均已验证并确认存在。核心问题是**数据契约错误**（使用worklist而非article）和**UI不符合规范**（单列而非diff）。建议按照4个Sprint逐步修复，优先解决P0问题以恢复核心功能。
