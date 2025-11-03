# CMS Automation - 云端部署完整指南 ☁️

**版本**: 2.0
**日期**: 2025-11-03
**状态**: Production-Ready
**架构**: 完全云端化 (GCP Cloud Run + Vercel)

---

## 📋 目录

1. [部署架构概览](#部署架构概览)
2. [前置要求](#前置要求)
3. [后端部署 (GCP Cloud Run)](#后端部署-gcp-cloud-run)
4. [前端部署 (Vercel)](#前端部署-vercel)
5. [配置与测试](#配置与测试)
6. [监控与维护](#监控与维护)
7. [故障排查](#故障排查)

---

## 部署架构概览

```
用户浏览器
    ↓ HTTPS
React 前端 (Vercel)
    ↓ REST API (HTTPS)
FastAPI 后端 (GCP Cloud Run)
├── Playwright (Headless Chrome) 💰 免费
├── Computer Use (Anthropic API) 💰 $0.20/篇
├── PostgreSQL (Supabase)
├── Redis (GCP Memorystore)
└── Secret Manager (GCP)
    ↓
WordPress CMS (目标网站)
```

### 核心特性

✅ **完全云端化**: 用户只需浏览器即可使用
✅ **自动扩展**: Cloud Run 自动处理负载
✅ **按需付费**: 闲置时不收费
✅ **全球可用**: CDN 加速
✅ **安全**: HTTPS + Secret Manager

---

## 前置要求

### 账号与工具

- [ ] Google Cloud Platform 账号 (有效信用卡)
- [ ] Vercel 账号 (可用 GitHub 登录)
- [ ] gcloud CLI 已安装
- [ ] Docker 已安装
- [ ] Git 已安装

### 安装 gcloud CLI

```bash
# macOS
brew install google-cloud-sdk

# 或下载安装包
# https://cloud.google.com/sdk/docs/install

# 登录
gcloud auth login

# 设置项目
gcloud config set project YOUR_PROJECT_ID
```

### 检查已安装工具

```bash
# 检查 gcloud
gcloud --version

# 检查 Docker
docker --version

# 检查 Git
git --version
```

---

## 后端部署 (GCP Cloud Run)

### 步骤 1: 准备 GCP 项目

#### 1.1 创建 GCP 项目（如果还没有）

```bash
# 创建项目
gcloud projects create YOUR_PROJECT_ID --name="CMS Automation"

# 设置为当前项目
gcloud config set project YOUR_PROJECT_ID

# 启用计费
# 访问: https://console.cloud.google.com/billing
```

#### 1.2 启用必要的 API

```bash
# 启用 Cloud Run API
gcloud services enable run.googleapis.com

# 启用 Container Registry API
gcloud services enable containerregistry.googleapis.com

# 启用 Secret Manager API
gcloud services enable secretmanager.googleapis.com

# 启用 Cloud Build API (可选，用于自动构建)
gcloud services enable cloudbuild.googleapis.com
```

### 步骤 2: 配置 Secret Manager

#### 2.1 创建必要的 secrets

```bash
# Anthropic API Key
echo -n "sk-ant-api03-..." | gcloud secrets create cms-automation-ANTHROPIC_API_KEY \
    --data-file=- \
    --replication-policy="automatic"

# Database URL (Supabase)
echo -n "postgresql://..." | gcloud secrets create cms-automation-DATABASE_URL \
    --data-file=- \
    --replication-policy="automatic"

# Redis URL
echo -n "redis://..." | gcloud secrets create cms-automation-REDIS_URL \
    --data-file=- \
    --replication-policy="automatic"

# CMS Application Password
echo -n "your-wp-app-password" | gcloud secrets create cms-automation-CMS_APPLICATION_PASSWORD \
    --data-file=- \
    --replication-policy="automatic"
```

#### 2.2 创建服务账号并授权

```bash
# 创建服务账号
gcloud iam service-accounts create cms-automation-backend \
    --description="Service account for CMS Automation backend" \
    --display-name="CMS Automation Backend"

# 授予 Secret Manager 访问权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:cms-automation-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 授予 Cloud Run 权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:cms-automation-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### 步骤 3: 构建和部署

#### 3.1 使用部署脚本（推荐）

```bash
# 进入 backend 目录
cd /Users/albertking/ES/cms_automation/backend

# 执行部署脚本
./scripts/deployment/deploy-to-cloud-run.sh \
    --project-id YOUR_PROJECT_ID \
    --region us-central1 \
    --image-tag v1.0.0
```

#### 3.2 手动部署

```bash
# 进入 backend 目录
cd /Users/albertking/ES/cms_automation/backend

# 构建 Docker 镜像
docker build -t gcr.io/YOUR_PROJECT_ID/cms-automation-backend:latest .

# 推送到 Container Registry
gcloud auth configure-docker
docker push gcr.io/YOUR_PROJECT_ID/cms-automation-backend:latest

# 部署到 Cloud Run
gcloud run deploy cms-automation-backend \
    --image gcr.io/YOUR_PROJECT_ID/cms-automation-backend:latest \
    --platform managed \
    --region us-central1 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 600 \
    --min-instances 0 \
    --max-instances 10 \
    --allow-unauthenticated \
    --service-account cms-automation-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,CREDENTIAL_STORAGE_BACKEND=gcp_secret_manager,GCP_PROJECT_ID=YOUR_PROJECT_ID,GCP_SECRET_PREFIX=cms-automation-,PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

### 步骤 4: 验证后端部署

```bash
# 获取服务 URL
SERVICE_URL=$(gcloud run services describe cms-automation-backend \
    --platform managed \
    --region us-central1 \
    --format 'value(status.url)')

echo "Backend URL: $SERVICE_URL"

# 测试 health 端点
curl ${SERVICE_URL}/health

# 应该返回: {"status": "healthy"}
```

---

## 前端部署 (Vercel)

### 步骤 1: 准备 Git 仓库

```bash
# 确保代码已推送到 GitHub
cd /Users/albertking/ES/cms_automation
git add .
git commit -m "feat: Add cloud deployment configuration"
git push origin main
```

### 步骤 2: 连接 Vercel

#### 2.1 访问 Vercel Dashboard

1. 访问 https://vercel.com
2. 使用 GitHub 登录
3. 点击 "Add New" → "Project"

#### 2.2 导入项目

1. 选择你的 GitHub 仓库: `cms_automation`
2. 选择 "Frontend" 目录作为根目录
3. Framework Preset: **Vite**
4. Build Command: `npm run build`
5. Output Directory: `dist`

### 步骤 3: 配置环境变量

在 Vercel 项目设置中添加环境变量：

```
VITE_API_URL=https://cms-automation-backend-YOUR_PROJECT_ID.run.app
VITE_APP_TITLE=CMS Automation
VITE_APP_DESCRIPTION=AI-powered CMS automation system
```

### 步骤 4: 部署

1. 点击 "Deploy" 按钮
2. 等待构建完成（约 2-3 分钟）
3. 获取前端 URL（类似 `https://cms-automation.vercel.app`）

### 步骤 5: 配置自定义域名（可选）

1. 在 Vercel Dashboard 中选择项目
2. Settings → Domains
3. 添加自定义域名
4. 按照指引配置 DNS

---

## 配置与测试

### 更新前端 API URL

#### 方法 1: Vercel 环境变量

```bash
# 使用 Vercel CLI
vercel env add VITE_API_URL production
# 输入: https://YOUR_BACKEND_URL.run.app
```

#### 方法 2: 在 Vercel Dashboard

1. Project Settings → Environment Variables
2. Add New → VITE_API_URL
3. Value: `https://YOUR_BACKEND_URL.run.app`
4. Redeploy 项目

### 更新后端 CORS 设置

```bash
# 更新 Cloud Run 服务，添加前端 URL 到 ALLOWED_ORIGINS
gcloud run services update cms-automation-backend \
    --region us-central1 \
    --set-env-vars "ALLOWED_ORIGINS=https://cms-automation.vercel.app,https://your-custom-domain.com"
```

### 端到端测试

```bash
# 1. 测试后端健康检查
curl https://YOUR_BACKEND_URL.run.app/health

# 2. 测试 API（需要认证）
curl -X POST https://YOUR_BACKEND_URL.run.app/v1/articles/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Test Article", "content": "Test content"}'

# 3. 在浏览器访问前端
open https://cms-automation.vercel.app
```

---

## 监控与维护

### Cloud Run 监控

```bash
# 查看日志
gcloud run logs read cms-automation-backend \
    --region us-central1 \
    --limit 50

# 实时日志
gcloud run logs tail cms-automation-backend \
    --region us-central1

# 查看指标
gcloud run services describe cms-automation-backend \
    --region us-central1 \
    --format="value(status.url,status.conditions)"
```

### 设置告警

```bash
# 创建告警策略 - 高错误率
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="CMS Automation High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=5 \
    --condition-threshold-duration=300s
```

### 成本监控

```bash
# 查看当前月费用
gcloud billing accounts list
gcloud billing projects link YOUR_PROJECT_ID \
    --billing-account=YOUR_BILLING_ACCOUNT

# 设置预算告警
# 访问: https://console.cloud.google.com/billing/budgets
```

### Vercel 监控

1. Vercel Dashboard → Analytics
2. 查看：
   - 请求量
   - 响应时间
   - 错误率
   - 带宽使用

---

## 故障排查

### 后端问题

#### 1. 容器启动失败

```bash
# 查看详细日志
gcloud run logs read cms-automation-backend \
    --region us-central1 \
    --format="table(timestamp,message)" \
    --limit 100

# 常见原因：
# - 环境变量缺失
# - Secret Manager 权限问题
# - 端口配置错误
```

#### 2. Playwright 无法运行

```bash
# 检查 Chromium 是否安装
gcloud run services describe cms-automation-backend \
    --region us-central1 \
    --format="value(spec.template.spec.containers[0].resources)"

# 增加内存（如果需要）
gcloud run services update cms-automation-backend \
    --region us-central1 \
    --memory 2Gi
```

#### 3. Secret Manager 访问失败

```bash
# 检查服务账号权限
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:cms-automation-backend@*"

# 重新授权
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:cms-automation-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 前端问题

#### 1. API 请求失败 (CORS)

**原因**: 后端未配置允许前端域名

**解决**:
```bash
gcloud run services update cms-automation-backend \
    --region us-central1 \
    --set-env-vars "ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app"
```

#### 2. 环境变量未生效

**解决**:
1. Vercel Dashboard → Settings → Environment Variables
2. 确认变量名正确（必须以 `VITE_` 开头）
3. Redeploy 项目

#### 3. 构建失败

```bash
# 本地测试构建
cd frontend
npm install
npm run build

# 查看构建日志
# Vercel Dashboard → Deployments → 点击失败的部署 → Build Logs
```

---

## 成本估算

### 月度成本（发布 100 篇文章）

#### 后端 (GCP Cloud Run)

```
计算费用:
- 100 篇 × 2 分钟 × $0.24/hour (1GB RAM) ≈ $0.80
- 请求费用: 可忽略（免费层）

Playwright: $0
Computer Use API: 30 篇 × $0.20 ≈ $6.00
Secret Manager: $0.45

后端总计: ~$7.25/月
```

#### 前端 (Vercel)

```
免费层包含:
- 100GB 带宽
- 无限次部署
- 自动 SSL

前端总计: $0/月（免费层足够）
```

#### 其他服务

```
Supabase (已有): $0-$25/月（取决于用量）
GCP Memorystore (已有): 包含在现有预算中

总成本: ~$7-32/月
```

---

## 更新与回滚

### 部署新版本

```bash
# 1. 更新代码
git pull origin main

# 2. 构建新镜像
cd backend
docker build -t gcr.io/YOUR_PROJECT_ID/cms-automation-backend:v1.1.0 .

# 3. 推送镜像
docker push gcr.io/YOUR_PROJECT_ID/cms-automation-backend:v1.1.0

# 4. 部署
gcloud run deploy cms-automation-backend \
    --image gcr.io/YOUR_PROJECT_ID/cms-automation-backend:v1.1.0 \
    --region us-central1
```

### 回滚到之前的版本

```bash
# 查看所有版本
gcloud run revisions list --service cms-automation-backend --region us-central1

# 回滚到特定版本
gcloud run services update-traffic cms-automation-backend \
    --region us-central1 \
    --to-revisions REVISION_NAME=100
```

---

## 安全最佳实践

### 1. 凭证管理

✅ 使用 GCP Secret Manager
✅ 不在代码中硬编码凭证
✅ 定期轮换 API 密钥（每 90 天）
✅ 最小权限原则（服务账号）

### 2. 网络安全

✅ 启用 HTTPS（Cloud Run 自动）
✅ 配置 CORS 白名单
✅ 设置速率限制
✅ 使用 Cloud Armor（可选，高级防护）

### 3. 代码安全

✅ 定期更新依赖
✅ 运行安全扫描（`npm audit`, `safety`）
✅ 使用非 root 用户运行容器
✅ 最小化镜像大小

---

## 附录

### A. 有用的命令

```bash
# Cloud Run 服务信息
gcloud run services describe cms-automation-backend --region us-central1

# 列出所有服务
gcloud run services list

# 删除服务
gcloud run services delete cms-automation-backend --region us-central1

# 查看配额
gcloud compute project-info describe --project=YOUR_PROJECT_ID

# 列出所有 secrets
gcloud secrets list
```

### B. 相关文档

- [GCP Cloud Run 文档](https://cloud.google.com/run/docs)
- [Vercel 文档](https://vercel.com/docs)
- [GCP Secret Manager 文档](https://cloud.google.com/secret-manager/docs)
- [Playwright 文档](https://playwright.dev/python/docs/intro)

---

**部署指南版本**: 2.0
**最后更新**: 2025-11-03
**维护者**: CMS Automation Team
