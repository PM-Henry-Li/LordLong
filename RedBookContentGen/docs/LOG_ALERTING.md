# 日志告警使用指南

## 概述

日志告警模块为 RedBookContentGen 项目提供实时的日志监控和告警功能。通过配置告警规则和通知器，可以在系统出现异常时及时收到通知。

## 功能特性

### 1. 告警规则

支持多种预定义的告警规则：

- **错误率告警** - 监控错误日志比例
- **慢响应告警** - 监控 P95 响应时间
- **API 失败告警** - 监控 API 调用失败次数
- **内存使用告警** - 监控内存使用情况

### 2. 告警通知器

支持多种告警通知方式：

- **日志通知器** - 将告警写入日志文件
- **HTTP 通知器** - 发送告警到 HTTP 端点（如钉钉、企业微信）
- **邮件通知器** - 发送告警邮件

### 3. 智能告警

- **持续时间检查** - 条件持续满足一定时间才触发，避免误报
- **冷却期机制** - 触发后在冷却期内不重复告警，避免告警风暴
- **时间窗口** - 只保留最近一段时间的日志用于规则检查，节省内存

## 快速开始

### 1. 启用日志告警

编辑 `config/config.json`，启用日志告警功能：

```json
{
  "logging": {
    "alerting": {
      "enabled": true,
      "window_size": 300,
      "check_interval": 10
    }
  }
}
```

### 2. 配置告警规则

在配置文件中添加告警规则：

```json
{
  "logging": {
    "alerting": {
      "enabled": true,
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
        }
      ]
    }
  }
}
```

### 3. 配置告警通知器

配置告警通知方式：

```json
{
  "logging": {
    "alerting": {
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
        }
      }
    }
  }
}
```

### 4. 运行应用

```bash
python run.py
```

日志告警系统会自动启动，监控应用日志并在触发规则时发送告警。

## 配置详解

### 告警规则配置

#### 错误率告警

监控错误日志（ERROR 和 CRITICAL 级别）占总日志的比例。

```json
{
  "type": "error_rate",
  "threshold": 0.05,
  "duration": 300,
  "severity": "critical"
}
```

**参数说明**：
- `threshold`: 错误率阈值（0-1），超过此比例触发告警
- `duration`: 持续时间（秒），条件持续满足此时间才触发
- `severity`: 告警严重级别（info, warning, critical）

**使用场景**：
- 监控系统整体健康状况
- 及时发现批量错误
- 适合设置为 critical 级别

#### 慢响应告警

监控响应时间的 P95 值（95% 的请求响应时间）。

```json
{
  "type": "slow_response",
  "threshold": 10.0,
  "duration": 300,
  "severity": "warning"
}
```

**参数说明**：
- `threshold`: 响应时间阈值（秒），P95 超过此值触发告警
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控系统性能
- 发现性能瓶颈
- 适合设置为 warning 级别

**注意事项**：
- 需要在日志中记录 `elapsed_time` 字段
- 示例：`Logger.info("操作完成", elapsed_time=2.5)`

#### API 失败告警

监控 API 调用失败次数。

```json
{
  "type": "api_failure",
  "threshold": 10,
  "duration": 60,
  "severity": "critical"
}
```

**参数说明**：
- `threshold`: 失败次数阈值，超过此次数触发告警
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控外部 API 调用
- 及时发现 API 服务异常
- 适合设置为 critical 级别

**注意事项**：
- 检测包含 "API" 关键字的 ERROR 级别日志
- 建议在 API 调用失败时记录包含 "API" 的错误日志

#### 内存使用告警

监控应用内存使用情况。

```json
{
  "type": "memory_usage",
  "threshold_mb": 1000.0,
  "duration": 300,
  "severity": "warning"
}
```

**参数说明**：
- `threshold_mb`: 内存使用阈值（MB），平均值超过此值触发告警
- `duration`: 持续时间（秒）
- `severity`: 告警严重级别

**使用场景**：
- 监控内存泄漏
- 防止 OOM
- 适合设置为 warning 级别

**注意事项**：
- 需要在日志中记录 `memory_mb` 字段
- 示例：`Logger.info("内存使用", memory_mb=512.5)`

### 告警通知器配置

#### 日志通知器

将告警写入日志文件，最简单的通知方式。

```json
{
  "log": {
    "enabled": true
  }
}
```

**优点**：
- 无需额外配置
- 可通过日志收集系统查看
- 适合开发和测试环境

**缺点**：
- 不够实时
- 需要主动查看日志

#### HTTP 通知器

发送告警到 HTTP 端点，支持钉钉、企业微信等。

```json
{
  "http": {
    "enabled": true,
    "url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

**钉钉机器人示例**：

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

告警消息格式：
```json
{
  "rule_name": "HighErrorRate",
  "severity": "critical",
  "message": "错误率超过 5%",
  "timestamp": "2026-02-13T10:30:00.000000",
  "details": {
    "log_count": 150,
    "window_size": 300,
    "duration": 300
  }
}
```

**企业微信机器人示例**：

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

#### 邮件通知器

发送告警邮件，适合重要告警。

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "from_addr": "alerts@example.com",
    "to_addrs": ["admin@example.com", "ops@example.com"],
    "username": "your-username",
    "password": "your-password",
    "use_tls": true
  }
}
```

**常用 SMTP 配置**：

**Gmail**：
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true
}
```

**QQ 邮箱**：
```json
{
  "smtp_host": "smtp.qq.com",
  "smtp_port": 587,
  "use_tls": true
}
```

**163 邮箱**：
```json
{
  "smtp_host": "smtp.163.com",
  "smtp_port": 465,
  "use_tls": false
}
```

## 高级用法

### 自定义告警规则

可以在代码中创建自定义告警规则：

```python
from src.core.log_alerting import AlertRule, AlertSeverity, LogAlertManager

# 创建告警管理器
alert_manager = LogAlertManager(window_size=300)

# 定义自定义条件函数
def custom_condition(logs):
    # 检查最近 5 分钟内是否有超过 3 次登录失败
    login_failures = sum(
        1 for log in logs
        if 'login' in log.get('message', '').lower() and log.get('level') == 'ERROR'
    )
    return login_failures > 3

# 创建自定义规则
rule = AlertRule(
    name="LoginFailure",
    condition=custom_condition,
    severity=AlertSeverity.WARNING,
    message="登录失败次数过多",
    duration=60,
    cooldown=300
)

# 添加规则
alert_manager.add_rule(rule)
```

### 自定义告警通知器

可以实现自定义的告警通知器：

```python
from src.core.log_alerting import AlertNotifier

class SlackNotifier(AlertNotifier):
    """Slack 告警通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, alert: dict) -> None:
        """发送告警到 Slack"""
        import requests
        
        payload = {
            "text": f"🚨 {alert['rule_name']}: {alert['message']}",
            "attachments": [{
                "color": "danger" if alert['severity'] == "critical" else "warning",
                "fields": [
                    {"title": "严重级别", "value": alert['severity'], "short": True},
                    {"title": "触发时间", "value": alert['timestamp'], "short": True}
                ]
            }]
        }
        
        requests.post(self.webhook_url, json=payload)

# 使用自定义通知器
notifier = SlackNotifier("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
alert_manager.add_notifier(notifier)
```

### 集成到应用

在应用启动时初始化告警系统：

```python
from src.core.config_manager import ConfigManager
from src.core.logger import Logger
from src.core.log_alerting import LogAlertManager, AlertingHandler, setup_from_config

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

## 监控和调试

### 查看告警日志

告警会记录到日志文件中，可以通过以下方式查看：

```bash
# 查看所有告警
grep "告警触发" logs/app.log

# 查看 critical 级别告警
grep "CRITICAL.*告警触发" logs/app.log

# 实时监控告警
tail -f logs/app.log | grep "告警触发"
```

### 测试告警规则

可以通过模拟日志来测试告警规则：

```python
from src.core.logger import Logger

# 模拟错误日志，触发错误率告警
for i in range(20):
    Logger.error(f"测试错误 {i}")

# 模拟慢响应，触发慢响应告警
for i in range(10):
    Logger.info("操作完成", elapsed_time=15.0)

# 模拟 API 失败，触发 API 失败告警
for i in range(15):
    Logger.error(f"API 调用失败: {i}")
```

### 调整告警参数

根据实际情况调整告警参数：

**减少误报**：
- 增大 `duration`（持续时间）
- 增大 `threshold`（阈值）
- 增大 `cooldown`（冷却期）

**提高灵敏度**：
- 减小 `duration`
- 减小 `threshold`
- 减小 `cooldown`

## 最佳实践

### 1. 告警规则设计

- **分级告警**：根据严重程度设置不同级别
  - `critical`: 需要立即处理的问题（如错误率过高、API 失败）
  - `warning`: 需要关注的问题（如慢响应、内存使用高）
  - `info`: 一般性通知

- **避免告警风暴**：
  - 设置合理的 `cooldown` 时间
  - 使用 `duration` 避免瞬时波动触发告警
  - 不要设置过多规则

- **告警可操作**：
  - 告警消息要清晰明确
  - 提供足够的上下文信息
  - 包含处理建议

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
  - 可以根据实际需求调整 `check_interval`

- **日志级别过滤**：
  - 只将需要监控的日志发送到告警管理器
  - 可以通过日志级别过滤

### 4. 安全考虑

- **敏感信息保护**：
  - 不要在告警消息中包含敏感信息
  - SMTP 密码使用环境变量
  - HTTP 通知器使用 HTTPS

- **访问控制**：
  - 限制告警接收端点的访问权限
  - 使用认证令牌

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
3. 检查规则参数：`threshold`、`duration` 是否合理
4. 模拟日志测试规则

### 告警通知失败

**可能原因**：
1. 通知器配置错误
2. 网络连接问题
3. 认证失败

**排查步骤**：
1. 查看日志：搜索 "发送告警失败"
2. 检查通知器配置：URL、认证信息等
3. 测试网络连接：`curl` 测试 HTTP 端点
4. 验证 SMTP 配置：使用邮件客户端测试

### 告警过多

**可能原因**：
1. 阈值设置过低
2. 冷却期过短
3. 持续时间过短

**解决方案**：
1. 调整 `threshold` 参数
2. 增大 `cooldown` 时间
3. 增大 `duration` 时间
4. 禁用不必要的规则

## 示例配置

### 完整配置示例

```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/app.log",
    
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

## 参考资料

- [日志系统文档](LOG_COLLECTOR.md)
- [配置管理文档](CONFIG.md)
- [钉钉机器人文档](https://open.dingtalk.com/document/robots/custom-robot-access)
- [企业微信机器人文档](https://developer.work.weixin.qq.com/document/path/91770)

## 总结

日志告警模块为 RedBookContentGen 项目提供了完整的实时监控和告警能力。通过合理配置告警规则和通知器，可以及时发现和处理系统异常，提高系统可靠性和可维护性。
