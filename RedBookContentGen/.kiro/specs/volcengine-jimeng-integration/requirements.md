# 需求文档：火山引擎即梦 AI 图片生成集成

## 简介

本需求文档描述了将火山引擎即梦 AI 图片生成模型集成到现有 RedBookContentGen 项目中的功能需求。该集成将为用户提供除阿里云通义万相之外的另一个 AI 图片生成选项，增强系统的灵活性和可用性。

## 术语表

- **ImageGenerator**: 现有的图片生成器类，位于 `src/image_generator.py`
- **ConfigManager**: 统一配置管理器类，位于 `src/core/config_manager.py`
- **火山引擎即梦 AI**: 火山引擎提供的文生图 AI 服务
- **通义万相**: 阿里云提供的文生图 AI 服务（现有系统使用）
- **AWS Signature V4**: 亚马逊 Web 服务签名版本 4，用于 API 请求认证
- **AccessKeyID**: 火山引擎 API 访问密钥 ID
- **SecretAccessKey**: 火山引擎 API 访问密钥（需 Base64 解码）
- **文生图**: 文本生成图片（Text-to-Image）
- **API 模式**: 使用 AI API 生成图片的模式（相对于模板模式）

## 需求

### 需求 1：配置管理

**用户故事**: 作为开发者，我希望能够在配置文件中配置火山引擎即梦 AI 的相关参数，以便灵活切换和管理不同的图片生成服务。

#### 验收标准

1. WHEN 配置文件被加载 THEN ConfigManager SHALL 支持读取火山引擎即梦 AI 的配置项
2. THE ConfigManager SHALL 支持以下火山引擎配置项：AccessKeyID、SecretAccessKey、API 端点、服务名、区域、模型名称
3. WHEN 环境变量被设置 THEN ConfigManager SHALL 允许通过环境变量覆盖火山引擎配置项
4. THE ConfigManager SHALL 支持 `${ENV_VAR}` 和 `${ENV_VAR:default}` 语法引用环境变量
5. WHEN 配置项缺失或无效 THEN ConfigManager SHALL 使用合理的默认值或返回明确的错误信息

### 需求 2：API 认证实现

**用户故事**: 作为开发者，我希望系统能够正确实现火山引擎 API 的认证机制，以便成功调用图片生成服务。

#### 验收标准

1. THE System SHALL 实现 AWS Signature V4 签名算法
2. WHEN 生成签名 THEN System SHALL 使用 AccessKeyID 和 SecretAccessKey 进行认证
3. WHEN SecretAccessKey 为 Base64 编码 THEN System SHALL 自动解码后使用
4. THE System SHALL 在 HTTP 请求头中正确设置 Authorization、X-Date、Content-Type 等必需字段
5. WHEN 签名生成失败 THEN System SHALL 返回明确的错误信息

### 需求 3：图片生成功能

**用户故事**: 作为用户，我希望能够使用火山引擎即梦 AI 生成图片，以便获得不同风格的 AI 生成图片。

#### 验收标准

1. WHEN 用户选择火山引擎模式 THEN ImageGenerator SHALL 调用火山引擎即梦 AI API 生成图片
2. WHEN 提供文本提示词 THEN System SHALL 将提示词发送到火山引擎 API 并返回生成的图片 URL
3. THE System SHALL 支持指定图片尺寸参数（如 1024x1365）
4. WHEN API 返回任务 ID THEN System SHALL 轮询任务状态直到图片生成完成或超时
5. WHEN 图片生成成功 THEN System SHALL 下载图片并保存到指定路径
6. WHEN API 调用失败 THEN System SHALL 记录错误信息并支持重试机制

### 需求 4：模型选择与切换

**用户故事**: 作为用户，我希望能够在配置中选择使用哪个图片生成模型（通义万相或火山引擎），以便根据需求灵活切换。

#### 验收标准

1. THE System SHALL 支持通过配置项 `image_api_provider` 选择图片生成服务提供商
2. WHEN `image_api_provider` 设置为 "volcengine" THEN System SHALL 使用火山引擎即梦 AI
3. WHEN `image_api_provider` 设置为 "aliyun" THEN System SHALL 使用阿里云通义万相
4. WHEN `image_api_provider` 未设置或为空 THEN System SHALL 使用默认值（阿里云通义万相）
5. THE System SHALL 在运行时根据配置动态选择对应的图片生成实现

### 需求 5：错误处理与重试

**用户故事**: 作为用户，我希望系统能够优雅地处理 API 调用失败的情况，以便提高系统的稳定性和可靠性。

#### 验收标准

1. WHEN API 调用失败 THEN System SHALL 记录详细的错误信息（包括状态码、错误消息）
2. WHEN 遇到可重试的错误（如网络超时、5xx 错误）THEN System SHALL 自动重试最多 3 次
3. WHEN 遇到不可重试的错误（如认证失败、4xx 错误）THEN System SHALL 立即返回错误而不重试
4. WHEN 重试次数耗尽 THEN System SHALL 返回最后一次的错误信息
5. THE System SHALL 在重试之间使用指数退避策略（如 1 秒、2 秒、4 秒）

### 需求 6：速率限制与缓存

**用户故事**: 作为开发者，我希望系统能够遵守 API 速率限制并利用缓存机制，以便避免超出配额并提高性能。

#### 验收标准

1. THE System SHALL 支持配置火山引擎 API 的速率限制（每分钟请求数）
2. WHEN 速率限制启用 THEN System SHALL 在发送请求前检查是否超出速率限制
3. WHEN 超出速率限制 THEN System SHALL 等待直到可以发送请求或超时
4. WHEN 缓存启用 THEN System SHALL 缓存已生成的图片 URL（基于提示词和参数的哈希）
5. WHEN 相同的提示词和参数再次请求 THEN System SHALL 从缓存返回结果而不调用 API

### 需求 7：日志记录

**用户故事**: 作为开发者，我希望系统能够记录详细的日志信息，以便调试和监控 API 调用情况。

#### 验收标准

1. THE System SHALL 使用现有的 Logger 模块记录日志
2. WHEN 调用火山引擎 API THEN System SHALL 记录请求参数（不包含敏感信息）
3. WHEN API 返回响应 THEN System SHALL 记录响应状态码和关键信息
4. WHEN 发生错误 THEN System SHALL 记录完整的错误堆栈信息
5. THE System SHALL 支持通过配置调整日志级别（DEBUG、INFO、WARNING、ERROR）

### 需求 8：命令行接口

**用户故事**: 作为用户，我希望能够通过命令行参数指定使用火山引擎模型，以便快速测试和使用。

#### 验收标准

1. THE System SHALL 支持命令行参数 `--image-provider` 或 `--provider` 指定图片生成服务提供商
2. WHEN 命令行参数指定 `--provider volcengine` THEN System SHALL 使用火山引擎即梦 AI
3. WHEN 命令行参数指定 `--provider aliyun` THEN System SHALL 使用阿里云通义万相
4. WHEN 命令行参数与配置文件冲突 THEN 命令行参数 SHALL 具有更高优先级
5. THE System SHALL 在帮助信息中显示可用的图片生成服务提供商选项

### 需求 9：向后兼容性

**用户故事**: 作为现有用户，我希望新功能不会破坏现有的系统行为，以便平滑升级。

#### 验收标准

1. WHEN 配置文件未包含火山引擎配置 THEN System SHALL 继续使用阿里云通义万相
2. WHEN 现有代码调用 ImageGenerator THEN System SHALL 保持原有行为不变
3. THE System SHALL 保持现有 API 接口的签名和行为
4. WHEN 火山引擎配置无效或缺失 THEN System SHALL 回退到阿里云通义万相并记录警告
5. THE System SHALL 不修改现有的配置文件结构（仅添加新字段）

### 需求 10：安全性

**用户故事**: 作为开发者，我希望系统能够安全地存储和使用 API 密钥，以便防止密钥泄露。

#### 验收标准

1. THE System SHALL 不在日志中记录完整的 API 密钥
2. WHEN 记录包含密钥的信息 THEN System SHALL 对密钥进行脱敏处理（如只显示前 4 位和后 4 位）
3. THE System SHALL 支持从环境变量读取 API 密钥
4. THE System SHALL 在配置示例文件中使用占位符而非真实密钥
5. WHEN 配置文件包含真实密钥 THEN System SHALL 确保该文件在 .gitignore 中

### 需求 11：文档与示例

**用户故事**: 作为用户，我希望有清晰的文档和示例，以便快速了解如何使用火山引擎集成功能。

#### 验收标准

1. THE System SHALL 提供配置示例文件（config.example.json）包含火山引擎配置项
2. THE System SHALL 在 README 或文档中说明如何配置和使用火山引擎
3. THE System SHALL 提供火山引擎 API 密钥的获取方法说明
4. THE System SHALL 提供命令行使用示例
5. THE System SHALL 说明火山引擎与阿里云通义万相的差异和选择建议
