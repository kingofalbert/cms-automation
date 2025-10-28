"""
集成测试 04: 完整发布流程

测试使用 Publishing Orchestrator 的完整发布流程
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_full_publish_workflow(test_publishing_context):
    """测试完整的文章发布流程"""
    from src.orchestrator import PublishingOrchestrator
    from src.providers.playwright_provider import PlaywrightProvider

    # 创建 Provider 和 Orchestrator
    provider = PlaywrightProvider()
    orchestrator = PublishingOrchestrator(
        primary_provider=provider,
        max_retries=2,
        enable_fallback=False  # 集成测试中禁用降级
    )

    # 执行发布
    result = await orchestrator.publish_article(test_publishing_context)

    # 验证结果
    assert result.success is True, f"发布应该成功，错误: {result.error}"
    assert result.url is not None, "应该返回发布 URL"
    assert result.provider_used == "PlaywrightProvider", "应该使用 Playwright Provider"
    assert result.fallback_triggered is False, "不应该触发降级"

    # 验证所有阶段都完成
    expected_phases = ["initialize", "login", "article", "images", "seo", "publish"]
    assert orchestrator.completed_phases == expected_phases, \
        f"应该完成所有阶段，实际: {orchestrator.completed_phases}"

    # 验证发布时间
    assert result.duration_seconds > 0, "应该记录发布时间"
    assert result.duration_seconds < 120, "发布时间应该少于 2 分钟"

    print(f"\n发布成功！")
    print(f"  文章 URL: {result.url}")
    print(f"  耗时: {result.duration_seconds:.2f} 秒")
    print(f"  重试次数: {result.retry_count}")
    print(f"  完成阶段: {', '.join(orchestrator.completed_phases)}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_publish_without_images(test_publishing_context):
    """测试不包含图片的发布流程"""
    from src.orchestrator import PublishingOrchestrator
    from src.providers.playwright_provider import PlaywrightProvider

    # 移除图片
    test_publishing_context.images = []

    # 创建 Provider 和 Orchestrator
    provider = PlaywrightProvider()
    orchestrator = PublishingOrchestrator(
        primary_provider=provider,
        max_retries=2
    )

    # 执行发布
    result = await orchestrator.publish_article(test_publishing_context)

    # 验证结果
    assert result.success is True, "发布应该成功"

    # 验证没有图片上传阶段
    assert "images" not in orchestrator.completed_phases, \
        "不应该有图片上传阶段"

    print(f"\n无图片发布成功！")
    print(f"  文章 URL: {result.url}")
    print(f"  完成阶段: {', '.join(orchestrator.completed_phases)}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_publish_with_retry(test_publishing_context):
    """测试发布流程的重试机制"""
    from src.orchestrator import PublishingOrchestrator
    from src.providers.playwright_provider import PlaywrightProvider
    from unittest.mock import patch

    # 创建 Provider
    provider = PlaywrightProvider()

    # 创建 Orchestrator（允许重试）
    orchestrator = PublishingOrchestrator(
        primary_provider=provider,
        max_retries=3,
        enable_fallback=False
    )

    # Mock login 方法，让它第一次失败
    original_login = provider.login
    call_count = 0

    async def mock_login(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # 第一次失败
            from src.providers.base import LoginError
            raise LoginError("模拟登录失败")
        else:
            # 后续成功
            return await original_login(*args, **kwargs)

    with patch.object(provider, 'login', side_effect=mock_login):
        # 执行发布
        result = await orchestrator.publish_article(test_publishing_context)

    # 验证结果
    assert result.success is True, "发布应该最终成功"
    assert result.retry_count >= 1, "应该至少重试一次"

    print(f"\n重试测试成功！")
    print(f"  总重试次数: {result.retry_count}")
    print(f"  login 调用次数: {call_count}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_orchestrator_screenshot_creation(test_publishing_context):
    """测试 Orchestrator 是否创建了截图"""
    from src.orchestrator import PublishingOrchestrator
    from src.providers.playwright_provider import PlaywrightProvider
    from pathlib import Path

    # 创建 Provider 和 Orchestrator
    provider = PlaywrightProvider()
    orchestrator = PublishingOrchestrator(primary_provider=provider)

    # 移除图片以加快测试
    test_publishing_context.images = []

    # 执行发布
    result = await orchestrator.publish_article(test_publishing_context)

    assert result.success is True, "发布应该成功"

    # 检查截图目录
    screenshot_dir = Path("./screenshots")
    if screenshot_dir.exists():
        screenshots = list(screenshot_dir.glob(f"{test_publishing_context.task_id}*.png"))
        assert len(screenshots) > 0, "应该创建至少一个截图"
        print(f"\n创建了 {len(screenshots)} 个截图")
    else:
        pytest.skip("截图目录不存在")
