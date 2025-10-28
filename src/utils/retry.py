"""
重试机制工具

提供装饰器和函数用于实现自动重试逻辑
"""

import asyncio
import functools
import logging
from typing import TypeVar, Callable, Optional, Type, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        初始化重试配置

        Args:
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            exponential_base: 指数退避基数
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, retry_count: int) -> float:
        """
        计算延迟时间

        使用指数退避算法: delay = min(initial_delay * (base ^ retry_count), max_delay)

        Args:
            retry_count: 当前重试次数

        Returns:
            延迟时间（秒）
        """
        delay = self.initial_delay * (self.exponential_base ** retry_count)
        delay = min(delay, self.max_delay)

        # 添加抖动（避免雷鸣群效应）
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    异步重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数 (func, exception, retry_count)

    Returns:
        装饰器函数
    """
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retry_count = 0
            last_exception = None

            while retry_count <= config.max_retries:
                try:
                    # 执行函数
                    result = await func(*args, **kwargs)
                    return result

                except exceptions as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > config.max_retries:
                        logger.error(
                            f"{func.__name__} 失败，已达最大重试次数 {config.max_retries}: {e}"
                        )
                        raise

                    # 计算延迟时间
                    delay = config.calculate_delay(retry_count - 1)

                    logger.warning(
                        f"{func.__name__} 失败 (尝试 {retry_count}/{config.max_retries}): {e}\n"
                        f"等待 {delay:.2f} 秒后重试..."
                    )

                    # 调用重试回调
                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(func, e, retry_count)
                            else:
                                on_retry(func, e, retry_count)
                        except Exception as callback_error:
                            logger.error(f"重试回调失败: {callback_error}")

                    # 等待后重试
                    await asyncio.sleep(delay)

            # 理论上不会到达这里
            raise last_exception

        return wrapper
    return decorator


class RetryableOperation:
    """可重试的操作类"""

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        初始化

        Args:
            config: 重试配置，如果为 None 则使用默认配置
        """
        self.config = config or RetryConfig()
        self.retry_count = 0
        self.total_delay = 0.0
        self.start_time: Optional[datetime] = None
        self.last_error: Optional[Exception] = None

    async def execute(
        self,
        operation: Callable,
        *args,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> T:
        """
        执行可重试的操作

        Args:
            operation: 要执行的操作（async 函数）
            *args: 操作参数
            exceptions: 需要重试的异常类型
            **kwargs: 操作关键字参数

        Returns:
            操作结果

        Raises:
            最后一次失败的异常
        """
        self.retry_count = 0
        self.total_delay = 0.0
        self.start_time = datetime.now()
        self.last_error = None

        while self.retry_count <= self.config.max_retries:
            try:
                # 执行操作
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                # 记录成功信息
                if self.retry_count > 0:
                    duration = (datetime.now() - self.start_time).total_seconds()
                    logger.info(
                        f"操作成功（重试 {self.retry_count} 次，耗时 {duration:.2f} 秒）"
                    )

                return result

            except exceptions as e:
                self.last_error = e
                self.retry_count += 1

                if self.retry_count > self.config.max_retries:
                    duration = (datetime.now() - self.start_time).total_seconds()
                    logger.error(
                        f"操作失败，已达最大重试次数 {self.config.max_retries} "
                        f"（耗时 {duration:.2f} 秒）: {e}"
                    )
                    raise

                # 计算延迟
                delay = self.config.calculate_delay(self.retry_count - 1)
                self.total_delay += delay

                logger.warning(
                    f"操作失败 (尝试 {self.retry_count}/{self.config.max_retries}): {e}\n"
                    f"等待 {delay:.2f} 秒后重试..."
                )

                # 等待后重试
                await asyncio.sleep(delay)

        # 理论上不会到达这里
        raise self.last_error

    def get_stats(self) -> dict:
        """
        获取重试统计信息

        Returns:
            统计信息字典
        """
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        return {
            'retry_count': self.retry_count,
            'total_delay': self.total_delay,
            'duration': duration,
            'last_error': str(self.last_error) if self.last_error else None
        }


# 预定义的重试配置
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0
)

AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0
)

CONSERVATIVE_RETRY_CONFIG = RetryConfig(
    max_retries=2,
    initial_delay=0.5,
    max_delay=10.0,
    exponential_base=1.5
)
