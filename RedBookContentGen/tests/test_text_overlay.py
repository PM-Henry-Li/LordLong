#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文字叠加功能单元测试
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.image_generator import ImageGenerator


def test_wrap_text_simple():
    """测试简化的文字换行功能"""
    print("测试文字换行功能...")
    
    gen = ImageGenerator(config_path="config/config.json")
    
    # 创建测试图片和字体
    img = Image.new('RGB', (1024, 1365), color='white')
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                if path.endswith('.ttc'):
                    font = ImageFont.truetype(path, 60, index=0)
                else:
                    font = ImageFont.truetype(path, 60)
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
    
    # 测试用例
    test_cases = [
        ("短文本测试", 500),
        ("这是一个比较长的文本，需要测试换行功能是否正常工作，确保文字能够正确分割成多行显示。", 500),
        ("标点符号测试，。！？；：、", 500),
        ("单独标点，。！？", 500),
        ("非常长的文本" * 10, 500),
    ]
    
    for text, max_width in test_cases:
        print(f"\n测试文本: {text[:30]}...")
        lines = gen._wrap_text_simple(text, max_width, font, draw, max_lines=3)
        print(f"  结果: {len(lines)} 行")
        for i, line in enumerate(lines, 1):
            print(f"  行{i}: {line[:50]}")
            # 检查是否有单独标点
            if len(line.strip()) == 1 and line.strip() in ['。', '，', '！', '？']:
                print(f"  ⚠️  警告: 发现单独标点符号行")
    
    print("\n✅ 文字换行测试完成")


def test_smart_truncate_simple():
    """测试简化的智能截断功能"""
    print("\n测试智能截断功能...")
    
    gen = ImageGenerator(config_path="config/config.json")
    
    # 创建测试图片和字体
    img = Image.new('RGB', (1024, 1365), color='white')
    draw = ImageDraw.Draw(img)
    
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                if path.endswith('.ttc'):
                    font = ImageFont.truetype(path, 60, index=0)
                else:
                    font = ImageFont.truetype(path, 60)
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
    
    # 测试用例
    test_cases = [
        ("短文本", 500, 3),
        ("这是一个非常长的文本，需要测试截断功能是否正常工作，确保文字能够正确截断并在最后一行添加省略号。", 500, 3),
        ("标点符号测试，。！？；：、需要确保截断时不会破坏标点符号的完整性。", 500, 2),
    ]
    
    for text, max_width, max_lines in test_cases:
        print(f"\n测试文本: {text[:30]}... (最多{max_lines}行)")
        lines = gen._smart_truncate_simple(text, max_lines, max_width, font, draw)
        print(f"  结果: {len(lines)} 行")
        for i, line in enumerate(lines, 1):
            print(f"  行{i}: {line[:50]}")
            if len(lines) > max_lines:
                print(f"  ⚠️  警告: 行数超过限制")
    
    print("\n✅ 智能截断测试完成")


def test_content_safety():
    """测试内容安全检查功能"""
    print("\n测试内容安全检查功能...")
    
    gen = ImageGenerator(config_path="config/config.json")
    
    # 测试用例
    test_cases = [
        ("天安门广场是北京的地标", True),  # 应该通过（正常历史文化内容）
        ("故宫是明清两朝的皇宫", True),  # 应该通过
        ("这是一个包含革命词汇的文本", False),  # 应该被标记
        ("血腥暴力的内容", False),  # 应该被标记
        ("正常的北京胡同记忆", True),  # 应该通过
    ]
    
    for text, should_pass in test_cases:
        is_safe, modified = gen.check_content_safety(text)
        print(f"\n文本: {text[:30]}...")
        print(f"  是否安全: {is_safe}")
        if not is_safe:
            print(f"  修改后: {modified[:30]}...")
        
        if should_pass and not is_safe:
            print(f"  ⚠️  警告: 正常内容被误判为不安全")
        elif not should_pass and is_safe:
            print(f"  ⚠️  警告: 敏感内容未被检测到")
    
    print("\n✅ 内容安全检查测试完成")


if __name__ == "__main__":
    print("=" * 60)
    print("文字叠加功能单元测试")
    print("=" * 60)
    
    try:
        test_wrap_text_simple()
        test_smart_truncate_simple()
        test_content_safety()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
