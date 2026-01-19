#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 演示如何使用需求打分器
"""

from requirement_scorer import RequirementScorer

def main():
    """快速测试示例"""
    
    # 创建打分器，设置可用总分为1000
    scorer = RequirementScorer(total_score=1000)
    
    # 方式1: 从CSV文件加载
    print("=" * 60)
    print("示例1: 从CSV文件加载数据")
    print("=" * 60)
    try:
        scorer.load_from_csv('requirements_example.csv')
        print(f"✓ 成功加载 {len(scorer.requirements)} 个需求")
        
        # 生成报告
        report = scorer.generate_report('output/test_csv_report.md')
        print("\n报告预览（前500字符）:")
        print(report[:500] + "...")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    # 方式2: 从JSON文件加载
    print("\n" + "=" * 60)
    print("示例2: 从JSON文件加载数据")
    print("=" * 60)
    try:
        scorer2 = RequirementScorer(total_score=1000)
        scorer2.load_from_json('requirements_example.json')
        print(f"✓ 成功加载 {len(scorer2.requirements)} 个需求")
        
        # 生成报告
        report2 = scorer2.generate_report('output/test_json_report.md')
        print("\n报告预览（前500字符）:")
        print(report2[:500] + "...")
    except Exception as e:
        print(f"✗ 错误: {e}")
    
    # 方式3: 手动添加需求
    print("\n" + "=" * 60)
    print("示例3: 手动添加需求")
    print("=" * 60)
    scorer3 = RequirementScorer(total_score=500)
    
    # 添加一些需求
    scorer3.add_requirement({
        'name': '手动添加-考核落地项',
        'business_line': '考研',
        'category': '考核落地项',
        'quarter_plan': '本季度',
        'status': '开发中',
        'is_fault': False,
        'related_projects': 0
    })
    
    scorer3.add_requirement({
        'name': '手动添加-故障需求',
        'business_line': '四六级',
        'category': '其他需求',
        'quarter_plan': '未进入',
        'status': '尚未启动',
        'is_fault': True,  # X类需求
        'related_projects': 0
    })
    
    print(f"✓ 手动添加了 {len(scorer3.requirements)} 个需求")
    
    # 生成报告
    report3 = scorer3.generate_report('output/test_manual_report.md')
    print("\n报告预览（前500字符）:")
    print(report3[:500] + "...")
    
    print("\n" + "=" * 60)
    print("所有测试完成！请查看 output/ 目录下的报告文件")
    print("=" * 60)

if __name__ == '__main__':
    main()
