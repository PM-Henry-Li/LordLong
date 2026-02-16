#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速率限制策略使用示例

演示如何使用不同的限流策略
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.rate_limiter import (
    RateLimiter,
    FixedWindowRateLimiter,
    SlidingWindowRateLimiter,
    LeakyBucketRateLimiter,
    create_rate_limiter,
    MultiRateLimiter
)


def example_token_bucket():
    """示例1：令牌桶算法 - 允许突发流量"""
    print("\n" + "=" * 70)
    print("示例1：令牌桶算法（Token Bucket）")
    print("=" * 70)
    
    # 创建令牌桶限制器：每秒生成5个令牌，容量10
    limiter = RateLimiter(rate=5, capacity=10)
    
    print(f"初始令牌数: {limiter.get_available_tokens():.2f}")
    
    # 突发请求：一次性消耗10个令牌
    print("\n尝试突发请求（一次性获取10个令牌）...")
    if limiter.acquire(10):
        print("✅ 突发请求成功！令牌桶允许突发流量")
        print(f"剩余令牌: {limiter.get_available_tokens():.2f}")
    
    # 等待令牌补充
    print("\n等待1秒，令牌自动补充...")
    time.sleep(1)
    print(f"补充后令牌数: {limiter.get_available_tokens():.2f}")


def example_fixed_window():
    """示例2：固定窗口算法 - 简单高效"""
    print("\n" + "=" * 70)
    print("示例2：固定窗口算法（Fixed Window）")
    print("=" * 70)
    
    # 创建固定窗口限制器：每5秒允许10次请求
    limiter = FixedWindowRateLimiter(rate=10, window_size=5)
    
    print(f"窗口配额: 10次/5秒")
    print(f"当前可用: {limiter.get_available_tokens():.0f}次")
    
    # 快速发送5次请求
    print("\n快速发送5次请求...")
    for i in range(5):
        if limiter.acquire(1):
            print(f"  请求 {i+1}: ✅ 通过")
    
    print(f"剩余配额: {limiter.get_available_tokens():.0f}次")
    
    # 等待窗口重置
    print("\n等待窗口重置（5秒）...")
    time.sleep(5.1)
    print(f"窗口重置后配额: {limiter.get_available_tokens():.0f}次")


def example_sliding_window():
    """示例3：滑动窗口算法 - 精确控制"""
    print("\n" + "=" * 70)
    print("示例3：滑动窗口算法（Sliding Window）")
    print("=" * 70)
    
    # 创建滑动窗口限制器：每5秒允许10次请求
    limiter = SlidingWindowRateLimiter(rate=10, window_size=5)
    
    print(f"窗口配额: 10次/5秒（滑动窗口，无临界问题）")
    print(f"当前可用: {limiter.get_available_tokens():.0f}次")
    
    # 发送5次请求
    print("\n发送5次请求...")
    for i in range(5):
        if limiter.acquire(1):
            print(f"  请求 {i+1}: ✅ 通过")
    
    print(f"剩余配额: {limiter.get_available_tokens():.0f}次")
    
    # 等待部分请求过期
    print("\n等待3秒（部分请求过期）...")
    time.sleep(3)
    print(f"3秒后可用配额: {limiter.get_available_tokens():.0f}次")
    print("（注意：滑动窗口会精确统计最近5秒内的请求）")


def example_leaky_bucket():
    """示例4：漏桶算法 - 平滑流量"""
    print("\n" + "=" * 70)
    print("示例4：漏桶算法（Leaky Bucket）")
    print("=" * 70)
    
    # 创建漏桶限制器：每秒处理5个请求，容量10
    limiter = LeakyBucketRateLimiter(rate=5, capacity=10)
    
    print(f"处理速率: 5次/秒")
    print(f"桶容量: 10")
    print(f"当前队列: {limiter.get_queue_size()}")
    
    # 快速发送10次请求（填满桶）
    print("\n快速发送10次请求（填满桶）...")
    for i in range(10):
        if limiter.acquire(1):
            print(f"  请求 {i+1}: ✅ 加入队列")
    
    print(f"队列大小: {limiter.get_queue_size()}")
    print(f"剩余空间: {limiter.get_available_tokens():.0f}")
    
    # 尝试再发送请求（应该失败）
    print("\n尝试再发送请求...")
    if not limiter.acquire(1):
        print("  ❌ 请求被拒绝（桶已满）")
    
    # 等待漏桶处理
    print("\n等待1秒（漏桶处理约5个请求）...")
    time.sleep(1)
    print(f"处理后队列大小: {limiter.get_queue_size()}")
    print(f"剩余空间: {limiter.get_available_tokens():.0f}")


def example_factory_function():
    """示例5：使用工厂函数创建限制器"""
    print("\n" + "=" * 70)
    print("示例5：使用工厂函数创建限制器")
    print("=" * 70)
    
    # 使用工厂函数创建不同策略的限制器
    strategies = [
        ("token_bucket", {"rate": 10, "capacity": 20}),
        ("fixed_window", {"rate": 100, "window_size": 60}),
        ("sliding_window", {"rate": 100, "window_size": 60}),
        ("leaky_bucket", {"rate": 10, "capacity": 20})
    ]
    
    for strategy, params in strategies:
        limiter = create_rate_limiter(strategy, **params)
        print(f"\n{strategy:20s}: {limiter}")


def example_multi_rate_limiter():
    """示例6：多速率限制器 - 管理多个限制器"""
    print("\n" + "=" * 70)
    print("示例6：多速率限制器（Multi Rate Limiter）")
    print("=" * 70)
    
    # 创建多速率限制器
    multi = MultiRateLimiter()
    
    # 为不同的 API 配置不同的限流策略
    print("\n配置不同的限流策略:")
    
    # OpenAI API：使用滑动窗口，精确控制
    multi.add_limiter(
        name="openai_api",
        rate=60,
        window_size=60,
        strategy="sliding_window"
    )
    print("  - openai_api: 滑动窗口, 60次/分钟")
    
    # 图片 API：使用令牌桶，允许突发
    multi.add_limiter(
        name="image_api",
        rate=10,
        capacity=20,
        strategy="token_bucket"
    )
    print("  - image_api: 令牌桶, 10次/秒, 容量20")
    
    # Web API：使用固定窗口，简单高效
    multi.add_limiter(
        name="web_api",
        rate=100,
        window_size=60,
        strategy="fixed_window"
    )
    print("  - web_api: 固定窗口, 100次/分钟")
    
    # 使用不同的限制器
    print("\n测试不同的限制器:")
    
    if multi.acquire("openai_api", 1):
        print("  ✅ OpenAI API 请求通过")
        openai_limiter = multi.get_limiter("openai_api")
        print(f"     剩余配额: {openai_limiter.get_available_tokens():.0f}")
    
    if multi.acquire("image_api", 5):
        print("  ✅ 图片 API 请求通过（突发5次）")
        image_limiter = multi.get_limiter("image_api")
        print(f"     剩余令牌: {image_limiter.get_available_tokens():.2f}")
    
    if multi.acquire("web_api", 1):
        print("  ✅ Web API 请求通过")
        web_limiter = multi.get_limiter("web_api")
        print(f"     剩余配额: {web_limiter.get_available_tokens():.0f}")
    
    # 列出所有限制器
    print(f"\n所有限制器: {multi.list_limiters()}")


def example_comparison():
    """示例7：策略对比 - 突发流量处理"""
    print("\n" + "=" * 70)
    print("示例7：策略对比 - 突发流量处理")
    print("=" * 70)
    
    # 创建不同策略的限制器（相同的速率限制）
    token_bucket = create_rate_limiter("token_bucket", rate=5, capacity=10)
    leaky_bucket = create_rate_limiter("leaky_bucket", rate=5, capacity=10)
    
    print("测试场景：尝试突发10次请求")
    print(f"速率限制：5次/秒，容量10\n")
    
    # 令牌桶：允许突发
    print("令牌桶算法:")
    if token_bucket.acquire(10):
        print("  ✅ 突发10次请求成功（允许突发）")
        print(f"  剩余令牌: {token_bucket.get_available_tokens():.2f}")
    
    # 漏桶：不允许突发（但可以排队）
    print("\n漏桶算法:")
    if leaky_bucket.acquire(10):
        print("  ✅ 10次请求加入队列（将以固定速率处理）")
        print(f"  队列大小: {leaky_bucket.get_queue_size()}")
        print(f"  剩余空间: {leaky_bucket.get_available_tokens():.0f}")
    
    print("\n结论:")
    print("  - 令牌桶：允许突发流量，适合需要弹性的场景")
    print("  - 漏桶：平滑流量，适合需要严格控制的场景")


def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("速率限制策略使用示例")
    print("=" * 70)
    
    try:
        # 运行所有示例
        example_token_bucket()
        example_fixed_window()
        example_sliding_window()
        example_leaky_bucket()
        example_factory_function()
        example_multi_rate_limiter()
        example_comparison()
        
        print("\n" + "=" * 70)
        print("✅ 所有示例运行完成！")
        print("=" * 70)
        print("\n详细文档请参考: docs/RATE_LIMITER_STRATEGIES.md")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
