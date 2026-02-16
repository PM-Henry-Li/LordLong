# 配置快速参考

## 快速开始

```bash
# 1. 复制配置模板
cp config/config.example.json config/config.json

# 2. 设置 API Key
export OPENAI_API_KEY="your-api-key"

# 3. 运行
python run.py
```

## 常用环境变量

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `OPENAI_API_KEY` | API 密钥（必填） | `sk-xxx` |
| `OPENAI_MODEL` | AI 模型 | `qwen-plus` |
| `IMAGE_GENERATION_MODE` | 图片生成模式 | `template` / `api` |
| `TEMPLATE_STYLE` | 模板风格 | `retro_chinese` |
| `LOG_LEVEL` | 日志级别 | `DEBUG` / `INFO` |

## 配置文件结构

```json
{
  "openai_api_key": "",
  "openai_model": "qwen-plus",
  "image_generation_mode": "template",
  "template_style": "retro_chinese",
  "rate_limit": {
    "openai": {
      "requests_per_minute": 60
    },
    "image": {
      "requests_per_minute": 10,
      "max_concurrent": 3
    }
  }
}
```

## 代码示例

### 基本使用

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
api_key = config.get('openai_api_key')
model = config.get('openai_model')
```

### 访问嵌套配置

```python
timeout = config.get('api.openai.timeout')
rpm = config.get('rate_limit.openai.requests_per_minute')
```

### 配置验证

```python
if config.validate():
    print("✅ 配置正确")
else:
    errors = config.get_validation_errors()
    print("❌ 配置错误:", errors)
```

## 模型选择

| 模型 | 速度 | 质量 | 成本 | 适用场景 |
|------|------|------|------|---------|
| `qwen-turbo` | ⚡⚡⚡ | ⭐⭐ | 💰 | 简单任务 |
| `qwen-plus` | ⚡⚡ | ⭐⭐⭐ | 💰💰 | 日常使用（推荐） |
| `qwen-max` | ⚡ | ⭐⭐⭐⭐ | 💰💰💰 | 复杂任务 |

## 图片生成模式

### Template 模式（推荐）

```bash
export IMAGE_GENERATION_MODE=template
export TEMPLATE_STYLE=retro_chinese
```

- ✅ 离线运行，无需 API Key
- ✅ 速度快（秒级）
- ✅ 零成本
- ❌ 模板风格，非真实照片

### API 模式

```bash
export IMAGE_GENERATION_MODE=api
export IMAGE_MODEL=wan2.2-t2i-flash
```

- ✅ AI 生成真实图片
- ❌ 需要 API Key
- ❌ 速度慢（30秒-2分钟/张）
- ❌ 消耗配额

## 模板风格

| 风格 | 代码 | 特点 |
|------|------|------|
| 复古中国风 | `retro_chinese` | 怀旧、温暖、传统 |
| 现代简约 | `modern_minimal` | 简洁、清爽、现代 |
| 怀旧胶片 | `vintage_film` | 胶片质感、复古 |
| 温暖记忆 | `warm_memory` | 温馨、柔和 |
| 水墨风格 | `ink_wash` | 中国风、艺术感 |

## 速率限制建议

### 个人开发

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 20
    },
    "image": {
      "requests_per_minute": 5,
      "max_concurrent": 2
    }
  }
}
```

### 生产环境

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 100
    },
    "image": {
      "requests_per_minute": 20,
      "max_concurrent": 5
    }
  }
}
```

## 日志级别

| 级别 | 用途 | 输出内容 |
|------|------|---------|
| `DEBUG` | 开发调试 | 所有详细信息 |
| `INFO` | 正常运行 | 关键操作信息 |
| `WARNING` | 警告 | 潜在问题 |
| `ERROR` | 错误 | 错误信息 |

## 配置优先级

```
环境变量 > 配置文件 > 默认值
```

示例：
```bash
# 默认值: qwen-plus
# 配置文件: qwen-max
export OPENAI_MODEL=qwen-turbo

# 最终结果: qwen-turbo（环境变量优先）
```

## 常用命令

```bash
# 指定配置文件
python run.py --config config/custom.json

# 跳过图片生成
python run.py --skip-images

# 使用模板模式
python run.py --image-mode template

# 指定模板风格
python run.py --image-mode template --style warm_memory

# 主题搜索模式
python run.py --mode topic --topic "老北京胡同"
```

## 故障排查

### API Key 未设置

```bash
export OPENAI_API_KEY="your-key"
```

### 配置文件不存在

```bash
cp config/config.example.json config/config.json
```

### 配置验证失败

```python
config = ConfigManager()
errors = config.get_validation_errors()
print(errors)
```

### 查看配置来源

```python
source = config.get_config_source('openai_model')
print(f"来源: {source}")  # environment / file / default
```

## 获取帮助

- 📖 [完整配置文档](CONFIG.md)
- 🔄 [配置迁移指南](CONFIG_MIGRATION_GUIDE.md)
- 💡 [最佳实践](CONFIG_BEST_PRACTICES.md)
- 📝 [README](../README.md)

## 示例代码

完整示例请查看：
- `examples/config_usage_example.py`
- `examples/config_hot_reload_example.py`
