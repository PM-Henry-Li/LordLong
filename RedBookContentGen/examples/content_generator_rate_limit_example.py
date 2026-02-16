#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容生成器速率限制使用示例

演示如何使用 RedBookContentGenerator 的速率限制功能
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.content_generator import RedBookContentGenerator
from src.core.config_manager import ConfigManager
from src.core.logger import Logger


def example_1_basic_rate_limit():
    """示例 1: 基本速率限制使用"""
    print("=" * 60)
    print("示例 1: 基本速率限制使用")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager("config/config.json")
    
    # 创建内容生成器（自动启用速率限制）
    generator = RedBookContentGenerator(config_manager=config_manager)
    
    # 查看速率限制状态
    rate_limit_stats = generator.get_rate_limit_stats()
    if rate_limit_stats:
        print("\n✅ 速率限制已启用")
        print(f"RPM 配置: {rate_limit_stats['rpm']['rate']:.1f} 请求/秒")
        print(f"RPM 容量: {rate_limit_stats['rpm']['capacity']:.0f} 令牌")
        print(f"TPM 配置: {rate_limit_stats['tpm']['rate']:.1f} 令牌/秒")
        print(f"TPM 容量: {rate_limit_stats['tpm']['capacity']:.0f} 令牌")
    else:
        print("\n❌ 速率限制未启用")
    
    print("\n" + "=" * 60)


def example_2_check_available_tokens():
    """示例 2: 检查可用令牌数"""
    print("=" * 60)
    print("示例 2: 检查可用令牌数")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    generator = RedBookContentGenerator(config_manager=config_manager)
    
    # 获取速率限制统计
    stats = generator.get_rate_limit_stats()
    
    if stats:
        print("\n当前可用令牌:")
        print(f"  RPM: {stats['rpm']['available_tokens']:.2f} / {stats['rpm']['capacity']:.0f}")
        print(f"  TPM: {stats['tpm']['available_tokens']:.2f} / {stats['tpm']['capacity']:.0f}")
    
    print("\n" + "=" * 60)


def example_3_simulate_api_calls():
    """示例 3: 模拟多次 API 调用"""
    print("=" * 60)
    print("示例 3: 模拟多次 API 调用（观察令牌消耗）")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    generator = RedBookContentGenerator(config_manager=config_manager)
    
    if not generator._rate_limit_enabled:
        print("\n⚠️  速率限制未启用，跳过此示例")
        print("=" * 60)
        return
    
    print("\n初始状态:")
    stats = generator.get_rate_limit_stats()
    print(f"  RPM 可用令牌: {stats['rpm']['available_tokens']:.2f}")
    print(f"  TPM 可用令牌: {stats['tpm']['available_tokens']:.2f}")
    
    # 模拟消耗令牌
    print("\n模拟 3 次 API 调用...")
    for i in range(3):
        # 消耗 1 个 RPM 令牌
        success = generator.rpm_limiter.acquire(tokens=1)
        if success:
            print(f"  第 {i+1} 次调用: ✅ 获取 RPM 令牌成功")
        else:
            print(f"  第 {i+1} 次调用: ❌ RPM 令牌不足，需要等待")
        
        # 消耗一些 TPM 令牌（模拟 token 使用）
        estimated_tokens = 1000
        generator.tpm_limiter.acquire(tokens=estimated_tokens)
        
        # 等待一小段时间
        time.sleep(0.1)
    
    print("\n调用后状态:")
    stats = generator.get_rate_limit_stats()
    print(f"  RPM 可用令牌: {stats['rpm']['available_tokens']:.2f}")
    print(f"  TPM 可用令牌: {stats['tpm']['available_tokens']:.2f}")
    
    print("\n" + "=" * 60)


def example_4_rate_limit_recovery():
    """示例 4: 观察令牌恢复"""
    print("=" * 60)
    print("示例 4: 观察令牌恢复")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    generator = RedBookContentGenerator(config_manager=config_manager)
    
    if not generator._rate_limit_enabled:
        print("\n⚠️  速率限制未启用，跳过此示例")
        print("=" * 60)
        return
    
    # 消耗一些令牌
    print("\n消耗 10 个 RPM 令牌...")
    generator.rpm_limiter.acquire(tokens=10)
    
    stats = generator.get_rate_limit_stats()
    print(f"消耗后: {stats['rpm']['available_tokens']:.2f} 令牌")
    
    # 等待令牌恢复
    print("\n等待 2 秒，观察令牌恢复...")
    time.sleep(2)
    
    stats = generator.get_rate_limit_stats()
    print(f"恢复后: {stats['rpm']['available_tokens']:.2f} 令牌")
    print(f"恢复速率: {stats['rpm']['rate']:.2f} 令牌/秒")
    
    print("\n" + "=" * 60)


def example_5_custom_rate_limit_config():
    """示例 5: 自定义速率限制配置"""
    print("=" * 60)
    print("示例 5: 自定义速率限制配置")
    print("=" * 60)
    
    # 创建自定义配置
    config_manager = ConfigManager("config/config.json")
    
    # 可以通过环境变量覆盖配置
    print("\n提示: 可以通过环境变量覆盖速率限制配置:")
    print("  export RATE_LIMIT_OPENAI_RPM=120")
    print("  export RATE_LIMIT_OPENAI_TPM=180000")
    
    # 或者在配置文件中修改
    print("\n或者在 config/config.json 中修改:")
    print('  "rate_limit": {')
    print('    "openai": {')
    print('      "enable_rate_limit": true,')
    print('      "requests_per_minute": 120,')
    print('      "tokens_per_minute": 180000')
    print('    }')
    print('  }')
    
    # 显示当前配置
    rpm = config_manager.get("rate_limit.openai.requests_per_minute", 60)
    tpm = config_manager.get("rate_limit.openai.tokens_per_minute", 90000)
    enabled = config_manager.get("rate_limit.openai.enable_rate_limit", True)
    
    print(f"\n当前配置:")
    print(f"  启用状态: {enabled}")
    print(f"  RPM: {rpm}")
    print(f"  TPM: {tpm}")
    
    print("\n" + "=" * 60)


def example_6_disable_rate_limit():
    """示例 6: 禁用速率限制"""
    print("=" * 60)
    print("示例 6: 禁用速率限制")
    print("=" * 60)
    
    print("\n如果需要禁用速率限制，可以在配置文件中设置:")
    print('  "rate_limit": {')
    print('    "openai": {')
    print('      "enable_rate_limit": false')
    print('    }')
    print('  }')
    
    print("\n或者通过环境变量:")
    print("  export RATE_LIMIT_OPENAI_ENABLE_RATE_LIMIT=false")
    
    print("\n⚠️  注意: 禁用速率限制可能导致超过 API 配额限制")
    
    print("\n" + "=" * 60)


def example_7_rate_limit_with_logging():
    """示例 7: 速率限制日志记录"""
    print("=" * 60)
    print("示例 7: 速率限制日志记录")
    print("=" * 60)
    
    config_manager = ConfigManager("config/config.json")
    
    # 设置日志级别为 DEBUG 以查看详细的速率限制日志
    print("\n提示: 设置日志级别为 DEBUG 可以查看详细的速率限制日志:")
    print('  "logging": {')
    print('    "level": "DEBUG"')
    print('  }')
    
    print("\n速率限制相关的日志包括:")
    print("  - 正在获取 RPM 令牌")
    print("  - ✅ 已获取 RPM 令牌")
    print("  - 正在获取 TPM 令牌")
    print("  - ✅ 已获取 TPM 令牌")
    print("  - 正在调用 OpenAI API")
    print("  - ✅ OpenAI API 调用成功")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("内容生成器速率限制使用示例")
    print("=" * 60)
    
    try:
        # 运行所有示例
        example_1_basic_rate_limit()
        print()
        
        example_2_check_available_tokens()
        print()
        
        example_3_simulate_api_calls()
        print()
        
        example_4_rate_limit_recovery()
        print()
        
        example_5_custom_rate_limit_config()
        print()
        
        example_6_disable_rate_limit()
        print()
        
        example_7_rate_limit_with_logging()
        print()
        
        print("=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
