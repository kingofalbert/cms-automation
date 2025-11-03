# 部署检查清单 ✅

**项目**: CMS Automation
**版本**: 1.0
**日期**: 2025-11-03

---

## 📋 目录

1. [开发环境初次部署](#开发环境初次部署)
2. [生产环境初次部署](#生产环境初次部署)
3. [常规更新部署](#常规更新部署)
4. [紧急回滚步骤](#紧急回滚步骤)

---

## 开发环境初次部署

### 1. GCP 项目设置

- [ ] 创建 GCP 项目 `cms-automation-dev`
- [ ] 启用计费账户
- [ ] 设置项目配额（防止意外超支）

### 2. 启用必要的 Google Cloud API

```bash
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com \
    --project cms-automation-dev
```

- [ ] Cloud Run API
- [ ] Container Registry API
- [ ] Secret Manager API
- [ ] Compute Engine API (for CDN)

### 3. Supabase 开发项目设置

- [ ] 创建 Supabase 项目 `cms-automation-dev`
- [ ] 选择地区（推荐: 离主要用户最近的地区）
- [ ] 记录连接信息：
  - [ ] Database URL
  - [ ] Supabase URL
  - [ ] Anon Key
  - [ ] Service Key
- [ ] 运行数据库迁移

### 4. Redis 配置（开发环境）

**选项 A: 本地 Redis**（推荐用于本地开发）
```bash
brew install redis  # macOS
brew services start redis
```
- [ ] 验证连接: `redis-cli ping`

**选项 B: GCP Memorystore**（云端开发环境）
- [ ] 创建 Memorystore 实例（Basic tier, 1GB）
- [ ] 记录 Redis URL

### 5. 创建 GCP Secrets（开发环境）

```bash
# 创建所有必要的 secrets
echo -n "your-anthropic-api-key" | gcloud secrets create cms-automation-dev-ANTHROPIC_API_KEY --data-file=- --project cms-automation-dev

echo -n "postgresql+asyncpg://..." | gcloud secrets create cms-automation-dev-DATABASE_URL --data-file=- --project cms-automation-dev

echo -n "redis://..." | gcloud secrets create cms-automation-dev-REDIS_URL --data-file=- --project cms-automation-dev

echo -n "https://admin.epochtimes.com" | gcloud secrets create cms-automation-dev-CMS_BASE_URL --data-file=- --project cms-automation-dev

echo -n "dev.user" | gcloud secrets create cms-automation-dev-CMS_USERNAME --data-file=- --project cms-automation-dev

echo -n "password" | gcloud secrets create cms-automation-dev-CMS_APPLICATION_PASSWORD --data-file=- --project cms-automation-dev

echo -n "djy" | gcloud secrets create cms-automation-dev-CMS_HTTP_AUTH_USERNAME --data-file=- --project cms-automation-dev

echo -n "djy2013" | gcloud secrets create cms-automation-dev-CMS_HTTP_AUTH_PASSWORD --data-file=- --project cms-automation-dev
```

- [ ] 创建所有 secrets
- [ ] 验证 secrets 存在: `gcloud secrets list --project cms-automation-dev`

### 6. 配置 Service Account 权限

```bash
PROJECT_ID="cms-automation-dev"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

- [ ] 授予 Cloud Run service account Secret Manager 访问权限

### 7. 部署后端

```bash
cd /Users/albertking/ES/cms_automation/backend
./scripts/deployment/deploy-dev.sh
```

- [ ] 执行部署脚本
- [ ] 记录后端 URL
- [ ] 测试健康检查: `curl https://your-backend-url/health`

### 8. 部署前端

```bash
cd /Users/albertking/ES/cms_automation/frontend
./scripts/deploy-to-gcp.sh \
    --project-id cms-automation-dev \
    --bucket-name cms-automation-frontend-dev \
    --backend-url https://your-backend-url
```

- [ ] 执行前端部署
- [ ] 记录前端 URL
- [ ] 测试前端访问

### 9. 配置 CORS

```bash
gcloud run services update cms-automation-backend \
    --region us-central1 \
    --set-env-vars "ALLOWED_ORIGINS=https://storage.googleapis.com" \
    --project cms-automation-dev
```

- [ ] 更新 CORS 配置
- [ ] 测试前端调用后端 API

### 10. 验证部署

- [ ] 测试文章生成功能
- [ ] 测试 WordPress 发布
- [ ] 检查日志是否有错误
- [ ] 验证 Secrets 正确加载

---

## 生产环境初次部署

### 1. GCP 项目设置（生产账户）

⚠️ **重要**: 使用独立的 GCP 账户

- [ ] 使用生产 Google 账户登录
- [ ] 创建 GCP 项目 `cms-automation-prod`
- [ ] 启用计费账户（生产账户）
- [ ] 设置预算告警（例如: $300/月）
- [ ] 配置项目标签：
  - Environment: production
  - ManagedBy: ops-team

### 2. 启用必要的 Google Cloud API

```bash
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com \
    cloudarmor.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    --project cms-automation-prod
```

- [ ] Cloud Run API
- [ ] Container Registry API
- [ ] Secret Manager API
- [ ] Compute Engine API
- [ ] Cloud Armor API（DDoS 防护）
- [ ] Cloud Monitoring
- [ ] Cloud Logging

### 3. Supabase 生产项目设置

- [ ] 创建 Supabase 项目 `cms-automation-prod`
- [ ] 选择 **Pro tier** ($25/月)
- [ ] 启用 Point-in-Time Recovery（数据恢复）
- [ ] 配置自动备份（每日）
- [ ] 记录连接信息（使用 Secret Manager）
- [ ] 配置 Connection Pooling
- [ ] 运行生产数据库迁移

### 4. Redis 配置（生产环境）

**GCP Memorystore（高可用）**

```bash
gcloud redis instances create cms-automation-prod-redis \
    --size=5 \
    --region=us-east1 \
    --redis-version=redis_7_0 \
    --tier=standard-ha \
    --project=cms-automation-prod
```

- [ ] 创建 Memorystore 实例（Standard HA, 5GB）
- [ ] 启用持久化
- [ ] 配置自动故障转移
- [ ] 记录 Redis URL

### 5. 创建 GCP Secrets（生产环境）

⚠️ **注意**: 使用生产环境的真实凭证

```bash
# 使用不同的 API Key（生产专用）
echo -n "sk-ant-api03-PRODUCTION-KEY" | gcloud secrets create cms-automation-prod-ANTHROPIC_API_KEY --data-file=- --project cms-automation-prod

# 使用生产 Supabase 数据库
echo -n "postgresql+asyncpg://...prod..." | gcloud secrets create cms-automation-prod-DATABASE_URL --data-file=- --project cms-automation-prod

# 使用生产 Redis
echo -n "redis://10.x.x.x:6379/0" | gcloud secrets create cms-automation-prod-REDIS_URL --data-file=- --project cms-automation-prod

# 使用生产 WordPress
echo -n "https://admin.epochtimes.com" | gcloud secrets create cms-automation-prod-CMS_BASE_URL --data-file=- --project cms-automation-prod

echo -n "prod.user" | gcloud secrets create cms-automation-prod-CMS_USERNAME --data-file=- --project cms-automation-prod

echo -n "secure-password" | gcloud secrets create cms-automation-prod-CMS_APPLICATION_PASSWORD --data-file=- --project cms-automation-prod

# 生产 HTTP Auth
echo -n "djy" | gcloud secrets create cms-automation-prod-CMS_HTTP_AUTH_USERNAME --data-file=- --project cms-automation-prod
echo -n "djy2013" | gcloud secrets create cms-automation-prod-CMS_HTTP_AUTH_PASSWORD --data-file=- --project cms-automation-prod
```

- [ ] 创建所有 secrets
- [ ] 启用 Secret rotation（定期轮换）
- [ ] 配置 Secret 版本管理

### 6. 配置 Cloud Armor（DDoS 防护）

```bash
gcloud compute security-policies create cms-automation-policy \
    --description="Security policy for CMS Automation" \
    --project=cms-automation-prod

gcloud compute security-policies rules create 1000 \
    --security-policy=cms-automation-policy \
    --expression="true" \
    --action=rate-based-ban \
    --rate-limit-threshold-count=100 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600 \
    --project=cms-automation-prod
```

- [ ] 创建安全策略
- [ ] 配置速率限制
- [ ] 测试防护规则

### 7. 配置监控和告警

```bash
# 创建告警策略
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="CMS Backend High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --project=cms-automation-prod
```

- [ ] 配置 Cloud Monitoring
- [ ] 设置错误率告警（> 5%）
- [ ] 设置延迟告警（> 5 秒）
- [ ] 设置 CPU 使用率告警（> 80%）
- [ ] 设置内存使用率告警（> 80%）
- [ ] 配置 Uptime Checks
- [ ] 设置通知渠道（Email、Slack）

### 8. 部署后端（生产）

⚠️ **重要**: 仔细验证所有配置

```bash
cd /Users/albertking/ES/cms_automation/backend
export GCP_PROJECT_ID_PROD="cms-automation-prod"
export GCP_REGION_PROD="us-east1"
./scripts/deployment/deploy-prod.sh prod-v1.0.0
```

- [ ] 确认部署到正确的项目
- [ ] 记录部署版本号
- [ ] 记录后端 URL
- [ ] 测试健康检查
- [ ] 检查所有环境变量正确加载

### 9. 部署前端（生产）

```bash
cd /Users/albertking/ES/cms_automation/frontend
./scripts/deploy-to-gcp.sh \
    --project-id cms-automation-prod \
    --bucket-name cms-automation-frontend-prod \
    --backend-url https://your-production-backend-url
```

- [ ] 执行前端部署
- [ ] 配置 Cloud CDN
- [ ] 记录前端 URL
- [ ] 测试前端访问
- [ ] 验证资源缓存策略

### 10. 配置自定义域名（可选但推荐）

**后端域名**:
```bash
gcloud run domain-mappings create \
    --service cms-automation-backend \
    --domain api.your-domain.com \
    --region us-east1 \
    --project=cms-automation-prod
```

**前端域名**:
- [ ] 创建 Load Balancer
- [ ] 配置 SSL 证书
- [ ] 更新 DNS 记录

### 11. 生产验证测试

- [ ] 功能测试：
  - [ ] 文章生成
  - [ ] WordPress 发布
  - [ ] 分类管理
  - [ ] 用户认证
- [ ] 性能测试：
  - [ ] 负载测试（100 并发请求）
  - [ ] 响应时间 < 5 秒
  - [ ] 错误率 < 1%
- [ ] 安全测试：
  - [ ] HTTPS 强制
  - [ ] CORS 正确配置
  - [ ] Secrets 不暴露

### 12. 监控设置

- [ ] 查看 Cloud Logging
- [ ] 查看 Cloud Monitoring Dashboard
- [ ] 测试告警触发
- [ ] 监控第一个 24 小时

---

## 常规更新部署

### 开发环境更新

```bash
cd /Users/albertking/ES/cms_automation/backend
./scripts/deployment/deploy-dev.sh
```

- [ ] 运行测试
- [ ] 执行部署
- [ ] 验证功能
- [ ] 检查日志

### 生产环境更新

⚠️ **关键步骤**:

1. **在开发环境测试**
   - [ ] 完全测试新功能
   - [ ] 运行自动化测试
   - [ ] 性能测试

2. **创建 Git Tag**
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

3. **备份检查**
   - [ ] 验证数据库备份
   - [ ] 验证 Secret 备份

4. **执行部署**
   ```bash
   cd /Users/albertking/ES/cms_automation/backend
   ./scripts/deployment/deploy-prod.sh v1.0.1
   ```

5. **后部署验证**
   - [ ] 健康检查通过
   - [ ] 关键功能测试
   - [ ] 监控 30 分钟
   - [ ] 检查错误日志

---

## 紧急回滚步骤

### 快速回滚（5 分钟内）

```bash
# 1. 找到上一个工作版本
gcloud run revisions list \
    --service cms-automation-backend \
    --region us-east1 \
    --project cms-automation-prod

# 2. 回滚到指定版本
gcloud run services update-traffic cms-automation-backend \
    --to-revisions=PREVIOUS_REVISION=100 \
    --region us-east1 \
    --project cms-automation-prod
```

- [ ] 执行回滚
- [ ] 验证服务恢复
- [ ] 通知团队
- [ ] 分析问题根因

### 完整回滚（需要时间）

如果快速回滚不够：

```bash
# 重新部署上一个稳定版本
./scripts/deployment/deploy-prod.sh v1.0.0
```

---

## 📞 紧急联系信息

**技术负责人**: [填写]
**运维团队**: [填写]
**GCP 支持**: https://cloud.google.com/support

---

## 📝 部署日志模板

```markdown
## 部署日志

**日期**: 2025-11-03
**环境**: Production
**版本**: v1.0.1
**部署人**: [姓名]

### 变更内容
- 功能 A
- Bug 修复 B

### 部署步骤
- [x] 备份验证
- [x] 部署执行
- [x] 健康检查

### 验证结果
- ✅ 所有测试通过
- ✅ 性能正常
- ✅ 无错误日志

### 问题记录
- 无

### 回滚计划
- 如有问题，立即回滚到 v1.0.0
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-03
**维护者**: CMS Automation Team
