#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证文字清理功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.image_generator import ImageGenerator


def test_clean_text():
    gen = ImageGenerator(config_path="config/config.json")

    test_cases = [
        ("n皇帝登基即位", "皇帝登基即位"),
        ("处理。n每", "处理。每"),
        ("n 作为整个紫禁城", "作为整个紫禁城"),
        ("测试。n", "测试。"),
        ("n", ""),
        ("nn", ""),
        ("n ", ""),
        ("n\n皇帝", "皇帝"),
        ("正常的nba", "正常的nba"),  # 不应误删正常的 n
        ("Sunlight", "Sunlight"),  # 不应误删单词中的 n
        ("建极绥猷", "建极绥猷"),
    ]

    success_count = 0
    for original, expected in test_cases:
        cleaned = gen.clean_text_for_display(original)
        if cleaned == expected:
            print(f"✅ PASS: [{repr(original)}] -> [{repr(cleaned)}]")
            success_count += 1
        else:
            print(f"❌ FAIL: [{repr(original)}] Expected [{repr(expected)}], but got [{repr(cleaned)}]")

    print(f"\nResult: {success_count}/{len(test_cases)} passed.")


if __name__ == "__main__":
    test_clean_text()
