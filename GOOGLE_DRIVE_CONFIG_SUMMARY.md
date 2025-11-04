# Google Drive 配置摘要

**配置日期**: 2025-11-03
**状态**: ✅ 核心功能已配置完成

---

## ⚠️ 重要说明

### Google Drive 功能分类

| 功能 | 状态 | 权限需求 | 说明 |
|------|------|---------|------|
| **📄 文档同步** | ✅ **已配置** | Viewer（只读） | 从 Drive 读取 YAML 文档同步到 Worklist |
| **📁 图片上传备份** | ⚠️ **未启用** | Editor（编辑） | 上传图片到 Drive 作为备份（可选功能） |

**当前配置**: 仅启用**只读访问**（Viewer 权限），足够支持核心的文档同步功能。

**关于图片发布**:
- ✅ Computer Use 发布时会**直接处理图片上传到 WordPress**
- ✅ 图片**不需要**经过 Google Drive 即可正常发布
- ⚠️ Google Drive 图片上传功能仅用于**可选的备份需求**

---

## 📋 配置信息

### Google Cloud 项目
- **项目 ID**: `cms-automation-2025`
- **项目名称**: CMS Automation
- **区域**: us-central1

### 服务账号
- **服务账号名称**: `cms-automation-drive-service`
- **服务账号邮箱**: `cms-automation-drive-service@cms-automation-2025.iam.gserviceaccount.com`
- **创建日期**: 2025-11-03
- **密钥文件位置**: `backend/credentials/google-drive-credentials.json`
- **密钥 ID**: ba2cf0865736e37419480d014451e3e984539692

### Google Drive 文件夹
- **文件夹 ID**: `1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG`
- **访问 URL**: https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
- **环境**: 开发环境 (Development)

---

## ✅ 已完成步骤

1. ✅ 启用 Google Drive API
2. ✅ 创建服务账号 `cms-automation-drive-service`
3. ✅ 生成服务账号密钥文件
4. ✅ 保存密钥文件到 `backend/credentials/google-drive-credentials.json`
5. ✅ 设置文件权限 (600)
6. ✅ 更新 `.env` 配置文件
7. ✅ 更新项目文档

---

## ⏳ 待完成步骤

### 1. 共享 Google Drive 文件夹 ✅ **已完成**

Google Drive 文件夹已共享给服务账号：

1. ✅ 访问: https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
2. ✅ 添加服务账号邮箱: `cms-automation-drive-service@cms-automation-2025.iam.gserviceaccount.com`
3. ✅ 权限设置为: **查看者 (Viewer)** - 只读权限，满足文档同步需求

**注意**:
- 当前权限为 **Viewer（查看者）**，满足核心功能需求
- 如需启用图片上传备份功能，需升级为 **Editor（编辑者）**

### 2. 验证配置

配置完成后，运行验证测试：

```bash
# 测试服务账号认证
cd /Users/albertking/ES/cms_automation
poetry run python -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build

credentials = service_account.Credentials.from_service_account_file(
    'backend/credentials/google-drive-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive']
)

service = build('drive', 'v3', credentials=credentials)
print('✅ Google Drive 服务初始化成功')

# 测试文件夹访问
folder_id = '1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG'
results = service.files().list(
    q=f\"'{folder_id}' in parents\",
    pageSize=10,
    fields='files(id, name)'
).execute()

files = results.get('files', [])
print(f'✅ 成功访问文件夹，找到 {len(files)} 个文件')
"
```

---

## 🔒 安全注意事项

1. ✅ 密钥文件已设置为 600 权限（仅所有者可读写）
2. ✅ 密钥文件路径已添加到 `.gitignore`
3. ⚠️ **绝对不要**将密钥文件提交到 Git
4. ⚠️ **定期轮换**服务账号密钥（建议每 90 天）
5. ✅ 仅授予文件夹级别的编辑权限，不要授予整个 Drive 的权限

---

## 📁 文件夹用途

这个 Google Drive 文件夹有两个用途（一个必需，一个可选）：

### 1. 文档同步源 (Worklist Sync) ✅ **必需，已启用**
- 从文件夹读取带 YAML front matter 的文档
- 自动创建/更新 WorklistItem
- 支持 tags、categories、meta_description 等元数据
- **权限需求**: Viewer（只读）

### 2. 文件上传存储 ⚠️ **可选，未启用**
- 存储上传的图片、文档、视频等作为备份
- 生成公开访问链接
- 关联到文章/Worklist
- **权限需求**: Editor（编辑）
- **当前状态**: 未启用（图片发布由 Computer Use 直接处理）

---

## 🔗 相关文档

- **详细集成指南**: `backend/docs/google_drive_integration_guide.md`
- **快速设置指南**: `backend/GOOGLE_DRIVE_SETUP_QUICKSTART.md`
- **文件夹信息**: `backend/GOOGLE_DRIVE_FOLDER_INFO.md`
- **YAML 格式文档**: `backend/docs/google_drive_yaml_format.md`

---

## 📞 支持

如果遇到问题：
1. 检查服务账号权限
2. 验证文件夹共享设置
3. 查看 `backend/docs/google_drive_integration_guide.md` 中的故障排除部分

---

**最后更新**: 2025-11-03
**配置状态**: ✅ 核心功能已配置完成（只读文档同步）
**可选功能**: ⚠️ 图片上传备份未启用（非必需）
