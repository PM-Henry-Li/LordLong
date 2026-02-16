#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文字处理器模块

提供文字换行、截断、清理等功能的统一接口
"""

import re
from typing import List

try:
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class TextProcessor:
    """文字处理器类，提供文字换行、截断、清理等功能"""

    # 标点符号集合
    PUNCTUATION = set(["。", "，", "！", "？", "；", "：", "、", "…", ".", ",", "!", "?", ";", ":"])
    OPENING_PUNCTUATION = set(["（", "(", "【", "[", "《", "<", '"', '"', """, """])
    CLOSING_PUNCTUATION = set(["）", ")", "】", "]", "》", ">", '"', '"', """, """])

    def __init__(self):
        """初始化文字处理器"""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文字，移除特殊符号和emoji

        Args:
            text: 原始文字

        Returns:
            清理后的文字
        """
        if not text:
            return ""

        # 移除emoji（使用更简单的方法）
        # 只保留中文、英文、数字、常用标点
        cleaned = []
        for char in text:
            code = ord(char)
            # 保留：
            # - 基本拉丁字母和数字 (0x0020 - 0x007E)
            # - 中文字符 (0x4E00 - 0x9FFF)
            # - 中文标点 (0x3000 - 0x303F, 0xFF00 - 0xFFEF)
            if (
                0x0020 <= code <= 0x007E  # ASCII可打印字符
                or 0x4E00 <= code <= 0x9FFF  # 中文字符
                or 0x3000 <= code <= 0x303F  # CJK符号和标点
                or 0xFF00 <= code <= 0xFFEF
            ):  # 全角ASCII、全角标点
                cleaned.append(char)

        text = "".join(cleaned)

        # 规范化空白字符
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def wrap_text_simple(text: str, max_width: int, font, draw, max_lines: int = 3) -> List[str]:
        """
        简化的文字换行函数

        Args:
            text: 原始文字
            max_width: 最大宽度
            font: 字体对象
            draw: 绘图对象
            max_lines: 最大行数

        Returns:
            分行后的文字列表
        """
        if not text:
            return []

        lines = []
        current_line = ""

        for char in text:
            test = current_line + char
            try:
                bbox = draw.textbbox((0, 0), test, font=font)
                test_width = bbox[2] - bbox[0]
            except (AttributeError, TypeError, ValueError):
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

        # 后处理：合并单独的标点符号
        result: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if len(line) == 1 and line in TextProcessor.PUNCTUATION and result:
                result[-1] += line
            else:
                result.append(line)

        return result if result else [text[:20]]

    @staticmethod
    def smart_truncate_simple(text: str, max_lines: int, max_width: int, font, draw) -> List[str]:
        """
        简化的智能截断函数

        Args:
            text: 原始文字
            max_lines: 最大行数
            max_width: 最大宽度
            font: 字体对象
            draw: 绘图对象

        Returns:
            截断后的文字行列表
        """
        lines = TextProcessor.wrap_text_simple(text, max_width, font, draw, max_lines + 1)
        if len(lines) <= max_lines:
            return lines

        result = lines[: max_lines - 1] if max_lines > 1 else []
        last = "".join(lines[max_lines - 1 :])

        ellipsis = "…"
        ellipsis_w = draw.textbbox((0, 0), ellipsis, font=font)[2] - draw.textbbox((0, 0), ellipsis, font=font)[0]
        available = max_width - ellipsis_w - 5

        last_line = ""
        for char in last:
            test = last_line + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= available:
                last_line = test
            else:
                break

        if last_line:
            result.append(last_line + ellipsis)
        elif result:
            prev = result[-1]
            while len(prev) > 0:
                test = prev + ellipsis
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    result[-1] = test
                    break
                prev = prev[:-1]

        return result if result else [ellipsis]

    @staticmethod
    def wrap_text(text: str, max_width: int, font, draw) -> List[str]:
        """
        将文字按宽度自动换行，智能处理标点符号

        Args:
            text: 原始文字
            max_width: 最大宽度
            font: 字体对象
            draw: 绘图对象

        Returns:
            分行后的文字列表
        """
        if not text:
            return []

        lines = []
        current_line = ""

        for char in text:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line = test_line
            else:
                # 检查是否需要将标点符号移到下一行
                if current_line and char in TextProcessor.PUNCTUATION:
                    lines.append(current_line)
                    current_line = char
                elif current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line = char

        if current_line:
            lines.append(current_line)

        return lines

    @staticmethod
    def smart_truncate(text: str, max_lines: int, max_width: int, font, draw) -> List[str]:
        """
        智能截断文字，在合适位置添加省略号

        Args:
            text: 原始文字
            max_lines: 最大行数
            max_width: 最大宽度
            font: 字体对象
            draw: 绘图对象

        Returns:
            截断后的文字行列表
        """
        if not text:
            return []

        all_lines = TextProcessor.wrap_text(text, max_width, font, draw)

        if len(all_lines) <= max_lines:
            return all_lines

        result_lines = all_lines[: max_lines - 1]

        ellipsis = "…"
        ellipsis_bbox = draw.textbbox((0, 0), ellipsis, font=font)
        ellipsis_width = ellipsis_bbox[2] - ellipsis_bbox[0]
        available_for_last_line = max_width - ellipsis_width - 5

        remaining_text = "".join(all_lines[max_lines - 1 :])
        last_line = ""

        for char in remaining_text:
            test_line = last_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= available_for_last_line:
                last_line = test_line
                if char in TextProcessor.PUNCTUATION and len(last_line) > 1:
                    break
            else:
                if len(last_line) > 1:
                    for i in range(len(last_line) - 1, 0, -1):
                        if last_line[i] in TextProcessor.PUNCTUATION:
                            last_line = last_line[: i + 1]
                            break
                break

        if last_line:
            result_lines.append(last_line + ellipsis)
        else:
            if result_lines:
                result_lines[-1] = result_lines[-1] + ellipsis
            else:
                result_lines.append(ellipsis)

        return result_lines

    @staticmethod
    def split_content_by_scenes(content: str, scenes: List[str]) -> List[str]:
        """
        根据图片场景描述，智能分段正文内容

        Args:
            content: 完整正文内容
            scenes: 场景描述列表

        Returns:
            分段后的正文内容列表
        """
        if not content or not scenes:
            return []

        # 清理内容
        clean_content = re.sub(r"\n{3,}", "\n\n", content)
        paragraphs = [p.strip() for p in clean_content.split("\n\n") if p.strip()]

        # 如果段落很长，进一步分割
        refined_paragraphs = []
        for para in paragraphs:
            if len(para) > 120:
                sentences = re.split(r"([。！？\n])", para)
                current_sentence = ""
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        current_sentence += sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
                        if len(current_sentence) > 100:
                            refined_paragraphs.append(current_sentence.strip())
                            current_sentence = ""
                if current_sentence.strip():
                    refined_paragraphs.append(current_sentence.strip())
            else:
                refined_paragraphs.append(para)

        paragraphs = refined_paragraphs if refined_paragraphs else paragraphs

        # 分配段落到图片
        result = []
        para_index = 0

        for i, scene in enumerate(scenes):
            segments_for_image = []

            if i == 0:
                if para_index < len(paragraphs):
                    segments_for_image.append(paragraphs[para_index])
                    para_index += 1
            elif i < len(scenes) - 1:
                if para_index < len(paragraphs):
                    segments_for_image.append(paragraphs[para_index])
                    para_index += 1
            else:
                while para_index < len(paragraphs):
                    segments_for_image.append(paragraphs[para_index])
                    para_index += 1

            result.append("\n\n".join(segments_for_image) if segments_for_image else "")

        return result
