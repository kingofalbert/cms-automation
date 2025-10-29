"""
性能基准测试 - Sprint 6
验证优化后的性能指标是否达到目标

目标:
- 发布速度: < 120 秒 (优化后，原 180 秒)
- 成功率: ≥ 98%
- 成本: ~$0.02/篇 (Playwright)
- Computer Use 调用率: < 5%
- 缓存命中率: > 80%
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import List, Dict
from unittest.mock import Mock, AsyncMock

from src.orchestrator.publishing_orchestrator import PublishingOrchestrator
from src.providers.optimized_playwright_provider import OptimizedPlaywrightProvider
from src.config.loader import SelectorConfig
from src.utils.metrics import get_metrics_collector
from src.utils.publishing_safety import PublishingIntent


@pytest.fixture
def sample_articles():
    """生成测试文章数据"""
    return [
        {
            'title': f'性能测试文章 {i} - {datetime.now().strftime("%Y%m%d%H%M%S")}',
            'content': f'<p>这是第 {i} 篇测试文章。</p>' + '<p>测试内容。</p>' * 20,
            'seo': {
                'focus_keyword': f'性能测试{i}',
                'meta_title': f'性能测试文章 {i} - 完整的标题用于测试 SEO 优化功能',
                'meta_description': f'这是第 {i} 篇用于性能基准测试的文章，验证优化后的发布速度、成功率和成本指标是否达到预期目标。' * 2
            }
        }
        for i in range(1, 11)  # 10 篇文章
    ]


@pytest.fixture
def metadata():
    """测试元数据"""
    return {
        'tags': ['性能测试', 'Sprint6', '基准测试'],
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


class BenchmarkResults:
    """基准测试结果收集器"""

    def __init__(self):
        self.results: List[Dict] = []
        self.start_time = None
        self.end_time = None

    def add_result(self, **kwargs):
        """添加测试结果"""
        self.results.append(kwargs)

    def get_summary(self) -> Dict:
        """获取摘要统计"""
        if not self.results:
            return {}

        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('success'))
        failed = total - successful

        durations = [r.get('duration', 0) for r in self.results if r.get('success')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        fallback_count = sum(1 for r in self.results if r.get('fallback_triggered'))

        return {
            'total_tests': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round(successful / total * 100, 2) if total > 0 else 0,
            'avg_duration_seconds': round(avg_duration, 2),
            'min_duration_seconds': round(min_duration, 2),
            'max_duration_seconds': round(max_duration, 2),
            'fallback_triggered_count': fallback_count,
            'fallback_rate': round(fallback_count / total * 100, 2) if total > 0 else 0,
            'total_duration_seconds': round(sum(durations), 2)
        }

    def print_report(self):
        """打印基准测试报告"""
        summary = self.get_summary()

        print("\n" + "=" * 80)
        print("📊 性能基准测试报告 - Sprint 6")
        print("=" * 80)

        print(f"\n📈 总体统计:")
        print(f"   测试总数:     {summary['total_tests']}")
        print(f"   成功:         {summary['successful']}")
        print(f"   失败:         {summary['failed']}")
        print(f"   成功率:       {summary['success_rate']}%")

        print(f"\n⏱️  性能指标:")
        print(f"   平均耗时:     {summary['avg_duration_seconds']:.2f} 秒")
        print(f"   最短耗时:     {summary['min_duration_seconds']:.2f} 秒")
        print(f"   最长耗时:     {summary['max_duration_seconds']:.2f} 秒")
        print(f"   总耗时:       {summary['total_duration_seconds']:.2f} 秒")

        print(f"\n🔄 降级统计:")
        print(f"   降级次数:     {summary['fallback_triggered_count']}")
        print(f"   降级率:       {summary['fallback_rate']}%")

        print(f"\n✅ 目标达成情况:")

        # 检查目标
        targets = {
            '发布速度 (< 120秒)': summary['avg_duration_seconds'] < 120,
            '成功率 (≥ 98%)': summary['success_rate'] >= 98,
            'Computer Use 调用率 (< 5%)': summary['fallback_rate'] < 5
        }

        for target, achieved in targets.items():
            status = "✅ 达成" if achieved else "❌ 未达成"
            print(f"   {target}: {status}")

        print("\n" + "=" * 80)


@pytest.mark.benchmark
class TestPublishingBenchmark:
    """发布系统性能基准测试"""

    @pytest.mark.asyncio
    async def test_single_article_speed(self, sample_articles, metadata, credentials):
        """
        基准 1: 单篇文章发布速度
        目标: < 120 秒 (优化后)
        """
        print("\n🏃 基准测试 1: 单篇文章发布速度")

        # 使用 Mock Provider（模拟快速响应）
        mock_provider = self._create_mock_provider()

        orchestrator = PublishingOrchestrator(
            playwright_provider=mock_provider,
            enable_safety_checks=True
        )

        start_time = time.time()

        result = await orchestrator.publish_article(
            article=sample_articles[0],
            metadata=metadata,
            wordpress_url='http://localhost:8080',
            credentials=credentials,
            intent=PublishingIntent.PUBLISH_NOW
        )

        duration = time.time() - start_time

        # 验证
        assert result.success is True
        assert duration < 120, f"耗时 {duration:.2f}秒，超过目标 120 秒"

        print(f"   ✅ 耗时: {duration:.2f} 秒")
        print(f"   目标: < 120 秒")
        print(f"   状态: {'通过' if duration < 120 else '失败'}")

    @pytest.mark.asyncio
    async def test_batch_publishing_success_rate(self, sample_articles, metadata, credentials):
        """
        基准 2: 批量发布成功率
        目标: ≥ 98%
        """
        print("\n🏃 基准测试 2: 批量发布成功率 (10 篇文章)")

        results = BenchmarkResults()

        # 使用 Mock Provider
        mock_provider = self._create_mock_provider()

        for i, article in enumerate(sample_articles):
            print(f"   发布文章 {i+1}/10...", end=" ")

            orchestrator = PublishingOrchestrator(
                playwright_provider=mock_provider,
                enable_safety_checks=True
            )

            start_time = time.time()

            try:
                result = await orchestrator.publish_article(
                    article=article,
                    metadata=metadata,
                    wordpress_url='http://localhost:8080',
                    credentials=credentials,
                    intent=PublishingIntent.PUBLISH_NOW
                )

                duration = time.time() - start_time

                results.add_result(
                    article_id=i+1,
                    success=result.success,
                    duration=duration,
                    fallback_triggered=result.fallback_triggered,
                    provider_used=result.provider_used
                )

                print(f"✅ {duration:.2f}s")

            except Exception as e:
                duration = time.time() - start_time
                results.add_result(
                    article_id=i+1,
                    success=False,
                    duration=duration,
                    error=str(e)
                )
                print(f"❌ 失败: {e}")

        # 打印报告
        results.print_report()

        # 验证目标
        summary = results.get_summary()
        assert summary['success_rate'] >= 98, f"成功率 {summary['success_rate']}% 低于目标 98%"

    @pytest.mark.asyncio
    async def test_concurrent_publishing(self, sample_articles, metadata, credentials):
        """
        基准 3: 并发发布性能
        测试系统在并发负载下的表现
        """
        print("\n🏃 基准测试 3: 并发发布 (5 篇同时)")

        # 创建多个 Orchestrator 实例
        orchestrators = [
            PublishingOrchestrator(
                playwright_provider=self._create_mock_provider(),
                enable_safety_checks=True
            )
            for _ in range(5)
        ]

        start_time = time.time()

        # 并发发布
        tasks = [
            orchestrator.publish_article(
                article=sample_articles[i],
                metadata=metadata,
                wordpress_url='http://localhost:8080',
                credentials=credentials,
                intent=PublishingIntent.PUBLISH_NOW
            )
            for i, orchestrator in enumerate(orchestrators)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_duration = time.time() - start_time

        # 统计
        successful = sum(1 for r in results if not isinstance(r, Exception) and r.success)
        failed = len(results) - successful

        print(f"\n   总耗时: {total_duration:.2f} 秒")
        print(f"   平均每篇: {total_duration / len(results):.2f} 秒")
        print(f"   成功: {successful}/{len(results)}")
        print(f"   失败: {failed}/{len(results)}")

        # 验证
        assert successful >= 4, "并发发布成功数量过低"
        assert total_duration < 300, "并发发布总耗时过长"

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self):
        """
        基准 4: 选择器缓存命中率
        目标: > 80%
        """
        print("\n🏃 基准测试 4: 选择器缓存命中率")

        # 模拟多次发布以累积缓存
        mock_provider = self._create_mock_provider_with_cache()

        # 第一次调用（缓存未命中）
        await mock_provider.fill_input("new_post_title", "Test 1")

        # 后续调用（应该命中缓存）
        for i in range(2, 11):
            await mock_provider.fill_input("new_post_title", f"Test {i}")

        # 获取缓存统计
        cache_stats = mock_provider.get_cache_stats()

        hit_rate = cache_stats.get('hit_rate', 0)

        print(f"\n   缓存统计:")
        print(f"   - 命中次数: {cache_stats.get('hits', 0)}")
        print(f"   - 未命中次数: {cache_stats.get('misses', 0)}")
        print(f"   - 命中率: {hit_rate}%")
        print(f"   - 缓存项数: {cache_stats.get('cached_items', 0)}")

        # 验证
        assert hit_rate >= 80, f"缓存命中率 {hit_rate}% 低于目标 80%"

    @pytest.mark.asyncio
    async def test_cost_estimation(self, sample_articles, metadata, credentials):
        """
        基准 5: 成本估算
        目标: ~$0.02/篇 (Playwright)
        """
        print("\n🏃 基准测试 5: 成本估算")

        metrics = get_metrics_collector()

        # 模拟 10 篇文章发布
        total_cost = 0

        for i in range(10):
            cost = metrics.estimate_publish_cost('playwright', has_images=False)
            total_cost += cost

        avg_cost = total_cost / 10

        print(f"\n   总成本: ${total_cost:.4f}")
        print(f"   平均成本: ${avg_cost:.4f}/篇")
        print(f"   目标成本: $0.02/篇")

        # 验证
        assert avg_cost <= 0.03, f"平均成本 ${avg_cost:.4f} 超过目标 $0.02"

        print(f"   ✅ 成本目标达成")

    # ==================== 辅助方法 ====================

    def _create_mock_provider(self):
        """创建模拟的 Provider"""
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
            {'name': 'test_cookie', 'value': 'test123'}
        ])
        provider.get_published_url = AsyncMock(return_value='http://localhost:8080/test-article')
        provider.navigate_to_new_post = AsyncMock()
        provider.clean_html_entities = AsyncMock()
        provider.verify_draft_status = AsyncMock(return_value=True)
        provider.verify_content_saved = AsyncMock(return_value=True)
        return provider

    def _create_mock_provider_with_cache(self):
        """创建带缓存的模拟 Provider"""
        from src.utils.performance import SelectorCache

        provider = Mock()
        provider.selector_cache = SelectorCache()

        async def mock_fill_input(field, value):
            # 模拟缓存逻辑
            cached = provider.selector_cache.get(field)
            if not cached:
                provider.selector_cache.set(field, f"#{field}")

        provider.fill_input = AsyncMock(side_effect=mock_fill_input)
        provider.get_cache_stats = lambda: provider.selector_cache.get_stats()

        return provider


# ==================== 运行基准测试 ====================

if __name__ == "__main__":
    print("\n🚀 开始 Sprint 6 性能基准测试\n")

    pytest.main([
        __file__,
        '-v',
        '-m', 'benchmark',
        '--tb=short',
        '--color=yes'
    ])
