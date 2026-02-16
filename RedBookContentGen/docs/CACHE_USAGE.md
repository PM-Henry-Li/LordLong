# 缓存功能使用指南

## 概述

内容生成模块和图片生成模块现已集成缓存功能，可以显著提升重复内容生成的性能。当使用相同的输入内容或图片提示词时，系统会直接返回缓存的结果，避免重复调用 AI API。

## 功能特性

- ✅ 基于输入内容/提示词的 SHA256 哈希自动生成缓存键
- ✅ 支持通过配置文件启用/禁用缓存
- ✅ 可配置的缓存过期时间（TTL）
- ✅ 可配置的缓存容量限制
- ✅ LRU（最近最少使用）淘汰策略
- ✅ 缓存命中/未命中日志记录
- ✅ 缓存统计信息查询
- ✅ 支持内容生成和图片生成两种场景

## 配置说明

在 `config/config.json` 中添加缓存配置：

```json
{
  "cache": {
    "enabled": true,
    "ttl": 3600,
    "max_size": 1000
  }
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用缓存功能 |
| `ttl` | integer | `3600` | 缓存过期时间（秒），内容生成默认 1 小时，图片生成默认 24 小时 |
| `max_size` | integer | `1000` | 缓存最大条目数，超过后使用 LRU 策略淘汰 |

**注意**：
- 内容生成缓存的 TTL 默认为 3600 秒（1 小时）
- 图片生成缓存的 TTL 默认为 86400 秒（24 小时），因为图片 URL 通常有效期更长

## 使用示例

### 内容生成器缓存

#### 基本使用

```python
from src.core.config_manager import ConfigManager
from src.content_generator import RedBookContentGenerator

# 初始化生成器（缓存默认启用）
config_manager = ConfigManager("config/config.json")
generator = RedBookContentGenerator(config_manager=config_manager)

# 第一次生成（调用 API）
content1 = generator.generate_content("老北京胡同文化")
# 输出: 缓存未命中，开始生成新内容

# 第二次生成相同内容（从缓存返回）
content2 = generator.generate_content("老北京胡同文化")
# 输出: ✅ 缓存命中，直接返回缓存结果
```

#### 查看缓存统计

```python
# 获取缓存统计信息
stats = generator.get_cache_stats()
print(stats)
# 输出:
# {
#   'size': 5,           # 当前缓存条目数
#   'max_size': 1000,    # 最大容量
#   'hits': 10,          # 命中次数
#   'misses': 5,         # 未命中次数
#   'hit_rate': 0.67,    # 命中率（67%）
#   'evictions': 0       # 淘汰次数
# }
```

#### 清空缓存

```python
# 清空所有缓存
generator.clear_cache()
# 输出: 缓存已清空
```

### 图片生成器缓存

#### 基本使用

```python
from src.core.config_manager import ConfigManager
from src.image_generator import ImageGenerator

# 初始化生成器（缓存默认启用）
config_manager = ConfigManager("config/config.json")
generator = ImageGenerator(config_manager=config_manager)

# 第一次生成（调用 API）
prompt = "老北京胡同，复古风格，温暖色调"
image_url1 = generator.generate_single_image(prompt)
# 输出: 正在生成图片...

# 第二次生成相同提示词（从缓存返回）
image_url2 = generator.generate_single_image(prompt)
# 输出: ✅ 缓存命中，直接返回图片URL
```

#### 查看缓存统计

```python
# 获取缓存统计信息
stats = generator.get_cache_stats()
print(stats)
# 输出:
# {
#   'size': 3,           # 当前缓存条目数
#   'max_size': 1000,    # 最大容量
#   'hits': 5,           # 命中次数
#   'misses': 3,         # 未命中次数
#   'hit_rate': 0.625,   # 命中率（62.5%）
#   'evictions': 0       # 淘汰次数
# }
```

#### 清空缓存

```python
# 清空所有缓存
generator.clear_cache()
# 输出: 缓存已清空
```

### 禁用缓存

在配置文件中设置：

```json
{
  "cache": {
    "enabled": false
  }
}
```

或者通过环境变量：

```bash
export CACHE_ENABLED=false
```

## 缓存键生成规则

### 内容生成器

缓存键基于输入内容的 SHA256 哈希值生成，格式为：

```
content_gen:<sha256_hash>
```

相同的输入内容会生成相同的缓存键，确保缓存命中。

### 图片生成器

缓存键基于图片提示词、尺寸和模型的 SHA256 哈希值生成，格式为：

```
image_gen:<sha256_hash>
```

缓存键包含以下信息：
- `prompt`: 图片提示词
- `size`: 图片尺寸（如 "1024*1365"）
- `model`: 图片生成模型（如 "qwen-image-plus"）

相同的提示词、尺寸和模型会生成相同的缓存键。

## 性能优化建议

### 1. 合理设置 TTL

- **短期使用**（如测试）：设置较短的 TTL（如 300 秒）
- **生产环境**：设置较长的 TTL（如 3600 秒或更长）
- **永久缓存**：设置 TTL 为 0（不推荐，除非内容永不变化）

### 2. 调整缓存容量

根据实际使用情况调整 `max_size`：

- **内存充足**：可以设置较大的值（如 5000）
- **内存受限**：设置较小的值（如 500）
- **监控使用**：定期查看 `evictions` 统计，如果频繁淘汰，考虑增加容量

### 3. 监控缓存效果

定期检查缓存统计信息：

```python
stats = generator.get_cache_stats()
hit_rate = stats['hit_rate']

if hit_rate < 0.3:
    print("⚠️ 缓存命中率较低，考虑调整策略")
elif hit_rate > 0.7:
    print("✅ 缓存效果良好")
```

## 日志输出

启用缓存后，系统会输出以下日志：

### 内容生成器日志

#### 初始化日志

```
✅ [2026-02-13 07:36:00] [INFO] content_generator: 缓存已启用 | ttl=3600, max_size=1000
```

#### 缓存命中日志

```
✅ [2026-02-13 07:36:05] [INFO] content_generator: ✅ 缓存命中，直接返回缓存结果 | cache_key=content_gen:d1fe...
```

#### 缓存未命中日志

```
✅ [2026-02-13 07:36:10] [INFO] content_generator: 缓存未命中，开始生成新内容 | cache_key=content_gen:a2b3...
```

#### 缓存保存日志

```
✅ [2026-02-13 07:36:15] [INFO] content_generator: ✅ 生成结果已保存到缓存 | cache_key=content_gen:a2b3...
```

### 图片生成器日志

#### 初始化日志

```
✅ [2026-02-13 07:50:00] [INFO] image_generator: 缓存已启用 | ttl=86400, max_size=1000
```

#### 缓存命中日志

```
✅ [2026-02-13 07:50:05] [INFO] image_generator: 从缓存获取图片URL | cache_key=image_gen:dc67c5...
```

#### 缓存保存日志

```
✅ [2026-02-13 07:50:10] [INFO] image_generator: 图片URL已缓存 | cache_key=image_gen:dc67c5...
```

## 注意事项

1. **缓存键唯一性**：缓存键基于输入内容生成，即使是微小的差异也会导致不同的缓存键
2. **内存使用**：缓存数据存储在内存中，大量缓存会占用内存
3. **进程隔离**：缓存仅在当前进程有效，重启应用后缓存会清空
4. **线程安全**：缓存管理器是线程安全的，可以在多线程环境中使用

## 故障排查

### 缓存未生效

1. 检查配置文件中 `cache.enabled` 是否为 `true`
2. 查看日志确认缓存是否已初始化
3. 确认输入内容完全相同（包括空格、换行等）

### 缓存命中率低

1. 检查输入内容是否有细微差异
2. 考虑增加 TTL 时间
3. 检查是否频繁清空缓存

### 内存占用过高

1. 减小 `max_size` 配置
2. 减小 `ttl` 配置，让缓存更快过期
3. 定期调用 `clear_cache()` 清理缓存

## 未来改进

- [ ] 支持 Redis 分布式缓存
- [ ] 支持缓存预热
- [ ] 支持缓存持久化到磁盘
- [ ] 支持更细粒度的缓存控制
- [ ] 支持缓存版本管理

## 相关文档

- [配置管理文档](CONFIG.md)
- [日志系统文档](../src/core/logger.py)
- [缓存管理器源码](../src/core/cache_manager.py)
- [内容生成器缓存示例](../examples/content_generator_cache_example.py)
- [图片生成器缓存示例](../examples/image_generator_cache_example.py)
