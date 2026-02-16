#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多种限流策略单元测试
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import threading
from src.core.rate_limiter import (
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    LeakyBucketRateLimiter,
    create_rate_limiter,
    MultiRateLimiter,
)


class TestFixedWindowRateLimiter:
    """固定窗口速率限制器测试"""

    def test_init_valid_params(self):
        """测试有效参数初始化"""
        limiter = FixedWindowRateLimiter(rate=100, window_size=60)
        assert limiter.get_available_tokens() == 100

    def test_init_invalid_rate(self):
        """测试无效速率"""
        with pytest.raises(ValueError, match="速率必须大于 0"):
            FixedWindowRateLimiter(rate=0)

    def test_init_invalid_window_size(self):
        """测试无效窗口大小"""
        with pytest.raises(ValueError, match="窗口大小必须大于 0"):
            FixedWindowRateLimiter(rate=100, window_size=0)

    def test_acquire_within_limit(self):
        """测试在限制内获取令牌"""
        limiter = FixedWindowRateLimiter(rate=10, window_size=1)

        # 应该能成功获取 5 个令牌
        assert limiter.acquire(5) is True
        assert limiter.get_available_tokens() == 5

        # 再获取 3 个令牌
        assert limiter.acquire(3) is True
        assert limiter.get_available_tokens() == 2

    def test_acquire_exceeds_limit(self):
        """测试超过限制"""
        limiter = FixedWindowRateLimiter(rate=10, window_size=1)

        # 消耗所有令牌
        assert limiter.acquire(10) is True

        # 尝试再次获取应该失败
        assert limiter.acquire(1) is False
        assert limiter.get_available_tokens() == 0

    def test_window_reset(self):
        """测试窗口重置"""
        limiter = FixedWindowRateLimiter(rate=10, window_size=0.5)

        # 消耗所有令牌
        assert limiter.acquire(10) is True
        assert limiter.get_available_tokens() == 0

        # 等待窗口过期
        time.sleep(0.6)

        # 窗口应该已重置
        assert limiter.get_available_tokens() == 10
        assert limiter.acquire(5) is True

    def test_wait_for_token_success(self):
        """测试等待获取令牌成功"""
        limiter = FixedWindowRateLimiter(rate=10, window_size=0.5)

        # 消耗所有令牌
        limiter.acquire(10)

        # 等待获取令牌（应该在窗口重置后成功）
        start = time.time()
        result = limiter.wait_for_token(1, timeout=1.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 0.7  # 应该在 0.5 秒左右成功

    def test_reset(self):
        """测试重置功能"""
        limiter = FixedWindowRateLimiter(rate=10, window_size=1)

        # 消耗一些令牌
        limiter.acquire(7)
        assert limiter.get_available_tokens() == 3

        # 重置
        limiter.reset()
        assert limiter.get_available_tokens() == 10


class TestSlidingWindowRateLimiter:
    """滑动窗口速率限制器测试"""

    def test_init_valid_params(self):
        """测试有效参数初始化"""
        limiter = SlidingWindowRateLimiter(rate=100, window_size=60)
        assert limiter.get_available_tokens() == 100

    def test_init_invalid_rate(self):
        """测试无效速率"""
        with pytest.raises(ValueError, match="速率必须大于 0"):
            SlidingWindowRateLimiter(rate=0)

    def test_init_invalid_window_size(self):
        """测试无效窗口大小"""
        with pytest.raises(ValueError, match="窗口大小必须大于 0"):
            SlidingWindowRateLimiter(rate=100, window_size=0)

    def test_acquire_within_limit(self):
        """测试在限制内获取令牌"""
        limiter = SlidingWindowRateLimiter(rate=10, window_size=1)

        # 应该能成功获取 5 个令牌
        assert limiter.acquire(5) is True
        assert limiter.get_available_tokens() == 5

        # 再获取 3 个令牌
        assert limiter.acquire(3) is True
        assert limiter.get_available_tokens() == 2

    def test_acquire_exceeds_limit(self):
        """测试超过限制"""
        limiter = SlidingWindowRateLimiter(rate=10, window_size=1)

        # 消耗所有令牌
        assert limiter.acquire(10) is True

        # 尝试再次获取应该失败
        assert limiter.acquire(1) is False
        assert limiter.get_available_tokens() == 0

    def test_sliding_window_behavior(self):
        """测试滑动窗口行为"""
        limiter = SlidingWindowRateLimiter(rate=10, window_size=0.5)

        # 消耗所有令牌
        assert limiter.acquire(10) is True
        assert limiter.get_available_tokens() == 0

        # 等待窗口滑动（过期一些请求）
        time.sleep(0.6)

        # 所有请求应该已过期
        assert limiter.get_available_tokens() == 10
        assert limiter.acquire(5) is True

    def test_precise_rate_control(self):
        """测试精确的速率控制（无临界问题）"""
        limiter = SlidingWindowRateLimiter(rate=10, window_size=1)

        # 在窗口开始时发送 10 个请求
        assert limiter.acquire(10) is True

        # 等待 0.5 秒
        time.sleep(0.5)

        # 此时窗口内仍有 10 个请求，不应该能再发送
        assert limiter.acquire(1) is False

        # 再等待 0.6 秒（总共 1.1 秒），所有请求应该过期
        time.sleep(0.6)
        assert limiter.acquire(10) is True

    def test_wait_for_token_success(self):
        """测试等待获取令牌成功"""
        limiter = SlidingWindowRateLimiter(rate=10, window_size=0.5)

        # 消耗所有令牌
        limiter.acquire(10)

        # 等待获取令牌
        start = time.time()
        result = limiter.wait_for_token(1, timeout=1.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 0.7  # 应该在 0.5 秒左右成功

    def test_reset(self):
        """测试重置功能"""
        limiter = SlidingWindowRateLimiter(rate=10, window_size=1)

        # 消耗一些令牌
        limiter.acquire(7)
        assert limiter.get_available_tokens() == 3

        # 重置
        limiter.reset()
        assert limiter.get_available_tokens() == 10


class TestLeakyBucketRateLimiter:
    """漏桶速率限制器测试"""

    def test_init_valid_params(self):
        """测试有效参数初始化"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=20)
        assert limiter.get_available_tokens() == 20
        assert limiter.get_queue_size() == 0

    def test_init_default_capacity(self):
        """测试默认容量"""
        limiter = LeakyBucketRateLimiter(rate=10)
        assert limiter.get_available_tokens() == 10

    def test_init_invalid_rate(self):
        """测试无效速率"""
        with pytest.raises(ValueError, match="速率必须大于 0"):
            LeakyBucketRateLimiter(rate=0)

    def test_init_invalid_capacity(self):
        """测试无效容量"""
        with pytest.raises(ValueError, match="容量必须大于 0"):
            LeakyBucketRateLimiter(rate=10, capacity=0)

    def test_acquire_within_capacity(self):
        """测试在容量内获取令牌"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=10)

        # 应该能成功获取 5 个令牌
        assert limiter.acquire(5) is True
        assert limiter.get_queue_size() == 5
        assert limiter.get_available_tokens() == 5

        # 再获取 3 个令牌
        assert limiter.acquire(3) is True
        assert limiter.get_queue_size() == 8
        assert limiter.get_available_tokens() == 2

    def test_acquire_exceeds_capacity(self):
        """测试超过容量"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=10)

        # 填满桶
        assert limiter.acquire(10) is True

        # 尝试再次获取应该失败
        assert limiter.acquire(1) is False
        assert limiter.get_available_tokens() == 0

    def test_leaky_behavior(self):
        """测试漏水行为"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=10)  # 每秒处理 10 个请求

        # 填满桶
        assert limiter.acquire(10) is True
        assert limiter.get_queue_size() == 10

        # 等待 0.5 秒，应该处理约 5 个请求
        time.sleep(0.5)
        queue_size = limiter.get_queue_size()
        assert 4 <= queue_size <= 6  # 允许一定误差

        # 应该能再获取约 5 个令牌
        assert limiter.acquire(4) is True

    def test_smooth_rate_limiting(self):
        """测试平滑限流（不允许突发）"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=10)

        # 填满桶
        assert limiter.acquire(10) is True

        # 立即尝试获取更多令牌应该失败（不允许突发）
        assert limiter.acquire(1) is False

        # 等待一段时间后才能获取
        time.sleep(0.2)
        assert limiter.acquire(1) is True

    def test_wait_for_token_success(self):
        """测试等待获取令牌成功"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=10)

        # 填满桶
        limiter.acquire(10)

        # 等待获取令牌
        start = time.time()
        result = limiter.wait_for_token(1, timeout=1.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 0.3  # 应该很快就能获取到

    def test_reset(self):
        """测试重置功能"""
        limiter = LeakyBucketRateLimiter(rate=10, capacity=10)

        # 消耗一些令牌
        limiter.acquire(7)
        assert limiter.get_queue_size() == 7

        # 重置
        limiter.reset()
        assert limiter.get_queue_size() == 0
        assert limiter.get_available_tokens() == 10


class TestCreateRateLimiter:
    """测试工厂函数"""

    def test_create_token_bucket(self):
        """测试创建令牌桶限制器"""
        limiter = create_rate_limiter("token_bucket", rate=10, capacity=20)
        assert limiter.__class__.__name__ == "RateLimiter"
        assert limiter.get_rate() == 10
        assert limiter.get_capacity() == 20

    def test_create_fixed_window(self):
        """测试创建固定窗口限制器"""
        limiter = create_rate_limiter("fixed_window", rate=100, window_size=60)
        assert limiter.__class__.__name__ == "FixedWindowRateLimiter"
        assert limiter.get_available_tokens() == 100

    def test_create_sliding_window(self):
        """测试创建滑动窗口限制器"""
        limiter = create_rate_limiter("sliding_window", rate=100, window_size=60)
        assert limiter.__class__.__name__ == "SlidingWindowRateLimiter"
        assert limiter.get_available_tokens() == 100

    def test_create_leaky_bucket(self):
        """测试创建漏桶限制器"""
        limiter = create_rate_limiter("leaky_bucket", rate=10, capacity=20)
        assert limiter.__class__.__name__ == "LeakyBucketRateLimiter"
        assert limiter.get_available_tokens() == 20

    def test_create_invalid_strategy(self):
        """测试创建无效策略"""
        with pytest.raises(ValueError, match="不支持的限流策略"):
            create_rate_limiter("invalid_strategy", rate=10)

    def test_case_insensitive_strategy(self):
        """测试策略名称大小写不敏感"""
        limiter1 = create_rate_limiter("TOKEN_BUCKET", rate=10)
        limiter2 = create_rate_limiter("Token_Bucket", rate=10)
        assert limiter1.__class__.__name__ == "RateLimiter"
        assert limiter2.__class__.__name__ == "RateLimiter"


class TestMultiRateLimiterWithStrategies:
    """测试多速率限制器支持不同策略"""

    def test_add_different_strategies(self):
        """测试添加不同策略的限制器"""
        multi = MultiRateLimiter()

        # 添加不同策略的限制器
        multi.add_limiter("api1", rate=10, strategy="token_bucket")
        multi.add_limiter("api2", rate=100, window_size=60, strategy="fixed_window")
        multi.add_limiter("api3", rate=100, window_size=60, strategy="sliding_window")
        multi.add_limiter("api4", rate=10, capacity=20, strategy="leaky_bucket")

        # 验证限制器类型
        assert multi.get_limiter("api1").__class__.__name__ == "RateLimiter"
        assert multi.get_limiter("api2").__class__.__name__ == "FixedWindowRateLimiter"
        assert multi.get_limiter("api3").__class__.__name__ == "SlidingWindowRateLimiter"
        assert multi.get_limiter("api4").__class__.__name__ == "LeakyBucketRateLimiter"

    def test_independent_limiters(self):
        """测试不同策略的限制器独立工作"""
        multi = MultiRateLimiter()

        # 添加两个不同策略的限制器
        multi.add_limiter("token", rate=10, strategy="token_bucket")
        multi.add_limiter("window", rate=10, window_size=1, strategy="fixed_window")

        # 从 token 获取令牌
        multi.acquire("token", 5)

        # token 应该剩余约 5 个令牌
        token_limiter = multi.get_limiter("token")
        assert 4.9 <= token_limiter.get_available_tokens() <= 5.1

        # window 应该仍然有 10 个令牌（不受影响）
        window_limiter = multi.get_limiter("window")
        assert window_limiter.get_available_tokens() == 10


class TestStrategyComparison:
    """测试不同策略的行为差异"""

    def test_token_bucket_vs_leaky_bucket(self):
        """测试令牌桶和漏桶的差异：突发流量处理"""
        # 令牌桶：允许突发流量
        token_bucket = create_rate_limiter("token_bucket", rate=10, capacity=10)

        # 漏桶：不允许突发流量
        leaky_bucket = create_rate_limiter("leaky_bucket", rate=10, capacity=10)

        # 令牌桶可以一次性消耗所有令牌（突发）
        assert token_bucket.acquire(10) is True

        # 漏桶也可以填满，但处理速率是固定的
        assert leaky_bucket.acquire(10) is True

        # 等待一段时间
        time.sleep(0.5)

        # 令牌桶会补充令牌（约 5 个）
        token_tokens = token_bucket.get_available_tokens()
        assert 4 <= token_tokens <= 6

        # 漏桶会处理请求（队列减少约 5 个）
        leaky_tokens = leaky_bucket.get_available_tokens()
        assert 4 <= leaky_tokens <= 6

    def test_fixed_window_vs_sliding_window(self):
        """测试固定窗口和滑动窗口的差异：临界问题"""
        # 固定窗口：存在临界问题
        fixed_window = create_rate_limiter("fixed_window", rate=10, window_size=0.5)

        # 滑动窗口：无临界问题
        sliding_window = create_rate_limiter("sliding_window", rate=10, window_size=0.5)

        # 两者都消耗所有令牌
        assert fixed_window.acquire(10) is True
        assert sliding_window.acquire(10) is True

        # 等待窗口过期
        time.sleep(0.6)

        # 固定窗口：窗口重置，可以立即获取所有令牌
        assert fixed_window.get_available_tokens() == 10

        # 滑动窗口：旧请求过期，也可以获取所有令牌
        assert sliding_window.get_available_tokens() == 10


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("开始运行多种限流策略单元测试")
    print("=" * 70)

    # 运行 pytest
    exit_code = pytest.main([__file__, "-v", "--tb=short", "-s"])  # 详细输出  # 简短的错误回溯  # 显示 print 输出

    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    exit(run_tests())
