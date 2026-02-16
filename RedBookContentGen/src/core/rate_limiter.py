#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制模块

提供多种 API 速率限制策略：
- 令牌桶算法（Token Bucket）
- 固定窗口算法（Fixed Window）
- 滑动窗口算法（Sliding Window）
- 漏桶算法（Leaky Bucket）
"""

import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional


class BaseRateLimiter(ABC):
    """速率限制器基类

    定义所有速率限制器的通用接口
    """

    @abstractmethod
    def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌（非阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1

        Returns:
            如果成功获取令牌返回 True，否则返回 False
        """

    @abstractmethod
    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """等待直到获取到令牌（阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1
            timeout: 超时时间（秒），如果为 None 则无限等待

        Returns:
            如果成功获取令牌返回 True，超时返回 False
        """

    @abstractmethod
    def get_available_tokens(self) -> float:
        """获取当前可用的令牌数

        Returns:
            当前可用的令牌数
        """

    @abstractmethod
    def reset(self) -> None:
        """重置速率限制器"""


class RateLimiter(BaseRateLimiter):
    """速率限制器（令牌桶算法）

    令牌桶算法原理：
    1. 令牌以固定速率生成并放入桶中
    2. 桶有最大容量限制
    3. 请求需要消耗令牌才能执行
    4. 如果桶中没有足够的令牌，请求需要等待

    特点：
    - 允许突发流量（桶满时可以一次性消耗多个令牌）
    - 平滑限流（长期平均速率受控）
    - 线程安全
    """

    def __init__(self, rate: float, capacity: Optional[int] = None):
        """初始化速率限制器

        Args:
            rate: 令牌生成速率（每秒生成的令牌数）
                  例如：rate=10 表示每秒生成 10 个令牌
            capacity: 令牌桶容量（最多存储的令牌数）
                     如果为 None，则容量等于速率
                     容量越大，允许的突发流量越大

        Raises:
            ValueError: 如果 rate 或 capacity 无效
        """
        if rate <= 0:
            raise ValueError(f"速率必须大于 0，当前值: {rate}")

        if capacity is not None and capacity <= 0:
            raise ValueError(f"容量必须大于 0，当前值: {capacity}")

        self._rate = float(rate)  # 令牌生成速率（每秒）
        self._capacity = float(capacity if capacity is not None else rate)  # 桶容量
        self._tokens = self._capacity  # 当前令牌数（初始时桶是满的）
        self._last_update = time.time()  # 上次更新时间
        self._lock = threading.RLock()  # 线程安全锁

    def _refill_tokens(self) -> None:
        """补充令牌

        根据距离上次更新的时间，计算应该生成的令牌数并添加到桶中
        """
        now = time.time()
        elapsed = now - self._last_update

        # 计算应该生成的令牌数
        new_tokens = elapsed * self._rate

        # 更新令牌数（不超过容量）
        self._tokens = min(self._capacity, self._tokens + new_tokens)

        # 更新时间戳
        self._last_update = now

    def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌（非阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1

        Returns:
            如果成功获取令牌返回 True，否则返回 False

        Raises:
            ValueError: 如果 tokens 无效
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        with self._lock:
            # 补充令牌
            self._refill_tokens()

            # 检查是否有足够的令牌
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """等待直到获取到令牌（阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1
            timeout: 超时时间（秒），如果为 None 则无限等待

        Returns:
            如果成功获取令牌返回 True，超时返回 False

        Raises:
            ValueError: 如果 tokens 无效或请求的令牌数超过桶容量
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        if tokens > self._capacity:
            raise ValueError(f"请求的令牌数 ({tokens}) 超过桶容量 ({self._capacity})，" "永远无法满足此请求")

        start_time = time.time()

        while True:
            # 尝试获取令牌
            if self.acquire(tokens):
                return True

            # 检查是否超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

            # 计算需要等待的时间
            with self._lock:
                self._refill_tokens()
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self._rate if tokens_needed > 0 else 0

            # 等待一小段时间后重试
            # 使用较小的等待时间以提高响应性
            sleep_time = min(wait_time, 0.01)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_available_tokens(self) -> float:
        """获取当前可用的令牌数

        Returns:
            当前桶中的令牌数
        """
        with self._lock:
            self._refill_tokens()
            return self._tokens

    def get_rate(self) -> float:
        """获取令牌生成速率

        Returns:
            每秒生成的令牌数
        """
        return self._rate

    def get_capacity(self) -> float:
        """获取桶容量

        Returns:
            桶的最大容量
        """
        return self._capacity

    def reset(self) -> None:
        """重置速率限制器

        将令牌数重置为满容量，并更新时间戳
        """
        with self._lock:
            self._tokens = self._capacity
            self._last_update = time.time()

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"RateLimiter(rate={self._rate}/s, "
            f"capacity={self._capacity}, "
            f"tokens={self.get_available_tokens():.2f})"
        )


class MultiRateLimiter:
    """多速率限制器

    管理多个不同的速率限制器，适用于需要对不同资源进行独立限流的场景
    例如：OpenAI API 和图片生成 API 使用不同的限流策略

    支持为不同的资源配置不同的限流策略
    """

    def __init__(self) -> None:
        """初始化多速率限制器"""
        self._limiters: dict[str, BaseRateLimiter] = {}
        self._lock = threading.RLock()

    def add_limiter(
        self,
        name: str,
        rate: float,
        capacity: Optional[int] = None,
        strategy: str = "token_bucket",
        window_size: Optional[float] = None,
    ) -> None:
        """添加速率限制器

        Args:
            name: 限制器名称（唯一标识）
            rate: 速率参数
            capacity: 容量参数（可选）
            strategy: 限流策略，可选值：
                - "token_bucket": 令牌桶算法（默认）
                - "fixed_window": 固定窗口算法
                - "sliding_window": 滑动窗口算法
                - "leaky_bucket": 漏桶算法
            window_size: 窗口大小（可选，仅用于窗口算法）
        """
        with self._lock:
            self._limiters[name] = create_rate_limiter(
                strategy=strategy, rate=rate, capacity=capacity, window_size=window_size
            )

    def get_limiter(self, name: str) -> Optional[BaseRateLimiter]:
        """获取速率限制器

        Args:
            name: 限制器名称

        Returns:
            速率限制器实例，如果不存在返回 None
        """
        with self._lock:
            return self._limiters.get(name)

    def remove_limiter(self, name: str) -> bool:
        """移除速率限制器

        Args:
            name: 限制器名称

        Returns:
            如果成功移除返回 True，否则返回 False
        """
        with self._lock:
            if name in self._limiters:
                del self._limiters[name]
                return True
            return False

    def acquire(self, name: str, tokens: int = 1) -> bool:
        """从指定限制器获取令牌

        Args:
            name: 限制器名称
            tokens: 令牌数

        Returns:
            如果成功获取返回 True，否则返回 False

        Raises:
            KeyError: 如果限制器不存在
        """
        limiter = self.get_limiter(name)
        if limiter is None:
            raise KeyError(f"速率限制器不存在: {name}")
        return limiter.acquire(tokens)

    def wait_for_token(self, name: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """从指定限制器等待获取令牌

        Args:
            name: 限制器名称
            tokens: 令牌数
            timeout: 超时时间（秒）

        Returns:
            如果成功获取返回 True，超时返回 False

        Raises:
            KeyError: 如果限制器不存在
        """
        limiter = self.get_limiter(name)
        if limiter is None:
            raise KeyError(f"速率限制器不存在: {name}")
        return limiter.wait_for_token(tokens, timeout)

    def list_limiters(self) -> list[str]:
        """列出所有限制器名称

        Returns:
            限制器名称列表
        """
        with self._lock:
            return list(self._limiters.keys())

    def __repr__(self) -> str:
        """字符串表示"""
        with self._lock:
            limiters_info = ", ".join(self._limiters.keys())
            return f"MultiRateLimiter(limiters=[{limiters_info}])"


class FixedWindowRateLimiter(BaseRateLimiter):
    """固定窗口速率限制器

    固定窗口算法原理：
    1. 将时间划分为固定大小的窗口（如 1 分钟）
    2. 每个窗口内允许固定数量的请求
    3. 窗口结束时，计数器重置

    特点：
    - 实现简单，内存占用小
    - 存在临界问题：窗口边界处可能出现突发流量
    - 适用于对精确度要求不高的场景

    示例：
        限制每分钟 60 次请求，窗口大小 60 秒
        如果在 00:59 秒发送 60 次请求，在 01:01 秒又发送 60 次请求
        实际上在 2 秒内发送了 120 次请求
    """

    def __init__(self, rate: float, window_size: float = 60.0):
        """初始化固定窗口速率限制器

        Args:
            rate: 每个窗口允许的请求数
            window_size: 窗口大小（秒），默认 60 秒

        Raises:
            ValueError: 如果参数无效
        """
        if rate <= 0:
            raise ValueError(f"速率必须大于 0，当前值: {rate}")

        if window_size <= 0:
            raise ValueError(f"窗口大小必须大于 0，当前值: {window_size}")

        self._rate = float(rate)  # 每个窗口允许的请求数
        self._window_size = float(window_size)  # 窗口大小（秒）
        self._counter = 0  # 当前窗口的请求计数
        self._window_start = time.time()  # 当前窗口开始时间
        self._lock = threading.RLock()

    def _reset_window_if_needed(self) -> None:
        """如果当前窗口已过期，重置窗口"""
        now = time.time()
        elapsed = now - self._window_start

        if elapsed >= self._window_size:
            # 窗口已过期，重置
            self._counter = 0
            # 计算新窗口的开始时间（对齐到窗口边界）
            windows_passed = int(elapsed / self._window_size)
            self._window_start += windows_passed * self._window_size

    def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌（非阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1

        Returns:
            如果成功获取令牌返回 True，否则返回 False

        Raises:
            ValueError: 如果 tokens 无效
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        with self._lock:
            self._reset_window_if_needed()

            # 检查是否超过限制
            if self._counter + tokens <= self._rate:
                self._counter += tokens
                return True

            return False

    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """等待直到获取到令牌（阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1
            timeout: 超时时间（秒），如果为 None 则无限等待

        Returns:
            如果成功获取令牌返回 True，超时返回 False

        Raises:
            ValueError: 如果 tokens 无效或超过窗口限制
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        if tokens > self._rate:
            raise ValueError(f"请求的令牌数 ({tokens}) 超过窗口限制 ({self._rate})，" "永远无法满足此请求")

        start_time = time.time()

        while True:
            # 尝试获取令牌
            if self.acquire(tokens):
                return True

            # 检查是否超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

            # 计算需要等待的时间（等到下一个窗口）
            with self._lock:
                self._reset_window_if_needed()
                now = time.time()
                time_until_next_window = self._window_start + self._window_size - now

            # 等待一小段时间后重试
            sleep_time = min(time_until_next_window, 0.01)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_available_tokens(self) -> float:
        """获取当前窗口剩余的令牌数

        Returns:
            当前窗口剩余的令牌数
        """
        with self._lock:
            self._reset_window_if_needed()
            return self._rate - self._counter

    def reset(self) -> None:
        """重置速率限制器"""
        with self._lock:
            self._counter = 0
            self._window_start = time.time()

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"FixedWindowRateLimiter(rate={self._rate}/{self._window_size}s, "
            f"available={self.get_available_tokens():.2f})"
        )


class SlidingWindowRateLimiter(BaseRateLimiter):
    """滑动窗口速率限制器

    滑动窗口算法原理：
    1. 记录每次请求的时间戳
    2. 检查时，统计窗口时间内的请求数
    3. 移除过期的请求记录

    特点：
    - 精确控制速率，无临界问题
    - 内存占用与请求数成正比
    - 适用于对精确度要求高的场景

    示例：
        限制每分钟 60 次请求，窗口大小 60 秒
        无论何时检查，都只统计最近 60 秒内的请求数
        不会出现固定窗口的临界问题
    """

    def __init__(self, rate: float, window_size: float = 60.0):
        """初始化滑动窗口速率限制器

        Args:
            rate: 窗口时间内允许的请求数
            window_size: 窗口大小（秒），默认 60 秒

        Raises:
            ValueError: 如果参数无效
        """
        if rate <= 0:
            raise ValueError(f"速率必须大于 0，当前值: {rate}")

        if window_size <= 0:
            raise ValueError(f"窗口大小必须大于 0，当前值: {window_size}")

        self._rate = float(rate)  # 窗口时间内允许的请求数
        self._window_size = float(window_size)  # 窗口大小（秒）
        self._requests: deque[float] = deque()  # 请求时间戳队列
        self._lock = threading.RLock()

    def _remove_expired_requests(self) -> None:
        """移除过期的请求记录"""
        now = time.time()
        cutoff_time = now - self._window_size

        # 移除所有早于窗口开始时间的请求
        while self._requests and self._requests[0] <= cutoff_time:
            self._requests.popleft()

    def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌（非阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1

        Returns:
            如果成功获取令牌返回 True，否则返回 False

        Raises:
            ValueError: 如果 tokens 无效
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        with self._lock:
            self._remove_expired_requests()

            # 检查是否超过限制
            if len(self._requests) + tokens <= self._rate:
                # 记录请求时间戳
                now = time.time()
                for _ in range(tokens):
                    self._requests.append(now)
                return True

            return False

    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """等待直到获取到令牌（阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1
            timeout: 超时时间（秒），如果为 None 则无限等待

        Returns:
            如果成功获取令牌返回 True，超时返回 False

        Raises:
            ValueError: 如果 tokens 无效或超过窗口限制
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        if tokens > self._rate:
            raise ValueError(f"请求的令牌数 ({tokens}) 超过窗口限制 ({self._rate})，" "永远无法满足此请求")

        start_time = time.time()

        while True:
            # 尝试获取令牌
            if self.acquire(tokens):
                return True

            # 检查是否超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

            # 计算需要等待的时间（等到最早的请求过期）
            with self._lock:
                self._remove_expired_requests()
                if self._requests:
                    # 计算最早的请求何时过期
                    oldest_request = self._requests[0]
                    now = time.time()
                    wait_time = oldest_request + self._window_size - now
                else:
                    wait_time = 0

            # 等待一小段时间后重试
            sleep_time = min(max(wait_time, 0), 0.01)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_available_tokens(self) -> float:
        """获取当前窗口剩余的令牌数

        Returns:
            当前窗口剩余的令牌数
        """
        with self._lock:
            self._remove_expired_requests()
            return self._rate - len(self._requests)

    def reset(self) -> None:
        """重置速率限制器"""
        with self._lock:
            self._requests.clear()

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"SlidingWindowRateLimiter(rate={self._rate}/{self._window_size}s, "
            f"available={self.get_available_tokens():.2f})"
        )


class LeakyBucketRateLimiter(BaseRateLimiter):
    """漏桶速率限制器

    漏桶算法原理：
    1. 请求进入漏桶（队列）
    2. 漏桶以固定速率处理请求
    3. 如果漏桶满了，新请求被拒绝

    特点：
    - 强制固定速率输出，平滑流量
    - 不允许突发流量
    - 适用于需要严格控制速率的场景

    与令牌桶的区别：
    - 令牌桶：允许突发流量（桶满时可以一次性消耗多个令牌）
    - 漏桶：不允许突发流量（严格按照固定速率处理）
    """

    def __init__(self, rate: float, capacity: Optional[int] = None):
        """初始化漏桶速率限制器

        Args:
            rate: 漏桶处理速率（每秒处理的请求数）
            capacity: 漏桶容量（最多排队的请求数）
                     如果为 None，则容量等于速率

        Raises:
            ValueError: 如果参数无效
        """
        if rate <= 0:
            raise ValueError(f"速率必须大于 0，当前值: {rate}")

        if capacity is not None and capacity <= 0:
            raise ValueError(f"容量必须大于 0，当前值: {capacity}")

        self._rate = float(rate)  # 处理速率（每秒）
        self._capacity = float(capacity if capacity is not None else rate)  # 桶容量
        self._queue: deque[float] = deque()  # 请求队列（存储请求时间戳）
        self._last_leak_time = time.time()  # 上次漏水时间
        self._lock = threading.RLock()

    def _leak(self) -> None:
        """漏水：移除已处理的请求"""
        now = time.time()
        elapsed = now - self._last_leak_time

        # 计算应该处理的请求数
        requests_to_process = int(elapsed * self._rate)

        if requests_to_process > 0:
            # 移除已处理的请求
            for _ in range(min(requests_to_process, len(self._queue))):
                self._queue.popleft()

            # 更新漏水时间
            self._last_leak_time = now

    def acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌（非阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1

        Returns:
            如果成功获取令牌返回 True，否则返回 False

        Raises:
            ValueError: 如果 tokens 无效
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        with self._lock:
            self._leak()

            # 检查是否有足够的空间
            if len(self._queue) + tokens <= self._capacity:
                # 将请求加入队列
                now = time.time()
                for _ in range(tokens):
                    self._queue.append(now)
                return True

            return False

    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """等待直到获取到令牌（阻塞）

        Args:
            tokens: 需要获取的令牌数，默认为 1
            timeout: 超时时间（秒），如果为 None 则无限等待

        Returns:
            如果成功获取令牌返回 True，超时返回 False

        Raises:
            ValueError: 如果 tokens 无效或超过桶容量
        """
        if tokens <= 0:
            raise ValueError(f"令牌数必须大于 0，当前值: {tokens}")

        if tokens > self._capacity:
            raise ValueError(f"请求的令牌数 ({tokens}) 超过桶容量 ({self._capacity})，" "永远无法满足此请求")

        start_time = time.time()

        while True:
            # 尝试获取令牌
            if self.acquire(tokens):
                return True

            # 检查是否超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

            # 计算需要等待的时间
            with self._lock:
                self._leak()
                # 需要等待队列中的请求被处理
                requests_to_wait = len(self._queue) + tokens - self._capacity
                if requests_to_wait > 0:
                    wait_time = requests_to_wait / self._rate
                else:
                    wait_time = 0

            # 等待一小段时间后重试
            sleep_time = min(max(wait_time, 0), 0.01)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_available_tokens(self) -> float:
        """获取当前可用的令牌数（桶中剩余空间）

        Returns:
            当前可用的令牌数
        """
        with self._lock:
            self._leak()
            return self._capacity - len(self._queue)

    def get_queue_size(self) -> int:
        """获取当前队列大小

        Returns:
            队列中的请求数
        """
        with self._lock:
            self._leak()
            return len(self._queue)

    def reset(self) -> None:
        """重置速率限制器"""
        with self._lock:
            self._queue.clear()
            self._last_leak_time = time.time()

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"LeakyBucketRateLimiter(rate={self._rate}/s, "
            f"capacity={self._capacity}, "
            f"queue_size={self.get_queue_size()}, "
            f"available={self.get_available_tokens():.2f})"
        )


def create_rate_limiter(
    strategy: str, rate: float, capacity: Optional[int] = None, window_size: Optional[float] = None
) -> BaseRateLimiter:
    """工厂函数：创建速率限制器

    Args:
        strategy: 限流策略，可选值：
            - "token_bucket": 令牌桶算法
            - "fixed_window": 固定窗口算法
            - "sliding_window": 滑动窗口算法
            - "leaky_bucket": 漏桶算法
        rate: 速率参数（含义取决于策略）
        capacity: 容量参数（可选，取决于策略）
        window_size: 窗口大小（可选，仅用于窗口算法）

    Returns:
        速率限制器实例

    Raises:
        ValueError: 如果策略名称无效

    Examples:
        >>> # 创建令牌桶限制器：每秒 10 个令牌，容量 20
        >>> limiter = create_rate_limiter("token_bucket", rate=10, capacity=20)

        >>> # 创建固定窗口限制器：每 60 秒 100 次请求
        >>> limiter = create_rate_limiter("fixed_window", rate=100, window_size=60)

        >>> # 创建滑动窗口限制器：每 60 秒 100 次请求
        >>> limiter = create_rate_limiter("sliding_window", rate=100, window_size=60)

        >>> # 创建漏桶限制器：每秒处理 10 个请求，容量 20
        >>> limiter = create_rate_limiter("leaky_bucket", rate=10, capacity=20)
    """
    strategy = strategy.lower()

    if strategy == "token_bucket":
        return RateLimiter(rate=rate, capacity=capacity)

    elif strategy == "fixed_window":
        window = window_size if window_size is not None else 60.0
        return FixedWindowRateLimiter(rate=rate, window_size=window)

    elif strategy == "sliding_window":
        window = window_size if window_size is not None else 60.0
        return SlidingWindowRateLimiter(rate=rate, window_size=window)

    elif strategy == "leaky_bucket":
        return LeakyBucketRateLimiter(rate=rate, capacity=capacity)

    else:
        raise ValueError(
            f"不支持的限流策略: {strategy}，" "可选值: token_bucket, fixed_window, sliding_window, leaky_bucket"
        )
