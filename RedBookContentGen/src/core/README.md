# 核心模块文档

## ConfigManager - 统一配置管理器

### 功能特性

- ✅ 支持多种配置源：JSON、YAML、环境变量
- ✅ 配置优先级管理：环境变量 > 配置文件 > 默认值
- ✅ 支持嵌套配置键（使用点号分隔）
- ✅ 配置验证和热重载
- ✅ 深度合并配置

### 快速开始

```python
from src.core.config_manager import ConfigManager

# 初始化配置管理器（默认加载 config/config.json）
config = ConfigManager()

# 或指定配置文件路径
config = ConfigManager(config_path="path/to/config.json")

# 获取配置项
api_key = config.get("openai_api_key")
timeout = config.get("api.openai.timeout")  # 支持嵌套键

# 获取配置项（带默认值）
model = config.get("openai_model", "qwen-plus")

# 设置配置项
config.set("openai_model", "qwen-max")
config.set("api.openai.timeout", 60)

# 验证配置
if config.validate():
    print("配置有效")

# 重新加载配置
config.reload()

# 获取所有配置
all_config = config.get_all()
```

### 配置优先级

配置按以下优先级加载（从低到高）：

1. **默认值** - 代码中定义的 `DEFAULT_CONFIG`
2. **配置文件** - JSON 或 YAML 格式的配置文件
3. **环境变量** - 系统环境变量（最高优先级）

### 环境变量映射

支持以下环境变量：

| 环境变量 | 配置键 |
|---------|--------|
| `OPENAI_API_KEY` | `openai_api_key` |
| `OPENAI_MODEL` | `openai_model` |
| `OPENAI_BASE_URL` | `openai_base_url` |
| `IMAGE_MODEL` | `image_model` |
| `IMAGE_GENERATION_MODE` | `image_generation_mode` |
| `TEMPLATE_STYLE` | `template_style` |
| `ENABLE_AI_REWRITE` | `enable_ai_rewrite` |
| `LOG_LEVEL` | `logging.level` |
| `CACHE_ENABLED` | `cache.enabled` |
| `CACHE_TTL` | `cache.ttl` |

### 配置文件格式

#### JSON 格式 (config.json)

```json
{
  "openai_api_key": "your-api-key",
  "openai_model": "qwen-plus",
  "api": {
    "openai": {
      "timeout": 30,
      "max_retries": 3
    }
  },
  "cache": {
    "enabled": true,
    "ttl": 3600
  }
}
```

#### YAML 格式 (config.yaml)

```yaml
openai_api_key: your-api-key
openai_model: qwen-plus
api:
  openai:
    timeout: 30
    max_retries: 3
cache:
  enabled: true
  ttl: 3600
```

### 使用示例

#### 示例 1：基本使用

```python
from src.core.config_manager import ConfigManager

# 加载配置
config = ConfigManager()

# 获取 API 配置
api_key = config.get("openai_api_key")
model = config.get("openai_model")
base_url = config.get("openai_base_url")

# 使用配置
from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url)
```

#### 示例 2：环境变量覆盖

```bash
# 设置环境变量
export OPENAI_API_KEY="prod-api-key"
export OPENAI_MODEL="qwen-max"
export CACHE_ENABLED="false"

# 运行程序
python run.py
```

```python
# 环境变量会自动覆盖配置文件中的值
config = ConfigManager()
print(config.get("openai_api_key"))  # 输出: prod-api-key
print(config.get("openai_model"))    # 输出: qwen-max
print(config.get("cache.enabled"))   # 输出: False
```

#### 示例 3：配置验证

```python
config = ConfigManager()

# 验证必需配置项是否存在
if not config.validate():
    print("配置不完整，请检查以下必需项：")
    print("- openai_api_key")
    print("- openai_model")
    print("- openai_base_url")
    exit(1)

# 配置有效，继续执行
print("配置验证通过，开始生成内容...")
```

#### 示例 4：动态修改配置

```python
config = ConfigManager()

# 运行时修改配置
config.set("api.openai.timeout", 60)
config.set("cache.enabled", False)

# 获取修改后的配置
timeout = config.get("api.openai.timeout")  # 60
cache_enabled = config.get("cache.enabled")  # False
```

### 测试

运行单元测试：

```bash
python tests/unit/test_config_manager.py
```

测试覆盖：
- ✅ 默认配置加载
- ✅ JSON 配置文件加载
- ✅ YAML 配置文件加载
- ✅ 环境变量覆盖
- ✅ 配置优先级
- ✅ get/set 方法
- ✅ 配置验证
- ✅ 配置重新加载
- ✅ 获取所有配置

### 注意事项

1. **YAML 支持**：需要安装 `pyyaml` 包才能加载 YAML 配置文件
   ```bash
   pip install pyyaml
   ```

2. **配置文件路径**：默认为 `config/config.json`，可通过构造函数参数指定

3. **嵌套键访问**：使用点号分隔，如 `api.openai.timeout`

4. **类型转换**：环境变量会自动转换类型（布尔值、整数）

5. **深拷贝**：`get_all()` 返回配置的深拷贝，修改不影响原配置

### 后续计划

- [ ] 添加配置模式（Schema）验证
- [ ] 支持配置加密存储
- [ ] 添加配置变更监听
- [ ] 支持远程配置中心

---

## ConfigSchema - 配置模式定义

### 功能特性

- ✅ 使用 Pydantic 定义配置数据结构
- ✅ 自动验证配置项的类型和取值范围
- ✅ 支持嵌套配置模式
- ✅ 提供详细的验证错误信息

### 配置模式列表

#### 1. OpenAIAPIConfig - OpenAI API 配置

```python
from src.core.config_schema import OpenAIAPIConfig

config = OpenAIAPIConfig(
    key="sk-xxx",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    timeout=30,
    max_retries=3
)
```

#### 2. ImageAPIConfig - 图片生成 API 配置

```python
from src.core.config_schema import ImageAPIConfig

config = ImageAPIConfig(
    model="wan2.2-t2i-flash",
    size="1024*1365",
    timeout=180,
    generation_mode="template",
    template_style="retro_chinese"
)
```

#### 3. CacheConfig - 缓存配置

```python
from src.core.config_schema import CacheConfig

config = CacheConfig(
    enabled=True,
    ttl=3600,
    max_size="1GB",
    eviction_policy="lru",
    content_cache_enabled=True,
    image_cache_enabled=True,
    cache_dir="cache"
)
```

#### 4. LoggingConfig - 日志配置

```python
from src.core.config_schema import LoggingConfig

config = LoggingConfig(
    level="INFO",
    format="json",
    file="logs/app.log",
    max_bytes=10485760,
    backup_count=5,
    console_output=True
)
```

#### 5. RateLimitConfig - 速率限制配置 ⭐ 新增

速率限制配置用于控制 API 调用频率，避免超过服务提供商的限额。

```python
from src.core.config_schema import RateLimitConfig

config = RateLimitConfig(
    openai={
        "requests_per_minute": 60,
        "tokens_per_minute": 90000,
        "enable_rate_limit": True
    },
    image={
        "requests_per_minute": 10,
        "enable_rate_limit": True,
        "max_concurrent": 3
    }
)
```

**OpenAI API 速率限制**：
- `requests_per_minute`: 每分钟最大请求数（1-10000）
- `tokens_per_minute`: 每分钟最大令牌数（1-10000000）
- `enable_rate_limit`: 是否启用速率限制

**图片生成 API 速率限制**：
- `requests_per_minute`: 每分钟最大请求数（1-1000）
- `enable_rate_limit`: 是否启用速率限制
- `max_concurrent`: 最大并发请求数（1-20）

详细说明请参考：[速率限制配置文档](./RATE_LIMIT_CONFIG.md)

#### 6. AppConfig - 应用完整配置

```python
from src.core.config_schema import AppConfig

config = AppConfig(
    api={
        "openai": {...},
        "image": {...}
    },
    cache={...},
    logging={...},
    rate_limit={...}
)
```

### 配置验证示例

```python
from pydantic import ValidationError
from src.core.config_schema import OpenAIRateLimitConfig

try:
    # 无效配置：令牌数与请求数比例过低
    config = OpenAIRateLimitConfig(
        requests_per_minute=1000,
        tokens_per_minute=50000  # 平均每请求 50 令牌
    )
except ValidationError as e:
    print(e.errors())
    # 输出：[{'msg': '令牌数与请求数比例过低...', ...}]
```

### 测试

运行配置模式测试：

```bash
# 测试速率限制配置
python3 -m pytest tests/unit/test_rate_limit_config.py -v

# 测试所有配置模式
python3 -m pytest tests/unit/test_*_config.py -v
```
