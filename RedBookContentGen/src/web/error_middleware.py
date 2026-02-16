#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理中间件

提供统一的错误处理和响应格式化功能。
"""

from typing import Dict, Any, Tuple, Optional
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from src.core.exceptions import (
    AppError,
    ErrorCode,
    ErrorSeverity,
    ValidationError,
    APIError,
    APITimeoutError,
    APIRateLimitError,
    ConfigError,
    ServiceError
)
from src.core.logger import Logger


class ErrorMiddleware:
    """
    错误处理中间件
    
    捕获所有异常并返回统一的 JSON 响应格式。
    """
    
    def __init__(self, app: Optional[Flask] = None):
        """
        初始化错误处理中间件
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """
        初始化 Flask 应用的错误处理
        
        Args:
            app: Flask 应用实例
        """
        self.app = app
        
        # 注册错误处理器
        app.register_error_handler(AppError, self.handle_app_error)
        app.register_error_handler(HTTPException, self.handle_http_exception)
        app.register_error_handler(Exception, self.handle_generic_exception)
    
    def handle_app_error(self, error: AppError) -> Tuple[Dict[str, Any], int]:
        """
        处理应用错误
        
        Args:
            error: 应用错误实例
            
        Returns:
            (响应数据, HTTP 状态码)
        """
        # 记录错误日志
        self._log_error(error)
        
        # 格式化错误响应
        response = self._format_error_response(error)
        
        # 确定 HTTP 状态码
        status_code = self._get_http_status_code(error)
        
        return jsonify(response), status_code
    
    def handle_http_exception(self, error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """
        处理 HTTP 异常
        
        Args:
            error: HTTP 异常实例
            
        Returns:
            (响应数据, HTTP 状态码)
        """
        # 记录错误日志
        Logger.warning(
            f"HTTP 异常: {error.code} - {error.name}",
            logger_name="error_middleware",
            status_code=error.code,
            description=error.description,
            url=request.url,
            method=request.method
        )
        
        # 格式化错误响应
        response = {
            "success": False,
            "error": {
                "code": f"HTTP_{error.code}",
                "message": error.description or error.name,
                "details": {
                    "status_code": error.code,
                    "url": request.url,
                    "method": request.method
                },
                "severity": "error",
                "suggestions": self._get_http_error_suggestions(error.code),
                "retryable": error.code in [408, 429, 500, 502, 503, 504]
            }
        }
        
        return jsonify(response), error.code or 500
    
    def handle_generic_exception(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """
        处理通用异常
        
        Args:
            error: 异常实例
            
        Returns:
            (响应数据, HTTP 状态码)
        """
        # 记录错误日志
        Logger.error(
            f"未捕获的异常: {type(error).__name__}",
            logger_name="error_middleware",
            error_type=type(error).__name__,
            error_message=str(error),
            url=request.url,
            method=request.method,
            exc_info=True
        )
        
        # 格式化错误响应
        response = {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
                "details": {
                    "error_type": type(error).__name__,
                    "url": request.url,
                    "method": request.method
                },
                "severity": "error",
                "suggestions": [
                    "请稍后重试",
                    "如果问题持续存在，请联系技术支持"
                ],
                "retryable": True
            }
        }
        
        return jsonify(response), 500
    
    def _format_error_response(self, error: AppError) -> Dict[str, Any]:
        """
        格式化错误响应
        
        Args:
            error: 应用错误实例
            
        Returns:
            错误响应字典
        """
        return {
            "success": False,
            "error": {
                "code": error.code.value,
                "message": error.message,
                "details": error.details,
                "severity": error.severity.value,
                "suggestions": error.suggestions,
                "retryable": error.retryable
            }
        }
    
    def _get_http_status_code(self, error: AppError) -> int:
        """
        根据错误类型确定 HTTP 状态码
        
        Args:
            error: 应用错误实例
            
        Returns:
            HTTP 状态码
        """
        # 根据错误类型映射 HTTP 状态码
        if isinstance(error, ValidationError):
            return 400  # Bad Request
        elif isinstance(error, ConfigError):
            return 500  # Internal Server Error
        elif isinstance(error, APITimeoutError):
            return 504  # Gateway Timeout
        elif isinstance(error, APIRateLimitError):
            return 429  # Too Many Requests
        elif isinstance(error, (APIError, ServiceError)):
            return 503  # Service Unavailable
        elif error.code == ErrorCode.AUTHENTICATION_ERROR:
            return 401  # Unauthorized
        elif error.code == ErrorCode.AUTHORIZATION_ERROR:
            return 403  # Forbidden
        elif error.code in [ErrorCode.INVALID_INPUT, ErrorCode.INPUT_TOO_SHORT, 
                           ErrorCode.INPUT_TOO_LONG, ErrorCode.INVALID_FORMAT]:
            return 400  # Bad Request
        elif error.code == ErrorCode.FILE_ERROR:
            return 404  # Not Found
        else:
            return 500  # Internal Server Error
    
    def _get_http_error_suggestions(self, status_code: int) -> list:
        """
        根据 HTTP 状态码获取修复建议
        
        Args:
            status_code: HTTP 状态码
            
        Returns:
            修复建议列表
        """
        suggestions_map = {
            400: ["请检查请求参数是否正确", "请参考 API 文档了解正确的请求格式"],
            401: ["请检查认证信息是否正确", "请确保已登录"],
            403: ["您没有权限访问此资源", "请联系管理员获取权限"],
            404: ["请求的资源不存在", "请检查 URL 是否正确"],
            405: ["请求方法不被允许", "请使用正确的 HTTP 方法"],
            408: ["请求超时", "请检查网络连接后重试"],
            429: ["请求过于频繁", "请稍后再试"],
            500: ["服务器内部错误", "请稍后重试或联系技术支持"],
            502: ["网关错误", "请稍后重试"],
            503: ["服务暂时不可用", "请稍后重试"],
            504: ["网关超时", "请稍后重试"]
        }
        
        return suggestions_map.get(status_code, ["请稍后重试"])
    
    def _log_error(self, error: AppError) -> None:
        """
        记录错误日志
        
        Args:
            error: 应用错误实例
        """
        log_data = {
            "logger_name": "error_middleware",
            "error_code": error.code.value,
            "error_message": error.message,
            "error_details": error.details,
            "severity": error.severity.value,
            "retryable": error.retryable,
            "url": request.url if request else None,
            "method": request.method if request else None
        }
        
        # 根据严重级别选择日志级别
        if error.severity == ErrorSeverity.ERROR:
            Logger.error(f"应用错误: {error.message}", **log_data)
        elif error.severity == ErrorSeverity.WARNING:
            Logger.warning(f"应用警告: {error.message}", **log_data)
        else:
            Logger.info(f"应用信息: {error.message}", **log_data)


def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[list] = None,
    severity: str = "error",
    retryable: bool = False
) -> Dict[str, Any]:
    """
    创建标准错误响应
    
    Args:
        code: 错误码
        message: 错误消息
        details: 错误详情
        suggestions: 修复建议
        severity: 严重级别
        retryable: 是否可重试
        
    Returns:
        错误响应字典
    """
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "severity": severity,
            "suggestions": suggestions or [],
            "retryable": retryable
        }
    }
