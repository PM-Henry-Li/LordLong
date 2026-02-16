#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 image_generator.py 的配置管理器集成
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.config_manager import ConfigManager
from src.image_generator import ImageGenerator


def test_init_with_config_manager():
    """测试使用 ConfigManager 初始化"""
    print("\n测试 1: 使用 ConfigManager 初始化")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {
            "openai_api_key": "test-key-123",
            "image_model": "wan2.2-t2i-flash",
            "output_image_dir": "test_output/images",
            "enable_ai_rewrite": False,
            "rewrite_model": "qwen-max",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        # 使用 ConfigManager 初始化
        config_manager = ConfigManager(temp_config_path)
        generator = ImageGenerator(config_manager=config_manager)

        # 验证配置已正确加载
        assert generator.config_manager.get("openai_api_key") == "test-key-123"
        assert generator.config_manager.get("image_model") == "wan2.2-t2i-flash"
        assert generator.config_manager.get("output_image_dir") == "test_output/images"
        assert generator.api_key == "test-key-123"
        assert generator.image_model == "wan2.2-t2i-flash"
        assert generator.enable_ai_rewrite == False
        assert generator.rewrite_model == "qwen-max"

        print("  ✅ 使用 ConfigManager 初始化成功")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_backward_compatibility():
    """测试向后兼容性（不传入 ConfigManager）"""
    print("\n测试 2: 向后兼容性测试")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {"openai_api_key": "test-key-456", "image_model": "qwen-image-plus", "enable_ai_rewrite": True}
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        # 使用旧方式初始化（只传入 config_path）
        generator = ImageGenerator(config_path=temp_config_path)

        # 验证配置已正确加载
        assert generator.config_manager.get("openai_api_key") == "test-key-456"
        assert generator.config_manager.get("image_model") == "qwen-image-plus"
        assert generator.api_key == "test-key-456"
        assert generator.image_model == "qwen-image-plus"
        assert generator.enable_ai_rewrite == True

        print("  ✅ 向后兼容性测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_config_access():
    """测试配置访问"""
    print("\n测试 3: 配置访问测试")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {
            "openai_api_key": "test-key-789",
            "image_model": "wan2.2-t2i-flash",
            "output_image_dir": "output/test_images",
            "enable_ai_rewrite": False,
            "rewrite_model": "qwen-turbo",
        }
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = ImageGenerator(config_manager=config_manager)

        # 测试各种配置访问
        assert generator.config_manager.get("image_model") == "wan2.2-t2i-flash"
        assert generator.config_manager.get("output_image_dir") == "output/test_images"
        assert generator.config_manager.get("enable_ai_rewrite") == False
        assert generator.config_manager.get("rewrite_model") == "qwen-turbo"

        # 测试默认值
        assert generator.config_manager.get("nonexistent_key", "default") == "default"

        print("  ✅ 配置访问测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_environment_variable_override():
    """测试环境变量覆盖"""
    print("\n测试 4: 环境变量覆盖测试")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {"openai_api_key": "file-key", "image_model": "qwen-image-plus"}
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    # 设置环境变量
    original_env = os.environ.get("IMAGE_MODEL")
    os.environ["IMAGE_MODEL"] = "wan2.2-t2i-flash-from-env"

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = ImageGenerator(config_manager=config_manager)

        # 环境变量应该覆盖配置文件
        assert generator.config_manager.get("image_model") == "wan2.2-t2i-flash-from-env"
        assert generator.image_model == "wan2.2-t2i-flash-from-env"

        print("  ✅ 环境变量覆盖测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 恢复环境变量
        if original_env is not None:
            os.environ["IMAGE_MODEL"] = original_env
        else:
            os.environ.pop("IMAGE_MODEL", None)

        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_nested_config_access():
    """测试嵌套配置访问"""
    print("\n测试 5: 嵌套配置访问测试")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {"openai_api_key": "test-key", "api": {"image": {"size": "1024*1365", "timeout": 180}}}
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = ImageGenerator(config_manager=config_manager)

        # 测试嵌套配置访问
        assert generator.config_manager.get("api.image.size") == "1024*1365"
        assert generator.config_manager.get("api.image.timeout") == 180

        print("  ✅ 嵌套配置访问测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_api_key_from_env():
    """测试从环境变量读取 API Key"""
    print("\n测试 6: 从环境变量读取 API Key")

    # 创建临时配置文件（不包含 API Key）
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {"image_model": "wan2.2-t2i-flash"}
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    # 设置环境变量
    original_env = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "env-api-key-123"

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = ImageGenerator(config_manager=config_manager)

        # API Key 应该从环境变量读取
        assert generator.api_key == "env-api-key-123"

        print("  ✅ 从环境变量读取 API Key 测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # 恢复环境变量
        if original_env is not None:
            os.environ["OPENAI_API_KEY"] = original_env
        else:
            os.environ.pop("OPENAI_API_KEY", None)

        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 image_generator.py 配置管理器集成")
    print("=" * 60)

    tests = [
        test_init_with_config_manager,
        test_backward_compatibility,
        test_config_access,
        test_environment_variable_override,
        test_nested_config_access,
        test_api_key_from_env,
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
    sys.exit(main())
