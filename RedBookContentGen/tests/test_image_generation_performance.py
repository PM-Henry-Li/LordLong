#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片生成性能测试

本测试用于对比串行和并行图片生成的性能差异
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from src.async_image_service import AsyncImageService, ImageGenerationResult
from src.core.config_manager import ConfigManager


class TestImageGenerationPerformance:
    """图片生成性能测试类"""

    @pytest.fixture
    def config_manager(self):
        """创建配置管理器"""
        config = ConfigManager()
        # 使用测试配置
        config.set("openai_api_key", "test-key")
        config.set("image_generation.model", "wanx-v1")
        config.set("image_generation.max_wait_time", 180)
        config.set("image_generation.poll_interval", 1)
        return config

    @pytest.fixture
    def async_service(self, config_manager):
        """创建异步图片生成服务"""
        return AsyncImageService(config_manager)

    @pytest.fixture
    def test_prompts(self):
        """测试提示词列表"""
        return [{"prompt": f"测试提示词 {i}", "index": i, "is_cover": i == 0} for i in range(5)]

    async def _mock_generate_single_image(
        self, prompt: str, index: int = 0, is_cover: bool = False, size: str = None, max_retries: int = 3
    ) -> ImageGenerationResult:
        """模拟单张图片生成（模拟60秒耗时）"""
        await asyncio.sleep(0.1)  # 模拟API调用时间（实际测试中用0.1秒代替60秒）
        return ImageGenerationResult(
            success=True,
            image_url=f"https://example.com/image_{index}.png",
            prompt=prompt,
            index=index,
            is_cover=is_cover,
        )

    @pytest.mark.asyncio
    async def test_serial_generation_performance(self, async_service, test_prompts):
        """测试串行生成性能"""
        # Mock 生成方法
        async_service.generate_single_image_async = self._mock_generate_single_image

        start_time = time.time()

        # 串行生成
        results = []
        for prompt_data in test_prompts:
            result = await async_service.generate_single_image_async(
                prompt=prompt_data["prompt"], index=prompt_data["index"], is_cover=prompt_data["is_cover"]
            )
            results.append(result)

        elapsed_time = time.time() - start_time

        # 验证结果
        assert len(results) == 5
        assert all(r.success for r in results)

        # 串行应该接近 5 * 0.1 = 0.5 秒
        assert elapsed_time >= 0.5
        assert elapsed_time < 0.7  # 允许一些误差

        print(f"\n串行生成耗时: {elapsed_time:.2f}秒")
        return elapsed_time

    @pytest.mark.asyncio
    async def test_parallel_generation_performance(self, async_service, test_prompts):
        """测试并行生成性能（3并发）"""
        # Mock 生成方法
        async_service.generate_single_image_async = self._mock_generate_single_image

        start_time = time.time()

        # 并行生成（3并发）
        results = await async_service.generate_batch_images_async(prompts=test_prompts, max_concurrent=3)

        elapsed_time = time.time() - start_time

        # 验证结果
        assert len(results) == 5
        assert all(r.success for r in results)

        # 并行（3并发）应该接近 ceil(5/3) * 0.1 = 0.2 秒
        assert elapsed_time >= 0.2
        assert elapsed_time < 0.35  # 允许一些误差

        print(f"\n并行生成耗时（3并发）: {elapsed_time:.2f}秒")
        return elapsed_time

    @pytest.mark.asyncio
    async def test_performance_comparison(self, async_service, test_prompts):
        """对比串行和并行性能"""
        # Mock 生成方法
        async_service.generate_single_image_async = self._mock_generate_single_image

        # 串行测试
        serial_start = time.time()
        serial_results = []
        for prompt_data in test_prompts:
            result = await async_service.generate_single_image_async(
                prompt=prompt_data["prompt"], index=prompt_data["index"], is_cover=prompt_data["is_cover"]
            )
            serial_results.append(result)
        serial_time = time.time() - serial_start

        # 并行测试
        parallel_start = time.time()
        parallel_results = await async_service.generate_batch_images_async(prompts=test_prompts, max_concurrent=3)
        parallel_time = time.time() - parallel_start

        # 计算性能提升
        improvement = (serial_time - parallel_time) / serial_time * 100

        print(f"\n性能对比:")
        print(f"  串行耗时: {serial_time:.2f}秒")
        print(f"  并行耗时: {parallel_time:.2f}秒")
        print(f"  性能提升: {improvement:.1f}%")

        # 验证性能提升至少50%
        assert improvement >= 50, f"性能提升不足50%，实际为{improvement:.1f}%"

        # 验证结果一致性
        assert len(serial_results) == len(parallel_results)
        assert all(r.success for r in serial_results)
        assert all(r.success for r in parallel_results)

    @pytest.mark.asyncio
    async def test_error_isolation(self, async_service, test_prompts):
        """测试错误隔离机制"""
        call_count = 0

        async def mock_with_error(
            prompt: str, index: int = 0, is_cover: bool = False, size: str = None, max_retries: int = 3
        ) -> ImageGenerationResult:
            """模拟部分失败的生成"""
            nonlocal call_count
            call_count += 1

            await asyncio.sleep(0.1)

            # 第3张图片失败
            if index == 2:
                return ImageGenerationResult(
                    success=False, error="模拟错误", prompt=prompt, index=index, is_cover=is_cover
                )

            return ImageGenerationResult(
                success=True,
                image_url=f"https://example.com/image_{index}.png",
                prompt=prompt,
                index=index,
                is_cover=is_cover,
            )

        async_service.generate_single_image_async = mock_with_error

        # 并行生成
        results = await async_service.generate_batch_images_async(prompts=test_prompts, max_concurrent=3)

        # 验证结果
        assert len(results) == 5
        assert call_count == 5  # 所有图片都尝试生成了

        # 验证错误隔离：只有第3张失败
        success_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)

        assert success_count == 4
        assert failed_count == 1
        assert not results[2].success  # 第3张（index=2）失败
        assert results[2].error == "模拟错误"

        print(f"\n错误隔离测试:")
        print(f"  成功: {success_count}张")
        print(f"  失败: {failed_count}张")
        print(f"  失败的图片不影响其他图片生成 ✓")

    @pytest.mark.asyncio
    async def test_concurrent_limit(self, async_service, test_prompts):
        """测试并发限制"""
        active_tasks = 0
        max_active = 0

        async def mock_with_tracking(
            prompt: str, index: int = 0, is_cover: bool = False, size: str = None, max_retries: int = 3
        ) -> ImageGenerationResult:
            """跟踪并发数的模拟生成"""
            nonlocal active_tasks, max_active

            active_tasks += 1
            max_active = max(max_active, active_tasks)

            await asyncio.sleep(0.1)

            active_tasks -= 1

            return ImageGenerationResult(
                success=True,
                image_url=f"https://example.com/image_{index}.png",
                prompt=prompt,
                index=index,
                is_cover=is_cover,
            )

        async_service.generate_single_image_async = mock_with_tracking

        # 并行生成（限制3并发）
        results = await async_service.generate_batch_images_async(prompts=test_prompts, max_concurrent=3)

        # 验证并发限制
        assert max_active <= 3, f"并发数超过限制：{max_active} > 3"
        assert len(results) == 5
        assert all(r.success for r in results)

        print(f"\n并发限制测试:")
        print(f"  最大并发数: {max_active}")
        print(f"  并发限制: 3")
        print(f"  并发控制正常 ✓")


class TestRealWorldScenario:
    """真实场景测试（需要真实API Key）"""

    @pytest.mark.skip(reason="需要真实API Key，手动运行")
    @pytest.mark.asyncio
    async def test_real_api_performance(self):
        """真实API性能测试（需要手动运行）"""
        config = ConfigManager()
        service = AsyncImageService(config)

        test_prompts = [{"prompt": "老北京胡同，复古风格，温暖色调", "index": i, "is_cover": False} for i in range(5)]

        # 串行测试
        print("\n开始串行生成测试...")
        serial_start = time.time()
        serial_results = []
        for prompt_data in test_prompts:
            result = await service.generate_single_image_async(prompt=prompt_data["prompt"], index=prompt_data["index"])
            serial_results.append(result)
        serial_time = time.time() - serial_start

        # 并行测试
        print("\n开始并行生成测试...")
        parallel_start = time.time()
        parallel_results = await service.generate_batch_images_async(prompts=test_prompts, max_concurrent=3)
        parallel_time = time.time() - parallel_start

        # 输出结果
        improvement = (serial_time - parallel_time) / serial_time * 100

        print(f"\n真实API性能测试结果:")
        print(f"  串行耗时: {serial_time:.2f}秒 ({serial_time/60:.1f}分钟)")
        print(f"  并行耗时: {parallel_time:.2f}秒 ({parallel_time/60:.1f}分钟)")
        print(f"  性能提升: {improvement:.1f}%")
        print(f"  串行成功: {sum(1 for r in serial_results if r.success)}/5")
        print(f"  并行成功: {sum(1 for r in parallel_results if r.success)}/5")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
