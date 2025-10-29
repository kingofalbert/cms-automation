"""
Prometheus 指标收集器
监控发布系统的性能和可靠性
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== Prometheus Metrics ====================

# 文章发布指标
article_published_total = Counter(
    'article_published_total',
    'Total number of articles published',
    ['status', 'provider']  # status: success/failed, provider: playwright/computer_use
)

article_publish_duration_seconds = Histogram(
    'article_publish_duration_seconds',
    'Time spent publishing an article',
    ['provider'],
    buckets=(30, 60, 90, 120, 180, 240, 300)  # 30s 到 5 分钟
)

# Provider 性能指标
provider_operation_duration_seconds = Histogram(
    'provider_operation_duration_seconds',
    'Time spent on provider operations',
    ['operation', 'provider'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30)  # 0.1s 到 30s
)

provider_operation_errors_total = Counter(
    'provider_operation_errors_total',
    'Total number of provider operation errors',
    ['operation', 'provider', 'error_type']
)

# 降级指标
provider_fallback_total = Counter(
    'provider_fallback_total',
    'Total number of provider fallbacks',
    ['from_provider', 'to_provider', 'reason']
)

# 选择器缓存指标
selector_cache_hits_total = Counter(
    'selector_cache_hits_total',
    'Total number of selector cache hits'
)

selector_cache_misses_total = Counter(
    'selector_cache_misses_total',
    'Total number of selector cache misses'
)

selector_cache_size = Gauge(
    'selector_cache_size',
    'Current number of cached selectors'
)

# 成本追踪指标
cost_estimate_dollars = Counter(
    'cost_estimate_dollars',
    'Estimated cost in dollars',
    ['provider', 'operation_type']
)

# API 请求指标
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status_code']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'Time spent processing API requests',
    ['endpoint', 'method'],
    buckets=(0.1, 0.5, 1, 2, 5, 10)
)

# 任务队列指标
task_queue_size = Gauge(
    'task_queue_size',
    'Current number of tasks in queue',
    ['status']  # pending/running/completed/failed
)

# 系统信息
system_info = Info(
    'publishing_system',
    'Information about the publishing system'
)


class MetricsCollector:
    """
    指标收集器
    提供便捷的方法来记录各种指标
    """

    def __init__(self):
        self.current_tasks: Dict[str, datetime] = {}
        self._initialize_system_info()

    def _initialize_system_info(self):
        """初始化系统信息"""
        system_info.info({
            'version': '1.0.0',
            'phase': '2',
            'primary_provider': 'playwright',
            'fallback_provider': 'computer_use'
        })

    # ==================== 文章发布指标 ====================

    def record_article_published(self, success: bool, provider: str, duration_seconds: float):
        """
        记录文章发布

        Args:
            success: 是否成功
            provider: 使用的 provider
            duration_seconds: 耗时（秒）
        """
        status = 'success' if success else 'failed'
        article_published_total.labels(status=status, provider=provider).inc()
        article_publish_duration_seconds.labels(provider=provider).observe(duration_seconds)

        logger.info(
            f"Article published: status={status}, provider={provider}, "
            f"duration={duration_seconds:.2f}s"
        )

    # ==================== Provider 操作指标 ====================

    def record_operation(
        self,
        operation: str,
        provider: str,
        duration_seconds: float,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """
        记录 Provider 操作

        Args:
            operation: 操作名称（如 "fill_input", "click_button"）
            provider: Provider 名称
            duration_seconds: 耗时
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        provider_operation_duration_seconds.labels(
            operation=operation,
            provider=provider
        ).observe(duration_seconds)

        if not success and error_type:
            provider_operation_errors_total.labels(
                operation=operation,
                provider=provider,
                error_type=error_type
            ).inc()

    # ==================== 降级指标 ====================

    def record_fallback(self, from_provider: str, to_provider: str, reason: str):
        """
        记录 Provider 降级

        Args:
            from_provider: 原 Provider
            to_provider: 降级到的 Provider
            reason: 降级原因
        """
        provider_fallback_total.labels(
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason
        ).inc()

        logger.warning(
            f"Provider fallback: {from_provider} -> {to_provider}, reason: {reason}"
        )

    # ==================== 选择器缓存指标 ====================

    def record_cache_hit(self):
        """记录缓存命中"""
        selector_cache_hits_total.inc()

    def record_cache_miss(self):
        """记录缓存未命中"""
        selector_cache_misses_total.inc()

    def update_cache_size(self, size: int):
        """更新缓存大小"""
        selector_cache_size.set(size)

    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        hits = selector_cache_hits_total._value.get()
        misses = selector_cache_misses_total._value.get()
        total = hits + misses

        if total == 0:
            return 0.0

        return round(hits / total * 100, 2)

    # ==================== 成本追踪 ====================

    def record_cost(self, provider: str, operation_type: str, cost_dollars: float):
        """
        记录成本

        Args:
            provider: Provider 名称
            operation_type: 操作类型（如 "publish", "upload_image"）
            cost_dollars: 成本（美元）
        """
        cost_estimate_dollars.labels(
            provider=provider,
            operation_type=operation_type
        ).inc(cost_dollars)

    def estimate_publish_cost(self, provider: str, has_images: bool = False) -> float:
        """
        估算发布成本

        Args:
            provider: Provider 名称
            has_images: 是否包含图片

        Returns:
            估算成本（美元）
        """
        if provider == 'playwright':
            # Playwright 本地执行，成本极低
            base_cost = 0.02
            image_cost = 0.005 if has_images else 0
            total_cost = base_cost + image_cost
        elif provider == 'computer_use':
            # Computer Use API 成本
            base_cost = 0.15  # 基础文本操作
            image_cost = 0.05 if has_images else 0
            total_cost = base_cost + image_cost
        else:
            total_cost = 0.0

        # 记录成本
        if total_cost > 0:
            self.record_cost(provider, 'publish', total_cost)

        return total_cost

    # ==================== API 指标 ====================

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_seconds: float
    ):
        """
        记录 API 请求

        Args:
            endpoint: API 端点
            method: HTTP 方法
            status_code: 状态码
            duration_seconds: 耗时
        """
        api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status_code=str(status_code)
        ).inc()

        api_request_duration_seconds.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration_seconds)

    # ==================== 任务队列指标 ====================

    def update_task_queue(self, pending: int, running: int, completed: int, failed: int):
        """
        更新任务队列指标

        Args:
            pending: 待处理数量
            running: 运行中数量
            completed: 已完成数量
            failed: 已失败数量
        """
        task_queue_size.labels(status='pending').set(pending)
        task_queue_size.labels(status='running').set(running)
        task_queue_size.labels(status='completed').set(completed)
        task_queue_size.labels(status='failed').set(failed)

    # ==================== 便捷方法 ====================

    def get_summary_stats(self) -> Dict:
        """获取摘要统计"""
        try:
            total_published = article_published_total._metrics.get(('success', 'playwright'), Counter._value).get()
            total_failed = article_published_total._metrics.get(('failed', 'playwright'), Counter._value).get()
            fallback_count = sum(
                metric._value.get()
                for metric in provider_fallback_total._metrics.values()
            )

            return {
                'total_published': total_published,
                'total_failed': total_failed,
                'success_rate': round(total_published / (total_published + total_failed) * 100, 2) if (total_published + total_failed) > 0 else 0,
                'fallback_count': fallback_count,
                'cache_hit_rate': self.get_cache_hit_rate()
            }
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {}


# 全局指标收集器实例
_global_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    return _global_metrics_collector
