# Phase 1 界面精简分析

## 背景概述
- 目标：在首个发布阶段（Phase 1）缩减前端可见范围，聚焦「工作清单」核心流程。
- 关键需求：
  1. 取消全局导航菜单。
  2. 将「校对规则」「标签管理」两类管理功能归入设置页。
  3. 将 `/worklist` 作为新的首页（默认路由）。
  4. 其余功能暂时隐藏，并在规格集中登记为后续迭代项。

## 现状评估
- 导航组件与路由  
  - `frontend/src/components/layout/Navigation.tsx` 与 `MobileMenu.tsx` 提供桌面与移动端主导航。  
  - `frontend/src/App.tsx` 在所有页面上渲染 `<Navigation />`。  
  - `frontend/src/config/routes.ts` 声明 15 个主路由，并通过 `showInNav` 控制是否出现在菜单。
- 工作清单  
  - `frontend/src/pages/WorklistPage.tsx` 已实现 Google Drive 同步 + 7 阶段审核工作流，是要求中的「核心首页」。
- 校对规则与标签管理  
  - 校对相关：`frontend/src/pages/PublishedRulesPage.tsx`、`frontend/src/components/proofreading/...`。  
  - 标签页面：`frontend/src/pages/TagsPage.tsx` 当前仅为占位文本。  
  - 设置页：`frontend/src/pages/SettingsPageModern.tsx` 已有折叠式布局，可扩展附加配置面板。

## 差距与改动点
1. **取消导航**
   - 移除或条件隐藏 `Navigation` / `MobileMenu`，避免 Phase 1 暴露未完成页面。
   - 处理 HashRouter 的默认 landing：去除导航后需确保用户仍可返回设置。

2. **首页重定向**
   - 将 `/` 路由映射到 WorklistPage 或在 App 初始化时强制重定向到 `/worklist`。
   - 更新 `routes.ts` 元数据，确保 `showInNav` 字段对 Phase 1 不再起作用。

3. **设置页聚合管理功能**
   - 在 `SettingsPageModern.tsx` 中新增 Accordion 分节，用于：
     - 手动维护标签（临时方案可放置“敬请期待”提示 + 链接到未来设计）。
     - 管理校对规则入口（同上，展示引用/禁用或占位说明）。
   - 隐藏原独立路由 `/tags`、`/proofreading/...`，避免直达访问。

4. **隐藏其余功能**
   - 通过路由守卫或条件渲染，Phase 1 只保留：`/worklist`、`/settings`。  
   - 对已有文件保留代码但不对外暴露（供后续迭代复用）。

5. **规格登记未来工作**
   - 需创建或更新一个待办列表（本文件之外额外 Markdown），描述被隐藏的功能及其状态，置于 `specs/` 目录作为“未来工作说明”。

## 建议实施步骤
1. **路由与重定向**  
   - 调整 `routes.ts`，在 Phase 1 构建配置中仅导出必要路由；其他路由移入“未来功能”列表。  
   - 配置默认路径 `HashRouter` -> `/worklist`。

2. **导航组件清理**  
   - 在 `App.tsx` 中删除 `<Navigation />`，并清理关联样式空位。  
   - 如后续需要，可保留组件但仅在 Phase >1 时挂载。

3. **设置页扩展**  
   - 增加“标签管理（草稿）”“校对规则（草稿）”分组：  
     - Phase 1 中可放置说明 + 按钮禁用状态。  
     - 引导用户了解未来能力，避免误解。

4. **未来功能档案**  
   - 新增 Markdown（例如 `specs/FUTURE_SCOPE_BACKLOG.md`），列出被隐藏的页面、相关接口和预期完善点。  
   - 标注来源路由与当前缺口，方便下一阶段恢复开发。

## 风险与依赖
- **路由访问风险**：旧链接可能直达隐藏页面，需返回 404 或重定向。  
- **设置页面复杂度**：将多个功能塞入设置，需要清晰划分折叠面板与开关提示。  
- **协作同步**：后端/QA 必须了解 Phase 1 Scope，避免测试或 API 校验覆盖隐藏端点。

## 交付物清单
1. 前端代码调整（导航、路由、设置页入口）。  
2. `specs/FUTURE_SCOPE_BACKLOG.md`（待建）记录所有被隐藏页面的后续工作。  
3. 如有发布说明，需在 README 或 Release Notes 中注明 Phase 1 限制。

