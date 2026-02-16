#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigManager 使用示例

演示如何在项目中使用统一配置管理器
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager


def example_basic_usage():
    """示例 1：基本使用"""
    print("=" * 60)
    print("示例 1：基本使用")
    print("=" * 60)
    
    # 初始化配置管理器
    config = ConfigManager()
    
    # 获取配置项
    print(f"OpenAI 模型: {config.get('openai_model')}")
    print(f"图片生成模式: {config.get('image_generation_mode')}")
    print(f"模板风格: {config.get('template_style')}")
    print(f"API 超时时间: {config.get('api.openai.timeout')} 秒")
    print(f"缓存启用: {config.get('cache.enabled')}")
    print()


def example_environment_override():
    """示例 2：环境变量覆盖"""
    print("=" * 60)
    print("示例 2：环境变量覆盖")
    print("=" * 60)
    
    import os
    
    # 设置环境变量
    os.environ["OPENAI_MODEL"] = "qwen-turbo"
    os.environ["CACHE_ENABLED"] = "false"
    
    # 重新初始化配置
    config = ConfigManager()
    
    print(f"OpenAI 模型（环境变量覆盖）: {config.get('openai_model')}")
    print(f"缓存启用（环境变量覆盖）: {config.get('cache.enabled')}")
    
    # 清理环境变量
    del os.environ["OPENAI_MODEL"]
    del os.environ["CACHE_ENABLED"]
    print()


def example_nested_config():
    """示例 3：嵌套配置访问"""
    print("=" * 60)
    print("示例 3：嵌套配置访问")
    print("=" * 60)
    
    config = ConfigManager()
    
    # 访问嵌套配置
    print("API 配置:")
    print(f"  OpenAI 超时: {config.get('api.openai.timeout')} 秒")
    print(f"  OpenAI 最大重试: {config.get('api.openai.max_retries')} 次")
    print(f"  图片尺寸: {config.get('api.image.size')}")
    print(f"  图片超时: {config.get('api.image.timeout')} 秒")
    
    print("\n速率限制配置:")
    print(f"  OpenAI 每分钟请求数: {config.get('rate_limit.openai.requests_per_minute')}")
    print(f"  OpenAI 每分钟令牌数: {config.get('rate_limit.openai.tokens_per_minute')}")
    print(f"  图片每分钟请求数: {config.get('rate_limit.image.requests_per_minute')}")
    print()


def example_dynamic_modification():
    """示例 4：动态修改配置"""
    print("=" * 60)
    print("示例 4：动态修改配置")
    print("=" * 60)
    
    config = ConfigManager()
    
    # 显示原始值
    print(f"原始超时时间: {config.get('api.openai.timeout')} 秒")
    
    # 修改配置
    config.set('api.openai.timeout', 60)
    print(f"修改后超时时间: {config.get('api.openai.timeout')} 秒")
    
    # 重新加载配置（恢复到文件中的值）
    config.reload()
    print(f"重新加载后超时时间: {config.get('api.openai.timeout')} 秒")
    print()


def example_validation():
    """示例 5：配置验证"""
    print("=" * 60)
    print("示例 5：配置验证")
    print("=" * 60)
    
    config = ConfigManager()
    
    # 验证配置
    is_valid = config.validate()
    print(f"配置验证结果: {'通过' if is_valid else '失败'}")
    
    # 获取详细的验证错误
    errors = config.get_validation_errors()
    if errors:
        print("\n验证错误详情:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    else:
        print("\n✅ 配置完全有效，没有发现任何问题")
    print()


def example_validation_details():
    """示例 5.1：详细的配置验证"""
    print("=" * 60)
    print("示例 5.1：详细的配置验证")
    print("=" * 60)
    
    config = ConfigManager()
    
    print("配置验证包括以下检查:\n")
    
    print("1. 必需字段检查:")
    print("   - openai_api_key: OpenAI API Key")
    print("   - openai_model: OpenAI 模型名称")
    print("   - openai_base_url: OpenAI API 基础URL")
    
    print("\n2. 类型验证:")
    print("   - api.openai.timeout: 必须是整数")
    print("   - api.openai.max_retries: 必须是整数")
    print("   - cache.enabled: 必须是布尔值")
    print("   - cache.ttl: 必须是整数")
    
    print("\n3. 值范围验证:")
    print("   - 超时时间必须 > 0")
    print("   - 重试次数必须 >= 0")
    print("   - 速率限制必须 > 0")
    
    print("\n4. 格式验证:")
    print("   - URL 必须以 http:// 或 https:// 开头")
    print("   - 模型名称不能为空字符串")
    
    print("\n5. 枚举值验证:")
    print("   - image_generation_mode: ['template', 'api']")
    print("   - template_style: ['retro_chinese', 'modern_minimal', 'vintage_film', 'warm_memory', 'ink_wash']")
    print("   - logging.level: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']")
    
    print("\n执行验证...")
    errors = config.get_validation_errors()
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个配置问题:")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    else:
        print("\n✅ 所有验证检查通过！")
    print()


def example_get_all():
    """示例 6：获取所有配置"""
    print("=" * 60)
    print("示例 6：获取所有配置")
    print("=" * 60)
    
    config = ConfigManager()
    
    # 获取所有配置
    all_config = config.get_all()
    
    print("所有配置项:")
    for key, value in all_config.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    print()


def example_integration_with_openai():
    """示例 7：与 OpenAI 客户端集成"""
    print("=" * 60)
    print("示例 7：与 OpenAI 客户端集成")
    print("=" * 60)
    
    config = ConfigManager()
    
    # 获取 OpenAI 配置
    api_key = config.get('openai_api_key')
    base_url = config.get('openai_base_url')
    model = config.get('openai_model')
    timeout = config.get('api.openai.timeout')
    max_retries = config.get('api.openai.max_retries')
    
    print("OpenAI 客户端配置:")
    print(f"  API Key: {'已设置' if api_key else '未设置'}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print(f"  Timeout: {timeout} 秒")
    print(f"  Max Retries: {max_retries} 次")
    
    # 如果有 API Key，可以创建客户端
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
                max_retries=max_retries
            )
            print("\n✅ OpenAI 客户端创建成功")
        except ImportError:
            print("\n⚠️  未安装 openai 包")
    else:
        print("\n⚠️  未设置 API Key，无法创建客户端")
    print()


def example_config_source():
    """示例 8：配置来源追踪"""
    print("=" * 60)
    print("示例 8：配置来源追踪")
    print("=" * 60)
    
    import os
    
    # 设置一个环境变量
    os.environ["OPENAI_MODEL"] = "qwen-max"
    
    config = ConfigManager()
    
    # 检查各个配置项的来源
    test_keys = [
        "openai_model",
        "template_style",
        "api.openai.timeout",
        "cache.enabled"
    ]
    
    print("配置项来源:")
    for key in test_keys:
        source = config.get_config_source(key)
        value = config.get(key)
        source_name = {
            'environment': '环境变量',
            'file': '配置文件',
            'default': '默认值',
            'not_found': '未找到'
        }.get(source, source)
        print(f"  {key}: {value} (来源: {source_name})")
    
    # 清理环境变量
    del os.environ["OPENAI_MODEL"]
    print()


def example_priority_demonstration():
    """示例 9：配置优先级演示"""
    print("=" * 60)
    print("示例 9：配置优先级演示")
    print("=" * 60)
    
    import os
    
    # 设置环境变量
    os.environ["OPENAI_MODEL"] = "qwen-turbo-from-env"
    os.environ["CACHE_ENABLED"] = "false"
    os.environ["OPENAI_TIMEOUT"] = "90"
    
    config = ConfigManager()
    
    print("配置优先级演示（环境变量 > 配置文件 > 默认值）:\n")
    
    print("1. 环境变量设置的配置（最高优先级）:")
    print(f"   OPENAI_MODEL = {config.get('openai_model')}")
    print(f"   CACHE_ENABLED = {config.get('cache.enabled')}")
    print(f"   OPENAI_TIMEOUT = {config.get('api.openai.timeout')}")
    
    print("\n2. 配置文件中的配置（中等优先级）:")
    print(f"   如果 config.json 中设置了 openai_api_key，会覆盖默认值")
    
    print("\n3. 默认值（最低优先级）:")
    print(f"   template_style = {config.get('template_style')}")
    print(f"   image_generation_mode = {config.get('image_generation_mode')}")
    
    # 清理环境变量
    del os.environ["OPENAI_MODEL"]
    del os.environ["CACHE_ENABLED"]
    del os.environ["OPENAI_TIMEOUT"]
    print()


def example_extended_env_vars():
    """示例 10：扩展的环境变量支持"""
    print("=" * 60)
    print("示例 10：扩展的环境变量支持")
    print("=" * 60)
    
    print("支持的环境变量映射:\n")
    
    env_examples = [
        ("OPENAI_API_KEY", "openai_api_key", "API 密钥"),
        ("OPENAI_MODEL", "openai_model", "模型名称"),
        ("OPENAI_TIMEOUT", "api.openai.timeout", "API 超时时间"),
        ("CACHE_ENABLED", "cache.enabled", "缓存开关"),
        ("CACHE_TTL", "cache.ttl", "缓存过期时间"),
        ("LOG_LEVEL", "logging.level", "日志级别"),
        ("RATE_LIMIT_OPENAI_RPM", "rate_limit.openai.requests_per_minute", "速率限制"),
    ]
    
    for env_var, config_key, description in env_examples:
        print(f"  {env_var}")
        print(f"    → {config_key}")
        print(f"    说明: {description}\n")
    
    print("使用方法:")
    print("  export OPENAI_API_KEY=your-api-key")
    print("  export CACHE_ENABLED=true")
    print("  export OPENAI_TIMEOUT=60")
    print("  python run.py")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("ConfigManager 使用示例")
    print("=" * 60 + "\n")
    
    example_basic_usage()
    example_environment_override()
    example_nested_config()
    example_dynamic_modification()
    example_validation()
    example_validation_details()
    example_get_all()
    example_integration_with_openai()
    example_config_source()
    example_priority_demonstration()
    example_extended_env_vars()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
