# RedBookContentGen 项目改进设计文档

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     Web Layer (Flask)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ REST API │  │ WebSocket│  │  Static  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Content Service│  │Image Service │  │Search Service│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   Core Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Config  │  │  Logger  │  │  Cache   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                 External Services                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │OpenAI API│  │Aliyun API│  │Xiaohongshu│             │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块设计

#### 1.2.1 配置管理模块 (ConfigManager)

**职责**: 统一管理所有配置项

**接口设计**:
```python
class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器"""
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        pass
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        pass
    
    def validate(self) -> bool:
        """验证配置完整性"""
        pass
    
    def reload(self) -> None:
        """重新加载配置"""
        pass
```

**配置优先级**:
1. 环境变量（最高）
2. 配置文件
3. 默认值（最低）

**配置结构**:
```json
{
  "api": {
    "openai": {
      "key": "${OPENAI_API_KEY}",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen-plus",
      "timeout": 30,
      "max_retries": 3
    },
    "image": {
      "model": "wan2.2-t2i-flash",
      "size": "1024*1365",
      "timeout": 180
    }
  },
  "cache": {
    "enabled": true,
    "ttl": 3600,
    "max_size": "1GB"
  },
  "rate_limit": {
    "openai": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000
    },
    "image": {
      "requests_per_minute": 10
    }
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 5
  }
}
```

#### 1.2.2 日志模块 (Logger)

**职责**: 提供结构化日志记录

**接口设计**:
```python
class Logger:
    """结构化日志记录器"""
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """获取日志记录器"""
        pass
    
    @staticmethod
    def debug(message: str, **kwargs):
        """调试日志"""
        pass
    
    @staticmethod
    def info(message: str, **kwargs):
        """信息日志"""
        pass
    
    @staticmethod
    def warning(message: str, **kwargs):
        """警告日志"""
        pass
    
    @staticmethod
    def error(message: str, **kwargs):
        """错误日志"""
        pass
```

**日志格式**:
```json
{
  "timestamp": "2026-02-12T10:30:00.000Z",
  "level": "INFO",
  "logger": "content_generator",
  "message": "开始生成内容",
  "context": {
    "user_id": "user123",
    "request_id": "req-abc-123",
    "input_length": 150
  }
}
```

#### 1.2.3 缓存模块 (CacheManager)

**职责**: 管理内容和图片缓存

**接口设计**:
```python
class CacheManager:
    """缓存管理器"""
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        pass
    
    def delete(self, key: str) -> None:
        """删除缓存"""
        pass
    
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        pass
```

**缓存策略**:
- 文案生成: 基于输入内容的hash，TTL=1小时
- 图片URL: 基于prompt的hash，TTL=24小时
- LRU淘汰策略

#### 1.2.4 速率限制模块 (RateLimiter)

**职责**: 控制API调用频率

**接口设计**:
```python
class RateLimiter:
    """速率限制器（令牌桶算法）"""
    
    def __init__(self, rate: int, capacity: int):
        """
        初始化速率限制器
        
        Args:
            rate: 每秒生成的令牌数
            capacity: 令牌桶容量
        """
        pass
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        获取令牌
        
        Returns:
            是否成功获取
        """
        pass
    
    def wait_for_token(self, tokens: int = 1) -> None:
        """等待直到获取到令牌"""
        pass
```

### 1.3 服务层设计

#### 1.3.1 内容生成服务 (ContentService)

**职责**: 封装内容生成逻辑

**接口设计**:
```python
class ContentService:
    """内容生成服务"""
    
    def __init__(self, config: ConfigManager, cache: CacheManager, 
                 rate_limiter: RateLimiter):
        pass
    
    async def generate_content(self, input_text: str, 
                              options: Dict) -> ContentResult:
        """
        生成小红书内容
        
        Args:
            input_text: 输入文本
            options: 生成选项
            
        Returns:
            生成结果
        """
        pass
    
    async def generate_batch(self, inputs: List[str], 
                            options: Dict) -> List[ContentResult]:
        """批量生成内容"""
        pass
```

#### 1.3.2 图片生成服务 (ImageService)

**职责**: 封装图片生成逻辑

**接口设计**:
```python
class ImageService:
    """图片生成服务"""
    
    def __init__(self, config: ConfigManager, cache: CacheManager,
                 rate_limiter: RateLimiter):
        pass
    
    async def generate_image(self, prompt: str, 
                            options: ImageOptions) -> ImageResult:
        """
        生成单张图片
        
        Args:
            prompt: 图片提示词
            options: 生成选项
            
        Returns:
            图片结果
        """
        pass
    
    async def generate_batch(self, prompts: List[str],
                            options: ImageOptions) -> List[ImageResult]:
        """
        并行生成多张图片
        
        Args:
            prompts: 提示词列表
            options: 生成选项
            
        Returns:
            图片结果列表
        """
        pass
```

## 2. 性能优化设计

### 2.1 并行图片生成

**实现方案**: 使用 asyncio + aiohttp

```python
async def generate_images_parallel(prompts: List[str], 
                                   max_concurrent: int = 3) -> List[ImageResult]:
    """
    并行生成图片
    
    Args:
        prompts: 提示词列表
        max_concurrent: 最大并发数
        
    Returns:
        图片结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def generate_with_semaphore(prompt: str) -> ImageResult:
        async with semaphore:
            return await generate_single_image(prompt)
    
    tasks = [generate_with_semaphore(p) for p in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results
```

**性能提升**:
- 串行: 5张图片 × 60秒 = 300秒
- 并行(3并发): 5张图片 ÷ 3 × 60秒 = 120秒
- 提升: 60%

### 2.2 缓存机制

**缓存层次**:
1. 内存缓存（Redis）- 热数据
2. 文件缓存 - 图片文件
3. 数据库缓存 - 历史记录

**缓存键设计**:
```python
def generate_cache_key(input_text: str, options: Dict) -> str:
    """生成缓存键"""
    content = f"{input_text}:{json.dumps(options, sort_keys=True)}"
    return hashlib.sha256(content.encode()).hexdigest()
```

### 2.3 数据库设计

**表结构**:

```sql
-- 生成历史表
CREATE TABLE generation_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64),
    input_text TEXT,
    content_result JSON,
    image_results JSON,
    options JSON,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_status (status)
);

-- 模板表
CREATE TABLE templates (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    description TEXT,
    style VARCHAR(50),
    config JSON,
    preview_url VARCHAR(500),
    downloads INT DEFAULT 0,
    rating DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_style (style),
    INDEX idx_rating (rating)
);

-- 缓存表
CREATE TABLE cache_entries (
    cache_key VARCHAR(64) PRIMARY KEY,
    value LONGTEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expires (expires_at)
);
```

## 3. 安全设计

### 3.1 敏感信息保护

**加密存储**:
```python
from cryptography.fernet import Fernet

class SecretManager:
    """密钥管理器"""
    
    def __init__(self, master_key: str):
        self.cipher = Fernet(master_key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """加密"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """解密"""
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

**环境变量**:
```bash
# .env
OPENAI_API_KEY=sk-xxx
MASTER_KEY=xxx
DATABASE_URL=postgresql://user:pass@localhost/db
```

### 3.2 输入验证

**验证规则**:
```python
from pydantic import BaseModel, Field, validator

class ContentGenerationRequest(BaseModel):
    """内容生成请求"""
    
    input_text: str = Field(..., min_length=10, max_length=5000)
    count: int = Field(default=1, ge=1, le=10)
    style: str = Field(default="retro_chinese")
    
    @validator('input_text')
    def validate_input_text(cls, v):
        """验证输入文本"""
        # 移除危险字符
        dangerous_chars = ['<', '>', '&', '"', "'"]
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"输入包含非法字符: {char}")
        return v
```

### 3.3 Web安全

**CSRF保护**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route('/api/generate', methods=['POST'])
@csrf.exempt  # API接口使用Token认证
def generate():
    pass
```

**速率限制**:
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/api/generate')
@limiter.limit("10 per minute")
def generate():
    pass
```

## 4. 用户体验设计

### 4.1 进度反馈

**WebSocket实现**:
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('generate_content')
def handle_generate(data):
    """处理生成请求"""
    task_id = str(uuid.uuid4())
    
    # 发送初始状态
    emit('progress', {
        'task_id': task_id,
        'status': 'started',
        'progress': 0
    })
    
    # 生成内容
    emit('progress', {
        'task_id': task_id,
        'status': 'generating_content',
        'progress': 20
    })
    
    # 生成图片
    for i, prompt in enumerate(prompts):
        emit('progress', {
            'task_id': task_id,
            'status': 'generating_image',
            'progress': 20 + (i + 1) * 60 / len(prompts),
            'current_image': i + 1,
            'total_images': len(prompts)
        })
    
    # 完成
    emit('progress', {
        'task_id': task_id,
        'status': 'completed',
        'progress': 100,
        'result': result
    })
```

### 4.2 错误处理

**错误分类**:
```python
class AppError(Exception):
    """应用错误基类"""
    def __init__(self, message: str, code: str, details: Dict = None):
        self.message = message
        self.code = code
        self.details = details or {}

class UserError(AppError):
    """用户错误（输入错误等）"""
    pass

class SystemError(AppError):
    """系统错误（服务异常等）"""
    pass

class NetworkError(AppError):
    """网络错误（API调用失败等）"""
    pass
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "输入文本过短，至少需要10个字符",
    "details": {
      "field": "input_text",
      "current_length": 5,
      "min_length": 10
    },
    "suggestions": [
      "请输入更详细的内容描述",
      "可以参考示例：记得小时候..."
    ]
  }
}
```

## 5. 测试设计

### 5.1 单元测试

**测试结构**:
```
tests/
├── unit/
│   ├── test_config_manager.py
│   ├── test_cache_manager.py
│   ├── test_rate_limiter.py
│   ├── test_content_service.py
│   └── test_image_service.py
├── integration/
│   ├── test_content_generation_flow.py
│   └── test_image_generation_flow.py
└── e2e/
    └── test_web_app.py
```

**测试示例**:
```python
import pytest
from src.core.config_manager import ConfigManager

class TestConfigManager:
    """配置管理器测试"""
    
    def test_get_default_value(self):
        """测试获取默认值"""
        config = ConfigManager()
        assert config.get('api.openai.timeout', 30) == 30
    
    def test_environment_variable_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
        config = ConfigManager()
        assert config.get('api.openai.key') == 'test-key'
    
    @pytest.mark.asyncio
    async def test_config_validation(self):
        """测试配置验证"""
        config = ConfigManager()
        assert config.validate() is True
```

### 5.2 性能测试

**测试指标**:
- 响应时间: P50, P95, P99
- 吞吐量: QPS
- 并发能力: 最大并发数
- 资源使用: CPU, 内存

**性能基准**:
- 内容生成 API: P95 < 3秒, P99 < 5秒
- 图片生成 API: P95 < 120秒, P99 < 180秒
- WebSocket 消息延迟: < 100ms
- 并发支持: 100 QPS (稳定), 200 QPS (峰值)
- 内存使用: < 512MB (单进程)
- CPU 使用: < 80% (4核心)

**测试工具**: locust

```python
from locust import HttpUser, task, between

class ContentGenerationUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_content(self):
        self.client.post("/api/generate_content", json={
            "input_text": "测试内容" * 50,
            "count": 1
        })
```

### 5.3 属性测试（Property-Based Testing）

**适用场景**:
- 输入验证逻辑
- 缓存键生成
- 文本处理函数
- 配置解析

**测试策略**:
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=10, max_size=5000))
def test_content_generation_accepts_valid_input(input_text):
    """属性：所有符合长度要求的文本都应该被接受"""
    request = ContentGenerationRequest(input_text=input_text)
    assert request.input_text == input_text

@given(st.text(max_size=9))
def test_content_generation_rejects_short_input(input_text):
    """属性：所有过短的文本都应该被拒绝"""
    with pytest.raises(ValidationError):
        ContentGenerationRequest(input_text=input_text)
```

**测试工具**: hypothesis

## 6. 部署设计

### 6.1 容器化

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "web_app:app"]
```

### 6.2 监控告警

**监控指标**:
- 应用指标: 请求数、错误率、响应时间
- 业务指标: 生成成功率、API调用次数
- 系统指标: CPU、内存、磁盘

**告警规则**:
```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 0.05
    duration: 5m
    severity: critical
    message: "错误率超过5%"
  
  - name: SlowResponse
    condition: p95_latency > 10s
    duration: 5m
    severity: warning
    message: "P95响应时间超过10秒"
```

## 7. 技术选型

### 7.1 核心技术栈
- **Web框架**: Flask 3.0 + Flask-SocketIO 5.3+
- **异步**: asyncio + aiohttp
- **数据库**: PostgreSQL 14 (可选)
- **缓存**: Redis 7 (可选)
- **任务队列**: Celery + Redis (可选)
- **测试**: pytest + pytest-asyncio + hypothesis
- **类型检查**: mypy
- **代码质量**: pylint + black + flake8
- **输入验证**: Pydantic 2.0+

### 7.2 第三方服务
- **AI服务**: 阿里云DashScope (通义千问 + 通义万相)
- **监控**: Prometheus + Grafana (可选)
- **日志**: ELK Stack (可选)
- **部署**: Docker + Kubernetes (可选)

## 8. 迁移策略

### 8.1 渐进式重构

**阶段1**: 基础设施
- 引入ConfigManager，保持向后兼容
- 添加日志系统，逐步替换print
- 搭建测试框架

**阶段2**: 服务层
- 提取ContentService，封装现有逻辑
- 提取ImageService，封装现有逻辑
- 保持API接口不变

**阶段3**: 性能优化
- 引入缓存层
- 实现并行生成
- 添加速率限制

**阶段4**: 功能增强
- 添加新功能
- 优化用户体验
- 完善文档

### 8.2 兼容性保证

**版本策略**:
- 主版本: 不兼容变更
- 次版本: 新功能，向后兼容
- 修订版本: Bug修复

**废弃策略**:
1. 标记为废弃（Deprecated）
2. 提供迁移指南
3. 保留2个版本周期
4. 完全移除

## 9. 文档规范

### 9.1 代码文档

**模块文档**:
```python
"""
内容生成服务模块

本模块提供小红书内容生成的核心功能，包括：
- 文案生成
- 提示词生成
- 内容优化

使用示例:
    >>> service = ContentService(config)
    >>> result = await service.generate_content("输入文本")
    >>> print(result.content)

注意事项:
    - 需要配置有效的API Key
    - 输入文本长度限制为10-5000字符
"""
```

**函数文档**:
```python
async def generate_content(
    self, 
    input_text: str, 
    options: Optional[Dict] = None
) -> ContentResult:
    """
    生成小红书内容
    
    Args:
        input_text: 输入文本，长度10-5000字符
        options: 生成选项，可选参数：
            - style: 风格，默认"retro_chinese"
            - temperature: 温度，默认0.8
            - max_retries: 最大重试次数，默认3
    
    Returns:
        ContentResult: 生成结果，包含：
            - titles: 标题列表
            - content: 正文内容
            - tags: 标签列表
            - image_prompts: 图片提示词列表
    
    Raises:
        ValueError: 输入文本不符合要求
        APIError: API调用失败
        RateLimitError: 超过速率限制
    
    Examples:
        >>> result = await service.generate_content("老北京胡同")
        >>> print(result.titles[0])
        "胡同里的老北京记忆"
    """
    pass
```

### 9.2 API文档

使用 OpenAPI 3.0 规范，自动生成文档

## 10. 总结

本设计文档提供了RedBookContentGen项目改进的完整技术方案，涵盖架构、性能、安全、用户体验等多个方面。通过渐进式重构和模块化设计，可以在保持系统稳定的前提下，逐步提升代码质量和用户体验。
