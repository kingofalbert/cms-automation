"""
WordPress Integration Tests

这些测试需要真实的 WordPress 环境运行。
使用方法：
1. 启动测试环境: docker compose -f docker-compose.test.yml up -d
2. 运行测试: pytest tests/integration/test_wordpress_integration.py -v
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from src.providers.playwright_provider import PlaywrightProvider
from src.models import (
    Article,
    SEOData,
    ImageAsset,
    ArticleMetadata,
    WordPressCredentials,
    PublishingContext
)


# ==================== Fixtures ====================

@pytest.fixture(scope="module")
def wordpress_url():
    """测试 WordPress URL"""
    return "http://localhost:8001"


@pytest.fixture(scope="module")
def credentials():
    """测试 WordPress 凭证"""
    return WordPressCredentials(
        username="admin",
        password="password"
    )


@pytest.fixture(scope="module")
def test_image(tmp_path_factory):
    """创建测试图片"""
    # 创建一个小的测试图片
    tmp_dir = tmp_path_factory.mktemp("images")
    image_path = tmp_dir / "test_image.jpg"

    # 创建一个简单的 JPEG 图片（最小有效 JPEG）
    # 这是一个 1x1 像素的红色 JPEG
    jpeg_data = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
        0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
        0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
        0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
        0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
        0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14,
        0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0x37, 0xFF, 0xD9
    ])

    image_path.write_bytes(jpeg_data)

    return ImageAsset(
        file_path=str(image_path),
        alt_text="集成测试图片的详细替代文字描述内容用于辅助功能支持需求",
        title="集成测试图片",
        caption="这是集成测试使用的图片说明文字内容",
        is_featured=True
    )


@pytest.fixture(scope="module")
def valid_seo_data():
    """创建有效的 SEO 数据"""
    return SEOData(
        focus_keyword="WordPress集成测试",
        meta_title="WordPress集成测试完整详细的搜索引擎优化标题示例文本内容必须符合字符长度要求标准规范指南要求",
        meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的WordPress集成测试网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了集成测试文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用系统功能。"
    )


@pytest.fixture(scope="module")
def valid_article(valid_seo_data):
    """创建有效的测试文章"""
    content_html = """
    <h2>WordPress 自动化发布系统集成测试</h2>

    <p>这是一篇由自动化系统生成的测试文章，用于验证 WordPress 发布功能的完整性和可靠性。</p>

    <h3>测试目标</h3>
    <ul>
        <li>验证文章创建功能</li>
        <li>验证图片上传功能</li>
        <li>验证 SEO 配置功能</li>
        <li>验证发布流程功能</li>
    </ul>

    <h3>技术栈</h3>
    <p>本系统使用以下技术：</p>
    <ul>
        <li>Python 3.12</li>
        <li>Playwright (浏览器自动化)</li>
        <li>Pydantic (数据验证)</li>
        <li>Pytest (测试框架)</li>
    </ul>

    <h3>测试内容</h3>
    <p>这个集成测试验证了以下功能点：</p>
    <ol>
        <li>WordPress 后台登录验证</li>
        <li>文章标题和内容填写</li>
        <li>图片上传到媒体库</li>
        <li>特色图片设置</li>
        <li>Yoast SEO 配置</li>
        <li>分类和标签添加</li>
        <li>文章发布</li>
    </ol>

    <blockquote>
        <p>注意：这是一个自动化测试生成的文章，用于验证系统功能。</p>
    </blockquote>

    <p>如果你看到这篇文章，说明 WordPress 自动化发布系统正在正常工作！</p>
    """ * 3  # 重复3次以满足最小字数要求

    return Article(
        id=9999,
        title="WordPress集成测试文章自动化发布系统功能验证",
        content_html=content_html,
        excerpt="这是一篇集成测试文章，用于验证WordPress自动化发布系统的各项功能是否正常工作，包括登录、创建文章、上传图片、配置SEO和发布等完整流程。",
        seo=valid_seo_data
    )


@pytest.fixture(scope="module")
def valid_metadata():
    """创建有效的元数据"""
    return ArticleMetadata(
        tags=["集成测试", "自动化", "Playwright"],
        categories=["测试"],
        publish_immediately=True
    )


# ==================== Integration Tests ====================

@pytest.mark.integration
@pytest.mark.asyncio
class TestWordPressIntegration:
    """WordPress 集成测试"""

    async def test_01_login_success(self, wordpress_url, credentials):
        """测试登录成功"""
        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            result = await provider.login(wordpress_url, credentials)

            assert result is True, "登录应该成功"

            # 验证当前 URL
            assert "wp-admin" in provider.page.url
            assert "wp-login.php" not in provider.page.url

        finally:
            await provider.cleanup()

    async def test_02_login_failure_wrong_password(self, wordpress_url):
        """测试登录失败（错误密码）"""
        provider = PlaywrightProvider()
        wrong_credentials = WordPressCredentials(
            username="admin",
            password="wrong_password_123"
        )

        try:
            await provider.initialize()

            with pytest.raises(Exception):
                await provider.login(wordpress_url, wrong_credentials)

        finally:
            await provider.cleanup()

    async def test_03_create_article_basic(self, wordpress_url, credentials, valid_article, valid_metadata):
        """测试创建文章（不含图片）"""
        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.login(wordpress_url, credentials)

            result = await provider.create_article(valid_article, valid_metadata)

            assert result is True, "文章创建应该成功"

            # 验证在编辑页面
            assert "post.php" in provider.page.url or "post-new.php" in provider.page.url

        finally:
            await provider.cleanup()

    async def test_04_configure_seo(self, wordpress_url, credentials, valid_article, valid_metadata, valid_seo_data):
        """测试 SEO 配置"""
        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.login(wordpress_url, credentials)
            await provider.create_article(valid_article, valid_metadata)

            result = await provider.configure_seo(valid_seo_data)

            assert result is True, "SEO 配置应该成功"

        finally:
            await provider.cleanup()

    async def test_05_upload_image(self, wordpress_url, credentials, valid_article, valid_metadata, test_image):
        """测试图片上传"""
        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.login(wordpress_url, credentials)
            await provider.create_article(valid_article, valid_metadata)

            # 上传图片
            uploaded_urls = await provider.upload_images([test_image])

            assert len(uploaded_urls) > 0, "应该成功上传至少一张图片"
            assert all(url for url in uploaded_urls), "所有上传的图片应该有 URL"

        finally:
            await provider.cleanup()

    async def test_06_set_featured_image(self, wordpress_url, credentials, valid_article, valid_metadata, test_image):
        """测试设置特色图片"""
        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.login(wordpress_url, credentials)
            await provider.create_article(valid_article, valid_metadata)
            await provider.upload_images([test_image])

            result = await provider.set_featured_image(test_image)

            assert result is True, "设置特色图片应该成功"

        finally:
            await provider.cleanup()

    async def test_07_publish_article(self, wordpress_url, credentials, valid_article, valid_metadata):
        """测试发布文章"""
        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.login(wordpress_url, credentials)
            await provider.create_article(valid_article, valid_metadata)

            # 发布文章
            published_url = await provider.publish(valid_metadata)

            assert published_url, "发布后应该返回文章 URL"
            assert wordpress_url in published_url, "发布的 URL 应该属于测试 WordPress 站点"

        finally:
            await provider.cleanup()

    @pytest.mark.slow
    async def test_08_full_workflow(
        self,
        wordpress_url,
        credentials,
        valid_article,
        valid_metadata,
        test_image
    ):
        """测试完整发布工作流"""
        # 创建发布上下文
        context = PublishingContext(
            task_id=f"integration-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            article=valid_article,
            images=[test_image],
            metadata=valid_metadata,
            wordpress_url=wordpress_url,
            credentials=credentials
        )

        provider = PlaywrightProvider()

        try:
            # 执行完整发布流程
            result = await provider.publish_article(context)

            # 验证结果
            assert result.success is True, "发布应该成功"
            assert result.url is not None, "应该返回文章 URL"
            assert result.error is None, "不应该有错误"
            assert result.task_id == context.task_id, "任务 ID 应该匹配"
            assert result.provider_used == "PlaywrightProvider", "应该使用 Playwright Provider"

            # 验证文章 URL
            assert wordpress_url in result.url, "文章 URL 应该属于测试站点"

            print(f"\n✅ 文章发布成功: {result.url}")
            print(f"⏱️  发布耗时: {result.duration_seconds:.2f} 秒")

        finally:
            # 清理不需要，因为 publish_article 已经处理了
            pass


# ==================== Selector Validation Tests ====================

@pytest.mark.integration
@pytest.mark.validator
@pytest.mark.asyncio
class TestSelectorValidation:
    """选择器验证测试 - 确保所有 CSS 选择器在实际 WordPress 中有效"""

    async def test_validate_login_selectors(self, wordpress_url):
        """验证登录页面选择器"""
        from src.config.loader import config

        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.page.goto(f"{wordpress_url}/wp-login.php")

            # 验证关键选择器存在
            username_selector = config.get_selector('login', 'username_input')
            password_selector = config.get_selector('login', 'password_input')
            submit_selector = config.get_selector('login', 'submit_button')

            assert await provider.page.query_selector(username_selector), f"用户名输入框选择器无效: {username_selector}"
            assert await provider.page.query_selector(password_selector), f"密码输入框选择器无效: {password_selector}"
            assert await provider.page.query_selector(submit_selector), f"登录按钮选择器无效: {submit_selector}"

        finally:
            await provider.cleanup()

    async def test_validate_editor_selectors(self, wordpress_url, credentials):
        """验证编辑器选择器"""
        from src.config.loader import config

        provider = PlaywrightProvider()

        try:
            await provider.initialize()
            await provider.login(wordpress_url, credentials)

            # 导航到新建文章页面
            await provider.page.goto(f"{wordpress_url}/wp-admin/post-new.php")
            await provider.page.wait_for_load_state('networkidle')

            # 验证编辑器选择器
            title_selector = config.get_selector('editor', 'classic', 'title_input')

            assert await provider.page.query_selector(title_selector), f"标题输入框选择器无效: {title_selector}"

        finally:
            await provider.cleanup()


# ==================== Performance Tests ====================

@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.asyncio
class TestPerformance:
    """性能测试"""

    async def test_publish_within_target_time(
        self,
        wordpress_url,
        credentials,
        valid_article,
        valid_metadata,
        test_image
    ):
        """测试发布是否在目标时间内完成（180秒）"""
        context = PublishingContext(
            task_id=f"perf-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            article=valid_article,
            images=[test_image],
            metadata=valid_metadata,
            wordpress_url=wordpress_url,
            credentials=credentials
        )

        provider = PlaywrightProvider()

        result = await provider.publish_article(context)

        assert result.success is True, "发布应该成功"
        assert result.duration_seconds < 180, f"发布时间应该小于180秒，实际: {result.duration_seconds:.2f}秒"

        print(f"\n⏱️  发布耗时: {result.duration_seconds:.2f} 秒 (目标: < 180 秒)")
