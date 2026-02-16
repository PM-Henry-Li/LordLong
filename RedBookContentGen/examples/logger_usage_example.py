#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger 模块使用示例

演示如何使用 Logger 模块进行日志记录
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.logger import Logger, LogContext, get_logger, info, warning, error
from src.core.config_manager import ConfigManager


def example_basic_logging():
    """示例1：基本日志记录"""
    print("\n=== 示例1：基本日志记录 ===")
    
    # 初始化日志系统
    config = ConfigManager()
    Logger.initialize(config)
    
    # 使用类方法记录日志
    Logger.debug("这是调试消息", logger_name="example")
    Logger.info("这是信息消息", logger_name="example")
    Logger.warning("这是警告消息", logger_name="example")
    Logger.error("这是错误消息", logger_name="example")
    Logger.critical("这是严重错误消息", logger_name="example")


def example_convenience_functions():
    """示例2：使用便捷函数"""
    print("\n=== 示例2：使用便捷函数 ===")
    
    # 使用便捷函数（更简洁）
    info("应用启动成功")
    warning("配置文件使用默认值")
    error("连接数据库失败")


def example_extra_fields():
    """示例3：添加额外字段"""
    print("\n=== 示例3：添加额外字段 ===")
    
    # 记录带额外字段的日志
    Logger.info(
        "用户登录成功",
        logger_name="auth",
        user_id="user123",
        ip_address="192.168.1.100",
        login_method="password"
    )
    
    Logger.error(
        "API 调用失败",
        logger_name="api",
        endpoint="/api/users",
        status_code=500,
        response_time=1.5
    )


def example_context_manager():
    """示例4：使用上下文管理器"""
    print("\n=== 示例4：使用上下文管理器 ===")
    
    # 使用上下文管理器自动添加上下文信息
    with LogContext(request_id="req-abc-123", user_id="user-456"):
        info("开始处理请求")
        info("验证用户权限")
        info("执行业务逻辑")
        info("请求处理完成")
        # 所有日志都会自动包含 request_id 和 user_id


def example_nested_context():
    """示例5：嵌套上下文"""
    print("\n=== 示例5：嵌套上下文 ===")
    
    with LogContext(request_id="req-xyz-789"):
        info("收到请求")
        
        with LogContext(operation="database_query"):
            info("执行数据库查询")
            # 日志包含 request_id 和 operation
        
        with LogContext(operation="cache_update"):
            info("更新缓存")
            # 日志包含 request_id 和 operation（不同的值）
        
        info("请求完成")
        # 只包含 request_id


def example_exception_logging():
    """示例6：异常日志"""
    print("\n=== 示例6：异常日志 ===")
    
    try:
        # 模拟一个错误
        result = 10 / 0
    except ZeroDivisionError:
        # 记录异常（包含堆栈跟踪）
        Logger.exception("计算过程中发生错误", logger_name="calculator")


def example_get_logger():
    """示例7：获取日志记录器实例"""
    print("\n=== 示例7：获取日志记录器实例 ===")
    
    # 获取特定模块的日志记录器
    logger = get_logger("my_module")
    
    # 使用标准 logging 接口
    logger.info("使用标准 logging 接口")
    logger.warning("这样可以与其他库兼容")


def example_real_world_scenario():
    """示例8：真实场景 - 内容生成流程"""
    print("\n=== 示例8：真实场景 - 内容生成流程 ===")
    
    # 模拟内容生成流程
    task_id = "task-001"
    user_id = "user-789"
    
    with LogContext(task_id=task_id, user_id=user_id):
        info("开始生成内容")
        
        # 步骤1：读取输入
        try:
            info("读取输入文件", file_path="input/content.txt")
            # 模拟读取
        except Exception as e:
            error("读取输入文件失败", error=str(e))
            return
        
        # 步骤2：调用 AI API
        with LogContext(step="ai_generation"):
            info("调用 AI API 生成文案")
            Logger.info(
                "API 调用成功",
                logger_name="api",
                model="qwen-plus",
                tokens=150,
                duration=2.3
            )
        
        # 步骤3：生成图片
        with LogContext(step="image_generation"):
            info("开始生成图片")
            for i in range(3):
                Logger.info(
                    "生成图片",
                    logger_name="image",
                    image_index=i+1,
                    prompt="老北京胡同",
                    status="success"
                )
        
        # 步骤4：保存结果
        with LogContext(step="save_results"):
            info("保存生成结果", output_path="output/result.xlsx")
        
        info("内容生成完成", total_time=5.8)


def main():
    """主函数"""
    print("=" * 60)
    print("Logger 模块使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_basic_logging()
    example_convenience_functions()
    example_extra_fields()
    example_context_manager()
    example_nested_context()
    example_exception_logging()
    example_get_logger()
    example_real_world_scenario()
    
    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("日志已保存到: logs/app.log")
    print("=" * 60)


if __name__ == "__main__":
    main()
