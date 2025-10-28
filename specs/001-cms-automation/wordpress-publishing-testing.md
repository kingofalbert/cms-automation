# WordPress 视觉自动化发布 - 测试方案

**文档版本**: v1.0
**创建日期**: 2025-10-27
**状态**: 设计中
**关联文档**:
- [wordpress-publishing-spec.md](./wordpress-publishing-spec.md)
- [wordpress-publishing-plan.md](./wordpress-publishing-plan.md)

---

## 目录

1. [测试策略](#测试策略)
2. [测试环境](#测试环境)
3. [单元测试](#单元测试)
4. [集成测试](#集成测试)
5. [E2E测试](#e2e测试)
6. [选择器验证测试](#选择器验证测试)
7. [降级机制测试](#降级机制测试)
8. [性能测试](#性能测试)
9. [兼容性测试](#兼容性测试)
10. [测试数据准备](#测试数据准备)
11. [测试执行计划](#测试执行计划)
12. [测试报告](#测试报告)

---

## 测试策略

### 测试金字塔

```
                    ┌──────────┐
                    │   E2E    │  10% (关键流程验证)
                    │  测试    │
                    └──────────┘
                 ┌─────────────────┐
                 │   集成测试       │  30% (组件交互验证)
                 └─────────────────┘
            ┌───────────────────────────┐
            │      单元测试              │  60% (功能模块验证)
            └───────────────────────────┘
```

### 测试原则

1. **快速反馈**: 单元测试在 1 秒内完成，集成测试在 10 秒内完成
2. **隔离性**: 每个测试独立运行，互不影响
3. **可重复性**: 测试结果稳定，避免 flaky tests
4. **真实性**: E2E 测试使用真实的 WordPress 环境
5. **覆盖率**: 代码覆盖率 ≥ 80%，关键路径 100%

### 测试范围

✅ **包含**:
- Playwright Provider 的所有方法
- Computer Use Provider 的所有方法
- Publishing Orchestrator 的编排逻辑
- 降级机制触发和切换
- 错误处理和重试逻辑
- 日志和审计功能
- 配置加载和验证

❌ **不包含**:
- WordPress 核心功能（假设 WordPress 本身正常工作）
- 浏览器内部实现（依赖 Playwright 和 Chromium）
- Anthropic API 的可靠性（使用 Mock）

---

## 测试环境

### 环境配置

#### 1. 本地开发环境

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  wordpress-test:
    image: wordpress:6.4-php8.2
    container_name: wordpress-test
    environment:
      WORDPRESS_DB_HOST: mysql-test
      WORDPRESS_DB_USER: wpuser
      WORDPRESS_DB_PASSWORD: wppass
      WORDPRESS_DB_NAME: wordpress_test
    volumes:
      - ./test-data/wordpress:/var/www/html
      - ./test-plugins:/var/www/html/wp-content/plugins
    ports:
      - "8080:80"
    networks:
      - test-network
    depends_on:
      - mysql-test

  mysql-test:
    image: mysql:8.0
    container_name: mysql-test
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: wordpress_test
      MYSQL_USER: wpuser
      MYSQL_PASSWORD: wppass
    volumes:
      - mysql-test-data:/var/lib/mysql
    networks:
      - test-network

  publisher-test:
    build: .
    container_name: publisher-test
    environment:
      - TEST_MODE=true
      - WORDPRESS_URL=http://wordpress-test
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./tests:/app/tests
      - ./logs-test:/logs
    networks:
      - test-network
    depends_on:
      - wordpress-test

networks:
  test-network:

volumes:
  mysql-test-data:
```

#### 2. WordPress 测试站点配置

**必需插件**:
- Classic Editor (v1.6.3)
- Yoast SEO (v21.5)
- Disable Gutenberg (防止自动切换到区块编辑器)

**主题**:
- Astra (v4.5.0) - 轻量级，加载快

**初始化脚本** (`tests/fixtures/init-wordpress.sh`):

```bash
#!/bin/bash
# 初始化测试 WordPress 站点

# 等待 WordPress 启动
sleep 10

# 安装 WP-CLI
docker exec wordpress-test bash -c "curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar && chmod +x wp-cli.phar && mv wp-cli.phar /usr/local/bin/wp"

# 安装 WordPress
docker exec wordpress-test wp core install \
  --url=http://localhost:8080 \
  --title="测试站点" \
  --admin_user=testadmin \
  --admin_password=testpass123 \
  --admin_email=test@example.com \
  --allow-root

# 安装插件
docker exec wordpress-test wp plugin install classic-editor --activate --allow-root
docker exec wordpress-test wp plugin install wordpress-seo --activate --allow-root

# 安装主题
docker exec wordpress-test wp theme install astra --activate --allow-root

# 创建测试分类
docker exec wordpress-test wp term create category "测试分类" --allow-root
docker exec wordpress-test wp term create category "技术" --allow-root

# 创建测试用户
docker exec wordpress-test wp user create editor editor@test.com --role=editor --user_pass=editorpass --allow-root

echo "WordPress 测试站点初始化完成"
```

---

## 单元测试

### 1. Playwright Provider 测试

#### 测试文件: `tests/unit/test_playwright_provider.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.providers.playwright_provider import PlaywrightProvider, ElementNotFoundError
from src.config.selector_config import SelectorConfig

@pytest.fixture
def mock_page():
    """创建 Mock Page 对象"""
    page = Mock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.locator = Mock(return_value=Mock(
        fill=AsyncMock(),
        click=AsyncMock(),
        is_visible=AsyncMock(return_value=True),
        first=Mock()
    ))
    page.select_option = AsyncMock()
    page.screenshot = AsyncMock(return_value=b'fake_screenshot')
    page.context = Mock()
    page.context.cookies = AsyncMock(return_value=[])
    return page

@pytest.fixture
def selector_config():
    """创建测试用选择器配置"""
    config = Mock(spec=SelectorConfig)
    config.get = Mock(return_value="#test-selector")
    return config

@pytest.fixture
def provider(mock_page, selector_config):
    """创建 Provider 实例"""
    provider = PlaywrightProvider(selector_config)
    provider.page = mock_page
    provider.base_url = "http://test.example.com"
    return provider


class TestPlaywrightProvider:
    """Playwright Provider 单元测试"""

    @pytest.mark.asyncio
    async def test_navigate_to(self, provider, mock_page):
        """测试导航到 URL"""
        url = "http://test.example.com/wp-admin"
        await provider.navigate_to(url)
        mock_page.goto.assert_called_once_with(url, wait_until='networkidle')

    @pytest.mark.asyncio
    async def test_fill_input_success(self, provider, mock_page):
        """测试填充输入框 - 成功场景"""
        await provider.fill_input("title", "测试标题")

        # 验证 locator 被调用
        mock_page.locator.assert_called()

        # 验证 fill 被调用
        locator = mock_page.locator.return_value
        locator.first.fill.assert_called_once_with("测试标题")

    @pytest.mark.asyncio
    async def test_fill_input_element_not_found(self, provider, mock_page):
        """测试填充输入框 - 元素未找到"""
        # 模拟元素不可见
        locator = mock_page.locator.return_value
        locator.first.is_visible = AsyncMock(return_value=False)

        # 应该抛出 ElementNotFoundError
        with pytest.raises(ElementNotFoundError):
            await provider.fill_input("nonexistent", "value")

    @pytest.mark.asyncio
    async def test_click_button_success(self, provider, mock_page):
        """测试点击按钮 - 成功场景"""
        await provider.click_button("save_draft")

        locator = mock_page.locator.return_value
        locator.first.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_element_timeout(self, provider, mock_page):
        """测试等待元素 - 超时场景"""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        # 模拟超时
        mock_page.wait_for_selector = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        with pytest.raises(PlaywrightTimeoutError):
            await provider.wait_for_element("missing_element", timeout=5)

    @pytest.mark.asyncio
    async def test_upload_file_success(self, provider, mock_page):
        """测试上传文件 - 成功场景"""
        # 模拟文件选择器
        file_chooser_mock = Mock()
        file_chooser_mock.set_files = AsyncMock()

        async def expect_file_chooser():
            class FileChooserInfo:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, *args):
                    pass
                @property
                def value(self):
                    return file_chooser_mock
            return FileChooserInfo()

        mock_page.expect_file_chooser = expect_file_chooser

        await provider.upload_file("/tmp/test-image.jpg")

        # 验证文件被设置
        file_chooser_mock.set_files.assert_called_once_with("/tmp/test-image.jpg")

    @pytest.mark.asyncio
    async def test_capture_screenshot(self, provider, mock_page):
        """测试捕获截图"""
        screenshot = await provider.capture_screenshot()

        assert screenshot == b'fake_screenshot'
        mock_page.screenshot.assert_called_once_with(full_page=True)

    @pytest.mark.asyncio
    async def test_get_cookies(self, provider, mock_page):
        """测试获取 cookies"""
        mock_cookies = [{"name": "session", "value": "abc123"}]
        mock_page.context.cookies = AsyncMock(return_value=mock_cookies)

        cookies = await provider.get_cookies()

        assert cookies == mock_cookies

    @pytest.mark.asyncio
    async def test_add_tag(self, provider, mock_page):
        """测试添加标签"""
        await provider.add_tag("测试标签")

        # 验证输入标签
        calls = mock_page.locator.call_args_list
        assert len(calls) >= 2  # 至少调用 2 次（输入框和按钮）

    @pytest.mark.asyncio
    async def test_configure_seo_plugin(self, provider, mock_page):
        """测试配置 SEO 插件"""
        seo_data = {
            "focus_keyword": "测试",
            "meta_title": "测试标题",
            "meta_description": "这是测试描述"
        }

        await provider.configure_seo_plugin(seo_data)

        # 验证所有字段都被填充
        assert mock_page.locator.call_count >= 3

    @pytest.mark.asyncio
    async def test_fallback_selector(self, provider, mock_page, selector_config):
        """测试备选选择器"""
        # 配置多个选择器
        selector_config.get = Mock(return_value=["#primary-selector", "#fallback-selector"])

        # 第一个选择器不可见
        first_locator = Mock()
        first_locator.first.is_visible = AsyncMock(return_value=False)

        # 第二个选择器可见
        second_locator = Mock()
        second_locator.first.is_visible = AsyncMock(return_value=True)
        second_locator.first.fill = AsyncMock()

        mock_page.locator = Mock(side_effect=[first_locator, second_locator])

        await provider.fill_input("title", "测试")

        # 验证备选选择器被使用
        second_locator.first.fill.assert_called_once_with("测试")


class TestPlaywrightProviderEdgeCases:
    """Playwright Provider 边界情况测试"""

    @pytest.mark.asyncio
    async def test_fill_empty_value(self, provider):
        """测试填充空值"""
        # 应该正常执行，不抛出错误
        await provider.fill_input("title", "")

    @pytest.mark.asyncio
    async def test_fill_very_long_value(self, provider):
        """测试填充超长值"""
        long_text = "A" * 10000
        await provider.fill_input("content", long_text)

    @pytest.mark.asyncio
    async def test_special_characters_in_input(self, provider):
        """测试特殊字符输入"""
        special_text = '<script>alert("XSS")</script>'
        await provider.fill_input("title", special_text)

    @pytest.mark.asyncio
    async def test_unicode_characters(self, provider):
        """测试 Unicode 字符"""
        unicode_text = "测试 🎉 émojis & spëcial çhars"
        await provider.fill_input("title", unicode_text)
```

### 2. Computer Use Provider 测试

#### 测试文件: `tests/unit/test_computer_use_provider.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.providers.computer_use_provider import ComputerUseProvider, ComputerUseError
from src.config.instruction_template import InstructionTemplate

@pytest.fixture
def mock_anthropic_client():
    """创建 Mock Anthropic Client"""
    client = Mock()
    client.messages = Mock()
    client.messages.create = AsyncMock()
    return client

@pytest.fixture
def instruction_template():
    """创建指令模板"""
    template = Mock(spec=InstructionTemplate)
    template.get = Mock(return_value="测试指令")
    return template

@pytest.fixture
def provider(mock_anthropic_client, instruction_template):
    """创建 Computer Use Provider 实例"""
    with patch('src.providers.computer_use_provider.anthropic.Anthropic', return_value=mock_anthropic_client):
        provider = ComputerUseProvider(api_key="test-key", instructions_template=instruction_template)
        return provider


class TestComputerUseProvider:
    """Computer Use Provider 单元测试"""

    @pytest.mark.asyncio
    async def test_initialize(self, provider):
        """测试初始化"""
        await provider.initialize("http://test.example.com")

        assert provider.base_url == "http://test.example.com"
        assert provider.session_id is not None

    @pytest.mark.asyncio
    async def test_execute_instruction_success(self, provider, mock_anthropic_client):
        """测试执行指令 - 成功场景"""
        # 模拟 API 响应
        mock_response = Mock()
        mock_response.content = [
            Mock(
                type="tool_use",
                name="computer",
                output={
                    "screenshot": b"fake_screenshot",
                    "text": "操作成功"
                }
            )
        ]
        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        # 执行指令
        result = await provider._execute_instruction("点击按钮")

        # 验证结果
        assert result.success == True
        assert result.screenshot == b"fake_screenshot"
        assert result.text_output == "操作成功"

    @pytest.mark.asyncio
    async def test_execute_instruction_failure(self, provider, mock_anthropic_client):
        """测试执行指令 - 失败场景"""
        # 模拟 API 响应（无工具调用）
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="无法完成操作")
        ]
        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        # 应该抛出错误
        with pytest.raises(ComputerUseError):
            await provider._execute_instruction("点击按钮")

    @pytest.mark.asyncio
    async def test_fill_input(self, provider):
        """测试填充输入框"""
        with patch.object(provider, '_execute_instruction', new_callable=AsyncMock) as mock_execute:
            await provider.fill_input("title", "测试标题")

            # 验证指令被构建并执行
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file(self, provider):
        """测试上传文件"""
        with patch.object(provider, '_execute_instruction', new_callable=AsyncMock) as mock_execute:
            await provider.upload_file("/tmp/test.jpg")

            mock_execute.assert_called_once()
            # 验证指令包含文件路径
            call_args = mock_execute.call_args[0][0]
            assert "/tmp/test.jpg" in call_args

    @pytest.mark.asyncio
    async def test_conversation_history(self, provider, mock_anthropic_client):
        """测试对话历史记录"""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                type="tool_use",
                name="computer",
                output={"screenshot": b"", "text": "成功"}
            )
        ]
        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        # 执行多个指令
        await provider._execute_instruction("指令1")
        await provider._execute_instruction("指令2")

        # 验证对话历史包含所有消息
        assert len(provider.conversation_history) >= 4  # 2条用户消息 + 2条助手消息

    @pytest.mark.asyncio
    async def test_extract_url_from_response(self, provider):
        """测试从响应中提取 URL"""
        from src.providers.computer_use_provider import ComputerUseResponse

        response = ComputerUseResponse(
            success=True,
            screenshot=b"",
            text_output="文章已发布：https://example.com/2025/10/27/test-article/",
            error=None
        )

        assert response.extracted_url == "https://example.com/2025/10/27/test-article/"
```

### 3. Publishing Orchestrator 测试

#### 测试文件: `tests/unit/test_orchestrator.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.orchestrator import PublishingOrchestrator, PublishingContext
from src.models import Article, SEOData, ImageAsset, ArticleMetadata

@pytest.fixture
def mock_primary_provider():
    """创建 Mock 主 Provider"""
    provider = Mock()
    provider.initialize = AsyncMock()
    provider.close = AsyncMock()
    provider.capture_screenshot = AsyncMock(return_value=b"screenshot")
    provider.get_cookies = AsyncMock(return_value=[])
    # 模拟所有接口方法
    for method in ['navigate_to_new_post', 'fill_input', 'click_button', 'upload_file', 'add_tag']:
        setattr(provider, method, AsyncMock())
    return provider

@pytest.fixture
def mock_fallback_provider():
    """创建 Mock 备用 Provider"""
    provider = Mock()
    provider.initialize = AsyncMock()
    provider.close = AsyncMock()
    provider.capture_screenshot = AsyncMock(return_value=b"screenshot")
    for method in ['navigate_to_new_post', 'fill_input', 'click_button', 'upload_file', 'add_tag']:
        setattr(provider, method, AsyncMock())
    return provider

@pytest.fixture
def orchestrator(mock_primary_provider, mock_fallback_provider):
    """创建 Orchestrator 实例"""
    return PublishingOrchestrator(
        primary_provider=mock_primary_provider,
        fallback_provider=mock_fallback_provider
    )

@pytest.fixture
def sample_article():
    """示例文章"""
    return Article(
        id=1,
        title="测试文章",
        content_html="<p>测试内容</p>",
        excerpt="摘要",
        seo=SEOData(
            focus_keyword="测试",
            meta_title="测试标题",
            meta_description="测试描述",
            primary_keywords=["测试", "自动化"],
            secondary_keywords=["WordPress", "发布"]
        )
    )

@pytest.fixture
def sample_images():
    """示例图片"""
    return [
        ImageAsset(
            file_path="/tmp/test1.jpg",
            alt_text="测试图片1",
            title="图片1",
            caption="说明1",
            keywords=["测试"],
            photographer="测试者",
            is_featured=True
        )
    ]

@pytest.fixture
def sample_metadata():
    """示例元数据"""
    return ArticleMetadata(
        tags=["测试", "自动化"],
        categories=["技术"],
        publish_immediately=True
    )


class TestPublishingOrchestrator:
    """Publishing Orchestrator 单元测试"""

    @pytest.mark.asyncio
    async def test_publish_article_success(
        self,
        orchestrator,
        sample_article,
        sample_images,
        sample_metadata,
        mock_primary_provider
    ):
        """测试发布文章 - 成功场景"""
        # 模拟所有步骤成功
        result = await orchestrator.publish_article(
            sample_article,
            sample_images,
            sample_metadata
        )

        # 验证结果
        assert result.success == True
        assert result.task_id is not None

        # 验证主 Provider 的方法被调用
        mock_primary_provider.navigate_to_new_post.assert_called_once()
        mock_primary_provider.fill_input.assert_called()

    @pytest.mark.asyncio
    async def test_retry_on_failure(
        self,
        orchestrator,
        sample_article,
        sample_images,
        sample_metadata,
        mock_primary_provider
    ):
        """测试失败重试"""
        from src.providers.playwright_provider import ElementNotFoundError

        # 模拟第一次失败，第二次成功
        mock_primary_provider.fill_input.side_effect = [
            ElementNotFoundError("元素未找到"),
            None
        ]

        result = await orchestrator.publish_article(
            sample_article,
            sample_images,
            sample_metadata
        )

        # 验证重试
        assert mock_primary_provider.fill_input.call_count >= 2

    @pytest.mark.asyncio
    async def test_fallback_to_computer_use(
        self,
        orchestrator,
        sample_article,
        sample_images,
        sample_metadata,
        mock_primary_provider,
        mock_fallback_provider
    ):
        """测试降级到 Computer Use"""
        from src.providers.playwright_provider import ElementNotFoundError

        # 模拟主 Provider 连续失败
        mock_primary_provider.fill_input.side_effect = ElementNotFoundError("元素未找到")

        # 备用 Provider 成功
        mock_fallback_provider.fill_input = AsyncMock()

        result = await orchestrator.publish_article(
            sample_article,
            sample_images,
            sample_metadata
        )

        # 验证切换到备用 Provider
        assert orchestrator.current_provider == mock_fallback_provider
        mock_fallback_provider.fill_input.assert_called()

    @pytest.mark.asyncio
    async def test_phase_execution_with_screenshots(
        self,
        orchestrator,
        sample_article,
        sample_images,
        sample_metadata,
        mock_primary_provider
    ):
        """测试阶段执行时的截图"""
        await orchestrator.publish_article(
            sample_article,
            sample_images,
            sample_metadata
        )

        # 验证每个阶段都有截图
        # 每个阶段：before + after = 2 次截图
        # 5 个阶段 = 至少 10 次截图
        assert mock_primary_provider.capture_screenshot.call_count >= 10
```

---

## 集成测试

### 测试文件: `tests/integration/test_publishing_workflow.py`

```python
import pytest
from src.orchestrator import PublishingOrchestrator
from src.providers.playwright_provider import PlaywrightProvider
from src.providers.computer_use_provider import ComputerUseProvider
from src.config.selector_config import SelectorConfig
from src.config.instruction_template import InstructionTemplate
from src.models import Article, SEOData, ImageAsset, ArticleMetadata
from pathlib import Path

@pytest.fixture(scope="module")
async def real_playwright_provider():
    """创建真实的 Playwright Provider"""
    selector_config = SelectorConfig.load_from_file("config/selectors.yaml")
    provider = PlaywrightProvider(selector_config)
    await provider.initialize("http://localhost:8080")
    yield provider
    await provider.close()


@pytest.mark.integration
class TestPublishingWorkflowIntegration:
    """发布流程集成测试"""

    @pytest.mark.asyncio
    async def test_login_and_navigate(self, real_playwright_provider):
        """测试登录和导航"""
        provider = real_playwright_provider

        # 登录
        await provider.navigate_to("http://localhost:8080/wp-admin")
        await provider.fill_input("username", "testadmin")
        await provider.fill_input("password", "testpass123")
        await provider.click_button("login")

        # 等待仪表板加载
        await provider.wait_for_element("dashboard", timeout=10)

        # 导航到新增文章
        await provider.navigate_to_new_post()

        # 验证页面加载
        await provider.wait_for_element("new_post_title", timeout=10)

    @pytest.mark.asyncio
    async def test_fill_article_content(self, real_playwright_provider):
        """测试填充文章内容"""
        provider = real_playwright_provider

        # 假设已经在新增文章页面
        await provider.navigate_to_new_post()

        # 填写标题
        await provider.fill_input("title", "集成测试文章")

        # 切换到文字模式
        await provider.click_button("text_mode")

        # 填充内容
        content = "<p>这是集成测试的内容。</p>\n<h2>小标题</h2>\n<p>更多内容...</p>"
        await provider.fill_textarea("content", content)

        # 保存草稿
        await provider.click_button("save_draft")
        await provider.wait_for_success_message("草稿已更新")

    @pytest.mark.asyncio
    async def test_upload_and_insert_image(self, real_playwright_provider):
        """测试上传和插入图片"""
        provider = real_playwright_provider

        # 准备测试图片
        test_image = Path("tests/fixtures/test-image.jpg")
        assert test_image.exists()

        # 打开媒体库
        await provider.open_media_library()

        # 上传图片
        await provider.upload_file(str(test_image))
        await provider.wait_for_upload_complete()

        # 填写元数据
        await provider.fill_image_metadata({
            "alt": "集成测试图片",
            "title": "测试图片",
            "caption": "这是测试图片说明",
            "keywords": "测试,集成,图片",
            "photographer": "测试摄影师"
        })

        # 配置显示设置
        await provider.configure_image_display(
            align="center",
            link_to="none",
            size="large"
        )

        # 插入到内容
        await provider.insert_image_to_content()

        # 验证图片已插入
        # (需要检查编辑器中是否有图片)

    @pytest.mark.asyncio
    async def test_set_featured_image_and_crop(self, real_playwright_provider):
        """测试设置特色图片并裁切"""
        provider = real_playwright_provider

        test_image = Path("tests/fixtures/test-image-large.jpg")
        assert test_image.exists()

        # 设置特色图片
        await provider.set_as_featured_image()

        # 上传图片
        await provider.upload_file(str(test_image))
        await provider.wait_for_upload_complete()

        # 编辑图片
        await provider.edit_image()

        # 裁切为缩略图
        await provider.crop_image("thumbnail")
        await provider.save_crop()

        # 裁切为 Facebook 分享图
        await provider.crop_image("facebook_700_359")
        await provider.save_crop()

        # 确认设置
        await provider.confirm_featured_image()

    @pytest.mark.asyncio
    async def test_configure_metadata_and_seo(self, real_playwright_provider):
        """测试配置元数据和 SEO"""
        provider = real_playwright_provider

        # 添加标签
        for tag in ["集成测试", "自动化", "Playwright"]:
            await provider.add_tag(tag)

        # 选择分类
        await provider.select_category("技术")

        # 配置 SEO
        await provider.configure_seo_plugin({
            "focus_keyword": "集成测试",
            "meta_title": "集成测试文章 | 测试站点",
            "meta_description": "这是一篇用于集成测试的文章，验证 Playwright 自动化发布功能。"
        })

    @pytest.mark.asyncio
    async def test_publish_article(self, real_playwright_provider):
        """测试发布文章"""
        provider = real_playwright_provider

        # 点击发布
        await provider.click_button("publish")

        # 等待发布成功
        await provider.wait_for_success_message("文章已發佈")

        # 获取发布 URL
        url = await provider.get_published_url()

        assert url is not None
        assert "localhost:8080" in url
```

---

## E2E测试

### 测试文件: `tests/e2e/test_end_to_end.py`

```python
import pytest
from src.orchestrator import PublishingOrchestrator
from src.providers.playwright_provider import PlaywrightProvider
from src.config.selector_config import SelectorConfig
from src.models import *
from datetime import datetime
from pathlib import Path

@pytest.mark.e2e
class TestEndToEndPublishing:
    """端到端发布测试"""

    @pytest.mark.asyncio
    async def test_complete_publishing_workflow(self):
        """测试完整的发布流程"""
        # 准备数据
        article = Article(
            id=9999,
            title="E2E 测试文章 - " + datetime.now().strftime("%Y%m%d%H%M%S"),
            content_html="""
                <p>这是一篇 End-to-End 测试文章。</p>
                <h2>功能验证</h2>
                <p>本文章用于验证以下功能：</p>
                <ul>
                    <li>文章创建</li>
                    <li>图片上传</li>
                    <li>元数据设置</li>
                    <li>SEO 配置</li>
                    <li>自动发布</li>
                </ul>
                <h2>测试结果</h2>
                <p>如果你能看到这篇文章，说明自动化发布成功！</p>
            """,
            excerpt="E2E 测试文章摘要",
            seo=SEOData(
                focus_keyword="E2E测试",
                meta_title="E2E 测试文章 | WordPress 自动化",
                meta_description="这是一篇用于 End-to-End 测试的文章，验证完整的自动化发布流程。",
                primary_keywords=["E2E", "测试", "自动化"],
                secondary_keywords=["WordPress", "Playwright", "发布"]
            )
        )

        images = [
            ImageAsset(
                file_path=str(Path("tests/fixtures/test-image-1.jpg").absolute()),
                alt_text="E2E 测试主图",
                title="测试主图",
                caption="这是 E2E 测试的主图",
                keywords=["E2E", "测试", "主图"],
                photographer="自动化测试",
                is_featured=True
            ),
            ImageAsset(
                file_path=str(Path("tests/fixtures/test-image-2.jpg").absolute()),
                alt_text="E2E 测试配图",
                title="测试配图",
                caption="这是 E2E 测试的配图",
                keywords=["E2E", "测试", "配图"],
                photographer="自动化测试",
                is_featured=False
            )
        ]

        metadata = ArticleMetadata(
            tags=["E2E测试", "自动化", "Playwright", "集成"],
            categories=["技术", "测试"],
            publish_immediately=True
        )

        credentials = WordPressCredentials(
            username="testadmin",
            password="testpass123"
        )

        # 创建 Orchestrator
        selector_config = SelectorConfig.load_from_file("config/selectors.yaml")
        playwright_provider = PlaywrightProvider(selector_config)

        orchestrator = PublishingOrchestrator(
            primary_provider=playwright_provider,
            fallback_provider=None  # E2E 测试只用 Playwright
        )

        # 创建上下文
        context = PublishingContext(
            task_id="e2e-test-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            article=article,
            images=images,
            metadata=metadata,
            wordpress_url="http://localhost:8080",
            credentials=credentials
        )

        # 执行发布
        result = await orchestrator.publish_article(article, images, metadata)

        # 验证结果
        assert result.success == True, f"发布失败: {result.error}"
        assert result.url is not None
        assert "localhost:8080" in result.url

        print(f"✅ 文章发布成功: {result.url}")

        # 验证审计日志
        audit_trail = result.audit_trail
        assert audit_trail is not None
        assert len(audit_trail['events']) > 0

        # 验证截图
        screenshots = [e for e in audit_trail['events'] if e['event'] == 'screenshot_saved']
        assert len(screenshots) >= 10, "截图数量不足"

        print(f"✅ 审计日志完整，共 {len(audit_trail['events'])} 条事件，{len(screenshots)} 张截图")

    @pytest.mark.asyncio
    async def test_scheduled_publishing(self):
        """测试排程发布"""
        # 准备数据
        publish_date = datetime(2025, 12, 31, 14, 30)

        article = Article(
            id=10000,
            title="排程测试文章",
            content_html="<p>这是一篇排程发布的测试文章。</p>",
            excerpt="排程测试",
            seo=SEOData(
                focus_keyword="排程",
                meta_title="排程测试",
                meta_description="测试排程发布功能"
            )
        )

        metadata = ArticleMetadata(
            tags=["排程", "测试"],
            categories=["技术"],
            publish_immediately=False,
            publish_date=publish_date
        )

        # 执行发布
        # ... (与上面类似)

        # 验证文章状态为「已排程」
        # ... (需要查询 WordPress API 或数据库)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_publishing(self):
        """测试批量发布"""
        from src.orchestrator import BatchPublisher

        # 准备 10 篇文章
        articles_data = []
        for i in range(10):
            article = Article(
                id=20000 + i,
                title=f"批量测试文章 {i+1}",
                content_html=f"<p>这是第 {i+1} 篇批量测试文章。</p>",
                excerpt=f"批量测试 {i+1}",
                seo=SEOData(
                    focus_keyword=f"批量{i+1}",
                    meta_title=f"批量测试文章 {i+1}",
                    meta_description=f"第 {i+1} 篇测试文章"
                )
            )

            images = []  # 为简化测试，不上传图片

            metadata = ArticleMetadata(
                tags=[f"批量{i+1}", "测试"],
                categories=["技术"],
                publish_immediately=True
            )

            articles_data.append((article, images, metadata))

        # 批量发布
        batch_publisher = BatchPublisher()
        results = await batch_publisher.publish_batch(articles_data, max_concurrent=3)

        # 验证结果
        successful = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successful) == 10, f"只有 {len(successful)}/10 篇文章发布成功"

        print(f"✅ 批量发布成功，共 {len(successful)} 篇文章")
```

---

## 选择器验证测试

### 测试文件: `tests/validators/test_selectors.py`

```python
import pytest
from playwright.async_api import async_playwright
from pathlib import Path
import yaml

@pytest.mark.validator
class TestSelectorValidation:
    """选择器验证测试"""

    @pytest.fixture(scope="class")
    async def browser_page(self):
        """创建浏览器页面"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # 可见模式
            page = await browser.new_page()

            # 登录 WordPress
            await page.goto("http://localhost:8080/wp-admin")
            await page.fill("#user_login", "testadmin")
            await page.fill("#user_pass", "testpass123")
            await page.click("#wp-submit")
            await page.wait_for_selector("#wpadminbar")

            yield page

            await browser.close()

    @pytest.fixture(scope="class")
    def selectors(self):
        """加载选择器配置"""
        with open("config/selectors.yaml", 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @pytest.mark.asyncio
    async def test_validate_all_selectors(self, browser_page, selectors):
        """验证所有选择器在真实页面中可用"""
        page = browser_page

        # 导航到新增文章页面
        await page.goto("http://localhost:8080/wp-admin/post-new.php")
        await page.wait_for_load_state('networkidle')

        validation_results = []

        for selector_name, selector_values in selectors.items():
            # 跳过非选择器配置项
            if not isinstance(selector_values, (str, list)):
                continue

            selectors_list = selector_values if isinstance(selector_values, list) else [selector_values]

            found = False
            used_selector = None

            for selector in selectors_list:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        found = True
                        used_selector = selector
                        break
                except Exception:
                    continue

            validation_results.append({
                "name": selector_name,
                "found": found,
                "selector": used_selector or selectors_list[0],
                "fallback_count": len(selectors_list)
            })

        # 生成报告
        failed = [r for r in validation_results if not r['found']]

        if failed:
            print("\n❌ 以下选择器验证失败:")
            for item in failed:
                print(f"   - {item['name']}: {item['selector']}")

            # 保存失败报告
            report_path = Path("tests/reports/selector-validation-failures.txt")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                for item in failed:
                    f.write(f"{item['name']}: {item['selector']}\n")

            pytest.fail(f"{len(failed)} 个选择器验证失败，详见 {report_path}")
        else:
            print(f"\n✅ 所有 {len(validation_results)} 个选择器验证通过")
```

---

## 降级机制测试

### 测试文件: `tests/integration/test_fallback.py`

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.orchestrator import PublishingOrchestrator
from src.providers.playwright_provider import ElementNotFoundError

@pytest.mark.integration
class TestFallbackMechanism:
    """降级机制测试"""

    @pytest.mark.asyncio
    async def test_fallback_triggered_on_repeated_failures(self):
        """测试连续失败触发降级"""
        # 创建 Mock Providers
        primary = Mock()
        primary.initialize = AsyncMock()
        primary.close = AsyncMock()
        primary.capture_screenshot = AsyncMock(return_value=b"screenshot")
        primary.fill_input = AsyncMock(side_effect=ElementNotFoundError("元素未找到"))

        fallback = Mock()
        fallback.initialize = AsyncMock()
        fallback.close = AsyncMock()
        fallback.capture_screenshot = AsyncMock(return_value=b"screenshot")
        fallback.fill_input = AsyncMock()  # 成功

        orchestrator = PublishingOrchestrator(
            primary_provider=primary,
            fallback_provider=fallback
        )

        # 执行步骤（会触发降级）
        context = Mock()
        await orchestrator._execute_phase("test_phase", lambda p, c: p.fill_input("test", "value"), context)

        # 验证切换到 fallback
        assert orchestrator.current_provider == fallback
        fallback.fill_input.assert_called()

    @pytest.mark.asyncio
    async def test_no_fallback_on_first_success(self):
        """测试第一次成功不触发降级"""
        primary = Mock()
        primary.initialize = AsyncMock()
        primary.capture_screenshot = AsyncMock(return_value=b"screenshot")
        primary.fill_input = AsyncMock()  # 成功

        fallback = Mock()
        fallback.fill_input = AsyncMock()

        orchestrator = PublishingOrchestrator(
            primary_provider=primary,
            fallback_provider=fallback
        )

        context = Mock()
        await orchestrator._execute_phase("test_phase", lambda p, c: p.fill_input("test", "value"), context)

        # 验证仍在使用 primary
        assert orchestrator.current_provider == primary
        fallback.fill_input.assert_not_called()

    @pytest.mark.asyncio
    async def test_cookies_preserved_on_fallback(self):
        """测试降级时保留 cookies"""
        primary = Mock()
        primary.initialize = AsyncMock()
        primary.close = AsyncMock()
        primary.capture_screenshot = AsyncMock(return_value=b"screenshot")
        primary.get_cookies = AsyncMock(return_value=[{"name": "session", "value": "abc123"}])
        primary.fill_input = AsyncMock(side_effect=ElementNotFoundError("失败"))

        fallback = Mock()
        fallback.initialize = AsyncMock()
        fallback.capture_screenshot = AsyncMock(return_value=b"screenshot")
        fallback.fill_input = AsyncMock()

        orchestrator = PublishingOrchestrator(
            primary_provider=primary,
            fallback_provider=fallback
        )

        context = Mock()
        context.browser_cookies = []

        # 先保存 cookies
        context.browser_cookies = await primary.get_cookies()

        # 执行步骤（触发降级）
        await orchestrator._execute_phase("test_phase", lambda p, c: p.fill_input("test", "value"), context)

        # 验证 fallback 初始化时传入了 cookies
        fallback.initialize.assert_called()
        call_kwargs = fallback.initialize.call_args[1]
        assert 'cookies' in call_kwargs
```

---

## 性能测试

### 测试文件: `tests/performance/test_performance.py`

```python
import pytest
import time
from src.orchestrator import PublishingOrchestrator
from src.models import *

@pytest.mark.performance
class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_single_article_publish_time(self):
        """测试单篇文章发布时间"""
        # 准备数据
        article = Article(...)  # 简化
        images = [ImageAsset(...)]  # 1 张图片
        metadata = ArticleMetadata(...)

        orchestrator = PublishingOrchestrator(...)

        # 测量时间
        start_time = time.time()
        result = await orchestrator.publish_article(article, images, metadata)
        end_time = time.time()

        duration = end_time - start_time

        # 验收标准：≤ 3 分钟（180 秒）
        assert duration <= 180, f"发布耗时 {duration:.2f} 秒，超过 180 秒"

        print(f"✅ 单篇文章发布耗时: {duration:.2f} 秒")

    @pytest.mark.asyncio
    async def test_image_upload_speed(self):
        """测试图片上传速度"""
        from pathlib import Path

        test_image = Path("tests/fixtures/test-image-5mb.jpg")
        assert test_image.exists()

        file_size_mb = test_image.stat().st_size / (1024 * 1024)

        provider = PlaywrightProvider(...)
        await provider.initialize("http://localhost:8080")

        # 登录并导航
        # ...

        # 测量上传时间
        start_time = time.time()
        await provider.upload_file(str(test_image))
        await provider.wait_for_upload_complete()
        end_time = time.time()

        duration = end_time - start_time
        speed_mbps = file_size_mb / duration

        # 验收标准：≥ 1 MB/s
        assert speed_mbps >= 1.0, f"上传速度 {speed_mbps:.2f} MB/s，低于 1 MB/s"

        print(f"✅ 图片上传速度: {speed_mbps:.2f} MB/s")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_publishing(self):
        """测试并发发布性能"""
        from src.orchestrator import BatchPublisher

        # 准备 10 篇文章
        articles_data = [...]  # 10 篇文章

        batch_publisher = BatchPublisher()

        # 测量时间
        start_time = time.time()
        results = await batch_publisher.publish_batch(articles_data, max_concurrent=3)
        end_time = time.time()

        duration = end_time - start_time
        avg_time = duration / len(articles_data)

        # 验收标准：平均每篇 ≤ 2 分钟
        assert avg_time <= 120, f"平均每篇耗时 {avg_time:.2f} 秒，超过 120 秒"

        print(f"✅ 批量发布 {len(articles_data)} 篇文章耗时: {duration:.2f} 秒")
        print(f"   平均每篇: {avg_time:.2f} 秒")
```

---

## 兼容性测试

### 测试文件: `tests/compatibility/test_wordpress_versions.py`

```python
import pytest

@pytest.mark.compatibility
class TestWordPressVersionCompatibility:
    """WordPress 版本兼容性测试"""

    @pytest.mark.parametrize("wp_version", [
        "6.2.0",
        "6.3.0",
        "6.4.0",
        "latest"
    ])
    @pytest.mark.asyncio
    async def test_publish_on_different_wp_versions(self, wp_version):
        """测试在不同 WordPress 版本上发布"""
        # 启动对应版本的 WordPress 容器
        # docker-compose -f docker-compose.test-wp-{version}.yml up -d

        # 执行发布测试
        # ...

        # 验证成功
        # ...

        print(f"✅ WordPress {wp_version} 测试通过")


@pytest.mark.compatibility
class TestThemeCompatibility:
    """主题兼容性测试"""

    @pytest.mark.parametrize("theme", [
        "astra",
        "generatepress",
        "oceanwp",
        "twentytwentythree"
    ])
    @pytest.mark.asyncio
    async def test_publish_with_different_themes(self, theme):
        """测试在不同主题下发布"""
        # 切换主题
        # wp theme activate {theme}

        # 执行发布测试
        # ...

        print(f"✅ 主题 {theme} 测试通过")


@pytest.mark.compatibility
class TestPluginCompatibility:
    """插件兼容性测试"""

    @pytest.mark.parametrize("seo_plugin", [
        "yoast-seo",
        "rank-math",
        "all-in-one-seo"
    ])
    @pytest.mark.asyncio
    async def test_publish_with_different_seo_plugins(self, seo_plugin):
        """测试与不同 SEO 插件的兼容性"""
        # 激活插件
        # wp plugin activate {seo_plugin}

        # 执行发布并配置 SEO
        # ...

        print(f"✅ SEO 插件 {seo_plugin} 测试通过")
```

---

## 测试数据准备

### Fixtures 目录结构

```
tests/fixtures/
├── images/
│   ├── test-image-small.jpg       # 500KB
│   ├── test-image-medium.jpg      # 2MB
│   ├── test-image-large.jpg       # 5MB
│   ├── test-image-portrait.jpg    # 竖版图片
│   └── test-image-landscape.jpg   # 横版图片
├── articles/
│   ├── sample-article-1.json
│   ├── sample-article-2.json
│   └── sample-article-batch.json  # 批量测试数据
└── wordpress/
    ├── init-wordpress.sh          # WordPress 初始化脚本
    └── test-config.php            # 测试配置
```

### 示例测试数据

**tests/fixtures/articles/sample-article-1.json**:

```json
{
  "article": {
    "id": 1001,
    "title": "如何使用 Playwright 实现浏览器自动化",
    "content_html": "<p>Playwright 是由微软开发的浏览器自动化框架...</p><h2>核心功能</h2><p>...</p>",
    "excerpt": "本文介绍 Playwright 的核心功能和使用方法。",
    "seo": {
      "focus_keyword": "Playwright",
      "meta_title": "如何使用 Playwright 实现浏览器自动化 | 技术博客",
      "meta_description": "Playwright 是一个强大的浏览器自动化工具，本文详细介绍其核心功能和实战应用。"
    }
  },
  "images": [
    {
      "file_path": "tests/fixtures/images/test-image-medium.jpg",
      "alt_text": "Playwright 架构图",
      "title": "Playwright 架构",
      "caption": "Playwright 的核心架构组件",
      "keywords": ["Playwright", "架构", "自动化"],
      "photographer": "技术团队",
      "is_featured": true
    }
  ],
  "metadata": {
    "tags": ["Playwright", "自动化", "测试"],
    "categories": ["技术", "教程"],
    "publish_immediately": true
  }
}
```

---

## 测试执行计划

### 本地开发环境

```bash
# 启动测试 WordPress 环境
docker-compose -f docker-compose.test.yml up -d

# 初始化 WordPress
bash tests/fixtures/init-wordpress.sh

# 运行单元测试（快速）
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行 E2E 测试
pytest tests/e2e/ -v --html=tests/reports/e2e-report.html

# 运行所有测试
pytest tests/ -v --cov=src --cov-report=html

# 清理测试环境
docker-compose -f docker-compose.test.yml down -v
```

### CI/CD 环境 (GitHub Actions)

**.github/workflows/test.yml**:

```yaml
name: Automated Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --junitxml=reports/unit-tests.xml
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: unit-test-results
          path: reports/unit-tests.xml

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start WordPress
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Initialize WordPress
        run: bash tests/fixtures/init-wordpress.sh
      - name: Run integration tests
        run: pytest tests/integration/ -v --junitxml=reports/integration-tests.xml
      - name: Cleanup
        run: docker-compose -f docker-compose.test.yml down -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v3
      - name: Start WordPress
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Initialize WordPress
        run: bash tests/fixtures/init-wordpress.sh
      - name: Run E2E tests
        run: pytest tests/e2e/ -v --html=reports/e2e-report.html
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Upload E2E report
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-report
          path: reports/e2e-report.html
```

---

## 测试报告

### 生成测试报告

```bash
# 生成 HTML 报告
pytest tests/ --html=reports/test-report.html --self-contained-html

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html --cov-report=term

# 生成 JUnit XML（用于 CI）
pytest tests/ --junitxml=reports/junit.xml
```

### 示例测试报告

**测试摘要**:

```
====================== test session starts =======================
platform linux -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0
rootdir: /app
plugins: asyncio-0.21.1, cov-4.1.0, html-3.2.0
collected 156 items

tests/unit/test_playwright_provider.py ................... [ 12%]
tests/unit/test_computer_use_provider.py ................ [ 21%]
tests/unit/test_orchestrator.py ........................ [ 36%]
tests/integration/test_publishing_workflow.py .......... [ 48%]
tests/e2e/test_end_to_end.py ........................... [ 68%]
tests/validators/test_selectors.py ..................... [ 81%]
tests/integration/test_fallback.py ..................... [ 90%]
tests/performance/test_performance.py .................. [100%]

====================== 156 passed in 245.32s =====================

---------- coverage: platform linux, python 3.11.0-final-0 ----------
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
src/__init__.py                               2      0   100%
src/orchestrator.py                         248     18    93%
src/providers/__init__.py                     4      0   100%
src/providers/playwright_provider.py        356     29    92%
src/providers/computer_use_provider.py      198     22    89%
src/config/selector_config.py                45      3    93%
src/models.py                                67      2    97%
-------------------------------------------------------------
TOTAL                                       920     74    92%

HTML coverage report generated at: htmlcov/index.html
```

---

**文档版本**: v1.0
**作者**: AI Architect
**审核**: Pending
**下一步**: 创建任务清单 (tasks.md)
