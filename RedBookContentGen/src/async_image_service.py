#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异步图片生成服务模块

本模块提供异步图片生成的核心功能，支持：
- 单张图片异步生成
- 多张图片并行生成
- 并发控制和错误隔离
- 任务状态轮询

使用示例:
    >>> service = AsyncImageService(config_manager)
    >>> result = await service.generate_single_image_async(prompt)
    >>> results = await service.generate_batch_images_async(prompts, max_concurrent=3)
"""

import asyncio
import aiohttp
import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.core.config_manager import ConfigManager
from src.core.logger import Logger


@dataclass
class ImageGenerationResult:
    """图片生成结果"""

    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None
    prompt: str = ""
    index: int = 0
    is_cover: bool = False
    retry_count: int = 0


class AsyncImageService:
    """异步图片生成服务"""

    def __init__(self, config_manager: ConfigManager):
        """
        初始化异步图片生成服务

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.api_key = config_manager.get("openai_api_key")
        self.image_model = config_manager.get("image_generation.model", "wanx-v1")
        self.image_generation_url = config_manager.get(
            "image_generation.api_url", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        )
        self.default_size = config_manager.get("image_generation.size", "1024*1365")
        self.max_wait_time = config_manager.get("image_generation.max_wait_time", 180)
        self.poll_interval = config_manager.get("image_generation.poll_interval", 5)

        Logger.info(
            "异步图片生成服务初始化完成",
            logger_name="async_image_service",
            model=self.image_model,
            size=self.default_size,
        )

    def _clean_prompt(self, prompt: str) -> str:
        """
        清理提示词，移除不支持的参数

        Args:
            prompt: 原始提示词

        Returns:
            清理后的提示词
        """
        # 移除 Midjourney 风格的参数
        clean_prompt = re.sub(r"--ar\s*\d+:\d+", "", prompt)
        clean_prompt = re.sub(r"--v\s*\d+(\.\d+)?", "", clean_prompt)
        clean_prompt = re.sub(r"--style\s+\w+", "", clean_prompt)
        clean_prompt = clean_prompt.strip()
        return clean_prompt

    def _build_request_data(self, prompt: str, is_cover: bool = False, size: Optional[str] = None) -> Dict:
        """
        构建图片生成请求数据

        Args:
            prompt: 图片提示词
            is_cover: 是否为封面图
            size: 图片尺寸

        Returns:
            请求数据字典
        """
        clean_prompt = self._clean_prompt(prompt)

        # 默认负面提示词
        default_negative_prompt = (
            "nsfw, text, watermark, username, signature, logo, "
            "worst quality, low quality, normal quality, lowres, "
            "bad anatomy, bad hands, missing fingers, extra digit, "
            "fewer digits, cropped, jpeg artifacts, blurry"
        )

        # 封面图额外的负面提示词
        if is_cover:
            cover_negative = (
                "乱码文字，错误汉字，无法识别的字符，文字模糊，文字扭曲，"
                "文字重叠，非标准汉字，错别字，文字不清晰，字符遗漏，"
                "文字不完整，缺少汉字"
            )
            negative_prompt = f"{default_negative_prompt}, {cover_negative}"
        else:
            negative_prompt = default_negative_prompt

        return {
            "model": self.image_model,
            "input": {"prompt": clean_prompt, "negative_prompt": negative_prompt},
            "parameters": {"size": size or self.default_size, "n": 1, "watermark": False},
        }

    async def _create_generation_task(
        self, session: aiohttp.ClientSession, prompt: str, is_cover: bool = False, size: Optional[str] = None
    ) -> str:
        """
        创建图片生成任务

        Args:
            session: aiohttp 会话
            prompt: 图片提示词
            is_cover: 是否为封面图
            size: 图片尺寸

        Returns:
            任务ID

        Raises:
            Exception: 任务创建失败
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        data = self._build_request_data(prompt, is_cover, size)

        async with session.post(
            self.image_generation_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status != 200:
                error_text = await response.text()

                # 检查内容审核失败
                if response.status == 400:
                    try:
                        error_json = await response.json()
                        if (
                            error_json.get("code") == "DataInspectionFailed"
                            or "inappropriate content" in error_text.lower()
                        ):
                            raise ValueError(f"内容审核未通过: {error_json.get('message', '内容可能包含不当信息')}")
                    except ValueError:
                        raise
                    except Exception:
                        pass

                raise Exception(f"创建任务失败: {response.status} - {error_text}")

            resp_json = await response.json()

            if "output" not in resp_json or "task_id" not in resp_json["output"]:
                raise Exception(f"响应格式错误: {resp_json}")

            task_id = resp_json["output"]["task_id"]
            return task_id

    async def _wait_for_task_completion_async(self, session: aiohttp.ClientSession, task_id: str) -> str:
        """
        异步等待任务完成

        Args:
            session: aiohttp 会话
            task_id: 任务ID

        Returns:
            图片URL

        Raises:
            Exception: 任务失败或超时
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}

        query_url = f"{self.image_generation_url}/{task_id}"
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self.max_wait_time:
                raise Exception(f"任务超时（{self.max_wait_time}秒）")

            async with session.get(query_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"查询任务失败: {response.status} - {error_text}")

                resp_json = await response.json()

                if "output" not in resp_json:
                    raise Exception(f"响应格式错误: {resp_json}")

                output = resp_json["output"]
                task_status = output.get("task_status", "")

                if task_status == "SUCCEEDED":
                    results = output.get("results", [])
                    if not results or "url" not in results[0]:
                        raise Exception("未找到图片URL")
                    return results[0]["url"]

                elif task_status == "FAILED":
                    error_msg = output.get("message", "未知错误")
                    raise Exception(f"任务失败: {error_msg}")

                # 任务进行中，等待后重试
                await asyncio.sleep(self.poll_interval)

    async def generate_single_image_async(
        self, prompt: str, index: int = 0, is_cover: bool = False, size: Optional[str] = None, max_retries: int = 3
    ) -> ImageGenerationResult:
        """
        异步生成单张图片

        Args:
            prompt: 图片提示词
            index: 图片索引
            is_cover: 是否为封面图
            size: 图片尺寸
            max_retries: 最大重试次数

        Returns:
            图片生成结果
        """
        label = "封面" if is_cover else f"图{index}"
        retry_count = 0

        async with aiohttp.ClientSession() as session:
            while retry_count <= max_retries:
                try:
                    Logger.info(
                        f"开始生成{label}", logger_name="async_image_service", prompt=prompt[:50], retry=retry_count
                    )

                    # 创建任务
                    task_id = await self._create_generation_task(session, prompt, is_cover, size)

                    Logger.info(f"{label}任务创建成功", logger_name="async_image_service", task_id=task_id)

                    # 等待完成
                    image_url = await self._wait_for_task_completion_async(session, task_id)

                    Logger.info(f"{label}生成成功", logger_name="async_image_service", image_url=image_url)

                    return ImageGenerationResult(
                        success=True,
                        image_url=image_url,
                        prompt=prompt,
                        index=index,
                        is_cover=is_cover,
                        retry_count=retry_count,
                    )

                except ValueError as e:
                    # 内容审核失败
                    if retry_count < max_retries:
                        retry_count += 1
                        Logger.warning(
                            f"{label}内容审核未通过，准备重试",
                            logger_name="async_image_service",
                            error=str(e),
                            retry=retry_count,
                        )
                        # 简化提示词后重试
                        prompt = self._simplify_prompt(prompt)
                    else:
                        Logger.error(
                            f"{label}生成失败（已重试{max_retries}次）", logger_name="async_image_service", error=str(e)
                        )
                        return ImageGenerationResult(
                            success=False,
                            error=str(e),
                            prompt=prompt,
                            index=index,
                            is_cover=is_cover,
                            retry_count=retry_count,
                        )

                except Exception as e:
                    # 其他错误
                    if retry_count < max_retries:
                        retry_count += 1
                        Logger.warning(
                            f"{label}生成失败，准备重试",
                            logger_name="async_image_service",
                            error=str(e),
                            retry=retry_count,
                        )
                        await asyncio.sleep(2)  # 等待2秒后重试
                    else:
                        Logger.error(
                            f"{label}生成失败（已重试{max_retries}次）", logger_name="async_image_service", error=str(e)
                        )
                        return ImageGenerationResult(
                            success=False,
                            error=str(e),
                            prompt=prompt,
                            index=index,
                            is_cover=is_cover,
                            retry_count=retry_count,
                        )

        # 不应该到达这里
        return ImageGenerationResult(
            success=False, error="未知错误", prompt=prompt, index=index, is_cover=is_cover, retry_count=retry_count
        )

    def _simplify_prompt(self, prompt: str) -> str:
        """
        简化提示词，移除可能敏感的内容

        Args:
            prompt: 原始提示词

        Returns:
            简化后的提示词
        """
        # 移除可能敏感的关键词
        sensitive_words = ["血腥", "暴力", "色情", "政治", "敏感", "争议", "战争", "武器", "裸露", "恐怖", "死亡"]

        simplified = prompt
        for word in sensitive_words:
            simplified = simplified.replace(word, "")

        # 清理多余空格
        simplified = re.sub(r"\s+", " ", simplified).strip()

        return simplified

    async def generate_batch_images_async(
        self, prompts: List[Dict], max_concurrent: int = 3
    ) -> List[ImageGenerationResult]:
        """
        并行生成多张图片

        Args:
            prompts: 提示词列表，每个元素包含 prompt, index, is_cover 等字段
            max_concurrent: 最大并发数

        Returns:
            图片生成结果列表
        """
        Logger.info(
            f"开始并行生成{len(prompts)}张图片", logger_name="async_image_service", max_concurrent=max_concurrent
        )

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(prompt_data: Dict) -> ImageGenerationResult:
            """带信号量控制的生成函数"""
            async with semaphore:
                return await self.generate_single_image_async(
                    prompt=prompt_data.get("prompt", ""),
                    index=prompt_data.get("index", 0),
                    is_cover=prompt_data.get("is_cover", False),
                    size=prompt_data.get("size"),
                )

        # 创建所有任务
        tasks = [generate_with_semaphore(p) for p in prompts]

        # 并行执行，使用 return_exceptions=True 确保错误隔离
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                Logger.error(f"图片{i}生成时发生异常", logger_name="async_image_service", error=str(result))
                processed_results.append(
                    ImageGenerationResult(
                        success=False,
                        error=str(result),
                        prompt=prompts[i].get("prompt", ""),
                        index=prompts[i].get("index", i),
                        is_cover=prompts[i].get("is_cover", False),
                    )
                )
            else:
                processed_results.append(result)

        # 统计结果
        success_count = sum(1 for r in processed_results if r.success)
        Logger.info(
            "批量生成完成",
            logger_name="async_image_service",
            total=len(prompts),
            success=success_count,
            failed=len(prompts) - success_count,
        )

        return processed_results
