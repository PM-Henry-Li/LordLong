#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片生成管道模块

使用责任链模式处理图片生成的各个阶段
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.core.logger import Logger


class ImageGenerationContext:
    """图片生成上下文，存储生成过程中的数据"""

    def __init__(self, prompt: str, size: str = "1024*1365"):
        self.prompt = prompt
        self.size = size
        self.clean_prompt: Optional[str] = None
        self.task_id: Optional[str] = None
        self.image_url: Optional[str] = None
        self.error: Optional[str] = None
        self.cached: bool = False
        self.metadata: Dict[str, Any] = {}

    def is_successful(self) -> bool:
        """检查是否成功生成图片"""
        return self.image_url is not None and self.error is None


class ImageGenerationHandler(ABC):
    """图片生成处理器基类"""

    def __init__(self):
        self._next_handler: Optional[ImageGenerationHandler] = None

    def set_next(self, handler: "ImageGenerationHandler") -> "ImageGenerationHandler":
        """设置下一个处理器"""
        self._next_handler = handler
        return handler

    def handle(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """处理请求"""
        # 执行当前处理器的逻辑
        context = self._process(context)

        # 如果出错或已完成，不继续传递
        if context.error or context.is_successful():
            return context

        # 传递给下一个处理器
        if self._next_handler:
            return self._next_handler.handle(context)

        return context

    @abstractmethod
    def _process(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """具体的处理逻辑，由子类实现"""


class CacheCheckHandler(ImageGenerationHandler):
    """缓存检查处理器"""

    def __init__(self, cache_manager, cache_key_generator):
        super().__init__()
        self.cache = cache_manager
        self.generate_cache_key = cache_key_generator

    def _process(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """检查缓存"""
        if self.cache is None:
            return context

        cache_key = self.generate_cache_key(context.prompt, context.size)
        cached_url = self.cache.get(cache_key)

        if cached_url is not None:
            Logger.info("从缓存获取图片URL", logger_name="image_generator", cache_key=cache_key[:16] + "...")
            print("  ✅ 缓存命中，直接返回图片URL")
            context.image_url = cached_url
            context.cached = True

        return context


class RateLimitHandler(ImageGenerationHandler):
    """速率限制处理器"""

    def __init__(self, rate_limiter):
        super().__init__()
        self.rate_limiter = rate_limiter

    def _process(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """应用速率限制"""
        if self.rate_limiter is None:
            return context

        Logger.debug(
            "正在获取 RPM 令牌",
            logger_name="image_generator",
            available_tokens=self.rate_limiter.get_available_tokens(),
        )

        success = self.rate_limiter.wait_for_token(tokens=1, timeout=120)
        if not success:
            Logger.warning("获取图片生成 RPM 令牌超时", logger_name="image_generator")
            print("  ⚠️  速率限制：请求超时")
            context.error = "速率限制超时"
            return context

        Logger.debug(
            "✅ 已获取 RPM 令牌",
            logger_name="image_generator",
            remaining_tokens=self.rate_limiter.get_available_tokens(),
        )

        return context


class PromptCleanHandler(ImageGenerationHandler):
    """提示词清理处理器"""

    def _process(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """清理提示词"""
        import re

        clean_prompt = re.sub(r"--ar\s*\d+:\d+", "", context.prompt)
        clean_prompt = re.sub(r"--v\s*\d+(\.\d+)?", "", clean_prompt)
        clean_prompt = re.sub(r"--style\s+\w+", "", clean_prompt)
        context.clean_prompt = clean_prompt.strip()

        return context


class ImageGenerationAPIHandler(ImageGenerationHandler):
    """图片生成API调用处理器"""

    def __init__(self, api_key: str, image_model: str, image_generation_url: str, wait_for_completion_func):
        super().__init__()
        self.api_key = api_key
        self.image_model = image_model
        self.image_generation_url = image_generation_url
        self.wait_for_completion = wait_for_completion_func

    def _process(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """调用API生成图片"""
        import requests

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            }

            data = {
                "model": self.image_model,
                "input": {
                    "prompt": context.clean_prompt or context.prompt,
                    "negative_prompt": "nsfw, text, watermark, username, signature, logo, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, blurry",
                },
                "parameters": {"size": context.size, "n": 1, "watermark": False},
            }

            print("  📤 正在生成图片...")

            response = requests.post(self.image_generation_url, headers=headers, json=data, timeout=30)

            if response.status_code != 200:
                print(f"  ❌ 创建任务失败: {response.status_code}")
                context.error = f"API调用失败: {response.status_code}"
                return context

            resp_json = response.json()
            if "output" not in resp_json or "task_id" not in resp_json["output"]:
                print("  ❌ 响应格式错误")
                context.error = "响应格式错误"
                return context

            context.task_id = resp_json["output"]["task_id"]
            print(f"  ✅ 任务创建成功: {context.task_id}")

            # 等待完成
            context.image_url = self.wait_for_completion(context.task_id)
            print(f"  🖼️  图片生成成功: {context.image_url}")

        except Exception as e:
            print(f"  ❌ 图片生成失败: {e}")
            context.error = str(e)

        return context


class CacheSaveHandler(ImageGenerationHandler):
    """缓存保存处理器"""

    def __init__(self, cache_manager, cache_key_generator):
        super().__init__()
        self.cache = cache_manager
        self.generate_cache_key = cache_key_generator

    def _process(self, context: ImageGenerationContext) -> ImageGenerationContext:
        """保存到缓存"""
        if self.cache is None or context.cached or not context.image_url:
            return context

        cache_key = self.generate_cache_key(context.prompt, context.size)
        self.cache.set(cache_key, context.image_url)
        Logger.info("图片URL已缓存", logger_name="image_generator", cache_key=cache_key[:16] + "...")

        return context


class ImageGenerationPipeline:
    """图片生成管道，组装各个处理器"""

    def __init__(self, generator):
        """
        初始化管道

        Args:
            generator: ImageGenerator实例
        """
        self.generator = generator
        self._build_pipeline()

    def _build_pipeline(self):
        """构建处理器链"""
        # 创建处理器
        cache_check = CacheCheckHandler(
            self.generator.cache if self.generator._cache_enabled else None, self.generator._generate_cache_key
        )

        rate_limit = RateLimitHandler(self.generator.rpm_limiter if self.generator._rate_limit_enabled else None)

        prompt_clean = PromptCleanHandler()

        api_call = ImageGenerationAPIHandler(
            self.generator.api_key,
            self.generator.image_model,
            self.generator.image_generation_url,
            self.generator._wait_for_task_completion,
        )

        cache_save = CacheSaveHandler(
            self.generator.cache if self.generator._cache_enabled else None, self.generator._generate_cache_key
        )

        # 组装链
        cache_check.set_next(rate_limit).set_next(prompt_clean).set_next(api_call).set_next(cache_save)

        self.first_handler = cache_check

    def generate(self, prompt: str, size: str = "1024*1365") -> Optional[str]:
        """
        执行图片生成管道

        Args:
            prompt: 图片提示词
            size: 图片尺寸

        Returns:
            图片URL，失败返回None
        """
        context = ImageGenerationContext(prompt, size)
        result = self.first_handler.handle(context)
        return result.image_url
