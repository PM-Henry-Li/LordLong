# API 文档设置指南

本文档说明如何设置和使用 RedBookContentGen 的 API 文档功能。

## 安装依赖

API 文档功能需要安装 `flasgger` 库。

### 方法 1：安装所有依赖

```bash
pip install -r requirements.txt
```

### 方法 2：仅安装 API 文档依赖

```bash
pip install flasgger>=0.9.7
```

## 启动应用

安装依赖后，启动 Web 应用：

```bash
python web_app.py
```

启动成功后，你会看到类似以下输出：

```
============================================================
小红书内容生成 Web 应用
============================================================
访问地址: http://localhost:8080
API 文档: http://localhost:8080/api/docs
按 Ctrl+C 停止服务
```

## 访问 API 文档

在浏览器中打开以下地址：

```
http://localhost:8080/api/docs
```

你将看到 Swagger UI 界面，包含：

- 📖 所有 API 接口列表
- 🔍 接口详细说明
- 🧪 在线测试功能
- 📝 请求/响应示例

## 使用 Swagger UI

### 1. 浏览接口

- 接口按功能分组（内容生成、图片生成、批量处理等）
- 点击接口名称展开详细信息
- 查看请求参数、响应格式和示例

### 2. 测试接口

1. 点击接口右侧的 "Try it out" 按钮
2. 填写请求参数（必填参数会标记为 required）
3. 点击 "Execute" 按钮执行请求
4. 查看响应结果（包括状态码、响应头和响应体）

### 3. 查看示例

每个接口都提供了多个示例：
- 基础示例：最简单的使用方式
- 详细示例：包含所有可选参数
- 错误示例：展示常见错误情况

## OpenAPI 规范文件

如果你需要导入到其他工具（如 Postman），可以使用 OpenAPI 规范文件：

```
docs/openapi.yaml
```

### 导入到 Postman

1. 打开 Postman
2. 点击 "Import" 按钮
3. 选择 "File" 标签
4. 选择 `docs/openapi.yaml` 文件
5. 点击 "Import" 完成导入

### 使用 Swagger Editor

1. 访问 https://editor.swagger.io/
2. 点击 "File" -> "Import file"
3. 选择 `docs/openapi.yaml` 文件
4. 在线编辑和预览

## 代码示例

详细的代码示例（cURL、Python、JavaScript）请查看：

```
docs/API_EXAMPLES.md
```

## 故障排查

### 问题 1：无法访问 /api/docs

**原因**：flasgger 未安装

**解决方案**：
```bash
pip install flasgger>=0.9.7
```

### 问题 2：Swagger UI 显示不正常

**原因**：静态资源加载失败

**解决方案**：
1. 检查网络连接
2. 清除浏览器缓存
3. 重启应用

### 问题 3：接口测试失败

**原因**：请求参数不正确

**解决方案**：
1. 检查必填参数是否填写
2. 检查参数格式是否正确
3. 查看错误响应中的详细信息

## 更多资源

- **使用示例**: [API_EXAMPLES.md](API_EXAMPLES.md)
- **API 文档说明**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **配置指南**: [CONFIG.md](CONFIG.md)

---

**最后更新**: 2026-02-14  
**文档版本**: v1.0.0
