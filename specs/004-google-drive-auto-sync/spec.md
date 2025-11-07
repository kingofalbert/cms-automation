# Google Drive 自动同步 + 校对审查闭环 - 需求规格说明

**Feature ID:** 004-google-drive-auto-sync  
**创建日期:** 2025-11-06  
**最后更新:** 2025-11-07  
**优先级:** High  
**状态:** 待实施 (Planned)

---

## 📋 概述

### 背景

当前系统虽然可以手动或半自动地将 Google Drive 中的稿件同步到 Worklist，但仍存在以下痛点：

1. 同步需要人工点击按钮，容易遗漏。
2. Worklist 仅显示粗粒度的“待评估”等内部状态，无法体现“校对中/审核中”等真实阶段。
3. 同步后的稿件不会自动创建 `Article` 记录，也不会触发校对服务，导致编辑点击 Drive 文件后没有“校对审查”界面。
4. 人工审查结果没有落库，无法追踪规则命中率和调优反馈。

### 目标

实现“Google Drive → Worklist → 自动校对 → 人工审查 → 发布”的完整闭环：

1. **自动发现**：使用 Cloud Scheduler 每 5 分钟扫描 Drive 文件夹并同步到 Worklist。
2. **自动处理**：对每个新稿件自动创建 `Article`，触发 AI + 确定性校对，并落地历史与决策数据。
3. **可视化跟踪**：Worklist 列表、详情、状态历史与告警全部与实际流程对齐。
4. **人工确认**：点击 Worklist 条目即可进入 `ProofreadingReviewPage` 左右分屏 diff，逐项接受/拒绝建议。
5. **可追溯**：人工决策写入 `proofreading_decisions`，为规则调优与 KPI 统计提供数据。

### 范围

- ✅ Google Drive 自动同步与错误重试
- ✅ Article 自动创建 & 校对流水线
- ✅ Worklist 状态、详情与 API 扩展
- ✅ ProofreadingReviewPage（左右分屏 diff + Meta/SEO/FAQ 卡片）
- ✅ 监控与测试方案
- ❌ 多文件夹支持（后续优化）
- ❌ Webhook 实时触发（本阶段仍使用轮询）

---

## 🎯 需求详情

### 功能需求 (FR)

| ID | 描述 |
|----|------|
| **FR-1** | 系统必须通过 Cloud Scheduler 每 5 分钟自动触发 `POST /v1/worklist/sync`，可通过环境变量覆盖频率。 |
| **FR-2** | 每次同步需处理最多 100 个文件，对新文件创建 WorklistItem，对已存在文件更新所有字段（title/content/tags/categories/metadata）。 |
| **FR-3** | 同步必须输出统计数据 `processed/created/updated/skipped/errors`，并写入 Cloud Logging；失败需自动重试 3 次。 |
| **FR-4** | 连续 3 次同步失败触发告警（Slack/Webhook），同时 Worklist 显示 `failed` 状态并附加错误信息。 |
| **FR-5** | Worklist 状态需与产品文档对齐：`pending → proofreading → under_review → ready_to_publish → publishing → published`，并允许 `failed` 回退；所有变更写入 `article_status_history`。 |
| **FR-6** | 每个新 WorklistItem 必须立即创建 `Article`（`source_type=google_drive`）并调用 `POST /v1/articles/{id}/proofread`，把结果写入 `articles.proofreading_issues` 与 `proofreading_history`；成功后 Worklist 状态跳转为 `proofreading`。 |
| **FR-7** | Worklist 详情 API (`GET /v1/worklist/{id}`) 需返回正文、Drive 元数据、校对摘要、状态历史、操作日志、备注、Google Doc 链接等结构化数据；列表接口暴露 `article_id` 与最新状态。 |
| **FR-8** | 前端 Worklist Drawer 要展示状态时间线、字数/阅读时长、错误提示、校对要点，并提供“进入校对审查”按钮，跳转到 `/articles/{article_id}/proofreading`。 |
| **FR-9** | `ProofreadingReviewPage` 必须实现左右分屏 diff、规则标签、段落级接受/拒绝/手动编辑、Meta/SEO/FAQ 对比卡片、批量接受、备注输入、最终确认按钮。 |
| **FR-10** | 人工决策通过 API 写入 `proofreading_decisions`（accepted/rejected/modified + note + timestamp），并同步到 Worklist notes；完成后状态进入 `ready_to_publish`。 |

### 非功能需求 (NFR)

1. **NFR-1:** 同步 API 平均耗时 < 10 秒，P95 < 20 秒。
2. **NFR-2:** Proofreading pipeline 在 5 篇稿件并发下总耗时 < 3 分钟/篇。
3. **NFR-3:** Worklist 页面在 100 条记录时加载时间 < 1 秒。
4. **NFR-4:** ProofreadingReviewPage diff 渲染 2000 行文本不崩溃，FPS ≥ 40。
5. **NFR-5:** 数据一致性：任何状态变化必须写入历史，审查页加载的状态与 Worklist 保持一致。

---

## 🔧 技术方案

### 架构图

```
Cloud Scheduler (*/5) ──HTTP──► Cloud Run /v1/worklist/sync
  │
  ▼
GoogleDriveSyncService
  │ 1. list files
  │ 2. parse YAML / text
  │ 3. upsert WorklistItem
  │ 4. trigger ArticleImporter
  ▼
ArticleImporter + ProofreadingAnalysisService
  │  - create Article(source=google_drive)
  │  - call AI + deterministic rules
  │  - store issues/history/decisions
  ▼
PostgreSQL (worklist_items, articles, proofreading_history,
           proofreading_decisions, article_status_history)
  │
  ▼
FastAPI Worklist APIs  +  React (Worklist & ProofreadingReviewPage)
```

### 数据流

1. Scheduler 触发 `POST /v1/worklist/sync`。
2. `GoogleDriveSyncService` 列出文件、解析内容（YAML front matter + 正文），Upsert WorklistItem。
3. 新建的 WorklistItem 触发 `ArticleImporter`：创建 Article → 触发 `ProofreadingAnalysisService`。
4. 校对结果写入 `articles.proofreading_issues`、`proofreading_history`，WorklistItem 状态置为 `proofreading` 并关联 `article_id`。
5. `WorklistService` 提供列表/详情/状态更新 API；状态变更记录 `article_status_history`。
6. 前端 Worklist 列表周期性轮询 + WebSocket（可选）刷新，Drawer 提供“进入校对”入口。
7. `ProofreadingReviewPage` 调用 `/v1/articles/{id}` 获取原稿、建议稿、issues、Meta/SEO/FAQ；用户操作后调用决策 API，完成后更新状态。

### 模块职责

1. **Cloud Scheduler**：调度 Cron、OIDC 认证。
2. **GoogleDriveSyncService**：Drive API 调用、内容解析、Upsert、错误记录。
3. **ArticleImporter**：创建 Article、写入 metadata、将 WorklistItem 与 Article 关联。
4. **ProofreadingAnalysisService**：封装 AI 调用 + 确定性规则，支持失败重试。
5. **WorklistService / API**：列表/详情/状态更新/统计/同步状态。
6. **Frontend Worklist**：状态过滤、Drawer、CTA、错误提示。
7. **ProofreadingReviewPage**：diff 渲染、交互、提交决策、更新 Worklist。
8. **Monitoring**：Cloud Logging、告警、仪表盘。

### 数据库影响

- `worklist_items`
  - `status` 改为字符串枚举 `pending/proofreading/...`
  - 新增 `status_history`（JSONB）缓存最近几条记录（可选）。
- `articles`
  - `source_type` 默认 `manual` → 改为包含 `google_drive`。
  - 确保 `proofreading_issues` 字段存储最新 AI 结果。
- `article_status_history`
  - 新建（若尚未存在）；记录 `article_id/old_status/new_status/changed_by/metadata/created_at`。
- `proofreading_history` & `proofreading_decisions`
  - 已存在的表需要保证通过 ORM 写入。

---

## 📊 当前实现状态

### ✅ 已完成

1. Google Drive API 集成（Service Account、YAML 解析、下载）。
2. `GoogleDriveSyncService` Upsert 逻辑与统计输出。
3. `POST /v1/worklist/sync` API（手动触发）。
4. Cloud Run 部署、Drive 凭证、文件夹 ID 配置。

### ⏳ 待实施

1. Cloud Scheduler Job + OIDC 认证。
2. Worklist 状态枚举 & 状态历史持久化。
3. Article 自动创建 + Proofreading 自动触发。
4. Worklist 详情 API / Drawer UI / CTA。
5. ProofreadingReviewPage（左右分屏 diff + 决策提交流程）。
6. 监控与告警（同步失败、校对失败、状态异常）。

---

## 🧑‍💻 用户体验

### 用户场景

1. **内容团队更新文章**  
   编辑在 Drive 修改稿件 → ≤5 分钟内 Worklist 自动刷新，状态为“校对中”，无需手动同步。
2. **批量上传新稿**  
   一次上传 10 篇文章 → Worklist 自动产生 10 条记录并触发校对，队列显示“待处理/校对中”。
3. **校对失败告警**  
   AI 服务异常 → Worklist 状态为 `failed`，Drawer 展示错误信息与“重试校对”按钮，Slack 收到失败告警。
4. **进入校对审查**  
   Worklist Drawer 点击“进入校对”→ ProofreadingReviewPage 左右分屏 diff，编辑逐项确认，提交后状态变为“待发布”。

### UI 变更

- **Worklist 列表**：
  - Badge 颜色 + 文案与 7 状态同步。
  - 新增 `status` 过滤器（全部/待处理/校对中/审核中/...）。
  - 列表行展示 `article_id`、Drive 链接、最新同步时间。
- **Worklist Drawer**：
  - 状态时间线、字数、阅读时长、质量/SEO score、错误提示。
  - “Google Doc 中打开”“进入校对”“重试同步”按钮。
- **ProofreadingReviewPage**：
  - 顶部概览：关键/错误/警告/信息数量、AI 模型、脚本命中数。
  - 左右分屏 diff（支持段落定位、高亮、规则标签、置信度）。
  - Meta 描述 / SEO 关键词 / FAQ Schema 卡片，支持一键接受。
  - 备注输入框 + 决策提交按钮，成功后 toast + 状态更新。

---

## 🧪 测试方案

### 后端
- **单元测试**：
  - `GoogleDriveSyncService`：YAML 解析、Upsert、错误分支。
  - `WorklistService`：状态过滤、详情、状态历史写入。
  - `ProofreadingAnalysisService`：成功/失败/重试路径，确保写入 history。
- **集成测试**：
  1. 伪造 Drive 文档 → `POST /v1/worklist/sync` → 验证 Worklist & Article & Proofreading 数据链路。
  2. `GET /v1/worklist/{id}` 返回正文、历史、notes、校对摘要。
  3. `POST /v1/worklist/{id}/status` 同时写入历史与 notes。
  4. `POST /api/v1/proofreading/decisions` 写入决策，并确认 Worklist notes 更新。

### 前端
- **单元测试 (Vitest)**：
  - WorklistStatusBadge 渲染 7 状态。
  - Drawer：时间线/备注/CTA/错误信息。
  - ProofreadingReviewPage 组件：diff 渲染、Meta/SEO 卡片、批量接受按钮。
- **E2E (Playwright)**：
  1. 同步后 Worklist 自动显示新稿且状态=“校对中”。
  2. Drawer → “进入校对” → 审查页加载成功。
  3. 接受所有建议 → 状态切换为“待发布”。
  4. 模拟校对失败 → Drawer 显示错误 + 重试按钮，重试后恢复。

### 性能/稳定性
- Scheduler 连续运行 24h 成功率 ≥99%。
- 自动校对并发 5 条任务 CPU 利用率 < 80%。
- Worklist 页面 100 条数据加载 <1s；审查页 diff 渲染 <2s。

---

## 📈 成功指标 & 监控

### KPI
1. 同步成功率 ≥ 99%。
2. 自动校对触发成功率 ≥ 97%。
3. 平均同步时间 < 10 秒。
4. Proofreading pipeline 平均耗时 < 3 分钟。
5. Worklist → 审查入口点击成功率 100%。
6. 手动同步次数下降 80%。

### 监控
- Cloud Logging：同步次数、失败原因、耗时。
- 自定义指标：自动校对成功/失败、状态分布、决策数量。
- 仪表盘：Worklist 状态堆叠图、Proofreading issue 分类。

### 告警
- 连续 3 次同步失败。
- 自动校对失败率 >5%（5 分钟窗口）。
- Worklist 中 `failed` 状态持续 30 分钟未处理。
- 审查页加载失败率 > 2%（前端埋点）。

---

## 🚧 风险与限制

| ID | 风险/限制 | 影响 | 缓解措施 |
|----|-----------|------|----------|
| R-1 | Google Drive API 配额超限 | 中 | 监控请求数，必要时降低频率或分页。 |
| R-2 | Cloud Run 冷启动导致同步超时 | 低 | `min-instances=1`，并设置 10 分钟超时。 |
| R-3 | AI 调用失败导致无法进入审查 | 高 | Celery 重试、失败告警、允许手动重试。 |
| R-4 | Worklist 状态与 UI 不一致 | 中 | 单一枚举源、Schema 校验、E2E 覆盖。 |
| R-5 | 大文档 diff 性能问题 | 中 | 分段 diff、虚拟滚动、懒加载。 |
| L-1 | 单次同步最多 100 文件 | 低 | 可通过分页或多文件夹缓解。 |
| L-2 | 校对耗时受外部模型影响 | 中 | 超时 fallback 到确定性结果、排队机制。 |

---

## 💰 成本估算

| 服务 | 使用量 | 单价 | 月度成本 |
|------|--------|------|---------|
| Cloud Scheduler | 1 job | $0.10/job/月 | **$0.10** |
| Cloud Run 调用 | 8,640 次/月 | Free tier | **$0.00** |
| Google Drive API | 8,640 次/月 | Free | **$0.00** |
| Cloud Logging | ~1 GB/月 | $0.50/GB | **$0.50** |
| Anthropic API | ~1,500 调用/月 | $0.00004/token（估） | **$40** |
| **总计** |  |  | **≈ $40.60/月** |

> 注：Anthropic 成本根据平均 25k token/篇、60 篇/天估算；如采用缓存/批量策略可进一步下降。

---

## 📅 实施时间线

| Phase | 主要内容 | 负责人 | 预估工期 |
|-------|----------|--------|----------|
| Phase 1 | Cloud Scheduler + IAM + 配置 | DevOps | 0.5 天 |
| Phase 2 | 后端数据流水线（状态、Article、Proofreading、API） | Backend | 5 天 |
| Phase 3 | Worklist 列表 & Drawer | Frontend | 3 天 |
| Phase 4 | ProofreadingReviewPage & 决策 API | Frontend + Backend | 4 天 |
| Phase 5 | 测试、E2E、监控告警 | QA + DevOps | 2 天 |
| **总计** |  |  | **约 10.5 工作日** |

---

## ✅ 验收标准

### 功能
- [ ] Cloud Scheduler job 已创建并按频率运行。
- [ ] Worklist 自动生成记录并关联 Article，状态从 `pending → proofreading → under_review → ready_to_publish` 正常流转。
- [ ] Worklist 详情 API 返回正文、历史、校对摘要、Drive 链接、错误信息。
- [ ] Drawer 展示时间线、质量评分、错误提示，“进入校对”跳转成功。
- [ ] ProofreadingReviewPage 支持 diff、接受/拒绝/编辑、Meta/SEO/FAQ 卡片。
- [ ] 提交人工决策后写入 `proofreading_decisions` 与 Worklist notes，状态变为 `ready_to_publish`。

### 技术
- [ ] IAM/认证正确，Scheduler→Cloud Run 的 OIDC token 验证通过。
- [ ] 自动校对失败会触发重试与告警，Worklist 可手动重试。
- [ ] `article_status_history` / `proofreading_history` / `proofreading_decisions` 数据完整。
- [ ] Worklist API 单元/集成测试覆盖率 ≥ 80%。

### 文档 & 运维
- [ ] README / plan / tasks 文档更新到位。
- [ ] 监控与告警仪表盘可查看关键指标。
- [ ] QA 测试报告包含同步和校对流程。 

---

**审批:** 待审批  
**实施者:** 待分配  
**审阅者:** 待分配
