# 生产环境数据库连接故障排查手册

**类型**: 故障排查指南
**适用场景**: Cloud Run + Supabase/PostgreSQL 连接问题
**难度级别**: 中高级
**预计解决时间**: 1-2小时

---

## 📋 目录

1. [故障现象识别](#故障现象识别)
2. [系统化诊断流程](#系统化诊断流程)
3. [常见根因分析](#常见根因分析)
4. [解决方案模板](#解决方案模板)
5. [预防措施](#预防措施)
6. [可复用工具](#可复用工具)

---

## 🔍 故障现象识别

### 典型症状

#### 症状1: API 超时但前端正常
```
✅ 前端加载快 (< 1秒)
❌ API 请求超时 (> 10秒)
❌ 数据库相关接口全部失败
✅ 非数据库接口正常 (/health, / 等)
```

**可能原因**:
- 数据库连接池配置问题
- 连接模式不匹配
- 网络连接问题

#### 症状2: 间歇性连接失败
```
⚠️ 有时成功，有时失败
⚠️ 高负载时更容易出现
⚠️ 新部署后更频繁
```

**可能原因**:
- 连接池耗尽
- Auto-scaling 导致连接数超限
- Session vs Transaction 模式配置错误

#### 症状3: 特定错误消息
```
MaxClientsInSessionMode: max clients reached
could not connect to server: Connection timed out
remaining connection slots are reserved
```

**确定原因**: Supabase Session 模式连接数限制

---

## 🔬 系统化诊断流程

### Phase 1: 快速隔离 (5-10分钟)

#### 1.1 验证前端
```bash
# 测试前端静态资源加载
curl -w "Time: %{time_total}s\n" https://your-frontend.com

# 检查 Network tab
# - 静态资源加载快 ✅
# - API 调用失败/超时 ❌
```

#### 1.2 验证后端服务
```bash
# 测试非数据库端点
curl https://your-backend.com/
curl https://your-backend.com/health

# 快速返回 → 后端服务运行正常 ✅
# 超时 → 整体服务问题 ❌
```

#### 1.3 验证数据库连接
```bash
# 测试数据库相关端点
timeout 15 curl https://your-backend.com/v1/worklist

# 超时 → 数据库连接问题 🎯
# 返回错误 → 查看错误消息
```

**隔离结果判断**:
- 前端✅ + 后端服务✅ + 数据库❌ → **数据库连接问题**
- 全部✅ → 缓存问题，清除后重试
- 全部❌ → 基础设施问题

---

### Phase 2: 创建诊断端点 (15-20分钟)

#### 2.1 添加调试路由

创建 `src/api/routes/debug_routes.py`:

```python
"""诊断端点 - 用于生产环境故障排查"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_session

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.get("/db-test")
async def test_database_connection(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """最简单的数据库连接测试"""
    try:
        result = await session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        return {
            "success": True,
            "message": "Database connection successful",
            "test_result": row[0] if row else None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }

@router.get("/db-pool-status")
async def get_pool_status(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """检查连接池状态"""
    engine = session.get_bind()
    pool = engine.pool

    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }

@router.get("/db-query-test/{table}")
async def test_table_query(
    table: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """测试特定表查询"""
    try:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        return {
            "success": True,
            "table": table,
            "count": count,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
```

#### 2.2 注册路由

在 `src/api/routes/__init__.py`:

```python
from src.api.routes import debug_routes

def register_routes(app: FastAPI) -> None:
    # ... 其他路由 ...
    app.include_router(debug_routes.router, tags=["Debug"])
```

#### 2.3 部署并测试

```bash
# 部署更新
bash scripts/deployment/deploy-prod.sh

# 测试诊断端点
curl -w "\nTime: %{time_total}s\n" \
  https://your-backend.com/debug/db-test

curl https://your-backend.com/debug/db-pool-status
```

---

### Phase 3: 根因分析 (10-15分钟)

#### 3.1 分析错误消息

| 错误消息 | 根本原因 | 解决方案 |
|---------|---------|---------|
| `MaxClientsInSessionMode` | Session模式连接数超限 | 切换到Transaction模式 |
| `Connection timed out` | 网络/防火墙问题 | 检查VPC/防火墙配置 |
| `remaining connection slots` | 数据库连接数达到上限 | 增加数据库连接数或优化连接池 |
| `password authentication failed` | 密码错误或特殊字符 | URL编码密码中的特殊字符 |
| `could not translate host name` | DNS解析失败 | 检查数据库URL拼写 |

#### 3.2 检查数据库健康状态

在 Supabase Dashboard 运行:

```sql
-- 检查当前连接数
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'postgres';

-- 检查最大连接数
SHOW max_connections;

-- 检查是否有锁等待
SELECT pid, usename, application_name, state,
       wait_event_type, wait_event, query,
       now() - query_start AS duration
FROM pg_stat_activity
WHERE wait_event_type = 'Lock'
   OR state = 'idle in transaction'
   OR (state = 'active' AND now() - query_start > interval '10 seconds');

-- 检查连接来源
SELECT application_name, count(*)
FROM pg_stat_activity
GROUP BY application_name;
```

#### 3.3 分析连接池配置

检查 `src/config/database.py`:

```python
# 当前配置
pool_size = 20          # 每个实例的连接数
max_overflow = 10       # 额外允许的连接数
pool_timeout = 30       # 获取连接的超时时间

# 计算总连接数需求
# Cloud Run实例数 × (pool_size + max_overflow)
# 例如: 5个实例 × (20 + 10) = 150个连接
```

**Session模式限制**: 通常 15-20 个连接
**Transaction模式限制**: 通常 1000+ 个连接

---

## 🎯 常见根因分析

### 根因1: Supabase Pooler 模式配置错误 ⭐⭐⭐⭐⭐

**发生频率**: 非常高 (80%)
**严重程度**: 高
**检测方法**: 检查 DATABASE_URL 端口号

#### 问题说明

Supabase 提供两种连接池模式:

| 模式 | 端口 | 最大连接数 | 适用场景 |
|-----|------|-----------|---------|
| **Session** | 5432 | ~15-20 | 单实例应用 |
| **Transaction** | 6543 | ~1000+ | 多实例/Serverless |

#### 错误配置示例

```bash
# ❌ 错误: 使用Session模式 (端口5432)
DATABASE_URL="postgresql+asyncpg://user:pass@xxx.pooler.supabase.com:5432/postgres"

# ✅ 正确: 使用Transaction模式 (端口6543)
DATABASE_URL="postgresql+asyncpg://user:pass@xxx.pooler.supabase.com:6543/postgres"
```

#### 修复脚本

创建 `scripts/fix-supabase-pooler.sh`:

```bash
#!/bin/bash
set -e

echo "🔧 修复 Supabase Pooler 配置"
echo ""

# 获取当前 DATABASE_URL
CURRENT_URL=$(gcloud secrets versions access latest \
  --secret="your-project-DATABASE_URL")

echo "当前配置: $CURRENT_URL"
echo ""

# 替换端口: 5432 → 6543
NEW_URL="${CURRENT_URL/:5432\//:6543\/}"

echo "新配置: $NEW_URL"
echo ""

# 更新 Secret
echo "📝 更新 DATABASE_URL..."
echo -n "$NEW_URL" | gcloud secrets versions add \
  your-project-DATABASE_URL --data-file=-

echo "✅ 修复完成！"
echo ""
echo "🔄 现在重新部署后端:"
echo "   gcloud run services update your-service \\"
echo "     --region=your-region \\"
echo "     --update-secrets='DATABASE_URL=your-project-DATABASE_URL:latest'"
```

#### 验证修复

```bash
# 1. 运行修复脚本
bash scripts/fix-supabase-pooler.sh

# 2. 重新部署
gcloud run services update your-backend \
  --region=us-east1 \
  --update-secrets="DATABASE_URL=your-project-DATABASE_URL:latest"

# 3. 测试连接
curl -w "Time: %{time_total}s\n" \
  https://your-backend.com/debug/db-test
```

**预期结果**:
- 响应时间: < 0.5秒 (之前 > 10秒)
- 成功率: 100% (之前失败或超时)

---

### 根因2: URL中的特殊字符未编码 ⭐⭐⭐

**发生频率**: 中等 (30%)
**严重程度**: 中

#### 问题说明

密码包含特殊字符(`$`, `@`, `:`, `/`, `?`, `#`)时必须URL编码。

#### 示例

```bash
# ❌ 错误: 密码包含 $ 符号
postgresql+asyncpg://user:Password123$@host:5432/db

# ✅ 正确: $ 编码为 %24
postgresql+asyncpg://user:Password123%24@host:5432/db
```

#### 常见特殊字符编码表

| 字符 | URL编码 | 字符 | URL编码 |
|-----|--------|------|--------|
| `$` | `%24` | `@` | `%40` |
| `:` | `%3A` | `/` | `%2F` |
| `?` | `%3F` | `#` | `%23` |
| `%` | `%25` | `&` | `%26` |

#### 修复脚本

```bash
#!/bin/bash
# 自动URL编码DATABASE_URL中的密码

CURRENT_URL=$(gcloud secrets versions access latest --secret="DATABASE_URL")

# 编码所有特殊字符
NEW_URL=$(echo "$CURRENT_URL" | sed 's/\$/\%24/g')
NEW_URL=$(echo "$NEW_URL" | sed 's/@/\%40/g' | sed 's/\%40@/\@/g')  # 保留host前的@

echo -n "$NEW_URL" | gcloud secrets versions add DATABASE_URL --data-file=-
```

---

### 根因3: 连接池配置不当 ⭐⭐

**发生频率**: 低 (10%)
**严重程度**: 中

#### 问题分析

```python
# 不当配置示例
DATABASE_POOL_SIZE = 50        # ❌ 过大
DATABASE_MAX_OVERFLOW = 50     # ❌ 过大
DATABASE_POOL_TIMEOUT = 5      # ❌ 过短

# 推荐配置 (Transaction模式)
DATABASE_POOL_SIZE = 20        # ✅ 适中
DATABASE_MAX_OVERFLOW = 10     # ✅ 适中
DATABASE_POOL_TIMEOUT = 30     # ✅ 足够长
DATABASE_POOL_RECYCLE = 3600   # ✅ 1小时回收
```

#### 计算公式

```
总连接数需求 = Cloud Run实例数 × (pool_size + max_overflow)

例如:
- 最大5个实例
- pool_size = 20
- max_overflow = 10
总计: 5 × 30 = 150个连接

确保: 总连接数 < 数据库最大连接数限制
```

---

## 🛠 解决方案模板

### 快速修复检查清单

```bash
# ✅ 检查清单

## 1. 验证 Supabase Pooler 模式
[ ] DATABASE_URL 使用端口 6543 (Transaction模式)
[ ] 不是端口 5432 (Session模式)

## 2. 验证密码编码
[ ] 密码中的特殊字符已URL编码
[ ] 特别检查: $, @, :, /, ?, # 等

## 3. 验证连接池配置
[ ] pool_size ≤ 20
[ ] max_overflow ≤ 10
[ ] pool_timeout ≥ 30
[ ] pool_pre_ping = True

## 4. 验证Cloud Run配置
[ ] min_instances ≥ 1 (保持warm)
[ ] max_instances 合理 (避免连接数过多)
[ ] memory ≥ 2Gi
[ ] timeout ≥ 300s

## 5. 验证数据库健康
[ ] Supabase Dashboard 无性能警告
[ ] 没有长时间运行的查询
[ ] 没有锁等待

## 6. 验证网络连接
[ ] 可以从Cloud Run ping通数据库主机
[ ] 端口6543可访问
[ ] 没有防火墙阻挡
```

---

## 🔐 预防措施

### 1. 部署前检查

创建 `scripts/pre-deployment-check.sh`:

```bash
#!/bin/bash
set -e

echo "🔍 部署前数据库配置检查"
echo ""

# 检查 DATABASE_URL
DATABASE_URL=$(gcloud secrets versions access latest --secret="DATABASE_URL")

# 检查端口
if [[ $DATABASE_URL == *":5432/"* ]]; then
    echo "❌ 错误: 使用Session模式 (端口5432)"
    echo "   请改用Transaction模式 (端口6543)"
    exit 1
else
    echo "✅ 使用Transaction模式 (端口6543)"
fi

# 检查特殊字符
if [[ $DATABASE_URL == *'$'* ]] && [[ $DATABASE_URL != *'%24'* ]]; then
    echo "⚠️  警告: 密码可能包含未编码的 $ 符号"
fi

echo ""
echo "✅ 所有检查通过！"
```

### 2. 监控告警

在 Google Cloud Monitoring 设置:

```yaml
# 连接超时告警
alert:
  name: "Database Connection Timeout"
  condition: "request_latency > 5s"
  for: "1m"
  notification: "ops-team@company.com"

# 错误率告警
alert:
  name: "High Database Error Rate"
  condition: "error_rate > 5%"
  for: "2m"
  notification: "ops-team@company.com"
```

### 3. 定期健康检查

添加到 CI/CD pipeline:

```bash
# .github/workflows/health-check.yml
- name: Database Health Check
  run: |
    RESPONSE=$(curl -s https://backend.com/debug/db-test)
    if [[ $RESPONSE != *"success\":true"* ]]; then
      echo "❌ Database health check failed"
      exit 1
    fi
```

---

## 📦 可复用工具

### 工具1: 数据库连接诊断脚本

保存为 `scripts/diagnose-db-connection.sh`:

```bash
#!/bin/bash

echo "🔬 数据库连接诊断工具"
echo "===================="
echo ""

BACKEND_URL="${1:-https://your-backend.com}"

# 测试1: 基本连接
echo "测试 1/4: 基本数据库连接..."
RESPONSE=$(curl -s -w "\nTime:%{time_total}s" "$BACKEND_URL/debug/db-test")
echo "$RESPONSE"
echo ""

# 测试2: 连接池状态
echo "测试 2/4: 连接池状态..."
curl -s "$BACKEND_URL/debug/db-pool-status" | python3 -m json.tool
echo ""

# 测试3: 查询性能
echo "测试 3/4: 查询性能测试..."
START=$(date +%s)
curl -s "$BACKEND_URL/v1/worklist" > /dev/null
END=$(date +%s)
echo "Worklist查询耗时: $((END-START))秒"
echo ""

# 测试4: 并发连接
echo "测试 4/4: 并发连接测试 (10个并发请求)..."
for i in {1..10}; do
  curl -s "$BACKEND_URL/debug/db-test" > /dev/null &
done
wait
echo "✅ 并发测试完成"
echo ""

echo "===================="
echo "诊断完成"
```

### 工具2: DATABASE_URL 验证器

保存为 `scripts/validate-database-url.py`:

```python
#!/usr/bin/env python3
"""验证 DATABASE_URL 配置"""

import sys
import re
from urllib.parse import urlparse, parse_qs

def validate_database_url(url: str) -> list[str]:
    """验证DATABASE_URL并返回问题列表"""
    issues = []

    # 解析URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return [f"❌ URL解析失败: {e}"]

    # 检查协议
    if not parsed.scheme.startswith('postgresql'):
        issues.append("⚠️  协议不是postgresql或postgresql+asyncpg")

    # 检查端口
    port = parsed.port or 5432
    if port == 5432:
        issues.append("❌ 使用Session模式 (端口5432)，应改用Transaction模式 (端口6543)")
    elif port == 6543:
        print("✅ 使用Transaction模式 (端口6543)")

    # 检查密码中的特殊字符
    password = parsed.password or ""
    special_chars = ['$', '@', ':', '/', '?', '#', '%']
    unencoded = []

    for char in special_chars:
        if char in password and f'%{ord(char):02X}' not in url:
            unencoded.append(char)

    if unencoded:
        issues.append(f"⚠️  密码可能包含未编码的特殊字符: {', '.join(unencoded)}")

    # 检查主机名
    if 'pooler.supabase.com' not in parsed.hostname:
        issues.append("⚠️  不是Supabase pooler地址")

    return issues

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python validate-database-url.py <DATABASE_URL>")
        sys.exit(1)

    url = sys.argv[1]
    issues = validate_database_url(url)

    if issues:
        print("\n".join(issues))
        sys.exit(1)
    else:
        print("✅ DATABASE_URL配置正确")
        sys.exit(0)
```

### 工具3: 自动化修复工具

保存为 `scripts/auto-fix-db-connection.sh`:

```bash
#!/bin/bash
set -e

PROJECT_ID="${1}"
SECRET_NAME="${2:-DATABASE_URL}"

if [ -z "$PROJECT_ID" ]; then
    echo "用法: $0 <PROJECT_ID> [SECRET_NAME]"
    exit 1
fi

echo "🔧 自动修复数据库连接配置"
echo "项目: $PROJECT_ID"
echo "Secret: $SECRET_NAME"
echo ""

# 1. 获取当前URL
echo "📥 获取当前配置..."
CURRENT_URL=$(gcloud secrets versions access latest \
  --project="$PROJECT_ID" \
  --secret="$SECRET_NAME")

# 2. 备份
echo "💾 备份当前配置..."
echo "$CURRENT_URL" > "/tmp/${SECRET_NAME}.backup.$(date +%Y%m%d_%H%M%S)"

# 3. 修复端口
echo "🔄 修复pooler模式 (5432→6543)..."
FIXED_URL="${CURRENT_URL/:5432\//:6543\/}"

# 4. 修复特殊字符
echo "🔄 编码特殊字符..."
FIXED_URL="${FIXED_URL//\$/\%24}"

# 5. 验证
echo "✅ 验证新配置..."
python3 scripts/validate-database-url.py "$FIXED_URL"

# 6. 更新Secret
echo "📝 更新Secret..."
echo -n "$FIXED_URL" | gcloud secrets versions add \
  --project="$PROJECT_ID" \
  "$SECRET_NAME" --data-file=-

echo ""
echo "✅ 修复完成！"
echo ""
echo "🔄 下一步: 重新部署后端"
echo "   gcloud run services update YOUR_SERVICE \\"
echo "     --project=$PROJECT_ID \\"
echo "     --region=YOUR_REGION \\"
echo "     --update-secrets='DATABASE_URL=${SECRET_NAME}:latest'"
```

---

## 📊 案例研究: 2025-11-07 生产故障

### 故障时间线

| 时间 | 事件 | 操作 |
|------|------|------|
| 00:00 | 用户报告首页加载慢 | - |
| 00:10 | 确认前端正常，API超时 | Playwright测试 |
| 00:30 | 部署debug端点 | 添加诊断路由 |
| 00:35 | 遇到GCR deprecated错误 | - |
| 00:50 | 迁移到Artifact Registry | 创建GAR仓库 |
| 01:10 | Debug端点部署成功 | 测试连接 |
| 01:15 | **发现根因**: MaxClientsInSessionMode | 🎯 |
| 01:20 | 修复: Session→Transaction模式 | 更新DATABASE_URL |
| 01:25 | 重新部署后端 | gcloud run update |
| 01:30 | ✅ 验证修复: 0.3秒响应 | 测试成功 |

### 性能对比

| 指标 | 修复前 | 修复后 | 提升 |
|------|--------|--------|------|
| 数据库连接 | 15.3s 超时 | 0.327s | **47倍** |
| Worklist查询 | 超时 | 0.267s | **∞** |
| 完整API请求 | 超时 | 0.632s | **∞** |

### 关键经验

1. **系统化诊断比猜测更快**
   - 不要直接猜测问题
   - 使用诊断端点隔离问题范围

2. **Debug端点是必需品**
   - 永久保留在生产环境
   - 提供实时诊断能力

3. **文档化所有决策**
   - 创建详细的故障报告
   - 记录解决方案供未来参考

4. **自动化修复流程**
   - 创建可复用的修复脚本
   - 集成到CI/CD pipeline

---

## 🔗 相关资源

### 官方文档
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/tips/general)
- [SQLAlchemy Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)

### 内部文档
- [Database Issue Resolution (本项目)](../backend/DATABASE_ISSUE_RESOLUTION.md)
- [Deployment Guide](./deployment-guide.md)
- [Monitoring Setup](./monitoring-setup.md)

### 工具和脚本
- `scripts/diagnose-db-connection.sh` - 连接诊断工具
- `scripts/validate-database-url.py` - URL验证器
- `scripts/auto-fix-db-connection.sh` - 自动修复工具
- `scripts/fix-supabase-pooler.sh` - Pooler模式修复

---

## 📝 维护记录

| 日期 | 版本 | 变更 | 作者 |
|------|------|------|------|
| 2025-11-07 | 1.0 | 初始版本，基于生产故障经验 | System |

---

## 💡 快速参考卡片

### 5分钟快速诊断

```bash
# 1. 测试前端
curl -w "Time:%{time_total}s\n" https://frontend.com

# 2. 测试后端服务
curl https://backend.com/health

# 3. 测试数据库连接
curl -w "Time:%{time_total}s\n" https://backend.com/debug/db-test

# 4. 检查DATABASE_URL
gcloud secrets versions access latest --secret="DATABASE_URL" | grep -o ':[0-9]*/'
# 应该显示 :6543/ (不是 :5432/)
```

### 常见错误代码对照

| HTTP状态 | 典型错误 | 快速修复 |
|---------|----------|---------|
| 504 Gateway Timeout | 数据库连接超时 | 检查pooler模式 |
| 500 Internal Server Error | MaxClientsInSessionMode | Session→Transaction |
| 502 Bad Gateway | 后端服务崩溃 | 检查日志和内存 |
| 503 Service Unavailable | 实例未就绪 | 增加min_instances |

---

**最后更新**: 2025-11-07
**适用版本**: Cloud Run + Supabase (所有版本)
**维护者**: DevOps Team
