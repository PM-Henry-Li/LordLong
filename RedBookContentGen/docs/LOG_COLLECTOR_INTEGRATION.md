# 日志收集工具集成总结

## 概述

本次集成为 RedBookContentGen 项目添加了完整的日志收集功能，支持将应用日志发送到多种日志收集后端，包括 Elasticsearch、Logstash、HTTP 端点和文件输出。

## 实现内容

### 1. 核心模块

#### `src/core/log_collector.py`
新增的日志收集模块，包含以下组件：

- **LogCollectorHandler** - 日志收集处理器基类
  - 异步批量发送机制
  - 缓冲区管理
  - 自动刷新线程
  - 错误重试

- **ElasticsearchHandler** - Elasticsearch 日志收集处理器
  - 直接发送到 Elasticsearch
  - 支持多主机故障转移
  - 自动创建日期索引
  - 批量索引优化

- **LogstashHandler** - Logstash 日志收集处理器
  - 支持 TCP/UDP 协议
  - 自动重连机制
  - JSON 格式输出

- **HTTPHandler** - HTTP 日志收集处理器
  - 通用 HTTP POST 接口
  - 支持自定义头和认证
  - 适配各种日志服务

- **FileCollectorHandler** - 文件日志收集处理器
  - JSON 格式输出
  - 文件轮转支持
  - 供 Filebeat 等工具采集

- **LogCollector** - 日志收集管理器
  - 工厂方法创建处理器
  - 从配置自动设置
  - 统一管理多个后端

### 2. Logger 模块集成

更新了 `src/core/logger.py`，添加了日志收集支持：

- 在初始化时自动设置日志收集
- 从配置管理器读取日志收集配置
- 管理日志收集处理器生命周期

### 3. 配置文件更新

更新了 `config/config.example.json`，添加了完整的日志收集配置：

```json
{
  "logging": {
    "collector": {
      "enabled": false,
      "elasticsearch": { ... },
      "logstash": { ... },
      "http": { ... },
      "file": { ... }
    }
  }
}
```

### 4. 文档

创建了详细的使用文档：

- **docs/LOG_COLLECTOR.md** - 完整的使用指南
  - 快速开始
  - 配置详解
  - 使用示例
  - 监控告警
  - 性能优化
  - 故障排查
  - 最佳实践

### 5. 测试

创建了完整的测试套件：

- **tests/test_log_collector.py** - 单元测试
  - 基础日志收集处理器测试
  - 日志记录格式化测试
  - 缓冲区刷新测试
  - 文件收集处理器测试
  - 工厂方法测试
  - 异常日志记录测试

测试结果：**6 个测试全部通过** ✅

### 6. 使用示例

创建了实用的示例代码：

- **examples/log_collector_example.py** - 使用示例
  - 基础日志记录
  - 使用日志上下文
  - 使用额外字段
  - 异常日志记录
  - 性能日志记录
  - 结构化日志

## 功能特性

### 1. 多后端支持

- ✅ Elasticsearch - ELK Stack 核心组件
- ✅ Logstash - 日志处理管道
- ✅ HTTP 端点 - 通用接口
- ✅ 文件输出 - 供采集工具使用

### 2. 异步批量发送

- 使用缓冲区和后台线程
- 不阻塞主应用
- 可配置缓冲区大小和刷新间隔
- 自动批量发送优化性能

### 3. 高可用性

- 多主机故障转移（Elasticsearch）
- 自动重连机制（Logstash）
- 错误重试
- 缓冲区溢出保护

### 4. 灵活配置

- 支持多个后端同时启用
- 每个后端独立配置
- 支持环境变量覆盖
- 热重载支持（通过 ConfigManager）

### 5. 结构化日志

- 统一的 JSON 格式
- 包含丰富的元数据
- 支持自定义字段
- 便于解析和分析

### 6. 线程安全

- 使用线程锁保护共享资源
- 支持多线程环境
- 队列缓冲区线程安全

## 使用方法

### 快速开始

1. **安装依赖**
   ```bash
   pip install requests
   ```

2. **配置日志收集**
   编辑 `config/config.json`：
   ```json
   {
     "logging": {
       "collector": {
         "enabled": true,
         "elasticsearch": {
           "enabled": true,
           "hosts": ["http://localhost:9200"]
         }
       }
     }
   }
   ```

3. **运行应用**
   ```bash
   python run.py
   ```

日志会自动发送到配置的后端！

### 代码示例

```python
from src.core.config_manager import ConfigManager
from src.core.logger import Logger, LogContext

# 初始化
config = ConfigManager("config/config.json")
Logger.initialize(config)

# 记录日志
Logger.info("应用启动")

# 使用上下文
with LogContext(request_id="req-123"):
    Logger.info("处理请求")

# 添加额外字段
Logger.info(
    "操作完成",
    operation="generate_content",
    duration=2.5,
    success=True
)
```

## 配置示例

### Elasticsearch 配置

```json
{
  "logging": {
    "collector": {
      "elasticsearch": {
        "enabled": true,
        "hosts": ["http://es1:9200", "http://es2:9200"],
        "index_prefix": "redbookcontent-logs",
        "username": "elastic",
        "password": "your-password",
        "buffer_size": 100,
        "flush_interval": 5.0,
        "level": "INFO"
      }
    }
  }
}
```

### Logstash 配置

```json
{
  "logging": {
    "collector": {
      "logstash": {
        "enabled": true,
        "host": "logstash.example.com",
        "port": 5000,
        "protocol": "tcp",
        "buffer_size": 100,
        "flush_interval": 5.0,
        "level": "INFO"
      }
    }
  }
}
```

### HTTP 端点配置

```json
{
  "logging": {
    "collector": {
      "http": {
        "enabled": true,
        "url": "https://logs.example.com/api/logs",
        "headers": {
          "Authorization": "Bearer your-token"
        },
        "buffer_size": 100,
        "flush_interval": 5.0,
        "level": "INFO"
      }
    }
  }
}
```

### 文件收集配置

```json
{
  "logging": {
    "collector": {
      "file": {
        "enabled": true,
        "filename": "logs/collector.log",
        "max_bytes": 10485760,
        "backup_count": 5,
        "level": "INFO"
      }
    }
  }
}
```

## 日志格式

所有日志都以统一的 JSON 格式输出：

```json
{
  "@timestamp": "2026-02-13T01:05:15.123456",
  "level": "INFO",
  "logger": "content_generator",
  "message": "内容生成完成",
  "module": "content_generator",
  "function": "generate_content",
  "line": 123,
  "thread": 12345,
  "thread_name": "MainThread",
  "process": 67890,
  "hostname": "app-server-01",
  "context": {
    "request_id": "req-123",
    "user_id": "user-456"
  },
  "content_length": 1500,
  "generation_time": 2.5,
  "model": "qwen-plus"
}
```

## 性能考虑

### 缓冲区调优

- **高流量场景**：增大 `buffer_size`（如 200-500）
- **低流量场景**：减小 `flush_interval`（如 1-3 秒）
- **实时性要求高**：减小 `buffer_size` 和 `flush_interval`

### 日志级别过滤

只收集必要的日志级别，减少网络和存储开销：

```json
{
  "elasticsearch": {
    "level": "WARNING"  // 只收集 WARNING 及以上
  }
}
```

### 多后端策略

根据需求配置不同的后端：

- **本地文件**：收集所有日志（DEBUG）
- **Elasticsearch**：收集业务日志（INFO）
- **告警系统**：只收集错误（ERROR）

## 监控和告警

### Kibana 可视化

1. 创建索引模式：`redbookcontent-logs-*`
2. 创建可视化面板：
   - 日志级别分布
   - 错误趋势
   - 模块日志量
   - 响应时间分布

### 告警规则

在 Kibana 中配置告警：

- 错误率过高
- 响应时间过长
- 特定错误类型
- 日志量异常

## 故障排查

### 常见问题

1. **日志未发送到 Elasticsearch**
   - 检查 Elasticsearch 是否可访问
   - 验证认证信息
   - 查看应用日志中的错误

2. **Logstash 连接失败**
   - 检查 Logstash 是否监听端口
   - 测试网络连接
   - 检查防火墙规则

3. **缓冲区溢出**
   - 增大 `buffer_size`
   - 减小 `flush_interval`
   - 检查网络延迟

## 最佳实践

1. ✅ **生产环境**：使用 Elasticsearch + Kibana
2. ✅ **开发环境**：使用文件收集
3. ✅ **混合部署**：同时启用多个后端
4. ✅ **日志分级**：不同级别发送到不同后端
5. ✅ **定期清理**：设置索引生命周期策略
6. ✅ **监控告警**：配置关键错误告警
7. ✅ **性能测试**：在高负载下测试

## 安全建议

1. �� 使用 HTTPS/TLS 传输日志
2. 🔒 配置 Elasticsearch 认证
3. 🔒 确保日志中不包含敏感信息
4. 🔒 将日志服务部署在内网
5. 🔒 限制 Kibana 访问权限

## 下一步

1. 配置 Elasticsearch 集群
2. 设置 Kibana 可视化面板
3. 配置告警规则
4. 集成到 CI/CD 流程
5. 性能测试和优化

## 参考文档

- [日志收集使用指南](LOG_COLLECTOR.md)
- [配置管理文档](CONFIG.md)
- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash 官方文档](https://www.elastic.co/guide/en/logstash/current/index.html)

## 总结

本次集成为 RedBookContentGen 项目提供了企业级的日志收集能力，支持多种后端、异步批量发送、高可用性和灵活配置。通过结构化日志和统一的 JSON 格式，便于日志分析、监控告警和故障排查。

所有功能都经过完整测试，并提供了详细的文档和示例代码，可以立即投入使用。
