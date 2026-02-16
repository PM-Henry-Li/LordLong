# RedBookContentGen API 使用示例

本文档提供了 RedBookContentGen API 的详细使用示例，包括 cURL、Python 和 JavaScript 三种语言的示例代码。

## 目录

- [基础说明](#基础说明)
- [内容生成 API](#内容生成-api)
- [批量内容生成 API](#批量内容生成-api)
- [图片生成 API](#图片生成-api)
- [日志查询 API](#日志查询-api)
- [批量导出 API](#批量导出-api)
- [错误处理](#错误处理)

---

## 基础说明

### API 基础地址

```
http://localhost:8080
```

### 通用响应格式

**成功响应**：
```json
{
  "success": true,
  "data": { ... }
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "errors": [ ... ],
    "total_errors": 1
  }
}
```

---

## 内容生成 API

### 接口信息

- **路径**: `/api/generate_content`
- **方法**: `POST`
- **功能**: 根据输入文本生成小红书风格的内容

### cURL 示例

```bash
# 基础示例
curl -X POST http://localhost:8080/api/generate_content \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息。清晨的叫卖声，傍晚的炊烟，还有那些邻里间的温暖故事。",
    "count": 3
  }'

# 详细示例（指定所有参数）
curl -X POST http://localhost:8080/api/generate_content \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "北京的四合院是传统建筑的代表，体现了中国人的居住智慧。院落布局讲究对称，体现了天人合一的哲学思想。",
    "count": 5,
    "style": "retro_chinese",
    "temperature": 0.8
  }'
```

### Python 示例

```python
import requests
import json

# API 基础地址
BASE_URL = "http://localhost:8080"

def generate_content(input_text: str, count: int = 3) -> dict:
    """
    生成小红书内容
    
    Args:
        input_text: 输入文本
        count: 生成标题数量
        
    Returns:
        生成结果字典
    """
    url = f"{BASE_URL}/api/generate_content"
    
    payload = {
        "input_text": input_text,
        "count": count
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if result["success"]:
            print("✅ 生成成功！")
            data = result["data"]
            
            print("\n📝 标题列表：")
            for i, title in enumerate(data["titles"], 1):
                print(f"  {i}. {title}")
            
            print(f"\n📄 正文内容：\n{data['content'][:200]}...")
            
            print(f"\n🏷️ 标签：{', '.join(data['tags'])}")
            
            print(f"\n🎨 图片提示词数量：{len(data['image_prompts'])}")
            
            return data
        else:
            print(f"❌ 生成失败：{result['error']['message']}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败：{e}")
        return None

# 使用示例
if __name__ == "__main__":
    input_text = "记得小时候，老北京的胡同里总是充满了生活的气息。清晨的叫卖声，傍晚的炊烟，还有那些邻里间的温暖故事。"
    
    result = generate_content(input_text, count=3)
```

### JavaScript 示例

```javascript
// 使用 fetch API
async function generateContent(inputText, count = 3) {
  const url = 'http://localhost:8080/api/generate_content';
  
  const payload = {
    input_text: inputText,
    count: count
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('✅ 生成成功！');
      const data = result.data;
      
      console.log('\n📝 标题列表：');
      data.titles.forEach((title, index) => {
        console.log(`  ${index + 1}. ${title}`);
      });
      
      console.log(`\n📄 正文内容：\n${data.content.substring(0, 200)}...`);
      
      console.log(`\n🏷️ 标签：${data.tags.join(', ')}`);
      
      console.log(`\n🎨 图片提示词数量：${data.image_prompts.length}`);
      
      return data;
    } else {
      console.error(`❌ 生成失败：${result.error.message}`);
      return null;
    }
  } catch (error) {
    console.error(`❌ 请求失败：${error.message}`);
    return null;
  }
}

// 使用示例
const inputText = "记得小时候，老北京的胡同里总是充满了生活的气息。清晨的叫卖声，傍晚的炊烟，还有那些邻里间的温暖故事。";

generateContent(inputText, 3)
  .then(result => {
    if (result) {
      console.log('生成完成！');
    }
  });
```

---

## 批量内容生成 API

### 接口信息

- **路径**: `/api/batch/generate_content`
- **方法**: `POST`
- **功能**: 批量生成多个小红书内容

### cURL 示例

```bash
curl -X POST http://localhost:8080/api/batch/generate_content \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [
      "记得小时候，老北京的胡同里总是充满了生活的气息...",
      "北京的四合院是传统建筑的代表，体现了中国人的居住智慧...",
      "老北京的小吃文化源远流长，每一种小吃都有自己的故事..."
    ],
    "count": 1
  }'
```

### Python 示例

```python
import requests

def batch_generate_content(inputs: list, count: int = 1) -> dict:
    """
    批量生成小红书内容
    
    Args:
        inputs: 输入文本列表
        count: 每个输入生成的标题数量
        
    Returns:
        批量生成结果
    """
    url = "http://localhost:8080/api/batch/generate_content"
    
    payload = {
        "inputs": inputs,
        "count": count
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if result["success"]:
            data = result["data"]
            print(f"✅ 批量生成完成！")
            print(f"📊 批次 ID：{data['batch_id']}")
            print(f"📈 总任务数：{data['total']}")
            print(f"✅ 成功：{data['summary']['success']}")
            print(f"❌ 失败：{data['summary']['failed']}")
            
            # 显示每个任务的结果
            for item in data["results"]:
                status_icon = "✅" if item["status"] == "success" else "❌"
                print(f"\n{status_icon} 任务 {item['index'] + 1}:")
                print(f"   输入：{item['input_text'][:50]}...")
                
                if item["status"] == "success":
                    print(f"   标题：{item['data']['titles'][0]}")
                else:
                    print(f"   错误：{item['error']}")
            
            return data
        else:
            print(f"❌ 批量生成失败：{result['error']['message']}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败：{e}")
        return None

# 使用示例
if __name__ == "__main__":
    inputs = [
        "记得小时候，老北京的胡同里总是充满了生活的气息...",
        "北京的四合院是传统建筑的代表，体现了中国人的居住智慧...",
        "老北京的小吃文化源远流长，每一种小吃都有自己的故事..."
    ]
    
    result = batch_generate_content(inputs, count=1)
```

### JavaScript 示例

```javascript
async function batchGenerateContent(inputs, count = 1) {
  const url = 'http://localhost:8080/api/batch/generate_content';
  
  const payload = {
    inputs: inputs,
    count: count
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.success) {
      const data = result.data;
      console.log('✅ 批量生成完成！');
      console.log(`📊 批次 ID：${data.batch_id}`);
      console.log(`📈 总任务数：${data.total}`);
      console.log(`✅ 成功：${data.summary.success}`);
      console.log(`❌ 失败：${data.summary.failed}`);
      
      // 显示每个任务的结果
      data.results.forEach(item => {
        const statusIcon = item.status === 'success' ? '✅' : '❌';
        console.log(`\n${statusIcon} 任务 ${item.index + 1}:`);
        console.log(`   输入：${item.input_text.substring(0, 50)}...`);
        
        if (item.status === 'success') {
          console.log(`   标题：${item.data.titles[0]}`);
        } else {
          console.log(`   错误：${item.error}`);
        }
      });
      
      return data;
    } else {
      console.error(`❌ 批量生成失败：${result.error.message}`);
      return null;
    }
  } catch (error) {
    console.error(`❌ 请求失败：${error.message}`);
    return null;
  }
}

// 使用示例
const inputs = [
  "记得小时候，老北京的胡同里总是充满了生活的气息...",
  "北京的四合院是传统建筑的代表，体现了中国人的居住智慧...",
  "老北京的小吃文化源远流长，每一种小吃都有自己的故事..."
];

batchGenerateContent(inputs, 1);
```

---

## 图片生成 API

### 接口信息

- **路径**: `/api/generate_image`
- **方法**: `POST`
- **功能**: 生成单张图片（支持 API 模式和模板模式）

### cURL 示例

```bash
# 模板模式（推荐，无需 API Key）
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

# API 模式（需要 API Key）
curl -X POST http://localhost:8080/api/generate_image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "老北京胡同，复古风格，温暖的阳光",
    "image_mode": "api",
    "image_model": "wanx-v1",
    "image_size": "vertical",
    "task_id": "task_20260213_002",
    "timestamp": "20260213_143000",
    "task_index": 0
  }'
```

### Python 示例

```python
import requests
from datetime import datetime

def generate_image_template(
    prompt: str,
    title: str = "",
    scene: str = "",
    content_text: str = "",
    template_style: str = "retro_chinese",
    image_size: str = "vertical"
) -> dict:
    """
    使用模板模式生成图片
    
    Args:
        prompt: 图片提示词
        title: 图片标题
        scene: 场景描述
        content_text: 内容文本
        template_style: 模板风格
        image_size: 图片尺寸
        
    Returns:
        生成结果
    """
    url = "http://localhost:8080/api/generate_image"
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = f"task_{timestamp}"
    
    payload = {
        "prompt": prompt,
        "image_mode": "template",
        "template_style": template_style,
        "image_size": image_size,
        "title": title,
        "scene": scene,
        "content_text": content_text,
        "task_id": task_id,
        "timestamp": timestamp,
        "task_index": 0,
        "image_type": "content"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if result["success"]:
            data = result["data"]
            print(f"✅ 图片生成成功！")
            print(f"🖼️ 图片 URL：{data['image_url']}")
            print(f"📋 任务 ID：{data['task_id']}")
            
            # 下载图片
            image_url = f"http://localhost:8080{data['image_url']}"
            print(f"\n💾 下载地址：{image_url}")
            
            return data
        else:
            print(f"❌ 图片生成失败：{result['error']['message']}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败：{e}")
        return None

# 使用示例
if __name__ == "__main__":
    result = generate_image_template(
        prompt="老北京胡同，复古风格，温暖的阳光",
        title="老北京的记忆",
        scene="夕阳下的胡同",
        content_text="记得小时候，胡同里总是充满了生活的气息...",
        template_style="retro_chinese",
        image_size="vertical"
    )
```

### JavaScript 示例

```javascript
async function generateImageTemplate(
  prompt,
  title = '',
  scene = '',
  contentText = '',
  templateStyle = 'retro_chinese',
  imageSize = 'vertical'
) {
  const url = 'http://localhost:8080/api/generate_image';
  
  // 生成时间戳
  const now = new Date();
  const timestamp = now.toISOString()
    .replace(/[-:]/g, '')
    .replace('T', '_')
    .substring(0, 15);
  const taskId = `task_${timestamp}`;
  
  const payload = {
    prompt: prompt,
    image_mode: 'template',
    template_style: templateStyle,
    image_size: imageSize,
    title: title,
    scene: scene,
    content_text: contentText,
    task_id: taskId,
    timestamp: timestamp,
    task_index: 0,
    image_type: 'content'
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.success) {
      const data = result.data;
      console.log('✅ 图片生成成功！');
      console.log(`🖼️ 图片 URL：${data.image_url}`);
      console.log(`📋 任务 ID：${data.task_id}`);
      
      // 下载图片
      const imageUrl = `http://localhost:8080${data.image_url}`;
      console.log(`\n💾 下载地址：${imageUrl}`);
      
      return data;
    } else {
      console.error(`❌ 图片生成失败：${result.error.message}`);
      return null;
    }
  } catch (error) {
    console.error(`❌ 请求失败：${error.message}`);
    return null;
  }
}

// 使用示例
generateImageTemplate(
  '老北京胡同，复古风格，温暖的阳光',
  '老北京的记忆',
  '夕阳下的胡同',
  '记得小时候，胡同里总是充满了生活的气息...',
  'retro_chinese',
  'vertical'
);
```

---

## 日志查询 API

### 接口信息

- **路径**: `/api/logs/search`
- **方法**: `GET`
- **功能**: 搜索和过滤应用日志

### cURL 示例

```bash
# 基础查询
curl "http://localhost:8080/api/logs/search?page=1&page_size=20"

# 按级别过滤
curl "http://localhost:8080/api/logs/search?level=ERROR&page=1&page_size=20"

# 按时间范围过滤
curl "http://localhost:8080/api/logs/search?start_time=2026-02-13T00:00:00&end_time=2026-02-14T23:59:59&page=1"

# 关键词搜索
curl "http://localhost:8080/api/logs/search?keyword=生成&page=1&page_size=20"

# 组合查询
curl "http://localhost:8080/api/logs/search?level=ERROR&logger=content_generator&keyword=失败&page=1"
```

### Python 示例

```python
import requests
from typing import Optional
from datetime import datetime, timedelta

def search_logs(
    page: int = 1,
    page_size: int = 50,
    level: Optional[str] = None,
    logger: Optional[str] = None,
    keyword: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> dict:
    """
    搜索日志
    
    Args:
        page: 页码
        page_size: 每页数量
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        logger: 日志来源
        keyword: 搜索关键词
        start_time: 开始时间（ISO 8601 格式）
        end_time: 结束时间（ISO 8601 格式）
        
    Returns:
        日志搜索结果
    """
    url = "http://localhost:8080/api/logs/search"
    
    params = {
        "page": page,
        "page_size": page_size
    }
    
    if level:
        params["level"] = level
    if logger:
        params["logger"] = logger
    if keyword:
        params["keyword"] = keyword
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()
        
        if result["success"]:
            print(f"✅ 查询成功！")
            print(f"📊 总日志数：{result['total']}")
            print(f"📄 当前页：{result['page']}/{(result['total'] + result['page_size'] - 1) // result['page_size']}")
            
            print(f"\n📝 日志列表：")
            for log in result["logs"]:
                level_icon = {
                    "DEBUG": "🔍",
                    "INFO": "ℹ️",
                    "WARNING": "⚠️",
                    "ERROR": "❌",
                    "CRITICAL": "🔥"
                }.get(log["level"], "📝")
                
                print(f"\n{level_icon} [{log['level']}] {log['timestamp']}")
                print(f"   来源：{log['logger']}")
                print(f"   消息：{log['message']}")
            
            return result
        else:
            print(f"❌ 查询失败：{result['error']['message']}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败：{e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 查询最近的错误日志
    result = search_logs(
        level="ERROR",
        page=1,
        page_size=20
    )
    
    # 查询今天的日志
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    result = search_logs(
        start_time=today.isoformat(),
        end_time=tomorrow.isoformat(),
        page=1,
        page_size=50
    )
```

### JavaScript 示例

```javascript
async function searchLogs(options = {}) {
  const {
    page = 1,
    pageSize = 50,
    level = null,
    logger = null,
    keyword = null,
    startTime = null,
    endTime = null
  } = options;
  
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString()
  });
  
  if (level) params.append('level', level);
  if (logger) params.append('logger', logger);
  if (keyword) params.append('keyword', keyword);
  if (startTime) params.append('start_time', startTime);
  if (endTime) params.append('end_time', endTime);
  
  const url = `http://localhost:8080/api/logs/search?${params.toString()}`;
  
  try {
    const response = await fetch(url);
    const result = await response.json();
    
    if (result.success) {
      console.log('✅ 查询成功！');
      console.log(`📊 总日志数：${result.total}`);
      console.log(`📄 当前页：${result.page}/${Math.ceil(result.total / result.page_size)}`);
      
      console.log('\n📝 日志列表：');
      result.logs.forEach(log => {
        const levelIcons = {
          'DEBUG': '🔍',
          'INFO': 'ℹ️',
          'WARNING': '⚠️',
          'ERROR': '❌',
          'CRITICAL': '🔥'
        };
        const icon = levelIcons[log.level] || '📝';
        
        console.log(`\n${icon} [${log.level}] ${log.timestamp}`);
        console.log(`   来源：${log.logger}`);
        console.log(`   消息：${log.message}`);
      });
      
      return result;
    } else {
      console.error(`❌ 查询失败：${result.error.message}`);
      return null;
    }
  } catch (error) {
    console.error(`❌ 请求失败：${error.message}`);
    return null;
  }
}

// 使用示例
// 查询最近的错误日志
searchLogs({
  level: 'ERROR',
  page: 1,
  pageSize: 20
});

// 查询今天的日志
const today = new Date();
today.setHours(0, 0, 0, 0);
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

searchLogs({
  startTime: today.toISOString(),
  endTime: tomorrow.toISOString(),
  page: 1,
  pageSize: 50
});
```

---

## 批量导出 API

### 导出为 Excel

#### cURL 示例

```bash
curl -X POST http://localhost:8080/api/batch/export/excel \
  -H "Content-Type: application/json" \
  -d '{
    "batch_result": {
      "batch_id": "batch_20260213_143000",
      "total": 3,
      "results": [...],
      "summary": {...}
    }
  }' \
  --output batch_export.xlsx
```

#### Python 示例

```python
import requests

def export_batch_excel(batch_result: dict, output_file: str = "batch_export.xlsx"):
    """
    导出批量结果为 Excel
    
    Args:
        batch_result: 批量生成结果
        output_file: 输出文件名
    """
    url = "http://localhost:8080/api/batch/export/excel"
    
    payload = {
        "batch_result": batch_result
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # 保存文件
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Excel 导出成功！")
        print(f"💾 文件保存至：{output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 导出失败：{e}")

# 使用示例（假设已有批量生成结果）
# export_batch_excel(batch_result, "my_batch_export.xlsx")
```

### 导出为 ZIP

#### cURL 示例

```bash
curl -X POST http://localhost:8080/api/batch/export/zip \
  -H "Content-Type: application/json" \
  -d '{
    "batch_result": {
      "batch_id": "batch_20260213_143000",
      "total": 3,
      "results": [...],
      "summary": {...}
    }
  }' \
  --output batch_export.zip
```

#### Python 示例

```python
import requests

def export_batch_zip(batch_result: dict, output_file: str = "batch_export.zip"):
    """
    导出批量结果为 ZIP
    
    Args:
        batch_result: 批量生成结果
        output_file: 输出文件名
    """
    url = "http://localhost:8080/api/batch/export/zip"
    
    payload = {
        "batch_result": batch_result
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # 保存文件
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ ZIP 导出成功！")
        print(f"💾 文件保存至：{output_file}")
        print(f"📦 包含内容：Excel 汇总、批次信息、所有图片")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 导出失败：{e}")

# 使用示例（假设已有批量生成结果）
# export_batch_zip(batch_result, "my_batch_export.zip")
```

---

## 错误处理

### 常见错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| `VALIDATION_ERROR` | 输入验证失败 | 检查请求参数是否符合要求 |
| `API_ERROR` | API 调用失败 | 检查 API Key 配置，稍后重试 |
| `TIMEOUT_ERROR` | 请求超时 | 增加超时时间或稍后重试 |
| `RESOURCE_NOT_FOUND` | 资源不存在 | 检查资源路径是否正确 |
| `RATE_LIMIT_ERROR` | 超过速率限制 | 等待一段时间后重试 |

### 错误处理示例

#### Python

```python
import requests
import time

def generate_content_with_retry(input_text: str, max_retries: int = 3) -> dict:
    """
    带重试的内容生成
    
    Args:
        input_text: 输入文本
        max_retries: 最大重试次数
        
    Returns:
        生成结果
    """
    url = "http://localhost:8080/api/generate_content"
    
    payload = {
        "input_text": input_text,
        "count": 3
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result["success"]:
                return result["data"]
            else:
                error = result["error"]
                error_code = error.get("code", "UNKNOWN")
                
                # 根据错误码决定是否重试
                if error_code == "RATE_LIMIT_ERROR":
                    print(f"⚠️ 超过速率限制，等待 5 秒后重试...")
                    time.sleep(5)
                    continue
                elif error_code == "VALIDATION_ERROR":
                    print(f"❌ 输入验证失败：{error['message']}")
                    # 显示详细错误
                    for err in error.get("errors", []):
                        print(f"   - {err['field_name']}: {err['message']}")
                        if err.get("suggestions"):
                            print(f"     建议：{', '.join(err['suggestions'])}")
                    return None
                else:
                    print(f"❌ 生成失败：{error['message']}")
                    if attempt < max_retries - 1:
                        print(f"⚠️ 重试中... ({attempt + 1}/{max_retries})")
                        time.sleep(2)
                        continue
                    return None
                    
        except requests.exceptions.Timeout:
            print(f"⚠️ 请求超时")
            if attempt < max_retries - 1:
                print(f"⚠️ 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2)
                continue
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败：{e}")
            if attempt < max_retries - 1:
                print(f"⚠️ 重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2)
                continue
            return None
    
    print(f"❌ 达到最大重试次数，生成失败")
    return None

# 使用示例
result = generate_content_with_retry("记得小时候，老北京的胡同里...")
```

#### JavaScript

```javascript
async function generateContentWithRetry(inputText, maxRetries = 3) {
  const url = 'http://localhost:8080/api/generate_content';
  
  const payload = {
    input_text: inputText,
    count: 3
  };
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(30000) // 30秒超时
      });
      
      const result = await response.json();
      
      if (result.success) {
        return result.data;
      } else {
        const error = result.error;
        const errorCode = error.code || 'UNKNOWN';
        
        // 根据错误码决定是否重试
        if (errorCode === 'RATE_LIMIT_ERROR') {
          console.log('⚠️ 超过速率限制，等待 5 秒后重试...');
          await new Promise(resolve => setTimeout(resolve, 5000));
          continue;
        } else if (errorCode === 'VALIDATION_ERROR') {
          console.error(`❌ 输入验证失败：${error.message}`);
          // 显示详细错误
          (error.errors || []).forEach(err => {
            console.error(`   - ${err.field_name}: ${err.message}`);
            if (err.suggestions) {
              console.error(`     建议：${err.suggestions.join(', ')}`);
            }
          });
          return null;
        } else {
          console.error(`❌ 生成失败：${error.message}`);
          if (attempt < maxRetries - 1) {
            console.log(`⚠️ 重试中... (${attempt + 1}/${maxRetries})`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            continue;
          }
          return null;
        }
      }
    } catch (error) {
      if (error.name === 'TimeoutError') {
        console.log('⚠️ 请求超时');
      } else {
        console.error(`❌ 请求失败：${error.message}`);
      }
      
      if (attempt < maxRetries - 1) {
        console.log(`⚠️ 重试中... (${attempt + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, 2000));
        continue;
      }
      return null;
    }
  }
  
  console.error('❌ 达到最大重试次数，生成失败');
  return null;
}

// 使用示例
generateContentWithRetry('记得小时候，老北京的胡同里...');
```

---

## 完整示例：端到端流程

### Python 完整示例

```python
import requests
from datetime import datetime
import time

class RedBookContentGenClient:
    """RedBookContentGen API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
    
    def generate_content(self, input_text: str, count: int = 3) -> dict:
        """生成内容"""
        url = f"{self.base_url}/api/generate_content"
        response = requests.post(url, json={"input_text": input_text, "count": count})
        response.raise_for_status()
        result = response.json()
        return result["data"] if result["success"] else None
    
    def generate_image(self, prompt: str, title: str = "", **kwargs) -> dict:
        """生成图片"""
        url = f"{self.base_url}/api/generate_image"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        payload = {
            "prompt": prompt,
            "image_mode": "template",
            "template_style": "retro_chinese",
            "image_size": "vertical",
            "title": title,
            "task_id": f"task_{timestamp}",
            "timestamp": timestamp,
            "task_index": 0,
            **kwargs
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["data"] if result["success"] else None

# 使用示例：完整流程
if __name__ == "__main__":
    client = RedBookContentGenClient()
    
    # 1. 生成内容
    print("📝 步骤 1：生成小红书内容...")
    input_text = "记得小时候，老北京的胡同里总是充满了生活的气息。清晨的叫卖声，傍晚的炊烟，还有那些邻里间的温暖故事。"
    content = client.generate_content(input_text, count=3)
    
    if content:
        print(f"✅ 内容生成成功！")
        print(f"   标题：{content['titles'][0]}")
        print(f"   标签：{', '.join(content['tags'])}")
        
        # 2. 生成图片
        print(f"\n🎨 步骤 2：生成配套图片...")
        for i, prompt in enumerate(content['image_prompts'][:2]):  # 只生成前2张
            print(f"   生成图片 {i+1}/{2}...")
            image = client.generate_image(
                prompt=prompt,
                title=content['titles'][0],
                content_text=content['content'][:100]
            )
            
            if image:
                print(f"   ✅ 图片 {i+1} 生成成功：{image['image_url']}")
            
            time.sleep(1)  # 避免请求过快
        
        print(f"\n🎉 完成！所有内容已生成。")
    else:
        print("❌ 内容生成失败")
```

---

## 更多资源

- **API 文档**: http://localhost:8080/api/docs
- **项目文档**: [README.md](../README.md)
- **配置指南**: [CONFIG.md](CONFIG.md)
- **故障排查**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**最后更新**: 2026-02-14  
**文档版本**: v1.0.0
