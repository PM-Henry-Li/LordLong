#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量引用语法示例

演示如何在配置文件中使用 ${ENV_VAR} 语法引用环境变量
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager


def example_basic_reference():
    """示例 1: 基本的环境变量引用"""
    print("=" * 60)
    print("示例 1: 基本的环境变量引用")
    print("=" * 60)

    # 设置环境变量
    os.environ["MY_API_KEY"] = "secret-key-123"
    os.environ["MY_MODEL"] = "qwen-max"

    # 创建配置文件，使用 ${ENV_VAR} 语法
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "openai_api_key": "${MY_API_KEY}",
            "openai_model": "${MY_MODEL}",
            "description": "Using ${MY_MODEL} model with API",
        }
        json.dump(config, f)
        temp_path = f.name

    try:
        # 加载配置
        config_manager = ConfigManager(config_path=temp_path)

        # 查看解析结果
        print(f"API Key: {config_manager.get('openai_api_key')}")
        print(f"Model: {config_manager.get('openai_model')}")
        print(f"Description: {config_manager.get('description')}")
        print()
    finally:
        os.unlink(temp_path)
        del os.environ["MY_API_KEY"]
        del os.environ["MY_MODEL"]


def example_default_value():
    """示例 2: 带默认值的环境变量引用"""
    print("=" * 60)
    print("示例 2: 带默认值的环境变量引用")
    print("=" * 60)

    # 只设置部分环境变量
    os.environ["EXISTING_VAR"] = "from-environment"

    # 创建配置文件，使用 ${ENV_VAR:default} 语法
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "existing_key": "${EXISTING_VAR}",
            "missing_key": "${MISSING_VAR:default-value}",
            "model": "${CUSTOM_MODEL:qwen-plus}",
            "timeout": "${TIMEOUT:30}",
        }
        json.dump(config, f)
        temp_path = f.name

    try:
        # 加载配置
        config_manager = ConfigManager(config_path=temp_path)

        # 查看解析结果
        print(f"Existing Key: {config_manager.get('existing_key')}")
        print(f"Missing Key: {config_manager.get('missing_key')}")
        print(f"Model: {config_manager.get('model')}")
        print(f"Timeout: {config_manager.get('timeout')}")
        print()
    finally:
        os.unlink(temp_path)
        del os.environ["EXISTING_VAR"]


def example_nested_config():
    """示例 3: 嵌套配置中的环境变量引用"""
    print("=" * 60)
    print("示例 3: 嵌套配置中的环境变量引用")
    print("=" * 60)

    # 设置环境变量
    os.environ["API_KEY"] = "nested-key-456"
    os.environ["API_TIMEOUT"] = "60"

    # 创建嵌套配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "api": {
                "openai": {
                    "key": "${API_KEY}",
                    "timeout": "${API_TIMEOUT}",
                    "base_url": "${API_BASE_URL:https://api.default.com}",
                }
            },
            "cache": {"enabled": True, "prefix": "cache_${API_KEY}"},
        }
        json.dump(config, f)
        temp_path = f.name

    try:
        # 加载配置
        config_manager = ConfigManager(config_path=temp_path)

        # 查看解析结果
        print(f"API Key: {config_manager.get('api.openai.key')}")
        print(f"API Timeout: {config_manager.get('api.openai.timeout')}")
        print(f"API Base URL: {config_manager.get('api.openai.base_url')}")
        print(f"Cache Prefix: {config_manager.get('cache.prefix')}")
        print()
    finally:
        os.unlink(temp_path)
        del os.environ["API_KEY"]
        del os.environ["API_TIMEOUT"]


def example_priority():
    """示例 4: 配置优先级演示"""
    print("=" * 60)
    print("示例 4: 配置优先级演示")
    print("=" * 60)

    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "direct-env-key"  # 直接映射的环境变量
    os.environ["REF_KEY"] = "ref-env-key"  # 用于引用的环境变量

    # 创建配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "openai_api_key": "${REF_KEY}",  # 配置文件中使用引用
            "openai_model": "qwen-plus",  # 配置文件中的普通值
        }
        json.dump(config, f)
        temp_path = f.name

    try:
        # 加载配置
        config_manager = ConfigManager(config_path=temp_path)

        # 查看解析结果
        print("配置优先级：环境变量 > 配置文件 > 默认值")
        print()
        print(f"openai_api_key: {config_manager.get('openai_api_key')}")
        print("  -> 来源: 直接环境变量映射 (OPENAI_API_KEY)")
        print("  -> 说明: 直接环境变量优先级最高，覆盖了配置文件中的 ${REF_KEY}")
        print()
        print(f"openai_model: {config_manager.get('openai_model')}")
        print("  -> 来源: 配置文件")
        print("  -> 说明: 没有对应的环境变量，使用配置文件中的值")
        print()
    finally:
        os.unlink(temp_path)
        del os.environ["OPENAI_API_KEY"]
        del os.environ["REF_KEY"]


def example_real_world():
    """示例 5: 实际应用场景"""
    print("=" * 60)
    print("示例 5: 实际应用场景 - 多环境配置")
    print("=" * 60)

    # 模拟不同环境的环境变量
    os.environ["ENV"] = "production"
    os.environ["OPENAI_API_KEY"] = "prod-api-key-xxx"
    os.environ["LOG_LEVEL"] = "WARNING"

    # 创建配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {
            "environment": "${ENV:development}",
            "openai_api_key": "${OPENAI_API_KEY}",
            "openai_model": "${OPENAI_MODEL:qwen-plus}",
            "openai_base_url": "${OPENAI_BASE_URL:https://dashscope.aliyuncs.com/compatible-mode/v1}",
            "logging": {
                "level": "${LOG_LEVEL:INFO}",
                "file": "logs/${ENV:dev}.log",
                "format": "${LOG_FORMAT:json}",
            },
            "cache": {"enabled": "${CACHE_ENABLED:true}", "ttl": "${CACHE_TTL:3600}"},
        }
        json.dump(config, f)
        temp_path = f.name

    try:
        # 加载配置
        config_manager = ConfigManager(config_path=temp_path)

        # 查看解析结果
        print("生产环境配置：")
        print(f"  Environment: {config_manager.get('environment')}")
        print(f"  API Key: {config_manager.get('openai_api_key')[:20]}...")
        print(f"  Model: {config_manager.get('openai_model')}")
        print(f"  Log Level: {config_manager.get('logging.level')}")
        print(f"  Log File: {config_manager.get('logging.file')}")
        print(f"  Log Format: {config_manager.get('logging.format')}")
        print(f"  Cache Enabled: {config_manager.get('cache.enabled')}")
        print(f"  Cache TTL: {config_manager.get('cache.ttl')}")
        print()
        print("说明：")
        print("  - 敏感信息（API Key）从环境变量读取")
        print("  - 环境特定配置（日志级别、日志文件）使用环境变量")
        print("  - 其他配置使用默认值")
        print()
    finally:
        os.unlink(temp_path)
        del os.environ["ENV"]
        del os.environ["OPENAI_API_KEY"]
        del os.environ["LOG_LEVEL"]


def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ConfigManager 环境变量引用语法示例" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    example_basic_reference()
    example_default_value()
    example_nested_config()
    example_priority()
    example_real_world()

    print("=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)
    print()
    print("更多信息请参考：")
    print("  - 文档: docs/CONFIG.md")
    print("  - 示例配置: config/config.example.json")
    print("  - 环境变量模板: .env.example")
    print()


if __name__ == "__main__":
    main()
