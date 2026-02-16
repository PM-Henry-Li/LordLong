#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理装饰器和中间件

提供统一的错误处理机制
"""

from functools import wraps
from typing import Callable, Tuple, Any
from flask import jsonify, current_app, Flask, Response, render_template, request
from pydantic import ValidationError as PydanticValidationError

from src.core.logger import Logger
from src.core.errors import (
    AppError,
    ValidationError,
    ContentGenerationError,
    ImageGenerationError,
    create_error_response,
)


def handle_errors(func: Callable) -> Callable:
    """
    统一错误处理装饰器

    捕获所有异常并返回统一格式的错误响应

    Usage:
        @app.route('/api/example')
        @handle_errors

        def example():
            # 路由逻辑
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, int]:
        try:
            return func(*args, **kwargs)

        except PydanticValidationError as e:
            # Pydantic 验证错误
            errors = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                message = error["msg"]
                errors.append(f"{field}: {message}")

            validation_error = ValidationError(message="请求参数验证失败", details={"validation_errors": errors})

            Logger.warning("请求参数验证失败", logger_name="web_app", errors=errors)

            response = create_error_response(validation_error)
            return jsonify(response), validation_error.status_code

        except ValueError as e:
            # 值错误（通常是业务逻辑验证失败）
            error_msg = str(e)

            # 根据错误消息判断错误类型
            if "生成失败" in error_msg or "内容" in error_msg:
                app_error = ContentGenerationError(message=error_msg)
            elif "图片" in error_msg:
                app_error = ImageGenerationError(message=error_msg)
            else:
                app_error = ValidationError(message=error_msg)

            Logger.warning("业务逻辑错误", logger_name="web_app", error=error_msg)

            response = create_error_response(app_error)
            return jsonify(response), app_error.status_code

        except AppError as e:
            # 应用自定义错误
            Logger.error(
                f"应用错误: {e.code.value}", logger_name="web_app", error_code=e.code.value, error_message=e.message
            )

            response = create_error_response(e)
            return jsonify(response), e.status_code

        except Exception as e:
            # 未知错误
            Logger.exception("未知错误", logger_name="web_app")

            # 检查是否为调试模式
            debug_mode = current_app.config.get("DEBUG", False)

            response = create_error_response(e, include_traceback=debug_mode)
            return jsonify(response), 500

    return wrapper


def register_error_handlers(app: Flask) -> None:
    """
    注册全局错误处理器

    Args:
        app: Flask 应用实例
    """

    def _is_api_request() -> bool:
        """判断是否为 API 请求"""
        return request.path.startswith('/api/') or request.accept_mimetypes.accept_json

    @app.errorhandler(400)
    def handle_bad_request(e: Exception) -> Tuple[Response, int]:
        """处理 400 错误"""
        error = ValidationError(message="无效的请求")
        
        if _is_api_request():
            response = create_error_response(error)
            return jsonify(response), 400
        else:
            return render_template(
                'error.html',
                error_code='400',
                error_title='无效的请求',
                error_message='您的请求格式不正确，请检查后重试。',
                suggestions=['检查请求参数是否正确', '确认请求格式符合要求'],
                show_retry=True
            ), 400

    @app.errorhandler(404)
    def handle_not_found(e: Exception) -> Tuple[Response, int]:
        """处理 404 错误"""
        from src.core.errors import ResourceNotFoundError

        error = ResourceNotFoundError(message="请求的页面或资源不存在")
        
        if _is_api_request():
            response = create_error_response(error)
            return jsonify(response), 404
        else:
            return render_template(
                'error.html',
                error_code='404',
                error_title='页面未找到',
                error_message='抱歉，您访问的页面不存在。',
                suggestions=['检查 URL 是否正确', '返回首页重新开始'],
                show_retry=False
            ), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e: Exception) -> Tuple[Response, int]:
        """处理 405 错误"""
        error = ValidationError(
            message="不支持的请求方法", suggestions=["请检查 HTTP 方法是否正确（GET/POST/PUT/DELETE）"]
        )
        
        if _is_api_request():
            response = create_error_response(error)
            return jsonify(response), 405
        else:
            return render_template(
                'error.html',
                error_code='405',
                error_title='请求方法不允许',
                error_message='该操作不支持当前的请求方法。',
                suggestions=['请检查 HTTP 方法是否正确（GET/POST/PUT/DELETE）'],
                show_retry=False
            ), 405

    @app.errorhandler(500)
    def handle_internal_error(e: Exception) -> Tuple[Response, int]:
        """处理 500 错误"""
        Logger.exception("服务器内部错误", logger_name="web_app")

        debug_mode = app.config.get("DEBUG", False)
        
        if _is_api_request():
            response = create_error_response(e, include_traceback=debug_mode)
            return jsonify(response), 500
        else:
            error_details = str(e) if debug_mode else None
            return render_template(
                'error.html',
                error_code='500',
                error_title='服务器错误',
                error_message='抱歉，服务器遇到了一个错误。我们正在努力修复，请稍后再试。',
                error_details=error_details,
                suggestions=['稍后重试', '如果问题持续，请联系技术支持'],
                show_retry=True
            ), 500

    @app.errorhandler(AppError)
    def handle_app_error(e: AppError) -> Tuple[Response, int]:
        """处理应用自定义错误"""
        Logger.error(
            f"应用错误: {e.code.value}", logger_name="web_app", error_code=e.code.value, error_message=e.message
        )

        if _is_api_request():
            response = create_error_response(e)
            return jsonify(response), e.status_code
        else:
            return render_template(
                'error.html',
                error_code=e.code.value,
                error_title=e.message,
                error_message=e.message,
                error_details=str(e.details) if e.details else None,
                suggestions=e.suggestions,
                show_retry=e.retryable
            ), e.status_code


def convert_service_errors(func: Callable) -> Callable:
    """
    服务层错误转换装饰器

    将服务层抛出的异常转换为 Web 层的错误类型

    Usage:
        @convert_service_errors

        def some_service_method():
            # 服务逻辑
            pass
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)

        except ValueError as e:
            error_msg = str(e)

            # 根据错误消息判断错误类型
            if "内容生成" in error_msg or "文案" in error_msg:
                raise ContentGenerationError(message=error_msg)
            elif "图片生成" in error_msg or "图片" in error_msg:
                raise ImageGenerationError(message=error_msg)
            else:
                raise ValidationError(message=error_msg)

        except Exception:
            # 其他异常直接抛出，由上层处理
            raise

    return wrapper
