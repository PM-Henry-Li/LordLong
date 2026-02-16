# 速率限制配置说明

## 概述

速率限制配置用于控制 API 调用的频率，避免超过服务提供商的限额，防止账号被限流或封禁。

## 配置结构

速率限制配置分为两部分：
1. **OpenAI API 速率限制** - 控制文案生成 API 的调用频率
2. **图片生成 API 速率限制** - 控制图片生成 API 的调用频率

## 配置示例

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000,
      "enable_rate_limit": true
    },
    "image": {
      "requests_per_minute": 10,
      "enable_rate_limit": true,
      "max_concurrent": 3
    }
  }
}
```

## OpenAI API 速率限制配置

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `requests_per_minute` | int | 60 | 每分钟最大请求数（1-10000） |
| `tokens_per_minute` | int | 90000 | 每分钟最大令牌数（1-10000000） |
| `enable_rate_limit` | bool | true | 是否启用速率限制 |

### 验证规则

1. **请求数限制**：必须大于 0，不超过 10000
2. **令牌数限制**：必须大于 0，不超过 10000000
3. **比例验证**：平均每个请求的令牌数应在 100-100000 之间
   - 如果比例过低（< 100），说明令牌数配置不足
   - 如果比例过高（> 100000），说明令牌数配置过高

### 使用示例

```python
from src.core.config_schema import OpenAIRateLimitConfig

# 使用默认配置
config = OpenAIRateLimitConfig()

# 自定义配置
config = OpenAIRateLimitConfig(
    requests_per_minute=100,
    tokens_per_minute=150000,
    enable_rate_limit=True
)

# 禁用速率限制（不推荐）
config = OpenAIRateLimitConfig(enable_rate_limit=False)
```

### 推荐配置

根据不同的使用场景，推荐以下配置：

#### 免费账号
```json
{
  "requests_per_minute": 20,
  "tokens_per_minute": 30000,
  "enable_rate_limit": true
}
```

#### 标准账号
```json
{
  "requests_per_minute": 60,
  "tokens_per_minute": 90000,
  "enable_rate_limit": true
}
```

#### 高级账号
```json
{
  "requests_per_minute": 200,
  "tokens_per_minute": 300000,
  "enable_rate_limit": true
}
```

## 图片生成 API 速率限制配置

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `requests_per_minute` | int | 10 | 每分钟最大请求数（1-1000） |
| `enable_rate_limit` | bool | true | 是否启用速率限制 |
| `max_concurrent` | int | 3 | 最大并发请求数（1-20） |

### 验证规则

1. **请求数限制**：必须大于 0，不超过 1000
2. **并发数限制**：必须大于 0，不超过 20
3. **一致性验证**：并发数不应超过每分钟请求数

### 使用示例

```python
from src.core.config_schema import ImageRateLimitConfig

# 使用默认配置
config = ImageRateLimitConfig()

# 自定义配置
config = ImageRateLimitConfig(
    requests_per_minute=20,
    enable_rate_limit=True,
    max_concurrent=5
)

# 禁用速率限制（不推荐）
config = ImageRateLimitConfig(enable_rate_limit=False)
```

### 推荐配置

根据不同的使用场景，推荐以下配置：

#### 免费账号
```json
{
  "requests_per_minute": 5,
  "enable_rate_limit": true,
  "max_concurrent": 2
}
```

#### 标准账号
```json
{
  "requests_per_minute": 10,
  "enable_rate_limit": true,
  "max_concurrent": 3
}
```

#### 高级账号
```json
{
  "requests_per_minute": 30,
  "enable_rate_limit": true,
  "max_concurrent": 5
}
```

## 完整配置示例

### Python 代码

```python
from src.core.config_schema import RateLimitConfig

# 使用默认配置
config = RateLimitConfig()

# 自定义配置
config = RateLimitConfig(
    openai={
        "requests_per_minute": 100,
        "tokens_per_minute": 150000,
        "enable_rate_limit": True
    },
    image={
        "requests_per_minute": 20,
        "enable_rate_limit": True,
        "max_concurrent": 5
    }
)

# 访问配置
print(f"OpenAI 每分钟请求数: {config.openai.requests_per_minute}")
print(f"图片每分钟请求数: {config.image.requests_per_minute}")
print(f"图片最大并发数: {config.image.max_concurrent}")
```

### JSON 配置文件

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000,
      "enable_rate_limit": true
    },
    "image": {
      "requests_per_minute": 10,
      "enable_rate_limit": true,
      "max_concurrent": 3
    }
  }
}
```

## 常见问题

### 1. 如何确定合适的速率限制？

查看 API 服务提供商的文档，了解账号的速率限制。通常：
- 阿里云 DashScope 免费账号：20 次/分钟
- 阿里云 DashScope 标准账号：60 次/分钟
- 通义万相图片生成：10 次/分钟

### 2. 为什么需要设置令牌数限制？

OpenAI API 不仅限制请求数，还限制令牌数。一个请求可能消耗数千个令牌，因此需要同时控制两个指标。

### 3. 并发数和每分钟请求数有什么区别？

- **并发数**：同时进行的请求数量
- **每分钟请求数**：一分钟内总共可以发送的请求数量

例如：`max_concurrent=3` 表示最多同时发送 3 个请求，`requests_per_minute=10` 表示一分钟内最多发送 10 个请求。

### 4. 禁用速率限制会有什么影响？

禁用速率限制可能导致：
- 超过 API 限额，请求被拒绝
- 账号被临时限流或封禁
- 产生额外费用

**不推荐在生产环境中禁用速率限制。**

### 5. 如何调试速率限制问题？

1. 启用日志记录，查看实际的 API 调用频率
2. 逐步降低速率限制配置，找到稳定值
3. 监控 API 响应，查看是否有限流错误（HTTP 429）

## 最佳实践

1. **保守配置**：初始配置应低于 API 限额的 80%，留有余地
2. **监控调整**：根据实际使用情况和错误日志调整配置
3. **分级配置**：为不同环境（开发、测试、生产）设置不同的限制
4. **启用限流**：始终启用速率限制，避免意外超额
5. **合理并发**：图片生成并发数不宜过高，建议 3-5 个

## 相关文档

- [配置管理器文档](./README.md)
- [配置模式定义](./config_schema.py)
- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
