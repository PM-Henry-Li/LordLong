#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器单元测试
"""

import sys
import time
import threading
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.cache_manager import CacheManager, get_global_cache, set_global_cache


def test_basic_operations():
    """测试基本的缓存操作"""
    print("测试基本操作...")
    cache = CacheManager(max_size=10)

    # 测试 set 和 get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1", "获取缓存值失败"

    # 测试不存在的键
    assert cache.get("nonexistent") is None, "不存在的键应返回 None"

    # 测试 delete
    cache.set("key2", "value2")
    assert cache.delete("key2") is True, "删除存在的键应返回 True"
    assert cache.get("key2") is None, "删除后应无法获取"
    assert cache.delete("key2") is False, "删除不存在的键应返回 False"

    # 测试 exists
    cache.set("key3", "value3")
    assert cache.exists("key3") is True, "exists 应返回 True"
    assert cache.exists("nonexistent") is False, "不存在的键 exists 应返回 False"

    # 测试 clear
    cache.clear()
    assert len(cache) == 0, "清空后缓存应为空"

    print("✓ 基本操作测试通过")


def test_lru_eviction():
    """测试 LRU 淘汰策略"""
    print("测试 LRU 淘汰策略...")
    cache = CacheManager(max_size=3)

    # 添加 3 个条目
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    assert len(cache) == 3, "应有 3 个条目"

    # 添加第 4 个条目，应淘汰最旧的 key1
    cache.set("key4", "value4")
    assert len(cache) == 3, "应保持 3 个条目"
    assert cache.get("key1") is None, "key1 应被淘汰"
    assert cache.get("key2") == "value2", "key2 应存在"
    assert cache.get("key3") == "value3", "key3 应存在"
    assert cache.get("key4") == "value4", "key4 应存在"

    # 访问 key2，使其成为最近使用
    cache.get("key2")

    # 添加 key5，应淘汰 key3（最久未使用）
    cache.set("key5", "value5")
    assert cache.get("key3") is None, "key3 应被淘汰"
    assert cache.get("key2") == "value2", "key2 应存在（最近访问过）"

    stats = cache.get_stats()
    assert stats["evictions"] == 2, "应有 2 次淘汰"

    print("✓ LRU 淘汰策略测试通过")


def test_ttl_expiration():
    """测试 TTL 过期功能"""
    print("测试 TTL 过期...")
    cache = CacheManager(default_ttl=1)  # 默认 1 秒过期

    # 测试默认 TTL
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1", "立即获取应成功"

    time.sleep(1.1)  # 等待过期
    assert cache.get("key1") is None, "过期后应返回 None"

    # 测试自定义 TTL
    cache.set("key2", "value2", ttl=2)
    time.sleep(1)
    assert cache.get("key2") == "value2", "1 秒后应仍然有效"
    time.sleep(1.1)
    assert cache.get("key2") is None, "2 秒后应过期"

    # 测试永不过期
    cache.set("key3", "value3", ttl=0)
    time.sleep(1.5)
    assert cache.get("key3") == "value3", "ttl=0 应永不过期"

    # 测试 exists 检查过期
    cache.set("key4", "value4", ttl=1)
    assert cache.exists("key4") is True, "立即检查应存在"
    time.sleep(1.1)
    assert cache.exists("key4") is False, "过期后 exists 应返回 False"

    print("✓ TTL 过期测试通过")


def test_cleanup_expired():
    """测试清理过期条目"""
    print("测试清理过期条目...")
    cache = CacheManager()

    # 添加一些条目，部分会过期
    cache.set("key1", "value1", ttl=1)
    cache.set("key2", "value2", ttl=1)
    cache.set("key3", "value3", ttl=0)  # 永不过期

    time.sleep(1.1)

    # 清理过期条目
    cleaned = cache.cleanup_expired()
    assert cleaned == 2, "应清理 2 个过期条目"
    assert len(cache) == 1, "应剩余 1 个条目"
    assert cache.get("key3") == "value3", "永不过期的条目应保留"

    print("✓ 清理过期条目测试通过")


def test_thread_safety():
    """测试线程安全"""
    print("测试线程安全...")
    cache = CacheManager(max_size=100)
    errors = []

    def worker(thread_id: int):
        """工作线程"""
        try:
            for i in range(50):
                key = f"thread{thread_id}_key{i}"
                cache.set(key, f"value{i}")
                value = cache.get(key)
                if value != f"value{i}":
                    errors.append(f"线程 {thread_id}: 值不匹配")
        except Exception as e:
            errors.append(f"线程 {thread_id}: {str(e)}")

    # 创建多个线程
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    assert len(errors) == 0, f"线程安全测试失败: {errors}"

    print("✓ 线程安全测试通过")


def test_statistics():
    """测试统计信息"""
    print("测试统计信息...")
    cache = CacheManager(max_size=5)

    # 添加一些数据
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # 命中
    cache.get("key1")
    cache.get("key1")

    # 未命中
    cache.get("nonexistent")

    stats = cache.get_stats()
    assert stats["size"] == 2, "应有 2 个条目"
    assert stats["max_size"] == 5, "最大容量应为 5"
    assert stats["hits"] == 2, "应有 2 次命中"
    assert stats["misses"] == 1, "应有 1 次未命中"
    assert abs(stats["hit_rate"] - 2 / 3) < 0.01, "命中率应约为 66.7%"

    # 测试淘汰统计
    for i in range(6):
        cache.set(f"key{i}", f"value{i}")

    stats = cache.get_stats()
    assert stats["evictions"] >= 1, "应有淘汰发生"

    print("✓ 统计信息测试通过")


def test_get_or_set():
    """测试 get_or_set 方法"""
    print("测试 get_or_set...")
    cache = CacheManager()

    call_count = [0]

    def factory():
        """工厂函数"""
        call_count[0] += 1
        return f"generated_value_{call_count[0]}"

    # 第一次调用，应生成新值
    value1 = cache.get_or_set("key1", factory)
    assert value1 == "generated_value_1", "应生成新值"
    assert call_count[0] == 1, "工厂函数应被调用 1 次"

    # 第二次调用，应返回缓存值
    value2 = cache.get_or_set("key1", factory)
    assert value2 == "generated_value_1", "应返回缓存值"
    assert call_count[0] == 1, "工厂函数不应再次调用"

    print("✓ get_or_set 测试通过")


def test_generate_key():
    """测试缓存键生成"""
    print("测试缓存键生成...")

    # 测试基本键生成
    key1 = CacheManager.generate_key("prefix", "arg1", "arg2")
    key2 = CacheManager.generate_key("prefix", "arg1", "arg2")
    assert key1 == key2, "相同参数应生成相同的键"

    # 测试不同参数
    key3 = CacheManager.generate_key("prefix", "arg1", "arg3")
    assert key1 != key3, "不同参数应生成不同的键"

    # 测试关键字参数
    key4 = CacheManager.generate_key("prefix", param1="value1", param2="value2")
    key5 = CacheManager.generate_key("prefix", param2="value2", param1="value1")
    assert key4 == key5, "关键字参数顺序不同应生成相同的键"

    # 测试复杂对象
    key6 = CacheManager.generate_key("prefix", {"a": 1, "b": 2})
    key7 = CacheManager.generate_key("prefix", {"b": 2, "a": 1})
    assert key6 == key7, "字典键顺序不同应生成相同的键"

    print("✓ 缓存键生成测试通过")


def test_global_cache():
    """测试全局缓存实例"""
    print("测试全局缓存实例...")

    # 获取全局缓存
    cache1 = get_global_cache()
    cache2 = get_global_cache()
    assert cache1 is cache2, "应返回同一个实例"

    # 设置值
    cache1.set("global_key", "global_value")
    assert cache2.get("global_key") == "global_value", "全局缓存应共享数据"

    # 设置新的全局缓存
    new_cache = CacheManager()
    set_global_cache(new_cache)
    cache3 = get_global_cache()
    assert cache3 is new_cache, "应返回新设置的实例"

    print("✓ 全局缓存实例测试通过")


def test_special_methods():
    """测试特殊方法"""
    print("测试特殊方法...")
    cache = CacheManager(max_size=5)

    # 测试 __len__
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    assert len(cache) == 2, "__len__ 应返回 2"

    # 测试 __contains__
    assert "key1" in cache, "__contains__ 应返回 True"
    assert "nonexistent" not in cache, "__contains__ 应返回 False"

    # 测试 __repr__
    repr_str = repr(cache)
    assert "CacheManager" in repr_str, "__repr__ 应包含类名"
    assert "size=" in repr_str, "__repr__ 应包含大小信息"

    print("✓ 特殊方法测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行缓存管理器测试")
    print("=" * 60)

    try:
        test_basic_operations()
        test_lru_eviction()
        test_ttl_expiration()
        test_cleanup_expired()
        test_thread_safety()
        test_statistics()
        test_get_or_set()
        test_generate_key()
        test_global_cache()
        test_special_methods()

        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
