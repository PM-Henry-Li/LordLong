# 文件缓存管理器文档

## 概述

`FileCacheManager` 是一个基于文件系统的持久化缓存管理器，支持将缓存数据保存到磁盘，即使程序重启后数据仍然存在。

## 主要特性

- ✅ **持久化存储**: 缓存数据保存到文件系统，程序重启后仍可访问
- ✅ **多种序列化格式**: 支持 JSON 和 pickle 两种序列化方式
- ✅ **TTL 过期机制**: 支持设置缓存过期时间，自动清理过期数据
- ✅ **大小限制**: 支持设置最大缓存大小，自动清理旧数据
- ✅ **线程安全**: 使用锁机制保证多线程环境下的安全性
- ✅ **统计信息**: 提供命中率、缓存大小等统计数据
- ✅ **自动清理**: 支持手动和自动清理过期缓存

## 快速开始

### 基本使用

```python
from src.core.cache_manager import FileCacheManager

# 创建文件缓存管理器
cache = FileCacheManager(
    cache_dir="cache",           # 缓存目录
    serializer="json",           # 序列化格式: "json" 或 "pickle"
    default_ttl=3600,            # 默认过期时间（秒）
    max_size_mb=100.0            # 最大缓存大小（MB）
)

# 设置缓存
cache.set("key", "value")

# 获取缓存
value = cache.get("key")

# 删除缓存
cache.delete("key")

# 清空所有缓存
cache.clear()
```

### 使用 TTL

```python
# 设置 5 分钟后过期
cache.set("temp_data", "临时数据", ttl=300)

# 设置永不过期
cache.set("permanent_data", "永久数据", ttl=0)

# 使用默认 TTL
cache.set("default_data", "默认过期时间")
```

### 自动生成和缓存

```python
def expensive_operation():
    # 耗时操作
    return "结果"

# 如果缓存存在则返回，否则执行函数并缓存结果
result = cache.get_or_set("cache_key", expensive_operation)
```

## API 参考

### 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cache_dir` | str/Path | "cache" | 缓存目录路径 |
| `serializer` | str | "json" | 序列化格式："json" 或 "pickle" |
| `default_ttl` | int/None | 3600 | 默认过期时间（秒），None 表示永不过期 |
| `max_size_mb` | float/None | 100.0 | 最大缓存大小（MB），None 表示无限制 |

### 核心方法

#### get(key: str) -> Optional[Any]

获取缓存值。

```python
value = cache.get("key")
if value is None:
    print("缓存不存在或已过期")
```

#### set(key: str, value: Any, ttl: Optional[int] = None) -> bool

设置缓存值。

```python
# 使用默认 TTL
cache.set("key", "value")

# 自定义 TTL
cache.set("key", "value", ttl=600)

# 永不过期
cache.set("key", "value", ttl=0)
```

#### delete(key: str) -> bool

删除缓存条目。

```python
if cache.delete("key"):
    print("删除成功")
else:
    print("键不存在")
```

#### exists(key: str) -> bool

检查缓存键是否存在且未过期。

```python
if cache.exists("key"):
    print("缓存存在")
```

#### clear() -> None

清空所有缓存。

```python
cache.clear()
```

#### get_or_set(key: str, factory: callable, ttl: Optional[int] = None) -> Any

获取缓存值，如果不存在则通过工厂函数生成并缓存。

```python
def generate_data():
    return "新数据"

value = cache.get_or_set("key", generate_data, ttl=300)
```

#### cleanup_expired() -> int

清理所有过期的缓存条目。

```python
cleaned = cache.cleanup_expired()
print(f"清理了 {cleaned} 个过期条目")
```

#### get_stats() -> Dict[str, Any]

获取缓存统计信息。

```python
stats = cache.get_stats()
print(f"缓存条目数: {stats['size']}")
print(f"缓存大小: {stats['size_mb']:.2f} MB")
print(f"命中率: {stats['hit_rate']:.2%}")
```

返回的统计信息包括：
- `size`: 当前缓存条目数
- `size_mb`: 缓存占用空间（MB）
- `max_size_mb`: 最大容量（MB）
- `hits`: 命中次数
- `misses`: 未命中次数
- `hit_rate`: 命中率（0-1）
- `writes`: 写入次数

### 静态方法

#### generate_key(prefix: str, *args, **kwargs) -> str

生成缓存键（使用 SHA256 哈希）。

```python
# 基本用法
key = FileCacheManager.generate_key("content", "input_text")

# 使用关键字参数
key = FileCacheManager.generate_key("image", prompt="老北京", style="retro")

# 使用复杂对象
key = FileCacheManager.generate_key("data", {"a": 1, "b": 2})
```

### 特殊方法

```python
# 获取缓存条目数
count = len(cache)

# 检查键是否存在
if "key" in cache:
    print("存在")

# 字符串表示
print(cache)  # FileCacheManager(size=10, size_mb=0.05MB, hit_rate=75.00%)
```

## 序列化格式对比

### JSON 序列化

**优点**:
- 人类可读
- 跨语言兼容
- 文件体积较小

**缺点**:
- 仅支持基本数据类型（字符串、数字、列表、字典等）
- 不支持自定义类对象

**适用场景**:
- 简单数据结构
- 需要人工查看缓存内容
- 需要跨语言共享缓存

```python
cache = FileCacheManager(serializer="json")
cache.set("data", {
    "title": "标题",
    "tags": ["标签1", "标签2"],
    "count": 100
})
```

### Pickle 序列化

**优点**:
- 支持几乎所有 Python 对象
- 可以缓存自定义类实例

**缺点**:
- 二进制格式，不可读
- 仅限 Python 使用
- 安全风险（不要反序列化不可信数据）

**适用场景**:
- 复杂 Python 对象
- 自定义类实例
- 不需要跨语言共享

```python
cache = FileCacheManager(serializer="pickle")

class ContentResult:
    def __init__(self, title, content):
        self.title = title
        self.content = content

result = ContentResult("标题", "内容")
cache.set("result", result)
```

## 使用场景

### 1. 内容生成缓存

```python
cache = FileCacheManager(
    cache_dir="cache/content",
    default_ttl=3600  # 1小时
)

def generate_content(input_text: str) -> dict:
    # 调用 AI API 生成内容
    return api.generate(input_text)

# 使用缓存避免重复调用 API
cache_key = FileCacheManager.generate_key("content", input_text)
result = cache.get_or_set(cache_key, lambda: generate_content(input_text))
```

### 2. 图片 URL 缓存

```python
cache = FileCacheManager(
    cache_dir="cache/images",
    default_ttl=86400  # 24小时
)

def generate_image(prompt: str) -> str:
    # 调用图片生成 API
    return api.generate_image(prompt)

cache_key = FileCacheManager.generate_key("image", prompt)
image_url = cache.get_or_set(cache_key, lambda: generate_image(prompt))
```

### 3. 配置缓存

```python
cache = FileCacheManager(
    cache_dir="cache/config",
    default_ttl=0  # 永不过期
)

# 缓存应用配置
cache.set("app_config", {
    "version": "1.0.0",
    "features": ["content_gen", "image_gen"]
})

# 程序重启后仍可读取
config = cache.get("app_config")
```

### 4. 两级缓存（内存 + 文件）

```python
from src.core.cache_manager import CacheManager, FileCacheManager

# 内存缓存 - 快速但不持久
memory_cache = CacheManager(max_size=100)

# 文件缓存 - 较慢但持久
file_cache = FileCacheManager(cache_dir="cache")

def get_data(key: str):
    # 先查内存缓存
    value = memory_cache.get(key)
    if value is not None:
        return value
    
    # 再查文件缓存
    value = file_cache.get(key)
    if value is not None:
        # 写入内存缓存
        memory_cache.set(key, value)
        return value
    
    # 生成新数据
    value = generate_data(key)
    memory_cache.set(key, value)
    file_cache.set(key, value)
    return value
```

## 全局缓存实例

```python
from src.core.cache_manager import get_global_file_cache, set_global_file_cache

# 获取全局缓存实例（单例模式）
cache = get_global_file_cache()

# 在不同模块中使用同一个实例
cache.set("key", "value")

# 设置自定义全局缓存
custom_cache = FileCacheManager(cache_dir="custom_cache")
set_global_file_cache(custom_cache)
```

## 性能优化建议

### 1. 选择合适的序列化格式

- 简单数据使用 JSON（更快，更小）
- 复杂对象使用 pickle

### 2. 设置合理的 TTL

- 频繁变化的数据：短 TTL（几分钟）
- 稳定的数据：长 TTL（几小时或几天）
- 静态数据：永不过期（ttl=0）

### 3. 控制缓存大小

```python
# 设置合理的最大缓存大小
cache = FileCacheManager(max_size_mb=100.0)

# 定期清理过期缓存
cache.cleanup_expired()
```

### 4. 使用两级缓存

结合内存缓存和文件缓存，平衡速度和持久性。

### 5. 批量操作

```python
# 避免频繁的小文件写入
data_batch = []
for item in items:
    data_batch.append(process(item))

# 一次性写入
cache.set("batch_result", data_batch)
```

## 线程安全

`FileCacheManager` 使用 `threading.RLock` 保证线程安全，可以在多线程环境中安全使用：

```python
import threading

cache = FileCacheManager()

def worker(thread_id):
    for i in range(100):
        key = f"thread{thread_id}_key{i}"
        cache.set(key, f"value{i}")
        cache.get(key)

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## 错误处理

```python
# 序列化失败会返回 False
success = cache.set("key", non_serializable_object)
if not success:
    print("缓存写入失败")

# 读取失败会返回 None
value = cache.get("key")
if value is None:
    print("缓存不存在或读取失败")

# 删除失败会返回 False
if not cache.delete("key"):
    print("键不存在")
```

## 注意事项

1. **Pickle 安全性**: 不要反序列化来自不可信来源的 pickle 数据
2. **磁盘空间**: 注意监控缓存目录的磁盘占用
3. **并发写入**: 虽然线程安全，但大量并发写入可能影响性能
4. **文件系统限制**: 注意文件系统的文件数量限制
5. **缓存键长度**: 使用 `generate_key()` 生成固定长度的哈希键

## 与内存缓存对比

| 特性 | FileCacheManager | CacheManager |
|------|------------------|--------------|
| 持久化 | ✅ 是 | ❌ 否 |
| 速度 | 🐢 较慢（磁盘 I/O） | 🚀 快速（内存） |
| 容量 | 💾 大（受磁盘限制） | 📦 小（受内存限制） |
| 程序重启 | ✅ 数据保留 | ❌ 数据丢失 |
| 线程安全 | ✅ 是 | ✅ 是 |
| TTL 支持 | ✅ 是 | ✅ 是 |
| 序列化 | JSON/Pickle | 无需序列化 |

## 最佳实践

1. **分类存储**: 为不同类型的缓存使用不同的目录
   ```python
   content_cache = FileCacheManager(cache_dir="cache/content")
   image_cache = FileCacheManager(cache_dir="cache/images")
   ```

2. **定期清理**: 设置定时任务清理过期缓存
   ```python
   import schedule
   
   def cleanup_job():
       cache.cleanup_expired()
   
   schedule.every().day.at("03:00").do(cleanup_job)
   ```

3. **监控统计**: 定期检查缓存统计信息
   ```python
   stats = cache.get_stats()
   if stats['hit_rate'] < 0.5:
       print("警告: 缓存命中率过低")
   ```

4. **错误恢复**: 处理缓存失败的情况
   ```python
   value = cache.get(key)
   if value is None:
       value = fallback_function()
       cache.set(key, value)
   ```

## 示例代码

完整的使用示例请参考：
- `examples/file_cache_usage_example.py` - 文件缓存使用示例
- `tests/unit/test_file_cache_manager.py` - 单元测试

## 相关文档

- [内存缓存文档](CACHE.md)
- [配置管理文档](CONFIG.md)
- [日志系统文档](LOGGING.md)
