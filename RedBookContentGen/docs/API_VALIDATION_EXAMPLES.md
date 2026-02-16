# API 验证示例文档

本文档展示了如何使用更新后的内容生成和图片生成 API，包括请求示例、响应示例和错误处理。

## 目录

- [内容生成 API](#内容生成-api)
  - [成功请求](#成功请求)
  - [验证错误示例](#验证错误示例)
- [图片生成 API](#图片生成-api)
  - [成功请求](#成功请求-1)
  - [验证错误示例](#验证错误示例-1)
- [错误响应格式](#错误响应格式)

---

## 内容生成 API

### 端点

```
POST /api/generate_content
```

### 成功请求

#### 请求示例

```bash
curl -X POST http://localhost:8080/api/generate_content \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息，邻里之间互相帮助，孩子们在胡同里嬉戏玩耍。",
    "count": 3,
    "style": "retro_chinese",
    "temperature": 0.8
  }'
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "titles": [
      "胡同里的老北京记忆",
      "那些年，我们在胡同里的时光",
      "老北京胡同：温暖的邻里情"
    ],
    "content": "记得小时候，老北京的胡同里总是充满了生活的气息...",
    "tags": ["老北京", "胡同", "童年", "回忆"],
    "image_prompts": [
      "老北京胡同，复古风格，温暖的阳光",
      "胡同里的孩子们，嬉戏玩耍，怀旧色调"
    ]
  }
}
```

### 验证错误示例

#### 1. 输入文本过短

**请求**:
```json
{
  "input_text": "短文本",
  "count": 1
}
```

**响应** (HTTP 400):
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
        "message": "输入文本长度不能少于 10 个字符（当前：3 个字符）",
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

#### 2. 输入文本过长

**请求**:
```json
{
  "input_text": "这是一段超过5000字符的文本...",
  "count": 1
}
```

**响应** (HTTP 400):
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
        "message": "输入文本长度不能超过 5000 个字符（当前：6000 个字符）",
        "suggestions": [
          "请精简输入内容",
          "建议将长文本分段处理",
          "单次输入不要超过 5000 个字符"
        ],
        "error_type": "string_too_long"
      }
    ],
    "total_errors": 1
  }
}
```

#### 3. 生成数量超出范围

**请求**:
```json
{
  "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息",
  "count": 15
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "count",
        "field_name": "生成数量",
        "message": "生成数量必须小于或等于 10（当前：15）",
        "suggestions": [
          "单次生成数量不能超过 10",
          "如需批量生成，建议分批处理"
        ],
        "error_type": "less_than_equal"
      }
    ],
    "total_errors": 1
  }
}
```

#### 4. 无效的风格

**请求**:
```json
{
  "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息",
  "count": 1,
  "style": "invalid_style"
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "style",
        "field_name": "生成风格",
        "message": "生成风格验证失败：风格必须是以下之一：retro_chinese, modern_minimal, vintage_film, warm_memory, ink_wash",
        "suggestions": [
          "请检查输入格式是否正确",
          "参考 API 文档了解详细要求"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 5. XSS 攻击防护

**请求**:
```json
{
  "input_text": "<script>alert('xss')</script>老北京的胡同",
  "count": 1
}
```

**响应** (HTTP 400):
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
        "message": "输入文本验证失败：输入包含非法内容：包含 script 标签",
        "suggestions": [
          "请检查输入内容是否包含非法字符",
          "确保输入包含有效的中文或英文内容",
          "避免使用特殊符号和敏感词"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 6. 敏感词过滤

**请求**:
```json
{
  "input_text": "这是一段包含暴力内容的文本，用于测试敏感词过滤功能",
  "count": 1
}
```

**响应** (HTTP 400):
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
        "message": "输入文本验证失败：输入包含敏感词：暴力",
        "suggestions": [
          "请检查输入内容是否包含非法字符",
          "确保输入包含有效的中文或英文内容",
          "避免使用特殊符号和敏感词"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 7. 批量生成质量检查

**请求**:
```json
{
  "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息",
  "count": 8,
  "temperature": 1.5
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "",
        "field_name": "",
        "message": "数据验证失败：批量生成时（数量 > 5），建议将温度设置为 1.0 或更低以保证质量",
        "suggestions": [
          "请检查输入格式是否正确",
          "参考 API 文档了解详细要求"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 8. 多个验证错误

**请求**:
```json
{
  "input_text": "短",
  "count": 20,
  "temperature": 3.0
}
```

**响应** (HTTP 400):
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
      },
      {
        "field": "count",
        "field_name": "生成数量",
        "message": "生成数量必须小于或等于 10（当前：20）",
        "suggestions": [
          "单次生成数量不能超过 10",
          "如需批量生成，建议分批处理"
        ],
        "error_type": "less_than_equal"
      },
      {
        "field": "temperature",
        "field_name": "生成温度",
        "message": "生成温度必须小于或等于 2.0（当前：3.0）",
        "suggestions": [
          "温度值不能超过 2.0",
          "较高的温度会导致输出不稳定"
        ],
        "error_type": "less_than_equal"
      }
    ],
    "total_errors": 3
  }
}
```

---

## 图片生成 API

### 端点

```
POST /api/generate_image
```

### 成功请求

#### 请求示例

```bash
curl -X POST http://localhost:8080/api/generate_image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "老北京胡同，复古风格，温暖的阳光",
    "image_mode": "template",
    "template_style": "retro_chinese",
    "image_size": "vertical",
    "title": "老北京的记忆",
    "scene": "夕阳下的胡同",
    "content_text": "记得小时候...",
    "task_id": "task_20260213_001",
    "timestamp": "20260213_143000",
    "task_index": 0,
    "image_type": "content"
  }'
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "image_url": "/api/download/images/20260213/image_001.png",
    "task_id": "task_20260213_001",
    "timestamp": "20260213_143000"
  }
}
```

### 验证错误示例

#### 1. 无效的时间戳格式

**请求**:
```json
{
  "prompt": "老北京胡同",
  "timestamp": "2026-02-13"
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "timestamp",
        "field_name": "时间戳",
        "message": "时间戳验证失败：时间戳格式必须为 YYYYMMDD_HHMMSS，例如：20260213_143000",
        "suggestions": [
          "时间戳格式必须为 YYYYMMDD_HHMMSS",
          "示例：20260213_143000",
          "请检查日期和时间是否有效"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 2. 无效的图片模式

**请求**:
```json
{
  "prompt": "老北京胡同",
  "image_mode": "invalid_mode",
  "timestamp": "20260213_143000"
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "image_mode",
        "field_name": "图片模式",
        "message": "图片模式验证失败：图片模式必须是 template, api 之一",
        "suggestions": [
          "请检查输入格式是否正确",
          "参考 API 文档了解详细要求"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 3. 无效的图片尺寸

**请求**:
```json
{
  "prompt": "老北京胡同",
  "image_size": "invalid_size",
  "timestamp": "20260213_143000"
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "image_size",
        "field_name": "图片尺寸",
        "message": "图片尺寸验证失败：图片尺寸必须是 vertical, horizontal, square 之一",
        "suggestions": [
          "请检查输入格式是否正确",
          "参考 API 文档了解详细要求"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

#### 4. 标题中的 XSS 攻击

**请求**:
```json
{
  "prompt": "老北京胡同",
  "title": "<script>alert('xss')</script>",
  "timestamp": "20260213_143000"
}
```

**响应** (HTTP 400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "title",
        "field_name": "标题",
        "message": "标题验证失败：文本包含非法内容：script 标签",
        "suggestions": [
          "请检查输入格式是否正确",
          "参考 API 文档了解详细要求"
        ],
        "error_type": "value_error"
      }
    ],
    "total_errors": 1
  }
}
```

---

## 错误响应格式

所有验证错误都遵循统一的响应格式：

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
        "suggestions": [
          "修复建议1",
          "修复建议2"
        ],
        "error_type": "错误类型"
      }
    ],
    "total_errors": 1
  }
}
```

### 字段说明

- **success**: 布尔值，表示请求是否成功
- **error.code**: 错误代码，验证错误固定为 `VALIDATION_ERROR`
- **error.message**: 错误总体描述
- **error.errors**: 错误详情数组
  - **field**: 字段路径（例如：`input_text`）
  - **field_name**: 字段的中文名称（例如：`输入文本`）
  - **message**: 友好的中文错误消息
  - **suggestions**: 修复建议数组
  - **error_type**: 错误类型（例如：`string_too_short`、`value_error`）
- **error.total_errors**: 错误总数

### 常见错误类型

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| `missing` | 缺少必填字段 | 未提供 `input_text` |
| `string_too_short` | 字符串过短 | 输入文本少于 10 个字符 |
| `string_too_long` | 字符串过长 | 输入文本超过 5000 个字符 |
| `greater_than_equal` | 数值小于最小值 | `count` 小于 1 |
| `less_than_equal` | 数值大于最大值 | `count` 大于 10 |
| `value_error` | 值验证失败 | 包含敏感词、XSS 攻击等 |
| `type_error` | 类型错误 | 期望数字但提供了字符串 |

---

## Python 客户端示例

### 成功请求

```python
import requests

# 内容生成
response = requests.post(
    'http://localhost:8080/api/generate_content',
    json={
        'input_text': '记得小时候，老北京的胡同里总是充满了生活的气息',
        'count': 3,
        'style': 'retro_chinese',
        'temperature': 0.8
    }
)

if response.status_code == 200:
    data = response.json()
    print('生成成功！')
    print('标题:', data['data']['titles'])
else:
    error = response.json()
    print('生成失败！')
    print('错误:', error['error']['message'])
    for err in error['error']['errors']:
        print(f"  - {err['field_name']}: {err['message']}")
        print(f"    建议: {', '.join(err['suggestions'])}")
```

### 错误处理

```python
import requests

def generate_content(input_text, count=1, style='retro_chinese', temperature=0.8):
    """
    生成小红书内容
    
    Args:
        input_text: 输入文本
        count: 生成数量
        style: 生成风格
        temperature: 生成温度
        
    Returns:
        生成结果或错误信息
    """
    try:
        response = requests.post(
            'http://localhost:8080/api/generate_content',
            json={
                'input_text': input_text,
                'count': count,
                'style': style,
                'temperature': temperature
            },
            timeout=30
        )
        
        data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': data['data']
            }
        else:
            # 处理验证错误
            error_messages = []
            for err in data['error']['errors']:
                error_messages.append({
                    'field': err['field_name'],
                    'message': err['message'],
                    'suggestions': err['suggestions']
                })
            
            return {
                'success': False,
                'errors': error_messages
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'errors': [{'message': '请求超时，请稍后重试'}]
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'errors': [{'message': f'网络错误: {str(e)}'}]
        }

# 使用示例
result = generate_content('记得小时候，老北京的胡同里总是充满了生活的气息', count=3)

if result['success']:
    print('生成成功！')
    print('标题:', result['data']['titles'])
else:
    print('生成失败！')
    for error in result['errors']:
        print(f"错误: {error['message']}")
        if 'suggestions' in error:
            print(f"建议: {', '.join(error['suggestions'])}")
```

---

## JavaScript 客户端示例

### 使用 Fetch API

```javascript
async function generateContent(inputText, options = {}) {
  try {
    const response = await fetch('http://localhost:8080/api/generate_content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input_text: inputText,
        count: options.count || 1,
        style: options.style || 'retro_chinese',
        temperature: options.temperature || 0.8,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      return {
        success: true,
        data: data.data,
      };
    } else {
      // 处理验证错误
      const errors = data.error.errors.map(err => ({
        field: err.field_name,
        message: err.message,
        suggestions: err.suggestions,
      }));

      return {
        success: false,
        errors: errors,
      };
    }
  } catch (error) {
    return {
      success: false,
      errors: [{ message: `网络错误: ${error.message}` }],
    };
  }
}

// 使用示例
generateContent('记得小时候，老北京的胡同里总是充满了生活的气息', { count: 3 })
  .then(result => {
    if (result.success) {
      console.log('生成成功！');
      console.log('标题:', result.data.titles);
    } else {
      console.log('生成失败！');
      result.errors.forEach(error => {
        console.log(`错误: ${error.message}`);
        if (error.suggestions) {
          console.log(`建议: ${error.suggestions.join(', ')}`);
        }
      });
    }
  });
```

---

## 总结

更新后的 API 提供了：

1. **统一的验证机制**: 使用 Pydantic 模型进行请求验证
2. **友好的错误消息**: 中文错误提示和修复建议
3. **详细的错误定位**: 精确指出哪个字段出错
4. **安全防护**: XSS 攻击、敏感词过滤等
5. **完整的文档**: 包含请求示例、响应示例和错误处理

这些改进大大提升了 API 的可用性和安全性。
