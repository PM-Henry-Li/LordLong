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


def test_wrap_text():
    """测试文字换行功能"""
    print("测试文字换行功能...")

    gen = ImageGenerator(config_path="config/config.json")

    # 创建测试图片和字体
    img = Image.new("RGB", (1024, 1365), color="white")
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
                if path.endswith(".ttc"):
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
        # 新增测试用例：测试标点符号不单独成行
        ("这是一段测试文本。应该在标点符号前换行，而不是让标点单独成行。", 400),
        ("测试引号「这是引号内容」和括号（这是括号内容）的处理。", 400),
        # 测试emoji和特殊字符
        ("这是包含emoji的文本😊😂🎉，看看换行是否正常。", 400),
        ("测试中英文混合text和数字123的换行效果。", 400),
    ]

    for text, max_width in test_cases:
        print(f"\n测试文本: {text[:30]}...")
        lines = gen._wrap_text(text, max_width, font, draw)
        print(f"  结果: {len(lines)} 行")
        for i, line in enumerate(lines, 1):
            print(f"  行{i}: {line[:50]}")
            # 检查是否有单独标点
            if len(line.strip()) == 1 and line.strip() in ["。", "，", "！", "？", "；", "：", "、"]:
                print(f"  ⚠️  警告: 发现单独标点符号行")

    print("\n✅ 文字换行测试完成")


def test_smart_truncate():
    """测试智能截断功能"""
    print("\n测试智能截断功能...")

    gen = ImageGenerator(config_path="config/config.json")

    # 创建测试图片和字体
    img = Image.new("RGB", (1024, 1365), color="white")
    draw = ImageDraw.Draw(img)

    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                if path.endswith(".ttc"):
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
        # 新增边界测试用例
        ("测试单行截断。", 500, 1),
        ("测试两行截断，第一行内容，第二行内容应该被截断。", 400, 2),
        # 测试极端情况
        ("极短", 500, 3),
        ("这是一个超级超级超级超级超级超级超级超级超级超级超级超级超级超级超级超级长的文本，需要测试在极端情况下的截断效果。", 300, 2),
        # 测试emoji截断
        ("这是包含emoji的长文本😊😂🎉需要测试截断时emoji的处理是否正确，不会出现乱码或显示问题。", 400, 2),
    ]

    for text, max_width, max_lines in test_cases:
        print(f"\n测试文本: {text[:30]}... (最多{max_lines}行)")
        lines = gen._smart_truncate(text, max_lines, max_width, font, draw)
        print(f"  结果: {len(lines)} 行")
        for i, line in enumerate(lines, 1):
            print(f"  行{i}: {line[:50]}")
        
        # 验证行数不超过限制
        if len(lines) > max_lines:
            print(f"  ❌ 错误: 行数({len(lines)})超过限制({max_lines})")
        
        # 验证最后一行是否有省略号（如果文本被截断）
        if len(lines) == max_lines and len(text) > 50:
            if not lines[-1].endswith("…"):
                print(f"  ⚠️  警告: 文本被截断但最后一行没有省略号")

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


def test_special_characters():
    """测试特殊字符处理（emoji、标点符号等）"""
    print("\n测试特殊字符处理...")

    gen = ImageGenerator(config_path="config/config.json")

    # 创建测试图片和字体
    img = Image.new("RGB", (1024, 1365), color="white")
    draw = ImageDraw.Draw(img)

    # 加载字体
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                if path.endswith(".ttc"):
                    font = ImageFont.truetype(path, 60, index=0)
                else:
                    font = ImageFont.truetype(path, 60)
                break
            except:
                continue

    if not font:
        font = ImageFont.load_default()

    # 测试用例：各种特殊字符
    test_cases = [
        # Emoji测试
        ("这是包含emoji的文本😊😂🎉", 500),
        ("多个emoji连续出现🌟✨💫⭐", 500),
        ("emoji在句中😊的位置", 500),
        
        # 标点符号测试
        ("测试各种标点：，。！？；：、", 500),
        ("引号测试「」『』""''", 500),
        ("括号测试（）【】《》", 500),
        ("省略号测试……", 500),
        
        # 中英文混合
        ("中英文混合text测试", 500),
        ("包含数字123和字母ABC", 500),
        ("URL测试https://example.com", 500),
        
        # 特殊空白字符
        ("包含\t制表符的文本", 500),
        ("包含  多个空格  的文本", 500),
        
        # 边界情况
        ("", 500),  # 空字符串
        ("单", 500),  # 单个字符
        ("。", 500),  # 单个标点
    ]

    for text, max_width in test_cases:
        print(f"\n测试文本: '{text[:30]}...'")
        try:
            lines = gen._wrap_text(text, max_width, font, draw)
            print(f"  结果: {len(lines)} 行")
            for i, line in enumerate(lines, 1):
                print(f"  行{i}: '{line[:50]}'")
            
            # 验证结果
            if not text and lines:
                print(f"  ⚠️  警告: 空字符串应返回空列表")
            
            # 检查是否有单独的标点符号行
            for line in lines:
                if len(line.strip()) == 1 and line.strip() in ["。", "，", "！", "？", "；", "：", "、"]:
                    print(f"  ⚠️  警告: 发现单独标点符号行: '{line}'")
        
        except Exception as e:
            print(f"  ❌ 错误: {e}")

    print("\n✅ 特殊字符处理测试完成")


def test_text_cleaning():
    """测试文字清理功能"""
    print("\n测试文字清理功能...")

    gen = ImageGenerator(config_path="config/config.json")

    # 测试用例
    test_cases = [
        ("正常文本", "正常文本"),
        ("包含emoji😊的文本", "包含emoji的文本"),  # emoji符号应该被移除，但"emoji"这个词保留
        ("多个emoji😊😂🎉", "多个emoji"),  # emoji符号应该被移除
        ("emoji在中间😊继续", "emoji在中间继续"),
        ("纯emoji😊😂", "纯emoji"),  # emoji符号被移除，但"emoji"这个词保留
        ("测试\t制表符", "测试制表符"),  # 制表符应该被规范化（多个空白字符合并）
        ("多个  空格", "多个 空格"),  # 多个空格应该被规范化为单个空格
    ]

    for input_text, expected_output in test_cases:
        cleaned = gen.clean_text_for_display(input_text)
        print(f"\n输入: '{input_text}'")
        print(f"  输出: '{cleaned}'")
        print(f"  期望: '{expected_output}'")
        
        if cleaned != expected_output:
            print(f"  ⚠️  警告: 输出与期望不符")

    print("\n✅ 文字清理测试完成")


if __name__ == "__main__":
    print("=" * 60)
    print("文字叠加功能单元测试")
    print("=" * 60)

    try:
        test_wrap_text()
        test_smart_truncate()
        test_content_safety()
        test_special_characters()
        test_text_cleaning()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
