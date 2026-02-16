# API 文档说明

## 访问 API 文档

RedBookContentGen 提供了完整的 API 文档，包括 Swagger UI 交互式文档和详细的使用示例。

### Swagger UI（推荐）

启动应用后，访问以下地址查看交互式 API 文档：

```
http://localhost:8080/api/docs
```

**功能特性**：
- 📖 完整的 API 接口列表
- 🔍 接口详细说明和参数定义
- 🧪 在线测试功能（Try it out）
- 📝 请求/响应示例
- 🏷️ 按功能分类的标签

### OpenAPI 规范文件

OpenAPI 3.0 规范文件位于：

```
docs/openapi.yaml
```

可以使用任何支持 OpenAPI 3.0 的工具查看和编辑此文件，例如：
- [Swagger Editor](https://editor.swagger.io/)
- [Stoplight Studio](https://stoplight.io/studio)
- [Postman](https://www.postman.com/)

### 使用示例文档

详细的代码示例（cURL、Python、JavaScript）请查看：

```
docs/API_EXAMPLES.md
```

包含内容：
- ✅ 所有 API 接口的完整示例
- ✅ 错误处理和重试逻辑
- ✅ 端到端使用流程
- ✅ 最佳实践建议

## 快速开始

### 1. 启动应用

```bash
python web_app.py
```

### 2. 访问文档

打开浏览器访问：http://localhost:8080/api/docs

### 3. 测试 API

在 Swagger UI 中：
1. 选择一个接口（如 `/api/generate_content`）
2. 点击 "Try it out" 按钮
3. 填写请求参数
4. 点击 "Execute" 执行请求
5. 查看响应结果

## API 概览

### 内容生成

- `POST /api/generate_content` - 生成单个小红书内容
- `POST /api/batch/generate_content` - 批量生成内容

### 图片生成

- `POST /api/generate_image` - 生成单张图片
- `GET /api/download/{filename}` - 下载图片

### 系统信息

- `GET /api/models` - 获取可用模型列表
- `GET /api/search` - 通用搜索接口

### 日志管理

- `GET /api/logs/search` - 搜索日志
- `GET /api/logs/stats` - 获取日志统计
- `GET /api/logs/loggers` - 获取日志来源列表

### 批量导出

- `POST /api/batch/export/excel` - 导出为 Excel
- `POST /api/batch/export/zip` - 导出为 ZIP

## 认证说明

当前版本为单用户工具，暂不需要认证。

## 速率限制

- 内容生成：60 次/分钟
- 图片生成：10 次/分钟

## 错误处理

所有 API 遵循统一的错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "errors": [...],
    "total_errors": 1
  }
}
```

详细的错误码说明请参考 [API_EXAMPLES.md](API_EXAMPLES.md#错误处理)。

## 更多资源

- **使用示例**: [API_EXAMPLES.md](API_EXAMPLES.md)
- **配置指南**: [CONFIG.md](CONFIG.md)
- **项目文档**: [../README.md](../README.md)

---

**最后更新**: 2026-02-14  
**文档版本**: v1.0.0
