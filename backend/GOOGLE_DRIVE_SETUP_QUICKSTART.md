# Google Drive Credential 设置快速指南

**用途**: 设置新的 Google Drive 服务账号和文件夹用于 CMS Automation 系统

**详细文档**: `backend/docs/google_drive_integration_guide.md`

---

## ⚠️ 重要说明

### Google Drive 功能分类

| 功能 | 状态 | 权限需求 | 说明 |
|------|------|---------|------|
| **📄 文档同步** | ✅ **必需** | Viewer（只读） | 从 Drive 读取 YAML 文档同步到 Worklist |
| **📁 图片上传备份** | ⚠️ **可选** | Editor（编辑） | 上传图片到 Drive 作为备份（非必需） |

**推荐配置**:
- 对于核心功能，只需配置 **Viewer（查看者）** 权限
- Computer Use 会直接处理图片上传到 WordPress，不需要通过 Google Drive

**本指南适用于**:
- ✅ 设置文档同步功能（只读权限）
- ⚠️ 设置图片备份功能（可选，需要编辑权限）

---

## 📋 设置步骤概览

```
1. 创建 Google Cloud 项目 (5分钟)
2. 启用 Google Drive API (2分钟)
3. 创建服务账号 (3分钟)
4. 生成 JSON 密钥文件 (2分钟)
5. 创建 Google Drive 文件夹 (2分钟)
6. 共享文件夹给服务账号 (2分钟)
7. 配置系统 (3分钟)
8. 验证配置 (2分钟)
---
总计: ~20分钟
```

---

## 🚀 详细步骤

### Step 1: 创建 Google Cloud 项目

1. **访问 Google Cloud Console**
   - 网址: https://console.cloud.google.com/
   - 使用你的 Google 账号登录

2. **创建新项目**
   - 点击顶部项目下拉菜单
   - 点击 "新建项目"
   - 项目名称: `CMS-Automation` (或你喜欢的名称)
   - 点击 "创建"

3. **记录项目 ID**
   - 项目创建后，记下 **项目 ID**
   - 例如: `cms-automation-2025`

---

### Step 2: 启用 Google Drive API

**方法 1: 通过控制台界面**

1. 在 Google Cloud Console 左侧菜单
2. 导航到: **APIs & Services > Library**
3. 搜索: "Google Drive API"
4. 点击 "Google Drive API"
5. 点击 "启用" (Enable)

**方法 2: 通过命令行 (可选)**

```bash
# 如果你安装了 gcloud CLI
gcloud services enable drive.googleapis.com --project=cms-automation-2025
```

**验证**: 启用后会看到 "API 已启用" 的消息

---

### Step 3: 创建服务账号

1. **导航到服务账号**
   - 左侧菜单: **IAM & Admin > Service Accounts**

2. **创建服务账号**
   - 点击顶部 **+ CREATE SERVICE ACCOUNT**

3. **填写服务账号详情**
   - **服务账号名称**: `cms-automation-drive-service`
   - **服务账号 ID**: 自动生成 (如 `cms-automation-drive-service`)
   - **描述**: `Service account for CMS automation Google Drive access`

4. **点击 "创建并继续"**

5. **授予此服务账号访问项目的权限**
   - 跳过此步骤 (点击 "继续")
   - 我们将在文件夹级别授予权限

6. **向用户授予访问此服务账号的权限**
   - 跳过此步骤 (点击 "完成")

**结果**: 服务账号创建完成，显示在列表中

---

### Step 4: 生成 JSON 密钥文件

1. **找到刚创建的服务账号**
   - 在服务账号列表中点击 `cms-automation-drive-service@...`

2. **生成密钥**
   - 点击顶部 **Keys** 标签
   - 点击 **Add Key > Create new key**

3. **选择密钥类型**
   - 选择 **JSON** 格式
   - 点击 **Create**

4. **保存密钥文件**
   - JSON 文件会自动下载到你的电脑
   - 文件名类似: `cms-automation-123456-abc123def456.json`
   - **重要**: 妥善保管此文件，它包含访问 Google Drive 的凭证

**JSON 文件结构示例**:
```json
{
  "type": "service_account",
  "project_id": "cms-automation-2025",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "cms-automation-drive-service@cms-automation-2025.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

**重要字段**:
- `client_email`: 服务账号邮箱 (Step 6 需要用到)
- `private_key`: 私钥 (用于身份验证)

---

### Step 5: 创建 Google Drive 文件夹

1. **打开 Google Drive**
   - 网址: https://drive.google.com/
   - 使用你的 Google 账号登录

2. **创建新文件夹**
   - 点击左上角 "新建" 按钮
   - 选择 "文件夹"
   - 文件夹名称: `CMS Automation Files` (或你喜欢的名称)
   - 点击 "创建"

3. **获取文件夹 ID**
   - 打开刚创建的文件夹
   - 从浏览器地址栏复制文件夹 ID

   **URL 格式**:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                          └────────────────┘
                                             这就是 Folder ID
   ```

   **示例**:
   - URL: `https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG`
   - Folder ID: `1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG`

4. **记录文件夹 ID**
   - 将 Folder ID 保存到记事本，后面配置时需要

---

### Step 6: 共享文件夹给服务账号

这是**最关键**的一步！服务账号需要访问文件夹的权限。

1. **打开文件夹共享设置**
   - 在 Google Drive 中，右键点击 `CMS Automation Files` 文件夹
   - 选择 "共享" (Share)

2. **添加服务账号**
   - 在 "添加人员和组" 输入框中
   - 粘贴服务账号邮箱 (从 Step 4 的 JSON 文件中的 `client_email`)
   - 例如: `cms-automation-drive-service@cms-automation-2025.iam.gserviceaccount.com`

3. **设置权限** ⚠️ **重要**

   **根据功能需求选择权限**:

   | 功能需求 | 权限选择 | 说明 |
   |---------|---------|------|
   | 仅文档同步（核心功能） | **查看者** (Viewer) | ✅ 推荐：只读权限即可 |
   | 包含图片备份（可选） | **编辑者** (Editor) | ⚠️ 仅在需要备份时使用 |

   **推荐配置**: 选择 **查看者** (Viewer)
   - ✅ 满足文档同步需求
   - ✅ 更安全（只读权限）
   - ✅ Computer Use 会直接处理图片上传到 WordPress

4. **发送共享邀请**
   - 取消勾选 "通知用户" (服务账号不需要通知)
   - 点击 "共享" 或 "发送"

**验证**: 共享列表中应该能看到服务账号邮箱和相应权限

---

### Step 7: 配置系统

#### 7.1 复制 JSON 密钥文件到项目

```bash
# 进入项目目录
cd /home/kingofalbert/projects/CMS

# 确保 credentials 目录存在
mkdir -p backend/credentials

# 复制下载的 JSON 文件
# 替换 ~/Downloads/your-service-account-key.json 为实际路径
cp ~/Downloads/cms-automation-2025-abc123def456.json \
   backend/credentials/google-drive-credentials.json

# 设置文件权限（重要！）
chmod 600 backend/credentials/google-drive-credentials.json

# 验证文件存在
ls -lh backend/credentials/google-drive-credentials.json
```

**预期输出**:
```
-rw------- 1 kingofalbert kingofalbert 2.4K Nov  1 10:30 backend/credentials/google-drive-credentials.json
```

#### 7.2 更新 .env 文件

编辑 `.env` 文件，更新以下配置：

```bash
# 打开 .env 文件
nano .env

# 找到 Google Drive 配置部分，更新为：
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG  # 替换为你的 Folder ID
```

**完整 Google Drive 配置示例**:
```bash
# =============================================================================
# Google Drive 配置
# =============================================================================

# 服务账号凭证路径（Docker 容器内路径）
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json

# 文件夹 ID（从 Step 5 获取）
GOOGLE_DRIVE_FOLDER_ID=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
```

#### 7.3 验证 Docker 挂载配置

检查 `docker-compose.yml` 是否正确挂载 credentials 目录：

```bash
# 查看 docker-compose.yml
grep -A 10 "backend:" docker-compose.yml | grep -A 10 "volumes:"
```

**应该包含**:
```yaml
services:
  backend:
    volumes:
      - ./backend:/app
      - ./backend/credentials:/app/credentials  # 确保有这一行
```

如果没有，添加这一行。

---

### Step 8: 验证配置

#### 8.1 重启服务

```bash
# 重启 backend 服务使配置生效
docker compose restart backend

# 查看启动日志
docker compose logs -f backend
```

**预期日志**:
```
backend  | INFO: Application startup complete
backend  | google_drive_service_initialized
```

#### 8.2 测试服务账号访问

```bash
# 方法 1: 检查环境变量
docker compose exec backend printenv | grep GOOGLE_DRIVE

# 预期输出:
# GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
# GOOGLE_DRIVE_FOLDER_ID=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG

# 方法 2: 检查凭证文件
docker compose exec backend ls -lh /app/credentials/

# 预期输出:
# -rw------- 1 root root 2.4K Nov  1 10:30 google-drive-credentials.json

# 方法 3: 测试 Google Drive API 访问
docker compose exec backend python -c "
from src.services.storage import create_google_drive_storage
import asyncio

async def test():
    storage = await create_google_drive_storage()
    print('✅ Google Drive service initialized successfully')

asyncio.run(test())
"
```

#### 8.3 测试文件上传 (可选)

创建一个测试文件并上传：

```bash
# 创建测试文件
echo "Test file for Google Drive integration" > /tmp/test-upload.txt

# 上传到 Google Drive
curl -X POST http://localhost:8000/api/v1/files/upload \
  -F "file=@/tmp/test-upload.txt"
```

**预期响应**:
```json
{
  "file_id": 1,
  "drive_file_id": "1xyz...",
  "filename": "test-upload.txt",
  "file_type": "document",
  "mime_type": "text/plain",
  "public_url": "https://drive.google.com/uc?id=1xyz...&export=download",
  "created_at": "2025-11-01T10:30:00Z"
}
```

在 Google Drive 中检查文件是否出现在 `CMS Automation Files` 文件夹中。

#### 8.4 测试 Worklist 同步

在 Google Drive 文件夹中创建一个测试文档：

**文件名**: `test-sync.txt`

**内容**:
```yaml
---
title: "测试同步文档"
tags:
  - 测试
  - 同步
categories:
  - 技术
---

这是一个测试文档，用于验证 Google Drive 同步功能。
```

**触发同步**:
```bash
curl -X POST http://localhost:8000/api/v1/worklist/sync
```

**检查结果**:
```bash
curl http://localhost:8000/api/v1/worklist/
```

应该能看到新创建的 WorklistItem。

---

## ✅ 配置检查清单

在完成所有步骤后，使用此清单验证配置：

```bash
# 运行配置检查脚本
./check_config.sh
```

**预期全部通过**:
- [x] Google Cloud 项目已创建
- [x] Google Drive API 已启用
- [x] 服务账号已创建
- [x] JSON 密钥文件已下载
- [x] Google Drive 文件夹已创建
- [x] 服务账号已获得文件夹编辑权限
- [x] JSON 文件已复制到 `backend/credentials/`
- [x] 文件权限设置为 600
- [x] `.env` 文件已更新
- [x] Docker 挂载配置正确
- [x] Backend 服务已重启
- [x] Google Drive 服务初始化成功
- [x] 文件上传测试通过
- [x] Worklist 同步测试通过

---

## 🔧 常见问题

### 问题 1: "Permission denied" 错误

**原因**: 服务账号没有文件夹访问权限

**解决**:
1. 检查 Google Drive 文件夹共享设置
2. 确认服务账号邮箱在共享列表中
3. 确认权限为 "编辑者" (Editor)
4. 重新共享文件夹

### 问题 2: "Credentials not found" 错误

**原因**: JSON 文件路径不正确或文件不存在

**解决**:
```bash
# 检查文件是否存在
ls -lh backend/credentials/google-drive-credentials.json

# 检查 Docker 容器内路径
docker compose exec backend ls -lh /app/credentials/

# 检查 .env 配置
grep GOOGLE_DRIVE_CREDENTIALS_PATH .env
```

### 问题 3: "Invalid folder ID" 错误

**原因**: Folder ID 不正确

**解决**:
1. 重新从 Google Drive URL 复制 Folder ID
2. 确保 ID 格式正确（通常是 33 个字符的字母数字组合）
3. 更新 `.env` 文件中的 `GOOGLE_DRIVE_FOLDER_ID`

### 问题 4: JSON 文件权限错误

**原因**: 文件权限过于宽松，存在安全风险

**解决**:
```bash
chmod 600 backend/credentials/google-drive-credentials.json
```

### 问题 5: Docker 容器找不到凭证文件

**原因**: Docker volume 挂载配置错误

**解决**:
```bash
# 检查 docker-compose.yml
grep -A 10 "backend:" docker-compose.yml | grep "volumes:"

# 确保包含:
# - ./backend/credentials:/app/credentials

# 重启容器
docker compose restart backend
```

---

## 📚 相关文档

- **详细集成指南**: `backend/docs/google_drive_integration_guide.md`
- **YAML 格式文档**: `backend/docs/google_drive_yaml_format.md`
- **实施总结**: `backend/docs/google_drive_implementation_summary.md`
- **文件夹信息**: `backend/GOOGLE_DRIVE_FOLDER_INFO.md`

---

## 🔐 安全建议

1. **永不提交 JSON 密钥文件到 Git**
   ```bash
   # 确保 .gitignore 包含:
   credentials/*.json
   *.json
   ```

2. **定期轮换密钥** (建议每 90 天)
   - 在 Google Cloud Console 创建新密钥
   - 更新系统配置
   - 删除旧密钥

3. **限制权限范围**
   - 仅授予文件夹级别的编辑权限
   - 不要授予整个 Drive 的访问权限

4. **备份凭证文件**
   - 将 JSON 文件保存到安全的位置
   - 使用加密存储

5. **监控访问日志**
   - 定期检查 Google Cloud Console 的审计日志
   - 监控异常访问活动

---

**设置完成时间**: ~20 分钟
**难度**: ⭐⭐⭐☆☆ (中等)

**下一步**: 配置完成后，可以开始测试 Tags/Categories 功能的端到端流程。
