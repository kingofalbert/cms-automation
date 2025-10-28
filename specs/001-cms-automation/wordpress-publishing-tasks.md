# WordPress 视觉自动化发布 - 任务清单

**文档版本**: v1.0
**创建日期**: 2025-10-27
**状态**: 规划中
**预计工期**: 4-6 周
**关联文档**:
- [wordpress-publishing-spec.md](./wordpress-publishing-spec.md)
- [wordpress-publishing-plan.md](./wordpress-publishing-plan.md)
- [wordpress-publishing-testing.md](./wordpress-publishing-testing.md)

---

## 任务概览

```
Phase 1: 基础设施搭建 (Week 1)          ████████░░░░░░░░░░░░  8 tasks
Phase 2: 核心组件开发 (Week 2-3)        ░░░░░░░░████████████  16 tasks
Phase 3: 高级功能开发 (Week 3-4)        ░░░░░░░░░░░░░░░░████  12 tasks
Phase 4: 测试与优化 (Week 4-5)          ░░░░░░░░░░░░░░░░░░██  10 tasks
Phase 5: 部署与文档 (Week 5-6)          ░░░░░░░░░░░░░░░░░░░█  6 tasks
                                         ────────────────────
                                         Total: 52 tasks
```

---

## Phase 1: 基础设施搭建 (Week 1)

### 1.1 项目结构初始化
**优先级**: P0
**预计工时**: 4 小时
**依赖**: 无

**任务描述**:
创建项目目录结构，初始化 Python 项目配置。

**验收标准**:
- ✅ 目录结构符合最佳实践
- ✅ `pyproject.toml` 配置完成
- ✅ Git 初始化并配置 `.gitignore`

**具体步骤**:
```bash
# 创建目录结构
mkdir -p src/{providers,config,models,utils}
mkdir -p tests/{unit,integration,e2e,fixtures,reports}
mkdir -p config
mkdir -p logs
mkdir -p uploads

# 创建 __init__.py
touch src/__init__.py
touch src/providers/__init__.py
touch src/config/__init__.py
touch src/models/__init__.py

# 创建配置文件
touch config/selectors.yaml
touch config/instructions.yaml
touch config/fallback_config.yaml
touch config/wordpress_sites.yaml

# 创建 requirements.txt
cat > requirements.txt << EOF
playwright==1.40.0
anthropic==0.8.1
pyyaml==6.0.1
pydantic==2.5.0
fastapi==0.104.1
uvicorn==0.24.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-html==4.1.1
pillow==10.1.0
python-dotenv==1.0.0
prometheus-client==0.19.0
EOF

# 安装依赖
pip install -r requirements.txt
playwright install chromium
```

---

### 1.2 数据模型定义
**优先级**: P0
**预计工时**: 6 小时
**依赖**: 1.1

**文件**: `src/models.py`

**任务描述**:
定义所有核心数据模型（Article, SEOData, ImageAsset, ArticleMetadata 等）。

**验收标准**:
- ✅ 所有模型使用 Pydantic 定义
- ✅ 包含必要的验证规则
- ✅ 提供序列化/反序列化方法
- ✅ 单元测试覆盖率 ≥ 90%

**核心代码**:
```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class SEOData(BaseModel):
    focus_keyword: str = Field(..., min_length=1, max_length=100)
    meta_title: str = Field(..., min_length=10, max_length=60)
    meta_description: str = Field(..., min_length=50, max_length=160)
    primary_keywords: List[str] = Field(default_factory=list)
    secondary_keywords: List[str] = Field(default_factory=list)

    @field_validator('meta_title')
    def validate_meta_title_length(cls, v):
        if len(v) < 50 or len(v) > 60:
            raise ValueError('Meta title should be 50-60 characters')
        return v

class Article(BaseModel):
    id: int
    title: str = Field(..., min_length=10, max_length=200)
    content_html: str = Field(..., min_length=100)
    excerpt: Optional[str] = None
    seo: SEOData

    @field_validator('content_html')
    def sanitize_html(cls, v):
        # 实现 HTML 清理逻辑
        return v

class ImageAsset(BaseModel):
    file_path: str
    alt_text: str = Field(..., min_length=5, max_length=100)
    title: str
    caption: str
    keywords: List[str]
    photographer: str
    is_featured: bool = False

    @field_validator('file_path')
    def validate_file_exists(cls, v):
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f'File not found: {v}')
        return v

class ArticleMetadata(BaseModel):
    tags: List[str] = Field(default_factory=list, max_items=10)
    categories: List[str] = Field(default_factory=list, max_items=5)
    publish_immediately: bool = True
    publish_date: Optional[datetime] = None
    status: str = Field(default="draft", pattern="^(draft|publish|scheduled)$")

class WordPressCredentials(BaseModel):
    username: str
    password: str

class PublishingContext(BaseModel):
    task_id: str
    article: Article
    images: List[ImageAsset]
    metadata: ArticleMetadata
    wordpress_url: str
    credentials: WordPressCredentials
    browser_cookies: Optional[List[dict]] = None
    published_url: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

class PublishResult(BaseModel):
    success: bool
    task_id: str
    url: Optional[str] = None
    audit_trail: Optional[dict] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
```

**测试文件**: `tests/unit/test_models.py`

---

### 1.3 配置管理器实现
**优先级**: P0
**预计工时**: 6 小时
**依赖**: 1.1

**文件**: `src/config/config_manager.py`

**任务描述**:
实现配置加载、验证和管理功能。

**验收标准**:
- ✅ 支持从 YAML 文件加载配置
- ✅ 支持环境变量覆盖
- ✅ 配置验证和错误提示
- ✅ 热重载配置（可选）

**核心代码**:
```python
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import os

class SelectorConfig:
    """选择器配置管理"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict

    @classmethod
    def load_from_file(cls, file_path: str) -> 'SelectorConfig':
        """从 YAML 文件加载配置"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Selector config not found: {file_path}')

        with open(path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        return cls(config_dict)

    def get(self, key: str, default: Any = None) -> Any:
        """获取选择器配置"""
        return self.config.get(key, default)

    def get_all_selectors(self, key: str) -> List[str]:
        """获取所有备选选择器"""
        value = self.get(key)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

class InstructionTemplate:
    """Computer Use 指令模板"""

    def __init__(self, templates: Dict[str, str]):
        self.templates = templates

    @classmethod
    def load_from_file(cls, file_path: str) -> 'InstructionTemplate':
        """从 YAML 文件加载模板"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Instruction template not found: {file_path}')

        with open(path, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)

        return cls(templates)

    def get(self, key: str, **kwargs) -> str:
        """获取并渲染指令模板"""
        template = self.templates.get(key)
        if template is None:
            raise KeyError(f'Instruction template not found: {key}')

        # 使用简单的字符串格式化（可以升级为 Jinja2）
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f'Missing template variable: {e}')

class PublishingConfig:
    """发布配置"""

    def __init__(self):
        self.max_retries: int = 3
        self.retry_delay: float = 2.0
        self.timeout: int = 30
        self.screenshot_enabled: bool = True
        self.log_level: str = "INFO"

    @classmethod
    def load_from_env(cls) -> 'PublishingConfig':
        """从环境变量加载配置"""
        config = cls()
        config.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        config.retry_delay = float(os.getenv('RETRY_DELAY', '2.0'))
        config.timeout = int(os.getenv('TIMEOUT', '30'))
        config.screenshot_enabled = os.getenv('SCREENSHOT_ENABLED', 'true').lower() == 'true'
        config.log_level = os.getenv('LOG_LEVEL', 'INFO')
        return config
```

---

### 1.4 Provider 接口定义
**优先级**: P0
**预计工时**: 4 小时
**依赖**: 1.2

**文件**: `src/providers/base_provider.py`

**任务描述**:
定义 `IPublishingProvider` 抽象接口。

**验收标准**:
- ✅ 使用 Python ABC 定义抽象基类
- ✅ 包含所有必需的抽象方法
- ✅ 方法签名清晰，带类型注解
- ✅ 包含详细的 docstring

**核心代码**: 参见 plan.md 中的 IPublishingProvider 定义

---

### 1.5 日志系统实现
**优先级**: P1
**预计工时**: 4 小时
**依赖**: 1.1

**文件**: `src/utils/audit_logger.py`

**任务描述**:
实现审计日志记录器。

**验收标准**:
- ✅ 支持 JSONL 格式日志
- ✅ 自动创建任务目录
- ✅ 支持截图保存
- ✅ 提供日志查询和摘要功能

**核心代码**: 参见 plan.md 中的 AuditLogger 实现

---

### 1.6 测试环境搭建
**优先级**: P1
**预计工时**: 8 小时
**依赖**: 无

**任务描述**:
搭建 WordPress 测试环境（Docker Compose）。

**验收标准**:
- ✅ WordPress 6.4 + MySQL 8.0
- ✅ 安装必需插件（Classic Editor, Yoast SEO）
- ✅ 配置测试用户和权限
- ✅ 提供初始化和清理脚本

**核心文件**:
- `docker-compose.test.yml`
- `tests/fixtures/init-wordpress.sh`

---

### 1.7 选择器配置文件编写
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 1.6

**文件**: `config/selectors.yaml`

**任务描述**:
在真实 WordPress 环境中测试并记录所有选择器。

**验收标准**:
- ✅ 覆盖所有 UI 元素
- ✅ 提供多个备选选择器
- ✅ 通过选择器验证测试

**工具**: Playwright Inspector

```bash
# 使用 Playwright Inspector 探索选择器
playwright codegen http://localhost:8080/wp-admin
```

---

### 1.8 Computer Use 指令模板编写
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 1.6

**文件**: `config/instructions.yaml`

**任务描述**:
编写所有操作的 Computer Use 自然语言指令模板。

**验收标准**:
- ✅ 覆盖所有操作步骤
- ✅ 指令清晰、具体
- ✅ 支持模板变量
- ✅ 通过手动验证（使用 Claude Desktop）

---

## Phase 2: 核心组件开发 (Week 2-3)

### 2.1 Playwright Provider - 基础方法实现
**优先级**: P0
**预计工时**: 12 小时
**依赖**: 1.2, 1.3, 1.4

**文件**: `src/providers/playwright_provider.py`

**任务描述**:
实现 Playwright Provider 的基础方法（初始化、关闭、导航、元素交互）。

**子任务**:
- [ ] 2.1.1 `initialize()` - 启动浏览器
- [ ] 2.1.2 `close()` - 关闭浏览器
- [ ] 2.1.3 `navigate_to()` - 导航
- [ ] 2.1.4 `fill_input()` - 填充输入框
- [ ] 2.1.5 `fill_textarea()` - 填充文本区域
- [ ] 2.1.6 `click_button()` - 点击按钮
- [ ] 2.1.7 `wait_for_element()` - 等待元素
- [ ] 2.1.8 `capture_screenshot()` - 截图

**验收标准**:
- ✅ 所有方法实现接口定义
- ✅ 单元测试覆盖率 ≥ 85%
- ✅ 支持多选择器备选
- ✅ 错误处理完善

---

### 2.2 Playwright Provider - 内容编辑功能
**优先级**: P0
**预计工时**: 8 小时
**依赖**: 2.1

**子任务**:
- [ ] 2.2.1 `navigate_to_new_post()` - 导航到新增文章
- [ ] 2.2.2 `clean_html_entities()` - 清理 HTML 实体
- [ ] 2.2.3 处理 TinyMCE iframe 编辑器

**验收标准**:
- ✅ 能成功填充文章标题和内容
- ✅ HTML 实体清理功能正常
- ✅ 集成测试通过

---

### 2.3 Playwright Provider - 媒体库功能
**优先级**: P0
**预计工时**: 12 小时
**依赖**: 2.1

**子任务**:
- [ ] 2.3.1 `open_media_library()` - 打开媒体库
- [ ] 2.3.2 `upload_file()` - 上传文件
- [ ] 2.3.3 `wait_for_upload_complete()` - 等待上传完成
- [ ] 2.3.4 `fill_image_metadata()` - 填写图片元数据
- [ ] 2.3.5 `configure_image_display()` - 配置显示设置
- [ ] 2.3.6 `insert_image_to_content()` - 插入图片

**验收标准**:
- ✅ 能成功上传图片
- ✅ 图片元数据填写完整
- ✅ 图片正确插入到内容中
- ✅ 集成测试通过

---

### 2.4 Playwright Provider - 特色图片功能
**优先级**: P0
**预计工时**: 10 小时
**依赖**: 2.3

**子任务**:
- [ ] 2.4.1 `set_as_featured_image()` - 设置特色图片
- [ ] 2.4.2 `edit_image()` - 进入编辑模式
- [ ] 2.4.3 `crop_image()` - 裁切图片
- [ ] 2.4.4 `save_crop()` - 保存裁切
- [ ] 2.4.5 `confirm_featured_image()` - 确认设置

**验收标准**:
- ✅ 能成功设置特色图片
- ✅ 能完成至少 2 种尺寸的裁切
- ✅ 裁切后的图片正确保存
- ✅ 集成测试通过

**⚠️ 难点**: 图片裁切框拖拽需要精确的鼠标操作

---

### 2.5 Playwright Provider - 元数据功能
**优先级**: P0
**预计工时**: 8 小时
**依赖**: 2.1

**子任务**:
- [ ] 2.5.1 `add_tag()` - 添加标签
- [ ] 2.5.2 `select_category()` - 选择分类
- [ ] 2.5.3 `configure_seo_plugin()` - 配置 SEO 插件

**验收标准**:
- ✅ 能成功添加多个标签
- ✅ 能选择多个分类
- ✅ SEO 插件配置正确（Yoast SEO）
- ✅ 集成测试通过

---

### 2.6 Playwright Provider - 发布功能
**优先级**: P0
**预计工时**: 6 小时
**依赖**: 2.1

**子任务**:
- [ ] 2.6.1 `schedule_publish()` - 设置排程
- [ ] 2.6.2 `get_published_url()` - 获取发布 URL
- [ ] 2.6.3 处理发布成功/失败消息

**验收标准**:
- ✅ 能立即发布文章
- ✅ 能排程发布文章
- ✅ 能正确获取发布后的 URL
- ✅ 集成测试通过

---

### 2.7 Computer Use Provider - 基础实现
**优先级**: P1
**预计工时**: 12 小时
**依赖**: 1.2, 1.4, 1.8

**文件**: `src/providers/computer_use_provider.py`

**任务描述**:
实现 Computer Use Provider 的核心功能。

**子任务**:
- [ ] 2.7.1 初始化 Anthropic Client
- [ ] 2.7.2 `_execute_instruction()` - 执行指令
- [ ] 2.7.3 处理 API 响应
- [ ] 2.7.4 提取结果（文本、截图、URL）
- [ ] 2.7.5 管理对话历史

**验收标准**:
- ✅ 能成功调用 Anthropic Computer Use API
- ✅ 能正确解析响应
- ✅ 对话历史管理正确
- ✅ 单元测试覆盖率 ≥ 80%

---

### 2.8 Computer Use Provider - 接口方法实现
**优先级**: P1
**预计工时**: 10 小时
**依赖**: 2.7

**任务描述**:
实现 IPublishingProvider 接口的所有方法（调用 `_execute_instruction`）。

**验收标准**:
- ✅ 所有接口方法实现
- ✅ 指令模板正确渲染
- ✅ 集成测试通过

---

### 2.9 Publishing Orchestrator - 核心逻辑
**优先级**: P0
**预计工时**: 16 小时
**依赖**: 2.1, 2.7

**文件**: `src/orchestrator.py`

**任务描述**:
实现发布协调器的核心逻辑。

**子任务**:
- [ ] 2.9.1 `publish_article()` - 主入口
- [ ] 2.9.2 `_execute_phase()` - 阶段执行
- [ ] 2.9.3 `_phase_login()` - 登录阶段
- [ ] 2.9.4 `_phase_fill_content()` - 内容填充阶段
- [ ] 2.9.5 `_phase_process_images()` - 图片处理阶段
- [ ] 2.9.6 `_phase_set_metadata()` - 元数据设置阶段
- [ ] 2.9.7 `_phase_publish()` - 发布阶段

**验收标准**:
- ✅ 能完整执行发布流程
- ✅ 每个阶段正确执行
- ✅ 审计日志完整
- ✅ 集成测试通过

---

### 2.10 降级机制实现
**优先级**: P0
**预计工时**: 8 小时
**依赖**: 2.9

**任务描述**:
实现从 Playwright 降级到 Computer Use 的逻辑。

**子任务**:
- [ ] 2.10.1 错误检测与重试
- [ ] 2.10.2 `_switch_to_fallback()` - 切换 Provider
- [ ] 2.10.3 保留浏览器状态（cookies）
- [ ] 2.10.4 从失败点继续执行

**验收标准**:
- ✅ 连续失败能触发降级
- ✅ 降级后能继续执行
- ✅ Cookies 正确传递
- ✅ 降级机制测试通过

---

## Phase 3: 高级功能开发 (Week 3-4)

### 3.1 图片预处理功能
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 无

**文件**: `src/utils/image_processor.py`

**任务描述**:
实现图片压缩和优化功能。

**子任务**:
- [ ] 3.1.1 图片大小检测
- [ ] 3.1.2 自动压缩（质量调整）
- [ ] 3.1.3 格式转换（WebP）
- [ ] 3.1.4 尺寸调整

**验收标准**:
- ✅ 能将 10MB 图片压缩到 2MB 以下
- ✅ 质量可接受（SSIM > 0.95）
- ✅ 单元测试覆盖率 ≥ 85%

**核心代码**:
```python
from PIL import Image
import io
from pathlib import Path

def optimize_image(
    image_path: str,
    max_size_mb: float = 2.0,
    quality: int = 85
) -> str:
    """优化图片大小"""
    img = Image.open(image_path)

    # 转换为 RGB（如果是 PNG 透明背景）
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    output_path = f"/tmp/{Path(image_path).stem}_optimized.jpg"

    while quality >= 50:
        img.save(output_path, format="JPEG", quality=quality, optimize=True)

        size_mb = Path(output_path).stat().st_size / (1024 * 1024)

        if size_mb <= max_size_mb:
            break

        quality -= 5

    return output_path
```

---

### 3.2 批量发布功能
**优先级**: P2
**预计工时**: 8 小时
**依赖**: 2.9

**文件**: `src/orchestrator.py` (扩展)

**任务描述**:
实现批量发布多篇文章的功能。

**子任务**:
- [ ] 3.2.1 `BatchPublisher` 类实现
- [ ] 3.2.2 并发控制（Semaphore）
- [ ] 3.2.3 批量结果汇总
- [ ] 3.2.4 失败重试策略

**验收标准**:
- ✅ 支持并发发布（最多 5 个并发）
- ✅ 能正确处理部分失败
- ✅ E2E 测试通过（发布 10 篇文章）

---

### 3.3 Rank Math SEO 插件支持
**优先级**: P2
**预计工时**: 6 小时
**依赖**: 2.5

**任务描述**:
添加对 Rank Math SEO 插件的支持。

**子任务**:
- [ ] 3.3.1 添加 Rank Math 选择器
- [ ] 3.3.2 实现 `configure_rank_math()` 方法
- [ ] 3.3.3 自动检测 SEO 插件类型

**验收标准**:
- ✅ 能正确配置 Rank Math
- ✅ 自动检测功能正常
- ✅ 集成测试通过

---

### 3.4 Gutenberg 编辑器支持（基础）
**优先级**: P2
**预计工时**: 16 小时
**依赖**: 2.1

**任务描述**:
添加对 Gutenberg（区块编辑器）的基础支持。

**⚠️ 注意**: Gutenberg 选择器和操作方式与经典编辑器完全不同。

**子任务**:
- [ ] 3.4.1 检测编辑器类型
- [ ] 3.4.2 Gutenberg 选择器配置
- [ ] 3.4.3 实现段落区块插入
- [ ] 3.4.4 实现标题区块插入
- [ ] 3.4.5 实现图片区块插入

**验收标准**:
- ✅ 能在 Gutenberg 中发布文章
- ✅ 能插入文本和图片
- ✅ 集成测试通过

---

### 3.5 多站点支持
**优先级**: P2
**预计工时**: 6 小时
**依赖**: 1.3

**文件**: `src/config/site_manager.py`

**任务描述**:
支持管理多个 WordPress 站点配置。

**子任务**:
- [ ] 3.5.1 `SiteManager` 类实现
- [ ] 3.5.2 从 `wordpress_sites.yaml` 加载配置
- [ ] 3.5.3 站点选择逻辑

**验收标准**:
- ✅ 能加载多个站点配置
- ✅ 能根据 site_id 选择站点
- ✅ 单元测试覆盖率 ≥ 85%

---

### 3.6 Webhook 通知
**优先级**: P2
**预计工时**: 4 小时
**依赖**: 2.9

**文件**: `src/utils/notifier.py`

**任务描述**:
发布成功/失败后发送 Webhook 通知（如 Slack, Discord）。

**验收标准**:
- ✅ 支持 Slack Webhook
- ✅ 支持自定义 Webhook
- ✅ 通知包含文章 URL 和状态

---

### 3.7 错误恢复机制
**优先级**: P1
**预计工时**: 8 小时
**依赖**: 2.9

**任务描述**:
实现任务中断后的恢复机制。

**子任务**:
- [ ] 3.7.1 保存任务状态到数据库/文件
- [ ] 3.7.2 `resume_task()` 方法实现
- [ ] 3.7.3 已完成步骤跳过逻辑

**验收标准**:
- ✅ 任务中断后能从断点继续
- ✅ 不重复执行已完成的步骤
- ✅ 集成测试通过

---

### 3.8 API 服务实现
**优先级**: P1
**预计工时**: 10 小时
**依赖**: 2.9

**文件**: `src/api/main.py`

**任务描述**:
使用 FastAPI 提供 REST API 服务。

**子任务**:
- [ ] 3.8.1 `/publish` 接口 - 发布文章
- [ ] 3.8.2 `/tasks/{task_id}` 接口 - 查询任务状态
- [ ] 3.8.3 `/tasks/{task_id}/logs` 接口 - 获取日志
- [ ] 3.8.4 `/health` 接口 - 健康检查

**验收标准**:
- ✅ 所有接口正常工作
- ✅ 支持异步任务
- ✅ 提供 OpenAPI 文档
- ✅ API 测试通过

**核心代码**:
```python
from fastapi import FastAPI, BackgroundTasks
from src.models import Article, ImageAsset, ArticleMetadata, PublishResult
from src.orchestrator import PublishingOrchestrator
import uuid

app = FastAPI(title="WordPress Publishing API")

tasks_db = {}  # 临时存储，实际应使用数据库

@app.post("/publish", response_model=dict)
async def publish_article(
    article: Article,
    images: list[ImageAsset],
    metadata: ArticleMetadata,
    background_tasks: BackgroundTasks
):
    """发布文章（异步）"""
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending"}

    background_tasks.add_task(
        run_publishing_task,
        task_id,
        article,
        images,
        metadata
    )

    return {"task_id": task_id, "status": "pending"}

async def run_publishing_task(
    task_id: str,
    article: Article,
    images: list[ImageAsset],
    metadata: ArticleMetadata
):
    """后台任务：执行发布"""
    try:
        tasks_db[task_id]["status"] = "running"

        orchestrator = PublishingOrchestrator(...)
        result = await orchestrator.publish_article(article, images, metadata)

        tasks_db[task_id] = {
            "status": "completed" if result.success else "failed",
            "result": result.dict()
        }
    except Exception as e:
        tasks_db[task_id] = {
            "status": "failed",
            "error": str(e)
        }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks_db:
        return {"error": "Task not found"}, 404
    return tasks_db[task_id]

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
```

---

## Phase 4: 测试与优化 (Week 4-5)

### 4.1 单元测试完善
**优先级**: P0
**预计工时**: 12 小时
**依赖**: Phase 2 所有任务

**任务描述**:
编写和完善所有单元测试。

**验收标准**:
- ✅ 代码覆盖率 ≥ 85%
- ✅ 所有 Provider 方法有单元测试
- ✅ 所有 Orchestrator 方法有单元测试
- ✅ 边界情况测试完善

---

### 4.2 集成测试开发
**优先级**: P0
**预计工时**: 10 小时
**依赖**: 2.9

**任务描述**:
编写集成测试，验证组件间交互。

**测试用例**:
- [ ] 4.2.1 完整发布流程（Playwright）
- [ ] 4.2.2 图片上传和插入
- [ ] 4.2.3 特色图片设置和裁切
- [ ] 4.2.4 元数据和 SEO 配置
- [ ] 4.2.5 降级机制触发

---

### 4.3 E2E 测试开发
**优先级**: P0
**预计工时**: 12 小时
**依赖**: 2.9, 4.2

**任务描述**:
编写端到端测试，在真实环境中验证。

**测试用例**:
- [ ] 4.3.1 单篇文章完整发布
- [ ] 4.3.2 排程发布
- [ ] 4.3.3 批量发布
- [ ] 4.3.4 失败恢复

---

### 4.4 选择器验证测试
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 1.7

**任务描述**:
验证所有选择器在真实 WordPress 环境中可用。

**验收标准**:
- ✅ 所有选择器通过验证
- ✅ 失败选择器有报告

---

### 4.5 性能优化
**优先级**: P1
**预计工时**: 8 小时
**依赖**: 4.3

**任务描述**:
优化发布速度和资源使用。

**优化项**:
- [ ] 4.5.1 减少不必要的等待时间
- [ ] 4.5.2 优化图片上传速度
- [ ] 4.5.3 优化选择器查找
- [ ] 4.5.4 减少截图数量（可配置）

**验收标准**:
- ✅ 单篇文章发布时间 ≤ 2.5 分钟
- ✅ 图片上传速度 ≥ 1 MB/s

---

### 4.6 性能测试
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 4.5

**任务描述**:
测量和验证性能指标。

**测试项**:
- [ ] 4.6.1 单篇文章发布时间
- [ ] 4.6.2 图片上传速度
- [ ] 4.6.3 并发发布性能
- [ ] 4.6.4 内存使用

---

### 4.7 兼容性测试
**优先级**: P2
**预计工时**: 10 小时
**依赖**: 4.3

**任务描述**:
测试在不同 WordPress 版本、主题、插件下的兼容性。

**测试矩阵**:
- WordPress 版本: 6.2, 6.3, 6.4
- 主题: Astra, GeneratePress, OceanWP
- SEO 插件: Yoast, Rank Math

---

### 4.8 错误处理完善
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 4.2

**任务描述**:
完善错误处理和用户友好的错误消息。

**验收标准**:
- ✅ 所有异常都被捕获
- ✅ 错误消息清晰易懂
- ✅ 提供解决建议

---

### 4.9 日志和监控完善
**优先级**: P1
**预计工时**: 6 小时
**依赖**: 1.5

**任务描述**:
完善日志系统和监控指标。

**子任务**:
- [ ] 4.9.1 添加 Prometheus 指标
- [ ] 4.9.2 日志级别配置
- [ ] 4.9.3 日志轮转和清理

---

### 4.10 代码审查和重构
**优先级**: P1
**预计工时**: 8 小时
**依赖**: Phase 2, Phase 3

**任务描述**:
代码审查，重构重复代码，提高可维护性。

**验收标准**:
- ✅ 消除重复代码
- ✅ 统一命名规范
- ✅ 添加必要的注释

---

## Phase 5: 部署与文档 (Week 5-6)

### 5.1 Docker 镜像构建
**优先级**: P0
**预计工时**: 4 小时
**依赖**: Phase 2, Phase 3

**文件**: `Dockerfile`, `docker-compose.yml`

**任务描述**:
创建生产环境的 Docker 镜像。

**验收标准**:
- ✅ 镜像大小 < 1GB
- ✅ 包含所有依赖
- ✅ Playwright 浏览器正确安装

---

### 5.2 环境变量配置
**优先级**: P0
**预计工时**: 2 小时
**依赖**: 5.1

**文件**: `.env.example`

**任务描述**:
提供清晰的环境变量配置文档。

**验收标准**:
- ✅ 所有必需环境变量有说明
- ✅ 提供示例值
- ✅ 安全提示

---

### 5.3 部署脚本
**优先级**: P0
**预计工时**: 4 小时
**依赖**: 5.1

**文件**: `deploy.sh`, `scripts/backup.sh`

**任务描述**:
提供一键部署和备份脚本。

**验收标准**:
- ✅ 部署脚本在全新环境中可用
- ✅ 支持配置验证
- ✅ 支持数据备份和恢复

---

### 5.4 API 文档
**优先级**: P1
**预计工时**: 4 小时
**依赖**: 3.8

**文件**: `docs/API.md`

**任务描述**:
编写 REST API 文档。

**验收标准**:
- ✅ 所有接口有文档
- ✅ 提供示例请求和响应
- ✅ Swagger/OpenAPI 文档可访问

---

### 5.5 用户手册
**优先级**: P1
**预计工时**: 6 小时
**依赖**: Phase 4

**文件**: `docs/USER_GUIDE.md`

**任务描述**:
编写用户使用手册。

**内容**:
- [ ] 5.5.1 快速开始
- [ ] 5.5.2 配置说明
- [ ] 5.5.3 常见问题 FAQ
- [ ] 5.5.4 故障排查

---

### 5.6 开发者文档
**优先级**: P2
**预计工时**: 6 小时
**依赖**: Phase 4

**文件**: `docs/DEVELOPER.md`

**任务描述**:
编写开发者文档。

**内容**:
- [ ] 5.6.1 架构设计
- [ ] 5.6.2 代码结构
- [ ] 5.6.3 如何添加新功能
- [ ] 5.6.4 如何调试

---

## 风险管理

### 高风险任务

| 任务 | 风险 | 缓解措施 | 备选方案 |
|------|------|---------|---------|
| 2.4 特色图片裁切 | Playwright 难以精确拖拽裁切框 | 使用 JavaScript 注入操作 TinyMCE | 优先使用 Computer Use |
| 3.4 Gutenberg 支持 | 选择器复杂且不稳定 | 提前进行大量测试 | 先支持经典编辑器 |
| 4.7 兼容性测试 | 不同版本行为差异大 | 建立测试矩阵 | 明确支持的版本范围 |
| 2.7 Computer Use | API 配额限制 | 优化指令减少调用次数 | 降级为可选功能 |

---

## 里程碑

### Milestone 1: MVP (Week 3 结束)
**目标**: 完成核心发布功能（仅 Playwright）

**包含任务**:
- Phase 1 所有任务
- Phase 2: 2.1-2.6, 2.9
- 基础测试

**交付物**:
- ✅ 能在经典编辑器中发布文章
- ✅ 能上传和插入图片
- ✅ 能配置 SEO（Yoast）
- ✅ 集成测试通过

---

### Milestone 2: Production Ready (Week 5 结束)
**目标**: 生产可用版本（含降级机制）

**包含任务**:
- Milestone 1
- Phase 2: 2.7-2.10
- Phase 3: 3.1-3.3, 3.7-3.8
- Phase 4 所有任务

**交付物**:
- ✅ 支持 Playwright + Computer Use 降级
- ✅ 提供 REST API
- ✅ 完整的测试覆盖
- ✅ 错误恢复机制

---

### Milestone 3: Feature Complete (Week 6 结束)
**目标**: 功能完整版本

**包含任务**:
- Milestone 2
- Phase 3 剩余任务
- Phase 5 所有任务

**交付物**:
- ✅ 支持 Gutenberg（基础）
- ✅ 支持 Rank Math
- ✅ 批量发布
- ✅ 完整文档
- ✅ Docker 部署

---

## 资源估算

### 人力资源
- **后端开发** (1人 x 6周): Python, Playwright, Async
- **测试工程师** (0.5人 x 4周): Pytest, E2E 测试
- **DevOps** (0.5人 x 1周): Docker, CI/CD

### 技术栈
- **语言**: Python 3.11+
- **核心库**: Playwright, Anthropic SDK
- **框架**: FastAPI, Pydantic
- **测试**: Pytest, pytest-asyncio
- **部署**: Docker, Docker Compose

### 成本估算
- **开发成本**: 6 人周
- **Anthropic API 成本**: ~$50-100/月（测试 + 生产）
- **服务器成本**: ~$20-50/月（2核4GB）

---

## 验收清单

### 功能验收
- [ ] 能在 WordPress 经典编辑器中发布文章
- [ ] 能上传和插入图片（元数据完整）
- [ ] 能设置特色图片并裁切
- [ ] 能配置标签、分类、SEO
- [ ] 能立即发布和排程发布
- [ ] Playwright 失败能降级到 Computer Use
- [ ] 提供 REST API
- [ ] 支持批量发布

### 质量验收
- [ ] 单元测试覆盖率 ≥ 85%
- [ ] 集成测试通过率 100%
- [ ] E2E 测试通过率 ≥ 95%
- [ ] 性能达标（单篇 ≤ 3 分钟）
- [ ] 代码审查通过
- [ ] 文档完整

### 部署验收
- [ ] Docker 镜像构建成功
- [ ] 在测试环境部署成功
- [ ] 健康检查正常
- [ ] 日志和监控正常
- [ ] 备份恢复流程验证

---

**文档版本**: v1.0
**作者**: AI Architect
**审核**: Pending
**状态**: ✅ **SpecKit 文档集完成**

---

## 下一步行动

1. **评审文档**: 与团队评审所有 SpecKit 文档，确认需求和设计
2. **环境准备**: 搭建开发和测试环境（参考 Task 1.6）
3. **Sprint 规划**: 根据任务清单规划 Sprint（建议 2 周一个 Sprint）
4. **开始开发**: 从 Phase 1 任务开始执行

**预祝项目成功！🚀**
