"""
重试机制单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock

from src.utils.retry import (
    async_retry,
    RetryConfig,
    RetryableOperation,
    DEFAULT_RETRY_CONFIG,
    AGGRESSIVE_RETRY_CONFIG,
    CONSERVATIVE_RETRY_CONFIG
)


class TestRetryConfig:
    """测试重试配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        assert config.max_retries == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_calculate_delay_exponential(self):
        """测试指数退避延迟计算"""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False
        )

        # 第 1 次重试: 1.0 * (2^0) = 1.0
        assert config.calculate_delay(0) == 1.0

        # 第 2 次重试: 1.0 * (2^1) = 2.0
        assert config.calculate_delay(1) == 2.0

        # 第 3 次重试: 1.0 * (2^2) = 4.0
        assert config.calculate_delay(2) == 4.0

        # 第 4 次重试: 1.0 * (2^3) = 8.0
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_max_limit(self):
        """测试延迟上限"""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False
        )

        # 超过上限应该被限制在 max_delay
        delay = config.calculate_delay(10)  # 1.0 * (2^10) = 1024.0 > 10.0
        assert delay == 10.0

    def test_calculate_delay_with_jitter(self):
        """测试带抖动的延迟计算"""
        config = RetryConfig(
            initial_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )

        # 带抖动的延迟应该在 [5.0, 15.0] 范围内（0.5 到 1.5 倍）
        delay = config.calculate_delay(0)
        assert 5.0 <= delay <= 15.0


@pytest.mark.asyncio
class TestAsyncRetryDecorator:
    """测试异步重试装饰器"""

    async def test_success_no_retry(self):
        """测试成功执行，无需重试"""
        call_count = 0

        @async_retry(max_retries=3)
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_operation()

        assert result == "success"
        assert call_count == 1

    async def test_retry_until_success(self):
        """测试重试直到成功"""
        call_count = 0

        @async_retry(max_retries=3, initial_delay=0.1)
        async def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("还没成功")
            return "success"

        result = await sometimes_fails()

        assert result == "success"
        assert call_count == 3

    async def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0

        @async_retry(max_retries=2, initial_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("总是失败")

        with pytest.raises(ValueError, match="总是失败"):
            await always_fails()

        # 应该调用 3 次（初始 1 次 + 重试 2 次）
        assert call_count == 3

    async def test_specific_exception_only(self):
        """测试只重试特定异常"""
        call_count = 0

        @async_retry(
            max_retries=3,
            initial_delay=0.1,
            exceptions=(ValueError,)
        )
        async def raise_runtime_error():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("不会重试")

        # RuntimeError 不在重试列表中，应该立即抛出
        with pytest.raises(RuntimeError, match="不会重试"):
            await raise_runtime_error()

        # 只调用一次，没有重试
        assert call_count == 1

    async def test_on_retry_callback(self):
        """测试重试回调"""
        call_count = 0
        retry_callbacks = []

        def on_retry_func(func, exception, retry_count):
            retry_callbacks.append({
                'func': func.__name__,
                'exception': str(exception),
                'retry_count': retry_count
            })

        @async_retry(
            max_retries=2,
            initial_delay=0.1,
            on_retry=on_retry_func
        )
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError(f"失败 {call_count}")
            return "success"

        result = await failing_operation()

        assert result == "success"
        assert len(retry_callbacks) == 2
        assert retry_callbacks[0]['retry_count'] == 1
        assert retry_callbacks[1]['retry_count'] == 2


@pytest.mark.asyncio
class TestRetryableOperation:
    """测试可重试操作类"""

    async def test_successful_operation(self):
        """测试成功的操作"""
        operation = RetryableOperation()

        async def successful_func():
            return "success"

        result = await operation.execute(successful_func)

        assert result == "success"
        assert operation.retry_count == 0

        stats = operation.get_stats()
        assert stats['retry_count'] == 0
        assert stats['last_error'] is None

    async def test_retry_and_success(self):
        """测试重试后成功"""
        call_count = 0

        async def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("还没成功")
            return "success"

        operation = RetryableOperation(
            RetryConfig(max_retries=5, initial_delay=0.1)
        )

        result = await operation.execute(
            sometimes_fails,
            exceptions=(ValueError,)
        )

        assert result == "success"
        assert operation.retry_count == 2  # 失败2次，第3次成功

        stats = operation.get_stats()
        assert stats['retry_count'] == 2

    async def test_all_retries_exhausted(self):
        """测试重试耗尽"""
        async def always_fails():
            raise ValueError("总是失败")

        operation = RetryableOperation(
            RetryConfig(max_retries=2, initial_delay=0.1)
        )

        with pytest.raises(ValueError, match="总是失败"):
            await operation.execute(
                always_fails,
                exceptions=(ValueError,)
            )

        assert operation.retry_count == 3  # 初始 + 2次重试
        assert operation.last_error is not None

        stats = operation.get_stats()
        assert stats['retry_count'] == 3
        assert '总是失败' in stats['last_error']


class TestPredefinedConfigs:
    """测试预定义配置"""

    def test_default_retry_config(self):
        """测试默认重试配置"""
        assert DEFAULT_RETRY_CONFIG.max_retries == 3
        assert DEFAULT_RETRY_CONFIG.initial_delay == 1.0

    def test_aggressive_retry_config(self):
        """测试激进重试配置"""
        assert AGGRESSIVE_RETRY_CONFIG.max_retries == 5
        assert AGGRESSIVE_RETRY_CONFIG.max_delay == 60.0

    def test_conservative_retry_config(self):
        """测试保守重试配置"""
        assert CONSERVATIVE_RETRY_CONFIG.max_retries == 2
        assert CONSERVATIVE_RETRY_CONFIG.initial_delay == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
