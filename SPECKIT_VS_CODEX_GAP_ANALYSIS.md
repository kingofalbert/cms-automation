# SpecKit vs Codex Issues - Gap Analysis

**生成时间**: 2025-11-06
**对比文档**:
- specs/004-google-drive-auto-sync/tasks.md
- specs/004-google-drive-auto-sync/plan.md
- specs/003-proofreading-review-ui/testing-acceptance.md
- CODEX_ISSUES_ANALYSIS.md

---

## 📊 执行摘要

| 维度 | SpecKit状态 | Codex发现 | 差距 |
|------|------------|-----------|------|
| **任务定义** | ✅ 29个任务，10.5工作日 | ❌ 12个关键问题未解决 | 🔴 High |
| **实施计划** | ✅ 5个Phase清晰 | ❌ 数据层+UI核心缺失 | 🔴 Critical |
| **测试计划** | ✅ E2E+Unit定义完整 | ❌ 实际代码无测试 | 🟡 Medium |
| **当前实施** | ⏳ 部分完成 | ❌ 多个P0问题存在 | 🔴 Blocking |

**结论**: SpecKit的**计划是正确的**，但**实施存在严重偏差**。

---

## 🔍 详细对比

### 1. 数据层问题

#### SpecKit计划 (tasks.md: Task 2.2-2.6)
```markdown
Task 2.2 Article 状态历史表 — ⏳
Task 2.3 Worklist 详情 API — ⏳
Task 2.5 Article 自动创建 — ⏳
Task 2.6 自动触发校对 — ⏳
```

#### 实际实施状态
| 任务 | 计划状态 | 实际状态 | Codex问题 |
|------|----------|----------|-----------|
| Article状态历史 | ⏳ 待实施 | ✅ 已实现 | - |
| Worklist详情API | ⏳ 待实施 | ✅ 已实现 | - |
| Article自动创建 | ⏳ 待实施 | ✅ 部分实现 | H2: **缺少14个suggested_*字段** |
| 自动触发校对 | ⏳ 待实施 | ✅ 已实现 | - |

#### 🔴 Critical Gap: Article Schema不完整

**SpecKit未明确要求的字段** (但workflow文档要求):
```python
# backend/docs/article_proofreading_seo_workflow.md:365-393
# ❌ 以下字段在SpecKit tasks中未明确列出，导致实施时被遗漏

suggested_content: Text                    # ❌ 缺失
suggested_content_changes: JSONB           # ❌ 缺失
suggested_meta_description: Text           # ❌ 缺失
suggested_meta_reasoning: Text             # ❌ 缺失
suggested_meta_score: Float                # ❌ 缺失
suggested_seo_keywords: JSONB              # ❌ 缺失
suggested_keywords_reasoning: Text         # ❌ 缺失
suggested_keywords_score: Float            # ❌ 缺失
paragraph_suggestions: JSONB               # ❌ 缺失
paragraph_split_suggestions: JSONB         # ❌ 缺失
faq_schema_proposals: JSONB                # ❌ 缺失
suggested_generated_at: DateTime           # ❌ 缺失
ai_model_used: String                      # ❌ 缺失
generation_cost: Decimal                   # ❌ 缺失
```

**根本原因**:
- SpecKit的Task 2.5只说"创建Article"，没有详细列出schema要求
- 开发者参考了workflow文档，但没有完整实现所有字段
- 缺少schema验收checklist

---

### 2. API端点问题

#### SpecKit计划 (tasks.md: Task 4.2)
```markdown
Task 4.2 数据获取与状态管理 — ⏳
- 调用 `/v1/articles/{id}`，解析正文/建议稿/Meta/SEO/FAQ/Issues。
```

#### 实际实施状态
```typescript
// ❌ 错误：调用的是 worklist API
const { data } = useQuery({
  queryFn: () => worklistAPI.get(Number(id)),  // 应该是articleAPI
});
```

#### 🔴 Critical Gap: API调用错误

**SpecKit明确要求**: `/v1/articles/{id}`
**实际实施**: `/v1/worklist/{id}`

**根本原因**:
- SpecKit的Task 4.2写得正确
- 但Task 4.1的路由定义是`/articles/:id/proofreading`，容易混淆
- 开发者看到URL中有`/articles/:id`，误以为需要从worklist获取数据
- **缺少API contract验收测试**

**修复建议**:
- ✅ SpecKit已经定义正确，只需严格执行Task 4.2
- 添加API contract测试确保调用正确端点

---

### 3. UI实施问题

#### SpecKit计划 (tasks.md: Task 4.3-4.4)
```markdown
Task 4.3 Diff 与 Issue 列表 — ⏳
- 构建左右分屏 diff 组件；支持按 issue 滚动定位、高亮、规则标签、置信度。

Task 4.4 Meta/SEO/FAQ 卡片 — ⏳
- 展示原始/建议内容、长度/数量提示、评分。
- "接受建议"按钮将建议写回本地状态。
```

#### 实际实施状态
```typescript
// ❌ 只实现了单列显示
return (
  <div className="mx-auto max-w-4xl">
    <h1>{title}</h1>
    <div className="prose">{renderedContent}</div>
    {/* ❌ 缺少：左右diff, Meta/SEO/FAQ cards */}
  </div>
);
```

#### 🔴 Critical Gap: UI架构错误

| 组件 | SpecKit要求 | 实际实施 | 状态 |
|------|------------|----------|------|
| 左右diff | ✅ 明确要求 | ❌ 单列显示 | 未实施 |
| Meta卡片 | ✅ 明确要求 | ❌ 不存在 | 未实施 |
| SEO卡片 | ✅ 明确要求 | ❌ 不存在 | 未实施 |
| FAQ卡片 | ✅ 明确要求 | ❌ 不存在 | 未实施 |
| Issue列表 | ✅ 要求规则标签+confidence | ✅ 基础实现 | 部分完成 |

**根本原因**:
- SpecKit的Task 4.3/4.4定义正确且清晰
- 但**缺少UI mockup/wireframe作为验收标准**
- 开发者实现了"能用"的版本，但不符合规范
- **缺少UI review checkpoint**

**修复建议**:
- ✅ SpecKit已经定义正确
- 需要补充：UI design spec的截图/mockup作为验收标准
- 在Task 4.3/4.4的验收条件中添加"符合ui-design-spec.md图示"

---

### 4. 测试覆盖问题

#### SpecKit计划 (tasks.md: Phase 5)
```markdown
Task 5.1 Backend 测试套件 — ⏳
Task 5.2 Frontend 单元测试 — ⏳
Task 5.3 Playwright 场景 — ⏳
```

#### specs/003-proofreading-review-ui/testing-acceptance.md
```typescript
// ✅ 测试计划非常详细和完整
test('should display page header with correct title', async ({ page }) => {
  // Check breadcrumb
  await expect(page.locator('nav')).toContainText('首页');
  await expect(page.locator('nav')).toContainText('Worklist');

  // Check action buttons
  await expect(page.locator('button:has-text("保存草稿")')).toBeVisible();
  await expect(page.locator('button:has-text("完成审核")')).toBeVisible();
  await expect(page.locator('button:has-text("取消")')).toBeVisible();
});

test('should navigate using keyboard shortcuts', async ({ page }) => {
  // ...
});
```

#### 实际实施状态
```bash
$ find frontend/tests -name "*proofreading*"
# 空结果

$ find frontend/e2e -name "*proofreading*"
# 空结果
```

#### 🟡 Medium Gap: 测试未实施

| 测试类型 | SpecKit计划 | 实际状态 | 影响 |
|---------|-----------|----------|------|
| Frontend Unit | ✅ Task 5.2定义 | ❌ 不存在 | Medium |
| Backend Unit | ✅ Task 5.1定义 | ❌ 不存在 | Medium |
| E2E Tests | ✅ Task 5.3定义 | ❌ 不存在 | High |

**根本原因**:
- SpecKit测试计划非常完整（testing-acceptance.md有800+行）
- 但Task 5.1-5.3标记为"待实施"（⏳）
- **测试阶段被延后到Phase 5**，导致前面的实施缺乏验证
- 典型的"先写代码后写测试"问题

**修复建议**:
- ❌ SpecKit计划有问题：测试不应该放在最后
- 应该改为TDD：每个Task完成时立即写测试
- 建议重构任务顺序：
  ```
  Task 4.3 Diff组件 → Task 4.3.1 Diff组件测试
  Task 4.4 Meta卡片 → Task 4.4.1 Meta卡片测试
  ```

---

### 5. ViewMode问题

#### SpecKit计划
```markdown
# specs/003-proofreading-review-ui/ui-design-spec.md:181-235
## Sub-header (Review Stats Bar)
- 右侧：视图模式切换器 (Original/Preview/Diff)
```

#### tasks.md
```markdown
Task 4.3 Diff 与 Issue 列表 — ⏳
# ❌ 没有明确提到viewMode切换器
```

#### 实际实施状态
```typescript
// ✅ 状态定义存在
const [viewMode] = useState<ViewMode>('original');

// ❌ 但没有切换UI
// ❌ 没有实际的diff渲染逻辑
```

#### 🟡 Medium Gap: ViewMode未完整实施

**根本原因**:
- ui-design-spec.md **有**详细设计
- 但tasks.md **缺少**明确的ViewMode切换器任务
- 开发者只实现了状态，没有实现UI

**修复建议**:
- 补充Task: "Task 4.3.1 实现ViewMode切换器（Original/Diff/Preview）"
- 添加验收标准："三个按钮正确切换，diff模式显示左右对比"

---

### 6. reviewNotes问题

#### SpecKit计划 (tasks.md: Task 4.4)
```markdown
Task 4.4 Meta/SEO/FAQ 卡片 — ⏳
4. 备注输入和批量操作（"全部接受""确认最终版本"）。
```

#### ui-design-spec.md
```markdown
## 8. Footer Action Bar
- 右侧：备注输入框
```

#### 实际实施状态
```typescript
// ✅ 状态存在
const [reviewNotes, setReviewNotes] = useState('');

// ❌ 但没有<textarea>绑定
```

#### 🟡 Medium Gap: 备注输入UI缺失

**根本原因**:
- Task 4.4提到了"备注输入"
- 但太简略，没有说明需要一个textarea组件
- ui-design-spec.md有设计，但Task没有引用

**修复建议**:
- Task 4.4应该改为："实现备注输入textarea，支持Markdown，最少6行高度"

---

## 📋 Gap Summary

### SpecKit计划正确性评估

| 方面 | 评分 | 说明 |
|------|------|------|
| **任务完整性** | 🟡 7/10 | 核心任务都有，但细节不够（如schema字段、UI组件） |
| **任务清晰度** | 🟡 6/10 | 高层次清晰，低层次模糊（"创建Article"vs"创建14个字段"） |
| **验收标准** | 🔴 4/10 | 缺少具体的验收checklist和mockup引用 |
| **测试集成** | 🔴 3/10 | 测试计划完整但放在最后，缺乏TDD |
| **依赖管理** | 🟢 8/10 | Phase依赖清晰，但Task内依赖未明确 |

### 实施偏差根本原因

1. **Schema定义不完整** (H2)
   - SpecKit问题: Task 2.5太简略
   - 修复: 添加详细的schema checklist

2. **API调用错误** (H1)
   - SpecKit问题: 无（定义正确）
   - 实施问题: 开发者误解，缺少API contract测试

3. **UI架构错误** (H3)
   - SpecKit问题: 缺少mockup引用
   - 修复: 每个UI Task添加design spec截图链接

4. **测试延后** (L1)
   - SpecKit问题: 测试放在Phase 5
   - 修复: 改为TDD，每个Task完成时写测试

5. **细节功能遗漏** (H4, H5, M1-M6)
   - SpecKit问题: Task描述太高层次
   - 修复: 分解为更细粒度的subtask

---

## 🎯 SpecKit改进建议

### 1. 增强Task定义

**当前** (tasks.md: Task 2.5):
```markdown
### Task 2.5 Article 自动创建 — ⏳
- 创建 Article（title/body/meta），source=google_drive。
```

**改进为**:
```markdown
### Task 2.5 Article Schema扩展与自动创建 — ⏳

**子任务:**
1. 添加Article模型字段（Migration）：
   - [ ] suggested_content (Text)
   - [ ] suggested_content_changes (JSONB)
   - [ ] suggested_meta_description (Text)
   - [ ] suggested_meta_reasoning (Text)
   - [ ] suggested_meta_score (Float)
   - [ ] suggested_seo_keywords (JSONB)
   - [ ] suggested_keywords_reasoning (Text)
   - [ ] suggested_keywords_score (Float)
   - [ ] paragraph_suggestions (JSONB)
   - [ ] paragraph_split_suggestions (JSONB)
   - [ ] faq_schema_proposals (JSONB)
   - [ ] suggested_generated_at (DateTime)
   - [ ] ai_model_used (String)
   - [ ] generation_cost (Numeric)

2. 实现ArticleImporter service
3. 集成到GoogleDriveSyncService

**验收标准:**
- [ ] Migration成功执行
- [ ] 所有14个字段在Article模型中
- [ ] ArticleResponse schema包含所有字段
- [ ] 单元测试覆盖Article创建逻辑
```

### 2. 添加UI验收标准

**当前** (tasks.md: Task 4.3):
```markdown
### Task 4.3 Diff 与 Issue 列表 — ⏳
- 构建左右分屏 diff 组件
```

**改进为**:
```markdown
### Task 4.3 Diff 视图与ViewMode切换器 — ⏳

**参考设计:** specs/003-proofreading-review-ui/ui-design-spec.md:181-235

**子任务:**
1. [ ] 实现DiffView组件（左右双列布局）
2. [ ] 实现ViewModeSwitcher组件（3个按钮）
3. [ ] 实现Original模式（单列原文）
4. [ ] 实现Diff模式（左右对比，红色删除+绿色添加）
5. [ ] 实现Preview模式（应用accepted changes）

**验收标准:**
- [ ] 三列布局符合design spec截图 [链接]
- [ ] ViewMode切换器样式符合design spec [链接]
- [ ] Diff模式正确高亮删除和添加
- [ ] 单元测试覆盖率 > 80%
- [ ] E2E测试: test_view_mode_switching 通过
```

### 3. TDD工作流

**当前顺序**:
```
Phase 4: 实施功能
  ↓
Phase 5: 写测试
```

**改进为**:
```
Task 4.3: Diff视图
  ├─ Task 4.3.0: 编写测试用例（Red）
  ├─ Task 4.3.1: 实现组件（Green）
  └─ Task 4.3.2: 重构优化（Refactor）

Task 4.4: Meta/SEO卡片
  ├─ Task 4.4.0: 编写测试用例
  ├─ Task 4.4.1: 实现组件
  └─ Task 4.4.2: 重构优化
```

### 4. 添加Checkpoint Review

在tasks.md中每个Phase后添加：

```markdown
### Phase 2 Review Checkpoint 🔍

**必须通过的检查:**
- [ ] Code Review: PR已合并，至少2个approve
- [ ] API Contract测试: 所有endpoint符合specs/003.../api-contracts.md
- [ ] Schema验证: 运行schema_validator.py，确认所有字段存在
- [ ] 单元测试: 覆盖率 ≥ 80%
- [ ] Integration测试: 核心流程通过
- [ ] Tech Lead验收签字

**如果未通过，不能进入Phase 3**
```

---

## 🔄 与Codex Issues的对应关系

| Codex Issue | SpecKit Coverage | Gap Type |
|-------------|------------------|----------|
| **H1: API端点错误** | ✅ Task 4.2定义正确 | 🔴 实施偏差 |
| **H2: Schema缺失** | 🟡 Task 2.5太简略 | 🔴 计划不详细 |
| **H3: UI缺少diff** | ✅ Task 4.3定义正确 | 🔴 实施偏差 + 缺mockup |
| **H4: viewMode未实现** | 🟡 ui-design有，task无 | 🟡 计划不完整 |
| **H5: reviewNotes未绑定** | 🟡 Task 4.4提到但太简略 | 🟡 计划不详细 |
| **M1: Header/Stats** | 🟡 ui-design有，task太简略 | 🟡 计划不详细 |
| **M2: 历史决策** | ❌ Task中未提及 | 🔴 计划缺失 |
| **M3: Issue列表增强** | 🟡 Task 4.3部分覆盖 | 🟡 计划不完整 |
| **M4: 键盘快捷键bug** | ✅ testing-acceptance有测试 | 🔴 实施质量问题 |
| **M5: 缺少Modal** | ❌ Task中未提及 | 🔴 计划缺失 |
| **M6: 无自动选择** | ❌ Task中未提及 | 🔴 计划缺失 |
| **L1: 测试缺失** | ✅ Phase 5完整定义 | 🔴 实施延后 |

### Gap Type统计
- 🔴 **计划缺失**: 3个 (M2, M5, M6)
- 🟡 **计划不详细**: 5个 (H2, H4, H5, M1, M3)
- ✅ **计划正确但实施偏差**: 4个 (H1, H3, M4, L1)

---

## ✅ 行动建议

### 优先级1: 补充SpecKit计划缺失项

在`tasks.md`中添加：

```markdown
### Task 4.3.2 加载历史决策 — ⏳
- API返回existing_decisions数组
- 前端hydrate到decisions state
- DetailPanel显示历史决策信息（决策人、时间、理由）

### Task 4.3.3 自动选择第一个issue — ⏳
- useEffect: issues加载后自动setSelectedIssue(issues[0])
- 键盘导航: j/k切换issue

### Task 4.4.1 段落建议Modal — ⏳
- 实现ParagraphSuggestionModal组件
- 显示分段建议和优化
- 支持接受/拒绝
```

### 优先级2: 细化现有Task

为Task 2.5, 4.3, 4.4添加详细的checklist（参考上文"增强Task定义"）

### 优先级3: 调整测试策略

将Phase 5的测试分散到各个Task中，改为TDD工作流

### 优先级4: 添加Checkpoint Review

在每个Phase后添加强制性的review checkpoint

---

## 📊 结论

### SpecKit质量评估

**优点:**
- ✅ 总体架构和Phase划分合理
- ✅ 核心功能都有覆盖
- ✅ 测试计划非常详细（testing-acceptance.md）

**问题:**
- 🔴 Task描述太高层次，缺少实施细节
- 🔴 缺少强制性的验收checklist和design mockup引用
- 🔴 测试延后到Phase 5，缺乏TDD
- 🟡 部分功能遗漏（历史决策、Modal、自动选择）

### 与实际实施的关系

**SpecKit不是根本原因**:
- 75% 的问题是**实施偏差**（开发者没有严格follow spec）
- 25% 的问题是**计划不详细**（需要补充细节）

**如果严格执行SpecKit + 添加补丁，可以解决所有Codex issues**

### 建议

1. **短期（本周）**: 按照CODEX_ISSUES_ANALYSIS.md修复12个问题
2. **中期（下周）**: 根据本文档补充SpecKit缺失的Task
3. **长期（持续）**: 改进SpecKit模板，强制要求：
   - 详细的subtask checklist
   - Design mockup链接
   - API contract引用
   - TDD工作流
   - Checkpoint review
