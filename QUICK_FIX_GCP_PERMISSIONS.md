# 🚀 GCP 权限问题快速修复指南

**问题**: 无法部署前端到 `gs://cms-automation-frontend-cmsupload-476323/` (403 权限被拒)

**解决时间**: 5-10 分钟

---

## ⚡ 最快解决方案（推荐）

### 运行自动化修复脚本

```bash
cd /home/kingofalbert/projects/CMS
./scripts/fix-gcp-permissions.sh
```

**脚本会自动**:
1. ✅ 诊断当前权限状态
2. ✅ 提供 3 种解决方案
3. ✅ 可选：自动创建新 bucket（5 分钟完成）

---

## 📋 三种解决方案对比

| 方案 | 时间 | 难度 | 推荐场景 |
|-----|------|------|---------|
| **方案 1: 新建 Bucket** | ⚡ 5 分钟 | ⭐ 简单 | 🏆 快速测试/开发 |
| **方案 2: 请求权限** | 🕐 1-2 天 | ⭐⭐ 中等 | 生产环境（需要管理员） |
| **方案 3: 服务账号** | 🕐 30 分钟 | ⭐⭐⭐ 复杂 | CI/CD 自动化部署 |

---

## 🎯 方案 1: 创建新 Bucket（推荐）

### 为什么推荐？
- ✅ 无需等待管理员批准
- ✅ 完全控制权限
- ✅ 5 分钟内完成
- ✅ 立即可以部署测试

### 手动步骤

```bash
# 1. 创建新 bucket
gsutil mb -p cmsupload-476323 \
  -l us-central1 \
  -b on \
  gs://cms-automation-frontend-dev-2025/

# 2. 设置公开访问
gsutil iam ch allUsers:objectViewer \
  gs://cms-automation-frontend-dev-2025/

# 3. 配置网站托管
gsutil web set -m index.html -e 404.html \
  gs://cms-automation-frontend-dev-2025/

# 4. 部署前端
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-dev-2025/
gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
  gs://cms-automation-frontend-dev-2025/*.html

# 5. 访问网站
echo "访问: https://storage.googleapis.com/cms-automation-frontend-dev-2025/index.html"
```

### 更新配置文件

**frontend/package.json**:
```json
{
  "scripts": {
    "deploy": "npm run build && gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-dev-2025/",
    "deploy:prod": "npm run build && gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-cmsupload-476323/"
  }
}
```

**frontend/playwright.config.ts**:
```typescript
export default defineConfig({
  use: {
    baseURL: process.env.TEST_ENV === 'prod'
      ? 'https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/'
      : 'https://storage.googleapis.com/cms-automation-frontend-dev-2025/',
  },
});
```

---

## 🔐 方案 2: 请求原 Bucket 权限

### 适用场景
- 必须使用生产环境 bucket
- 有管理员支持

### 步骤

#### 1. 找到 Bucket 管理员
```bash
# Bucket 不在你的项目中，需要联系组织/团队管理员
# 询问：
# - gs://cms-automation-frontend-cmsupload-476323/ 属于哪个项目？
# - 谁是管理员？
# - 如何申请权限？
```

#### 2. 请求管理员执行
管理员需要运行（替换你的邮箱）:
```bash
gsutil iam ch user:albert.king@epochtimes.nyc:roles/storage.objectAdmin \
  gs://cms-automation-frontend-cmsupload-476323
```

#### 3. 验证权限
```bash
# 测试上传
echo "test" > /tmp/test.txt
gsutil cp /tmp/test.txt gs://cms-automation-frontend-cmsupload-476323/test.txt

# 测试删除
gsutil rm gs://cms-automation-frontend-cmsupload-476323/test.txt

# ✅ 如果都成功，权限配置完成
```

---

## 🤖 方案 3: 服务账号（CI/CD）

### 适用场景
- 需要自动化部署
- GitHub Actions / CI/CD

### 步骤

#### 1. 创建服务账号
```bash
gcloud iam service-accounts create frontend-deployer \
  --display-name="Frontend Deployment Service Account" \
  --project=cmsupload-476323
```

#### 2. 授予权限（需要 Bucket 管理员）
```bash
# 管理员运行：
gsutil iam ch serviceAccount:frontend-deployer@cmsupload-476323.iam.gserviceaccount.com:roles/storage.objectAdmin \
  gs://cms-automation-frontend-cmsupload-476323
```

#### 3. 创建密钥
```bash
gcloud iam service-accounts keys create ~/frontend-deployer-key.json \
  --iam-account=frontend-deployer@cmsupload-476323.iam.gserviceaccount.com \
  --project=cmsupload-476323
```

#### 4. 配置环境
```bash
# 本地使用
export GOOGLE_APPLICATION_CREDENTIALS=~/frontend-deployer-key.json

# 验证
gcloud auth application-default print-access-token
```

#### 5. GitHub Actions 配置
```yaml
# .github/workflows/deploy.yml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Build
        run: cd frontend && npm run build

      - name: Deploy to GCS
        run: |
          gsutil -m rsync -r -d frontend/dist/ gs://cms-automation-frontend-cmsupload-476323/
          gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
            gs://cms-automation-frontend-cmsupload-476323/*.html

      - name: Run smoke tests
        run: cd frontend && npx playwright test e2e/production-smoke.spec.ts
```

**添加 Secret 到 GitHub**:
1. 复制 `~/frontend-deployer-key.json` 内容
2. 去 GitHub 仓库 → Settings → Secrets → New secret
3. Name: `GCP_SERVICE_ACCOUNT_KEY`
4. Value: 粘贴 JSON 内容

---

## 🔍 诊断命令

```bash
# 检查当前认证
gcloud auth list
gcloud config get-value project
echo $GOOGLE_APPLICATION_CREDENTIALS

# 测试权限
./scripts/fix-gcp-permissions.sh

# 查看详细分析
cat GCP_PERMISSION_ISSUE_ANALYSIS.md
```

---

## ✅ 验证部署成功

```bash
# 1. 部署
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://YOUR-BUCKET/

# 2. 检查文件
gsutil ls gs://YOUR-BUCKET/

# 3. 测试访问
curl -I https://storage.googleapis.com/YOUR-BUCKET/index.html

# 4. 运行 E2E 测试
npx playwright test e2e/production-smoke.spec.ts
```

**成功标志**:
- ✅ HTTP 200 响应
- ✅ Content-Type: text/html
- ✅ 文件大小 > 0
- ✅ E2E 测试通过

---

## 🆘 常见问题

### Q1: 脚本提示 "permission denied"
```bash
chmod +x scripts/fix-gcp-permissions.sh
```

### Q2: gsutil 命令未找到
```bash
# 安装 Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### Q3: 新 bucket 无法公开访问
```bash
# 确认 IAM 策略
gsutil iam get gs://YOUR-BUCKET/

# 重新设置公开访问
gsutil iam ch allUsers:objectViewer gs://YOUR-BUCKET/
```

### Q4: 部署后 404 错误
```bash
# 检查文件是否上传
gsutil ls -r gs://YOUR-BUCKET/

# 检查 index.html 是否存在
gsutil ls gs://YOUR-BUCKET/index.html

# 访问完整路径
https://storage.googleapis.com/YOUR-BUCKET/index.html
```

---

## 📞 需要帮助？

1. **运行诊断脚本**: `./scripts/fix-gcp-permissions.sh`
2. **查看详细文档**: `GCP_PERMISSION_ISSUE_ANALYSIS.md`
3. **联系团队管理员**: 询问 `gs://cms-automation-frontend-cmsupload-476323/` 权限

---

## 🎯 推荐行动

### 立即行动（5 分钟）
```bash
# 运行自动化脚本，选择选项 1（创建新 bucket）
./scripts/fix-gcp-permissions.sh

# 部署测试
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-dev-2025/

# 访问测试
open https://storage.googleapis.com/cms-automation-frontend-dev-2025/index.html
```

### 长期方案（等待管理员批准）
1. 联系 `gs://cms-automation-frontend-cmsupload-476323/` 管理员
2. 请求 `roles/storage.objectAdmin` 权限
3. 配置服务账号用于 CI/CD
4. 更新生产部署流程

---

**完成后**: 运行 E2E 测试验证部署 ✅
```bash
cd frontend
npx playwright test e2e/production-smoke.spec.ts
```
