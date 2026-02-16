#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置热重载使用示例

演示如何使用 ConfigManager 的热重载功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager


def example_manual_reload():
    """示例1: 手动重载配置"""
    print("=" * 60)
    print("示例1: 手动重载配置")
    print("=" * 60)
    
    # 创建配置管理器
    config = ConfigManager()
    
    print(f"当前模型: {config.get('openai_model')}")
    
    # 修改内存中的配置
    config.set('openai_model', 'qwen-turbo')
    print(f"修改后的模型: {config.get('openai_model')}")
    
    # 手动重载配置（从文件重新加载）
    print("\n手动重载配置...")
    config.reload()
    print(f"重载后的模型: {config.get('openai_model')}")
    print()


def example_auto_reload():
    """示例2: 自动重载配置"""
    print("=" * 60)
    print("示例2: 自动重载配置")
    print("=" * 60)
    
    # 创建配置管理器
    config = ConfigManager()
    
    print(f"当前模型: {config.get('openai_model')}")
    
    # 启动配置文件监控
    print("\n启动配置文件监控...")
    config.start_watching(check_interval=1.0)
    
    print("配置文件监控已启动，现在可以修改 config/config.json 文件")
    print("修改后配置会自动重新加载")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        # 持续监控
        while True:
            current_model = config.get('openai_model')
            print(f"当前模型: {current_model}", end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止监控...")
        config.stop_watching()
        print("监控已停止")
    print()


def example_reload_callback():
    """示例3: 使用重载回调"""
    print("=" * 60)
    print("示例3: 使用重载回调")
    print("=" * 60)
    
    # 创建配置管理器
    config = ConfigManager()
    
    # 定义回调函数
    def on_config_reload():
        """配置重载时的回调函数"""
        print("🔄 配置已重新加载！")
        print(f"   新的模型: {config.get('openai_model')}")
        print(f"   新的超时时间: {config.get('api.openai.timeout')}秒")
    
    # 注册回调
    config.register_reload_callback(on_config_reload)
    print("已注册重载回调函数\n")
    
    # 手动重载触发回调
    print("执行手动重载...")
    config.reload()
    
    # 取消注册回调
    print("\n取消注册回调...")
    config.unregister_reload_callback(on_config_reload)
    
    print("再次重载（不会触发回调）...")
    config.reload()
    print()


def example_multiple_callbacks():
    """示例4: 多个回调函数"""
    print("=" * 60)
    print("示例4: 多个回调函数")
    print("=" * 60)
    
    # 创建配置管理器
    config = ConfigManager()
    
    # 定义多个回调函数
    def log_reload():
        print("📝 日志: 配置已重载")
    
    def update_cache():
        print("🗑️  缓存: 清空旧缓存")
    
    def notify_services():
        print("📢 通知: 通知相关服务配置已更新")
    
    # 注册多个回调
    config.register_reload_callback(log_reload)
    config.register_reload_callback(update_cache)
    config.register_reload_callback(notify_services)
    
    print("已注册3个回调函数\n")
    
    # 重载配置，触发所有回调
    print("执行重载...")
    config.reload()
    print()


def example_thread_safe():
    """示例5: 线程安全的配置访问"""
    print("=" * 60)
    print("示例5: 线程安全的配置访问")
    print("=" * 60)
    
    import threading
    
    # 创建配置管理器
    config = ConfigManager()
    
    def reader_thread(thread_id: int):
        """读取配置的线程"""
        for i in range(5):
            model = config.get('openai_model')
            timeout = config.get('api.openai.timeout')
            print(f"线程{thread_id}: 读取配置 - 模型={model}, 超时={timeout}秒")
            time.sleep(0.1)
    
    def writer_thread():
        """修改配置的线程"""
        for i in range(3):
            time.sleep(0.15)
            config.set('api.openai.timeout', 30 + i * 10)
            print(f"写入线程: 更新超时时间为 {30 + i * 10}秒")
    
    # 创建多个线程
    threads = []
    for i in range(3):
        t = threading.Thread(target=reader_thread, args=(i+1,))
        threads.append(t)
    
    threads.append(threading.Thread(target=writer_thread))
    
    # 启动所有线程
    print("启动多个线程并发访问配置...\n")
    for t in threads:
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print("\n所有线程已完成，配置访问是线程安全的")
    print()


def main():
    """主函数"""
    print("\n配置热重载功能示例\n")
    
    # 示例1: 手动重载
    example_manual_reload()
    
    # 示例3: 重载回调
    example_reload_callback()
    
    # 示例4: 多个回调
    example_multiple_callbacks()
    
    # 示例5: 线程安全
    example_thread_safe()
    
    # 示例2: 自动重载（需要用户交互，放在最后）
    print("是否要运行自动重载示例？（需要手动修改配置文件）")
    print("输入 'y' 运行，其他键跳过: ", end='')
    
    try:
        choice = input().strip().lower()
        if choice == 'y':
            example_auto_reload()
    except (EOFError, KeyboardInterrupt):
        print("\n跳过自动重载示例")
    
    print("\n所有示例运行完成！")


if __name__ == "__main__":
    main()
