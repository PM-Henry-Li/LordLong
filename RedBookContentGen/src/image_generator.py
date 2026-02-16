#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成器
读取图片提示词文件，调用通义万相API生成图片
"""

import os
import re
import time
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING, Any

import requests

from src.core.logger import Logger
from src.text_processor import TextProcessor
from src.image_pipeline import ImageGenerationPipeline
from src.image_resource_manager import ImageResourceManager

if TYPE_CHECKING:
    from src.core.config_manager import ConfigManager
    from PIL import Image, ImageDraw as ImageDrawModule, ImageFont

try:
    from PIL import Image, ImageDraw, ImageFont

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Logger.warning("未安装PIL/Pillow，无法使用文字叠加功能。请运行: pip install Pillow", logger_name="image_generator")


class ImageGenerator:
    """图片生成器"""

    def __init__(self, config_manager: Optional["ConfigManager"] = None, config_path: str = "config/config.json"):
        """
        初始化生成器

        Args:
            config_manager: ConfigManager 实例（推荐使用）
            config_path: 配置文件路径（向后兼容，当 config_manager 为 None 时使用）
        """
        # 支持两种初始化方式：新方式（ConfigManager）和旧方式（config_path）
        if config_manager is not None:
            self.config_manager = config_manager
            self._use_config_manager = True
        else:
            # 向后兼容：如果没有传入 ConfigManager，则使用旧的配置加载方式
            from src.core.config_manager import ConfigManager

            self.config_manager = ConfigManager(config_path)
            self._use_config_manager = True

        # 初始化日志系统
        Logger.initialize(self.config_manager)
        self.logger = Logger.get_logger("image_generator")

        # API Key检查
        self.api_key = self.config_manager.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ 未找到API Key，请设置环境变量 OPENAI_API_KEY 或在config.json中配置 openai_api_key")

        # 通义万相API配置（文生图）
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.image_generation_url = f"{self.base_url}/services/aigc/text2image/image-synthesis"
        self.task_status_url = f"{self.base_url}/tasks"

        # 图片生成模型
        self.image_model = self.config_manager.get("image_model", "jimeng_t2i_v40")

        # AI改写配置
        self.enable_ai_rewrite = self.config_manager.get("enable_ai_rewrite", True)
        self.rewrite_model = self.config_manager.get("rewrite_model", "qwen-max")

        # 通义千问API配置(用于文案改写)
        self.llm_base_url = self.config_manager.get(
            "openai_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 可疑内容记录文件
        self.suspicious_content_file = None

        # 初始化缓存
        self._cache_enabled = self.config_manager.get("cache.enabled", False)
        if self._cache_enabled:
            from src.core.cache_manager import CacheManager

            cache_ttl = self.config_manager.get("cache.ttl", 86400)  # 默认24小时
            cache_max_size = self.config_manager.get("cache.max_size", 1000)

            # 确保 max_size 是整数
            if isinstance(cache_max_size, str):
                # 如果是字符串（如 "1GB"），使用默认值
                cache_max_size = 1000

            self.cache = CacheManager(max_size=cache_max_size, default_ttl=cache_ttl)
            Logger.info("缓存已启用", logger_name="image_generator", ttl=cache_ttl, max_size=cache_max_size)
        else:
            self.cache = None
            Logger.info("缓存已禁用", logger_name="image_generator")

        # 初始化速率限制器
        self._init_rate_limiter()

        # 初始化图片生成管道
        self._pipeline = None  # 延迟初始化

    def _init_rate_limiter(self) -> None:
        """初始化速率限制器"""
        from src.core.rate_limiter import RateLimiter

        # 检查是否启用速率限制
        rate_limit_enabled = self.config_manager.get("rate_limit.image.enable_rate_limit", True)

        if rate_limit_enabled:
            # 获取速率限制配置
            rpm = self.config_manager.get("rate_limit.image.requests_per_minute", 10)

            # 创建速率限制器
            # RPM 限制器：每分钟请求数
            self.rpm_limiter = RateLimiter(rate=rpm / 60.0, capacity=rpm)

            self._rate_limit_enabled = True

            Logger.info("速率限制已启用", logger_name="image_generator", requests_per_minute=rpm)
        else:
            self.rpm_limiter = None
            self._rate_limit_enabled = False

            Logger.info("速率限制已禁用", logger_name="image_generator")

    def _get_image_provider(self):
        """
        根据配置获取图片生成服务提供商（工厂方法）

        Returns:
            BaseImageProvider 实例
        """
        from src.image_providers.aliyun_provider import AliyunImageProvider
        from src.image_providers.volcengine_provider import VolcengineImageProvider

        provider_name = self.config_manager.get("image_api_provider", "aliyun")

        if provider_name == "volcengine":
            Logger.info(
                "使用火山引擎即梦 AI 图片生成服务",
                logger_name="image_generator"
            )
            return VolcengineImageProvider(
                config_manager=self.config_manager,
                logger=self.logger,
                rate_limiter=self.rpm_limiter,
                cache=self.cache
            )
        elif provider_name == "aliyun":
            Logger.info(
                "使用阿里云通义万相图片生成服务",
                logger_name="image_generator"
            )
            return AliyunImageProvider(
                config_manager=self.config_manager,
                logger=self.logger,
                rate_limiter=self.rpm_limiter,
                cache=self.cache
            )
        else:
            Logger.warning(
                f"未知的图片生成服务提供商: {provider_name}，使用默认值 aliyun",
                logger_name="image_generator"
            )
            return AliyunImageProvider(
                config_manager=self.config_manager,
                logger=self.logger,
                rate_limiter=self.rpm_limiter,
                cache=self.cache
            )

    def _get_pipeline(self) -> ImageGenerationPipeline:
        """获取图片生成管道实例（延迟初始化）"""
        if self._pipeline is None:
            self._pipeline = ImageGenerationPipeline(self)
        return self._pipeline

    def get_rate_limit_stats(self) -> Optional[Dict]:
        """
        获取速率限制统计信息

        Returns:
            速率限制统计字典，如果速率限制未启用则返回 None
        """
        if not self._rate_limit_enabled:
            return None

        stats = {
            "enabled": True,
            "rpm": {
                "available_tokens": self.rpm_limiter.get_available_tokens() if self.rpm_limiter else None,
                "capacity": self.rpm_limiter.get_capacity() if self.rpm_limiter else None,
                "rate": self.rpm_limiter.get_rate() if self.rpm_limiter else None,
            },
        }

        return stats

    def check_content_safety(self, prompt: str, content_type: str = "prompt") -> Tuple[bool, str]:
        """
        检查内容是否可能触发内容审核失败

        注意：此函数只检查真正敏感的内容，不会误杀正常的历史文化内容
        （如天安门、故宫、广场等历史文化地标是正常的）

        Args:
            prompt: 要检查的内容（提示词或正文）
            content_type: 内容类型（"prompt" 或 "content"）

        Returns:
            (是否安全, 修改后的内容)
        """
        if not prompt:
            return True, prompt

        # 真正敏感的词汇（只检查明显不当的内容）
        # 注意：不包含"天安门"、"广场"、"故宫"等正常历史文化词汇
        sensitive_keywords = [
            # 明显政治敏感（不含正常历史描述）
            "革命",
            "暴动",
            "叛乱",
            "政变",
            # 明显暴力
            "血腥",
            "杀戮",
            "屠杀",
            "武器",
            "枪",
            "刀",
            # 明显色情
            "色情",
            "裸露",
            "情色",
            # 其他明显敏感
            "恐怖",
            "爆炸",
            "毒品",
            "赌博",
        ]

        # 检查是否包含敏感词
        # 注意：中文没有词边界，所以直接检查是否包含关键词
        # 但只检查明显敏感的词，不误杀正常历史文化内容
        found_keywords = []
        for keyword in sensitive_keywords:
            if keyword in prompt:
                found_keywords.append(keyword)

        if found_keywords:
            # 尝试移除敏感词
            modified_prompt = prompt
            for keyword in found_keywords:
                modified_prompt = modified_prompt.replace(keyword, "")
            # 清理多余空格
            modified_prompt = re.sub(r"\s+", " ", modified_prompt).strip()
            return False, modified_prompt

        return True, prompt

    def _generate_cache_key(self, prompt: str, size: str = "1024*1365") -> str:
        """
        生成缓存键（基于提示词和尺寸的 hash）

        Args:
            prompt: 图片提示词
            size: 图片尺寸

        Returns:
            缓存键
        """
        import hashlib
        import json

        # 构建缓存键内容
        cache_content = {"prompt": prompt, "size": size, "model": self.image_model}

        # 生成 hash
        content_str = json.dumps(cache_content, sort_keys=True, ensure_ascii=False)
        hash_value = hashlib.sha256(content_str.encode("utf - 8")).hexdigest()

        return f"image_gen:{hash_value}"

    def get_cache_stats(self) -> Optional[Dict]:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典，如果缓存未启用则返回 None
        """
        if not self._cache_enabled or self.cache is None:
            return None

        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        if self._cache_enabled and self.cache is not None:
            self.cache.clear()
            Logger.info("缓存已清空", logger_name="image_generator")

    def save_suspicious_content(self, prompts_dir: str, content: str, content_type: str, reason: str) -> None:
        """
        保存可疑内容到文件，供用户修改

        Args:
            prompts_dir: 输出目录
            content: 可疑内容
            content_type: 内容类型
            reason: 失败原因
        """
        if self.suspicious_content_file is None:
            self.suspicious_content_file = os.path.join(prompts_dir, "suspicious_content.txt")
            with open(self.suspicious_content_file, "w", encoding="utf - 8") as f:
                f.write("# 可疑内容记录\n\n")
                f.write("以下内容在生成图片时可能触发内容审核失败，请手动修改后重新生成。\n\n")
                f.write("=" * 60 + "\n\n")

        with open(self.suspicious_content_file, "a", encoding="utf - 8") as f:
            f.write(f"## {content_type}\n\n")
            f.write(f"**失败原因**: {reason}\n\n")
            f.write(f"**原始内容**:\n```\n{content}\n```\n\n")
            f.write("**建议**: 请移除或替换上述敏感词汇，然后重新运行脚本。\n\n")
            f.write("-" * 60 + "\n\n")

    def parse_prompts_file(self, prompts_file: str) -> Tuple[List[Dict], str]:
        """
        解析图片提示词文件

        Args:
            prompts_file: 提示词文件路径

        Returns:
            (提示词列表, 正文内容)
        """
        if not os.path.exists(prompts_file):
            raise FileNotFoundError(f"❌ 提示词文件不存在: {prompts_file}")

        with open(prompts_file, "r", encoding="utf - 8") as f:
            content = f.read()

        # 解析正文内容
        body_text = ""
        body_match = re.search(r"## 正文内容\n\n(.*?)\n\n---", content, re.DOTALL)
        if body_match:
            body_text = body_match.group(1).strip()

        # 解析提示词：图1 - 4（故事图）+ 封面
        prompts = []
        # 匹配 ## 图N: 场景\n\n``` prompt ```
        for m in re.finditer(r"## 图(\d+): (.*?)\n\n```(.*?)```", content, re.DOTALL):
            idx = int(m.group(1))
            scene = m.group(2).strip()
            prompt = m.group(3).strip()
            prompts.append({"index": idx, "scene": scene, "prompt": prompt, "is_cover": False, "title": None})

        # 匹配 ## 封面: 短标题\n\n``` prompt ```
        cover_m = re.search(r"## 封面:\s*(.*?)\n\n```(.*?)```", content, re.DOTALL)
        if cover_m:
            title = cover_m.group(1).strip()
            prompt = cover_m.group(2).strip()
            prompts.append({"index": 0, "scene": f"封面：{title}", "prompt": prompt, "is_cover": True, "title": title})

        if not prompts:
            raise ValueError(f"❌ 无法从文件中解析出提示词: {prompts_file}")

        n_cover = sum(1 for p in prompts if p.get("is_cover"))
        Logger.info(
            f"成功解析 {len(prompts)} 个提示词" + ("（含 1 张封面）" if n_cover else ""),
            logger_name="image_generator",
            prompt_count=len(prompts),
            has_cover=n_cover > 0,
        )
        if body_text:
            Logger.info(
                f"已读取正文内容（{len(body_text)} 字符）", logger_name="image_generator", content_length=len(body_text)
            )
        return prompts, body_text

    def generate_image_async(self, prompt: str, index: int, is_cover: bool = False) -> str:
        """
        异步生成单张图片

        Args:
            prompt: 图片提示词
            index: 图片索引
            is_cover: 是否为封面图

        Returns:
            图片URL
        """
        # 使用提供商接口生成图片
        provider = self._get_image_provider()
        return provider.generate(prompt, "1024*1365", is_cover=is_cover)

    def generate_single_image(self, prompt: str, size: str = "1024*1365") -> Optional[str]:
        """
        为Web API生成单张图片

        Args:
            prompt: 图片提示词
            size: 图片尺寸，格式为 "宽*高"，如 "1024*1365" (3:4) 或 "1080*1080" (1:1)

        Returns:
            图片URL，失败返回None
        """
        # 使用提供商接口生成图片
        provider = self._get_image_provider()
        return provider.generate(prompt, size)

    def generate_image_sync(self, prompt: str, size: str = "1024*1365") -> Optional[str]:
        """
        使用千问 Qwen-Image 同步接口生成图片（推荐）

        Args:
            prompt: 图片提示词
            size: 图片尺寸，格式为 "宽*高"，如 "1024*1365" (3:4)

        Returns:
            图片URL，失败返回None
        """
        # 速率限制：获取令牌
        if self._rate_limit_enabled and self.rpm_limiter:
            Logger.debug(
                "正在获取 RPM 令牌",
                logger_name="image_generator",
                available_tokens=self.rpm_limiter.get_available_tokens(),
            )

            success = self.rpm_limiter.wait_for_token(tokens=1, timeout=120)
            if not success:
                Logger.warning("获取图片生成 RPM 令牌超时", logger_name="image_generator")
                print("  ⚠️  速率限制：请求超时")
                return None

            Logger.debug(
                "✅ 已获取 RPM 令牌",
                logger_name="image_generator",
                remaining_tokens=self.rpm_limiter.get_available_tokens(),
            )

        try:
            # 清理提示词
            clean_prompt = re.sub(r"--ar\s*\d+:\d+", "", prompt)
            clean_prompt = re.sub(r"--v\s*\d+(\.\d+)?", "", clean_prompt)
            clean_prompt = re.sub(r"--style\s+\w+", "", clean_prompt)
            clean_prompt = clean_prompt.strip()

            # 千问 Qwen-Image 同步接口
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            # 解析尺寸
            width, height = 1024, 1365
            if size and "*" in size:
                parts = size.split("*")
                width = int(parts[0])
                height = int(parts[1])

            data = {
                "model": self.image_model,
                "input": {"messages": [{"role": "user", "content": [{"type": "text", "text": clean_prompt}]}]},
                "parameters": {"size": f"{width}*{height}"},
            }

            print("  📤 正在调用千问 Qwen-Image 同步接口...")

            # 优化: 降低超时时间到60秒,同步接口通常10 - 30秒内返回
            response = requests.post(url, headers=headers, json=data, timeout=60)

            if response.status_code != 200:
                print(f"  ❌ 请求失败: {response.status_code} - {response.text[:200]}")
                return None

            resp_json = response.json()

            # 解析响应 - 千问 Qwen-Image 同步接口格式
            if "output" in resp_json:
                output = resp_json.get("output", {})

                # 方式1: 直接 image_url 字段
                image_url = output.get("image_url")
                if image_url:
                    print("  ✅ 图片生成成功")
                    return image_url

                # 方式2: choices[0].message.content[0].image
                choices = output.get("choices", [])
                if choices:
                    first_choice = choices[0]
                    message = first_choice.get("message", {})
                    content = message.get("content", [])
                    if content and isinstance(content, list) and len(content) > 0:
                        first_content = content[0]
                        if isinstance(first_content, dict):
                            image_url = first_content.get("image")
                            if image_url:
                                print("  ✅ 图片生成成功")
                                return image_url

            # 检查是否有错误
            if "error" in resp_json:
                error_msg = resp_json.get("error", {})
                if isinstance(error_msg, dict):
                    print(f"  ❌ API错误: {error_msg.get('message', '未知错误')}")
                else:
                    print(f"  ❌ API错误: {error_msg}")
                return None

            print(f"  ❌ 响应格式未知: {resp_json}")
            return None

        except Exception as e:
            print(f"  ❌ 图片生成失败: {e}")
            return None

    def _wait_for_task_completion(self, task_id: str, max_wait: int = 180) -> str:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            max_wait: 最大等待时间（秒）

        Returns:
            图片URL
        """
        status_url = f"{self.task_status_url}/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        start_time = time.time()
        # 优化: 缩短轮询间隔,从3秒降到2秒,加快获取结果
        poll_interval = 2

        while time.time() - start_time < max_wait:
            response = requests.get(status_url, headers=headers)

            if response.status_code != 200:
                raise Exception(f"❌ 查询任务状态失败: {response.status_code} - {response.text}")

            resp_json = response.json()
            task_status = resp_json.get("output", {}).get("task_status", "")

            if task_status == "SUCCEEDED":
                # 获取图片URL（兼容 output.results[0].url 与 output.choices[0].image）
                output = resp_json.get("output", {})
                results = output.get("results", [])
                if results and "url" in results[0]:
                    image_url = results[0]["url"]
                    print("  ✅ 图片生成成功")
                    return image_url
                choices = output.get("choices", [])
                if choices and choices[0].get("image"):
                    image_url = choices[0]["image"]
                    print("  ✅ 图片生成成功")
                    return image_url
                raise Exception("❌ 任务成功但未返回图片URL")

            elif task_status == "FAILED":
                raise Exception(f"❌ 任务失败: {resp_json}")

            elif task_status in ["PENDING", "RUNNING", "INITIALIZING"]:
                print(f"  ⏳ 等待中... 状态: {task_status}", end="\r")
                time.sleep(poll_interval)

            else:
                print(f"  ⚠️  未知状态: {task_status}")
                time.sleep(poll_interval)

        raise Exception(f"❌ 任务超时（{max_wait}秒）")

    def download_image(self, image_url: str, save_path: str) -> None:
        """
        下载图片

        Args:
            image_url: 图片URL
            save_path: 保存路径
        """
        with ImageResourceManager.download_image(image_url, save_path):
            print(f"  💾 已保存: {save_path}")

    def clean_text_for_display(self, text: str) -> str:
        """
        清理文字用于显示（移除emoji和特殊符号）

        Args:
            text: 原始文字

        Returns:
            清理后的文字
        """
        return TextProcessor.clean_text(text)

    def _load_font(self, size: int) -> Any:
        """
        加载指定大小的字体

        Args:
            size: 字体大小

        Returns:
            字体对象（ImageFont.FreeTypeFont 或 ImageFont.ImageFont）
        """
        font_paths = [
            # macOS - 优先使用粗体字体
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            # Windows - 优先黑体
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simkai.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            # Linux
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if font_path.endswith(".ttc"):
                        from PIL import ImageFont

                        try:
                            return ImageFont.truetype(font_path, size, index=1)
                        except Exception:
                            return ImageFont.truetype(font_path, size, index=0)
                    else:
                        return ImageFont.truetype(font_path, size)
                except Exception:
                    continue

        # 如果找不到字体，使用默认字体
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _calculate_font_size(self, height: int, is_cover: bool) -> int:
        """
        根据图片类型计算字体大小

        Args:
            height: 图片高度
            is_cover: 是否为封面图

        Returns:
            字体大小（像素）
        """
        if is_cover:
            return int(height * 0.10)  # 封面：字体大小为图片高度的10%
        else:
            return int(height * 0.06)  # 故事图：字体大小为图片高度的6%

    def _calculate_text_metrics(self, text: str, font: Any, draw: Any, width: int) -> Dict[str, int]:
        """
        计算文字的各种度量信息

        Args:
            text: 文字内容
            font: 字体对象
            draw: 绘图对象
            width: 图片宽度

        Returns:
            包含文字度量信息的字典
        """
        # 计算可用宽度（留出左右边距）
        margin = int(width * 0.1)
        available_width = width - 2 * margin

        # 计算文字高度
        test_chars = "测\n测"
        bbox_test = draw.textbbox((0, 0), test_chars, font=font)

        if bbox_test[3] - bbox_test[1] < font.size * 1.5:
            test_chars = "测"
            bbox_test = draw.textbbox((0, 0), test_chars, font=font)
            text_height = bbox_test[3] - bbox_test[1]
        else:
            text_height = (bbox_test[3] - bbox_test[1]) / 2

        # 计算文字宽度
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        return {
            "available_width": available_width,
            "text_width": text_width,
            "text_height": text_height,
            "margin": margin,
        }

    def _adjust_font_to_fit(
        self, text: str, font: Any, draw: Any, available_width: int, height: int, max_font_size: int
    ) -> Tuple[Any, int, int, int]:
        """
        调整字体大小以适应可用宽度

        Args:
            text: 文字内容
            font: 当前字体对象
            draw: 绘图对象
            available_width: 可用宽度
            height: 图片高度
            max_font_size: 最大字体大小

        Returns:
            (调整后的字体对象, 字体大小, 文字宽度, 文字高度)
        """
        min_font_size = int(height * 0.06)
        optimal_font_size = max_font_size
        optimal_font = font

        for test_size in range(max_font_size, min_font_size - 1, -2):
            try:
                test_font = self._load_font(test_size)
                test_bbox = draw.textbbox((0, 0), text, font=test_font)
                test_width = test_bbox[2] - test_bbox[0]
                if test_width <= available_width:
                    optimal_font_size = test_size
                    optimal_font = test_font
                    break
            except Exception:
                continue

        # 重新计算文字尺寸
        bbox = draw.textbbox((0, 0), text, font=optimal_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        return optimal_font, optimal_font_size, text_width, text_height

    def _process_text_wrapping(self, text: str, available_width: int, font: Any, draw: Any, max_lines: int = 3) -> List[str]:
        """
        处理文字换行和截断

        Args:
            text: 文字内容
            available_width: 可用宽度
            font: 字体对象
            draw: 绘图对象
            max_lines: 最大行数

        Returns:
            处理后的文字行列表
        """
        lines = self._wrap_text(text, available_width, font, draw)

        # 如果文字超过最大行数,尝试AI改写
        if len(lines) > max_lines:
            estimated_max_chars = self._estimate_max_chars(available_width, max_lines, font, draw)
            print(f"  📏 文字超长({len(text)}字),尝试AI改写到{estimated_max_chars}字以内...")

            rewritten_text = self.rewrite_text_for_display(text, estimated_max_chars)

            if rewritten_text and rewritten_text != text:
                text = rewritten_text
                lines = self._wrap_text(text, available_width, font, draw)

            if len(lines) > max_lines:
                print("  ✂️  改写后仍超长,使用智能截断")
                lines = self._smart_truncate(text, max_lines, available_width, font, draw)

        return lines

    def _calculate_line_metrics(self, lines: List[str], font: Any, draw: Any, is_cover: bool) -> Dict[str, int]:
        """
        计算行高和总高度

        Args:
            lines: 文字行列表
            font: 字体对象
            draw: 绘图对象
            is_cover: 是否为封面图

        Returns:
            包含行度量信息的字典
        """
        test_bbox = draw.textbbox((0, 0), "测", font=font)
        text_height = test_bbox[3] - test_bbox[1]

        try:
            ascent, descent = font.getmetrics()
            base_line_height = ascent + descent
        except Exception:
            base_line_height = int(text_height)

        n_lines = max(1, len(lines))

        # 行间距比例
        line_spacing_ratio = 0.25 if is_cover else 0.30
        line_spacing = int(base_line_height * line_spacing_ratio)

        # 行高计算
        line_height = base_line_height + line_spacing
        min_line_height = int(base_line_height * 1.2)
        max_line_height = int(base_line_height * 1.6)
        line_height = max(min_line_height, min(line_height, max_line_height))

        total_height = (n_lines - 1) * line_height + base_line_height

        return {
            "line_height": line_height,
            "total_height": total_height,
            "text_height": text_height,
            "base_line_height": base_line_height,
        }

    def _calculate_start_position(
        self,
        position: str,
        height: int,
        total_height: int,
        lines: List[str],
        line_height: int,
        text_height: int,
        available_width: int,
        font: Any,
        draw: Any,
        is_cover: bool,
    ) -> int:
        """
        计算文字起始Y位置

        Args:
            position: 位置（"top"或"bottom"）
            height: 图片高度
            total_height: 文字总高度
            lines: 文字行列表
            line_height: 行高
            text_height: 单行文字高度
            available_width: 可用宽度
            font: 字体对象
            draw: 绘图对象
            is_cover: 是否为封面图

        Returns:
            起始Y坐标
        """
        margin_y = int(height * 0.08)

        if position == "bottom":
            start_y = height - total_height - int(height * 0.15)

            if start_y < height * 0.55:
                start_y = int(height * 0.55)

            # 检查是否超出底部边界
            last_line_y = start_y + (len(lines) - 1) * line_height
            margin_bottom = int(height * 0.08)

            if last_line_y + text_height > height - margin_bottom:
                available_height = height - start_y - margin_bottom
                max_lines_by_height = int(available_height / line_height)
                max_lines = min(max_lines_by_height, 3)

                if max_lines < 1:
                    max_lines = 1

                if len(lines) > max_lines:
                    lines = self._smart_truncate(lines[0] if lines else "", max_lines, available_width, font, draw)
                    len(lines)
                    # 需要重新计算总高度
                    line_metrics = self._calculate_line_metrics(lines, font, draw, is_cover)
                    total_height = line_metrics["total_height"]
                    start_y = height - total_height - margin_bottom
        else:
            # 顶部位置
            start_y = int(height * 0.20)
            if total_height > height * 0.3:
                start_y = int(height * 0.15)
            if start_y < int(height * 0.1):
                start_y = int(height * 0.1)

        # 确保不超出边界
        if start_y + total_height > height - margin_y:
            start_y = height - total_height - margin_y
        if start_y < margin_y:
            start_y = margin_y

        return start_y

    def _draw_text_lines(
        self, img: Any, lines: List[str], start_y: int, line_height: int, font: Any, font_size: int, is_cover: bool
    ) -> None:
        """
        在图片上绘制文字行

        Args:
            img: PIL图片对象
            lines: 文字行列表
            start_y: 起始Y坐标
            line_height: 行高
            font: 字体对象
            font_size: 字体大小
            is_cover: 是否为封面图
        """
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 设置颜色
        if is_cover:
            text_color = (101, 67, 33)
            shadow_color = (255, 255, 255)
        else:
            text_color = (255, 255, 255)
            shadow_color = (0, 0, 0)

        shadow_offset = max(2, int(font_size * 0.05))
        margin_x = int(width * 0.08)
        margin_y = int(height * 0.08)

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2

            # 确保不超出左右边界
            if x < margin_x:
                x = margin_x
            elif x + line_width > width - margin_x:
                x = width - line_width - margin_x

            y = start_y + i * line_height

            # 确保不超出上下边界
            if y < margin_y or y + line_height > height - margin_y:
                continue

            # 绘制描边
            for dx in range(-shadow_offset, shadow_offset + 1):
                for dy in range(-shadow_offset, shadow_offset + 1):
                    if abs(dx) + abs(dy) <= shadow_offset:
                        draw.text((x + dx, y + dy), line, font=font, fill=shadow_color)

            # 绘制主文字
            draw.text((x, y), line, font=font, fill=text_color)

    def _estimate_max_chars(self, max_width: int, max_lines: int, font: Any, draw: Any) -> int:
        """
        估算给定宽度和行数下,最多可以容纳多少字符

        Args:
            max_width: 每行最大宽度(像素)
            max_lines: 最大行数
            font: 字体对象
            draw: 绘图对象

        Returns:
            估算的最大字符数
        """
        # 使用常见中文字符测试平均宽度
        test_chars = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"

        # 计算单个字符平均宽度
        total_width = 0
        sample_size = min(50, len(test_chars))
        for char in test_chars[:sample_size]:
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            total_width += char_width

        avg_char_width = total_width / sample_size if sample_size > 0 else font.size

        # 估算每行字符数
        chars_per_line = int(max_width / avg_char_width)

        # 总字符数 = 每行字符数 × 行数,留10%余量
        estimated_chars = int(chars_per_line * max_lines * 0.9)

        return max(10, estimated_chars)  # 至少10个字符

    def rewrite_text_for_display(self, text: str, max_chars: int, context: str = "") -> str:
        """
        使用AI改写文案,使其符合长度限制且语义通顺

        Args:
            text: 原始文案
            max_chars: 最大字符数
            context: 上下文信息(如场景描述)

        Returns:
            改写后的文案,如果改写失败则返回原文
        """
        # 如果未启用AI改写,直接返回原文
        if not self.enable_ai_rewrite:
            return text

        # 如果文案本身就不长,无需改写
        if len(text) <= max_chars:
            return text

        try:
            # 构建改写提示词
            prompt = """请将以下文案精简改写,要求:
1. 保留核心信息和关键内容
2. 语言通顺流畅,符合小红书风格
3. 控制在{max_chars}字以内
4. 不要添加任何额外说明,只输出改写后的文案

原文案({len(text)}字):
{text}

改写后的文案:"""

            # 调用通义千问API
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            data = {
                "model": self.rewrite_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": max_chars * 2,  # 留足够的token空间
            }

            response = requests.post(f"{self.llm_base_url}/chat/completions", headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                rewritten = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

                # 验证改写结果
                if rewritten and len(rewritten) <= max_chars * 1.1:  # 允许10%误差
                    print(f"  ✨ AI改写成功: {len(text)}字 → {len(rewritten)}字")
                    return rewritten
                else:
                    print("  ⚠️  AI改写结果不符合要求,使用原文")
                    return text
            else:
                print(f"  ⚠️  AI改写API调用失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"  ⚠️  AI改写失败: {e}")
            return text

    def add_text_overlay(
        self,
        image_path: str,
        text: str,
        output_path: Optional[str] = None,
        is_cover: bool = True,
        position: str = "top",
    ) -> None:
        """
        在图片上叠加文字（用于封面图和故事图）

        Args:
            image_path: 图片路径
            text: 要叠加的文字
            output_path: 输出路径（如果为None，则覆盖原文件）
            is_cover: 是否为封面图（True=封面，False=故事图）
            position: 文字位置（"top"=顶部，"bottom"=底部）
        """
        if not HAS_PIL:
            print("  ⚠️  跳过文字叠加：未安装PIL/Pillow")
            return

        if not text or not text.strip():
            print("  ⚠️  跳过文字叠加：文字为空")
            return

        # 清理文字
        text = self.clean_text_for_display(text)
        if not text or not text.strip():
            print("  ⚠️  跳过文字叠加：清理后文字为空")
            return

        try:
            # 使用资源管理器打开图片
            with ImageResourceManager.open_image(image_path, "RGB") as img:
                draw = ImageDraw.Draw(img)
                width, height = img.size

                # 计算字体大小并加载字体
                font_size = self._calculate_font_size(height, is_cover)
                font = self._load_font(font_size)

                # 计算文字度量
                metrics = self._calculate_text_metrics(text, font, draw, width)
                available_width = metrics["available_width"]
                text_width = metrics["text_width"]

                # 如果文字宽度超过可用宽度，调整字体
                if text_width > available_width:
                    font, font_size, text_width, text_height = self._adjust_font_to_fit(
                        text, font, draw, available_width, height, font_size
                    )

                # 处理文字换行
                max_lines = 3
                lines = self._process_text_wrapping(text, available_width, font, draw, max_lines)

                # 计算行度量
                line_metrics = self._calculate_line_metrics(lines, font, draw, is_cover)
                line_height = line_metrics["line_height"]
                total_height = line_metrics["total_height"]
                text_height = line_metrics["text_height"]

                # 计算起始位置
                start_y = self._calculate_start_position(
                    position,
                    height,
                    total_height,
                    lines,
                    line_height,
                    text_height,
                    available_width,
                    font,
                    draw,
                    is_cover,
                )

                # 绘制文字
                self._draw_text_lines(img, lines, start_y, line_height, font, font_size, is_cover)

                # 保存图片
                if output_path is None:
                    output_path = image_path
                ImageResourceManager.save_image_safely(img, output_path, "PNG", quality=95)
                Logger.info("已添加文字叠加", logger_name="image_generator", text_preview=text[:30])

        except Exception as e:
            print(f"  ⚠️  文字叠加失败: {e}")
            import traceback

            traceback.print_exc()

    def split_content_by_scenes(self, content: str, scenes: List[str]) -> List[str]:
        """根据图片场景描述，智能分段正文内容"""
        return TextProcessor.split_content_by_scenes(content, scenes)

    def _smart_truncate(self, text: str, max_lines: int, max_width: int, font: Any, draw: Any) -> List[str]:
        """
        智能截断文字，确保不超过指定行数，并在合适位置添加省略号

        Args:
            text: 原始文字
            max_lines: 最大行数
            max_width: 每行最大宽度
            font: 字体对象
            draw: 绘图对象

        Returns:
            截断后的文字行列表（最多max_lines行）
        """
        if not text:
            return []

        # 先按宽度换行
        all_lines = self._wrap_text(text, max_width, font, draw)

        # 如果行数不超过限制，直接返回
        if len(all_lines) <= max_lines:
            return all_lines

        # 如果超过，只取前max_lines - 1行，最后一行添加省略号
        result_lines = all_lines[: max_lines - 1]

        # 计算省略号宽度
        ellipsis = "…"
        ellipsis_bbox = draw.textbbox((0, 0), ellipsis, font=font)
        ellipsis_width = ellipsis_bbox[2] - ellipsis_bbox[0]
        available_for_last_line = max_width - ellipsis_width - 5  # 留5像素安全边距

        # 从剩余文字中截取能放入最后一行的内容
        remaining_text = "".join(all_lines[max_lines - 1 :])
        last_line = ""

        # 优先在标点符号处截断（更自然），但避免标点符号单独成行
        punctuation_marks = ["。", "，", "！", "？", "；", "：", "、", "…", ".", ",", "!", "?", ";", ":"]

        for char in remaining_text:
            test_line = last_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width <= available_for_last_line:
                last_line = test_line
                # 如果遇到标点符号，且已经有足够内容，可以在这里截断（更自然）
                # 但确保标点符号不会单独成行（即last_line长度>1）
                if char in punctuation_marks and len(last_line) > 1:
                    # 检查标点符号是否在行尾（如果是，可以截断）
                    break
            else:
                # 如果超出，尝试在最后一个标点处截断
                if len(last_line) > 1:  # 确保不是只有标点符号
                    # 从后往前找标点符号，但确保标点符号前面有内容
                    for i in range(len(last_line) - 1, 0, -1):  # 从倒数第二个字符开始，避免只有标点
                        if last_line[i] in punctuation_marks:
                            last_line = last_line[: i + 1]
                            break
                break

        # 如果最后一行有内容，添加省略号
        if last_line:
            # 确保添加省略号后不超出
            test_line = last_line + ellipsis
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width <= max_width:
                result_lines.append(test_line)
            else:
                # 如果超出，移除最后一个字符再添加省略号
                while len(last_line) > 0:
                    last_line = last_line[:-1]
                    test_line = last_line + ellipsis
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    test_width = bbox[2] - bbox[0]
                    if test_width <= max_width:
                        result_lines.append(test_line)
                        break
                else:
                    # 如果还是放不下，只用省略号
                    result_lines.append(ellipsis)
        else:
            # 如果最后一行放不下任何内容，在前一行的末尾添加省略号
            if result_lines:
                prev_line = result_lines[-1]
                if len(prev_line) > 0:
                    # 尝试移除字符直到能放下省略号
                    while len(prev_line) > 0:
                        test_line = prev_line + ellipsis
                        bbox = draw.textbbox((0, 0), test_line, font=font)
                        test_width = bbox[2] - bbox[0]
                        if test_width <= max_width:
                            result_lines[-1] = test_line
                            break
                        prev_line = prev_line[:-1]
                    else:
                        # 如果还是放不下，直接用省略号替换
                        result_lines[-1] = ellipsis
                else:
                    result_lines.append(ellipsis)
            else:
                result_lines.append(ellipsis)

        return result_lines

    def _wrap_text(self, text: str, max_width: int, font: Any, draw: Any) -> List[str]:
        """
        将文字按宽度自动换行，智能处理标点符号，避免标点单独成行

        Args:
            text: 原始文字
            max_width: 最大宽度
            font: 字体对象
            draw: 绘图对象

        Returns:
            分行后的文字列表（已优化，避免标点单独成行）
        """
        if not text:
            return []

        # 定义标点符号（不应单独成行）
        punctuation_marks = set(["。", "，", "！", "？", "；", "：", "、", "…", ".", ",", "!", "?", ";", ":", "…"])
        # 前引号、后引号等特殊标点
        set(["（", "(", "【", "[", "《", "<", '"', '"', """, """])
        set(["）", ")", "】", "]", "》", ">", '"', '"', """, """])

        lines = []
        current_line = ""
        i = 0

        while i < len(text):
            char = text[i]

            # 测试添加当前字符后的宽度
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                # 可以添加，继续
                current_line = test_line
                i += 1
            else:
                # 当前行已满，需要换行
                if current_line:
                    # 检查当前行末尾是否是标点符号
                    # 如果是标点，应该保留在当前行，不换行
                    if current_line[-1] in punctuation_marks:
                        # 标点已经在行尾，保留在当前行
                        lines.append(current_line)
                        current_line = ""
                    else:
                        # 尝试向后查找，看下一个字符是否是标点
                        if i < len(text) and text[i] in punctuation_marks:
                            # 下一个字符是标点，应该保留在当前行
                            # 尝试缩小字体或截断，但这里先尝试将标点加入当前行
                            # 如果标点加入后仍然超出，则保留当前行，标点放到下一行
                            test_with_punct = current_line + text[i]
                            bbox_punct = draw.textbbox((0, 0), test_with_punct, font=font)
                            if bbox_punct[2] - bbox_punct[0] <= max_width:
                                # 标点可以加入当前行
                                current_line = test_with_punct
                                i += 1
                                lines.append(current_line)
                                current_line = ""
                            else:
                                # 标点加入后超出，保留当前行，标点放到下一行（但我们会后续优化）
                                lines.append(current_line)
                                current_line = text[i]
                                i += 1
                        else:
                            # 下一个字符不是标点，正常换行
                            lines.append(current_line)
                            current_line = char
                            i += 1
                else:
                    # 当前行为空，但单个字符就超出（不应该发生，但处理一下）
                    # 强制添加，因为单个字符必须显示
                    current_line = char
                    i += 1

        # 添加最后一行
        if current_line:
            lines.append(current_line)

        # 后处理：优化标点符号位置，避免标点单独成行
        optimized_lines = []
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 如果当前行只有一个标点符号，尝试合并到上一行
            if len(line) == 1 and line in punctuation_marks:
                if optimized_lines:
                    # 合并到上一行
                    optimized_lines[-1] = optimized_lines[-1] + line
                else:
                    # 没有上一行，保留（但这种情况应该很少）
                    optimized_lines.append(line)
            # 如果当前行以标点开头，且上一行存在，尝试合并
            elif line and line[0] in punctuation_marks and optimized_lines:
                # 检查合并后是否超出宽度
                merged = optimized_lines[-1] + line
                bbox_merged = draw.textbbox((0, 0), merged, font=font)
                if bbox_merged[2] - bbox_merged[0] <= max_width:
                    optimized_lines[-1] = merged
                else:
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)

        # 如果只有一行且仍然超出，强制按字符数分割（每行最多10个字符）
        if len(optimized_lines) == 1 and len(text) > 10:
            # 智能分割：尽量在语义断点分割
            optimized_lines = []
            # 尝试在"的"、"之"、"前"、"后"等字后分割
            split_points = ["的", "之", "前", "后", "上", "下", "里", "中", "为", "是", "，", "。", "！", "？"]
            current_line = ""

            for i, char in enumerate(text):
                current_line += char
                # 如果当前行达到一定长度，且在分割点，则换行
                if len(current_line) >= 8 and char in split_points:
                    optimized_lines.append(current_line)
                    current_line = ""
                # 如果当前行超过10个字符，强制换行
                elif len(current_line) >= 10:
                    optimized_lines.append(current_line)
                    current_line = ""

            if current_line:
                optimized_lines.append(current_line)

        return optimized_lines if optimized_lines else [text]

    def generate_all_images(self, prompts_file: str) -> None:
        """
        生成所有图片

        Args:
            prompts_file: 提示词文件路径
        """
        print("=" * 60)
        print("🎨 图片生成器")
        print("=" * 60)

        # 解析提示词和正文内容
        print(f"\n📖 正在读取提示词文件: {prompts_file}")
        prompts, body_text = self.parse_prompts_file(prompts_file)

        # 如果有正文内容，进行智能分段
        content_segments = []
        if body_text:
            story_scenes = [p.get("scene", "") for p in prompts if not p.get("is_cover", False)]
            content_segments = self.split_content_by_scenes(body_text, story_scenes)
            print(f"✅ 正文内容已分段为 {len(content_segments)} 段")

        # 确定输出目录
        prompts_dir = os.path.dirname(prompts_file)
        if not prompts_dir:
            prompts_dir = "."

        print(f"\n📁 输出目录: {prompts_dir}")

        # 初始化可疑内容记录文件
        self.suspicious_content_file = None

        # 预检查所有提示词和正文内容
        print("\n🔍 正在预检查内容安全性...")
        checked_prompts = []
        for prompt_data in prompts:
            is_cover = prompt_data.get("is_cover", False)
            prompt = prompt_data.get("prompt", "")

            # 检查提示词
            is_safe, modified_prompt = self.check_content_safety(prompt, "提示词")
            if not is_safe:
                print(
                    f"  ⚠️  检测到可疑内容（{'封面' if is_cover else f'图{prompt_data.get("index", 0)}'}），已自动修改"
                )
                prompt_data["prompt"] = modified_prompt
                # 如果修改后仍然可疑，记录
                is_safe_after, _ = self.check_content_safety(modified_prompt, "提示词")
                if not is_safe_after:
                    self.save_suspicious_content(
                        prompts_dir,
                        prompt,
                        f"{'封面' if is_cover else f'图{prompt_data.get("index", 0)}'}提示词",
                        "包含敏感词汇，自动修改后仍可能有问题",
                    )

            checked_prompts.append(prompt_data)

        # 检查正文内容分段
        if content_segments:
            for idx, segment in enumerate(content_segments, start=1):
                is_safe, modified_segment = self.check_content_safety(segment, "正文内容")
                if not is_safe:
                    print(f"  ⚠️  检测到可疑正文内容（图{idx}），已自动修改")
                    content_segments[idx - 1] = modified_segment
                    is_safe_after, _ = self.check_content_safety(modified_segment, "正文内容")
                    if not is_safe_after:
                        self.save_suspicious_content(
                            prompts_dir, segment, f"图{idx}正文内容", "包含敏感词汇，自动修改后仍可能有问题"
                        )

        prompts = checked_prompts
        print("✅ 内容预检查完成\n")

        # 生成每张图片
        print(f"\n🎨 开始生成图片（模型: {self.image_model}）\n")

        for prompt_data in prompts:
            max_retries = 3  # 最多重试3次
            retry_count = 0
            success = False
            original_prompt = prompt_data["prompt"]  # 保存原始提示词

            while retry_count <= max_retries and not success:
                try:
                    is_cover = prompt_data.get("is_cover", False)
                    if is_cover:
                        print(f"\n{'=' * 50}")
                        print(f"封面: {prompt_data.get('title', '')}")
                        print(f"{'=' * 50}")
                        lbl = "封面"
                    else:
                        print(f"\n{'=' * 50}")
                        print(f"图{prompt_data['index']}: {prompt_data['scene'][:60]}...")
                        print(f"{'=' * 50}")
                        lbl = prompt_data["index"]

                    # 如果是重试，进一步修改提示词
                    current_prompt = prompt_data["prompt"]
                    if retry_count > 0:
                        print(f"  🔄 第 {retry_count} 次重试，正在进一步修改提示词...")
                        # 再次检查并修改
                        is_safe, modified_prompt = self.check_content_safety(current_prompt, "提示词")
                        if not is_safe:
                            current_prompt = modified_prompt
                        # 移除更多可能敏感的关键词
                        sensitive_words = ["血腥", "暴力", "色情", "政治", "敏感", "争议", "战争", "武器"]
                        for word in sensitive_words:
                            current_prompt = current_prompt.replace(word, "")
                        # 简化描述
                        current_prompt = re.sub(r"\s+", " ", current_prompt).strip()
                        prompt_data["prompt"] = current_prompt
                        print("  ✅ 提示词已修改")

                    image_url = self.generate_image_async(current_prompt, lbl, is_cover=is_cover)

                    if is_cover:
                        image_filename = "cover.png"
                    else:
                        image_filename = f"image_{prompt_data['index']:02d}.png"
                    save_path = os.path.join(prompts_dir, image_filename)
                    self.download_image(image_url, save_path)

                    # 添加文字叠加
                    if is_cover:
                        # 封面图：叠加标题
                        title = prompt_data.get("title", "")
                        if title:
                            print(f"  📝 正在添加文字叠加: {title}")
                            self.add_text_overlay(save_path, title, is_cover=True, position="top")
                    else:
                        # 故事图：叠加正文内容分段
                        idx = prompt_data.get("index", 0)
                        if content_segments and idx > 0 and idx <= len(content_segments):
                            content_segment = content_segments[idx - 1]
                            if content_segment:
                                print(f"  📝 正在添加文字叠加: {content_segment[:30]}...")
                                self.add_text_overlay(save_path, content_segment, is_cover=False, position="bottom")
                        else:
                            # 如果没有正文分段，使用场景描述作为后备
                            scene = prompt_data.get("scene", "")
                            if scene:
                                print(f"  📝 正在添加文字叠加（场景描述）: {scene[:30]}...")
                                self.add_text_overlay(save_path, scene, is_cover=False, position="bottom")

                    success = True

                except ValueError as e:
                    # 内容审核未通过的错误
                    who = "封面" if prompt_data.get("is_cover") else f"图{prompt_data['index']}"
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"\n⚠️  生成{who}失败（内容审核未通过）: {e}")
                        print("  🔄 将尝试修改提示词后重试...")
                    else:
                        print(f"\n❌ 生成{who}失败（已重试{max_retries}次）: {e}")
                        # 保存可疑内容到文件
                        self.save_suspicious_content(
                            prompts_dir,
                            original_prompt,
                            f"{who}提示词",
                            f"内容审核未通过，已尝试{max_retries}次自动修改仍失败",
                        )
                        print(f"  📝 可疑内容已保存到: {os.path.basename(self.suspicious_content_file)}")
                        print("  💡 请查看可疑内容文件，手动修改后重新运行脚本")
                        success = False
                        break

                except Exception as e:
                    who = "封面" if prompt_data.get("is_cover") else f"图{prompt_data['index']}"
                    error_msg = str(e)
                    # 检查是否是内容不当的错误
                    if "DataInspectionFailed" in error_msg or "inappropriate content" in error_msg.lower():
                        if retry_count < max_retries:
                            retry_count += 1
                            print(f"\n⚠️  生成{who}失败（内容审核未通过）: {e}")
                            print("  🔄 将尝试修改提示词后重试...")
                        else:
                            print(f"\n❌ 生成{who}失败（已重试{max_retries}次）: {e}")
                            # 保存可疑内容到文件
                            self.save_suspicious_content(
                                prompts_dir,
                                original_prompt,
                                f"{who}提示词",
                                f"内容审核未通过，已尝试{max_retries}次自动修改仍失败",
                            )
                            print(f"  📝 可疑内容已保存到: {os.path.basename(self.suspicious_content_file)}")
                            print("  💡 请查看可疑内容文件，手动修改后重新运行脚本")
                            success = False
                            break
                    else:
                        print(f"\n❌ 生成{who}失败: {e}")
                        success = False
                        break

        print(f"\n{'=' * 60}")
        print("✅ 所有任务完成！")
        print(f"📁 图片已保存到: {prompts_dir}")
        if self.suspicious_content_file and os.path.exists(self.suspicious_content_file):
            print(f"⚠️  发现可疑内容，已保存到: {os.path.basename(self.suspicious_content_file)}")
            print("   请查看并手动修改后重新生成相关图片")
        print(f"{'=' * 60}\n")


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="图片生成器 - 基于提示词文件生成图片")
    parser.add_argument("-p", "--prompts", help="提示词文件路径（默认：使用最新日期文件夹下的 image_prompts.txt）")
    parser.add_argument("-c", "--config", default="config.json", help="配置文件路径（默认：config.json）")

    args = parser.parse_args()

    generator = ImageGenerator(config_path=args.config)

    # 确定提示词文件路径
    if args.prompts:
        prompts_file = args.prompts
    else:
        # 使用最新日期文件夹
        output_dir = generator.config_manager.get("output_image_dir", "output/images")
        if os.path.exists(output_dir):
            # 找出最新的日期文件夹
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

    # 生成所有图片
    generator.generate_all_images(prompts_file)


if __name__ == "__main__":
    main()
