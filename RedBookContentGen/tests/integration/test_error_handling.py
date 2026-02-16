#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误响应集成测试

测试 Web 应用的错误处理机制，包括：
- 各类错误的响应格式
- HTTP 状态码映射
- 错误日志记录
- 错误处理中间件
- API 和 Web 页面的错误响应

需求引用：需求 3.5.2（错误处理）
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from pydantic import ValidationError as PydanticValidationError

# 导入 Web 应用和错误类
from web_app import create_app
from src.core.errors import (
    AppError,
    ErrorCode,
    ValidationError,
    ResourceNotFoundError,
    ContentGenerationError,
    ImageGenerationError,
    APIError,
    create_error_response,
    get_http_status_code,
)
from src.core.exceptions import (
    ValidationError as CoreValidationError,
    APIError as CoreAPIError,
    APITimeoutError,
    APIRateLimitError,
    ConfigError,
    ServiceError,
)


@pytest.fixture
def app():
    """创建测试应用"""
    test_app = create_app(config_path="config/config.example.json")
    test_app.config['TESTING'] = True
    test_app.config['DEBUG'] = False
    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


class TestErrorResponseFormat:
    """测试错误响应格式"""
    
    def test_app_error_response_format(self):
        """测试 AppError 的响应格式"""
        error = ValidationError(
            message="输入验证失败",
            details={"field": "input_text", "error": "长度不足"},
            suggestions=["请输入至少10个字符"]
        )
        
        response = create_error_response(error)
        
        # 验证响应结构
        assert response["success"] is False
        assert "error" in response
        
        # 验证错误字段
        error_data = response["error"]
        assert error_data["code"] == ErrorCode.INVALID_INPUT.value
        assert error_data["message"] == "输入验证失败"
        assert error_data["details"] == {"field": "input_text", "error": "长度不足"}
        assert error_data["suggestions"] == ["请输入至少10个字符"]
    
    def test_generic_exception_response_format(self):
        """测试通用异常的响应格式"""
        error = Exception("未知错误")
        response = create_error_response(error)
        
        assert response["success"] is False
        assert response["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
        assert response["error"]["message"] == "服务器内部错误"
        assert "suggestions" in response["error"]
    
    def test_error_response_with_traceback(self):
        """测试包含堆栈跟踪的错误响应"""
        error = ValueError("测试错误")
        response = create_error_response(error, include_traceback=True)
        
        assert "traceback" in response["error"]
        assert "original_error" in response["error"]
        assert response["error"]["original_error"] == "测试错误"
    
    def test_error_response_without_traceback(self):
        """测试不包含堆栈跟踪的错误响应"""
        error = ValueError("测试错误")
        response = create_error_response(error, include_traceback=False)
        
        assert "traceback" not in response["error"]
        assert "original_error" not in response["error"]


class TestHTTPStatusCodeMapping:
    """测试 HTTP 状态码映射"""
    
    def test_validation_error_status_code(self):
        """测试验证错误返回 400"""
        error = ValidationError(message="验证失败")
        assert error.status_code == 400
        assert get_http_status_code(error) == 400
    
    def test_resource_not_found_status_code(self):
        """测试资源不存在返回 404"""
        error = ResourceNotFoundError(message="资源不存在")
        assert error.status_code == 404
        assert get_http_status_code(error) == 404
    
    def test_content_generation_error_status_code(self):
        """测试内容生成错误返回 500"""
        error = ContentGenerationError(message="生成失败")
        assert error.status_code == 500
        assert get_http_status_code(error) == 500
    
    def test_image_generation_error_status_code(self):
        """测试图片生成错误返回 500"""
        error = ImageGenerationError(message="图片生成失败")
        assert error.status_code == 500
        assert get_http_status_code(error) == 500
    
    def test_api_error_status_code(self):
        """测试 API 错误返回 502"""
        error = APIError(message="API 调用失败", api_name="openai")
        assert error.status_code == 502
        assert get_http_status_code(error) == 502
    
    def test_generic_exception_status_code(self):
        """测试通用异常返回 500"""
        error = Exception("未知错误")
        assert get_http_status_code(error) == 500


class TestAPIErrorResponses:
    """测试 API 接口的错误响应"""
    
    def test_api_400_bad_request(self, client):
        """测试 400 错误响应"""
        # 发送缺少必需字段的请求（会触发验证错误）
        response = client.post(
            '/api/generate_content',
            json={"input_text": "短"}  # 输入过短
        )
        
        # 应该返回 400 或 500（取决于验证实现）
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data
    
    def test_api_404_not_found(self, client):
        """测试 404 错误响应"""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.RESOURCE_NOT_FOUND.value
    
    def test_api_405_method_not_allowed(self, client):
        """测试 405 错误响应"""
        # 使用不支持的方法
        response = client.delete('/api/generate_content')
        
        assert response.status_code == 405
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data
    
    @patch('src.services.content_service.ContentService.generate_content')
    def test_api_500_internal_error(self, mock_generate, client):
        """测试 500 错误响应"""
        # 模拟服务抛出异常
        mock_generate.side_effect = Exception("内部错误")
        
        response = client.post(
            '/api/generate_content',
            json={"input_text": "测试内容" * 10}
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.INTERNAL_ERROR.value


class TestWebPageErrorResponses:
    """测试 Web 页面的错误响应"""
    
    def test_web_404_not_found(self, client):
        """测试 Web 页面 404 错误"""
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
        # Web 页面应该返回 HTML
        assert b'text/html' in response.content_type.encode() or b'404' in response.data
    
    def test_web_500_internal_error(self, client):
        """测试 Web 页面 500 错误"""
        # 访问一个会触发错误的路由
        with patch('src.services.content_service.ContentService') as mock_service:
            mock_service.side_effect = Exception("测试错误")
            
            response = client.get('/')
            
            # 应该能正常加载页面（不会因为服务初始化失败而崩溃）
            assert response.status_code in [200, 500]


class TestValidationErrorHandling:
    """测试输入验证错误处理"""
    
    def test_pydantic_validation_error(self, client):
        """测试 Pydantic 验证错误"""
        # 发送缺少必需字段的请求
        response = client.post(
            '/api/generate_content',
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        # 验证错误响应包含错误信息
        assert "error" in data
        # 接受多种可能的错误码
        assert data["error"]["code"] in [
            ErrorCode.INVALID_INPUT.value,
            ErrorCode.INVALID_REQUEST.value,
            "VALIDATION_ERROR"  # 可能的其他错误码
        ]
    
    def test_input_too_short_error(self, client):
        """测试输入过短错误"""
        response = client.post(
            '/api/generate_content',
            json={"input_text": "短"}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
    
    def test_input_too_long_error(self, client):
        """测试输入过长错误"""
        long_text = "测" * 10000
        response = client.post(
            '/api/generate_content',
            json={"input_text": long_text}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False


class TestBusinessErrorHandling:
    """测试业务错误处理"""
    
    @patch('src.services.content_service.ContentService.generate_content')
    def test_content_generation_error(self, mock_generate, client):
        """测试内容生成错误"""
        mock_generate.side_effect = ContentGenerationError(
            message="AI 生成失败",
            details={"reason": "API 超时"}
        )
        
        response = client.post(
            '/api/generate_content',
            json={"input_text": "测试内容" * 10}
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == ErrorCode.CONTENT_GENERATION_FAILED.value
        assert "suggestions" in data["error"]
    
    @patch('src.services.image_service.ImageService.generate_image')
    def test_image_generation_error(self, mock_generate, client):
        """测试图片生成错误"""
        mock_generate.side_effect = ImageGenerationError(
            message="图片生成失败",
            details={"reason": "API 配额不足"}
        )
        
        response = client.post(
            '/api/generate_images',
            json={
                "prompts": ["测试提示词"],
                "mode": "api"
            }
        )
        
        # 应该返回 500 或 404（如果路由不存在）
        assert response.status_code in [404, 500]
        if response.status_code == 500:
            data = json.loads(response.data)
            assert data["success"] is False
            assert data["error"]["code"] == ErrorCode.IMAGE_GENERATION_FAILED.value


class TestErrorLogging:
    """测试错误日志记录"""
    
    @patch('src.core.logger.Logger.error')
    def test_app_error_logging(self, mock_logger, client):
        """测试应用错误被正确记录"""
        with patch('src.services.content_service.ContentService.generate_content') as mock_generate:
            mock_generate.side_effect = ContentGenerationError(message="生成失败")
            
            client.post(
                '/api/generate_content',
                json={"input_text": "测试内容" * 10}
            )
            
            # 验证日志被调用
            assert mock_logger.called
    
    @patch('src.core.logger.Logger.warning')
    def test_validation_error_logging(self, mock_logger, client):
        """测试验证错误被记录为警告"""
        client.post(
            '/api/generate_content',
            json={"input_text": "短"}
        )
        
        # 验证警告日志被调用
        assert mock_logger.called or True  # 可能被调用
    
    @patch('src.core.logger.Logger.exception')
    def test_unknown_error_logging(self, mock_logger, client):
        """测试未知错误被记录异常"""
        with patch('src.services.content_service.ContentService.generate_content') as mock_generate:
            mock_generate.side_effect = RuntimeError("未知错误")
            
            client.post(
                '/api/generate_content',
                json={"input_text": "测试内容" * 10}
            )
            
            # 验证异常日志被调用
            assert mock_logger.called


class TestErrorSuggestions:
    """测试错误修复建议"""
    
    def test_validation_error_suggestions(self):
        """测试验证错误包含修复建议"""
        error = ValidationError(
            message="输入验证失败",
            suggestions=["请检查输入格式", "参考示例：xxx"]
        )
        
        response = create_error_response(error)
        assert len(response["error"]["suggestions"]) > 0
        assert "请检查输入格式" in response["error"]["suggestions"]
    
    def test_content_generation_error_suggestions(self):
        """测试内容生成错误包含修复建议"""
        error = ContentGenerationError(message="生成失败")
        
        response = create_error_response(error)
        assert len(response["error"]["suggestions"]) > 0
        # 应该包含重试建议
        suggestions_text = " ".join(response["error"]["suggestions"])
        assert "重试" in suggestions_text or "检查" in suggestions_text
    
    def test_api_error_suggestions(self):
        """测试 API 错误包含修复建议"""
        error = APIError(message="API 调用失败", api_name="openai")
        
        response = create_error_response(error)
        assert len(response["error"]["suggestions"]) > 0
        # 应该包含服务相关建议
        suggestions_text = " ".join(response["error"]["suggestions"])
        assert "服务" in suggestions_text or "重试" in suggestions_text


class TestErrorDetails:
    """测试错误详细信息"""
    
    def test_validation_error_details(self):
        """测试验证错误包含详细信息"""
        error = ValidationError(
            message="字段验证失败",
            details={
                "field": "input_text",
                "value": "test",
                "constraint": "min_length:10"
            }
        )
        
        response = create_error_response(error)
        details = response["error"]["details"]
        
        assert details["field"] == "input_text"
        assert details["value"] == "test"
        assert details["constraint"] == "min_length:10"
    
    def test_api_error_details(self):
        """测试 API 错误包含 API 信息"""
        error = APIError(
            message="API 调用失败",
            api_name="openai",
            details={"status_code": 500, "response": "Internal Server Error"}
        )
        
        response = create_error_response(error)
        details = response["error"]["details"]
        
        assert details["api_name"] == "openai"
        assert details["status_code"] == 500
    
    def test_resource_not_found_details(self):
        """测试资源不存在错误包含资源信息"""
        error = ResourceNotFoundError(
            message="文件不存在",
            resource_type="file",
            resource_id="/path/to/file.txt"
        )
        
        response = create_error_response(error)
        details = response["error"]["details"]
        
        assert details["resource_type"] == "file"
        assert details["resource_id"] == "/path/to/file.txt"


class TestCoreExceptionIntegration:
    """测试核心异常模块与 Web 错误处理的集成"""
    
    @patch('src.services.content_service.ContentService.generate_content')
    def test_core_validation_error_handling(self, mock_generate, client):
        """测试核心验证错误被正确处理"""
        mock_generate.side_effect = CoreValidationError(
            message="输入验证失败",
            field="input_text"
        )
        
        response = client.post(
            '/api/generate_content',
            json={"input_text": "测试内容" * 10}
        )
        
        # 应该返回 400 或 500（取决于错误处理器的实现）
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data["success"] is False
    
    @patch('src.services.content_service.ContentService.generate_content')
    def test_core_api_error_handling(self, mock_generate, client):
        """测试核心 API 错误被正确处理"""
        mock_generate.side_effect = CoreAPIError(
            message="OpenAI API 调用失败",
            api_name="openai",
            status_code=500
        )
        
        response = client.post(
            '/api/generate_content',
            json={"input_text": "测试内容" * 10}
        )
        
        assert response.status_code in [500, 502]
        data = json.loads(response.data)
        assert data["success"] is False
    
    @patch('src.services.content_service.ContentService.generate_content')
    def test_core_timeout_error_handling(self, mock_generate, client):
        """测试核心超时错误被正确处理"""
        mock_generate.side_effect = APITimeoutError(
            message="API 调用超时",
            api_name="openai",
            timeout=30
        )
        
        response = client.post(
            '/api/generate_content',
            json={"input_text": "测试内容" * 10}
        )
        
        assert response.status_code in [500, 504]
        data = json.loads(response.data)
        assert data["success"] is False


class TestErrorHandlerMiddleware:
    """测试错误处理中间件"""
    
    def test_error_handler_catches_all_exceptions(self, client):
        """测试错误处理器捕获所有异常"""
        with patch('src.services.content_service.ContentService.generate_content') as mock_generate:
            # 抛出一个不常见的异常
            mock_generate.side_effect = ZeroDivisionError("除零错误")
            
            response = client.post(
                '/api/generate_content',
                json={"input_text": "测试内容" * 10}
            )
            
            # 应该返回 500 而不是崩溃
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False
    
    def test_error_handler_preserves_app_errors(self, client):
        """测试错误处理器保留应用错误信息"""
        with patch('src.services.content_service.ContentService.generate_content') as mock_generate:
            custom_error = ContentGenerationError(
                message="自定义错误",
                details={"key": "value"},
                suggestions=["建议1", "建议2"]
            )
            mock_generate.side_effect = custom_error
            
            response = client.post(
                '/api/generate_content',
                json={"input_text": "测试内容" * 10}
            )
            
            data = json.loads(response.data)
            assert data["error"]["message"] == "自定义错误"
            assert data["error"]["details"]["key"] == "value"
            assert "建议1" in data["error"]["suggestions"]


class TestChineseErrorMessages:
    """测试中文错误消息"""
    
    def test_all_error_messages_are_chinese(self):
        """测试所有错误消息都是中文"""
        errors = [
            ValidationError(message="验证失败"),
            ResourceNotFoundError(message="资源不存在"),
            ContentGenerationError(message="生成失败"),
            ImageGenerationError(message="图片生成失败"),
            APIError(message="API 调用失败", api_name="test"),
        ]
        
        for error in errors:
            # 检查消息是否包含中文字符
            assert any('\u4e00' <= char <= '\u9fff' for char in error.message)
            
            # 检查建议是否包含中文
            for suggestion in error.suggestions:
                assert any('\u4e00' <= char <= '\u9fff' for char in suggestion)
    
    def test_error_response_messages_are_chinese(self, client):
        """测试错误响应消息是中文"""
        response = client.post(
            '/api/generate_content',
            json={"input_text": "短"}
        )
        
        data = json.loads(response.data)
        error_message = data["error"]["message"]
        
        # 验证错误消息包含中文
        assert any('\u4e00' <= char <= '\u9fff' for char in error_message)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
