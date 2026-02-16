#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 content_generator.py 的缓存功能
验证缓存集成、缓存命中、缓存统计等功能
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.config_manager import ConfigManager
from src.content_generator import RedBookContentGenerator


def test_cache_initialization_enabled():
    """测试缓存启用时的初始化"""
    print("\n测试 1: 缓存启用时的初始化")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "cache": {"enabled": True, "ttl": 7200, "max_size": 500},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

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
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "cache": {"enabled": False},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

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
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "cache": {"enabled": True},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 测试相同内容生成相同的键
            content1 = "老北京胡同文化"
            content2 = "老北京胡同文化"
            content3 = "老北京四合院"

            key1 = generator._generate_cache_key(content1)
            key2 = generator._generate_cache_key(content2)
            key3 = generator._generate_cache_key(content3)

            # 相同内容应该生成相同的键
            assert key1 == key2
            # 不同内容应该生成不同的键
            assert key1 != key3
            # 键应该有前缀
            assert key1.startswith("content_gen:")

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
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "cache": {"enabled": True, "ttl": 3600},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 模拟生成结果
            test_content = "老北京胡同文化"
            mock_result = {
                "titles": ["标题1", "标题2"],
                "content": "正文内容",
                "tags": "#老北京 #胡同",
                "image_prompts": [],
            }

            # 手动设置缓存
            cache_key = generator._generate_cache_key(test_content)
            generator.cache.set(cache_key, mock_result)

            # 验证缓存命中
            cached = generator.cache.get(cache_key)
            assert cached is not None
            assert cached["titles"] == ["标题1", "标题2"]

            # 验证统计
            stats = generator.get_cache_stats()
            assert stats["hits"] == 1
            assert stats["misses"] == 0

            # 测试缓存未命中
            different_content = "老北京四合院"
            different_key = generator._generate_cache_key(different_content)
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
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "cache": {"enabled": True},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 添加一些缓存数据
            test_content = "老北京胡同文化"
            mock_result = {"titles": ["标题1"]}
            cache_key = generator._generate_cache_key(test_content)
            generator.cache.set(cache_key, mock_result)

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
            # 注意：clear() 会重置统计信息，所以 hits 和 misses 都应该是 0
            assert stats["hits"] == 0
            # misses 可能不是 0，因为上面的 get 操作会增加 misses
            # 但 clear() 应该重置它

            print("  ✅ 缓存清空功能正常")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_with_generate_content_mock():
    """测试 generate_content 方法的缓存集成（使用 mock）"""
    print("\n测试 6: generate_content 缓存集成（mock）")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "cache": {"enabled": True, "ttl": 3600},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            test_content = "老北京胡同文化"
            mock_result = {
                "titles": ["标题1", "标题2"],
                "content": "正文内容",
                "tags": "#老北京 #胡同",
                "image_prompts": [],
                "cover": {},
            }

            # 预先设置缓存
            cache_key = generator._generate_cache_key(test_content)
            generator.cache.set(cache_key, mock_result)

            # 调用 generate_content，应该直接返回缓存结果
            # 不会真正调用 API
            result = generator.generate_content(test_content)

            # 验证返回的是缓存结果
            assert result == mock_result
            assert result["titles"] == ["标题1", "标题2"]

            # 验证缓存统计
            stats = generator.get_cache_stats()
            assert stats["hits"] >= 1  # 至少有一次命中

            print("  ✅ generate_content 缓存集成测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_disabled_no_caching():
    """测试缓存禁用时不进行缓存"""
    print("\n测试 7: 缓存禁用时不进行缓存")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
            "cache": {"enabled": False},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

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
    print("开始测试 content_generator.py 缓存功能")
    print("=" * 60)

    tests = [
        test_cache_initialization_enabled,
        test_cache_initialization_disabled,
        test_cache_key_generation,
        test_cache_hit_and_miss,
        test_cache_clear,
        test_cache_with_generate_content_mock,
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
