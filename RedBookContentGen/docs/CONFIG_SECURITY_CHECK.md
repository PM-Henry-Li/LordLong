# 配置安全检查

## 概述

配置安全检查脚本 (`scripts/check_config_security.py`) 用于检测配置文件中的安全问题，防止敏感信息（如 API Key、密码、Token）以明文形式存储在配置文件中。

## 主要功能

### 1. 安全问题检测

脚本会自动检测以下类型的敏感信息：

| 类型 | 严重级别 | 检测模式 | 示例 |
|------|----------|----------|------|
| API Key | 严重 | `sk-*`, `dashscope-*` | `sk-1234567890abcdef...` |
| 密码 | 严重 | 任何非空值 | `mypassword123` |
| Token | 严重 | 20+ 字符的字母数字 | `abc123def456ghi789...` |
| 密钥 | 严重 | 任何非空值 | `secret-key-value` |
| 认证信息 | 警告 | `Bearer *` | `Bearer your-token` |

### 2. 环境变量识别

脚本会自动识别并跳过安全的环境变量引用：

✅ **安全**（不会报告）：
```json
{
  "openai_api_key": "${OPENAI_API_KEY}",
  "database_url": "${DATABASE_URL:postgresql://localhost/db}"
}
```

❌ **不安全**（会报告）：
```json
{
  "openai_api_key": "sk-1234567890abcdefghijklmnopqrstuvwxyz",
  "password": "mypassword123"
}
```

### 3. 自动修复

脚本可以自动生成修复后的配置文件和环境变量文件：

```bash
python3 scripts/check_config_security.py --fix
```

生成的文件：
- `config/config.fixed.json` - 将敏感值替换为环境变量引用
- `.env.generated` - 包含所有敏感值的环境变量文件

## 使用方法

### 基本检查

```bash
# 检查默认配置文件
python3 scripts/check_config_security.py

# 检查指定配置文件
python3 scripts/check_config_security.py --config path/to/config.json
```

### 自动修复

```bash
# 生成修复文件（使用默认路径）
python3 scripts/check_config_security.py --fix

# 指定输出路径
python3 scripts/check_config_security.py --fix \
  --output config/config.safe.json \
  --env-output .env.production
```

### 完整修复流程

```bash
# 1. 检查配置
python3 scripts/check_config_security.py

# 2. 生成修复文件
python3 scripts/check_config_security.py --fix

# 3. 检查生成的文件
cat config/config.fixed.json
cat .env.generated

# 4. 应用修复
mv .env.generated .env
mv config/config.fixed.json config/config.json

# 5. 确保 .env 在 .gitignore 中
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# 6. 验证修复结果
python3 scripts/check_config_security.py
```

## 输出示例

### 发现问题时

```
🔍 正在检查配置文件安全性...

======================================================================
配置安全检查报告
======================================================================
配置文件: config/config.json
发现问题: 2 个 (严重: 2, 警告: 0, 信息: 0)
======================================================================

🔴 严重问题 (Critical)
----------------------------------------------------------------------

1. 发现明文 API Key: sk-1...wxyz
   位置: openai_api_key
   类型: api_key
   修复建议:
   建议使用环境变量:
     1. 在 .env 文件中设置: OPENAI_API_KEY=sk-1234567890...
     2. 在配置文件中引用: "${OPENAI_API_KEY}"
     3. 或直接使用环境变量: export OPENAI_API_KEY=sk-...

2. 发现明文密码: mypa...d123
   位置: database.password
   类型: password
   修复建议:
   建议使用环境变量:
     1. 在 .env 文件中设置: DATABASE_PASSWORD=mypassword123
     2. 在配置文件中引用: "${DATABASE_PASSWORD}"
     3. 或直接使用环境变量: export DATABASE_PASSWORD=...

======================================================================
修复步骤总结
======================================================================
1. 创建 .env 文件（如果不存在）
2. 将敏感信息移动到 .env 文件中
3. 在配置文件中使用 ${ENV_VAR} 语法引用环境变量
4. 确保 .env 文件已添加到 .gitignore
5. 重新运行此脚本验证修复结果

参考文档: docs/CONFIG.md
======================================================================
```

### 无问题时

```
🔍 正在检查配置文件安全性...

✅ 未发现安全问题！配置文件安全。
```

## 退出码

脚本使用不同的退出码表示检查结果：

| 退出码 | 含义 | 说明 |
|--------|------|------|
| 0 | 成功 | 未发现任何安全问题 |
| 1 | 警告 | 发现警告级别的问题 |
| 2 | 严重 | 发现严重级别的问题 |

可以在脚本或 CI/CD 中使用退出码：

```bash
#!/bin/bash
python3 scripts/check_config_security.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "配置安全检查通过"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "发现警告，请检查"
    exit 1
elif [ $EXIT_CODE -eq 2 ]; then
    echo "发现严重安全问题，必须修复"
    exit 1
fi
```

## CI/CD 集成

### GitHub Actions

```yaml
name: Config Security Check

on: [push, pull_request]

jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Check config security
        run: |
          python3 scripts/check_config_security.py --config config/config.example.json
```

### Pre-commit Hook

创建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash

# 检查配置文件安全性
if [ -f "config/config.json" ]; then
    python3 scripts/check_config_security.py --config config/config.json
    if [ $? -ne 0 ]; then
        echo "❌ 配置文件包含敏感信息，提交被拒绝"
        echo "   请运行: python3 scripts/check_config_security.py --fix"
        exit 1
    fi
fi

exit 0
```

## 最佳实践

### 1. 定期检查

建议在以下情况下运行安全检查：

- ✅ 修改配置文件后
- ✅ 提交代码前
- ✅ 部署到生产环境前
- ✅ 定期安全审计时

### 2. 环境变量管理

推荐的环境变量管理方式：

**开发环境**：
```bash
# .env 文件（不提交到 Git）
OPENAI_API_KEY=sk-your-dev-key
DATABASE_URL=postgresql://localhost/dev_db
```

**生产环境**：
- 使用云服务商的密钥管理服务（如 AWS Secrets Manager、Azure Key Vault）
- 使用容器编排工具的密钥管理（如 Kubernetes Secrets）
- 使用环境变量注入

### 3. .gitignore 配置

确保以下文件已添加到 `.gitignore`：

```gitignore
# 环境变量文件
.env
.env.*
!.env.example

# 包含敏感信息的配置文件
config/config.json
!config/config.example.json

# 自动生成的文件
.env.generated
config/config.fixed.json
```

### 4. 配置文件模板

使用 `config.example.json` 作为模板：

```json
{
  "openai_api_key": "${OPENAI_API_KEY}",
  "_comment": "请复制此文件为 config.json 并设置环境变量",
  "openai_model": "${OPENAI_MODEL:qwen-plus}"
}
```

## 故障排查

### 问题：脚本报告误报

**原因**：某些字段名包含敏感关键词但实际不是敏感信息

**解决方案**：
1. 检查字段值是否真的是敏感信息
2. 如果不是，可以忽略该警告
3. 如果是误报，可以修改字段名避免敏感关键词

### 问题：环境变量引用仍被报告

**原因**：环境变量引用格式不正确

**解决方案**：
确保使用正确的格式：
- ✅ `"${ENV_VAR}"`
- ✅ `"${ENV_VAR:default_value}"`
- ❌ `"$ENV_VAR"`
- ❌ `"${ENV_VAR"`

### 问题：修复后的配置文件无法使用

**原因**：环境变量未设置

**解决方案**：
1. 确保 .env 文件存在并包含所有必需的变量
2. 确保应用程序正确加载 .env 文件
3. 验证环境变量：`echo $OPENAI_API_KEY`

## 相关文档

- [配置管理文档](CONFIG.md) - 完整的配置系统说明
- [环境变量参考](ENV_VAR_REFERENCE.md) - 所有支持的环境变量
- [脚本使用说明](../scripts/README.md) - 脚本工具详细说明

## 技术实现

### 检测算法

1. **递归遍历**：递归遍历配置文件的所有键值对
2. **字段名匹配**：检查字段名是否包含敏感关键词
3. **值模式匹配**：使用正则表达式匹配敏感值模式
4. **环境变量识别**：跳过 `${ENV_VAR}` 格式的引用
5. **问题分类**：根据类型和严重程度分类问题

### 修复策略

1. **生成环境变量名**：将配置路径转换为大写下划线格式
2. **替换配置值**：将敏感值替换为环境变量引用
3. **保留结构**：保持原配置文件的结构和注释
4. **生成 .env**：创建包含所有敏感值的环境变量文件

## 更新日志

### v1.0.0 (2026-02-13)

- ✅ 初始版本发布
- ✅ 支持检测 API Key、密码、Token 等敏感信息
- ✅ 支持自动修复功能
- ✅ 支持环境变量引用识别
- ✅ 提供详细的安全报告
- ✅ 包含完整的单元测试

## 反馈与贡献

如果发现问题或有改进建议，请：

1. 查看现有的 Issues
2. 创建新的 Issue 描述问题
3. 提交 Pull Request 贡献代码

---

**最后更新**: 2026-02-13  
**版本**: v1.0.0
