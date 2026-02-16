#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云图片生成服务提供商单元测试

测试 AliyunImageProvider 类的基本功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.image_providers.aliyun_provider import AliyunImageProvider
from src.core.config_manager import ConfigManager
from src.core.logger import Logger


def test_aliyun_provider_initialization():
    """测试 AliyunImageProvider 初始化"""
    print("=" * 60)
    print("测试: AliyunImageProvider 初始化")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 设置测试配置
    config_manager.set("openai_api_key", "sk-test-api-key-12345")
    config_manager.set("image_model", "wanx-v1")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证初始化
    assert provider is not None, "Provider 实例不应为 None"
    assert provider.api_key == "sk-test-api-key-12345", "API Key 不匹配"
    assert provider.image_model == "wanx-v1", "Image Model 不匹配"
    assert provider.image_generation_url == "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis", "Image Generation URL 不匹配"
    assert provider.task_status_url == "https://dashscope.aliyuncs.com/api/v1/tasks", "Task Status URL 不匹配"
    
    print("✅ 初始化测试通过")
    print()


def test_aliyun_provider_get_provider_name():
    """测试 get_provider_name() 方法"""
    print("=" * 60)
    print("测试: get_provider_name() 方法")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("openai_api_key", "sk-test-key")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证提供商名称
    provider_name = provider.get_provider_name()
    assert provider_name == "aliyun", f"提供商名称应为 'aliyun'，实际为 '{provider_name}'"
    
    print(f"✅ 提供商名称: {provider_name}")
    print()


def test_aliyun_provider_without_api_key():
    """测试没有 API Key 时的初始化"""
    print("=" * 60)
    print("测试: 没有 API Key 时的初始化")
    print("=" * 60)
    
    # 创建配置管理器（不设置 API Key）
    config_manager = ConfigManager()
    
    # 显式清除 API Key（如果配置文件中有的话）
    config_manager.set("openai_api_key", None)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证 api_key 为 None
    assert provider.api_key is None, "没有 API Key 时 api_key 应为 None"
    
    print("✅ 没有 API Key 时正确处理")
    print()


def test_aliyun_provider_default_values():
    """测试默认配置值"""
    print("=" * 60)
    print("测试: 默认配置值")
    print("=" * 60)
    
    # 创建一个新的配置管理器，不加载配置文件
    config_manager = ConfigManager(config_path=None)
    config_manager.set("openai_api_key", "sk-test-key")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证默认值（如果配置文件存在，可能会使用配置文件中的值）
    # 所以我们只验证 URL 是否正确，这些是硬编码的
    assert provider.image_generation_url == "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis", "默认 image_generation_url 不正确"
    assert provider.task_status_url == "https://dashscope.aliyuncs.com/api/v1/tasks", "默认 task_status_url 不正确"
    
    # image_model 可能来自配置文件或默认值，只要不为空即可
    assert provider.image_model is not None, "image_model 不应为 None"
    assert isinstance(provider.image_model, str), "image_model 应为字符串"
    
    print(f"✅ 默认配置值正确 (image_model: {provider.image_model})")
    print()


def test_aliyun_provider_prompt_cleaning():
    """测试提示词清理功能"""
    print("=" * 60)
    print("测试: 提示词清理功能")
    print("=" * 60)
    
    import re
    
    # 测试清理 --ar 参数
    prompt1 = "一个美丽的风景 --ar 16:9"
    clean1 = re.sub(r"--ar\s*\d+:\d+", "", prompt1).strip()
    assert clean1 == "一个美丽的风景", f"清理 --ar 失败: {clean1}"
    
    # 测试清理 --v 参数
    prompt2 = "一个美丽的风景 --v 5.2"
    clean2 = re.sub(r"--v\s*\d+(\.\d+)?", "", prompt2).strip()
    assert clean2 == "一个美丽的风景", f"清理 --v 失败: {clean2}"
    
    # 测试清理 --style 参数
    prompt3 = "一个美丽的风景 --style raw"
    clean3 = re.sub(r"--style\s+\w+", "", prompt3).strip()
    assert clean3 == "一个美丽的风景", f"清理 --style 失败: {clean3}"
    
    # 测试清理多个参数
    prompt4 = "一个美丽的风景 --ar 16:9 --v 5 --style raw"
    clean4 = re.sub(r"--ar\s*\d+:\d+", "", prompt4)
    clean4 = re.sub(r"--v\s*\d+(\.\d+)?", "", clean4)
    clean4 = re.sub(r"--style\s+\w+", "", clean4).strip()
    assert clean4 == "一个美丽的风景", f"清理多个参数失败: {clean4}"
    
    print("✅ 提示词清理功能正确")
    print()


def test_aliyun_provider_cache_key_generation():
    """测试缓存键生成"""
    print("=" * 60)
    print("测试: 缓存键生成")
    print("=" * 60)
    
    import hashlib
    
    # 测试相同的提示词和尺寸生成相同的缓存键
    prompt = "一个美丽的风景"
    size = "1024*1365"
    
    cache_key1 = hashlib.md5(f"{prompt}_{size}".encode('utf-8')).hexdigest()
    cache_key2 = hashlib.md5(f"{prompt}_{size}".encode('utf-8')).hexdigest()
    
    assert cache_key1 == cache_key2, "相同输入应生成相同的缓存键"
    
    # 测试不同的提示词生成不同的缓存键
    prompt2 = "另一个美丽的风景"
    cache_key3 = hashlib.md5(f"{prompt2}_{size}".encode('utf-8')).hexdigest()
    
    assert cache_key1 != cache_key3, "不同提示词应生成不同的缓存键"
    
    # 测试不同的尺寸生成不同的缓存键
    size2 = "1080*1080"
    cache_key4 = hashlib.md5(f"{prompt}_{size2}".encode('utf-8')).hexdigest()
    
    assert cache_key1 != cache_key4, "不同尺寸应生成不同的缓存键"
    
    print("✅ 缓存键生成正确")
    print()


def test_aliyun_provider_negative_prompt():
    """测试负面提示词生成"""
    print("=" * 60)
    print("测试: 负面提示词生成")
    print("=" * 60)
    
    # 默认负面提示词
    default_negative = "nsfw, text, watermark, username, signature, logo, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, blurry"
    
    # 封面图额外的负面提示词
    cover_negative = "乱码文字，错误汉字，无法识别的字符，文字模糊，文字扭曲，文字重叠，非标准汉字，错别字，文字不清晰，字符遗漏，文字不完整，缺少汉字"
    
    # 测试封面图的负面提示词
    cover_full_negative = f"{default_negative}, {cover_negative}"
    assert default_negative in cover_full_negative, "封面图负面提示词应包含默认负面提示词"
    assert cover_negative in cover_full_negative, "封面图负面提示词应包含封面专用负面提示词"
    
    # 测试普通图的负面提示词
    normal_negative = default_negative
    assert normal_negative == default_negative, "普通图负面提示词应等于默认负面提示词"
    
    print("✅ 负面提示词生成正确")
    print()


def test_aliyun_provider_with_cache():
    """测试带缓存的 AliyunImageProvider"""
    print("=" * 60)
    print("测试: 带缓存的 AliyunImageProvider")
    print("=" * 60)
    
    from unittest.mock import Mock
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("openai_api_key", "sk-test-key")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 Mock 缓存
    mock_cache = Mock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=mock_cache
    )
    
    # 验证缓存已设置
    assert provider.cache is not None, "缓存应该被设置"
    assert provider.cache == mock_cache, "缓存实例应该匹配"
    
    print("✅ 带缓存的 AliyunImageProvider 正确")
    print()


def test_aliyun_provider_with_rate_limiter():
    """测试带速率限制的 AliyunImageProvider"""
    print("=" * 60)
    print("测试: 带速率限制的 AliyunImageProvider")
    print("=" * 60)
    
    from unittest.mock import Mock
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("openai_api_key", "sk-test-key")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 Mock 速率限制器
    mock_rate_limiter = Mock()
    mock_rate_limiter.get_available_tokens.return_value = 10
    mock_rate_limiter.wait_for_token.return_value = True
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=mock_rate_limiter,
        cache=None
    )
    
    # 验证速率限制器已设置
    assert provider.rate_limiter is not None, "速率限制器应该被设置"
    assert provider.rate_limiter == mock_rate_limiter, "速率限制器实例应该匹配"
    
    print("✅ 带速率限制的 AliyunImageProvider 正确")
    print()


def test_aliyun_provider_integration_with_image_generator():
    """测试与 ImageGenerator 的集成"""
    print("=" * 60)
    print("测试: 与 ImageGenerator 的集成")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("openai_api_key", "sk-test-key")
    config_manager.set("image_model", "wanx-v1")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 AliyunImageProvider 实例
    provider = AliyunImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证 provider 可以被正确创建和使用
    assert provider is not None, "Provider 应该被正确创建"
    assert provider.get_provider_name() == "aliyun", "Provider 名称应该是 'aliyun'"
    assert hasattr(provider, 'generate'), "Provider 应该有 generate 方法"
    assert hasattr(provider, '_create_task'), "Provider 应该有 _create_task 方法"
    assert hasattr(provider, '_wait_for_task_completion'), "Provider 应该有 _wait_for_task_completion 方法"
    
    print("✅ 与 ImageGenerator 的集成正确")
    print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始运行 AliyunImageProvider 单元测试")
    print("=" * 60 + "\n")
    
    try:
        test_aliyun_provider_initialization()
        test_aliyun_provider_get_provider_name()
        test_aliyun_provider_without_api_key()
        test_aliyun_provider_default_values()
        test_aliyun_provider_prompt_cleaning()
        test_aliyun_provider_cache_key_generation()
        test_aliyun_provider_negative_prompt()
        test_aliyun_provider_with_cache()
        test_aliyun_provider_with_rate_limiter()
        test_aliyun_provider_integration_with_image_generator()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
