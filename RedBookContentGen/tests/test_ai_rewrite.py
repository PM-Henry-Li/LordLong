#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI改写功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.image_generator import ImageGenerator


def test_ai_rewrite():
    """测试AI改写功能"""
    print("=" * 60)
    print("测试AI智能改写功能")
    print("=" * 60)

    # 初始化生成器
    gen = ImageGenerator(config_path="config/config.json")

    # 测试用例1: 超长文案
    long_text = "穿过红墙绿瓦,走进故宫的那一刻,仿佛穿越回了明清两代。耳边似乎还能听到皇帝登基时的钟鼓齐鸣。太和殿,俗称金銮殿,是故宫三大殿中南面的第一座,也是明清两代京城内最高的建筑。"
    max_chars = 40

    print(f"\n📝 测试用例1: 超长文案改写")
    print(f"原文({len(long_text)}字): {long_text}")
    print(f"目标长度: {max_chars}字以内")
    print(f"\n正在调用AI改写...")

    result = gen.rewrite_text_for_display(long_text, max_chars)

    print(f"\n✅ 改写结果({len(result)}字): {result}")
    print(f"长度符合要求: {'✓' if len(result) <= max_chars * 1.1 else '✗'}")

    # 测试用例2: 适中长度文案(无需改写)
    print(f"\n" + "=" * 60)
    print(f"📝 测试用例2: 适中长度文案(无需改写)")
    medium_text = "太和殿,故宫里的中华第一殿"
    print(f"原文({len(medium_text)}字): {medium_text}")

    result2 = gen.rewrite_text_for_display(medium_text, max_chars)
    print(f"结果: {result2}")
    print(f"是否改写: {'否(长度已符合)' if result2 == medium_text else '是'}")

    print(f"\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_ai_rewrite()
