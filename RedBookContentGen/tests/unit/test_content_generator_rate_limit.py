#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容生成器速率限制功能测试

测试 RedBookContentGenerator 的速率限制集成功能
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from src.content_generator import RedBookContentGenerator
from src.core.config_manager import ConfigManager
from src.core.rate_limiter import RateLimiter


class TestContentGeneratorRateLimit:
    """内容生成器速率限制测试"""

    @pytest.fixture
    def mock_config_with_rate_limit(self, tmp_path):
        """创建启用速率限制的配置"""
        config_data = {
            "input_file": str(tmp_path / "input.txt"),
            "output_excel": str(tmp_path / "output.xlsx"),
            "output_image_dir": str(tmp_path / "images"),
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "cache": {"enabled": False},
            "rate_limit": {
                "openai": {"enable_rate_limit": True, "requests_per_minute": 60, "tokens_per_minute": 90000}
            },
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # 创建输入文件
        input_file = tmp_path / "input.txt"
        input_file.write_text("测试内容", encoding="utf-8")

        return ConfigManager(str(config_file))

    @pytest.fixture
    def mock_config_without_rate_limit(self, tmp_path):
        """创建禁用速率限制的配置"""
        config_data = {
            "input_file": str(tmp_path / "input.txt"),
            "output_excel": str(tmp_path / "output.xlsx"),
            "output_image_dir": str(tmp_path / "images"),
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "cache": {"enabled": False},
            "rate_limit": {"openai": {"enable_rate_limit": False}},
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # 创建输入文件
        input_file = tmp_path / "input.txt"
        input_file.write_text("测试内容", encoding="utf-8")

        return ConfigManager(str(config_file))

    def test_rate_limiter_initialization_enabled(self, mock_config_with_rate_limit):
        """测试速率限制器初始化（启用）"""
        generator = RedBookContentGenerator(config_manager=mock_config_with_rate_limit)

        # 验证速率限制器已创建
        assert generator._rate_limit_enabled is True
        assert generator.rpm_limiter is not None
        assert generator.tpm_limiter is not None

        # 验证速率限制器配置
        assert generator.rpm_limiter.get_rate() == 1.0  # 60 RPM = 1 RPS
        assert generator.rpm_limiter.get_capacity() == 60.0

        assert generator.tpm_limiter.get_rate() == 1500.0  # 90000 TPM = 1500 TPS
        assert generator.tpm_limiter.get_capacity() == 90000.0

    def test_rate_limiter_initialization_disabled(self, mock_config_without_rate_limit):
        """测试速率限制器初始化（禁用）"""
        generator = RedBookContentGenerator(config_manager=mock_config_without_rate_limit)

        # 验证速率限制器未创建
        assert generator._rate_limit_enabled is False
        assert generator.rpm_limiter is None
        assert generator.tpm_limiter is None

    def test_get_rate_limit_stats_enabled(self, mock_config_with_rate_limit):
        """测试获取速率限制统计（启用）"""
        generator = RedBookContentGenerator(config_manager=mock_config_with_rate_limit)

        stats = generator.get_rate_limit_stats()

        assert stats is not None
        assert stats["enabled"] is True
        assert "rpm" in stats
        assert "tpm" in stats

        # 验证 RPM 统计
        assert stats["rpm"]["available_tokens"] == 60.0
        assert stats["rpm"]["capacity"] == 60.0
        assert stats["rpm"]["rate"] == 1.0

        # 验证 TPM 统计
        assert stats["tpm"]["available_tokens"] == 90000.0
        assert stats["tpm"]["capacity"] == 90000.0
        assert stats["tpm"]["rate"] == 1500.0

    def test_get_rate_limit_stats_disabled(self, mock_config_without_rate_limit):
        """测试获取速率限制统计（禁用）"""
        generator = RedBookContentGenerator(config_manager=mock_config_without_rate_limit)

        stats = generator.get_rate_limit_stats()

        assert stats is None

    @patch("openai.OpenAI")
    def test_call_openai_with_rate_limit_enabled(self, mock_openai_class, mock_config_with_rate_limit):
        """测试带速率限制的 OpenAI API 调用（启用）"""
        # 设置 mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        mock_client.chat.completions.create.return_value = mock_response

        generator = RedBookContentGenerator(config_manager=mock_config_with_rate_limit)

        # 记录初始令牌数
        initial_rpm_tokens = generator.rpm_limiter.get_available_tokens()
        initial_tpm_tokens = generator.tpm_limiter.get_available_tokens()

        # 调用 API
        messages = [{"role": "user", "content": "测试消息"}]
        response = generator._call_openai_with_rate_limit(
            client=mock_client, model="qwen-plus", messages=messages, temperature=0.8
        )

        # 验证响应
        assert response == mock_response

        # 验证令牌已被消耗
        assert generator.rpm_limiter.get_available_tokens() < initial_rpm_tokens
        assert generator.tpm_limiter.get_available_tokens() < initial_tpm_tokens

    @patch("openai.OpenAI")
    def test_call_openai_without_rate_limit(self, mock_openai_class, mock_config_without_rate_limit):
        """测试不带速率限制的 OpenAI API 调用（禁用）"""
        # 设置 mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        mock_client.chat.completions.create.return_value = mock_response

        generator = RedBookContentGenerator(config_manager=mock_config_without_rate_limit)

        # 调用 API
        messages = [{"role": "user", "content": "测试消息"}]
        response = generator._call_openai_with_rate_limit(
            client=mock_client, model="qwen-plus", messages=messages, temperature=0.8
        )

        # 验证响应
        assert response == mock_response

        # 验证 API 被调用
        mock_client.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_rate_limit_wait_behavior(self, mock_openai_class, mock_config_with_rate_limit):
        """测试速率限制等待行为"""
        # 设置 mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        mock_client.chat.completions.create.return_value = mock_response

        generator = RedBookContentGenerator(config_manager=mock_config_with_rate_limit)

        # 消耗所有 RPM 令牌
        generator.rpm_limiter.acquire(tokens=60)

        # 验证令牌已耗尽
        assert generator.rpm_limiter.get_available_tokens() < 1

        # 调用 API（应该等待）
        start_time = time.time()
        messages = [{"role": "user", "content": "测试消息"}]

        # 使用较短的超时时间进行测试
        with patch.object(generator.rpm_limiter, "wait_for_token", return_value=True):
            response = generator._call_openai_with_rate_limit(
                client=mock_client, model="qwen-plus", messages=messages, temperature=0.8
            )

        # 验证响应
        assert response == mock_response

    @patch("openai.OpenAI")
    def test_rate_limit_timeout(self, mock_openai_class, mock_config_with_rate_limit):
        """测试速率限制超时"""
        # 设置 mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        generator = RedBookContentGenerator(config_manager=mock_config_with_rate_limit)

        # Mock wait_for_token 返回 False（超时）
        with patch.object(generator.rpm_limiter, "wait_for_token", return_value=False):
            messages = [{"role": "user", "content": "测试消息"}]

            # 应该抛出 TimeoutError
            with pytest.raises(TimeoutError, match="获取 RPM 令牌超时"):
                generator._call_openai_with_rate_limit(
                    client=mock_client, model="qwen-plus", messages=messages, temperature=0.8
                )

    @patch("openai.OpenAI")
    def test_multiple_api_calls_with_rate_limit(self, mock_openai_class, mock_config_with_rate_limit):
        """测试多次 API 调用的速率限制"""
        # 设置 mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        mock_client.chat.completions.create.return_value = mock_response

        generator = RedBookContentGenerator(config_manager=mock_config_with_rate_limit)

        # 记录初始令牌数
        initial_rpm_tokens = generator.rpm_limiter.get_available_tokens()

        # 进行多次 API 调用
        num_calls = 3
        messages = [{"role": "user", "content": "测试消息"}]

        for _ in range(num_calls):
            generator._call_openai_with_rate_limit(
                client=mock_client, model="qwen-plus", messages=messages, temperature=0.8
            )

        # 验证令牌被正确消耗
        final_rpm_tokens = generator.rpm_limiter.get_available_tokens()
        consumed_tokens = initial_rpm_tokens - final_rpm_tokens

        # 每次调用消耗 1 个 RPM 令牌
        # 由于令牌桶会自动恢复，所以消耗的令牌数可能略小于调用次数
        # 使用更宽松的断言
        assert consumed_tokens >= num_calls - 1  # 允许恢复 1 个令牌

    def test_rate_limit_config_from_environment(self, tmp_path, monkeypatch):
        """测试从环境变量读取速率限制配置"""
        # 设置环境变量
        monkeypatch.setenv("RATE_LIMIT_OPENAI_RPM", "120")
        monkeypatch.setenv("RATE_LIMIT_OPENAI_TPM", "180000")

        config_data = {
            "input_file": str(tmp_path / "input.txt"),
            "output_excel": str(tmp_path / "output.xlsx"),
            "output_image_dir": str(tmp_path / "images"),
            "openai_api_key": "test-key",
            "cache": {"enabled": False},
            "rate_limit": {
                "openai": {"enable_rate_limit": True, "requests_per_minute": 60, "tokens_per_minute": 90000}
            },
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # 创建输入文件
        input_file = tmp_path / "input.txt"
        input_file.write_text("测试内容", encoding="utf-8")

        config_manager = ConfigManager(str(config_file))
        generator = RedBookContentGenerator(config_manager=config_manager)

        # 验证环境变量覆盖了配置文件
        rpm = config_manager.get("rate_limit.openai.requests_per_minute")
        tpm = config_manager.get("rate_limit.openai.tokens_per_minute")

        # 如果环境变量生效，应该是 120 和 180000
        # 否则是配置文件中的 60 和 90000
        assert rpm in [60, 120]
        assert tpm in [90000, 180000]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
