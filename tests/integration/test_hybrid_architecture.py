"""
集成测试：混合架构验证
测试 Playwright + Computer Use 混合架构的完整功能
Sprint 6: 验证性能优化和降级机制
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.orchestrator.publishing_orchestrator import (
    PublishingOrchestrator,
    PublishingContext,
    PublishResult
)
from src.providers.base_provider import ElementNotFoundError, ProviderError
from src.utils.publishing_safety import PublishingIntent
from src.utils.metrics import get_metrics_collector


# ==================== 测试夹具 ====================

@pytest.fixture
def article_data():
    """测试文章数据"""
    return {
        'title': '集成测试文章 - ' + datetime.now().strftime('%Y%m%d%H%M%S'),
        'content': '<p>这是一篇用于集成测试的文章。</p><h2>测试章节</h2><p>更多测试内容。</p>',
        'seo': {
            'focus_keyword': '集成测试',
            'meta_title': '集成测试文章标题（50-60字符之间的完整标题用于测试）',
            'meta_description': '这是一篇用于集成测试的文章，验证 Playwright 和 Computer Use 混合架构的完整功能，包括性能优化和降级机制。（150-160字符）'
        }
    }


@pytest.fixture
def metadata():
    """测试元数据"""
    return {
        'tags': ['集成测试', '自动化', 'Sprint6'],
        'categories': ['技术'],
        'images': []
    }


@pytest.fixture
def credentials():
    """测试凭证"""
    return {
        'username': 'testadmin',
        'password': 'testpass123'
    }


@pytest.fixture
def mock_playwright_provider():
    """Mock Playwright Provider"""
    provider = Mock()
    provider.initialize = AsyncMock()
    provider.close = AsyncMock()
    provider.navigate_to = AsyncMock()
    provider.fill_input = AsyncMock()
    provider.fill_textarea = AsyncMock()
    provider.click_button = AsyncMock()
    provider.wait_for_element = AsyncMock()
    provider.wait_for_success_message = AsyncMock()
    provider.get_cookies = AsyncMock(return_value=[
        {'name': 'wordpress_test_cookie', 'value': 'test123', 'domain': 'localhost'}
    ])
    provider.get_published_url = AsyncMock(return_value='http://localhost:8080/test-article')
    provider.navigate_to_new_post = AsyncMock()
    provider.clean_html_entities = AsyncMock()
    provider.verify_draft_status = AsyncMock(return_value=True)
    provider.verify_content_saved = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_computer_use_provider():
    """Mock Computer Use Provider"""
    provider = Mock()
    provider.initialize = AsyncMock()
    provider.close = AsyncMock()
    provider.navigate_to = AsyncMock()
    provider.fill_input = AsyncMock()
    provider.fill_textarea = AsyncMock()
    provider.click_button = AsyncMock()
    provider.wait_for_element = AsyncMock()
    provider.wait_for_success_message = AsyncMock()
    provider.get_cookies = AsyncMock(return_value=[])
    provider.get_published_url = AsyncMock(return_value='http://localhost:8080/test-article-cu')
    provider.navigate_to_new_post = AsyncMock()
    provider.clean_html_entities = AsyncMock()
    provider.verify_draft_status = AsyncMock(return_value=True)
    provider.verify_content_saved = AsyncMock(return_value=True)
    return provider


# ==================== 测试场景 ====================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_playwright_only_publish(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 1: Playwright Provider 独立发布
    验证 Playwright Provider 能够独立完成发布流程
    """
    # 创建 Orchestrator（仅 Playwright）
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        computer_use_provider=None,
        enable_safety_checks=True
    )

    # 执行发布
    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    # 验证结果
    assert result.success is True
    assert result.provider_used == 'playwright'
    assert result.fallback_triggered is False
    assert result.url == 'http://localhost:8080/test-article'
    assert result.duration_seconds > 0

    # 验证调用流程
    mock_playwright_provider.initialize.assert_called_once()
    mock_playwright_provider.navigate_to.assert_called()
    mock_playwright_provider.fill_input.assert_called()
    mock_playwright_provider.click_button.assert_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fallback_to_computer_use(
    mock_playwright_provider,
    mock_computer_use_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 2: 降级机制 - Playwright 失败后切换到 Computer Use
    验证降级机制能够正常工作，包括 Cookie 传递
    """
    # 配置 Playwright 失败（连续 3 次）
    mock_playwright_provider.fill_input.side_effect = ElementNotFoundError("元素未找到")

    # 创建 Orchestrator（混合架构）
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        computer_use_provider=mock_computer_use_provider,
        max_retries=3,
        enable_safety_checks=True
    )

    # 执行发布
    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    # 验证结果
    assert result.success is True
    assert result.provider_used == 'computer_use'
    assert result.fallback_triggered is True
    assert result.url == 'http://localhost:8080/test-article-cu'

    # 验证 Playwright 尝试了多次
    assert mock_playwright_provider.fill_input.call_count >= 3

    # 验证切换到 Computer Use
    mock_computer_use_provider.initialize.assert_called_once()

    # 验证 Cookie 传递
    init_call_args = mock_computer_use_provider.initialize.call_args
    assert 'cookies' in init_call_args.kwargs
    cookies = init_call_args.kwargs['cookies']
    assert len(cookies) > 0
    assert cookies[0]['name'] == 'wordpress_test_cookie'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_safety_validation_blocks_publish(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 3: 安全验证阻止发布
    验证安全检查能够阻止不安全的发布操作
    """
    # 修改文章数据为不合法（标题过短）
    invalid_article = {
        'title': 'Test',  # 过短
        'content': '<p>测试</p>',  # 过短
        'seo': article_data['seo']
    }

    # 创建 Orchestrator
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        enable_safety_checks=True
    )

    # 执行发布（应该失败）
    result = await orchestrator.publish_article(
        article=invalid_article,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    # 验证结果
    assert result.success is False
    assert '安全检查失败' in result.error or '内容过短' in result.error or '标题过短' in result.error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_draft_save_on_error(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 4: 错误时保存为草稿
    验证发布失败时能够自动保存为草稿
    """
    # 配置发布按钮点击失败
    mock_playwright_provider.click_button.side_effect = lambda btn: (
        AsyncMock()() if btn != 'publish' else (_ for _ in ()).throw(ProviderError("发布失败"))
    )

    # 创建 Orchestrator
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        enable_safety_checks=True
    )

    # 执行发布
    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    # 验证保存草稿被调用
    save_draft_calls = [
        call for call in mock_playwright_provider.click_button.call_args_list
        if len(call.args) > 0 and call.args[0] == 'save_draft'
    ]
    assert len(save_draft_calls) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance_tracking(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 5: 性能追踪
    验证性能指标被正确收集
    """
    # 获取指标收集器
    metrics = get_metrics_collector()

    # 创建 Orchestrator
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        enable_safety_checks=True
    )

    # 执行发布
    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    # 验证性能指标
    assert result.duration_seconds > 0

    # 验证成本估算
    cost = metrics.estimate_publish_cost('playwright', has_images=False)
    assert cost > 0
    assert cost < 0.05  # Playwright 成本应该很低


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_draft_intent(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 6: 仅保存草稿模式
    验证 SAVE_DRAFT 意图能够正确执行
    """
    # 创建 Orchestrator
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        enable_safety_checks=True
    )

    # 执行保存草稿
    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.SAVE_DRAFT
    )

    # 验证结果
    assert result.success is True

    # 验证没有点击发布按钮
    publish_calls = [
        call for call in mock_playwright_provider.click_button.call_args_list
        if len(call.args) > 0 and call.args[0] == 'publish'
    ]
    assert len(publish_calls) == 0

    # 验证点击了保存草稿按钮
    save_draft_calls = [
        call for call in mock_playwright_provider.click_button.call_args_list
        if len(call.args) > 0 and call.args[0] == 'save_draft'
    ]
    assert len(save_draft_calls) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_publishes(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 7: 并发发布
    验证系统能够处理多个并发发布请求
    """
    # 创建多个 Orchestrator 实例
    orchestrators = [
        PublishingOrchestrator(
            playwright_provider=mock_playwright_provider,
            enable_safety_checks=True
        )
        for _ in range(3)
    ]

    # 并发执行发布
    tasks = [
        orchestrator.publish_article(
            article={**article_data, 'title': f"{article_data['title']} - {i}"},
            metadata=metadata,
            wordpress_url='http://localhost:8080',
            credentials=credentials,
            intent=PublishingIntent.PUBLISH_NOW
        )
        for i, orchestrator in enumerate(orchestrators)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 验证所有请求都成功
    for result in results:
        assert not isinstance(result, Exception)
        assert result.success is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_mechanism(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    测试 8: 重试机制
    验证失败后能够正确重试
    """
    # 配置前 2 次失败，第 3 次成功
    call_count = {'count': 0}

    def failing_fill_input(field, value):
        call_count['count'] += 1
        if call_count['count'] < 3:
            raise ElementNotFoundError("元素未找到")
        return AsyncMock()()

    mock_playwright_provider.fill_input.side_effect = failing_fill_input

    # 创建 Orchestrator
    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        max_retries=3,
        enable_safety_checks=True
    )

    # 执行发布
    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    # 验证结果
    assert result.success is True
    assert call_count['count'] == 3  # 尝试了 3 次


# ==================== 性能基准测试 ====================

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_publish_performance_benchmark(
    mock_playwright_provider,
    article_data,
    metadata,
    credentials
):
    """
    性能基准测试：测量发布操作的性能
    目标：< 180 秒（3 分钟）
    """
    import time

    orchestrator = PublishingOrchestrator(
        playwright_provider=mock_playwright_provider,
        enable_safety_checks=True
    )

    start_time = time.time()

    result = await orchestrator.publish_article(
        article=article_data,
        metadata=metadata,
        wordpress_url='http://localhost:8080',
        credentials=credentials,
        intent=PublishingIntent.PUBLISH_NOW
    )

    duration = time.time() - start_time

    # 验证性能目标
    assert result.success is True
    assert duration < 180, f"发布耗时 {duration:.2f}秒，超过 3 分钟阈值"

    print(f"\n✅ 性能基准测试通过: {duration:.2f}秒")
    print(f"   目标: < 180 秒")
    print(f"   实际: {duration:.2f} 秒")
    print(f"   节省: {180 - duration:.2f} 秒")
