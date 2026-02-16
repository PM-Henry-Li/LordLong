#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志收集使用示例

演示如何使用日志收集功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager
from src.core.logger import Logger, LogContext


def example_basic_logging():
    """基础日志记录示例"""
    print("\n=== 基础日志记录示例 ===\n")
    
    # 初始化配置管理器
    config = ConfigManager("config/config.json")
    
    # 初始化日志系统（会自动设置日志收集）
    Logger.initialize(config)
    
    # 获取日志记录器
    logger = Logger.get_logger("example")
    
    # 记录不同级别的日志
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    print("✅ 日志已记录，如果启用了日志收集，日志会自动发送到配置的后端")


def example_with_context():
    """使用日志上下文示例"""
    print("\n=== 使用日志上下文示例 ===\n")
    
    # 初始化
    config = ConfigManager("config/config.json")
    Logger.initialize(config)
    
    # 使用上下文管理器
    with LogContext(request_id="req-12345", user_id="user-789"):
        Logger.info("处理用户请求", logger_name="api")
        Logger.info("查询数据库", logger_name="database")
        Logger.info("返回结果", logger_name="api")
    
    print("✅ 带上下文的日志已记录，所有日志都会包含 request_id 和 user_id")


def example_with_extra_fields():
    """使用额外字段示例"""
    print("\n=== 使用额外字段示例 ===\n")
    
    # 初始化
    config = ConfigManager("config/config.json")
    Logger.initialize(config)
    
    # 记录带额外字段的日志
    Logger.info(
        "内容生成完成",
        logger_name="content_generator",
        content_length=1500,
        generation_time=2.5,
        model="qwen-plus",
        success=True
    )
    
    Logger.info(
        "图片生成完成",
        logger_name="image_generator",
        image_count=5,
        total_time=120.5,
        mode="template",
        style="retro_chinese"
    )
    
    print("✅ 带额外字段的日志已记录，便于后续分析和查询")


def example_exception_logging():
    """异常日志记录示例"""
    print("\n=== 异常日志记录示例 ===\n")
    
    # 初始化
    config = ConfigManager("config/config.json")
    Logger.initialize(config)
    
    logger = Logger.get_logger("example")
    
    # 模拟异常
    try:
        result = 10 / 0
    except Exception as e:
        logger.exception("计算出错")
    
    print("✅ 异常日志已记录，包含完整的堆栈跟踪信息")


def example_performance_logging():
    """性能日志记录示例"""
    print("\n=== 性能日志记录示例 ===\n")
    
    # 初始化
    config = ConfigManager("config/config.json")
    Logger.initialize(config)
    
    # 模拟性能监控
    with LogContext(operation="content_generation"):
        start_time = time.time()
        
        Logger.info("开始生成内容", logger_name="performance")
        
        # 模拟耗时操作
        time.sleep(0.5)
        
        elapsed = time.time() - start_time
        Logger.info(
            "内容生成完成",
            logger_name="performance",
            elapsed_time=elapsed,
            status="success"
        )
    
    print(f"✅ 性能日志已记录，耗时 {elapsed:.2f} 秒")


def example_structured_logging():
    """结构化日志示例"""
    print("\n=== 结构化日志示例 ===\n")
    
    # 初始化
    config = ConfigManager("config/config.json")
    Logger.initialize(config)
    
    # 记录结构化业务日志
    Logger.info(
        "用户注册",
        logger_name="user_service",
        event_type="user_registration",
        user_id="user-123",
        email="user@example.com",
        registration_source="web",
        timestamp=time.time()
    )
    
    Logger.info(
        "订单创建",
        logger_name="order_service",
        event_type="order_created",
        order_id="order-456",
        user_id="user-123",
        amount=99.99,
        currency="CNY",
        items_count=3
    )
    
    print("✅ 结构化日志已记录，便于业务分析和数据挖掘")


def main():
    """主函数"""
    print("=" * 60)
    print("日志收集使用示例")
    print("=" * 60)
    
    examples = [
        ("基础日志记录", example_basic_logging),
        ("使用日志上下文", example_with_context),
        ("使用额外字段", example_with_extra_fields),
        ("异常日志记录", example_exception_logging),
        ("性能日志记录", example_performance_logging),
        ("结构化日志", example_structured_logging),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ 示例 '{name}' 执行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)
    print("\n提示:")
    print("1. 查看 logs/app.log 文件可以看到所有日志")
    print("2. 如果启用了日志收集，日志会发送到配置的后端")
    print("3. 编辑 config/config.json 启用日志收集功能")
    print("4. 参考 docs/LOG_COLLECTOR.md 了解详细配置")


if __name__ == "__main__":
    main()
