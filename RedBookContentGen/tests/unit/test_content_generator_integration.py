#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 content_generator.py 的集成功能
验证配置迁移后的完整工作流程
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


def test_setup_paths():
    """测试路径设置功能"""
    print("\n测试 1: 路径设置功能")

    # 创建临时配置
    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "input_file": f"{temp_dir}/input.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 验证路径已创建
            assert os.path.exists(generator.image_dir)
            assert "output/images" in generator.image_dir

            print("  ✅ 路径设置功能正常")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            return False


def test_read_input_file():
    """测试读取输入文件功能"""
    print("\n测试 2: 读取输入文件功能")

    # 创建临时配置和输入文件
    with tempfile.TemporaryDirectory() as temp_dir:
        input_file = os.path.join(temp_dir, "input.txt")
        test_content = "这是一段测试内容，关于老北京的胡同文化。"

        with open(input_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        config_data = {
            "input_file": input_file,
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 读取输入文件
            content = generator.read_input_file()

            # 验证内容正确
            assert content == test_content

            print("  ✅ 读取输入文件功能正常")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            return False


def test_config_priority():
    """测试配置优先级（环境变量 > 配置文件 > 默认值）"""
    print("\n测试 3: 配置优先级")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 配置文件中设置一个值
        config_data = {
            "openai_model": "qwen-plus-from-file",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # 设置环境变量
        original_env = os.environ.get("OPENAI_MODEL")
        os.environ["OPENAI_MODEL"] = "qwen-turbo-from-env"

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 环境变量应该覆盖配置文件
            assert generator.config_manager.get("openai_model") == "qwen-turbo-from-env"

            print("  ✅ 配置优先级正确")
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


def test_missing_input_file():
    """测试缺失输入文件的错误处理"""
    print("\n测试 4: 缺失输入文件的错误处理")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            "input_file": f"{temp_dir}/nonexistent.txt",
            "output_excel": f"{temp_dir}/output/test.xlsx",
            "output_image_dir": f"{temp_dir}/output/images",
            "openai_api_key": "test-key",
        }

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 尝试读取不存在的文件，应该抛出 FileNotFoundError
            try:
                generator.read_input_file()
                print("  ❌ 应该抛出 FileNotFoundError")
                return False
            except FileNotFoundError as e:
                # 预期的错误
                assert "不存在" in str(e)
                print("  ✅ 错误处理正确")
                return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            return False


def test_default_config_values():
    """测试默认配置值"""
    print("\n测试 5: 默认配置值")

    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建最小配置文件
        config_data = {"openai_api_key": "test-key"}

        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        try:
            config_manager = ConfigManager(config_file)
            generator = RedBookContentGenerator(config_manager=config_manager)

            # 验证默认值
            assert generator.config_manager.get("openai_model") == "qwen-plus"
            assert generator.config_manager.get("input_file") == "input/input_content.txt"
            assert generator.config_manager.get("output_excel") == "output/redbook_content.xlsx"
            assert generator.config_manager.get("api.openai.timeout") == 30
            assert generator.config_manager.get("api.openai.max_retries") == 3

            print("  ✅ 默认配置值正确")
            return True
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            return False


def main():
    """运行所有集成测试"""
    print("=" * 60)
    print("开始集成测试：content_generator.py 配置迁移")
    print("=" * 60)

    tests = [
        test_setup_paths,
        test_read_input_file,
        test_config_priority,
        test_missing_input_file,
        test_default_config_values,
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
        print("✅ 所有集成测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
