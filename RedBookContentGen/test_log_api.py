#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志查询 API
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_log_stats():
    """测试日志统计 API"""
    print("📊 测试日志统计 API...")
    try:
        response = requests.get(f"{BASE_URL}/api/logs/stats")
        data = response.json()
        
        if data.get('success'):
            stats = data.get('stats', {})
            print(f"  ✅ 总日志数: {stats.get('total')}")
            print(f"  ✅ 错误数: {stats.get('error')}")
            print(f"  ✅ 警告数: {stats.get('warning')}")
            print(f"  ✅ 今日日志: {stats.get('today')}")
        else:
            print(f"  ❌ 失败: {data.get('error')}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

def test_log_loggers():
    """测试日志来源 API"""
    print("\n📝 测试日志来源 API...")
    try:
        response = requests.get(f"{BASE_URL}/api/logs/loggers")
        data = response.json()
        
        if data.get('success'):
            loggers = data.get('loggers', [])
            print(f"  ✅ 找到 {len(loggers)} 个日志来源:")
            for logger in loggers[:5]:
                print(f"    - {logger}")
            if len(loggers) > 5:
                print(f"    ... 还有 {len(loggers) - 5} 个")
        else:
            print(f"  ❌ 失败: {data.get('error')}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")

def test_log_search():
    """测试日志搜索 API"""
    print("\n🔍 测试日志搜索 API...")
    try:
        # 测试基本搜索
        response = requests.get(f"{BASE_URL}/api/logs/search?page=1&page_size=5")
        data = response.json()
        
        if data.get('success'):
            logs = data.get('logs', [])
            total = data.get('total', 0)
            print(f"  ✅ 找到 {total} 条日志，显示前 {len(logs)} 条:")
            for log in logs[:3]:
                print(f"    [{log.get('level')}] {log.get('logger')}: {log.get('message')[:50]}")
        else:
            print(f"  ❌ 失败: {data.get('error')}")
        
        # 测试级别过滤
        print("\n  测试级别过滤 (ERROR)...")
        response = requests.get(f"{BASE_URL}/api/logs/search?level=ERROR&page_size=5")
        data = response.json()
        
        if data.get('success'):
            logs = data.get('logs', [])
            print(f"  ✅ 找到 {len(logs)} 条 ERROR 日志")
        else:
            print(f"  ❌ 失败: {data.get('error')}")
        
        # 测试关键词搜索
        print("\n  测试关键词搜索 (生成)...")
        response = requests.get(f"{BASE_URL}/api/logs/search?keyword=生成&page_size=5")
        data = response.json()
        
        if data.get('success'):
            logs = data.get('logs', [])
            print(f"  ✅ 找到 {len(logs)} 条包含'生成'的日志")
        else:
            print(f"  ❌ 失败: {data.get('error')}")
    
    except Exception as e:
        print(f"  ❌ 异常: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("日志查询 API 测试")
    print("=" * 60)
    print("\n⚠️  请确保 Web 应用已启动 (python web_app.py)")
    print()
    
    test_log_stats()
    test_log_loggers()
    test_log_search()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
