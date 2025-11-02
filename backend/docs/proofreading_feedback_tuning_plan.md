# 校对反馈调优功能 - 需求与实施方案分析

**版本**: 1.0.0  
**创建日期**: 2025-10-27  
**适用范围**: Proofreading & SEO 建议的用户决策、反馈调优闭环  
**说明**: 这里的“调优”指语言质量/运营团队基于用户反馈，手动复盘并修订 deterministic 脚本或 AI Prompt；**不包含**任何机器学习模型训练。

---

## 1. 背景与目标

### 1.1 背景
- 校对/SEO/TAG 建议产生后，用户可能接受、拒绝或部分采纳。
- 过往系统仅记录“最终内容”，缺乏对拒绝原因、用户偏好的结构化沉淀。
- Prompt 与脚本质量迭代主要依赖人工观察，缺少数据驱动依据。

### 1.2 目标
1. 捕捉用户对每条建议的决策（接受/拒绝/部分采用）。
2. 支持用户在拒绝/部分采用时提供可选的反馈原因与自定义说明。
3. 为语言质量/运营团队提供“待调优”的决策清单，形成复盘→调优→完成的闭环。
4. 将调优动作（脚本、Prompt 版本）与反馈记录关联，便于溯源与输出报表。
5. 提供仪表盘与 API 查看 pending/completed/failed 状态，支持重新处理失败项。

---

## 2. 需求分析

### 2.1 功能性需求
| 编号 | 需求描述 | 关键字段/接口 |
|------|----------|---------------|
| FR-D1 | 每条建议生成稳定的 `suggestion_id`（UUID），在校对结果中返回 | ProofreadingResponse.issues |
| FR-D2 | 用户对建议执行“接受/保留原文/部分采纳”，可批量提交 | `POST /api/v1/proofreading/decisions` |
| FR-D3 | 拒绝或部分采纳时，提供预设反馈选项 + 自定义文本（可选） | `feedback_option_id`、`feedback_text` |
| FR-D4 | 同步记录最终文本（如部分采纳后用户编辑的版本） | `final_text` |
| FR-D5 | 批量提交时更新 `proofreading_history` 的统计：accepted/rejected/modified/pending_feedback/feedback_completed | DB 触发逻辑/Service |
| FR-D6 | 提供查询接口返回单篇文章的所有决策，含反馈、调优状态 | `GET /api/v1/proofreading/decisions?history_id=` |
| FR-D7 | 提供运营接口重置失败的反馈记录状态，用于重新复盘 | `PATCH /api/v1/proofreading/decisions/{id}/feedback-status` |
| FR-D8 | 后台 worker 仅消费 `feedback_status='pending'` 的记录，避免重复处理 | Celery Worker |
| FR-D9 | 处理完成后记录批次 (`tuning_batch_id`)、Prompt/规则版本、完成时间 | 数据库字段 |
| FR-D10 | 失败时写明原因，允许运营重置为 pending 重新处理 | `feedback_status='failed'` + error notes |
| FR-D11 | 仪表盘/API 支持按反馈状态、建议类型、Prompt/规则版本过滤统计 | Monitoring |
| FR-D12 | 所有操作写入审计日志，保留操作人、时间、修改前后状态 | Audit Service |

### 2.2 非功能性需求
- **性能**：批量提交 ≤ 50 条建议，接口响应时间 < 500ms（p95）。
- **一致性**：同一 `suggestion_id` 只允许存在一条最新决策（重复提交需校验）。
- **并发控制**：Worker 需使用行锁或乐观锁避免重复消费。
- **可观测性**：关键指标（pending/completed/failed 数量、平均处理时长）必须上报。
- **安全性**：反馈说明可能含敏感信息，需采用适当权限控制与脱敏策略。

---

## 3. 数据模型设计

### 3.1 表结构变更

1. **`proofreading_history`**  
   - 新增：`accepted_count`、`rejected_count`、`modified_count`、`pending_feedback_count`、`feedback_completed_count`、`last_feedback_processed_at`。  
   - 索引：`idx_proofreading_feedback_pending (pending_feedback_count)`。

2. **`proofreading_decisions`** *(新表)*  
   | 字段 | 说明 |
   |------|------|
   | id (UUID) | 主键 |
   | history_id | 对应 `proofreading_history.id` |
   | suggestion_id | 建议唯一标识 |
   | suggestion_type | proofreading / seo / tag / segmentation / other |
   | rule_id | 对应规则编号（可选） |
   | original_text / suggested_text / final_text | 原始/建议/最终文本 |
   | decision | accepted / rejected / modified |
   | feedback_option_id / feedback_text | 反馈选项与自定义说明 |
   | decided_by / decided_at | 决策人与时间 |
   | feedback_status | pending / in_progress / completed / failed |
   | feedback_processed_at | 调优完成时间 |
   | tuning_batch_id | 调优批次（UUID，可选） |
   | prompt_or_rule_version | 调优后采用的 Prompt/规则版本 |
   | metadata (JSONB) | 扩展信息（如阻断原因、上下文标签） |

   索引：  
   - `idx_decisions_history (history_id)`  
   - `idx_decisions_suggestion (suggestion_id)`  
   - `idx_decisions_feedback_status (feedback_status, decided_at)`

3. **`feedback_tuning_jobs`** *(可选)*  
   - 记录每次 Prompt/规则调优的批次：`job_type`、`target_version`、`status`、`started_at/completed_at`。
   - 与 `proofreading_decisions` 的 `tuning_batch_id` 关联。

### 3.2 现有表字段复用
- `feedback_options`（若已有）：配置多语言反馈选项列表。
- `audit_logs`：记录运营操作（重置状态等）。

---

## 4. 服务与 API 设计

### 4.1 服务层调整
- `ProofreadingAnalysisService`：返回时附带 `suggestion_id`、`suggestion_type`，保存在 history 中。
- 新增 `ProofreadingDecisionService`：
  - `record_user_decisions(history_id, decisions[])`
  - `list_decisions(history_id, filters)`
  - `update_feedback_status(decision_id, status, operator)`
  - 触发事件 `proofreading.decision.recorded`，供监控/调优队列使用。

### 4.2 API 规范
1. `POST /api/v1/proofreading/decisions`  
   - Body: `{ "history_id": 456, "decisions": [ ... ] }`  
   - 校验：history 存在、suggestion_id 属于该 history、重复提交处理。  
   - 返回：更新后的 `accepted_count` 等统计。

2. `GET /api/v1/proofreading/decisions`  
   - 参数：`history_id`（必填）、`decision`、`feedback_status`、`suggestion_type`、分页参数。  
   - 返回列表 + 汇总信息。

3. `PATCH /api/v1/proofreading/decisions/{id}/feedback-status`  
   - Body: `{ "feedback_status": "pending", "note": "手动复盘失败，重新排期" }`  
   - 权限：仅运营/语言质量角色。  
   - 行为：更新状态 → 写审计日志 → 若改为 pending，重新入队。

### 4.3 Worker / Pipeline
- 名称：`feedback_export_worker`  
- 流程：  
  1. 拉取 `feedback_status='pending'` 的记录（可批量）。  
  2. 标记为 `in_progress`，写入处理人/时间。  
  3. 输出调优所需素材（如导出到 S3、写入调优看板、通知语料团队）。  
  4. 人工复盘完成后调用内部接口将状态更新为 `completed` 并补充 `tuning_batch_id`、`prompt_or_rule_version`。  
  5. 失败时标记 `failed` 并记录错误信息。  
- 错误处理：自动重试有限次，最终失败交由运营手动重置。

### 4.4 审计与监控
- 审计日志：  
  - 记录决策提交者、时间、变更前后状态。  
  - 运营重置状态时必须留存 `note`。
- 指标：  
  - `feedback_pending_total`、`feedback_completed_total`、`feedback_failed_total`。  
  - 平均处理时长（决定时间 → feedback_processed_at）。  
  - 按 Prompt/规则版本统计的反馈数量与拒绝率。  
- 仪表盘：`monitoring/dashboards/proofreading_feedback_tuning.json`。

---

## 5. 前端与 UX 要求

### 5.1 建议卡片交互
- 按建议类型显示按钮：`接受`、`保留原文`、`部分采纳`。
- 拒绝/部分采纳时弹出反馈面板：
  - 预设反馈选项（复选框）。
  - 可选自定义说明（限长 500 字）。
  - 最终文本展示与可编辑（部分采纳时）。
- 允许批量操作并缓存未提交的决策，支持撤销或修改。
- 成功提交后在 UI 上标记状态（颜色或角标），并可展开查看反馈详情。

### 5.2 决策历史查看
- 在文章详情页提供“反馈记录”标签，展示所有决策（含反馈、状态、处理时间）。
- 运营界面提供筛选、导出功能，便于批量分析。

---

## 6. 调优流程与角色分工

| 角色 | 权限 | 职责 |
|------|------|------|
| 编辑/作者 | 提交决策 | 反馈内容和最终文本 |
| 语言质量团队 | 查看 pending 列表、完成调优后更新状态 | 复盘拒绝原因、调整规则/Prompt |
| 运营 | 监控仪表盘、重置失败状态 | 保证流程顺畅、协调调优批次 |
| 工程 | 维护 worker、指标和审计 | 保证系统运行可靠 |

> 建议在调优完成后同步产出文档记录：“使用的反馈条目 + 调整设计 + 影响范围”，供 PM/研发跟踪。

---

## 7. 集成测试与验证

新增 `tests/integration/test_05_proofreading_feedback.py`：
1. `test_submit_decisions_batch`：验证批量提交后数据库写入与 history 计数更新。
2. `test_get_decisions_with_feedback_status`：验证分页、过滤与返回字段。
3. `test_feedback_export_status_transition`：模拟 worker 将记录从 pending→in_progress→completed，覆盖失败重置流程。

---

## 8. 任务拆分与里程碑

参考 `specs/001-cms-automation/tasks.md` Phase 7：
1. **T7.1** 数据库迁移与模型扩展  
2. **T7.2** 后端决策写入服务 + 事件发布  
3. **T7.3** REST API 与权限控制  
4. **T7.4** 前端交互与反馈收集 UI  
5. **T7.5** 反馈调优导出 Worker  
6. **T7.6** 调优监控仪表盘与指标

---

## 9. 风险与缓解措施

| 风险 | 描述 | 缓解策略 |
|------|------|-----------|
| 数据一致性 | 同一建议多次提交导致状态混乱 | 提交时加唯一约束（history_id, suggestion_id）+ 幂等处理 |
| 反馈质量不足 | 用户拒绝但不提供说明 | 预设选项覆盖常见原因，允许运营补充备注 |
| 调优滞后 | pending 堆积导致 Prompt/规则更新缓慢 | 仪表盘 + SLA（如 48 小时内处理）并设提醒机制 |
| 权限滥用 | 非授权人员重置状态 | 强制校验角色 + 审计日志 |
| 统计误导 | 反馈数据未区分建议类型 | 在仪表盘中按 suggestion_type、rule_id 分类展示 |

---

## 10. 文档与对外沟通

- 更新 `specs/001-cms-automation/requirements.md`、`tasks.md`、`spec.md`、`INTEGRATION_TESTS_SUMMARY.md`（已完成）。
- 新增用户操作文档（FAQ、最佳实践），指导编辑如何提供有效反馈。
- 在产品变更日志中注明：反馈调优功能上线，帮助团队更好地收集拒绝原因。

---

**结论**：通过该功能，系统能够持续捕捉用户决策与反馈，将拒绝原因沉淀为结构化数据，为 Prompt 与 deterministic 规则的人工调优提供可追踪、可量化的闭环支持，从而不断提升校对与 SEO 建议的质量。***
