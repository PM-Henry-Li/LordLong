# 配置管理最佳实践

## 目录

- [安全性](#安全性)
- [环境管理](#环境管理)
- [性能优化](#性能优化)
- [调试技巧](#调试技巧)
- [常见场景](#常见场景)

## 安全性

### 1. 永远不要提交敏感信息

❌ **错误做法**：

```json
{
  "openai_api_key": "sk-abc123xyz789"
}
```

```bash
git add config/config.json
git commit -m "添加配置"  # 危险！API Key 会被提交
```

✅ **正确做法**：

```bash
# 使用环境变量
export OPENAI_API_KEY="sk-abc123xyz789"
```

```json
{
  "openai_api_key": ""
}
```

### 2. 使用 .env 文件管理本地环境变量

创建 `.env` 文件（确保在 `.gitignore` 中）：

```bash
# .env
OPENAI_API_KEY=sk-abc123xyz789
OPENAI_MODEL=qwen-max
IMAGE_GENERATION_MODE=api
```

使用 `python-dotenv` 加载：

```python
from dotenv import load_dotenv
load_dotenv()

# 环境变量会自动加载
config = ConfigManager()
```

### 3. 定期轮换 API Key

```bash
# 1. 在阿里云控制台创建新的 API Key
# 2. 更新环境变量
export OPENAI_API_KEY="new-api-key"

# 3. 重启应用或重新加载配置
config.reload()

# 4. 删除旧的 API Key
```

### 4. 使用密钥管理服务

对于生产环境，考虑使用专业的密钥管理服务：

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- 阿里云密钥管理服务（KMS）

## 环境管理

### 1. 为不同环境创建独立配置

```
config/
├── config.example.json      # 配置模板
├── config.dev.json          # 开发环境
├── config.test.json         # 测试环境
├── config.staging.json      # 预发布环境
└── config.prod.json         # 生产环境
```

**开发环境** (`config.dev.json`)：

```json
{
  "openai_model": "qwen-plus",
  "image_generation_mode": "template",
  "logging": {
    "level": "DEBUG"
  },
  "rate_limit": {
    "openai": {
      "enable_rate_limit": false
    }
  }
}
```

**生产环境** (`config.prod.json`)：

```json
{
  "openai_model": "qwen-max",
  "image_generation_mode": "api",
  "logging": {
    "level": "INFO"
  },
  "rate_limit": {
    "openai": {
      "enable_rate_limit": true,
      "requests_per_minute": 100
    }
  }
}
```

### 2. 使用环境变量切换配置

```bash
# 开发环境
export APP_ENV=dev
python run.py --config config/config.${APP_ENV}.json

# 生产环境
export APP_ENV=prod
python run.py --config config/config.${APP_ENV}.json
```

### 3. 配置继承

创建基础配置和环境特定配置：

```python
# config_loader.py
import json
from src.core.config_manager import ConfigManager

def load_config_with_inheritance(env='dev'):
    """加载带继承的配置"""
    # 加载基础配置
    base_config = ConfigManager('config/config.base.json')
    
    # 加载环境特定配置
    env_config = ConfigManager(f'config/config.{env}.json')
    
    # 合并配置（环境配置覆盖基础配置）
    # 实现配置合并逻辑...
    
    return merged_config
```

## 性能优化

### 1. 合理设置速率限制

根据您的 API 配额和使用场景设置：

**低频使用**（个人开发）：

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 20,
      "tokens_per_minute": 30000
    },
    "image": {
      "requests_per_minute": 5,
      "max_concurrent": 2
    }
  }
}
```

**高频使用**（生产环境）：

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 100,
      "tokens_per_minute": 150000
    },
    "image": {
      "requests_per_minute": 20,
      "max_concurrent": 5
    }
  }
}
```

### 2. 启用缓存

```json
{
  "cache": {
    "enabled": true,
    "ttl": 3600,
    "max_size": "1GB"
  }
}
```

**缓存策略建议**：

- 开发环境：短 TTL（1小时），便于测试
- 生产环境：长 TTL（24小时），提高性能
- 定期清理：避免缓存占用过多空间

### 3. 调整超时时间

根据网络状况和 API 响应时间调整：

```json
{
  "api": {
    "openai": {
      "timeout": 30
    },
    "image": {
      "timeout": 180
    }
  }
}
```

**建议**：

- 国内网络：30-60秒
- 国际网络：60-120秒
- 图片生成：180-300秒

### 4. 并发控制

```json
{
  "rate_limit": {
    "image": {
      "max_concurrent": 3
    }
  }
}
```

**建议**：

- 低配置机器：2-3 并发
- 高配置机器：5-10 并发
- 注意 API 限流：不要超过 API 提供商的限制

## 调试技巧

### 1. 启用调试日志

```bash
export LOG_LEVEL=DEBUG
python run.py
```

或在配置文件中：

```json
{
  "logging": {
    "level": "DEBUG",
    "format": "text"
  }
}
```

### 2. 查看配置来源

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()

# 查看关键配置的来源
print(f"API Key 来源: {config.get_config_source('openai_api_key')}")
print(f"模型来源: {config.get_config_source('openai_model')}")
print(f"超时设置来源: {config.get_config_source('api.openai.timeout')}")
```

### 3. 验证配置

```python
config = ConfigManager()

if not config.validate():
    print("配置验证失败：")
    for error in config.get_validation_errors():
        print(f"  ❌ {error}")
else:
    print("✅ 配置验证通过")
```

### 4. 导出当前配置

```python
config = ConfigManager()

# 导出所有配置（用于调试）
import json
print(json.dumps(config.get_all(), indent=2, ensure_ascii=False))
```

### 5. 配置热重载调试

```python
config = ConfigManager()

# 注册调试回调
def on_reload():
    print("配置已重新加载")
    print(f"当前模型: {config.get('openai_model')}")

config.register_reload_callback(on_reload)
config.start_watching()

# 修改配置文件后会自动触发回调
```

## 常见场景

### 场景 1：本地开发

```bash
# 使用模板模式，无需 API Key
export IMAGE_GENERATION_MODE=template
export LOG_LEVEL=DEBUG

python run.py
```

### 场景 2：测试 API 集成

```bash
# 使用测试 API Key
export OPENAI_API_KEY="test-key"
export OPENAI_MODEL="qwen-plus"
export IMAGE_GENERATION_MODE="api"

python run.py --config config/config.test.json
```

### 场景 3：批量生成（生产环境）

```json
{
  "openai_model": "qwen-max",
  "image_generation_mode": "api",
  "rate_limit": {
    "openai": {
      "requests_per_minute": 100,
      "enable_rate_limit": true
    },
    "image": {
      "requests_per_minute": 20,
      "max_concurrent": 5,
      "enable_rate_limit": true
    }
  },
  "cache": {
    "enabled": true,
    "ttl": 7200
  }
}
```

### 场景 4：CI/CD 环境

```yaml
# .github/workflows/test.yml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  OPENAI_MODEL: qwen-plus
  IMAGE_GENERATION_MODE: template
  LOG_LEVEL: INFO

steps:
  - name: Run tests
    run: python run.py --config config/config.ci.json
```

### 场景 5：Docker 部署

```dockerfile
# Dockerfile
FROM python:3.10-slim

# 复制配置模板
COPY config/config.example.json /app/config/config.json

# 使用环境变量覆盖配置
ENV OPENAI_API_KEY=""
ENV OPENAI_MODEL="qwen-plus"
ENV IMAGE_GENERATION_MODE="template"

CMD ["python", "run.py"]
```

```bash
# 运行容器时传入环境变量
docker run -e OPENAI_API_KEY="sk-xxx" your-image
```

### 场景 6：多用户环境

```python
# 为每个用户创建独立的配置实例
def create_user_config(user_id, api_key):
    """为用户创建配置"""
    config = ConfigManager()
    config.set('openai_api_key', api_key)
    config.set('output_image_dir', f'output/users/{user_id}/images')
    return config

# 使用
user_config = create_user_config('user123', 'sk-xxx')
generator = RedBookContentGenerator(config_manager=user_config)
```

## 配置检查清单

部署前检查：

- [ ] API Key 已设置（通过环境变量）
- [ ] 配置文件中没有敏感信息
- [ ] 速率限制已根据 API 配额设置
- [ ] 日志级别适合当前环境（生产环境使用 INFO）
- [ ] 超时时间已根据网络状况调整
- [ ] 缓存配置已启用（生产环境）
- [ ] 输出目录有写入权限
- [ ] 配置验证通过
- [ ] 已测试配置热重载（如果使用）
- [ ] 已设置监控和告警（生产环境）

## 故障排查

### 问题：配置未生效

**检查步骤**：

1. 确认配置优先级：环境变量 > 配置文件 > 默认值
2. 检查环境变量名称是否正确（大写，使用下划线）
3. 重新加载配置：`config.reload()`
4. 查看配置来源：`config.get_config_source(key)`

### 问题：API 调用失败

**检查步骤**：

1. 验证 API Key：`config.get('openai_api_key')`
2. 检查网络连接
3. 查看速率限制设置
4. 增加超时时间
5. 启用调试日志查看详细错误

### 问题：性能问题

**优化步骤**：

1. 启用缓存
2. 增加并发数
3. 调整速率限制
4. 使用更快的模型（qwen-turbo）
5. 使用模板模式而非 API 模式

## 相关文档

- [配置说明文档](CONFIG.md) - 完整配置项说明
- [配置迁移指南](CONFIG_MIGRATION_GUIDE.md) - 迁移到新配置系统
- [README.md](../README.md) - 项目使用说明
