# 批量处理界面文档

## 概述

批量处理界面允许用户一次性生成多条小红书内容，提高工作效率。支持文本输入和文件上传两种方式，最多可批量处理 50 条内容。

## 功能特性

### 1. 批量输入方式

#### 1.1 文本输入
- 在多行文本框中输入内容，每行一条
- 自动过滤空行
- 实时显示输入数量
- 最多支持 50 条

**示例**：
```
故宫雪景
治愈系咖啡店
日落海边
京都和服体验
春日樱花
```

#### 1.2 文件上传
- 支持 TXT 文件格式
- 支持拖拽上传
- 自动解析文件内容
- 显示文件读取状态

**TXT 文件格式**：
```
每行一条内容
自动过滤空行
支持中英文
```

### 2. 批量任务管理

#### 2.1 任务列表显示
- 显示所有待处理任务
- 实时更新任务状态
- 支持任务重试
- 显示任务数量统计

**任务状态**：
- 🕐 等待中（pending）
- 🔄 生成中（processing）
- ✅ 成功（success）
- ❌ 失败（failed）

#### 2.2 任务操作
- 单个任务重试
- 查看任务详情
- 删除失败任务（开发中）

### 3. 批量进度显示

#### 3.1 进度统计
- 总任务数
- 成功数量
- 失败数量
- 成功率百分比

#### 3.2 进度条
- 实时更新进度
- 动画效果
- 颜色区分状态

#### 3.3 批次信息
- 批次 ID
- 生成时间
- 完成状态

### 4. 批量结果展示

#### 4.1 结果卡片
- 显示生成的标题
- 显示标签列表
- 显示生成状态
- 显示错误信息（如果失败）

#### 4.2 结果筛选
- 查看所有结果
- 仅查看成功
- 仅查看失败

### 5. 批量下载

#### 5.1 Excel 导出
- 包含所有生成结果
- 包含汇总信息
- 格式化表格
- 自动命名：`{batch_id}_summary.xlsx`

**Excel 内容**：
- 序号
- 状态
- 输入文本
- 标题
- 内容
- 标签
- 错误信息

#### 5.2 ZIP 打包下载
- 包含 Excel 汇总文件
- 包含批次信息文本
- 包含所有生成的图片
- 自动命名：`{batch_id}_export.zip`

**ZIP 结构**：
```
batch_20260213_143000_export.zip
├── batch_20260213_143000_summary.xlsx
├── batch_info.txt
└── images/
    ├── image_001.png
    ├── image_002.png
    └── ...
```

## 使用流程

### 基本流程

1. **选择输入方式**
   - 点击"文本输入"或"文件上传"按钮

2. **输入内容**
   - 文本输入：在文本框中输入，每行一条
   - 文件上传：点击或拖拽上传 TXT 文件

3. **配置生成选项**
   - 选择每条生成的图片数量（1/3/5 张）

4. **开始生成**
   - 点击"开始批量生成"按钮
   - 等待生成完成

5. **查看结果**
   - 查看任务列表状态
   - 查看批量进度统计
   - 查看生成结果卡片

6. **下载结果**
   - 点击"下载 Excel"导出汇总表格
   - 点击"下载 ZIP"打包下载所有内容

### 错误处理

#### 输入验证错误
- 输入为空：提示"请输入至少一条内容"
- 数量超限：提示"输入数量超过限制（X/50）"
- 文件格式错误：提示"不支持的文件格式"

#### 生成错误
- API 调用失败：显示错误信息，支持重试
- 网络错误：自动重试 3 次
- 超时错误：提示用户稍后重试

#### 下载错误
- Excel 导出失败：提示安装 openpyxl 或使用 ZIP 导出
- ZIP 打包失败：显示具体错误信息

## API 接口

### 批量生成内容

**请求**：
```http
POST /api/batch/generate_content
Content-Type: application/json

{
  "inputs": [
    "记得小时候，老北京的胡同里总是充满了生活的气息...",
    "北京的四合院是传统建筑的代表，体现了中国人的居住智慧..."
  ],
  "count": 1,
  "style": "retro_chinese",
  "temperature": 0.8
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_20260213_143000",
    "total": 2,
    "results": [
      {
        "index": 0,
        "input_text": "记得小时候，老北京的胡同里...",
        "status": "success",
        "data": {
          "titles": ["标题1", "标题2"],
          "content": "生成的内容...",
          "tags": ["标签1", "标签2"],
          "image_tasks": [...]
        },
        "error": null
      },
      {
        "index": 1,
        "input_text": "北京的四合院是传统建筑...",
        "status": "success",
        "data": {...},
        "error": null
      }
    ],
    "summary": {
      "success": 2,
      "failed": 0,
      "total": 2
    }
  }
}
```

### 导出 Excel

**请求**：
```http
POST /api/batch/export/excel
Content-Type: application/json

{
  "batch_result": {
    "batch_id": "batch_20260213_143000",
    "total": 2,
    "results": [...],
    "summary": {...}
  }
}
```

**响应**：
- 成功：返回 Excel 文件下载
- 失败：返回错误 JSON

### 导出 ZIP

**请求**：
```http
POST /api/batch/export/zip
Content-Type: application/json

{
  "batch_result": {
    "batch_id": "batch_20260213_143000",
    "total": 2,
    "results": [...],
    "summary": {...}
  }
}
```

**响应**：
- 成功：返回 ZIP 文件下载
- 失败：返回错误 JSON

## 技术实现

### 前端技术栈
- HTML5 + CSS3
- 原生 JavaScript（无框架依赖）
- Fetch API（HTTP 请求）
- File API（文件读取）

### 后端技术栈
- Flask（Web 框架）
- Pydantic（数据验证）
- openpyxl（Excel 导出，可选）
- zipfile（ZIP 打包）

### 关键文件
- `templates/batch.html` - 批量处理页面模板
- `static/css/batch.css` - 批量处理样式
- `static/js/batch.js` - 批量处理脚本
- `src/web/blueprints/api.py` - API 路由
- `src/web/blueprints/main.py` - 页面路由
- `src/services/content_service.py` - 内容生成服务
- `src/utils/export_utils.py` - 导出工具

## 性能优化

### 前端优化
- 虚拟滚动（任务列表超过 100 条时）
- 防抖处理（文本输入）
- 懒加载（结果卡片）

### 后端优化
- 批量处理使用串行生成（避免 API 限流）
- 错误隔离（单个任务失败不影响其他任务）
- 内存优化（大文件分块处理）

## 用户体验

### 响应式设计
- 支持桌面端（1024px+）
- 支持平板端（768px-1024px）
- 支持移动端（<768px）

### 交互反馈
- 加载状态提示
- 进度实时更新
- 错误友好提示
- 成功操作确认

### 无障碍支持
- 语义化 HTML
- ARIA 标签
- 键盘导航
- 屏幕阅读器支持

## 常见问题

### Q: 批量处理最多支持多少条？
A: 最多支持 50 条内容的批量处理。

### Q: 支持哪些文件格式？
A: 目前支持 TXT 文本文件，Excel 文件解析功能开发中。

### Q: 批量生成需要多长时间？
A: 取决于内容数量和图片数量，平均每条内容需要 30-60 秒。

### Q: 如果部分任务失败怎么办？
A: 可以单独重试失败的任务，或重新提交整个批次。

### Q: 下载的 ZIP 包含什么内容？
A: 包含 Excel 汇总文件、批次信息文本和所有生成的图片。

### Q: Excel 导出失败怎么办？
A: 需要安装 openpyxl 库（`pip install openpyxl`），或使用 ZIP 导出功能。

## 未来计划

### 短期计划
- [ ] 支持 Excel 文件上传
- [ ] 支持模板导入
- [ ] 支持任务暂停/恢复
- [ ] 支持批量编辑

### 长期计划
- [ ] 支持批量任务队列
- [ ] 支持定时批量生成
- [ ] 支持批量结果对比
- [ ] 支持批量历史记录

## 更新日志

### v1.0.0 (2026-02-13)
- ✅ 实现批量输入界面（文本输入、文件上传）
- ✅ 实现批量任务列表（状态显示、任务重试）
- ✅ 实现批量进度显示（进度统计、进度条）
- ✅ 实现批量下载（Excel 导出、ZIP 打包）
- ✅ 集成错误处理组件
- ✅ 响应式设计支持

## 参考资料

- [Flask 文档](https://flask.palletsprojects.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [openpyxl 文档](https://openpyxl.readthedocs.io/)
- [File API 文档](https://developer.mozilla.org/en-US/docs/Web/API/File_API)

---

**最后更新**: 2026-02-13  
**文档版本**: v1.0.0  
**维护者**: Kiro AI Assistant
