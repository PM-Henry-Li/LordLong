# 日志收集系统使用指南

## 概述

RedBookContentGen 项目集成了强大的日志收集系统，支持将应用日志发送到多种日志收集后端，包括：

- **Elasticsearch** - ELK Stack 的核心组件，用于日志存储和搜索
- **Logstash** - 日志处理管道，支持 TCP/UDP 协议
- **HTTP 端点** - 通用的 HTTP POST 接口，适配各种日志服务
- **文件收集** - 输出 JSON 格式日志文件，供 Filebeat 等工具采集

## 架构设计

```
应用日志 → Logger → LogCollectorHandler → 缓冲区 → 批量发送 → 日志后端
                                              ↓
                                         定期刷新
```

### 核心特性

1. **异步批量发送** - 使用缓冲区和后台线程，不阻塞主应用
2. **自动重试** - 发送失败时自动重试，支持多主机故障转移
3. **灵活配置** - 支持多种后端同时启用，独立配置
4. **结构化日志** - 统一的 JSON 格式，便于解析和分析
5. **线程安全** - 支持多线程环境

## 快速开始

### 1. 安装依赖

```bash
# 基础依赖（HTTP 和 Elasticsearch 需要）
pip install requests

# 可选：YAML 配置文件支持
pip install pyyaml
```

### 2. 配置日志收集

编辑 `config/config.json`，启用所需的日志收集后端：

```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/app.log",
    "collector": {
      "enabled": true,
      "elasticsearch": {
        "enabled": true,
        "hosts": ["http://localhost:9200"],
        "index_prefix": "redbookcontent-logs"
      }
    }
  }
}
```

### 3. 运行应用

日志收集会在应用启动时自动初始化：

```bash
python run.py
```

## 配置详解

### Elasticsearch 配置

适用于 ELK Stack 部署，直接将日志发送到 Elasticsearch。

```json
{
  "logging": {
    "collector": {
      "elasticsearch": {
        "enabled": true,
        "hosts": [
          "http://es-node1:9200",
          "http://es-node2:9200"
        ],
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

**配置说明**：

- `enabled` - 是否启用 Elasticsearch 日志收集
- `hosts` - Elasticsearch 主机列表，支持多主机故障转移
- `index_prefix` - 索引前缀，实际索引名为 `{prefix}-YYYY.MM.DD`
- `username/password` - 认证信息（可选）
- `buffer_size` - 缓冲区大小，达到此大小时自动刷新
- `flush_interval` - 刷新间隔（秒），定期刷新缓冲区
- `level` - 日志级别过滤

**索引模板示例**：

```json
PUT _index_template/redbookcontent-logs
{
  "index_patterns": ["redbookcontent-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "level": { "type": "keyword" },
        "logger": { "type": "keyword" },
        "message": { "type": "text" },
        "module": { "type": "keyword" },
        "function": { "type": "keyword" },
        "hostname": { "type": "keyword" }
      }
    }
  }
}
```

### Logstash 配置

通过 TCP 或 UDP 将日志发送到 Logstash。

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

**配置说明**：

- `host` - Logstash 主机地址
- `port` - Logstash 端口
- `protocol` - 协议类型，`tcp` 或 `udp`
- 其他参数同 Elasticsearch

**Logstash 配置示例**：

```ruby
input {
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  # 添加自定义字段
  mutate {
    add_field => { "application" => "redbookcontent" }
  }
}

output {
  elasticsearch {
    hosts => ["http://localhost:9200"]
    index => "redbookcontent-logs-%{+YYYY.MM.dd}"
  }
}
```

### HTTP 端点配置

通过 HTTP POST 将日志发送到任意 HTTP 端点。

```json
{
  "logging": {
    "collector": {
      "http": {
        "enabled": true,
        "url": "https://logs.example.com/api/logs",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer your-token"
        },
        "username": null,
        "password": null,
        "buffer_size": 100,
        "flush_interval": 5.0,
        "level": "INFO"
      }
    }
  }
}
```

**配置说明**：

- `url` - HTTP 端点 URL
- `headers` - 自定义 HTTP 头
- `username/password` - HTTP Basic 认证（可选）

**请求格式**：

```json
POST /api/logs
Content-Type: application/json

{
  "logs": [
    {
      "@timestamp": "2026-02-12T10:30:00.000Z",
      "level": "INFO",
      "logger": "content_generator",
      "message": "开始生成内容",
      "module": "content_generator",
      "function": "generate_content",
      "line": 123,
      "hostname": "app-server-01"
    }
  ]
}
```

### 文件收集配置

输出 JSON 格式的日志文件，供 Filebeat 等工具采集。

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

**配置说明**：

- `filename` - 日志文件路径
- `max_bytes` - 单个文件最大字节数（默认 10MB）
- `backup_count` - 保留的备份文件数量

**Filebeat 配置示例**：

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /path/to/logs/collector.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["http://localhost:9200"]
  index: "redbookcontent-logs-%{+yyyy.MM.dd}"
```

## 环境变量配置

支持通过环境变量覆盖配置：

```bash
# 启用日志收集
export LOG_COLLECTOR_ENABLED=true

# Elasticsearch 配置
export LOG_COLLECTOR_ES_ENABLED=true
export LOG_COLLECTOR_ES_HOSTS="http://es1:9200,http://es2:9200"
export LOG_COLLECTOR_ES_USERNAME=elastic
export LOG_COLLECTOR_ES_PASSWORD=your-password

# Logstash 配置
export LOG_COLLECTOR_LS_ENABLED=true
export LOG_COLLECTOR_LS_HOST=logstash.example.com
export LOG_COLLECTOR_LS_PORT=5000
```

## 使用示例

### 基础使用

日志收集会自动集成到现有的日志系统中，无需修改代码：

```python
from src.core.logger import Logger

# 初始化日志系统（会自动设置日志收集）
Logger.initialize(config_manager)

# 正常使用日志
logger = Logger.get_logger(__name__)
logger.info("这条日志会自动发送到配置的收集后端")
```

### 添加上下文信息

使用日志上下文为日志添加额外信息：

```python
from src.core.logger import Logger, LogContext

with LogContext(request_id="req-123", user_id="user-456"):
    Logger.info("处理用户请求")
    # 日志会自动包含 request_id 和 user_id
```

### 添加自定义字段

```python
Logger.info(
    "生成内容完成",
    logger_name="content_generator",
    content_length=1500,
    generation_time=2.5,
    model="qwen-plus"
)
```

## 监控和告警

### Kibana 可视化

1. 创建索引模式：`redbookcontent-logs-*`
2. 创建可视化面板：
   - 日志级别分布（饼图）
   - 错误趋势（时间序列）
   - 模块日志量（柱状图）
   - 响应时间分布（直方图）

### 告警规则示例

在 Kibana 中创建告警规则：

```json
{
  "name": "高错误率告警",
  "conditions": {
    "query": {
      "bool": {
        "must": [
          { "term": { "level": "ERROR" } },
          { "range": { "@timestamp": { "gte": "now-5m" } } }
        ]
      }
    },
    "threshold": 10
  },
  "actions": {
    "email": {
      "to": ["admin@example.com"],
      "subject": "RedBookContentGen 错误率过高"
    }
  }
}
```

## 性能优化

### 缓冲区调优

根据日志量调整缓冲区大小和刷新间隔：

```json
{
  "buffer_size": 200,      // 高流量：增大缓冲区
  "flush_interval": 10.0   // 低流量：增加刷新间隔
}
```

### 日志级别过滤

只收集重要日志，减少网络和存储开销：

```json
{
  "elasticsearch": {
    "level": "WARNING"  // 只收集 WARNING 及以上级别
  }
}
```

### 多后端策略

- **本地文件** - 收集所有日志（DEBUG 级别）
- **Elasticsearch** - 收集业务日志（INFO 级别）
- **告警系统** - 只收集错误（ERROR 级别）

```json
{
  "collector": {
    "file": {
      "enabled": true,
      "level": "DEBUG"
    },
    "elasticsearch": {
      "enabled": true,
      "level": "INFO"
    },
    "http": {
      "enabled": true,
      "url": "https://alert.example.com/api/logs",
      "level": "ERROR"
    }
  }
}
```

## 故障排查

### 日志未发送到 Elasticsearch

1. 检查 Elasticsearch 是否可访问：
   ```bash
   curl http://localhost:9200/_cluster/health
   ```

2. 检查认证信息是否正确

3. 查看应用日志中的错误信息：
   ```bash
   grep "Elasticsearch" logs/app.log
   ```

### Logstash 连接失败

1. 检查 Logstash 是否监听指定端口：
   ```bash
   netstat -an | grep 5000
   ```

2. 测试连接：
   ```bash
   telnet logstash.example.com 5000
   ```

3. 检查防火墙规则

### 缓冲区溢出

如果看到 "缓冲区满" 的警告：

1. 增大 `buffer_size`
2. 减小 `flush_interval`
3. 检查网络延迟
4. 考虑使用多个收集后端分散负载

## 最佳实践

1. **生产环境** - 使用 Elasticsearch + Kibana，便于查询和分析
2. **开发环境** - 使用文件收集，简单快速
3. **混合部署** - 同时启用多个后端，提高可靠性
4. **日志分级** - 不同级别的日志发送到不同后端
5. **定期清理** - 设置 Elasticsearch 索引生命周期策略
6. **监控告警** - 配置关键错误的实时告警
7. **性能测试** - 在高负载下测试日志收集性能

## 安全建议

1. **加密传输** - 使用 HTTPS/TLS 传输日志
2. **认证授权** - 配置 Elasticsearch 用户名密码
3. **敏感信息** - 确保日志中不包含 API Key 等敏感信息
4. **网络隔离** - 将日志收集服务部署在内网
5. **访问控制** - 限制 Kibana 访问权限

## 参考资料

- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash 官方文档](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Filebeat 官方文档](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)
- [Python logging 模块文档](https://docs.python.org/3/library/logging.html)
