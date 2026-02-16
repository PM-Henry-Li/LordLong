# 速率限制器使用文档

## 概述

速率限制器（RateLimiter）基于令牌桶算法实现，用于控制 API 调用频率，防止超过服务提供商的速率限制。

## 令牌桶算法原理

令牌桶算法是一种常用的流量控制算法：

1. **令牌生成**：令牌以固定速率生成并放入桶中
2. **桶容量限制**：桶有最大容量，令牌数不会超过容量
3. **令牌消耗**：每次请求需要消耗一定数量的令牌
4. **等待机制**：如果令牌不足，请求需要等待

### 特点

- ✅ **允许突发流量**：桶满时可以一次性处理多个请求
- ✅ **平滑限流**：长期平均速率受控
- ✅ **线程安全**：支持多线程并发访问
- ✅ **灵活配置**：可独立配置速率和容量

## 基本使用

### 1. 创建速率限制器

```python
from src.core.rate_limiter import RateLimiter

# 创建限制器：每秒生成 10 个令牌，容量为 20
limiter = RateLimiter(rate=10, capacity=20)

# 如果不指定容量，默认等于速率
limiter = RateLimiter(rate=10)  # 容量也是 10
```

### 2. 获取令牌（非阻塞）

```python
# 尝试获取 1 个令牌
if limiter.acquire(1):
    print("✅ 获取成功，可以执行请求")
    # 执行 API 调用
else:
    print("❌ 令牌不足，请稍后重试")
```

### 3. 等待获取令牌（阻塞）

```python
# 等待直到获取到令牌（无限等待）
limiter.wait_for_token(1)
print("✅ 获取到令牌")

# 设置超时时间
if limiter.wait_for_token(1, timeout=5.0):
    print("✅ 获取到令牌")
else:
    print("❌ 等待超时")
```

### 4. 查询状态

```python
# 获取当前可用令牌数
tokens = limiter.get_available_tokens()
print(f"可用令牌: {tokens:.2f}")

# 获取速率和容量
print(f"速率: {limiter.get_rate()}/秒")
print(f"容量: {limiter.get_capacity()}")
```

### 5. 重置限制器

```python
# 重置为满容量
limiter.reset()
```

## 高级使用

### 管理多个 API 的速率限制

使用 `MultiRateLimiter` 可以方便地管理多个不同的速率限制器：

```python
from src.core.rate_limiter import MultiRateLimiter

# 创建多速率限制器
multi = MultiRateLimiter()

# 为不同的 API 添加限制器
multi.add_limiter("openai", rate=60, capacity=60)    # 每秒 60 次
multi.add_limiter("image", rate=10, capacity=10)     # 每秒 10 次
multi.add_limiter("search", rate=30, capacity=30)    # 每秒 30 次

# 从指定限制器获取令牌
if multi.acquire("openai", 1):
    print("✅ OpenAI API 调用成功")

# 等待获取令牌
multi.wait_for_token("image", 1)
print("✅ 图片生成 API 调用成功")

# 列出所有限制器
limiters = multi.list_limiters()
print(f"已配置的限制器: {limiters}")

# 移除限制器
multi.remove_limiter("search")
```

### 结合配置管理器使用

```python
from src.core.config_manager import ConfigManager
from src.core.rate_limiter import MultiRateLimiter

# 加载配置
config = ConfigManager()

# 从配置创建速率限制器
openai_rpm = config.get("rate_limit.openai.requests_per_minute", 60)
image_rpm = config.get("rate_limit.image.requests_per_minute", 10)

# 创建多速率限制器
multi = MultiRateLimiter()

# 将每分钟的速率转换为每秒
multi.add_limiter("openai", rate=openai_rpm/60, capacity=openai_rpm/60)
multi.add_limiter("image", rate=image_rpm/60, capacity=image_rpm/60)
```

## 实际应用示例

### 示例 1: API 调用包装

```python
from src.core.rate_limiter import RateLimiter
import requests

class APIClient:
    def __init__(self, rate_limit=10):
        self.limiter = RateLimiter(rate=rate_limit)
    
    def call_api(self, url, **kwargs):
        """带速率限制的 API 调用"""
        # 等待获取令牌
        self.limiter.wait_for_token(1)
        
        # 执行请求
        response = requests.get(url, **kwargs)
        return response

# 使用
client = APIClient(rate_limit=10)  # 每秒最多 10 次请求
response = client.call_api("https://api.example.com/data")
```

### 示例 2: 批量处理

```python
from src.core.rate_limiter import RateLimiter

def process_batch(items, rate_limit=5):
    """批量处理，带速率限制"""
    limiter = RateLimiter(rate=rate_limit)
    results = []
    
    for item in items:
        # 等待令牌
        limiter.wait_for_token(1)
        
        # 处理项目
        result = process_item(item)
        results.append(result)
    
    return results

# 使用
items = ["item1", "item2", "item3", ...]
results = process_batch(items, rate_limit=5)  # 每秒处理 5 个
```

### 示例 3: 突发流量处理

```python
from src.core.rate_limiter import RateLimiter

# 创建限制器：每秒生成 2 个令牌，但容量为 10
# 这允许短时间内处理突发流量
limiter = RateLimiter(rate=2, capacity=10)

# 处理突发请求
if limiter.acquire(8):  # 一次性处理 8 个请求
    print("✅ 处理突发流量")
else:
    print("❌ 令牌不足")
```

## 配置说明

在 `config/config.json` 中配置速率限制：

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000
    },
    "image": {
      "requests_per_minute": 10
    }
  }
}
```

也可以通过环境变量配置：

```bash
export RATE_LIMIT_OPENAI_RPM=60
export RATE_LIMIT_OPENAI_TPM=90000
export RATE_LIMIT_IMAGE_RPM=10
```

## 性能考虑

### 速率和容量的选择

- **速率（rate）**：决定长期平均速率
  - 设置为 API 提供商的限制值
  - 例如：60 次/分钟 = 1 次/秒

- **容量（capacity）**：决定突发流量处理能力
  - 容量越大，允许的突发流量越大
  - 建议设置为速率的 1-2 倍
  - 例如：速率 10/秒，容量可设为 10-20

### 线程安全

RateLimiter 使用 `threading.RLock` 保证线程安全，可以在多线程环境中安全使用：

```python
import threading
from src.core.rate_limiter import RateLimiter

limiter = RateLimiter(rate=10)

def worker():
    for _ in range(100):
        limiter.wait_for_token(1)
        # 执行任务

# 创建多个线程
threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## 常见问题

### Q: 如何处理不同的 API 限制？

A: 使用 `MultiRateLimiter` 为每个 API 创建独立的限制器。

### Q: 如何处理令牌和请求的限制？

A: 创建两个限制器，分别控制请求数和令牌数：

```python
request_limiter = RateLimiter(rate=60)  # 60 请求/分钟
token_limiter = RateLimiter(rate=90000)  # 90000 令牌/分钟

# 使用时同时检查两个限制器
request_limiter.wait_for_token(1)
token_limiter.wait_for_token(estimated_tokens)
```

### Q: 如何动态调整速率？

A: 创建新的限制器实例：

```python
# 方法 1: 创建新实例
limiter = RateLimiter(rate=new_rate)

# 方法 2: 使用 MultiRateLimiter 动态替换
multi.remove_limiter("api")
multi.add_limiter("api", rate=new_rate)
```

## 最佳实践

1. **合理设置容量**：容量应该略大于速率，以处理突发流量
2. **使用超时**：在 `wait_for_token` 中设置合理的超时时间
3. **错误处理**：捕获 `ValueError` 异常，处理无效参数
4. **监控统计**：定期检查 `get_available_tokens()` 了解使用情况
5. **配置化管理**：将速率限制配置放在配置文件中，便于调整

## 参考资料

- [令牌桶算法 - Wikipedia](https://en.wikipedia.org/wiki/Token_bucket)
- [速率限制策略文档](RATE_LIMITER_STRATEGIES.md)
- [内容生成器速率限制文档](CONTENT_GENERATOR_RATE_LIMIT.md)
- [图片生成器速率限制文档](IMAGE_GENERATOR_RATE_LIMIT.md)
- [API 速率限制最佳实践](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [阿里云 DashScope API 限制](https://help.aliyun.com/document_detail/2712195.html)
