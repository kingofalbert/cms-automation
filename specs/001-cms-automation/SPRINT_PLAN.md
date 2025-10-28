# WordPress 视觉自动化发布 - Sprint 执行计划

**策略**: 稳健生产版（5 周）
**创建日期**: 2025-10-27
**项目周期**: 2025-11-04 ~ 2025-12-06 (5 周)
**团队配置**: 1 后端开发 + 0.5 测试工程师

---

## 📋 总体规划

```
Sprint 1 (Week 1)     ████████░░░░░░░░░░░░  基础设施 + 环境准备
Sprint 2 (Week 2-3)   ░░░░░░░░████████████  Playwright 核心实现
Sprint 3 (Week 3-4)   ░░░░░░░░░░░░████████  Computer Use + 降级
Sprint 4 (Week 4-5)   ░░░░░░░░░░░░░░░░████  测试 + 优化 + API
Sprint 5 (Week 5)     ░░░░░░░░░░░░░░░░░░██  部署 + 文档
                      ────────────────────
                      5 Sprints, 5 Weeks
```

### 里程碑
- **Week 1 结束**: 基础设施完成，可以开始编码
- **Week 3 中**: MVP 完成（仅 Playwright）
- **Week 4 中**: 生产版完成（含降级机制）
- **Week 5 结束**: 部署上线

---

## 🏃 Sprint 1: 基础设施搭建 (Week 1)

**时间**: 2025-11-04 ~ 2025-11-08 (5 天)
**目标**: 完成所有基础设施，为核心开发做准备
**团队**: 1 后端开发

### Sprint 目标
✅ 项目结构和环境配置完成
✅ 核心数据模型和接口定义完成
✅ WordPress 测试环境搭建完成
✅ 选择器和指令模板配置完成

---

### 📅 Day 1 (Monday) - 项目初始化

#### 上午 (4h)
**任务**: 1.1 项目结构初始化 (P0, 4h)

```bash
# 1. 创建目录结构
mkdir -p src/{providers,config,models,utils,api}
mkdir -p tests/{unit,integration,e2e,fixtures,reports}
mkdir -p config logs uploads

# 2. 初始化 Git
git init
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
.env
logs/
uploads/
*.log
.pytest_cache/
htmlcov/
.coverage
dist/
build/
*.egg-info/
EOF

# 3. 创建 requirements.txt
cat > requirements.txt << 'EOF'
# Core
playwright==1.40.0
anthropic==0.8.1
pyyaml==6.0.1
pydantic==2.5.0

# API
fastapi==0.104.1
uvicorn==0.24.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-html==4.1.1

# Utils
pillow==10.1.0
python-dotenv==1.0.0
prometheus-client==0.19.0
EOF

# 4. 创建 __init__.py
touch src/__init__.py
touch src/providers/__init__.py
touch src/config/__init__.py
touch src/models/__init__.py
touch src/utils/__init__.py
touch src/api/__init__.py

# 5. 安装依赖
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**验收**:
- [ ] 目录结构正确
- [ ] 依赖安装成功
- [ ] Git 仓库初始化

#### 下午 (4h)
**任务**: 1.2 数据模型定义 (P0, 6h，今天完成 4h，明天继续 2h)

**创建文件**: `src/models.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from pathlib import Path

class SEOData(BaseModel):
    """SEO 数据模型"""
    focus_keyword: str = Field(..., min_length=1, max_length=100)
    meta_title: str = Field(..., min_length=10, max_length=60)
    meta_description: str = Field(..., min_length=50, max_length=160)
    primary_keywords: List[str] = Field(default_factory=list, max_length=5)
    secondary_keywords: List[str] = Field(default_factory=list, max_length=10)

    @field_validator('meta_title')
    @classmethod
    def validate_meta_title_length(cls, v: str) -> str:
        if len(v) < 50 or len(v) > 60:
            raise ValueError('Meta title should be 50-60 characters')
        return v

    @field_validator('meta_description')
    @classmethod
    def validate_meta_description_length(cls, v: str) -> str:
        if len(v) < 150 or len(v) > 160:
            raise ValueError('Meta description should be 150-160 characters')
        return v


class Article(BaseModel):
    """文章数据模型"""
    id: int
    title: str = Field(..., min_length=10, max_length=200)
    content_html: str = Field(..., min_length=100)
    excerpt: Optional[str] = Field(None, max_length=500)
    seo: SEOData

    @field_validator('content_html')
    @classmethod
    def sanitize_html(cls, v: str) -> str:
        # 基础 HTML 清理（可以后续增强）
        import re
        # 移除危险标签
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL)
        v = re.sub(r'<iframe[^>]*>.*?</iframe>', '', v, flags=re.DOTALL)
        # 移除 onclick 等事件属性
        v = re.sub(r'\son\w+="[^"]*"', '', v)
        return v


class ImageAsset(BaseModel):
    """图片资源模型"""
    file_path: str
    alt_text: str = Field(..., min_length=5, max_length=100)
    title: str = Field(..., min_length=1, max_length=100)
    caption: str = Field(default="", max_length=500)
    keywords: List[str] = Field(default_factory=list, max_length=10)
    photographer: str = Field(default="", max_length=100)
    is_featured: bool = False

    @field_validator('file_path')
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        path = Path(v)
        if not path.exists():
            raise ValueError(f'Image file not found: {v}')
        if not path.is_file():
            raise ValueError(f'Path is not a file: {v}')
        # 验证文件类型
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f'Invalid image format: {path.suffix}')
        return v


class ArticleMetadata(BaseModel):
    """文章元数据模型"""
    tags: List[str] = Field(default_factory=list, max_length=10)
    categories: List[str] = Field(default_factory=list, max_length=5)
    publish_immediately: bool = True
    publish_date: Optional[datetime] = None
    status: str = Field(default="draft", pattern="^(draft|publish|scheduled)$")

    @field_validator('publish_date')
    @classmethod
    def validate_publish_date(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and info.data.get('publish_immediately'):
            raise ValueError('Cannot set publish_date when publish_immediately is True')
        if not v and not info.data.get('publish_immediately'):
            raise ValueError('publish_date is required when publish_immediately is False')
        if v and v < datetime.now():
            raise ValueError('publish_date cannot be in the past')
        return v


class WordPressCredentials(BaseModel):
    """WordPress 凭证"""
    username: str = Field(..., min_length=3, max_length=60)
    password: str = Field(..., min_length=8)


class PublishingContext(BaseModel):
    """发布上下文（在整个流程中传递）"""
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
    """发布结果"""
    success: bool
    task_id: str
    url: Optional[str] = None
    audit_trail: Optional[dict] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    provider_used: str = "unknown"  # "playwright" or "computer_use"
    fallback_triggered: bool = False
```

**验收**:
- [ ] 所有模型定义完成
- [ ] 验证规则正确
- [ ] 可以实例化测试

---

### 📅 Day 2 (Tuesday) - 配置系统 + 测试环境

#### 上午 (4h)

**任务 1**: 完成 1.2 数据模型 (剩余 2h)
- 编写单元测试: `tests/unit/test_models.py`
- 测试所有验证规则

**任务 2**: 1.3 配置管理器实现 (P0, 6h，今天开始 2h)

**创建文件**: `src/config/config_manager.py`

```python
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)


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

        logger.info(f"Loaded {len(config_dict)} selectors from {file_path}")
        return cls(config_dict)

    def get(self, key: str, default: Any = None) -> Any:
        """获取选择器配置"""
        return self.config.get(key, default)

    def get_all_selectors(self, key: str) -> List[str]:
        """获取所有备选选择器（支持多选择器）"""
        value = self.get(key)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def validate(self) -> bool:
        """验证配置完整性"""
        required_keys = [
            'new_post_title', 'content_textarea', 'add_media_button',
            'save_draft', 'publish'
        ]
        missing = [key for key in required_keys if key not in self.config]
        if missing:
            raise ValueError(f"Missing required selectors: {missing}")
        return True


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

        logger.info(f"Loaded {len(templates)} instruction templates from {file_path}")
        return cls(templates)

    def get(self, key: str, **kwargs) -> str:
        """获取并渲染指令模板"""
        template = self.templates.get(key)
        if template is None:
            raise KeyError(f'Instruction template not found: {key}')

        # 使用简单的字符串格式化
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f'Missing template variable in "{key}": {e}')

    def validate(self) -> bool:
        """验证模板完整性"""
        required_keys = [
            'navigate_to_new_post', 'fill_title', 'fill_content',
            'open_media_library', 'upload_file'
        ]
        missing = [key for key in required_keys if key not in self.templates]
        if missing:
            raise ValueError(f"Missing required templates: {missing}")
        return True


class PublishingConfig:
    """发布配置"""

    def __init__(self):
        self.max_retries: int = 3
        self.retry_delay: float = 2.0
        self.timeout: int = 30
        self.screenshot_enabled: bool = True
        self.log_level: str = "INFO"
        self.primary_provider: str = "playwright"
        self.fallback_provider: str = "computer_use"

    @classmethod
    def load_from_env(cls) -> 'PublishingConfig':
        """从环境变量加载配置"""
        config = cls()
        config.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        config.retry_delay = float(os.getenv('RETRY_DELAY', '2.0'))
        config.timeout = int(os.getenv('TIMEOUT', '30'))
        config.screenshot_enabled = os.getenv('SCREENSHOT_ENABLED', 'true').lower() == 'true'
        config.log_level = os.getenv('LOG_LEVEL', 'INFO')
        config.primary_provider = os.getenv('PRIMARY_PROVIDER', 'playwright')
        config.fallback_provider = os.getenv('FALLBACK_PROVIDER', 'computer_use')
        return config

    def validate(self) -> bool:
        """验证配置"""
        if self.max_retries < 1 or self.max_retries > 10:
            raise ValueError("max_retries must be between 1 and 10")
        if self.retry_delay < 0 or self.retry_delay > 60:
            raise ValueError("retry_delay must be between 0 and 60")
        if self.timeout < 5 or self.timeout > 300:
            raise ValueError("timeout must be between 5 and 300")
        return True
```

#### 下午 (4h)

**任务**: 1.6 测试环境搭建 (P1, 8h，今天完成全部)

**创建文件**: `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  wordpress-test:
    image: wordpress:6.4-php8.2
    container_name: wordpress-test
    environment:
      WORDPRESS_DB_HOST: mysql-test
      WORDPRESS_DB_USER: wpuser
      WORDPRESS_DB_PASSWORD: wppass123
      WORDPRESS_DB_NAME: wordpress_test
    volumes:
      - wordpress-test-data:/var/www/html
    ports:
      - "8080:80"
    networks:
      - test-network
    depends_on:
      mysql-test:
        condition: service_healthy
    restart: unless-stopped

  mysql-test:
    image: mysql:8.0
    container_name: mysql-test
    environment:
      MYSQL_ROOT_PASSWORD: rootpass123
      MYSQL_DATABASE: wordpress_test
      MYSQL_USER: wpuser
      MYSQL_PASSWORD: wppass123
    volumes:
      - mysql-test-data:/var/lib/mysql
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

networks:
  test-network:
    driver: bridge

volumes:
  wordpress-test-data:
  mysql-test-data:
```

**创建文件**: `tests/fixtures/init-wordpress.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Initializing WordPress test environment..."

# 等待 WordPress 启动
echo "⏳ Waiting for WordPress to start..."
sleep 15

# 检查 WordPress 是否可访问
until curl -f http://localhost:8080 > /dev/null 2>&1; do
    echo "   Still waiting..."
    sleep 5
done

echo "✅ WordPress is running"

# 安装 WP-CLI
echo "📦 Installing WP-CLI..."
docker exec wordpress-test bash -c "
    curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && \
    chmod +x wp-cli.phar && \
    mv wp-cli.phar /usr/local/bin/wp
"

# 安装 WordPress
echo "🔧 Installing WordPress..."
docker exec wordpress-test wp core install \
    --url=http://localhost:8080 \
    --title="WordPress Test Site" \
    --admin_user=testadmin \
    --admin_password=testpass123 \
    --admin_email=test@example.com \
    --allow-root

# 安装必需插件
echo "🔌 Installing plugins..."
docker exec wordpress-test wp plugin install classic-editor --activate --allow-root
docker exec wordpress-test wp plugin install wordpress-seo --activate --allow-root

# 安装主题
echo "🎨 Installing theme..."
docker exec wordpress-test wp theme install astra --activate --allow-root

# 创建测试分类
echo "📁 Creating test categories..."
docker exec wordpress-test wp term create category "技术" --allow-root
docker exec wordpress-test wp term create category "教程" --allow-root
docker exec wordpress-test wp term create category "测试" --allow-root

# 配置 Yoast SEO
echo "⚙️  Configuring Yoast SEO..."
docker exec wordpress-test wp option update wpseo_titles '{"title-post":"%%title%% %%sep%% %%sitename%%"}' --format=json --allow-root

echo "✅ WordPress test environment initialized successfully!"
echo ""
echo "📝 Access details:"
echo "   URL: http://localhost:8080"
echo "   Admin: http://localhost:8080/wp-admin"
echo "   Username: testadmin"
echo "   Password: testpass123"
```

**执行**:
```bash
chmod +x tests/fixtures/init-wordpress.sh
docker-compose -f docker-compose.test.yml up -d
./tests/fixtures/init-wordpress.sh
```

**验收**:
- [ ] WordPress 可访问
- [ ] 能登录后台
- [ ] Classic Editor 已激活
- [ ] Yoast SEO 已激活

---

### 📅 Day 3 (Wednesday) - 完成配置 + Provider 接口

#### 上午 (4h)

**任务 1**: 完成 1.3 配置管理器 (剩余 4h)
- 编写单元测试: `tests/unit/test_config_manager.py`
- 测试加载和验证功能

**任务 2**: 1.4 Provider 接口定义 (P0, 4h)

**创建文件**: `src/providers/base_provider.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime


class IPublishingProvider(ABC):
    """
    发布提供者的抽象接口
    所有 Provider（Playwright、Computer Use）必须实现此接口
    """

    @abstractmethod
    async def initialize(self, base_url: str, **kwargs) -> None:
        """
        初始化 Provider（启动浏览器、连接服务等）

        Args:
            base_url: WordPress 站点 URL
            **kwargs: 额外参数（如 cookies）
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭 Provider 并释放资源"""
        pass

    @abstractmethod
    async def capture_screenshot(self) -> bytes:
        """
        捕获当前屏幕截图

        Returns:
            PNG 格式的截图字节
        """
        pass

    @abstractmethod
    async def get_cookies(self) -> List[Dict]:
        """
        获取当前浏览器 cookies

        Returns:
            Cookie 字典列表
        """
        pass

    # ==================== 导航类操作 ====================

    @abstractmethod
    async def navigate_to(self, url: str) -> None:
        """导航到指定 URL"""
        pass

    @abstractmethod
    async def navigate_to_new_post(self) -> None:
        """导航到「新增文章」页面"""
        pass

    # ==================== 元素交互操作 ====================

    @abstractmethod
    async def fill_input(self, field_name: str, value: str) -> None:
        """
        填充输入框

        Args:
            field_name: 字段名称（如 "title", "username"）
            value: 要填充的值
        """
        pass

    @abstractmethod
    async def fill_textarea(self, field_name: str, value: str) -> None:
        """填充文本区域（如文章内容）"""
        pass

    @abstractmethod
    async def click_button(self, button_name: str) -> None:
        """点击按钮（如 "save_draft", "publish"）"""
        pass

    @abstractmethod
    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """等待元素出现"""
        pass

    @abstractmethod
    async def wait_for_success_message(self, message_text: str) -> None:
        """等待成功提示消息出现"""
        pass

    # ==================== 内容编辑操作 ====================

    @abstractmethod
    async def clean_html_entities(self) -> None:
        """清理内容中的 HTML 实体（如 &nbsp;）"""
        pass

    # ==================== 媒体库操作 ====================

    @abstractmethod
    async def open_media_library(self) -> None:
        """打开媒体库弹窗"""
        pass

    @abstractmethod
    async def upload_file(self, file_path: str) -> None:
        """上传文件"""
        pass

    @abstractmethod
    async def wait_for_upload_complete(self) -> None:
        """等待文件上传完成"""
        pass

    @abstractmethod
    async def fill_image_metadata(self, metadata: Dict[str, str]) -> None:
        """
        填写图片元数据

        Args:
            metadata: {
                "alt": "替代文字",
                "title": "图片标题",
                "caption": "图片说明",
                "keywords": "关键字1,关键字2",
                "photographer": "摄影师"
            }
        """
        pass

    @abstractmethod
    async def configure_image_display(
        self,
        align: str,
        link_to: str,
        size: str
    ) -> None:
        """
        配置图片显示设置

        Args:
            align: 对齐方式（"none", "left", "center", "right"）
            link_to: 连结至（"none", "media", "attachment", "custom"）
            size: 尺寸（"thumbnail", "medium", "large", "full"）
        """
        pass

    @abstractmethod
    async def insert_image_to_content(self) -> None:
        """将图片插入到文章内容"""
        pass

    @abstractmethod
    async def close_media_library(self) -> None:
        """关闭媒体库弹窗"""
        pass

    # ==================== 特色图片操作 ====================

    @abstractmethod
    async def set_as_featured_image(self) -> None:
        """将当前选中的图片设为特色图片"""
        pass

    @abstractmethod
    async def edit_image(self) -> None:
        """进入图片编辑模式"""
        pass

    @abstractmethod
    async def crop_image(self, size_name: str) -> None:
        """
        裁切图片到指定尺寸

        Args:
            size_name: 尺寸名称（如 "thumbnail", "facebook_700_359"）
        """
        pass

    @abstractmethod
    async def save_crop(self) -> None:
        """保存裁切"""
        pass

    @abstractmethod
    async def confirm_featured_image(self) -> None:
        """确认设置特色图片"""
        pass

    # ==================== 元数据操作 ====================

    @abstractmethod
    async def add_tag(self, tag: str) -> None:
        """添加标签"""
        pass

    @abstractmethod
    async def select_category(self, category: str) -> None:
        """选择分类"""
        pass

    @abstractmethod
    async def configure_seo_plugin(self, seo_data: Dict[str, str]) -> None:
        """
        配置 SEO 插件

        Args:
            seo_data: {
                "focus_keyword": "焦点关键字",
                "meta_title": "SEO 标题",
                "meta_description": "Meta 描述"
            }
        """
        pass

    # ==================== 发布操作 ====================

    @abstractmethod
    async def schedule_publish(self, publish_date: datetime) -> None:
        """设置排程发布时间"""
        pass

    @abstractmethod
    async def get_published_url(self) -> str:
        """获取已发布文章的 URL"""
        pass
```

#### 下午 (4h)

**任务 1**: 1.5 日志系统实现 (P1, 4h)

**创建文件**: `src/utils/audit_logger.py`

```python
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def log_phase_success(self, task_id: str, phase_name: str, retry_count: int) -> None:
        """记录阶段成功"""
        self._write_log(task_id, {
            "event": "phase_success",
            "phase": phase_name,
            "retry_count": retry_count,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.info(f"[{task_id}] Phase '{phase_name}' completed (retries: {retry_count})")

    def log_phase_failure(
        self,
        task_id: str,
        phase_name: str,
        retry_count: int,
        error: str
    ) -> None:
        """记录阶段失败"""
        self._write_log(task_id, {
            "event": "phase_failure",
            "phase": phase_name,
            "retry_count": retry_count,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.warning(f"[{task_id}] Phase '{phase_name}' failed (retry {retry_count}): {error}")

    def log_provider_switch(self, task_id: str, new_provider: str) -> None:
        """记录 Provider 切换"""
        self._write_log(task_id, {
            "event": "provider_switch",
            "new_provider": new_provider,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.warning(f"[{task_id}] Switched to provider: {new_provider}")

    def save_screenshot(self, task_id: str, step_name: str, screenshot: bytes) -> str:
        """
        保存截图

        Returns:
            截图文件路径
        """
        task_log_dir = self.log_dir / task_id
        task_log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        screenshot_path = task_log_dir / f"{timestamp}_{step_name}.png"
        screenshot_path.write_bytes(screenshot)

        self._write_log(task_id, {
            "event": "screenshot_saved",
            "step_name": step_name,
            "path": str(screenshot_path),
            "size_bytes": len(screenshot),
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.debug(f"[{task_id}] Screenshot saved: {screenshot_path.name}")
        return str(screenshot_path)

    def log_failure(self, task_id: str, error: str) -> None:
        """记录任务失败"""
        self._write_log(task_id, {
            "event": "task_failed",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.error(f"[{task_id}] Task failed: {error}")

    def get_trail(self, task_id: str) -> Dict[str, Any]:
        """
        获取完整审计追踪

        Returns:
            包含所有事件和摘要的字典
        """
        log_file = self.log_dir / task_id / "audit.jsonl"
        if not log_file.exists():
            return {"task_id": task_id, "events": [], "summary": {}}

        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse log line: {line}")

        return {
            "task_id": task_id,
            "events": logs,
            "summary": self._generate_summary(logs)
        }

    def _write_log(self, task_id: str, log_entry: Dict[str, Any]) -> None:
        """写入日志到 JSONL 文件"""
        task_log_dir = self.log_dir / task_id
        task_log_dir.mkdir(parents=True, exist_ok=True)

        log_file = task_log_dir / "audit.jsonl"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def _generate_summary(self, logs: List[Dict]) -> Dict[str, Any]:
        """生成日志摘要"""
        success_phases = [log for log in logs if log.get('event') == 'phase_success']
        failures = [log for log in logs if log.get('event') == 'phase_failure']
        screenshots = [log for log in logs if log.get('event') == 'screenshot_saved']
        provider_switches = [log for log in logs if log.get('event') == 'provider_switch']

        return {
            "total_phases": len(success_phases),
            "failures": len(failures),
            "screenshots": len(screenshots),
            "provider_switches": len(provider_switches),
            "total_events": len(logs)
        }
```

**验收**:
- [ ] 能记录各类事件
- [ ] 能保存截图
- [ ] 能生成摘要

---

### 📅 Day 4-5 (Thursday-Friday) - 选择器配置

#### Day 4 上午 (4h)

**任务**: 1.7 选择器配置文件编写 (P1, 6h，第 1 部分)

**活动**:
1. 使用 Playwright Inspector 探索 WordPress 后台
   ```bash
   playwright codegen http://localhost:8080/wp-admin
   ```

2. 记录所有关键元素的选择器

**创建文件**: `config/selectors.yaml` (部分)

```yaml
# WordPress 后台选择器配置 (繁体中文界面)

# ==================== 登录 ====================
login_username:
  - "#user_login"
  - "input[name='log']"

login_password:
  - "#user_pass"
  - "input[name='pwd']"

login_button:
  - "#wp-submit"
  - "input[type='submit']"

dashboard:
  - "#dashboard-widgets"
  - "#wpbody-content"

# ==================== 菜单导航 ====================
menu_posts:
  - "#menu-posts > a"
  - "a[href='edit.php']"

menu_new_post:
  - "#menu-posts ul > li > a:has-text('新增文章')"
  - "a[href='post-new.php']"

# ==================== 文章编辑器 ====================
new_post_title:
  - "#title"
  - "input[name='post_title']"

content_text_mode_button:
  - "#content-html"
  - "a.wp-switch-editor[data-mode='html']"

content_visual_mode_button:
  - "#content-tmce"
  - "a.wp-switch-editor[data-mode='tmce']"

content_textarea:
  - "#content"
  - "textarea[name='content']"

content_iframe:
  - "#content_ifr"
  - "iframe.wp-editor-area"

# ==================== 按钮 ====================
save_draft:
  - "#save-post"
  - "input[name='save']"

publish:
  - "#publish"
  - "input[name='publish']"

preview:
  - "#post-preview"
  - "a#preview-action"

# ==================== 媒体库 ====================
add_media_button:
  - "#insert-media-button"
  - "button.insert-media"

media_modal:
  - ".media-modal"
  - ".media-frame"

upload_files_tab:
  - "button:has-text('上傳檔案')"
  - ".media-menu-item:nth-child(1)"

select_files_button:
  - "button:has-text('選擇檔案')"
  - ".browser button.button"

media_attachment:
  - ".media-modal .attachment"
  - "li.attachment"

attachment_details:
  - ".media-sidebar"
  - ".attachment-details"

# 图片元数据字段
image_alt:
  - ".media-modal .setting[data-setting='alt'] input"
  - "input[aria-describedby='alt-text-description']"

image_title:
  - ".media-modal .setting[data-setting='title'] input"
  - "input[data-setting='title']"

image_caption:
  - ".media-modal .setting[data-setting='caption'] textarea"
  - "textarea[data-setting='caption']"

# ... (更多选择器在 Day 5 继续添加)
```

#### Day 4 下午 + Day 5 (4h + 8h)

**继续任务**: 完成所有选择器配置
- 标签、分类、SEO 插件
- 特色图片、图片编辑
- 发布设置

**创建文件**: `config/instructions.yaml` (Computer Use 指令)

```yaml
# Computer Use 自然语言指令模板 (繁体中文)

navigate_to_new_post: |
  找到左側選單中帶有圖釘圖示且標籤為『文章』的項目，點擊它。
  在展開的子選單中，找到並點擊標籤為『新增文章』的連結。
  等待頁面載入完成，確認頁面頂部出現文字『新增文章』。

fill_title: |
  找到標籤為『新增標題』或 ID 為 'title' 的大型文字輸入框。
  在此輸入框中輸入以下文字：『{value}』。
  確認輸入框中已顯示輸入的標題文字。

fill_content: |
  找到主要內容編輯器右上方的『文字』(Text) 分頁標籤，點擊它。
  在主要內容編輯器的大型文字區域中，貼上以下內容：
  ---
  {content}
  ---
  確認文字區域中已顯示貼上的內容。

# ... (更多指令)
```

**验收**:
- [ ] 所有关键元素都有选择器
- [ ] 每个选择器至少 2 个备选
- [ ] Computer Use 指令完整

---

### Sprint 1 验收标准

**完成的任务**:
- [x] 1.1 项目结构初始化 (P0)
- [x] 1.2 数据模型定义 (P0)
- [x] 1.3 配置管理器实现 (P0)
- [x] 1.4 Provider 接口定义 (P0)
- [x] 1.5 日志系统实现 (P1)
- [x] 1.6 测试环境搭建 (P1)
- [x] 1.7 选择器配置文件 (P1)
- [x] 1.8 Computer Use 指令模板 (P1，部分完成)

**交付物检查**:
- [ ] ✅ 项目结构完整，依赖安装成功
- [ ] ✅ 所有核心模型定义并通过单元测试
- [ ] ✅ 配置系统可正常加载
- [ ] ✅ Provider 接口清晰完整
- [ ] ✅ WordPress 测试环境可访问
- [ ] ✅ 选择器配置覆盖主要元素
- [ ] ✅ Git 提交记录清晰

**下周准备**:
- [ ] 复查选择器准确性
- [ ] 准备测试图片素材
- [ ] 熟悉 Playwright API

---

## 🏃 Sprint 2: Playwright 核心实现 (Week 2-3)

**时间**: 2025-11-11 ~ 2025-11-22 (2 周)
**目标**: 完成 Playwright Provider 所有功能，实现 MVP
**团队**: 1 后端开发

### Sprint 目标
✅ Playwright Provider 完整实现
✅ 能发布完整文章（文本 + 图片 + SEO）
✅ 核心流程集成测试通过
✅ MVP 可演示

---

### Week 2 Day 1 (Monday) - Playwright 基础方法

**任务**: 2.1 Playwright Provider - 基础方法 (P0, 12h，分 2 天完成)

**创建文件**: `src/providers/playwright_provider.py`

**今日目标** (6h):
- 实现初始化和关闭
- 实现导航方法
- 实现基础元素交互

**核心代码框架**:
```python
from playwright.async_api import async_playwright, Page, Browser, Playwright
from typing import Optional, List, Dict
from src.providers.base_provider import IPublishingProvider
from src.config.config_manager import SelectorConfig
import asyncio
import logging

logger = logging.getLogger(__name__)


class PlaywrightProvider(IPublishingProvider):
    """基于 Playwright 的发布提供者"""

    def __init__(self, selectors: SelectorConfig):
        self.selectors = selectors
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        self.base_url: str = ""

    async def initialize(self, base_url: str, **kwargs) -> None:
        """初始化浏览器"""
        logger.info("Initializing Playwright provider")

        self.playwright = await async_playwright().start()

        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # 创建上下文
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-TW',
            timezone_id='Asia/Taipei'
        )

        # 如果提供了 cookies，恢复会话
        if 'cookies' in kwargs:
            await context.add_cookies(kwargs['cookies'])
            logger.info("Restored browser cookies")

        self.page = await context.new_page()
        self.page.set_default_timeout(30000)
        self.base_url = base_url

        logger.info(f"Playwright initialized with base URL: {base_url}")

    async def close(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
        if self.playwright:
            await self.playwright.stop()

    async def capture_screenshot(self) -> bytes:
        """捕获截图"""
        if not self.page:
            raise RuntimeError("Page not initialized")
        screenshot = await self.page.screenshot(full_page=True)
        logger.debug(f"Screenshot captured ({len(screenshot)} bytes)")
        return screenshot

    async def get_cookies(self) -> List[Dict]:
        """获取 cookies"""
        if not self.page:
            raise RuntimeError("Page not initialized")
        return await self.page.context.cookies()

    # 导航方法
    async def navigate_to(self, url: str) -> None:
        """导航到 URL"""
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, wait_until='networkidle')

    async def navigate_to_new_post(self) -> None:
        """导航到新增文章"""
        logger.info("Navigating to new post page")
        await self.navigate_to(f"{self.base_url}/wp-admin/post-new.php")
        await self.wait_for_element("new_post_title")

    # 元素交互方法
    async def fill_input(self, field_name: str, value: str) -> None:
        """填充输入框"""
        logger.info(f"Filling input '{field_name}' with value")
        selector = self.selectors.get(field_name)
        await self._fill_by_selector(selector, value)

    async def click_button(self, button_name: str) -> None:
        """点击按钮"""
        logger.info(f"Clicking button '{button_name}'")
        selector = self.selectors.get(button_name)
        await self._click_by_selector(selector)

    async def wait_for_element(self, element_name: str, timeout: int = 30) -> None:
        """等待元素"""
        logger.debug(f"Waiting for element '{element_name}'")
        selector = self.selectors.get(element_name)
        await self.page.wait_for_selector(selector, timeout=timeout * 1000)

    # 辅助方法
    async def _click_by_selector(self, selector: str) -> None:
        """通过选择器点击（支持多选择器）"""
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                if await element.is_visible(timeout=5000):
                    await element.click()
                    logger.debug(f"Clicked element with selector: {sel}")
                    return
            except Exception as e:
                logger.debug(f"Selector '{sel}' failed: {e}")
                continue

        raise ElementNotFoundError(f"Could not find clickable element with selectors: {selectors}")

    async def _fill_by_selector(self, selector: str, value: str) -> None:
        """通过选择器填充（支持多选择器）"""
        selectors = selector if isinstance(selector, list) else [selector]

        for sel in selectors:
            try:
                element = self.page.locator(sel).first
                if await element.is_visible(timeout=5000):
                    await element.fill(value)
                    logger.debug(f"Filled element with selector: {sel}")
                    return
            except Exception as e:
                logger.debug(f"Selector '{sel}' failed: {e}")
                continue

        raise ElementNotFoundError(f"Could not find fillable element with selectors: {selectors}")


class ElementNotFoundError(Exception):
    """元素未找到错误"""
    pass
```

**单元测试**: `tests/unit/test_playwright_provider.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.providers.playwright_provider import PlaywrightProvider, ElementNotFoundError

@pytest.fixture
def mock_page():
    page = Mock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.locator = Mock(return_value=Mock(
        fill=AsyncMock(),
        click=AsyncMock(),
        is_visible=AsyncMock(return_value=True),
        first=Mock()
    ))
    page.screenshot = AsyncMock(return_value=b'fake_screenshot')
    return page

@pytest.fixture
def selector_config():
    config = Mock()
    config.get = Mock(return_value="#test-selector")
    return config

@pytest.fixture
def provider(mock_page, selector_config):
    provider = PlaywrightProvider(selector_config)
    provider.page = mock_page
    provider.base_url = "http://test.example.com"
    return provider

@pytest.mark.asyncio
async def test_navigate_to(provider, mock_page):
    """测试导航"""
    await provider.navigate_to("http://test.example.com/page")
    mock_page.goto.assert_called_once()

@pytest.mark.asyncio
async def test_fill_input_success(provider, mock_page):
    """测试填充输入框"""
    await provider.fill_input("title", "测试标题")
    mock_page.locator.assert_called()
```

**验收**:
- [ ] 浏览器能正常启动和关闭
- [ ] 能导航到 WordPress 后台
- [ ] 能填充输入框和点击按钮
- [ ] 单元测试通过

---

### Week 2 Day 2-5 + Week 3 Day 1-3

继续实现剩余的 Playwright Provider 方法：

**Day 2 下午 + Day 3** (12h):
- 2.2 内容编辑功能 (8h)
- 2.3 媒体库功能开始 (4h)

**Day 4-5** (16h):
- 完成 2.3 媒体库功能 (8h)
- 2.4 特色图片功能 (8h)

**Week 3 Day 1** (8h):
- 完成 2.4 特色图片 (2h)
- 2.5 元数据功能 (6h)

**Week 3 Day 2** (8h):
- 完成 2.5 元数据 (2h)
- 2.6 发布功能 (6h)

**Week 3 Day 3** (8h):
- 2.9 Orchestrator 开始 (8h)

*(详细代码实现参考 plan.md，这里省略以节省篇幅)*

---

### Week 3 Day 4-5 (Thursday-Friday) - Orchestrator 完成

**任务**: 完成 2.9 Publishing Orchestrator (P0, 剩余 8h)

**创建文件**: `src/orchestrator.py`

**核心实现**: 5 个阶段的流程编排

```python
class PublishingOrchestrator:
    """发布协调器"""

    def __init__(
        self,
        primary_provider: IPublishingProvider,
        fallback_provider: Optional[IPublishingProvider] = None,
        config: Optional[PublishingConfig] = None
    ):
        self.primary = primary_provider
        self.fallback = fallback_provider
        self.config = config or PublishingConfig.load_from_env()
        self.audit_logger = AuditLogger()
        self.current_provider = primary_provider

    async def publish_article(
        self,
        article: Article,
        images: List[ImageAsset],
        metadata: ArticleMetadata,
        credentials: WordPressCredentials,
        wordpress_url: str
    ) -> PublishResult:
        """发布文章主入口"""
        task_id = self._generate_task_id()
        start_time = datetime.now()

        context = PublishingContext(
            task_id=task_id,
            article=article,
            images=images,
            metadata=metadata,
            wordpress_url=wordpress_url,
            credentials=credentials
        )

        try:
            # 初始化 Provider
            await self.current_provider.initialize(wordpress_url)

            # 阶段一：登录
            await self._execute_phase("login", self._phase_login, context)

            # 阶段二：填充内容
            await self._execute_phase("content", self._phase_fill_content, context)

            # 阶段三：处理图片
            await self._execute_phase("images", self._phase_process_images, context)

            # 阶段四：设置元数据
            await self._execute_phase("metadata", self._phase_set_metadata, context)

            # 阶段五：发布
            await self._execute_phase("publish", self._phase_publish, context)

            duration = (datetime.now() - start_time).total_seconds()

            return PublishResult(
                success=True,
                task_id=task_id,
                url=context.published_url,
                audit_trail=self.audit_logger.get_trail(task_id),
                duration_seconds=duration,
                provider_used=self.current_provider.__class__.__name__
            )

        except Exception as e:
            logger.error(f"Publishing failed: {e}")
            self.audit_logger.log_failure(task_id, str(e))
            raise
        finally:
            await self.current_provider.close()

    async def _execute_phase(self, phase_name: str, phase_func, context):
        """执行单个阶段（带重试）"""
        # 实现重试逻辑
        # ... (参考 plan.md)

    async def _phase_login(self, provider, context):
        """登录阶段"""
        await provider.navigate_to(f"{context.wordpress_url}/wp-admin")
        await provider.fill_input("login_username", context.credentials.username)
        await provider.fill_input("login_password", context.credentials.password)
        await provider.click_button("login_button")
        await provider.wait_for_element("dashboard")
        context.browser_cookies = await provider.get_cookies()

    # ... 其他阶段实现
```

**集成测试**: `tests/integration/test_publishing_workflow.py`

```python
@pytest.mark.integration
class TestPublishingWorkflow:
    @pytest.mark.asyncio
    async def test_full_workflow_playwright(self):
        """测试完整发布流程"""
        # 准备测试数据
        article = Article(...)
        images = [ImageAsset(...)]
        metadata = ArticleMetadata(...)

        # 创建 Orchestrator
        selector_config = SelectorConfig.load_from_file("config/selectors.yaml")
        playwright_provider = PlaywrightProvider(selector_config)
        orchestrator = PublishingOrchestrator(playwright_provider)

        # 执行发布
        result = await orchestrator.publish_article(
            article, images, metadata,
            credentials=WordPressCredentials(username="testadmin", password="testpass123"),
            wordpress_url="http://localhost:8080"
        )

        # 验证
        assert result.success == True
        assert result.url is not None
        assert "localhost:8080" in result.url
```

**验收**:
- [ ] 能完整执行 5 个阶段
- [ ] 集成测试通过
- [ ] 审计日志完整
- [ ] 能成功发布到测试 WordPress

---

### Sprint 2 验收标准

**完成的任务**:
- [x] 2.1 Playwright Provider - 基础方法 (P0)
- [x] 2.2 Playwright Provider - 内容编辑 (P0)
- [x] 2.3 Playwright Provider - 媒体库 (P0)
- [x] 2.4 Playwright Provider - 特色图片 (P0)
- [x] 2.5 Playwright Provider - 元数据 (P0)
- [x] 2.6 Playwright Provider - 发布 (P0)
- [x] 2.9 Publishing Orchestrator (P0)

**MVP 演示检查**:
- [ ] ✅ 能发布完整文章（标题 + 内容）
- [ ] ✅ 能上传图片并填写元数据
- [ ] ✅ 能设置特色图片
- [ ] ✅ 能配置标签、分类
- [ ] ✅ 能配置 Yoast SEO
- [ ] ✅ 能获取发布后的 URL
- [ ] ✅ 集成测试通过率 ≥ 90%

**里程碑**: 🎉 **MVP 完成！**

---

## 🏃 Sprint 3: Computer Use + 降级机制 (Week 3-4)

**时间**: 2025-11-25 ~ 2025-11-29 (1 周)
**目标**: 实现 Computer Use 和降级机制
**团队**: 1 后端开发

### Sprint 目标
✅ Computer Use Provider 完整实现
✅ 降级机制正常工作
✅ 错误恢复机制完成
✅ REST API 基础实现

---

### Week 4 Day 1-2 (Monday-Tuesday) - Computer Use Provider

**任务**: 2.7-2.8 Computer Use Provider (P1, 22h，分 3 天)

**创建文件**: `src/providers/computer_use_provider.py`

```python
import anthropic
from src.providers.base_provider import IPublishingProvider
from src.config.config_manager import InstructionTemplate

class ComputerUseProvider(IPublishingProvider):
    """基于 Anthropic Computer Use 的提供者"""

    def __init__(self, api_key: str, instructions: InstructionTemplate):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.instructions = instructions
        self.conversation_history = []

    async def initialize(self, base_url: str, **kwargs) -> None:
        self.base_url = base_url
        self.session_id = self._generate_session_id()

    async def _execute_instruction(self, instruction: str):
        """执行 Computer Use 指令"""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=[{
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": 1920,
                "display_height_px": 1080,
            }],
            messages=self.conversation_history + [{
                "role": "user",
                "content": instruction
            }]
        )

        # 处理响应
        # ... (实现细节参考 plan.md)

    # 实现所有 IPublishingProvider 接口
    async def fill_input(self, field_name: str, value: str) -> None:
        instruction = self.instructions.get(f"fill_{field_name}", value=value)
        await self._execute_instruction(instruction)

    # ... 其他方法
```

**验收**:
- [ ] 能成功调用 Anthropic API
- [ ] 能执行基础指令
- [ ] 对话历史管理正确

---

### Week 4 Day 3 (Wednesday) - 降级机制

**任务**: 2.10 降级机制实现 (P0, 8h)

**在 `src/orchestrator.py` 中添加**:

```python
async def _execute_phase(self, phase_name: str, phase_func, context):
    """执行阶段（带降级）"""
    max_retries = self.config.max_retries
    retry_count = 0

    while retry_count < max_retries:
        try:
            # 截图前
            screenshot_before = await self.current_provider.capture_screenshot()
            self.audit_logger.save_screenshot(context.task_id, f"{phase_name}_before", screenshot_before)

            # 执行阶段
            await phase_func(self.current_provider, context)

            # 截图后
            screenshot_after = await self.current_provider.capture_screenshot()
            self.audit_logger.save_screenshot(context.task_id, f"{phase_name}_after", screenshot_after)

            self.audit_logger.log_phase_success(context.task_id, phase_name, retry_count)
            return

        except (ElementNotFoundError, TimeoutError) as e:
            retry_count += 1
            self.audit_logger.log_phase_failure(context.task_id, phase_name, retry_count, str(e))

            if retry_count >= max_retries:
                # 降级到 Computer Use
                if self.fallback and self.current_provider != self.fallback:
                    logger.warning(f"Falling back to {self.fallback.__class__.__name__}")
                    await self._switch_to_fallback(context)
                    retry_count = 0  # 重置计数
                else:
                    raise

            await asyncio.sleep(self.config.retry_delay)

async def _switch_to_fallback(self, context):
    """切换到备用 Provider"""
    await self.current_provider.close()
    self.current_provider = self.fallback
    await self.current_provider.initialize(
        context.wordpress_url,
        cookies=context.browser_cookies
    )
    self.audit_logger.log_provider_switch(context.task_id, "computer_use")
```

**降级测试**: `tests/integration/test_fallback.py`

```python
@pytest.mark.asyncio
async def test_fallback_triggered():
    """测试降级触发"""
    # Mock Playwright 连续失败
    playwright_mock = Mock()
    playwright_mock.fill_input = AsyncMock(side_effect=ElementNotFoundError("失败"))

    # Computer Use 成功
    computer_use_mock = Mock()
    computer_use_mock.fill_input = AsyncMock()

    orchestrator = PublishingOrchestrator(
        primary_provider=playwright_mock,
        fallback_provider=computer_use_mock
    )

    # 执行会触发降级
    # ...

    # 验证切换
    assert orchestrator.current_provider == computer_use_mock
```

---

### Week 4 Day 4 (Thursday) - 错误恢复 + API

**任务 1**: 3.7 错误恢复机制 (P1, 8h，今天 4h)

**创建文件**: `src/utils/task_state.py`

```python
import json
from pathlib import Path
from typing import Dict, Any

class TaskStateManager:
    """任务状态管理器"""

    def __init__(self, state_dir: str = "logs"):
        self.state_dir = Path(state_dir)

    def save_state(self, task_id: str, phase: str, context: Dict[str, Any]):
        """保存任务状态"""
        state_file = self.state_dir / task_id / "state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "task_id": task_id,
            "current_phase": phase,
            "completed_phases": context.get("completed_phases", []),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, task_id: str) -> Dict[str, Any]:
        """加载任务状态"""
        state_file = self.state_dir / task_id / "state.json"
        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            return json.load(f)

    async def resume_task(self, task_id: str, orchestrator):
        """恢复任务"""
        state = self.load_state(task_id)
        if not state:
            raise ValueError(f"No state found for task {task_id}")

        # 跳过已完成的阶段，从失败点继续
        # ... 实现
```

**任务 2**: 3.8 API 服务实现 (P1, 10h，今天开始 4h)

**创建文件**: `src/api/main.py`

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from src.models import Article, ImageAsset, ArticleMetadata
from src.orchestrator import PublishingOrchestrator
import uuid

app = FastAPI(title="WordPress Publishing API", version="1.0.0")

tasks_db = {}  # 简化版，生产应使用数据库

@app.post("/publish")
async def publish_article(
    article: Article,
    images: list[ImageAsset],
    metadata: ArticleMetadata,
    wordpress_url: str,
    username: str,
    password: str,
    background_tasks: BackgroundTasks
):
    """发布文章（异步）"""
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "pending", "progress": 0}

    background_tasks.add_task(
        run_publishing_task,
        task_id, article, images, metadata,
        wordpress_url, username, password
    )

    return {"task_id": task_id, "status": "pending"}

async def run_publishing_task(task_id, article, images, metadata, wordpress_url, username, password):
    """后台任务"""
    try:
        tasks_db[task_id]["status"] = "running"

        # 创建 Orchestrator
        # ...

        result = await orchestrator.publish_article(...)

        tasks_db[task_id] = {
            "status": "completed" if result.success else "failed",
            "result": result.dict()
        }
    except Exception as e:
        tasks_db[task_id] = {"status": "failed", "error": str(e)}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

**启动服务**:
```bash
uvicorn src.api.main:app --reload
```

---

### Week 4 Day 5 (Friday) - 完成 API + 图片处理

**任务 1**: 完成 3.8 API (剩余 6h，上午)
- `/tasks/{task_id}/logs` 接口
- OpenAPI 文档完善
- API 测试

**任务 2**: 3.1 图片预处理 (P1, 6h，下午)

**创建文件**: `src/utils/image_processor.py`

```python
from PIL import Image
from pathlib import Path

def optimize_image(image_path: str, max_size_mb: float = 2.0) -> str:
    """优化图片大小"""
    img = Image.open(image_path)

    # 转换为 RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        img = background

    output_path = f"/tmp/{Path(image_path).stem}_optimized.jpg"
    quality = 85

    while quality >= 50:
        img.save(output_path, format="JPEG", quality=quality, optimize=True)
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)

        if size_mb <= max_size_mb:
            break

        quality -= 5

    return output_path
```

---

### Sprint 3 验收标准

**完成的任务**:
- [x] 2.7 Computer Use Provider - 基础 (P1)
- [x] 2.8 Computer Use Provider - 接口 (P1)
- [x] 2.10 降级机制 (P0)
- [x] 3.7 错误恢复机制 (P1)
- [x] 3.8 API 服务 (P1)
- [x] 3.1 图片预处理 (P1)

**验收检查**:
- [ ] ✅ Computer Use 能成功发布文章
- [ ] ✅ Playwright 失败能自动降级
- [ ] ✅ Cookies 正确传递
- [ ] ✅ 任务中断能恢复
- [ ] ✅ REST API 正常工作
- [ ] ✅ 图片自动压缩

**里程碑**: 🎉 **生产版核心功能完成！**

---

## 🏃 Sprint 4: 测试与优化 (Week 4-5)

**时间**: 2025-12-02 ~ 2025-12-06 (1 周)
**目标**: 完善测试、性能优化、质量保障
**团队**: 1 后端开发 + 0.5 测试工程师

### Sprint 目标
✅ 单元测试覆盖率 ≥ 85%
✅ 集成测试和 E2E 测试完整
✅ 性能优化达标
✅ 生产可用

---

### Week 5 Day 1-2 (Monday-Tuesday) - 测试完善

**Day 1 任务**: 4.1 单元测试完善 (P0, 12h，今天 8h)
- 完善所有 Provider 的单元测试
- 完善 Orchestrator 的单元测试
- 边界情况测试

**Day 2 任务**:
- 完成 4.1 单元测试 (4h)
- 4.2 集成测试开发 (P0, 10h，今天开始 4h)

**运行测试**:
```bash
# 单元测试
pytest tests/unit/ -v --cov=src --cov-report=html

# 目标: 覆盖率 ≥ 85%
```

---

### Week 5 Day 3 (Wednesday) - E2E 测试

**任务**: 4.3 E2E 测试开发 (P0, 12h，今天 8h)

**创建文件**: `tests/e2e/test_end_to_end.py`

```python
@pytest.mark.e2e
class TestEndToEndPublishing:
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """完整发布流程测试"""
        # 准备完整的测试数据
        article = Article(
            id=1,
            title=f"E2E 测试 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
            content_html="<p>测试内容</p><h2>小标题</h2><p>更多内容</p>",
            excerpt="测试摘要",
            seo=SEOData(
                focus_keyword="E2E测试",
                meta_title="E2E 测试文章标题（50-60字符之间的完整标题）",
                meta_description="这是一篇用于 End-to-End 测试的文章，验证完整的自动化发布流程，包括文本、图片、SEO等所有功能。（150-160字符）"
            )
        )

        images = [ImageAsset(...)]  # 真实图片
        metadata = ArticleMetadata(
            tags=["E2E", "测试", "自动化"],
            categories=["技术"],
            publish_immediately=True
        )

        # 执行发布
        orchestrator = PublishingOrchestrator(...)
        result = await orchestrator.publish_article(...)

        # 验证结果
        assert result.success == True
        assert result.url is not None

        # 验证文章可访问
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(result.url)
            assert response.status_code == 200
            assert article.title in response.text
```

---

### Week 5 Day 4 (Thursday) - 性能优化

**任务**: 4.5 性能优化 (P1, 8h)

**优化项**:
1. 减少不必要的等待（使用精确的元素等待）
2. 优化选择器查找（缓存常用选择器）
3. 并行处理独立操作
4. 减少截图数量（可配置）

**性能测试**: 4.6 (P1, 6h，部分时间)

```python
@pytest.mark.performance
async def test_single_article_publish_time():
    """测试发布时间"""
    import time
    start = time.time()

    result = await orchestrator.publish_article(...)

    duration = time.time() - start
    assert duration <= 180, f"耗时 {duration}秒，超过 3 分钟"
```

**验收标准**:
- [ ] 单篇文章 ≤ 2.5 分钟
- [ ] 图片上传 ≥ 1 MB/s

---

### Week 5 Day 5 (Friday) - 代码审查 + 选择器验证

**任务 1**: 4.10 代码审查和重构 (P1, 8h，上午 4h)
- 消除重复代码
- 统一命名规范
- 添加注释

**任务 2**: 4.4 选择器验证测试 (P1, 6h，下午)

**创建文件**: `tests/validators/test_selectors.py`

```python
@pytest.mark.validator
async def test_validate_all_selectors():
    """验证所有选择器"""
    # 在真实 WordPress 环境中测试每个选择器
    # 生成验证报告
```

---

### Sprint 4 验收标准

**完成的任务**:
- [x] 4.1 单元测试完善 (P0)
- [x] 4.2 集成测试开发 (P0)
- [x] 4.3 E2E 测试开发 (P0)
- [x] 4.4 选择器验证 (P1)
- [x] 4.5 性能优化 (P1)
- [x] 4.6 性能测试 (P1)
- [x] 4.10 代码审查 (P1)

**质量检查**:
- [ ] ✅ 单元测试覆盖率 ≥ 85%
- [ ] ✅ 集成测试通过率 100%
- [ ] ✅ E2E 测试通过率 ≥ 95%
- [ ] ✅ 性能达标
- [ ] ✅ 代码规范统一

---

## 🏃 Sprint 5: 部署与文档 (Week 5)

**时间**: 2025-12-09 ~ 2025-12-13 (1 周，与 Sprint 4 部分重叠)
**目标**: 生产部署就绪
**团队**: 1 后端开发 + 0.5 DevOps

### Sprint 目标
✅ Docker 镜像构建完成
✅ 部署脚本可用
✅ 文档完整
✅ 生产环境部署

---

### Day 1-2 (Monday-Tuesday) - Docker + 部署

**任务 1**: 5.1 Docker 镜像构建 (P0, 4h)

**创建文件**: `Dockerfile`

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium

# 复制代码
COPY src/ ./src/
COPY config/ ./config/

# 创建日志目录
RUN mkdir -p /logs /uploads

# 环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**任务 2**: 5.2 环境变量配置 (P0, 2h)

**创建文件**: `.env.example`

```bash
# WordPress 配置
WORDPRESS_URL=http://localhost:8080
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=admin123

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 发布配置
PRIMARY_PROVIDER=playwright
FALLBACK_PROVIDER=computer_use
MAX_RETRIES=3
RETRY_DELAY=2.0
TIMEOUT=30
SCREENSHOT_ENABLED=true

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=/logs

# 安全提示
# ⚠️  不要将此文件提交到 Git！
# ⚠️  生产环境请使用强密码
# ⚠️  Anthropic API Key 请妥善保管
```

**任务 3**: 5.3 部署脚本 (P0, 4h)

**创建文件**: `deploy.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Starting WordPress Publishing Service deployment..."

# 检查环境变量
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please copy .env.example to .env and configure it"
    exit 1
fi

# 构建镜像
echo "🔨 Building Docker image..."
docker build -t wordpress-publisher:latest .

# 启动服务
echo "▶️  Starting services..."
docker-compose up -d

# 健康检查
echo "🏥 Waiting for service to be healthy..."
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo ""
    echo "📝 Service info:"
    echo "   API: http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
else
    echo "❌ Health check failed"
    exit 1
fi
```

**构建和部署**:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

### Day 3-4 (Wednesday-Thursday) - 文档

**任务 1**: 5.4 API 文档 (P1, 4h)

**FastAPI 自动生成**: http://localhost:8000/docs

**手动编写**: `docs/API.md`

```markdown
# API 文档

## POST /publish

发布文章到 WordPress

**请求体**:
\`\`\`json
{
  "article": {
    "id": 1,
    "title": "文章标题",
    "content_html": "<p>内容</p>",
    "seo": {...}
  },
  "images": [...],
  "metadata": {...},
  "wordpress_url": "http://example.com",
  "username": "admin",
  "password": "password"
}
\`\`\`

**响应**:
\`\`\`json
{
  "task_id": "uuid",
  "status": "pending"
}
\`\`\`

## GET /tasks/{task_id}

查询任务状态

**响应**:
\`\`\`json
{
  "status": "completed",
  "result": {
    "success": true,
    "url": "http://example.com/article",
    "duration_seconds": 120.5
  }
}
\`\`\`
```

**任务 2**: 5.5 用户手册 (P1, 6h)

**创建文件**: `docs/USER_GUIDE.md`

```markdown
# 用户手册

## 快速开始

### 1. 安装

\`\`\`bash
git clone https://github.com/yourorg/wordpress-publisher.git
cd wordpress-publisher
cp .env.example .env
# 编辑 .env 配置
./deploy.sh
\`\`\`

### 2. 发布第一篇文章

\`\`\`python
import httpx

data = {
    "article": {...},
    "wordpress_url": "http://your-site.com",
    "username": "admin",
    "password": "password"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/publish",
        json=data
    )
    task_id = response.json()["task_id"]

    # 查询状态
    status = await client.get(f"http://localhost:8000/tasks/{task_id}")
    print(status.json())
\`\`\`

## 常见问题

### Q: 如何切换到 Computer Use？
A: 设置环境变量 `PRIMARY_PROVIDER=computer_use`

### Q: 图片上传失败怎么办？
A: 1. 检查图片大小（建议 < 5MB）
   2. 检查网络连接
   3. 查看日志：`docker-compose logs`

## 故障排查

### 选择器失效
如果 WordPress 版本更新导致选择器失效：

1. 运行选择器验证：
   \`\`\`bash
   pytest tests/validators/test_selectors.py
   \`\`\`

2. 更新 `config/selectors.yaml`

3. 或启用 Computer Use 作为主 Provider
```

---

### Day 5 (Friday) - 最终验收

**最终检查清单**:

#### 功能验收
- [ ] 能在 WordPress 经典编辑器中发布文章
- [ ] 能上传和插入图片（元数据完整）
- [ ] 能设置特色图片并裁切
- [ ] 能配置标签、分类、SEO
- [ ] 能立即发布和排程发布
- [ ] Playwright 失败能降级到 Computer Use
- [ ] 提供 REST API
- [ ] 支持任务恢复

#### 质量验收
- [ ] 单元测试覆盖率 ≥ 85%
- [ ] 集成测试通过率 100%
- [ ] E2E 测试通过率 ≥ 95%
- [ ] 性能达标（单篇 ≤ 2.5 分钟）
- [ ] 代码审查通过
- [ ] 文档完整

#### 部署验收
- [ ] Docker 镜像构建成功（< 1GB）
- [ ] 在测试环境部署成功
- [ ] 健康检查正常
- [ ] 日志和监控正常
- [ ] 能正常重启和恢复

---

## 📊 项目总结

### 完成情况

| Sprint | 目标 | 状态 | 交付物 |
|--------|------|------|--------|
| Sprint 1 | 基础设施 | ✅ | 项目结构、数据模型、测试环境 |
| Sprint 2 | Playwright 核心 | ✅ | MVP 可演示 |
| Sprint 3 | Computer Use + 降级 | ✅ | 生产版核心功能 |
| Sprint 4 | 测试与优化 | ✅ | 质量保障 |
| Sprint 5 | 部署与文档 | ✅ | 生产就绪 |

### 最终交付物

**代码**:
- ✅ 52 个任务中的 46 个完成（P0+P1）
- ✅ 约 3500 行 Python 代码
- ✅ 150+ 个测试用例

**文档**:
- ✅ API 文档
- ✅ 用户手册
- ✅ 部署指南

**部署**:
- ✅ Docker 镜像
- ✅ 部署脚本
- ✅ 监控配置

### 里程碑达成

- [x] **Week 3 中**: MVP 完成 ✅
- [x] **Week 4 中**: 生产版完成 ✅
- [x] **Week 5 结束**: 部署上线 ✅

---

## 🎉 项目完成！

**下一步**:
1. 生产环境部署
2. 监控和告警配置
3. 用户培训
4. 持续优化

**预祝项目成功！** 🚀
