# Google Drive 文件夹信息

**文件夹 ID**: `1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG`

**访问 URL**: https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG

**环境**: 开发环境 (Development)

---

## ⚠️ 重要说明：功能分类

### Google Drive 在本系统中的使用分为两类：

| 功能 | 状态 | 权限需求 | 说明 |
|------|------|---------|------|
| **📄 文档同步** | ✅ **必需，已配置** | Viewer（只读） | 从 Drive 读取 YAML 文档同步到 Worklist |
| **📁 图片上传备份** | ⚠️ **可选，未启用** | Editor（编辑） | 上传图片到 Drive 作为备份（非必需） |

**当前配置**: 仅启用**只读访问**（Viewer 权限），足够支持核心的文档同步功能。

**关于图片处理**:
- ✅ Computer Use 发布时会**直接处理图片上传到 WordPress**
- ✅ 图片**不需要**经过 Google Drive 存储即可正常发布
- ⚠️ Google Drive 图片上传功能仅用于**可选的备份和归档需求**

---

## 📋 文件夹用途

这个 Google Drive 文件夹在系统中有**两个用途**（一个必需，一个可选）：

### 1. 📄 文档同步源（Worklist Sync）✅ **必需功能**

**功能**: 从 Google Drive 文件夹中读取文档，自动同步到 Worklist

**权限需求**: ✅ **Viewer（查看者）** - 只读权限即可

**工作流程**:
```
Google Drive 文件夹
    ↓ (包含带 YAML front matter 的文档)
GoogleDriveSyncService 读取
    ↓ (解析 YAML: title, tags, categories, meta_description, seo_keywords)
创建/更新 WorklistItem
    ↓
待发布文章列表
```

**服务代码**: `src/services/google_drive/sync_service.py`

**关键方法**:
```python
class GoogleDriveSyncService:
    def __init__(self, session, folder_id=None):
        self.folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID

    async def sync_worklist(self, max_results=100):
        # 列出文件夹中的所有文档
        files = await storage.list_files(folder_id=self.folder_id, max_results=max_results)

        # 下载并解析每个文档
        for file_metadata in files:
            parsed = await self._hydrate_document(storage, file_metadata)
            # 创建/更新 WorklistItem
            await self._upsert_worklist_item(parsed)
```

**支持的文档格式**:
- Google Docs（自动转为纯文本）
- 纯文本文件 (.txt)
- 带 YAML front matter 的文档

**YAML front matter 示例**:
```yaml
---
title: "文章标题"
meta_description: "SEO 描述"
seo_keywords:
  - 关键词1
  - 关键词2
tags:
  - 标签1
  - 标签2
categories:
  - 分类1
---

文章正文内容...
```

**API 端点**:
```bash
# 触发同步
POST /api/v1/worklist/sync

# 同步特定文件夹
POST /api/v1/worklist/sync
{
  "folder_id": "1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG"
}
```

---

### 2. 📁 文件上传存储（File Upload Storage）⚠️ **可选功能，未启用**

**功能**: 存储上传的文件（图片、文档、视频等）作为备份

**权限需求**: ⚠️ **Editor（编辑者）** - 需要写入权限

**当前状态**: **未启用** - 因为图片发布由 Computer Use 直接处理，不需要通过 Google Drive

**工作流程**:
```
用户上传文件
    ↓ (通过 API)
GoogleDriveStorage 服务
    ↓ (上传到指定文件夹)
Google Drive 文件夹
    ↓ (生成公开链接)
存储到 uploaded_files 表
    ↓
关联到文章/Worklist
```

**服务代码**: `src/services/storage/google_drive_storage.py`

**关键方法**:
```python
class GoogleDriveStorage:
    def __init__(self):
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID

    async def upload_file(self, file_content, filename, mime_type, folder_id=None):
        # 上传到默认文件夹或指定文件夹
        folder = folder_id or self.folder_id
        # ... 上传逻辑
        return public_url
```

**支持的文件类型**:
- **图片**: JPG, PNG, GIF, WebP
- **文档**: PDF, DOCX, TXT
- **视频**: MP4, MOV, AVI
- **其他**: 所有 MIME 类型

**API 端点**:
```bash
# 上传单个文件
POST /api/v1/files/upload
Content-Type: multipart/form-data
- file: [文件]
- article_id: [可选]
- folder_id: [可选，默认使用配置的文件夹]

# 上传多个文件
POST /api/v1/files/upload-bulk
Content-Type: multipart/form-data
- files: [文件数组]
- article_id: [可选]

# 列出文件夹中的文件
GET /api/v1/files/?folder_id=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
```

---

## 🔐 访问权限

### 服务账号设置

**服务账号邮箱**: 从凭证文件中的 `client_email` 字段获取

**当前配置权限**: ✅ **Viewer（查看者）** - 只读权限

**权限说明**:
| 功能 | 所需权限 | 当前状态 |
|------|---------|---------|
| 文档同步（核心功能） | Viewer（只读） | ✅ 已配置 |
| 图片上传备份（可选） | Editor（编辑） | ❌ 未配置 |

**设置步骤**（当前只需只读权限）:
1. 打开 Google Drive 文件夹
2. 右键 → 共享
3. 添加服务账号邮箱
4. 权限设置为 **"查看者"**（核心功能）或 "编辑者"（如需备份功能）
5. 发送共享邀请

**凭证文件**: `backend/credentials/google-drive-credentials.json`

**验证命令**:
```bash
# 检查凭证文件
ls -lh backend/credentials/google-drive-credentials.json

# 查看服务账号邮箱
cat backend/credentials/google-drive-credentials.json | grep client_email
# 应该显示: "client_email": "cms-automation-drive-service@cms-automation-2025.iam.gserviceaccount.com"
```

---

## 📊 文件夹使用场景

### 场景 1: Tags/Categories 功能端到端测试

**目标**: 测试 YAML front matter 解析和 tags/categories 自动设置

**步骤**:
1. **创建测试文档** (tags-mvp-test.txt):
```yaml
---
title: "Tags MVP 测试文章"
meta_description: "测试 Computer Use 自动设置 WordPress Tags 和 Categories"
seo_keywords:
  - Computer Use
  - WordPress 自动化
tags:
  - 测试标签1
  - 测试标签2
  - 芳香疗法
categories:
  - 技术测试
  - 健康与保健
---

# 测试内容

这是一篇测试文章，用于验证 Tags/Categories 完整数据流。
```

2. **上传到 Google Drive**:
   - 打开: https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
   - 上传文件: `tags-mvp-test.txt`

3. **触发同步**:
```bash
curl -X POST http://localhost:8000/api/v1/worklist/sync
```

4. **验证 WorklistItem**:
```bash
curl http://localhost:8000/api/v1/worklist/
# 检查最新的 item 是否包含 tags 和 categories
```

5. **发布到 WordPress**:
```bash
curl -X POST http://localhost:8000/api/v1/worklist/{item_id}/publish \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "computer_use",
    "options": {"headless": false}
  }'
```

6. **验证 WordPress**:
   - 检查 WordPress 文章是否有正确的 tags 和 categories
   - 查看 Computer Use 截图验证每个步骤

---

### 场景 2: 批量文章导入

**目标**: 从 Google Drive 批量导入待发布文章

**步骤**:
1. 在文件夹中放置多个 YAML 文档
2. 触发批量同步
3. 在 Worklist 中管理文章队列
4. 批量发布到 WordPress

**示例文档列表**:
```
/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG/
├── article-001.txt  (带 YAML front matter)
├── article-002.txt
├── article-003.txt
└── images/
    ├── article-001-featured.jpg
    ├── article-002-featured.jpg
    └── article-003-featured.jpg
```

---

### 场景 3: 图片存储和引用 ⚠️ **可选功能，未启用**

**目标**: 上传文章图片到 Google Drive 作为备份

**注意**: ⚠️ **此功能为可选，当前未启用**
- Computer Use 发布时会**直接处理图片上传到 WordPress**
- **不需要**将图片先上传到 Google Drive
- 此功能仅用于需要在 Google Drive 中保留图片备份的场景

**步骤**（如需启用备份功能）:
1. 升级服务账号权限为 Editor
2. 上传图片到 Google Drive 文件夹
3. 系统生成公开 URL 并记录到数据库
4. 发布时从 Drive 下载到临时目录，再上传到 WordPress

**上传示例**:
```bash
# 上传文章特色图片
curl -X POST http://localhost:8000/api/v1/files/upload \
  -F "file=@featured-image.jpg" \
  -F "article_id=123"

# 返回
{
  "file_id": 456,
  "drive_file_id": "1xyz...",
  "public_url": "https://drive.google.com/uc?id=1xyz...&export=download",
  "article_id": 123
}
```

---

## 📁 文件夹结构建议

### 推荐的组织方式

```
/CMS Automation Files (1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG)/
│
├── 📄 articles/                    # 待同步的文章文档
│   ├── 2025-10/
│   │   ├── article-001.txt
│   │   ├── article-002.txt
│   │   └── article-003.txt
│   └── 2025-11/
│       └── article-004.txt
│
├── 🖼️ images/                      # 上传的图片
│   ├── featured/                  # 特色图片
│   │   ├── article-001-featured.jpg
│   │   └── article-002-featured.jpg
│   └── content/                   # 文章内容图片
│       ├── image-001.jpg
│       └── image-002.jpg
│
├── 📝 drafts/                      # 草稿（暂不同步）
│   └── draft-article.txt
│
└── 📋 templates/                   # 模板文件
    ├── article-template.txt       # YAML front matter 模板
    └── seo-checklist.md
```

**注意**:
- 当前系统会同步文件夹中的**所有文档**
- 如果只想同步特定文档，可以使用子文件夹并在同步时指定

---

## 🔧 配置详情

### 环境变量

```bash
# Google Drive 配置
GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
```

### Settings 类定义

**文件**: `src/config/settings.py`

```python
class Settings(BaseSettings):
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = Field(
        default="",
        description="Path to Google Drive service account credentials JSON file"
    )
    GOOGLE_DRIVE_FOLDER_ID: str = Field(
        default="",
        description="Google Drive folder ID for file uploads"
    )
```

### 使用位置

1. **GoogleDriveSyncService** (`src/services/google_drive/sync_service.py:35`)
   ```python
   self.folder_id = folder_id or self.settings.GOOGLE_DRIVE_FOLDER_ID
   ```

2. **GoogleDriveStorage** (`src/services/storage/google_drive_storage.py:31`)
   ```python
   self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
   ```

3. **ArticleImporter** (`src/services/article_importer/service.py:267`)
   ```python
   if not settings.GOOGLE_DRIVE_FOLDER_ID:
       raise ValueError("Google Drive folder ID not configured")
   ```

---

## 🧪 测试验证

### 验证文件夹访问

```bash
# 方法 1: 通过浏览器
# 访问: https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
# 检查是否可以看到文件夹内容

# 方法 2: 通过 API 测试
curl -X GET http://localhost:8000/api/v1/worklist/sync

# 方法 3: 通过 Backend 容器
docker compose exec backend python -c "
from src.config import get_settings
settings = get_settings()
print(f'Folder ID: {settings.GOOGLE_DRIVE_FOLDER_ID}')
"
```

### 验证服务账号权限

```bash
# 检查凭证文件
cat backend/credentials/google-drive-credentials.json | grep client_email

# 示例输出:
# "client_email": "cms-automation-drive-service@cms-automation-2025.iam.gserviceaccount.com"

# 在 Google Drive 中验证:
# 1. 打开文件夹: https://drive.google.com/drive/folders/1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG
# 2. 点击右上角"共享"图标
# 3. 检查服务账号邮箱是否在共享列表中
# 4. 确认权限为"编辑者"
```

---

## 📚 相关文档

- **Google Drive 集成指南**: `backend/docs/google_drive_integration_guide.md`
- **YAML 格式文档**: `backend/docs/google_drive_yaml_format.md`
- **实施总结**: `backend/docs/google_drive_implementation_summary.md`
- **配置完成报告**: `backend/CONFIGURATION_COMPLETE.md`
- **Tags Feature MVP**: `backend/TAGS_COMPUTER_USE_MVP_COMPLETED.md`

---

**最后更新**: 2025-11-03
**状态**: ✅ 核心功能已配置（只读文档同步）
**可选功能**: ⚠️ 图片上传备份功能未启用（非必需）
