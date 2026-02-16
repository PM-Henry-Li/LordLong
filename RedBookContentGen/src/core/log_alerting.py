#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志告警模块

提供日志告警规则配置和告警通知功能
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from datetime import datetime
from enum import Enum


class AlertSeverity(Enum):
    """告警严重级别"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        condition: Callable[[List[Dict[str, Any]]], bool],
        severity: AlertSeverity,
        message: str,
        duration: int = 60,
        cooldown: int = 300,
    ):
        """
        初始化告警规则

        Args:
            name: 规则名称
            condition: 条件函数，接收日志列表，返回是否触发告警
            severity: 告警严重级别
            message: 告警消息
            duration: 持续时间（秒），条件在此时间内持续满足才触发
            cooldown: 冷却时间（秒），触发后在此时间内不再重复告警
        """
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message = message
        self.duration = duration
        self.cooldown = cooldown
        self.last_triggered = 0
        self.condition_met_since = None

    def check(self, logs: List[Dict[str, Any]]) -> bool:
        """
        检查规则是否触发

        Args:
            logs: 日志列表

        Returns:
            是否触发告警
        """
        current_time = time.time()

        # 检查是否在冷却期
        if current_time - self.last_triggered < self.cooldown:
            return False

        # 检查条件
        condition_met = self.condition(logs)

        if condition_met:
            # 条件满足
            if self.condition_met_since is None:
                self.condition_met_since = current_time

            # 检查是否持续满足足够长时间
            if current_time - self.condition_met_since >= self.duration:
                self.last_triggered = current_time
                self.condition_met_since = None
                return True
        else:
            # 条件不满足，重置
            self.condition_met_since = None

        return False


class AlertNotifier:
    """告警通知器基类"""

    def send(self, alert: Dict[str, Any]) -> None:
        """
        发送告警

        Args:
            alert: 告警信息
        """
        raise NotImplementedError


class LogAlertNotifier(AlertNotifier):
    """日志告警通知器"""

    def __init__(self, logger_name: str = "alerting"):
        """
        初始化日志告警通知器

        Args:
            logger_name: 日志记录器名称
        """
        self.logger = logging.getLogger(logger_name)

    def send(self, alert: Dict[str, Any]) -> None:
        """发送告警到日志"""
        severity = alert.get("severity", "info")
        msg = f"🚨 告警触发: {alert.get('rule_name')} - {alert.get('message')}"

        # 创建额外字段，避免与 LogRecord 的保留字段冲突
        extra = {
            "alert_rule_name": alert.get("rule_name"),
            "alert_severity": alert.get("severity"),
            "alert_message": alert.get("message"),
            "alert_timestamp": alert.get("timestamp"),
            "alert_details": alert.get("details"),
        }

        if severity == "critical":
            self.logger.critical(msg, extra=extra)
        elif severity == "warning":
            self.logger.warning(msg, extra=extra)
        else:
            self.logger.info(msg, extra=extra)


class HTTPAlertNotifier(AlertNotifier):
    """HTTP 告警通知器"""

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """
        初始化 HTTP 告警通知器

        Args:
            url: 告警接收端点 URL
            headers: 自定义 HTTP 头
        """
        self.url = url
        self.headers = headers or {}
        self.logger = logging.getLogger("alerting.http")

    def send(self, alert: Dict[str, Any]) -> None:
        """发送告警到 HTTP 端点"""
        try:
            import requests

            response = requests.post(self.url, json=alert, headers=self.headers, timeout=10)
            response.raise_for_status()
            self.logger.debug(f"告警已发送到 {self.url}")
        except Exception as e:
            self.logger.error(f"发送告警失败: {e}")


class EmailAlertNotifier(AlertNotifier):
    """邮件告警通知器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        from_addr: str,
        to_addrs: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
    ):
        """
        初始化邮件告警通知器

        Args:
            smtp_host: SMTP 服务器地址
            smtp_port: SMTP 端口
            from_addr: 发件人地址
            to_addrs: 收件人地址列表
            username: SMTP 用户名
            password: SMTP 密码
            use_tls: 是否使用 TLS
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.logger = logging.getLogger("alerting.email")

    def send(self, alert: Dict[str, Any]) -> None:
        """发送告警邮件"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg["Subject"] = f"[{alert.get('severity', 'INFO').upper()}] {alert.get('rule_name')}"

            # 邮件正文
            body = """
告警规则: {alert.get('rule_name')}
严重级别: {alert.get('severity', 'info').upper()}
触发时间: {alert.get('timestamp')}
告警消息: {alert.get('message')}

详细信息:
{self._format_details(alert.get('details', {}))}
"""
            msg.attach(MIMEText(body, "plain", "utf - 8"))

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.debug(f"告警邮件已发送到 {', '.join(self.to_addrs)}")
        except Exception as e:
            self.logger.error(f"发送告警邮件失败: {e}")

    def _format_details(self, details: Dict[str, Any]) -> str:
        """格式化详细信息"""
        lines = []
        for key, value in details.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines) if lines else "  无"


class AlertingHandler(logging.Handler):
    """日志告警处理器

    将日志记录发送到告警管理器进行规则检查
    """

    def __init__(self, alert_manager: "LogAlertManager"):
        """
        初始化告警处理器

        Args:
            alert_manager: 告警管理器
        """
        super().__init__()
        self.alert_manager = alert_manager

    def emit(self, record: logging.LogRecord) -> None:
        """处理日志记录"""
        try:
            # 格式化日志记录
            log_dict = {
                "@timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # 添加额外字段
            if hasattr(record, "elapsed_time"):
                log_dict["elapsed_time"] = record.elapsed_time
            if hasattr(record, "memory_mb"):
                log_dict["memory_mb"] = record.memory_mb

            # 发送到告警管理器
            self.alert_manager.add_log(log_dict)
        except Exception:
            self.handleError(record)


class LogAlertManager:
    """日志告警管理器"""

    def __init__(self, window_size: int = 300):
        """
        初始化告警管理器

        Args:
            window_size: 时间窗口大小（秒），保留最近这段时间的日志用于规则检查
        """
        self.window_size = window_size
        self.logs = deque()
        self.rules: List[AlertRule] = []
        self.notifiers: List[AlertNotifier] = []
        self.lock = threading.Lock()
        self.running = False
        self.check_thread = None
        self.logger = logging.getLogger("alerting")

    def add_rule(self, rule: AlertRule) -> None:
        """
        添加告警规则

        Args:
            rule: 告警规则
        """
        with self.lock:
            self.rules.append(rule)
            self.logger.info(f"添加告警规则: {rule.name}")

    def add_notifier(self, notifier: AlertNotifier) -> None:
        """
        添加告警通知器

        Args:
            notifier: 告警通知器
        """
        with self.lock:
            self.notifiers.append(notifier)
            self.logger.info(f"添加告警通知器: {notifier.__class__.__name__}")

    def add_log(self, log: Dict[str, Any]) -> None:
        """
        添加日志记录

        Args:
            log: 日志记录
        """
        with self.lock:
            # 添加时间戳（使用当前时间）
            if "@timestamp" not in log:
                log["@timestamp"] = datetime.utcnow().isoformat()

            # 添加内部时间戳用于过期检查
            if "_added_at" not in log:
                log["_added_at"] = time.time()

            self.logs.append(log)

            # 清理过期日志
            cutoff_time = time.time() - self.window_size
            while self.logs and self.logs[0].get("_added_at", 0) < cutoff_time:
                self.logs.popleft()

    def _get_log_timestamp(self, log: Dict[str, Any]) -> float:
        """获取日志时间戳"""
        # 优先使用内部时间戳
        if "_added_at" in log:
            return log["_added_at"]

        # 否则解析 @timestamp
        timestamp_str = log.get("@timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return time.time()

    def check_rules(self) -> None:
        """检查所有告警规则"""
        with self.lock:
            logs_list = list(self.logs)
            rules = list(self.rules)
            notifiers = list(self.notifiers)

        for rule in rules:
            try:
                if rule.check(logs_list):
                    # 触发告警
                    alert = {
                        "rule_name": rule.name,
                        "severity": rule.severity.value,
                        "message": rule.message,
                        "timestamp": datetime.utcnow().isoformat(),
                        "details": self._get_alert_details(rule, logs_list),
                    }

                    # 发送告警
                    for notifier in notifiers:
                        try:
                            notifier.send(alert)
                        except Exception as e:
                            self.logger.error(f"发送告警失败: {e}")
            except Exception as e:
                self.logger.error(f"检查规则 {rule.name} 失败: {e}")

    def _get_alert_details(self, rule: AlertRule, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取告警详细信息"""
        return {"log_count": len(logs), "window_size": self.window_size, "duration": rule.duration}

    def start(self, check_interval: int = 10) -> None:
        """
        启动告警检查

        Args:
            check_interval: 检查间隔（秒）
        """
        if self.running:
            return

        self.running = True
        self.check_thread = threading.Thread(target=self._check_worker, args=(check_interval,), daemon=True)
        self.check_thread.start()
        self.logger.info("告警管理器已启动")

    def stop(self) -> None:
        """停止告警检查"""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=5)
        self.logger.info("告警管理器已停止")

    def _check_worker(self, check_interval: int) -> None:
        """告警检查工作线程"""
        while self.running:
            try:
                self.check_rules()
            except Exception as e:
                self.logger.error(f"告警检查失败: {e}")

            time.sleep(check_interval)


# 预定义的告警规则工厂函数


def create_error_rate_rule(
    threshold: float = 0.05, duration: int = 300, severity: AlertSeverity = AlertSeverity.CRITICAL
) -> AlertRule:
    """
    创建错误率告警规则

    Args:
        threshold: 错误率阈值（0 - 1）
        duration: 持续时间（秒）
        severity: 告警严重级别

    Returns:
        告警规则
    """

    def condition(logs: List[Dict[str, Any]]) -> bool:
        if not logs:
            return False

        error_count = sum(1 for log in logs if log.get("level") in ["ERROR", "CRITICAL"])
        error_rate = error_count / len(logs)
        return error_rate > threshold

    return AlertRule(
        name="HighErrorRate",
        condition=condition,
        severity=severity,
        message=f"错误率超过 {threshold * 100}%",
        duration=duration,
    )


def create_slow_response_rule(
    threshold: float = 10.0, duration: int = 300, severity: AlertSeverity = AlertSeverity.WARNING
) -> AlertRule:
    """
    创建慢响应告警规则

    Args:
        threshold: 响应时间阈值（秒）
        duration: 持续时间（秒）
        severity: 告警严重级别

    Returns:
        告警规则
    """

    def condition(logs: List[Dict[str, Any]]) -> bool:
        response_times = [log.get("elapsed_time", 0) for log in logs if "elapsed_time" in log]

        if not response_times:
            return False

        # 计算 P95
        response_times.sort()
        p95_index = int(len(response_times) * 0.95)
        p95_latency = response_times[p95_index] if p95_index < len(response_times) else response_times[-1]

        return p95_latency > threshold

    return AlertRule(
        name="SlowResponse",
        condition=condition,
        severity=severity,
        message=f"P95 响应时间超过 {threshold} 秒",
        duration=duration,
    )


def create_api_failure_rule(
    threshold: int = 10, duration: int = 60, severity: AlertSeverity = AlertSeverity.CRITICAL
) -> AlertRule:
    """
    创建 API 调用失败告警规则

    Args:
        threshold: 失败次数阈值
        duration: 持续时间（秒）
        severity: 告警严重级别

    Returns:
        告警规则
    """

    def condition(logs: List[Dict[str, Any]]) -> bool:
        failure_count = sum(1 for log in logs if log.get("level") == "ERROR" and "API" in log.get("message", ""))
        return failure_count >= threshold

    return AlertRule(
        name="APIFailure",
        condition=condition,
        severity=severity,
        message=f"API 调用失败次数超过 {threshold} 次",
        duration=duration,
    )


def create_memory_usage_rule(
    threshold_mb: float = 1000.0, duration: int = 300, severity: AlertSeverity = AlertSeverity.WARNING
) -> AlertRule:
    """
    创建内存使用告警规则

    Args:
        threshold_mb: 内存使用阈值（MB）
        duration: 持续时间（秒）
        severity: 告警严重级别

    Returns:
        告警规则
    """

    def condition(logs: List[Dict[str, Any]]) -> bool:
        memory_usages = [log.get("memory_mb", 0) for log in logs if "memory_mb" in log]

        if not memory_usages:
            return False

        avg_memory = sum(memory_usages) / len(memory_usages)
        return avg_memory > threshold_mb

    return AlertRule(
        name="HighMemoryUsage",
        condition=condition,
        severity=severity,
        message=f"平均内存使用超过 {threshold_mb} MB",
        duration=duration,
    )


def setup_from_config(config_manager: Any, alert_manager: LogAlertManager) -> None:
    """
    从配置管理器设置告警规则和通知器

    Args:
        config_manager: 配置管理器
        alert_manager: 告警管理器
    """
    alerting_config = config_manager.get("logging.alerting", {})

    if not alerting_config.get("enabled", False):
        return

    # 设置告警规则
    rules_config = alerting_config.get("rules", [])
    for rule_config in rules_config:
        rule_type = rule_config.get("type")

        if rule_type == "error_rate":
            rule = create_error_rate_rule(
                threshold=rule_config.get("threshold", 0.05),
                duration=rule_config.get("duration", 300),
                severity=AlertSeverity(rule_config.get("severity", "critical")),
            )
            alert_manager.add_rule(rule)

        elif rule_type == "slow_response":
            rule = create_slow_response_rule(
                threshold=rule_config.get("threshold", 10.0),
                duration=rule_config.get("duration", 300),
                severity=AlertSeverity(rule_config.get("severity", "warning")),
            )
            alert_manager.add_rule(rule)

        elif rule_type == "api_failure":
            rule = create_api_failure_rule(
                threshold=rule_config.get("threshold", 10),
                duration=rule_config.get("duration", 60),
                severity=AlertSeverity(rule_config.get("severity", "critical")),
            )
            alert_manager.add_rule(rule)

        elif rule_type == "memory_usage":
            rule = create_memory_usage_rule(
                threshold_mb=rule_config.get("threshold_mb", 1000.0),
                duration=rule_config.get("duration", 300),
                severity=AlertSeverity(rule_config.get("severity", "warning")),
            )
            alert_manager.add_rule(rule)

    # 设置告警通知器
    notifiers_config = alerting_config.get("notifiers", {})

    # 日志通知器
    if notifiers_config.get("log", {}).get("enabled", True):
        notifier = LogAlertNotifier()
        alert_manager.add_notifier(notifier)

    # HTTP 通知器
    http_config = notifiers_config.get("http", {})
    if http_config.get("enabled", False):
        notifier = HTTPAlertNotifier(url=http_config["url"], headers=http_config.get("headers", {}))
        alert_manager.add_notifier(notifier)

    # 邮件通知器
    email_config = notifiers_config.get("email", {})
    if email_config.get("enabled", False):
        notifier = EmailAlertNotifier(
            smtp_host=email_config["smtp_host"],
            smtp_port=email_config["smtp_port"],
            from_addr=email_config["from_addr"],
            to_addrs=email_config["to_addrs"],
            username=email_config.get("username"),
            password=email_config.get("password"),
            use_tls=email_config.get("use_tls", True),
        )
        alert_manager.add_notifier(notifier)

    # 启动告警管理器
    check_interval = alerting_config.get("check_interval", 10)
    alert_manager.start(check_interval)
