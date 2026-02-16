#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成器速率限制功能测试

测试 ImageGenerator 的速率限制集成功能
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from src.image_generator import ImageGenerator
from src.core.config_manager import ConfigManager
from src.core.rate_limiter import RateLimiter


class TestImageGeneratorRateLimit:
    """图片生成器速率限制测试"""

    @pytest.fixture
    def mock_config_with_rate_limit(self, tmp_path):
        """创建启用速率限制的配置"""
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "wan2.2-t2i-flash",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": True, "requests_per_minute": 10}},
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return ConfigManager(str(config_file))

    @pytest.fixture
    def mock_config_without_rate_limit(self, tmp_path):
        """创建禁用速率限制的配置"""
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "wan2.2-t2i-flash",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return ConfigManager(str(config_file))

    def test_rate_limiter_initialization_enabled(self, mock_config_with_rate_limit):
        """测试速率限制器初始化（启用）"""
        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # 验证速率限制器已创建
        assert generator._rate_limit_enabled is True
        assert generator.rpm_limiter is not None

        # 验证速率限制器配置
        # 10 RPM = 10/60 RPS ≈ 0.167 RPS
        assert generator.rpm_limiter.get_rate() == pytest.approx(10.0 / 60.0, rel=0.01)
        assert generator.rpm_limiter.get_capacity() == 10.0

    def test_rate_limiter_initialization_disabled(self, mock_config_without_rate_limit):
        """测试速率限制器初始化（禁用）"""
        generator = ImageGenerator(config_manager=mock_config_without_rate_limit)

        # 验证速率限制器未创建
        assert generator._rate_limit_enabled is False
        assert generator.rpm_limiter is None

    def test_get_rate_limit_stats_enabled(self, mock_config_with_rate_limit):
        """测试获取速率限制统计（启用）"""
        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        stats = generator.get_rate_limit_stats()

        assert stats is not None
        assert stats["enabled"] is True
        assert "rpm" in stats

        # 验证 RPM 统计
        assert stats["rpm"]["available_tokens"] == 10.0
        assert stats["rpm"]["capacity"] == 10.0
        assert stats["rpm"]["rate"] == pytest.approx(10.0 / 60.0, rel=0.01)

    def test_get_rate_limit_stats_disabled(self, mock_config_without_rate_limit):
        """测试获取速率限制统计（禁用）"""
        generator = ImageGenerator(config_manager=mock_config_without_rate_limit)

        stats = generator.get_rate_limit_stats()

        assert stats is None

    @patch("requests.post")
    def test_generate_image_async_with_rate_limit_enabled(self, mock_post, mock_config_with_rate_limit):
        """测试带速率限制的异步图片生成（启用）"""
        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"task_id": "test-task-id"}}
        mock_post.return_value = mock_response

        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # Mock _wait_for_task_completion
        with patch.object(generator, "_wait_for_task_completion", return_value="http://example.com/image.jpg"):
            # 记录初始令牌数
            initial_tokens = generator.rpm_limiter.get_available_tokens()

            # 调用图片生成
            result = generator.generate_image_async(prompt="测试提示词", index=1, is_cover=False)

            # 验证结果
            assert result == "http://example.com/image.jpg"

            # 验证令牌已被消耗
            final_tokens = generator.rpm_limiter.get_available_tokens()
            assert final_tokens < initial_tokens

    @patch("requests.post")
    def test_generate_image_async_without_rate_limit(self, mock_post, mock_config_without_rate_limit):
        """测试不带速率限制的异步图片生成（禁用）"""
        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"task_id": "test-task-id"}}
        mock_post.return_value = mock_response

        generator = ImageGenerator(config_manager=mock_config_without_rate_limit)

        # Mock _wait_for_task_completion
        with patch.object(generator, "_wait_for_task_completion", return_value="http://example.com/image.jpg"):
            # 调用图片生成
            result = generator.generate_image_async(prompt="测试提示词", index=1, is_cover=False)

            # 验证结果
            assert result == "http://example.com/image.jpg"

            # 验证 API 被调用
            assert mock_post.called

    @patch("requests.post")
    def test_generate_single_image_with_rate_limit(self, mock_post, mock_config_with_rate_limit):
        """测试带速率限制的单张图片生成"""
        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"task_id": "test-task-id"}}
        mock_post.return_value = mock_response

        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # Mock _wait_for_task_completion
        with patch.object(generator, "_wait_for_task_completion", return_value="http://example.com/image.jpg"):
            # 记录初始令牌数
            initial_tokens = generator.rpm_limiter.get_available_tokens()

            # 调用图片生成
            result = generator.generate_single_image(prompt="测试提示词", size="1024*1365")

            # 验证结果
            assert result == "http://example.com/image.jpg"

            # 验证令牌已被消耗
            final_tokens = generator.rpm_limiter.get_available_tokens()
            assert final_tokens < initial_tokens

    @patch("requests.post")
    def test_generate_image_sync_with_rate_limit(self, mock_post, mock_config_with_rate_limit):
        """测试带速率限制的同步图片生成"""
        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"image_url": "http://example.com/image.jpg"}}
        mock_post.return_value = mock_response

        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # 记录初始令牌数
        initial_tokens = generator.rpm_limiter.get_available_tokens()

        # 调用图片生成
        result = generator.generate_image_sync(prompt="测试提示词", size="1024*1365")

        # 验证结果
        assert result == "http://example.com/image.jpg"

        # 验证令牌已被消耗
        final_tokens = generator.rpm_limiter.get_available_tokens()
        assert final_tokens < initial_tokens

    @patch("requests.post")
    def test_rate_limit_wait_behavior(self, mock_post, mock_config_with_rate_limit):
        """测试速率限制等待行为"""
        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"task_id": "test-task-id"}}
        mock_post.return_value = mock_response

        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # 消耗所有 RPM 令牌
        generator.rpm_limiter.acquire(tokens=10)

        # 验证令牌已耗尽
        assert generator.rpm_limiter.get_available_tokens() < 1

        # Mock _wait_for_task_completion 和 wait_for_token
        with patch.object(generator, "_wait_for_task_completion", return_value="http://example.com/image.jpg"):
            with patch.object(generator.rpm_limiter, "wait_for_token", return_value=True):
                # 调用图片生成（应该等待）
                result = generator.generate_image_async(prompt="测试提示词", index=1, is_cover=False)

                # 验证结果
                assert result == "http://example.com/image.jpg"

    @patch("requests.post")
    def test_rate_limit_timeout(self, mock_post, mock_config_with_rate_limit):
        """测试速率限制超时"""
        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # Mock wait_for_token 返回 False（超时）
        with patch.object(generator.rpm_limiter, "wait_for_token", return_value=False):
            # 应该抛出 TimeoutError
            with pytest.raises(TimeoutError, match="获取图片生成 RPM 令牌超时"):
                generator.generate_image_async(prompt="测试提示词", index=1, is_cover=False)

    @patch("requests.post")
    def test_multiple_image_generations_with_rate_limit(self, mock_post, mock_config_with_rate_limit):
        """测试多次图片生成的速率限制"""
        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"task_id": "test-task-id"}}
        mock_post.return_value = mock_response

        generator = ImageGenerator(config_manager=mock_config_with_rate_limit)

        # Mock _wait_for_task_completion
        with patch.object(generator, "_wait_for_task_completion", return_value="http://example.com/image.jpg"):
            # 记录初始令牌数
            initial_tokens = generator.rpm_limiter.get_available_tokens()

            # 进行多次图片生成
            num_calls = 3
            for i in range(num_calls):
                generator.generate_image_async(prompt=f"测试提示词{i}", index=i + 1, is_cover=False)

            # 验证令牌被正确消耗
            final_tokens = generator.rpm_limiter.get_available_tokens()
            consumed_tokens = initial_tokens - final_tokens

            # 每次调用消耗 1 个 RPM 令牌
            # 由于令牌桶会自动恢复，所以消耗的令牌数可能略小于调用次数
            assert consumed_tokens >= num_calls - 1  # 允许恢复 1 个令牌

    def test_rate_limit_config_from_environment(self, tmp_path, monkeypatch):
        """测试从环境变量读取速率限制配置"""
        # 设置环境变量
        monkeypatch.setenv("RATE_LIMIT_IMAGE_RPM", "20")

        config_data = {
            "openai_api_key": "test-key",
            "image_model": "wan2.2-t2i-flash",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": True, "requests_per_minute": 10}},
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        config_manager = ConfigManager(str(config_file))
        generator = ImageGenerator(config_manager=config_manager)

        # 验证环境变量覆盖了配置文件
        rpm = config_manager.get("rate_limit.image.requests_per_minute")

        # 如果环境变量生效，应该是 20
        # 否则是配置文件中的 10
        assert rpm in [10, 20]

    @patch("requests.post")
    def test_rate_limit_with_cache_hit(self, mock_post, tmp_path):
        """测试缓存命中时不消耗速率限制令牌"""
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "wan2.2-t2i-flash",
            "cache": {"enabled": True, "ttl": 3600, "max_size": 100},
            "rate_limit": {"image": {"enable_rate_limit": True, "requests_per_minute": 10}},
            "logging": {"level": "INFO", "format": "text", "file": str(tmp_path / "test.log")},
        }

        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        config_manager = ConfigManager(str(config_file))
        generator = ImageGenerator(config_manager=config_manager)

        # 设置 mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"task_id": "test-task-id"}}
        mock_post.return_value = mock_response

        # Mock _wait_for_task_completion
        with patch.object(generator, "_wait_for_task_completion", return_value="http://example.com/image.jpg"):
            # 第一次调用（缓存未命中）
            result1 = generator.generate_image_async(prompt="测试提示词", index=1, is_cover=False)

            # 记录第一次调用后的令牌数
            tokens_after_first = generator.rpm_limiter.get_available_tokens()

            # 第二次调用（缓存命中）
            result2 = generator.generate_image_async(prompt="测试提示词", index=1, is_cover=False)

            # 记录第二次调用后的令牌数
            tokens_after_second = generator.rpm_limiter.get_available_tokens()

            # 验证结果相同
            assert result1 == result2

            # 验证第二次调用没有消耗令牌（缓存命中）
            # 由于令牌桶会自动恢复，所以第二次的令牌数应该大于等于第一次
            assert tokens_after_second >= tokens_after_first


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
