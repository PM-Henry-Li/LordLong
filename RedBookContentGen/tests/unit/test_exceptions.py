#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误类型单元测试

测试 src/core/exceptions.py 中定义的所有错误类型，包括：
- 错误消息格式
- 错误码映射
- 错误上下文
- 错误序列化
- 错误继承关系
"""

import pytest
from src.core.exceptions import (
    # 基础类
    AppError,
    ErrorCode,
    ErrorSeverity,
    # 用户错误
    ValidationError,
    InputError,
    AuthenticationError,
    # 系统错误
    ConfigError,
    ServiceError,
    ResourceError,
    # 网络错误
    APIError,
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    ConnectionError,
    # 业务错误
    ContentGenerationError,
    # 文件错误
    FileNotFoundError,
    # 内容验证错误
    ContentValidationError,
    ContentSafetyError,
    # 工具函数
    wrap_exception,
)


class TestErrorCode:
    """测试错误码枚举"""
    
    def test_error_code_values(self):
        """测试错误码的值"""
        assert ErrorCode.INVALID_INPUT.value == "INVALID_INPUT"
        assert ErrorCode.API_ERROR.value == "API_ERROR"
        assert ErrorCode.TIMEOUT.value == "TIMEOUT"
        assert ErrorCode.CONFIG_ERROR.value == "CONFIG_ERROR"
        assert ErrorCode.SERVICE_ERROR.value == "SERVICE_ERROR"
    
    def test_error_code_is_string(self):
        """测试错误码是字符串类型"""
        for code in ErrorCode:
            assert isinstance(code.value, str)
            assert len(code.value) > 0


class TestErrorSeverity:
    """测试错误严重级别枚举"""
    
    def test_severity_values(self):
        """测试严重级别的值"""
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"
    
    def test_severity_is_string(self):
        """测试严重级别是字符串类型"""
        for severity in ErrorSeverity:
            assert isinstance(severity.value, str)


class TestAppError:
    """测试应用错误基类"""
    
    def test_basic_error_creation(self):
        """测试基本错误创建"""
        error = AppError(
            message="测试错误",
            code=ErrorCode.UNKNOWN_ERROR
        )
        assert error.message == "测试错误"
        assert error.code == ErrorCode.UNKNOWN_ERROR
        assert error.severity == ErrorSeverity.ERROR
        assert error.details == {}
        assert error.suggestions == []
        assert error.retryable is False
    
    def test_error_with_details(self):
        """测试带详细信息的错误"""
        details = {"key": "value", "count": 42}
        error = AppError(
            message="测试错误",
            code=ErrorCode.SERVICE_ERROR,
            details=details
        )
        assert error.details == details
        assert error.details["key"] == "value"
        assert error.details["count"] == 42
    
    def test_error_with_suggestions(self):
        """测试带修复建议的错误"""
        suggestions = ["建议1", "建议2"]
        error = AppError(
            message="测试错误",
            suggestions=suggestions
        )
        assert error.suggestions == suggestions
        assert len(error.suggestions) == 2
    
    def test_error_severity_levels(self):
        """测试不同严重级别"""
        error_error = AppError("错误", severity=ErrorSeverity.ERROR)
        error_warning = AppError("警告", severity=ErrorSeverity.WARNING)
        error_info = AppError("信息", severity=ErrorSeverity.INFO)
        
        assert error_error.severity == ErrorSeverity.ERROR
        assert error_warning.severity == ErrorSeverity.WARNING
        assert error_info.severity == ErrorSeverity.INFO
    
    def test_error_retryable_flag(self):
        """测试可重试标志"""
        retryable_error = AppError("可重试", retryable=True)
        non_retryable_error = AppError("不可重试", retryable=False)
        
        assert retryable_error.retryable is True
        assert non_retryable_error.retryable is False
    
    def test_error_to_dict(self):
        """测试错误序列化为字典"""
        error = AppError(
            message="测试错误",
            code=ErrorCode.API_ERROR,
            details={"api": "test"},
            severity=ErrorSeverity.WARNING,
            suggestions=["建议1"],
            retryable=True
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["code"] == "API_ERROR"
        assert error_dict["message"] == "测试错误"
        assert error_dict["details"] == {"api": "test"}
        assert error_dict["severity"] == "warning"
        assert error_dict["suggestions"] == ["建议1"]
        assert error_dict["retryable"] is True
    
    def test_error_str_representation(self):
        """测试错误的字符串表示"""
        error = AppError(
            message="测试错误",
            code=ErrorCode.INVALID_INPUT
        )
        assert str(error) == "[INVALID_INPUT] 测试错误"
    
    def test_error_repr_representation(self):
        """测试错误的调试表示"""
        error = AppError(
            message="测试错误",
            code=ErrorCode.API_ERROR,
            severity=ErrorSeverity.WARNING
        )
        repr_str = repr(error)
        assert "AppError" in repr_str
        assert "API_ERROR" in repr_str
        assert "测试错误" in repr_str
        assert "warning" in repr_str


class TestValidationError:
    """测试输入验证错误"""
    
    def test_basic_validation_error(self):
        """测试基本验证错误"""
        error = ValidationError(message="输入无效")
        assert error.message == "输入无效"
        assert error.code == ErrorCode.INVALID_INPUT
        assert error.severity == ErrorSeverity.ERROR
        assert error.retryable is False
    
    def test_validation_error_with_field(self):
        """测试带字段信息的验证错误"""
        error = ValidationError(
            message="字段无效",
            field="username",
            value="test@user",
            constraint="只能包含字母和数字"
        )
        assert error.details["field"] == "username"
        assert error.details["value"] == "test@user"
        assert error.details["constraint"] == "只能包含字母和数字"
    
    def test_validation_error_with_suggestions(self):
        """测试带建议的验证错误"""
        suggestions = ["请输入有效的用户名", "用户名长度应为3-20个字符"]
        error = ValidationError(
            message="用户名无效",
            suggestions=suggestions
        )
        assert error.suggestions == suggestions


class TestInputError:
    """测试输入格式错误"""
    
    def test_basic_input_error(self):
        """测试基本输入错误"""
        error = InputError(message="格式错误")
        assert error.message == "格式错误"
        assert error.code == ErrorCode.INVALID_FORMAT
    
    def test_input_error_with_format_info(self):
        """测试带格式信息的输入错误"""
        error = InputError(
            message="日期格式错误",
            input_type="date",
            expected_format="YYYY-MM-DD"
        )
        assert error.details["input_type"] == "date"
        assert error.details["expected_format"] == "YYYY-MM-DD"


class TestAuthenticationError:
    """测试认证错误"""
    
    def test_basic_authentication_error(self):
        """测试基本认证错误"""
        error = AuthenticationError()
        assert error.message == "认证失败"
        assert error.code == ErrorCode.AUTHENTICATION_ERROR
        assert "请检查认证凭据是否正确" in error.suggestions
    
    def test_authentication_error_with_type(self):
        """测试带认证类型的错误"""
        error = AuthenticationError(
            message="API Key 认证失败",
            auth_type="api_key"
        )
        assert error.details["auth_type"] == "api_key"


class TestConfigError:
    """测试配置错误"""
    
    def test_basic_config_error(self):
        """测试基本配置错误"""
        error = ConfigError(message="配置缺失")
        assert error.message == "配置缺失"
        assert error.code == ErrorCode.CONFIG_ERROR
    
    def test_config_error_with_details(self):
        """测试带详细信息的配置错误"""
        error = ConfigError(
            message="API Key 未配置",
            config_key="openai_api_key",
            config_file="config/config.json"
        )
        assert error.details["config_key"] == "openai_api_key"
        assert error.details["config_file"] == "config/config.json"


class TestServiceError:
    """测试服务错误"""
    
    def test_basic_service_error(self):
        """测试基本服务错误"""
        error = ServiceError(message="服务异常")
        assert error.message == "服务异常"
        assert error.code == ErrorCode.SERVICE_ERROR
        assert error.retryable is True
    
    def test_service_error_with_context(self):
        """测试带上下文的服务错误"""
        error = ServiceError(
            message="内容生成失败",
            service_name="ContentGenerator",
            operation="generate_content"
        )
        assert error.details["service_name"] == "ContentGenerator"
        assert error.details["operation"] == "generate_content"


class TestResourceError:
    """测试资源错误"""
    
    def test_basic_resource_error(self):
        """测试基本资源错误"""
        error = ResourceError(message="资源不足")
        assert error.message == "资源不足"
        assert error.code == ErrorCode.RESOURCE_ERROR
        assert error.retryable is True
    
    def test_resource_error_with_details(self):
        """测试带详细信息的资源错误"""
        error = ResourceError(
            message="内存不足",
            resource_type="memory",
            required="2GB",
            available="512MB"
        )
        assert error.details["resource_type"] == "memory"
        assert error.details["required"] == "2GB"
        assert error.details["available"] == "512MB"


class TestAPIError:
    """测试 API 错误"""
    
    def test_basic_api_error(self):
        """测试基本 API 错误"""
        error = APIError()
        assert error.message == "API 调用失败"
        assert error.code == ErrorCode.API_ERROR
        assert error.retryable is True
    
    def test_api_error_with_details(self):
        """测试带详细信息的 API 错误"""
        error = APIError(
            message="OpenAI API 调用失败",
            api_name="openai",
            status_code=500,
            response_body='{"error": "Internal Server Error"}'
        )
        assert error.details["api_name"] == "openai"
        assert error.details["status_code"] == 500
        assert "Internal Server Error" in error.details["response_body"]


class TestAPITimeoutError:
    """测试 API 超时错误"""
    
    def test_basic_timeout_error(self):
        """测试基本超时错误"""
        error = APITimeoutError()
        assert error.message == "API 调用超时"
        assert error.code == ErrorCode.TIMEOUT
        assert error.severity == ErrorSeverity.WARNING
        assert error.retryable is True
    
    def test_timeout_error_with_details(self):
        """测试带详细信息的超时错误"""
        error = APITimeoutError(
            message="图片生成超时",
            api_name="image_api",
            timeout=180
        )
        assert error.details["api_name"] == "image_api"
        assert error.details["timeout"] == 180


class TestAPIRateLimitError:
    """测试 API 速率限制错误"""
    
    def test_basic_rate_limit_error(self):
        """测试基本速率限制错误"""
        error = APIRateLimitError()
        assert error.message == "超过 API 速率限制"
        assert error.code == ErrorCode.API_RATE_LIMIT
        assert error.retryable is True
    
    def test_rate_limit_error_with_retry_after(self):
        """测试带重试时间的速率限制错误"""
        error = APIRateLimitError(
            api_name="openai",
            retry_after=60
        )
        assert error.details["api_name"] == "openai"
        assert error.details["retry_after"] == 60
        assert "60 秒" in error.suggestions[0]


class TestAPIAuthenticationError:
    """测试 API 认证错误"""
    
    def test_basic_api_auth_error(self):
        """测试基本 API 认证错误"""
        error = APIAuthenticationError()
        assert error.message == "API 认证失败"
        assert error.code == ErrorCode.API_INVALID_KEY
        assert error.retryable is False
    
    def test_api_auth_error_with_suggestion(self):
        """测试带建议的 API 认证错误（向后兼容）"""
        error = APIAuthenticationError(
            api_name="openai",
            suggestion="请在环境变量中设置 OPENAI_API_KEY"
        )
        assert error.details["api_name"] == "openai"
        assert "请在环境变量中设置 OPENAI_API_KEY" in error.suggestions
    
    def test_api_auth_error_with_suggestions_list(self):
        """测试带建议列表的 API 认证错误"""
        suggestions = ["检查 API Key", "验证环境变量"]
        error = APIAuthenticationError(
            api_name="openai",
            suggestions=suggestions
        )
        assert error.suggestions == suggestions


class TestConnectionError:
    """测试连接错误"""
    
    def test_basic_connection_error(self):
        """测试基本连接错误"""
        error = ConnectionError()
        assert error.message == "网络连接失败"
        assert error.code == ErrorCode.CONNECTION_ERROR
        assert error.retryable is True
    
    def test_connection_error_with_details(self):
        """测试带详细信息的连接错误"""
        error = ConnectionError(
            message="无法连接到服务器",
            host="api.openai.com",
            port=443
        )
        assert error.details["host"] == "api.openai.com"
        assert error.details["port"] == 443


class TestContentGenerationError:
    """测试内容生成错误"""
    
    def test_basic_content_generation_error(self):
        """测试基本内容生成错误"""
        error = ContentGenerationError(message="生成失败")
        assert error.message == "生成失败"
        assert error.code == ErrorCode.SERVICE_ERROR
        assert error.retryable is True
    
    def test_content_generation_error_with_attempts(self):
        """测试带尝试次数的内容生成错误"""
        error = ContentGenerationError(
            message="内容生成失败",
            generation_type="image",
            attempt=3,
            max_attempts=3
        )
        assert error.details["generation_type"] == "image"
        assert error.details["attempt"] == 3
        assert error.details["max_attempts"] == 3


class TestFileNotFoundError:
    """测试文件未找到错误"""
    
    def test_basic_file_not_found_error(self):
        """测试基本文件未找到错误"""
        error = FileNotFoundError()
        assert error.message == "文件未找到"
        assert error.code == ErrorCode.FILE_ERROR
        assert error.retryable is False
    
    def test_file_not_found_error_with_path(self):
        """测试带路径的文件未找到错误"""
        error = FileNotFoundError(
            message="配置文件不存在",
            file_path="/path/to/config.json"
        )
        assert error.details["file_path"] == "/path/to/config.json"


class TestContentValidationError:
    """测试内容验证错误"""
    
    def test_basic_content_validation_error(self):
        """测试基本内容验证错误"""
        error = ContentValidationError(message="内容验证失败")
        assert error.message == "内容验证失败"
        assert error.code == ErrorCode.INVALID_INPUT
        assert error.retryable is False
    
    def test_content_validation_error_with_details(self):
        """测试带详细信息的内容验证错误"""
        error = ContentValidationError(
            message="文本长度超限",
            content_type="text",
            validation_rule="max_length:5000"
        )
        assert error.details["content_type"] == "text"
        assert error.details["validation_rule"] == "max_length:5000"


class TestContentSafetyError:
    """测试内容安全错误"""
    
    def test_basic_content_safety_error(self):
        """测试基本内容安全错误"""
        error = ContentSafetyError()
        assert error.message == "内容包含敏感信息"
        assert error.code == ErrorCode.FORBIDDEN_CONTENT
        assert error.retryable is False
    
    def test_content_safety_error_with_forbidden_words(self):
        """测试带敏感词的内容安全错误"""
        forbidden_words = ["敏感词1", "敏感词2"]
        error = ContentSafetyError(
            message="内容包含敏感词",
            forbidden_words=forbidden_words
        )
        assert error.details["forbidden_words"] == forbidden_words


class TestWrapException:
    """测试异常包装函数"""
    
    def test_wrap_basic_exception(self):
        """测试包装基本异常"""
        original = ValueError("原始错误")
        wrapped = wrap_exception(
            original,
            message="包装后的错误"
        )
        
        assert isinstance(wrapped, AppError)
        assert wrapped.message == "包装后的错误"
        assert wrapped.details["original_error"] == "原始错误"
        assert wrapped.details["original_type"] == "ValueError"
    
    def test_wrap_exception_with_custom_class(self):
        """测试包装为自定义错误类"""
        original = ConnectionError("连接失败")
        wrapped = wrap_exception(
            original,
            message="API 连接失败",
            exception_class=APIError,
            api_name="openai"
        )
        
        assert isinstance(wrapped, APIError)
        assert wrapped.message == "API 连接失败"
        assert "连接失败" in wrapped.details["original_error"]
    
    def test_wrap_exception_preserves_details(self):
        """测试包装异常保留详细信息"""
        original = RuntimeError("运行时错误")
        custom_details = {"key": "value"}
        wrapped = wrap_exception(
            original,
            message="包装错误",
            details=custom_details
        )
        
        assert wrapped.details["key"] == "value"
        assert "original_error" in wrapped.details
        assert "original_type" in wrapped.details


class TestErrorCodeMapping:
    """测试错误码映射"""
    
    def test_user_error_codes(self):
        """测试用户错误码范围（1xxx）"""
        user_errors = [
            ErrorCode.INVALID_INPUT,
            ErrorCode.INPUT_TOO_SHORT,
            ErrorCode.INPUT_TOO_LONG,
            ErrorCode.INVALID_FORMAT,
            ErrorCode.FORBIDDEN_CONTENT,
        ]
        for code in user_errors:
            assert isinstance(code, ErrorCode)
    
    def test_api_error_codes(self):
        """测试 API 错误码范围（2xxx）"""
        api_errors = [
            ErrorCode.API_ERROR,
            ErrorCode.API_RATE_LIMIT,
            ErrorCode.API_QUOTA_EXCEEDED,
            ErrorCode.API_INVALID_KEY,
        ]
        for code in api_errors:
            assert isinstance(code, ErrorCode)
    
    def test_network_error_codes(self):
        """测试网络错误码范围（3xxx）"""
        network_errors = [
            ErrorCode.TIMEOUT,
            ErrorCode.CONNECTION_ERROR,
            ErrorCode.NETWORK_ERROR,
        ]
        for code in network_errors:
            assert isinstance(code, ErrorCode)
    
    def test_config_error_codes(self):
        """测试配置错误码范围（4xxx）"""
        config_errors = [
            ErrorCode.CONFIG_ERROR,
            ErrorCode.CONFIG_MISSING,
            ErrorCode.CONFIG_INVALID,
        ]
        for code in config_errors:
            assert isinstance(code, ErrorCode)
    
    def test_system_error_codes(self):
        """测试系统错误码范围（5xxx）"""
        system_errors = [
            ErrorCode.SERVICE_ERROR,
            ErrorCode.RESOURCE_ERROR,
            ErrorCode.FILE_ERROR,
        ]
        for code in system_errors:
            assert isinstance(code, ErrorCode)


class TestErrorInheritance:
    """测试错误继承关系"""
    
    def test_all_errors_inherit_from_app_error(self):
        """测试所有错误都继承自 AppError"""
        error_classes = [
            ValidationError,
            InputError,
            AuthenticationError,
            ConfigError,
            ServiceError,
            ResourceError,
            APIError,
            APITimeoutError,
            APIRateLimitError,
            APIAuthenticationError,
            ConnectionError,
            ContentGenerationError,
            FileNotFoundError,
            ContentValidationError,
            ContentSafetyError,
        ]
        
        for error_class in error_classes:
            error = error_class(message="测试")
            assert isinstance(error, AppError)
            assert isinstance(error, Exception)
    
    def test_error_can_be_caught_as_app_error(self):
        """测试错误可以作为 AppError 捕获"""
        try:
            raise ValidationError(message="验证失败")
        except AppError as e:
            assert e.message == "验证失败"
            assert isinstance(e, ValidationError)
    
    def test_error_can_be_caught_as_exception(self):
        """测试错误可以作为 Exception 捕获"""
        try:
            raise APIError(message="API 失败")
        except Exception as e:
            assert isinstance(e, AppError)
            assert isinstance(e, APIError)


class TestErrorMessageFormat:
    """测试错误消息格式"""
    
    def test_all_errors_have_chinese_messages(self):
        """测试所有错误都有中文消息"""
        errors = [
            ValidationError(message="验证失败"),
            InputError(message="输入错误"),
            AuthenticationError(),
            ConfigError(message="配置错误"),
            ServiceError(message="服务错误"),
            APIError(),
            APITimeoutError(),
            APIRateLimitError(),
            ConnectionError(),
            ContentGenerationError(message="生成失败"),
        ]
        
        for error in errors:
            # 检查消息是否包含中文字符
            assert any('\u4e00' <= char <= '\u9fff' for char in error.message)
    
    def test_error_suggestions_are_chinese(self):
        """测试错误建议是中文"""
        error = ValidationError(
            message="输入无效",
            suggestions=["请检查输入格式", "参考示例：xxx"]
        )
        
        for suggestion in error.suggestions:
            assert any('\u4e00' <= char <= '\u9fff' for char in suggestion)
    
    def test_default_suggestions_are_provided(self):
        """测试默认建议被提供"""
        errors_with_defaults = [
            AuthenticationError(),
            ConfigError(message="配置错误"),
            ServiceError(message="服务错误"),
            APIError(),
            ConnectionError(),
        ]
        
        for error in errors_with_defaults:
            assert len(error.suggestions) > 0
            assert all(isinstance(s, str) for s in error.suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
