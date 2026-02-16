# 验证错误处理文档

## 概述

验证错误处理模块提供了友好的中文错误消息、精确的错误字段定位和实用的修复建议，帮助开发者和用户快速理解和解决输入验证问题。

## 功能特性

### 1. 友好的中文错误消息

将 Pydantic 的英文错误消息转换为易于理解的中文消息：

- ✅ 字段名称中文化（例如：`input_text` → `输入文本`）
- ✅ 错误类型中文化（例如：`string_too_short` → `长度不能少于 X 个字符`）
- ✅ 包含具体的数值信息（当前值、期望值等）

### 2. 精确的错误字段定位

每个错误都包含：

- **field**: 字段路径（例如：`input_text`、`api.timeout`）
- **field_name**: 字段的中文名称
- **error_type**: 错误类型（例如：`missing`、`string_too_short`）

### 3. 实用的修复建议

针对常见错误提供具体的修复建议：

- 输入过短：建议提供更详细的内容
- 数值超限：建议调整到合理范围
- 格式错误：提供正确的格式示例
- 安全问题：提示避免使用危险字符

### 4. 统一的错误响应格式

所有验证错误都使用统一的 JSON 格式返回，便于前端处理。

## 快速开始

### 基本使用

```python
from pydantic import ValidationError
from src.models.requests import ContentGenerationRequest
from src.models.validation_errors import format_validation_error

try:
    request = ContentGenerationRequest(input_text="短")
except ValidationError as e:
    error_response = format_validation_error(e)
    print(error_response)
```

输出：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "input_text",
        "field_name": "输入文本",
        "message": "输入文本长度不能少于 10 个字符（当前：1 个字符）",
        "suggestions": [
          "请提供更详细的内容描述",
          "建议至少输入 10 个字符",
          "可以参考示例：记得小时候，老北京的胡同里..."
        ],
        "error_type": "string_too_short"
      }
    ],
    "total_errors": 1
  }
}
```

### Web API 集成

在 Flask 路由中使用：

```python
from flask import request, jsonify
from pydantic import ValidationError
from src.models.requests import ContentGenerationRequest
from src.models.validation_errors import format_validation_error

@app.route('/api/generate', methods=['POST'])
def generate_content():
    try:
        # 验证请求数据
        request_data = ContentGenerationRequest(**request.json)
        
        # 执行业务逻辑
        result = content_service.generate(request_data)
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except ValidationError as e:
        # 返回友好的错误响应
        error_response = format_validation_error(e)
        return jsonify(error_response), 400
```

## 错误响应格式

### 响应结构

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "字段路径",
        "field_name": "字段中文名称",
        "message": "友好的错误消息",
        "suggestions": ["修复建议1", "修复建议2"],
        "error_type": "错误类型"
      }
    ],
    "total_errors": 1
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 请求是否成功，验证错误时为 `false` |
| `error.code` | string | 错误代码，固定为 `VALIDATION_ERROR` |
| `error.message` | string | 错误总体描述 |
| `error.errors` | array | 错误详情列表 |
| `error.total_errors` | integer | 错误总数 |
| `errors[].field` | string | 字段路径 |
| `errors[].field_name` | string | 字段中文名称 |
| `errors[].message` | string | 友好的错误消息 |
| `errors[].suggestions` | array | 修复建议列表 |
| `errors[].error_type` | string | 错误类型 |

## 支持的错误类型

### 1. 必填字段缺失 (missing)

**示例**：

```python
ContentGenerationRequest()  # 缺少 input_text
```

**错误消息**：

```
输入文本是必填项
```

### 2. 字符串过短 (string_too_short)

**示例**：

```python
ContentGenerationRequest(input_text="短")
```

**错误消息**：

```
输入文本长度不能少于 10 个字符（当前：1 个字符）
```

**修复建议**：

- 请提供更详细的内容描述
- 建议至少输入 10 个字符
- 可以参考示例：记得小时候，老北京的胡同里...

### 3. 字符串过长 (string_too_long)

**示例**：

```python
ContentGenerationRequest(input_text="测试" * 3000)
```

**错误消息**：

```
输入文本长度不能超过 5000 个字符（当前：6000 个字符）
```

**修复建议**：

- 请精简输入内容
- 建议将长文本分段处理
- 单次输入不要超过 5000 个字符

### 4. 数值超出范围 (greater_than_equal / less_than_equal)

**示例**：

```python
ContentGenerationRequest(
    input_text="测试文本",
    count=20  # 超过最大值 10
)
```

**错误消息**：

```
生成数量必须小于或等于 10（当前：20）
```

**修复建议**：

- 单次生成数量不能超过 10
- 如需批量生成，建议分批处理

### 5. 枚举值无效 (value_error)

**示例**：

```python
ContentGenerationRequest(
    input_text="测试文本",
    style="invalid_style"
)
```

**错误消息**：

```
生成风格验证失败：风格必须是以下之一：retro_chinese, modern_minimal, vintage_film, warm_memory, ink_wash
```

### 6. XSS 攻击检测 (value_error)

**示例**：

```python
ContentGenerationRequest(
    input_text="<script>alert('xss')</script>测试"
)
```

**错误消息**：

```
输入文本验证失败：输入包含非法内容：包含 script 标签
```

**修复建议**：

- 请检查输入内容是否包含非法字符
- 确保输入包含有效的中文或英文内容
- 避免使用特殊符号和敏感词

### 7. 敏感词检测 (value_error)

**示例**：

```python
ContentGenerationRequest(
    input_text="包含暴力内容的文本"
)
```

**错误消息**：

```
输入文本验证失败：输入包含敏感词：暴力
```

### 8. 时间戳格式错误 (value_error)

**示例**：

```python
ImageGenerationRequest(
    prompt="测试",
    timestamp="2026-02-13"  # 错误格式
)
```

**错误消息**：

```
时间戳验证失败：时间戳格式必须为 YYYYMMDD_HHMMSS，例如：20260213_143000
```

**修复建议**：

- 时间戳格式必须为 YYYYMMDD_HHMMSS
- 示例：20260213_143000
- 请检查日期和时间是否有效

### 9. SQL 注入检测 (value_error)

**示例**：

```python
SearchRequest(keyword="test' OR '1'='1")
```

**错误消息**：

```
搜索关键词验证失败：关键词包含非法字符：'
```

**修复建议**：

- 关键词不能包含特殊字符
- 请使用普通的中文或英文字符

## 字段名称映射

所有字段都有对应的中文名称：

| 英文字段名 | 中文名称 |
|-----------|---------|
| `input_text` | 输入文本 |
| `count` | 生成数量 |
| `style` | 生成风格 |
| `temperature` | 生成温度 |
| `prompt` | 图片提示词 |
| `image_mode` | 图片模式 |
| `image_model` | 图片模型 |
| `template_style` | 模板风格 |
| `image_size` | 图片尺寸 |
| `title` | 标题 |
| `scene` | 场景描述 |
| `content_text` | 内容文本 |
| `task_id` | 任务ID |
| `timestamp` | 时间戳 |
| `task_index` | 任务索引 |
| `image_type` | 图片类型 |
| `page` | 页码 |
| `page_size` | 每页数量 |
| `keyword` | 搜索关键词 |
| `start_time` | 开始时间 |
| `end_time` | 结束时间 |
| `sort_by` | 排序字段 |
| `sort_order` | 排序顺序 |

## 高级用法

### 自定义错误处理

如果需要自定义错误处理逻辑，可以直接使用 `ValidationErrorHandler` 类：

```python
from src.models.validation_errors import ValidationErrorHandler

# 处理验证错误
error_response = ValidationErrorHandler.handle_validation_error(validation_error)

# 获取字段中文名称
field_name = ValidationErrorHandler._get_field_name("input_text")
# 返回：输入文本

# 获取修复建议
suggestions = ValidationErrorHandler._get_fix_suggestions("input_text", "string_too_short")
# 返回：["请提供更详细的内容描述", ...]
```

### 添加新的字段映射

如果需要添加新的字段名称映射，编辑 `src/models/validation_errors.py`：

```python
class ValidationErrorHandler:
    FIELD_NAMES = {
        # 现有映射...
        "new_field": "新字段的中文名称",
    }
```

### 添加新的修复建议

如果需要为特定字段和错误类型添加修复建议：

```python
class ValidationErrorHandler:
    FIX_SUGGESTIONS = {
        "new_field": {
            "string_too_short": [
                "建议1",
                "建议2",
            ],
        },
    }
```

## 前端集成示例

### JavaScript/TypeScript

```typescript
interface ValidationError {
  success: false;
  error: {
    code: 'VALIDATION_ERROR';
    message: string;
    errors: Array<{
      field: string;
      field_name: string;
      message: string;
      suggestions: string[];
      error_type: string;
    }>;
    total_errors: number;
  };
}

async function generateContent(data: any) {
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    
    const result = await response.json();
    
    if (!result.success) {
      // 显示验证错误
      result.error.errors.forEach(error => {
        console.error(`${error.field_name}: ${error.message}`);
        console.log('修复建议:', error.suggestions);
      });
    }
    
    return result;
  } catch (error) {
    console.error('请求失败:', error);
  }
}
```

### React 组件示例

```jsx
function ContentForm() {
  const [errors, setErrors] = useState([]);
  
  const handleSubmit = async (data) => {
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      const result = await response.json();
      
      if (!result.success) {
        setErrors(result.error.errors);
      } else {
        // 处理成功响应
      }
    } catch (error) {
      console.error('请求失败:', error);
    }
  };
  
  return (
    <div>
      {errors.map((error, index) => (
        <div key={index} className="error">
          <strong>{error.field_name}:</strong> {error.message}
          <ul>
            {error.suggestions.map((suggestion, i) => (
              <li key={i}>{suggestion}</li>
            ))}
          </ul>
        </div>
      ))}
      {/* 表单内容 */}
    </div>
  );
}
```

## 测试

运行单元测试：

```bash
python3 -m pytest tests/unit/test_validation_errors.py -v
```

运行示例代码：

```bash
python3 examples/validation_errors_example.py
```

## 最佳实践

### 1. 始终使用 format_validation_error

在 API 端点中始终使用 `format_validation_error` 函数来处理验证错误：

```python
try:
    request = ContentGenerationRequest(**data)
except ValidationError as e:
    return jsonify(format_validation_error(e)), 400
```

### 2. 记录验证错误

在生产环境中，建议记录验证错误以便分析：

```python
from src.core.logger import Logger

try:
    request = ContentGenerationRequest(**data)
except ValidationError as e:
    error_response = format_validation_error(e)
    Logger.warning("验证错误", error=error_response)
    return jsonify(error_response), 400
```

### 3. 提供清晰的错误反馈

在前端显示错误时，确保：

- 显示字段的中文名称
- 显示具体的错误消息
- 显示所有修复建议
- 使用醒目的样式突出错误

### 4. 定期更新错误消息

根据用户反馈，定期更新错误消息和修复建议，使其更加友好和实用。

## 相关文档

- [请求模型文档](REQUEST_MODELS.md) - 了解所有可用的请求模型
- [API 文档](API.md) - 了解 API 端点的使用方法
- [安全指南](SECURITY.md) - 了解输入验证的安全考虑

## 常见问题

### Q: 如何添加新的错误类型？

A: 在 `ValidationErrorHandler.ERROR_MESSAGES` 中添加新的错误类型模板。

### Q: 如何自定义错误消息？

A: 修改 `ValidationErrorHandler.ERROR_MESSAGES` 中的消息模板。

### Q: 如何处理嵌套字段的错误？

A: 错误处理器会自动处理嵌套字段，字段路径使用点号分隔（例如：`api.timeout`）。

### Q: 错误消息支持多语言吗？

A: 当前仅支持中文。如需支持多语言，可以扩展 `ValidationErrorHandler` 类添加语言参数。

## 更新日志

### v1.0.0 (2026-02-13)

- ✅ 初始版本发布
- ✅ 支持所有常见的验证错误类型
- ✅ 提供友好的中文错误消息
- ✅ 提供精确的错误字段定位
- ✅ 提供实用的修复建议
- ✅ 统一的错误响应格式
- ✅ 完整的单元测试覆盖
- ✅ 详细的使用示例和文档
