#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一错误处理模块

本模块定义了应用程序的统一错误类型体系，包括：
- 错误基类 AppError
- 错误码枚举 ErrorCode
- 错误严重级别 ErrorSeverity
- 各类具体错误类型

所有错误消息使用中文，便于用户理解。
"""

from enum import Enum
from typing import Dict, Any, Optional, List


class ErrorSeverity(str, Enum):
    """错误严重级别"""
    ERROR = "error"      # 错误：需要用户处理
    WARNING = "warning"  # 警告：可能影响功能
    INFO = "info"        # 信息：提示性消息


class ErrorCode(str, Enum):
    """错误码枚举"""
    # 用户输入错误 (1xxx)
    INVALID_INPUT = "INVALID_INPUT"
    INPUT_TOO_SHORT = "INPUT_TOO_SHORT"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"
    INVALID_FORMAT = "INVALID_FORMAT"
    FORBIDDEN_CONTENT = "FORBIDDEN_CONTENT"
    
    # API 错误 (2xxx)
    API_ERROR = "API_ERROR"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"
    API_INVALID_KEY = "API_INVALID_KEY"
    
    # 网络错误 (3xxx)
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    
    # 配置错误 (4xxx)
    CONFIG_ERROR = "CONFIG_ERROR"
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"
    
    # 系统错误 (5xxx)
    SERVICE_ERROR = "SERVICE_ERROR"
    RESOURCE_ERROR = "RESOURCE_ERROR"
    FILE_ERROR = "FILE_ERROR"
    
    # 认证错误 (6xxx)
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    
    # 未知错误 (9xxx)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class AppError(Exception):
    """
    应用错误基类
    
    所有自定义错误都应该继承此类。
    
    Attributes:
        message: 错误消息（中文）
        code: 错误码
        details: 错误详细信息
        severity: 错误严重级别
        suggestions: 修复建议列表
        retryable: 是否可重试
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        suggestions: Optional[List[str]] = None,
        retryable: bool = False
    ):
        """
        初始化错误
        
        Args:
            message: 错误消息（中文）
            code: 错误码
            details: 错误详细信息
            severity: 错误严重级别
            suggestions: 修复建议列表
            retryable: 是否可重试
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.severity = severity
        self.suggestions = suggestions or []
        self.retryable = retryable
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            错误信息字典
        """
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "suggestions": self.suggestions,
            "retryable": self.retryable
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"[{self.code.value}] {self.message}"
    
    def __repr__(self) -> str:
        """调试表示"""
        return (
            f"AppError(code={self.code.value}, "
            f"message={self.message!r}, "
            f"severity={self.severity.value})"
        )


# ============================================================================
# 用户错误类（输入验证、格式错误等）
# ============================================================================

class ValidationError(AppError):
    """
    输入验证错误
    
    当用户输入不符合验证规则时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        constraint: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            field: 字段名
            value: 字段值
            constraint: 约束条件
            suggestions: 修复建议
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if constraint:
            details["constraint"] = constraint
        
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_INPUT,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or [],
            retryable=False
        )


class InputError(AppError):
    """
    输入格式错误
    
    当用户输入格式不正确时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        input_type: Optional[str] = None,
        expected_format: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化输入错误
        
        Args:
            message: 错误消息
            input_type: 输入类型
            expected_format: 期望格式
            suggestions: 修复建议
        """
        details = {}
        if input_type:
            details["input_type"] = input_type
        if expected_format:
            details["expected_format"] = expected_format
        
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_FORMAT,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or [],
            retryable=False
        )


class AuthenticationError(AppError):
    """
    认证错误
    
    当认证失败时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "认证失败",
        auth_type: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化认证错误
        
        Args:
            message: 错误消息
            auth_type: 认证类型
            suggestions: 修复建议
        """
        details = {}
        if auth_type:
            details["auth_type"] = auth_type
        
        super().__init__(
            message=message,
            code=ErrorCode.AUTHENTICATION_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查认证凭据是否正确"],
            retryable=False
        )


# ============================================================================
# 系统错误类（配置、服务、资源等）
# ============================================================================

class ConfigError(AppError):
    """
    配置错误
    
    当配置文件缺失或无效时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化配置错误
        
        Args:
            message: 错误消息
            config_key: 配置键
            config_file: 配置文件路径
            suggestions: 修复建议
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_file:
            details["config_file"] = config_file
        
        super().__init__(
            message=message,
            code=ErrorCode.CONFIG_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查配置文件是否正确"],
            retryable=False
        )


class ServiceError(AppError):
    """
    服务异常
    
    当服务内部发生异常时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化服务错误
        
        Args:
            message: 错误消息
            service_name: 服务名称
            operation: 操作名称
            suggestions: 修复建议
        """
        details = {}
        if service_name:
            details["service_name"] = service_name
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            code=ErrorCode.SERVICE_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请稍后重试或联系技术支持"],
            retryable=True
        )


class ResourceError(AppError):
    """
    资源不足错误
    
    当系统资源不足时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        required: Optional[str] = None,
        available: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化资源错误
        
        Args:
            message: 错误消息
            resource_type: 资源类型
            required: 所需资源
            available: 可用资源
            suggestions: 修复建议
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if required:
            details["required"] = required
        if available:
            details["available"] = available
        
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请释放部分资源后重试"],
            retryable=True
        )


# ============================================================================
# 网络错误类（API、超时、连接等）
# ============================================================================

class APIError(AppError):
    """
    API 调用失败错误
    
    当 API 调用失败时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "API 调用失败",
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化 API 错误
        
        Args:
            message: 错误消息
            api_name: API 名称
            status_code: HTTP 状态码
            response_body: 响应体
            suggestions: 修复建议
        """
        details = {}
        if api_name:
            details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        
        super().__init__(
            message=message,
            code=ErrorCode.API_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查 API 配置或稍后重试"],
            retryable=True
        )


class APITimeoutError(AppError):
    """
    API 超时错误
    
    当 API 调用超时时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "API 调用超时",
        api_name: Optional[str] = None,
        timeout: Optional[int] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化超时错误
        
        Args:
            message: 错误消息
            api_name: API 名称
            timeout: 超时时间（秒）
            suggestions: 修复建议
        """
        details = {}
        if api_name:
            details["api_name"] = api_name
        if timeout:
            details["timeout"] = timeout
        
        super().__init__(
            message=message,
            code=ErrorCode.TIMEOUT,
            details=details,
            severity=ErrorSeverity.WARNING,
            suggestions=suggestions or ["请检查网络连接或增加超时时间"],
            retryable=True
        )


class APIRateLimitError(AppError):
    """
    API 速率限制错误
    
    当超过 API 速率限制时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "超过 API 速率限制",
        api_name: Optional[str] = None,
        retry_after: Optional[int] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化速率限制错误
        
        Args:
            message: 错误消息
            api_name: API 名称
            retry_after: 重试等待时间（秒）
            suggestions: 修复建议
        """
        details = {}
        if api_name:
            details["api_name"] = api_name
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            code=ErrorCode.API_RATE_LIMIT,
            details=details,
            severity=ErrorSeverity.WARNING,
            suggestions=suggestions or [f"请等待 {retry_after} 秒后重试" if retry_after else "请稍后重试"],
            retryable=True
        )


class APIAuthenticationError(AppError):
    """
    API 认证错误
    
    当 API 认证失败时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "API 认证失败",
        api_name: Optional[str] = None,
        suggestion: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化 API 认证错误
        
        Args:
            message: 错误消息
            api_name: API 名称
            suggestion: 单个修复建议（向后兼容）
            suggestions: 修复建议列表
        """
        details = {}
        if api_name:
            details["api_name"] = api_name
        
        # 合并 suggestion 和 suggestions
        all_suggestions = suggestions or []
        if suggestion and suggestion not in all_suggestions:
            all_suggestions.insert(0, suggestion)
        if not all_suggestions:
            all_suggestions = ["请检查 API Key 是否正确配置"]
        
        super().__init__(
            message=message,
            code=ErrorCode.API_INVALID_KEY,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=all_suggestions,
            retryable=False
        )


class ConnectionError(AppError):
    """
    连接错误
    
    当网络连接失败时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "网络连接失败",
        host: Optional[str] = None,
        port: Optional[int] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化连接错误
        
        Args:
            message: 错误消息
            host: 主机地址
            port: 端口号
            suggestions: 修复建议
        """
        details = {}
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        
        super().__init__(
            message=message,
            code=ErrorCode.CONNECTION_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查网络连接是否正常"],
            retryable=True
        )


# ============================================================================
# 业务错误类（内容生成等）
# ============================================================================

class ContentGenerationError(AppError):
    """
    内容生成错误
    
    当内容生成失败时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        generation_type: Optional[str] = None,
        attempt: Optional[int] = None,
        max_attempts: Optional[int] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化内容生成错误
        
        Args:
            message: 错误消息
            generation_type: 生成类型（content, image 等）
            attempt: 当前尝试次数
            max_attempts: 最大尝试次数
            suggestions: 修复建议
        """
        details = {}
        if generation_type:
            details["generation_type"] = generation_type
        if attempt:
            details["attempt"] = attempt
        if max_attempts:
            details["max_attempts"] = max_attempts
        
        super().__init__(
            message=message,
            code=ErrorCode.SERVICE_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查输入内容或稍后重试"],
            retryable=True
        )


# ============================================================================
# 工具函数
# ============================================================================

def wrap_exception(
    original_exception: Exception,
    message: str,
    exception_class: type = AppError,
    **kwargs: Any
) -> AppError:
    """
    包装原始异常为应用错误
    
    Args:
        original_exception: 原始异常
        message: 错误消息
        exception_class: 目标异常类
        **kwargs: 其他参数
    
    Returns:
        包装后的应用错误
    """
    # 提取 details 参数（如果存在）
    details = kwargs.pop("details", {})
    
    # 添加原始异常信息到 details
    details["original_error"] = str(original_exception)
    details["original_type"] = type(original_exception).__name__
    
    # 创建异常实例
    try:
        # 尝试使用所有参数创建异常
        error = exception_class(message=message, **kwargs)
        # 手动设置 details（因为某些子类可能不接受 details 参数）
        if hasattr(error, 'details'):
            error.details.update(details)
        return error
    except TypeError:
        # 如果失败，只使用 message 参数
        error = exception_class(message=message)
        if hasattr(error, 'details'):
            error.details.update(details)
            # 将其他 kwargs 也添加到 details
            error.details.update(kwargs)
        return error



# ============================================================================
# 文件错误类
# ============================================================================

class FileNotFoundError(AppError):
    """
    文件未找到错误
    
    当文件不存在时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "文件未找到",
        file_path: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化文件未找到错误
        
        Args:
            message: 错误消息
            file_path: 文件路径
            suggestions: 修复建议
        """
        details = {}
        if file_path:
            details["file_path"] = file_path
        
        super().__init__(
            message=message,
            code=ErrorCode.FILE_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查文件路径是否正确"],
            retryable=False
        )


# ============================================================================
# 内容验证错误类
# ============================================================================

class ContentValidationError(AppError):
    """
    内容验证错误
    
    当内容验证失败时抛出此错误。
    """
    
    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        validation_rule: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化内容验证错误
        
        Args:
            message: 错误消息
            content_type: 内容类型
            validation_rule: 验证规则
            suggestions: 修复建议
        """
        details = {}
        if content_type:
            details["content_type"] = content_type
        if validation_rule:
            details["validation_rule"] = validation_rule
        
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_INPUT,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请检查内容是否符合要求"],
            retryable=False
        )


class ContentSafetyError(AppError):
    """
    内容安全错误
    
    当内容包含敏感或不安全信息时抛出此错误。
    """
    
    def __init__(
        self,
        message: str = "内容包含敏感信息",
        forbidden_words: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        初始化内容安全错误
        
        Args:
            message: 错误消息
            forbidden_words: 敏感词列表
            suggestions: 修复建议
        """
        details = {}
        if forbidden_words:
            details["forbidden_words"] = forbidden_words
        
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN_CONTENT,
            details=details,
            severity=ErrorSeverity.ERROR,
            suggestions=suggestions or ["请移除敏感内容后重试"],
            retryable=False
        )
