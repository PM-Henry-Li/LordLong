# 缓存管理器使用文档

## 概述

`CacheManager` 是一个基于 LRU（最近最少使用）策略的内存缓存管理器，提供高效的缓存功能。

## 主要特性

- ✅ **LRU 淘汰策略**: 自动淘汰最久未使用的缓存条目
- ✅ **TTL 支持**: 支持设置缓存过期时间
- ✅ **线程安全**: 所有操作都是线程安全的
- ✅ **统计信息**: 提供命中率、淘汰次数等统计数据
- ✅ **灵活配置**: 可配置最大容量和默认 TTL
- ✅ **键生成工具**: 提供便捷的缓存键生成方法

## 快速开始

### 基本使用

```python
from src.core.cache_manager import CacheManager

# 创建缓存管理器
cache = CacheManager(max_size=1000, default_ttl=3600)

# 设置缓存
cache.set("user:123", {"name": "张三", "age": 25})

# 获取缓存
user = cache.get("user:123")
print(user)  # {'name': '张三', 'age': 25}

# 检查是否存在
if "user:123" in cache:
    print("用户存在")

# 删除缓存
cache.delete("user:123")

# 清空所有缓存
cache.clear()
```

### 使用全局缓存

```python
from src.core.cache_manager import get_global_cache

# 获取全局缓存实例（单例）
cache = get_global_cache()

# 在任何地方都可以获取同一个实例
cache.set("config", {"version": "1.0.0"})
```

## API 参考

### 初始化

```python
cache = CacheManager(max_size=1000, default_ttl=3600)
```

**参数**:
- `max_size` (int): 缓存最大条目数，默认 1000
- `default_ttl` (int|None): 默认过期时间（秒），None 表示永不过期，默认 3600

### 核心方法

#### get(key: str) -> Optional[Any]

获取缓存值。

```python
value = cache.get("key1")
```

**返回**: 缓存值，如果不存在或已过期则返回 `None`

#### set(key: str, value: Any, ttl: Optional[int] = None) -> None

设置缓存值。

```python
# 使用默认 TTL
cache.set("key1", "value1")

# 自定义 TTL（5 分钟）
cache.set("key2", "value2", ttl=300)

# 永不过期
cache.set("key3", "value3", ttl=0)
```

**参数**:
- `key`: 缓存键
- `value`: 缓存值（任意类型）
- `ttl`: 过期时间（秒），`None` 使用默认 TTL，`0` 表示永不过期

#### delete(key: str) -> bool

删除缓存条目。

```python
success = cache.delete("key1")
```

**返回**: `True` 表示存在并已删除，`False` 表示不存在

#### clear() -> None

清空所有缓存。

```python
cache.clear()
```

#### exists(key: str) -> bool

检查缓存键是否存在且未过期。

```python
if cache.exists("key1"):
    print("存在")
```

#### get_or_set(key: str, factory: callable, ttl: Optional[int] = None) -> Any

获取缓存值，如果不存在则通过工厂函数生成并缓存。

```python
def generate_data():
    # 耗时操作
    return expensive_computation()

# 第一次调用会执行 generate_data
value = cache.get_or_set("key1", generate_data)

# 第二次调用直接返回缓存值
value = cache.get_or_set("key1", generate_data)
```

### 统计方法

#### get_stats() -> Dict[str, Any]

获取缓存统计信息。

```python
stats = cache.get_stats()
print(stats)
# {
#     'size': 10,           # 当前条目数
#     'max_size': 1000,     # 最大容量
#     'hits': 50,           # 命中次数
#     'misses': 10,         # 未命中次数
#     'hit_rate': 0.833,    # 命中率
#     'evictions': 5        # 淘汰次数
# }
```

#### cleanup_expired() -> int

清理所有过期的缓存条目。

```python
cleaned = cache.cleanup_expired()
print(f"清理了 {cleaned} 个过期条目")
```

### 工具方法

#### generate_key(prefix: str, *args, **kwargs) -> str

生成缓存键（使用 SHA256 哈希）。

```python
# 基本用法
key = CacheManager.generate_key("user", "123")

# 使用多个参数
key = CacheManager.generate_key("content", input_text, style="retro")

# 使用字典参数（自动排序保证一致性）
key = CacheManager.generate_key("image", {"prompt": "老北京", "size": "1024x1024"})
```

## 使用场景

### 1. 内容生成缓存

避免重复调用 AI API，节省时间和成本。

```python
from src.core.cache_manager import CacheManager

cache = CacheManager(default_ttl=3600)  # 1 小时

def generate_content(input_text: str) -> dict:
    # 生成缓存键
    cache_key = CacheManager.generate_key("content", input_text)
    
    # 尝试从缓存获取
    result = cache.get(cache_key)
    if result is not None:
        return result
    
    # 调用 AI API 生成内容
    result = call_openai_api(input_text)
    
    # 缓存结果
    cache.set(cache_key, result)
    return result
```

或者使用更简洁的方式：

```python
def generate_content(input_text: str) -> dict:
    cache_key = CacheManager.generate_key("content", input_text)
    return cache.get_or_set(cache_key, lambda: call_openai_api(input_text))
```

### 2. 图片 URL 缓存

缓存已生成的图片 URL，避免重复生成。

```python
cache = CacheManager(default_ttl=86400)  # 24 小时

def generate_image(prompt: str) -> str:
    cache_key = CacheManager.generate_key("image", prompt)
    return cache.get_or_set(cache_key, lambda: call_image_api(prompt))
```

### 3. 配置缓存

缓存频繁访问的配置数据。

```python
from src.core.cache_manager import get_global_cache

def get_app_config() -> dict:
    cache = get_global_cache()
    return cache.get_or_set("app_config", load_config_from_file, ttl=0)
```

### 4. 搜索结果缓存

缓存小红书搜索结果。

```python
cache = CacheManager(default_ttl=1800)  # 30 分钟

def search_xiaohongshu(keyword: str) -> list:
    cache_key = CacheManager.generate_key("search", keyword)
    return cache.get_or_set(cache_key, lambda: perform_search(keyword))
```

## 性能优化建议

### 1. 合理设置容量

根据应用需求设置合适的 `max_size`：

```python
# 小型应用
cache = CacheManager(max_size=100)

# 中型应用
cache = CacheManager(max_size=1000)

# 大型应用
cache = CacheManager(max_size=10000)
```

### 2. 合理设置 TTL

根据数据特性设置合适的过期时间：

```python
# 短期数据（5 分钟）
cache.set("temp_data", data, ttl=300)

# 中期数据（1 小时）
cache.set("content", data, ttl=3600)

# 长期数据（24 小时）
cache.set("image_url", url, ttl=86400)

# 永久数据
cache.set("config", config, ttl=0)
```

### 3. 定期清理过期条目

在后台任务中定期清理过期条目：

```python
import threading
import time

def cleanup_task(cache: CacheManager, interval: int = 300):
    """每 5 分钟清理一次过期条目"""
    while True:
        time.sleep(interval)
        cleaned = cache.cleanup_expired()
        print(f"清理了 {cleaned} 个过期条目")

# 启动清理任务
cache = CacheManager()
thread = threading.Thread(target=cleanup_task, args=(cache,), daemon=True)
thread.start()
```

### 4. 监控缓存性能

定期检查缓存统计信息：

```python
stats = cache.get_stats()
print(f"缓存命中率: {stats['hit_rate']:.2%}")
print(f"缓存使用率: {stats['size']}/{stats['max_size']}")

# 如果命中率过低，考虑：
# 1. 增加缓存容量
# 2. 延长 TTL
# 3. 优化缓存键生成策略
```

## 线程安全

`CacheManager` 的所有操作都是线程安全的，可以在多线程环境中安全使用：

```python
import threading

cache = CacheManager()

def worker(thread_id: int):
    for i in range(100):
        key = f"thread{thread_id}_key{i}"
        cache.set(key, f"value{i}")
        value = cache.get(key)

# 创建多个线程
threads = []
for i in range(10):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

## 注意事项

1. **内存使用**: 缓存存储在内存中，注意控制 `max_size` 避免内存溢出
2. **序列化**: 缓存值不会被序列化，重启应用后缓存会丢失
3. **过期检查**: 过期条目在访问时才会被删除，建议定期调用 `cleanup_expired()`
4. **键冲突**: 使用 `generate_key()` 生成键可以避免冲突
5. **全局缓存**: 使用全局缓存时注意键命名规范，避免不同模块间的键冲突

## 与 ConfigManager 集成

可以通过 `ConfigManager` 配置缓存参数：

```python
from src.core.config_manager import ConfigManager
from src.core.cache_manager import CacheManager

config = ConfigManager()

# 从配置读取缓存参数
cache_config = config.get("cache", {})
cache = CacheManager(
    max_size=cache_config.get("max_size", 1000),
    default_ttl=cache_config.get("ttl", 3600)
)
```

配置文件示例（`config/config.json`）：

```json
{
  "cache": {
    "enabled": true,
    "max_size": 1000,
    "ttl": 3600
  }
}
```

## 完整示例

查看 `examples/cache_usage_example.py` 获取更多使用示例。

运行示例：

```bash
python3 examples/cache_usage_example.py
```

## 测试

运行单元测试：

```bash
python3 tests/unit/test_cache_manager.py
```

## 相关文档

- [配置管理文档](CONFIG.md)
- [日志系统文档](LOGGING.md)
