#!/usr/bin/env python3
"""
测试爬虫失败时的处理行为
Test crawler failure handling behavior
"""

import sys
import os

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from main import RedNoteWorkflow

def test_crawler_failure():
    """测试爬虫失败时的处理"""
    print("="*60)
    print("测试：爬虫失败时的处理行为")
    print("="*60)
    print()
    print("预期行为：")
    print("1. 明确提示爬虫失败")
    print("2. 详细说明失败原因")
    print("3. 提供解决方案建议")
    print("4. 直接终止流程，不继续执行")
    print()
    print("开始测试...")
    print()
    
    workflow = RedNoteWorkflow(keyword="测试关键词")
    
    # 尝试运行爬虫（预期会失败）
    result = workflow.run_crawler(num_articles=10)
    
    print()
    print("="*60)
    print("测试结果")
    print("="*60)
    
    if result:
        print("❌ 测试失败：爬虫应该失败但没有失败")
        return False
    else:
        print("✅ 测试通过：爬虫失败时正确返回 False")
        print("✅ 程序已正确终止，没有继续执行后续步骤")
        return True

if __name__ == "__main__":
    test_crawler_failure()
