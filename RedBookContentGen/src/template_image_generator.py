#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板图片生成器
纯编程方式生成小红书图片，无需AI API Key
支持多种风格模板：复古中国风、现代简约、怀旧胶片等
"""

import os
import re
import json
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from src.core.logger import Logger

try:
    from PIL import ImageDraw as PILImageDraw

    HAS_PIL = True
except ImportError:
    PILImageDraw = None
    HAS_PIL = False
    Logger.warning(
        "未安装PIL/Pillow，无法使用模板图片生成功能。请运行: pip install Pillow", logger_name="template_image_generator"
    )


class TemplateImageGenerator:
    """模板图片生成器 - 纯编程生成，无需API Key"""

    TEMPLATE_STYLES = [
        "retro_chinese",  # 复古中国风
        "modern_minimal",  # 现代简约
        "vintage_film",  # 怀旧胶片
        "warm_memory",  # 温暖记忆
        "ink_wash",  # 水墨风格
        "info_chart",  # 信息图表
    ]

    def __init__(self, config_path: str = "config.json"):
        """
        初始化模板图片生成器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        self.output_image_dir = self.config.get("output_image_dir", "output/images")
        self.image_width = 1024
        self.image_height = 1365
        self.aspect_ratio = 3 / 4

        self.font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simkai.ttf",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]

        self._load_common_chars()

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "output_image_dir": "output/images",
            "template_style": "retro_chinese",
            "enable_ai_rewrite": False,
        }

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf - 8") as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def generate_image(
        self,
        text: str,
        title: str = "老北京记忆",
        output_path: str = "output.png",
        size: Tuple[int, int] = (1080, 1440),
        style: Optional[str] = None,
    ) -> str:
        """
        为Web API生成单张模板图片

        Args:
            text: 正文内容（会显示在图片底部）
            title: 标题（会显示在图片顶部）
            output_path: 输出路径
            size: 图片尺寸 (width, height)
            style: 模板风格

        Returns:
            输出文件路径
        """
        if style is None:
            style = self.config.get("template_style", "retro_chinese")

        self.image_width, self.image_height = size

        if HAS_PIL:
            return self._create_image_with_style(text, title, output_path, style)
        else:
            raise ImportError("PIL/Pillow 未安装，无法生成图片")

    def _create_image_with_style(self, text: str, title: str, output_path: str, style: str) -> str:
        """根据风格创建图片"""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        if style == "retro_chinese":
            return self._create_retro_chinese(text, title, output_path)
        elif style == "modern_minimal":
            return self._create_modern_minimal(text, title, output_path)
        elif style == "vintage_film":
            return self._create_vintage_film(text, title, output_path)
        elif style == "warm_memory":
            return self._create_warm_memory(text, title, output_path)
        elif style == "ink_wash":
            return self._create_ink_wash(text, title, output_path)
        elif style == "info_chart":
            return self._create_info_chart(text, title, output_path)
        else:
            return self._create_retro_chinese(text, title, output_path)

    def _create_retro_chinese(self, text: str, title: str, output_path: str) -> str:
        """创建复古中国风图片"""
        colors = {
            "bg_top": "#8B0000",
            "bg_bottom": "#2F1810",
            "text_primary": "#FFD700",
            "text_secondary": "#FFFAF0",
            "accent": "#DAA520",
            "border": "#B8860B",
        }
        return self._create_base_image(text, title, output_path, colors, style="retro_chinese")

    def _create_modern_minimal(self, text: str, title: str, output_path: str) -> str:
        """创建现代简约风格图片"""
        colors = {
            "bg_top": "#FFFFFF",
            "bg_bottom": "#F5F5F5",
            "text_primary": "#333333",
            "text_secondary": "#666666",
            "accent": "#007AFF",
            "border": "#E0E0E0",
        }
        return self._create_base_image(text, title, output_path, colors, style="modern_minimal")

    def _create_vintage_film(self, text: str, title: str, output_path: str) -> str:
        """创建怀旧胶片风格图片"""
        colors = {
            "bg_top": "#4A4A4A",
            "bg_bottom": "#1A1A1A",
            "text_primary": "#F4E4BC",
            "text_secondary": "#DDD0B8",
            "accent": "#D4A574",
            "border": "#8B7355",
        }
        return self._create_base_image(text, title, output_path, colors, style="vintage_film")

    def _create_warm_memory(self, text: str, title: str, output_path: str) -> str:
        """创建温暖记忆风格图片"""
        colors = {
            "bg_top": "#FF9966",
            "bg_bottom": "#FF6644",
            "text_primary": "#FFFFFF",
            "text_secondary": "#FFF5EE",
            "accent": "#FFE4B5",
            "border": "#DEB887",
        }
        return self._create_base_image(text, title, output_path, colors, style="warm_memory")

    def _create_ink_wash(self, text: str, title: str, output_path: str) -> str:
        """创建水墨风格图片"""
        colors = {
            "bg_top": "#F5F5F5",
            "bg_bottom": "#E8E8E8",
            "text_primary": "#333333",
            "text_secondary": "#555555",
            "accent": "#8B0000",
            "border": "#A9A9A9",
        }
        return self._create_base_image(text, title, output_path, colors, style="ink_wash")

    def _create_info_chart(self, text: str, title: str, output_path: str) -> str:
        """创建信息图表风格图片"""
        colors = {
            "bg_top": "#F5F0E6",
            "bg_bottom": "#EDE4D3",
            "text_primary": "#8B0000",
            "text_secondary": "#4A4A4A",
            "accent": "#FFD700",
            "border": "#B8860B",
        }
        return self._create_base_image(text, title, output_path, colors, style="info_chart")

    def _create_base_image(self, text: str, title: str, output_path: str, colors: Dict, style: str) -> str:
        """创建基础图片"""
        img = Image.new("RGB", (self.image_width, self.image_height), colors["bg_bottom"])

        gradient = Image.new("RGBA", (self.image_width, self.image_height // 2))
        for y in range(self.image_height // 2):
            alpha = int(255 * (1 - y / (self.image_height // 2)))
            for x in range(self.image_width):
                gradient.putpixel((x, y), self._hex_to_rgb(colors["bg_top"], alpha))
        img.paste(gradient, (0, 0), gradient)

        draw = ImageDraw.Draw(img)

        font_title = self._load_font(int(self.image_width * 0.08), bold=True)
        font_content = self._load_font(int(self.image_width * 0.05))

        title_y = int(self.image_height * 0.1)
        draw.text((self.image_width // 2, title_y), title, fill=colors["text_primary"], font=font_title, anchor="mm")

        content_y = int(self.image_height * 0.25)
        lines = self._wrap_text(text, self.image_width - 100, font_content, draw, max_lines=8)
        for i, line in enumerate(lines):
            y = content_y + i * int(self.image_height * 0.07)
            draw.text((50, y), line, fill=colors["text_secondary"], font=font_content)

        img.save(output_path, "PNG", quality=95)
        Logger.info("图片已保存", logger_name="template_image_generator", file_path=output_path)
        return output_path

    def _hex_to_rgb(self, hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)

    def _load_font(self, size: int, bold: bool = False):
        """加载指定大小的字体"""
        for font_path in self.font_paths:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith(".ttc"):
                        index = 1 if bold else 0
                        return ImageFont.truetype(font_path, size, index=index)
                    else:
                        return ImageFont.truetype(font_path, size)
                except Exception:
                    continue

        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _load_common_chars(self):
        """预加载常用字符用于宽度估算"""
        self.common_chars = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"

    def _estimate_char_width(self, font, draw) -> float:
        """估算中文字符平均宽度"""
        total_width = 0
        sample_size = min(50, len(self.common_chars))
        for char in self.common_chars[:sample_size]:
            try:
                bbox = draw.textbbox((0, 0), char, font=font)
                total_width += bbox[2] - bbox[0]
            except Exception:
                total_width += font.size
        return total_width / sample_size if sample_size > 0 else font.size

    def clean_text_for_display(self, text: str) -> str:
        """清理文字，移除特殊符号"""
        if not text:
            return ""

        text = re.sub(r"[\U0001F300-\U0001F9FF]", "", text)
        text = re.sub(r"[\U0001F600-\U0001F64F]", "", text)
        text = re.sub(r"[\U0001F680-\U0001F6FF]", "", text)
        text = re.sub(r"[\U00002600-\U000026FF]", "", text)
        text = re.sub(r"[\U00002700-\U000027BF]", "", text)
        text = re.sub(r"[👇👆🔔🌿👴💡⭐🌟✨🔥💯📝📖📕📝🎨🏷️]", "", text)
        text = re.sub(r"[→←↑↓⇒⇐⇑⇓↗↘↙↖]", "", text)
        text = re.sub(r"[【】《》〈〉「」『』]", "", text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff。，！？：；、""' "（）——…\n]", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = text.replace("\\\\n", "\n").replace("\\n", "\n")

        lines = text.split("\n")
        cleaned = []
        for line in lines:
            stripped = line.strip()
            if re.fullmatch(r"[n\s]+", stripped):
                continue
            line = re.sub(r"^n\s*", "", line)
            line = re.sub(r"([\u4e00-\u9fff]|[，。！？：；、])\s*n\s*(?=[\u4e00-\u9fff])", r"\1", line)
            line = re.sub(r"\s*n$", "", line)
            if line.strip():
                cleaned.append(line)

        text = "\n".join(cleaned)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +\n", "\n", text)
        text = re.sub(r"\n +", "\n", text)
        text = text.strip()

        return text

    def _wrap_text(self, text: str, max_width: int, font, draw, max_lines: int = 3) -> List[str]:
        """文字换行"""
        if not text:
            return []

        lines = []
        current_line = ""
        punctuation = set(["。", "，", "！", "？", "；", "：", "、"])

        for char in text:
            test = current_line + char
            try:
                bbox = draw.textbbox((0, 0), test, font=font)
                test_width = bbox[2] - bbox[0]
            except Exception:
                test_width = len(test) * (font.size if hasattr(font, "size") else 60)

            if test_width <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                    if len(lines) >= max_lines:
                        break
                    current_line = char
                else:
                    current_line = char

        if current_line and len(lines) < max_lines:
            lines.append(current_line)

        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if len(line) == 1 and line in punctuation and result:
                result[-1] += line
            else:
                result.append(line)

        return result if result else [text[:20]]

    def _smart_truncate(self, text: str, max_lines: int, font, draw) -> List[str]:
        """智能截断"""
        lines = self._wrap_text(text, 0, font, draw, max_lines + 1)
        if len(lines) <= max_lines:
            return lines

        result = lines[: max_lines - 1]
        remaining = "".join(lines[max_lines - 1 :])
        ellipsis = "…"

        try:
            ellipsis_bbox = draw.textbbox((0, 0), ellipsis, font=font)
            ellipsis_width = ellipsis_bbox[2] - ellipsis_bbox[0]
        except Exception:
            ellipsis_width = font.size

        last_line = ""
        for char in remaining:
            test = last_line + char
            try:
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] <= ellipsis_width * 10:
                    last_line = test
                else:
                    break
            except Exception:
                if len(last_line) < 10:
                    last_line += char

        if last_line:
            result.append(last_line + ellipsis)
        else:
            result[-1] = result[-1] + ellipsis if result else ellipsis

        return result

    def create_gradient_background(
        self, width: int, height: int, colors: List[Tuple[int, int, int]], direction: str = "vertical"
    ) -> Image.Image:
        """创建渐变背景"""
        base_color = colors[0]
        img = Image.new("RGB", (width, height), base_color)
        draw = ImageDraw.Draw(img)

        if len(colors) == 1:
            return img

        if direction == "vertical":
            for y in range(height):
                ratio = y / height
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        else:
            for x in range(width):
                ratio = x / width
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))

        return img

    def add_border(
        self,
        img: Image.Image,
        border_width: int = 20,
        border_color: Tuple[int, int, int] = (255, 255, 255),
        corner_radius: int = 0,
    ) -> Image.Image:
        """添加边框"""
        draw = ImageDraw.Draw(img)
        width, height = img.size
        draw.rectangle([0, 0, width - 1, height - 1], outline=border_color, width=border_width)
        return img

    def add_decorative_pattern(self, img: Image.Image, style: str) -> Image.Image:
        """添加装饰图案"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        if style == "retro_chinese":
            self._add_chinese_pattern(draw, width, height)
        elif style == "modern_minimal":
            self._add_modern_pattern(draw, width, height)
        elif style == "vintage_film":
            self._add_vintage_pattern(draw, width, height)
        elif style == "warm_memory":
            self._add_warm_pattern(draw, width, height)
        elif style == "ink_wash":
            self._add_ink_pattern(draw, width, height)

        return img

    def _add_chinese_pattern(self, draw, width: int, height: int):
        """中国风装饰图案"""
        pattern_color = (180, 140, 100, 50)

        draw.rectangle([20, 20, width - 20, height - 20], outline=pattern_color, width=3)

        for i in range(4):
            x = 40 + i * 60
            draw.arc([x, 40, x + 40, height - 40], 0, 180, fill=pattern_color[:3], width=2)

        draw.rectangle([30, 100, width - 30, height - 100], outline=pattern_color[:3], width=1)

    def _add_modern_pattern(self, draw, width: int, height: int):
        """现代简约装饰"""
        accent_color = (50, 50, 50)

        draw.rectangle([0, height * 0.7, width, height * 0.7], fill=accent_color)

        for i in range(5):
            x = 50 + i * 200
            draw.ellipse([x, height * 0.65, x + 80, height * 0.75], fill=(200, 200, 200, 100))

    def _add_vintage_pattern(self, draw, width: int, height: int):
        """怀旧胶片装饰"""
        overlay_color = (139, 69, 19, 30)

        draw.rectangle([0, 0, width, height], fill=overlay_color[:3])

        for i in range(3):
            y = 50 + i * 400
            draw.rectangle([20, y, width - 20, y + 5], fill=(180, 150, 120))

        for i in range(7):
            x = 30 + i * 140
            draw.rectangle([x, 20, x + 60, height - 20], outline=(160, 130, 100), width=2)

    def _add_warm_pattern(self, draw, width: int, height: int):
        """温暖记忆装饰"""
        for i in range(20):
            x = (i * 73) % width
            y = (i * 97) % height
            r = 10 + i % 20
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 150, 30))

        draw.line([(0, height * 0.3), (width, height * 0.3)], fill=(255, 180, 100), width=3)
        draw.line([(0, height * 0.6), (width, height * 0.6)], fill=(255, 180, 100), width=3)

    def _add_ink_pattern(self, draw, width: int, height: int):
        """水墨风格装饰"""
        ink_color = (40, 40, 40)

        for i in range(15):
            x = 50 + (i * 67) % (width - 100)
            y = 100 + (i * 83) % (height - 200)
            draw.ellipse([x, y, x + 120, y + 40], fill=(50, 50, 50, 20))

        draw.rectangle([30, 50, width - 30, height - 50], outline=ink_color, width=2)

        for i in range(4):
            y = 80 + i * 300
            draw.line([40, y, width - 40, y], fill=ink_color, width=1)

    def add_text_to_image(
        self, img: Image.Image, text: str, is_cover: bool = True, position: str = "top"
    ) -> Image.Image:
        """在图片上添加文字"""
        if not text or not text.strip():
            return img

        text = self.clean_text_for_display(text)
        if not text:
            return img

        draw = ImageDraw.Draw(img)
        width, height = img.size

        if is_cover:
            font_size = int(height * 0.08)
            text_color = (60, 40, 20)
            shadow_color = (255, 248, 220)
        else:
            font_size = int(height * 0.05)
            text_color = (255, 255, 255)
            shadow_color = (0, 0, 0)

        font = self._load_font(font_size)

        margin = int(width * 0.12)
        available_width = width - 2 * margin

        max_lines = 3
        lines = self._wrap_text(text, available_width, font, draw, max_lines)

        if len(lines) > max_lines:
            lines = self._smart_truncate(text, max_lines, font, draw)

        try:
            bbox = draw.textbbox((0, 0), "测", font=font)
            line_height = int((bbox[3] - bbox[1]) * 1.8)
        except Exception:
            line_height = int(font_size * 1.8)

        total_height = len(lines) * line_height

        if position == "bottom":
            margin_y = int(height * 0.12)
            start_y = height - total_height - margin_y
            if start_y < height * 0.55:
                start_y = int(height * 0.55)
        else:
            start_y = int(height * 0.15)
            if total_height > height * 0.3:
                start_y = int(height * 0.1)

        shadow_offset = max(2, int(font_size * 0.08))

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
            except Exception:
                line_width = len(line) * font_size

            x = (width - line_width) // 2
            y = start_y + i * line_height

            for dx in range(-shadow_offset, shadow_offset + 1):
                for dy in range(-shadow_offset, shadow_offset + 1):
                    if abs(dx) + abs(dy) <= shadow_offset:
                        draw.text((x + dx, y + dy), line, font=font, fill=shadow_color)

            draw.text((x, y), line, font=font, fill=text_color)

        return img

    def create_cover_image(self, title: str, style: Optional[str] = None, output_path: Optional[str] = None) -> str:
        """创建封面图"""
        if not HAS_PIL:
            raise Exception("未安装PIL/Pillow，无法生成图片")

        if style is None:
            style = "retro_chinese"

        width, height = self.image_width, self.image_height

        bg_colors = self._get_style_colors(style, is_cover=True)
        img = self.create_gradient_background(width, height, bg_colors, "vertical")

        img = self.add_decorative_pattern(img, style)

        if title:
            img = self.add_text_to_image(img, title, is_cover=True, position="top")

        if output_path is None:
            style_prefix = style.replace("_", "-")
            output_path = f"{style_prefix}-cover.png"

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        Logger.info("已生成封面图", logger_name="template_image_generator", file_path=output_path)

        return output_path

    def create_story_image(
        self, content: str, style: Optional[str] = None, index: int = 1, output_path: Optional[str] = None
    ) -> str:
        """创建故事图"""
        if not HAS_PIL:
            raise Exception("未安装PIL/Pillow，无法生成图片")

        if style is None:
            style = "retro_chinese"

        width, height = self.image_width, self.image_height

        bg_colors = self._get_style_colors(style, is_cover=False)
        img = self.create_gradient_background(width, height, bg_colors, "vertical")

        img = self.add_decorative_pattern(img, style)

        if content:
            img = self.add_text_to_image(img, content, is_cover=False, position="bottom")

        if output_path is None:
            style_prefix = style.replace("_", "-")
            output_path = f"{style_prefix}-story-{index:02d}.png"

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        Logger.info(f"已生成故事图 {index}", logger_name="template_image_generator", file_path=output_path, index=index)

        return output_path

    def _get_style_colors(self, style: str, is_cover: bool = True) -> List[Tuple[int, int, int]]:
        """获取风格对应的颜色方案"""
        color_schemes = {
            "retro_chinese": [
                (245, 235, 220) if is_cover else (70, 55, 40),
                (210, 190, 160) if is_cover else (50, 40, 30),
            ],
            "modern_minimal": [
                (250, 250, 250) if is_cover else (240, 240, 245),
                (230, 230, 235) if is_cover else (220, 220, 225),
            ],
            "vintage_film": [
                (180, 140, 100) if is_cover else (60, 50, 40),
                (140, 110, 80) if is_cover else (45, 35, 28),
            ],
            "warm_memory": [
                (255, 220, 180) if is_cover else (80, 60, 40),
                (255, 190, 140) if is_cover else (60, 45, 30),
            ],
            "ink_wash": [
                (240, 240, 235) if is_cover else (45, 45, 40),
                (220, 220, 215) if is_cover else (35, 35, 32),
            ],
        }
        return color_schemes.get(style, color_schemes["retro_chinese"])

    def generate_all_from_prompts(self, prompts_file: str, style: Optional[str] = None):
        """根据提示词文件生成所有图片"""
        Logger.info("=" * 60, logger_name="template_image_generator")
        Logger.info("模板图片生成器", logger_name="template_image_generator")
        Logger.info("=" * 60, logger_name="template_image_generator")

        if style is None:
            style = self.config.get("template_style", "retro_chinese")

        Logger.info("正在读取提示词文件", logger_name="template_image_generator", file_path=prompts_file)

        if not os.path.exists(prompts_file):
            raise FileNotFoundError(f"❌ 提示词文件不存在: {prompts_file}")

        with open(prompts_file, "r", encoding="utf - 8") as f:
            content = f.read()

        body_text = ""
        body_match = re.search(r"## 正文内容\n\n(.*?)\n\n---", content, re.DOTALL)
        if body_match:
            body_text = body_match.group(1).strip()

        prompts = []
        for m in re.finditer(r"## 图(\d+): (.*?)\n\n```(.*?)```", content, re.DOTALL):
            idx = int(m.group(1))
            scene = m.group(2).strip()
            prompt = m.group(3).strip()
            prompts.append({"index": idx, "scene": scene, "prompt": prompt, "is_cover": False, "title": None})

        cover_m = re.search(r"## 封面:\s*(.*?)\n\n```(.*?)```", content, re.DOTALL)
        if cover_m:
            title = cover_m.group(1).strip()
            prompts.append({"index": 0, "scene": f"封面：{title}", "prompt": "", "is_cover": True, "title": title})

        prompts_dir = os.path.dirname(prompts_file) or "."
        os.makedirs(prompts_dir, exist_ok=True)

        print(f"✅ 成功解析 {len(prompts)} 个项目")
        if body_text:
            print(f"✅ 已读取正文内容（{len(body_text)} 字符）")

        story_scenes = [p.get("scene", "") for p in prompts if not p.get("is_cover", False)]
        content_segments = []
        if body_text and story_scenes:
            content_segments = self._split_content(body_text, len(story_scenes))
            print(f"✅ 正文已分段为 {len(content_segments)} 段")

        print(f"\n🎨 开始生成图片（风格: {style}）\n")

        cover_created = False
        for prompt_data in sorted(prompts, key=lambda x: x.get("index", 0)):
            is_cover = prompt_data.get("is_cover", False)

            if is_cover:
                title = prompt_data.get("title", "")
                if title:
                    output_path = os.path.join(prompts_dir, "cover.png")
                    self.create_cover_image(title, style=style, output_path=output_path)
                    cover_created = True
            else:
                idx = prompt_data.get("index", 0)
                scene = prompt_data.get("scene", "")

                segment = ""
                if content_segments and 0 < idx <= len(content_segments):
                    segment = content_segments[idx - 1]
                elif scene:
                    segment = scene

                output_path = os.path.join(prompts_dir, f"image_{idx:02d}.png")
                self.create_story_image(segment, style=style, index=idx, output_path=output_path)

        if not cover_created and prompts:
            first_title = prompts[0].get("title", "") if prompts else "老北京记忆"
            output_path = os.path.join(prompts_dir, "cover.png")
            self.create_cover_image(first_title, style=style, output_path=output_path)

        print(f"\n{'=' * 60}")
        print("✅ 所有图片生成完成！")
        print(f"📁 图片已保存到: {prompts_dir}")
        print(f"{'=' * 60}\n")

    def _split_content(self, content: str, num_parts: int) -> List[str]:
        """智能分段"""
        if not content or not num_parts:
            return []

        clean_content = re.sub(r"\n{3,}", "\n\n", content)
        paragraphs = [p.strip() for p in clean_content.split("\n\n") if p.strip()]

        refined = []
        for para in paragraphs:
            if len(para) > 150:
                sentences = re.split(r"([。！？\n])", para)
                current = ""
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        current += sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
                        if len(current) > 80:
                            refined.append(current.strip())
                            current = ""
                if current.strip():
                    refined.append(current.strip())
            else:
                refined.append(para)

        paragraphs = refined if refined else paragraphs

        if len(paragraphs) < num_parts:
            expanded = []
            for para in paragraphs:
                if len(para) > 100:
                    sentences = re.split(r"([。！？])", para)
                    current = ""
                    for i in range(0, len(sentences), 2):
                        if i < len(sentences):
                            current += sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
                            if len(current) > 50:
                                expanded.append(current.strip())
                                current = ""
                    if current.strip():
                        expanded.append(current.strip())
                else:
                    expanded.append(para)
            paragraphs = expanded

        result = []
        para_idx = 0
        for i in range(num_parts):
            segments = []
            if i == 0:
                if para_idx < len(paragraphs):
                    segments.append(paragraphs[para_idx])
                    para_idx += 1
            elif i < num_parts - 1:
                if para_idx < len(paragraphs):
                    segments.append(paragraphs[para_idx])
                    para_idx += 1
            else:
                while para_idx < len(paragraphs):
                    segments.append(paragraphs[para_idx])
                    para_idx += 1
            result.append("\n\n".join(segments) if segments else "")

        return result


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="模板图片生成器 - 纯编程生成，无需API Key")
    parser.add_argument("-p", "--prompts", help="提示词文件路径（默认：使用最新日期文件夹下的 image_prompts.txt）")
    parser.add_argument("-c", "--config", default="config/config.json", help="配置文件路径（默认：config/config.json）")
    parser.add_argument("-s", "--style", choices=TemplateImageGenerator.TEMPLATE_STYLES, help="图片风格")

    args = parser.parse_args()

    generator = TemplateImageGenerator(config_path=args.config)

    if args.prompts:
        prompts_file = args.prompts
    else:
        output_dir = generator.config.get("output_image_dir", "output/images")
        if os.path.exists(output_dir):
            date_dirs = sorted(
                [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))], reverse=True
            )
            if date_dirs:
                prompts_file = os.path.join(output_dir, date_dirs[0], "image_prompts.txt")
                print(f"💡 使用最新日期文件夹: {date_dirs[0]}")
            else:
                raise FileNotFoundError(f"❌ 在 {output_dir} 中未找到日期文件夹")
        else:
            raise FileNotFoundError(f"❌ 输出目录不存在: {output_dir}")

    style = args.style or generator.config.get("template_style", "retro_chinese")
    generator.generate_all_from_prompts(prompts_file, style=style)


if __name__ == "__main__":
    main()
