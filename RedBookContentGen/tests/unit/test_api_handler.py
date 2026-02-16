#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 处理器测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.core.api_handler import APIHandler


class TestAPIHandler:
    """API 处理器测试类"""

    def test_init_without_rate_limit(self):
        """测试不启用速率限制的初始化"""
        handler = APIHandler(rate_limit_enabled=False, logger_name="test")

        assert handler.rate_limit_enabled is False
        assert handler.rpm_limiter is None
        assert handler.tpm_limiter is None

    def test_init_with_rate_limit(self):
        """测试启用速率限制的初始化"""
        rpm_limiter = Mock()
        tpm_limiter = Mock()

        handler = APIHandler(
            rpm_limiter=rpm_limiter, tpm_limiter=tpm_limiter, rate_limit_enabled=True, logger_name="test"
        )

        assert handler.rate_limit_enabled is True
        assert handler.rpm_limiter is rpm_limiter
        assert handler.tpm_limiter is tpm_limiter

    def test_estimate_tokens(self):
        """测试 token 估算"""
        messages = [{"content": "这是一个测试消息"}, {"content": "另一个测试消息"}]

        estimated = APIHandler._estimate_tokens(messages)

        # 总字符数：8 + 7 = 15
        # 估算 token：15 / 2 = 7.5，但至少 100
        assert estimated == 100

    def test_estimate_tokens_long_message(self):
        """测试长消息的 token 估算"""
        messages = [{"content": "x" * 500}]

        estimated = APIHandler._estimate_tokens(messages)

        # 500 / 2 = 250
        assert estimated == 250

    @patch("src.core.api_handler.Logger")
    def test_acquire_rate_limit_tokens_disabled(self, mock_logger):
        """测试禁用速率限制时不获取令牌"""
        handler = APIHandler(rate_limit_enabled=False)

        messages = [{"content": "test"}]

        # 不应该抛出异常
        handler._acquire_rate_limit_tokens(messages)

    @patch("src.core.api_handler.Logger")
    def test_acquire_rate_limit_tokens_success(self, mock_logger):
        """测试成功获取速率限制令牌"""
        rpm_limiter = Mock()
        rpm_limiter.wait_for_token.return_value = True
        rpm_limiter.get_available_tokens.return_value = 50

        tpm_limiter = Mock()
        tpm_limiter.wait_for_token.return_value = True
        tpm_limiter.get_available_tokens.return_value = 5000

        handler = APIHandler(rpm_limiter=rpm_limiter, tpm_limiter=tpm_limiter, rate_limit_enabled=True)

        messages = [{"content": "test"}]

        handler._acquire_rate_limit_tokens(messages)

        # 验证调用
        rpm_limiter.wait_for_token.assert_called_once_with(tokens=1, timeout=60)
        tpm_limiter.wait_for_token.assert_called_once()

    @patch("src.core.api_handler.Logger")
    def test_acquire_rate_limit_tokens_timeout(self, mock_logger):
        """测试获取令牌超时"""
        from src.core.exceptions import APITimeoutError

        rpm_limiter = Mock()
        rpm_limiter.wait_for_token.return_value = False

        handler = APIHandler(rpm_limiter=rpm_limiter, rate_limit_enabled=True)

        messages = [{"content": "test"}]

        with pytest.raises(APITimeoutError):
            handler._acquire_rate_limit_tokens(messages)

    @patch("src.core.api_handler.Logger")
    def test_call_openai_success(self, mock_logger):
        """测试成功调用 OpenAI API"""
        # 创建模拟的 OpenAI 客户端
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response

        handler = APIHandler(rate_limit_enabled=False)

        messages = [{"role": "user", "content": "test"}]

        response = handler.call_openai(client=mock_client, model="gpt-4", messages=messages, temperature=0.8)

        assert response == mock_response
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.core.api_handler.Logger")
    def test_call_openai_with_response_format(self, mock_logger):
        """测试带响应格式的 API 调用"""
        mock_client = Mock()
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        handler = APIHandler(rate_limit_enabled=False)

        messages = [{"role": "user", "content": "test"}]
        response_format = {"type": "json_object"}

        response = handler.call_openai(
            client=mock_client, model="gpt-4", messages=messages, response_format=response_format
        )

        # 验证调用参数
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == response_format

    @patch("src.core.api_handler.Logger")
    def test_call_openai_with_evaluation(self, mock_logger):
        """测试带评估的 API 调用"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"result": "test"}'
        mock_client.chat.completions.create.return_value = mock_response

        handler = APIHandler(rate_limit_enabled=False)

        def prompt_builder(content):
            return f"Generate content for: {content}"

        def evaluator(result):
            # 第一次返回需要继续，第二次返回不需要
            if not hasattr(evaluator, "call_count"):
                evaluator.call_count = 0
            evaluator.call_count += 1

            if evaluator.call_count == 1:
                return True, "需要改进"
            else:
                return False, ""

        result = handler.call_openai_with_evaluation(
            client=mock_client,
            model="gpt-4",
            raw_content="test content",
            prompt_builder=prompt_builder,
            max_iterations=3,
            evaluator=evaluator,
        )

        assert result == {"result": "test"}
        # 应该调用了 2 次（第一次需要改进，第二次通过）
        assert mock_client.chat.completions.create.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
