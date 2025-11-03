# CMS Automation - 多环境配置策略 🌍

**版本**: 1.0
**日期**: 2025-11-03
**状态**: Production-Ready

---

## 🎯 目标

为 CMS Automation 系统建立完善的多环境配置策略，确保：
- **开发环境 (Dev)**: 用于日常开发和测试
- **生产环境 (Prod)**: 用于正式业务运行
- **环境隔离**: 完全独立，互不影响
- **配置管理**: 清晰、安全、易于维护

---

## 📊 当前环境状态分析

### 现有配置

```
当前部署目标: talkmail-production (GCP)
实际用途: 开发环境 ❌ (命名有误)
生产环境: 另一个 GCP 账户 ✅ (待配置)
```

### 问题分析

1. ❌ **命名混淆**: `talkmail-production` 实际是开发环境
2. ❌ **环境未分离**: Supabase、Redis 可能混用
3. ❌ **配置硬编码**: 环境相关配置写死在代码中
4. ❌ **Secret 管理**: 未按环境分离
5. ❌ **部署流程**: 未区分环境

---

## 🏗️ 多环境架构设计

### 环境定义

| 环境 | 用途 | 数据重要性 | 可用性要求 |
|------|------|------------|------------|
| **Development** | 日常开发、功能测试 | 低 | 低 (允许停机) |
| **Production** | 正式业务运行 | 高 | 高 (99.9%+) |

### 可选环境（推荐）

| 环境 | 用途 | 何时需要 |
|------|------|----------|
| **Staging** | 生产前验证 | 团队规模 > 3 人 |
| **Testing** | 自动化测试 | 有 CI/CD 需求 |

---

## 🔧 各层次环境配置

### 1. GCP 项目配置

#### 开发环境

```yaml
项目 ID: cms-automation-dev
计费账户: 开发账户
地区: us-central1
服务:
  - Cloud Run (后端)
  - Cloud Storage (前端)
  - Cloud CDN
  - Secret Manager
  - Container Registry
```

#### 生产环境

```yaml
项目 ID: cms-automation-prod
计费账户: 生产账户（另一个 GCP 账户）
地区: us-east1 (或根据用户位置选择)
服务:
  - Cloud Run (后端) + 更高配置
  - Cloud Storage (前端) + Cloud CDN
  - Cloud Armor (DDoS 防护)
  - Secret Manager + 备份
  - Container Registry
  - Cloud Monitoring + Alerting
```

#### 配置建议

```bash
# 开发环境
GCP_PROJECT_ID_DEV="cms-automation-dev"
GCP_REGION_DEV="us-central1"

# 生产环境
GCP_PROJECT_ID_PROD="cms-automation-prod"
GCP_REGION_PROD="us-east1"
```

---

### 2. Supabase 配置

#### 为什么需要两个 Supabase 项目？

- ✅ **数据隔离**: 开发数据不污染生产
- ✅ **测试安全**: 可以随意测试，不影响生产
- ✅ **版本管理**: 可以测试数据库迁移
- ✅ **成本控制**: 开发环境可以用免费层

#### 配置结构

```yaml
开发环境:
  项目名: cms-automation-dev
  URL: https://xxx-dev.supabase.co
  Database: postgres (开发数据)
  费用: 免费层 ($0/月)

生产环境:
  项目名: cms-automation-prod
  URL: https://xxx-prod.supabase.co
  Database: postgres (生产数据)
  费用: Pro 层 ($25/月) - 支持更高性能
```

#### 环境变量

```bash
# 开发环境 (.env.development)
DATABASE_URL=postgresql+asyncpg://postgres.xxx-dev:password@aws-0-region.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://xxx-dev.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...dev
SUPABASE_SERVICE_KEY=eyJhbGc...dev

# 生产环境 (GCP Secret Manager)
DATABASE_URL=postgresql+asyncpg://postgres.xxx-prod:password@aws-0-region.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://xxx-prod.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...prod
SUPABASE_SERVICE_KEY=eyJhbGc...prod
```

---

### 3. Redis 配置

#### 开发环境

```yaml
类型: 本地 Redis 或 GCP Memorystore (低配)
配置:
  - 容量: 1GB
  - 实例类型: Basic
  - 持久化: 关闭（节省成本）
  - 费用: ~$15/月
```

```bash
# 本地开发
REDIS_URL=redis://localhost:6379/0

# GCP Memorystore (开发)
REDIS_URL=redis://10.0.0.3:6379/0
```

#### 生产环境

```yaml
类型: GCP Memorystore (高可用)
配置:
  - 容量: 5GB
  - 实例类型: Standard (HA)
  - 持久化: 开启
  - 自动故障转移: 是
  - 费用: ~$150/月
```

```bash
# GCP Memorystore (生产)
REDIS_URL=redis://10.1.0.3:6379/0
```

---

### 4. Secret Manager 配置

#### 命名规范

```
格式: {项目}-{环境}-{SECRET_NAME}

开发环境:
  - cms-automation-dev-ANTHROPIC_API_KEY
  - cms-automation-dev-DATABASE_URL
  - cms-automation-dev-REDIS_URL
  - cms-automation-dev-CMS_BASE_URL
  - cms-automation-dev-CMS_USERNAME
  - cms-automation-dev-CMS_APPLICATION_PASSWORD

生产环境:
  - cms-automation-prod-ANTHROPIC_API_KEY
  - cms-automation-prod-DATABASE_URL
  - cms-automation-prod-REDIS_URL
  - cms-automation-prod-CMS_BASE_URL
  - cms-automation-prod-CMS_USERNAME
  - cms-automation-prod-CMS_APPLICATION_PASSWORD
```

#### 访问权限控制

```yaml
开发环境:
  - 开发者: secretmanager.secretAccessor
  - Cloud Run 服务账号: secretmanager.secretAccessor

生产环境:
  - 仅 Cloud Run 服务账号: secretmanager.secretAccessor
  - 管理员: secretmanager.admin (仅紧急情况)
```

---

### 5. WordPress CMS 配置

#### 选项 A: 使用相同的生产 WordPress

```yaml
开发环境:
  CMS_BASE_URL: https://admin.epochtimes.com
  CMS_USERNAME: dev-user (创建专用开发账号)

生产环境:
  CMS_BASE_URL: https://admin.epochtimes.com
  CMS_USERNAME: prod-user (生产账号)
```

**优点**:
- ✅ 只需维护一个 WordPress
- ✅ 文章分类可以用于区分测试/生产

**缺点**:
- ⚠️ 开发测试可能创建垃圾文章
- ⚠️ 需要手动清理测试数据

#### 选项 B: 使用独立的测试 WordPress

```yaml
开发环境:
  CMS_BASE_URL: https://test.epochtimes.com (或本地 Docker)
  CMS_USERNAME: admin

生产环境:
  CMS_BASE_URL: https://admin.epochtimes.com
  CMS_USERNAME: prod-user
```

**优点**:
- ✅ 完全隔离，无污染风险
- ✅ 可以随意测试

**缺点**:
- ❌ 需要维护两个 WordPress 实例
- ❌ 测试数据不够真实

**推荐**: 选项 A + 使用特定分类标记测试文章

---

## 📁 项目配置文件结构

### 建议的文件结构

```
cms_automation/
├── .env.example               # 环境变量模板
├── .env.development           # 本地开发配置（不提交）
├── .env.production            # 生产环境模板（不提交）
│
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py           # 基础配置
│   │   ├── development.py    # 开发环境配置
│   │   ├── production.py     # 生产环境配置
│   │   └── settings.py       # 配置加载器
│   │
│   └── scripts/
│       └── deployment/
│           ├── deploy-dev.sh      # 开发环境部署
│           └── deploy-prod.sh     # 生产环境部署
│
├── frontend/
│   ├── .env.development
│   ├── .env.production
│   └── scripts/
│       ├── deploy-dev.sh
│       └── deploy-prod.sh
│
└── docs/
    ├── MULTI_ENVIRONMENT_STRATEGY.md  # 本文档
    └── DEPLOYMENT_CHECKLIST.md        # 部署检查清单
```

---

## 🔐 环境变量管理策略

### 本地开发

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database (Supabase Dev)
DATABASE_URL=postgresql+asyncpg://...dev...

# API Keys (测试 Key)
ANTHROPIC_API_KEY=sk-ant-api03-xxx-dev

# CMS (测试账号)
CMS_BASE_URL=https://admin.epochtimes.com
CMS_USERNAME=dev.user

# Redis (本地)
REDIS_URL=redis://localhost:6379/0
```

### GCP 部署（开发环境）

```bash
# 通过 Cloud Run 环境变量设置
ENVIRONMENT=development
GCP_PROJECT_ID=cms-automation-dev

# Secrets 从 Secret Manager 读取
ANTHROPIC_API_KEY: secret://cms-automation-dev-ANTHROPIC_API_KEY
DATABASE_URL: secret://cms-automation-dev-DATABASE_URL
```

### GCP 部署（生产环境）

```bash
# 通过 Cloud Run 环境变量设置
ENVIRONMENT=production
GCP_PROJECT_ID=cms-automation-prod

# Secrets 从 Secret Manager 读取
ANTHROPIC_API_KEY: secret://cms-automation-prod-ANTHROPIC_API_KEY
DATABASE_URL: secret://cms-automation-prod-DATABASE_URL
```

---

## 🚀 部署脚本修改

### 开发环境部署脚本

创建 `backend/scripts/deployment/deploy-dev.sh`:

```bash
#!/bin/bash
set -euo pipefail

# 开发环境配置
PROJECT_ID="cms-automation-dev"
REGION="us-central1"
SERVICE_NAME="cms-automation-backend"
IMAGE_TAG="${1:-dev-$(date +%Y%m%d-%H%M%S)}"

echo "🚀 部署到开发环境..."
echo "Project: $PROJECT_ID"
echo "Image Tag: $IMAGE_TAG"

# 设置 GCP 项目
gcloud config set project "$PROJECT_ID"

# 构建镜像
docker build -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" .

# 推送镜像
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"

# 部署到 Cloud Run
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    --region "$REGION" \
    --platform managed \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --timeout 600 \
    --set-env-vars "ENVIRONMENT=development,GCP_PROJECT_ID=${PROJECT_ID}" \
    --set-secrets="ANTHROPIC_API_KEY=cms-automation-dev-ANTHROPIC_API_KEY:latest,DATABASE_URL=cms-automation-dev-DATABASE_URL:latest,REDIS_URL=cms-automation-dev-REDIS_URL:latest" \
    --allow-unauthenticated

echo "✅ 开发环境部署完成！"
```

### 生产环境部署脚本

创建 `backend/scripts/deployment/deploy-prod.sh`:

```bash
#!/bin/bash
set -euo pipefail

# 生产环境配置
PROJECT_ID="cms-automation-prod"
REGION="us-east1"
SERVICE_NAME="cms-automation-backend"
IMAGE_TAG="${1:-prod-v$(date +%Y%m%d)}"

echo "🚀 部署到生产环境..."
echo "⚠️  警告: 这将部署到生产环境！"
echo "Project: $PROJECT_ID"
echo "Image Tag: $IMAGE_TAG"

# 确认部署
read -p "确认部署到生产环境？(yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ 部署已取消"
    exit 1
fi

# 设置 GCP 项目
gcloud config set project "$PROJECT_ID"

# 构建镜像
docker build -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" .

# 推送镜像
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"

# 部署到 Cloud Run（生产配置）
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    --region "$REGION" \
    --platform managed \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --timeout 600 \
    --set-env-vars "ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID}" \
    --set-secrets="ANTHROPIC_API_KEY=cms-automation-prod-ANTHROPIC_API_KEY:latest,DATABASE_URL=cms-automation-prod-DATABASE_URL:latest,REDIS_URL=cms-automation-prod-REDIS_URL:latest" \
    --allow-unauthenticated

echo "✅ 生产环境部署完成！"
```

---

## 📋 部署检查清单

### 开发环境初次部署

- [ ] 创建 GCP 项目 `cms-automation-dev`
- [ ] 启用必要的 API
- [ ] 创建 Supabase Dev 项目
- [ ] 配置 Redis (本地或 GCP)
- [ ] 创建 GCP Secrets (dev)
- [ ] 运行 `deploy-dev.sh`
- [ ] 测试所有 API 端点
- [ ] 配置 CORS

### 生产环境初次部署

- [ ] 创建 GCP 项目 `cms-automation-prod` (独立账户)
- [ ] 启用必要的 API
- [ ] 创建 Supabase Prod 项目 (Pro tier)
- [ ] 配置 GCP Memorystore (高可用)
- [ ] 创建 GCP Secrets (prod)
- [ ] 配置 Cloud Armor（DDoS 防护）
- [ ] 配置监控告警
- [ ] 运行 `deploy-prod.sh`
- [ ] 进行压力测试
- [ ] 配置自定义域名
- [ ] 配置 SSL 证书
- [ ] 设置备份策略

---

## 💰 成本估算

### 开发环境

```
GCP Cloud Run: $2-5/月 (低流量)
Cloud Storage + CDN: $0.05/月
Supabase: $0/月 (免费层)
Redis: $0/月 (本地) 或 $15/月 (GCP)
Secret Manager: $0.45/月
──────────────────────────
总计: $2.50-$20/月
```

### 生产环境

```
GCP Cloud Run: $30-50/月 (正常流量)
Cloud Storage + CDN: $0.50/月
Cloud Armor: $10/月
Supabase Pro: $25/月
Redis (HA): $150/月
Secret Manager: $0.45/月
Monitoring: $5/月
──────────────────────────
总计: $221-$241/月
```

---

## 🔄 CI/CD 流程（推荐）

### 开发流程

```
1. 开发者提交代码到 feature/* 分支
   ↓
2. 自动运行测试
   ↓
3. 合并到 develop 分支
   ↓
4. 自动部署到开发环境
   ↓
5. 开发环境验证通过
```

### 生产部署流程

```
1. 从 develop 创建 release/* 分支
   ↓
2. 代码审查 (Code Review)
   ↓
3. 合并到 main 分支
   ↓
4. 创建 Git Tag (v1.0.0)
   ↓
5. 手动触发生产部署
   ↓
6. 生产环境验证
   ↓
7. 监控 24 小时
```

---

## 🎯 立即行动建议

### 第一步：重命名当前环境 (立即)

```bash
# 当前的 "talkmail-production" 应该重命名
# 选项 1: 在 GCP 控制台修改项目 ID（需要管理员）
# 选项 2: 创建新项目 "cms-automation-dev"，迁移资源
```

### 第二步：创建生产环境配置 (本周)

1. 在生产 GCP 账户创建 `cms-automation-prod` 项目
2. 创建 Supabase 生产项目
3. 配置生产环境 Secrets
4. 测试生产部署脚本（不上线）

### 第三步：完善配置管理 (本月)

1. 实现配置文件结构
2. 创建部署检查清单
3. 编写环境切换文档
4. 建立监控告警

---

## 📚 相关文档

- [GCP 统一部署指南](./DEPLOYMENT_GUIDE_GCP_UNIFIED.md)
- [安全架构文档](./backend/docs/SECURITY_ARCHITECTURE.md)
- [GCP Secret Manager 设置](./backend/docs/GCP_SECRET_MANAGER_SETUP.md)

---

**文档版本**: 1.0
**最后更新**: 2025-11-03
**维护者**: CMS Automation Team
