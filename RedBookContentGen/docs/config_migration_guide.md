# 配置管理迁移指南

## 概述

本指南帮助您从旧的配置管理方式迁移到新的统一配置管理系统（`ConfigManager`）。

## 为什么要迁移？

### 旧方式的问题

- ❌ 每个模块独立加载配置文件
- ❌ 配置分散，难以维护
- ❌ 不支持环境变量覆盖
- ❌ 缺少配置验证
- ❌ 无法热重载配置

### 新方式的优势

- ✅ 统一的配置管理入口
- ✅ 支持多层配置覆盖（默认值 < 配置文件 < 环境变量）
- ✅ 自动配置验证
- ✅ 支持配置热重载
- ✅ 更好的类型安全
- ✅ 配置来源追踪

## 迁移步骤

### 步骤 1：了解新的配置结构

新的配置管理器使用点号分隔的键路径访问嵌套配置：

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

# 访问顶层配置
api_key = config.get('openai_api_key')
model = config.get('openai_model')

# 访问嵌套配置
timeout = config.get('api.openai.timeout')
rpm = config.get('rate_limit.openai.requests_per_minute')
```

### 步骤 2：更新代码

#### 旧方式（不推荐）

```python
import json

class MyGenerator:
    def __init__(self, config_path="config/config.json"):
        # 直接加载 JSON 文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 访问配置
        self.api_key = self.config.get('openai_api_key')
        self.model = self.config.get('openai_model', 'qwen-plus')
```

#### 新方式（推荐）

```python
from src.core.config_manager import ConfigManager

class MyGenerator:
    def __init__(self, config_manager=None):
        # 使用 ConfigManager
        if config_manager is None:
            config_manager = ConfigManager()
        
        self.config_manager = config_manager
        
        # 访问配置
        self.api_key = self.config_manager.get('openai_api_key')
        self.model = self.config_manager.get('openai_model')
```

### 步骤 3：更新配置文件

确保您的 `config/config.json` 包含新的配置结构：

```json
{
  "openai_api_key": "your-api-key-here",
  "openai_model": "qwen-plus",
  "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "image_model": "wan2.2-t2i-flash",
  "image_generation_mode": "template",
  "template_style": "retro_chinese",
  "enable_ai_rewrite": false,
  "api": {
    "openai": {
      "timeout": 30,
      "max_retries": 3
    },
    "image": {
      "size": "1024*1365",
      "timeout": 180
    }
  },
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

### 步骤 4：使用环境变量（可选）

新的配置管理器支持通过环境变量覆盖配置：

```bash
# 设置 API Key
export OPENAI_API_KEY="sk-xxx"

# 设置模型
export OPENAI_MODEL="qwen-max"

# 设置超时
export OPENAI_TIMEOUT="60"

# 设置日志级别
export LOG_LEVEL="DEBUG"
```

支持的环境变量列表：

| 环境变量 | 配置键 | 说明 |
|---------|--------|------|
| `OPENAI_API_KEY` | `openai_api_key` | OpenAI API 密钥 |
| `OPENAI_MODEL` | `openai_model` | 模型名称 |
| `OPENAI_BASE_URL` | `openai_base_url` | API 基础 URL |
| `OPENAI_TIMEOUT` | `api.openai.timeout` | 请求超时时间 |
| `IMAGE_MODEL` | `image_model` | 图片生成模型 |
| `IMAGE_GENERATION_MODE` | `image_generation_mode` | 图片生成模式 |
| `TEMPLATE_STYLE` | `template_style` | 模板风格 |
| `ENABLE_AI_REWRITE` | `enable_ai_rewrite` | 启用 AI 改写 |
| `LOG_LEVEL` | `logging.level` | 日志级别 |
| `CACHE_ENABLED` | `cache.enabled` | 启用缓存 |

## 配置优先级

配置值按以下优先级加载（从低到高）：

1. **默认值** - 内置在 `ConfigManager.DEFAULT_CONFIG` 中
2. **配置文件** - `config/config.json` 或指定的配置文件
3. **环境变量** - 系统环境变量（优先级最高）

示例：

```python
# 默认值: openai_model = "qwen-plus"
# 配置文件: openai_model = "qwen-max"
# 环境变量: OPENAI_MODEL = "qwen-turbo"

# 最终结果: openai_model = "qwen-turbo" (环境变量优先)
```

## 高级功能

### 配置验证

配置管理器会自动验证配置的完整性：

```python
config = ConfigManager()

# 检查配置是否有效
if config.validate():
    print("✅ 配置验证通过")
else:
    print("❌ 配置验证失败")
    errors = config.get_validation_errors()
    for error in errors:
        print(f"  - {error}")
```

### 配置热重载

支持在运行时重新加载配置：

```python
config = ConfigManager()

# 手动重载
config.reload()

# 自动监控文件变化并重载
config.start_watching(check_interval=1.0)

# 注册重载回调
def on_config_reload():
    print("配置已重新加载")

config.register_reload_callback(on_config_reload)
```

### 配置来源追踪

查看配置值来自哪里：

```python
config = ConfigManager()

source = config.get_config_source('openai_model')
print(f"openai_model 来自: {source}")
# 输出: "environment" / "file" / "default"
```

## 向后兼容性

为了保持向后兼容，所有模块都支持两种初始化方式：

```python
# 新方式（推荐）
config_manager = ConfigManager()
generator = RedBookContentGenerator(config_manager=config_manager)

# 旧方式（仍然支持）
generator = RedBookContentGenerator(config_path="config/config.json")
```

## 常见问题

### Q: 我需要修改现有代码吗？

A: 不需要立即修改。旧的初始化方式仍然支持，但建议逐步迁移到新方式。

### Q: 如何在测试中使用？

A: 可以创建临时配置文件或使用环境变量：

```python
import tempfile
import json

# 创建临时配置
config_data = {
    "openai_api_key": "test-key",
    "openai_model": "qwen-plus"
}

with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(config_data, f)
    config_path = f.name

config = ConfigManager(config_path)
```

### Q: 环境变量的值会被保存到配置文件吗？

A: 不会。环境变量只在运行时覆盖配置，不会修改配置文件。

### Q: 如何禁用配置验证？

A: 配置验证是自动的，但不会阻止程序运行。如果验证失败，会在日志中记录警告。

### Q: 支持 YAML 配置文件吗？

A: 目前主要支持 JSON 格式。如需 YAML 支持，可以手动转换或提交功能请求。

## 迁移检查清单

- [ ] 已了解新的配置结构
- [ ] 已更新 `config/config.json` 文件
- [ ] 已将模块初始化改为使用 `ConfigManager`
- [ ] 已测试配置加载是否正常
- [ ] 已设置必要的环境变量（如 API Key）
- [ ] 已验证配置优先级是否符合预期
- [ ] 已更新相关文档和注释

## 示例代码

完整的迁移示例请参考：

- `examples/config_usage_example.py` - 基本用法示例
- `examples/config_hot_reload_example.py` - 热重载示例
- `src/content_generator.py` - 实际迁移案例
- `src/image_generator.py` - 实际迁移案例

## 获取帮助

如果在迁移过程中遇到问题，请：

1. 查看 `docs/CONFIG.md` 了解详细配置说明
2. 运行示例代码验证配置是否正确
3. 检查日志输出中的配置验证信息
4. 提交 Issue 描述您遇到的问题
