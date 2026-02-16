#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 image_generator.py 的缓存功能
验证缓存集成、缓存命中、缓存统计等功能
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.config_manager import ConfigManager
from src.image_generator import ImageGenerator


def test_cache_initialization_enabled():
    """测试缓存启用时的初始化"""
    print("\n测试 1: 缓存启用时的初始化")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": True, "ttl": 86400, "max_size": 500},  # 24小时
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 验证缓存已启用
            assert generator._cache_enabled is True
            assert generator.cache is not None

            # 验证缓存配置
            stats = generator.get_cache_stats()
            assert stats is not None
            assert stats["max_size"] == 500

            print("  ✅ 缓存启用初始化成功")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_initialization_disabled():
    """测试缓存禁用时的初始化"""
    print("\n测试 2: 缓存禁用时的初始化")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {"openai_api_key": "test-key", "image_model": "qwen-image-plus", "cache": {"enabled": False}}

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 验证缓存已禁用
            assert generator._cache_enabled is False
            assert generator.cache is None

            # 验证获取统计返回 None
            stats = generator.get_cache_stats()
            assert stats is None

            print("  ✅ 缓存禁用初始化成功")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_key_generation():
    """测试缓存键生成"""
    print("\n测试 3: 缓存键生成")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {"openai_api_key": "test-key", "image_model": "qwen-image-plus", "cache": {"enabled": True}}

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 测试相同内容生成相同的键
            prompt1 = "老北京胡同，复古风格，温暖色调"
            prompt2 = "老北京胡同，复古风格，温暖色调"
            prompt3 = "老北京四合院，传统建筑"

            key1 = generator._generate_cache_key(prompt1)
            key2 = generator._generate_cache_key(prompt2)
            key3 = generator._generate_cache_key(prompt3)

            # 相同内容应该生成相同的键
            assert key1 == key2
            # 不同内容应该生成不同的键
            assert key1 != key3
            # 键应该有前缀
            assert key1.startswith("image_gen:")

            # 测试不同尺寸生成不同的键
            key4 = generator._generate_cache_key(prompt1, "1080*1080")
            assert key1 != key4

            print("  ✅ 缓存键生成正确")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_hit_and_miss():
    """测试缓存命中和未命中"""
    print("\n测试 4: 缓存命中和未命中")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": True, "ttl": 3600},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 模拟图片URL
            test_prompt = "老北京胡同，复古风格"
            mock_url = "https://example.com/image.png"

            # 手动设置缓存
            cache_key = generator._generate_cache_key(test_prompt)
            generator.cache.set(cache_key, mock_url)

            # 验证缓存命中
            cached = generator.cache.get(cache_key)
            assert cached is not None
            assert cached == mock_url

            # 验证统计
            stats = generator.get_cache_stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 0

            # 测试缓存未命中
            different_prompt = "老北京四合院"
            different_key = generator._generate_cache_key(different_prompt)
            not_cached = generator.cache.get(different_key)
            assert not_cached is None

            # 验证统计更新
            stats = generator.get_cache_stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 1

            print("  ✅ 缓存命中和未命中测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_clear():
    """测试缓存清空功能"""
    print("\n测试 5: 缓存清空功能")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {"openai_api_key": "test-key", "image_model": "qwen-image-plus", "cache": {"enabled": True}}

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 添加一些缓存数据
            test_prompt = "老北京胡同"
            mock_url = "https://example.com/image.png"
            cache_key = generator._generate_cache_key(test_prompt)
            generator.cache.set(cache_key, mock_url)

            # 验证缓存存在
            assert generator.cache.get(cache_key) is not None
            stats = generator.get_cache_stats()
            assert stats["size"] == 1

            # 清空缓存
            generator.clear_cache()

            # 验证缓存已清空
            assert generator.cache.get(cache_key) is None
            stats = generator.get_cache_stats()
            assert stats["size"] == 0
            assert stats["hits"] == 0

            print("  ✅ 缓存清空功能正常")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_generate_single_image_with_cache():
    """测试 generate_single_image 方法的缓存集成"""
    print("\n测试 6: generate_single_image 缓存集成")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": True, "ttl": 3600},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            test_prompt = "老北京胡同，复古风格"
            mock_url = "https://example.com/cached_image.png"

            # 预先设置缓存
            cache_key = generator._generate_cache_key(test_prompt, "1024*1365")
            generator.cache.set(cache_key, mock_url)

            # 调用 generate_single_image，应该直接返回缓存结果
            result = generator.generate_single_image(test_prompt)

            # 验证返回的是缓存结果
            assert result == mock_url

            # 验证缓存统计
            stats = generator.get_cache_stats()
            assert stats["hits"] >= 1

            print("  ✅ generate_single_image 缓存集成测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_generate_image_async_with_cache():
    """测试 generate_image_async 方法的缓存集成"""
    print("\n测试 7: generate_image_async 缓存集成")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": True, "ttl": 3600},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            test_prompt = "老北京胡同，复古风格"
            mock_url = "https://example.com/cached_image.png"

            # 预先设置缓存
            cache_key = generator._generate_cache_key(test_prompt, "1024*1365")
            generator.cache.set(cache_key, mock_url)

            # 调用 generate_image_async，应该直接返回缓存结果
            result = generator.generate_image_async(test_prompt, 1, is_cover=False)

            # 验证返回的是缓存结果
            assert result == mock_url

            # 验证缓存统计
            stats = generator.get_cache_stats()
            assert stats["hits"] >= 1

            print("  ✅ generate_image_async 缓存集成测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_disabled_no_caching():
    """测试缓存禁用时不进行缓存"""
    print("\n测试 8: 缓存禁用时不进行缓存")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {"openai_api_key": "test-key", "image_model": "qwen-image-plus", "cache": {"enabled": False}}

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 验证缓存已禁用
            assert generator._cache_enabled is False
            assert generator.cache is None

            # 尝试清空缓存应该不会报错
            generator.clear_cache()

            # 获取统计应该返回 None
            stats = generator.get_cache_stats()
            assert stats is None

            print("  ✅ 缓存禁用测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """运行所有缓存测试"""
    print("=" * 60)
    print("开始测试 image_generator.py 缓存功能")
    print("=" * 60)

    tests = [
        test_cache_initialization_enabled,
        test_cache_initialization_disabled,
        test_cache_key_generation,
        test_cache_hit_and_miss,
        test_cache_clear,
        test_generate_single_image_with_cache,
        test_generate_image_async_with_cache,
        test_cache_disabled_no_caching,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)

    if all(results):
        print("✅ 所有缓存测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
