# 图片生成器速率限制文档

## 概述

图片生成器速率限制功能用于控制图片生成 API 的调用频率，避免超过 API 配额限制，确保系统稳定运行。

## 功能特性

- ✅ 令牌桶算法实现
- ✅ 支持每分钟请求数（RPM）限制
- ✅ 自动等待机制
- ✅ 与缓存功能无缝集成
- ✅ 实时统计监控
- ✅ 灵活的配置方式

## 快速开始

### 1. 启用速率限制

在 `config/config.json` 中配置：

```json
{
  "rate_limit": {
    "image": {
      "enable_rate_limit": true,
      "requests_per_minute": 10
    }
  }
}
```

### 2. 使用示例

```python
from src.image_generator import ImageGenerator
from src.core.config_manager import ConfigManager

# 创建配置和生成器
config = ConfigManager()
generator = ImageGenerator(config_manager=config)

# 生成图片（自动应用速率限制）
image_url = generator.generate_single_image(
    prompt="一张老北京胡同的照片",
    size="1024*1365"
)
```

## 配置说明

### 配置文件方式

在 `config/config.json` 中配置：

```json
{
  "rate_limit": {
    "image": {
      "enable_rate_limit": true,
      "requests_per_minute": 10
    }
  }
}
```

**配置项说明**：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_rate_limit` | boolean | `true` | 是否启用速率限制 |
| `requests_per_minute` | integer | `10` | 每分钟最大请求数 |

### 环境变量方式

```bash
# 启用速率限制
export RATE_LIMIT_IMAGE_ENABLE_RATE_LIMIT=true

# 设置每分钟请求数
export RATE_LIMIT_IMAGE_RPM=10
```

### 程序化配置

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.set('rate_limit.image.enable_rate_limit', True)
config.set('rate_limit.image.requests_per_minute', 10)
```

## 工作原理

### 令牌桶算法

速率限制器使用令牌桶算法实现：

1. **令牌生成**：以固定速率（RPM/60）生成令牌并放入桶中
2. **令牌消耗**：每次 API 调用消耗 1 个令牌
3. **桶容量限制**：桶的最大容量为 RPM 值
4. **等待机制**：如果令牌不足，自动等待直到获取到令牌

### 集成点

速率限制在以下方法中自动应用：

- `generate_image_async()` - 异步图片生成
- `generate_single_image()` - 单张图片生成
- `generate_image_sync()` - 同步图片生成

### 与缓存的协作

- **缓存命中**：直接返回缓存结果，不消耗速率限制令牌
- **缓存未命中**：调用 API 生成图片，消耗 1 个令牌

## API 参考

### ImageGenerator 类

#### 初始化

```python
generator = ImageGenerator(config_manager=config)
```

速率限制器在初始化时自动创建（如果启用）。

#### 获取速率限制统计

```python
stats = generator.get_rate_limit_stats()

# 返回示例
{
    "enabled": True,
    "rpm": {
        "available_tokens": 10.0,
        "capacity": 10.0,
        "rate": 0.1667
    }
}
```

**返回值说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | boolean | 速率限制是否启用 |
| `rpm.available_tokens` | float | 当前可用令牌数 |
| `rpm.capacity` | float | 令牌桶容量 |
| `rpm.rate` | float | 令牌生成速率（令牌/秒） |

#### 生成图片（带速率限制）

```python
# 异步生成
image_url = generator.generate_image_async(
    prompt="提示词",
    index=1,
    is_cover=False
)

# 单张生成
image_url = generator.generate_single_image(
    prompt="提示词",
    size="1024*1365"
)

# 同步生成
image_url = generator.generate_image_sync(
    prompt="提示词",
    size="1024*1365"
)
```

所有方法都会自动应用速率限制。

## 使用场景

### 场景 1: 基本使用

```python
from src.image_generator import ImageGenerator
from src.core.config_manager import ConfigManager

# 创建生成器
config = ConfigManager()
generator = ImageGenerator(config_manager=config)

# 生成图片（自动限流）
for i in range(5):
    image_url = generator.generate_single_image(
        prompt=f"图片 {i+1}",
        size="1024*1365"
    )
    print(f"生成成功: {image_url}")
```

### 场景 2: 监控速率限制状态

```python
# 获取统计信息
stats = generator.get_rate_limit_stats()

if stats:
    print(f"可用令牌: {stats['rpm']['available_tokens']}")
    print(f"桶容量: {stats['rpm']['capacity']}")
    print(f"生成速率: {stats['rpm']['rate']} 令牌/秒")
    
    # 计算使用率
    usage = (stats['rpm']['capacity'] - stats['rpm']['available_tokens']) / stats['rpm']['capacity']
    print(f"使用率: {usage * 100:.1f}%")
```

### 场景 3: 批量生成

```python
prompts = [
    "老北京胡同",
    "故宫太和殿",
    "天坛祈年殿",
    "颐和园长廊",
    "北海公园白塔"
]

results = []
for prompt in prompts:
    try:
        # 自动应用速率限制
        image_url = generator.generate_single_image(
            prompt=prompt,
            size="1024*1365"
        )
        results.append(image_url)
        print(f"✅ {prompt}: {image_url}")
    except TimeoutError:
        print(f"❌ {prompt}: 速率限制超时")
    except Exception as e:
        print(f"❌ {prompt}: {e}")
```

### 场景 4: 与缓存结合

```python
# 启用缓存和速率限制
config = ConfigManager()
generator = ImageGenerator(config_manager=config)

# 第一次调用（缓存未命中，消耗令牌）
image_url_1 = generator.generate_single_image(
    prompt="老北京胡同",
    size="1024*1365"
)

# 第二次调用（缓存命中，不消耗令牌）
image_url_2 = generator.generate_single_image(
    prompt="老北京胡同",
    size="1024*1365"
)

# 两次调用返回相同结果，但第二次不消耗速率限制令牌
assert image_url_1 == image_url_2
```

## 最佳实践

### 1. 合理设置 RPM 限制

```python
# 根据 API 配额设置
# 图片生成 API 通常较慢，建议设置为 10-20 RPM
{
  "rate_limit": {
    "image": {
      "requests_per_minute": 10  # 推荐值
    }
  }
}
```

### 2. 启用缓存

```python
# 缓存可以减少 API 调用次数
{
  "cache": {
    "enabled": true,
    "ttl": 86400  # 24小时
  },
  "rate_limit": {
    "image": {
      "enable_rate_limit": true,
      "requests_per_minute": 10
    }
  }
}
```

### 3. 监控速率限制状态

```python
import time

def monitor_rate_limit(generator):
    """监控速率限制状态"""
    while True:
        stats = generator.get_rate_limit_stats()
        if stats:
            available = stats['rpm']['available_tokens']
            capacity = stats['rpm']['capacity']
            usage = (capacity - available) / capacity * 100
            
            print(f"速率限制状态: {available:.1f}/{capacity:.1f} ({usage:.1f}%)")
            
            if usage > 80:
                print("⚠️  警告：速率限制使用率超过 80%")
        
        time.sleep(10)  # 每 10 秒检查一次
```

### 4. 优雅处理超限情况

```python
def generate_with_retry(generator, prompt, max_retries=3):
    """带重试的图片生成"""
    for attempt in range(max_retries):
        try:
            return generator.generate_single_image(
                prompt=prompt,
                size="1024*1365"
            )
        except TimeoutError:
            if attempt < max_retries - 1:
                print(f"速率限制超时，重试 {attempt + 1}/{max_retries}")
                time.sleep(5)  # 等待 5 秒后重试
            else:
                print("达到最大重试次数，放弃")
                raise
```

### 5. 批量处理优化

```python
def batch_generate_with_rate_limit(generator, prompts, batch_size=3):
    """批量生成图片（控制并发）"""
    results = []
    
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i+batch_size]
        
        # 检查速率限制状态
        stats = generator.get_rate_limit_stats()
        if stats and stats['rpm']['available_tokens'] < batch_size:
            print("等待速率限制恢复...")
            time.sleep(10)
        
        # 生成批次
        for prompt in batch:
            try:
                image_url = generator.generate_single_image(
                    prompt=prompt,
                    size="1024*1365"
                )
                results.append(image_url)
            except Exception as e:
                print(f"生成失败: {e}")
                results.append(None)
    
    return results
```

## 故障排查

### 问题 1: 速率限制未生效

**症状**：API 调用没有被限流

**解决方案**：

1. 检查配置是否正确：
   ```python
   config = ConfigManager()
   enabled = config.get('rate_limit.image.enable_rate_limit')
   print(f"速率限制启用状态: {enabled}")
   ```

2. 检查生成器初始化：
   ```python
   generator = ImageGenerator(config_manager=config)
   print(f"速率限制器: {generator._rate_limit_enabled}")
   ```

### 问题 2: 频繁超时

**症状**：经常出现 `TimeoutError`

**解决方案**：

1. 增加 RPM 限制：
   ```json
   {
     "rate_limit": {
       "image": {
         "requests_per_minute": 20  # 增加到 20
       }
     }
   }
   ```

2. 启用缓存减少 API 调用：
   ```json
   {
     "cache": {
       "enabled": true,
       "ttl": 86400
     }
   }
   ```

3. 增加超时时间（修改源码）：
   ```python
   # 在 generate_single_image 中
   success = self.rpm_limiter.wait_for_token(tokens=1, timeout=180)  # 增加到 180 秒
   ```

### 问题 3: 令牌恢复太慢

**症状**：等待时间过长

**解决方案**：

1. 检查 RPM 配置：
   ```python
   stats = generator.get_rate_limit_stats()
   print(f"令牌生成速率: {stats['rpm']['rate']} 令牌/秒")
   ```

2. 增加 RPM 值：
   ```json
   {
     "rate_limit": {
       "image": {
         "requests_per_minute": 20  # 增加 RPM
       }
     }
   }
   ```

## 性能影响

### 开销分析

- **CPU 开销**：极低（< 0.1%）
- **内存开销**：极低（< 1MB）
- **延迟影响**：
  - 令牌充足时：< 1ms
  - 令牌不足时：等待时间 = (所需令牌数 - 可用令牌数) / 生成速率

### 性能优化建议

1. **合理设置 RPM**：根据实际 API 配额设置
2. **启用缓存**：减少重复 API 调用
3. **批量处理**：控制并发数量，避免令牌快速耗尽
4. **监控告警**：及时发现速率限制问题

## 与其他功能的集成

### 与缓存的集成

速率限制与缓存无缝集成：

- 缓存命中时不消耗令牌
- 缓存未命中时才消耗令牌
- 两者结合可以显著减少 API 调用

### 与并行生成的集成

在并行生成图片时，速率限制确保不会超过 API 配额：

```python
from src.async_image_service import AsyncImageService

# 创建异步服务（内部使用 ImageGenerator）
service = AsyncImageService(config_manager=config)

# 并行生成（自动应用速率限制）
results = await service.generate_images_parallel(
    prompts=["图1", "图2", "图3"],
    max_concurrent=3
)
```

### 与日志系统的集成

速率限制事件会自动记录到日志：

```python
# 日志示例
✅ [2026-02-13 08:00:00] [INFO] image_generator: 速率限制已启用 | requests_per_minute=10
✅ [2026-02-13 08:00:01] [DEBUG] image_generator: 正在获取 RPM 令牌 | available_tokens=10.0
✅ [2026-02-13 08:00:01] [DEBUG] image_generator: ✅ 已获取 RPM 令牌 | remaining_tokens=9.0
```

## 参考资料

- [速率限制器文档](RATE_LIMITER.md)
- [速率限制策略文档](RATE_LIMITER_STRATEGIES.md)
- [内容生成器速率限制文档](CONTENT_GENERATOR_RATE_LIMIT.md)
- [配置管理文档](CONFIG.md)
- [缓存管理文档](CACHE_MANAGER.md)

## 更新日志

### v1.0.0 (2026-02-13)

- ✅ 初始版本
- ✅ 实现令牌桶算法
- ✅ 支持 RPM 限制
- ✅ 集成到图片生成 API
- ✅ 与缓存功能集成
- ✅ 添加统计监控
- ✅ 完善文档和示例
