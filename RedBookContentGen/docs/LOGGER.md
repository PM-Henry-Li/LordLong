# Logger 模块文档

## 概述

Logger 模块提供了统一的结构化日志记录功能，支持 JSON 和文本两种格式、文件轮转、日志上下文管理等特性。

## 主要特性

### 1. 结构化日志记录
- 支持多种日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL
- 自动记录时间戳、模块名、函数名、行号等元信息
- 支持添加自定义字段

### 2. 多种输出格式
- **文本格式**：易读的文本格式，带 emoji 图标
- **JSON 格式**：结构化 JSON 格式，便于日志收集和分析

### 3. 文件轮转
- 基于文件大小的自动轮转
- 可配置备份文件数量
- 自动压缩旧日志文件

### 4. 日志上下文管理
- 使用上下文管理器自动添加上下文信息
- 支持嵌套上下文
- 线程安全

### 5. 与 ConfigManager 集成
- 从配置文件读取日志设置
- 支持环境变量覆盖
- 热重载配置

## 快速开始

### 基本使用

```python
from src.core.logger import Logger, info, warning, error
from src.core.config_manager import ConfigManager

# 初始化日志系统
config = ConfigManager()
Logger.initialize(config)

# 记录日志
info("应用启动成功")
warning("配置文件使用默认值")
error("连接数据库失败")
```

### 使用上下文管理器

```python
from src.core.logger import LogContext, info

# 自动添加上下文信息
with LogContext(request_id="req-123", user_id="user-456"):
    info("开始处理请求")
    info("验证用户权限")
    info("请求处理完成")
    # 所有日志都会自动包含 request_id 和 user_id
```

### 添加额外字段

```python
from src.core.logger import Logger

Logger.info(
    "用户登录成功",
    logger_name="auth",
    user_id="user123",
    ip_address="192.168.1.100",
    login_method="password"
)
```

### 记录异常

```python
from src.core.logger import Logger

try:
    result = 10 / 0
except ZeroDivisionError:
    Logger.exception("计算过程中发生错误", logger_name="calculator")
```

## 配置说明

在 `config/config.json` 中配置日志系统：

```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 5
  }
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `level` | string | `"INFO"` | 日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL |
| `format` | string | `"text"` | 日志格式：text（文本）、json（JSON） |
| `file` | string | `"logs/app.log"` | 日志文件路径 |
| `max_bytes` | int | `10485760` | 单个日志文件最大大小（字节），默认 10MB |
| `backup_count` | int | `5` | 保留的备份文件数量 |

### 环境变量覆盖

可以使用环境变量覆盖配置：

```bash
export LOG_LEVEL="DEBUG"
export LOG_FORMAT="json"
export LOG_FILE="logs/custom.log"
```

## API 参考

### Logger 类

#### 类方法

##### `initialize(config=None)`
初始化日志系统。

**参数**：
- `config` (ConfigManager, optional): 配置管理器实例

**示例**：
```python
from src.core.logger import Logger
from src.core.config_manager import ConfigManager

config = ConfigManager()
Logger.initialize(config)
```

##### `get_logger(name)`
获取日志记录器实例。

**参数**：
- `name` (str): 日志记录器名称

**返回**：
- `logging.Logger`: 日志记录器实例

**示例**：
```python
logger = Logger.get_logger("my_module")
logger.info("使用标准 logging 接口")
```

##### `debug(message, logger_name='app', **kwargs)`
记录调试日志。

**参数**：
- `message` (str): 日志消息
- `logger_name` (str): 日志记录器名称
- `**kwargs`: 额外字段

**示例**：
```python
Logger.debug("调试信息", logger_name="test", var1="value1")
```

##### `info(message, logger_name='app', **kwargs)`
记录信息日志。

##### `warning(message, logger_name='app', **kwargs)`
记录警告日志。

##### `error(message, logger_name='app', **kwargs)`
记录错误日志。

##### `critical(message, logger_name='app', **kwargs)`
记录严重错误日志。

##### `exception(message, logger_name='app', **kwargs)`
记录异常日志（包含堆栈跟踪）。

### LogContext 类

#### 上下文管理器

##### `__init__(**context)`
创建日志上下文。

**参数**：
- `**context`: 上下文键值对

**示例**：
```python
with LogContext(request_id="req-123", user_id="user-456"):
    info("处理请求")
```

#### 静态方法

##### `set(**context)`
设置全局日志上下文。

**参数**：
- `**context`: 上下文键值对

**示例**：
```python
LogContext.set(app_version="1.0.0", environment="production")
```

##### `clear()`
清除全局日志上下文。

**示例**：
```python
LogContext.clear()
```

##### `get()`
获取当前日志上下文。

**返回**：
- `dict`: 上下文字典

**示例**：
```python
context = LogContext.get()
print(context)
```

### 便捷函数

为了简化使用，模块提供了以下便捷函数：

```python
from src.core.logger import debug, info, warning, error, critical, exception, get_logger

debug("调试消息")
info("信息消息")
warning("警告消息")
error("错误消息")
critical("严重错误消息")
exception("异常消息")

logger = get_logger("my_module")
```

## 日志格式

### 文本格式

```
✅ [2026-02-12 23:16:42] [INFO] app: 应用启动成功
⚠️ [2026-02-12 23:16:42] [WARNING] app: 配置文件使用默认值 | config_path=config/config.json
❌ [2026-02-12 23:16:42] [ERROR] api: API 调用失败 | endpoint=/api/users, status_code=500
```

**Emoji 映射**：
- 🔍 DEBUG
- ✅ INFO
- ⚠️ WARNING
- ❌ ERROR
- 🔥 CRITICAL

### JSON 格式

```json
{
  "timestamp": "2026-02-12T23:16:42.123456",
  "level": "INFO",
  "logger": "app",
  "message": "应用启动成功",
  "module": "main",
  "function": "start_app",
  "line": 42,
  "context": {
    "request_id": "req-123",
    "user_id": "user-456"
  },
  "user_id": "user123",
  "action": "login"
}
```

## 最佳实践

### 1. 使用合适的日志级别

```python
# DEBUG - 详细的调试信息
Logger.debug("变量值", logger_name="debug", var1=value1, var2=value2)

# INFO - 一般信息
Logger.info("操作成功", logger_name="app")

# WARNING - 警告信息
Logger.warning("配置项缺失，使用默认值", logger_name="config")

# ERROR - 错误信息
Logger.error("操作失败", logger_name="app", error=str(e))

# CRITICAL - 严重错误
Logger.critical("系统崩溃", logger_name="system")
```

### 2. 使用上下文管理器

```python
# 为一组操作添加统一的上下文
with LogContext(task_id="task-001", user_id="user-789"):
    info("开始任务")
    # ... 执行任务
    info("任务完成")
```

### 3. 记录关键信息

```python
# 记录 API 调用
Logger.info(
    "API 调用",
    logger_name="api",
    method="POST",
    endpoint="/api/generate",
    status_code=200,
    duration=1.23
)

# 记录业务操作
Logger.info(
    "生成内容",
    logger_name="content",
    input_length=150,
    output_length=500,
    model="qwen-plus"
)
```

### 4. 异常处理

```python
try:
    # 可能出错的代码
    result = risky_operation()
except Exception as e:
    # 记录异常（包含堆栈跟踪）
    Logger.exception("操作失败", logger_name="app", operation="risky_operation")
    # 或者只记录错误信息
    Logger.error("操作失败", logger_name="app", error=str(e))
```

### 5. 生产环境配置

```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/app.log",
    "max_bytes": 52428800,
    "backup_count": 10
  }
}
```

### 6. 开发环境配置

```json
{
  "logging": {
    "level": "DEBUG",
    "format": "text",
    "file": "logs/dev.log",
    "max_bytes": 10485760,
    "backup_count": 3
  }
}
```

## 与现有代码集成

### 替换 print 语句

**之前**：
```python
print("✅ 开始生成内容")
print(f"⚠️ 警告: {warning_message}")
print(f"❌ 错误: {error_message}")
```

**之后**：
```python
from src.core.logger import info, warning, error

info("开始生成内容")
warning(f"警告: {warning_message}")
error(f"错误: {error_message}")
```

### 在类中使用

```python
from src.core.logger import Logger, LogContext

class ContentGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = Logger.get_logger(__name__)
    
    def generate(self, input_text):
        with LogContext(operation="generate", input_length=len(input_text)):
            self.logger.info("开始生成内容")
            
            try:
                result = self._do_generate(input_text)
                self.logger.info("生成成功", output_length=len(result))
                return result
            except Exception as e:
                self.logger.exception("生成失败")
                raise
```

## 故障排查

### 日志文件未创建

**问题**：日志文件不存在

**解决方案**：
1. 检查日志目录是否有写权限
2. 确保日志目录存在（Logger 会自动创建）
3. 检查配置文件中的路径是否正确

### 日志级别不生效

**问题**：DEBUG 日志没有输出

**解决方案**：
1. 检查配置文件中的 `logging.level` 设置
2. 确认环境变量 `LOG_LEVEL` 没有覆盖配置
3. 重新初始化 Logger：`Logger._initialized = False; Logger.initialize(config)`

### 日志轮转不工作

**问题**：日志文件超过限制但没有轮转

**解决方案**：
1. 检查 `max_bytes` 配置是否正确
2. 确认有足够的磁盘空间
3. 检查日志目录的写权限

## 性能考虑

### 1. 日志级别

在生产环境使用 INFO 或 WARNING 级别，避免过多的 DEBUG 日志影响性能。

### 2. 额外字段

避免在高频调用的代码中添加过多额外字段。

### 3. 异步日志

对于高并发场景，考虑使用异步日志处理器（未来版本支持）。

## 示例代码

完整的使用示例请参考：
- `examples/logger_usage_example.py` - 基本使用示例
- `tests/unit/test_logger.py` - 单元测试示例

## 相关文档

- [配置管理文档](CONFIG.md)
- [项目改进设计文档](../.kiro/specs/project-improvement/design.md)
- [项目改进需求文档](../.kiro/specs/project-improvement/requirements.md)
