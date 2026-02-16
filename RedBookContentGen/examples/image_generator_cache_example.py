#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成器缓存功能使用示例

演示如何使用 ImageGenerator 的缓存功能来提高性能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config_manager import ConfigManager
from src.image_generator import ImageGenerator


def example_basic_cache_usage():
    """示例 1: 基本缓存使用"""
    print("\n" + "=" * 60)
    print("示例 1: 基本缓存使用")
    print("=" * 60)
    
    # 创建配置管理器（启用缓存）
    config_manager = ConfigManager("config/config.json")
    
    # 确保缓存已启用
    config_manager.set("cache.enabled", True)
    config_manager.set("cache.ttl", 3600)  # 1小时
    config_manager.set("cache.max_size", 1000)
    
    # 创建图片生成器
    generator = ImageGenerator(config_manager=config_manager)
    
    # 查看缓存统计
    stats = generator.get_cache_stats()
    print(f"\n初始缓存统计:")
    print(f"  - 大小: {stats['size']}/{stats['max_size']}")
    print(f"  - 命中率: {stats['hit_rate']:.2%}")
    print(f"  - 命中次数: {stats['hits']}")
    print(f"  - 未命中次数: {stats['misses']}")


def example_cache_with_generation():
    """示例 2: 图片生成中的缓存"""
    print("\n" + "=" * 60)
    print("示例 2: 图片生成中的缓存")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    config_manager.set("cache.enabled", True)
    config_manager.set("cache.ttl", 86400)  # 24小时
    
    generator = ImageGenerator(config_manager=config_manager)
    
    # 第一次生成（会调用API）
    prompt = "老北京胡同，复古风格，温暖色调，下午阳光"
    print(f"\n第一次生成图片...")
    print(f"提示词: {prompt}")
    
    # 注意：这里只是演示，实际调用需要有效的 API Key
    # result1 = generator.generate_single_image(prompt)
    
    # 第二次生成相同提示词（会从缓存获取）
    print(f"\n第二次生成相同图片...")
    # result2 = generator.generate_single_image(prompt)
    
    # 查看缓存统计
    stats = generator.get_cache_stats()
    print(f"\n缓存统计:")
    print(f"  - 命中率: {stats['hit_rate']:.2%}")
    print(f"  - 命中次数: {stats['hits']}")
    print(f"  - 未命中次数: {stats['misses']}")


def example_cache_key_generation():
    """示例 3: 缓存键生成"""
    print("\n" + "=" * 60)
    print("示例 3: 缓存键生成")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    config_manager.set("cache.enabled", True)
    
    generator = ImageGenerator(config_manager=config_manager)
    
    # 生成不同提示词的缓存键
    prompts = [
        "老北京胡同，复古风格",
        "老北京胡同，复古风格",  # 相同提示词
        "老北京四合院，传统建筑",  # 不同提示词
    ]
    
    print("\n缓存键生成示例:")
    for i, prompt in enumerate(prompts, 1):
        key = generator._generate_cache_key(prompt)
        print(f"  {i}. {prompt[:30]}...")
        print(f"     键: {key}")
    
    # 验证相同提示词生成相同的键
    key1 = generator._generate_cache_key(prompts[0])
    key2 = generator._generate_cache_key(prompts[1])
    key3 = generator._generate_cache_key(prompts[2])
    
    print(f"\n验证:")
    print(f"  - 提示词1和2的键相同: {key1 == key2}")
    print(f"  - 提示词1和3的键不同: {key1 != key3}")


def example_cache_management():
    """示例 4: 缓存管理"""
    print("\n" + "=" * 60)
    print("示例 4: 缓存管理")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    config_manager.set("cache.enabled", True)
    
    generator = ImageGenerator(config_manager=config_manager)
    
    # 手动添加一些缓存数据（模拟）
    print("\n添加缓存数据...")
    test_prompts = [
        "老北京胡同，复古风格",
        "老北京四合院，传统建筑",
        "老北京天坛，蓝天白云",
    ]
    
    for prompt in test_prompts:
        key = generator._generate_cache_key(prompt)
        mock_url = f"https://example.com/image_{hash(prompt)}.png"
        generator.cache.set(key, mock_url)
        print(f"  - 已缓存: {prompt[:30]}...")
    
    # 查看缓存统计
    stats = generator.get_cache_stats()
    print(f"\n当前缓存统计:")
    print(f"  - 大小: {stats['size']}/{stats['max_size']}")
    print(f"  - 命中次数: {stats['hits']}")
    print(f"  - 未命中次数: {stats['misses']}")
    
    # 清空缓存
    print(f"\n清空缓存...")
    generator.clear_cache()
    
    stats = generator.get_cache_stats()
    print(f"\n清空后缓存统计:")
    print(f"  - 大小: {stats['size']}/{stats['max_size']}")
    print(f"  - 命中次数: {stats['hits']}")
    print(f"  - 未命中次数: {stats['misses']}")


def example_cache_disabled():
    """示例 5: 禁用缓存"""
    print("\n" + "=" * 60)
    print("示例 5: 禁用缓存")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    config_manager.set("cache.enabled", False)
    
    generator = ImageGenerator(config_manager=config_manager)
    
    print(f"\n缓存状态:")
    print(f"  - 已启用: {generator._cache_enabled}")
    print(f"  - 缓存对象: {generator.cache}")
    
    # 获取统计（应该返回 None）
    stats = generator.get_cache_stats()
    print(f"  - 统计信息: {stats}")
    
    # 清空缓存（应该不会报错）
    generator.clear_cache()
    print(f"  - 清空缓存: 成功（无操作）")


def example_cache_ttl():
    """示例 6: 缓存过期时间"""
    print("\n" + "=" * 60)
    print("示例 6: 缓存过期时间")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    config_manager.set("cache.enabled", True)
    config_manager.set("cache.ttl", 10)  # 10秒过期
    
    generator = ImageGenerator(config_manager=config_manager)
    
    print(f"\n缓存配置:")
    print(f"  - TTL: 10秒")
    print(f"  - 说明: 缓存的图片URL将在10秒后过期")
    
    # 添加缓存
    prompt = "老北京胡同"
    key = generator._generate_cache_key(prompt)
    mock_url = "https://example.com/image.png"
    generator.cache.set(key, mock_url)
    
    print(f"\n已添加缓存:")
    print(f"  - 提示词: {prompt}")
    print(f"  - URL: {mock_url}")
    
    # 立即获取（应该命中）
    cached = generator.cache.get(key)
    print(f"\n立即获取:")
    print(f"  - 结果: {cached}")
    print(f"  - 命中: {'是' if cached else '否'}")
    
    # 等待过期后获取（需要实际等待，这里只是演示）
    print(f"\n注意: 10秒后再次获取将返回 None（缓存已过期）")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("图片生成器缓存功能使用示例")
    print("=" * 60)
    
    try:
        example_basic_cache_usage()
        example_cache_with_generation()
        example_cache_key_generation()
        example_cache_management()
        example_cache_disabled()
        example_cache_ttl()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
