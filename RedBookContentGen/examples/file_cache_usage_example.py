#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件缓存管理器使用示例

演示如何使用 FileCacheManager 进行持久化缓存
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.cache_manager import FileCacheManager, get_global_file_cache


# 测试用的类（必须在模块级别定义以支持 pickle）
class ContentResult:
    def __init__(self, title, content):
        self.title = title
        self.content = content


def example_basic_usage():
    """示例 1: 基本使用"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 创建文件缓存管理器
    cache = FileCacheManager(
        cache_dir="cache/example",
        serializer="json",
        default_ttl=3600
    )
    
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


def example_json_vs_pickle():
    """示例 2: JSON vs Pickle 序列化"""
    print("=" * 60)
    print("示例 2: JSON vs Pickle 序列化")
    print("=" * 60)
    
    # JSON 序列化 - 适合简单数据类型
    json_cache = FileCacheManager(
        cache_dir="cache/json",
        serializer="json"
    )
    
    data = {
        "title": "老北京胡同",
        "tags": ["文化", "历史"],
        "count": 100
    }
    json_cache.set("data", data)
    print(f"JSON 缓存: {json_cache.get('data')}")
    
    # Pickle 序列化 - 支持复杂 Python 对象
    pickle_cache = FileCacheManager(
        cache_dir="cache/pickle",
        serializer="pickle"
    )
    
    # 可以缓存任意 Python 对象
    result = ContentResult("标题", "内容")
    pickle_cache.set("result", result)
    cached_result = pickle_cache.get("result")
    print(f"Pickle 缓存: {cached_result.title}, {cached_result.content}")
    print()


def example_persistence():
    """示例 3: 持久化特性"""
    print("=" * 60)
    print("示例 3: 持久化特性")
    print("=" * 60)
    
    # 第一次运行 - 写入缓存
    cache1 = FileCacheManager(cache_dir="cache/persistent")
    cache1.set("app_config", {
        "version": "1.0.0",
        "features": ["content_gen", "image_gen"]
    }, ttl=0)  # 永不过期
    print("已写入配置到文件缓存")
    
    # 模拟程序重启 - 创建新实例
    cache2 = FileCacheManager(cache_dir="cache/persistent")
    config = cache2.get("app_config")
    print(f"从文件缓存读取配置: {config}")
    print("✓ 数据在程序重启后仍然存在")
    print()


def example_ttl_and_cleanup():
    """示例 4: TTL 和清理"""
    print("=" * 60)
    print("示例 4: TTL 和清理")
    print("=" * 60)
    
    cache = FileCacheManager(cache_dir="cache/ttl")
    
    # 设置不同 TTL 的缓存
    cache.set("short_lived", "5秒后过期", ttl=5)
    cache.set("medium_lived", "10秒后过期", ttl=10)
    cache.set("permanent", "永不过期", ttl=0)
    
    print(f"初始缓存条目数: {len(cache)}")
    
    # 等待 6 秒
    print("等待 6 秒...")
    time.sleep(6)
    
    # 清理过期条目
    cleaned = cache.cleanup_expired()
    print(f"清理了 {cleaned} 个过期条目")
    print(f"剩余条目数: {len(cache)}")
    
    # 检查哪些还存在
    print(f"short_lived 存在: {cache.exists('short_lived')}")
    print(f"medium_lived 存在: {cache.exists('medium_lived')}")
    print(f"permanent 存在: {cache.exists('permanent')}")
    print()


def example_content_caching():
    """示例 5: 内容生成缓存"""
    print("=" * 60)
    print("示例 5: 内容生成缓存")
    print("=" * 60)
    
    cache = FileCacheManager(
        cache_dir="cache/content",
        default_ttl=3600  # 1小时
    )
    
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
    cache_key = FileCacheManager.generate_key("content", input_text)
    
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
    print(f"耗时: {elapsed:.2f} 秒 (从文件缓存获取)")
    print(f"结果: {result}")
    print()


def example_image_url_caching():
    """示例 6: 图片 URL 缓存"""
    print("=" * 60)
    print("示例 6: 图片 URL 缓存")
    print("=" * 60)
    
    cache = FileCacheManager(
        cache_dir="cache/images",
        default_ttl=86400  # 24 小时
    )
    
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
        cache_key = FileCacheManager.generate_key("image", prompt)
        
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


def example_size_management():
    """示例 7: 缓存大小管理"""
    print("=" * 60)
    print("示例 7: 缓存大小管理")
    print("=" * 60)
    
    # 设置最大缓存大小为 1MB
    cache = FileCacheManager(
        cache_dir="cache/limited",
        max_size_mb=1.0
    )
    
    # 添加一些数据
    for i in range(10):
        large_data = "x" * 50000  # 约 50KB
        cache.set(f"data_{i}", large_data)
    
    stats = cache.get_stats()
    print(f"缓存条目数: {stats['size']}")
    print(f"缓存大小: {stats['size_mb']:.2f} MB")
    print(f"最大限制: {stats['max_size_mb']} MB")
    print(f"命中率: {stats['hit_rate']:.2%}")
    print()


def example_global_cache():
    """示例 8: 使用全局缓存"""
    print("=" * 60)
    print("示例 8: 使用全局缓存")
    print("=" * 60)
    
    # 获取全局缓存实例
    cache = get_global_file_cache()
    
    # 在不同模块中使用同一个缓存实例
    cache.set("app_config", {"version": "1.0.0", "debug": False})
    
    # 在另一个地方获取
    config = get_global_file_cache().get("app_config")
    print(f"应用配置: {config}")
    
    print(f"全局缓存统计: {cache.get_stats()}")
    print()


def example_mixed_cache():
    """示例 9: 内存缓存 + 文件缓存"""
    print("=" * 60)
    print("示例 9: 内存缓存 + 文件缓存")
    print("=" * 60)
    
    from src.core.cache_manager import CacheManager
    
    # 内存缓存 - 快速但不持久
    memory_cache = CacheManager(max_size=100)
    
    # 文件缓存 - 较慢但持久
    file_cache = FileCacheManager(cache_dir="cache/mixed")
    
    def get_data(key: str) -> str:
        """两级缓存获取"""
        # 先查内存缓存
        value = memory_cache.get(key)
        if value is not None:
            print(f"从内存缓存获取: {key}")
            return value
        
        # 再查文件缓存
        value = file_cache.get(key)
        if value is not None:
            print(f"从文件缓存获取: {key}")
            # 写入内存缓存
            memory_cache.set(key, value)
            return value
        
        # 生成新数据
        print(f"生成新数据: {key}")
        value = f"data_for_{key}"
        memory_cache.set(key, value)
        file_cache.set(key, value)
        return value
    
    # 测试两级缓存
    print("第一次获取:")
    get_data("test_key")
    
    print("\n第二次获取:")
    get_data("test_key")
    
    print("\n清空内存缓存后:")
    memory_cache.clear()
    get_data("test_key")
    print()


def cleanup_examples():
    """清理示例缓存"""
    print("=" * 60)
    print("清理示例缓存")
    print("=" * 60)
    
    import shutil
    cache_dir = Path("cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("✓ 已清理所有示例缓存")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("文件缓存管理器使用示例")
    print("=" * 60 + "\n")
    
    example_basic_usage()
    example_json_vs_pickle()
    example_persistence()
    example_ttl_and_cleanup()
    example_content_caching()
    example_image_url_caching()
    example_size_management()
    example_global_cache()
    example_mixed_cache()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)
    
    # 询问是否清理
    try:
        response = input("\n是否清理示例缓存？(y/n): ")
        if response.lower() == 'y':
            cleanup_examples()
    except (KeyboardInterrupt, EOFError):
        print("\n")


if __name__ == "__main__":
    main()
