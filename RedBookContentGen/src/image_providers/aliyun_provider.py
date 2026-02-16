#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云通义万相图片生成服务提供商

实现阿里云通义万相的图片生成功能，支持文本生成图片。
"""

import re
import time
import requests
from typing import Optional
from .base import BaseImageProvider
from src.core.logger import Logger


class AliyunImageProvider(BaseImageProvider):
    """阿里云通义万相图片生成服务提供商"""

    def __init__(self, config_manager, logger, rate_limiter=None, cache=None):
        """
        初始化阿里云图片生成服务提供商

        Args:
            config_manager: ConfigManager 实例，用于读取配置
            logger: Logger 实例，用于记录日志
            rate_limiter: RateLimiter 实例（可选），用于速率限制
            cache: CacheManager 实例（可选），用于缓存结果
        """
        super().__init__(config_manager, logger, rate_limiter, cache)

        # 从配置中读取阿里云相关配置
        self.api_key = self.config_manager.get("openai_api_key")
        self.image_model = self.config_manager.get("image_model", "wanx-v1")
        self.image_generation_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        self.task_status_url = "https://dashscope.aliyuncs.com/api/v1/tasks"

        if not self.api_key:
            Logger.warning(
                "阿里云 API 密钥未配置，无法使用阿里云图片生成服务",
                logger_name="aliyun_provider"
            )

    def generate(self, prompt: str, size: str = "1024*1365", **kwargs) -> Optional[str]:
        """
        生成图片

        流程:
        1. 检查缓存
        2. 检查速率限制
        3. 清理提示词
        4. 创建图片生成任务
        5. 轮询任务状态
        6. 缓存结果

        Args:
            prompt: 图片提示词，描述要生成的图片内容
            size: 图片尺寸，格式为 "宽*高"，默认 "1024*1365"
            **kwargs: 其他参数，如 is_cover（是否为封面图）等

        Returns:
            生成的图片 URL，失败返回 None
        """
        if not self.api_key:
            Logger.error(
                "阿里云 API 密钥未配置，无法生成图片",
                logger_name="aliyun_provider"
            )
            return None

        is_cover = kwargs.get("is_cover", False)

        # 1. 检查缓存
        cache_key = None
        if self.cache:
            import hashlib
            cache_key = hashlib.md5(f"{prompt}_{size}".encode('utf-8')).hexdigest()
            cached_url = self.cache.get(cache_key)
            if cached_url:
                Logger.info(
                    "从缓存返回图片 URL",
                    logger_name="aliyun_provider",
                    cache_key=cache_key[:16] + "..."
                )
                return cached_url

        # 2. 检查速率限制
        if self.rate_limiter:
            Logger.debug(
                "正在获取 RPM 令牌",
                logger_name="aliyun_provider",
                available_tokens=self.rate_limiter.get_available_tokens(),
            )

            success = self.rate_limiter.wait_for_token(tokens=1, timeout=120)
            if not success:
                raise TimeoutError("获取图片生成 RPM 令牌超时（120秒）")

            Logger.debug(
                "已获取 RPM 令牌",
                logger_name="aliyun_provider",
                remaining_tokens=self.rate_limiter.get_available_tokens(),
            )

        try:
            # 3. 创建图片生成任务
            task_id = self._create_task(prompt, size, is_cover)
            Logger.info(
                f"任务创建成功: {task_id}",
                logger_name="aliyun_provider"
            )

            # 4. 轮询任务状态
            image_url = self._wait_for_task_completion(task_id)

            # 5. 缓存结果
            if self.cache and image_url and cache_key:
                self.cache.set(cache_key, image_url)
                Logger.info(
                    "图片URL已缓存",
                    logger_name="aliyun_provider",
                    cache_key=cache_key[:16] + "..."
                )

            return image_url

        except Exception as e:
            Logger.error(
                f"图片生成失败: {str(e)}",
                logger_name="aliyun_provider"
            )
            return None

    def _create_task(self, prompt: str, size: str, is_cover: bool = False) -> str:
        """
        创建图片生成任务

        Args:
            prompt: 图片提示词
            size: 图片尺寸
            is_cover: 是否为封面图

        Returns:
            任务 ID
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        # 清理提示词，移除 --ar --v 等参数（通义万相不需要）
        clean_prompt = re.sub(r"--ar\s*\d+:\d+", "", prompt)
        clean_prompt = re.sub(r"--v\s*\d+(\.\d+)?", "", clean_prompt)
        clean_prompt = re.sub(r"--style\s+\w+", "", clean_prompt)
        clean_prompt = clean_prompt.strip()

        # 构建请求数据
        data = {
            "model": self.image_model,
            "input": {"prompt": clean_prompt},
            "parameters": {"size": size, "n": 1, "watermark": False},
        }

        # 默认负面提示词（用于所有图片）
        default_negative_prompt = "nsfw, text, watermark, username, signature, logo, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, blurry"

        # 如果是封面图，添加额外的负面提示词
        if is_cover:
            # 针对文字的负面提示词
            cover_negative = "乱码文字，错误汉字，无法识别的字符，文字模糊，文字扭曲，文字重叠，非标准汉字，错别字，文字不清晰，字符遗漏，文字不完整，缺少汉字"
            data["input"]["negative_prompt"] = f"{default_negative_prompt}, {cover_negative}"
        else:
            # 故事图也可以使用默认负面提示词
            data["input"]["negative_prompt"] = default_negative_prompt

        Logger.info(
            f"正在生成图片: {prompt[:50]}...",
            logger_name="aliyun_provider"
        )

        # 创建任务
        response = requests.post(self.image_generation_url, headers=headers, json=data)

        if response.status_code != 200:
            error_text = response.text
            # 检查是否是内容不当的错误
            if response.status_code == 400:
                try:
                    error_json = response.json()
                    if (
                        error_json.get("code") == "DataInspectionFailed"
                        or "inappropriate content" in error_text.lower()
                    ):
                        raise ValueError(f"内容审核未通过: {error_json.get('message', '内容可能包含不当信息')}")
                except Exception:
                    pass
            raise Exception(f"创建任务失败: {response.status_code} - {error_text}")

        resp_json = response.json()

        if "output" not in resp_json or "task_id" not in resp_json["output"]:
            raise Exception(f"响应格式错误: {resp_json}")

        return resp_json["output"]["task_id"]

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
                raise Exception(f"查询任务状态失败: {response.status_code} - {response.text}")

            resp_json = response.json()
            task_status = resp_json.get("output", {}).get("task_status", "")

            if task_status == "SUCCEEDED":
                # 获取图片URL（兼容 output.results[0].url 与 output.choices[0].image）
                output = resp_json.get("output", {})
                results = output.get("results", [])
                if results and "url" in results[0]:
                    image_url = results[0]["url"]
                    Logger.info("图片生成成功", logger_name="aliyun_provider")
                    return image_url
                choices = output.get("choices", [])
                if choices and choices[0].get("image"):
                    image_url = choices[0]["image"]
                    Logger.info("图片生成成功", logger_name="aliyun_provider")
                    return image_url
                raise Exception("任务成功但未返回图片URL")

            elif task_status == "FAILED":
                raise Exception(f"任务失败: {resp_json}")

            elif task_status in ["PENDING", "RUNNING", "INITIALIZING"]:
                Logger.debug(
                    f"等待中... 状态: {task_status}",
                    logger_name="aliyun_provider"
                )
                time.sleep(poll_interval)

            else:
                Logger.warning(
                    f"未知状态: {task_status}",
                    logger_name="aliyun_provider"
                )
                time.sleep(poll_interval)

        raise Exception(f"任务超时（{max_wait}秒）")

    def get_provider_name(self) -> str:
        """
        获取服务提供商名称

        Returns:
            服务提供商名称 "aliyun"
        """
        return "aliyun"
