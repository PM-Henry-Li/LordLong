# 环境变量引用语法文档

## 概述

ConfigManager 支持在配置文件中使用 `${ENV_VAR}` 语法引用环境变量，提供更灵活和安全的配置管理方式。

## 功能特性

✅ **基本引用**: `${ENV_VAR}` - 引用环境变量  
✅ **默认值支持**: `${ENV_VAR:default}` - 提供默认值  
✅ **嵌套配置**: 支持在嵌套的 JSON 对象中使用  
✅ **列表支持**: 支持在数组中使用  
✅ **字符串插值**: 支持在字符串中间使用  
✅ **优先级管理**: 与直接环境变量映射协同工作  

## 语法说明

### 基本语法

```json
{
  "openai_api_key": "${OPENAI_API_KEY}"
}
```

- 如果环境变量 `OPENAI_API_KEY` 存在，使用其值
- 如果不存在，保留原始字符串 `"${OPENAI_API_KEY}"`

### 带默认值的语法

```json
{
  "openai_model": "${OPENAI_MODEL:qwen-max}",
  "timeout": "${TIMEOUT:30}",
  "empty_default": "${OPTIONAL_VAR:}"
}
```

- `${ENV_VAR:default}` - 如果环境变量不存在，使用 `default`
- `${ENV_VAR:}` - 如果环境变量不存在，使用空字符串

### 字符串插值

```json
{
  "description": "Using ${OPENAI_MODEL} model",
  "log_file": "logs/${ENV}.log",
  "cache_key": "cache_${USER}_${SESSION}"
}
```

可以在字符串中间使用环境变量引用。

### 嵌套配置

```json
{
  "api": {
    "openai": {
      "key": "${OPENAI_API_KEY}",
      "timeout": "${OPENAI_TIMEOUT:30}",
      "base_url": "${OPENAI_BASE_URL:https://api.default.com}"
    }
  }
}
```

支持在任意深度的嵌套配置中使用。

### 列表中使用

```json
{
  "allowed_models": [
    "${PRIMARY_MODEL:qwen-max}",
    "${SECONDARY_MODEL:qwen-plus}",
    "qwen-turbo"
  ]
}
```

可以在数组元素中使用环境变量引用。

## 配置优先级

ConfigManager 的配置优先级（从高到低）：

1. **直接环境变量映射** (最高优先级)
2. **配置文件中的 `${ENV_VAR}` 引用**
3. **配置文件中的普通值**
4. **默认值** (最低优先级)

### 优先级示例

```bash
# 设置环境变量
export OPENAI_API_KEY="direct-env-value"
export OPENAI_MODEL="qwen-max"
```

```json
{
  "openai_api_key": "${OPENAI_MODEL}",
  "openai_model": "qwen-plus"
}
```

**结果**：
- `openai_api_key` = `"direct-env-value"` (直接环境变量映射 `OPENAI_API_KEY`)
- `openai_model` = `"qwen-max"` (直接环境变量映射 `OPENAI_MODEL`)

**说明**：
- `OPENAI_API_KEY` 环境变量通过 `ENV_VAR_MAPPING` 直接映射到 `openai_api_key`，优先级最高
- `OPENAI_MODEL` 环境变量通过 `ENV_VAR_MAPPING` 直接映射到 `openai_model`，覆盖配置文件中的值

## 使用场景

### 1. 敏感信息保护

**不推荐** ❌：
```json
{
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

**推荐** ✅：
```json
{
  "openai_api_key": "${OPENAI_API_KEY}"
}
```

### 2. 多环境配置

```json
{
  "environment": "${ENV:development}",
  "openai_api_key": "${OPENAI_API_KEY}",
  "openai_model": "${OPENAI_MODEL:qwen-plus}",
  "logging": {
    "level": "${LOG_LEVEL:INFO}",
    "file": "logs/${ENV:dev}.log"
  }
}
```

**开发环境**：
```bash
export ENV="development"
export LOG_LEVEL="DEBUG"
```

**生产环境**：
```bash
export ENV="production"
export OPENAI_API_KEY="sk-prod-xxx"
export LOG_LEVEL="WARNING"
```

### 3. Docker 容器配置

**docker-compose.yml**：
```yaml
services:
  app:
    image: redbookcontent:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=qwen-max
      - ENV=production
    volumes:
      - ./config:/app/config
```

**config/config.json**：
```json
{
  "openai_api_key": "${OPENAI_API_KEY}",
  "openai_model": "${OPENAI_MODEL:qwen-plus}",
  "environment": "${ENV:development}"
}
```

### 4. CI/CD 流水线

**GitHub Actions**：
```yaml
- name: Run tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    OPENAI_MODEL: qwen-turbo
    ENV: test
  run: |
    python -m pytest
```

配置文件会自动使用这些环境变量。

## 最佳实践

### 1. 敏感信息管理

✅ **推荐做法**：
- 使用环境变量存储 API Key、密码等敏感信息
- 在配置文件中使用 `${ENV_VAR}` 引用
- 将 `.env` 文件添加到 `.gitignore`
- 提供 `.env.example` 作为模板

❌ **避免做法**：
- 在配置文件中明文存储敏感信息
- 将包含敏感信息的配置文件提交到版本控制

### 2. 默认值设置

✅ **推荐做法**：
```json
{
  "openai_model": "${OPENAI_MODEL:qwen-plus}",
  "timeout": "${TIMEOUT:30}",
  "cache_enabled": "${CACHE_ENABLED:true}"
}
```

为非敏感配置提供合理的默认值，简化配置。

### 3. 环境特定配置

✅ **推荐做法**：
```json
{
  "environment": "${ENV:development}",
  "debug": "${DEBUG:false}",
  "logging": {
    "level": "${LOG_LEVEL:INFO}",
    "file": "logs/${ENV:dev}.log"
  }
}
```

使用环境变量区分不同环境的配置。

### 4. 配置文档化

✅ **推荐做法**：
- 在 `.env.example` 中列出所有可用的环境变量
- 为每个环境变量添加注释说明
- 标注必填和可选变量
- 提供示例值

示例 `.env.example`：
```bash
# [必填] OpenAI API Key
# 获取方式：https://dashscope.console.aliyun.com/apiKey
OPENAI_API_KEY=your-api-key-here

# [可选] OpenAI 模型选择
# 可选值：qwen-turbo, qwen-plus, qwen-max
# 默认值：qwen-plus
OPENAI_MODEL=qwen-max

# [可选] 环境标识
# 可选值：development, staging, production
# 默认值：development
ENV=development
```

## 常见问题

### Q1: 环境变量不存在时会发生什么？

**A**: 取决于是否提供了默认值：
- `${ENV_VAR}` - 保留原始字符串 `"${ENV_VAR}"`
- `${ENV_VAR:default}` - 使用默认值 `"default"`
- `${ENV_VAR:}` - 使用空字符串 `""`

### Q2: 如何在配置文件中使用 `$` 字符？

**A**: 如果需要在配置中使用字面量 `$` 字符，确保它不符合 `${...}` 模式：
```json
{
  "price": "$100",
  "formula": "x + $y"
}
```

这些不会被解析为环境变量引用。

### Q3: 环境变量引用和直接环境变量映射有什么区别？

**A**: 
- **直接环境变量映射**: 通过 `ENV_VAR_MAPPING` 定义，优先级最高
- **环境变量引用**: 在配置文件中使用 `${ENV_VAR}`，优先级次之

示例：
```python
# ConfigManager 中的映射
ENV_VAR_MAPPING = {
    "OPENAI_API_KEY": "openai_api_key",  # 直接映射
}
```

```json
{
  "openai_api_key": "${MY_KEY}"  // 引用
}
```

如果同时设置了 `OPENAI_API_KEY` 和 `MY_KEY` 环境变量，`OPENAI_API_KEY` 会覆盖 `${MY_KEY}`。

### Q4: 可以在环境变量引用中使用嵌套吗？

**A**: 不支持嵌套引用。以下语法无效：
```json
{
  "key": "${${NESTED_VAR}}"  // ❌ 不支持
}
```

### Q5: 环境变量值的类型转换如何处理？

**A**: 
- 通过 `${ENV_VAR}` 引用的值始终是字符串
- 通过直接环境变量映射的值会自动类型转换（布尔、整数、浮点数）

示例：
```bash
export TIMEOUT="30"
export CACHE_ENABLED="true"
```

```json
{
  "timeout_ref": "${TIMEOUT}",        // 字符串 "30"
  "cache_ref": "${CACHE_ENABLED}"     // 字符串 "true"
}
```

如果需要类型转换，使用直接环境变量映射：
```bash
export OPENAI_TIMEOUT="30"           // 会被转换为整数 30
export CACHE_ENABLED="true"          // 会被转换为布尔值 True
```

## 示例代码

完整的示例代码请参考：
- `examples/env_var_reference_example.py` - 环境变量引用语法示例
- `examples/config_usage_example.py` - ConfigManager 使用示例

## 相关文档

- [配置说明文档](CONFIG.md) - 完整的配置项说明
- [配置迁移指南](CONFIG_MIGRATION_GUIDE.md) - 从旧配置迁移到新配置
- [.env.example](../.env.example) - 环境变量模板
- [config.example.json](../config/config.example.json) - 配置文件模板

## 安全提示

⚠️ **重要安全提示**：

1. **永远不要将包含敏感信息的配置文件提交到版本控制**
2. **使用 `.gitignore` 忽略 `.env` 和 `config/config.json`**
3. **定期更换 API Key 和密码**
4. **限制配置文件的访问权限**: `chmod 600 .env`
5. **在日志中脱敏敏感信息**
6. **使用环境变量或密钥管理服务存储敏感信息**

## 更新日志

### v1.0.0 (2026-02-13)
- ✨ 新增 `${ENV_VAR}` 基本语法支持
- ✨ 新增 `${ENV_VAR:default}` 默认值语法支持
- ✨ 支持在嵌套配置中使用
- ✨ 支持在列表中使用
- ✨ 支持字符串插值
- ✅ 完整的单元测试覆盖
- 📝 完善的文档和示例

