#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片资源管理器模块

提供图片资源的统一管理，确保资源正确释放
"""

import os
import requests
from contextlib import contextmanager

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ImageResourceManager:
    """图片资源管理器，使用上下文管理器确保资源正确释放"""

    @staticmethod
    @contextmanager
    def open_image(image_path: str, mode: str = "RGB"):
        """
        打开图片的上下文管理器

        Args:
            image_path: 图片路径
            mode: 图片模式（默认RGB）

        Yields:
            PIL Image对象
        """
        if not HAS_PIL:
            raise ImportError("未安装PIL/Pillow")

        img = None
        try:
            img = Image.open(image_path)
            if mode and img.mode != mode:
                img = img.convert(mode)
            yield img
        finally:
            if img is not None:
                img.close()

    @staticmethod
    @contextmanager
    def download_image(image_url: str, save_path: str, chunk_size: int = 8192):
        """
        下载图片的上下文管理器

        Args:
            image_url: 图片URL
            save_path: 保存路径
            chunk_size: 下载块大小

        Yields:
            保存路径
        """
        # 确保目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        response = None
        file_handle = None
        temp_path = save_path + ".tmp"

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(image_url, headers=headers, stream=True, timeout=30)

            if response.status_code != 200:
                raise Exception(f"下载图片失败: HTTP {response.status_code}")

            file_handle = open(temp_path, "wb")
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file_handle.write(chunk)

            file_handle.close()
            file_handle = None

            # 下载成功，重命名临时文件
            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_path, save_path)

            yield save_path

        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise e
        finally:
            if file_handle is not None:
                try:
                    file_handle.close()
                except Exception:
                    pass
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

    @staticmethod
    @contextmanager
    def create_image(width: int, height: int, mode: str = "RGB", color=None):
        """
        创建新图片的上下文管理器

        Args:
            width: 宽度
            height: 高度
            mode: 图片模式
            color: 背景颜色

        Yields:
            PIL Image对象
        """
        if not HAS_PIL:
            raise ImportError("未安装PIL/Pillow")

        img = None
        try:
            img = Image.new(mode, (width, height), color)
            yield img
        finally:
            if img is not None:
                img.close()

    @staticmethod
    def save_image_safely(img, save_path: str, format: str = "PNG", **kwargs):
        """
        安全地保存图片

        Args:
            img: PIL Image对象
            save_path: 保存路径
            format: 图片格式
            **kwargs: 其他保存参数
        """
        # 确保目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

        # 使用临时文件，确保原子性
        temp_path = save_path + ".tmp"

        try:
            img.save(temp_path, format, **kwargs)

            # 保存成功，替换原文件
            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_path, save_path)

        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise e

    @staticmethod
    def cleanup_temp_files(directory: str, pattern: str = "*.tmp"):
        """
        清理临时文件

        Args:
            directory: 目录路径
            pattern: 文件模式
        """
        if not os.path.exists(directory):
            return

        import glob

        temp_files = glob.glob(os.path.join(directory, pattern))

        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass
