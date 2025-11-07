# 004: Google Drive 自动同步 + 校对闭环

**状态:** 📝 待实施 (Planned)  
**优先级:** High  
**预估工期:** ~10.5 工作日  
**最后更新:** 2025-11-07

---

## 📋 快速概述

该 Spec Kit 定义并计划了完整的“Google Drive → Worklist → 自动校对 → 人工审查 → 发布”流程。核心目标：

1. **自动同步**：Cloud Scheduler 每 5 分钟调用 `/v1/worklist/sync`，同步 Drive 文件。
2. **自动处理**：新稿自动创建 `Article` 并触发校对（AI + 确定性规则）。
3. **可视化跟踪**：Worklist 状态、详情、时间线与错误提示全面升级。
4. **人工确认**：实现 `ProofreadingReviewPage` 左右分屏 diff，支持逐项接受/拒绝。
5. **数据闭环**：人工决策写入 `proofreading_decisions`，便于调优与审计。

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| **[spec.md](./spec.md)** | 需求、架构、测试方案、验收标准的完整描述。 |
| **[plan.md](./plan.md)** | 分阶段实施计划、资源分配、风险与退出标准。 |
| **[tasks.md](./tasks.md)** | 29 个可执行任务，包含步骤、命令和验收标准。 |
| **README.md** | 本文件，快速导览与关键指标。 |

---

## 🎯 核心能力对比

| 能力 | 当前 | 目标 |
|------|------|------|
| Drive 同步 | 手动按钮 | Cloud Scheduler 自动触发 |
| Worklist 状态 | `to_evaluate` 等内部命名 | 业务语义：待处理/校对中/审核中… |
| Article 创建 | 无 | 自动创建 Article + 绑定 Worklist |
| 自动校对 | 手动触发 | 同步后自动触发 AI + Script 校对 |
| Worklist Drawer | 基础元数据 | 状态时间线、质量评分、错误信息、CTA |
| 校对审查 UI | 未实现 | 左右分屏 diff + Meta/SEO/FAQ 卡片 + 决策 |
| 决策追踪 | 无 | `proofreading_decisions` + notes + 告警 |

---

## ⛓️ 流程概览

```
Cloud Scheduler → POST /v1/worklist/sync
    ↓
GoogleDriveSyncService (解析/Upsert)
    ↓
ArticleImporter + ProofreadingAnalysisService
    ↓
PostgreSQL (worklist_items / articles / proofreading_*)
    ↓
Worklist API & Frontend (列表 + Drawer + 审查页)
```

---

## 🏗️ 实施阶段（摘要）

1. **Phase 1 – Cloud Scheduler & IAM (0.5 天)**  
   设置 Service Account、授权、Cron job。

2. **Phase 2 – 后端数据流水线 (5 天)**  
   状态机、Article 自动创建、校对调用、API 扩展、告警。

3. **Phase 3 – Worklist 列表 & Drawer (3 天)**  
   状态过滤、时间线、CTA、错误提示。

4. **Phase 4 – ProofreadingReviewPage (4 天)**  
   左右分屏 diff、Meta/SEO/FAQ 卡片、决策 API。

5. **Phase 5 – 测试 & 监控 (2 天)**  
   单元/集成/E2E、性能测试、仪表盘、Runbook。

---

## 📈 关键指标

- 同步成功率 ≥ 99%
- 自动校对触发成功率 ≥ 97%
- 平均同步时间 < 10 秒
- Proofreading pipeline 平均耗时 < 3 分钟
- Worklist→审查入口点击成功率 100%
- 手动同步次数下降 80%

监控/告警：
- Cloud Logging 指标 + Slack/Webhook 告警（同步失败、校对失败、`failed` 状态超时）。

---

## 🧪 测试矩阵

| 层级 | 工具 | 覆盖 |
|------|------|------|
| Backend Unit | pytest | Worklist 状态机、Article/Proofreading 自动化、API。 |
| Backend Integration | pytest + Test DB | `/v1/worklist/sync` → Article/Proofreading → API。 |
| Frontend Unit | Vitest | Worklist 组件、Drawer、审查页。 |
| E2E | Playwright | Drive 同步 → Worklist → Drawer → 审查 → 决策 → 状态更新。 |

---

## 🧭 快速开始

1. 阅读 [spec.md](./spec.md) 了解需求和验收标准。
2. 查看 [plan.md](./plan.md) 明确阶段与责任人。
3. 按 [tasks.md](./tasks.md) 顺序执行（支持勾选与链接）。
4. 更新 Runbook / README / 监控配置。

---

## 📞 相关资源

- 代码：`backend/src/services/google_drive/sync_service.py`, `backend/src/services/worklist/`, `frontend/src/pages/WorklistPage.tsx`。
- 文档：`docs/GOOGLE_DRIVE_AUTOMATION_ANALYSIS.md`, `docs/USER_EXPERIENCE_GUIDE_PROOFREADING.md`。
- GCP 控制台：Cloud Scheduler / Cloud Run / Cloud Logging / Cloud Monitoring。

---

**审批:** 待审批  
**实施者:** 待分配  
**审阅者:** 待分配

