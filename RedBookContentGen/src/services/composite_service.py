#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复合生图服务
负责将 AI 生成的背景图与高质量的程序化文字叠加合成
"""

import os
import base64
from typing import Dict, Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from src.core.logger import Logger

class CompositeImageService:
    """复合生图服务类"""

    def __init__(self, output_dir: Path):
        """
        初始化复合生图服务

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self.font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        ]

    def composite_text(
        self, 
        background_path: str, 
        title: str, 
        content_text: str, 
        output_filename: str,
        is_cover: bool = True,
        comic_panels: Optional[List[str]] = None,
    ) -> Dict:
        """
        在背景图上叠加文字

        Args:
            background_path: 背景图路径
            title: 标题
            content_text: 正文内容
            output_filename: 输出文件名
            is_cover: 是否为封面模式
            comic_panels: 漫画分镜文案列表（4或6元素），有值时自动进入漫画布局模式

        Returns:
            包含图片数据的字典
        """
        try:
            # 加载背景图
            bg_img = Image.open(background_path).convert("RGBA")
            width, height = bg_img.size
            
            # ★ 第一层防线：高斯模糊消除 AI 乱码文字的锐利边缘
            bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=2.5))
            
            # 创建绘图层
            overlay = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            if comic_panels:
                # 漫画布局模式：根据格数确定列数
                cols = 2  # 四格和六格都用2列
                self._draw_comic_layout(draw, width, height, comic_panels, cols)
            elif is_cover and title:
                self._draw_cover_style(draw, width, height, title)
            elif content_text:
                self._draw_story_style(draw, width, height, content_text)
                
            # 合并图层
            combined = Image.alpha_composite(bg_img, overlay).convert("RGB")
            
            # 保存结果
            final_path = self.output_dir / output_filename
            combined.save(final_path, "PNG", quality=95)
            
            # 转换为 base64
            with open(final_path, "rb") as f:
                content_bytes = f.read()
            b64 = base64.b64encode(content_bytes).decode("utf-8")
            
            return {
                "data": f"data:image/png;base64,{b64}",
                "path": str(final_path)
            }
            
        except Exception as e:
            Logger.error(f"图像合成失败: {str(e)}", logger_name="composite_service")
            raise e

    def _draw_cover_style(self, draw: ImageDraw.Draw, width: int, height: int, title: str):
        """绘制封面风格标题（自适应字号 + 半透明底板 + 居中渲染）"""
        if not title:
            return
            
        margin = int(width * 0.08)
        max_width = width - 2 * margin
        
        # 自适应字号：从大到小尝试，直到标题能在合理行数内排列
        for font_pct in [0.10, 0.085, 0.07, 0.06, 0.05]:
            font_size = int(height * font_pct)
            font = self._load_font(font_size, bold=True)
            lines = self._wrap_text(title, max_width, font, draw, max_lines=5)
            line_height = int(font_size * 1.3)
            total_text_height = len(lines) * line_height
            # 标题区域不超过图片高度的 40%
            if total_text_height < height * 0.40:
                break
        
        # 垂直居中偏上（黄金分割位 ~38%）
        start_y = int((height * 0.38) - (total_text_height / 2))
        start_y = max(int(height * 0.06), start_y)  # 防止顶部溢出
        
        # ★ 第二层防线：扩大半透明底板覆盖图片中心 60%~70% 区域
        #   遮盖建筑中心的牌匾、招牌等 AI 易出错区域
        card_padding_x = int(width * 0.04)
        # 底板上下各扩展，覆盖中心大面积区域
        card_y_start = max(0, int(height * 0.15))  # 从 15% 处开始
        card_y_end = min(height, int(height * 0.75))  # 到 75% 处结束
        draw.rounded_rectangle(
            [card_padding_x, card_y_start, width - card_padding_x, card_y_end],
            radius=24,
            fill=(0, 0, 0, 110)
        )
        
        # 绘制文字描边 + 主体
        shadow_offset = max(2, int(font_size * 0.04))
        for i, line in enumerate(lines):
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
            except Exception:
                line_width = len(line) * font_size
            
            x = (width - line_width) // 2
            y = start_y + i * line_height
            
            # 描边（只绘制 4 个方向，性能更好）
            for dx, dy in [(-shadow_offset, 0), (shadow_offset, 0), (0, -shadow_offset), (0, shadow_offset)]:
                draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 160))
            
            # 主文字
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    def _draw_story_style(self, draw: ImageDraw.Draw, width: int, height: int, content: str):
        """绘制正文图风格（底部说明文字 + 对比度增强）"""
        if not content:
            return
            
        font_size = int(height * 0.042)  # 略微调小字号以容纳更多内容
        font = self._load_font(font_size)
        
        margin_x = int(width * 0.08)
        max_width = width - 2 * margin_x
        
        # 实现带完整句子的换行
        lines = self._wrap_text(content, max_width, font, draw, max_lines=4)
        
        # 如果原文还有剩余，添加省略号
        if len(lines) == 4 and len(content) > sum(len(l) for l in lines) + 2:
            lines[-1] = lines[-1][: -2] + "..."

        line_height = int(font_size * 1.6)
        total_text_height = len(lines) * line_height
        
        # 底部预留更多空间（躲避 UI 下载按钮和点赞图标）
        bottom_padding = int(height * 0.08)
        text_block_y = height - total_text_height - bottom_padding - int(height * 0.03)
        
        # ★ 第三层防线：渐变蒙层（从底部 50% 高度开始，透明度从 0 渐变到 180）
        gradient_start = int(height * 0.45)  # 从 45% 高度开始渐变
        gradient_height = height - gradient_start
        for y_pos in range(gradient_start, height):
            progress = (y_pos - gradient_start) / gradient_height
            alpha = int(180 * progress)  # 0 → 180 渐变
            draw.line([(0, y_pos), (width, y_pos)], fill=(0, 0, 0, alpha))
        
        for i, line in enumerate(lines):
            y = text_block_y + int(height * 0.02) + i * line_height
            # 绘制文字描边增强可读性
            shadow = max(1, int(font_size * 0.03))
            for dx, dy in [(-shadow, 0), (shadow, 0), (0, -shadow), (0, shadow)]:
                draw.text((margin_x + dx, y + dy), line, font=font, fill=(0, 0, 0, 140))
            draw.text((margin_x, y), line, font=font, fill=(255, 255, 255, 255))

    def _load_font(self, size: int, bold: bool = False):
        """加载字体"""
        for font_path in self.font_paths:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith(".ttc"):
                        index = 1 if bold else 0
                        return ImageFont.truetype(font_path, size, index=index)
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _wrap_text(self, text: str, max_width: int, font, draw, max_lines: int = 3) -> List[str]:
        """简单的文字换行逻辑"""
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                w = bbox[2] - bbox[0]
            except Exception:
                w = len(test_line) * font.size
            
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
                if len(lines) >= max_lines:
                    break
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        return lines

    def _draw_comic_layout(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        panels: List[str],
        cols: int = 2,
    ):
        """
        绘制漫画格子布局

        Args:
            draw: PIL ImageDraw 绘图对象
            width: 图片宽度
            height: 图片高度
            panels: 分镜文案列表（4 或 6 个元素）
            cols: 每行列数（默认 2）
        """
        n = len(panels)
        rows = (n + cols - 1) // cols  # 向上取整

        border = 8          # 格子边框厚度（像素）
        margin = 12         # 外边距
        gap = 6             # 格子间距

        # 计算每格宽高
        cell_w = (width - 2 * margin - (cols - 1) * gap) // cols
        cell_h = (height - 2 * margin - (rows - 1) * gap) // rows

        font_size = max(18, int(cell_h * 0.055))
        font = self._load_font(font_size)

        for idx, panel_text in enumerate(panels):
            row = idx // cols
            col = idx % cols

            # 计算格子坐标
            x0 = margin + col * (cell_w + gap)
            y0 = margin + row * (cell_h + gap)
            x1 = x0 + cell_w
            y1 = y0 + cell_h

            # 绘制白色边框（漫画格子感）
            draw.rectangle([x0, y0, x1, y1], outline=(255, 255, 255, 230), width=border)

            # 底部文字区域高度（约 25% 的格子）
            text_area_h = int(cell_h * 0.28)
            text_y0 = y1 - text_area_h

            # 半透明黑底
            draw.rectangle(
                [x0 + border, text_y0, x1 - border, y1 - border],
                fill=(0, 0, 0, 160)
            )

            # 文字换行
            max_text_w = cell_w - 2 * border - 16
            lines = self._wrap_text(panel_text, max_text_w, font, draw, max_lines=3)

            line_h = int(font_size * 1.35)
            total_text_h = len(lines) * line_h
            # 垂直居中于文字区域
            txt_start_y = text_y0 + max(8, (text_area_h - total_text_h) // 2)

            for i, line in enumerate(lines):
                tx = x0 + border + 8
                ty = txt_start_y + i * line_h
                # 描边
                shadow = max(1, int(font_size * 0.05))
                for dx, dy in [(-shadow, 0), (shadow, 0), (0, -shadow), (0, shadow)]:
                    draw.text((tx + dx, ty + dy), line, font=font, fill=(0, 0, 0, 160))
                # 主文字
                draw.text((tx, ty), line, font=font, fill=(255, 255, 255, 240))

            # 右上角格子编号
            num_font_size = max(14, int(cell_h * 0.04))
            num_font = self._load_font(num_font_size, bold=True)
            num_text = str(idx + 1)
            draw.text(
                (x1 - border - num_font_size - 4, y0 + border + 4),
                num_text,
                font=num_font,
                fill=(255, 255, 255, 200)
            )
