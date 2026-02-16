#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试处理器测试
"""

import pytest
import time
from src.core.retry_handler import RetryHandler, ErrorHandler, retry


class TestRetryHandler:
    """重试处理器测试类"""

    def test_successful_execution_no_retry(self):
        """测试成功执行，无需重试"""
        call_count = 0

        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = RetryHandler.execute_with_retry(successful_func, max_retries=3, operation_name="测试操作")

        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """测试失败时重试"""
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("临时错误")
            return "success"

        result = RetryHandler.execute_with_retry(
            failing_func, max_retries=3, retry_delay=0.1, operation_name="测试操作"
        )

        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0

        def always_failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("永久错误")

        with pytest.raises(ValueError, match="永久错误"):
            RetryHandler.execute_with_retry(
                always_failing_func, max_retries=3, retry_delay=0.1, operation_name="测试操作"
            )

        assert call_count == 3

    def test_backoff_factor(self):
        """测试退避因子"""
        call_times = []

        def failing_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("临时错误")
            return "success"

        result = RetryHandler.execute_with_retry(
            failing_func, max_retries=3, retry_delay=0.1, backoff_factor=2.0, operation_name="测试操作"
        )

        assert result == "success"
        assert len(call_times) == 3

        # 验证退避时间
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 >= 0.1  # 第一次重试延迟至少 0.1 秒

        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert delay2 >= 0.2  # 第二次重试延迟至少 0.2 秒（0.1 * 2）

    def test_retry_decorator(self):
        """测试重试装饰器"""
        call_count = 0

        @retry(max_retries=3, retry_delay=0.1, operation_name="装饰器测试")
        def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("临时错误")
            return "success"

        result = decorated_func()

        assert result == "success"
        assert call_count == 2

    def test_specific_exceptions(self):
        """测试只重试特定异常"""
        call_count = 0

        def func_with_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("可重试错误")
            elif call_count == 2:
                raise TypeError("不可重试错误")

        # 只重试 ValueError
        with pytest.raises(TypeError, match="不可重试错误"):
            RetryHandler.execute_with_retry(
                func_with_different_errors,
                max_retries=3,
                retry_delay=0.1,
                exceptions=(ValueError,),
                operation_name="测试操作",
            )

        assert call_count == 2


class TestErrorHandler:
    """错误处理器测试类"""

    def test_handle_error_with_raise(self):
        """测试错误处理并重新抛出"""
        error = ValueError("测试错误")

        with pytest.raises(ValueError, match="测试错误"):
            ErrorHandler.handle_error(error=error, operation_name="测试操作", raise_error=True)

    def test_handle_error_without_raise(self):
        """测试错误处理不重新抛出"""
        error = ValueError("测试错误")

        # 不应该抛出异常
        ErrorHandler.handle_error(error=error, operation_name="测试操作", raise_error=False)

    def test_safe_execute_success(self):
        """测试安全执行成功"""

        def successful_func(x, y):
            return x + y

        result = ErrorHandler.safe_execute(successful_func, 10, 20, operation_name="测试操作")

        assert result == 30

    def test_safe_execute_with_default(self):
        """测试安全执行失败返回默认值"""

        def failing_func():
            raise ValueError("错误")

        result = ErrorHandler.safe_execute(failing_func, operation_name="测试操作", default_value="默认值")

        assert result == "默认值"

    def test_safe_execute_with_context(self):
        """测试安全执行带上下文"""

        def failing_func():
            raise ValueError("错误")

        result = ErrorHandler.safe_execute(
            failing_func, operation_name="测试操作", default_value=None, context={"user_id": "123", "action": "test"}
        )

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
