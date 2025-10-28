"""
Unit Tests for Playwright Provider

测试 PlaywrightProvider 的核心功能（使用 Mock）
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path

from src.providers.playwright_provider import PlaywrightProvider
from src.providers.base import (
    LoginError,
    ArticleCreationError,
    ImageUploadError,
    FeaturedImageError,
    SEOConfigError,
    PublishError
)
from src.models import (
    Article,
    SEOData,
    ImageAsset,
    ArticleMetadata,
    WordPressCredentials,
    PublishingContext
)


@pytest.fixture
def provider():
    """创建 PlaywrightProvider 实例"""
    return PlaywrightProvider()


@pytest.fixture
def mock_page():
    """创建 Mock Page 对象"""
    page = AsyncMock()
    page.url = "http://localhost:8000/wp-admin"
    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.is_visible = AsyncMock(return_value=True)
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    page.evaluate = AsyncMock()
    page.keyboard = AsyncMock()
    page.keyboard.press = AsyncMock()
    page.screenshot = AsyncMock()
    page.expect_file_chooser = AsyncMock()
    return page


@pytest.fixture
def valid_credentials():
    """创建有效的登录凭证"""
    return WordPressCredentials(
        username="admin",
        password="password123"
    )


@pytest.fixture
def valid_seo_data():
    """创建有效的 SEO 数据"""
    return SEOData(
        focus_keyword="测试关键字",
        meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
        meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
    )


@pytest.fixture
def valid_article(valid_seo_data):
    """创建有效的文章数据"""
    return Article(
        id=1,
        title="测试文章标题示例内容",
        content_html="<p>这是测试文章的内容。</p>" * 20,
        excerpt="这是文章摘要",
        seo=valid_seo_data
    )


@pytest.fixture
def valid_metadata():
    """创建有效的元数据"""
    return ArticleMetadata(
        tags=["测试", "Playwright"],
        categories=["技术"],
        publish_immediately=True
    )


class TestPlaywrightProviderInitialization:
    """测试 Provider 初始化"""

    @pytest.mark.asyncio
    async def test_initialize(self, provider):
        """测试初始化成功"""
        with patch('src.providers.playwright_provider.async_playwright') as mock_playwright:
            # Mock Playwright 对象
            mock_pw = AsyncMock()
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            mock_pw.start = AsyncMock(return_value=mock_pw)
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.set_default_timeout = Mock()

            mock_playwright.return_value = mock_pw

            # 执行初始化
            await provider.initialize()

            # 验证
            assert provider.playwright is not None
            assert provider.browser is not None
            assert provider.context is not None
            assert provider.page is not None

    @pytest.mark.asyncio
    async def test_cleanup(self, provider, mock_page):
        """测试清理资源"""
        # 设置 Mock 对象
        provider.page = mock_page
        provider.context = AsyncMock()
        provider.browser = AsyncMock()
        provider.playwright = AsyncMock()

        # 执行清理
        await provider.cleanup()

        # 验证所有资源都被关闭/停止
        mock_page.close.assert_called_once()
        provider.context.close.assert_called_once()
        provider.browser.close.assert_called_once()
        provider.playwright.stop.assert_called_once()


class TestPlaywrightProviderLogin:
    """测试登录功能"""

    @pytest.mark.asyncio
    async def test_login_success(self, provider, mock_page, valid_credentials):
        """测试登录成功"""
        provider.page = mock_page
        mock_page.url = "http://localhost:8000/wp-admin/index.php"

        # 执行登录
        result = await provider.login("http://localhost:8000", valid_credentials)

        # 验证
        assert result is True
        mock_page.goto.assert_called_once()
        assert mock_page.fill.call_count == 2  # 用户名和密码
        mock_page.click.assert_called_once()  # 登录按钮

    @pytest.mark.asyncio
    async def test_login_failure_wrong_credentials(self, provider, mock_page, valid_credentials):
        """测试登录失败（错误凭证）"""
        provider.page = mock_page

        # 模拟登录后 URL 仍然在登录页面
        async def mock_goto(*args, **kwargs):
            mock_page.url = "http://localhost:8000/wp-login.php?error=invalid"

        mock_page.goto = AsyncMock(side_effect=mock_goto)

        # 执行登录并验证抛出异常
        with pytest.raises(LoginError) as exc_info:
            await provider.login("http://localhost:8000", valid_credentials)

        assert "登录失败" in str(exc_info.value)


class TestPlaywrightProviderArticleCreation:
    """测试文章创建功能"""

    @pytest.mark.asyncio
    async def test_create_article_basic(self, provider, mock_page, valid_article, valid_metadata):
        """测试基本文章创建"""
        provider.page = mock_page

        # 执行文章创建
        result = await provider.create_article(valid_article, valid_metadata)

        # 验证
        assert result is True
        # 验证导航到新建文章页面
        assert mock_page.click.call_count >= 1
        # 验证填写了标题和内容
        assert mock_page.fill.call_count >= 2

    @pytest.mark.asyncio
    async def test_fill_title(self, provider, mock_page):
        """测试填写标题"""
        provider.page = mock_page

        await provider._fill_title("测试标题")

        mock_page.fill.assert_called_once()
        call_args = mock_page.fill.call_args
        assert "测试标题" in str(call_args)

    @pytest.mark.asyncio
    async def test_fill_content(self, provider, mock_page):
        """测试填写内容"""
        provider.page = mock_page

        content_html = "<p>测试内容</p>"
        await provider._fill_content(content_html)

        # 验证切换到文本编辑器并填写内容
        assert mock_page.click.call_count >= 1  # 切换到文本编辑器
        assert mock_page.fill.call_count >= 1


class TestPlaywrightProviderImageUpload:
    """测试图片上传功能"""

    @pytest.fixture
    def test_image(self, tmp_path):
        """创建测试图片"""
        image_file = tmp_path / "test_image.jpg"
        image_file.write_bytes(b"fake image content")

        return ImageAsset(
            file_path=str(image_file),
            alt_text="测试图片替代文字内容",
            title="测试图片",
            caption="测试图片说明"
        )

    @pytest.mark.asyncio
    async def test_upload_single_image(self, provider, mock_page, test_image):
        """测试上传单张图片"""
        provider.page = mock_page

        # Mock 文件选择器
        file_chooser_mock = AsyncMock()
        file_chooser_mock.set_files = AsyncMock()

        # Mock fc_info 对象 (expect_file_chooser context manager yields this)
        class FileChooserInfo:
            async def get_value(self):
                return file_chooser_mock

            @property
            def value(self):
                return self.get_value()

        class FileChooserContext:
            def __init__(self):
                self.info = FileChooserInfo()

            async def __aenter__(self):
                return self.info

            async def __aexit__(self, *args):
                pass

        # Mock expect_file_chooser() 返回 context manager
        mock_page.expect_file_chooser = Mock(return_value=FileChooserContext())

        # Mock 媒体库相关的选择器
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=AsyncMock())

        # 执行上传
        result = await provider.upload_images([test_image])

        # 验证
        assert len(result) == 1
        assert test_image.file_path in result[0]


class TestPlaywrightProviderSEO:
    """测试 SEO 配置功能"""

    @pytest.mark.asyncio
    async def test_configure_seo(self, provider, mock_page, valid_seo_data):
        """测试 SEO 配置"""
        provider.page = mock_page

        # 执行 SEO 配置
        result = await provider.configure_seo(valid_seo_data)

        # 验证
        assert result is True
        # 验证填写了焦点关键字、SEO 标题、Meta 描述
        assert mock_page.fill.call_count >= 3

    @pytest.mark.asyncio
    async def test_set_focus_keyword(self, provider, mock_page):
        """测试设置焦点关键字"""
        provider.page = mock_page

        await provider._set_focus_keyword("测试关键字")

        mock_page.fill.assert_called_once()
        call_args = mock_page.fill.call_args
        assert "测试关键字" in str(call_args)


class TestPlaywrightProviderPublish:
    """测试发布功能"""

    @pytest.mark.asyncio
    async def test_publish_immediately(self, provider, mock_page, valid_metadata):
        """测试立即发布"""
        provider.page = mock_page
        mock_page.url = "http://localhost:8000/wp-admin/post.php?post=123&action=edit"

        # Mock 成功消息
        success_element = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=success_element)

        # Mock "查看文章"链接
        view_link = AsyncMock()
        view_link.get_attribute = AsyncMock(return_value="http://localhost:8000/test-post/")
        mock_page.query_selector = AsyncMock(return_value=view_link)

        # 执行发布
        result = await provider.publish(valid_metadata)

        # 验证
        assert "http://localhost:8000" in result
        mock_page.click.assert_called_once()  # 点击发布按钮


class TestPlaywrightProviderScreenshot:
    """测试截图功能"""

    @pytest.mark.asyncio
    async def test_take_screenshot(self, provider, mock_page):
        """测试截图"""
        provider.page = mock_page

        # 执行截图
        result = await provider.take_screenshot("test_screenshot", "测试截图")

        # 验证
        assert result is not None
        assert "test_screenshot" in result
        assert result.endswith(".png")
        mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_screenshot_disabled(self, provider, mock_page):
        """测试禁用截图"""
        provider.page = mock_page

        # 禁用截图
        with patch('src.providers.playwright_provider.settings') as mock_settings:
            mock_settings.enable_screenshots = False

            # 执行截图
            result = await provider.take_screenshot("test", "test")

            # 验证
            assert result is None
            mock_page.screenshot.assert_not_called()


class TestPlaywrightProviderIntegration:
    """集成测试（模拟完整流程）"""

    @pytest.fixture
    def publishing_context(self, valid_article, valid_metadata, valid_credentials, tmp_path):
        """创建发布上下文"""
        # 创建测试图片
        image_file = tmp_path / "test.jpg"
        image_file.write_bytes(b"fake image")

        return PublishingContext(
            task_id="test-task-123",
            article=valid_article,
            images=[
                ImageAsset(
                    file_path=str(image_file),
                    alt_text="测试图片替代文字内容",
                    title="测试图片",
                    is_featured=True
                )
            ],
            metadata=valid_metadata,
            wordpress_url="http://localhost:8000",
            credentials=valid_credentials
        )

    @pytest.mark.asyncio
    async def test_publish_article_workflow(self, provider, mock_page, publishing_context):
        """测试完整发布流程"""
        # Mock 所有必要的方法
        provider.page = mock_page
        provider.initialize = AsyncMock()
        provider.cleanup = AsyncMock()
        provider.login = AsyncMock(return_value=True)
        provider.create_article = AsyncMock(return_value=True)
        provider.upload_images = AsyncMock(return_value=["http://example.com/image.jpg"])
        provider.set_featured_image = AsyncMock(return_value=True)
        provider.configure_seo = AsyncMock(return_value=True)
        provider.publish = AsyncMock(return_value="http://localhost:8000/test-post/")
        provider.take_screenshot = AsyncMock(return_value="/path/to/screenshot.png")

        # 执行完整发布流程
        result = await provider.publish_article(publishing_context)

        # 验证
        assert result.success is True
        assert result.url == "http://localhost:8000/test-post/"
        assert result.task_id == "test-task-123"

        # 验证所有阶段都被调用
        provider.initialize.assert_called_once()
        provider.login.assert_called_once()
        provider.create_article.assert_called_once()
        provider.upload_images.assert_called_once()
        provider.set_featured_image.assert_called_once()
        provider.configure_seo.assert_called_once()
        provider.publish.assert_called_once()
        provider.cleanup.assert_called_once()
