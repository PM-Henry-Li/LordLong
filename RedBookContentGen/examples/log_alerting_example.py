#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志告警使用示例

演示如何使用日志告警功能
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager
from src.core.logger import Logger
from src.core.log_alerting import (
    LogAlertManager,
    AlertingHandler,
    setup_from_config,
    create_error_rate_rule,
    create_slow_response_rule,
    AlertSeverity,
    LogAlertNotifier
)


def example_basic_alerting():
    """基础告警示例"""
    print("\n=== 基础告警示例 ===\n")
    
    # 创建告警管理器
    alert_manager = LogAlertManager(window_size=60)
    
    # 添加错误率告警规则
    rule = create_error_rate_rule(
        threshold=0.3,  # 30% 错误率
        duration=5,     # 持续 5 秒
        severity=AlertSeverity.CRITICAL
    )
    alert_manager.add_rule(rule)
    
    # 添加日志通知器
    notifier = LogAlertNotifier()
    alert_manager.add_notifier(notifier)
    
    # 启动告警管理器
    alert_manager.start(check_interval=2)
    
    # 初始化日志系统
    Logger.initialize(ConfigManager())
    
    # 添加告警处理器
    alerting_handler = AlertingHandler(alert_manager)
    root_logger = logging.getLogger()
    root_logger.addHandler(alerting_handler)
    
    print("开始记录日志，模拟高错误率...")
    
    # 模拟正常日志
    for i in range(5):
        Logger.info(f"正常操作 {i}")
        time.sleep(0.2)
    
    # 模拟大量错误日志
    for i in range(10):
        Logger.error(f"错误操作 {i}")
        time.sleep(0.2)
    
    # 等待告警检查
    print("等待告警检查...")
    time.sleep(6)
    
    # 停止告警管理器
    alert_manager.stop()
    
    print("✅ 基础告警示例完成")


def example_slow_response_alerting():
    """慢响应告警示例"""
    print("\n=== 慢响应告警示例 ===\n")
    
    # 创建告警管理器
    alert_manager = LogAlertManager(window_size=60)
    
    # 添加慢响应告警规则
    rule = create_slow_response_rule(
        threshold=2.0,  # 2 秒
        duration=5,     # 持续 5 秒
        severity=AlertSeverity.WARNING
    )
    alert_manager.add_rule(rule)
    
    # 添加日志通知器
    notifier = LogAlertNotifier()
    alert_manager.add_notifier(notifier)
    
    # 启动告警管理器
    alert_manager.start(check_interval=2)
    
    # 初始化日志系统
    Logger.initialize(ConfigManager())
    
    # 添加告警处理器
    alerting_handler = AlertingHandler(alert_manager)
    root_logger = logging.getLogger()
    root_logger.addHandler(alerting_handler)
    
    print("开始记录日志，模拟慢响应...")
    
    # 模拟快速响应
    for i in range(5):
        Logger.info(f"快速操作 {i}", elapsed_time=0.5)
        time.sleep(0.2)
    
    # 模拟慢响应
    for i in range(10):
        Logger.info(f"慢速操作 {i}", elapsed_time=3.5)
        time.sleep(0.2)
    
    # 等待告警检查
    print("等待告警检查...")
    time.sleep(6)
    
    # 停止告警管理器
    alert_manager.stop()
    
    print("✅ 慢响应告警示例完成")


def example_config_based_alerting():
    """基于配置的告警示例"""
    print("\n=== 基于配置的告警示例 ===\n")
    
    # 初始化配置管理器
    config = ConfigManager("config/config.json")
    
    # 检查告警是否启用
    if not config.get('logging.alerting.enabled', False):
        print("⚠️  告警功能未启用，请在 config/config.json 中启用")
        print("   设置 logging.alerting.enabled = true")
        return
    
    # 创建告警管理器
    alert_manager = LogAlertManager(
        window_size=config.get('logging.alerting.window_size', 300)
    )
    
    # 从配置设置告警规则和通知器
    setup_from_config(config, alert_manager)
    
    # 初始化日志系统
    Logger.initialize(config)
    
    # 添加告警处理器
    alerting_handler = AlertingHandler(alert_manager)
    root_logger = logging.getLogger()
    root_logger.addHandler(alerting_handler)
    
    print("告警系统已启动，使用配置文件中的规则")
    print("开始记录测试日志...")
    
    # 记录一些测试日志
    Logger.info("应用启动")
    Logger.info("开始处理任务")
    
    # 模拟一些错误
    for i in range(3):
        Logger.error(f"测试错误 {i}")
        time.sleep(1)
    
    Logger.info("任务处理完成")
    
    # 等待告警检查
    print("等待告警检查...")
    time.sleep(15)
    
    # 停止告警管理器
    alert_manager.stop()
    
    print("✅ 基于配置的告警示例完成")


def example_custom_rule():
    """自定义告警规则示例"""
    print("\n=== 自定义告警规则示例 ===\n")
    
    from src.core.log_alerting import AlertRule
    
    # 创建告警管理器
    alert_manager = LogAlertManager(window_size=60)
    
    # 定义自定义条件：检测登录失败
    def login_failure_condition(logs):
        failures = sum(
            1 for log in logs
            if 'login' in log.get('message', '').lower() 
            and log.get('level') == 'ERROR'
        )
        return failures >= 3
    
    # 创建自定义规则
    rule = AlertRule(
        name="LoginFailure",
        condition=login_failure_condition,
        severity=AlertSeverity.WARNING,
        message="登录失败次数过多，可能存在暴力破解",
        duration=5,
        cooldown=60
    )
    
    alert_manager.add_rule(rule)
    
    # 添加日志通知器
    notifier = LogAlertNotifier()
    alert_manager.add_notifier(notifier)
    
    # 启动告警管理器
    alert_manager.start(check_interval=2)
    
    # 初始化日志系统
    Logger.initialize(ConfigManager())
    
    # 添加告警处理器
    alerting_handler = AlertingHandler(alert_manager)
    root_logger = logging.getLogger()
    root_logger.addHandler(alerting_handler)
    
    print("开始记录日志，模拟登录失败...")
    
    # 模拟正常登录
    Logger.info("用户 user1 登录成功")
    Logger.info("用户 user2 登录成功")
    
    # 模拟登录失败
    for i in range(5):
        Logger.error(f"用户 hacker{i} 登录失败：密码错误")
        time.sleep(0.5)
    
    # 等待告警检查
    print("等待告警检查...")
    time.sleep(6)
    
    # 停止告警管理器
    alert_manager.stop()
    
    print("✅ 自定义告警规则示例完成")


def example_multiple_notifiers():
    """多通知器示例"""
    print("\n=== 多通知器示例 ===\n")
    
    from src.core.log_alerting import HTTPAlertNotifier
    
    # 创建告警管理器
    alert_manager = LogAlertManager(window_size=60)
    
    # 添加错误率告警规则
    rule = create_error_rate_rule(
        threshold=0.3,
        duration=5,
        severity=AlertSeverity.CRITICAL
    )
    alert_manager.add_rule(rule)
    
    # 添加多个通知器
    
    # 1. 日志通知器
    log_notifier = LogAlertNotifier()
    alert_manager.add_notifier(log_notifier)
    
    # 2. HTTP 通知器（模拟，实际使用时需要真实的 URL）
    # http_notifier = HTTPAlertNotifier(
    #     url="https://oapi.dingtalk.com/robot/send?access_token=xxx",
    #     headers={"Content-Type": "application/json"}
    # )
    # alert_manager.add_notifier(http_notifier)
    
    print("已添加多个通知器：日志通知器")
    print("（HTTP 通知器已注释，需要配置真实的 URL）")
    
    # 启动告警管理器
    alert_manager.start(check_interval=2)
    
    # 初始化日志系统
    Logger.initialize(ConfigManager())
    
    # 添加告警处理器
    alerting_handler = AlertingHandler(alert_manager)
    root_logger = logging.getLogger()
    root_logger.addHandler(alerting_handler)
    
    print("开始记录日志，触发告警...")
    
    # 模拟大量错误
    for i in range(15):
        Logger.error(f"严重错误 {i}")
        time.sleep(0.2)
    
    # 等待告警检查
    print("等待告警检查...")
    time.sleep(6)
    
    # 停止告警管理器
    alert_manager.stop()
    
    print("✅ 多通知器示例完成")


def main():
    """主函数"""
    print("=" * 60)
    print("日志告警使用示例")
    print("=" * 60)
    
    examples = [
        ("基础告警", example_basic_alerting),
        ("慢响应告警", example_slow_response_alerting),
        ("基于配置的告警", example_config_based_alerting),
        ("自定义告警规则", example_custom_rule),
        ("多通知器", example_multiple_notifiers),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ 示例 '{name}' 执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 等待一下，避免日志混乱
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)
    print("\n提示:")
    print("1. 查看 logs/app.log 文件可以看到告警日志")
    print("2. 编辑 config/config.json 启用告警功能")
    print("3. 参考 docs/LOG_ALERTING.md 了解详细配置")
    print("4. 可以配置 HTTP 通知器发送到钉钉、企业微信等")


if __name__ == "__main__":
    main()
