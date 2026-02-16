# 配置说明文档

## 目录

- [概述](#概述)
- [配置文件](#配置文件)
- [配置项说明](#配置项说明)
- [环境变量](#环境变量)
- [配置优先级](#配置优先级)
- [配置验证](#配置验证)
- [最佳实践](#最佳实践)

## 概述

RedBookContentGen 使用统一的配置管理系统（`ConfigManager`），支持：

- 📁 JSON 格式配置文件
- 🌍 环境变量覆盖
- ✅ 自动配置验证
- 🔄 配置热重载
- 🎯 默认值回退

## 配置文件

### 配置文件位置

默认配置文件路径：`config/config.json`

您也可以指定自定义配置文件：

```bash
python run.py --config path/to/your/config.json
```

### 配置文件模板

使用 `config/config.example.json` 作为模板创建您的配置文件：

```bash
cp config/config.example.json config/config.json
```

**重要提示**：`config/config.json` 包含敏感信息（如 API Key），已被 `.gitignore` 忽略，不会提交到版本控制系统。

## 配置项说明

### 基础配置

#### `input_file`
- **类型**: `string`
- **默认值**: `"input/input_content.txt"`
- **说明**: 输入文本文件路径
- **示例**: `"input/my_content.txt"`

#### `output_excel`
- **类型**: `string`
- **默认值**: `"output/redbook_content.xlsx"`
- **说明**: 输出 Excel 文件路径
- **示例**: `"output/results.xlsx"`

#### `output_image_dir`
- **类型**: `string`
- **默认值**: `"output/images"`
- **说明**: 图片输出目录
- **示例**: `"output/my_images"`

### API 配置

#### `openai_api_key`
- **类型**: `string`
- **必填**: ✅ 是
- **说明**: OpenAI 兼容 API 的密钥（阿里云 DashScope API Key）
- **获取方式**: [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
- **示例**: `"sk-xxxxxxxxxxxxxxxx"`
- **安全建议**: 使用环境变量 `OPENAI_API_KEY` 而不是直接写在配置文件中

#### `openai_model`
- **类型**: `string`
- **默认值**: `"qwen-plus"`
- **说明**: 使用的 AI 模型
- **可选值**:
  - `"qwen-turbo"` - 快速模型，适合简单任务
  - `"qwen-plus"` - 平衡模型（推荐）
  - `"qwen-max"` - 最强模型，适合复杂任务
- **示例**: `"qwen-max"`

#### `openai_base_url`
- **类型**: `string`
- **默认值**: `"https://dashscope.aliyuncs.com/compatible-mode/v1"`
- **说明**: API 基础 URL
- **注意**: 使用阿里云通义千问时保持默认值即可

#### `image_model`
- **类型**: `string`
- **默认值**: `"wan2.2-t2i-flash"`
- **说明**: 图片生成模型（通义万相）
- **可选值**:
  - `"wan2.2-t2i-flash"` - 快速生成（推荐）
  - `"wan2.2-t2i-plus"` - 高质量生成
  - `"wanx-v1"` - 稳定版本
- **示例**: `"wan2.2-t2i-plus"`

### 图片生成配置

#### `image_generation_mode`
- **类型**: `string`
- **默认值**: `"template"`
- **说明**: 图片生成模式
- **可选值**:
  - `"template"` - 模板模式（离线，快速，免费）
  - `"api"` - API 模式（需要 API Key，生成真实图片）
- **示例**: `"api"`

#### `template_style`
- **类型**: `string`
- **默认值**: `"retro_chinese"`
- **说明**: 模板风格（仅在 template 模式下有效）
- **可选值**:
  - `"retro_chinese"` - 复古中国风
  - `"modern_minimal"` - 现代简约
  - `"vintage_film"` - 怀旧胶片
  - `"warm_memory"` - 温暖记忆
  - `"ink_wash"` - 水墨风格
- **示例**: `"warm_memory"`

### 功能开关

#### `enable_ai_rewrite`
- **类型**: `boolean`
- **默认值**: `false`
- **说明**: 是否启用 AI 改写功能
- **示例**: `true`

### API 详细配置

#### `api.openai.timeout`
- **类型**: `integer`
- **默认值**: `30`
- **单位**: 秒
- **说明**: OpenAI API 请求超时时间
- **示例**: `60`

#### `api.openai.max_retries`
- **类型**: `integer`
- **默认值**: `3`
- **说明**: API 请求失败时的最大重试次数
- **示例**: `5`

#### `api.image.size`
- **类型**: `string`
- **默认值**: `"1024*1365"`
- **说明**: 生成图片的尺寸
- **可选值**:
  - `"1024*1024"` - 正方形 (1:1)
  - `"1024*1365"` - 竖版 (3:4) - 小红书推荐
  - `"1365*1024"` - 横版 (4:3)
- **示例**: `"1024*1024"`

#### `api.image.timeout`
- **类型**: `integer`
- **默认值**: `180`
- **单位**: 秒
- **说明**: 图片生成 API 请求超时时间
- **示例**: `300`

### 缓存配置

#### `cache.enabled`
- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否启用缓存
- **示例**: `false`

#### `cache.ttl`
- **类型**: `integer`
- **默认值**: `3600`
- **单位**: 秒
- **说明**: 缓存过期时间（Time To Live）
- **示例**: `7200`

#### `cache.max_size`
- **类型**: `string`
- **默认值**: `"1GB"`
- **说明**: 缓存最大大小
- **示例**: `"2GB"`

### 速率限制配置

#### `rate_limit.openai.requests_per_minute`
- **类型**: `integer`
- **默认值**: `60`
- **说明**: OpenAI API 每分钟最大请求数
- **示例**: `100`

#### `rate_limit.openai.tokens_per_minute`
- **类型**: `integer`
- **默认值**: `90000`
- **说明**: OpenAI API 每分钟最大 token 数
- **示例**: `120000`

#### `rate_limit.openai.enable_rate_limit`
- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否启用 OpenAI API 速率限制
- **示例**: `false`

#### `rate_limit.image.requests_per_minute`
- **类型**: `integer`
- **默认值**: `10`
- **说明**: 图片生成 API 每分钟最大请求数
- **示例**: `20`

#### `rate_limit.image.enable_rate_limit`
- **类型**: `boolean`
- **默认值**: `true`
- **说明**: 是否启用图片生成 API 速率限制
- **示例**: `false`

#### `rate_limit.image.max_concurrent`
- **类型**: `integer`
- **默认值**: `3`
- **说明**: 图片生成最大并发数
- **示例**: `5`

### 日志配置

#### `logging.level`
- **类型**: `string`
- **默认值**: `"INFO"`
- **说明**: 日志级别
- **可选值**: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
- **示例**: `"DEBUG"`

#### `logging.format`
- **类型**: `string`
- **默认值**: `"json"`
- **说明**: 日志格式
- **可选值**: `"json"`, `"text"`
- **示例**: `"text"`

#### `logging.file`
- **类型**: `string`
- **默认值**: `"logs/app.log"`
- **说明**: 日志文件路径
- **示例**: `"logs/my_app.log"`

#### `logging.max_bytes`
- **类型**: `integer`
- **默认值**: `10485760` (10MB)
- **说明**: 单个日志文件最大大小（字节）
- **示例**: `20971520` (20MB)

#### `logging.backup_count`
- **类型**: `integer`
- **默认值**: `5`
- **说明**: 保留的日志文件备份数量
- **示例**: `10`

### 小红书搜索配置

#### `xiaohongshu.search_mode`
- **类型**: `string`
- **默认值**: `"browser"`
- **说明**: 搜索模式
- **可选值**: `"browser"`, `"api"`
- **示例**: `"browser"`

#### `xiaohongshu.browser_type`
- **类型**: `string`
- **默认值**: `"chrome"`
- **说明**: 浏览器类型
- **可选值**: `"chrome"`, `"firefox"`, `"edge"`
- **示例**: `"firefox"`

#### `xiaohongshu.headless`
- **类型**: `boolean`
- **默认值**: `false`
- **说明**: 是否使用无头浏览器模式
- **示例**: `true`

#### `xiaohongshu.max_search_results`
- **类型**: `integer`
- **默认值**: `10`
- **说明**: 最大搜索结果数量
- **示例**: `20`

#### `xiaohongshu.min_likes_threshold`
- **类型**: `integer`
- **默认值**: `1000`
- **说明**: 最小点赞数阈值
- **示例**: `5000`

#### `xiaohongshu.login_required`
- **类型**: `boolean`
- **默认值**: `false`
- **说明**: 是否需要登录
- **示例**: `true`

#### `xiaohongshu.request_delay`
- **类型**: `integer`
- **默认值**: `2`
- **单位**: 秒
- **说明**: 请求之间的延迟时间
- **示例**: `3`

## 环境变量

### 支持的环境变量

所有配置项都可以通过环境变量覆盖。环境变量名称规则：

1. 顶层配置：直接使用大写形式，如 `OPENAI_API_KEY`
2. 嵌套配置：使用下划线分隔，如 `RATE_LIMIT_OPENAI_RPM`

### 配置文件中引用环境变量

ConfigManager 支持在配置文件中使用 `${ENV_VAR}` 语法引用环境变量，提供更灵活的配置方式。

#### 基本语法

```json
{
  "openai_api_key": "${OPENAI_API_KEY}",
  "openai_model": "${OPENAI_MODEL}",
  "description": "Using ${OPENAI_MODEL} model"
}
```

#### 带默认值的语法

如果环境变量不存在，可以提供默认值：

```json
{
  "openai_model": "${OPENAI_MODEL:qwen-max}",
  "openai_base_url": "${OPENAI_BASE_URL:https://dashscope.aliyuncs.com/compatible-mode/v1}",
  "cache_ttl": "${CACHE_TTL:3600}"
}
```

语法说明：
- `${ENV_VAR}` - 引用环境变量，如果不存在则保留原始字符串
- `${ENV_VAR:default}` - 引用环境变量，如果不存在则使用默认值
- `${ENV_VAR:}` - 引用环境变量，如果不存在则使用空字符串

#### 嵌套配置中使用

```json
{
  "api": {
    "openai": {
      "key": "${OPENAI_API_KEY}",
      "timeout": "${OPENAI_TIMEOUT:30}",
      "base_url": "${OPENAI_BASE_URL:https://dashscope.aliyuncs.com/compatible-mode/v1}"
    }
  },
  "cache": {
    "enabled": true,
    "prefix": "cache_${OPENAI_MODEL:qwen-plus}"
  }
}
```

#### 列表中使用

```json
{
  "allowed_models": [
    "${PRIMARY_MODEL:qwen-max}",
    "${SECONDARY_MODEL:qwen-plus}",
    "qwen-turbo"
  ]
}
```

#### 优先级说明

当同时使用配置文件中的 `${ENV_VAR}` 引用和直接的环境变量映射时：

1. **直接环境变量映射**（如 `OPENAI_API_KEY`）优先级最高
2. **配置文件中的 `${ENV_VAR}` 引用**次之
3. **配置文件中的普通值**最低

示例：

```bash
# 设置环境变量
export OPENAI_API_KEY="direct-env-value"
export OPENAI_MODEL="qwen-max"
```

```json
{
  "openai_api_key": "${OPENAI_MODEL}",  // 会被 OPENAI_API_KEY 环境变量覆盖
  "openai_model": "qwen-plus"           // 会被 OPENAI_MODEL 环境变量覆盖
}
```

最终结果：
- `openai_api_key` = `"direct-env-value"` （直接环境变量映射）
- `openai_model` = `"qwen-max"` （直接环境变量映射）

### 常用环境变量

```bash
# API 配置
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
export OPENAI_MODEL="qwen-max"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# 图片配置
export IMAGE_MODEL="wan2.2-t2i-plus"
export IMAGE_GENERATION_MODE="api"
export TEMPLATE_STYLE="warm_memory"

# 功能开关
export ENABLE_AI_REWRITE="true"

# 日志配置
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="text"

# 缓存配置
export CACHE_ENABLED="true"
export CACHE_TTL="7200"

# 速率限制
export RATE_LIMIT_OPENAI_RPM="100"
export RATE_LIMIT_IMAGE_RPM="20"
```

### 在不同环境中设置

#### Linux / macOS

```bash
# 临时设置（当前会话）
export OPENAI_API_KEY="sk-xxx"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY="sk-xxx"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows (PowerShell)

```powershell
# 临时设置
$env:OPENAI_API_KEY="sk-xxx"

# 永久设置
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-xxx', 'User')
```

#### Docker

```bash
# 命令行传递
docker run -e OPENAI_API_KEY="sk-xxx" your-image

# 使用 .env 文件
docker run --env-file .env your-image
```

#### .env 文件

创建 `.env` 文件（不要提交到版本控制）：

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=qwen-max
IMAGE_GENERATION_MODE=api
LOG_LEVEL=DEBUG
```

## 配置优先级

配置值按以下优先级加载（从低到高）：

```
默认值 < 配置文件 < 环境变量
```

### 示例

假设有以下配置：

```python
# 1. 默认值（ConfigManager.DEFAULT_CONFIG）
openai_model = "qwen-plus"

# 2. 配置文件（config/config.json）
{
  "openai_model": "qwen-max"
}

# 3. 环境变量
export OPENAI_MODEL="qwen-turbo"
```

最终结果：`openai_model = "qwen-turbo"`（环境变量优先级最高）

### 查看配置来源

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

# 查看配置值来自哪里
source = config.get_config_source('openai_model')
print(f"openai_model 来自: {source}")
# 输出: "environment" / "file" / "default"
```

## 配置验证

### 自动验证

配置管理器会在加载时自动验证配置：

```python
config = ConfigManager()

if config.validate():
    print("✅ 配置验证通过")
else:
    print("❌ 配置验证失败")
    errors = config.get_validation_errors()
    for error in errors:
        print(f"  - {error}")
```

### 验证规则

配置验证包括以下检查：

1. **必填项检查**
   - `openai_api_key` 必须设置

2. **类型检查**
   - 数值类型配置必须是有效数字
   - 布尔类型配置必须是 true/false

3. **范围检查**
   - `api.openai.timeout` 必须 > 0
   - `api.openai.max_retries` 必须 >= 0
   - `rate_limit.*.requests_per_minute` 必须 > 0

4. **枚举值检查**
   - `openai_model` 必须是支持的模型之一
   - `image_generation_mode` 必须是 "template" 或 "api"
   - `template_style` 必须是支持的风格之一

5. **路径检查**
   - 输入文件路径必须存在（如果指定）
   - 输出目录必须可写

## 最佳实践

### 1. 使用环境变量存储敏感信息

❌ **不推荐**：在配置文件中直接写 API Key

```json
{
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

✅ **推荐**：使用环境变量

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

```json
{
  "openai_api_key": ""
}
```

### 2. 为不同环境使用不同配置

```bash
# 开发环境
python run.py --config config/config.dev.json

# 测试环境
python run.py --config config/config.test.json

# 生产环境
python run.py --config config/config.prod.json
```

### 3. 使用配置验证

在程序启动时验证配置：

```python
config = ConfigManager()

if not config.validate():
    errors = config.get_validation_errors()
    print("配置错误：")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
```

### 4. 合理设置速率限制

根据您的 API 配额设置合理的速率限制：

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000,
      "enable_rate_limit": true
    }
  }
}
```

### 5. 启用缓存提高性能

对于重复的内容生成，启用缓存可以显著提高性能：

```json
{
  "cache": {
    "enabled": true,
    "ttl": 3600
  }
}
```

### 6. 使用配置热重载

在长时间运行的服务中，使用配置热重载避免重启：

```python
config = ConfigManager()
config.start_watching(check_interval=1.0)

# 配置文件修改后会自动重新加载
```

### 7. 记录配置来源

在日志中记录关键配置的来源，便于调试：

```python
config = ConfigManager()

print(f"API Key 来源: {config.get_config_source('openai_api_key')}")
print(f"模型来源: {config.get_config_source('openai_model')}")
```

## 完整配置示例

### 开发环境配置

```json
{
  "openai_api_key": "",
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
  "cache": {
    "enabled": true,
    "ttl": 3600,
    "max_size": "1GB"
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
  },
  "logging": {
    "level": "DEBUG",
    "format": "text",
    "file": "logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 5
  }
}
```

### 生产环境配置

```json
{
  "openai_api_key": "",
  "openai_model": "qwen-max",
  "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "image_model": "wan2.2-t2i-plus",
  "image_generation_mode": "api",
  "enable_ai_rewrite": true,
  "api": {
    "openai": {
      "timeout": 60,
      "max_retries": 5
    },
    "image": {
      "size": "1024*1365",
      "timeout": 300
    }
  },
  "cache": {
    "enabled": true,
    "ttl": 7200,
    "max_size": "5GB"
  },
  "rate_limit": {
    "openai": {
      "requests_per_minute": 100,
      "tokens_per_minute": 150000,
      "enable_rate_limit": true
    },
    "image": {
      "requests_per_minute": 20,
      "enable_rate_limit": true,
      "max_concurrent": 5
    }
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/app.log",
    "max_bytes": 52428800,
    "backup_count": 10
  }
}
```

## 故障排除

### 问题：找不到配置文件

**错误信息**：`FileNotFoundError: config/config.json not found`

**解决方案**：
```bash
cp config/config.example.json config/config.json
```

### 问题：API Key 未设置

**错误信息**：`配置验证失败: openai_api_key 未设置`

**解决方案**：
```bash
export OPENAI_API_KEY="your-api-key"
```

### 问题：配置值类型错误

**错误信息**：`配置验证失败: api.openai.timeout 必须是数字`

**解决方案**：检查配置文件中的值类型是否正确
```json
{
  "api": {
    "openai": {
      "timeout": 30  // 数字，不是字符串 "30"
    }
  }
}
```

### 问题：环境变量未生效

**解决方案**：
1. 确认环境变量名称正确（大写，使用下划线）
2. 重新加载环境变量：`source ~/.bashrc`
3. 检查环境变量是否设置：`echo $OPENAI_API_KEY`

## 相关文档

- [配置迁移指南](CONFIG_MIGRATION_GUIDE.md) - 从旧配置系统迁移到新系统
- [README.md](../README.md) - 项目使用说明
- [AGENTS.md](../AGENTS.md) - 项目架构说明
