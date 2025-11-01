# 文档对齐检查清单 - 单一 Prompt 方案

**版本:** 1.0.0
**创建日期:** 2025-10-27
**目的:** 确保所有技术文档与"单一 Prompt 综合分析方案"对齐

---

## 一、核心变更说明

### 变更前（旧方案）
```
用户提交文章
  ↓
第1次 AI 调用: 450条校对规则检查
  ↓
第2次 AI 调用: Meta描述优化
  ↓
第3次 AI 调用: SEO关键词提取
  ↓
第4次 AI 调用: FAQ Schema生成
  ↓
返回所有结果

Token使用: ~9,550 tokens
处理时间: ~6秒
成本: $0.0605/篇
问题: 术语可能不一致
```

### 变更后（新方案）
```
用户提交文章
  ↓
单次 AI 调用: 综合 Prompt
  - 450条校对规则检查
  - Meta描述优化
  - SEO关键词提取/优化
  - FAQ Schema生成（3/5/7版本）
  - 发布合规性检查
  ↓
返回完整JSON结果

Token使用: ~6,300 tokens (节省34%)
处理时间: ~2.5秒 (节省58%)
成本: $0.0525/篇 (节省13%)
优势: 术语自动保持一致
```

---

## 二、需要更新的文档清单

### ✅ 已完成

| # | 文档名称 | 状态 | 更新日期 | 备注 |
|---|---------|------|---------|------|
| 1 | `single_prompt_design.md` | ✅ 已创建 | 2025-10-27 | 新方案的完整设计文档 |

### 🔄 进行中

| # | 文档名称 | 状态 | 优先级 | 需要更新的部分 |
|---|---------|------|--------|---------------|
| 2 | `article_proofreading_seo_workflow.md` | 🔄 待更新 | P0 | • 第5节：完整工作流程<br>• 第6节：功能模块设计<br>• 第10节：AI服务集成<br>• 代码示例 |
| 3 | `user_experience_workflow.md` | 🔄 待更新 | P0 | • 第二步：系统自动处理<br>• 第三步：审核建议<br>• 处理时间说明<br>• UI流程图 |
| 4 | `structured_data_faq_schema.md` | 🔄 待更新 | P1 | • 第4节：AI生成策略<br>• API接口设计<br>• 集成方式说明 |
| 5 | `database_schema_updates.md` | 🔄 待更新 | P1 | • ArticleVersion表字段<br>• JSON存储结构<br>• 查询示例 |
| 6 | `proofreading_requirements.md` | 🔄 待更新 | P2 | • 添加单一Prompt方案说明<br>• 更新实现指南引用 |

---

## 三、具体更新要点

### 3.1 `article_proofreading_seo_workflow.md`

#### 需要更新的章节

**第5节：完整工作流程**
- ❌ 删除：多个AI调用步骤的描述
- ✅ 更新：改为单一AI分析步骤
- ✅ 添加：引用 `single_prompt_design.md`

**第6节：功能模块详细设计**
- ❌ 删除：
  - `ParagraphAnalyzer` 单独调用AI的代码
  - `MetaOptimizer._generate_new()` 单独调用
  - `KeywordOptimizer._generate_new()` 单独调用
  - `FAQGenerator.generate()` 单独调用
- ✅ 更新：改为引用 `ProofreadingAnalysisService` 统一服务
- ✅ 添加：JSON响应解析逻辑

**第10节：AI服务集成**
- ❌ 删除：多个Prompt模板
- ✅ 更新：改为单一综合Prompt
- ✅ 添加：Token优化说明
- ✅ 添加：术语一致性保证说明

**代码示例**
- ❌ 删除：所有分散的AI调用代码
- ✅ 更新：改为 `ProofreadingAnalysisService.analyze_article()`
- ✅ 添加：完整JSON Schema定义

#### 具体修改位置

| 行号范围 | 原内容 | 新内容 |
|---------|-------|-------|
| ~300-350 | 工作流程图（多步AI调用） | 工作流程图（单步AI调用） |
| ~1440-1470 | `_ai_suggest_splits()` 方法 | 删除，改为引用综合分析 |
| ~1525-1548 | `_generate_new()` Meta生成 | 删除，改为引用综合分析 |
| ~1560-1587 | `_optimize_existing()` Meta优化 | 删除，改为引用综合分析 |
| ~1663-1690 | FAQ生成Prompt | 删除，改为引用综合分析 |
| ~2515-2560 | Prompt设计原则 | 更新为综合Prompt设计 |

---

### 3.2 `user_experience_workflow.md`

#### 需要更新的章节

**第二步：系统自动处理**
- ❌ 删除："正在校对..." → "正在优化Meta..." → "正在生成FAQ..." 的分步描述
- ✅ 更新：改为 "AI正在进行综合分析..." 单一进度提示
- ✅ 更新：处理时间从 "48秒" 改为 "2-3秒"

**第三步：审核建议**
- ✅ 更新：强调所有内容（校对+Meta+关键词+FAQ）术语一致
- ✅ 添加：一致性保证的说明

**时间效率对比表**
- ✅ 更新：AI处理时间从 ~48秒 → ~2.5秒

**UI流程图**
- ✅ 更新：进度条显示 "AI综合分析中..." 而不是多个步骤

#### 具体修改位置

| 行号范围 | 原内容 | 新内容 |
|---------|-------|-------|
| ~54 | `AI自动处理 (48秒)` | `AI自动处理 (2.5秒)` |
| ~200-250 | 多步处理进度UI | 单步综合分析UI |
| ~400-450 | 时间效率表 | 更新AI处理时间 |

---

### 3.3 `structured_data_faq_schema.md`

#### 需要更新的章节

**第4节：AI生成策略**
- ❌ 删除：单独调用FAQ生成的描述
- ✅ 更新：改为"作为综合分析的一部分"
- ✅ 添加：与正文、Meta、关键词术语保持一致的说明

**第8节：API接口设计**
- ❌ 删除：独立的 `/generate-faq` 端点
- ✅ 更新：FAQ作为 `/analyze` 端点响应的一部分

#### 具体修改位置

| 行号范围 | 原内容 | 新内容 |
|---------|-------|-------|
| ~150-200 | 独立FAQ生成流程 | 集成到综合分析流程 |
| ~300-350 | 独立API端点 | 作为分析结果的子集 |

---

### 3.4 `database_schema_updates.md`

#### 需要更新的章节

**ArticleVersion表设计**
- ✅ 添加：`ai_analysis_result` JSONB 字段，存储完整的综合分析结果
- ✅ 更新：字段注释说明单一Prompt返回

**JSON存储结构**
- ✅ 添加：完整的分析结果JSON Schema示例

#### 具体修改位置

| 行号范围 | 原内容 | 新内容 |
|---------|-------|-------|
| ~200-250 | 分散的AI结果字段 | 单一JSON字段存储所有结果 |

---

### 3.5 `proofreading_requirements.md`

#### 需要更新的章节

**实现方案**
- ✅ 添加：引用 `single_prompt_design.md`
- ✅ 添加：单一Prompt优势说明

---

## 四、更新步骤

### 步骤1：备份现有文档 ✅
```bash
cd /home/kingofalbert/projects/CMS/backend/docs
cp article_proofreading_seo_workflow.md article_proofreading_seo_workflow.md.backup
cp user_experience_workflow.md user_experience_workflow.md.backup
cp structured_data_faq_schema.md structured_data_faq_schema.md.backup
cp database_schema_updates.md database_schema_updates.md.backup
cp proofreading_requirements.md proofreading_requirements.md.backup
```

### 步骤2：按优先级更新文档
1. ✅ P0: `article_proofreading_seo_workflow.md` - 核心工作流
2. ✅ P0: `user_experience_workflow.md` - 用户体验
3. ✅ P1: `structured_data_faq_schema.md` - FAQ集成
4. ✅ P1: `database_schema_updates.md` - 数据库
5. ✅ P2: `proofreading_requirements.md` - 需求说明

### 步骤3：交叉验证一致性
- 确保所有文档引用相同的架构
- 确保时间/成本数据一致
- 确保代码示例对齐

### 步骤4：更新版本号
所有文档版本升级：
- `article_proofreading_seo_workflow.md`: 1.0.0 → **2.0.0** (重大架构变更)
- `user_experience_workflow.md`: 1.0.0 → **1.1.0** (流程细节更新)
- `structured_data_faq_schema.md`: 1.0.0 → **1.1.0** (集成方式更新)
- `database_schema_updates.md`: 1.0.0 → **1.1.0** (字段新增)
- `proofreading_requirements.md`: 3.0.0 → **3.1.0** (实现方案更新)

---

## 五、验证清单

更新完成后，逐项验证：

### 架构一致性
- [ ] 所有文档描述的AI调用方式一致（单一Prompt）
- [ ] 工作流程图对齐
- [ ] 处理时间数据一致（~2.5秒）
- [ ] Token使用数据一致（~6,300 tokens）
- [ ] 成本数据一致（~$0.0525/篇）

### 术语一致性
- [ ] "单一 Prompt" / "综合分析" 术语统一
- [ ] "ProofreadingAnalysisService" 服务名统一
- [ ] JSON响应格式引用统一

### 引用完整性
- [ ] 所有文档正确引用 `single_prompt_design.md`
- [ ] API接口定义一致
- [ ] 数据库Schema引用一致

### 代码示例有效性
- [ ] 删除所有过时的分散AI调用代码
- [ ] 所有代码示例使用新的 `ProofreadingAnalysisService`
- [ ] JSON Schema定义完整且一致

---

## 六、关键信息对照表

| 维度 | 旧方案 | 新方案 | 文档中应使用 |
|------|-------|-------|-------------|
| AI调用次数 | 4次 | 1次 | **1次** |
| 处理时间 | ~6秒 | ~2.5秒 | **~2.5秒** |
| Token使用 | ~9,550 | ~6,300 | **~6,300** |
| 成本/篇 | $0.0605 | $0.0525 | **$0.0525** |
| Token节省 | - | 34% | **34%** |
| 时间节省 | - | 58% | **58%** |
| 成本节省 | - | 13% | **13%** |
| 术语一致性 | ❌ 不保证 | ✅ 保证 | **保证** |

---

## 七、更新责任人

| 文档 | 更新人 | 审核人 | 目标完成日期 |
|------|-------|-------|-------------|
| `single_prompt_design.md` | ✅ Claude | - | 2025-10-27 |
| `article_proofreading_seo_workflow.md` | Claude | 用户 | 2025-10-27 |
| `user_experience_workflow.md` | Claude | 用户 | 2025-10-27 |
| `structured_data_faq_schema.md` | Claude | 用户 | 2025-10-27 |
| `database_schema_updates.md` | Claude | 用户 | 2025-10-27 |
| `proofreading_requirements.md` | Claude | 用户 | 2025-10-27 |

---

## 八、常见问题（FAQ）

### Q1: 为什么要从多次调用改为单次调用？
**A:** 三个主要原因：
1. **成本优化**：节省34% token使用
2. **性能提升**：处理时间减少58%
3. **质量保证**：AI在统一上下文中生成所有内容，自动保持术语一致性

### Q2: 旧方案的文档还保留吗？
**A:** 保留备份（.backup后缀），但主文档全部更新为新方案。

### Q3: 如果需要单独调用某个功能（如只生成FAQ）怎么办？
**A:** 依然使用综合分析端点，前端只使用需要的部分结果。这样保持了后端的简洁性，也确保了一致性。

### Q4: 数据库需要迁移吗？
**A:** 不需要。新增的 `ai_analysis_result` 字段是可空的，现有数据不受影响。

---

## 九、下一步行动

1. ✅ 创建本检查清单
2. 🔄 开始更新文档（按优先级）
3. ⏳ 交叉验证一致性
4. ⏳ 用户审核
5. ⏳ 更新版本号并发布

---

**文档结束**
