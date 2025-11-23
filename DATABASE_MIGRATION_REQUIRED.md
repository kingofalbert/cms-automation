# 生产数据库迁移需求

**日期**: 2025-11-23  
**优先级**: 🔴 高 - 影响核心功能  
**预计时间**: 5-10 分钟  

---

## 🎯 问题描述

生产环境中，Worklist 中的文件一直卡在 **"Parsing"** 状态，无法继续处理。

**根本原因**：
1. ✅ **后端代码已更新** - 新 Docker 镜像已部署（包含 `google`, `bs4` 等依赖）
2. ❌ **数据库表结构过时** - 缺少新代码所需的字段和枚举值

---

## 🔍 技术分析

### 缺少的数据库元素

#### 1. WorklistStatus 枚举值（关键）

**当前生产环境**缺少以下状态值：
```sql
-- 缺少的枚举值
'parsing'           -- 正在解析中
'parsing_review'    -- 解析完成待审核
'proofreading_review'  -- 校对审核
```

**影响**：
```python
# 代码尝试设置状态时会失败
item.mark_status(WorklistStatus.PARSING)  # ❌ 数据库不认识 'parsing'
→ psycopg2.DataError: invalid input value for enum workliststatus: "parsing"
→ Worker 崩溃 → 重启 → 再次崩溃 → 无限循环
```

#### 2. worklist_items.raw_html 字段（关键）

**缺少的列**：
```sql
ALTER TABLE worklist_items ADD COLUMN raw_html TEXT;
```

**影响**：
```python
# 解析服务尝试读取原始 HTML
html_content = item.raw_html  # ❌ 列不存在
→ AttributeError / Column does not exist
→ 解析失败
```

#### 3. SEO 相关字段（次要）

还缺少 SEO Title 相关字段，但不影响解析功能，可延后处理。

---

## 📋 必须执行的迁移

### 优先级 P0（立即执行）

| 迁移 ID | 版本 | 描述 | 是否必须 |
|---------|------|------|---------|
| `20251110_1000` | `20251110_1000` | 添加 `parsing`, `parsing_review` 状态 | 🔴 **必须** |
| `77fd4b324d80` | `20251112_1809` | 添加 `raw_html` 字段到 worklist_items | 🔴 **必须** |

### 优先级 P1（建议执行）

| 迁移 ID | 版本 | 描述 | 是否必须 |
|---------|------|------|---------|
| `a1b2c3d4e5f6` | `20251114_1400` | 添加 SEO Title 字段 | 🟡 建议 |
| `b2c3d4e5f6g7` | `20251114_1401` | 添加 SEO 建议字段 | 🟡 建议 |
| `af50da9ccee0` | `20251118_0947` | 添加优化时间戳字段 | 🟡 建议 |

---

## 🚀 执行步骤

### 前置条件

- 有权限访问生产数据库
- 有权限执行 `alembic` 命令
- **强烈建议**：先备份数据库

### 方式 A: 使用 Alembic（推荐）

```bash
# 1. 进入 backend 目录
cd /path/to/CMS/backend

# 2. 设置数据库连接（替换为实际值）
export DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE"

# 3. 检查当前迁移版本
poetry run alembic current

# 4. 执行必须的迁移（P0）
poetry run alembic upgrade 20251110_1000  # 添加状态枚举
poetry run alembic upgrade 77fd4b324d80   # 添加 raw_html

# 5. (可选) 执行建议的迁移（P1）
poetry run alembic upgrade a1b2c3d4e5f6   # SEO Title
poetry run alembic upgrade b2c3d4e5f6g7   # SEO 建议

# 6. 如果遇到 "column already exists" 错误
poetry run alembic stamp af50da9ccee0    # 标记为已应用
poetry run alembic upgrade head          # 升级到最新

# 7. 验证迁移成功
poetry run alembic current
# 预期输出：b2c3d4e5f6g7 或更高版本
```

### 方式 B: 使用 SQL（备选）

如果无法使用 Alembic，可以直接执行 SQL：

```sql
-- 1. 添加新的枚举值到 workliststatus
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing';
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'parsing_review';
ALTER TYPE workliststatus ADD VALUE IF NOT EXISTS 'proofreading_review';
COMMIT; -- PostgreSQL 需要单独 commit 枚举变更

-- 2. 添加 raw_html 字段
BEGIN;
ALTER TABLE worklist_items ADD COLUMN IF NOT EXISTS raw_html TEXT;
COMMIT;

-- 3. (可选) 添加 SEO 字段
BEGIN;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS seo_title VARCHAR(200);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS seo_title_extracted BOOLEAN DEFAULT FALSE;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS seo_title_source VARCHAR(50);
COMMIT;

-- 4. 更新 alembic_version 表（手动标记迁移已应用）
-- 仅在使用 SQL 方式时需要
UPDATE alembic_version SET version_num = '77fd4b324d80';
```

---

## ✅ 验证步骤

### 1. 验证枚举值

```sql
SELECT unnest(enum_range(NULL::workliststatus))::text as status 
ORDER BY status;
```

**预期结果**应包含：
```
parsing
parsing_review
proofreading_review
```

### 2. 验证表结构

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'worklist_items' 
AND column_name IN ('raw_html', 'status');
```

**预期结果**：
```
column_name | data_type
------------+-----------
raw_html    | text
status      | USER-DEFINED
```

### 3. 功能测试

执行迁移后，在生产环境：

1. **访问 Worklist 页面**
2. **触发一次 Google Drive 同步**（如果有同步按钮）
3. **观察新导入的文件**：
   - ✅ 应该能从 `pending` → `parsing` → `parsing_review`
   - ✅ 不应再卡在 `parsing` 状态

4. **检查日志**（无 ModuleNotFoundError）：
   ```bash
   gcloud logging read \
     "resource.type=cloud_run_revision AND resource.labels.service_name=cms-backend AND severity>=ERROR" \
     --limit 20
   ```

---

## 🔄 回滚方案

如果迁移后发现问题：

```bash
# 回滚到迁移前的版本
cd /path/to/CMS/backend
poetry run alembic downgrade 20251108_1800
```

⚠️ **警告**：回滚可能导致数据丢失，建议先备份！

---

## 📊 预期影响

### 执行时间
- **迁移时间**: 30-60 秒
- **停机时间**: 0（在线执行）
- **锁表时间**: 最短（ADD COLUMN 操作）

### 风险评估
- **风险等级**: 🟡 中低
- **可回滚**: ✅ 是（但可能丢失数据）
- **数据丢失风险**: 🟢 低（只是添加字段）

---

## 📞 联系信息

如果迁移过程中遇到问题：

1. **检查迁移日志**：查看 alembic 输出的错误信息
2. **检查数据库日志**：查看 PostgreSQL 日志
3. **联系技术负责人**

---

## 📝 执行记录

**执行人**: _____________________  
**执行时间**: _____________________  
**迁移版本**: _____________________  
**验证结果**: ☐ 通过  ☐ 失败  
**备注**: _____________________

---

**文档版本**: 1.0  
**创建时间**: 2025-11-23  
**项目**: CMS Automation
