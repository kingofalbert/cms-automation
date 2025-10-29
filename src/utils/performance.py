"""
性能优化工具
提供选择器缓存、性能追踪、并行处理等优化功能
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, error: Optional[str] = None):
        """完成计时"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'operation': self.operation_name,
            'duration_ms': round(self.duration_ms, 2) if self.duration_ms else None,
            'success': self.success,
            'error': self.error,
            'metadata': self.metadata,
            'timestamp': datetime.fromtimestamp(self.start_time).isoformat()
        }


class PerformanceTracker:
    """
    性能追踪器
    记录和分析所有操作的性能指标
    """

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)

    def start_operation(self, operation_name: str, **metadata) -> PerformanceMetrics:
        """开始追踪操作"""
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata
        )
        self.metrics.append(metric)
        return metric

    def record_operation(self, operation_name: str, duration_ms: float, success: bool = True):
        """记录操作性能"""
        if success:
            self.operation_stats[operation_name].append(duration_ms)

    def get_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计"""
        if operation_name:
            durations = self.operation_stats.get(operation_name, [])
            if not durations:
                return {}

            return {
                'operation': operation_name,
                'count': len(durations),
                'avg_ms': round(sum(durations) / len(durations), 2),
                'min_ms': round(min(durations), 2),
                'max_ms': round(max(durations), 2),
                'total_ms': round(sum(durations), 2)
            }
        else:
            # 所有操作的统计
            return {
                op: self.get_stats(op)
                for op in self.operation_stats.keys()
            }

    def get_total_duration(self) -> float:
        """获取总耗时（毫秒）"""
        return sum(
            metric.duration_ms
            for metric in self.metrics
            if metric.duration_ms is not None
        )

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_operations = len(self.metrics)
        successful_operations = sum(1 for m in self.metrics if m.success)
        failed_operations = total_operations - successful_operations

        return {
            'total_operations': total_operations,
            'successful': successful_operations,
            'failed': failed_operations,
            'success_rate': round(successful_operations / total_operations * 100, 2) if total_operations > 0 else 0,
            'total_duration_ms': round(self.get_total_duration(), 2),
            'operation_stats': self.get_stats()
        }

    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.operation_stats.clear()


class SelectorCache:
    """
    选择器缓存
    缓存已验证的选择器，避免重复查找
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Args:
            ttl_seconds: 缓存过期时间（秒），默认 5 分钟
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[str]:
        """获取缓存的选择器"""
        if key not in self.cache:
            self.miss_count += 1
            return None

        entry = self.cache[key]

        # 检查是否过期
        if time.time() - entry['timestamp'] > self.ttl_seconds:
            del self.cache[key]
            self.miss_count += 1
            return None

        self.hit_count += 1
        return entry['selector']

    def set(self, key: str, selector: str):
        """设置选择器缓存"""
        self.cache[key] = {
            'selector': selector,
            'timestamp': time.time()
        }

    def invalidate(self, key: Optional[str] = None):
        """清除缓存"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return round(self.hit_count / total * 100, 2)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'hits': self.hit_count,
            'misses': self.miss_count,
            'hit_rate': self.get_hit_rate(),
            'cached_items': len(self.cache)
        }


class BatchProcessor:
    """
    批处理器
    对独立操作进行并行处理
    """

    @staticmethod
    async def run_parallel(tasks: List[Callable], max_concurrent: int = 5) -> List[Any]:
        """
        并行执行任务

        Args:
            tasks: 任务列表（async 函数）
            max_concurrent: 最大并发数

        Returns:
            结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_task(task):
            async with semaphore:
                return await task()

        results = await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True
        )

        return results

    @staticmethod
    async def run_sequential_with_delay(
        tasks: List[Callable],
        delay_ms: int = 100
    ) -> List[Any]:
        """
        顺序执行任务（带延迟）

        Args:
            tasks: 任务列表
            delay_ms: 任务间延迟（毫秒）

        Returns:
            结果列表
        """
        results = []

        for i, task in enumerate(tasks):
            result = await task()
            results.append(result)

            # 最后一个任务不延迟
            if i < len(tasks) - 1:
                await asyncio.sleep(delay_ms / 1000)

        return results


class OptimizedWaiter:
    """
    优化的等待器
    使用智能等待策略减少不必要的等待时间
    """

    @staticmethod
    async def wait_for_any(
        page,
        selectors: List[str],
        timeout_ms: int = 30000,
        check_interval_ms: int = 100
    ) -> Optional[str]:
        """
        等待任意一个选择器出现（返回第一个匹配的）

        Args:
            page: Playwright Page 对象
            selectors: 选择器列表
            timeout_ms: 总超时时间
            check_interval_ms: 检查间隔

        Returns:
            成功的选择器，如果都失败则返回 None
        """
        start_time = time.time()

        while (time.time() - start_time) * 1000 < timeout_ms:
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        logger.debug(f"Element found with selector: {selector}")
                        return selector
                except Exception:
                    pass

            await asyncio.sleep(check_interval_ms / 1000)

        logger.warning(f"No element found from selectors: {selectors}")
        return None

    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool],
        timeout_ms: int = 30000,
        check_interval_ms: int = 100,
        error_message: str = "Condition not met"
    ):
        """
        等待条件满足

        Args:
            condition: 条件函数（返回 bool）
            timeout_ms: 超时时间
            check_interval_ms: 检查间隔
            error_message: 错误消息
        """
        start_time = time.time()

        while (time.time() - start_time) * 1000 < timeout_ms:
            try:
                if await condition():
                    return
            except Exception:
                pass

            await asyncio.sleep(check_interval_ms / 1000)

        raise TimeoutError(error_message)


# 全局性能追踪器实例
_global_tracker = PerformanceTracker()


def get_global_tracker() -> PerformanceTracker:
    """获取全局性能追踪器"""
    return _global_tracker


def reset_global_tracker():
    """重置全局性能追踪器"""
    _global_tracker.reset()
