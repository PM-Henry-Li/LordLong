# 搜索 API 文档

## 概述

搜索 API 提供了通用的搜索接口，支持关键词搜索、分页、时间范围过滤和排序功能。接口已集成 Pydantic 验证模型，确保输入安全和数据有效性。

## 接口信息

- **路径**: `/api/search`
- **方法**: `GET`
- **验证模型**: `SearchRequest`
- **需求引用**: 需求 3.4.2（输入验证）

## 查询参数

| 参数名 | 类型 | 必填 | 默认值 | 范围/格式 | 说明 |
|--------|------|------|--------|-----------|------|
| `page` | int | 否 | 1 | ≥ 1 | 页码，从 1 开始 |
| `page_size` | int | 否 | 50 | 1-200 | 每页数量 |
| `keyword` | string | 否 | null | 最大 200 字符 | 搜索关键词 |
| `start_time` | string | 否 | null | ISO 8601 格式 | 开始时间（YYYY-MM-DDTHH:MM:SS） |
| `end_time` | string | 否 | null | ISO 8601 格式 | 结束时间（YYYY-MM-DDTHH:MM:SS） |
| `sort_by` | string | 否 | created_at | - | 排序字段 |
| `sort_order` | string | 否 | desc | asc/desc | 排序顺序 |

## 请求示例

### 基本搜索

```bash
GET /api/search?keyword=老北京
```

### 分页搜索

```bash
GET /api/search?keyword=老北京&page=2&page_size=20
```

### 时间范围搜索

```bash
GET /api/search?start_time=2026-02-01T00:00:00&end_time=2026-02-13T23:59:59
```

### 排序搜索

```bash
GET /api/search?sort_by=title&sort_order=asc
```

### 组合查询

```bash
GET /api/search?keyword=老北京&page=1&page_size=20&start_time=2026-02-01T00:00:00&end_time=2026-02-13T23:59:59&sort_by=created_at&sort_order=desc
```

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "total_pages": 0
  },
  "query": {
    "keyword": "老北京",
    "page": 1,
    "page_size": 20,
    "sort_by": "created_at",
    "sort_order": "desc",
    "start_time": "2026-02-01T00:00:00",
    "end_time": "2026-02-13T23:59:59"
  }
}
```

### 错误响应

#### 验证错误示例

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "errors": [
      {
        "field": "page_size",
        "field_name": "每页数量",
        "message": "每页数量必须小于或等于 200（当前：500）",
        "suggestions": [
          "请将每页数量设置为 200 或更小",
          "建议使用 50-100 的页面大小以获得最佳性能"
        ],
        "error_type": "less_than_equal"
      }
    ],
    "total_errors": 1
  }
}
```

## 验证规则

### 分页参数

- **page**: 必须 ≥ 1
- **page_size**: 必须在 1-200 之间

### 关键词

- 最大长度：200 字符
- 自动去除首尾空白
- 防止 SQL 注入：拒绝包含 `'`, `"`, `;`, `--`, `/*`, `*/`, `\`, `xp_`, `sp_` 等危险字符

### 时间参数

- **格式**: ISO 8601 格式（YYYY-MM-DDTHH:MM:SS）
- **示例**: `2026-02-13T14:30:00`
- **验证**: 
  - 必须是有效的日期时间
  - 开始时间不能晚于结束时间

### 排序参数

- **sort_order**: 只能是 `asc` 或 `desc`

## 安全特性

### SQL 注入防护

接口会检测并拒绝包含以下危险字符的关键词：

- 单引号 `'`
- 双引号 `"`
- 分号 `;`
- SQL 注释 `--`
- SQL 注释 `/*` 和 `*/`
- 反斜杠 `\`
- 存储过程前缀 `xp_` 和 `sp_`

### 输入验证

所有输入参数都经过 Pydantic 模型验证：

- 类型检查
- 范围验证
- 格式验证
- 自动去除空白字符

## 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `VALIDATION_ERROR` | 400 | 输入数据验证失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

## 使用示例

### Python 示例

```python
import requests

# 基本搜索
response = requests.get(
    "http://localhost:8080/api/search",
    params={"keyword": "老北京", "page": 1, "page_size": 20}
)

if response.status_code == 200:
    data = response.json()
    print(f"找到 {data['data']['total']} 条结果")
    for item in data['data']['items']:
        print(item)
else:
    error = response.json()
    print(f"错误: {error['error']['message']}")
```

### JavaScript 示例

```javascript
// 使用 fetch API
async function search(keyword, page = 1, pageSize = 20) {
  const params = new URLSearchParams({
    keyword: keyword,
    page: page,
    page_size: pageSize
  });
  
  try {
    const response = await fetch(`/api/search?${params}`);
    const data = await response.json();
    
    if (data.success) {
      console.log(`找到 ${data.data.total} 条结果`);
      return data.data.items;
    } else {
      console.error('搜索失败:', data.error.message);
      return [];
    }
  } catch (error) {
    console.error('请求失败:', error);
    return [];
  }
}

// 使用示例
search('老北京', 1, 20).then(items => {
  console.log('搜索结果:', items);
});
```

### cURL 示例

```bash
# 基本搜索
curl "http://localhost:8080/api/search?keyword=老北京"

# 带分页的搜索
curl "http://localhost:8080/api/search?keyword=老北京&page=1&page_size=20"

# 时间范围搜索
curl "http://localhost:8080/api/search?start_time=2026-02-01T00:00:00&end_time=2026-02-13T23:59:59"

# 组合查询
curl "http://localhost:8080/api/search?keyword=老北京&page=1&page_size=20&sort_by=created_at&sort_order=desc"
```

## 当前状态

**注意**: 此接口为通用搜索接口框架，当前返回空结果。实际搜索功能需要在实现以下功能后集成：

- 历史记录管理（阶段六 - 任务 17）
- 模板管理（阶段六 - 任务 16）
- 其他需要搜索的数据源

接口已完成：
- ✅ Pydantic 验证模型集成
- ✅ 输入安全验证
- ✅ SQL 注入防护
- ✅ 错误处理和友好提示
- ✅ 完整的单元测试

待实现：
- ⏳ 实际数据源集成
- ⏳ 全文搜索功能
- ⏳ 搜索结果高亮

## 相关文档

- [请求模型文档](REQUEST_MODELS.md)
- [验证错误文档](VALIDATION_ERRORS.md)
- [API 验证示例](API_VALIDATION_EXAMPLES.md)

## 测试

运行搜索 API 测试：

```bash
python3 -m pytest tests/unit/test_search_api.py -v
```

测试覆盖：
- ✅ 默认参数测试
- ✅ 关键词搜索测试
- ✅ 分页参数测试
- ✅ 时间范围测试
- ✅ 排序参数测试
- ✅ 参数验证测试
- ✅ SQL 注入防护测试
- ✅ XSS 攻击防护测试
- ✅ 组合查询测试

## 更新日志

### 2026-02-13
- ✅ 创建搜索 API 接口
- ✅ 集成 SearchRequest 验证模型
- ✅ 添加完整的单元测试
- ✅ 编写 API 文档
