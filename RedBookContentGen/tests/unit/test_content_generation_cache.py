#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内容生成缓存集成

任务 9.1.4: 测试缓存集成
- 测试缓存命中
- 测试缓存未命中
- 测试缓存失效

目标：测试覆盖率 > 70%

注意：由于 _check_cache 和 _save_to_cache 是嵌套在 _build_generation_prompt 内部的函数，
我们无法直接测试它们。因此，我们通过测试 generate_content 方法的行为来间接测试缓存功能。
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.content_generator import RedBookContentGenerator
from src.core.config_manager import ConfigManager
from src.core.cache_manager import CacheManager


# ============================================================================
# 测试固件
# ============================================================================


@pytest.fixture
def test_config_with_cache(temp_dir):
    """创建启用缓存的测试配置"""
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "openai_model": "qwen-plus",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "cache": {
            "enabled": True,
            "max_size": 100,
            "default_ttl": 3600,  # 1小时
        },
        "rate_limit": {"openai": {"enable_rate_limit": False}},
    }

    config_file = temp_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    return config_file


@pytest.fixture
def test_config_with_short_ttl(temp_dir):
    """创建短TTL的测试配置（用于测试缓存失效）"""
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "openai_model": "qwen-plus",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "cache": {
            "enabled": True,
            "max_size": 100,
            "default_ttl": 1,  # 1秒（用于测试失效）
        },
        "rate_limit": {"openai": {"enable_rate_limit": False}},
    }

    config_file = temp_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    return config_file


@pytest.fixture
def generator_with_cache(test_config_with_cache):
    """创建启用缓存的内容生成器实例"""
    config_manager = ConfigManager(str(test_config_with_cache))
    return RedBookContentGenerator(config_manager=config_manager)


@pytest.fixture
def generator_with_short_ttl(test_config_with_short_ttl):
    """创建短TTL的内容生成器实例"""
    config_manager = ConfigManager(str(test_config_with_short_ttl))
    return RedBookContentGenerator(config_manager=config_manager)


@pytest.fixture
def mock_openai_response():
    """模拟 OpenAI API 响应"""
    return {
        "titles": [
            "胡同里的老北京记忆 🏮",
            "那些年，我们一起走过的胡同",
            "老北京胡同：时光里的温暖",
            "胡同深处的童年时光",
            "寻找老北京的味道",
        ],
        "content": "记得小时候的老北京胡同吗？清晨的豆腐吆喝声从巷子深处传来，悠长而亲切。",
        "tags": "#老北京 #胡同文化 #童年回忆",
        "image_prompts": [
            {"scene": "胡同清晨", "prompt": "老北京胡同清晨场景"},
            {"scene": "孩子们玩耍", "prompt": "胡同里的孩子们在玩耍"},
            {"scene": "四合院", "prompt": "传统北京四合院"},
            {"scene": "邻里聊天", "prompt": "邻居们在胡同口聊天"},
        ],
        "cover": {"scene": "胡同全景", "title": "老北京胡同记忆", "prompt": "老北京胡同全景"},
    }


# ============================================================================
# 测试 1: 缓存初始化
# ============================================================================


@pytest.mark.unit
def test_cache_initialization_enabled(generator_with_cache):
    """测试缓存初始化 - 启用缓存"""
    # 验证缓存已启用
    assert generator_with_cache._cache_enabled is True
    assert generator_with_cache.cache is not None
    assert isinstance(generator_with_cache.cache, CacheManager)


@pytest.mark.unit
def test_cache_initialization_disabled(test_config_with_cache, temp_dir):
    """测试缓存初始化 - 禁用缓存"""
    # 修改配置禁用缓存
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "cache": {"enabled": False},
        "rate_limit": {"openai": {"enable_rate_limit": False}},
    }

    config_file = temp_dir / "config_no_cache.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    config_manager = ConfigManager(str(config_file))
    generator = RedBookContentGenerator(config_manager=config_manager)

    # 验证缓存被禁用
    assert generator._cache_enabled is False
    assert generator.cache is None


# ============================================================================
# 测试 2: 缓存键生成
# ============================================================================


@pytest.mark.unit
def test_cache_key_generation_consistency(generator_with_cache):
    """测试缓存键生成的一致性"""
    input_text = "老北京的胡同文化"

    key1 = generator_with_cache._generate_cache_key(input_text)
    key2 = generator_with_cache._generate_cache_key(input_text)

    # 相同输入应该生成相同的缓存键
    assert key1 == key2
    assert key1.startswith("content_gen:")


@pytest.mark.unit
def test_cache_key_generation_uniqueness(generator_with_cache):
    """测试缓存键生成的唯一性"""
    input_text1 = "老北京的胡同文化"
    input_text2 = "不同的输入内容"

    key1 = generator_with_cache._generate_cache_key(input_text1)
    key2 = generator_with_cache._generate_cache_key(input_text2)

    # 不同输入应该生成不同的缓存键
    assert key1 != key2


# ============================================================================
# 测试 3: 缓存未命中（第一次生成）
# ============================================================================


@pytest.mark.unit
def test_cache_miss_first_generation(generator_with_cache, mock_openai_response):
    """测试缓存未命中 - 第一次生成内容"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 第一次调用应该触发 API 调用
        result = generator_with_cache.generate_content(input_text)

        # 验证结果
        assert isinstance(result, dict)
        assert "titles" in result
        assert "content" in result

        # 验证 API 被调用了
        assert mock_call.called
        assert mock_call.call_count >= 1


# ============================================================================
# 测试 4: 缓存命中（第二次生成）
# ============================================================================


@pytest.mark.unit
def test_cache_hit_second_generation(generator_with_cache, mock_openai_response):
    """测试缓存命中 - 第二次生成相同内容"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 第一次调用 - 缓存未命中
        result1 = generator_with_cache.generate_content(input_text)
        first_call_count = mock_call.call_count

        # 第二次调用 - 应该命中缓存
        result2 = generator_with_cache.generate_content(input_text)
        second_call_count = mock_call.call_count

        # 验证结果相同
        assert result1 == result2

        # 验证第二次调用没有触发 API（缓存命中）
        assert second_call_count == first_call_count


@pytest.mark.unit
def test_cache_hit_performance_improvement(generator_with_cache, mock_openai_response):
    """测试缓存命中 - 性能提升"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用（带延迟）
    def slow_api_call(*args, **kwargs):
        time.sleep(0.1)  # 模拟 API 延迟
        return mock_openai_response

    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.side_effect = slow_api_call

        # 第一次调用 - 缓存未命中（慢）
        start_time = time.time()
        result1 = generator_with_cache.generate_content(input_text)
        first_duration = time.time() - start_time

        # 第二次调用 - 缓存命中（快）
        start_time = time.time()
        result2 = generator_with_cache.generate_content(input_text)
        second_duration = time.time() - start_time

        # 验证结果相同
        assert result1 == result2

        # 验证第二次调用更快（缓存命中）
        assert second_duration < first_duration
        assert second_duration < 0.05  # 缓存命中应该非常快


# ============================================================================
# 测试 5: 缓存失效（TTL 过期）
# ============================================================================


@pytest.mark.unit
def test_cache_expiration_ttl(generator_with_short_ttl, mock_openai_response):
    """测试缓存失效 - TTL 过期"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用
    with patch.object(
        generator_with_short_ttl.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 第一次调用 - 缓存未命中
        result1 = generator_with_short_ttl.generate_content(input_text)
        first_call_count = mock_call.call_count

        # 等待缓存过期（TTL = 1秒）
        time.sleep(1.5)

        # 第二次调用 - 缓存已过期，应该重新生成
        result2 = generator_with_short_ttl.generate_content(input_text)
        second_call_count = mock_call.call_count

        # 验证结果相同（内容相同）
        assert result1 == result2

        # 验证第二次调用触发了 API（缓存已过期）
        assert second_call_count > first_call_count


# ============================================================================
# 测试 6: 缓存保存（通过 generate_content 间接测试）
# ============================================================================


@pytest.mark.unit
def test_cache_save_through_generate(generator_with_cache, mock_openai_response):
    """测试缓存保存 - 通过 generate_content 间接测试"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 第一次调用 - 应该保存到缓存
        result1 = generator_with_cache.generate_content(input_text)

        # 验证缓存中有数据
        cache_key = generator_with_cache._generate_cache_key(input_text)
        cached_result = generator_with_cache.cache.get(cache_key)

        assert cached_result is not None
        assert cached_result == result1


# ============================================================================
# 测试 7: 缓存统计
# ============================================================================


@pytest.mark.unit
def test_cache_stats_enabled(generator_with_cache, mock_openai_response):
    """测试缓存统计 - 缓存启用时"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用并生成内容（会保存到缓存）
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response
        generator_with_cache.generate_content(input_text)

    # 获取缓存统计
    stats = generator_with_cache.get_cache_stats()

    # 验证统计信息
    assert stats is not None
    assert isinstance(stats, dict)
    assert "size" in stats
    assert "max_size" in stats
    assert "hits" in stats
    assert "misses" in stats
    assert "hit_rate" in stats


@pytest.mark.unit
def test_cache_stats_disabled(test_config_with_cache, temp_dir):
    """测试缓存统计 - 缓存禁用时"""
    # 创建禁用缓存的生成器
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "cache": {"enabled": False},
        "rate_limit": {"openai": {"enable_rate_limit": False}},
    }

    config_file = temp_dir / "config_no_cache.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    config_manager = ConfigManager(str(config_file))
    generator = RedBookContentGenerator(config_manager=config_manager)

    # 获取缓存统计（应该返回 None）
    stats = generator.get_cache_stats()

    assert stats is None


# ============================================================================
# 测试 8: 缓存清空
# ============================================================================


@pytest.mark.unit
def test_cache_clear(generator_with_cache, mock_openai_response):
    """测试缓存清空"""
    input_text1 = "老北京的胡同文化"
    input_text2 = "不同的输入内容"

    # 模拟 API 调用并生成多个内容
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 生成两个内容（会保存到缓存）
        generator_with_cache.generate_content(input_text1)
        generator_with_cache.generate_content(input_text2)

    # 验证缓存存在
    cache_key1 = generator_with_cache._generate_cache_key(input_text1)
    cache_key2 = generator_with_cache._generate_cache_key(input_text2)
    assert generator_with_cache.cache.get(cache_key1) is not None
    assert generator_with_cache.cache.get(cache_key2) is not None

    # 清空缓存
    generator_with_cache.clear_cache()

    # 验证缓存已清空
    assert generator_with_cache.cache.get(cache_key1) is None
    assert generator_with_cache.cache.get(cache_key2) is None


@pytest.mark.unit
def test_cache_clear_disabled(test_config_with_cache, temp_dir):
    """测试缓存清空 - 缓存禁用时"""
    # 创建禁用缓存的生成器
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "cache": {"enabled": False},
        "rate_limit": {"openai": {"enable_rate_limit": False}},
    }

    config_file = temp_dir / "config_no_cache.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    config_manager = ConfigManager(str(config_file))
    generator = RedBookContentGenerator(config_manager=config_manager)

    # 清空缓存（不应该抛出异常）
    generator.clear_cache()


# ============================================================================
# 测试 9: 不同输入的缓存隔离
# ============================================================================


@pytest.mark.unit
def test_cache_isolation_different_inputs(generator_with_cache, mock_openai_response):
    """测试不同输入的缓存隔离"""
    input_text1 = "老北京的胡同文化"
    input_text2 = "不同的输入内容"

    # 为不同输入创建不同的响应
    response1 = mock_openai_response.copy()
    response1["content"] = "第一个输入的内容"

    response2 = mock_openai_response.copy()
    response2["content"] = "第二个输入的内容"

    # 模拟 API 调用
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        # 第一次调用返回 response1
        mock_call.return_value = response1
        result1 = generator_with_cache.generate_content(input_text1)

        # 第二次调用返回 response2
        mock_call.return_value = response2
        result2 = generator_with_cache.generate_content(input_text2)

    # 验证缓存隔离
    assert result1 is not None
    assert result2 is not None
    assert result1["content"] == "第一个输入的内容"
    assert result2["content"] == "第二个输入的内容"
    assert result1 != result2


# ============================================================================
# 测试 10: 缓存与 API 调用的集成
# ============================================================================


@pytest.mark.unit
def test_cache_integration_with_api_calls(generator_with_cache, mock_openai_response):
    """测试缓存与 API 调用的集成"""
    input_text = "老北京的胡同文化"

    # 模拟 API 调用
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 第一次调用 - 应该触发 API 调用并保存到缓存
        result1 = generator_with_cache.generate_content(input_text)
        assert mock_call.call_count >= 1

        # 第二次调用 - 应该从缓存读取，不触发 API 调用
        first_call_count = mock_call.call_count
        result2 = generator_with_cache.generate_content(input_text)
        assert mock_call.call_count == first_call_count  # 调用次数不变

        # 第三次调用 - 仍然从缓存读取
        result3 = generator_with_cache.generate_content(input_text)
        assert mock_call.call_count == first_call_count  # 调用次数不变

        # 验证所有结果相同
        assert result1 == result2 == result3


@pytest.mark.unit
def test_cache_integration_multiple_inputs(generator_with_cache, mock_openai_response):
    """测试缓存与多个输入的集成"""
    inputs = [
        "老北京的胡同文化",
        "四合院的建筑特色",
        "传统北京小吃",
    ]

    # 模拟 API 调用
    with patch.object(
        generator_with_cache.api_handler, "call_openai_with_evaluation"
    ) as mock_call:
        mock_call.return_value = mock_openai_response

        # 第一轮：所有输入都应该触发 API 调用
        results1 = []
        for input_text in inputs:
            result = generator_with_cache.generate_content(input_text)
            results1.append(result)

        first_round_calls = mock_call.call_count

        # 第二轮：所有输入都应该从缓存读取
        results2 = []
        for input_text in inputs:
            result = generator_with_cache.generate_content(input_text)
            results2.append(result)

        second_round_calls = mock_call.call_count

        # 验证第二轮没有触发新的 API 调用
        assert second_round_calls == first_round_calls

        # 验证结果相同
        for i in range(len(inputs)):
            assert results1[i] == results2[i]


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=src.content_generator",
        "--cov=src.core.cache_manager",
        "--cov-report=term-missing",
    ])
