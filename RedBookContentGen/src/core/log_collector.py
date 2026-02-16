#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志收集模块

提供日志收集和转发功能，支持多种日志收集后端：
- Elasticsearch (ELK Stack)
- Logstash
- Fluentd
- HTTP 端点
- 文件输出（用于 Filebeat 等采集）
"""

import json
import logging
import logging.handlers
import queue
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  未安装 requests 库，HTTP 日志收集功能将不可用")
    print("   请运行: pip install requests")


class LogCollectorHandler(logging.Handler):
    """日志收集处理器基类

    提供日志收集的基础功能，子类需要实现具体的发送逻辑
    """

    def __init__(self, level=logging.NOTSET, buffer_size: int = 100, flush_interval: float = 5.0):
        """初始化日志收集处理器

        Args:
            level: 日志级别
            buffer_size: 缓冲区大小，达到此大小时自动刷新
            flush_interval: 刷新间隔（秒），定期刷新缓冲区
        """
        super().__init__(level)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer: queue.Queue = queue.Queue(maxsize=buffer_size * 2)
        self.flush_thread: Optional[threading.Thread] = None
        self.running = False
        self.last_flush_time = time.time()
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录

        Args:
            record: 日志记录对象
        """
        try:
            # 格式化日志记录
            log_entry = self.format_record(record)

            # 添加到缓冲区
            try:
                self.buffer.put_nowait(log_entry)
            except queue.Full:
                # 缓冲区满，丢弃最旧的记录
                try:
                    self.buffer.get_nowait()
                    self.buffer.put_nowait(log_entry)
                except queue.Empty:
                    pass

            # 检查是否需要刷新
            if self.buffer.qsize() >= self.buffer_size:
                self.flush()

        except Exception:
            self.handleError(record)

    def format_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        """格式化日志记录为字典

        Args:
            record: 日志记录对象

        Returns:
            日志字典
        """
        log_data = {
            "@timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
            "hostname": socket.gethostname(),
        }

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.format(record),
            }

        return log_data

    def flush(self) -> None:
        """刷新缓冲区"""
        with self._lock:
            if self.buffer.empty():
                return

            # 收集所有待发送的日志
            logs = []
            while not self.buffer.empty() and len(logs) < self.buffer_size:
                try:
                    logs.append(self.buffer.get_nowait())
                except queue.Empty:
                    break

            if logs:
                try:
                    self.send_logs(logs)
                    self.last_flush_time = time.time()
                except Exception:
                    # 发送失败，将日志放回缓冲区
                    for log in logs:
                        try:
                            self.buffer.put_nowait(log)
                        except queue.Full:
                            break

    def send_logs(self, logs: List[Dict[str, Any]]) -> None:
        """发送日志到收集后端

        子类需要实现此方法

        Args:
            logs: 日志列表
        """
        raise NotImplementedError("子类必须实现 send_logs 方法")

    def start(self) -> None:
        """启动后台刷新线程"""
        if self.running:
            return

        self.running = True
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True, name="LogCollectorFlush")
        self.flush_thread.start()

    def stop(self) -> None:
        """停止后台刷新线程"""
        if not self.running:
            return

        self.running = False
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=2.0)

        # 最后刷新一次
        self.flush()

    def _flush_worker(self) -> None:
        """后台刷新工作线程"""
        while self.running:
            try:
                # 检查是否需要刷新
                if time.time() - self.last_flush_time >= self.flush_interval:
                    self.flush()

                # 短暂休眠
                time.sleep(0.5)
            except Exception:
                pass

    def close(self) -> None:
        """关闭处理器"""
        self.stop()
        super().close()


class ElasticsearchHandler(LogCollectorHandler):
    """Elasticsearch 日志收集处理器

    直接将日志发送到 Elasticsearch
    """

    def __init__(
        self,
        hosts: List[str],
        index_prefix: str = "logs",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        """初始化 Elasticsearch 处理器

        Args:
            hosts: Elasticsearch 主机列表，如 ["http://localhost:9200"]
            index_prefix: 索引前缀，实际索引名为 {prefix}-YYYY.MM.DD
            username: 用户名（可选）
            password: 密码（可选）
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)

        if not HAS_REQUESTS:
            raise ImportError("Elasticsearch 处理器需要 requests 库")

        self.hosts = hosts
        self.index_prefix = index_prefix
        self.auth = (username, password) if username and password else None
        self.current_host_index = 0

    def get_index_name(self) -> str:
        """获取当前日期的索引名

        Returns:
            索引名，格式为 {prefix}-YYYY.MM.DD
        """
        date_str = datetime.now().strftime("%Y.%m.%d")
        return f"{self.index_prefix}-{date_str}"

    def send_logs(self, logs: List[Dict[str, Any]]) -> None:
        """发送日志到 Elasticsearch

        Args:
            logs: 日志列表
        """
        if not logs:
            return

        # 构建批量索引请求
        bulk_data = []
        index_name = self.get_index_name()

        for log in logs:
            # 索引元数据
            bulk_data.append(json.dumps({"index": {"_index": index_name}}))
            # 文档数据
            bulk_data.append(json.dumps(log, ensure_ascii=False))

        bulk_body = "\n".join(bulk_data) + "\n"

        # 尝试发送到所有主机
        last_error = None
        for _ in range(len(self.hosts)):
            host = self.hosts[self.current_host_index]
            url = f"{host}/_bulk"

            try:
                response = requests.post(
                    url,
                    data=bulk_body.encode("utf - 8"),
                    headers={"Content-Type": "application/x-ndjson"},
                    auth=self.auth,
                    timeout=10,
                )

                if response.status_code in (200, 201):
                    return  # 成功
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"

            except Exception as e:
                last_error = str(e)

            # 切换到下一个主机
            self.current_host_index = (self.current_host_index + 1) % len(self.hosts)

        # 所有主机都失败
        if last_error:
            raise Exception(f"发送日志到 Elasticsearch 失败: {last_error}")


class LogstashHandler(LogCollectorHandler):
    """Logstash 日志收集处理器

    通过 TCP 或 UDP 将日志发送到 Logstash
    """

    def __init__(self, host: str, port: int, protocol: str = "tcp", **kwargs):
        """初始化 Logstash 处理器

        Args:
            host: Logstash 主机地址
            port: Logstash 端口
            protocol: 协议类型，"tcp" 或 "udp"
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.socket: Optional[socket.socket] = None

        if self.protocol not in ("tcp", "udp"):
            raise ValueError(f"不支持的协议: {protocol}")

    def _ensure_connection(self) -> None:
        """确保 socket 连接已建立"""
        if self.socket is not None:
            return

        if self.protocol == "tcp":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
        else:  # udp
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_logs(self, logs: List[Dict[str, Any]]) -> None:
        """发送日志到 Logstash

        Args:
            logs: 日志列表
        """
        if not logs:
            return

        try:
            self._ensure_connection()

            for log in logs:
                message = json.dumps(log, ensure_ascii=False) + "\n"
                data = message.encode("utf - 8")

                if self.protocol == "tcp":
                    self.socket.sendall(data)
                else:  # udp
                    self.socket.sendto(data, (self.host, self.port))

        except Exception as e:
            # 连接失败，关闭 socket 以便下次重连
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
                self.socket = None
            raise Exception(f"发送日志到 Logstash 失败: {e}")

    def close(self) -> None:
        """关闭处理器"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        super().close()


class HTTPHandler(LogCollectorHandler):
    """HTTP 日志收集处理器

    通过 HTTP POST 将日志发送到指定端点
    """

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, auth: Optional[tuple] = None, **kwargs):
        """初始化 HTTP 处理器

        Args:
            url: HTTP 端点 URL
            headers: 自定义 HTTP 头（可选）
            auth: HTTP 认证元组 (username, password)（可选）
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)

        if not HAS_REQUESTS:
            raise ImportError("HTTP 处理器需要 requests 库")

        self.url = url
        self.headers = headers or {}
        self.auth = auth

        # 设置默认 Content-Type
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

    def send_logs(self, logs: List[Dict[str, Any]]) -> None:
        """发送日志到 HTTP 端点

        Args:
            logs: 日志列表
        """
        if not logs:
            return

        try:
            response = requests.post(self.url, json={"logs": logs}, headers=self.headers, auth=self.auth, timeout=10)

            if response.status_code not in (200, 201, 202):
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            raise Exception(f"发送日志到 HTTP 端点失败: {e}")


class FileCollectorHandler(logging.handlers.RotatingFileHandler):
    """文件日志收集处理器

    将日志以 JSON 格式写入文件，供 Filebeat 等工具采集
    """

    def __init__(self, filename: str, maxBytes: int = 10485760, backupCount: int = 5, **kwargs):
        """初始化文件收集处理器

        Args:
            filename: 日志文件路径
            maxBytes: 单个文件最大字节数
            backupCount: 保留的备份文件数量
            **kwargs: 传递给父类的参数
        """
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding="utf - 8", **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录

        Args:
            record: 日志记录对象
        """
        try:
            # 格式化为 JSON
            log_data = {
                "@timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "hostname": socket.gethostname(),
            }

            # 添加额外字段
            if hasattr(record, "extra_fields"):
                log_data.update(record.extra_fields)

            # 添加异常信息
            if record.exc_info:
                log_data["exception"] = {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatter.formatException(record.exc_info) if self.formatter else "",
                }

            # 写入文件
            msg = json.dumps(log_data, ensure_ascii=False) + "\n"

            if self.shouldRollover(record):
                self.doRollover()

            self.stream.write(msg)
            self.flush()

        except Exception:
            self.handleError(record)


class LogCollector:
    """日志收集管理器

    统一管理日志收集处理器的创建和配置
    """

    @staticmethod
    def create_elasticsearch_handler(config: Dict[str, Any]) -> ElasticsearchHandler:
        """创建 Elasticsearch 处理器

        Args:
            config: 配置字典，包含以下键：
                - hosts: 主机列表
                - index_prefix: 索引前缀（可选）
                - username: 用户名（可选）
                - password: 密码（可选）
                - buffer_size: 缓冲区大小（可选）
                - flush_interval: 刷新间隔（可选）
                - level: 日志级别（可选）

        Returns:
            Elasticsearch 处理器实例
        """
        handler = ElasticsearchHandler(
            hosts=config.get("hosts", ["http://localhost:9200"]),
            index_prefix=config.get("index_prefix", "logs"),
            username=config.get("username"),
            password=config.get("password"),
            buffer_size=config.get("buffer_size", 100),
            flush_interval=config.get("flush_interval", 5.0),
        )

        # 设置日志级别
        level = config.get("level", "INFO")
        handler.setLevel(getattr(logging, level))

        # 启动后台刷新线程
        handler.start()

        return handler

    @staticmethod
    def create_logstash_handler(config: Dict[str, Any]) -> LogstashHandler:
        """创建 Logstash 处理器

        Args:
            config: 配置字典，包含以下键：
                - host: 主机地址
                - port: 端口
                - protocol: 协议（tcp 或 udp）（可选）
                - buffer_size: 缓冲区大小（可选）
                - flush_interval: 刷新间隔（可选）
                - level: 日志级别（可选）

        Returns:
            Logstash 处理器实例
        """
        handler = LogstashHandler(
            host=config.get("host", "localhost"),
            port=config.get("port", 5000),
            protocol=config.get("protocol", "tcp"),
            buffer_size=config.get("buffer_size", 100),
            flush_interval=config.get("flush_interval", 5.0),
        )

        # 设置日志级别
        level = config.get("level", "INFO")
        handler.setLevel(getattr(logging, level))

        # 启动后台刷新线程
        handler.start()

        return handler

    @staticmethod
    def create_http_handler(config: Dict[str, Any]) -> HTTPHandler:
        """创建 HTTP 处理器

        Args:
            config: 配置字典，包含以下键：
                - url: HTTP 端点 URL
                - headers: HTTP 头（可选）
                - username: 用户名（可选）
                - password: 密码（可选）
                - buffer_size: 缓冲区大小（可选）
                - flush_interval: 刷新间隔（可选）
                - level: 日志级别（可选）

        Returns:
            HTTP 处理器实例
        """
        auth = None
        if config.get("username") and config.get("password"):
            auth = (config["username"], config["password"])

        handler = HTTPHandler(
            url=config.get("url"),
            headers=config.get("headers"),
            auth=auth,
            buffer_size=config.get("buffer_size", 100),
            flush_interval=config.get("flush_interval", 5.0),
        )

        # 设置日志级别
        level = config.get("level", "INFO")
        handler.setLevel(getattr(logging, level))

        # 启动后台刷新线程
        handler.start()

        return handler

    @staticmethod
    def create_file_collector_handler(config: Dict[str, Any]) -> FileCollectorHandler:
        """创建文件收集处理器

        Args:
            config: 配置字典，包含以下键：
                - filename: 文件路径
                - max_bytes: 最大字节数（可选）
                - backup_count: 备份数量（可选）
                - level: 日志级别（可选）

        Returns:
            文件收集处理器实例
        """
        handler = FileCollectorHandler(
            filename=config.get("filename", "logs/collector.log"),
            maxBytes=config.get("max_bytes", 10485760),
            backupCount=config.get("backup_count", 5),
        )

        # 设置日志级别
        level = config.get("level", "INFO")
        handler.setLevel(getattr(logging, level))

        return handler

    @staticmethod
    def setup_from_config(config_manager: Any) -> List[logging.Handler]:
        """从配置管理器设置日志收集

        Args:
            config_manager: 配置管理器实例

        Returns:
            创建的处理器列表
        """
        handlers = []

        # 获取日志收集配置
        collector_config = config_manager.get("logging.collector", {})

        if not collector_config.get("enabled", False):
            return handlers

        # 创建 Elasticsearch 处理器
        if collector_config.get("elasticsearch", {}).get("enabled", False):
            try:
                es_config = collector_config["elasticsearch"]
                handler = LogCollector.create_elasticsearch_handler(es_config)
                handlers.append(handler)
                print("✅ 已启用 Elasticsearch 日志收集")
            except Exception as e:
                print(f"⚠️  创建 Elasticsearch 处理器失败: {e}")

        # 创建 Logstash 处理器
        if collector_config.get("logstash", {}).get("enabled", False):
            try:
                logstash_config = collector_config["logstash"]
                handler = LogCollector.create_logstash_handler(logstash_config)
                handlers.append(handler)
                print("✅ 已启用 Logstash 日志收集")
            except Exception as e:
                print(f"⚠️  创建 Logstash 处理器失败: {e}")

        # 创建 HTTP 处理器
        if collector_config.get("http", {}).get("enabled", False):
            try:
                http_config = collector_config["http"]
                handler = LogCollector.create_http_handler(http_config)
                handlers.append(handler)
                print("✅ 已启用 HTTP 日志收集")
            except Exception as e:
                print(f"⚠️  创建 HTTP 处理器失败: {e}")

        # 创建文件收集处理器
        if collector_config.get("file", {}).get("enabled", False):
            try:
                file_config = collector_config["file"]
                handler = LogCollector.create_file_collector_handler(file_config)
                handlers.append(handler)
                print("✅ 已启用文件日志收集")
            except Exception as e:
                print(f"⚠️  创建文件收集处理器失败: {e}")

        # 将处理器添加到根日志记录器
        root_logger = logging.getLogger()
        for handler in handlers:
            root_logger.addHandler(handler)

        return handlers
