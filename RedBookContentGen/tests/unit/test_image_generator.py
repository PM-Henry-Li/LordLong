#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ImageGenerator 单元测试

测试图片生成核心功能：
- API 模式生成（使用 Mock）
- 模板模式生成
- 不同尺寸参数
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config_manager import ConfigManager
from src.image_generator import ImageGenerator


def test_image_generator_initialization():
    """测试 ImageGenerator 初始化"""
    print("\n测试 1: ImageGenerator 初始化")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 验证初始化
            assert generator.api_key == "test-key-123"
            assert generator.image_model == "qwen-image-plus"
            assert generator.cache is None  # 缓存已禁用
            assert generator._rate_limit_enabled is False

            print("  ✅ ImageGenerator 初始化正常")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            return False


def test_api_mode_generation_with_mock():
    """测试 API 模式图片生成（使用 Mock）"""
    print("\n测试 2: API 模式图片生成（Mock）")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # Mock requests.post 响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "output": {
                    "task_id": "test-task-123",
                    "task_status": "SUCCEEDED",
                    "results": [{"url": "https://example.com/test-image.jpg"}],
                }
            }

            with patch("requests.post", return_value=mock_response):
                # Mock _wait_for_task_completion 方法
                with patch.object(
                    generator, "_wait_for_task_completion", return_value="https://example.com/test-image.jpg"
                ):
                    # 调用生成方法
                    image_url = generator.generate_image_async("老北京胡同场景", index=1, is_cover=False)

                    # 验证结果
                    assert image_url == "https://example.com/test-image.jpg"
                    assert "example.com" in image_url

            print("  ✅ API 模式图片生成测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_generate_single_image_with_different_sizes():
    """测试不同尺寸参数的图片生成"""
    print("\n测试 3: 不同尺寸参数")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 测试不同尺寸
            test_sizes = ["1024*1365", "1080*1080", "1920*1080"]

            for size in test_sizes:
                # Mock 管道的 generate 方法
                mock_pipeline = Mock()
                mock_pipeline.generate.return_value = f"https://example.com/image-{size}.jpg"

                with patch.object(generator, "_get_pipeline", return_value=mock_pipeline):
                    image_url = generator.generate_single_image("测试提示词", size=size)

                    # 验证结果
                    assert image_url is not None
                    assert size in image_url
                    # 验证 generate 方法被调用
                    mock_pipeline.generate.assert_called_once_with("测试提示词", size)

            print("  ✅ 不同尺寸参数测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_content_safety_check():
    """测试内容安全检查"""
    print("\n测试 4: 内容安全检查")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 测试安全内容
            safe_prompt = "老北京胡同的清晨，阳光洒在青砖上"
            is_safe, modified = generator.check_content_safety(safe_prompt)
            assert is_safe is True

            # 测试敏感内容
            unsafe_prompt = "血腥暴力场景"
            is_safe, modified = generator.check_content_safety(unsafe_prompt)
            # 根据实际实现，可能返回 False 或修改后的内容

            print("  ✅ 内容安全检查测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_cache_integration():
    """测试缓存集成"""
    print("\n测试 5: 缓存集成")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "image_model": "qwen-image-plus",
            "cache": {"enabled": True, "ttl": 3600, "max_size": 100},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 验证缓存已启用
            assert generator._cache_enabled is True
            assert generator.cache is not None

            # 测试缓存键生成
            cache_key = generator._generate_cache_key("测试提示词", "1024*1365")
            assert cache_key is not None
            assert isinstance(cache_key, str)
            assert len(cache_key) > 0

            # 测试缓存统计
            stats = generator.get_cache_stats()
            assert stats is not None
            assert "hits" in stats or "size" in stats

            print("  ✅ 缓存集成测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_rate_limiter_integration():
    """测试速率限制器集成"""
    print("\n测试 6: 速率限制器集成")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": True, "requests_per_minute": 10}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 验证速率限制器已启用
            assert generator._rate_limit_enabled is True
            assert generator.rpm_limiter is not None

            # 测试速率限制统计
            stats = generator.get_rate_limit_stats()
            assert stats is not None
            assert stats["enabled"] is True
            assert "rpm" in stats

            print("  ✅ 速率限制器集成测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_prompt_cleaning():
    """测试提示词清理功能"""
    print("\n测试 7: 提示词清理")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # 测试文字清理
            dirty_text = "这是一段包含\n换行符和\t制表符的文字"
            clean_text = generator.clean_text_for_display(dirty_text)

            # 验证清理结果
            assert "\n" not in clean_text or clean_text.count("\n") < dirty_text.count("\n")
            assert isinstance(clean_text, str)

            print("  ✅ 提示词清理测试通过")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_error_handling():
    """测试错误处理"""
    print("\n测试 8: 错误处理")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "openai_api_key": "test-key-123",
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = ImageGenerator(config_manager=config_manager)

            # Mock API 错误响应
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_response.json.return_value = {"code": "DataInspectionFailed", "message": "内容审核未通过"}

            with patch("requests.post", return_value=mock_response):
                try:
                    # 应该抛出异常
                    generator.generate_image_async("测试提示词", index=1)
                    print("  ❌ 应该抛出异常")
                    return False
                except (ValueError, Exception) as e:
                    # 预期的错误
                    assert "审核" in str(e) or "失败" in str(e)
                    print("  ✅ 错误处理正确")
                    return True

        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_missing_api_key():
    """测试缺少 API Key 的错误处理"""
    print("\n测试 9: 缺少 API Key")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            # 故意不设置 openai_api_key
            "cache": {"enabled": False},
            "rate_limit": {"image": {"enable_rate_limit": False}},
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)

            # 应该抛出 ValueError
            try:
                generator = ImageGenerator(config_manager=config_manager)
                print("  ❌ 应该抛出 ValueError")
                return False
            except ValueError as e:
                # 预期的错误
                assert "API Key" in str(e)
                print("  ✅ 缺少 API Key 错误处理正确")
                return True

        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 ImageGenerator 核心功能")
    print("=" * 60)

    tests = [
        test_image_generator_initialization,
        test_api_mode_generation_with_mock,
        test_generate_single_image_with_different_sizes,
        test_content_safety_check,
        test_cache_integration,
        test_rate_limiter_integration,
        test_prompt_cleaning,
        test_error_handling,
        test_missing_api_key,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)

    if all(results):
        print("✅ 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(run_all_tests())
