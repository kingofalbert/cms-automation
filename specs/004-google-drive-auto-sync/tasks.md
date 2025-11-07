# Google Drive 自动同步 + 校对闭环 - 任务列表

**Feature ID:** 004-google-drive-auto-sync  
**状态:** 待实施 (Planned)  
**预估总工期:** ~10.5 工作日

---

## 📊 任务总览

| Phase | 任务数 | 预估时间 | 负责人 |
|-------|--------|----------|--------|
| Phase 1: Cloud Scheduler & IAM | 4 | 0.5 天 | DevOps |
| Phase 2: 后端数据流水线 | 8 | 5 天 | Backend |
| Phase 3: Worklist 列表 & Drawer | 5 | 3 天 | Frontend |
| Phase 4: ProofreadingReviewPage & 决策 | 6 | 4 天 | Frontend + Backend |
| Phase 5: 测试、监控、发布 | 6 | 2 天 | QA + DevOps |
| **总计** | **29** | **≈10.5 天** | |

> 状态图例：`⏳ 待开始` / `🚧 进行中` / `✅ 完成`

---

## Phase 1: Cloud Scheduler & IAM (DevOps)

### Task 1.1 创建/验证 Service Account — ⏳
- **目标:** `cloud-scheduler-runner@cmsupload-476323.iam.gserviceaccount.com`
- **步骤:**
  1. `gcloud iam service-accounts list ... --filter="cloud-scheduler-runner"`。
  2. 若不存在，执行 `gcloud iam service-accounts create ...`。
  3. 将邮箱记录在 Runbook。
- **验收:** SA 存在且不可被删除；README/Runbook 更新。

### Task 1.2 授予 Cloud Run Invoker — ⏳
- **命令:**
  ```bash
  gcloud run services add-iam-policy-binding cms-automation-backend \
    --project=cmsupload-476323 \
    --region=us-east1 \
    --member="serviceAccount:cloud-scheduler-runner@cmsupload-476323.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
  ```
- **验收:** `gcloud run services get-iam-policy` 可看到该 SA。

### Task 1.3 创建 Cloud Scheduler Job — ⏳
- **命令:**
  ```bash
  gcloud scheduler jobs create http google-drive-sync-cron \
    --project=cmsupload-476323 \
    --location=us-east1 \
    --schedule="*/5 * * * *" \
    --time-zone="America/New_York" \
    --uri="https://cms-automation-backend-baau2zqeqq-ue.a.run.app/v1/worklist/sync" \
    --http-method=POST \
    --oidc-service-account-email="cloud-scheduler-runner@cmsupload-476323.iam.gserviceaccount.com" \
    --oidc-token-audience="https://cms-automation-backend-baau2zqeqq-ue.a.run.app" \
    --headers="Content-Type=application/json" \
    --message-body='{}'
  ```
- **验收:** `gcloud scheduler jobs describe google-drive-sync-cron` status=ENABLED。

### Task 1.4 手动触发 + 记录日志 — ⏳
- `gcloud scheduler jobs run google-drive-sync-cron ...`
- 确认 Cloud Logging 中出现 `worklist_sync` 条目。
- 更新 Runbook：如何停用/启用 Job、如何修改 schedule。

---

## Phase 2: 后端数据流水线 (Backend)

### Task 2.1 Worklist 状态枚举迁移 — ⏳
- **内容:** 更新 `backend/src/models/worklist.py`，枚举改为 7 个新状态。
- **迁移:** Alembic 迁移脚本，将旧值（`to_evaluate` 等）映射到新值。
- **验收:** 单元测试覆盖 `WorklistStatus` 枚举；数据库中无旧值。

### Task 2.2 Article 状态历史表 — ⏳
- 创建 `article_status_history`（如果尚未存在）或扩展字段。
- 编写 DAO/ORM + Service 写入逻辑。
- **验收:** 任何状态更新都会插入一行历史记录。

### Task 2.3 Worklist 详情 API — ⏳
- 新增 `GET /v1/worklist/{id}`：返回正文、Drive 元数据、状态历史、notes、校对摘要、Google Doc 链接。
- **验收:** Swagger 文档更新；单元测试覆盖 200 / 404 情况。

### Task 2.4 Worklist 列表增强 — ⏳
- `GET /v1/worklist` 增加过滤：status、author、date_range、search。
- 响应包含 `article_id`、`current_status`、`proofreading_summary`。
- **验收:** 新参数经由 schema 校验，返回分页数据。

### Task 2.5 Article 自动创建 — ⏳
- 在 `GoogleDriveSyncService._upsert_worklist_item` 后调用 `ArticleImporter`。
- 创建 Article（title/body/meta），source=google_drive。
- 存储 Drive metadata 至 `article.article_metadata`。
- **验收:** 新 WorklistItem 的 `article_id` 自动填充；若创建失败则 Worklist 状态 `failed`。

### Task 2.6 自动触发校对 — ⏳
- 调用 `ProofreadingAnalysisService`（同步或 Celery），写入 `articles.proofreading_issues`、`proofreading_history`。
- 将 Worklist 状态设置为 `proofreading`，完成后置为 `under_review`。
- **验收:** 数据库可见最新 issues / history；失败写入 notes 并触发告警。

### Task 2.7 Worklist 状态更新与 notes — ⏳
- 扩展 `POST /v1/worklist/{id}/status`：校验状态机、写入 history + notes。
- 支持“重试同步/校对”的特殊 note。
- **验收:** API 返回最新 WorklistItem，notes 中含操作人、时间。

### Task 2.8 监控与告警 — ⏳
- 在同步/Article/Proofreading 关键点写入结构化日志。
- 创建 Cloud Monitoring 指标 + Slack/Webhook 告警。
- **验收:** 故障模拟可触发告警；Runbook 记录响应步骤。

---

## Phase 3: Worklist 列表 & Drawer (Frontend)

### Task 3.1 状态枚举与 Badge 更新 — ⏳
- 更新 `WorklistStatus` 类型与 `WorklistStatusBadge` 组件。
- 新增状态过滤器下拉 & 本地化文案。

### Task 3.2 列表查询参数 & 轮询 — ⏳
- `WorklistPage` 使用新过滤器构建请求参数。
- 轮询间隔 30s；出现错误时显示 toast。

### Task 3.3 Drawer 数据绑定 — ⏳
- 调用新 `GET /v1/worklist/{id}`。
- 渲染状态时间线、质量/SEO score、备注历史、Drive 链接。

### Task 3.4 CTA & 错误处理 — ⏳
- “进入校对审查”：跳转 `/articles/{article_id}/proofreading`。
- “重试同步/校对”：调用新 API，展示 loading 与结果反馈。
- 错误状态（failed）展示红色提示。

### Task 3.5 样式/无障碍验证 — ⏳
- 响应式布局（≥1280 宽度三列）。
- 键盘导航、ARIA 属性。

---

## Phase 4: ProofreadingReviewPage & 决策 (Front/Back)

### Task 4.1 页面骨架与路由 — ⏳
- 新建 `frontend/src/pages/ProofreadingReviewPage.tsx`（替换占位符）。
- 注册路由 `/articles/:id/proofreading`。

### Task 4.2 数据获取与状态管理 — ⏳
- 调用 `/v1/articles/{id}`，解析正文/建议稿/Meta/SEO/FAQ/Issues。
- 使用 React Query 管理加载、错误状态。

### Task 4.3 Diff 与 Issue 列表 — ⏳
- 构建左右分屏 diff 组件；支持按 issue 滚动定位、高亮、规则标签、置信度。
- Issue 列表可筛选严重级别、来源（AI/Script）。

### Task 4.4 Meta/SEO/FAQ 卡片 — ⏳
- 展示原始/建议内容、长度/数量提示、评分。
- “接受建议”按钮将建议写回本地状态。

### Task 4.5 决策 API & 状态更新 — ⏳
- 新建 `POST /api/v1/proofreading/decisions`（若已存在则扩展），接收 decisions 列表、备注。
- 成功后调用 `POST /v1/worklist/{id}/status` 把状态设为 `ready_to_publish`。
- 前端展示 toast + 重定向 (可选)。

### Task 4.6 测试 & 错误处理 — ⏳
- Vitest：diff、issue 列表、Meta 卡片、按钮交互。
- Playwright：完整流（进入页面→接受建议→提交→Worklist 状态变化）。

---

## Phase 5: 测试、监控、发布 (QA + DevOps)

### Task 5.1 Backend 测试套件 — ⏳
- 新增 pytest 用例：同步流水线、状态历史、决策写入。
- CLI：`poetry run pytest backend/tests/test_worklist_auto_sync.py`。

### Task 5.2 Frontend 单元测试 — ⏳
- `npm run test -- WorklistStatusBadge.test.tsx` 等。
- 覆盖 Drawer、ProofreadingReviewPage 关键组件。

### Task 5.3 Playwright 场景 — ⏳
- **Scenario 1:** 同步→Worklist→Drawer→审查→提交。
- **Scenario 2:** 校对失败→告警→重试成功。
- 命令：`npm run test:e2e -- --project=chromium --grep @proofreading-flow`。

### Task 5.4 性能/稳定性验证 — ⏳
- Scheduler 连续运行 24h，记录 KPI。
- 压力测试：一次性导入 20 篇稿件。

### Task 5.5 监控 & 告警配置 — ⏳
- Cloud Monitoring dashboard + Slack 告警。
- Runbook：如何启停 Job、如何手动重试校对。

### Task 5.6 文档/验收 — ⏳
- 更新 README、Spec、Plan、Runbook。
- PM/UX 验收 Worklist + 审查体验。
- 输出 QA 报告与回归测试结果。

---

## ✅ 完成定义 (DoD)

- 所有任务更新状态为 ✅，且附带链接（PR/日志/截图）。
- 自动化测试（unit + integration + e2e）通过，CI 绿灯。
- 监控与告警已验证可用。
- Runbook、README、Spec/Plan/Tasks 同步更新。
- Stakeholder 签字确认上线。

