#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志告警模块测试
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.log_alerting import (
    AlertRule,
    AlertSeverity,
    LogAlertManager,
    LogAlertNotifier,
    HTTPAlertNotifier,
    AlertingHandler,
    create_error_rate_rule,
    create_slow_response_rule,
    create_api_failure_rule,
    create_memory_usage_rule,
)


def test_alert_rule_basic():
    """测试基础告警规则"""
    print("\n=== 测试基础告警规则 ===")

    # 创建简单的条件函数
    def simple_condition(logs):
        return len(logs) > 5

    # 创建规则
    rule = AlertRule(
        name="TestRule",
        condition=simple_condition,
        severity=AlertSeverity.WARNING,
        message="日志数量超过 5 条",
        duration=0,  # 立即触发
        cooldown=10,
    )

    # 测试条件不满足
    logs = [{"level": "INFO"} for _ in range(3)]
    assert not rule.check(logs), "条件不满足时不应触发"

    # 测试条件满足
    logs = [{"level": "INFO"} for _ in range(10)]
    assert rule.check(logs), "条件满足时应触发"

    # 测试冷却期
    assert not rule.check(logs), "冷却期内不应重复触发"

    print("✅ 基础告警规则测试通过")


def test_error_rate_rule():
    """测试错误率告警规则"""
    print("\n=== 测试错误率告警规则 ===")

    rule = create_error_rate_rule(threshold=0.3, duration=0, severity=AlertSeverity.CRITICAL)  # 30%

    # 测试低错误率
    logs = [{"level": "INFO"} for _ in range(8)] + [{"level": "ERROR"} for _ in range(2)]
    assert not rule.check(logs), "错误率 20% 不应触发（阈值 30%）"

    # 测试高错误率
    logs = [{"level": "INFO"} for _ in range(6)] + [{"level": "ERROR"} for _ in range(4)]
    assert rule.check(logs), "错误率 40% 应触发（阈值 30%）"

    print("✅ 错误率告警规则测试通过")


def test_slow_response_rule():
    """测试慢响应告警规则"""
    print("\n=== 测试慢响应告警规则 ===")

    rule = create_slow_response_rule(threshold=5.0, duration=0, severity=AlertSeverity.WARNING)  # 5 秒

    # 测试快速响应
    logs = [{"elapsed_time": i * 0.5} for i in range(10)]
    assert not rule.check(logs), "P95 < 5 秒不应触发"

    # 测试慢响应
    logs = [{"elapsed_time": i * 1.0} for i in range(10)]
    assert rule.check(logs), "P95 > 5 秒应触发"

    print("✅ 慢响应告警规则测试通过")


def test_api_failure_rule():
    """测试 API 失败告警规则"""
    print("\n=== 测试 API 失败告警规则 ===")

    rule = create_api_failure_rule(threshold=5, duration=0, severity=AlertSeverity.CRITICAL)

    # 测试少量失败
    logs = [{"level": "ERROR", "message": "API 调用失败"} for _ in range(3)] + [
        {"level": "INFO", "message": "正常操作"} for _ in range(5)
    ]
    assert not rule.check(logs), "失败 3 次不应触发（阈值 5）"

    # 测试大量失败
    logs = [{"level": "ERROR", "message": "API 调用失败"} for _ in range(8)] + [
        {"level": "INFO", "message": "正常操作"} for _ in range(2)
    ]
    assert rule.check(logs), "失败 8 次应触发（阈值 5）"

    print("✅ API 失败告警规则测试通过")


def test_memory_usage_rule():
    """测试内存使用告警规则"""
    print("\n=== 测试内存使用告警规则 ===")

    rule = create_memory_usage_rule(threshold_mb=500.0, duration=0, severity=AlertSeverity.WARNING)

    # 测试低内存使用
    logs = [{"memory_mb": 300.0 + i * 10} for i in range(10)]
    assert not rule.check(logs), "平均内存 < 500 MB 不应触发"

    # 测试高内存使用
    logs = [{"memory_mb": 600.0 + i * 10} for i in range(10)]
    assert rule.check(logs), "平均内存 > 500 MB 应触发"

    print("✅ 内存使用告警规则测试通过")


def test_alert_manager():
    """测试告警管理器"""
    print("\n=== 测试告警管理器 ===")

    # 创建告警管理器
    manager = LogAlertManager(window_size=60)

    # 添加规则
    rule = create_error_rate_rule(threshold=0.3, duration=0)
    manager.add_rule(rule)

    # 添加通知器
    notifier = LogAlertNotifier()
    manager.add_notifier(notifier)

    # 添加日志
    for i in range(10):
        manager.add_log({"level": "ERROR" if i < 5 else "INFO", "message": f"测试日志 {i}"})

    # 检查规则
    manager.check_rules()

    # 验证日志数量
    assert len(manager.logs) == 10, "应该有 10 条日志"

    print("✅ 告警管理器测试通过")


def test_alerting_handler():
    """测试告警处理器"""
    print("\n=== 测试告警处理器 ===")

    # 创建告警管理器
    manager = LogAlertManager(window_size=60)

    # 创建告警处理器
    handler = AlertingHandler(manager)

    # 创建日志记录器
    logger = logging.getLogger("test_alerting")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # 记录日志
    logger.info("测试信息")
    logger.error("测试错误")

    # 验证日志已添加到管理器
    assert len(manager.logs) == 2, "应该有 2 条日志"
    assert manager.logs[0]["level"] == "INFO", "第一条应该是 INFO"
    assert manager.logs[1]["level"] == "ERROR", "第二条应该是 ERROR"

    print("✅ 告警处理器测试通过")


def test_log_notifier():
    """测试日志通知器"""
    print("\n=== 测试日志通知器 ===")

    notifier = LogAlertNotifier()

    # 发送告警
    alert = {
        "rule_name": "TestRule",
        "severity": "critical",
        "message": "测试告警",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 不应抛出异常
    notifier.send(alert)

    print("✅ 日志通知器测试通过")


def test_duration_check():
    """测试持续时间检查"""
    print("\n=== 测试持续时间检查 ===")

    def always_true(logs):
        return True

    rule = AlertRule(
        name="DurationTest",
        condition=always_true,
        severity=AlertSeverity.INFO,
        message="测试持续时间",
        duration=2,  # 需要持续 2 秒
        cooldown=10,
    )

    logs = [{"level": "INFO"}]

    # 第一次检查，条件满足但持续时间不够
    assert not rule.check(logs), "持续时间不够不应触发"

    # 等待 2 秒
    time.sleep(2)

    # 第二次检查，持续时间够了
    assert rule.check(logs), "持续时间够了应触发"

    print("✅ 持续时间检查测试通过")


def test_cooldown_period():
    """测试冷却期"""
    print("\n=== 测试冷却期 ===")

    def always_true(logs):
        return True

    rule = AlertRule(
        name="CooldownTest",
        condition=always_true,
        severity=AlertSeverity.INFO,
        message="测试冷却期",
        duration=0,
        cooldown=2,  # 冷却期 2 秒
    )

    logs = [{"level": "INFO"}]

    # 第一次触发
    assert rule.check(logs), "第一次应触发"

    # 立即再次检查，应该在冷却期内
    assert not rule.check(logs), "冷却期内不应触发"

    # 等待冷却期结束
    time.sleep(2)

    # 冷却期后再次检查
    assert rule.check(logs), "冷却期后应该可以再次触发"

    print("✅ 冷却期测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("日志告警模块测试")
    print("=" * 60)

    tests = [
        test_alert_rule_basic,
        test_error_rate_rule,
        test_slow_response_rule,
        test_api_failure_rule,
        test_memory_usage_rule,
        test_alert_manager,
        test_alerting_handler,
        test_log_notifier,
        test_duration_check,
        test_cooldown_period,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test_func.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {test_func.__name__}")
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
