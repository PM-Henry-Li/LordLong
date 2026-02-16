#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 错误处理模块

定义统一的错误类型和错误响应格式
"""

from typing import Dict, List, Optional, Any
from enum import Enum


class ErrorCode(str, Enum):
    """错误代码枚举"""

    # 客户端错误 (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"  # 无效请求
    INVALID_INPUT = "INVALID_INPUT"  # 输入验证失败
    INVALID_JSON = "INVALID_JSON"  # JSON 格式错误
    MISSING_FIELD = "MISSING_FIELD"  # 缺少必需字段
    INVALID_FIELD = "INVALID_FIELD"  # 字段值无效
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"  # 资源不存在

    # 服务器错误 (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"  # 内部错误
    SERVICE_ERROR = "SERVICE_ERROR"  # 服务错误
    API_ERROR = "API_ERROR"  # 外部 API 错误
    GENERATION_ERROR = "GENERATION_ERROR"  # 生成失败

    # 业务错误
    CONTENT_GENERATION_FAILED = "CONTENT_GENERATION_FAILED"  # 内容生成失败
    IMAGE_GENERATION_FAILED = "IMAGE_GENERATION_FAILED"  # 图片生成失败
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"  # 下载失败


class AppError(Exception):
    """应用错误基类"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        """
        初始化应用错误

        Args:
            message: 错误消息（用户友好的中文描述）
            code: 错误代码
            status_code: HTTP 状态码
            details: 错误详情（可选）
            suggestions: 解决建议（可选）
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.suggestions = suggestions or []

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            错误响应字典
        """
        error_dict: Dict[str, Any] = {"code": self.code.value, "message": self.message}

        if self.details:
            error_dict["details"] = self.details

        if self.suggestions:
            error_dict["suggestions"] = self.suggestions

        return error_dict


class ValidationError(AppError):
    """验证错误（400）"""

    def __init__(
        self,
        message: str = "请求参数验证失败",
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details,
            suggestions=suggestions or ["请检查输入参数是否符合要求"],
        )


class ResourceNotFoundError(AppError):
    """资源不存在错误（404）"""

    def __init__(
        self, message: str = "请求的资源不存在", resource_type: str = "资源", resource_id: Optional[str] = None
    ):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details=details,
            suggestions=["请检查资源路径是否正确", "资源可能已被删除"],
        )


class ContentGenerationError(AppError):
    """内容生成错误（500）"""

    def __init__(
        self,
        message: str = "内容生成失败",
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.CONTENT_GENERATION_FAILED,
            status_code=500,
            details=details,
            suggestions=suggestions or ["请检查输入文本是否符合要求", "请稍后重试", "如果问题持续，请联系技术支持"],
        )


class ImageGenerationError(AppError):
    """图片生成错误（500）"""

    def __init__(
        self,
        message: str = "图片生成失败",
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.IMAGE_GENERATION_FAILED,
            status_code=500,
            details=details,
            suggestions=suggestions or ["请检查图片生成参数是否正确", "请稍后重试", "可以尝试切换到模板模式"],
        )


class APIError(AppError):
    """外部 API 错误（502）"""

    def __init__(
        self, message: str = "外部服务调用失败", api_name: str = "未知服务", details: Optional[Dict[str, Any]] = None
    ):
        error_details = {"api_name": api_name}
        if details:
            error_details.update(details)

        super().__init__(
            message=message,
            code=ErrorCode.API_ERROR,
            status_code=502,
            details=error_details,
            suggestions=["外部服务暂时不可用", "请稍后重试", "如果问题持续，请联系技术支持"],
        )


def create_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """
    创建统一的错误响应

    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪（仅用于调试）

    Returns:
        错误响应字典
    """
    if isinstance(error, AppError):
        response: Dict[str, Any] = {"success": False, "error": error.to_dict()}
    else:
        # 未知错误，返回通用错误信息
        response = {
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": "服务器内部错误",
                "suggestions": ["请稍后重试", "如果问题持续，请联系技术支持"],
            },
        }

    # 调试模式下包含详细错误信息
    if include_traceback:
        import traceback

        response["error"]["traceback"] = traceback.format_exc()
        response["error"]["original_error"] = str(error)

    return response


def get_http_status_code(error: Exception) -> int:
    """
    获取错误对应的 HTTP 状态码

    Args:
        error: 异常对象

    Returns:
        HTTP 状态码
    """
    if isinstance(error, AppError):
        return error.status_code
    return 500
