#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报图片生成器
根据周报数据生成SVG格式的可视化图表
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class WeekReportImageGenerator:
    """周报图片生成器"""
    
    # 颜色定义
    COLORS = {
        'M端': '#8b5cf6',      # Purple
        'P端': '#3b82f6',      # Blue
        '线下': '#10b981',     # Green
        '总进度-未完成': '#f59e0b',  # Amber
        '总进度-完成': '#22c55e',    # Green
    }
    
    def __init__(self, data_file: str):
        """
        初始化生成器
        
        Args:
            data_file: 数据文件路径
        """
        self.data_file = data_file
        self.projects = []
        
    def parse_data(self) -> None:
        """解析数据文件"""
        self.projects = []
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式匹配项目分组
        # 格式：【季度计划】或【月度计划】或【迭代计划】
        section_pattern = r'【(.*?)】'
        sections = re.split(section_pattern, content)
        
        # sections[0]是空字符串，sections[1]是第一个分组名，sections[2]是第一个分组内容
        for i in range(1, len(sections), 2):
            if i >= len(sections):
                break
            
            section_title = sections[i].strip()
            section_content = sections[i + 1] if (i + 1) < len(sections) else ""
            
            # 解析每个分组的详细内容
            items, total_data = self.parse_section_content(section_content)
            
            if items:
                # 提取更清晰的标题
                title = self.extract_title(section_content, section_title)
                self.projects.append({
                    'title': title,
                    'items': items,
                    'total_data': total_data  # 保存总体数据用于校验
                })
        
        # 数据校验
        self.validate_data()
    
    def validate_data(self) -> None:
        """
        数据校验：检查分子、分母合计和分计是否一致，各项推进率是否超过100%
        """
        errors = []
        warnings = []
        
        for project in self.projects:
            title = project['title']
            items = project['items']
            total_data = project.get('total_data', {})
            
            # 计算分项合计
            items_total_sum = sum(item['total'] for item in items)
            items_started_sum = sum(item['started'] for item in items)
            
            # 校验1：检查分母合计（计划数）
            if total_data.get('total', 0) > 0:
                if items_total_sum != total_data['total']:
                    errors.append(
                        f"【{title}】计划数不一致："
                        f"总体={total_data['total']}，分项合计={items_total_sum}"
                    )
            
            # 校验2：检查分子合计（已启动数）
            if total_data.get('started', 0) > 0 or items_started_sum > 0:
                if items_started_sum != total_data.get('started', 0):
                    errors.append(
                        f"【{title}】已启动数不一致："
                        f"总体={total_data.get('started', 0)}，分项合计={items_started_sum}"
                    )
            
            # 校验3：检查各项推进率是否超过100%
            for item in items:
                if item['progress'] > 100:
                    errors.append(
                        f"【{title}】{item['platform']}推进率超过100%：{item['progress']}%"
                    )
                elif item['progress'] < 0:
                    errors.append(
                        f"【{title}】{item['platform']}推进率为负数：{item['progress']}%"
                    )
                
                # 检查已启动数是否超过计划数
                if item['started'] > item['total']:
                    errors.append(
                        f"【{title}】{item['platform']}已启动数({item['started']})超过计划数({item['total']})"
                    )
            
            # 校验4：检查总体推进率是否超过100%
            if total_data.get('progress', 0) > 100:
                errors.append(
                    f"【{title}】总体推进率超过100%：{total_data['progress']}%"
                )
            
            # 警告：如果分项推进率与总体推进率差异较大
            if total_data.get('progress', 0) > 0 and items:
                avg_progress = sum(item['progress'] for item in items) / len(items)
                if abs(avg_progress - total_data['progress']) > 10:
                    warnings.append(
                        f"【{title}】分项平均推进率({avg_progress:.1f}%)与总体推进率({total_data['progress']}%)差异较大"
                    )
        
        # 输出校验结果
        if errors:
            print("\n" + "=" * 80)
            print("❌ 数据校验发现错误：")
            print("=" * 80)
            for error in errors:
                print(f"  ✗ {error}")
            print("=" * 80)
            raise ValueError(f"数据校验失败，发现 {len(errors)} 个错误")
        
        if warnings:
            print("\n" + "=" * 80)
            print("⚠️  数据校验警告：")
            print("=" * 80)
            for warning in warnings:
                print(f"  ⚠ {warning}")
            print("=" * 80)
        
        if not errors and not warnings:
            print("\n✓ 数据校验通过：所有数据一致，推进率正常")
    
    def extract_title(self, content: str, section_name: str) -> str:
        """
        从内容中提取标题
        
        Args:
            content: 分组内容
            section_name: 分组名称（季度计划/月度计划/迭代计划）
            
        Returns:
            提取的标题
        """
        # 尝试提取第一行的计划名称
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if lines:
            # 第一行通常包含计划名称，如"Q3已排长线计划总计30项..."
            first_line = lines[0]
            
            # 提取计划名称（季度/月份/迭代号）
            if re.search(r'Q[1-4]', first_line):
                # 提取Q1, Q2, Q3, Q4
                match = re.search(r'Q[1-4]', first_line)
                if match:
                    return f"{match.group()} 季度计划"
            
            if '月' in first_line:
                # 提取月份
                match = re.search(r'(\d+)月', first_line)
                if match:
                    month = match.group(1)
                    return f"{month}月计划"
            
            if re.search(r'\d{4}', first_line):
                # 提取迭代号（4位数字）
                match = re.search(r'(\d{4})', first_line)
                if match:
                    return f"迭代{match.group()}"
        
        # 如果无法提取，返回默认标题
        return section_name
    
    def parse_section_content(self, content: str) -> Tuple[List[Dict], Dict]:
        """
        解析分组内容
        
        Args:
            content: 分组内容文本
            
        Returns:
            (项目列表, 总体数据)
        """
        items = []
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # 提取总体数据
        total_data = self.extract_total_data(lines[0] if lines else "")
        
        # 检查第一行的总体推进率
        total_progress = total_data.get('progress', 0)
        total_progress_100 = (total_progress == 100)
        
        # 跳过第一行（总计行）
        for line in lines[1:]:
            # 解析每一行
            item = self.parse_item_line(line, total_progress, total_progress_100)
            if item:
                items.append(item)
        
        return items, total_data
    
    def extract_total_data(self, first_line: str) -> Dict:
        """
        从第一行提取总体数据
        
        Args:
            first_line: 第一行文本
            
        Returns:
            总体数据字典
        """
        total_data = {'total': 0, 'started': 0, 'progress': 0}
        
        # 提取总计数量
        total_match = re.search(r'总计(\d+)项', first_line)
        if total_match:
            total_data['total'] = int(total_match.group(1))
        
        # 提取已启动数量
        started_match = re.search(r'已启动(\d+)项', first_line)
        if started_match:
            total_data['started'] = int(started_match.group(1))
        
        # 提取推进率
        progress_match = re.search(r'推进率(\d+)%', first_line)
        if progress_match:
            total_data['progress'] = int(progress_match.group(1))
        elif total_data['total'] > 0:
            # 如果没有明确指定推进率，根据已启动数计算
            total_data['progress'] = int((total_data['started'] / total_data['total']) * 100)
        
        return total_data
    
    def parse_item_line(self, line: str, total_progress: int = 0, total_progress_100: bool = False) -> Dict:
        """
        解析单行数据
        
        支持两种格式：
        1. M端10项，已启动9项，推进率90%；
        2. M端17项（无已启动数和推进率）
        
        Args:
            line: 数据行
            total_progress: 总体推进率（0-100）
            total_progress_100: 总体推进率是否为100%
            
        Returns:
            解析后的项目数据
        """
        # 移除末尾的分号
        line = line.rstrip('；').strip()
        
        # 提取平台名称（M端、P端、线下端）
        platform_match = re.match(r'(M端|P端|线下端|线下)', line)
        if not platform_match:
            return None
        
        platform = platform_match.group(1)
        # 术语标准化：线下端 -> 线下
        if platform == '线下端':
            platform = '线下'
        
        # 提取计划数
        total_match = re.search(r'(\d+)项', line)
        if not total_match:
            return None
        
        total = int(total_match.group(1))
        
        # 提取已启动数
        started_match = re.search(r'已启动(\d+)项', line)
        has_started = bool(started_match)
        if started_match:
            started = int(started_match.group(1))
        else:
            started = 0
        
        # 提取推进率
        progress_match = re.search(r'推进率(\d+)%', line)
        has_progress = bool(progress_match)
        if progress_match:
            progress = int(progress_match.group(1))
        else:
            # 如果没有明确指定推进率
            if not has_started:
                # 如果没有直接给单端口的数据，则整体推进率代表每个端口的推进率
                progress = total_progress
                # 根据总体推进率计算已启动数
                started = int(total * total_progress / 100) if total_progress > 0 else 0
            elif total_progress_100:
                # 如果总体推进率为100%，默认该项也100%
                progress = 100
                # 补全已启动数
                if started == 0:
                    started = total
            elif started == 0 and total > 0:
                # 如果没有已启动数，假设推进率为0%
                progress = 0
            elif total > 0:
                progress = int((started / total) * 100)
            else:
                progress = 0
        
        # 数据补全：如果推进率为100%但已启动数为0，则已启动数=计划数
        if progress == 100 and started == 0:
            started = total
        
        return {
            'platform': platform,
            'total': total,
            'started': started,
            'progress': progress
        }
    
    def calculate_view_b(self, items: List[Dict]) -> Tuple[Dict, List[Dict]]:
        """
        计算视图B的数据（剔除M端）
        
        Args:
            items: 视图A的所有项目
            
        Returns:
            (总计数据, 过滤后的项目列表)
        """
        filtered_items = [item for item in items if item['platform'] != 'M端']
        
        if not filtered_items:
            return {'total': 0, 'started': 0, 'progress': 0}, []
        
        total = sum(item['total'] for item in filtered_items)
        started = sum(item['started'] for item in filtered_items)
        progress = int((started / total) * 100) if total > 0 else 0
        
        return {'total': total, 'started': started, 'progress': progress}, filtered_items
    
    def calculate_view_a(self, items: List[Dict]) -> Tuple[Dict, List[Dict]]:
        """
        计算视图A的数据（包含M端、P端、线下）
        
        Args:
            items: 视图A的所有项目
            
        Returns:
            (总计数据, 项目列表)
        """
        if not items:
            return {'total': 0, 'started': 0, 'progress': 0}, []
        
        total = sum(item['total'] for item in items)
        started = sum(item['started'] for item in items)
        progress = int((started / total) * 100) if total > 0 else 0
        
        return {'total': total, 'started': started, 'progress': progress}, items
    
    def get_progress_color(self, progress: int) -> str:
        """获取进度条颜色"""
        return self.COLORS['总进度-完成'] if progress == 100 else self.COLORS['总进度-未完成']
    
    def get_platform_color(self, platform: str) -> str:
        """获取平台颜色"""
        return self.COLORS.get(platform, '#6b7280')
    
    def escape_xml(self, text: str) -> str:
        """
        转义XML特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            转义后的文本
        """
        if not text:
            return ''
        
        # XML/SVG中需要转义的特殊字符
        text = text.replace('&', '&amp;')  # 必须最先替换
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        return text
    
    def generate_svg_card(self, 
                         title: str,
                         total_data: Dict,
                         items: List[Dict],
                         x: int,
                         y: int,
                         card_width: int = 270,
                         card_height: int = 460) -> str:
        """
        生成单个卡片的SVG代码
        
        Args:
            title: 卡片标题
            total_data: 总计数据
            items: 项目列表
            x: 卡片X坐标
            y: 卡片Y坐标
            card_width: 卡片宽度
            card_height: 卡片高度
            
        Returns:
            SVG代码字符串
        """
        progress_color = self.get_progress_color(total_data['progress'])
        
        # 计算卡片内部分项数量，动态调整间距
        num_items = len(items)
        spacing_adjustment = 60 if num_items == 2 else 70  # 2个分项时间距更小
        
        svg_parts = []
        
        # 卡片背景
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" '
                        f'class="card" />')
        
        # 标题
        escaped_title = self.escape_xml(title)
        svg_parts.append(f'<text x="{x + 20}" y="{y + 35}" class="title">{escaped_title}</text>')
        
        # 副标题（根据项目数量）
        subtitle = 'P端 & 线下' if num_items == 2 else 'M端 & P端 & 线下'
        escaped_subtitle = self.escape_xml(subtitle)
        svg_parts.append(f'<text x="{x + 20}" y="{y + 58}" class="subtitle">{escaped_subtitle}</text>')
        
        # 主统计数字（左侧：已启动数/总计划）
        svg_parts.append(f'<text x="{x + 20}" y="{y + 110}" class="main-stat-val">{total_data["started"]}</text>')
        svg_parts.append(f'<text x="{x + 20}" y="{y + 135}" class="main-stat-unit">/ {total_data["total"]}</text>')
        
        # 主百分比（右侧）
        svg_parts.append(f'<text x="{x + card_width - 20}" y="{y + 110}" '
                        f'class="main-percent" fill="{progress_color}" text-anchor="end">'
                        f'{total_data["progress"]}%</text>')
        
        # 主进度条背景
        bar_y = y + 155
        bar_width = card_width - 40
        svg_parts.append(f'<rect x="{x + 20}" y="{bar_y}" width="{bar_width}" height="10" '
                        f'class="progress-bg" />')
        
        # 主进度条
        progress_width = int(bar_width * total_data['progress'] / 100)
        svg_parts.append(f'<rect x="{x + 20}" y="{bar_y}" width="{progress_width}" height="10" '
                        f'class="progress-bar" fill="{progress_color}" />')
        
        # 分隔线
        svg_parts.append(f'<line x1="{x + 20}" y1="{y + 180}" x2="{x + card_width - 20}" '
                        f'y2="{y + 180}" class="divider" />')
        
        # 分项详情
        item_start_y = y + 210
        for idx, item in enumerate(items):
            item_y = item_start_y + idx * spacing_adjustment
            
            # 分项标题
            platform_color = self.get_platform_color(item['platform'])
            escaped_platform = self.escape_xml(item['platform'])
            svg_parts.append(f'<text x="{x + 20}" y="{item_y}" class="breakdown-title" '
                            f'fill="{platform_color}">{escaped_platform}</text>')
            
            # 分项详情
            detail_text = f'已启动 {item["started"]} / 计划 {item["total"]}'
            escaped_detail = self.escape_xml(detail_text)
            svg_parts.append(f'<text x="{x + 20}" y="{item_y + 20}" class="breakdown-text">'
                            f'{escaped_detail}</text>')
            
            # 分项进度条背景
            item_bar_y = item_y + 35
            item_bar_width = card_width - 40
            svg_parts.append(f'<rect x="{x + 20}" y="{item_bar_y}" width="{item_bar_width}" '
                            f'height="8" class="progress-bg" />')
            
            # 分项进度条
            item_progress_width = int(item_bar_width * item['progress'] / 100)
            svg_parts.append(f'<rect x="{x + 20}" y="{item_bar_y}" width="{item_progress_width}" '
                            f'height="8" class="progress-bar" fill="{platform_color}" />')
        
        return '\n    '.join(svg_parts)
    
    def generate_svg(self, view_type: str) -> str:
        """
        生成完整的SVG图片
        
        Args:
            view_type: 视图类型 ('A' 或 'B')
            
        Returns:
            SVG代码字符串
        """
        canvas_width = 880
        canvas_height = 480
        card_width = 270
        card_height = 460
        card_gap = 35
        start_x = 15
        start_y = 10
        
        svg_parts = [f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .bg {{ fill: #f9fafb; }}
      .card {{ fill: #ffffff; stroke: #e5e7eb; stroke-width: 1; rx: 12; ry: 12; }}
      .title {{ font-size: 19px; font-weight: bold; fill: #111827; font-family: Arial, sans-serif; }}
      .subtitle {{ font-size: 14px; fill: #6b7280; font-family: Arial, sans-serif; }}
      .main-stat-val {{ font-size: 28px; font-weight: bold; fill: #1f2937; font-family: Arial, sans-serif; }}
      .main-stat-unit {{ font-size: 16px; fill: #4b5563; font-family: Arial, sans-serif; }}
      .main-percent {{ font-size: 28px; font-weight: bold; font-family: Arial, sans-serif; }}
      .progress-bg {{ fill: #e5e7eb; rx: 5; ry: 5; }}
      .progress-bar {{ rx: 5; ry: 5; }}
      .breakdown-title {{ font-size: 15px; font-weight: 600; fill: #374151; font-family: Arial, sans-serif; }}
      .breakdown-text {{ font-size: 13px; fill: #4b5563; font-family: Arial, sans-serif; }}
      .divider {{ stroke: #f3f4f6; stroke-width: 1.5; }}
    </style>
  </defs>
  <rect width="100%" height="100%" class="bg" />''']
        
        for idx, project in enumerate(self.projects):
            if view_type == 'A':
                total_data, items = self.calculate_view_a(project['items'])
            else:  # view_type == 'B'
                total_data, items = self.calculate_view_b(project['items'])
            
            if idx >= 3:  # 最多显示3个卡片
                break
            
            x = start_x + idx * (card_width + card_gap)
            card_svg = self.generate_svg_card(
                title=project['title'],
                total_data=total_data,
                items=items,
                x=x,
                y=start_y
            )
            svg_parts.append(f'  {card_svg}')
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)
    
    def save_svg(self, svg_content: str, output_path: str) -> None:
        """
        保存SVG文件
        
        Args:
            svg_content: SVG代码
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    
    def generate(self) -> Tuple[str, str]:
        """
        生成周报图片
        
        Returns:
            (视图A的文件路径, 视图B的文件路径)
        """
        self.parse_data()
        
        # 生成输出目录
        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)
        
        # 生成日期字符串
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 生成视图A
        svg_a = self.generate_svg('A')
        svg_path_a = output_dir / f'周报_视图A_{today}.svg'
        self.save_svg(svg_a, str(svg_path_a))
        
        # 生成视图B
        svg_b = self.generate_svg('B')
        svg_path_b = output_dir / f'周报_视图B_{today}.svg'
        self.save_svg(svg_b, str(svg_path_b))
        
        return str(svg_path_a), str(svg_path_b)
    
    def print_summary(self) -> None:
        """打印数据摘要"""
        print("=" * 80)
        print("【视图 A：M端 & P端 & 线下】")
        print("=" * 80)
        
        for project in self.projects:
            total_data, items = self.calculate_view_a(project['items'])
            print(f"\n{project['title']}:")
            print(f"  总计划: {total_data['total']}, 已启动: {total_data['started']}, 推进率: {total_data['progress']}%")
            for item in items:
                print(f"  - {item['platform']}: 已启动 {item['started']} / 计划 {item['total']} ({item['progress']}%)")
        
        print("\n" + "=" * 80)
        print("【视图 B：已剔除 M端】")
        print("=" * 80)
        
        for project in self.projects:
            total_data, items = self.calculate_view_b(project['items'])
            print(f"\n{project['title']}:")
            print(f"  总计划: {total_data['total']}, 已启动: {total_data['started']}, 推进率: {total_data['progress']}%")
            for item in items:
                print(f"  - {item['platform']}: 已启动 {item['started']} / 计划 {item['total']} ({item['progress']}%)")
        
        print("\n" + "=" * 80)


def main():
    """主函数"""
    # 数据文件路径
    data_file = Path(__file__).parent / 'data.txt'
    
    # 检查数据文件是否存在
    if not data_file.exists():
        print(f"错误：数据文件不存在 - {data_file}")
        print("请创建 data.txt 文件并添加周报数据")
        return
    
    # 创建生成器并生成图片
    generator = WeekReportImageGenerator(str(data_file))
    generator.parse_data()
    
    # 打印摘要
    generator.print_summary()
    
    # 生成图片
    svg_path_a, svg_path_b = generator.generate()
    
    print("\n✓ 图片生成成功！")
    print(f"  视图 A (M端 & P端 & 线下): {svg_path_a}")
    print(f"  视图 B (剔除 M端): {svg_path_b}")
    print("\n提示：")
    print("  - 生成的文件为 SVG 格式（矢量图）")
    print("  - 可以在浏览器中直接打开查看")
    print("  - 可以使用在线工具转换为 PNG：https://cloudconvert.com/svg-to-png")


if __name__ == '__main__':
    main()
