# 火山引擎即梦 AI 图片生成集成指南

本文档详细说明如何在 RedBookContentGen 项目中使用火山引擎即梦 AI 图片生成服务。

## 目录

- [简介](#简介)
- [获取 API 密钥](#获取-api-密钥)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [与阿里云的对比](#与阿里云的对比)
- [故障排除](#故障排除)
- [API 参考](#api-参考)

## 简介

火山引擎即梦 AI 是字节跳动旗下的 AI 图片生成服务，提供高质量的文生图功能。本项目已集成火山引擎即梦 AI，作为阿里云通义万相的替代选项。

### 主要特点

- ✅ **高质量图片**：生成的图片质量高，细节丰富
- ✅ **多样化风格**：支持多种艺术风格和画面效果
- ✅ **稳定可靠**：基于字节跳动的技术积累，服务稳定
- ✅ **灵活配置**：支持多种参数调整，满足不同需求

## 获取 API 密钥

### 步骤 1：注册火山引擎账号

1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 点击「注册」按钮
3. 按照提示完成账号注册和实名认证

### 步骤 2：开通即梦 AI 服务

1. 登录火山引擎控制台
2. 在左侧菜单中找到「视觉智能」
3. 点击「即梦 AI」服务
4. 点击「立即开通」按钮
5. 阅读并同意服务协议
6. 完成开通流程

### 步骤 3：创建 API 密钥

1. 在即梦 AI 服务页面，点击「API 密钥管理」
2. 点击「创建密钥」按钮
3. 输入密钥名称（如 "RedBookContentGen"）
4. 点击「确定」
5. **重要**：立即复制并保存 `Access Key ID` 和 `Secret Access Key`
   - Access Key ID：类似 `AKLT...`
   - Secret Access Key：一串 Base64 编码的字符串
   - **注意**：Secret Access Key 只显示一次，请妥善保存

### 步骤 4：充值和配额

1. 在控制台中查看当前配额
2. 根据需要进行充值
3. 建议先充值少量金额进行测试

## 配置说明

### 方式 1：使用环境变量（推荐）

在终端中设置环境变量：

```bash
# 设置火山引擎 API 密钥
export VOLCENGINE_ACCESS_KEY_ID="your-access-key-id"
export VOLCENGINE_SECRET_ACCESS_KEY="your-secret-access-key"

# 设置图片生成服务提供商为火山引擎
export IMAGE_API_PROVIDER="volcengine"
```

**macOS/Linux 永久设置**：

将上述命令添加到 `~/.bashrc` 或 `~/.zshrc` 文件中：

```bash
echo 'export VOLCENGINE_ACCESS_KEY_ID="your-access-key-id"' >> ~/.zshrc
echo 'export VOLCENGINE_SECRET_ACCESS_KEY="your-secret-access-key"' >> ~/.zshrc
echo 'export IMAGE_API_PROVIDER="volcengine"' >> ~/.zshrc
source ~/.zshrc
```

**Windows PowerShell**：

```powershell
$env:VOLCENGINE_ACCESS_KEY_ID="your-access-key-id"
$env:VOLCENGINE_SECRET_ACCESS_KEY="your-secret-access-key"
$env:IMAGE_API_PROVIDER="volcengine"
```

### 方式 2：使用配置文件

编辑 `config/config.json` 文件：

```json
{
  "image_api_provider": "volcengine",
  "volcengine": {
    "access_key_id": "${VOLCENGINE_ACCESS_KEY_ID}",
    "secret_access_key": "${VOLCENGINE_SECRET_ACCESS_KEY}",
    "endpoint": "https://visual.volcengineapi.com",
    "service": "cv",
    "region": "cn-north-1",
    "model": "general_v2",
    "timeout": 180,
    "max_retries": 3
  }
}
```

**配置项说明**：

| 配置项 | 说明 | 默认值 | 是否必填 |
|--------|------|--------|---------|
| `access_key_id` | 火山引擎 Access Key ID | - | 是 |
| `secret_access_key` | 火山引擎 Secret Access Key | - | 是 |
| `endpoint` | API 端点 | `https://visual.volcengineapi.com` | 否 |
| `service` | 服务名称 | `cv` | 否 |
| `region` | 区域 | `cn-north-1` | 否 |
| `model` | 图片生成模型 | `general_v2` | 否 |
| `timeout` | 请求超时时间（秒） | 180 | 否 |
| `max_retries` | 最大重试次数 | 3 | 否 |

**注意**：
- 建议使用 `${VOLCENGINE_ACCESS_KEY_ID}` 语法引用环境变量，避免将密钥直接写入配置文件
- `config/config.json` 文件已在 `.gitignore` 中，不会被提交到 Git 仓库

## 使用方法

### 基本使用

#### 1. 使用命令行参数

```bash
# 使用火山引擎生成图片
python run.py --image-mode api --provider volcengine

# 使用火山引擎 + 异步并行模式
python run.py --image-mode api --provider volcengine --async-mode

# 使用火山引擎 + 主题搜索模式
python run.py --mode topic --topic "老北京胡同" --image-mode api --provider volcengine
```

#### 2. 使用配置文件

如果在配置文件中设置了 `image_api_provider: "volcengine"`，则无需指定 `--provider` 参数：

```bash
# 直接运行（使用配置文件中的设置）
python run.py --image-mode api

# 异步并行模式
python run.py --image-mode api --async-mode
```

### 高级使用

#### 自定义并发数

```bash
# 使用火山引擎 + 5 并发
python run.py --image-mode api --provider volcengine --async-mode --max-concurrent 5
```

#### 仅生成图片

```bash
# 先生成内容
python -m src.content_generator

# 再使用火山引擎生成图片
python -m src.image_generator
# 注意：需要在配置文件中设置 image_api_provider: "volcengine"
```

#### 在代码中使用

```python
from src.image_generator import ImageGenerator
from src.core.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager("config/config.json")

# 设置使用火山引擎
config_manager.set("image_api_provider", "volcengine")

# 创建图片生成器
generator = ImageGenerator(config_manager=config_manager)

# 生成单张图片
image_url = generator.generate_single_image(
    prompt="一幅老北京胡同的水墨画，清晨的阳光洒在青砖灰瓦上",
    size="1024*1365"
)

print(f"图片 URL: {image_url}")
```

## 与阿里云的对比

### 功能对比

| 特性 | 阿里云通义万相 | 火山引擎即梦 AI |
|------|--------------|----------------|
| 图片质量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 生成速度 | 快（约 10-30 秒） | 中等（约 20-60 秒） |
| 风格多样性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 价格 | 中等 | 中等 |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 文档完善度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 选择建议

**选择阿里云通义万相**：
- ✅ 需要快速批量生成图片
- ✅ 对生成速度要求高
- ✅ 需要稳定可靠的服务
- ✅ 已有阿里云账号和配额

**选择火山引擎即梦 AI**：
- ✅ 追求更高的图片质量
- ✅ 需要更多样化的艺术风格
- ✅ 对生成速度要求不高
- ✅ 已有火山引擎账号和配额

**建议**：
- 可以同时配置两个服务，根据需求灵活切换
- 建议先用少量配额测试两个服务，选择更适合自己需求的

## 故障排除

### 常见问题

#### 1. 认证失败

**错误信息**：
```
❌ 创建任务失败: 401 - Unauthorized
```

**解决方法**：
- 检查 Access Key ID 和 Secret Access Key 是否正确
- 确认密钥是否已激活
- 检查密钥是否有足够的权限

#### 2. 配额不足

**错误信息**：
```
❌ 创建任务失败: 403 - Quota exceeded
```

**解决方法**：
- 登录火山引擎控制台查看配额
- 进行充值或申请更多配额

#### 3. 内容审核未通过

**错误信息**：
```
❌ 创建任务失败: 400 - Content inspection failed
```

**解决方法**：
- 检查提示词是否包含敏感内容
- 修改提示词，移除可能触发审核的词汇
- 系统会自动尝试修改提示词并重试

#### 4. 请求超时

**错误信息**：
```
❌ 查询任务状态失败: Timeout
```

**解决方法**：
- 增加 `timeout` 配置值（默认 180 秒）
- 检查网络连接是否稳定
- 稍后重试

#### 5. Base64 密钥解码错误

**错误信息**：
```
❌ 签名计算失败: Invalid Base64 string
```

**解决方法**：
- 确认 Secret Access Key 是否正确复制
- 检查是否包含多余的空格或换行符
- 系统会自动尝试解码 Base64 编码的密钥

### 调试技巧

#### 1. 启用详细日志

在配置文件中设置日志级别：

```json
{
  "log_level": "DEBUG"
}
```

#### 2. 查看日志文件

日志文件位于 `logs/` 目录：

```bash
# 查看最新日志
tail -f logs/app.log

# 搜索错误日志
grep "ERROR" logs/app.log
```

#### 3. 测试 API 连接

```python
from src.image_providers.volcengine_provider import VolcengineImageProvider
from src.core.config_manager import ConfigManager

config_manager = ConfigManager("config/config.json")
provider = VolcengineImageProvider(
    config_manager=config_manager,
    logger=None
)

# 测试生成图片
result = provider.generate("测试图片", "1024*1365")
print(f"结果: {result}")
```

## API 参考

### VolcengineImageProvider

火山引擎图片生成服务提供商类。

#### 初始化

```python
from src.image_providers.volcengine_provider import VolcengineImageProvider
from src.core.config_manager import ConfigManager

config_manager = ConfigManager("config/config.json")
provider = VolcengineImageProvider(
    config_manager=config_manager,
    logger=logger,
    rate_limiter=rate_limiter,  # 可选
    cache=cache  # 可选
)
```

#### 方法

##### generate()

生成图片。

**参数**：
- `prompt` (str): 图片提示词
- `size` (str): 图片尺寸，格式为 "宽*高"，默认 "1024*1365"
- `**kwargs`: 其他参数

**返回**：
- `str | None`: 图片 URL，失败返回 None

**示例**：

```python
image_url = provider.generate(
    prompt="一幅老北京胡同的水墨画",
    size="1024*1365"
)
```

##### get_provider_name()

获取服务提供商名称。

**返回**：
- `str`: "volcengine"

### VolcengineSignatureV4

AWS Signature V4 签名算法实现类。

#### 初始化

```python
from src.volcengine.signature import VolcengineSignatureV4

signer = VolcengineSignatureV4(
    access_key_id="your-access-key-id",
    secret_access_key="your-secret-access-key",
    service="cv",
    region="cn-north-1"
)
```

#### 方法

##### sign()

签名 HTTP 请求。

**参数**：
- `method` (str): HTTP 方法（GET, POST 等）
- `url` (str): 完整的请求 URL
- `headers` (dict): 请求头字典
- `body` (str): 请求体（可选）

**返回**：
- `dict`: 包含 Authorization 头的字典

**示例**：

```python
signed_headers = signer.sign(
    method="POST",
    url="https://visual.volcengineapi.com/CreateImageTask",
    headers={"Content-Type": "application/json"},
    body='{"prompt": "test"}'
)
```

## 相关链接

- [火山引擎官网](https://www.volcengine.com/)
- [火山引擎控制台](https://console.volcengine.com/)
- [即梦 AI 文档](https://www.volcengine.com/docs/6791/1104851)
- [API 参考文档](https://www.volcengine.com/docs/6791/1104852)

## 更新日志

### v1.0.0 (2024-02-15)

- ✅ 初始版本
- ✅ 支持火山引擎即梦 AI 图片生成
- ✅ 实现 AWS Signature V4 签名算法
- ✅ 支持速率限制和缓存
- ✅ 支持错误重试和指数退避
- ✅ 完整的单元测试和集成测试

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。
