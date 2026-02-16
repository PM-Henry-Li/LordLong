# 速率限制策略使用指南

## 概述

`rate_limiter.py` 模块提供了四种不同的速率限制策略，每种策略都有其特定的使用场景和特点。

## 支持的策略

### 1. 令牌桶算法（Token Bucket）

**原理**：
- 令牌以固定速率生成并放入桶中
- 桶有最大容量限制
- 请求需要消耗令牌才能执行
- 如果桶中没有足够的令牌，请求需要等待

**特点**：
- ✅ 允许突发流量（桶满时可以一次性消耗多个令牌）
- ✅ 平滑限流（长期平均速率受控）
- ✅ 线程安全
- ⚠️ 可能出现短时间内的流量突发

**适用场景**：
- 需要允许短时间突发流量的场景
- API 调用限流（如 OpenAI API）
- 网络请求限流

**使用示例**：

```python
from src.core.rate_limiter import RateLimiter, create_rate_limiter

# 方式1：直接创建
limiter = RateLimiter(rate=10, capacity=20)  # 每秒生成10个令牌，容量20

# 方式2：使用工厂函数
limiter = create_rate_limiter("token_bucket", rate=10, capacity=20)

# 获取令牌（非阻塞）
if limiter.acquire(1):
    print("获取令牌成功")
else:
    print("令牌不足")

# 等待获取令牌（阻塞）
limiter.wait_for_token(1, timeout=5.0)  # 最多等待5秒

# 查看可用令牌数
print(f"可用令牌: {limiter.get_available_tokens()}")
```

### 2. 固定窗口算法（Fixed Window）

**原理**：
- 将时间划分为固定大小的窗口（如 1 分钟）
- 每个窗口内允许固定数量的请求
- 窗口结束时，计数器重置

**特点**：
- ✅ 实现简单，内存占用小
- ⚠️ 存在临界问题：窗口边界处可能出现突发流量
- ⚠️ 精确度较低

**临界问题示例**：
```
限制：每分钟 60 次请求，窗口大小 60 秒

时间轴：
00:59 秒 -> 发送 60 次请求 ✅
01:00 秒 -> 窗口重置
01:01 秒 -> 发送 60 次请求 ✅

结果：在 2 秒内实际发送了 120 次请求！
```

**适用场景**：
- 对精确度要求不高的场景
- 需要简单实现的场景
- 内存受限的场景

**使用示例**：

```python
from src.core.rate_limiter import FixedWindowRateLimiter, create_rate_limiter

# 方式1：直接创建
limiter = FixedWindowRateLimiter(rate=100, window_size=60)  # 每60秒允许100次请求

# 方式2：使用工厂函数
limiter = create_rate_limiter("fixed_window", rate=100, window_size=60)

# 使用方式与令牌桶相同
if limiter.acquire(1):
    print("请求通过")

# 查看当前窗口剩余配额
print(f"剩余配额: {limiter.get_available_tokens()}")
```

### 3. 滑动窗口算法（Sliding Window）

**原理**：
- 记录每次请求的时间戳
- 检查时，统计窗口时间内的请求数
- 移除过期的请求记录

**特点**：
- ✅ 精确控制速率，无临界问题
- ✅ 平滑限流
- ⚠️ 内存占用与请求数成正比
- ⚠️ 性能略低于固定窗口

**与固定窗口的对比**：
```
限制：每分钟 60 次请求，窗口大小 60 秒

滑动窗口：
- 无论何时检查，都只统计最近 60 秒内的请求数
- 不会出现固定窗口的临界问题
- 更精确的速率控制
```

**适用场景**：
- 对精确度要求高的场景
- 需要严格控制速率的场景
- 可以接受较高内存占用的场景

**使用示例**：

```python
from src.core.rate_limiter import SlidingWindowRateLimiter, create_rate_limiter

# 方式1：直接创建
limiter = SlidingWindowRateLimiter(rate=100, window_size=60)  # 每60秒允许100次请求

# 方式2：使用工厂函数
limiter = create_rate_limiter("sliding_window", rate=100, window_size=60)

# 使用方式与其他策略相同
if limiter.acquire(1):
    print("请求通过")

# 查看当前窗口剩余配额
print(f"剩余配额: {limiter.get_available_tokens()}")
```

### 4. 漏桶算法（Leaky Bucket）

**原理**：
- 请求进入漏桶（队列）
- 漏桶以固定速率处理请求
- 如果漏桶满了，新请求被拒绝

**特点**：
- ✅ 强制固定速率输出，平滑流量
- ✅ 不允许突发流量
- ⚠️ 可能导致请求延迟

**与令牌桶的区别**：
- **令牌桶**：允许突发流量（桶满时可以一次性消耗多个令牌）
- **漏桶**：不允许突发流量（严格按照固定速率处理）

**适用场景**：
- 需要严格控制速率的场景
- 不允许突发流量的场景
- 需要平滑流量的场景

**使用示例**：

```python
from src.core.rate_limiter import LeakyBucketRateLimiter, create_rate_limiter

# 方式1：直接创建
limiter = LeakyBucketRateLimiter(rate=10, capacity=20)  # 每秒处理10个请求，容量20

# 方式2：使用工厂函数
limiter = create_rate_limiter("leaky_bucket", rate=10, capacity=20)

# 使用方式与其他策略相同
if limiter.acquire(1):
    print("请求加入队列")

# 查看队列大小
print(f"队列大小: {limiter.get_queue_size()}")
print(f"剩余空间: {limiter.get_available_tokens()}")
```

## 多速率限制器（MultiRateLimiter）

`MultiRateLimiter` 允许管理多个不同的速率限制器，每个限制器可以使用不同的策略。

**使用示例**：

```python
from src.core.rate_limiter import MultiRateLimiter

# 创建多速率限制器
multi = MultiRateLimiter()

# 为不同的 API 添加不同策略的限制器
multi.add_limiter(
    name="openai_api",
    rate=60,
    window_size=60,
    strategy="sliding_window"  # 使用滑动窗口，精确控制
)

multi.add_limiter(
    name="image_api",
    rate=10,
    capacity=20,
    strategy="token_bucket"  # 使用令牌桶，允许突发
)

multi.add_limiter(
    name="web_api",
    rate=100,
    window_size=60,
    strategy="fixed_window"  # 使用固定窗口，简单高效
)

# 使用不同的限制器
if multi.acquire("openai_api", 1):
    print("OpenAI API 请求通过")

if multi.acquire("image_api", 1):
    print("图片 API 请求通过")

# 等待获取令牌
multi.wait_for_token("web_api", 1, timeout=5.0)

# 获取限制器实例
openai_limiter = multi.get_limiter("openai_api")
print(f"OpenAI API 剩余配额: {openai_limiter.get_available_tokens()}")
```

## 策略选择指南

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| API 调用限流（允许突发） | 令牌桶 | 允许短时间突发，长期平均速率受控 |
| API 调用限流（严格控制） | 滑动窗口 | 精确控制速率，无临界问题 |
| 简单场景（内存受限） | 固定窗口 | 实现简单，内存占用小 |
| 流量整形（平滑输出） | 漏桶 | 强制固定速率，平滑流量 |
| 需要精确控制 | 滑动窗口 | 最精确的速率控制 |
| 需要高性能 | 令牌桶或固定窗口 | 性能较好 |

## 性能对比

| 策略 | 内存占用 | CPU 占用 | 精确度 | 是否允许突发 |
|------|---------|---------|--------|-------------|
| 令牌桶 | 低 | 低 | 中 | ✅ |
| 固定窗口 | 低 | 低 | 低 | ⚠️（临界问题） |
| 滑动窗口 | 高 | 中 | 高 | ❌ |
| 漏桶 | 中 | 低 | 高 | ❌ |

## 配置示例

在 `config.json` 中配置不同的限流策略：

```json
{
  "rate_limit": {
    "openai": {
      "strategy": "sliding_window",
      "requests_per_minute": 60,
      "window_size": 60
    },
    "image": {
      "strategy": "token_bucket",
      "requests_per_minute": 10,
      "capacity": 20
    },
    "web": {
      "strategy": "fixed_window",
      "requests_per_minute": 100,
      "window_size": 60
    }
  }
}
```

## 最佳实践

1. **选择合适的策略**：根据业务需求选择合适的限流策略
2. **合理设置参数**：根据 API 限制和业务需求设置速率和容量
3. **监控和调整**：监控限流效果，根据实际情况调整参数
4. **错误处理**：处理限流导致的请求失败，提供友好的错误提示
5. **日志记录**：记录限流事件，便于分析和优化

## 常见问题

### Q: 如何选择令牌桶和漏桶？

**A**: 
- 如果需要允许突发流量，选择**令牌桶**
- 如果需要严格平滑流量，选择**漏桶**

### Q: 固定窗口和滑动窗口有什么区别？

**A**:
- **固定窗口**：简单高效，但存在临界问题
- **滑动窗口**：精确控制，无临界问题，但内存占用较高

### Q: 如何处理限流导致的请求失败？

**A**:
```python
# 方式1：非阻塞，立即返回
if not limiter.acquire(1):
    # 请求被限流，返回错误
    return {"error": "请求过于频繁，请稍后再试"}

# 方式2：阻塞等待（带超时）
if not limiter.wait_for_token(1, timeout=5.0):
    # 等待超时，返回错误
    return {"error": "服务繁忙，请稍后再试"}

# 方式3：重试机制
max_retries = 3
for i in range(max_retries):
    if limiter.acquire(1):
        # 执行请求
        break
    time.sleep(1)  # 等待1秒后重试
else:
    return {"error": "请求失败，请稍后再试"}
```

## 参考资料

- [令牌桶算法 - Wikipedia](https://en.wikipedia.org/wiki/Token_bucket)
- [漏桶算法 - Wikipedia](https://en.wikipedia.org/wiki/Leaky_bucket)
- [Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
