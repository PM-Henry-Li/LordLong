# 配置优先级管理文档

## 概述

ConfigManager 实现了完整的配置优先级管理系统，确保配置按照以下优先级顺序加载：

**环境变量 > 配置文件 > 默认值**

## 配置优先级说明

### 1. 环境变量（最高优先级）

环境变量具有最高优先级，可以覆盖配置文件和默认值。这对于以下场景特别有用：

- 在不同环境（开发、测试、生产）中使用不同配置
- 在容器化部署中注入敏感信息（如 API Key）
- 临时覆盖配置进行测试

**支持的环境变量：**

| 环境变量 | 配置键 | 说明 |
|---------|--------|------|
| `OPENAI_API_KEY` | `openai_api_key` | OpenAI API 密钥 |
| `OPENAI_MODEL` | `openai_model` | 模型名称 |
| `OPENAI_BASE_URL` | `openai_base_url` | API 基础 URL |
| `OPENAI_TIMEOUT` | `api.openai.timeout` | API 超时时间（秒） |
| `OPENAI_MAX_RETRIES` | `api.openai.max_retries` | 最大重试次数 |
| `IMAGE_MODEL` | `image_model` | 图片生成模型 |
| `IMAGE_GENERATION_MODE` | `image_generation_mode` | 图片生成模式 |
| `IMAGE_SIZE` | `api.image.size` | 图片尺寸 |
| `IMAGE_TIMEOUT` | `api.image.timeout` | 图片生成超时时间 |
| `TEMPLATE_STYLE` | `template_style` | 模板风格 |
| `ENABLE_AI_REWRITE` | `enable_ai_rewrite` | 启用 AI 改写 |
| `LOG_LEVEL` | `logging.level` | 日志级别 |
| `LOG_FORMAT` | `logging.format` | 日志格式 |
| `LOG_FILE` | `logging.file` | 日志文件路径 |
| `CACHE_ENABLED` | `cache.enabled` | 启用缓存 |
| `CACHE_TTL` | `cache.ttl` | 缓存过期时间（秒） |
| `CACHE_MAX_SIZE` | `cache.max_size` | 缓存最大大小 |
| `RATE_LIMIT_OPENAI_RPM` | `rate_limit.openai.requests_per_minute` | OpenAI 每分钟请求数 |
| `RATE_LIMIT_OPENAI_TPM` | `rate_limit.openai.tokens_per_minute` | OpenAI 每分钟令牌数 |
| `RATE_LIMIT_IMAGE_RPM` | `rate_limit.image.requests_per_minute` | 图片每分钟请求数 |
| `INPUT_FILE` | `input_file` | 输入文件路径 |
| `OUTPUT_EXCEL` | `output_excel` | 输出 Excel 路径 |
| `OUTPUT_IMAGE_DIR` | `output_image_dir` | 输出图片目录 |

**使用示例：**

```bash
# 设置环境变量
export OPENAI_API_KEY=sk-your-api-key
export OPENAI_MODEL=qwen-turbo
export CACHE_ENABLED=true
export OPENAI_TIMEOUT=60

# 运行程序
python run.py
```

### 2. 配置文件（中等优先级）

配置文件（`config/config.json` 或 `config/config.yaml`）中的配置会覆盖默认值，但会被环境变量覆盖。

**示例配置文件：**

```json
{
  "openai_api_key": "sk-your-api-key",
  "openai_model": "qwen-max",
  "image_generation_mode": "template",
  "template_style": "retro_chinese",
  "api": {
    "openai": {
      "timeout": 45,
      "max_retries": 5
    }
  },
  "cache": {
    "enabled": true,
    "ttl": 7200
  }
}
```

### 3. 默认值（最低优先级）

如果配置项既没有在环境变量中设置，也没有在配置文件中设置，则使用默认值。

默认值在 `ConfigManager.DEFAULT_CONFIG` 中定义。

## 类型转换

环境变量始终是字符串类型，ConfigManager 会自动进行类型转换：

| 环境变量值 | 转换后类型 | 示例 |
|-----------|-----------|------|
| `true`, `1`, `yes`, `on` | `bool` (True) | `CACHE_ENABLED=true` → `True` |
| `false`, `0`, `no`, `off` | `bool` (False) | `CACHE_ENABLED=false` → `False` |
| 纯数字 | `int` | `OPENAI_TIMEOUT=60` → `60` |
| 包含小数点的数字 | `float` | `CACHE_TTL=3.5` → `3.5` |
| `none`, `null` | `None` | `LOG_FILE=none` → `None` |
| 其他 | `str` | `OPENAI_MODEL=qwen-plus` → `"qwen-plus"` |

## 配置来源追踪

ConfigManager 提供了 `get_config_source()` 方法来追踪配置项的来源：

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

# 检查配置来源
source = config.get_config_source("openai_model")
# 返回值: 'environment', 'file', 'default', 或 'not_found'

print(f"openai_model 来源: {source}")
```

## 配置热重载

ConfigManager 支持配置热重载功能，允许在运行时动态更新配置，无需重启应用程序。

### 手动重载

使用 `reload()` 方法手动重新加载配置：

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

# 修改内存中的配置
config.set('openai_model', 'qwen-turbo')
print(f"修改后: {config.get('openai_model')}")  # qwen-turbo

# 手动重载（从文件重新加载）
config.reload()
print(f"重载后: {config.get('openai_model')}")  # 恢复为文件中的值
```

### 自动重载

启动文件监控，当配置文件变化时自动重新加载：

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

# 启动监控（每秒检查一次文件变化）
config.start_watching(check_interval=1.0)

# 现在可以修改 config/config.json 文件
# 配置会自动重新加载

# 检查监控状态
if config.is_watching():
    print("配置文件监控正在运行")

# 停止监控
config.stop_watching()
```

### 重载回调

注册回调函数，在配置重载时执行自定义操作：

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

def on_config_reload():
    """配置重载时的回调函数"""
    print("配置已更新！")
    # 执行清理缓存、重新初始化等操作
    cache.clear()
    logger.info("配置已重新加载")

# 注册回调
config.register_reload_callback(on_config_reload)

# 重载时会自动调用回调
config.reload()  # 输出: 配置已更新！

# 取消注册
config.unregister_reload_callback(on_config_reload)
```

### 多个回调函数

可以注册多个回调函数，它们会按注册顺序依次执行：

```python
config = ConfigManager()

def log_reload():
    print("日志: 配置已重载")

def clear_cache():
    print("缓存: 清空旧缓存")

def notify_services():
    print("通知: 通知相关服务")

# 注册多个回调
config.register_reload_callback(log_reload)
config.register_reload_callback(clear_cache)
config.register_reload_callback(notify_services)

# 重载时会依次调用所有回调
config.reload()
```

### 线程安全

所有配置操作都是线程安全的，可以在多线程环境中安全使用：

```python
import threading
from src.core.config_manager import ConfigManager

config = ConfigManager()

def reader_thread():
    """读取配置的线程"""
    value = config.get('openai_model')  # 线程安全

def writer_thread():
    """写入配置的线程"""
    config.set('openai_model', 'qwen-max')  # 线程安全

def reload_thread():
    """重载配置的线程"""
    config.reload()  # 线程安全

# 多个线程可以安全地并发访问配置
threads = [
    threading.Thread(target=reader_thread),
    threading.Thread(target=writer_thread),
    threading.Thread(target=reload_thread)
]

for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 热重载使用场景

**场景 1：开发环境调试**

在开发过程中，无需重启应用即可调整配置：

```python
config = ConfigManager()
config.start_watching()

# 现在可以在运行时修改 config.json
# 应用会自动使用新配置
```

**场景 2：生产环境配置更新**

在生产环境中，动态调整配置参数（如超时时间、重试次数）：

```python
config = ConfigManager()

# 注册回调清理缓存
config.register_reload_callback(lambda: cache.clear())

# 启动监控
config.start_watching()

# 运维人员可以修改配置文件
# 应用会自动重载并清理缓存
```

**场景 3：A/B 测试**

动态切换不同的配置进行测试：

```python
config = ConfigManager()

def on_model_change():
    """模型变化时重新初始化客户端"""
    global client
    client = OpenAI(
        api_key=config.get('openai_api_key'),
        base_url=config.get('openai_base_url')
    )

config.register_reload_callback(on_model_change)
config.start_watching()

# 可以动态切换不同的模型进行测试
```

### 注意事项

1. **文件监控开销**：文件监控会定期检查文件修改时间，建议设置合理的检查间隔（默认 1 秒）

2. **回调异常处理**：回调函数中的异常会被捕获并打印，不会影响其他回调的执行

3. **环境变量优先级**：热重载只会重新加载配置文件，环境变量的优先级仍然最高

4. **线程清理**：监控线程是守护线程，程序退出时会自动停止。也可以手动调用 `stop_watching()` 停止

5. **配置一致性**：在重载过程中，所有配置操作都是原子的，不会出现部分更新的情况

## 使用场景

### 场景 1：开发环境

在开发环境中，使用配置文件设置基本配置，使用环境变量覆盖敏感信息：

```bash
# 配置文件中设置基本配置
# config/config.json

# 环境变量中设置 API Key
export OPENAI_API_KEY=sk-dev-key
python run.py
```

### 场景 2：生产环境

在生产环境中，使用环境变量设置所有敏感配置：

```bash
export OPENAI_API_KEY=sk-prod-key
export OPENAI_MODEL=qwen-max
export CACHE_ENABLED=true
export LOG_LEVEL=WARNING
python run.py
```

### 场景 3：Docker 容器

在 Docker 容器中，通过环境变量注入配置：

```dockerfile
ENV OPENAI_API_KEY=sk-your-key
ENV OPENAI_MODEL=qwen-plus
ENV CACHE_ENABLED=true
```

或使用 docker-compose.yml：

```yaml
services:
  app:
    image: redbook-content-gen
    environment:
      - OPENAI_API_KEY=sk-your-key
      - OPENAI_MODEL=qwen-plus
      - CACHE_ENABLED=true
```

### 场景 4：临时测试

临时覆盖配置进行测试：

```bash
# 临时使用不同的模型
OPENAI_MODEL=qwen-turbo python run.py

# 临时禁用缓存
CACHE_ENABLED=false python run.py
```

## 最佳实践

1. **敏感信息使用环境变量**：API Key 等敏感信息应该通过环境变量设置，不要提交到版本控制系统

2. **基础配置使用配置文件**：非敏感的基础配置可以放在配置文件中，便于管理和版本控制

3. **使用 .env 文件**：在开发环境中，可以使用 `.env` 文件管理环境变量（需要 python-dotenv 包）

4. **配置验证**：在程序启动时调用 `config.validate()` 验证必需的配置项是否存在

5. **配置来源追踪**：在调试时使用 `get_config_source()` 方法确认配置来源

## 测试

运行配置管理器的单元测试：

```bash
python3 tests/unit/test_config_manager.py
```

测试覆盖：
- ✅ 默认配置加载
- ✅ JSON 配置文件加载
- ✅ YAML 配置文件加载
- ✅ 环境变量覆盖
- ✅ 配置优先级顺序
- ✅ 全面配置优先级场景
- ✅ 环境变量类型转换
- ✅ 配置来源追踪
- ✅ 嵌套配置环境变量覆盖
- ✅ get/set 方法
- ✅ 配置验证
- ✅ 手动配置重载
- ✅ 文件变化自动重载
- ✅ 重载回调函数
- ✅ 多个回调函数
- ✅ 线程安全性
- ✅ 监控不存在的文件
- ✅ 停止未启动的监控
- ✅ 重复启动监控
- ✅ 回调函数异常处理
- ✅ 获取所有配置

## 示例代码

查看完整的使用示例：

**基本配置使用：**
```bash
python3 examples/config_usage_example.py
```

**配置热重载示例：**
```bash
python3 examples/config_hot_reload_example.py
```

示例包括：

### config_usage_example.py
1. 基本使用
2. 环境变量覆盖
3. 嵌套配置访问
4. 动态修改配置
5. 配置验证
6. 获取所有配置
7. 与 OpenAI 客户端集成
8. 配置来源追踪
9. 配置优先级演示
10. 扩展的环境变量支持

### config_hot_reload_example.py
1. 手动重载配置
2. 自动重载配置（文件监控）
3. 使用重载回调
4. 多个回调函数
5. 线程安全的配置访问
