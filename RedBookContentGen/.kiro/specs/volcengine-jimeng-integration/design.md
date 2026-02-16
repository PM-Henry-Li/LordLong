# 设计文档：火山引擎即梦 AI 图片生成集成

## 概述

本设计文档描述了如何将火山引擎即梦 AI 图片生成服务集成到现有的 RedBookContentGen 项目中。设计遵循以下原则：

1. **最小侵入性**: 尽量不修改现有代码结构，通过扩展而非修改来实现新功能
2. **统一接口**: 为不同的图片生成服务提供统一的接口，便于切换和扩展
3. **配置驱动**: 通过配置文件和环境变量控制行为，无需修改代码
4. **向后兼容**: 确保现有功能不受影响，新功能作为可选项添加
5. **安全第一**: 妥善处理 API 密钥，避免泄露

### 技术栈

- **Python 3**: 主要编程语言
- **requests**: HTTP 请求库
- **hashlib**: 用于 AWS Signature V4 签名计算
- **hmac**: 用于 HMAC 签名
- **base64**: 用于密钥解码
- **现有的 ConfigManager**: 统一配置管理
- **现有的 Logger**: 日志记录
- **现有的 RateLimiter**: 速率限制
- **现有的 CacheManager**: 缓存管理

## 架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         run.py                              │
│                    (主入口，命令行参数)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   ImageGenerator                            │
│              (现有图片生成器，协调者)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _get_image_provider() -> BaseImageProvider          │  │
│  │  根据配置返回具体的图片生成服务提供商实例                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────────┐
│AliyunImageProvider│          │VolcengineImageProvider│
│  (阿里云通义万相)  │          │  (火山引擎即梦 AI)     │
│                  │          │                      │
│ - generate()     │          │ - generate()         │
│ - _create_task() │          │ - _sign_request()    │
│ - _poll_status() │          │ - _create_task()     │
└──────────────────┘          │ - _poll_status()     │
                              └──────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │VolcengineSignatureV4 │
                              │  (AWS 签名算法)       │
                              │                      │
                              │ - sign()             │
                              │ - _get_canonical_*() │
                              └──────────────────────┘
```

### 设计模式

1. **策略模式 (Strategy Pattern)**: 
   - `BaseImageProvider` 作为抽象策略
   - `AliyunImageProvider` 和 `VolcengineImageProvider` 作为具体策略
   - `ImageGenerator` 作为上下文，根据配置选择策略

2. **工厂模式 (Factory Pattern)**:
   - `ImageGenerator._get_image_provider()` 作为工厂方法
   - 根据配置创建对应的图片生成服务提供商实例

3. **单一职责原则 (Single Responsibility Principle)**:
   - `VolcengineSignatureV4` 专门负责签名计算
   - `VolcengineImageProvider` 负责与火山引擎 API 交互
   - `ImageGenerator` 负责协调和流程控制

## 组件与接口

### 1. BaseImageProvider (抽象基类)

**职责**: 定义图片生成服务提供商的统一接口

**接口**:

```python
from abc import ABC, abstractmethod
from typing import Optional

class BaseImageProvider(ABC):
    """图片生成服务提供商抽象基类"""
    
    def __init__(self, config_manager, logger, rate_limiter=None, cache=None):
        """
        初始化图片生成服务提供商
        
        Args:
            config_manager: ConfigManager 实例
            logger: Logger 实例
            rate_limiter: RateLimiter 实例（可选）
            cache: CacheManager 实例（可选）
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str, size: str = "1024*1365", **kwargs) -> Optional[str]:
        """
        生成图片
        
        Args:
            prompt: 图片提示词
            size: 图片尺寸，格式为 "宽*高"
            **kwargs: 其他参数
            
        Returns:
            图片 URL，失败返回 None
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取服务提供商名称
        
        Returns:
            服务提供商名称（如 "aliyun", "volcengine"）
        """
        pass
```

### 2. AliyunImageProvider (阿里云实现)

**职责**: 封装现有的阿里云通义万相图片生成逻辑

**实现**: 将 `ImageGenerator` 中现有的阿里云相关代码重构到此类中

**关键方法**:
- `generate()`: 调用阿里云 API 生成图片
- `_create_task()`: 创建异步任务
- `_poll_status()`: 轮询任务状态
- `_download_image()`: 下载图片

### 3. VolcengineImageProvider (火山引擎实现)

**职责**: 实现火山引擎即梦 AI 的图片生成逻辑

**配置项**:
```python
{
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

**关键方法**:

```python
def generate(self, prompt: str, size: str = "1024*1365", **kwargs) -> Optional[str]:
    """
    生成图片
    
    流程:
    1. 检查缓存
    2. 检查速率限制
    3. 构建请求参数
    4. 签名请求
    5. 发送请求创建任务
    6. 轮询任务状态
    7. 下载图片
    8. 缓存结果
    
    Args:
        prompt: 图片提示词
        size: 图片尺寸
        **kwargs: 其他参数
        
    Returns:
        图片 URL 或 None
    """
    pass

def _sign_request(self, method: str, path: str, query: dict, headers: dict, body: str) -> dict:
    """
    使用 AWS Signature V4 签名请求
    
    Args:
        method: HTTP 方法
        path: 请求路径
        query: 查询参数
        headers: 请求头
        body: 请求体
        
    Returns:
        包含签名的请求头
    """
    pass

def _create_task(self, prompt: str, size: str) -> str:
    """
    创建图片生成任务
    
    Args:
        prompt: 图片提示词
        size: 图片尺寸
        
    Returns:
        任务 ID
    """
    pass

def _poll_status(self, task_id: str, max_wait: int = 180) -> str:
    """
    轮询任务状态
    
    Args:
        task_id: 任务 ID
        max_wait: 最大等待时间（秒）
        
    Returns:
        图片 URL
    """
    pass
```

### 4. VolcengineSignatureV4 (签名工具类)

**职责**: 实现 AWS Signature V4 签名算法

**关键方法**:

```python
class VolcengineSignatureV4:
    """AWS Signature V4 签名算法实现"""
    
    def __init__(self, access_key_id: str, secret_access_key: str, service: str, region: str):
        """
        初始化签名器
        
        Args:
            access_key_id: 访问密钥 ID
            secret_access_key: 访问密钥（如果是 Base64 编码，会自动解码）
            service: 服务名（如 "cv"）
            region: 区域（如 "cn-north-1"）
        """
        self.access_key_id = access_key_id
        # 自动检测并解码 Base64 编码的密钥
        self.secret_access_key = self._decode_secret_key(secret_access_key)
        self.service = service
        self.region = region
    
    def _decode_secret_key(self, secret_key: str) -> str:
        """
        解码 Base64 编码的密钥
        
        Args:
            secret_key: 可能是 Base64 编码的密钥
            
        Returns:
            解码后的密钥
        """
        pass
    
    def sign(self, method: str, url: str, headers: dict, body: str = "") -> dict:
        """
        签名 HTTP 请求
        
        Args:
            method: HTTP 方法（GET, POST 等）
            url: 完整的请求 URL
            headers: 请求头字典
            body: 请求体（可选）
            
        Returns:
            包含 Authorization 头的字典
        """
        pass
    
    def _get_canonical_request(self, method: str, path: str, query: str, 
                               headers: dict, signed_headers: str, 
                               payload_hash: str) -> str:
        """
        构建规范请求
        
        Returns:
            规范请求字符串
        """
        pass
    
    def _get_string_to_sign(self, timestamp: str, credential_scope: str, 
                           canonical_request_hash: str) -> str:
        """
        构建待签名字符串
        
        Returns:
            待签名字符串
        """
        pass
    
    def _get_signature(self, secret_key: str, timestamp: str, 
                      credential_scope: str, string_to_sign: str) -> str:
        """
        计算签名
        
        Returns:
            签名字符串（十六进制）
        """
        pass
```

**签名算法流程**:

1. **创建规范请求 (Canonical Request)**:
   ```
   HTTP_METHOD + '\n' +
   CANONICAL_URI + '\n' +
   CANONICAL_QUERY_STRING + '\n' +
   CANONICAL_HEADERS + '\n' +
   SIGNED_HEADERS + '\n' +
   HASHED_PAYLOAD
   ```

2. **创建待签名字符串 (String to Sign)**:
   ```
   'AWS4-HMAC-SHA256' + '\n' +
   TIMESTAMP + '\n' +
   CREDENTIAL_SCOPE + '\n' +
   HASHED_CANONICAL_REQUEST
   ```

3. **计算签名 (Signature)**:
   ```
   kDate = HMAC-SHA256("AWS4" + SECRET_KEY, DATE)
   kRegion = HMAC-SHA256(kDate, REGION)
   kService = HMAC-SHA256(kRegion, SERVICE)
   kSigning = HMAC-SHA256(kService, "aws4_request")
   signature = HMAC-SHA256(kSigning, STRING_TO_SIGN)
   ```

4. **构建 Authorization 头**:
   ```
   'AWS4-HMAC-SHA256 ' +
   'Credential=' + ACCESS_KEY_ID + '/' + CREDENTIAL_SCOPE + ', ' +
   'SignedHeaders=' + SIGNED_HEADERS + ', ' +
   'Signature=' + SIGNATURE
   ```

### 5. ImageGenerator 修改

**修改内容**:

1. 添加工厂方法 `_get_image_provider()`:
```python
def _get_image_provider(self) -> BaseImageProvider:
    """
    根据配置获取图片生成服务提供商
    
    Returns:
        BaseImageProvider 实例
    """
    provider_name = self.config_manager.get("image_api_provider", "aliyun")
    
    if provider_name == "volcengine":
        return VolcengineImageProvider(
            config_manager=self.config_manager,
            logger=self.logger,
            rate_limiter=self.rpm_limiter,
            cache=self.cache
        )
    elif provider_name == "aliyun":
        return AliyunImageProvider(
            config_manager=self.config_manager,
            logger=self.logger,
            rate_limiter=self.rpm_limiter,
            cache=self.cache
        )
    else:
        self.logger.warning(f"未知的图片生成服务提供商: {provider_name}，使用默认值 aliyun")
        return AliyunImageProvider(
            config_manager=self.config_manager,
            logger=self.logger,
            rate_limiter=self.rpm_limiter,
            cache=self.cache
        )
```

2. 修改 `generate_single_image()` 和 `generate_image_async()`:
```python
def generate_single_image(self, prompt: str, size: str = "1024*1365") -> Optional[str]:
    """为 Web API 生成单张图片"""
    provider = self._get_image_provider()
    return provider.generate(prompt, size)

def generate_image_async(self, prompt: str, index: int, is_cover: bool = False) -> str:
    """异步生成单张图片"""
    provider = self._get_image_provider()
    return provider.generate(prompt, "1024*1365", is_cover=is_cover)
```

## 数据模型

### 配置数据模型

```python
# config/config.json 新增部分
{
    "image_api_provider": "aliyun",  # 可选: "aliyun", "volcengine"
    
    "volcengine": {
        "access_key_id": "${VOLCENGINE_ACCESS_KEY_ID}",
        "secret_access_key": "${VOLCENGINE_SECRET_ACCESS_KEY}",
        "endpoint": "https://visual.volcengineapi.com",
        "service": "cv",
        "region": "cn-north-1",
        "model": "general_v2",
        "timeout": 180,
        "max_retries": 3,
        "retry_delay": 1.0,
        "api_version": "2022-08-31"
    }
}
```

### 环境变量映射

在 `ConfigManager.ENV_VAR_MAPPING` 中添加:

```python
ENV_VAR_MAPPING = {
    # ... 现有映射 ...
    
    # 火山引擎配置
    "VOLCENGINE_ACCESS_KEY_ID": "volcengine.access_key_id",
    "VOLCENGINE_SECRET_ACCESS_KEY": "volcengine.secret_access_key",
    "VOLCENGINE_ENDPOINT": "volcengine.endpoint",
    "VOLCENGINE_SERVICE": "volcengine.service",
    "VOLCENGINE_REGION": "volcengine.region",
    "VOLCENGINE_MODEL": "volcengine.model",
    "IMAGE_API_PROVIDER": "image_api_provider",
}
```

### 火山引擎 API 请求/响应模型

**创建任务请求**:
```python
{
    "req_key": "text2image_task_<timestamp>",
    "prompt": "图片提示词",
    "model_version": "general_v2",
    "scale": 2,  # 图片质量
    "width": 1024,
    "height": 1365,
    "seed": -1,  # 随机种子，-1 表示随机
    "use_sr": False  # 是否使用超分辨率
}
```

**创建任务响应**:
```python
{
    "code": 10000,  # 10000 表示成功
    "message": "Success",
    "data": {
        "task_id": "7123456789012345678",
        "status": "processing"  # processing, success, failed
    },
    "time_elapsed": "123ms"
}
```

**查询任务状态请求**:
```python
# GET 请求
# URL: /GetImageTask?task_id=<task_id>
```

**查询任务状态响应**:
```python
{
    "code": 10000,
    "message": "Success",
    "data": {
        "task_id": "7123456789012345678",
        "status": "success",  # processing, success, failed
        "image_urls": [
            "https://example.com/image.jpg"
        ],
        "progress": 100  # 0-100
    },
    "time_elapsed": "45ms"
}
```

### 错误码映射

```python
VOLCENGINE_ERROR_CODES = {
    10000: "成功",
    10001: "参数错误",
    10002: "认证失败",
    10003: "权限不足",
    10004: "配额不足",
    10005: "任务不存在",
    10006: "任务失败",
    10007: "内容审核未通过",
    10008: "服务内部错误",
    10009: "请求超时",
}
```


## 正确性属性

属性是一种特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。

### 属性反思

在编写属性之前，我识别并消除了以下冗余：

1. **需求 6.4 和 6.5 合并**: 两者都测试缓存功能，可以合并为一个综合属性
2. **需求 1.3 和 10.3 合并**: 两者都测试环境变量读取功能，可以合并
3. **需求 4.2 和 4.3**: 这些是特定示例，不需要单独的属性，可以作为单元测试

### 配置管理属性

**属性 1: 配置加载完整性**
*对于任何* 包含火山引擎配置的有效配置文件，加载后应该能够读取所有必需的配置项（AccessKeyID、SecretAccessKey、端点、服务名、区域、模型名称）
**验证需求: 1.1, 1.2**

**属性 2: 环境变量覆盖**
*对于任何* 支持环境变量的配置项，当环境变量被设置时，其值应该覆盖配置文件中的值
**验证需求: 1.3, 10.3**

**属性 3: 环境变量引用解析**
*对于任何* 包含 `${ENV_VAR}` 或 `${ENV_VAR:default}` 语法的配置值，应该正确解析为环境变量的值或默认值
**验证需求: 1.4**

**属性 4: 配置默认值和错误处理**
*对于任何* 缺失或无效的配置项，系统应该使用合理的默认值或返回明确的错误信息
**验证需求: 1.5**

### API 认证属性

**属性 5: 签名密钥依赖性**
*对于任何* 给定的请求参数，使用不同的 AccessKeyID 或 SecretAccessKey 应该生成不同的签名
**验证需求: 2.2**

**属性 6: Base64 密钥解码**
*对于任何* Base64 编码的 SecretAccessKey，系统应该自动解码后使用，生成的签名应该与使用解码后密钥直接生成的签名相同
**验证需求: 2.3**

**属性 7: 请求头完整性**
*对于任何* 签名请求，生成的请求头应该包含所有必需字段（Authorization、X-Date、Content-Type），且格式符合 AWS Signature V4 规范
**验证需求: 2.4**

**属性 8: 签名错误处理**
*对于任何* 无效的签名输入（如空密钥、无效 URL），系统应该返回明确的错误信息而不是崩溃
**验证需求: 2.5**

### 图片生成属性

**属性 9: 提供商选择正确性**
*对于任何* 配置的 `image_api_provider` 值，系统应该选择对应的图片生成服务提供商实现
**验证需求: 3.1, 4.1, 4.5**

**属性 10: 尺寸参数传递**
*对于任何* 指定的图片尺寸参数，该参数应该正确传递到 API 请求中
**验证需求: 3.3**

**属性 11: 轮询终止条件**
*对于任何* 图片生成任务，轮询应该在以下条件之一满足时终止：任务成功、任务失败、或达到超时时间
**验证需求: 3.4**

**属性 12: 图片保存完整性**
*对于任何* 成功生成的图片，图片应该被下载并保存到指定路径，且文件应该存在且可读
**验证需求: 3.5**

**属性 13: API 失败重试**
*对于任何* API 调用失败，系统应该记录错误信息，并在错误可重试时进行重试
**验证需求: 3.6**

### 模型选择属性

**属性 14: 默认提供商回退**
*对于任何* 未设置、为空、或无效的 `image_api_provider` 配置，系统应该使用默认的阿里云通义万相
**验证需求: 4.4, 9.1, 9.4**

**属性 15: 命令行参数优先级**
*对于任何* 同时设置的命令行参数和配置文件值，命令行参数应该具有更高优先级
**验证需求: 8.4**

### 错误处理与重试属性

**属性 16: 错误日志完整性**
*对于任何* API 调用失败，日志应该包含详细的错误信息（状态码、错误消息、堆栈信息）
**验证需求: 5.1, 7.4**

**属性 17: 可重试错误重试次数**
*对于任何* 可重试的错误（网络超时、5xx 错误），系统应该重试最多 3 次
**验证需求: 5.2**

**属性 18: 不可重试错误立即返回**
*对于任何* 不可重试的错误（认证失败、4xx 错误），系统应该立即返回错误而不重试
**验证需求: 5.3**

**属性 19: 重试耗尽错误返回**
*对于任何* 重试次数耗尽的情况，系统应该返回最后一次的错误信息
**验证需求: 5.4**

**属性 20: 指数退避策略**
*对于任何* 重试序列，重试之间的时间间隔应该遵循指数退避策略（每次重试的等待时间是前一次的 2 倍）
**验证需求: 5.5**

### 速率限制与缓存属性

**属性 21: 速率限制检查**
*对于任何* 启用速率限制的配置，在发送请求前应该检查是否超出速率限制，超出时应该等待
**验证需求: 6.1, 6.2, 6.3**

**属性 22: 缓存幂等性**
*对于任何* 相同的提示词和参数，第一次请求应该调用 API，后续请求应该从缓存返回相同的结果
**验证需求: 6.4, 6.5**

### 日志记录属性

**属性 23: 日志系统集成**
*对于任何* 日志记录操作，应该使用现有的 Logger 模块，且日志级别应该可通过配置调整
**验证需求: 7.1, 7.5**

**属性 24: 请求日志脱敏**
*对于任何* 包含 API 密钥的日志记录，密钥应该被脱敏处理（只显示前 4 位和后 4 位）
**验证需求: 7.2, 10.1, 10.2**

**属性 25: 响应日志记录**
*对于任何* API 响应，日志应该包含响应状态码和关键信息
**验证需求: 7.3**

### 向后兼容性属性

**属性 26: API 接口兼容性**
*对于任何* 现有的 ImageGenerator 调用方式，系统应该保持原有行为不变，接口签名应该保持不变
**验证需求: 9.2, 9.3**

**属性 27: 配置结构兼容性**
*对于任何* 现有的配置文件，系统应该能够正常加载和使用，新配置项应该是可选的
**验证需求: 9.5**

## 错误处理

### 错误分类

系统将错误分为以下几类：

1. **配置错误**:
   - 缺失必需的配置项（如 API 密钥）
   - 配置格式错误（如无效的 JSON）
   - 配置值无效（如负数的超时时间）
   
   **处理策略**: 在初始化时检测并抛出明确的异常，提供详细的错误信息和修复建议

2. **认证错误**:
   - API 密钥无效
   - 签名计算错误
   - 权限不足
   
   **处理策略**: 立即返回错误，不重试，记录详细的错误信息

3. **网络错误**:
   - 连接超时
   - 读取超时
   - DNS 解析失败
   
   **处理策略**: 使用指数退避策略重试最多 3 次

4. **API 错误**:
   - 4xx 客户端错误（除 429 外）：立即返回，不重试
   - 429 速率限制错误：等待后重试
   - 5xx 服务器错误：使用指数退避策略重试最多 3 次
   
   **处理策略**: 根据错误码决定是否重试

5. **业务错误**:
   - 内容审核未通过
   - 任务失败
   - 配额不足
   
   **处理策略**: 记录详细信息，返回明确的错误消息，不重试

### 错误处理流程

```python
def _handle_api_error(self, error: Exception, retry_count: int) -> tuple[bool, str]:
    """
    处理 API 错误
    
    Args:
        error: 异常对象
        retry_count: 当前重试次数
        
    Returns:
        (是否应该重试, 错误消息)
    """
    # 1. 记录错误
    self.logger.error(f"API 调用失败", error=str(error), retry_count=retry_count)
    
    # 2. 分类错误
    if isinstance(error, requests.exceptions.Timeout):
        # 网络超时，可重试
        return (retry_count < 3, "网络超时")
    
    elif isinstance(error, requests.exceptions.ConnectionError):
        # 连接错误，可重试
        return (retry_count < 3, "连接失败")
    
    elif isinstance(error, requests.exceptions.HTTPError):
        status_code = error.response.status_code
        
        if status_code == 429:
            # 速率限制，可重试
            return (retry_count < 3, "速率限制")
        
        elif 400 <= status_code < 500:
            # 客户端错误，不重试
            return (False, f"客户端错误: {status_code}")
        
        elif 500 <= status_code < 600:
            # 服务器错误，可重试
            return (retry_count < 3, f"服务器错误: {status_code}")
    
    # 3. 未知错误，不重试
    return (False, f"未知错误: {str(error)}")
```

### 错误恢复策略

1. **配置错误**: 提供详细的错误信息和修复建议，引导用户修正配置
2. **认证错误**: 提示用户检查 API 密钥是否正确
3. **网络错误**: 自动重试，如果持续失败则建议用户检查网络连接
4. **API 错误**: 根据错误码提供具体的解决方案
5. **业务错误**: 提供明确的错误原因和可能的解决方案

### 降级策略

当火山引擎服务不可用时，系统应该：

1. 记录警告日志
2. 自动回退到阿里云通义万相
3. 通知用户已切换到备用服务
4. 继续正常运行

## 测试策略

### 双重测试方法

系统采用单元测试和基于属性的测试相结合的方法：

- **单元测试**: 验证特定示例、边界情况和错误条件
- **属性测试**: 验证跨所有输入的通用属性
- 两者互补，共同确保全面覆盖

### 单元测试

单元测试专注于：

1. **特定示例**: 
   - 使用已知的测试向量验证 AWS Signature V4 签名算法
   - 测试特定的配置值（如 "volcengine", "aliyun"）
   - 测试特定的错误码处理

2. **边界情况**:
   - 空字符串、None 值
   - 最大/最小配置值
   - 未设置的配置项

3. **错误条件**:
   - 无效的配置格式
   - 网络错误
   - API 错误响应

4. **集成点**:
   - ConfigManager 集成
   - Logger 集成
   - RateLimiter 集成
   - CacheManager 集成

### 基于属性的测试

基于属性的测试专注于：

1. **通用属性**: 验证跨所有输入的通用规则
2. **随机输入**: 使用随机生成的输入测试系统行为
3. **边界探索**: 自动发现边界情况和异常输入

**配置**:
- 每个属性测试运行最少 100 次迭代
- 每个测试必须引用其设计文档属性
- 标签格式: `Feature: volcengine-jimeng-integration, Property {number}: {property_text}`

**示例**:

```python
# 使用 hypothesis 库进行基于属性的测试
from hypothesis import given, strategies as st
import pytest

@given(
    access_key_id=st.text(min_size=1, max_size=100),
    secret_access_key=st.text(min_size=1, max_size=100)
)
def test_property_5_signature_key_dependency(access_key_id, secret_access_key):
    """
    Feature: volcengine-jimeng-integration
    Property 5: 签名密钥依赖性
    
    对于任何给定的请求参数，使用不同的 AccessKeyID 或 SecretAccessKey 
    应该生成不同的签名
    """
    signer1 = VolcengineSignatureV4(access_key_id, secret_access_key, "cv", "cn-north-1")
    signer2 = VolcengineSignatureV4(access_key_id + "x", secret_access_key, "cv", "cn-north-1")
    
    method = "POST"
    url = "https://visual.volcengineapi.com/CreateImageTask"
    headers = {"Content-Type": "application/json"}
    body = '{"prompt": "test"}'
    
    sig1 = signer1.sign(method, url, headers, body)
    sig2 = signer2.sign(method, url, headers, body)
    
    assert sig1["Authorization"] != sig2["Authorization"]

@given(
    prompt=st.text(min_size=1, max_size=1000),
    size=st.sampled_from(["1024*1365", "1080*1080", "512*512"])
)
def test_property_10_size_parameter_passing(prompt, size):
    """
    Feature: volcengine-jimeng-integration
    Property 10: 尺寸参数传递
    
    对于任何指定的图片尺寸参数，该参数应该正确传递到 API 请求中
    """
    # Mock API 调用
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "code": 10000,
            "data": {"task_id": "test_task_id"}
        }
        
        provider = VolcengineImageProvider(config_manager, logger)
        provider._create_task(prompt, size)
        
        # 验证请求参数
        call_args = mock_post.call_args
        request_body = json.loads(call_args[1]['data'])
        
        width, height = size.split('*')
        assert request_body['width'] == int(width)
        assert request_body['height'] == int(height)

@given(
    prompt=st.text(min_size=1, max_size=100),
    size=st.text(min_size=1, max_size=20)
)
def test_property_22_cache_idempotency(prompt, size):
    """
    Feature: volcengine-jimeng-integration
    Property 22: 缓存幂等性
    
    对于任何相同的提示词和参数，第一次请求应该调用 API，
    后续请求应该从缓存返回相同的结果
    """
    # Mock API 调用
    with patch.object(provider, '_create_task') as mock_create:
        mock_create.return_value = "test_task_id"
        
        with patch.object(provider, '_poll_status') as mock_poll:
            mock_poll.return_value = "https://example.com/image.jpg"
            
            # 第一次调用
            result1 = provider.generate(prompt, size)
            assert mock_create.call_count == 1
            
            # 第二次调用（应该从缓存返回）
            result2 = provider.generate(prompt, size)
            assert mock_create.call_count == 1  # 没有增加
            assert result1 == result2
```

### 测试覆盖目标

- **代码覆盖率**: 目标 80% 以上
- **属性覆盖率**: 所有 27 个属性都应该有对应的属性测试
- **边界情况覆盖**: 所有标记为 edge-case 的验收标准都应该有单元测试
- **错误路径覆盖**: 所有错误处理分支都应该被测试

### Mock 策略

为了避免在测试中调用真实的 API，我们使用以下 mock 策略：

1. **HTTP 请求 Mock**: 使用 `unittest.mock.patch` mock `requests` 库
2. **配置 Mock**: 创建测试专用的配置对象
3. **文件系统 Mock**: 使用临时目录进行文件操作测试
4. **时间 Mock**: 使用 `freezegun` 库 mock 时间相关功能

### 测试数据

使用以下测试数据：

1. **AWS Signature V4 测试向量**: 使用 AWS 官方提供的测试向量
2. **火山引擎 API 响应示例**: 基于官方文档的响应示例
3. **随机生成的测试数据**: 使用 `hypothesis` 库生成

### 持续集成

虽然当前项目没有 CI/CD 配置，但建议：

1. 在每次提交前运行所有测试
2. 使用 `pytest` 作为测试运行器
3. 生成测试覆盖率报告
4. 在 PR 中要求测试通过

### 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_volcengine_provider.py

# 运行属性测试（更多迭代）
pytest tests/test_volcengine_properties.py --hypothesis-iterations=1000

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行特定属性测试
pytest tests/test_volcengine_properties.py::test_property_5_signature_key_dependency
```
