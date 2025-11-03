# 快速开始 - 云端部署 🚀

**适合**: 想要快速部署到生产环境的用户
**时间**: 约 30 分钟
**前提**: 有 GCP 账号和 GitHub 账号

---

## 🎯 3 步部署

### 步骤 1: 后端部署到 GCP Cloud Run (15 分钟)

```bash
# 1. 登录 GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. 启用 API
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# 3. 创建 secrets
echo -n "你的 Anthropic API Key" | gcloud secrets create cms-automation-ANTHROPIC_API_KEY --data-file=-
echo -n "你的数据库 URL" | gcloud secrets create cms-automation-DATABASE_URL --data-file=-
echo -n "你的 Redis URL" | gcloud secrets create cms-automation-REDIS_URL --data-file=-

# 4. 部署！
cd /Users/albertking/ES/cms_automation/backend
./scripts/deployment/deploy-to-cloud-run.sh --project-id YOUR_PROJECT_ID

# 完成！记下输出的 Service URL
```

### 步骤 2: 前端部署到 Vercel (10 分钟)

```bash
# 1. 推送代码到 GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. 访问 Vercel: https://vercel.com/new
# 3. 选择你的 GitHub 仓库
# 4. Root Directory: frontend
# 5. Framework: Vite
# 6. 环境变量:
#    VITE_API_URL = https://你的cloud-run-url.run.app

# 7. 点击 Deploy

# 完成！
```

### 步骤 3: 连接与测试 (5 分钟)

```bash
# 1. 更新后端 CORS
gcloud run services update cms-automation-backend \
    --region us-central1 \
    --set-env-vars "ALLOWED_ORIGINS=https://your-vercel-url.vercel.app"

# 2. 测试后端
curl https://your-cloud-run-url.run.app/health

# 3. 在浏览器访问前端
open https://your-vercel-url.vercel.app

# 完成！🎉
```

---

## 📊 你获得了什么

✅ **完全云端化**: 用户只需浏览器
✅ **自动扩展**: 处理任意负载
✅ **低成本**: ~$7-32/月
✅ **全球可用**: CDN 加速
✅ **HTTPS**: 自动 SSL
✅ **监控**: 内置日志和指标

---

## 🆘 遇到问题？

### 后端部署失败

```bash
# 查看日志
gcloud run logs read cms-automation-backend --region us-central1 --limit 50
```

### 前端连接不上后端

1. 检查 CORS 设置
2. 确认 VITE_API_URL 正确
3. Vercel Dashboard → Settings → Redeploy

### 详细文档

- [完整部署指南](./DEPLOYMENT_GUIDE_CLOUD.md)
- [云端架构分析](./CLOUD_DEPLOYMENT_ARCHITECTURE_ANALYSIS.md)

---

**准备好了吗？开始部署吧！** 🚀
