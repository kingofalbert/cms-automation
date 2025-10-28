"""
Unit Tests for Publishing Orchestrator

测试 PublishingOrchestrator 的核心功能（使用 Mock）
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path

from src.orchestrator import PublishingOrchestrator
from src.providers.base import (
    IPublishingProvider,
    LoginError,
    ArticleCreationError,
    PublishError
)
from src.models import (
    Article,
    SEOData,
    ImageAsset,
    ArticleMetadata,
    WordPressCredentials,
    PublishingContext,
    PublishResult
)


@pytest.fixture
def mock_primary_provider():
    """创建 Mock 主要 Provider"""
    provider = AsyncMock(spec=IPublishingProvider)
    provider.__class__.__name__ = "MockPlaywrightProvider"
    provider.initialize = AsyncMock()
    provider.cleanup = AsyncMock()
    provider.login = AsyncMock(return_value=True)
    provider.create_article = AsyncMock(return_value=True)
    provider.upload_images = AsyncMock(return_value=["http://example.com/image.jpg"])
    provider.set_featured_image = AsyncMock(return_value=True)
    provider.configure_seo = AsyncMock(return_value=True)
    provider.publish = AsyncMock(return_value="http://example.com/test-post/")
    provider.take_screenshot = AsyncMock(return_value="/path/to/screenshot.png")
    return provider


@pytest.fixture
def mock_fallback_provider():
    """创建 Mock 备用 Provider"""
    provider = AsyncMock(spec=IPublishingProvider)
    provider.__class__.__name__ = "MockComputerUseProvider"
    provider.initialize = AsyncMock()
    provider.cleanup = AsyncMock()
    provider.login = AsyncMock(return_value=True)
    provider.create_article = AsyncMock(return_value=True)
    provider.upload_images = AsyncMock(return_value=["http://example.com/image.jpg"])
    provider.set_featured_image = AsyncMock(return_value=True)
    provider.configure_seo = AsyncMock(return_value=True)
    provider.publish = AsyncMock(return_value="http://example.com/test-post-fallback/")
    provider.take_screenshot = AsyncMock(return_value="/path/to/screenshot.png")
    return provider


@pytest.fixture
def valid_publishing_context(tmp_path):
    """创建有效的发布上下文"""
    # 创建测试图片
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake image content")

    seo = SEOData(
        focus_keyword="测试关键字",
        meta_title="这是一个非常详细且完整符合长度要求的搜索引擎优化标题文本内容示例，字符数量必须精确控制在五十到六十个字符之间范围内",
        meta_description="这是一个完整符合搜索引擎优化最佳实践严格要求的网页元描述文本内容详细示例信息数据资料材料。本描述文本非常详细地说明了文章页面的核心主题内容和实际价值作用效果，能够帮助各大搜索引擎系统准确理解和索引页面主题内容，同时有效吸引目标用户主动点击访问浏览查看阅读使用网站系统平台产品服务功能特性优势亮点价值意义。"
    )

    article = Article(
        id=1,
        title="测试文章标题内容示例",
        content_html="<p>这是测试文章的完整内容部分。" * 20 + "</p>",
        excerpt="这是文章摘要部分",
        seo=seo
    )

    metadata = ArticleMetadata(
        tags=["测试", "自动化"],
        categories=["技术"],
        publish_immediately=True
    )

    credentials = WordPressCredentials(
        username="admin",
        password="password123"
    )

    return PublishingContext(
        task_id="test-task-123",
        article=article,
        images=[
            ImageAsset(
                file_path=str(image_file),
                alt_text="测试图片替代文字内容",
                title="测试图片",
                is_featured=True
            )
        ],
        metadata=metadata,
        wordpress_url="http://localhost:8000",
        credentials=credentials
    )


class TestPublishingOrchestratorBasic:
    """测试 Orchestrator 基础功能"""

    @pytest.mark.asyncio
    async def test_successful_publish(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试成功的发布流程"""
        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider,
            max_retries=3
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is True
        assert result.task_id == "test-task-123"
        assert result.url == "http://example.com/test-post/"
        assert result.provider_used == "MockPlaywrightProvider"
        assert result.fallback_triggered is False
        assert result.retry_count == 0

        # 验证所有阶段都被调用
        mock_primary_provider.initialize.assert_called()
        mock_primary_provider.login.assert_called_once()
        mock_primary_provider.create_article.assert_called_once()
        mock_primary_provider.upload_images.assert_called_once()
        mock_primary_provider.set_featured_image.assert_called_once()
        mock_primary_provider.configure_seo.assert_called_once()
        mock_primary_provider.publish.assert_called_once()
        mock_primary_provider.cleanup.assert_called()

    @pytest.mark.asyncio
    async def test_publish_without_images(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试无图片的发布流程"""
        # 移除图片
        valid_publishing_context.images = []

        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is True

        # 验证图片相关方法没有被调用
        mock_primary_provider.upload_images.assert_not_called()
        mock_primary_provider.set_featured_image.assert_not_called()


class TestPublishingOrchestratorRetry:
    """测试重试机制"""

    @pytest.mark.asyncio
    async def test_retry_on_failure_then_success(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试失败后重试并成功"""
        # 第一次调用失败，第二次成功
        mock_primary_provider.login.side_effect = [
            LoginError("连接超时"),
            True
        ]

        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider,
            max_retries=3
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is True
        assert result.retry_count == 1  # 重试了一次
        assert mock_primary_provider.login.call_count == 2  # 第一次失败，第二次成功

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试超过最大重试次数"""
        # 所有调用都失败
        mock_primary_provider.login.side_effect = LoginError("持续失败")

        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider,
            fallback_provider=None,  # 没有备用 Provider
            max_retries=2
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is False
        assert result.error is not None
        assert "持续失败" in result.error
        assert result.retry_count >= 2  # 至少重试了 2 次


class TestPublishingOrchestratorFallback:
    """测试降级机制"""

    @pytest.mark.asyncio
    async def test_fallback_triggered_on_primary_failure(
        self,
        mock_primary_provider,
        mock_fallback_provider,
        valid_publishing_context
    ):
        """测试主 Provider 失败时触发降级"""
        # 主 Provider 持续失败
        mock_primary_provider.login.side_effect = LoginError("主 Provider 失败")

        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider,
            fallback_provider=mock_fallback_provider,
            max_retries=2,
            enable_fallback=True
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is True
        assert result.fallback_triggered is True
        assert result.provider_used == "MockComputerUseProvider"
        assert result.url == "http://example.com/test-post-fallback/"

        # 验证主 Provider 被清理
        mock_primary_provider.cleanup.assert_called()

        # 验证备用 Provider 被初始化和使用
        mock_fallback_provider.initialize.assert_called()
        mock_fallback_provider.login.assert_called()

    @pytest.mark.asyncio
    async def test_fallback_disabled(
        self,
        mock_primary_provider,
        mock_fallback_provider,
        valid_publishing_context
    ):
        """测试禁用降级机制"""
        # 主 Provider 失败
        mock_primary_provider.login.side_effect = LoginError("主 Provider 失败")

        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider,
            fallback_provider=mock_fallback_provider,
            max_retries=1,
            enable_fallback=False  # 禁用降级
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is False
        assert result.fallback_triggered is False

        # 验证备用 Provider 没有被调用
        mock_fallback_provider.initialize.assert_not_called()
        mock_fallback_provider.login.assert_not_called()


class TestPublishingOrchestratorPhases:
    """测试各个阶段的执行"""

    @pytest.mark.asyncio
    async def test_all_phases_executed_in_order(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试所有阶段按顺序执行"""
        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证阶段执行顺序（通过 completed_phases 列表）
        assert result.success is True
        expected_phases = ["initialize", "login", "article", "images", "seo", "publish"]
        assert orchestrator.completed_phases == expected_phases

    @pytest.mark.asyncio
    async def test_phase_failure_stops_execution(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试阶段失败会停止执行"""
        # 文章创建阶段失败
        mock_primary_provider.create_article.side_effect = ArticleCreationError("创建失败")

        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider,
            fallback_provider=None,
            max_retries=1
        )

        result = await orchestrator.publish_article(valid_publishing_context)

        # 验证结果
        assert result.success is False

        # 验证后续阶段没有被执行
        mock_primary_provider.upload_images.assert_not_called()
        mock_primary_provider.configure_seo.assert_not_called()
        mock_primary_provider.publish.assert_not_called()


class TestPublishingOrchestratorAudit:
    """测试审计追踪"""

    @pytest.mark.asyncio
    async def test_completed_phases_tracking(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试已完成阶段的追踪"""
        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider
        )

        await orchestrator.publish_article(valid_publishing_context)

        # 验证完成的阶段列表
        expected_phases = ["initialize", "login", "article", "images", "seo", "publish"]
        assert orchestrator.completed_phases == expected_phases

    @pytest.mark.asyncio
    async def test_screenshots_taken(
        self,
        mock_primary_provider,
        valid_publishing_context
    ):
        """测试截图功能"""
        orchestrator = PublishingOrchestrator(
            primary_provider=mock_primary_provider
        )

        await orchestrator.publish_article(valid_publishing_context)

        # 验证截图被调用（每个阶段前后各一次）
        assert mock_primary_provider.take_screenshot.call_count >= 10  # 至少 5 个阶段 x 2
