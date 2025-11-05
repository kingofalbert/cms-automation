# GCP 权限问题分析与解决方案

**问题发现日期**: 2025-11-04
**影响范围**: Frontend 部署到 GCS bucket `gs://cms-automation-frontend-2025/`
**严重程度**: 🔴 Critical - 阻碍生产部署

---

## 🔍 问题描述

### Codex CLI 报告
```
因为当前环境里并没有具有写入 gs://cms-automation-frontend-2025/ 权限的服务帐号或凭证，
所以 gsutil rsync 一直被 403 拒绝。

要执行"下一步"，必须先获取具备 storage.objects.create/storage.objects.delete 权限的
GCP 身份。
```

### 错误信息
```bash
$ gsutil cp /tmp/test-upload.txt gs://cms-automation-frontend-2025/test-upload.txt

AccessDeniedException: 403 albert.king@epochtimes.nyc does not have
storage.objects.create access to the Google Cloud Storage object.
Permission 'storage.objects.create' denied on resource (or it may not exist).
```

---

## 🧪 诊断结果

### 当前认证状态
```bash
$ gcloud auth list
ACTIVE  ACCOUNT
*       albert.king@epochtimes.nyc

$ gcloud config get-value project
cmsupload-476323

$ echo $GOOGLE_APPLICATION_CREDENTIALS
(not set)
```

### 权限检查结果

| 操作 | 结果 | 错误 |
|-----|------|-----|
| **列出 bucket 内容** | ✅ 成功 | `gsutil ls gs://cms-automation-frontend-2025/` 正常 |
| **读取 bucket IAM** | ❌ 失败 | `storage.buckets.getIamPolicy` 被拒绝 |
| **写入文件到 bucket** | ❌ 失败 | `storage.objects.create` 被拒绝 |
| **删除文件** | ❌ 失败 | `storage.objects.delete` 被拒绝（推测） |

### 用户角色
```bash
$ gcloud projects get-iam-policy cmsupload-476323 --filter="albert.king@epochtimes.nyc"

Role: roles/owner
```

---

## 🎯 根本原因分析

### 原因 1: Bucket 可能在不同项目中
- 当前项目: `cmsupload-476323`
- Bucket `gs://cms-automation-frontend-2025/` 的所属项目**未知**（无法读取 bucket 元数据）
- 用户在 `cmsupload-476323` 是 owner，但 bucket 可能在其他项目

### 原因 2: Bucket 级别 IAM 策略覆盖
- 即使用户在项目级别有 owner 权限
- Bucket 级别的 IAM 策略可能明确拒绝或未授予写入权限
- 常见于跨项目共享的 bucket

### 原因 3: 组织策略限制
- 组织级别的策略可能限制特定用户/服务账号的权限
- Uniform Bucket-Level Access 可能启用但配置不当

---

## ✅ 解决方案

### 方案 1: 授予用户 Bucket 写入权限 (推荐)

**适用场景**: 你有 bucket 的管理权限或可以联系管理员

#### 步骤 A: 找到 Bucket 所有者/管理员
```bash
# 尝试通过 console 或联系团队确认 bucket 所属项目和管理员
```

#### 步骤 B: 请求管理员添加权限
管理员需要在 GCS bucket 上授予以下角色之一：

**选项 1: Storage Admin (完全控制)**
```bash
gsutil iam ch user:albert.king@epochtimes.nyc:roles/storage.admin \
  gs://cms-automation-frontend-2025
```

**选项 2: Storage Object Admin (对象级别完全控制)**
```bash
gsutil iam ch user:albert.king@epochtimes.nyc:roles/storage.objectAdmin \
  gs://cms-automation-frontend-2025
```

**选项 3: 自定义角色 (最小权限)**
```bash
# 创建自定义角色（仅需要的权限）
gcloud iam roles create frontendDeployer --project=<BUCKET_PROJECT_ID> \
  --title="Frontend Deployer" \
  --description="Minimal permissions for frontend deployment" \
  --permissions=storage.objects.create,storage.objects.delete,storage.objects.get,storage.objects.list

# 授予角色
gsutil iam ch user:albert.king@epochtimes.nyc:projects/<BUCKET_PROJECT_ID>/roles/frontendDeployer \
  gs://cms-automation-frontend-2025
```

#### 验证权限
```bash
# 测试上传
echo "test" > /tmp/test.txt
gsutil cp /tmp/test.txt gs://cms-automation-frontend-2025/test.txt

# 测试删除
gsutil rm gs://cms-automation-frontend-2025/test.txt

# 如果都成功，权限配置正确 ✅
```

---

### 方案 2: 使用服务账号 (推荐用于 CI/CD)

**适用场景**: 自动化部署、CI/CD pipeline

#### 步骤 A: 创建服务账号
```bash
# 在拥有 bucket 的项目中创建服务账号
gcloud iam service-accounts create frontend-deployer \
  --display-name="Frontend Deployment Service Account" \
  --project=<BUCKET_PROJECT_ID>
```

#### 步骤 B: 授予服务账号权限
```bash
# 授予 bucket 写入权限
gsutil iam ch serviceAccount:frontend-deployer@<BUCKET_PROJECT_ID>.iam.gserviceaccount.com:roles/storage.objectAdmin \
  gs://cms-automation-frontend-2025
```

#### 步骤 C: 创建密钥并下载
```bash
# 创建 JSON 密钥
gcloud iam service-accounts keys create ~/frontend-deployer-key.json \
  --iam-account=frontend-deployer@<BUCKET_PROJECT_ID>.iam.gserviceaccount.com \
  --project=<BUCKET_PROJECT_ID>

# ⚠️ 安全提示：妥善保管此密钥文件！
```

#### 步骤 D: 配置环境变量
```bash
# 在本地环境
export GOOGLE_APPLICATION_CREDENTIALS=~/frontend-deployer-key.json

# 验证认证
gcloud auth application-default print-access-token

# 测试部署
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-2025/
```

#### 步骤 E: CI/CD 配置
```yaml
# .github/workflows/deploy.yml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    credentials_json: ${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}

- name: Deploy to GCS
  run: |
    npm run build
    gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-2025/
    gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
      gs://cms-automation-frontend-2025/*.html
```

---

### 方案 3: 切换到有权限的账号

**适用场景**: 团队中其他成员已有权限

```bash
# 列出所有已认证的账号
gcloud auth list

# 切换到有权限的账号
gcloud config set account <AUTHORIZED_ACCOUNT>

# 如果没有其他账号，登录新账号
gcloud auth login

# 选择具有 bucket 写入权限的账号登录
```

---

### 方案 4: 使用其他 Bucket (临时方案)

**适用场景**: 无法快速获取现有 bucket 权限，需要紧急部署测试

#### 步骤 A: 创建新 Bucket
```bash
# 在你的项目中创建新 bucket
gsutil mb -p cmsupload-476323 \
  -l us-central1 \
  -b on \
  gs://cms-automation-frontend-dev-2025/

# 配置公开访问（用于托管静态网站）
gsutil iam ch allUsers:objectViewer gs://cms-automation-frontend-dev-2025/
```

#### 步骤 B: 配置网站托管
```bash
# 设置主页和 404 页面
gsutil web set -m index.html -e 404.html gs://cms-automation-frontend-dev-2025/
```

#### 步骤 C: 更新部署脚本
```bash
# 修改 package.json 或部署脚本
npm run build
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-dev-2025/

# 新的访问 URL
echo "https://storage.googleapis.com/cms-automation-frontend-dev-2025/index.html"
```

---

## 🚀 立即行动步骤

### 第一步: 确定 Bucket 所属和管理员
```bash
# 联系团队/组织管理员确认：
# 1. gs://cms-automation-frontend-2025/ 属于哪个 GCP 项目？
# 2. 谁是 bucket 管理员？
# 3. 如何申请权限？
```

### 第二步: 选择解决方案
根据你的情况选择：
- ✅ **有管理员支持**: 选择方案 1（授予用户权限）
- ✅ **需要自动化部署**: 选择方案 2（服务账号）
- ✅ **紧急测试**: 选择方案 4（新 bucket）

### 第三步: 验证权限
```bash
# 成功配置权限后，运行完整部署测试
cd /home/kingofalbert/projects/CMS/frontend

# 构建
npm run build

# 部署
gsutil -m rsync -r -d dist/ gs://cms-automation-frontend-2025/

# 设置缓存策略
gsutil -m setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
  gs://cms-automation-frontend-2025/*.html

# 访问测试
curl -I https://storage.googleapis.com/cms-automation-frontend-2025/index.html
```

### 第四步: 运行 E2E 测试
```bash
# 验证 UI 正常
cd /home/kingofalbert/projects/CMS/frontend
npx playwright test e2e/production-smoke.spec.ts
```

---

## 📋 权限检查清单

验证部署权限是否完整：

- [ ] `storage.objects.create` - 上传新文件
- [ ] `storage.objects.delete` - 删除旧文件（rsync -d 需要）
- [ ] `storage.objects.get` - 读取对象（验证上传）
- [ ] `storage.objects.list` - 列出对象（rsync 需要）
- [ ] `storage.objects.update` - 更新元数据（setmeta 需要）

**最小权限角色**: `roles/storage.objectAdmin`

---

## 🔧 调试命令

```bash
# 检查当前认证
gcloud auth list
echo $GOOGLE_APPLICATION_CREDENTIALS

# 测试读取权限
gsutil ls gs://cms-automation-frontend-2025/

# 测试写入权限
echo "test" > /tmp/test.txt
gsutil cp /tmp/test.txt gs://cms-automation-frontend-2025/test.txt

# 测试删除权限
gsutil rm gs://cms-automation-frontend-2025/test.txt

# 检查项目
gcloud config get-value project

# 检查用户角色
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:$(gcloud config get-value account)"
```

---

## 🔐 安全最佳实践

### 服务账号密钥管理
- ❌ **不要**: 将密钥提交到 Git 仓库
- ❌ **不要**: 在公开日志中打印密钥
- ✅ **要**: 使用环境变量或密钥管理服务
- ✅ **要**: 定期轮换密钥（每 90 天）
- ✅ **要**: 使用 Workload Identity（GKE/Cloud Run）

### 权限最小化
```bash
# 好的做法：最小权限
roles/storage.objectAdmin  # 仅 bucket 对象权限

# 避免：过度权限
roles/storage.admin        # 包含 bucket 管理权限
roles/owner                # 项目所有者权限
```

---

## 📞 需要帮助？

### 联系团队管理员
询问以下信息：
1. Bucket `gs://cms-automation-frontend-2025/` 所属的 GCP 项目 ID
2. Bucket 管理员联系方式
3. 权限申请流程

### GCP 支持文档
- [IAM 权限参考](https://cloud.google.com/storage/docs/access-control/iam-permissions)
- [Storage 角色](https://cloud.google.com/storage/docs/access-control/iam-roles)
- [服务账号最佳实践](https://cloud.google.com/iam/docs/best-practices-service-accounts)

---

## ✅ 问题解决验证

成功配置权限后，应该能够执行：

```bash
✅ gsutil ls gs://cms-automation-frontend-2025/
✅ gsutil cp file.txt gs://cms-automation-frontend-2025/
✅ gsutil rm gs://cms-automation-frontend-2025/file.txt
✅ gsutil -m rsync -r dist/ gs://cms-automation-frontend-2025/
✅ gsutil setmeta -h "Cache-Control:no-cache" gs://cms-automation-frontend-2025/index.html
```

全部成功 = 权限配置完成！🎉

---

**下一步**: 配置好权限后，更新 `frontend/package.json` 的部署脚本，并在 CI/CD 中配置服务账号。
