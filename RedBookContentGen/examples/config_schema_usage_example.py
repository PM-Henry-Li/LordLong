#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模式使用示例

演示如何使用 Pydantic 配置模式进行配置验证和管理
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pydantic import ValidationError
from src.core.config_schema import OpenAIAPIConfig, ImageAPIConfig, APIConfig, CacheConfig, LoggingConfig


def example_1_basic_usage():
    """示例 1: 基本使用"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 创建 OpenAI API 配置
    openai_config = OpenAIAPIConfig(
        openai_api_key="sk-test-key-123",
        openai_model="qwen-max",
        timeout=60
    )
    
    print(f"✅ OpenAI 配置创建成功:")
    print(f"   - API Key: {openai_config.key[:10]}...")
    print(f"   - 模型: {openai_config.model}")
    print(f"   - 超时: {openai_config.timeout}秒")
    print(f"   - Base URL: {openai_config.base_url}")
    print()


def example_2_validation():
    """示例 2: 配置验证"""
    print("=" * 60)
    print("示例 2: 配置验证")
    print("=" * 60)
    
    # 尝试创建无效配置
    try:
        invalid_config = OpenAIAPIConfig(
            openai_api_key="sk-test",
            timeout=-10  # 无效：超时时间必须 > 0
        )
    except ValidationError as e:
        print("❌ 配置验证失败（预期行为）:")
        for error in e.errors():
            print(f"   - 字段: {error['loc']}")
            print(f"     错误: {error['msg']}")
    print()


def example_3_default_values():
    """示例 3: 默认值"""
    print("=" * 60)
    print("示例 3: 默认值")
    print("=" * 60)
    
    # 只提供必需字段，其他使用默认值
    config = OpenAIAPIConfig(openai_api_key="sk-test")
    
    print("✅ 使用默认值创建配置:")
    print(f"   - 模型: {config.model} (默认)")
    print(f"   - 超时: {config.timeout}秒 (默认)")
    print(f"   - 最大重试: {config.max_retries}次 (默认)")
    print(f"   - Base URL: {config.base_url} (默认)")
    print()


def example_4_image_config():
    """示例 4: 图片配置"""
    print("=" * 60)
    print("示例 4: 图片配置")
    print("=" * 60)
    
    # 创建图片生成配置
    image_config = ImageAPIConfig(
        image_model="wan2.2-t2i-flash",
        size="2048*2048",
        image_generation_mode="api",
        template_style=None  # API 模式不需要模板风格
    )
    
    print("✅ 图片配置创建成功:")
    print(f"   - 模型: {image_config.model}")
    print(f"   - 尺寸: {image_config.size}")
    print(f"   - 生成模式: {image_config.generation_mode}")
    print(f"   - 超时: {image_config.timeout}秒")
    print()


def example_5_template_mode():
    """示例 5: 模板模式配置"""
    print("=" * 60)
    print("示例 5: 模板模式配置")
    print("=" * 60)
    
    # 模板模式配置
    template_config = ImageAPIConfig(
        image_generation_mode="template",
        template_style="retro_chinese"
    )
    
    print("✅ 模板模式配置:")
    print(f"   - 生成模式: {template_config.generation_mode}")
    print(f"   - 模板风格: {template_config.template_style}")
    print()
    
    # 尝试创建无效的模板配置
    try:
        invalid_template = ImageAPIConfig(
            image_generation_mode="template",
            template_style=None  # 无效：template 模式必须指定风格
        )
    except ValidationError as e:
        print("❌ 模板配置验证失败（预期行为）:")
        for error in e.errors():
            print(f"   - {error['msg']}")
    print()


def example_6_complete_config():
    """示例 6: 完整配置"""
    print("=" * 60)
    print("示例 6: 完整配置")
    print("=" * 60)
    
    # 创建完整的 API 配置
    api_config = APIConfig(
        openai=OpenAIAPIConfig(
            openai_api_key="sk-test-key-123",
            openai_model="qwen-plus",
            timeout=30
        ),
        image=ImageAPIConfig(
            image_generation_mode="template",
            template_style="warm_memory"
        )
    )
    
    print("✅ 完整 API 配置创建成功:")
    print(f"   OpenAI:")
    print(f"     - 模型: {api_config.openai.model}")
    print(f"     - 超时: {api_config.openai.timeout}秒")
    print(f"   图片生成:")
    print(f"     - 模式: {api_config.image.generation_mode}")
    print(f"     - 风格: {api_config.image.template_style}")
    print()


def example_7_from_dict():
    """示例 7: 从字典创建配置"""
    print("=" * 60)
    print("示例 7: 从字典创建配置")
    print("=" * 60)
    
    # 从字典创建配置（模拟从 JSON 加载）
    config_dict = {
        "openai": {
            "openai_api_key": "sk-from-dict",
            "openai_model": "qwen-max",
            "timeout": 45
        },
        "image": {
            "image_model": "wan2.2-t2i-flash",
            "size": "1024*1365",
            "image_generation_mode": "api"
        }
    }
    
    api_config = APIConfig(**config_dict)
    
    print("✅ 从字典创建配置成功:")
    print(f"   - OpenAI 模型: {api_config.openai.model}")
    print(f"   - 图片尺寸: {api_config.image.size}")
    print()


def example_8_to_dict():
    """示例 8: 转换为字典"""
    print("=" * 60)
    print("示例 8: 转换为字典")
    print("=" * 60)
    
    # 创建配置
    api_config = APIConfig(
        openai=OpenAIAPIConfig(openai_api_key="sk-test"),
        image=ImageAPIConfig()
    )
    
    # 转换为字典
    config_dict = api_config.model_dump()
    
    print("✅ 配置转换为字典:")
    print(f"   - OpenAI 配置键: {list(config_dict['openai'].keys())}")
    print(f"   - 图片配置键: {list(config_dict['image'].keys())}")
    print()


def example_9_validation_errors():
    """示例 9: 详细的验证错误"""
    print("=" * 60)
    print("示例 9: 详细的验证错误")
    print("=" * 60)
    
    # 尝试创建多个错误的配置
    try:
        invalid_config = ImageAPIConfig(
            size="invalid-size",  # 错误 1: 格式无效
            timeout=-10,  # 错误 2: 超时时间无效
            image_generation_mode="wrong_mode"  # 错误 3: 生成模式无效
        )
    except ValidationError as e:
        print("❌ 发现多个验证错误:")
        for i, error in enumerate(e.errors(), 1):
            print(f"   错误 {i}:")
            print(f"     - 字段: {'.'.join(str(loc) for loc in error['loc'])}")
            print(f"     - 类型: {error['type']}")
            print(f"     - 消息: {error['msg']}")
    print()


def example_10_size_validation():
    """示例 10: 图片尺寸验证"""
    print("=" * 60)
    print("示例 10: 图片尺寸验证")
    print("=" * 60)
    
    # 有效的尺寸
    valid_sizes = ["512*512", "1024*768", "1920*1080", "2048*2048"]
    
    print("✅ 有效的图片尺寸:")
    for size in valid_sizes:
        config = ImageAPIConfig(size=size)
        print(f"   - {size} ✓")
    
    print()
    
    # 无效的尺寸
    invalid_sizes = [
        ("1024x768", "错误的分隔符"),
        ("abc*def", "非数字"),
        ("-1024*768", "负数"),
        ("5000*5000", "超过最大值")
    ]
    
    print("❌ 无效的图片尺寸:")
    for size, reason in invalid_sizes:
        try:
            ImageAPIConfig(size=size)
        except ValidationError:
            print(f"   - {size} ✗ ({reason})")
    print()


def example_11_cache_config():
    """示例 11: 缓存配置"""
    print("=" * 60)
    print("示例 11: 缓存配置")
    print("=" * 60)
    
    # 创建缓存配置
    cache_config = CacheConfig(
        enabled=True,
        ttl=7200,  # 2小时
        max_size="2GB",
        eviction_policy="lru",
        content_cache_enabled=True,
        image_cache_enabled=True,
        cache_dir="output/cache"
    )
    
    print("✅ 缓存配置创建成功:")
    print(f"   - 启用状态: {cache_config.enabled}")
    print(f"   - 过期时间: {cache_config.ttl}秒")
    print(f"   - 最大大小: {cache_config.max_size}")
    print(f"   - 淘汰策略: {cache_config.eviction_policy}")
    print(f"   - 内容缓存: {cache_config.content_cache_enabled}")
    print(f"   - 图片缓存: {cache_config.image_cache_enabled}")
    print(f"   - 缓存目录: {cache_config.cache_dir}")
    print()


def example_12_cache_validation():
    """示例 12: 缓存配置验证"""
    print("=" * 60)
    print("示例 12: 缓存配置验证")
    print("=" * 60)
    
    # 有效的缓存大小
    valid_sizes = ["1MB", "500MB", "1.5GB", "2GB"]
    print("✅ 有效的缓存大小:")
    for size in valid_sizes:
        config = CacheConfig(max_size=size)
        print(f"   - {size} ✓")
    
    print()
    
    # 无效的缓存大小
    invalid_sizes = [
        ("500KB", "小于最小值 1MB"),
        ("101GB", "超过最大值 100GB"),
        ("1gb", "单位必须大写"),
        ("1TB", "不支持的单位")
    ]
    
    print("❌ 无效的缓存大小:")
    for size, reason in invalid_sizes:
        try:
            CacheConfig(max_size=size)
        except ValidationError:
            print(f"   - {size} ✗ ({reason})")
    print()


def example_13_cache_policies():
    """示例 13: 缓存淘汰策略"""
    print("=" * 60)
    print("示例 13: 缓存淘汰策略")
    print("=" * 60)
    
    policies = {
        "lru": "最近最少使用 (Least Recently Used)",
        "lfu": "最不经常使用 (Least Frequently Used)",
        "fifo": "先进先出 (First In First Out)"
    }
    
    print("✅ 支持的淘汰策略:")
    for policy, description in policies.items():
        config = CacheConfig(eviction_policy=policy)
        print(f"   - {policy}: {description}")
    print()


def example_14_partial_cache_disable():
    """示例 14: 部分禁用缓存"""
    print("=" * 60)
    print("示例 14: 部分禁用缓存")
    print("=" * 60)
    
    # 只禁用图片缓存
    config1 = CacheConfig(
        enabled=True,
        content_cache_enabled=True,
        image_cache_enabled=False
    )
    
    print("✅ 配置 1 - 只启用内容缓存:")
    print(f"   - 总开关: {config1.enabled}")
    print(f"   - 内容缓存: {config1.content_cache_enabled}")
    print(f"   - 图片缓存: {config1.image_cache_enabled}")
    print()
    
    # 完全禁用缓存
    config2 = CacheConfig(enabled=False)
    
    print("✅ 配置 2 - 完全禁用缓存:")
    print(f"   - 总开关: {config2.enabled}")
    print()


def example_15_logging_config():
    """示例 15: 日志配置"""
    print("=" * 60)
    print("示例 15: 日志配置")
    print("=" * 60)
    
    # 创建日志配置
    logging_config = LoggingConfig(
        level="DEBUG",
        format="json",
        file="logs/app.log",
        max_bytes=20971520,  # 20MB
        backup_count=10,
        console_output=True,
        date_format="%Y-%m-%d %H:%M:%S",
        log_dir="logs",
        enable_rotation=True
    )
    
    print("✅ 日志配置创建成功:")
    print(f"   - 日志级别: {logging_config.level}")
    print(f"   - 日志格式: {logging_config.format}")
    print(f"   - 日志文件: {logging_config.file}")
    print(f"   - 文件大小: {logging_config.max_bytes / 1024 / 1024:.1f}MB")
    print(f"   - 备份数量: {logging_config.backup_count}")
    print(f"   - 控制台输出: {logging_config.console_output}")
    print(f"   - 日期格式: {logging_config.date_format}")
    print(f"   - 日志目录: {logging_config.log_dir}")
    print(f"   - 启用轮转: {logging_config.enable_rotation}")
    print()


def example_16_logging_levels():
    """示例 16: 日志级别"""
    print("=" * 60)
    print("示例 16: 日志级别")
    print("=" * 60)
    
    levels = {
        "DEBUG": "调试信息，最详细",
        "INFO": "一般信息",
        "WARNING": "警告信息",
        "ERROR": "错误信息",
        "CRITICAL": "严重错误"
    }
    
    print("✅ 支持的日志级别:")
    for level, description in levels.items():
        config = LoggingConfig(level=level)
        print(f"   - {level}: {description}")
    print()


def example_17_logging_formats():
    """示例 17: 日志格式"""
    print("=" * 60)
    print("示例 17: 日志格式")
    print("=" * 60)
    
    # JSON 格式
    json_config = LoggingConfig(format="json")
    print("✅ JSON 格式配置:")
    print(f"   - 格式: {json_config.format}")
    print("   - 优点: 结构化，易于解析和查询")
    print("   - 适用: 生产环境，日志分析")
    print()
    
    # 文本格式
    text_config = LoggingConfig(format="text")
    print("✅ 文本格式配置:")
    print(f"   - 格式: {text_config.format}")
    print("   - 优点: 人类可读，易于调试")
    print("   - 适用: 开发环境，快速查看")
    print()


def example_18_logging_rotation():
    """示例 18: 日志轮转"""
    print("=" * 60)
    print("示例 18: 日志轮转")
    print("=" * 60)
    
    # 启用轮转
    rotation_config = LoggingConfig(
        enable_rotation=True,
        max_bytes=10485760,  # 10MB
        backup_count=5
    )
    
    print("✅ 日志轮转配置:")
    print(f"   - 启用轮转: {rotation_config.enable_rotation}")
    print(f"   - 单文件大小: {rotation_config.max_bytes / 1024 / 1024:.0f}MB")
    print(f"   - 备份文件数: {rotation_config.backup_count}")
    print(f"   - 总存储空间: {rotation_config.max_bytes * (rotation_config.backup_count + 1) / 1024 / 1024:.0f}MB")
    print()
    
    # 尝试无效配置
    try:
        invalid_rotation = LoggingConfig(
            enable_rotation=True,
            backup_count=0  # 无效：启用轮转时备份数必须 > 0
        )
    except ValidationError as e:
        print("❌ 轮转配置验证失败（预期行为）:")
        for error in e.errors():
            print(f"   - {error['msg']}")
    print()


def example_19_logging_validation():
    """示例 19: 日志配置验证"""
    print("=" * 60)
    print("示例 19: 日志配置验证")
    print("=" * 60)
    
    # 有效的文件路径
    valid_paths = [
        "app.log",
        "logs/app.log",
        "output/logs/application.log"
    ]
    
    print("✅ 有效的日志文件路径:")
    for path in valid_paths:
        config = LoggingConfig(file=path)
        print(f"   - {path} ✓")
    
    print()
    
    # 无效的文件路径
    invalid_paths = [
        ("logs/app.txt", "必须以 .log 结尾"),
        ("", "不能为空")
    ]
    
    print("❌ 无效的日志文件路径:")
    for path, reason in invalid_paths:
        try:
            LoggingConfig(file=path)
        except ValidationError:
            print(f"   - '{path}' ✗ ({reason})")
    print()


def example_20_logging_size_limits():
    """示例 20: 日志文件大小限制"""
    print("=" * 60)
    print("示例 20: 日志文件大小限制")
    print("=" * 60)
    
    # 有效的文件大小
    valid_sizes = [
        (1024, "1KB"),
        (1048576, "1MB"),
        (10485760, "10MB"),
        (104857600, "100MB"),
        (1073741824, "1GB")
    ]
    
    print("✅ 有效的日志文件大小:")
    for size, label in valid_sizes:
        config = LoggingConfig(max_bytes=size)
        print(f"   - {label} ({size} 字节) ✓")
    
    print()
    
    # 无效的文件大小
    invalid_sizes = [
        (512, "小于最小值 1KB"),
        (1073741825, "超过最大值 1GB")
    ]
    
    print("❌ 无效的日志文件大小:")
    for size, reason in invalid_sizes:
        try:
            LoggingConfig(max_bytes=size)
        except ValidationError:
            print(f"   - {size} 字节 ✗ ({reason})")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("配置模式使用示例")
    print("=" * 60 + "\n")
    
    examples = [
        example_1_basic_usage,
        example_2_validation,
        example_3_default_values,
        example_4_image_config,
        example_5_template_mode,
        example_6_complete_config,
        example_7_from_dict,
        example_8_to_dict,
        example_9_validation_errors,
        example_10_size_validation,
        example_11_cache_config,
        example_12_cache_validation,
        example_13_cache_policies,
        example_14_partial_cache_disable,
        example_15_logging_config,
        example_16_logging_levels,
        example_17_logging_formats,
        example_18_logging_rotation,
        example_19_logging_validation,
        example_20_logging_size_limits
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"❌ 示例执行失败: {e}\n")
    
    print("=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
