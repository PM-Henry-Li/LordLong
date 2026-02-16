# 速率限制模块更新说明

## 更新内容

本次更新为 `src/core/rate_limiter.py` 模块添加了多种限流策略支持，提供更灵活的速率控制选项。

## 新增功能

### 1. 基类抽象（BaseRateLimiter）

新增 `BaseRateLimiter` 抽象基类，定义了所有速率限制器的统一接口：
- `acquire(tokens)` - 非阻塞获取令牌
- `wait_for_token(tokens, timeout)` - 阻塞等待获取令牌
- `get_available_tokens()` - 获取可用令牌数
- `reset()` - 重置限制器

### 2. 新增限流策略

#### 固定窗口算法（FixedWindowRateLimiter）
- 将时间划分为固定窗口
- 每个窗口内允许固定数量的请求
- 实现简单，内存占用小
- 适用于对精确度要求不高的场景

#### 滑动窗口算法（SlidingWindowRateLimiter）
- 记录每次请求的时间戳
- 精确统计窗口时间内的请求数
- 无临界问题，精确控制速率
- 适用于对精确度要求高的场景

#### 漏桶算法（LeakyBucketRateLimiter）
- 请求进入队列，以固定速率处理
- 强制固定速率输出，平滑流量
- 不允许突发流量
- 适用于需要严格控制速率的场景

### 3. 工厂函数（create_rate_limiter）

新增工厂函数，方便创建不同策略的限制器：

```python
from src.core.rate_limiter import create_rate_limiter

# 创建令牌桶限制器
limiter = create_rate_limiter("token_bucket", rate=10, capacity=20)

# 创建固定窗口限制器
limiter = create_rate_limiter("fixed_window", rate=100, window_size=60)

# 创建滑动窗口限制器
limiter = create_rate_limiter("sliding_window", rate=100, window_size=60)

# 创建漏桶限制器
limiter = create_rate_limiter("leaky_bucket", rate=10, capacity=20)
```

### 4. 增强的 MultiRateLimiter

`MultiRateLimiter` 现在支持为不同资源配置不同的限流策略：

```python
from src.core.rate_limiter import MultiRateLimiter

multi = MultiRateLimiter()

# 为不同 API 配置不同策略
multi.add_limiter("openai", rate=60, window_size=60, strategy="sliding_window")
multi.add_limiter("image", rate=10, capacity=20, strategy="token_bucket")
multi.add_limiter("web", rate=100, window_size=60, strategy="fixed_window")
```

## 向后兼容性

✅ 完全向后兼容！

- 原有的 `RateLimiter` 类（令牌桶算法）保持不变
- 原有的 `MultiRateLimiter` 接口保持不变
- 所有现有代码无需修改即可继续使用

## 测试覆盖

新增了完整的单元测试：
- `tests/unit/test_rate_limiter_strategies.py` - 新策略的测试（37个测试用例）
- `tests/unit/test_rate_limiter.py` - 原有测试保持通过（27个测试用例）

测试覆盖率：
- 固定窗口算法：100%
- 滑动窗口算法：100%
- 漏桶算法：100%
- 工厂函数：100%
- MultiRateLimiter 增强：100%

## 使用建议

### 策略选择

| 场景 | 推荐策略 |
|------|---------|
| OpenAI API 调用 | 滑动窗口（精确控制） |
| 图片生成 API | 令牌桶（允许突发） |
| Web 接口限流 | 固定窗口（简单高效） |
| 流量整形 | 漏桶（平滑输出） |

### 配置示例

```python
from src.core.rate_limiter import MultiRateLimiter

# 创建多速率限制器
rate_limiters = MultiRateLimiter()

# OpenAI API：使用滑动窗口，精确控制每分钟60次
rate_limiters.add_limiter(
    name="openai",
    rate=60,
    window_size=60,
    strategy="sliding_window"
)

# 图片 API：使用令牌桶，允许突发，每秒10次，容量20
rate_limiters.add_limiter(
    name="image",
    rate=10,
    capacity=20,
    strategy="token_bucket"
)

# 使用
if rate_limiters.acquire("openai", 1):
    # 调用 OpenAI API
    pass
```

## 性能影响

- **令牌桶**：性能最好，内存占用最小
- **固定窗口**：性能好，内存占用小
- **滑动窗口**：性能中等，内存占用与请求数成正比
- **漏桶**：性能好，内存占用中等

对于大多数场景，性能差异可以忽略不计。

## 文档

详细文档请参考：
- [速率限制策略使用指南](./RATE_LIMITER_STRATEGIES.md)

## 相关任务

- ✅ 任务 6.1.1：实现令牌桶算法（已完成）
- ✅ 任务 6.1.2：支持多种限流策略（本次更新）
- ⏳ 任务 6.1.3：实现分布式限流（待实现）
- ⏳ 任务 6.1.4：添加限流统计（待实现）

## 下一步计划

1. 集成到 API 调用模块
2. 添加限流统计和监控
3. 实现分布式限流（可选）
4. 添加限流告警机制
