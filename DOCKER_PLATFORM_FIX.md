# Docker 平台架构问题修复 🐳

**日期**: 2025-11-03
**问题**: Cloud Run 部署失败,架构不匹配

---

## ❌ 问题描述

### 错误信息

```
Cloud Run does not support image 'gcr.io/talkmail-production/cms-automation-backend:v1.0.0':
Container manifest type 'application/vnd.oci.image.index.v1+json' must support amd64/linux.
```

### 根本原因

在 Mac M1/M2 (ARM64 架构) 上使用 `docker build` 命令时,默认会构建 ARM64 架构的镜像。
但是 **Google Cloud Run 只支持 amd64/linux 架构**。

```bash
# ❌ 错误做法 (在 Mac M1/M2 上)
docker build -t gcr.io/project/image:tag .
# 结果: 构建了 ARM64 镜像,Cloud Run 无法运行
```

---

## ✅ 解决方案

### 方案 1: 使用 docker buildx (推荐)

```bash
# ✅ 正确做法
docker buildx build --platform linux/amd64 \
    -t gcr.io/project/image:tag \
    --push \
    .
```

**优点**:
- 一步完成构建和推送
- 明确指定目标平台
- 支持多平台构建

### 方案 2: 使用 Google Cloud Build

```bash
# 在 GCP 云端构建 (自动使用正确架构)
gcloud builds submit --tag gcr.io/project/image:tag .
```

**优点**:
- 在云端构建,不占用本地资源
- 自动使用 amd64 架构
- 适合 CI/CD 流程

---

## 🔧 已修复的文件

### 1. `backend/scripts/deployment/deploy-dev.sh`

**修改前**:
```bash
docker build -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" .
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"
```

**修改后**:
```bash
docker buildx build --platform linux/amd64 \
    -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    --push \
    .
```

### 2. `backend/scripts/deployment/deploy-prod.sh`

**修改前**:
```bash
docker build -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" .
docker tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
           "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
```

**修改后**:
```bash
docker buildx build --platform linux/amd64 \
    -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}" \
    -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
    --push \
    .
```

---

## 🚀 使用说明

### 开发环境部署

```bash
cd /Users/albertking/ES/cms_automation/backend

# 方式 1: 使用部署脚本 (已修复)
./scripts/deployment/deploy-dev.sh

# 方式 2: 手动构建
docker buildx build --platform linux/amd64 \
    -t gcr.io/cms-automation-dev/cms-automation-backend:latest \
    --push \
    .
```

### 生产环境部署

```bash
cd /Users/albertking/ES/cms_automation/backend

# 使用部署脚本 (已修复)
./scripts/deployment/deploy-prod.sh v1.0.0

# 会自动构建 amd64 架构镜像并部署
```

---

## 🎯 最佳实践

### 1. 总是指定平台

```bash
# ✅ 推荐
docker buildx build --platform linux/amd64 -t image:tag .

# ❌ 避免 (在 Mac M1/M2 上)
docker build -t image:tag .
```

### 2. 在 CI/CD 中使用 docker buildx

```yaml
# GitHub Actions 示例
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64
    push: true
    tags: gcr.io/${{ env.PROJECT_ID }}/app:${{ env.TAG }}
```

### 3. 验证镜像架构

```bash
# 检查已推送的镜像架构
docker manifest inspect gcr.io/project/image:tag | grep architecture

# 应该输出: "architecture": "amd64"
```

---

## 📋 架构对照表

| 平台 | 本地架构 | Cloud Run 要求 | 是否兼容 |
|------|----------|----------------|----------|
| Mac Intel | amd64 | amd64 | ✅ |
| Mac M1/M2/M3 | arm64 | amd64 | ❌ 需要跨平台构建 |
| Linux (Intel/AMD) | amd64 | amd64 | ✅ |
| Linux (ARM) | arm64 | amd64 | ❌ 需要跨平台构建 |
| Windows (Intel/AMD) | amd64 | amd64 | ✅ |

---

## 🔍 故障排查

### 问题: docker buildx 命令不存在

```bash
# 解决方案: 更新 Docker Desktop
# Docker Desktop >= 19.03 自带 buildx

# 手动启用
docker buildx create --use
```

### 问题: 跨平台构建很慢

这是正常现象。在 ARM64 机器上构建 amd64 镜像需要使用 QEMU 模拟,会比原生构建慢 2-3 倍。

**解决方案**:
1. 使用 Google Cloud Build (云端构建,无需模拟)
2. 设置缓存加速后续构建
3. 只在需要部署时才构建 amd64 镜像

### 问题: Cloud Run 仍然报错

```bash
# 1. 检查镜像架构
docker manifest inspect gcr.io/project/image:tag | grep -A 3 "platform"

# 2. 强制重新部署
gcloud run deploy service-name \
    --image gcr.io/project/image:tag \
    --platform managed \
    --region us-central1

# 3. 删除旧服务重新创建
gcloud run services delete service-name --region us-central1
# 然后重新部署
```

---

## 📚 相关文档

- [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)
- [Cloud Run 容器要求](https://cloud.google.com/run/docs/container-contract)
- [多平台镜像构建指南](https://docs.docker.com/build/building/multi-platform/)

---

**总结**:
- ✅ Mac M1/M2 用户必须使用 `docker buildx build --platform linux/amd64`
- ✅ 部署脚本已更新,无需手动修改
- ✅ 后续部署会自动使用正确架构

---

**文档版本**: 1.0
**最后更新**: 2025-11-03
**维护者**: CMS Automation Team
