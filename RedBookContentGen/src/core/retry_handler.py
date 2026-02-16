#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试处理器模块

提供统一的重试逻辑和错误处理机制
"""

import time
from typing import Callable, TypeVar, Optional, Any, Dict
from functools import wraps
from src.core.logger import Logger
from src.core.exceptions import AppError

T = TypeVar("T")


class RetryHandler:
    """重试处理器，提供统一的重试逻辑"""

    @staticmethod
    def with_retry(
        func: Callable[..., T],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
        logger_name: str = "retry_handler",
        operation_name: str = "操作",
    ) -> Callable[..., T]:
        """
        为函数添加重试逻辑的装饰器

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 退避因子（每次重试延迟乘以此因子）
            exceptions: 需要重试的异常类型元组
            logger_name: 日志记录器名称
            operation_name: 操作名称（用于日志）

        Returns:
            包装后的函数
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = retry_delay

            for attempt in range(1, max_retries + 1):
                try:
                    Logger.debug(
                        f"正在执行{operation_name}", logger_name=logger_name, attempt=attempt, max_retries=max_retries
                    )

                    result = func(*args, **kwargs)

                    if attempt > 1:
                        Logger.info(f"{operation_name}成功", logger_name=logger_name, attempt=attempt)

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        Logger.warning(
                            f"{operation_name}失败，将在 {current_delay:.1f} 秒后重试",
                            logger_name=logger_name,
                            attempt=attempt,
                            max_retries=max_retries,
                            error=str(e),
                            retry_delay=current_delay,
                        )

                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        Logger.error(
                            f"{operation_name}失败，已达到最大重试次数",
                            logger_name=logger_name,
                            max_retries=max_retries,
                            error=str(e),
                        )

            # 所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception
            raise Exception("重试失败但没有捕获到异常")

        return wrapper

    @staticmethod
    def execute_with_retry(
        func: Callable[..., T],
        *args: Any,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
        logger_name: str = "retry_handler",
        operation_name: str = "操作",
        **kwargs: Any,
    ) -> T:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 退避因子
            exceptions: 需要重试的异常类型元组
            logger_name: 日志记录器名称
            operation_name: 操作名称
            **kwargs: 函数的关键字参数

        Returns:
            函数执行结果
        """
        wrapped_func = RetryHandler.with_retry(
            func,
            max_retries=max_retries,
            retry_delay=retry_delay,
            backoff_factor=backoff_factor,
            exceptions=exceptions,
            logger_name=logger_name,
            operation_name=operation_name,
        )

        return wrapped_func(*args, **kwargs)


class ErrorHandler:
    """错误处理器，提供统一的错误处理机制"""

    @staticmethod
    def handle_error(
        error: Exception,
        logger_name: str = "error_handler",
        operation_name: str = "操作",
        context: Optional[Dict[str, Any]] = None,
        raise_error: bool = True,
    ) -> None:
        """
        统一的错误处理

        Args:
            error: 捕获的异常
            logger_name: 日志记录器名称
            operation_name: 操作名称
            context: 错误上下文信息
            raise_error: 是否重新抛出异常
        """
        error_info = {"operation": operation_name, "error_type": type(error).__name__, "error_message": str(error)}

        # 如果是自定义异常，添加更多详细信息
        if isinstance(error, AppError):
            error_info["error_code"] = str(error.code)
            error_info["error_details"] = error.details  # type: ignore[assignment]

        if context:
            error_info.update(context)

        Logger.error(f"{operation_name}发生错误", logger_name=logger_name, **error_info)

        if raise_error:
            raise error

    @staticmethod
    def safe_execute(
        func: Callable[..., T],
        *args: Any,
        logger_name: str = "error_handler",
        operation_name: str = "操作",
        default_value: Optional[T] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[T]:
        """
        安全执行函数，捕获异常并返回默认值

        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            logger_name: 日志记录器名称
            operation_name: 操作名称
            default_value: 发生错误时返回的默认值
            context: 错误上下文信息
            **kwargs: 函数的关键字参数

        Returns:
            函数执行结果或默认值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(
                error=e, logger_name=logger_name, operation_name=operation_name, context=context, raise_error=False
            )
            return default_value


def retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    logger_name: str = "retry_handler",
    operation_name: str = "操作",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    重试装饰器

    使用示例:
        @retry(max_retries=3, operation_name="API调用")

        def call_api():
            # API 调用代码
            pass

    Args:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型元组
        logger_name: 日志记录器名称
        operation_name: 操作名称
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return RetryHandler.with_retry(
            func,
            max_retries=max_retries,
            retry_delay=retry_delay,
            backoff_factor=backoff_factor,
            exceptions=exceptions,
            logger_name=logger_name,
            operation_name=operation_name,
        )

    return decorator
