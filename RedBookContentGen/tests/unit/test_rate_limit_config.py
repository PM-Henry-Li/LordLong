#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制配置模式测试

测试速率限制配置的验证规则和边界条件
"""

import pytest
from pydantic import ValidationError
from src.core.config_schema import OpenAIRateLimitConfig, ImageRateLimitConfig, RateLimitConfig


class TestOpenAIRateLimitConfig:
    """测试 OpenAI API 速率限制配置"""

    def test_default_values(self):
        """测试默认值"""
        config = OpenAIRateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.tokens_per_minute == 90000
        assert config.enable_rate_limit is True

    def test_valid_config(self):
        """测试有效配置"""
        config = OpenAIRateLimitConfig(requests_per_minute=100, tokens_per_minute=150000, enable_rate_limit=True)
        assert config.requests_per_minute == 100
        assert config.tokens_per_minute == 150000
        assert config.enable_rate_limit is True

    def test_invalid_requests_per_minute_zero(self):
        """测试无效的每分钟请求数（零）"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(requests_per_minute=0)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_requests_per_minute_negative(self):
        """测试无效的每分钟请求数（负数）"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(requests_per_minute=-10)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_requests_per_minute_too_large(self):
        """测试无效的每分钟请求数（超过上限）"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(requests_per_minute=20000)

        errors = exc_info.value.errors()
        assert any("less than or equal to 10000" in str(error["msg"]).lower() for error in errors)

    def test_invalid_tokens_per_minute_zero(self):
        """测试无效的每分钟令牌数（零）"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(tokens_per_minute=0)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_tokens_per_minute_negative(self):
        """测试无效的每分钟令牌数（负数）"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(tokens_per_minute=-1000)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_ratio_too_low(self):
        """测试令牌数与请求数比例过低"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(requests_per_minute=1000, tokens_per_minute=50000)  # 平均每请求 50 令牌，低于 100

        errors = exc_info.value.errors()
        assert any("比例过低" in str(error["msg"]) for error in errors)

    def test_invalid_ratio_too_high(self):
        """测试令牌数与请求数比例过高"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIRateLimitConfig(
                requests_per_minute=10, tokens_per_minute=2000000  # 平均每请求 200000 令牌，高于 100000
            )

        errors = exc_info.value.errors()
        assert any("比例过高" in str(error["msg"]) for error in errors)

    def test_valid_ratio_boundary_low(self):
        """测试令牌数与请求数比例边界（低）"""
        config = OpenAIRateLimitConfig(
            requests_per_minute=1000, tokens_per_minute=100000  # 平均每请求 100 令牌，刚好达到下限
        )
        assert config.requests_per_minute == 1000
        assert config.tokens_per_minute == 100000

    def test_valid_ratio_boundary_high(self):
        """测试令牌数与请求数比例边界（高）"""
        config = OpenAIRateLimitConfig(
            requests_per_minute=10, tokens_per_minute=1000000  # 平均每请求 100000 令牌，刚好达到上限
        )
        assert config.requests_per_minute == 10
        assert config.tokens_per_minute == 1000000

    def test_disable_rate_limit(self):
        """测试禁用速率限制"""
        config = OpenAIRateLimitConfig(enable_rate_limit=False)
        assert config.enable_rate_limit is False
        # 即使禁用，其他配置仍应有效
        assert config.requests_per_minute == 60
        assert config.tokens_per_minute == 90000


class TestImageRateLimitConfig:
    """测试图片生成 API 速率限制配置"""

    def test_default_values(self):
        """测试默认值"""
        config = ImageRateLimitConfig()
        assert config.requests_per_minute == 10
        assert config.enable_rate_limit is True
        assert config.max_concurrent == 3

    def test_valid_config(self):
        """测试有效配置"""
        config = ImageRateLimitConfig(requests_per_minute=20, enable_rate_limit=True, max_concurrent=5)
        assert config.requests_per_minute == 20
        assert config.enable_rate_limit is True
        assert config.max_concurrent == 5

    def test_invalid_requests_per_minute_zero(self):
        """测试无效的每分钟请求数（零）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(requests_per_minute=0)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_requests_per_minute_negative(self):
        """测试无效的每分钟请求数（负数）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(requests_per_minute=-5)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_requests_per_minute_too_large(self):
        """测试无效的每分钟请求数（超过上限）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(requests_per_minute=2000)

        errors = exc_info.value.errors()
        assert any("less than or equal to 1000" in str(error["msg"]).lower() for error in errors)

    def test_invalid_max_concurrent_zero(self):
        """测试无效的最大并发数（零）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(max_concurrent=0)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_max_concurrent_negative(self):
        """测试无效的最大并发数（负数）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(max_concurrent=-3)

        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error["msg"]).lower() for error in errors)

    def test_invalid_max_concurrent_too_large(self):
        """测试无效的最大并发数（超过上限）"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(max_concurrent=30)

        errors = exc_info.value.errors()
        assert any("less than or equal to 20" in str(error["msg"]).lower() for error in errors)

    def test_invalid_concurrent_exceeds_rate_limit(self):
        """测试并发数超过每分钟请求数"""
        with pytest.raises(ValidationError) as exc_info:
            ImageRateLimitConfig(requests_per_minute=5, max_concurrent=10)  # 并发数大于每分钟请求数

        errors = exc_info.value.errors()
        assert any("不应超过每分钟请求数" in str(error["msg"]) for error in errors)

    def test_valid_concurrent_equals_rate_limit(self):
        """测试并发数等于每分钟请求数（边界情况）"""
        config = ImageRateLimitConfig(requests_per_minute=10, max_concurrent=10)
        assert config.requests_per_minute == 10
        assert config.max_concurrent == 10

    def test_disable_rate_limit(self):
        """测试禁用速率限制"""
        config = ImageRateLimitConfig(enable_rate_limit=False)
        assert config.enable_rate_limit is False
        # 即使禁用，其他配置仍应有效
        assert config.requests_per_minute == 10
        assert config.max_concurrent == 3


class TestRateLimitConfig:
    """测试速率限制配置总模式"""

    def test_default_values(self):
        """测试默认值"""
        config = RateLimitConfig()

        # 验证 OpenAI 配置
        assert config.openai.requests_per_minute == 60
        assert config.openai.tokens_per_minute == 90000
        assert config.openai.enable_rate_limit is True

        # 验证图片配置
        assert config.image.requests_per_minute == 10
        assert config.image.enable_rate_limit is True
        assert config.image.max_concurrent == 3

    def test_custom_config(self):
        """测试自定义配置"""
        config = RateLimitConfig(
            openai={"requests_per_minute": 100, "tokens_per_minute": 200000, "enable_rate_limit": False},
            image={"requests_per_minute": 20, "enable_rate_limit": False, "max_concurrent": 5},
        )

        # 验证 OpenAI 配置
        assert config.openai.requests_per_minute == 100
        assert config.openai.tokens_per_minute == 200000
        assert config.openai.enable_rate_limit is False

        # 验证图片配置
        assert config.image.requests_per_minute == 20
        assert config.image.enable_rate_limit is False
        assert config.image.max_concurrent == 5

    def test_partial_config(self):
        """测试部分配置（使用默认值）"""
        config = RateLimitConfig(openai={"requests_per_minute": 80})

        # 自定义的值
        assert config.openai.requests_per_minute == 80

        # 默认值
        assert config.openai.tokens_per_minute == 90000
        assert config.openai.enable_rate_limit is True
        assert config.image.requests_per_minute == 10

    def test_invalid_nested_config(self):
        """测试嵌套配置验证"""
        with pytest.raises(ValidationError) as exc_info:
            RateLimitConfig(openai={"requests_per_minute": 1000, "tokens_per_minute": 50000})  # 比例过低

        errors = exc_info.value.errors()
        assert any("比例过低" in str(error["msg"]) for error in errors)

    def test_json_serialization(self):
        """测试 JSON 序列化"""
        config = RateLimitConfig()
        json_data = config.model_dump()

        assert "openai" in json_data
        assert "image" in json_data
        assert json_data["openai"]["requests_per_minute"] == 60
        assert json_data["image"]["requests_per_minute"] == 10

    def test_json_deserialization(self):
        """测试 JSON 反序列化"""
        json_data = {
            "openai": {"requests_per_minute": 50, "tokens_per_minute": 100000, "enable_rate_limit": True},
            "image": {"requests_per_minute": 15, "enable_rate_limit": True, "max_concurrent": 4},
        }

        config = RateLimitConfig(**json_data)
        assert config.openai.requests_per_minute == 50
        assert config.image.requests_per_minute == 15


class TestRateLimitConfigEdgeCases:
    """测试速率限制配置的边界情况"""

    def test_minimum_valid_openai_config(self):
        """测试 OpenAI 配置的最小有效值"""
        config = OpenAIRateLimitConfig(requests_per_minute=1, tokens_per_minute=100)  # 平均每请求 100 令牌
        assert config.requests_per_minute == 1
        assert config.tokens_per_minute == 100

    def test_maximum_valid_openai_config(self):
        """测试 OpenAI 配置的最大有效值"""
        config = OpenAIRateLimitConfig(requests_per_minute=10000, tokens_per_minute=10000000)
        assert config.requests_per_minute == 10000
        assert config.tokens_per_minute == 10000000

    def test_minimum_valid_image_config(self):
        """测试图片配置的最小有效值"""
        config = ImageRateLimitConfig(requests_per_minute=1, max_concurrent=1)
        assert config.requests_per_minute == 1
        assert config.max_concurrent == 1

    def test_maximum_valid_image_config(self):
        """测试图片配置的最大有效值"""
        config = ImageRateLimitConfig(requests_per_minute=1000, max_concurrent=20)
        assert config.requests_per_minute == 1000
        assert config.max_concurrent == 20

    def test_realistic_production_config(self):
        """测试真实生产环境配置"""
        config = RateLimitConfig(
            openai={"requests_per_minute": 60, "tokens_per_minute": 90000, "enable_rate_limit": True},
            image={"requests_per_minute": 10, "enable_rate_limit": True, "max_concurrent": 3},
        )

        # 验证配置合理性
        assert config.openai.tokens_per_minute / config.openai.requests_per_minute == 1500
        assert config.image.max_concurrent <= config.image.requests_per_minute
