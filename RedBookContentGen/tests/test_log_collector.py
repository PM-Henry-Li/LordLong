#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志收集模块测试

测试日志收集功能的各个组件
"""

import json
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.log_collector import (
    LogCollectorHandler,
    ElasticsearchHandler,
    LogstashHandler,
    HTTPHandler,
    FileCollectorHandler,
    LogCollector,
)


class MockCollectorHandler(LogCollectorHandler):
    """模拟日志收集处理器，用于测试"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sent_logs = []

    def send_logs(self, logs):
        """记录发送的日志"""
        self.sent_logs.extend(logs)
        print(f"✅ 模拟发送 {len(logs)} 条日志")


def test_collector_handler_basic():
    """测试基础日志收集处理器"""
    print("\n=== 测试基础日志收集处理器 ===")

    # 创建处理器
    handler = MockCollectorHandler(buffer_size=3, flush_interval=1.0)
    handler.start()

    # 创建日志记录器
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # 发送日志
    print("发送 5 条日志...")
    for i in range(5):
        logger.info(f"测试日志 {i+1}")
        time.sleep(0.1)

    # 等待刷新
    time.sleep(2)

    # 验证
    assert len(handler.sent_logs) >= 5, f"应该发送至少 5 条日志，实际发送 {len(handler.sent_logs)} 条"
    print(f"✅ 成功发送 {len(handler.sent_logs)} 条日志")

    # 清理
    handler.stop()
    logger.removeHandler(handler)


def test_format_record():
    """测试日志记录格式化"""
    print("\n=== 测试日志记录格式化 ===")

    handler = MockCollectorHandler()

    # 创建日志记录
    logger = logging.getLogger("test")
    record = logger.makeRecord("test", logging.INFO, "test.py", 10, "测试消息", (), None, "test_function")

    # 格式化
    log_data = handler.format_record(record)

    # 验证
    assert "@timestamp" in log_data, "应该包含时间戳"
    assert log_data["level"] == "INFO", "日志级别应该是 INFO"
    assert log_data["message"] == "测试消息", "消息内容不正确"
    assert log_data["logger"] == "test", "日志记录器名称不正确"

    print("✅ 日志记录格式化正确")
    print(f"   格式化结果: {json.dumps(log_data, ensure_ascii=False, indent=2)}")


def test_buffer_flush():
    """测试缓冲区刷新"""
    print("\n=== 测试缓冲区刷新 ===")

    # 创建小缓冲区
    handler = MockCollectorHandler(buffer_size=2, flush_interval=10.0)
    handler.start()

    logger = logging.getLogger("test_buffer")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # 发送日志触发缓冲区刷新
    print("发送 3 条日志（缓冲区大小为 2）...")
    logger.info("日志 1")
    logger.info("日志 2")
    logger.info("日志 3")  # 这条应该触发刷新

    # 短暂等待
    time.sleep(0.5)

    # 验证至少刷新了一次
    assert len(handler.sent_logs) >= 2, f"应该至少刷新 2 条日志，实际 {len(handler.sent_logs)} 条"
    print(f"✅ 缓冲区自动刷新成功，已发送 {len(handler.sent_logs)} 条日志")

    # 清理
    handler.stop()
    logger.removeHandler(handler)


def test_file_collector_handler():
    """测试文件收集处理器"""
    print("\n=== 测试文件收集处理器 ===")

    # 创建临时日志文件
    log_file = "logs/test_collector.log"
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # 删除旧的测试文件
    if Path(log_file).exists():
        Path(log_file).unlink()

    # 创建处理器（使用更大的文件大小避免轮转）
    handler = FileCollectorHandler(log_file, maxBytes=10240, backupCount=2)
    handler.setLevel(logging.INFO)

    # 创建日志记录器
    logger = logging.getLogger("test_file")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # 发送日志
    print(f"写入日志到 {log_file}...")
    for i in range(5):
        # 创建日志记录并添加额外字段
        record = logger.makeRecord(
            logger.name, logging.INFO, "test.py", 10, f"文件收集测试日志 {i+1}", (), None, "test_function"
        )
        record.extra_fields = {"test_id": i + 1, "test_type": "file_collector"}
        logger.handle(record)

    # 刷新
    handler.flush()

    # 验证文件存在
    assert Path(log_file).exists(), f"日志文件应该存在: {log_file}"

    # 读取并验证内容
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 5, f"应该有至少 5 行日志，实际 {len(lines)} 行"

    # 验证 JSON 格式
    first_log = json.loads(lines[0])
    assert "@timestamp" in first_log, "日志应该包含时间戳"
    assert first_log["level"] == "INFO", "日志级别应该是 INFO"

    print(f"✅ 文件收集处理器测试成功，写入 {len(lines)} 行日志")
    print(f"   示例日志: {json.dumps(first_log, ensure_ascii=False)}")

    # 清理
    logger.removeHandler(handler)
    handler.close()


def test_log_collector_factory():
    """测试日志收集器工厂方法"""
    print("\n=== 测试日志收集器工厂方法 ===")

    # 测试文件收集处理器创建
    config = {"filename": "logs/test_factory.log", "max_bytes": 1024, "backup_count": 2, "level": "DEBUG"}

    handler = LogCollector.create_file_collector_handler(config)
    assert handler is not None, "应该成功创建文件收集处理器"
    assert handler.level == logging.DEBUG, "日志级别应该是 DEBUG"

    print("✅ 文件收集处理器创建成功")

    handler.close()


def test_exception_logging():
    """测试异常日志记录"""
    print("\n=== 测试异常日志记录 ===")

    handler = MockCollectorHandler()
    handler.start()

    logger = logging.getLogger("test_exception")
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

    # 触发异常并记录
    try:
        raise ValueError("这是一个测试异常")
    except Exception as e:
        logger.exception("捕获到异常")

    # 等待刷新
    time.sleep(0.5)
    handler.flush()

    # 验证
    assert len(handler.sent_logs) > 0, "应该记录异常日志"

    exception_log = handler.sent_logs[0]
    assert "exception" in exception_log, "日志应该包含异常信息"
    assert exception_log["exception"]["type"] == "ValueError", "异常类型不正确"
    assert "测试异常" in exception_log["exception"]["message"], "异常消息不正确"

    print("✅ 异常日志记录成功")
    print(f"   异常信息: {exception_log['exception']}")

    # 清理
    handler.stop()
    logger.removeHandler(handler)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("日志收集模块测试")
    print("=" * 60)

    tests = [
        ("基础日志收集处理器", test_collector_handler_basic),
        ("日志记录格式化", test_format_record),
        ("缓冲区刷新", test_buffer_flush),
        ("文件收集处理器", test_file_collector_handler),
        ("日志收集器工厂方法", test_log_collector_factory),
        ("异常日志记录", test_exception_logging),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {name}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试出错: {name}")
            print(f"   异常: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
