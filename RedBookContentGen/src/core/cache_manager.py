#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理模块

提供基于 LRU（最近最少使用）策略的内存缓存功能
支持 TTL（过期时间）和线程安全操作
支持文件系统持久化缓存
"""

import hashlib
import json
import pickle
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union


class CacheManager:
    """缓存管理器

    实现 LRU（Least Recently Used）缓存策略
    支持 TTL（Time To Live）过期时间
    线程安全的缓存操作
    """

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = 3600):
        """
        初始化缓存管理器

        Args:
            max_size: 缓存最大条目数，默认 1000
            default_ttl: 默认过期时间（秒），None 表示永不过期，默认 3600 秒（1小时）
        """
        self._cache: OrderedDict[str, Tuple[Any, Optional[float]]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expire_time = self._cache[key]

            # 检查是否过期
            if expire_time is not None and time.time() > expire_time:
                # 已过期，删除并返回 None
                del self._cache[key]
                self._misses += 1
                return None

            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认 TTL，0 表示永不过期
        """
        with self._lock:
            # 计算过期时间
            if ttl is None:
                ttl = self._default_ttl

            if ttl == 0:
                expire_time = None
            elif ttl is not None:
                expire_time = time.time() + ttl
            else:
                expire_time = None

            # 如果键已存在，先删除（会更新位置）
            if key in self._cache:
                del self._cache[key]

            # 添加新条目
            self._cache[key] = (value, expire_time)

            # 检查是否超过最大容量
            if len(self._cache) > self._max_size:
                # 删除最旧的条目（第一个）
                self._cache.popitem(last=False)
                self._evictions += 1

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否成功删除（True 表示存在并已删除，False 表示不存在）
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            # 重置统计信息
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在且未过期
        """
        with self._lock:
            if key not in self._cache:
                return False

            _, expire_time = self._cache[key]

            # 检查是否过期
            if expire_time is not None and time.time() > expire_time:
                del self._cache[key]
                return False

            return True

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含统计信息的字典：
            - size: 当前缓存条目数
            - max_size: 最大容量
            - hits: 命中次数
            - misses: 未命中次数
            - hit_rate: 命中率（0 - 1）
            - evictions: 淘汰次数
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
            }

    def cleanup_expired(self) -> int:
        """
        清理所有过期的缓存条目

        Returns:
            清理的条目数量
        """
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, (_, expire_time) in self._cache.items():
                if expire_time is not None and current_time > expire_time:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        获取缓存值，如果不存在则通过工厂函数生成并缓存

        Args:
            key: 缓存键
            factory: 工厂函数，用于生成缓存值
            ttl: 过期时间（秒）

        Returns:
            缓存值
        """
        value = self.get(key)
        if value is not None:
            return value

        # 生成新值
        value = factory()
        self.set(key, value, ttl)
        return value

    @staticmethod
    def generate_key(prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            生成的缓存键（使用 SHA256 哈希）
        """
        # 构建键内容
        key_parts = [prefix]

        # 添加位置参数
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        # 添加关键字参数（排序以保证一致性）
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))

        # 生成哈希
        key_content = ":".join(key_parts)
        return hashlib.sha256(key_content.encode()).hexdigest()

    def __len__(self) -> int:
        """返回当前缓存条目数"""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.exists(key)

    def __repr__(self) -> str:
        """返回缓存管理器的字符串表示"""
        stats = self.get_stats()
        return f"CacheManager(size={stats['size']}/{stats['max_size']}, " f"hit_rate={stats['hit_rate']:.2%})"


# 全局缓存实例（可选）
_global_cache: Optional[CacheManager] = None


def get_global_cache() -> CacheManager:
    """
    获取全局缓存实例（单例模式）

    Returns:
        全局缓存管理器实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def set_global_cache(cache: CacheManager) -> None:
    """
    设置全局缓存实例

    Args:
        cache: 缓存管理器实例
    """
    global _global_cache
    _global_cache = cache


class FileCacheManager:
    """文件缓存管理器

    将缓存数据持久化到文件系统
    支持 JSON 和 pickle 两种序列化格式
    支持 TTL 过期时间和自动清理
    线程安全的缓存操作
    """

    def __init__(
        self,
        cache_dir: Union[str, Path] = "cache",
        serializer: str = "json",
        default_ttl: Optional[int] = 3600,
        max_size_mb: Optional[float] = 100.0,
    ):
        """
        初始化文件缓存管理器

        Args:
            cache_dir: 缓存目录路径，默认为 "cache"
            serializer: 序列化格式，"json" 或 "pickle"，默认 "json"
            default_ttl: 默认过期时间（秒），None 表示永不过期，默认 3600 秒（1小时）
            max_size_mb: 最大缓存大小（MB），None 表示无限制，默认 100MB

        Raises:
            ValueError: 如果 serializer 不是 "json" 或 "pickle"
        """
        if serializer not in ("json", "pickle"):
            raise ValueError(f"不支持的序列化格式: {serializer}，仅支持 'json' 或 'pickle'")

        self._cache_dir = Path(cache_dir)
        self._serializer = serializer
        self._default_ttl = default_ttl
        self._max_size_mb = max_size_mb
        self._lock = threading.RLock()

        # 创建缓存目录
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._writes = 0

    def _get_cache_path(self, key: str) -> Path:
        """
        获取缓存文件路径

        Args:
            key: 缓存键

        Returns:
            缓存文件的完整路径
        """
        # 使用键的哈希值作为文件名，避免特殊字符问题
        filename = hashlib.sha256(key.encode()).hexdigest()
        extension = ".json" if self._serializer == "json" else ".pkl"
        return self._cache_dir / f"{filename}{extension}"

    def _get_metadata_path(self, key: str) -> Path:
        """
        获取元数据文件路径

        Args:
            key: 缓存键

        Returns:
            元数据文件的完整路径
        """
        filename = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{filename}.meta"

    def _serialize(self, value: Any) -> bytes:
        """
        序列化值

        Args:
            value: 要序列化的值

        Returns:
            序列化后的字节数据
        """
        if self._serializer == "json":
            return json.dumps(value, ensure_ascii=False).encode("utf - 8")
        else:  # pickle
            return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """
        反序列化数据

        Args:
            data: 序列化的字节数据

        Returns:
            反序列化后的值
        """
        if self._serializer == "json":
            return json.loads(data.decode("utf - 8"))
        else:  # pickle
            return pickle.loads(data)

    def _write_metadata(self, key: str, expire_time: Optional[float]) -> None:
        """
        写入元数据

        Args:
            key: 缓存键
            expire_time: 过期时间戳，None 表示永不过期
        """
        metadata = {"key": key, "expire_time": expire_time, "created_at": time.time()}

        meta_path = self._get_metadata_path(key)
        with open(meta_path, "w", encoding="utf - 8") as f:
            json.dump(metadata, f)

    def _read_metadata(self, key: str) -> Optional[Dict]:
        """
        读取元数据

        Args:
            key: 缓存键

        Returns:
            元数据字典，如果不存在则返回 None
        """
        meta_path = self._get_metadata_path(key)
        if not meta_path.exists():
            return None

        try:
            with open(meta_path, "r", encoding="utf - 8") as f:
                return json.load(f)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, IOError):
            return None

    def _is_expired(self, metadata: Dict) -> bool:
        """
        检查缓存是否过期

        Args:
            metadata: 元数据字典

        Returns:
            是否已过期
        """
        expire_time = metadata.get("expire_time")
        if expire_time is None:
            return False
        return time.time() > expire_time  # type: ignore[no-any-return]

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回 None
        """
        with self._lock:
            cache_path = self._get_cache_path(key)

            # 检查文件是否存在
            if not cache_path.exists():
                self._misses += 1
                return None

            # 读取元数据
            metadata = self._read_metadata(key)
            if metadata is None:
                self._misses += 1
                return None

            # 检查是否过期
            if self._is_expired(metadata):
                # 删除过期文件
                self._delete_files(key)
                self._misses += 1
                return None

            # 读取缓存值
            try:
                with open(cache_path, "rb") as f:
                    data = f.read()
                value = self._deserialize(data)
                self._hits += 1
                return value
            except (IOError, pickle.UnpicklingError, json.JSONDecodeError):
                # 读取失败，删除损坏的文件
                self._delete_files(key)
                self._misses += 1
                return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认 TTL，0 表示永不过期

        Returns:
            是否成功设置
        """
        with self._lock:
            try:
                # 检查缓存大小限制
                if self._max_size_mb is not None:
                    current_size = self._get_cache_size_mb()
                    if current_size >= self._max_size_mb:
                        # 清理过期条目
                        self.cleanup_expired()
                        # 如果仍然超限，清理最旧的条目
                        if self._get_cache_size_mb() >= self._max_size_mb:
                            self._cleanup_oldest()

                # 计算过期时间
                if ttl is None:
                    ttl = self._default_ttl

                if ttl == 0:
                    expire_time = None
                elif ttl is not None:
                    expire_time = time.time() + ttl
                else:
                    expire_time = None

                # 序列化并写入文件
                data = self._serialize(value)
                cache_path = self._get_cache_path(key)

                with open(cache_path, "wb") as f:
                    f.write(data)

                # 写入元数据
                self._write_metadata(key, expire_time)

                self._writes += 1
                return True

            except (IOError, pickle.PicklingError, TypeError):
                return False

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否成功删除（True 表示存在并已删除，False 表示不存在）
        """
        with self._lock:
            return self._delete_files(key)

    def _delete_files(self, key: str) -> bool:
        """
        删除缓存文件和元数据文件

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)

        deleted = False

        if cache_path.exists():
            try:
                cache_path.unlink()
                deleted = True
            except IOError:
                pass

        if meta_path.exists():
            try:
                meta_path.unlink()
            except IOError:
                pass

        return deleted

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            # 删除所有缓存文件
            for file_path in self._cache_dir.glob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except IOError:
                        pass

            # 重置统计信息
            self._hits = 0
            self._misses = 0
            self._writes = 0

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在且未过期
        """
        with self._lock:
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                return False

            metadata = self._read_metadata(key)
            if metadata is None:
                return False

            if self._is_expired(metadata):
                self._delete_files(key)
                return False

            return True

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含统计信息的字典：
            - size: 当前缓存条目数
            - size_mb: 缓存占用空间（MB）
            - max_size_mb: 最大容量（MB）
            - hits: 命中次数
            - misses: 未命中次数
            - hit_rate: 命中率（0 - 1）
            - writes: 写入次数
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            # 统计缓存文件数量
            cache_files = list(self._cache_dir.glob("*.json" if self._serializer == "json" else "*.pkl"))

            return {
                "size": len(cache_files),
                "size_mb": self._get_cache_size_mb(),
                "max_size_mb": self._max_size_mb,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "writes": self._writes,
            }

    def _get_cache_size_mb(self) -> float:
        """
        获取缓存目录占用的空间大小（MB）

        Returns:
            缓存大小（MB）
        """
        total_size = 0
        for file_path in self._cache_dir.glob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except IOError:
                    pass

        return total_size / (1024 * 1024)  # 转换为 MB

    def cleanup_expired(self) -> int:
        """
        清理所有过期的缓存条目

        Returns:
            清理的条目数量
        """
        with self._lock:
            cleaned = 0

            # 遍历所有元数据文件
            for meta_path in self._cache_dir.glob("*.meta"):
                try:
                    with open(meta_path, "r", encoding="utf - 8") as f:
                        metadata = json.load(f)

                    if self._is_expired(metadata):
                        key = metadata.get("key")
                        if key:
                            self._delete_files(key)
                            cleaned += 1
                except (json.JSONDecodeError, IOError):
                    # 元数据文件损坏，删除
                    try:
                        meta_path.unlink()
                    except IOError:
                        pass

            return cleaned

    def _cleanup_oldest(self, count: int = 10) -> int:
        """
        清理最旧的缓存条目

        Args:
            count: 要清理的条目数量

        Returns:
            实际清理的条目数量
        """
        # 获取所有元数据文件及其创建时间
        files_with_time = []

        for meta_path in self._cache_dir.glob("*.meta"):
            try:
                with open(meta_path, "r", encoding="utf - 8") as f:
                    metadata = json.load(f)
                created_at = metadata.get("created_at", 0)
                key = metadata.get("key")
                if key:
                    files_with_time.append((created_at, key))
            except (json.JSONDecodeError, IOError):
                pass

        # 按创建时间排序
        files_with_time.sort()

        # 删除最旧的条目
        cleaned = 0
        for _, key in files_with_time[:count]:
            if self._delete_files(key):
                cleaned += 1

        return cleaned

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        获取缓存值，如果不存在则通过工厂函数生成并缓存

        Args:
            key: 缓存键
            factory: 工厂函数，用于生成缓存值
            ttl: 过期时间（秒）

        Returns:
            缓存值
        """
        value = self.get(key)
        if value is not None:
            return value

        # 生成新值
        value = factory()
        self.set(key, value, ttl)
        return value

    @staticmethod
    def generate_key(prefix: str, *args: Any, **kwargs: Any) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            生成的缓存键（使用 SHA256 哈希）
        """
        # 构建键内容
        key_parts = [prefix]

        # 添加位置参数
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        # 添加关键字参数（排序以保证一致性）
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))

        # 生成哈希
        key_content = ":".join(key_parts)
        return hashlib.sha256(key_content.encode()).hexdigest()

    def __len__(self) -> int:
        """返回当前缓存条目数"""
        with self._lock:
            cache_files = list(self._cache_dir.glob("*.json" if self._serializer == "json" else "*.pkl"))
            return len(cache_files)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.exists(key)

    def __repr__(self) -> str:
        """返回缓存管理器的字符串表示"""
        stats = self.get_stats()
        return (
            f"FileCacheManager(size={stats['size']}, "
            f"size_mb={stats['size_mb']:.2f}MB, "
            f"hit_rate={stats['hit_rate']:.2%})"
        )


# 全局文件缓存实例（可选）
_global_file_cache: Optional[FileCacheManager] = None


def get_global_file_cache() -> FileCacheManager:
    """
    获取全局文件缓存实例（单例模式）

    Returns:
        全局文件缓存管理器实例
    """
    global _global_file_cache
    if _global_file_cache is None:
        _global_file_cache = FileCacheManager()
    return _global_file_cache


def set_global_file_cache(cache: FileCacheManager) -> None:
    """
    设置全局文件缓存实例

    Args:
        cache: 文件缓存管理器实例
    """
    global _global_file_cache
    _global_file_cache = cache
