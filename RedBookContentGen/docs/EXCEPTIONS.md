# 自定义异常使用指南

## 概述

本项目实现了一套完整的自定义异常体系，用于更好地分类和处理各种错误情况。所有自定义异常都继承自 `AppError` 基类，提供统一的错误信息格式和处理机制。

## 异常层次结构

```
AppError (基类)
├── ConfigError (配置错误)
│   ├── ConfigValidationError (配置验证错误)
│   └── ConfigMissingError (配置缺失错误)
├── APIError (API 错误)
│   ├── APITimeoutError (API 超时错误)
│   ├── APIRateLimitError (API 速率限制错误)
│   └── APIAuthenticationError (API 认证错误)
├── ContentError (内容错误)
│   ├── ContentValidationError (内容验证错误)
│   ├── ContentSafetyError (内容安全错误)
│   └── ContentGenerationError (内容生成错误)
├── FileError (文件错误)
│   ├── FileNotFoundError (文件不存在错误)
│   └── FilePermissionError (文件权限错误)
├── CacheError (缓存错误)
├── RateLimitError (速率限制错误)
└── ValidationError (验证错误)
```

## 基类 AppError

所有自定义异常的基类，提供以下功能：

### 属性

- `message`: 错误消息（中文）
- `code`: 错误代码（大写下划线格式）
- `details`: 错误详细信息（字典）

### 方法

- `to_dict()`: 将错误转换为字典格式，便于 JSON 序列化
- `__str__()`: 返回友好的错误字符串表示

### 使用示例

```python
from src.core.exceptions import AppError

# 创建基础错误
error = AppError(
    message="操作失败",
    code="OPERATION_FAILED",
    details={"operation": "save", "file": "data.json"}
)

# 转换为字典（用于 API 响应）
error_dict = error.to_dict()
# {
#     "error": {
#         "code": "OPERATION_FAILED",
#         "message": "操作失败",
#         "details": {"operation": "save", "file": "data.json"},
#         "type": "AppError"
#     }
# }

# 字符串表示
print(error)
# 操作失败 (代码: OPERATION_FAILED, 详情: {'operation': 'save', 'file': 'data.json'})
```

## 配置相关错误

### ConfigError

通用配置错误。

```python
from src.core.exceptions import ConfigError

raise ConfigError(
    message="配置加载失败",
    config_key="api.openai.key",
    details={"reason": "文件不存在"}
)
```

### ConfigValidationError

配置验证失败。

```python
from src.core.exceptions import ConfigValidationError

raise ConfigValidationError(
    message="配置类型错误",
    config_key="api.timeout",
    expected_type="int",
    actual_value="abc"
)
```

### ConfigMissingError

缺少必需的配置项。

```python
from src.core.exceptions import ConfigMissingError

raise ConfigMissingError(
    config_key="openai_api_key",
    suggestion="请在配置文件中添加 OPENAI_API_KEY，或设置环境变量"
)
```

## API 相关错误

### APIError

通用 API 调用错误。

```python
from src.core.exceptions import APIError

raise APIError(
    message="API 调用失败",
    api_name="OpenAI",
    status_code=500,
    response_body="Internal Server Error"
)
```

### APITimeoutError

API 调用超时。

```python
from src.core.exceptions import APITimeoutError

raise APITimeoutError(
    api_name="OpenAI",
    timeout=30,
    details={"endpoint": "/v1/chat/completions"}
)
```

### APIRateLimitError

超过 API 速率限制。

```python
from src.core.exceptions import APIRateLimitError

raise APIRateLimitError(
    api_name="OpenAI",
    retry_after=60,
    details={"limit_type": "RPM"}
)
```

### APIAuthenticationError

API 认证失败。

```python
from src.core.exceptions import APIAuthenticationError

raise APIAuthenticationError(
    api_name="OpenAI",
    suggestion="请检查 API Key 是否正确配置"
)
```

## 内容相关错误

### ContentValidationError

内容验证失败。

```python
from src.core.exceptions import ContentValidationError

raise ContentValidationError(
    message="输入文本过短",
    field="input_text",
    validation_rule="min_length",
    details={"min_length": 10, "actual_length": 5}
)
```

### ContentSafetyError

内容包含敏感词或不安全内容。

```python
from src.core.exceptions import ContentSafetyError

raise ContentSafetyError(
    message="内容包含敏感词",
    unsafe_content="测试内容...",
    matched_keywords=["敏感词1", "敏感词2"],
    details={"action": "removed"}
)
```

### ContentGenerationError

内容生成失败。

```python
from src.core.exceptions import ContentGenerationError

raise ContentGenerationError(
    message="内容生成失败，已达到最大尝试次数",
    generation_type="text",
    attempt=3,
    max_attempts=3,
    details={"last_error": "API timeout"}
)
```

## 文件相关错误

### FileNotFoundError

文件不存在。

```python
from src.core.exceptions import FileNotFoundError

raise FileNotFoundError(
    file_path="/path/to/file.txt",
    suggestion="请确保文件存在，或在配置中指定正确的路径"
)
```

### FilePermissionError

文件权限不足。

```python
from src.core.exceptions import FilePermissionError

raise FilePermissionError(
    file_path="/path/to/file.txt",
    operation="write",
    suggestion="请检查文件权限，确保程序有写入权限"
)
```

## 其他错误

### CacheError

缓存操作错误。

```python
from src.core.exceptions import CacheError

raise CacheError(
    message="缓存写入失败",
    cache_key="content:abc123",
    operation="set"
)
```

### RateLimitError

速率限制错误。

```python
from src.core.exceptions import RateLimitError

raise RateLimitError(
    message="超过速率限制",
    limiter_type="RPM",
    retry_after=30.0
)
```

### ValidationError

通用验证错误。

```python
from src.core.exceptions import ValidationError

raise ValidationError(
    message="字段验证失败",
    field="email",
    value="invalid-email",
    constraint="email_format"
)
```

## 异常包装

使用 `wrap_exception` 函数可以将标准 Python 异常包装为自定义异常：

```python
from src.core.exceptions import wrap_exception, APIError

try:
    # 可能抛出标准异常的代码
    response = requests.get("https://api.example.com")
    response.raise_for_status()
except requests.RequestException as e:
    # 包装为自定义异常
    raise wrap_exception(
        e,
        message="API 请求失败",
        exception_class=APIError,
        api_name="ExampleAPI"
    )
```

包装后的异常会保留原始异常信息：

```python
{
    "error": {
        "code": "API_ERROR",
        "message": "API 请求失败",
        "details": {
            "api_name": "ExampleAPI",
            "original_error": {
                "type": "RequestException",
                "message": "Connection timeout"
            }
        },
        "type": "APIError"
    }
}
```

## 最佳实践

### 1. 选择合适的异常类型

根据错误的性质选择最具体的异常类型：

```python
# ❌ 不好：使用通用异常
raise Exception("配置文件不存在")

# ✅ 好：使用具体的异常类型
raise ConfigMissingError(
    config_key="config_file",
    suggestion="请创建 config/config.json 文件"
)
```

### 2. 提供详细的错误信息

包含足够的上下文信息，帮助定位和解决问题：

```python
# ❌ 不好：信息不足
raise APIError("API 调用失败")

# ✅ 好：提供详细信息
raise APIError(
    message="OpenAI API 调用失败",
    api_name="OpenAI",
    status_code=500,
    response_body="Internal Server Error",
    details={
        "endpoint": "/v1/chat/completions",
        "model": "gpt-4",
        "request_id": "req-123"
    }
)
```

### 3. 添加修复建议

在错误消息中包含修复建议，提升用户体验：

```python
raise ConfigMissingError(
    config_key="openai_api_key",
    suggestion="请在配置文件中添加 OPENAI_API_KEY，或设置环境变量 OPENAI_API_KEY"
)
```

### 4. 使用异常链

保留原始异常信息，便于调试：

```python
try:
    # 可能失败的操作
    result = some_operation()
except ValueError as e:
    raise ContentValidationError(
        message="内容验证失败",
        field="content",
        details={"original_error": str(e)}
    ) from e  # 保留异常链
```

### 5. 在日志中记录异常

结合日志系统记录异常详情：

```python
from src.core.logger import Logger
from src.core.exceptions import APIError

try:
    # API 调用
    response = call_api()
except Exception as e:
    error = wrap_exception(
        e,
        exception_class=APIError,
        api_name="OpenAI"
    )
    
    Logger.error(
        "API 调用失败",
        logger_name="api_handler",
        error_code=error.code,
        error_details=error.details
    )
    
    raise error
```

## 错误处理模式

### 模式 1：捕获并重新抛出

```python
from src.core.exceptions import ContentGenerationError

def generate_content(text: str) -> dict:
    try:
        # 生成逻辑
        result = ai_generate(text)
        return result
    except Exception as e:
        raise ContentGenerationError(
            message="内容生成失败",
            generation_type="text",
            details={"error": str(e)}
        ) from e
```

### 模式 2：捕获并返回默认值

```python
from src.core.exceptions import CacheError
from src.core.logger import Logger

def get_from_cache(key: str) -> Optional[dict]:
    try:
        return cache.get(key)
    except CacheError as e:
        Logger.warning(
            "缓存读取失败，返回 None",
            logger_name="cache",
            error=str(e)
        )
        return None
```

### 模式 3：捕获并重试

```python
from src.core.exceptions import APITimeoutError
from src.core.retry_handler import retry

@retry(
    max_retries=3,
    exceptions=(APITimeoutError,),
    operation_name="API 调用"
)
def call_api():
    # API 调用逻辑
    pass
```

## Web API 错误响应

在 Web 应用中使用自定义异常：

```python
from flask import jsonify
from src.core.exceptions import AppError, ValidationError, APIError

@app.errorhandler(ValidationError)
def handle_validation_error(error: ValidationError):
    """处理验证错误"""
    return jsonify(error.to_dict()), 400

@app.errorhandler(APIError)
def handle_api_error(error: APIError):
    """处理 API 错误"""
    return jsonify(error.to_dict()), 502

@app.errorhandler(AppError)
def handle_app_error(error: AppError):
    """处理通用应用错误"""
    return jsonify(error.to_dict()), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        
        # 验证输入
        if not data.get('text'):
            raise ValidationError(
                message="缺少必需字段",
                field="text",
                constraint="required"
            )
        
        # 生成内容
        result = generator.generate(data['text'])
        return jsonify({"success": True, "data": result})
        
    except AppError:
        # 自定义异常会被错误处理器捕获
        raise
    except Exception as e:
        # 其他异常包装为 AppError
        raise wrap_exception(e)
```

## 测试

测试自定义异常：

```python
import pytest
from src.core.exceptions import ContentValidationError

def test_content_validation():
    """测试内容验证错误"""
    with pytest.raises(ContentValidationError) as exc_info:
        validate_content("")
    
    error = exc_info.value
    assert error.code == "CONTENT_VALIDATION_ERROR"
    assert "field" in error.details
```

## 总结

自定义异常体系的优势：

1. **类型安全**：通过异常类型快速识别错误类别
2. **信息丰富**：包含详细的错误上下文和修复建议
3. **易于处理**：统一的错误格式便于集中处理
4. **便于调试**：保留原始异常信息和调用栈
5. **用户友好**：提供中文错误消息和修复建议

## 相关文档

- [日志系统](./LOGGER.md)
- [重试处理](./CODE_REFACTORING_RETRY_ERROR_HANDLING.md)
- [API 处理器](./API_HANDLER.md)
