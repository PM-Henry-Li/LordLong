#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 image_generator 重构后的功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.text_processor import TextProcessor
from src.image_pipeline import ImageGenerationContext, ImageGenerationPipeline
from src.image_resource_manager import ImageResourceManager


class TestTextProcessor:
    """测试 TextProcessor 类"""

    def test_clean_text_removes_emoji(self):
        """测试清理文字移除emoji"""
        text = "这是一段文字😀🎉"
        cleaned = TextProcessor.clean_text(text)
        assert "😀" not in cleaned
        assert "🎉" not in cleaned
        assert "这是一段文字" in cleaned

    def test_clean_text_preserves_punctuation(self):
        """测试清理文字保留标点符号"""
        text = "你好，世界！这是一个测试。"
        cleaned = TextProcessor.clean_text(text)
        assert "，" in cleaned
        assert "！" in cleaned
        assert "。" in cleaned

    def test_wrap_text_simple(self):
        """测试简单换行功能"""
        # 创建模拟对象
        mock_font = Mock()
        mock_font.size = 60
        mock_draw = Mock()

        # 模拟 textbbox 返回值
        def mock_textbbox(pos, text, font):
            # 简单模拟：每个字符宽度为 font.size
            width = len(text) * font.size
            return (0, 0, width, font.size)

        mock_draw.textbbox = mock_textbbox

        text = "这是一段很长的文字需要换行"
        max_width = 300  # 约5个字符的宽度

        lines = TextProcessor.wrap_text_simple(text, max_width, mock_font, mock_draw, max_lines=3)

        assert len(lines) > 0
        assert len(lines) <= 3


class TestImageGenerationContext:
    """测试 ImageGenerationContext 类"""

    def test_context_initialization(self):
        """测试上下文初始化"""
        context = ImageGenerationContext("test prompt", "1024*1365")
        assert context.prompt == "test prompt"
        assert context.size == "1024*1365"
        assert context.image_url is None
        assert context.error is None
        assert not context.cached

    def test_is_successful(self):
        """测试成功状态检查"""
        context = ImageGenerationContext("test prompt")
        assert not context.is_successful()

        context.image_url = "http://example.com/image.png"
        assert context.is_successful()

        context.error = "some error"
        assert not context.is_successful()


class TestImageResourceManager:
    """测试 ImageResourceManager 类"""

    def test_cleanup_temp_files(self):
        """测试清理临时文件"""
        import tempfile
        import os

        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一些临时文件
            temp_file1 = os.path.join(tmpdir, "test1.tmp")
            temp_file2 = os.path.join(tmpdir, "test2.tmp")
            normal_file = os.path.join(tmpdir, "normal.txt")

            with open(temp_file1, "w") as f:
                f.write("test")
            with open(temp_file2, "w") as f:
                f.write("test")
            with open(normal_file, "w") as f:
                f.write("test")

            # 清理临时文件
            ImageResourceManager.cleanup_temp_files(tmpdir, "*.tmp")

            # 验证临时文件被删除，普通文件保留
            assert not os.path.exists(temp_file1)
            assert not os.path.exists(temp_file2)
            assert os.path.exists(normal_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
