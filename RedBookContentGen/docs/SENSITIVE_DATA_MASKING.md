# 敏感信息脱敏使用指南

## 概述

RedBookContentGen 项目的日志系统内置了敏感信息脱敏功能，可以自动识别和脱敏日志中的敏感数据，包括：

- API Key、Token、密码等认证信息
- 手机号、邮箱、身份证等个人信息
- 数据库连接字符串、URL 等

## 自动脱敏

日志系统会自动脱敏以下类型的敏感信息：

### 1. API Key

```python
from src.core.logger import Logger

# 自动脱敏 API Key
Logger.info("API 调用", api_key="sk-abc123def456ghi789jkl012mno345pqr678")
# 输出: api_key=sk-***r678
```

支持的 API Key 格式：
- OpenAI API Key: `sk-xxx` → `sk-***xxx`
- DashScope API Key: `dashscope-xxx` → `dashscope-***xxx`

### 2. 密码

```python
# 自动脱敏密码
Logger.info("用户登录", password="MyPassword123")
# 输出: password=***
```

支持的密码字段名（不区分大小写）：
- `password`
- `passwd`
- `pwd`

### 3. Token

```python
# 自动脱敏 Token
Logger.info("认证", token="abcdefghijklmnopqrstuvwxyz")
# 输出: token=abcd...wxyz

Logger.info("认证", authorization="Bearer abc123def456ghi789")
# 输出: authorization=Bearer ***i789
```

### 4. 手机号

```python
# 自动脱敏手机号
Logger.info("用户信息", phone="13812345678")
# 输出: phone=138****5678

Logger.info("用户信息", mobile="+8613812345678")
# 输出: mobile=+86****5678
```

### 5. 邮箱

```python
# 自动脱敏邮箱
Logger.info("用户信息", email="user@example.com")
# 输出: email=u***@example.com
```

### 6. 身份证号

```python
# 自动脱敏身份证号
Logger.info("实名认证", id_card="110101199001011234")
# 输出: id_card=110101****1234
```

### 7. 数据库连接字符串

```python
# 自动脱敏数据库 URL
Logger.info("数据库连接", db_url="postgresql://user:password@host:5432/db")
# 输出: db_url=postgresql://user:***@host:5432/db
```

## 手动脱敏

如果需要在日志记录之外脱敏数据，可以使用 `mask_sensitive_data` 函数：

```python
from src.core.logger import mask_sensitive_data

# 脱敏字符串
masked = mask_sensitive_data("sk-abc123def456ghi789jkl012mno345pqr678")
print(masked)  # sk-***r678

# 脱敏字典
data = {
    "api_key": "sk-abc123",
    "password": "secret",
    "email": "user@example.com"
}
masked_data = mask_sensitive_data(data)
print(masked_data)
# {'api_key': 'sk-***', 'password': '***', 'email': 'u***@example.com'}

# 脱敏列表
items = ["sk-abc123", "user@example.com", "13812345678"]
masked_items = mask_sensitive_data(items)
print(masked_items)
# ['sk-***', 'u***@example.com', '138****5678']
```

## 嵌套结构脱敏

脱敏功能支持递归处理嵌套的字典和列表：

```python
from src.core.logger import Logger

# 嵌套结构会被递归脱敏
Logger.info("用户配置", config={
    "api_key": "sk-abc123",
    "database": {
        "url": "postgresql://user:password@host:5432/db",
        "password": "dbpass123"
    },
    "users": [
        {"email": "user1@example.com", "phone": "13812345678"},
        {"email": "user2@example.com", "phone": "19987654321"}
    ]
})

# 输出:
# config={
#     'api_key': 'sk-***',
#     'database': {
#         'url': 'postgresql://user:***@host:5432/db',
#         'password': '***'
#     },
#     'users': [
#         {'email': 'u***@example.com', 'phone': '138****5678'},
#         {'email': 'u***@example.com', 'phone': '199****4321'}
#     ]
# }
```

## 日志上下文脱敏

使用 `LogContext` 时，上下文中的敏感信息也会被自动脱敏：

```python
from src.core.logger import Logger, LogContext

with LogContext(
    api_key="sk-abc123def456ghi789jkl012mno345pqr678",
    password="secret",
    user_id="user123"
):
    Logger.info("处理请求")
    # 输出: 处理请求 | api_key=sk-***r678, password=***, user_id=user123
```

## 配置脱敏行为

可以通过 `configure_masking` 函数配置脱敏行为：

```python
from src.core.logger import configure_masking

# 禁用邮箱脱敏
configure_masking(mask_emails=False)

# 禁用所有脱敏
configure_masking(enabled=False)

# 重新启用脱敏
configure_masking(enabled=True)
```

可配置的选项：

- `enabled`: 是否启用脱敏（默认 `True`）
- `mask_api_keys`: 是否脱敏 API Key（默认 `True`）
- `mask_passwords`: 是否脱敏密码（默认 `True`）
- `mask_tokens`: 是否脱敏 Token（默认 `True`）
- `mask_phone_numbers`: 是否脱敏手机号（默认 `True`）
- `mask_emails`: 是否脱敏邮箱（默认 `True`）
- `mask_id_cards`: 是否脱敏身份证（默认 `True`）
- `mask_urls`: 是否脱敏 URL（默认 `True`）

## 敏感字段名清单

### Critical 级别（完全隐藏或高度脱敏）

以下字段名（不区分大小写）会被识别为 Critical 级别敏感字段：

- `api_key`, `apikey`, `key`
- `password`, `passwd`, `pwd`
- `secret`, `secret_key`
- `access_key`, `private_key`
- `credential`, `token`
- `auth_token`, `access_token`, `refresh_token`
- `id_card`, `identity_card`, `ssn`

### Warning 级别（部分脱敏）

以下字段名（不区分大小写）会被识别为 Warning 级别敏感字段：

- `authorization`, `auth`
- `phone`, `mobile`, `telephone`
- `email`, `mail`
- `username`, `user`, `account`

## 脱敏规则

| 敏感信息类型 | 脱敏方式 | 示例 |
|------------|---------|------|
| API Key (sk-) | 前缀 + *** + 后4位 | `sk-***abc1` |
| API Key (dashscope-) | 前缀 + *** + 后4位 | `dashscope-***xyz9` |
| 密码 | 完全隐藏 | `***` |
| Token (长) | 前4位 + *** + 后4位 | `abcd...xyz9` |
| Token (短) | 完全隐藏 | `***` |
| 手机号 | 前3位 + **** + 后4位 | `138****5678` |
| 邮箱 | 用户名首字母 + *** + @域名 | `a***@example.com` |
| 身份证 | 前6位 + **** + 后4位 | `110101****1234` |
| Bearer Token | Bearer + *** + 后4位 | `Bearer ***xyz9` |
| 数据库 URL | 隐藏密码部分 | `postgresql://user:***@host/db` |

## 性能优化

脱敏功能使用了以下性能优化措施：

1. **编译后的正则表达式**: 所有正则表达式在首次使用时编译并缓存
2. **延迟初始化**: 正则表达式只在需要时才编译
3. **高效的字段名匹配**: 使用集合（set）进行 O(1) 时间复杂度的字段名查找

## 安全注意事项

1. **脱敏不是加密**: 脱敏只是隐藏部分信息，不能恢复原始值
2. **不要依赖脱敏来保护存储**: 敏感数据应该使用加密存储
3. **日志收集系统**: 确保日志收集系统（Elasticsearch、Logstash 等）也有适当的访问控制
4. **脱敏后的日志仍然敏感**: 脱敏后的日志仍然应该被视为敏感信息

## 合规性

根据 GDPR、CCPA 等法规要求，某些个人信息必须脱敏。本脱敏功能可以帮助满足以下合规要求：

- **GDPR**: 个人数据保护（邮箱、手机号、身份证等）
- **CCPA**: 加州消费者隐私法案
- **PCI DSS**: 支付卡行业数据安全标准（密码、Token 等）

## 测试

项目包含完整的脱敏功能测试：

```bash
# 运行单元测试
python3 tests/unit/test_sensitive_data_masker.py

# 运行集成测试
python3 tests/unit/test_logger_masking_integration.py
```

## 参考资料

- **需求文档**: `.kiro/specs/project-improvement/requirements.md` - 需求 3.4.1
- **设计文档**: `.kiro/specs/project-improvement/design.md` - 设计 3.1
- **敏感数据模式**: `docs/SENSITIVE_DATA_PATTERNS.md`
- **配置文档**: `docs/CONFIG.md`

---

**文档版本**: 1.0  
**创建日期**: 2024-02-14  
**维护者**: Kiro AI Assistant
