# 错误处理文档

## 概述

本项目实现了统一的错误处理机制，确保所有 API 接口返回一致的错误格式，提供友好的错误消息和解决建议。

## 错误响应格式

所有错误响应遵循统一的 JSON 格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误描述",
    "details": {
      "field": "具体字段",
      "additional_info": "额外信息"
    },
    "suggestions": [
      "解决建议1",
      "解决建议2"
    ]
  }
}
```

### 字段说明

- **success**: 布尔值，始终为 `false`
- **error.code**: 错误代码（字符串），用于程序化处理
- **error.message**: 用户友好的中文错误描述
- **error.details**: 可选，包含错误的详细信息
- **error.suggestions**: 可选，提供解决问题的建议

## 错误代码

### 客户端错误 (4xx)

| 错误代码 | HTTP 状态码 | 说明 |
|---------|-----------|------|
| `INVALID_REQUEST` | 400 | 无效请求 |
| `INVALID_INPUT` | 400 | 输入验证失败 |
| `INVALID_JSON` | 400 | JSON 格式错误 |
| `MISSING_FIELD` | 400 | 缺少必需字段 |
| `INVALID_FIELD` | 400 | 字段值无效 |
| `RESOURCE_NOT_FOUND` | 404 | 资源不存在 |

### 服务器错误 (5xx)

| 错误代码 | HTTP 状态码 | 说明 |
|---------|-----------|------|
| `INTERNAL_ERROR` | 500 | 内部错误 |
| `SERVICE_ERROR` | 500 | 服务错误 |
| `API_ERROR` | 502 | 外部 API 错误 |
| `GENERATION_ERROR` | 500 | 生成失败 |

### 业务错误

| 错误代码 | HTTP 状态码 | 说明 |
|---------|-----------|------|
| `CONTENT_GENERATION_FAILED` | 500 | 内容生成失败 |
| `IMAGE_GENERATION_FAILED` | 500 | 图片生成失败 |
| `DOWNLOAD_FAILED` | 500 | 下载失败 |

## 错误类型

### ValidationError

输入验证失败错误（HTTP 400）

**示例**：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "输入文本不能为空",
    "details": {
      "field": "input_text"
    },
    "suggestions": [
      "请输入至少10个字符的内容描述"
    ]
  }
}
```

### ResourceNotFoundError

资源不存在错误（HTTP 404）

**示例**：

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "文件不存在",
    "details": {
      "resource_type": "图片文件",
      "resource_id": "test.png"
    },
    "suggestions": [
      "请检查资源路径是否正确",
      "资源可能已被删除"
    ]
  }
}
```

### ContentGenerationError

内容生成失败错误（HTTP 500）

**示例**：

```json
{
  "success": false,
  "error": {
    "code": "CONTENT_GENERATION_FAILED",
    "message": "文案生成失败: API调用超时",
    "details": {
      "input_preview": "老北京胡同的记忆..."
    },
    "suggestions": [
      "请检查输入文本是否符合要求",
      "请稍后重试",
      "如果问题持续，请联系技术支持"
    ]
  }
}
```

### ImageGenerationError

图片生成失败错误（HTTP 500）

**示例**：

```json
{
  "success": false,
  "error": {
    "code": "IMAGE_GENERATION_FAILED",
    "message": "图片生成失败（已重试5次）",
    "details": {
      "task_id": "cover",
      "model": "wan2.2-t2i-flash",
      "last_error": "API未返回URL",
      "retries": 5
    },
    "suggestions": [
      "请检查图片生成参数是否正确",
      "请稍后重试",
      "可以尝试切换到模板模式"
    ]
  }
}
```

### APIError

外部 API 调用失败错误（HTTP 502）

**示例**：

```json
{
  "success": false,
  "error": {
    "code": "API_ERROR",
    "message": "外部服务调用失败",
    "details": {
      "api_name": "OpenAI",
      "status_code": 429
    },
    "suggestions": [
      "外部服务暂时不可用",
      "请稍后重试",
      "如果问题持续，请联系技术支持"
    ]
  }
}
```

## 使用方法

### 在路由中使用错误处理装饰器

```python
from flask import Blueprint, jsonify
from src.web.error_handlers import handle_errors
from src.core.errors import ValidationError, ResourceNotFoundError

api_bp = Blueprint('api', __name__)

@api_bp.route('/example', methods=['POST'])
@handle_errors
def example_route():
    # 抛出验证错误
    if not request.json:
        raise ValidationError(
            message="请求体不能为空",
            suggestions=["请提供 JSON 格式的请求体"]
        )
    
    # 抛出资源不存在错误
    if not file_exists:
        raise ResourceNotFoundError(
            message="文件不存在",
            resource_type="图片",
            resource_id=filename
        )
    
    # 正常返回
    return jsonify({"success": True, "data": result})
```

### 在服务层抛出错误

```python
from src.core.errors import ContentGenerationError, ImageGenerationError

class ContentService:
    def generate_content(self, input_text: str):
        try:
            # 生成逻辑
            result = self.generator.generate(input_text)
            return result
        except Exception as e:
            raise ContentGenerationError(
                message=f"文案生成失败: {str(e)}",
                details={"input_preview": input_text[:50]},
                suggestions=[
                    "请检查输入文本是否符合要求",
                    "请稍后重试"
                ]
            )
```

### 注册全局错误处理器

在 `web_app.py` 中：

```python
from flask import Flask
from src.web.error_handlers import register_error_handlers

app = Flask(__name__)

# 注册全局错误处理器
register_error_handlers(app)
```

这将自动处理以下 HTTP 错误：
- 400 Bad Request
- 404 Not Found
- 405 Method Not Allowed
- 500 Internal Server Error

## 调试模式

在调试模式下（`DEBUG=True`），错误响应会包含额外的调试信息：

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务器内部错误",
    "traceback": "Traceback (most recent call last):\n  ...",
    "original_error": "division by zero"
  }
}
```

**注意**：生产环境中应禁用调试模式，避免泄露敏感信息。

## 最佳实践

### 1. 使用合适的错误类型

根据错误的性质选择合适的错误类型：

- 用户输入错误 → `ValidationError`
- 资源不存在 → `ResourceNotFoundError`
- 业务逻辑错误 → `ContentGenerationError` 或 `ImageGenerationError`
- 外部服务错误 → `APIError`

### 2. 提供详细的错误信息

在 `details` 字段中包含有助于调试的信息：

```python
raise ImageGenerationError(
    message="图片生成失败",
    details={
        "task_id": task_id,
        "model": image_model,
        "last_error": str(last_error),
        "retries": max_retries
    }
)
```

### 3. 提供有用的建议

在 `suggestions` 字段中提供用户可以采取的行动：

```python
raise ValidationError(
    message="输入文本过短",
    details={"current_length": len(text), "min_length": 10},
    suggestions=[
        "请输入至少10个字符的内容描述",
        "可以参考示例：记得小时候..."
    ]
)
```

### 4. 不要泄露敏感信息

错误消息中不应包含：
- API 密钥
- 数据库连接字符串
- 内部路径
- 用户隐私信息

### 5. 记录错误日志

所有错误都会自动记录到日志系统中，包含完整的堆栈跟踪和上下文信息。

## 前端处理示例

### JavaScript

```javascript
async function generateContent(inputText) {
  try {
    const response = await fetch('/api/generate_content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ input_text: inputText })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      // 显示错误消息
      showError(data.error.message);
      
      // 显示建议
      if (data.error.suggestions) {
        showSuggestions(data.error.suggestions);
      }
      
      return null;
    }
    
    return data.data;
    
  } catch (error) {
    showError('网络错误，请检查网络连接');
    return null;
  }
}

function showError(message) {
  // 显示错误提示
  alert(message);
}

function showSuggestions(suggestions) {
  // 显示建议列表
  console.log('建议：', suggestions);
}
```

## 测试

错误处理功能包含完整的单元测试，位于 `tests/unit/test_error_handlers.py`。

运行测试：

```bash
python3 -m pytest tests/unit/test_error_handlers.py -v
```

## 相关文件

- `src/core/errors.py` - 错误类型定义
- `src/web/error_handlers.py` - 错误处理装饰器和全局处理器
- `src/web/blueprints/api.py` - API 路由（应用错误处理）
- `src/services/content_service.py` - 内容服务（抛出业务错误）
- `src/services/image_service.py` - 图片服务（抛出业务错误）
- `tests/unit/test_error_handlers.py` - 单元测试

## 更新日志

### 2026-02-13
- 创建统一的错误响应格式
- 实现错误处理装饰器
- 应用到所有 API 路由
- 添加完整的单元测试
- 编写错误处理文档
