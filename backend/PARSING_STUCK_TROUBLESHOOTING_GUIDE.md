# 解析卡住问题 - 详细故障排除指南

**问题**: 2 个 Worklist 文件卡在 "parsing" 状态
**优先级**: 🔴 高
**预计解决时间**: 15-30 分钟

---

## 🎯 问题根源分析

### 为什么数据库架构正确但文件还是卡住?

虽然数据库现在支持 `parsing` 状态,但以下几个原因可能导致文件仍然卡住:

1. **后端服务运行的是旧代码**
   - Cloud Run 可能还在运行部署前的容器版本
   - 需要强制重新部署或重启

2. **Worker 进程未运行或崩溃**
   - Celery worker 可能没有启动
   - Worker 可能在处理这些文件时崩溃了

3. **文件特定的错误**
   - Item #13 (5.1 MB) 可能因文件太大而超时
   - 解析逻辑可能在这些特定文件上失败

4. **状态机卡住**
   - 文件的状态已经是 `parsing`,但没有 worker 在处理它
   - 需要重置状态以触发重新处理

---

## 📋 解决方案 (按优先级顺序)

---

## 方案 1: 检查应用日志 (5 分钟)

### 目的
确定问题的具体原因 - 是代码错误、超时还是 worker 未运行

### 步骤

#### 1.1 查看最近的错误日志

```bash
gcloud logging read \
  "resource.type=cloud_run_revision \
   AND resource.labels.service_name=cms-automation-backend \
   AND severity>=ERROR \
   AND timestamp>=\"2025-11-23T00:00:00Z\"" \
  --limit 100 \
  --format json \
  --project=cmsupload-476323 > error_logs.json
```

#### 1.2 搜索解析相关的日志

```bash
gcloud logging read \
  "resource.type=cloud_run_revision \
   AND resource.labels.service_name=cms-automation-backend \
   AND (textPayload=~'parsing' OR textPayload=~'ArticleParser' OR textPayload=~'worklist') \
   AND timestamp>=\"2025-11-23T00:00:00Z\"" \
  --limit 100 \
  --format json \
  --project=cmsupload-476323 > parsing_logs.json
```

#### 1.3 查找特定文件的日志

```bash
gcloud logging read \
  "resource.type=cloud_run_revision \
   AND resource.labels.service_name=cms-automation-backend \
   AND (textPayload=~'902386' OR textPayload=~'收藏10種') \
   AND timestamp>=\"2025-11-18T00:00:00Z\"" \
  --limit 50 \
  --format json \
  --project=cmsupload-476323
```

### 预期发现

**如果看到这些错误**: 说明问题类型

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'bs4'` | 依赖缺失 | 重新部署带依赖的镜像 |
| `psycopg2.DataError: invalid input value for enum` | 旧代码运行中 | 重启服务 |
| `Timeout` 或 `504` | 文件太大 | 调整超时设置 |
| `AttributeError: 'NoneType' object has no attribute 'raw_html'` | 数据问题 | 检查数据完整性 |
| 没有任何日志 | Worker 未运行 | 启动 worker |

### 示例分析

```json
{
  "textPayload": "ERROR: Failed to parse item 13: Timeout after 300s",
  "timestamp": "2025-11-23T22:50:30.204Z"
}
```

→ **结论**: Item #13 因为文件太大(5.1 MB)导致超时

---

## 方案 2: 重启 Cloud Run 服务 (5 分钟) ⭐ **推荐优先执行**

### 目的
确保运行的是包含最新代码和依赖的容器

### 为什么需要重启?

1. **代码更新未生效**: 虽然新镜像已部署,但旧实例可能仍在运行
2. **Worker 进程未启动**: 重启会重新启动所有后台 worker
3. **状态清理**: 清除任何内存中的卡住状态

### 步骤

#### 2.1 检查当前运行的版本

```bash
gcloud run services describe cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --format="value(status.latestCreatedRevisionName)"
```

#### 2.2 查看当前活跃的实例

```bash
gcloud run services describe cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --format="value(status.traffic)"
```

#### 2.3 强制重新部署 (方法 A - 推荐)

```bash
# 获取当前镜像
IMAGE=$(gcloud run services describe cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --format="value(spec.template.spec.containers[0].image)")

# 强制重新部署相同镜像 (会创建新修订版)
gcloud run services update cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --image=$IMAGE \
  --min-instances=1 \
  --max-instances=3
```

#### 2.4 等待部署完成

```bash
# 监控部署状态
gcloud run services describe cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --format="value(status.conditions)"
```

预期输出:
```
type=Ready status=True
```

#### 2.5 触发所有流量到新版本

```bash
# 确保 100% 流量到最新版本
gcloud run services update-traffic cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --to-latest
```

### 验证重启成功

```bash
# 检查新版本是否接收流量
gcloud run services describe cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --format="table(status.latestCreatedRevisionName, status.traffic)"
```

预期: 最新版本显示 100% 流量

---

## 方案 3: 检查 Worker 状态 (3 分钟)

### 目的
确认后台处理 worker (Celery) 正在运行

### 步骤

#### 3.1 检查容器内的进程

```bash
# 方法 1: 通过日志查看
gcloud logging read \
  "resource.type=cloud_run_revision \
   AND resource.labels.service_name=cms-automation-backend \
   AND (textPayload=~'celery' OR textPayload=~'worker')" \
  --limit 20 \
  --project=cmsupload-476323
```

#### 3.2 检查 entrypoint.sh 配置

查看 `backend/entrypoint.sh`:

```bash
cat backend/entrypoint.sh
```

预期看到 Celery worker 启动命令:
```bash
celery -A src.celery_app worker --loglevel=info &
```

#### 3.3 验证 Redis 连接 (Worker 依赖)

```bash
# 检查 Redis 相关的日志
gcloud logging read \
  "resource.type=cloud_run_revision \
   AND resource.labels.service_name=cms-automation-backend \
   AND textPayload=~'redis'" \
  --limit 20 \
  --project=cmsupload-476323
```

### 常见问题

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| 没有 celery 相关日志 | Worker 未启动 | 检查 entrypoint.sh |
| `redis.exceptions.ConnectionError` | Redis 未配置 | 检查 REDIS_URL 环境变量 |
| Worker started but no tasks | 任务未排队 | 检查任务调度逻辑 |

---

## 方案 4: 重置卡住的文件 (2 分钟) ⭐ **最直接的解决方案**

### 目的
将卡住的文件重置回 `pending` 状态,触发重新处理

### 步骤

#### 4.1 使用 Supabase 仪表板 (推荐)

1. **打开 Supabase**
   - 访问: https://supabase.com/dashboard/project/twsbhjmlmspjwfystpti
   - 点击左侧 "SQL Editor"

2. **执行重置查询**

```sql
-- 先查看当前状态
SELECT id, title, status, updated_at
FROM worklist_items
WHERE id IN (13, 6);

-- 重置为 pending
BEGIN;

UPDATE worklist_items
SET
    status = 'pending',
    updated_at = NOW()
WHERE id IN (13, 6);

COMMIT;

-- 验证重置成功
SELECT id, title, status, updated_at
FROM worklist_items
WHERE id IN (13, 6);
```

#### 4.2 使用 psql 命令行

```bash
PGPASSWORD='Xieping890$' psql \
  -h aws-1-us-east-1.pooler.supabase.com \
  -p 6543 \
  -U postgres.twsbhjmlmspjwfystpti \
  -d postgres \
  -c "UPDATE worklist_items SET status = 'pending', updated_at = NOW() WHERE id IN (13, 6);"
```

#### 4.3 验证重置

```bash
PGPASSWORD='Xieping890$' psql \
  -h aws-1-us-east-1.pooler.supabase.com \
  -p 6543 \
  -U postgres.twsbhjmlmspjwfystpti \
  -d postgres \
  -c "SELECT id, title, status, updated_at FROM worklist_items WHERE id IN (13, 6);"
```

预期输出:
```
 id |          title           | status  |          updated_at
----+--------------------------+---------+-------------------------------
 13 | 902386                   | pending | 2025-11-23 23:15:00.000000+00
  6 | 收藏10种「天然補血食物」 | pending | 2025-11-23 23:15:00.000000+00
```

---

## 方案 5: 监控处理进度 (持续监控)

### 目的
确保文件重新处理后能正常进行

### 步骤

#### 5.1 设置监控查询

```bash
# 创建监控脚本
cat > monitor_parsing.sh << 'EOF'
#!/bin/bash

echo "=== Worklist Items Status Monitor ==="
echo "Monitoring items 13 and 6..."
echo ""

while true; do
    clear
    echo "Last updated: $(date)"
    echo ""

    PGPASSWORD='Xieping890$' psql \
      -h aws-1-us-east-1.pooler.supabase.com \
      -p 6543 \
      -U postgres.twsbhjmlmspjwfystpti \
      -d postgres \
      -c "
        SELECT
            id,
            title,
            status,
            updated_at,
            EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as minutes_ago
        FROM worklist_items
        WHERE id IN (13, 6)
        ORDER BY id;
      "

    echo ""
    echo "Press Ctrl+C to stop monitoring"
    sleep 30
done
EOF

chmod +x monitor_parsing.sh
./monitor_parsing.sh
```

#### 5.2 预期的状态转换

**正常进度** (每个阶段约 1-5 分钟):

```
pending → parsing → parsing_review → proofreading → ready_to_publish
   ↓          ↓            ↓                ↓              ↓
  1分钟     2-3分钟      等待审核         1-2分钟        等待发布
```

#### 5.3 检查应用日志 (并行监控)

在另一个终端窗口:

```bash
# 实时跟踪日志
gcloud logging tail \
  "resource.type=cloud_run_revision \
   AND resource.labels.service_name=cms-automation-backend" \
  --project=cmsupload-476323
```

### 成功标志

✅ **处理成功**:
- 状态从 `pending` 变为 `parsing`
- 几分钟后变为 `parsing_review`
- 没有错误日志
- `updated_at` 持续更新

❌ **仍然有问题**:
- 状态停留在 `pending` 超过 5 分钟
- 状态又卡在 `parsing`
- 错误日志持续出现

---

## 方案 6: 处理大文件特殊问题 (如果 Item #13 持续失败)

### 背景
Item #13 是 5.1 MB,可能因为文件太大而超时

### 解决方案 A: 增加超时限制

#### 6.1 更新 Cloud Run 超时设置

```bash
gcloud run services update cms-automation-backend \
  --region=us-east1 \
  --project=cmsupload-476323 \
  --timeout=900 \
  --memory=2Gi \
  --cpu=2
```

参数说明:
- `--timeout=900`: 15 分钟超时 (默认 5 分钟)
- `--memory=2Gi`: 2GB 内存 (处理大文件)
- `--cpu=2`: 2 个 CPU (加快处理)

#### 6.2 检查代码中的超时设置

查看 `src/config/settings.py`:

```python
# 可能需要添加
PARSING_TIMEOUT = 600  # 10 分钟
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
```

### 解决方案 B: 临时跳过大文件

如果需要先让其他文件继续处理:

```sql
-- 将大文件标记为失败,稍后手动处理
UPDATE worklist_items
SET status = 'failed',
    updated_at = NOW()
WHERE id = 13;

-- 只重置小文件
UPDATE worklist_items
SET status = 'pending',
    updated_at = NOW()
WHERE id = 6;
```

---

## 🎯 推荐的执行顺序

### 快速修复 (10-15 分钟)

```
1️⃣ 重启 Cloud Run 服务 (方案 2)
   ↓ 等待 2-3 分钟
2️⃣ 重置卡住的文件 (方案 4)
   ↓ 立即开始
3️⃣ 监控处理进度 (方案 5)
   ↓ 持续 10 分钟
4️⃣ 成功! ✅
```

### 如果快速修复失败 (额外 15-20 分钟)

```
1️⃣ 检查应用日志 (方案 1)
   ↓ 找到具体错误
2️⃣ 检查 Worker 状态 (方案 3)
   ↓ 确认 worker 运行
3️⃣ 处理大文件问题 (方案 6, 如果需要)
   ↓ 调整超时/资源
4️⃣ 重新测试
```

---

## 📝 执行清单

### 准备工作
- [ ] 已安装 gcloud CLI
- [ ] 已登录正确的 GCP 项目 (cmsupload-476323)
- [ ] 有 Supabase 仪表板访问权限
- [ ] 有 Cloud Run 服务管理权限

### 执行步骤
- [ ] **步骤 1**: 重启 Cloud Run 服务
  - [ ] 运行 `gcloud run services update` 命令
  - [ ] 验证新版本接收 100% 流量
  - [ ] 检查服务健康状态

- [ ] **步骤 2**: 重置卡住的文件
  - [ ] 连接到 Supabase SQL Editor
  - [ ] 执行 UPDATE 查询
  - [ ] 验证状态改为 `pending`

- [ ] **步骤 3**: 监控处理
  - [ ] 启动监控脚本
  - [ ] 观察状态转换 (pending → parsing → parsing_review)
  - [ ] 检查没有新的错误日志

- [ ] **步骤 4**: 验证成功
  - [ ] 两个文件都到达 `parsing_review` 或更高状态
  - [ ] 没有错误日志
  - [ ] `updated_at` 时间戳正常更新

### 如果问题持续
- [ ] 检查错误日志 (方案 1)
- [ ] 检查 Worker 状态 (方案 3)
- [ ] 考虑大文件特殊处理 (方案 6)
- [ ] 联系开发团队

---

## 🔍 常见问题 (FAQ)

### Q1: 重启服务会导致停机吗?
**A**: 不会。Cloud Run 执行滚动更新,新实例启动后才会关闭旧实例。通常 0 停机时间。

### Q2: 重置文件会丢失数据吗?
**A**: 不会。只是改变状态标志,所有数据 (raw_html, title 等) 都保留。

### Q3: 如何知道是哪个步骤失败了?
**A**: 查看日志中的错误信息,或观察文件卡在哪个状态。

### Q4: 多久应该看到文件开始处理?
**A**: 重置后 1-2 分钟内应该从 `pending` 变为 `parsing`。

### Q5: 如果两个方案都试过了还是不行怎么办?
**A**:
1. 检查详细错误日志
2. 验证 Celery worker 正在运行
3. 检查 Redis 连接
4. 考虑代码级别的 bug,需要查看具体的解析逻辑

---

## 📞 获取帮助

如果按照本指南操作后问题仍然存在:

1. **收集诊断信息**:
   ```bash
   # 导出最近的日志
   gcloud logging read \
     "resource.labels.service_name=cms-automation-backend \
      AND timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
     --limit 500 \
     --format json > diagnostic_logs.json

   # 导出当前数据库状态
   PGPASSWORD='Xieping890$' psql \
     -h aws-1-us-east-1.pooler.supabase.com \
     -p 6543 \
     -U postgres.twsbhjmlmspjwfystpti \
     -d postgres \
     -c "\copy (SELECT * FROM worklist_items WHERE id IN (13, 6)) TO 'stuck_items.csv' CSV HEADER"
   ```

2. **提供给技术团队**:
   - `diagnostic_logs.json`
   - `stuck_items.csv`
   - 执行过的步骤清单
   - 观察到的错误信息

---

**文档版本**: 1.0
**创建时间**: 2025-11-23
**最后更新**: 2025-11-23
**适用于**: CMS Automation Backend (Cloud Run)
