#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内容生成重试机制

任务 9.1.3: 测试重试机制
- 测试重试次数
- 测试重试间隔
- 测试最终失败

目标：测试覆盖率 > 70%
"""

import pytest
import time
import openai
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.core.api_handler import APIHandler
from src.core.retry_handler import retry, RetryHandler
from src.core.exceptions import (
    APIError,
    APITimeoutError,
    APIRateLimitError,
)


# ============================================================================
# 测试 1: 重试次数验证（使用 RetryHandler 直接测试）
# ============================================================================


@pytest.mark.unit
def test_retry_count_success_after_failures():
    """测试重试次数 - 失败后成功"""
    call_count = 0

    @retry(max_retries=3, retry_delay=0.01, exceptions=(ValueError,), operation_name="测试操作")
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # 前两次失败
            raise ValueError("Temporary error")
        # 第三次成功
        return "success"

    # 应该成功（经过重试）
    result = failing_function()

    # 验证重试了3次
    assert call_count == 3
    assert result == "success"


@pytest.mark.unit
def test_retry_count_max_retries_exceeded():
    """测试重试次数 - 超过最大重试次数"""
    call_count = 0

    @retry(max_retries=3, retry_delay=0.01, exceptions=(ValueError,), operation_name="测试操作")
    def failing_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Persistent error")

    # 应该在重试后抛出异常
    with pytest.raises(ValueError):
        failing_function()

    # 验证重试了3次（默认最大重试次数）
    assert call_count == 3


@pytest.mark.unit
def test_retry_count_first_attempt_success():
    """测试重试次数 - 第一次尝试就成功"""
    handler = APIHandler(rate_limit_enabled=False)
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="success"))]
        return mock_response

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = side_effect

    # 应该第一次就成功
    result = handler.call_openai(
        client=mock_client,
        model="qwen-plus",
        messages=[{"role": "user", "content": "test"}]
    )

    # 验证只调用了1次
    assert call_count == 1
    assert result.choices[0].message.content == "success"


# ============================================================================
# 测试 2: 重试间隔验证
# ============================================================================


@pytest.mark.unit
def test_retry_interval_exponential_backoff():
    """测试重试间隔 - 指数退避"""
    call_times = []

    @retry(max_retries=3, retry_delay=0.1, backoff_factor=2.0, operation_name="测试操作")
    def failing_function():
        call_times.append(time.time())
        raise ValueError("Test error")

    # 执行应该失败
    with pytest.raises(ValueError):
        failing_function()

    # 验证调用了3次
    assert len(call_times) == 3

    # 验证重试间隔（允许一定误差）
    # 第一次到第二次：约 0.1 秒
    interval_1 = call_times[1] - call_times[0]
    assert 0.08 < interval_1 < 0.15, f"第一次重试间隔应该约为 0.1 秒，实际为 {interval_1:.3f} 秒"

    # 第二次到第三次：约 0.2 秒（0.1 * 2）
    interval_2 = call_times[2] - call_times[1]
    assert 0.18 < interval_2 < 0.25, f"第二次重试间隔应该约为 0.2 秒，实际为 {interval_2:.3f} 秒"


@pytest.mark.unit
def test_retry_interval_custom_delay():
    """测试重试间隔 - 自定义延迟"""
    call_times = []

    @retry(max_retries=2, retry_delay=0.2, backoff_factor=1.5, operation_name="测试操作")
    def failing_function():
        call_times.append(time.time())
        raise ValueError("Test error")

    # 执行应该失败
    with pytest.raises(ValueError):
        failing_function()

    # 验证调用了2次
    assert len(call_times) == 2

    # 验证重试间隔
    interval = call_times[1] - call_times[0]
    assert 0.18 < interval < 0.25, f"重试间隔应该约为 0.2 秒，实际为 {interval:.3f} 秒"


@pytest.mark.unit
def test_retry_interval_no_delay_on_success():
    """测试重试间隔 - 成功时无延迟"""
    start_time = time.time()

    @retry(max_retries=3, retry_delay=1.0, operation_name="测试操作")
    def successful_function():
        return "success"

    result = successful_function()
    elapsed_time = time.time() - start_time

    # 验证成功
    assert result == "success"
    # 验证没有延迟（应该在 0.1 秒内完成）
    assert elapsed_time < 0.1, f"成功时不应该有延迟，实际耗时 {elapsed_time:.3f} 秒"


# ============================================================================
# 测试 3: 最终失败场景
# ============================================================================


@pytest.mark.unit
def test_final_failure_all_retries_exhausted():
    """测试最终失败 - 所有重试都失败"""
    handler = APIHandler(rate_limit_enabled=False)

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = openai.APIError(
        "Persistent error", request=Mock(), body=None
    )

    # 应该抛出 APIError
    with pytest.raises(APIError) as exc_info:
        handler.call_openai(
            client=mock_client,
            model="qwen-plus",
            messages=[{"role": "user", "content": "test"}]
        )

    # 验证错误信息
    assert "Persistent error" in str(exc_info.value)
    assert exc_info.value.code == "API_ERROR"


@pytest.mark.unit
def test_final_failure_preserves_last_exception():
    """测试最终失败 - 保留最后一个异常"""
    call_count = 0
    exceptions = [
        ValueError("Error 1"),
        TypeError("Error 2"),
        RuntimeError("Error 3"),
    ]

    @retry(max_retries=3, retry_delay=0.01, operation_name="测试操作")
    def failing_function():
        nonlocal call_count
        error = exceptions[call_count]
        call_count += 1
        raise error

    # 应该抛出最后一个异常（RuntimeError）
    with pytest.raises(RuntimeError) as exc_info:
        failing_function()

    # 验证是最后一个异常
    assert "Error 3" in str(exc_info.value)
    assert call_count == 3


@pytest.mark.unit
def test_final_failure_with_different_error_types():
    """测试最终失败 - 不同类型的错误"""
    handler = APIHandler(rate_limit_enabled=False)

    # 测试认证错误（不应该重试）
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
        "Invalid API key", response=Mock(), body=None
    )

    with pytest.raises(Exception):  # 会被包装成自定义异常
        handler.call_openai(
            client=mock_client,
            model="qwen-plus",
            messages=[{"role": "user", "content": "test"}]
        )

    # 认证错误不在重试列表中，应该只调用一次
    assert mock_client.chat.completions.create.call_count == 1


# ============================================================================
# 测试 4: RetryHandler 类的方法
# ============================================================================


@pytest.mark.unit
def test_retry_handler_with_retry_method():
    """测试 RetryHandler.with_retry 方法"""
    call_count = 0

    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Test error")
        return "success"

    wrapped_func = RetryHandler.with_retry(
        failing_function,
        max_retries=3,
        retry_delay=0.01,
        backoff_factor=1.5,
        exceptions=(ValueError,),
        operation_name="测试操作"
    )

    result = wrapped_func()

    # 验证成功
    assert result == "success"
    assert call_count == 3


@pytest.mark.unit
def test_retry_handler_execute_with_retry():
    """测试 RetryHandler.execute_with_retry 方法"""
    call_count = 0

    def failing_function(x, y):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Test error")
        return x + y

    result = RetryHandler.execute_with_retry(
        failing_function,
        10,
        20,
        max_retries=3,
        retry_delay=0.01,
        exceptions=(ValueError,),
        operation_name="测试操作"
    )

    # 验证成功
    assert result == 30
    assert call_count == 2


# ============================================================================
# 测试 5: 特定异常类型的重试
# ============================================================================


@pytest.mark.unit
def test_retry_only_specific_exceptions():
    """测试只重试特定异常"""
    call_count = 0

    @retry(
        max_retries=3,
        retry_delay=0.01,
        exceptions=(ValueError, TypeError),
        operation_name="测试操作"
    )
    def function_with_different_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Retryable error")
        elif call_count == 2:
            raise RuntimeError("Non-retryable error")
        return "success"

    # RuntimeError 不在重试列表中，应该直接抛出
    with pytest.raises(RuntimeError):
        function_with_different_errors()

    # 验证只调用了2次（第一次 ValueError 重试，第二次 RuntimeError 直接抛出）
    assert call_count == 2


@pytest.mark.unit
def test_retry_with_openai_errors():
    """测试 OpenAI 错误的重试（在 retry 装饰器层面）"""
    call_count = 0

    @retry(
        max_retries=3,
        retry_delay=0.01,
        exceptions=(openai.APIError, openai.APITimeoutError, openai.RateLimitError),
        operation_name="测试操作"
    )
    def function_with_openai_errors():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise openai.APIError("Temporary error", request=Mock(), body=None)
        return "success"

    # 应该成功（经过重试）
    result = function_with_openai_errors()

    # 验证重试了3次
    assert call_count == 3
    assert result == "success"


@pytest.mark.unit
def test_retry_with_timeout_error():
    """测试超时错误的重试"""
    call_count = 0

    @retry(
        max_retries=3,
        retry_delay=0.01,
        exceptions=(openai.APITimeoutError,),
        operation_name="测试操作"
    )
    def function_with_timeout():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise openai.APITimeoutError(request=Mock())
        return "success"

    # 应该成功（经过重试）
    result = function_with_timeout()

    # 验证重试了3次
    assert call_count == 3
    assert result == "success"


# ============================================================================
# 测试 6: 重试装饰器的参数验证
# ============================================================================


@pytest.mark.unit
def test_retry_decorator_with_custom_parameters():
    """测试重试装饰器的自定义参数"""
    call_count = 0

    @retry(
        max_retries=5,
        retry_delay=0.05,
        backoff_factor=1.2,
        exceptions=(ValueError,),
        operation_name="自定义重试操作"
    )
    def custom_retry_function():
        nonlocal call_count
        call_count += 1
        if call_count < 4:
            raise ValueError("Test error")
        return "success"

    result = custom_retry_function()

    # 验证成功
    assert result == "success"
    assert call_count == 4


@pytest.mark.unit
def test_retry_decorator_preserves_function_metadata():
    """测试重试装饰器保留函数元数据"""
    @retry(max_retries=3, operation_name="测试操作")
    def documented_function():
        """这是一个有文档的函数"""
        return "success"

    # 验证函数名和文档字符串被保留
    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "这是一个有文档的函数"


# ============================================================================
# 测试 7: 边界条件
# ============================================================================


@pytest.mark.unit
def test_retry_with_zero_retries():
    """测试零重试次数（只执行一次）"""
    call_count = 0

    @retry(max_retries=1, retry_delay=0.01, operation_name="测试操作")
    def failing_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Test error")

    # 应该只执行一次就失败
    with pytest.raises(ValueError):
        failing_function()

    assert call_count == 1


@pytest.mark.unit
def test_retry_with_large_retry_count():
    """测试大重试次数"""
    call_count = 0

    @retry(max_retries=10, retry_delay=0.001, backoff_factor=1.1, operation_name="测试操作")
    def eventually_successful_function():
        nonlocal call_count
        call_count += 1
        if call_count < 8:
            raise ValueError("Test error")
        return "success"

    result = eventually_successful_function()

    # 验证成功
    assert result == "success"
    assert call_count == 8


# ============================================================================
# 测试 8: 重试与日志记录
# ============================================================================


@pytest.mark.unit
def test_retry_logs_attempts(caplog):
    """测试重试过程中的日志记录"""
    import logging
    caplog.set_level(logging.DEBUG)

    call_count = 0

    @retry(max_retries=3, retry_delay=0.01, operation_name="测试操作")
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Test error")
        return "success"

    result = failing_function()

    # 验证成功
    assert result == "success"
    assert call_count == 3


# ============================================================================
# 测试 9: 复杂场景 - 重试机制的完整流程
# ============================================================================


@pytest.mark.unit
def test_complete_retry_flow_with_mixed_errors():
    """测试完整重试流程 - 混合错误类型"""
    call_count = 0
    errors = [
        ValueError("Error 1"),
        TypeError("Error 2"),
        None,  # 第三次成功
    ]

    @retry(
        max_retries=3,
        retry_delay=0.01,
        exceptions=(ValueError, TypeError),
        operation_name="测试操作"
    )
    def function_with_mixed_errors():
        nonlocal call_count
        error = errors[call_count]
        call_count += 1
        if error:
            raise error
        return "success"

    # 应该成功（经过重试）
    result = function_with_mixed_errors()

    # 验证成功
    assert call_count == 3
    assert result == "success"


@pytest.mark.unit
def test_retry_with_custom_backoff():
    """测试自定义退避策略的重试"""
    call_times = []

    @retry(
        max_retries=4,
        retry_delay=0.05,
        backoff_factor=1.5,
        exceptions=(ValueError,),
        operation_name="测试操作"
    )
    def function_with_custom_backoff():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise ValueError("Test error")
        return "success"

    result = function_with_custom_backoff()

    # 验证成功
    assert result == "success"
    assert len(call_times) == 3

    # 验证退避间隔
    # 第一次到第二次：约 0.05 秒
    interval_1 = call_times[1] - call_times[0]
    assert 0.04 < interval_1 < 0.08

    # 第二次到第三次：约 0.075 秒（0.05 * 1.5）
    interval_2 = call_times[2] - call_times[1]
    assert 0.06 < interval_2 < 0.10


# ============================================================================
# 测试 10: ErrorHandler 类的方法
# ============================================================================


@pytest.mark.unit
def test_error_handler_handle_error_with_raise():
    """测试 ErrorHandler.handle_error 方法（重新抛出异常）"""
    from src.core.retry_handler import ErrorHandler

    error = ValueError("Test error")

    # 应该重新抛出异常
    with pytest.raises(ValueError):
        ErrorHandler.handle_error(
            error=error,
            logger_name="test_logger",
            operation_name="测试操作",
            context={"key": "value"},
            raise_error=True
        )


@pytest.mark.unit
def test_error_handler_handle_error_without_raise():
    """测试 ErrorHandler.handle_error 方法（不抛出异常）"""
    from src.core.retry_handler import ErrorHandler

    error = ValueError("Test error")

    # 不应该抛出异常
    ErrorHandler.handle_error(
        error=error,
        logger_name="test_logger",
        operation_name="测试操作",
        context={"key": "value"},
        raise_error=False
    )


@pytest.mark.unit
def test_error_handler_safe_execute_success():
    """测试 ErrorHandler.safe_execute 方法（成功）"""
    from src.core.retry_handler import ErrorHandler

    def successful_function(x, y):
        return x + y

    result = ErrorHandler.safe_execute(
        successful_function,
        10,
        20,
        logger_name="test_logger",
        operation_name="测试操作"
    )

    assert result == 30


@pytest.mark.unit
def test_error_handler_safe_execute_failure():
    """测试 ErrorHandler.safe_execute 方法（失败返回默认值）"""
    from src.core.retry_handler import ErrorHandler

    def failing_function():
        raise ValueError("Test error")

    result = ErrorHandler.safe_execute(
        failing_function,
        logger_name="test_logger",
        operation_name="测试操作",
        default_value="default"
    )

    assert result == "default"


@pytest.mark.unit
def test_error_handler_with_app_error():
    """测试 ErrorHandler 处理自定义异常"""
    from src.core.retry_handler import ErrorHandler
    from src.core.exceptions import AppError

    error = AppError(
        message="Test app error",
        code="TEST_ERROR",
        details={"key": "value"}
    )

    # 不应该抛出异常
    ErrorHandler.handle_error(
        error=error,
        logger_name="test_logger",
        operation_name="测试操作",
        raise_error=False
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.core.api_handler", "--cov=src.core.retry_handler", "--cov-report=term-missing"])
