# Google Drive 自动化触发器需求分析

**创建日期**: 2025-10-27
**版本**: 1.0.0
**状态**: 🆕 新需求分析
**影响范围**: 架构级变更（新增自动化触发层）

---

## 📋 一、需求概述

### 1.1 核心需求

**当前流程**（手动触发）：
```
用户打开 UI → 粘贴文稿 → 点击"提交校对" → 进入工作流
```

**新需求流程**（自动触发）：
```
记者写稿 → 保存到 Google Drive → 系统自动发现 → 自动进入工作流 → Worklist 显示进度
```

### 1.2 具体功能点

1. **Google Drive 监控器**
   - 系统定期（如每 5 分钟）查询 Google Drive 指定目录
   - 发现新的 Google Doc 文档
   - 自动读取文档内容
   - 自动触发工作流

2. **Worklist UI**
   - 显示所有文档（正在处理、已处理、待处理）
   - 显示每个文档的进度状态
   - 显示历史状态记录
   - 支持筛选和搜索

3. **状态追踪**
   - 文档在每个工作流阶段的状态
   - 时间戳记录
   - 错误和重试记录

---

## 🎯 二、需求分解

### 2.1 Google Drive 集成

#### 功能需求

**FR-071**: 系统必须能够连接到 Google Drive API
- Google OAuth 2.0 认证
- 读取指定文件夹权限
- 支持服务账号（Service Account）

**FR-072**: 系统必须能够监控指定目录的新文档
- 定时扫描机制（可配置间隔，默认 5 分钟）
- 识别新增文档（基于创建时间或修改时间）
- 避免重复处理同一文档

**FR-073**: 系统必须能够读取 Google Doc 内容
- 支持 Google Docs 格式
- 提取纯文本和基本格式（标题、段落、列表）
- 保留图片引用（Google Drive 链接）

**FR-074**: 系统必须能够标记已处理文档
- 移动到"已处理"子文件夹，或
- 添加"已处理"标签/元数据，或
- 在数据库中记录已处理文档 ID

**FR-075**: 系统必须处理 Google Drive 集成错误
- 认证失效自动刷新 token
- API 限流重试机制（指数退避）
- 错误日志和告警

#### 非功能需求

**NFR-071**: Google Drive API 调用延迟 <2 秒（P95）
**NFR-072**: 扫描频率可配置（1-60 分钟）
**NFR-073**: 并发处理能力 ≥5 个文档同时处理

---

### 2.2 Worklist UI

#### 功能需求

**FR-076**: 系统必须提供 Worklist 页面
- 路由：`/worklist`
- 显示所有文档的列表

**FR-077**: Worklist 必须显示文档基本信息
- 文档标题
- 来源（Google Drive 文件名）
- 创建时间
- 当前状态
- 负责人（如果有）

**FR-078**: Worklist 必须显示文档进度状态
- **待处理**（Pending）：已导入，等待校对
- **校对中**（Proofreading）：AI 正在分析
- **审核中**（Under Review）：等待人工审核
- **待发布**（Ready to Publish）：已确认，等待发布
- **发布中**（Publishing）：正在发布到 WordPress
- **已发布**（Published）：成功发布
- **失败**（Failed）：处理失败

**FR-079**: Worklist 必须支持筛选功能
- 按状态筛选（全部/待处理/进行中/已完成/失败）
- 按日期范围筛选
- 按关键词搜索（标题、内容）

**FR-080**: Worklist 必须支持排序
- 按创建时间排序（默认：最新在前）
- 按更新时间排序
- 按状态排序

**FR-081**: 点击文档进入详情页
- 显示完整内容
- 显示所有历史状态
- 显示操作日志
- 提供操作按钮（审核、编辑、发布、删除）

**FR-082**: Worklist 必须实时更新
- 使用 WebSocket 或轮询（每 5 秒）
- 新文档自动出现在列表顶部
- 状态变化自动刷新

**FR-083**: Worklist 必须支持批量操作
- 批量删除
- 批量重试（失败的文档）
- 批量标记为待处理

#### 非功能需求

**NFR-074**: Worklist 加载时间 <1 秒（100 条文档）
**NFR-075**: 支持分页（20/50/100 条/页）
**NFR-076**: 响应式设计（支持桌面、平板、手机）

---

### 2.3 状态追踪与历史记录

#### 功能需求

**FR-084**: 系统必须记录文档的所有状态变化
- 每次状态变化都记录到数据库
- 包含时间戳、旧状态、新状态、操作人

**FR-085**: 系统必须记录文档的操作日志
- 谁在什么时间做了什么操作
- 操作结果（成功/失败）
- 错误信息（如果有）

**FR-086**: 系统必须支持状态回退
- 如果发布失败，回退到"待发布"状态
- 保留错误信息和失败原因

**FR-087**: 系统必须计算并显示处理时长
- 每个阶段的耗时
- 总处理时长（从导入到发布）
- 平均处理时长统计

---

## 🏗️ 三、架构设计

### 3.1 新增组件

```
┌─────────────────────────────────────────────────────────────────────┐
│ Google Drive 自动化层（新增）                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐        ┌──────────────────────┐         │
│  │ Google Drive Monitor │◄───────┤ Scheduler (Celery)   │         │
│  │ - 定期扫描指定目录     │        │ - 每 5 分钟触发      │         │
│  │ - 识别新文档           │        │ - 可配置间隔         │         │
│  │ - 读取内容             │        └──────────────────────┘         │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │ Google Docs Reader   │                                          │
│  │ - 解析 Google Doc    │                                          │
│  │ - 提取文本和格式     │                                          │
│  │ - 下载图片           │                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
└─────────────┼───────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 工作流触发器（修改）                                                 │
├─────────────────────────────────────────────────────────────────────┤
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │ Article Importer     │                                          │
│  │ - 创建 Article 记录  │                                          │
│  │ - 状态: pending      │                                          │
│  │ - 触发校对流程       │                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
└─────────────┼───────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 现有工作流                                                           │
├─────────────────────────────────────────────────────────────────────┤
│  校对分析 → 人工审核 → 最终确认 → 发布                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 新增数据库表

#### `google_drive_documents` 表

```sql
CREATE TABLE google_drive_documents (
    id SERIAL PRIMARY KEY,

    -- Google Drive 信息
    google_doc_id VARCHAR(255) UNIQUE NOT NULL,  -- Google Doc 唯一 ID
    file_name VARCHAR(500) NOT NULL,             -- 文件名
    folder_id VARCHAR(255),                       -- 所在文件夹 ID
    folder_path VARCHAR(1000),                    -- 文件夹路径

    -- 文档内容
    raw_content TEXT,                             -- 原始内容
    parsed_content TEXT,                          -- 解析后的内容

    -- 关联信息
    article_id INTEGER REFERENCES articles(id),   -- 关联的文章 ID

    -- 处理状态
    status VARCHAR(20) NOT NULL DEFAULT 'discovered',
    -- 状态: discovered, processing, imported, failed

    -- 时间戳
    discovered_at TIMESTAMP DEFAULT NOW(),        -- 发现时间
    processed_at TIMESTAMP,                       -- 处理时间
    last_sync_at TIMESTAMP,                       -- 最后同步时间

    -- 错误信息
    error_message TEXT,                           -- 错误信息
    retry_count INTEGER DEFAULT 0,                -- 重试次数

    -- 元数据
    metadata JSONB,                               -- 其他元数据

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_google_drive_docs_status ON google_drive_documents(status);
CREATE INDEX idx_google_drive_docs_discovered_at ON google_drive_documents(discovered_at DESC);
CREATE INDEX idx_google_drive_docs_article_id ON google_drive_documents(article_id);
```

#### `article_status_history` 表

```sql
CREATE TABLE article_status_history (
    id SERIAL PRIMARY KEY,

    -- 关联文章
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- 状态信息
    old_status VARCHAR(30),                       -- 旧状态
    new_status VARCHAR(30) NOT NULL,              -- 新状态

    -- 操作信息
    changed_by VARCHAR(100),                      -- 操作人（user_id 或 'system'）
    change_reason VARCHAR(500),                   -- 变更原因

    -- 附加信息
    metadata JSONB,                               -- 附加元数据

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_article_status_history_article_id ON article_status_history(article_id);
CREATE INDEX idx_article_status_history_created_at ON article_status_history(created_at DESC);
```

#### 修改 `articles` 表（新增字段）

```sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) DEFAULT 'manual';
-- source_type: manual, google_drive, csv, json

ALTER TABLE articles ADD COLUMN IF NOT EXISTS google_drive_doc_id VARCHAR(255);
-- 关联的 Google Drive 文档 ID

ALTER TABLE articles ADD COLUMN IF NOT EXISTS current_status VARCHAR(30) DEFAULT 'pending';
-- 当前状态: pending, proofreading, under_review, ready_to_publish,
--          publishing, published, failed

ALTER TABLE articles ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP DEFAULT NOW();
-- 状态最后更新时间

ALTER TABLE articles ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP;
-- 开始处理时间

ALTER TABLE articles ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP;
-- 完成处理时间

ALTER TABLE articles ADD COLUMN IF NOT EXISTS total_processing_duration_seconds INTEGER;
-- 总处理时长（秒）
```

### 3.3 新增 API 端点

#### Google Drive 集成 API

```python
# 触发手动扫描
POST   /api/v1/google-drive/scan
Response: { "status": "scanning", "message": "Scan triggered" }

# 获取 Google Drive 文档列表
GET    /api/v1/google-drive/documents?status=discovered&limit=50
Response: { "documents": [...], "total": 150 }

# 获取单个 Google Drive 文档详情
GET    /api/v1/google-drive/documents/{doc_id}
Response: { "id": "...", "file_name": "...", "status": "...", ... }

# 手动导入 Google Drive 文档
POST   /api/v1/google-drive/documents/{doc_id}/import
Response: { "article_id": 123, "status": "imported" }

# 重新同步 Google Drive 文档
POST   /api/v1/google-drive/documents/{doc_id}/sync
Response: { "status": "synced", "content_updated": true }
```

#### Worklist API

```python
# 获取 Worklist
GET    /api/v1/worklist?status=all&page=1&page_size=20&sort_by=created_at&order=desc
Response: {
  "items": [
    {
      "id": 123,
      "title": "中共病毒最新消息",
      "source_type": "google_drive",
      "current_status": "under_review",
      "created_at": "2025-10-27T10:00:00Z",
      "updated_at": "2025-10-27T10:15:00Z",
      "processing_duration_seconds": 900,
      "assigned_to": "user123"
    },
    ...
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}

# 获取文档详情（含历史状态）
GET    /api/v1/worklist/{article_id}
Response: {
  "article": { ... },
  "status_history": [
    {
      "old_status": "pending",
      "new_status": "proofreading",
      "changed_by": "system",
      "created_at": "2025-10-27T10:05:00Z"
    },
    ...
  ],
  "google_drive_info": { ... }
}

# 批量操作
POST   /api/v1/worklist/batch-action
Body: {
  "action": "delete",  // or "retry", "mark_as_pending"
  "article_ids": [123, 456, 789]
}
Response: {
  "success": true,
  "processed": 3,
  "failed": 0
}

# WebSocket 实时更新（可选）
WS     /api/v1/worklist/ws
Message: {
  "type": "status_update",
  "article_id": 123,
  "new_status": "published"
}
```

### 3.4 后端服务组件

#### `GoogleDriveMonitor` 服务

```python
# backend/src/services/google_drive_monitor.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class GoogleDriveMonitor:
    """监控 Google Drive 指定目录的新文档"""

    def __init__(self, credentials: Credentials, folder_id: str):
        self.service = build('drive', 'v3', credentials=credentials)
        self.folder_id = folder_id

    def scan_for_new_documents(self, since: datetime = None) -> List[Dict]:
        """
        扫描指定文件夹的新文档

        Args:
            since: 只查找此时间之后创建的文档（默认：最后扫描时间）

        Returns:
            List of document metadata dicts
        """
        if since is None:
            since = self._get_last_scan_time()

        query = (
            f"'{self.folder_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.document' "
            f"and createdTime > '{since.isoformat()}' "
            f"and trashed = false"
        )

        results = self.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, createdTime, modifiedTime, parents)"
        ).execute()

        documents = results.get('files', [])
        return documents

    def read_document_content(self, doc_id: str) -> str:
        """
        读取 Google Doc 内容

        Args:
            doc_id: Google Doc ID

        Returns:
            Document content as plain text
        """
        service = build('docs', 'v1', credentials=self.credentials)
        document = service.documents().get(documentId=doc_id).execute()

        # 提取文本内容
        content = self._extract_text_from_document(document)
        return content

    def _extract_text_from_document(self, document: Dict) -> str:
        """从 Google Docs API 响应中提取纯文本"""
        text_parts = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_parts.append(elem['textRun']['content'])

        return ''.join(text_parts)

    def mark_as_processed(self, doc_id: str):
        """标记文档为已处理（移动到子文件夹或添加标签）"""
        # 选项 1: 移动到"已处理"文件夹
        processed_folder_id = self._get_or_create_processed_folder()
        self.service.files().update(
            fileId=doc_id,
            addParents=processed_folder_id,
            removeParents=self.folder_id,
            fields='id, parents'
        ).execute()
```

#### Celery 定时任务

```python
# backend/src/tasks/google_drive_tasks.py

from celery import shared_task
from src.services.google_drive_monitor import GoogleDriveMonitor
from src.services.article_importer import ArticleImporter
from src.models import GoogleDriveDocument, Article

@shared_task(name="scan_google_drive_for_new_documents")
def scan_google_drive_for_new_documents():
    """
    Celery 定时任务：扫描 Google Drive 的新文档

    频率：每 5 分钟运行一次（可配置）
    """
    monitor = GoogleDriveMonitor(
        credentials=get_google_credentials(),
        folder_id=settings.GOOGLE_DRIVE_FOLDER_ID
    )

    # 扫描新文档
    new_documents = monitor.scan_for_new_documents()

    logger.info(f"Found {len(new_documents)} new documents in Google Drive")

    # 处理每个新文档
    for doc in new_documents:
        try:
            # 1. 记录到数据库
            google_doc = GoogleDriveDocument.create(
                google_doc_id=doc['id'],
                file_name=doc['name'],
                folder_id=monitor.folder_id,
                status='discovered'
            )

            # 2. 触发导入任务
            import_google_drive_document.delay(google_doc.id)

        except Exception as e:
            logger.error(f"Failed to process Google Doc {doc['id']}: {e}")
            continue


@shared_task(name="import_google_drive_document")
def import_google_drive_document(google_doc_id: int):
    """
    导入单个 Google Drive 文档到系统

    Args:
        google_doc_id: google_drive_documents 表的 ID
    """
    google_doc = GoogleDriveDocument.get_by_id(google_doc_id)

    if google_doc.status != 'discovered':
        logger.warning(f"Google Doc {google_doc_id} already processed, skipping")
        return

    try:
        # 1. 更新状态
        google_doc.update(status='processing')

        # 2. 读取内容
        monitor = GoogleDriveMonitor(...)
        content = monitor.read_document_content(google_doc.google_doc_id)

        google_doc.update(raw_content=content)

        # 3. 解析内容（提取正文、Meta、关键词）
        parsed_data = parse_article_content(content)

        google_doc.update(parsed_content=parsed_data)

        # 4. 创建 Article 记录
        article = Article.create(
            title=parsed_data['title'],
            content=parsed_data['content'],
            source_type='google_drive',
            google_drive_doc_id=google_doc.google_doc_id,
            current_status='pending'
        )

        google_doc.update(article_id=article.id, status='imported')

        # 5. 触发校对流程
        trigger_proofreading_workflow.delay(article.id)

        # 6. 标记 Google Drive 文档为已处理
        monitor.mark_as_processed(google_doc.google_doc_id)

        logger.info(f"Successfully imported Google Doc {google_doc_id} as Article {article.id}")

    except Exception as e:
        google_doc.update(
            status='failed',
            error_message=str(e),
            retry_count=google_doc.retry_count + 1
        )
        logger.error(f"Failed to import Google Doc {google_doc_id}: {e}")
        raise


# Celery Beat 配置
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scan-google-drive-every-5-minutes': {
        'task': 'scan_google_drive_for_new_documents',
        'schedule': crontab(minute='*/5'),  # 每 5 分钟
    },
}
```

---

## 🎨 四、Worklist UI 设计

### 4.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│ Worklist - 文稿工作列表                             [设置] [帮助]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 统计概览                                                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐         │
│  │ 待处理   │ 校对中   │ 审核中   │ 发布中   │ 已完成   │         │
│  │   15     │    8     │    12    │    3     │   156    │         │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘         │
│                                                                     │
│  🔍 筛选和搜索                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ [状态: 全部 ▼] [日期: 最近 7 天 ▼] [搜索: ____________] [🔄] │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  📝 文档列表                                                        │
│  ┌────┬──────────────┬─────────┬────────┬──────────┬──────────┐   │
│  │ ID │ 标题         │ 来源    │ 状态   │ 创建时间 │ 操作     │   │
│  ├────┼──────────────┼─────────┼────────┼──────────┼──────────┤   │
│  │123 │中共病毒最新...│GD: doc1 │🔵审核中│10:30:00  │[查看详情]│   │
│  │124 │世卫组织警告...│GD: doc2 │🟡校对中│10:25:00  │[查看详情]│   │
│  │125 │新变种传播...  │手动输入 │⏳待处理│10:20:00  │[查看详情]│   │
│  │126 │专家呼吁民众...│GD: doc3 │✅已发布│10:15:00  │[查看文章]│   │
│  │127 │疫情防控措施...│CSV导入  │❌失败  │10:10:00  │[重试]    │   │
│  └────┴──────────────┴─────────┴────────┴──────────┴──────────┘   │
│                                                                     │
│  ← Prev | Page 1 of 10 | Next →                 [20 条/页 ▼]     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 状态颜色编码

| 状态 | 颜色 | 图标 | 描述 |
|------|------|------|------|
| **待处理** (Pending) | ⏳ 灰色 | Clock | 已导入，等待校对 |
| **校对中** (Proofreading) | 🟡 黄色 | FileSearch | AI 正在分析 |
| **审核中** (Under Review) | 🔵 蓝色 | Eye | 等待人工审核 |
| **待发布** (Ready to Publish) | 🟢 绿色 | CheckCircle | 已确认，等待发布 |
| **发布中** (Publishing) | 🔄 蓝色（脉动）| Rocket | 正在发布到 WordPress |
| **已发布** (Published) | ✅ 深绿色 | CheckDouble | 成功发布 |
| **失败** (Failed) | ❌ 红色 | XCircle | 处理失败 |

### 4.3 详情页面

点击"查看详情"后，打开详情页面或抽屉：

```
┌─────────────────────────────────────────────────────────────────────┐
│ 文档详情 #123 - 中共病毒（COVID-19）最新消息：专家警告新变种来袭    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📋 基本信息                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 标题: 中共病毒（COVID-19）最新消息：专家警告新变种来袭      │   │
│  │ 来源: Google Drive (doc_12345abcde)                         │   │
│  │ 文件名: 2025-10-27-covid-news.gdoc                          │   │
│  │ 当前状态: 🔵 审核中                                          │   │
│  │ 创建时间: 2025-10-27 10:30:00                               │   │
│  │ 更新时间: 2025-10-27 10:35:00                               │   │
│  │ 总耗时: 5 分钟                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  📜 状态历史                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ✅ 已发现 (Discovered)           10:30:00  系统自动         │   │
│  │ ✅ 正在处理 (Processing)         10:30:15  系统自动         │   │
│  │ ✅ 已导入 (Imported)             10:30:45  系统自动         │   │
│  │ ✅ 校对中 (Proofreading)         10:31:00  系统自动         │   │
│  │ ✅ 校对完成 (Proofread)          10:33:00  系统自动         │   │
│  │ 🔵 审核中 (Under Review)         10:33:15  系统自动         │   │
│  │ ⏳ 待发布 (Ready to Publish)     -         等待确认         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  📄 文章内容预览                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 【大纪元2025年10月27日讯】周五（10月25日），世界卫生组织...  │   │
│  │                                                             │   │
│  │ [展开查看完整内容]                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  🔗 操作按钮                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ [进入审核页面] [编辑内容] [删除] [查看 Google Doc 原文]     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 实时更新

**WebSocket 实时更新**（推荐）：

```javascript
// frontend/src/hooks/useWorklistRealtime.ts

import { useEffect, useState } from 'react';

export function useWorklistRealtime() {
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    // 连接 WebSocket
    const ws = new WebSocket('ws://localhost:8000/api/v1/worklist/ws');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'status_update') {
        // 更新文章状态
        setArticles(prev =>
          prev.map(article =>
            article.id === message.article_id
              ? { ...article, current_status: message.new_status }
              : article
          )
        );
      } else if (message.type === 'new_article') {
        // 新文章添加到列表顶部
        setArticles(prev => [message.article, ...prev]);
      }
    };

    return () => ws.close();
  }, []);

  return { articles, setArticles };
}
```

---

## 🧪 五、测试策略

### 5.1 Google Drive 集成测试

**单元测试**：
```python
# tests/unit/test_google_drive_monitor.py

def test_scan_for_new_documents():
    """测试扫描新文档功能"""
    mock_service = Mock()
    monitor = GoogleDriveMonitor(credentials=mock_credentials, folder_id='test_folder')

    # 模拟 API 响应
    mock_service.files().list().execute.return_value = {
        'files': [
            {'id': 'doc1', 'name': 'Test Article 1.gdoc', 'createdTime': '2025-10-27T10:00:00Z'},
            {'id': 'doc2', 'name': 'Test Article 2.gdoc', 'createdTime': '2025-10-27T10:05:00Z'}
        ]
    }

    documents = monitor.scan_for_new_documents()

    assert len(documents) == 2
    assert documents[0]['id'] == 'doc1'


def test_read_document_content():
    """测试读取文档内容"""
    monitor = GoogleDriveMonitor(...)

    content = monitor.read_document_content('doc_id')

    assert len(content) > 0
    assert '中共病毒' in content  # 检查关键词
```

**集成测试**：
```python
# tests/integration/test_google_drive_workflow.py

@pytest.mark.integration
def test_full_google_drive_import_workflow():
    """测试完整的 Google Drive 导入工作流"""

    # 1. 创建测试 Google Doc
    test_doc_id = create_test_google_doc(content="测试文章内容")

    # 2. 触发扫描任务
    scan_google_drive_for_new_documents()

    # 3. 验证文档被发现
    google_doc = GoogleDriveDocument.get_by_google_doc_id(test_doc_id)
    assert google_doc is not None
    assert google_doc.status == 'discovered'

    # 4. 触发导入任务
    import_google_drive_document(google_doc.id)

    # 5. 验证文章创建
    article = Article.get_by_google_drive_doc_id(test_doc_id)
    assert article is not None
    assert article.source_type == 'google_drive'
    assert article.current_status == 'pending'

    # 6. 清理
    cleanup_test_google_doc(test_doc_id)
```

### 5.2 Worklist UI 测试

**E2E 测试**（Playwright）：
```python
# tests/e2e/test_worklist_ui.py

def test_worklist_displays_articles(page):
    """测试 Worklist 显示文章列表"""

    # 1. 导航到 Worklist 页面
    page.goto('http://localhost:3000/worklist')

    # 2. 验证表格显示
    table = page.locator('table')
    assert table.is_visible()

    # 3. 验证至少有一行数据
    rows = page.locator('table tbody tr')
    assert rows.count() > 0

    # 4. 验证状态徽章
    status_badge = page.locator('.status-badge').first
    assert status_badge.is_visible()


def test_worklist_filter_by_status(page):
    """测试按状态筛选"""

    page.goto('http://localhost:3000/worklist')

    # 选择"审核中"状态
    page.select_option('select[name="status"]', 'under_review')

    # 等待表格更新
    page.wait_for_timeout(1000)

    # 验证所有显示的文章状态都是"审核中"
    status_badges = page.locator('.status-badge').all()
    for badge in status_badges:
        assert badge.inner_text() == '审核中'


def test_worklist_realtime_update(page):
    """测试实时更新功能"""

    page.goto('http://localhost:3000/worklist')

    # 记录初始文章数量
    initial_count = page.locator('table tbody tr').count()

    # 模拟后台添加新文章
    trigger_new_article_creation()

    # 等待 WebSocket 更新
    page.wait_for_timeout(2000)

    # 验证文章数量增加
    new_count = page.locator('table tbody tr').count()
    assert new_count == initial_count + 1
```

---

## 📦 六、实施计划

### 6.1 阶段划分

**Phase 0: Google Drive 集成（1 周）**
- [ ] 设置 Google API 凭证
- [ ] 实现 GoogleDriveMonitor 服务
- [ ] 实现 Celery 定时任务
- [ ] 创建数据库表
- [ ] 单元测试和集成测试

**Phase 1: 状态追踪系统（1 周）**
- [ ] 修改 articles 表（添加状态字段）
- [ ] 创建 article_status_history 表
- [ ] 实现状态变更追踪逻辑
- [ ] 实现状态历史记录 API

**Phase 2: Worklist UI（2 周）**
- [ ] 创建 Worklist 页面组件
- [ ] 实现筛选和搜索功能
- [ ] 实现详情页面
- [ ] 实现实时更新（WebSocket 或轮询）
- [ ] 实现批量操作

**Phase 3: 集成和测试（1 周）**
- [ ] 端到端工作流测试
- [ ] 性能测试（大量文档）
- [ ] UI 测试（E2E）
- [ ] Bug 修复

**总计：5 周**

### 6.2 优先级

**P0（必须实现）**：
- Google Drive 监控器
- 自动导入工作流
- Worklist 基础 UI
- 状态追踪

**P1（高优先级）**：
- 实时更新（WebSocket）
- 详情页面
- 批量操作

**P2（中优先级）**：
- 高级筛选
- 统计概览
- 导出功能

---

## ✅ 七、完成标准

### 7.1 功能完整性

- [ ] 系统能够每 5 分钟自动扫描 Google Drive
- [ ] 发现新文档后自动触发导入
- [ ] Worklist 显示所有文档及其状态
- [ ] 状态变化实时更新
- [ ] 支持筛选、搜索、排序
- [ ] 详情页面显示完整历史

### 7.2 性能指标

- [ ] Google Drive 扫描延迟 <2 秒
- [ ] 单文档导入时间 <10 秒
- [ ] Worklist 加载时间 <1 秒（100 条文档）
- [ ] 实时更新延迟 <2 秒

### 7.3 测试覆盖率

- [ ] 单元测试覆盖率 ≥80%
- [ ] 集成测试覆盖核心工作流
- [ ] E2E 测试覆盖 Worklist 主要功能

---

## 📝 八、总结

这个自动化触发器和 Worklist 需求是一个**重要的用户体验提升**，能够：

1. **减少手工操作**：记者只需在 Google Drive 写稿，无需登录系统手动提交
2. **提高效率**：系统自动发现和处理，节省时间
3. **增强可观测性**：Worklist 提供所有文档的全局视图
4. **便于协作**：团队可以看到所有文档的状态和进度

**关键成功因素**：
- Google Drive API 集成稳定可靠
- 定时任务准确执行
- Worklist UI 性能良好
- 实时更新流畅

**风险和缓解**：
- **风险**：Google API 限流
  - **缓解**：实现指数退避重试机制
- **风险**：大量文档导致性能问题
  - **缓解**：分页、索引优化、后台处理
- **风险**：WebSocket 连接不稳定
  - **缓解**：提供轮询作为降级方案

---

**文档创建**: 2025-10-27
**创建者**: Claude (AI Assistant)
**状态**: ✅ 分析完成，待审批
