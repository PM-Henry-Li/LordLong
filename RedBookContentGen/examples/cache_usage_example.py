#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器使用示例

演示如何使用 CacheManager 进行内容缓存

注意: 本示例演示内存缓存（CacheManager）
如需持久化缓存，请参考 file_cache_usage_example.py（FileCacheManager）
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.cache_manager import CacheManager, get_global_cache


def example_basic_usage():
    """示例 1: 基本使用"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 创建缓存管理器
    cache = CacheManager(max_size=100, default_ttl=3600)
    
    # 设置缓存
    cache.set("user:123", {"name": "张三", "age": 25})
    cache.set("user:456", {"name": "李四", "age": 30})
    
    # 获取缓存
    user = cache.get("user:123")
    print(f"获取用户: {user}")
    
    # 检查是否存在
    if "user:123" in cache:
        print("用户 123 存在于缓存中")
    
    # 删除缓存
    cache.delete("user:456")
    print("已删除用户 456")
    
    # 查看统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
    print()


def example_ttl_usage():
    """示例 2: TTL 过期时间"""
    print("=" * 60)
    print("示例 2: TTL 过期时间")
    print("=" * 60)
    
    cache = CacheManager()
    
    # 设置 5 秒后过期
    cache.set("temp_data", "这是临时数据", ttl=5)
    print("设置临时数据，5 秒后过期")
    
    # 立即获取
    data = cache.get("temp_data")
    print(f"立即获取: {data}")
    
    # 等待 3 秒
    print("等待 3 秒...")
    time.sleep(3)
    data = cache.get("temp_data")
    print(f"3 秒后获取: {data}")
    
    # 等待 3 秒（总共 6 秒）
    print("再等待 3 秒...")
    time.sleep(3)
    data = cache.get("temp_data")
    print(f"6 秒后获取: {data} (已过期)")
    
    # 设置永不过期的数据
    cache.set("permanent_data", "永久数据", ttl=0)
    print("设置永久数据（永不过期）")
    print()


def example_lru_eviction():
    """示例 3: LRU 淘汰策略"""
    print("=" * 60)
    print("示例 3: LRU 淘汰策略")
    print("=" * 60)
    
    # 创建容量为 3 的缓存
    cache = CacheManager(max_size=3)
    
    # 添加 3 个条目
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    print(f"添加 3 个条目，当前大小: {len(cache)}")
    
    # 添加第 4 个条目，会淘汰最旧的 key1
    cache.set("key4", "value4")
    print(f"添加第 4 个条目，当前大小: {len(cache)}")
    print(f"key1 是否存在: {cache.exists('key1')} (已被淘汰)")
    print(f"key2 是否存在: {cache.exists('key2')}")
    
    # 访问 key2，使其成为最近使用
    cache.get("key2")
    print("访问 key2，使其成为最近使用")
    
    # 添加 key5，会淘汰 key3（最久未使用）
    cache.set("key5", "value5")
    print(f"添加 key5，key3 是否存在: {cache.exists('key3')} (已被淘汰)")
    print(f"key2 是否存在: {cache.exists('key2')} (最近访问过，保留)")
    
    stats = cache.get_stats()
    print(f"淘汰次数: {stats['evictions']}")
    print()


def example_content_caching():
    """示例 4: 内容生成缓存"""
    print("=" * 60)
    print("示例 4: 内容生成缓存")
    print("=" * 60)
    
    cache = CacheManager()
    
    def generate_content(input_text: str) -> dict:
        """模拟内容生成（耗时操作）"""
        print(f"  正在生成内容: {input_text}...")
        time.sleep(1)  # 模拟 API 调用
        return {
            "title": f"标题: {input_text}",
            "content": f"内容: {input_text} 的详细描述",
            "tags": ["标签1", "标签2"]
        }
    
    # 第一次生成（无缓存）
    input_text = "老北京胡同"
    cache_key = CacheManager.generate_key("content", input_text)
    
    print(f"第一次生成内容: {input_text}")
    start_time = time.time()
    result = cache.get_or_set(cache_key, lambda: generate_content(input_text))
    elapsed = time.time() - start_time
    print(f"耗时: {elapsed:.2f} 秒")
    print(f"结果: {result}")
    
    # 第二次生成（有缓存）
    print(f"\n第二次生成内容: {input_text}")
    start_time = time.time()
    result = cache.get_or_set(cache_key, lambda: generate_content(input_text))
    elapsed = time.time() - start_time
    print(f"耗时: {elapsed:.2f} 秒 (从缓存获取)")
    print(f"结果: {result}")
    print()


def example_image_url_caching():
    """示例 5: 图片 URL 缓存"""
    print("=" * 60)
    print("示例 5: 图片 URL 缓存")
    print("=" * 60)
    
    cache = CacheManager(default_ttl=86400)  # 24 小时
    
    # 模拟图片生成
    def generate_image(prompt: str) -> str:
        """模拟图片生成（耗时操作）"""
        print(f"  正在生成图片: {prompt}...")
        time.sleep(0.5)
        return f"https://example.com/images/{hash(prompt)}.jpg"
    
    prompts = [
        "老北京胡同的秋天",
        "故宫的红墙",
        "老北京胡同的秋天"  # 重复
    ]
    
    for prompt in prompts:
        cache_key = CacheManager.generate_key("image", prompt)
        
        if cache.exists(cache_key):
            url = cache.get(cache_key)
            print(f"从缓存获取: {prompt}")
            print(f"  URL: {url}")
        else:
            url = generate_image(prompt)
            cache.set(cache_key, url)
            print(f"  URL: {url}")
    
    print(f"\n缓存统计: {cache.get_stats()}")
    print()


def example_global_cache():
    """示例 6: 使用全局缓存"""
    print("=" * 60)
    print("示例 6: 使用全局缓存")
    print("=" * 60)
    
    # 获取全局缓存实例
    cache = get_global_cache()
    
    # 在不同模块中使用同一个缓存实例
    cache.set("app_config", {"version": "1.0.0", "debug": False})
    
    # 在另一个地方获取
    config = get_global_cache().get("app_config")
    print(f"应用配置: {config}")
    
    print(f"全局缓存统计: {cache.get_stats()}")
    print()


def example_cleanup():
    """示例 7: 清理过期条目"""
    print("=" * 60)
    print("示例 7: 清理过期条目")
    print("=" * 60)
    
    cache = CacheManager()
    
    # 添加一些会过期的条目
    cache.set("temp1", "data1", ttl=2)
    cache.set("temp2", "data2", ttl=2)
    cache.set("temp3", "data3", ttl=2)
    cache.set("permanent", "data", ttl=0)
    
    print(f"添加 4 个条目，当前大小: {len(cache)}")
    
    # 等待过期
    print("等待 3 秒...")
    time.sleep(3)
    
    # 清理过期条目
    cleaned = cache.cleanup_expired()
    print(f"清理了 {cleaned} 个过期条目")
    print(f"剩余条目数: {len(cache)}")
    print(f"永久数据是否存在: {cache.exists('permanent')}")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("缓存管理器使用示例")
    print("=" * 60 + "\n")
    
    example_basic_usage()
    example_ttl_usage()
    example_lru_eviction()
    example_content_caching()
    example_image_url_caching()
    example_global_cache()
    example_cleanup()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
