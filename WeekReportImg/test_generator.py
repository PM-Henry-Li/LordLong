#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试周报图片生成器（仅生成SVG，不依赖cairosvg）
"""

import sys
from pathlib import Path

# 将当前目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from weeKReportImgGen import WeekReportImageGenerator


def main():
    """测试函数"""
    # 数据文件路径
    data_file = Path(__file__).parent / 'data.txt'
    
    # 创建生成器
    generator = WeekReportImageGenerator(str(data_file))
    
    # 解析数据
    generator.parse_data()
    
    # 打印摘要
    generator.print_summary()
    
    # 生成SVG（不转换为PNG）
    svg_a = generator.generate_svg('A')
    svg_b = generator.generate_svg('B')
    
    # 保存SVG文件
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    svg_path_a = output_dir / f'周报_视图A_{today}.svg'
    svg_path_b = output_dir / f'周报_视图B_{today}.svg'
    
    with open(svg_path_a, 'w', encoding='utf-8') as f:
        f.write(svg_a)
    
    with open(svg_path_b, 'w', encoding='utf-8') as f:
        f.write(svg_b)
    
    print(f"\n✓ SVG文件生成成功！")
    print(f"  视图 A (M端 & P端 & 线下): {svg_path_a}")
    print(f"  视图 B (剔除 M端): {svg_path_b}")
    
    print("\n提示：如需生成PNG格式图片，请先安装 cairosvg：")
    print("  pip install cairosvg")
    print("\n然后运行完整版本：")
    print("  python weeKReportImgGen.py")


if __name__ == '__main__':
    main()
