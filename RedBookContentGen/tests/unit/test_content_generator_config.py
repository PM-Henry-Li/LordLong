#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 content_generator.py 的配置管理器集成
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.config_manager import ConfigManager
from src.content_generator import RedBookContentGenerator


def test_init_with_config_manager():
    """测试使用 ConfigManager 初始化"""
    print("\n测试 1: 使用 ConfigManager 初始化")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {
            "input_file": "test_input.txt",
            "output_excel": "test_output/test.xlsx",
            "output_image_dir": "test_output/images",
            "openai_api_key": "test-key-123",
            "openai_model": "qwen-plus",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        # 使用 ConfigManager 初始化
        config_manager = ConfigManager(temp_config_path)
        generator = RedBookContentGenerator(config_manager=config_manager)

        # 验证配置已正确加载
        assert generator.config_manager.get("openai_api_key") == "test-key-123"
        assert generator.config_manager.get("openai_model") == "qwen-plus"
        assert generator.config_manager.get("input_file") == "test_input.txt"

        print("  ✅ 使用 ConfigManager 初始化成功")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
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
        config_data = {
            "input_file": "test_input.txt",
            "output_excel": "test_output/test.xlsx",
            "output_image_dir": "test_output/images",
            "openai_api_key": "test-key-456",
            "openai_model": "qwen-turbo",
        }
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        # 使用旧方式初始化（只传入 config_path）
        generator = RedBookContentGenerator(config_path=temp_config_path)

        # 验证配置已正确加载
        assert generator.config_manager.get("openai_api_key") == "test-key-456"
        assert generator.config_manager.get("openai_model") == "qwen-turbo"

        print("  ✅ 向后兼容性测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
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
            "input_file": "input/test.txt",
            "output_excel": "output/test.xlsx",
            "output_image_dir": "output/images",
            "openai_api_key": "test-key-789",
            "openai_model": "qwen-max",
        }
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = RedBookContentGenerator(config_manager=config_manager)

        # 测试各种配置访问
        assert generator.config_manager.get("input_file") == "input/test.txt"
        assert generator.config_manager.get("output_excel") == "output/test.xlsx"
        assert generator.config_manager.get("output_image_dir") == "output/images"
        assert generator.config_manager.get("openai_model") == "qwen-max"

        # 测试默认值
        assert generator.config_manager.get("nonexistent_key", "default") == "default"

        print("  ✅ 配置访问测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
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
        config_data = {"openai_api_key": "file-key", "openai_model": "qwen-plus"}
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    # 设置环境变量
    original_env = os.environ.get("OPENAI_MODEL")
    os.environ["OPENAI_MODEL"] = "qwen-turbo-from-env"

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = RedBookContentGenerator(config_manager=config_manager)

        # 环境变量应该覆盖配置文件
        assert generator.config_manager.get("openai_model") == "qwen-turbo-from-env"

        print("  ✅ 环境变量覆盖测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False
    finally:
        # 恢复环境变量
        if original_env is not None:
            os.environ["OPENAI_MODEL"] = original_env
        else:
            os.environ.pop("OPENAI_MODEL", None)

        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def test_nested_config_access():
    """测试嵌套配置访问"""
    print("\n测试 5: 嵌套配置访问测试")

    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        config_data = {"openai_api_key": "test-key", "api": {"openai": {"timeout": 60, "max_retries": 5}}}
        json.dump(config_data, f, ensure_ascii=False, indent=2)
        temp_config_path = f.name

    try:
        config_manager = ConfigManager(temp_config_path)
        generator = RedBookContentGenerator(config_manager=config_manager)

        # 测试嵌套配置访问
        assert generator.config_manager.get("api.openai.timeout") == 60
        assert generator.config_manager.get("api.openai.max_retries") == 5

        print("  ✅ 嵌套配置访问测试通过")
        return True
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_config_path):
            os.unlink(temp_config_path)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 content_generator.py 配置管理器集成")
    print("=" * 60)

    tests = [
        test_init_with_config_manager,
        test_backward_compatibility,
        test_config_access,
        test_environment_variable_override,
        test_nested_config_access,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
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
