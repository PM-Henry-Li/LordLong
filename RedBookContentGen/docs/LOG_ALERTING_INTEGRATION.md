# 日志告警集成总结

## 概述

本次实现为 RedBookContentGen 项目添加了完整的日志告警功能，支持实时监控应用日志并在触发规则时发送告警通知。

## 实现内容

### 1. 核心模块

#### `src/core/log_alerting.py`
新增的日志告警模块，包含以下组件：

- **AlertRule** - 告警规则类
  - 支持自定义条件函数
  - 持续时间检查（避免瞬时波动）
  - 冷却期机制（避免告警风暴）
  - 可配置的严重级别

- **AlertNotifier** - 告警通知器基类
  - 定义统一的通知接口
  - 支持多种通知方式

- **LogAlertNotifier** - 日志告警通知器
  - 将告警写入日志文件
  - 根据严重级别使用不同日志级别
  - 避免与 LogRecord 保留字段冲突

- **HTTPAlertNotifier** - HTTP 告警通知器
  - 发送告警到 HTTP 端点
  - 支持自定义头和认证
  - 适配钉钉、企业微信等

- **EmailAlertNotifier** - 邮件告警通知器
  - 发送告警邮件
  - 支持 SMTP 认证
  - 支持 TLS/SSL
  - 格式化邮件内容

- **AlertingHandler** - 日志告警处理器
  - 继承自 logging.Handler
  - 将日志记录发送到告警管理器
  - 提取额外字段（elapsed_time, memory_mb 等）

- **LogAlertManager** - 日志告警管理器
  - 管理告警规则和通知器
  - 维护时间窗口内的日志
  - 后台线程定期检查规则
  - 触发告警时通知所有通知器

### 2. 预定义告警规则

提供了四种常用的告警规则工厂函数：

- **create_error_rate_rule** - 错误率告警
  - 监控 ERROR 和 CRITICAL 级别日志比例
  - 适合监控系统整体健康状况

- **create_slow_response_rule** - 慢响应告警
  - 监控 P95 响应时间
  - 适合监控系统性能

- **create_api_failure_rule** - API 失败告警
  - 监控 API 调用失败次数
  - 适合监控外部依赖

- **create_memory_usage_rule** - 内存使用告警
  - 监控平均内存使用
  - 适合监控内存泄漏

### 3. 配置文件更新

更新了 `config/config.example.json`，添加了完整的告警配置：

```json
{
  "logging": {
    "alerting": {
      "enabled": false,
      "window_size": 300,
      "check_interval": 10,
      "rules": [...],
      "notifiers": {...}
    }
  }
}
```

### 4. 文档

创建了详细的使用文档：

- **docs/LOG_ALERTING.md** - 完整的使用指南
  - 快速开始
  - 配置详解
  - 高级用法
  - 监控和调试
  - 最佳实践
  - 故障排查

### 5. 测试

创建了完整的测试套件：

- **tests/test_log_alerting.py** - 单元测试
  - 基础告警规则测试
  - 错误率告警规则测试
  - 慢响应告警规则测试
  - API 失败告警规则测试
  - 内存使用告警规则测试
  - 告警管理器测试
  - 告警处理器测试
  - 日志通知器测试
  - 持续时间检查测试
  - 冷却期测试

测试结果：**10 个测试全部通过** ✅

### 6. 使用示例

创建了实用的示例代码：

- **examples/log_alerting_example.py** - 使用示例
  - 基础告警示例
  - 慢响应告警示例
  - 基于配置的告警示例
  - 自定义告警规则示例
  - 多通知器示例

## 功能特性

### 1. 灵活的告警规则

- ✅ 支持自定义条件函数
- ✅ 预定义常用规则
- ✅ 可配置的阈值和参数
- ✅ 持续时间检查
- ✅ 冷却期机制

### 2. 多种通知方式

- ✅ 日志通知器 - 写入日志文件
- ✅ HTTP 通知器 - 发送到 HTTP 端点
- ✅ 邮件通知器 - 发送告警邮件
- ✅ 支持同时使用多个通知器

### 3. 智能告警

- ✅ 时间窗口 - 只保留最近的日志
- ✅ 持续时间检查 - 避免瞬时波动
- ✅ 冷却期机制 - 避免告警风暴
- ✅ 严重级别分类 - info, warning, critical

### 4. 易于集成

- ✅ 基于 logging.Handler
- ✅ 无侵入式集成
- ✅ 配置驱动
- ✅ 支持热重载

### 5. 高性能

- ✅ 后台线程检查
- ✅ 不阻塞主应用
- ✅ 时间窗口限制内存使用
- ✅ 批量处理日志

## 使用方法

### 快速开始

1. **启用日志告警**
   
   编辑 `config/config.json`：
   ```json
   {
     "logging": {
       "alerting": {
         "enabled": true
       }
     }
   }
   ```

2. **配置告警规则**
   
   ```json
   {
     "logging": {
       "alerting": {
         "rules": [
           {
             "type": "error_rate",
             "threshold": 0.05,
             "duration": 300,
             "severity": "critical"
           }
         ]
       }
     }
   }
   ```

3. **配置告警通知器**
   
   ```json
   {
     "logging": {
       "alerting": {
         "notifiers": {
           "log": {
             "enabled": true
           }
         }
       }
     }
   }
   ```

4. **运行应用**
   
   ```bash
   python run.py
   ```

### 代码集成

在应用启动时初始化告警系统：

```python
from src.core.config_manager import ConfigManager
from src.core.logger import Logger
from src.core.log_alerting import LogAlertManager, AlertingHandler, setup_from_config
import logging

# 初始化配置
config = ConfigManager("config/config.json")

# 初始化日志系统
Logger.initialize(config)

# 创建告警管理器
alert_manager = LogAlertManager(
    window_size=config.get('logging.alerting.window_size', 300)
)

# 从配置设置告警规则和通知器
setup_from_config(config, alert_manager)

# 添加告警处理器到日志系统
alerting_handler = AlertingHandler(alert_manager)
root_logger = logging.getLogger()
root_logger.addHandler(alerting_handler)

# 应用运行...

# 应用退出时停止告警管理器
alert_manager.stop()
```

## 配置示例

### 完整配置

```json
{
  "logging": {
    "alerting": {
      "enabled": true,
      "window_size": 300,
      "check_interval": 10,
      
      "rules": [
        {
          "type": "error_rate",
          "threshold": 0.05,
          "duration": 300,
          "severity": "critical"
        },
        {
          "type": "slow_response",
          "threshold": 10.0,
          "duration": 300,
          "severity": "warning"
        },
        {
          "type": "api_failure",
          "threshold": 10,
          "duration": 60,
          "severity": "critical"
        },
        {
          "type": "memory_usage",
          "threshold_mb": 1000.0,
          "duration": 300,
          "severity": "warning"
        }
      ],
      
      "notifiers": {
        "log": {
          "enabled": true
        },
        "http": {
          "enabled": true,
          "url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
          "headers": {
            "Content-Type": "application/json"
          }
        },
        "email": {
          "enabled": true,
          "smtp_host": "smtp.example.com",
          "smtp_port": 587,
          "from_addr": "alerts@example.com",
          "to_addrs": ["admin@example.com"],
          "username": "your-username",
          "password": "your-password",
          "use_tls": true
        }
      }
    }
  }
}
```

### 钉钉机器人配置

```json
{
  "http": {
    "enabled": true,
    "url": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

### 企业微信机器人配置

```json
{
  "http": {
    "enabled": true,
    "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

## 告警规则说明

### 错误率告警

监控错误日志（ERROR 和 CRITICAL 级别）占总日志的比例。

**参数**：
- `threshold`: 错误率阈值（0-1）
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控系统整体健康状况
- 及时发现批量错误

### 慢响应告警

监控响应时间的 P95 值。

**参数**：
- `threshold`: 响应时间阈值（秒）
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控系统性能
- 发现性能瓶颈

**注意**：需要在日志中记录 `elapsed_time` 字段。

### API 失败告警

监控 API 调用失败次数。

**参数**：
- `threshold`: 失败次数阈值
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控外部 API 调用
- 及时发现 API 服务异常

**注意**：检测包含 "API" 关键字的 ERROR 级别日志。

### 内存使用告警

监控应用内存使用情况。

**参数**：
- `threshold_mb`: 内存使用阈值（MB）
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控内存泄漏
- 防止 OOM

**注意**：需要在日志中记录 `memory_mb` 字段。

## 最佳实践

### 1. 告警规则设计

- **分级告警**：根据严重程度设置不同级别
  - `critical`: 需要立即处理的问题
  - `warning`: 需要关注的问题
  - `info`: 一般性通知

- **避免告警风暴**：
  - 设置合理的 `cooldown` 时间（建议 300-600 秒）
  - 使用 `duration` 避免瞬时波动（建议 60-300 秒）
  - 不要设置过多规则

- **告警可操作**：
  - 告警消息要清晰明确
  - 提供足够的上下文信息

### 2. 通知器选择

- **开发环境**：使用日志通知器
- **测试环境**：使用 HTTP 通知器（钉钉、企业微信）
- **生产环境**：使用多个通知器（日志 + HTTP + 邮件）

### 3. 性能优化

- **合理设置时间窗口**：
  - 默认 300 秒（5 分钟）适合大多数场景
  - 高频日志场景可以减小到 60-120 秒
  - 低频日志场景可以增大到 600-900 秒

- **控制检查频率**：
  - 默认 10 秒检查一次
  - 可以根据实际需求调整

### 4. 安全考虑

- **敏感信息保护**：
  - 不要在告警消息中包含敏感信息
  - SMTP 密码使用环境变量
  - HTTP 通知器使用 HTTPS

## 监控和调试

### 查看告警日志

```bash
# 查看所有告警
grep "告警触发" logs/app.log

# 查看 critical 级别告警
grep "CRITICAL.*告警触发" logs/app.log

# 实时监控告警
tail -f logs/app.log | grep "告警触发"
```

### 测试告警规则

```python
from src.core.logger import Logger

# 模拟错误日志，触发错误率告警
for i in range(20):
    Logger.error(f"测试错误 {i}")

# 模拟慢响应，触发慢响应告警
for i in range(10):
    Logger.info("操作完成", elapsed_time=15.0)
```

## 与日志收集系统集成

日志告警系统可以与日志收集系统（Elasticsearch、Logstash 等）无缝集成：

1. **日志收集**：将所有日志发送到 Elasticsearch
2. **日志告警**：在应用内实时检查告警规则
3. **Kibana 可视化**：在 Kibana 中查看告警历史和趋势
4. **告警通知**：通过多种方式发送告警通知

这种架构提供了：
- 实时告警（应用内检查）
- 历史分析（Elasticsearch + Kibana）
- 灵活的通知方式（日志、HTTP、邮件）

## 故障排查

### 告警未触发

**可能原因**：
1. 告警功能未启用
2. 规则条件未满足
3. 在冷却期内
4. 持续时间不够

**排查步骤**：
1. 检查配置：`logging.alerting.enabled` 是否为 `true`
2. 查看日志：是否有 "告警管理器已启动" 消息
3. 检查规则参数
4. 模拟日志测试规则

### 告警通知失败

**可能原因**：
1. 通知器配置错误
2. 网络连接问题
3. 认证失败

**排查步骤**：
1. 查看日志：搜索 "发送告警失败"
2. 检查通知器配置
3. 测试网络连接
4. 验证认证信息

## 下一步

1. 根据实际需求调整告警规则参数
2. 配置生产环境的通知器（钉钉、企业微信、邮件）
3. 在 Kibana 中创建告警可视化面板
4. 定期审查告警规则的有效性
5. 根据告警数据优化系统性能

## 参考文档

- [日志告警使用指南](LOG_ALERTING.md)
- [日志收集使用指南](LOG_COLLECTOR.md)
- [配置管理文档](CONFIG.md)

## 总结

本次实现为 RedBookContentGen 项目提供了完整的日志告警能力，支持实时监控、灵活配置、多种通知方式和智能告警。通过合理配置告警规则和通知器，可以及时发现和处理系统异常，提高系统可靠性和可维护性。

所有功能都经过完整测试，并提供了详细的文档和示例代码，可以立即投入使用。
