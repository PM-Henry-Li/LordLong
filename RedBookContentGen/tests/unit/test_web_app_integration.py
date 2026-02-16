#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_app.py 集成测试

验证 web_app.py 与 ConfigManager 的集成工作正常
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_web_app_basic_functionality():
    """测试 web_app 基本功能"""
    import web_app

    # 验证 Flask 应用已创建
    assert web_app.app is not None
    print("✅ Flask 应用已创建")

    # 验证 ConfigManager 已初始化
    assert web_app.config_manager is not None
    print("✅ ConfigManager 已初始化")

    # 验证输出目录已创建
    assert web_app.OUTPUT_DIR.exists()
    print(f"✅ 输出目录已创建: {web_app.OUTPUT_DIR}")


def test_web_app_routes():
    """测试 web_app 路由"""
    import web_app

    # 使用测试客户端
    client = web_app.app.test_client()

    # 测试首页
    response = client.get("/")
    assert response.status_code == 200
    print("✅ 首页路由正常")

    # 测试模型列表接口
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "models" in data
    assert "image_sizes" in data
    print("✅ 模型列表接口正常")


def test_config_manager_integration():
    """测试 ConfigManager 集成"""
    import web_app
    from src.core.config_manager import ConfigManager

    # 验证 config_manager 是 ConfigManager 实例
    assert isinstance(web_app.config_manager, ConfigManager)

    # 验证可以获取配置
    api_key = web_app.config_manager.get("openai_api_key")
    assert api_key is not None or os.getenv("OPENAI_API_KEY") is not None
    print("✅ ConfigManager 集成正常")


def test_helper_functions():
    """测试辅助函数"""
    import web_app

    # 测试 get_available_models
    models = web_app.get_available_models()
    assert isinstance(models, dict)
    assert len(models) > 0
    print(f"✅ get_available_models 返回 {len(models)} 个模型")

    # 测试 get_xiaohongshu_image_sizes
    sizes = web_app.get_xiaohongshu_image_sizes()
    assert isinstance(sizes, dict)
    assert len(sizes) > 0
    print(f"✅ get_xiaohongshu_image_sizes 返回 {len(sizes)} 种尺寸")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("web_app.py 集成测试")
    print("=" * 60)
    print()

    tests = [
        ("基本功能", test_web_app_basic_functionality),
        ("路由功能", test_web_app_routes),
        ("ConfigManager 集成", test_config_manager_integration),
        ("辅助函数", test_helper_functions),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\n测试: {name}")
            print("-" * 60)
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
