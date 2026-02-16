#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内容生成错误处理

任务 9.1.2: 测试错误处理
- 测试 API 错误
- 测试网络错误
- 测试超时错误

目标：测试覆盖率 > 70%
"""

import pytest
import json
import openai
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.content_generator import RedBookContentGenerator
from src.core.config_manager import ConfigManager
from src.core.exceptions import (
    APIError,
    APITimeoutError,
    APIRateLimitError,
    APIAuthenticationError,
    ContentGenerationError,
)


# ============================================================================
# 测试固件
# ============================================================================


@pytest.fixture
def test_config(temp_dir):
    """创建测试配置"""
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "openai_model": "qwen-plus",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "cache": {"enabled": False},
        "rate_limit": {"openai": {"enable_rate_limit": False}},
    }

    config_file = temp_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    return config_file


@pytest.fixture
def generator(test_config):
    """创建内容生成器实例"""
    config_manager = ConfigManager(str(test_config))
    return RedBookContentGenerator(config_manager=config_manager)


@pytest.fixture
def valid_api_response():
    """有效的 API 响应"""
    return {
        "titles": ["测试标题1", "测试标题2", "测试标题3", "测试标题4", "测试标题5"],
        "content": "这是测试内容",
        "tags": "#测试 #标签",
        "image_prompts": [
            {"scene": "场景1", "prompt": "提示词1"},
            {"scene": "场景2", "prompt": "提示词2"},
            {"scene": "场景3", "prompt": "提示词3"},
            {"scene": "场景4", "prompt": "提示词4"},
        ],
        "cover": {"scene": "封面场景", "title": "封面标题", "prompt": "封面提示词"},
    }


# ============================================================================
# 测试 1: API 认证错误
# ============================================================================


@pytest.mark.unit
def test_api_authentication_error(generator):
    """测试 API 认证错误处理"""
    input_text = "老北京的胡同文化"

    # 模拟认证错误 - 直接 mock api_handler 的方法
    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        mock_call.side_effect = APIAuthenticationError(
            api_name="OpenAI", suggestion="请检查 API Key 是否正确配置"
        )

        # 应该抛出 APIAuthenticationError
        with pytest.raises(APIAuthenticationError) as exc_info:
            generator.generate_content(input_text)

        # 验证错误信息
        assert "认证失败" in str(exc_info.value)
        assert exc_info.value.code == "API_AUTHENTICATION_ERROR"
        assert "OpenAI" in exc_info.value.details.get("api_name", "")


@pytest.mark.unit
def test_api_authentication_error_details(generator):
    """测试 API 认证错误包含详细信息"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        mock_call.side_effect = APIAuthenticationError(
            api_name="OpenAI", 
            suggestion="请检查 API Key 是否正确配置",
            details={"error": "Invalid API key"}
        )

        with pytest.raises(APIAuthenticationError) as exc_info:
            generator.generate_content(input_text)

        # 验证错误详情
        error = exc_info.value
        assert error.details is not None
        assert "api_name" in error.details
        assert error.details["api_name"] == "OpenAI"


# ============================================================================
# 测试 2: API 超时错误
# ============================================================================


@pytest.mark.unit
def test_api_timeout_error(generator):
    """测试 API 超时错误处理"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        # 模拟超时错误
        mock_call.side_effect = APITimeoutError(api_name="OpenAI", timeout=60)

        # 应该抛出 APITimeoutError
        with pytest.raises(APITimeoutError) as exc_info:
            generator.generate_content(input_text)

        # 验证错误信息
        assert "超时" in str(exc_info.value)
        assert exc_info.value.code == "API_TIMEOUT_ERROR"


@pytest.mark.unit
def test_api_timeout_error_with_details(generator):
    """测试 API 超时错误包含超时时间"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        mock_call.side_effect = APITimeoutError(
            api_name="OpenAI", 
            timeout=60,
            details={"limiter_type": "RPM"}
        )

        with pytest.raises(APITimeoutError) as exc_info:
            generator.generate_content(input_text)

        # 验证超时时间在错误详情中
        assert exc_info.value.details.get("timeout") == 60


# ============================================================================
# 测试 3: API 速率限制错误
# ============================================================================


@pytest.mark.unit
def test_api_rate_limit_error(generator):
    """测试 API 速率限制错误处理"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        # 模拟速率限制错误
        mock_call.side_effect = APIRateLimitError(api_name="OpenAI")

        # 应该抛出 APIRateLimitError
        with pytest.raises(APIRateLimitError) as exc_info:
            generator.generate_content(input_text)

        # 验证错误信息
        assert "速率限制" in str(exc_info.value)
        assert exc_info.value.code == "API_RATE_LIMIT_ERROR"


@pytest.mark.unit
def test_api_rate_limit_error_with_retry_after(generator):
    """测试速率限制错误包含重试等待时间"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        mock_call.side_effect = APIRateLimitError(
            api_name="OpenAI",
            retry_after=30
        )

        with pytest.raises(APIRateLimitError) as exc_info:
            generator.generate_content(input_text)

        # 验证重试等待时间
        assert exc_info.value.details.get("retry_after") == 30


# ============================================================================
# 测试 4: 一般 API 错误
# ============================================================================


@pytest.mark.unit
def test_general_api_error(generator):
    """测试一般 API 错误处理"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        # 模拟一般 API 错误
        mock_call.side_effect = APIError(
            message="Internal server error",
            api_name="OpenAI"
        )

        # 应该抛出 APIError
        with pytest.raises(APIError) as exc_info:
            generator.generate_content(input_text)

        # 验证错误信息
        assert exc_info.value.code == "API_ERROR"


@pytest.mark.unit
def test_api_error_with_status_code(generator):
    """测试带状态码的 API 错误"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        # 模拟 500 错误
        mock_call.side_effect = APIError(
            message="Internal server error",
            api_name="OpenAI",
            status_code=500
        )

        with pytest.raises(APIError) as exc_info:
            generator.generate_content(input_text)

        # 验证状态码
        assert exc_info.value.details.get("status_code") == 500


# ============================================================================
# 测试 5: 内容生成错误
# ============================================================================


@pytest.mark.unit
def test_content_generation_error(generator):
    """测试内容生成错误"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        # 模拟内容生成失败
        mock_call.side_effect = ContentGenerationError(
            message="内容生成失败，已达到最大尝试次数",
            generation_type="content",
            attempt=3,
            max_attempts=3
        )

        with pytest.raises(ContentGenerationError) as exc_info:
            generator.generate_content(input_text)

        # 验证错误信息
        assert "内容生成失败" in str(exc_info.value)
        assert exc_info.value.code == "CONTENT_GENERATION_ERROR"


# ============================================================================
# 测试 6: 成功生成（验证正常流程）
# ============================================================================


@pytest.mark.unit
def test_successful_generation(generator, valid_api_response):
    """测试成功生成内容"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        # 模拟成功响应
        mock_call.return_value = valid_api_response

        result = generator.generate_content(input_text)

        # 验证结果
        assert isinstance(result, dict)
        assert "titles" in result
        assert "content" in result
        assert "image_prompts" in result


# ============================================================================
# 测试 7: 错误信息格式
# ============================================================================


@pytest.mark.unit
def test_error_to_dict_format(generator):
    """测试错误转换为字典格式"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        mock_call.side_effect = APITimeoutError(api_name="OpenAI", timeout=60)

        with pytest.raises(APITimeoutError) as exc_info:
            generator.generate_content(input_text)

        # 验证可以转换为字典
        error_dict = exc_info.value.to_dict()
        assert "error" in error_dict
        assert "code" in error_dict["error"]
        assert "message" in error_dict["error"]
        assert "details" in error_dict["error"]
        assert "type" in error_dict["error"]


@pytest.mark.unit
def test_error_string_representation(generator):
    """测试错误的字符串表示"""
    input_text = "老北京的胡同文化"

    with patch.object(generator.api_handler, "call_openai_with_evaluation") as mock_call:
        mock_call.side_effect = APIError(
            message="Test error",
            api_name="OpenAI",
            details={"test_key": "test_value"}
        )

        with pytest.raises(APIError) as exc_info:
            generator.generate_content(input_text)

        # 验证字符串表示包含必要信息
        error_str = str(exc_info.value)
        assert "Test error" in error_str
        assert "API_ERROR" in error_str


# ============================================================================
# 测试 8: API Handler 的错误处理
# ============================================================================


@pytest.mark.unit
def test_api_handler_authentication_error():
    """测试 APIHandler 的认证错误处理"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
            "Invalid API key", response=Mock(), body=None
        )
        mock_openai_class.return_value = mock_client

        with pytest.raises(APIAuthenticationError) as exc_info:
            handler.call_openai(
                client=mock_client,
                model="qwen-plus",
                messages=[{"role": "user", "content": "test"}]
            )

        assert "认证失败" in str(exc_info.value)


@pytest.mark.unit
def test_api_handler_timeout_error():
    """测试 APIHandler 的超时错误处理"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(request=Mock())
        mock_openai_class.return_value = mock_client

        with pytest.raises(APITimeoutError) as exc_info:
            handler.call_openai(
                client=mock_client,
                model="qwen-plus",
                messages=[{"role": "user", "content": "test"}]
            )

        assert "超时" in str(exc_info.value)


@pytest.mark.unit
def test_api_handler_rate_limit_error():
    """测试 APIHandler 的速率限制错误处理"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = openai.RateLimitError(
            "Rate limit exceeded", response=Mock(), body=None
        )
        mock_openai_class.return_value = mock_client

        with pytest.raises(APIRateLimitError) as exc_info:
            handler.call_openai(
                client=mock_client,
                model="qwen-plus",
                messages=[{"role": "user", "content": "test"}]
            )

        assert "速率限制" in str(exc_info.value)


@pytest.mark.unit
def test_api_handler_general_api_error():
    """测试 APIHandler 的一般 API 错误处理"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = openai.APIError(
            "Internal server error", request=Mock(), body=None
        )
        mock_openai_class.return_value = mock_client

        with pytest.raises(APIError) as exc_info:
            handler.call_openai(
                client=mock_client,
                model="qwen-plus",
                messages=[{"role": "user", "content": "test"}]
            )

        assert exc_info.value.code == "API_ERROR"


# ============================================================================
# 测试 9: 重试机制（通过 retry_handler 测试）
# ============================================================================


@pytest.mark.unit
def test_retry_mechanism_success_after_failure():
    """测试重试机制 - 失败后成功"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # 第一次失败
            raise openai.APIError("Temporary error", request=Mock(), body=None)
        # 第二次成功
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="success"))]
        return mock_response

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = side_effect

    # 应该成功（经过重试）
    result = handler.call_openai(
        client=mock_client,
        model="qwen-plus",
        messages=[{"role": "user", "content": "test"}]
    )

    # 验证重试了
    assert call_count == 2
    assert result.choices[0].message.content == "success"


@pytest.mark.unit
def test_retry_mechanism_max_retries_exceeded():
    """测试重试机制 - 超过最大重试次数"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)

    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = openai.APIError(
        "Persistent error", request=Mock(), body=None
    )

    # 应该在重试后抛出异常
    with pytest.raises(APIError):
        handler.call_openai(
            client=mock_client,
            model="qwen-plus",
            messages=[{"role": "user", "content": "test"}]
        )

    # 验证重试了多次（默认3次）
    assert mock_client.chat.completions.create.call_count >= 3


# ============================================================================
# 测试 10: 网络错误（不在重试列表中）
# ============================================================================


@pytest.mark.unit
def test_network_connection_error():
    """测试网络连接错误处理"""
    from src.core.api_handler import APIHandler

    handler = APIHandler(rate_limit_enabled=False)

    mock_client = Mock()
    # APIConnectionError 不在重试列表中，会直接抛出
    mock_client.chat.completions.create.side_effect = openai.APIConnectionError(request=Mock())

    # 应该抛出异常（不会重试）
    with pytest.raises(Exception):  # APIConnectionError 会被包装或直接抛出
        handler.call_openai(
            client=mock_client,
            model="qwen-plus",
            messages=[{"role": "user", "content": "test"}]
        )


# ============================================================================
# 测试 11: 异常包装
# ============================================================================


@pytest.mark.unit
def test_exception_wrapping():
    """测试异常包装功能"""
    from src.core.exceptions import wrap_exception

    original_error = ValueError("Original error message")

    wrapped_error = wrap_exception(
        original_error,
        message="Wrapped error message",
        exception_class=APIError,
        api_name="TestAPI"
    )

    # 验证包装后的异常
    assert isinstance(wrapped_error, APIError)
    assert "Wrapped error message" in str(wrapped_error)
    assert wrapped_error.details["api_name"] == "TestAPI"
    assert "original_error" in wrapped_error.details
    assert wrapped_error.details["original_error"]["type"] == "ValueError"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.content_generator", "--cov=src.core.api_handler", "--cov-report=term-missing"])
