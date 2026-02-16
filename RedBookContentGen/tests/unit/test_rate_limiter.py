#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制器单元测试
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import threading
from src.core.rate_limiter import RateLimiter, MultiRateLimiter


class TestRateLimiter:
    """RateLimiter 类测试"""

    def test_init_valid_params(self):
        """测试有效参数初始化"""
        limiter = RateLimiter(rate=10, capacity=20)
        assert limiter.get_rate() == 10
        assert limiter.get_capacity() == 20
        assert limiter.get_available_tokens() == 20  # 初始时桶是满的

    def test_init_default_capacity(self):
        """测试默认容量（等于速率）"""
        limiter = RateLimiter(rate=10)
        assert limiter.get_capacity() == 10

    def test_init_invalid_rate(self):
        """测试无效速率"""
        with pytest.raises(ValueError, match="速率必须大于 0"):
            RateLimiter(rate=0)

        with pytest.raises(ValueError, match="速率必须大于 0"):
            RateLimiter(rate=-1)

    def test_init_invalid_capacity(self):
        """测试无效容量"""
        with pytest.raises(ValueError, match="容量必须大于 0"):
            RateLimiter(rate=10, capacity=0)

        with pytest.raises(ValueError, match="容量必须大于 0"):
            RateLimiter(rate=10, capacity=-1)

    def test_acquire_single_token(self):
        """测试获取单个令牌"""
        limiter = RateLimiter(rate=10, capacity=10)

        # 初始时应该能成功获取
        assert limiter.acquire(1) is True
        assert 8.9 <= limiter.get_available_tokens() <= 9.1

        # 再次获取
        assert limiter.acquire(1) is True
        assert 7.9 <= limiter.get_available_tokens() <= 8.1

    def test_acquire_multiple_tokens(self):
        """测试获取多个令牌"""
        limiter = RateLimiter(rate=10, capacity=10)

        # 获取 5 个令牌
        assert limiter.acquire(5) is True
        assert 4.9 <= limiter.get_available_tokens() <= 5.1

        # 再获取 3 个令牌
        assert limiter.acquire(3) is True
        assert 1.9 <= limiter.get_available_tokens() <= 2.1

    def test_acquire_insufficient_tokens(self):
        """测试令牌不足时获取失败"""
        limiter = RateLimiter(rate=10, capacity=10)

        # 消耗所有令牌
        assert limiter.acquire(10) is True

        # 尝试再次获取应该失败
        assert limiter.acquire(1) is False
        assert limiter.get_available_tokens() < 0.1

    def test_acquire_invalid_tokens(self):
        """测试无效的令牌数"""
        limiter = RateLimiter(rate=10)

        with pytest.raises(ValueError, match="令牌数必须大于 0"):
            limiter.acquire(0)

        with pytest.raises(ValueError, match="令牌数必须大于 0"):
            limiter.acquire(-1)

    def test_token_refill(self):
        """测试令牌自动补充"""
        limiter = RateLimiter(rate=10, capacity=10)  # 每秒生成 10 个令牌

        # 消耗所有令牌
        assert limiter.acquire(10) is True
        assert limiter.get_available_tokens() < 0.1

        # 等待 0.5 秒，应该生成约 5 个令牌
        time.sleep(0.5)
        tokens = limiter.get_available_tokens()
        assert 4 <= tokens <= 6  # 允许一定误差

        # 应该能获取 4 个令牌
        assert limiter.acquire(4) is True

    def test_capacity_limit(self):
        """测试容量限制"""
        limiter = RateLimiter(rate=10, capacity=5)

        # 初始时令牌数等于容量
        assert limiter.get_available_tokens() == 5

        # 等待一段时间，令牌数不应超过容量
        time.sleep(1)
        assert limiter.get_available_tokens() == 5

    def test_wait_for_token_success(self):
        """测试等待获取令牌成功"""
        limiter = RateLimiter(rate=10, capacity=10)

        # 消耗所有令牌
        limiter.acquire(10)

        # 等待获取 1 个令牌（应该在 0.2 秒内成功）
        start = time.time()
        result = limiter.wait_for_token(1, timeout=1.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed < 0.3  # 应该很快就能获取到

    def test_wait_for_token_timeout(self):
        """测试等待获取令牌超时"""
        limiter = RateLimiter(rate=1, capacity=1)  # 每秒只生成 1 个令牌

        # 消耗所有令牌
        limiter.acquire(1)

        # 尝试获取 1 个令牌，但超时时间很短
        start = time.time()
        result = limiter.wait_for_token(1, timeout=0.1)
        elapsed = time.time() - start

        assert result is False
        assert 0.08 <= elapsed <= 0.15  # 应该在超时时间附近返回

    def test_wait_for_token_exceeds_capacity(self):
        """测试请求的令牌数超过容量"""
        limiter = RateLimiter(rate=10, capacity=5)

        with pytest.raises(ValueError, match="超过桶容量"):
            limiter.wait_for_token(10)

    def test_wait_for_token_invalid_tokens(self):
        """测试无效的令牌数"""
        limiter = RateLimiter(rate=10)

        with pytest.raises(ValueError, match="令牌数必须大于 0"):
            limiter.wait_for_token(0)

    def test_reset(self):
        """测试重置功能"""
        limiter = RateLimiter(rate=10, capacity=10)

        # 消耗一些令牌
        limiter.acquire(7)
        assert 2.9 <= limiter.get_available_tokens() <= 3.1

        # 重置
        limiter.reset()
        assert 9.9 <= limiter.get_available_tokens() <= 10.1

    def test_thread_safety(self):
        """测试线程安全性"""
        # 使用较大的速率以减少令牌补充的影响
        limiter = RateLimiter(rate=1000, capacity=100)
        success_count = [0]
        lock = threading.Lock()

        def worker():
            """工作线程"""
            for _ in range(10):
                if limiter.acquire(1):
                    with lock:
                        success_count[0] += 1

        # 创建 20 个线程，每个尝试获取 10 个令牌
        threads = [threading.Thread(target=worker) for _ in range(20)]

        # 快速启动所有线程以减少时间差
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 由于令牌桶会自动补充，成功次数可能略大于初始容量
        # 但应该在合理范围内（考虑到线程执行时间内的令牌补充）
        # 20个线程 * 10次尝试 = 200次尝试，初始100个令牌
        # 允许一定的令牌补充，但不应该所有请求都成功
        assert 100 <= success_count[0] <= 150  # 放宽限制以适应令牌补充

    def test_repr(self):
        """测试字符串表示"""
        limiter = RateLimiter(rate=10, capacity=20)
        repr_str = repr(limiter)

        assert "RateLimiter" in repr_str
        assert "rate=10" in repr_str
        assert "capacity=20" in repr_str


class TestMultiRateLimiter:
    """MultiRateLimiter 类测试"""

    def test_add_and_get_limiter(self):
        """测试添加和获取限制器"""
        multi = MultiRateLimiter()

        # 添加限制器
        multi.add_limiter("api1", rate=10, capacity=20)

        # 获取限制器
        limiter = multi.get_limiter("api1")
        assert limiter is not None
        assert limiter.get_rate() == 10
        assert limiter.get_capacity() == 20

    def test_get_nonexistent_limiter(self):
        """测试获取不存在的限制器"""
        multi = MultiRateLimiter()

        limiter = multi.get_limiter("nonexistent")
        assert limiter is None

    def test_remove_limiter(self):
        """测试移除限制器"""
        multi = MultiRateLimiter()

        # 添加限制器
        multi.add_limiter("api1", rate=10)
        assert multi.get_limiter("api1") is not None

        # 移除限制器
        result = multi.remove_limiter("api1")
        assert result is True
        assert multi.get_limiter("api1") is None

        # 再次移除应该返回 False
        result = multi.remove_limiter("api1")
        assert result is False

    def test_acquire_from_limiter(self):
        """测试从指定限制器获取令牌"""
        multi = MultiRateLimiter()
        multi.add_limiter("api1", rate=10, capacity=10)

        # 获取令牌
        assert multi.acquire("api1", 5) is True

        # 检查剩余令牌
        limiter = multi.get_limiter("api1")
        assert 4.9 <= limiter.get_available_tokens() <= 5.1

    def test_acquire_from_nonexistent_limiter(self):
        """测试从不存在的限制器获取令牌"""
        multi = MultiRateLimiter()

        with pytest.raises(KeyError, match="速率限制器不存在"):
            multi.acquire("nonexistent")

    def test_wait_for_token_from_limiter(self):
        """测试从指定限制器等待获取令牌"""
        multi = MultiRateLimiter()
        multi.add_limiter("api1", rate=10, capacity=10)

        # 消耗所有令牌
        multi.acquire("api1", 10)

        # 等待获取令牌
        result = multi.wait_for_token("api1", 1, timeout=1.0)
        assert result is True

    def test_wait_for_token_from_nonexistent_limiter(self):
        """测试从不存在的限制器等待获取令牌"""
        multi = MultiRateLimiter()

        with pytest.raises(KeyError, match="速率限制器不存在"):
            multi.wait_for_token("nonexistent")

    def test_list_limiters(self):
        """测试列出所有限制器"""
        multi = MultiRateLimiter()

        # 初始时应该为空
        assert multi.list_limiters() == []

        # 添加多个限制器
        multi.add_limiter("api1", rate=10)
        multi.add_limiter("api2", rate=20)
        multi.add_limiter("api3", rate=30)

        # 列出所有限制器
        limiters = multi.list_limiters()
        assert len(limiters) == 3
        assert "api1" in limiters
        assert "api2" in limiters
        assert "api3" in limiters

    def test_multiple_independent_limiters(self):
        """测试多个独立的限制器"""
        multi = MultiRateLimiter()

        # 添加两个限制器
        multi.add_limiter("api1", rate=10, capacity=10)
        multi.add_limiter("api2", rate=20, capacity=20)

        # 从 api1 获取令牌
        multi.acquire("api1", 5)

        # api1 应该剩余 5 个令牌
        limiter1 = multi.get_limiter("api1")
        assert 4.9 <= limiter1.get_available_tokens() <= 5.1

        # api2 应该仍然有 20 个令牌（不受影响）
        limiter2 = multi.get_limiter("api2")
        assert 19.9 <= limiter2.get_available_tokens() <= 20.1

    def test_repr(self):
        """测试字符串表示"""
        multi = MultiRateLimiter()
        multi.add_limiter("api1", rate=10)
        multi.add_limiter("api2", rate=20)

        repr_str = repr(multi)
        assert "MultiRateLimiter" in repr_str
        assert "api1" in repr_str
        assert "api2" in repr_str


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("开始运行速率限制器单元测试")
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
