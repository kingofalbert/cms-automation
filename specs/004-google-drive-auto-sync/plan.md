# Google Drive 自动同步 + 校对闭环 - 实施计划

**Feature ID:** 004-google-drive-auto-sync  
**计划日期:** 2025-11-07  
**优先级:** High  
**预估总工期:** ~10.5 工作日

---

## 1. 计划概述

### 目标

- 用 Cloud Scheduler 替代手动同步，确保 Drive 文档 5 分钟内进入 Worklist。
- 自动创建 `Article` 并触发校对服务，维持 Worklist→Proofreading→Review 的闭环。
- 提供 Worklist 详情 + “进入校对”入口，以及完整的 `ProofreadingReviewPage` diff 体验。
- 让人工决策、状态历史与告警全部落地并可追踪。

### 里程碑

| 里程碑 | 说明 | 目标日期 |
|--------|------|----------|
| M1 | Cloud Scheduler + IAM 配置完成 | Day 1 |
| M2 | 后端状态机、Article 自动创建、校对流水线完成 | Day 5 |
| M3 | Worklist 列表 & Drawer 升级完成 | Day 8 |
| M4 | ProofreadingReviewPage + 决策 API 完成 | Day 10 |
| M5 | 测试、监控、验收 | Day 11 |

---

## 2. 阶段拆解

### Phase 1: Cloud Scheduler & 基础设施 (0.5 天)

**Objectives**
- 创建专用 Service Account 并授予 `roles/run.invoker`。
- 通过 OIDC 调用 Cloud Run `/v1/worklist/sync`。
- 配置 Cron（默认 */5 * * * *），支持通过 env 覆盖。

**Key Steps**
1. 检查/创建 `cloud-scheduler-runner@cmsupload-476323.iam.gserviceaccount.com`。
2. 使用 `gcloud run services add-iam-policy-binding` 授权 `roles/run.invoker`。
3. 创建 Scheduler job（`google-drive-sync-cron`），设置 POST、Content-Type、OIDC audience、message body。
4. 手动触发一次并在 Cloud Logging 验证结果。

**Exit Criteria**
- ✅ Scheduler job 正常运行；最近一次执行状态为 SUCCESS。
- ✅ `settings.DRIVE_SYNC_CRON_MINUTES` 支持覆盖频率。
- ✅ README/Runbook 记录创建命令。

### Phase 2: 后端数据流水线 (5 天)

**Objectives**
- 重构 Worklist 状态枚举、历史记录与 API。
- 自动创建 Article、触发 Proofreading，并将结果写入相关表。
- 设计告警与错误回退机制。

**Tasks**
1. **状态与模型更新**
   - 更新 `WorklistStatus` 枚举 → `pending/proofreading/under_review/...`。
   - 新增/迁移 `article_status_history` 表及 ORM。
   - 编写数据迁移脚本：旧状态映射（`to_review`→`under_review` 等）。

2. **Worklist API 扩展**
   - 列表 API 返回 `article_id`、`current_status`、概要统计。
   - 新建 `GET /v1/worklist/{id}` 返回正文、Drive 元数据、状态历史、notes、校对摘要。
   - `POST /v1/worklist/{id}/status` 支持写入 notes + history。

3. **Article + Proofreading 自动化**
   - 在 `GoogleDriveSyncService` Upsert 新文档后调用新的 `ArticleImporter` 服务。
   - 创建 Article（source=google_drive, body=content, metadata=Drive meta）。
   - 调用 `ProofreadingAnalysisService`（异步队列/同步调用），写入 `proofreading_history`、`articles.proofreading_issues`，将 Worklist 状态更新为 `proofreading`。
   - 捕获失败：状态标记 `failed`，notes 中写入错误信息。

4. **告警与可观测性**
   - Cloud Logging 中记录 `worklist_sync`、`article_auto_create`、`proofreading_auto_run` 事件。
   - 针对同步/校对失败添加 Slack/Webhook 告警。

**Exit Criteria**
- ✅ 新文档自动生成 Article 并触发校对；数据库可见历史记录。
- ✅ Worklist API 可返回完整详情与状态历史。
- ✅ 自动校对失败会被捕捉并可重试（API 或 Celery 任务）。

### Phase 3: Worklist 列表 & Drawer (3 天)

**Objectives**
- 让前端列表、筛选、Badge 与七个状态保持一致。
- Drawer 展示全部上下文，并提供 CTA。

**Tasks**
1. 更新 `WorklistStatusBadge` 枚举与颜色文本。
2. `WorklistPage` 增加状态过滤器（全部/待处理/校对中/...）、搜索、作者、日期区间等。
3. Drawer：
   - 状态时间线组件（根据 `article_status_history` 渲染）。
   - Metadata 卡片：字数、阅读时长、质量分、SEO 分。
   - 错误提醒+“重试同步/校对”按钮（调用新 API）。
   - “在 Google Drive 打开”+“进入校对审查”按钮。
4. 接入新详情 API，替换现有假数据。

**Exit Criteria**
- ✅ Worklist 列表渲染新的状态与过滤器。
- ✅ Drawer 使用真实 API 数据并可点击 CTA。
- ✅ 样式通过设计验收。

### Phase 4: ProofreadingReviewPage & 决策 (4 天)

**Objectives**
- 实现核心审查界面与交互，确保人工决策写回后端。

**Tasks**
1. 根据 Spec 构建页面布局：概览 → 左右分屏 diff → Meta/SEO/FAQ → CTA。
2. Diff 逻辑：支持逐项跳转、规则标签、置信度提示、段落级接受/拒绝/编辑。
3. Meta 描述/SEO 关键词/FAQ 卡片：显示评分、字数/数量提示，支持“一键接受”。
4. 备注输入和批量操作（“全部接受”“确认最终版本”）。
5. 调用新 `POST /api/v1/proofreading/decisions` API，把人工决策和备注写入数据库，并同步到 Worklist。
6. 成功提交后触发 Worklist 状态更新为 `ready_to_publish`，显示 toast。

**Exit Criteria**
- ✅ 审查页面在实际数据下正常渲染。
- ✅ 接受/拒绝结果能立即反映在 Worklist。
- ✅ Playwright 流程测试通过。

### Phase 5: 测试、监控与发布 (2 天)

1. **自动化测试**
   - Backend：pytest 增量覆盖（Worklist/Proofreading/Importer）。
   - Frontend：Vitest 组件测试 + Playwright E2E（Worklist→审查→状态更新）。
2. **性能/稳定**
   - Scheduler 连续运行 24h。
   - 校对流水线并发压力测试。
3. **监控/Runbook**
   - 更新 Grafana/Looker Studio 仪表盘。
   - Runbook：如何手动重试同步/校对、如何回滚。
4. **验收**
   - 按照 spec 中的验收清单逐项确认。

---

## 3. 资源与协作

| 角色 | 职责 |
|------|------|
| Backend Engineer | 状态机、API、Article/Proofreading 自动化、告警 |
| Frontend Engineer | Worklist UI、Drawer、ProofreadingReviewPage |
| DevOps | Cloud Scheduler、IAM、监控、告警 |
| QA | Test plan、自动化测试、E2E、验收 |
| PM/UX | 确认状态文案、UI 验收、文档同步 |

依赖：
- Anthropic API Key & 配额可用。
- Slack/Webhook 通道已配置。
- Playwright 测试环境可连接后端。

---

## 4. 风险与缓解

| 风险 | 描述 | 缓解 |
|------|------|------|
| AI 调用耗时过长 | 影响 Worklist 状态刷新 | 增加异步队列 + 超时 fallback；UI 展示“校对中”状态和重试按钮 |
| 枚举兼容性 | Worklist 旧数据使用旧状态值 | 提供迁移脚本 + 双写兼容 + 只读模式切换 |
| Diff 性能 | 大段文本渲染卡顿 | 使用虚拟列表/按段懒加载、浏览器性能 profiling |
| Scheduler 失败未告警 | 导致长时间无同步 | Cloud Build/Logging 告警 + Dashboard |

---

## 5. 沟通与文档

- 文档：`spec.md`（需求）、`plan.md`（本文件）、`tasks.md`（任务清单）、Runbook (DevOps)。
- 每日 stand-up 汇报阶段进度；关键节点（M2/M3/M4）需要 Demo。
- QA 测试用例存放于 `tests/README.md` 并在 PR 中引用。

---

## 6. 退出标准

- 所有 Phase 的 Exit Criteria 均达成。
- 自动化测试（backend+frontend+E2E）通过，覆盖率 ≥80%。
- 监控/告警上线，Runbook 更新。
- PM/UX 与业务侧确认 Worklist + 校对审查体验符合预期。
- Feature Flag（若使用）默认开启；如需灰度可在运行手册中说明切换步骤。

