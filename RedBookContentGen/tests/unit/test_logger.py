#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger 模块单元测试
"""

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.logger import (
    Logger,
    LogContext,
    JSONFormatter,
    TextFormatter,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
    exception,
)
from src.core.config_manager import ConfigManager


class TestJSONFormatter:
    """测试 JSON 格式化器"""

    def test_basic_formatting(self):
        """测试基本格式化"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="测试消息", args=(), exc_info=None
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "测试消息"
        assert data["line"] == 10
        assert "timestamp" in data
        print("✅ JSON 基本格式化测试通过")

    def test_formatting_with_context(self):
        """测试带上下文的格式化"""
        formatter = JSONFormatter()

        with LogContext(request_id="req-123", user_id="user-456"):
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="测试消息", args=(), exc_info=None
            )

            result = formatter.format(record)
            data = json.loads(result)

            assert "context" in data
            assert data["context"]["request_id"] == "req-123"
            assert data["context"]["user_id"] == "user-456"

        print("✅ JSON 上下文格式化测试通过")

    def test_formatting_with_exception(self):
        """测试异常格式化"""
        formatter = JSONFormatter()

        try:
            raise ValueError("测试异常")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="发生错误",
                args=(),
                exc_info=sys.exc_info(),
            )

            result = formatter.format(record)
            data = json.loads(result)

            assert "exception" in data
            assert data["exception"]["type"] == "ValueError"
            assert data["exception"]["message"] == "测试异常"
            assert "traceback" in data["exception"]

        print("✅ JSON 异常格式化测试通过")


class TestTextFormatter:
    """测试文本格式化器"""

    def test_basic_formatting(self):
        """测试基本格式化"""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="测试消息", args=(), exc_info=None
        )

        result = formatter.format(record)

        assert "✅" in result  # INFO emoji
        assert "[INFO]" in result
        assert "test" in result
        assert "测试消息" in result
        print("✅ 文本基本格式化测试通过")

    def test_formatting_with_context(self):
        """测试带上下文的格式化"""
        formatter = TextFormatter()

        with LogContext(request_id="req-123"):
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="test.py", lineno=10, msg="测试消息", args=(), exc_info=None
            )

            result = formatter.format(record)

            assert "request_id=req-123" in result

        print("✅ 文本上下文格式化测试通过")


class TestLogger:
    """测试 Logger 类"""

    def test_initialization(self):
        """测试初始化"""
        # 重置初始化状态
        Logger._initialized = False
        Logger._loggers.clear()

        Logger.initialize()

        assert Logger._initialized is True
        print("✅ Logger 初始化测试通过")

    def test_initialization_with_config(self):
        """测试使用配置初始化"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "logging": {
                    "level": "DEBUG",
                    "format": "json",
                    "file": "logs/test.log",
                    "max_bytes": 1048576,
                    "backup_count": 3,
                }
            }
            json.dump(config_data, f)
            config_path = f.name

        try:
            # 重置初始化状态
            Logger._initialized = False
            Logger._loggers.clear()

            config = ConfigManager(config_path=config_path)
            Logger.initialize(config)

            assert Logger._initialized is True
            assert Logger._config is config
            print("✅ Logger 配置初始化测试通过")
        finally:
            os.unlink(config_path)

    def test_get_logger(self):
        """测试获取日志记录器"""
        Logger._initialized = False
        Logger._loggers.clear()

        logger1 = Logger.get_logger("test1")
        logger2 = Logger.get_logger("test1")
        logger3 = Logger.get_logger("test2")

        assert logger1 is logger2  # 同名日志记录器应该是同一个实例
        assert logger1 is not logger3
        assert logger1.name == "test1"
        assert logger3.name == "test2"
        print("✅ 获取日志记录器测试通过")

    def test_log_levels(self):
        """测试不同日志级别"""
        # 创建临时日志文件
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            # 创建配置
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_data = {
                    "logging": {
                        "level": "DEBUG",
                        "format": "text",
                        "file": log_file,
                        "max_bytes": 1048576,
                        "backup_count": 3,
                    }
                }
                json.dump(config_data, f)
                config_path = f.name

            try:
                # 重置并初始化
                Logger._initialized = False
                Logger._loggers.clear()

                config = ConfigManager(config_path=config_path)
                Logger.initialize(config)

                # 记录不同级别的日志
                Logger.debug("调试消息", logger_name="test")
                Logger.info("信息消息", logger_name="test")
                Logger.warning("警告消息", logger_name="test")
                Logger.error("错误消息", logger_name="test")
                Logger.critical("严重错误消息", logger_name="test")

                # 等待日志写入
                time.sleep(0.1)

                # 验证日志文件
                assert os.path.exists(log_file)
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "调试消息" in content
                    assert "信息消息" in content
                    assert "警告消息" in content
                    assert "错误消息" in content
                    assert "严重错误消息" in content

                print("✅ 日志级别测试通过")
            finally:
                os.unlink(config_path)

    def test_log_with_extra_fields(self):
        """测试带额外字段的日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_data = {"logging": {"level": "INFO", "format": "json", "file": log_file}}
                json.dump(config_data, f)
                config_path = f.name

            try:
                Logger._initialized = False
                Logger._loggers.clear()

                config = ConfigManager(config_path=config_path)
                Logger.initialize(config)

                Logger.info("测试消息", logger_name="test", user_id="user123", action="login")

                time.sleep(0.1)

                with open(log_file, "r", encoding="utf-8") as f:
                    line = f.readline()
                    data = json.loads(line)
                    assert data["message"] == "测试消息"
                    assert data["user_id"] == "user123"
                    assert data["action"] == "login"

                print("✅ 额外字段日志测试通过")
            finally:
                os.unlink(config_path)

    def test_exception_logging(self):
        """测试异常日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_data = {"logging": {"level": "ERROR", "format": "json", "file": log_file}}
                json.dump(config_data, f)
                config_path = f.name

            try:
                Logger._initialized = False
                Logger._loggers.clear()

                config = ConfigManager(config_path=config_path)
                Logger.initialize(config)

                try:
                    raise ValueError("测试异常")
                except ValueError:
                    Logger.exception("捕获到异常", logger_name="test")

                time.sleep(0.1)

                with open(log_file, "r", encoding="utf-8") as f:
                    line = f.readline()
                    data = json.loads(line)
                    assert "exception" in data
                    assert data["exception"]["type"] == "ValueError"
                    assert data["exception"]["message"] == "测试异常"

                print("✅ 异常日志测试通过")
            finally:
                os.unlink(config_path)


class TestLogContext:
    """测试日志上下文管理器"""

    def test_context_manager(self):
        """测试上下文管理器"""
        # 初始状态
        assert LogContext.get() == {}

        # 使用上下文管理器
        with LogContext(request_id="req-123", user_id="user-456"):
            context = LogContext.get()
            assert context["request_id"] == "req-123"
            assert context["user_id"] == "user-456"

        # 退出后应该恢复
        assert LogContext.get() == {}
        print("✅ 上下文管理器测试通过")

    def test_nested_context(self):
        """测试嵌套上下文"""
        with LogContext(request_id="req-123"):
            assert LogContext.get()["request_id"] == "req-123"

            with LogContext(user_id="user-456"):
                context = LogContext.get()
                assert context["request_id"] == "req-123"
                assert context["user_id"] == "user-456"

            # 内层退出后，外层上下文应该保留
            context = LogContext.get()
            assert context["request_id"] == "req-123"
            assert "user_id" not in context

        assert LogContext.get() == {}
        print("✅ 嵌套上下文测试通过")

    def test_set_and_clear(self):
        """测试设置和清除上下文"""
        LogContext.set(key1="value1", key2="value2")
        context = LogContext.get()
        assert context["key1"] == "value1"
        assert context["key2"] == "value2"

        LogContext.clear()
        assert LogContext.get() == {}
        print("✅ 设置和清除上下文测试通过")


class TestLogRotation:
    """测试日志轮转"""

    def test_size_based_rotation(self):
        """测试基于大小的日志轮转"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            # 设置很小的文件大小以触发轮转
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_data = {
                    "logging": {
                        "level": "INFO",
                        "format": "text",
                        "file": log_file,
                        "max_bytes": 1024,  # 1KB
                        "backup_count": 3,
                    }
                }
                json.dump(config_data, f)
                config_path = f.name

            try:
                Logger._initialized = False
                Logger._loggers.clear()

                config = ConfigManager(config_path=config_path)
                Logger.initialize(config)

                # 写入大量日志以触发轮转
                for i in range(100):
                    Logger.info(f"测试消息 {i} " + "x" * 100, logger_name="test")

                time.sleep(0.2)

                # 检查是否生成了轮转文件
                log_files = list(Path(tmpdir).glob("test.log*"))
                assert len(log_files) > 1  # 应该有主文件和至少一个备份文件
                print(f"✅ 日志轮转测试通过（生成了 {len(log_files)} 个文件）")
            finally:
                os.unlink(config_path)


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_convenience_functions(self):
        """测试便捷函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_data = {"logging": {"level": "DEBUG", "format": "text", "file": log_file}}
                json.dump(config_data, f)
                config_path = f.name

            try:
                Logger._initialized = False
                Logger._loggers.clear()

                config = ConfigManager(config_path=config_path)
                Logger.initialize(config)

                # 测试便捷函数
                debug("调试消息")
                info("信息消息")
                warning("警告消息")
                error("错误消息")
                critical("严重错误消息")

                time.sleep(0.1)

                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "调试消息" in content
                    assert "信息消息" in content
                    assert "警告消息" in content
                    assert "错误消息" in content
                    assert "严重错误消息" in content

                print("✅ 便捷函数测试通过")
            finally:
                os.unlink(config_path)

    def test_get_logger_function(self):
        """测试 get_logger 便捷函数"""
        Logger._initialized = False
        Logger._loggers.clear()

        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
        print("✅ get_logger 便捷函数测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行 Logger 模块单元测试")
    print("=" * 60)

    # JSON 格式化器测试
    print("\n--- JSON 格式化器测试 ---")
    json_formatter_tests = TestJSONFormatter()
    json_formatter_tests.test_basic_formatting()
    json_formatter_tests.test_formatting_with_context()
    json_formatter_tests.test_formatting_with_exception()

    # 文本格式化器测试
    print("\n--- 文本格式化器测试 ---")
    text_formatter_tests = TestTextFormatter()
    text_formatter_tests.test_basic_formatting()
    text_formatter_tests.test_formatting_with_context()

    # Logger 类测试
    print("\n--- Logger 类测试 ---")
    logger_tests = TestLogger()
    logger_tests.test_initialization()
    logger_tests.test_initialization_with_config()
    logger_tests.test_get_logger()
    logger_tests.test_log_levels()
    logger_tests.test_log_with_extra_fields()
    logger_tests.test_exception_logging()

    # 日志上下文测试
    print("\n--- 日志上下文测试 ---")
    context_tests = TestLogContext()
    context_tests.test_context_manager()
    context_tests.test_nested_context()
    context_tests.test_set_and_clear()

    # 日志轮转测试
    print("\n--- 日志轮转测试 ---")
    rotation_tests = TestLogRotation()
    rotation_tests.test_size_based_rotation()

    # 便捷函数测试
    print("\n--- 便捷函数测试 ---")
    convenience_tests = TestConvenienceFunctions()
    convenience_tests.test_convenience_functions()
    convenience_tests.test_get_logger_function()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
