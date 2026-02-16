# API 配置模式文档

## 概述

本文档介绍如何使用 Pydantic 定义的 API 配置模式进行配置验证和管理。

## 配置模式类

### 1. OpenAIAPIConfig

OpenAI API 配置模式，用于验证和管理 OpenAI 兼容 API 的配置。

**字段说明**:

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `key` | `str` | 是 | - | API Key，别名 `openai_api_key` |
| `base_url` | `str` | 否 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API 基础 URL |
| `model` | `str` | 否 | `qwen-plus` | 模型名称 |
| `timeout` | `int` | 否 | `30` | 请求超时时间（秒），范围：1-300 |
| `max_retries` | `int` | 否 | `3` | 最大重试次数，范围：0-10 |

**验证规则**:
- `key`: 不能为空
- `base_url`: 必须以 `http://` 或 `https://` 开头，自动移除末尾斜杠
- `model`: 不能为空字符串
- `timeout`: 必须大于 0，不超过 300
- `max_retries`: 必须大于等于 0，不超过 10

**使用示例**:

```python
from src.core.config_schema import OpenAIAPIConfig

# 创建配置
config = OpenAIAPIConfig(
    openai_api_key="sk-your-api-key",
    openai_model="qwen-max",
    timeout=60
)

# 访问配置
print(config.key)        # sk-your-api-key
print(config.model)      # qwen-max
print(config.timeout)    # 60
```

### 2. ImageAPIConfig

图片生成 API 配置模式，用于验证和管理图片生成相关配置。

**字段说明**:

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model` | `str` | 否 | `wan2.2-t2i-flash` | 图片生成模型名称 |
| `size` | `str` | 否 | `1024*1365` | 图片尺寸，格式：`宽度*高度` |
| `timeout` | `int` | 否 | `180` | 超时时间（秒），范围：1-600 |
| `generation_mode` | `Literal["template", "api"]` | 否 | `template` | 生成模式 |
| `template_style` | `str` | 否 | `retro_chinese` | 模板风格（仅 template 模式） |

**验证规则**:
- `size`: 必须符合 `数字*数字` 格式，宽高必须大于 0 且不超过 4096
- `timeout`: 必须大于 0，不超过 600
- `generation_mode`: 只能是 `template` 或 `api`
- `template_style`: 只能是以下之一：
  - `retro_chinese` (复古中国风)
  - `modern_minimal` (现代简约)
  - `vintage_film` (怀旧胶片)
  - `warm_memory` (温暖记忆)
  - `ink_wash` (水墨风格)
- 当 `generation_mode` 为 `template` 时，必须指定 `template_style`

**使用示例**:

```python
from src.core.config_schema import ImageAPIConfig

# Template 模式
template_config = ImageAPIConfig(
    image_generation_mode="template",
    template_style="retro_chinese",
    size="1024*1365"
)

# API 模式
api_config = ImageAPIConfig(
    image_generation_mode="api",
    size="2048*2048",
    timeout=300
)
```

### 3. CacheConfig

缓存配置模式，用于验证和管理缓存相关配置。

**字段说明**:

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `enabled` | `bool` | 否 | `True` | 是否启用缓存 |
| `ttl` | `int` | 否 | `3600` | 缓存过期时间（秒），0 表示永不过期，范围：0-604800（7天） |
| `max_size` | `str` | 否 | `1GB` | 缓存最大大小，支持单位：KB、MB、GB |
| `eviction_policy` | `Literal["lru", "lfu", "fifo"]` | 否 | `lru` | 缓存淘汰策略 |
| `content_cache_enabled` | `bool` | 否 | `True` | 是否启用内容生成缓存 |
| `image_cache_enabled` | `bool` | 否 | `True` | 是否启用图片生成缓存 |
| `cache_dir` | `str` | 否 | `cache` | 缓存目录路径 |

**验证规则**:
- `ttl`: 必须大于等于 0，不超过 604800（7天）
- `max_size`: 必须符合 `数字+单位` 格式（如 `1GB`、`500MB`），最小 1MB，最大 100GB
- `eviction_policy`: 只能是以下之一：
  - `lru` (Least Recently Used - 最近最少使用)
  - `lfu` (Least Frequently Used - 最不经常使用)
  - `fifo` (First In First Out - 先进先出)
- `cache_dir`: 不能为空字符串

**使用示例**:

```python
from src.core.config_schema import CacheConfig

# 创建缓存配置
cache_config = CacheConfig(
    enabled=True,
    ttl=7200,  # 2小时
    max_size="2GB",
    eviction_policy="lru",
    content_cache_enabled=True,
    image_cache_enabled=True,
    cache_dir="output/cache"
)

# 访问配置
print(cache_config.enabled)              # True
print(cache_config.ttl)                  # 7200
print(cache_config.max_size)             # 2GB
print(cache_config.eviction_policy)      # lru
```

**禁用缓存示例**:

```python
# 完全禁用缓存
cache_config = CacheConfig(enabled=False)

# 只禁用图片缓存
cache_config = CacheConfig(
    enabled=True,
    content_cache_enabled=True,
    image_cache_enabled=False
)
```

### 4. LoggingConfig

日志配置模式，用于验证和管理日志系统相关配置。

**字段说明**:

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `level` | `Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]` | 否 | `INFO` | 日志级别 |
| `format` | `Literal["text", "json"]` | 否 | `json` | 日志格式 |
| `file` | `str` | 否 | `logs/app.log` | 日志文件路径 |
| `max_bytes` | `int` | 否 | `10485760` (10MB) | 单个日志文件最大字节数，范围：1024-1073741824 (1KB-1GB) |
| `backup_count` | `int` | 否 | `5` | 保留的日志备份文件数量，范围：0-100 |
| `console_output` | `bool` | 否 | `True` | 是否同时输出到控制台 |
| `date_format` | `str` | 否 | `%Y-%m-%d %H:%M:%S` | 日志时间格式 |
| `log_dir` | `str` | 否 | `logs` | 日志目录路径 |
| `enable_rotation` | `bool` | 否 | `True` | 是否启用日志轮转 |

**验证规则**:
- `level`: 只能是 `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL` 之一（必须大写）
- `format`: 只能是 `text`（文本格式）或 `json`（JSON 结构化格式）
- `file`: 不能为空，必须以 `.log` 结尾
- `max_bytes`: 必须大于等于 1024（1KB），不超过 1073741824（1GB）
- `backup_count`: 必须大于等于 0，不超过 100
- `date_format`: 不能为空字符串
- `log_dir`: 不能为空字符串
- 当 `enable_rotation=True` 时，`backup_count` 必须大于 0

**日志级别说明**:
- `DEBUG`: 调试信息，最详细，用于开发调试
- `INFO`: 一般信息，记录正常运行状态
- `WARNING`: 警告信息，可能存在问题但不影响运行
- `ERROR`: 错误信息，功能执行失败
- `CRITICAL`: 严重错误，系统可能无法继续运行

**日志格式说明**:
- `text`: 人类可读的文本格式，适合开发环境快速查看
- `json`: 结构化 JSON 格式，适合生产环境日志分析和查询

**使用示例**:

```python
from src.core.config_schema import LoggingConfig

# 生产环境配置（JSON 格式，INFO 级别）
production_logging = LoggingConfig(
    level="INFO",
    format="json",
    file="logs/app.log",
    max_bytes=20971520,  # 20MB
    backup_count=10,
    console_output=True,
    enable_rotation=True
)

# 开发环境配置（文本格式，DEBUG 级别）
dev_logging = LoggingConfig(
    level="DEBUG",
    format="text",
    file="logs/dev.log",
    max_bytes=5242880,  # 5MB
    backup_count=3,
    console_output=True,
    enable_rotation=True
)

# 错误日志配置（只记录错误）
error_logging = LoggingConfig(
    level="ERROR",
    format="json",
    file="logs/error.log",
    max_bytes=10485760,  # 10MB
    backup_count=20,
    console_output=False,
    enable_rotation=True
)

# 访问配置
print(production_logging.level)          # INFO
print(production_logging.format)         # json
print(production_logging.max_bytes)      # 20971520
```

**日志轮转示例**:

```python
# 启用日志轮转（当文件达到 10MB 时自动轮转，保留 5 个备份）
rotation_config = LoggingConfig(
    enable_rotation=True,
    max_bytes=10485760,  # 10MB
    backup_count=5
)
# 生成的文件：app.log, app.log.1, app.log.2, ..., app.log.5

# 禁用日志轮转
no_rotation_config = LoggingConfig(
    enable_rotation=False,
    backup_count=0
)
```

**自定义日期格式示例**:

```python
# ISO 8601 格式
iso_logging = LoggingConfig(
    date_format="%Y-%m-%dT%H:%M:%S.%f"
)

# 简短日期格式
short_logging = LoggingConfig(
    date_format="%Y-%m-%d"
)

# 自定义格式
custom_logging = LoggingConfig(
    date_format="%d/%m/%Y %H:%M:%S"
)
```

### 5. APIConfig

完整的 API 配置模式，包含 OpenAI 和图片生成两部分配置。

**字段说明**:

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `openai` | `OpenAIAPIConfig` | 是 | OpenAI API 配置 |
| `image` | `ImageAPIConfig` | 是 | 图片生成 API 配置 |

**使用示例**:

```python
from src.core.config_schema import APIConfig, OpenAIAPIConfig, ImageAPIConfig

# 创建完整配置
config = APIConfig(
    openai=OpenAIAPIConfig(
        openai_api_key="sk-your-api-key",
        openai_model="qwen-plus"
    ),
    image=ImageAPIConfig(
        image_generation_mode="template",
        template_style="warm_memory"
    )
)

# 访问配置
print(config.openai.model)           # qwen-plus
print(config.image.generation_mode)  # template
```

## 从字典创建配置

可以从字典（例如从 JSON 文件加载）创建配置对象：

```python
config_dict = {
    "openai": {
        "openai_api_key": "sk-your-api-key",
        "openai_model": "qwen-max",
        "timeout": 60
    },
    "image": {
        "image_model": "wan2.2-t2i-flash",
        "size": "1024*1365",
        "image_generation_mode": "template",
        "template_style": "retro_chinese"
    }
}

config = APIConfig(**config_dict)
```

## 转换为字典

可以将配置对象转换为字典：

```python
config_dict = config.model_dump()
```

## 配置验证

Pydantic 会自动验证配置，如果配置无效会抛出 `ValidationError`：

```python
from pydantic import ValidationError

try:
    config = OpenAIAPIConfig(
        openai_api_key="sk-test",
        timeout=-10  # 无效：超时时间必须 > 0
    )
except ValidationError as e:
    print("配置验证失败:")
    for error in e.errors():
        print(f"  字段: {error['loc']}")
        print(f"  错误: {error['msg']}")
```

## 与 ConfigManager 集成

配置模式可以与现有的 `ConfigManager` 集成使用：

```python
from src.core.config_manager import ConfigManager
from src.core.config_schema import APIConfig, OpenAIAPIConfig, ImageAPIConfig, CacheConfig

# 加载配置
config_manager = ConfigManager()

# 创建并验证 API 配置
try:
    api_config = APIConfig(
        openai=OpenAIAPIConfig(
            openai_api_key=config_manager.get('openai_api_key'),
            openai_model=config_manager.get('openai_model'),
            timeout=config_manager.get('api.openai.timeout')
        ),
        image=ImageAPIConfig(
            image_model=config_manager.get('image_model'),
            size=config_manager.get('api.image.size'),
            image_generation_mode=config_manager.get('image_generation_mode'),
            template_style=config_manager.get('template_style')
        )
    )
    
    # 创建并验证缓存配置
    cache_config = CacheConfig(
        enabled=config_manager.get('cache.enabled', True),
        ttl=config_manager.get('cache.ttl', 3600),
        max_size=config_manager.get('cache.max_size', '1GB'),
        eviction_policy=config_manager.get('cache.eviction_policy', 'lru'),
        content_cache_enabled=config_manager.get('cache.content_cache_enabled', True),
        image_cache_enabled=config_manager.get('cache.image_cache_enabled', True),
        cache_dir=config_manager.get('cache.cache_dir', 'cache')
    )
    
    print("✅ 配置验证通过")
except ValidationError as e:
    print("❌ 配置验证失败")
    for error in e.errors():
        print(f"  - {error['loc']}: {error['msg']}")
```

## 完整示例

查看 `examples/config_schema_usage_example.py` 获取更多使用示例。

运行示例：

```bash
python3 examples/config_schema_usage_example.py
```

### 缓存配置完整示例

```python
from src.core.config_schema import CacheConfig
from pydantic import ValidationError

# 示例 1: 生产环境配置（启用所有缓存）
production_cache = CacheConfig(
    enabled=True,
    ttl=3600,  # 1小时
    max_size="5GB",
    eviction_policy="lru",
    content_cache_enabled=True,
    image_cache_enabled=True,
    cache_dir="cache"
)

# 示例 2: 开发环境配置（较短的 TTL）
dev_cache = CacheConfig(
    enabled=True,
    ttl=300,  # 5分钟
    max_size="500MB",
    eviction_policy="lru",
    content_cache_enabled=True,
    image_cache_enabled=True,
    cache_dir="dev_cache"
)

# 示例 3: 测试环境配置（禁用缓存）
test_cache = CacheConfig(
    enabled=False
)

# 示例 4: 只缓存内容，不缓存图片
content_only_cache = CacheConfig(
    enabled=True,
    ttl=7200,  # 2小时
    max_size="1GB",
    eviction_policy="lru",
    content_cache_enabled=True,
    image_cache_enabled=False,  # 禁用图片缓存
    cache_dir="cache"
)

# 示例 5: 使用 FIFO 策略的缓存
fifo_cache = CacheConfig(
    enabled=True,
    ttl=1800,  # 30分钟
    max_size="2GB",
    eviction_policy="fifo",  # 先进先出
    content_cache_enabled=True,
    image_cache_enabled=True,
    cache_dir="cache"
)

# 示例 6: 永不过期的缓存
permanent_cache = CacheConfig(
    enabled=True,
    ttl=0,  # 0 表示永不过期
    max_size="10GB",
    eviction_policy="lru",
    content_cache_enabled=True,
    image_cache_enabled=True,
    cache_dir="permanent_cache"
)

# 验证配置
try:
    # 尝试创建无效配置
    invalid_cache = CacheConfig(
        max_size="500KB"  # 错误：小于最小值 1MB
    )
except ValidationError as e:
    print("配置验证失败:")
    for error in e.errors():
        print(f"  - {error['loc']}: {error['msg']}")
```

## 测试

运行配置模式的单元测试：

```bash
python3 tests/unit/test_config_schema.py
```

## 优势

使用 Pydantic 配置模式的优势：

1. **类型安全**: 自动进行类型检查和转换
2. **数据验证**: 自动验证配置值的有效性
3. **清晰的错误信息**: 提供详细的验证错误信息
4. **IDE 支持**: 提供代码补全和类型提示
5. **文档化**: 配置结构清晰，易于理解和维护
6. **序列化**: 轻松转换为字典或 JSON

## 配置模式总结

当前已实现的配置模式：

| 配置模式 | 用途 | 主要字段 |
|---------|------|---------|
| `OpenAIAPIConfig` | OpenAI API 配置 | key, base_url, model, timeout, max_retries |
| `ImageAPIConfig` | 图片生成配置 | model, size, timeout, generation_mode, template_style |
| `CacheConfig` | 缓存配置 | enabled, ttl, max_size, eviction_policy, cache_dir |
| `LoggingConfig` | 日志配置 | level, format, file, max_bytes, backup_count, enable_rotation |
| `APIConfig` | 完整 API 配置 | openai, image |

### 缓存配置特点

- **灵活的大小配置**: 支持 KB、MB、GB 单位，自动验证范围（1MB-100GB）
- **多种淘汰策略**: 支持 LRU、LFU、FIFO 三种策略
- **细粒度控制**: 可以分别控制内容缓存和图片缓存
- **TTL 配置**: 支持 0（永不过期）到 7 天的过期时间
- **自定义目录**: 可以指定缓存存储目录

### 日志配置特点

- **多级别支持**: 支持 DEBUG、INFO、WARNING、ERROR、CRITICAL 五个级别
- **双格式输出**: 支持文本格式（开发）和 JSON 格式（生产）
- **自动轮转**: 支持基于文件大小的日志轮转，可配置备份数量
- **灵活输出**: 可同时输出到文件和控制台
- **自定义格式**: 支持自定义日期时间格式
- **大小控制**: 单文件大小范围 1KB-1GB，备份数量 0-100

## 参考资料

- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [配置管理文档](config_priority.md)
