#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成器速率限制使用示例

演示如何使用 ImageGenerator 的速率限制功能
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.image_generator import ImageGenerator
from src.core.config_manager import ConfigManager
import time


def example_1_basic_rate_limit():
    """示例 1: 基本速率限制使用"""
    print("=" * 60)
    print("示例 1: 基本速率限制使用")
    print("=" * 60)
    
    # 创建配置（启用速率限制）
    config = ConfigManager()
    
    # 创建图片生成器
    generator = ImageGenerator(config_manager=config)
    
    # 检查速率限制是否启用
    if generator._rate_limit_enabled:
        print("✅ 速率限制已启用")
        
        # 获取速率限制统计
        stats = generator.get_rate_limit_stats()
        print(f"\n速率限制配置:")
        print(f"  - 每分钟请求数: {stats['rpm']['capacity']}")
        print(f"  - 当前可用令牌: {stats['rpm']['available_tokens']}")
        print(f"  - 令牌生成速率: {stats['rpm']['rate']:.4f} 令牌/秒")
    else:
        print("⚠️  速率限制未启用")
    
    print()


def example_2_rate_limit_in_action():
    """示例 2: 速率限制实际效果"""
    print("=" * 60)
    print("示例 2: 速率限制实际效果")
    print("=" * 60)
    
    # 创建配置（启用速率限制，设置较低的 RPM）
    config = ConfigManager()
    
    # 创建图片生成器
    generator = ImageGenerator(config_manager=config)
    
    if not generator._rate_limit_enabled:
        print("⚠️  速率限制未启用，跳过此示例")
        return
    
    print(f"初始可用令牌: {generator.rpm_limiter.get_available_tokens():.2f}")
    
    # 模拟多次 API 调用
    num_calls = 3
    print(f"\n模拟 {num_calls} 次 API 调用...")
    
    for i in range(num_calls):
        # 获取令牌
        success = generator.rpm_limiter.acquire(tokens=1)
        
        if success:
            print(f"  调用 {i+1}: ✅ 成功获取令牌")
            print(f"    剩余令牌: {generator.rpm_limiter.get_available_tokens():.2f}")
        else:
            print(f"  调用 {i+1}: ❌ 令牌不足，需要等待")
            
            # 等待获取令牌
            print(f"    等待令牌...")
            generator.rpm_limiter.wait_for_token(tokens=1, timeout=10)
            print(f"    ✅ 获取到令牌")
            print(f"    剩余令牌: {generator.rpm_limiter.get_available_tokens():.2f}")
        
        # 模拟 API 调用耗时
        time.sleep(0.1)
    
    print()


def example_3_rate_limit_with_cache():
    """示例 3: 速率限制与缓存结合使用"""
    print("=" * 60)
    print("示例 3: 速率限制与缓存结合使用")
    print("=" * 60)
    
    # 创建配置（同时启用速率限制和缓存）
    config = ConfigManager()
    
    # 创建图片生成器
    generator = ImageGenerator(config_manager=config)
    
    if not generator._rate_limit_enabled:
        print("⚠️  速率限制未启用，跳过此示例")
        return
    
    if not generator._cache_enabled:
        print("⚠️  缓存未启用，跳过此示例")
        return
    
    print("✅ 速率限制和缓存均已启用")
    
    # 获取初始统计
    initial_tokens = generator.rpm_limiter.get_available_tokens()
    print(f"\n初始可用令牌: {initial_tokens:.2f}")
    
    # 模拟第一次调用（缓存未命中，消耗令牌）
    print("\n第一次调用（缓存未命中）:")
    print("  - 消耗 1 个令牌")
    generator.rpm_limiter.acquire(tokens=1)
    tokens_after_first = generator.rpm_limiter.get_available_tokens()
    print(f"  - 剩余令牌: {tokens_after_first:.2f}")
    
    # 模拟第二次调用（缓存命中，不消耗令牌）
    print("\n第二次调用（缓存命中）:")
    print("  - 从缓存获取，不消耗令牌")
    tokens_after_second = generator.rpm_limiter.get_available_tokens()
    print(f"  - 剩余令牌: {tokens_after_second:.2f}")
    
    # 验证令牌数
    if tokens_after_second >= tokens_after_first:
        print("\n✅ 缓存命中时没有消耗令牌（或令牌已恢复）")
    
    print()


def example_4_custom_rate_limit_config():
    """示例 4: 自定义速率限制配置"""
    print("=" * 60)
    print("示例 4: 自定义速率限制配置")
    print("=" * 60)
    
    # 方式 1: 通过配置文件
    print("方式 1: 通过配置文件")
    print("在 config/config.json 中设置:")
    print("""
{
  "rate_limit": {
    "image": {
      "enable_rate_limit": true,
      "requests_per_minute": 10
    }
  }
}
    """)
    
    # 方式 2: 通过环境变量
    print("\n方式 2: 通过环境变量")
    print("设置环境变量:")
    print("  export RATE_LIMIT_IMAGE_RPM=10")
    print("  export RATE_LIMIT_IMAGE_ENABLE_RATE_LIMIT=true")
    
    # 方式 3: 程序化配置
    print("\n方式 3: 程序化配置")
    print("在代码中设置:")
    print("""
config = ConfigManager()
config.set('rate_limit.image.enable_rate_limit', True)
config.set('rate_limit.image.requests_per_minute', 10)
generator = ImageGenerator(config_manager=config)
    """)
    
    print()


def example_5_rate_limit_monitoring():
    """示例 5: 速率限制监控"""
    print("=" * 60)
    print("示例 5: 速率限制监控")
    print("=" * 60)
    
    # 创建配置
    config = ConfigManager()
    
    # 创建图片生成器
    generator = ImageGenerator(config_manager=config)
    
    if not generator._rate_limit_enabled:
        print("⚠️  速率限制未启用，跳过此示例")
        return
    
    # 获取速率限制统计
    stats = generator.get_rate_limit_stats()
    
    print("速率限制统计信息:")
    print(f"  状态: {'启用' if stats['enabled'] else '禁用'}")
    print(f"\nRPM 限制器:")
    print(f"  - 可用令牌: {stats['rpm']['available_tokens']:.2f}")
    print(f"  - 桶容量: {stats['rpm']['capacity']:.2f}")
    print(f"  - 生成速率: {stats['rpm']['rate']:.4f} 令牌/秒")
    print(f"  - 每分钟请求数: {stats['rpm']['capacity']:.0f}")
    
    # 计算使用率
    usage_rate = (stats['rpm']['capacity'] - stats['rpm']['available_tokens']) / stats['rpm']['capacity'] * 100
    print(f"\n当前使用率: {usage_rate:.1f}%")
    
    # 预估等待时间
    if stats['rpm']['available_tokens'] < 1:
        wait_time = (1 - stats['rpm']['available_tokens']) / stats['rpm']['rate']
        print(f"预估等待时间: {wait_time:.2f} 秒")
    else:
        print("无需等待，可以立即发起请求")
    
    print()


def example_6_rate_limit_best_practices():
    """示例 6: 速率限制最佳实践"""
    print("=" * 60)
    print("示例 6: 速率限制最佳实践")
    print("=" * 60)
    
    print("最佳实践:")
    print()
    
    print("1. 合理设置 RPM 限制")
    print("   - 图片生成 API 通常较慢，建议设置为 10-20 RPM")
    print("   - 根据 API 配额和实际需求调整")
    print()
    
    print("2. 结合缓存使用")
    print("   - 启用缓存可以减少 API 调用次数")
    print("   - 缓存命中时不消耗速率限制令牌")
    print()
    
    print("3. 监控速率限制状态")
    print("   - 定期检查可用令牌数")
    print("   - 记录速率限制触发次数")
    print("   - 根据监控数据调整配置")
    print()
    
    print("4. 优雅处理超限情况")
    print("   - 使用 wait_for_token 等待令牌")
    print("   - 设置合理的超时时间")
    print("   - 向用户提供友好的提示信息")
    print()
    
    print("5. 批量处理优化")
    print("   - 使用并行生成时注意速率限制")
    print("   - 控制并发数量，避免令牌快速耗尽")
    print("   - 实现智能调度，平滑分配请求")
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("图片生成器速率限制使用示例")
    print("=" * 60 + "\n")
    
    # 运行所有示例
    example_1_basic_rate_limit()
    example_2_rate_limit_in_action()
    example_3_rate_limit_with_cache()
    example_4_custom_rate_limit_config()
    example_5_rate_limit_monitoring()
    example_6_rate_limit_best_practices()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
