#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制器使用示例

演示如何使用 RateLimiter 和 MultiRateLimiter 进行 API 速率限制
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.rate_limiter import RateLimiter, MultiRateLimiter


def example_basic_usage():
    """示例 1: 基本使用"""
    print("\n" + "=" * 70)
    print("示例 1: 基本使用")
    print("=" * 70)
    
    # 创建速率限制器：每秒生成 2 个令牌，容量为 5
    limiter = RateLimiter(rate=2, capacity=5)
    
    print(f"初始状态: {limiter}")
    print(f"可用令牌数: {limiter.get_available_tokens():.2f}")
    
    # 尝试获取令牌
    print("\n尝试获取 3 个令牌...")
    if limiter.acquire(3):
        print("✅ 成功获取 3 个令牌")
        print(f"剩余令牌: {limiter.get_available_tokens():.2f}")
    else:
        print("❌ 令牌不足")
    
    # 再次尝试获取令牌
    print("\n尝试获取 3 个令牌...")
    if limiter.acquire(3):
        print("✅ 成功获取 3 个令牌")
    else:
        print("❌ 令牌不足")
        print(f"当前令牌: {limiter.get_available_tokens():.2f}")


def example_wait_for_token():
    """示例 2: 等待获取令牌"""
    print("\n" + "=" * 70)
    print("示例 2: 等待获取令牌")
    print("=" * 70)
    
    # 创建速率限制器：每秒生成 5 个令牌
    limiter = RateLimiter(rate=5, capacity=10)
    
    # 消耗所有令牌
    limiter.acquire(10)
    print(f"已消耗所有令牌，当前令牌: {limiter.get_available_tokens():.2f}")
    
    # 等待获取令牌
    print("\n等待获取 2 个令牌...")
    start = time.time()
    
    if limiter.wait_for_token(2, timeout=2.0):
        elapsed = time.time() - start
        print(f"✅ 成功获取令牌，等待时间: {elapsed:.2f} 秒")
        print(f"剩余令牌: {limiter.get_available_tokens():.2f}")
    else:
        print("❌ 获取令牌超时")


def example_api_rate_limiting():
    """示例 3: API 速率限制"""
    print("\n" + "=" * 70)
    print("示例 3: 模拟 API 调用速率限制")
    print("=" * 70)
    
    # 创建速率限制器：每秒最多 3 次请求
    limiter = RateLimiter(rate=3, capacity=3)
    
    def call_api(api_name: str):
        """模拟 API 调用"""
        if limiter.acquire(1):
            print(f"✅ 调用 {api_name} 成功")
            return True
        else:
            print(f"⏳ {api_name} 被限流，等待令牌...")
            limiter.wait_for_token(1)
            print(f"✅ 调用 {api_name} 成功")
            return True
    
    # 快速连续调用 API
    print("\n快速连续调用 5 次 API:")
    for i in range(5):
        call_api(f"API-{i+1}")
        time.sleep(0.1)  # 模拟一些处理时间


def example_burst_traffic():
    """示例 4: 突发流量处理"""
    print("\n" + "=" * 70)
    print("示例 4: 突发流量处理")
    print("=" * 70)
    
    # 创建速率限制器：每秒生成 2 个令牌，但容量为 10
    # 这允许短时间内处理突发流量
    limiter = RateLimiter(rate=2, capacity=10)
    
    print(f"速率: {limiter.get_rate()}/秒")
    print(f"容量: {limiter.get_capacity()}")
    print(f"初始令牌: {limiter.get_available_tokens():.2f}")
    
    # 突发请求：一次性处理 8 个请求
    print("\n处理突发流量（8 个请求）:")
    if limiter.acquire(8):
        print("✅ 成功处理 8 个请求")
        print(f"剩余令牌: {limiter.get_available_tokens():.2f}")
    
    # 尝试再次处理请求
    print("\n尝试再次处理 3 个请求:")
    if limiter.acquire(3):
        print("✅ 成功处理")
    else:
        print("❌ 令牌不足，需要等待")
        print(f"当前令牌: {limiter.get_available_tokens():.2f}")
        
        # 等待令牌补充
        print("\n等待 2 秒，令牌补充中...")
        time.sleep(2)
        print(f"补充后令牌: {limiter.get_available_tokens():.2f}")


def example_multi_rate_limiter():
    """示例 5: 多速率限制器"""
    print("\n" + "=" * 70)
    print("示例 5: 管理多个 API 的速率限制")
    print("=" * 70)
    
    # 创建多速率限制器
    multi = MultiRateLimiter()
    
    # 为不同的 API 添加限制器
    multi.add_limiter("openai", rate=60, capacity=60)  # 每秒 60 次
    multi.add_limiter("image", rate=10, capacity=10)   # 每秒 10 次
    multi.add_limiter("search", rate=30, capacity=30)  # 每秒 30 次
    
    print(f"已添加的限制器: {multi.list_limiters()}")
    
    # 模拟调用不同的 API
    print("\n模拟 API 调用:")
    
    # 调用 OpenAI API
    if multi.acquire("openai", 5):
        print("✅ OpenAI API: 成功调用 5 次")
        limiter = multi.get_limiter("openai")
        print(f"   剩余令牌: {limiter.get_available_tokens():.2f}")
    
    # 调用图片生成 API
    if multi.acquire("image", 3):
        print("✅ 图片生成 API: 成功调用 3 次")
        limiter = multi.get_limiter("image")
        print(f"   剩余令牌: {limiter.get_available_tokens():.2f}")
    
    # 调用搜索 API
    if multi.acquire("search", 10):
        print("✅ 搜索 API: 成功调用 10 次")
        limiter = multi.get_limiter("search")
        print(f"   剩余令牌: {limiter.get_available_tokens():.2f}")


def example_with_config():
    """示例 6: 结合配置管理器使用"""
    print("\n" + "=" * 70)
    print("示例 6: 结合配置管理器使用")
    print("=" * 70)
    
    try:
        from src.core.config_manager import ConfigManager
        
        # 加载配置
        config = ConfigManager()
        
        # 从配置创建速率限制器
        openai_rpm = config.get("rate_limit.openai.requests_per_minute", 60)
        image_rpm = config.get("rate_limit.image.requests_per_minute", 10)
        
        print(f"OpenAI API 速率限制: {openai_rpm} 请求/分钟")
        print(f"图片生成 API 速率限制: {image_rpm} 请求/分钟")
        
        # 创建多速率限制器
        multi = MultiRateLimiter()
        
        # 将每分钟的速率转换为每秒
        multi.add_limiter("openai", rate=openai_rpm/60, capacity=openai_rpm/60)
        multi.add_limiter("image", rate=image_rpm/60, capacity=image_rpm/60)
        
        print(f"\n已创建限制器: {multi.list_limiters()}")
        
        # 模拟使用
        print("\n模拟 API 调用:")
        if multi.acquire("openai", 1):
            print("✅ OpenAI API 调用成功")
        
        if multi.acquire("image", 1):
            print("✅ 图片生成 API 调用成功")
        
    except ImportError:
        print("⚠️  未找到 ConfigManager，跳过此示例")


def example_reset():
    """示例 7: 重置速率限制器"""
    print("\n" + "=" * 70)
    print("示例 7: 重置速率限制器")
    print("=" * 70)
    
    limiter = RateLimiter(rate=5, capacity=10)
    
    # 消耗一些令牌
    limiter.acquire(7)
    print(f"消耗 7 个令牌后: {limiter.get_available_tokens():.2f}")
    
    # 重置
    print("\n重置速率限制器...")
    limiter.reset()
    print(f"重置后: {limiter.get_available_tokens():.2f}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("速率限制器使用示例")
    print("=" * 70)
    
    try:
        example_basic_usage()
        example_wait_for_token()
        example_api_rate_limiting()
        example_burst_traffic()
        example_multi_rate_limiter()
        example_with_config()
        example_reset()
        
        print("\n" + "=" * 70)
        print("✅ 所有示例运行完成")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
