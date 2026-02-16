#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制配置使用示例

演示如何使用速率限制配置来控制 API 调用频率
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config_schema import (
    RateLimitConfig,
    OpenAIRateLimitConfig,
    ImageRateLimitConfig
)


def example_1_default_config():
    """示例 1：使用默认配置"""
    print("=" * 60)
    print("示例 1：使用默认配置")
    print("=" * 60)
    
    config = RateLimitConfig()
    
    print(f"OpenAI API 配置：")
    print(f"  - 每分钟请求数: {config.openai.requests_per_minute}")
    print(f"  - 每分钟令牌数: {config.openai.tokens_per_minute}")
    print(f"  - 启用速率限制: {config.openai.enable_rate_limit}")
    
    print(f"\n图片生成 API 配置：")
    print(f"  - 每分钟请求数: {config.image.requests_per_minute}")
    print(f"  - 最大并发数: {config.image.max_concurrent}")
    print(f"  - 启用速率限制: {config.image.enable_rate_limit}")
    print()


def example_2_custom_config():
    """示例 2：自定义配置"""
    print("=" * 60)
    print("示例 2：自定义配置（高级账号）")
    print("=" * 60)
    
    config = RateLimitConfig(
        openai={
            "requests_per_minute": 200,
            "tokens_per_minute": 300000,
            "enable_rate_limit": True
        },
        image={
            "requests_per_minute": 30,
            "enable_rate_limit": True,
            "max_concurrent": 5
        }
    )
    
    print(f"OpenAI API 配置：")
    print(f"  - 每分钟请求数: {config.openai.requests_per_minute}")
    print(f"  - 每分钟令牌数: {config.openai.tokens_per_minute}")
    print(f"  - 平均每请求令牌数: {config.openai.tokens_per_minute // config.openai.requests_per_minute}")
    
    print(f"\n图片生成 API 配置：")
    print(f"  - 每分钟请求数: {config.image.requests_per_minute}")
    print(f"  - 最大并发数: {config.image.max_concurrent}")
    print()


def example_3_json_serialization():
    """示例 3：JSON 序列化和反序列化"""
    print("=" * 60)
    print("示例 3：JSON 序列化和反序列化")
    print("=" * 60)
    
    # 创建配置
    config = RateLimitConfig(
        openai={
            "requests_per_minute": 100,
            "tokens_per_minute": 150000
        }
    )
    
    # 序列化为字典
    config_dict = config.model_dump()
    print("序列化为字典：")
    print(config_dict)
    
    # 从字典反序列化
    new_config = RateLimitConfig(**config_dict)
    print(f"\n反序列化后的配置：")
    print(f"  - OpenAI 每分钟请求数: {new_config.openai.requests_per_minute}")
    print(f"  - 图片每分钟请求数: {new_config.image.requests_per_minute}")
    print()


def example_4_validation_error():
    """示例 4：配置验证错误处理"""
    print("=" * 60)
    print("示例 4：配置验证错误处理")
    print("=" * 60)
    
    from pydantic import ValidationError
    
    # 尝试创建无效配置
    test_cases = [
        {
            "name": "令牌数与请求数比例过低",
            "config": {
                "requests_per_minute": 1000,
                "tokens_per_minute": 50000
            }
        },
        {
            "name": "请求数为零",
            "config": {
                "requests_per_minute": 0,
                "tokens_per_minute": 90000
            }
        },
        {
            "name": "请求数超过上限",
            "config": {
                "requests_per_minute": 20000,
                "tokens_per_minute": 2000000
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试用例：{test_case['name']}")
        try:
            config = OpenAIRateLimitConfig(**test_case['config'])
            print(f"  ✅ 配置有效")
        except ValidationError as e:
            print(f"  ❌ 配置无效")
            for error in e.errors():
                print(f"     - {error['msg']}")
    print()


def example_5_different_account_types():
    """示例 5：不同账号类型的推荐配置"""
    print("=" * 60)
    print("示例 5：不同账号类型的推荐配置")
    print("=" * 60)
    
    account_configs = {
        "免费账号": RateLimitConfig(
            openai={
                "requests_per_minute": 20,
                "tokens_per_minute": 30000,
                "enable_rate_limit": True
            },
            image={
                "requests_per_minute": 5,
                "enable_rate_limit": True,
                "max_concurrent": 2
            }
        ),
        "标准账号": RateLimitConfig(
            openai={
                "requests_per_minute": 60,
                "tokens_per_minute": 90000,
                "enable_rate_limit": True
            },
            image={
                "requests_per_minute": 10,
                "enable_rate_limit": True,
                "max_concurrent": 3
            }
        ),
        "高级账号": RateLimitConfig(
            openai={
                "requests_per_minute": 200,
                "tokens_per_minute": 300000,
                "enable_rate_limit": True
            },
            image={
                "requests_per_minute": 30,
                "enable_rate_limit": True,
                "max_concurrent": 5
            }
        )
    }
    
    for account_type, config in account_configs.items():
        print(f"\n{account_type}：")
        print(f"  OpenAI API：")
        print(f"    - 每分钟请求数: {config.openai.requests_per_minute}")
        print(f"    - 每分钟令牌数: {config.openai.tokens_per_minute}")
        print(f"  图片生成 API：")
        print(f"    - 每分钟请求数: {config.image.requests_per_minute}")
        print(f"    - 最大并发数: {config.image.max_concurrent}")
    print()


def example_6_partial_config():
    """示例 6：部分配置（使用默认值）"""
    print("=" * 60)
    print("示例 6：部分配置（使用默认值）")
    print("=" * 60)
    
    # 只配置 OpenAI，图片使用默认值
    config = RateLimitConfig(
        openai={
            "requests_per_minute": 80,
            "tokens_per_minute": 120000
        }
    )
    
    print(f"OpenAI API（自定义）：")
    print(f"  - 每分钟请求数: {config.openai.requests_per_minute}")
    print(f"  - 每分钟令牌数: {config.openai.tokens_per_minute}")
    
    print(f"\n图片生成 API（默认值）：")
    print(f"  - 每分钟请求数: {config.image.requests_per_minute}")
    print(f"  - 最大并发数: {config.image.max_concurrent}")
    print()


def main():
    """主函数"""
    print("\n🚀 速率限制配置使用示例\n")
    
    # 运行所有示例
    example_1_default_config()
    example_2_custom_config()
    example_3_json_serialization()
    example_4_validation_error()
    example_5_different_account_types()
    example_6_partial_config()
    
    print("=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)
    print("\n📚 更多信息请参考：src/core/RATE_LIMIT_CONFIG.md\n")


if __name__ == "__main__":
    main()
