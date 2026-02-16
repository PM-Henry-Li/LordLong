# 敏感信息脱敏模式识别文档

## 文档概述

本文档识别了 RedBookContentGen 项目中需要在日志系统中进行脱敏处理的敏感信息模式。这些模式将用于实现日志脱敏功能（任务 10.2.2）。

**相关任务**: 10.2.1 识别需要脱敏的字段  
**需求引用**: 需求 3.4.1（敏感信息保护）  
**相关文件**: `src/core/logger.py`

---

## 1. API Key 模式

### 1.1 OpenAI/阿里云 DashScope API Key

**模式特征**:
- 以 `sk-` 开头，后跟 32 个或更多字母数字字符
- 以 `dashscope-` 开头，后跟 32 个或更多字母数字字符

**正则表达式**:
```python
r'(sk-[a-zA-Z0-9]{32,}|dashscope-[a-zA-Z0-9]{32,})'
```

**示例**:
- `sk-abc123def456ghi789jkl012mno345pqr678`
- `dashscope-xyz789abc456def123ghi890jkl567mno234`

**脱敏方式**:
- 显示前缀和后4位: `sk-***abc1`
- 显示前缀和后4位: `dashscope-***xyz9`

**严重级别**: 🔴 Critical（严重）

**出现位置**:
- 配置文件: `config.json` 中的 `openai_api_key` 字段
- 环境变量: `OPENAI_API_KEY`
- HTTP 请求头: `Authorization: Bearer sk-xxx`
- 日志上下文: `api_key`, `key` 等字段

---

## 2. 密码和认证信息

### 2.1 密码字段

**字段名称模式**（不区分大小写）:
- `password`
- `passwd`
- `pwd`

**正则表达式**:
```python
r'(?i)(password|passwd|pwd)'
```

**脱敏方式**:
- 完全隐藏: `***`

**严重级别**: 🔴 Critical（严重）

**出现位置**:
- SMTP 配置: `logging.alerting.notifiers.email.password`
- Elasticsearch 配置: `logging.collector.elasticsearch.password`
- HTTP 认证: `logging.collector.http.password`

### 2.2 Token 和 Secret

**字段名称模式**（不区分大小写）:
- `token`
- `secret`
- `secret_key`
- `access_key`
- `private_key`
- `credential`

**Token 值模式**:
- 20 个或更多字母数字字符、下划线、连字符

**正则表达式**:
```python
# 字段名
r'(?i)(token|secret|secret_key|access_key|private_key|credential)'

# Token 值
r'[a-zA-Z0-9_-]{20,}'
```

**脱敏方式**:
- 显示前4位和后4位: `abcd...xyz9`
- 如果长度 ≤ 8: `***`

**严重级别**: 🔴 Critical（严重）

### 2.3 Authorization Header

**模式特征**:
- Bearer Token: `Bearer <token>`
- Basic Auth: `Basic <base64>`

**正则表达式**:
```python
r'Bearer\s+[a-zA-Z0-9_-]+'
r'Basic\s+[a-zA-Z0-9+/=]+'
```

**脱敏方式**:
- `Bearer ***xyz9`
- `Basic ***abc=`

**严重级别**: 🟡 Warning（警告）

---

## 3. 用户敏感信息

### 3.1 手机号

**模式特征**:
- 中国大陆手机号: 11 位数字，以 1 开头
- 国际手机号: 带国家代码

**正则表达式**:
```python
# 中国大陆手机号
r'1[3-9]\d{9}'

# 国际手机号（带 + 或 00）
r'(\+|00)\d{1,3}[-\s]?\d{6,14}'
```

**脱敏方式**:
- 显示前3位和后4位: `138****5678`
- 国际号码: `+86****5678`

**严重级别**: 🟡 Warning（警告）

**出现位置**:
- 用户输入内容
- 日志上下文中的用户信息

### 3.2 邮箱地址

**模式特征**:
- 标准邮箱格式: `username@domain.com`

**正则表达式**:
```python
r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
```

**脱敏方式**:
- 显示用户名首字母和域名: `a***@example.com`
- 或显示前2位和后2位: `ab***yz@example.com`

**严重级别**: 🟡 Warning（警告）

**出现位置**:
- SMTP 配置: `from_addr`, `to_addrs`
- 用户输入内容
- 日志上下文中的用户信息

### 3.3 身份证号

**模式特征**:
- 18 位身份证号: 6位地区码 + 8位生日 + 3位顺序码 + 1位校验码

**正则表达式**:
```python
r'\d{17}[\dXx]'
```

**脱敏方式**:
- 显示前6位和后4位: `110101****1234`

**严重级别**: 🔴 Critical（严重）

**出现位置**:
- 用户输入内容（如果涉及实名认证）

---

## 4. URL 和连接字符串

### 4.1 数据库连接字符串

**模式特征**:
- PostgreSQL: `postgresql://user:password@host:port/database`
- MySQL: `mysql://user:password@host:port/database`
- MongoDB: `mongodb://user:password@host:port/database`

**正则表达式**:
```python
r'(postgresql|mysql|mongodb)://([^:]+):([^@]+)@([^/]+)/(.+)'
```

**脱敏方式**:
- 隐藏密码部分: `postgresql://user:***@host:port/database`

**严重级别**: 🔴 Critical（严重）

**出现位置**:
- 配置文件中的数据库连接字符串
- 环境变量: `DATABASE_URL`

### 4.2 带认证信息的 URL

**模式特征**:
- `http://username:password@host:port/path`
- `https://username:password@host:port/path`

**正则表达式**:
```python
r'https?://([^:]+):([^@]+)@(.+)'
```

**脱敏方式**:
- 隐藏密码: `https://username:***@host:port/path`

**严重级别**: 🟡 Warning（警告）

---

## 5. 敏感字段名称清单

以下字段名称（不区分大小写）在日志中出现时，其值应该被脱敏：

### 5.1 Critical 级别（完全隐藏或高度脱敏）

```python
CRITICAL_FIELD_NAMES = [
    'api_key',
    'apikey',
    'key',
    'password',
    'passwd',
    'pwd',
    'secret',
    'secret_key',
    'access_key',
    'private_key',
    'credential',
    'token',
    'auth_token',
    'access_token',
    'refresh_token',
    'id_card',
    'identity_card',
    'ssn',  # Social Security Number
]
```

### 5.2 Warning 级别（部分脱敏）

```python
WARNING_FIELD_NAMES = [
    'authorization',
    'auth',
    'phone',
    'mobile',
    'telephone',
    'email',
    'mail',
    'username',
    'user',
    'account',
]
```

---

## 6. 脱敏规则总结

### 6.1 脱敏策略

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

### 6.2 检测优先级

1. **字段名匹配**: 首先检查字段名是否在敏感字段列表中
2. **值模式匹配**: 然后检查值是否匹配敏感信息的正则表达式
3. **上下文分析**: 考虑字段所在的上下文（如 HTTP 头、配置等）

### 6.3 脱敏实现位置

脱敏应该在以下位置实现：

1. **日志格式化器** (`JSONFormatter`, `TextFormatter`)
   - 在 `format()` 方法中，输出前对敏感字段进行脱敏

2. **日志记录方法** (`Logger._log()`)
   - 在创建日志记录时，对 `extra_fields` 进行脱敏

3. **日志上下文** (`LogContext`)
   - 在设置上下文时，自动脱敏敏感字段

---

## 7. 实现建议

### 7.1 脱敏函数接口

```python
def mask_sensitive_data(data: Any, field_name: str = "") -> Any:
    """
    脱敏敏感数据
    
    Args:
        data: 要脱敏的数据（可以是字符串、字典、列表等）
        field_name: 字段名称（用于判断是否为敏感字段）
    
    Returns:
        脱敏后的数据
    """
    pass

def mask_api_key(value: str) -> str:
    """脱敏 API Key"""
    pass

def mask_password(value: str) -> str:
    """脱敏密码"""
    pass

def mask_phone(value: str) -> str:
    """脱敏手机号"""
    pass

def mask_email(value: str) -> str:
    """脱敏邮箱"""
    pass

def mask_token(value: str) -> str:
    """脱敏 Token"""
    pass
```

### 7.2 配置选项

建议在配置文件中添加脱敏相关配置：

```json
{
  "logging": {
    "masking": {
      "enabled": true,
      "mask_api_keys": true,
      "mask_passwords": true,
      "mask_tokens": true,
      "mask_phone_numbers": true,
      "mask_emails": true,
      "custom_patterns": [
        {
          "name": "custom_secret",
          "pattern": "secret_\\w+",
          "replacement": "***"
        }
      ]
    }
  }
}
```

---

## 8. 测试用例

### 8.1 API Key 脱敏测试

```python
def test_mask_api_key():
    # OpenAI API Key
    assert mask_api_key("sk-abc123def456ghi789jkl012mno345pqr678") == "sk-***r678"
    
    # DashScope API Key
    assert mask_api_key("dashscope-xyz789abc456def123ghi890jkl567mno234") == "dashscope-***o234"
```

### 8.2 密码脱敏测试

```python
def test_mask_password():
    assert mask_password("MyP@ssw0rd123") == "***"
    assert mask_password("") == ""
```

### 8.3 手机号脱敏测试

```python
def test_mask_phone():
    assert mask_phone("13812345678") == "138****5678"
    assert mask_phone("+8613812345678") == "+86****5678"
```

### 8.4 邮箱脱敏测试

```python
def test_mask_email():
    assert mask_email("user@example.com") == "u***@example.com"
    assert mask_email("admin@test.org") == "a***@test.org"
```

### 8.5 字典脱敏测试

```python
def test_mask_dict():
    data = {
        "api_key": "sk-abc123def456ghi789jkl012mno345pqr678",
        "password": "MyPassword123",
        "username": "admin",
        "normal_field": "normal_value"
    }
    
    masked = mask_sensitive_data(data)
    
    assert masked["api_key"] == "sk-***r678"
    assert masked["password"] == "***"
    assert masked["username"] == "admin"  # username 可能不需要完全隐藏
    assert masked["normal_field"] == "normal_value"
```

---

## 9. 安全注意事项

### 9.1 脱敏不是加密

- 脱敏只是隐藏部分信息，不能恢复原始值
- 不要依赖脱敏来保护敏感数据的存储
- 敏感数据应该使用加密存储

### 9.2 日志收集

- 确保日志收集系统（Elasticsearch、Logstash 等）也有适当的访问控制
- 脱敏后的日志仍然应该被视为敏感信息

### 9.3 性能考虑

- 脱敏操作会增加日志记录的开销
- 对于高频日志，考虑使用缓存或优化正则表达式
- 可以通过配置选项控制脱敏的严格程度

### 9.4 合规性

- 根据 GDPR、CCPA 等法规要求，某些个人信息必须脱敏
- 定期审查脱敏规则，确保符合最新的法规要求

---

## 10. 参考资料

- **需求文档**: `.kiro/specs/project-improvement/requirements.md` - 需求 3.4.1
- **设计文档**: `.kiro/specs/project-improvement/design.md` - 设计 3.1
- **配置安全检查**: `scripts/check_config_security.py`
- **配置示例**: `config/config.example.json`
- **环境变量示例**: `.env.example`

---

## 11. 下一步

完成本文档后，下一步任务：

- **任务 10.2.2**: 实现脱敏函数
  - 在 `src/core/logger.py` 中实现脱敏函数
  - 支持本文档中识别的所有敏感信息模式
  - 支持自定义脱敏规则

- **任务 10.2.3**: 集成到日志系统
  - 在日志格式化器中自动脱敏
  - 在日志上下文中自动脱敏
  - 添加配置选项控制脱敏行为

- **任务 10.2.4**: 编写测试
  - 单元测试覆盖所有脱敏函数
  - 集成测试验证日志输出
  - 性能测试评估脱敏开销

---

**文档版本**: 1.0  
**创建日期**: 2024-02-12  
**最后更新**: 2024-02-12  
**维护者**: Kiro AI Assistant
