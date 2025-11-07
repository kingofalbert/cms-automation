# Proofreading Review 修复实施计划

**基于**: CODEX_ISSUES_ANALYSIS.md
**优先级**: P0 - Critical
**预估时间**: 13-18 工作日

---

## 🎯 实施策略

### 方案选择

**选项A: 渐进式修复**（推荐）
- ✅ 降低风险
- ✅ 可以分阶段上线
- ✅ 保留现有功能
- ❌ 耗时较长

**选项B: 全面重写**
- ✅ 彻底解决架构问题
- ❌ 高风险
- ❌ 长时间功能不可用

**决策**: 采用**选项A**，按照4个Sprint渐进式修复。

---

## 📋 Sprint 详细规划

### Sprint 1: 数据层修复 (3-4天)

**目标**: 建立正确的数据契约，支持完整的审核workflow

#### Task 1.1: Article模型扩展 (1天)
```python
# backend/src/models/article.py

# 新增字段清单：
- suggested_content: Text (AI优化后的正文)
- suggested_content_changes: JSONB (diff数据结构)
- suggested_meta_description: Text
- suggested_meta_reasoning: Text
- suggested_meta_score: Float (0-1)
- suggested_seo_keywords: JSONB
- suggested_keywords_reasoning: Text
- suggested_keywords_score: Float
- paragraph_suggestions: JSONB
- paragraph_split_suggestions: JSONB
- faq_schema_proposals: JSONB
- suggested_generated_at: DateTime
- ai_model_used: String(100)
- generation_cost: Numeric(10, 4)
```

**验收标准**:
- [ ] Alembic migration成功生成
- [ ] 所有字段nullable=True，不影响现有数据
- [ ] Model单元测试通过

#### Task 1.2: Article Review API (1.5天)
```python
# backend/src/api/routes/article_routes.py

@router.get("/articles/{article_id}/review-data")
async def get_article_review_data(
    article_id: int,
    db: AsyncSession = Depends(get_db)
) -> ArticleReviewResponse:
    """
    返回审核页面所需的完整数据
    """
    article = await get_article_with_proofreading_data(article_id, db)

    # 加载已有决策
    existing_decisions = await get_proofreading_decisions(article_id, db)

    return ArticleReviewResponse(
        id=article.id,
        title=article.title,
        # 内容对比
        original_content=article.body,
        suggested_content=article.suggested_content,
        content_changes=article.suggested_content_changes,
        # Meta对比
        original_meta=article.meta_description,
        suggested_meta=article.suggested_meta_description,
        meta_reasoning=article.suggested_meta_reasoning,
        meta_score=article.suggested_meta_score,
        # SEO对比
        original_keywords=article.seo_keywords or [],
        suggested_keywords=article.suggested_seo_keywords,
        keywords_reasoning=article.suggested_keywords_reasoning,
        keywords_score=article.suggested_keywords_score,
        # FAQ建议
        faq_proposals=article.faq_schema_proposals,
        # 段落建议
        paragraph_suggestions=article.paragraph_suggestions,
        # 校对数据
        proofreading_issues=article.proofreading_issues or [],
        existing_decisions=[
            ProofreadingDecisionDetail.from_orm(d)
            for d in existing_decisions
        ],
        # 元数据
        ai_model_used=article.ai_model_used,
        generated_at=article.suggested_generated_at,
    )
```

**验收标准**:
- [ ] API endpoint正确返回数据
- [ ] existing_decisions正确加载
- [ ] Swagger文档更新
- [ ] 集成测试通过

#### Task 1.3: Schema定义 (0.5天)
```python
# backend/src/api/schemas/article.py

class ContentComparison(BaseSchema):
    original: str
    suggested: str | None
    changes: dict | None

class MetaComparison(BaseSchema):
    original: str | None
    suggested: str | None
    reasoning: str | None
    score: float | None
    length_original: int
    length_suggested: int

class SEOComparison(BaseSchema):
    original_keywords: list[str]
    suggested_keywords: dict | None
    reasoning: str | None
    score: float | None

class ProofreadingDecisionDetail(BaseSchema):
    issue_id: str
    decision_type: DecisionType
    rationale: str | None
    modified_content: str | None
    reviewer: str
    decided_at: datetime

class ArticleReviewResponse(BaseSchema):
    id: int
    title: str

    # 内容对比
    content: ContentComparison

    # Meta对比
    meta: MetaComparison

    # SEO对比
    seo: SEOComparison

    # FAQ建议
    faq_proposals: list[FAQProposal] | None

    # 段落建议
    paragraph_suggestions: list[ParagraphSuggestion] | None

    # 校对数据
    proofreading_issues: list[ProofreadingIssue]
    existing_decisions: list[ProofreadingDecisionDetail]

    # 元数据
    ai_model_used: str | None
    generated_at: datetime | None
```

**验收标准**:
- [ ] Schema清晰定义所有字段
- [ ] Pydantic validation正确
- [ ] Type hints完整

#### Task 1.4: 测试 (1天)
```python
# backend/tests/api/test_article_routes.py

async def test_get_article_review_data_with_suggestions():
    """测试带建议的审核数据加载"""
    article = await create_article_with_suggestions(
        suggested_content="优化后的内容",
        suggested_meta_description="优化后的Meta",
        faq_proposals=[{...}]
    )

    response = await client.get(f"/v1/articles/{article.id}/review-data")

    assert response.status_code == 200
    data = response.json()
    assert data["content"]["suggested"] == "优化后的内容"
    assert data["meta"]["suggested"] == "优化后的Meta"
    assert len(data["faq_proposals"]) > 0

async def test_get_article_review_data_with_existing_decisions():
    """测试历史决策加载"""
    article = await create_article_with_issues()
    decision = await create_proofreading_decision(
        article_id=article.id,
        issue_id="issue-1",
        decision_type="accepted",
        rationale="理由充分"
    )

    response = await client.get(f"/v1/articles/{article.id}/review-data")

    data = response.json()
    assert len(data["existing_decisions"]) == 1
    assert data["existing_decisions"][0]["issue_id"] == "issue-1"
    assert data["existing_decisions"][0]["decision_type"] == "accepted"
```

**验收标准**:
- [ ] 所有单元测试通过
- [ ] 集成测试覆盖核心场景
- [ ] 测试覆盖率 > 80%

---

### Sprint 2: 核心UI重构 (5-7天)

**目标**: 实现符合规范的ProofreadingReviewPage UI

#### Task 2.1: API调用修复 (0.5天)
```typescript
// frontend/src/services/article.ts

export const articleAPI = {
  /**
   * 获取审核页面所需的完整数据
   */
  getReviewData: (articleId: number) =>
    api.get<ArticleReviewData>(`/v1/articles/${articleId}/review-data`),

  /**
   * 保存审核决策
   */
  saveReviewDecisions: (articleId: number, payload: ReviewDecisionsPayload) =>
    api.post(`/v1/articles/${articleId}/proofreading-decisions`, payload),
};

// frontend/src/pages/ProofreadingReviewPage.tsx

// ✅ 从URL获取articleId（不是worklistId）
const { articleId } = useParams<{ articleId: string }>();

// ✅ 调用正确的API
const { data: articleReview } = useQuery<ArticleReviewData>({
  queryKey: ['article-review', articleId],
  queryFn: () => articleAPI.getReviewData(Number(articleId)),
  enabled: Boolean(articleId),
});
```

**验收标准**:
- [ ] URL路由改为 `/articles/:articleId/review`
- [ ] 正确调用 `/v1/articles/{id}/review-data`
- [ ] 数据加载成功

#### Task 2.2: 左右Diff视图 (2天)
```typescript
// frontend/src/components/ProofreadingReview/DiffView.tsx

export function DiffView({ original, suggested, viewMode, issues, decisions }: Props) {
  if (viewMode === 'original') {
    return <SingleColumnView content={original} />;
  }

  if (viewMode === 'preview') {
    return <SingleColumnView content={applyAcceptedChanges(suggested, decisions)} />;
  }

  // viewMode === 'diff'
  return (
    <div className="grid grid-cols-2 gap-6 h-full">
      {/* 左侧：原文 */}
      <div className="border-r pr-6 overflow-y-auto">
        <div className="sticky top-0 bg-white py-2 border-b mb-4">
          <h3 className="font-semibold text-lg">原文</h3>
        </div>
        <OriginalContentView
          content={original}
          issues={issues}
          selectedIssue={selectedIssue}
          onIssueClick={onIssueClick}
        />
      </div>

      {/* 右侧：建议 */}
      <div className="pl-6 overflow-y-auto">
        <div className="sticky top-0 bg-white py-2 border-b mb-4">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            AI建议
            <Badge variant="success">✨ 优化版本</Badge>
          </h3>
        </div>
        <SuggestedContentView
          content={suggested}
          changes={changes}
          issues={issues}
          decisions={decisions}
        />
      </div>
    </div>
  );
}

// 使用 react-diff-viewer 或自定义diff算法
import ReactDiffViewer from 'react-diff-viewer-continued';

function renderDiffBlock(originalParagraph, suggestedParagraph) {
  return (
    <ReactDiffViewer
      oldValue={originalParagraph}
      newValue={suggestedParagraph}
      splitView={true}
      showDiffOnly={false}
      useDarkTheme={false}
    />
  );
}
```

**验收标准**:
- [ ] 左右两列正确显示
- [ ] 高亮问题位置
- [ ] Diff颜色清晰（红色删除，绿色添加）
- [ ] 滚动同步（可选）

#### Task 2.3: ViewMode切换器 (0.5天)
```typescript
// frontend/src/components/ProofreadingReview/ViewModeSwitcher.tsx

export function ViewModeSwitcher({ mode, onChange }: Props) {
  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
      <Button
        variant={mode === 'original' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onChange('original')}
      >
        <FileText className="w-4 h-4 mr-2" />
        原文
      </Button>
      <Button
        variant={mode === 'diff' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onChange('diff')}
      >
        <Columns className="w-4 h-4 mr-2" />
        Diff对比
      </Button>
      <Button
        variant={mode === 'preview' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onChange('preview')}
      >
        <Eye className="w-4 h-4 mr-2" />
        预览
      </Button>
    </div>
  );
}

// 在 ProofreadingReviewPage 中使用
const [viewMode, setViewMode] = useState<ViewMode>('diff'); // 默认diff模式
```

**验收标准**:
- [ ] 三个按钮正确显示
- [ ] 切换viewMode时内容正确更新
- [ ] 样式符合设计规范

#### Task 2.4: Meta/SEO/FAQ卡片 (1.5天)
```typescript
// frontend/src/components/ProofreadingReview/MetaComparisonCard.tsx

export function MetaComparisonCard({ meta, onAccept }: Props) {
  const lengthDiff = (meta.suggested?.length || 0) - (meta.original?.length || 0);

  return (
    <Card className="shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Meta Description 对比
          <Badge variant={meta.score > 0.8 ? 'success' : 'warning'}>
            得分: {(meta.score * 100).toFixed(0)}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 原Meta */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label>原Meta描述</Label>
            <span className="text-sm text-gray-500">
              {meta.original?.length || 0} 字
            </span>
          </div>
          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
            {meta.original || '（未设置）'}
          </p>
        </div>

        {/* 建议Meta */}
        {meta.suggested && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label className="flex items-center gap-2">
                AI建议
                <Sparkles className="w-4 h-4 text-yellow-500" />
              </Label>
              <span className={cn(
                "text-sm font-medium",
                lengthDiff > 0 ? "text-green-600" : "text-red-600"
              )}>
                {lengthDiff > 0 ? '+' : ''}{lengthDiff} 字
              </span>
            </div>
            <p className="text-sm text-green-700 bg-green-50 p-3 rounded border border-green-200">
              {meta.suggested}
            </p>
            {meta.reasoning && (
              <p className="text-xs text-gray-600 mt-2 italic">
                💡 {meta.reasoning}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="default"
            className="flex-1"
            onClick={() => onAccept(meta.suggested)}
            disabled={!meta.suggested}
          >
            <Check className="w-4 h-4 mr-2" />
            采用建议
          </Button>
          <Button variant="outline" className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            手动编辑
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// SEOKeywordsCard 类似结构
export function SEOKeywordsCard({ seo, onAccept }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>SEO关键词对比</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <Label>原关键词</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {seo.original_keywords.map(kw => (
                <Badge key={kw} variant="secondary">{kw}</Badge>
              ))}
            </div>
          </div>
          <div>
            <Label>建议关键词 ✨</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {seo.suggested_keywords?.map(kw => (
                <Badge key={kw} variant="success">{kw}</Badge>
              ))}
            </div>
          </div>
          <Button onClick={() => onAccept(seo.suggested_keywords)}>
            采用建议
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// FAQSelectorCard
export function FAQSelectorCard({ proposals, onSelect }: Props) {
  const [selectedProposal, setSelectedProposal] = useState<number>(0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>FAQ Schema 方案选择</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={selectedProposal.toString()} onValueChange={(v) => setSelectedProposal(Number(v))}>
          {proposals.map((proposal, idx) => (
            <TabsContent key={idx} value={idx.toString()}>
              <div className="space-y-2">
                {proposal.items.map((faq, faqIdx) => (
                  <div key={faqIdx} className="border p-3 rounded">
                    <p className="font-semibold">{faq.question}</p>
                    <p className="text-sm text-gray-600 mt-1">{faq.answer}</p>
                  </div>
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
        <Button onClick={() => onSelect(proposals[selectedProposal])}>
          选择此方案
        </Button>
      </CardContent>
    </Card>
  );
}
```

**验收标准**:
- [ ] 三张卡片正确显示
- [ ] 对比数据清晰
- [ ] 采用建议按钮工作正常
- [ ] 样式美观

#### Task 2.5: Review Notes输入框 (0.5天)
```typescript
// 在 ProofreadingReviewPage 底部添加

<div className="mt-8 border-t pt-6">
  <Label htmlFor="review-notes" className="text-base font-semibold">
    审核备注（可选）
  </Label>
  <p className="text-sm text-gray-600 mt-1 mb-3">
    记录审核过程中的想法、改进建议、需要讨论的问题等
  </p>
  <Textarea
    id="review-notes"
    value={reviewNotes}
    onChange={(e) => setReviewNotes(e.target.value)}
    placeholder="例如：
- 第3段的表达建议改为...
- 需要和作者确认数据来源
- SEO关键词已全部采用"
    rows={6}
    className="font-mono text-sm"
  />
  <p className="text-xs text-gray-500 mt-2">
    支持Markdown格式 · {reviewNotes.length} 字
  </p>
</div>
```

**验收标准**:
- [ ] 输入框正确绑定reviewNotes状态
- [ ] 保存时reviewNotes包含在payload中
- [ ] 支持多行输入

#### Task 2.6: 键盘快捷键修复 (0.5天)
```typescript
// 从 useState 改为 useEffect

// ❌ 错误做法
useState(() => {
  const handler = (e) => { /* ... */ };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
});

// ✅ 正确做法
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    // 忽略输入框内的快捷键
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return;
    }

    switch (e.key) {
      case 'j': // 下一个issue
        selectNextIssue();
        break;
      case 'k': // 上一个issue
        selectPreviousIssue();
        break;
      case 'a': // 接受
        acceptCurrentIssue();
        break;
      case 'r': // 拒绝
        rejectCurrentIssue();
        break;
      case 'm': // 修改
        openModifyModal();
        break;
      case 'Escape':
        closeDetailPanel();
        break;
    }
  };

  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [selectedIssue, issues, decisions]); // 依赖项

// 添加快捷键提示
<div className="fixed bottom-4 right-4 bg-gray-900 text-white p-3 rounded-lg text-xs">
  <div className="font-semibold mb-1">键盘快捷键</div>
  <div>J/K: 上/下一个问题</div>
  <div>A/R/M: 接受/拒绝/修改</div>
  <div>ESC: 关闭面板</div>
</div>
```

**验收标准**:
- [ ] 快捷键正确工作
- [ ] 组件卸载时listener正确清除
- [ ] 输入框内不触发快捷键
- [ ] 快捷键提示显示

---

### Sprint 3: 功能增强 (3-4天)

#### Task 3.1: Header和Breadcrumb (1天)
```typescript
// frontend/src/components/ProofreadingReview/ProofreadingReviewHeader.tsx

export function ProofreadingReviewHeader({
  article,
  worklistItem,
  onSave,
  onCancel,
  onComplete,
  isSaving,
}: Props) {
  return (
    <div className="sticky top-0 z-50 bg-white border-b shadow-sm">
      {/* Breadcrumb */}
      <div className="px-6 py-3 border-b bg-gray-50">
        <nav className="flex items-center text-sm text-gray-600">
          <Link to="/" className="hover:text-gray-900">
            <Home className="w-4 h-4" />
          </Link>
          <ChevronRight className="w-4 h-4 mx-2" />
          <Link to="/worklist" className="hover:text-gray-900">
            Worklist
          </Link>
          <ChevronRight className="w-4 h-4 mx-2" />
          <span className="text-gray-900 font-medium truncate max-w-md">
            {article.title}
          </span>
        </nav>
      </div>

      {/* Actions Bar */}
      <div className="px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">校对审核</h1>
          <p className="text-sm text-gray-600 mt-1">
            来自 Google Drive · 最后同步: {formatRelativeTime(worklistItem.synced_at)}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            onClick={onCancel}
            disabled={isSaving}
          >
            <X className="w-4 h-4 mr-2" />
            取消
          </Button>
          <Button
            variant="outline"
            onClick={onSave}
            disabled={isSaving || dirtyCount === 0}
          >
            <Save className="w-4 h-4 mr-2" />
            保存草稿
            {dirtyCount > 0 && (
              <Badge variant="secondary" className="ml-2">
                {dirtyCount}
              </Badge>
            )}
          </Button>
          <Button
            onClick={onComplete}
            disabled={!allIssuesDecided || isSaving}
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            完成审核
          </Button>
        </div>
      </div>
    </div>
  );
}
```

**验收标准**:
- [ ] Breadcrumb正确显示和导航
- [ ] 取消按钮有确认对话框
- [ ] 按钮状态正确（disabled逻辑）
- [ ] Sticky定位工作正常

#### Task 3.2: Stats Bar增强 (0.5天)
```typescript
// frontend/src/components/ProofreadingReview/ReviewStatsBar.tsx

export function ReviewStatsBar({
  issues,
  decisions,
  viewMode,
  onViewModeChange,
}: Props) {
  const stats = useMemo(() => {
    const total = issues.length;
    const critical = issues.filter(i => i.severity === 'critical').length;
    const warning = issues.filter(i => i.severity === 'warning').length;
    const decided = Object.keys(decisions).length;
    const accepted = Object.values(decisions).filter(d => d.decision_type === 'accepted').length;
    const rejected = Object.values(decisions).filter(d => d.decision_type === 'rejected').length;

    return { total, critical, warning, decided, accepted, rejected };
  }, [issues, decisions]);

  const progress = (stats.decided / stats.total) * 100;

  return (
    <div className="sticky top-[73px] h-14 bg-gray-50 border-b border-gray-200 z-40">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left: Stats */}
        <div className="flex items-center space-x-6">
          <h2 className="text-lg font-semibold text-gray-900">
            问题总览
          </h2>
          <div className="flex items-center space-x-4 text-sm">
            <StatBadge color="red" label="Critical" count={stats.critical} />
            <StatBadge color="yellow" label="Warning" count={stats.warning} />
            <StatBadge color="gray" label="Info" count={stats.total - stats.critical - stats.warning} />
          </div>
          <div className="flex items-center space-x-2 text-sm">
            <span className="text-gray-600">进度:</span>
            <span className="font-semibold text-gray-900">
              {stats.decided} / {stats.total}
            </span>
            <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Right: View Mode Switcher */}
        <ViewModeSwitcher mode={viewMode} onChange={onViewModeChange} />
      </div>
    </div>
  );
}

function StatBadge({ color, label, count }: { color: string; label: string; count: number }) {
  return (
    <div className="flex items-center">
      <div className={`w-2 h-2 rounded-full bg-${color}-500 mr-2`} />
      <span className="text-gray-600">{label}:</span>
      <span className="ml-1 font-medium text-gray-900">{count}</span>
    </div>
  );
}
```

**验收标准**:
- [ ] Stats正确计算和显示
- [ ] 进度条正确反映完成度
- [ ] ViewModeSwitcher集成
- [ ] Sticky定位正确（top-[73px]）

#### Task 3.3: Issue列表增强 (1天)
```typescript
// frontend/src/components/ProofreadingReview/ProofreadingIssueList.tsx

export function ProofreadingIssueList({
  issues,
  decisions,
  selectedIssue,
  onIssueClick,
  onBatchAccept,
  onBatchReject,
}: Props) {
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const filteredIssues = useMemo(() => {
    if (categoryFilter === 'all') return issues;
    return issues.filter(i => i.rule_category === categoryFilter);
  }, [issues, categoryFilter]);

  return (
    <div className="h-full flex flex-col">
      {/* Filter Header */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between">
          <Label>规则类别</Label>
          <span className="text-sm text-gray-600">
            {filteredIssues.length} 个问题
          </span>
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有规则</SelectItem>
            <SelectItem value="A">A类 - 事实错误</SelectItem>
            <SelectItem value="B">B类 - 逻辑问题</SelectItem>
            <SelectItem value="C">C类 - 表达建议</SelectItem>
            <SelectItem value="D">D类 - 格式优化</SelectItem>
            <SelectItem value="E">E类 - SEO优化</SelectItem>
            <SelectItem value="F">F类 - 关键错误</SelectItem>
          </SelectContent>
        </Select>

        {/* Batch Actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 bg-blue-50 p-3 rounded-lg">
            <span className="text-sm font-medium text-blue-900">
              已选择 {selectedIds.size} 个
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onBatchAccept(Array.from(selectedIds))}
            >
              批量接受
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onBatchReject(Array.from(selectedIds))}
            >
              批量拒绝
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedIds(new Set())}
            >
              取消选择
            </Button>
          </div>
        )}
      </div>

      {/* Issue List */}
      <div className="flex-1 overflow-y-auto">
        {filteredIssues.map((issue, idx) => (
          <IssueListItem
            key={issue.id}
            issue={issue}
            index={idx + 1}
            decision={decisions[issue.id]}
            isSelected={selectedIssue?.id === issue.id}
            isChecked={selectedIds.has(issue.id)}
            onSelect={() => onIssueClick(issue)}
            onCheck={(checked) => {
              const newSet = new Set(selectedIds);
              if (checked) {
                newSet.add(issue.id);
              } else {
                newSet.delete(issue.id);
              }
              setSelectedIds(newSet);
            }}
          />
        ))}
      </div>
    </div>
  );
}

function IssueListItem({ issue, index, decision, isSelected, isChecked, onSelect, onCheck }: Props) {
  return (
    <div
      className={cn(
        'p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors',
        isSelected && 'bg-blue-50 border-l-4 border-l-blue-600'
      )}
      onClick={onSelect}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <Checkbox
          checked={isChecked}
          onCheckedChange={onCheck}
          onClick={(e) => e.stopPropagation()}
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-gray-900">
              问题 #{index}
            </span>
            <Badge variant={getSeverityVariant(issue.severity)}>
              {issue.severity}
            </Badge>
            <Badge variant="outline">
              {issue.rule_category}类
            </Badge>
            {issue.confidence && (
              <Badge
                variant={getConfidenceVariant(issue.confidence)}
                className="text-xs"
              >
                {(issue.confidence * 100).toFixed(0)}%
              </Badge>
            )}
          </div>
          <p className="text-sm text-gray-700 line-clamp-2">
            {issue.explanation}
          </p>
          {decision && (
            <div className="mt-2">
              <DecisionBadge decision={decision} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

**验收标准**:
- [ ] 规则类别过滤器工作
- [ ] AI confidence正确显示
- [ ] 批量选择和操作正常
- [ ] 样式美观

#### Task 3.4: 加载历史决策 (0.5天)
```typescript
// frontend/src/pages/ProofreadingReviewPage.tsx

// Hydrate existing decisions
useEffect(() => {
  if (articleReview?.existing_decisions) {
    const hydrated = articleReview.existing_decisions.reduce(
      (acc, d) => ({
        ...acc,
        [d.issue_id]: {
          decision_type: d.decision_type,
          rationale: d.rationale,
          modified_content: d.modified_content,
          reviewer: d.reviewer,
          decided_at: d.decided_at,
        },
      }),
      {}
    );
    setDecisions(hydrated);
  }
}, [articleReview]);

// 在Detail Panel显示历史决策
{selectedIssue && decisions[selectedIssue.id] && (
  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm font-semibold text-blue-900">
        已有决策
      </span>
      <Badge variant="outline">
        {decisions[selectedIssue.id].reviewer}
      </Badge>
    </div>
    <div className="text-sm text-blue-800">
      <p>
        <strong>决策:</strong> {decisions[selectedIssue.id].decision_type}
      </p>
      {decisions[selectedIssue.id].rationale && (
        <p className="mt-1">
          <strong>理由:</strong> {decisions[selectedIssue.id].rationale}
        </p>
      )}
      {decisions[selectedIssue.id].modified_content && (
        <p className="mt-1">
          <strong>修改内容:</strong> {decisions[selectedIssue.id].modified_content}
        </p>
      )}
      <p className="text-xs text-blue-600 mt-2">
        决策时间: {formatDateTime(decisions[selectedIssue.id].decided_at)}
      </p>
    </div>
  </div>
)}
```

**验收标准**:
- [ ] 历史决策正确加载
- [ ] Detail Panel显示完整决策信息
- [ ] 可以修改已有决策

#### Task 3.5: 自动选择第一个issue (0.5天)
```typescript
// frontend/src/pages/ProofreadingReviewPage.tsx

// Auto-select first issue
useEffect(() => {
  if (
    articleReview?.proofreading_issues &&
    articleReview.proofreading_issues.length > 0 &&
    !selectedIssue
  ) {
    setSelectedIssue(articleReview.proofreading_issues[0]);
  }
}, [articleReview, selectedIssue]);

// Keyboard navigation
const selectNextIssue = useCallback(() => {
  if (!selectedIssue || !issues) return;
  const currentIndex = issues.findIndex(i => i.id === selectedIssue.id);
  if (currentIndex < issues.length - 1) {
    setSelectedIssue(issues[currentIndex + 1]);
  }
}, [selectedIssue, issues]);

const selectPreviousIssue = useCallback(() => {
  if (!selectedIssue || !issues) return;
  const currentIndex = issues.findIndex(i => i.id === selectedIssue.id);
  if (currentIndex > 0) {
    setSelectedIssue(issues[currentIndex - 1]);
  }
}, [selectedIssue, issues]);
```

**验收标准**:
- [ ] 页面加载后自动选择issue #1
- [ ] J/K键正确导航
- [ ] 边界情况处理正确

---

### Sprint 4: 测试和优化 (2-3天)

#### Task 4.1: 单元测试 (1.5天)
```typescript
// frontend/tests/pages/ProofreadingReviewPage.test.tsx

describe('ProofreadingReviewPage', () => {
  it('should load article review data on mount', async () => {
    const mockData = createMockArticleReviewData();
    mockAPI.get.mockResolvedValue(mockData);

    render(<ProofreadingReviewPage />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText(mockData.title)).toBeInTheDocument();
    });
  });

  it('should auto-select first issue', async () => {
    const mockData = createMockArticleReviewData();
    render(<ProofreadingReviewPage />, { wrapper: TestWrapper });

    await waitFor(() => {
      const firstIssue = screen.getByText('问题 #1');
      expect(firstIssue.closest('div')).toHaveClass('bg-blue-50');
    });
  });

  it('should save decisions with review notes', async () => {
    render(<ProofreadingReviewPage />, { wrapper: TestWrapper });

    // Make decisions
    await userEvent.click(screen.getByText('接受'));

    // Enter notes
    const notesInput = screen.getByLabelText('审核备注');
    await userEvent.type(notesInput, '测试备注');

    // Save
    await userEvent.click(screen.getByText('保存草稿'));

    await waitFor(() => {
      expect(mockAPI.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          review_notes: '测试备注',
        })
      );
    });
  });

  it('should handle keyboard shortcuts', async () => {
    render(<ProofreadingReviewPage />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText('问题 #1')).toBeInTheDocument();
    });

    // Press 'j' to go to next issue
    fireEvent.keyDown(window, { key: 'j' });

    await waitFor(() => {
      const secondIssue = screen.getByText('问题 #2');
      expect(secondIssue.closest('div')).toHaveClass('bg-blue-50');
    });
  });

  it('should display existing decisions', async () => {
    const mockData = createMockArticleReviewData({
      existing_decisions: [{
        issue_id: 'issue-1',
        decision_type: 'accepted',
        rationale: '理由充分',
        reviewer: 'user@example.com',
        decided_at: '2025-11-01T10:00:00Z',
      }],
    });

    render(<ProofreadingReviewPage />, { wrapper: TestWrapper });

    await waitFor(() => {
      expect(screen.getByText('已有决策')).toBeInTheDocument();
      expect(screen.getByText('理由充分')).toBeInTheDocument();
    });
  });
});

// frontend/tests/components/ProofreadingReview/DiffView.test.tsx

describe('DiffView', () => {
  it('should render original view mode', () => {
    render(
      <DiffView
        original="原文内容"
        suggested="建议内容"
        viewMode="original"
        issues={[]}
        decisions={{}}
      />
    );

    expect(screen.getByText('原文内容')).toBeInTheDocument();
    expect(screen.queryByText('建议内容')).not.toBeInTheDocument();
  });

  it('should render diff view mode with two columns', () => {
    render(
      <DiffView
        original="原文内容"
        suggested="建议内容"
        viewMode="diff"
        issues={[]}
        decisions={{}}
      />
    );

    expect(screen.getByText('原文')).toBeInTheDocument();
    expect(screen.getByText('AI建议')).toBeInTheDocument();
  });

  it('should highlight issues in content', () => {
    const issues = [{
      id: 'issue-1',
      position: { start: 0, end: 4 },
      severity: 'critical',
    }];

    render(
      <DiffView
        original="原文内容测试"
        suggested="建议内容测试"
        viewMode="original"
        issues={issues}
        decisions={{}}
      />
    );

    const highlighted = screen.getByText('原文内容');
    expect(highlighted).toHaveClass('bg-red-100');
  });
});
```

**验收标准**:
- [ ] 测试覆盖率 > 80%
- [ ] 所有核心功能有测试
- [ ] CI通过

#### Task 4.2: E2E测试 (1天)
```typescript
// frontend/e2e/proofreading-complete-workflow.spec.ts

test('complete proofreading review workflow', async ({ page }) => {
  // 1. Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // 2. Navigate to worklist
  await page.goto('/worklist');
  await expect(page.locator('h1:has-text("Worklist")')).toBeVisible();

  // 3. Find an item with proofreading status
  const worklistItem = page.locator('[data-status="proofreading"]').first();
  await expect(worklistItem).toBeVisible();

  // 4. Click "进入校对"
  await worklistItem.click('[data-testid="enter-review"]');

  // 5. Wait for review page to load
  await expect(page.locator('[data-testid="diff-view"]')).toBeVisible();

  // 6. Verify Meta/SEO cards are visible
  await expect(page.locator('[data-testid="meta-card"]')).toBeVisible();
  await expect(page.locator('[data-testid="seo-card"]')).toBeVisible();

  // 7. Accept first issue using keyboard
  await page.keyboard.press('a');
  await expect(page.locator('[data-testid="issue-1"]')).toHaveClass(/accepted/);

  // 8. Navigate to second issue and reject
  await page.keyboard.press('j');
  await page.keyboard.press('r');

  // 9. Enter review notes
  await page.fill('[data-testid="review-notes"]', '测试审核备注\n- 已接受建议1\n- 已拒绝建议2');

  // 10. Save draft
  await page.click('[data-testid="save-draft"]');
  await expect(page.locator('.toast:has-text("保存成功")')).toBeVisible();

  // 11. Complete review
  await page.click('[data-testid="complete-review"]');

  // 12. Confirm dialog
  await page.click('[data-testid="confirm-complete"]');

  // 13. Verify redirect to worklist
  await expect(page).toHaveURL(/\/worklist/);

  // 14. Verify status updated to ready_to_publish
  await expect(
    page.locator('[data-status="ready_to_publish"]')
  ).toBeVisible();
});

test('review page displays historical decisions', async ({ page }) => {
  // Setup: Create article with existing decisions via API
  const articleId = await createArticleWithDecisions({
    decisions: [{
      issue_id: 'issue-1',
      decision_type: 'accepted',
      rationale: '之前已接受',
    }],
  });

  // Navigate to review page
  await page.goto(`/articles/${articleId}/review`);

  // Verify historical decision is displayed
  await expect(page.locator('[data-testid="existing-decision"]')).toBeVisible();
  await expect(page.locator('text=之前已接受')).toBeVisible();
});

test('view mode switcher works correctly', async ({ page }) => {
  await page.goto('/articles/123/review');

  // Default: diff mode
  await expect(page.locator('.grid-cols-2')).toBeVisible();

  // Switch to original
  await page.click('[data-testid="view-mode-original"]');
  await expect(page.locator('.grid-cols-2')).not.toBeVisible();
  await expect(page.locator('text=原文')).toBeVisible();

  // Switch to preview
  await page.click('[data-testid="view-mode-preview"]');
  // Verify accepted changes are applied
  await expect(page.locator('[data-accepted="true"]')).toBeVisible();
});
```

**验收标准**:
- [ ] E2E测试覆盖完整workflow
- [ ] 所有关键路径有测试
- [ ] 测试稳定可靠

#### Task 4.3: 性能优化 (0.5天)
```typescript
// NFR-4: diff渲染2000行文本FPS ≥ 40

// 1. 虚拟滚动优化
import { FixedSizeList as List } from 'react-window';

function VirtualizedDiffView({ items }: Props) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <DiffLine data={items[index]} />
    </div>
  );

  return (
    <List
      height={800}
      itemCount={items.length}
      itemSize={35}
      width="100%"
    >
      {Row}
    </List>
  );
}

// 2. Memoization
const DiffView = memo(({ original, suggested, viewMode }: Props) => {
  const renderedContent = useMemo(() => {
    return renderDiffContent(original, suggested);
  }, [original, suggested]);

  return <div>{renderedContent}</div>;
});

// 3. Debounce滚动同步
const [leftScroll, setLeftScroll] = useState(0);
const [rightScroll, setRightScroll] = useState(0);

const handleLeftScroll = useMemo(
  () => debounce((e) => {
    setRightScroll(e.target.scrollTop);
  }, 16), // 60fps
  []
);
```

**验收标准**:
- [ ] 2000行文本渲染流畅
- [ ] 滚动FPS ≥ 40
- [ ] 内存占用合理

---

## 🔄 迁移策略

### 数据库Migration
```bash
# 1. 生成migration
cd backend
alembic revision --autogenerate -m "Add article suggested fields for proofreading workflow"

# 2. Review migration file
# 确保所有新字段 nullable=True

# 3. 测试migration (dev环境)
alembic upgrade head

# 4. 回滚测试
alembic downgrade -1
alembic upgrade head

# 5. 生产环境部署
# 先部署migration，再部署代码
```

### 前端部署
```bash
# 1. Feature flag控制
ENABLE_NEW_PROOFREADING_UI=false

# 2. 逐步迁移
# Phase 1: 新UI在 /articles/:id/review-v2
# Phase 2: A/B testing
# Phase 3: 完全切换到新UI

# 3. 监控
# - Error rate
# - Performance metrics
# - User feedback
```

---

## 📊 成功指标

### 功能完整性
- [ ] 所有12个Codex问题修复
- [ ] FR-9完全实现
- [ ] UI符合design spec

### 性能指标
- [ ] NFR-4: Diff渲染FPS ≥ 40
- [ ] 页面加载时间 < 2秒
- [ ] API响应时间 < 500ms

### 质量指标
- [ ] 单元测试覆盖率 > 80%
- [ ] E2E测试覆盖核心workflow
- [ ] 0 critical bugs

### 用户体验
- [ ] 审核流程流畅
- [ ] 历史决策可查看
- [ ] 键盘快捷键高效

---

## ⚠️ 风险管理

### 技术风险
| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Migration失败 | High | Low | 充分测试，可回滚 |
| 性能不达标 | High | Medium | 虚拟滚动，memoization |
| API breaking change | Medium | Low | 保留旧API，逐步迁移 |

### 业务风险
| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 用户培训成本 | Medium | High | 提供引导和文档 |
| 数据迁移问题 | High | Low | 充分测试，备份数据 |

---

## 📅 时间表

| Sprint | 任务 | 天数 | 开始日期 | 结束日期 |
|--------|------|------|----------|----------|
| Sprint 1 | 数据层修复 | 3-4 | Day 1 | Day 4 |
| Sprint 2 | 核心UI重构 | 5-7 | Day 5 | Day 11 |
| Sprint 3 | 功能增强 | 3-4 | Day 12 | Day 15 |
| Sprint 4 | 测试和优化 | 2-3 | Day 16 | Day 18 |

**总计**: 13-18 工作日

---

## ✅ 下一步行动

1. [ ] 评审此计划，获得团队认可
2. [ ] 确定开始日期和资源分配
3. [ ] 创建详细的issue/ticket
4. [ ] 开始Sprint 1 - Task 1.1: Article模型扩展
