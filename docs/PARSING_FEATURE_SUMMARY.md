# Article Structured Parsing Feature - Documentation Summary

**Date**: 2025-11-08
**Status**: ✅ Design Complete - Ready for Implementation
**Feature ID**: Article Structured Parsing (Phase 7)

---

## 📋 Executive Summary

本文档总结了文章结构化解析功能（Article Structured Parsing）的完整设计和规划工作。该功能是 CMS 自动化系统的关键升级，旨在将原始 Google Doc 内容转换为规范化的结构化数据，显著提升数据质量和下游处理效率。

### 核心价值

- **✅ 数据质量提升**：结构化字段支持精确验证
- **✅ 图片资产管理**：完整追踪源文件及技术规格
- **✅ SEO 优化增强**：显式元数据字段提升搜索优化效果
- **✅ 审计追踪完整**：解析确认状态确保问责制

### 关键变更

| 领域 | 当前状态 | 目标状态 |
|------|---------|----------|
| **标题存储** | 单一 `title` 字段 | `title_prefix`, `title_main`, `title_suffix` |
| **作者信息** | 嵌入在内容中 | 提取的 `author_line`, `author_name` |
| **正文** | 完整 HTML（包含所有内容） | 清理后的 `body_html`（无标题/图片/Meta） |
| **图片** | 内联引用 | 独立 `article_images` 表（含技术规格） |
| **SEO 字段** | 嵌入或缺失 | 提取的 `meta_description`, `seo_keywords`, `tags` |
| **审核流程** | 单步审核 | 两步流程（Step 1: 解析确认, Step 2: 正文校对） |

---

## 📚 完成的文档清单

### 1. 技术分析文档 ✅
**文件**: `docs/ARTICLE_PARSING_TECHNICAL_ANALYSIS.md`

**内容**:
- 完整的需求分解（数据库、后端、前端）
- 6 周实施计划（140 小时）
- 详细的成功标准和风险管理
- 数据模型设计（数据类和 JSONB 结构）
- API 设计和前端组件架构

**关键亮点**:
- AI 驱动的解析器（Claude 4.5 Sonnet）
- 图片处理管道（PIL/Pillow 提取规格）
- 两步 UI 工作流（解析确认 → 正文校对）
- 完整的错误处理和降级策略

---

### 2. 功能规格更新 ✅
**文件**: `specs/001-cms-automation/spec.md`

**新增内容**:
- **User Story 7**: Structured Article Parsing & Review Confirmation
  - 7 个验收场景（标题解析、作者提取、图片处理、Meta 提取、UI 确认等）
  - P0 优先级（数据质量基础）

- **FR-088 to FR-105**: 18 项功能需求
  - **Backend Parsing Engine** (FR-088 to FR-093): AI 解析器、图片下载、Meta 提取、HTML 清理
  - **Database Schema** (FR-094 to FR-096): 扩展 `articles` 表、新建 `article_images` 和 `article_image_reviews` 表
  - **Frontend Step 1 UI** (FR-097 to FR-102): 解析确认 UI、图片规格表、Step 2 阻断逻辑
  - **Image Processing** (FR-103 to FR-105): ImageProcessor 服务、EXIF 提取、发布前预处理（future）

- **Key Entities 更新**:
  - 更新 `Articles` 实体（新增解析字段，标记弃用字段）
  - 新增 `Article Images` 实体（JSONB metadata 结构）
  - 新增 `Article Image Reviews` 实体

- **Success Criteria**: SC-016 到 SC-023（8 项新标准）
  - 解析准确率 ≥90%
  - 解析延迟 ≤20 秒
  - 图片元数据完整率 100%
  - Step 1 UI 操作时间 <2 分钟
  - 测试覆盖率 ≥85% (backend), ≥80% (frontend)

---

### 3. 实施计划更新 ✅
**文件**: `specs/001-cms-automation/plan.md`

**新增内容**:
- **Phase 7 - Article Structured Parsing** (6 weeks, Week 16-21)

**详细任务分解**:

#### Week 16: Database Schema & Migrations (16h)
- T-PARSE-1.1: 设计扩展的 Articles Schema (4h)
- T-PARSE-1.2: 创建 Alembic 迁移 (6h)
- T-PARSE-1.3: 更新 SQLAlchemy 模型 (4h)
- T-PARSE-1.4: 在开发环境测试迁移 (2h)

#### Week 17-18: Backend Parsing Engine (40h)
- T-PARSE-2.1: 实现 ArticleParserService 骨架 (6h)
- T-PARSE-2.2: 实现标题解析（AI + fallback）(8h)
- T-PARSE-2.3: 实现作者提取 (4h)
- T-PARSE-2.4: 实现图片提取 (10h)
- T-PARSE-2.5: 实现 ImageProcessor 服务 (6h)
- T-PARSE-2.6: 实现 Meta/SEO 提取 (4h)
- T-PARSE-2.7: 实现正文 HTML 清理 (4h)

#### Week 19: API & Integration (12h)
- T-PARSE-3.1: 扩展 Worklist API (4h)
- T-PARSE-3.2: 创建解析确认端点 (4h)
- T-PARSE-3.3: 集成解析器到 Google Drive Sync (4h)

#### Week 20-21: Frontend Step 1 UI (48h)
- T-PARSE-4.1: 创建 Step Indicator 组件 (4h)
- T-PARSE-4.2: 构建结构化标题卡片 (6h)
- T-PARSE-4.3: 构建作者信息卡片 (4h)
- T-PARSE-4.4: 构建图片画廊卡片（含规格表）(12h)
- T-PARSE-4.5: 构建 Meta/SEO 卡片 (6h)
- T-PARSE-4.6: 构建正文 HTML 预览卡片 (4h)
- T-PARSE-4.7: 实现确认操作和状态管理 (6h)
- T-PARSE-4.8: 添加 Step 2 阻断逻辑 (4h)
- T-PARSE-4.9: i18n 支持 (2h)

#### Week 21: Integration & Testing (24h)
- T-PARSE-5.1: 端到端工作流测试 (8h)
- T-PARSE-5.2: 解析准确性验证 (8h)
- T-PARSE-5.3: 性能测试 (4h)
- T-PARSE-5.4: Bug 修复和边缘案例处理 (4h)

**成功标准**:
- 解析准确率 ≥90%
- 解析延迟 ≤20 秒
- 图片元数据完整率 100%
- 测试覆盖率 ≥85% (backend), ≥80% (frontend)

**风险管理**:
- AI 解析准确率 <90% → 广泛测试套件、Fallback 启发式、迭代 Prompt 工程
- 图片下载失败 → 重试逻辑、保存部分结果、手动上传选项
- 解析延迟 >20 秒 → 异步处理、进度指示器、优化 Claude Prompts

---

### 4. 数据模型规范更新 ✅
**文件**: `specs/001-cms-automation/data-model.md`

**新增内容**:

#### 扩展的 `articles` 表
```sql
-- Article Structured Parsing Fields 🆕 (Phase 7)
title_prefix VARCHAR(200),                  -- 前标题（可选）
title_main VARCHAR(500) NOT NULL,           -- 主标题（必需）
title_suffix VARCHAR(200),                  -- 副标题（可选）
author_line VARCHAR(300),                   -- 原始作者行（如 "文／张三"）
author_name VARCHAR(100),                   -- 清理后的作者名（如 "张三"）
body_html TEXT,                             -- 清理后的正文 HTML
meta_description TEXT,                      -- 提取的 Meta 描述
seo_keywords TEXT[],                        -- SEO 关键词数组
tags TEXT[],                                -- 内容标签/分类数组
parsing_confirmed BOOLEAN DEFAULT FALSE,    -- 解析是否已审核确认
parsing_confirmed_at TIMESTAMP,             -- 确认时间
parsing_confirmed_by VARCHAR(100),          -- 确认人
parsing_feedback TEXT,                      -- 审核反馈
```

#### 新表: `article_images`
```sql
CREATE TABLE article_images (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    preview_path VARCHAR(500),           -- 预览/缩略图路径
    source_path VARCHAR(500),            -- 下载的高分辨率源图路径
    source_url VARCHAR(1000),            -- 原始"点此下载"URL
    caption TEXT,                        -- 图片标题
    position INTEGER NOT NULL,           -- 段落索引（从 0 开始）
    metadata JSONB,                      -- 技术规格
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT positive_position CHECK (position >= 0)
);
```

**JSONB metadata 结构**:
```json
{
  "width": 1920,
  "height": 1080,
  "aspect_ratio": "16:9",
  "file_size_bytes": 2458624,
  "mime_type": "image/jpeg",
  "format": "JPEG",
  "color_mode": "RGB",
  "has_transparency": false,
  "exif_date": "2025-11-08T10:30:00Z",
  "download_timestamp": "2025-11-08T12:00:00Z"
}
```

#### 新表: `article_image_reviews`
```sql
CREATE TABLE article_image_reviews (
    id SERIAL PRIMARY KEY,
    article_image_id INTEGER NOT NULL REFERENCES article_images(id) ON DELETE CASCADE,
    worklist_item_id INTEGER,
    action VARCHAR(20) NOT NULL CHECK (action IN (
        'keep', 'remove', 'replace_caption', 'replace_source'
    )),
    new_caption TEXT,
    new_source_url VARCHAR(1000),
    reviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**ER Diagram 更新**:
- 添加 `articles ||--o{ article_images : "has images"`
- 添加 `article_images ||--o{ article_image_reviews : "has reviews"`

**Version History**:
- Version 4.0 (2025-11-08): Added article structured parsing, article_images, article_image_reviews

---

## 🎯 下一步行动

### 立即行动（本周）

1. **✅ 技术审查会议**
   - 召集前端、后端、产品负责人
   - 审查所有设计文档
   - 确认开放决策（存储后端选择、图片规格 KPI）

2. **⏳ 创建开发任务票**
   - 在项目管理工具（Jira/Linear）中创建 Phase 7 任务
   - 关联到 `plan.md` 中的任务 ID（T-PARSE-1.1 到 T-PARSE-5.4）
   - 分配到前端和后端工程师

3. **⏳ 环境准备**
   - 确保开发环境有 Claude 4.5 Sonnet API 访问
   - 决定图片存储后端（Supabase Storage vs Google Drive）
   - 准备测试用 Google Docs（涵盖各种结构）

### 短期行动（下 1-2 周）

4. **⏳ Week 16 实施**
   - 数据库 Schema 设计最终确认
   - 创建 Alembic 迁移脚本
   - 在开发环境测试迁移

5. **⏳ 原型开发**
   - 构建 ArticleParserService 最小可行原型
   - 测试 Claude 4.5 Sonnet 的解析准确性
   - 验证 PIL 图片规格提取

### 中期行动（Week 17-21）

6. **⏳ 完整实施**
   - 按照 `plan.md` Phase 7 执行所有任务
   - 每周进度检查和风险评估
   - 持续集成测试

7. **⏳ 测试和验证**
   - 单元测试（目标覆盖率 ≥85%）
   - 集成测试
   - E2E 测试（Playwright）
   - 解析准确性验证（20+ 测试文档）

---

## 📊 工作量估算

| 阶段 | 工时 | 资源需求 |
|------|------|----------|
| Database Schema | 16h | 1 后端工程师 |
| Backend Parsing Engine | 40h | 1 后端工程师 |
| API & Integration | 12h | 1 后端工程师 |
| Frontend Step 1 UI | 48h | 1 前端工程师 |
| Integration & Testing | 24h | 1 前端 + 1 后端 |
| **总计** | **140h** | **~6 周（并行开发）** |

---

## 🔑 关键决策点

### 需要立即决策

| 决策 | 选项 | 建议 | 状态 |
|------|------|------|------|
| **图片存储后端** | Google Drive vs Supabase Storage | Supabase Storage（更快、更便宜） | ⏳ 待定 |
| **段落位置追踪** | DOM 节点 ID vs 顺序索引 | 顺序索引（更简单） | ⏳ 待定 |
| **历史文章回填** | 自动解析 vs 手动标记 | 手动标记（"legacy-unparsed"） | ⏳ 待定 |
| **图片发布管道** | 立即预处理 vs 延迟预处理 | 延迟（独立 epic） | ✅ 已决定 |

### 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|-------|------|----------|
| AI 解析准确率 <85% | 中 | 高 | 广泛测试套件；Fallback 启发式 |
| 图片下载失败（403, timeout） | 中 | 中 | 重试逻辑；保存部分结果；手动上传选项 |
| 大图片超出存储限制 | 低 | 中 | 压缩；最大文件大小限制（10MB） |
| 解析延迟 >30 秒 | 中 | 中 | 异步处理；进度指示器；缓存 |
| 数据库迁移在生产环境失败 | 低 | 关键 | 在暂存环境测试；回滚计划；迁移前备份 |

---

## 📖 参考文档清单

### 核心设计文档
1. `docs/article_parsing_requirements.md` - 原始需求文档
2. `docs/ARTICLE_PARSING_TECHNICAL_ANALYSIS.md` - 详细技术分析
3. `specs/001-cms-automation/requirements.md` - 需求检查清单（FR-010a ~ FR-010n）

### SpecKit 文档
4. `specs/001-cms-automation/spec.md` - 功能规格（User Story 7, FR-088 ~ FR-105）
5. `specs/001-cms-automation/plan.md` - 实施计划（Phase 7）
6. `specs/001-cms-automation/data-model.md` - 数据模型规范（Version 4.0）

### 待创建文档
7. `specs/001-cms-automation/tasks.md` - 具体开发任务（需要创建/更新）
8. 测试计划文档（单元测试、集成测试、E2E 测试）
9. API 文档（Swagger/OpenAPI 规范）

---

## ✅ 文档完成状态

| 文档 | 状态 | 完成度 | 备注 |
|------|------|--------|------|
| Technical Analysis | ✅ 完成 | 100% | 完整的技术分解和实施计划 |
| spec.md | ✅ 完成 | 100% | User Story 7, FR-088~FR-105, Success Criteria |
| plan.md | ✅ 完成 | 100% | Phase 7 with week-by-week breakdown |
| data-model.md | ✅ 完成 | 100% | Schema updates, new tables, migrations |
| requirements.md | ✅ 已有 | 100% | FR-010a~FR-010n 已定义 |
| tasks.md | ⏳ 待创建 | 0% | 需要从 plan.md 提取任务 |
| 测试文档 | ⏳ 待创建 | 0% | 需要创建测试计划和用例 |

---

## 💡 成功标准总结

### 技术标准
- ✅ 解析准确率 ≥90%（标题、作者、图片、Meta）
- ✅ 解析延迟 ≤20 秒（1500 字、5 图）
- ✅ 图片元数据完整率 100%（width, height, size, MIME）
- ✅ 测试覆盖率 ≥85% (backend), ≥80% (frontend)

### 用户体验标准
- ✅ 审核员可在 <2 分钟内完成 Step 1 解析确认
- ✅ Step 2 阻断逻辑 100% 有效（未确认无法访问）
- ✅ 所有解析字段在 Step 1 UI 可编辑，即时保存

### 运维标准
- ✅ 数据库迁移完成，零数据丢失
- ✅ 所有边缘案例优雅处理（缺失字段、格式错误的 HTML、下载失败）

---

**文档所有者**: CMS Automation Team
**下次审查**: Phase 7 Week 16 结束后
**联系人**: tech-lead@example.com

---

**🎉 设计阶段完成！准备进入实施阶段。**
