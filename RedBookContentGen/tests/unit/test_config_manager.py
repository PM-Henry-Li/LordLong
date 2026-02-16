#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigManager 单元测试
"""

import json
import os
import sys
import tempfile
import time
import threading
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config_manager import ConfigManager


def test_default_config():
    """测试默认配置"""
    config = ConfigManager(config_path="nonexistent.json")

    # 验证默认值
    assert config.get("openai_model") == "qwen-plus"
    assert config.get("image_generation_mode") == "template"
    assert config.get("template_style") == "retro_chinese"
    assert config.get("api.openai.timeout") == 30
    assert config.get("cache.enabled") is True

    print("✅ 默认配置测试通过")


def test_json_config_loading():
    """测试 JSON 配置文件加载"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max", "openai_api_key": "test-key-123", "api": {"openai": {"timeout": 60}}}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证配置文件覆盖了默认值
        assert config.get("openai_model") == "qwen-max"
        assert config.get("openai_api_key") == "test-key-123"
        assert config.get("api.openai.timeout") == 60

        # 验证未覆盖的默认值仍然存在
        assert config.get("template_style") == "retro_chinese"

        print("✅ JSON 配置文件加载测试通过")
    finally:
        os.unlink(temp_path)


def test_yaml_config_loading():
    """测试 YAML 配置文件加载"""
    try:
        import yaml
    except ImportError:
        print("⚠️  跳过 YAML 测试（未安装 PyYAML）")
        return

    # 创建临时 YAML 配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml_content = """
openai_model: qwen-turbo
openai_api_key: yaml-test-key
api:
  openai:
    timeout: 45
"""
        f.write(yaml_content)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证 YAML 配置加载
        assert config.get("openai_model") == "qwen-turbo"
        assert config.get("openai_api_key") == "yaml-test-key"
        assert config.get("api.openai.timeout") == 45

        print("✅ YAML 配置文件加载测试通过")
    finally:
        os.unlink(temp_path)


def test_environment_variable_override():
    """测试环境变量覆盖"""
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = "env-test-key"
    os.environ["OPENAI_MODEL"] = "qwen-max-env"
    os.environ["ENABLE_AI_REWRITE"] = "true"
    os.environ["CACHE_TTL"] = "7200"

    try:
        config = ConfigManager(config_path="nonexistent.json")

        # 验证环境变量覆盖了默认值
        assert config.get("openai_api_key") == "env-test-key"
        assert config.get("openai_model") == "qwen-max-env"
        assert config.get("enable_ai_rewrite") is True
        assert config.get("cache.ttl") == 7200

        print("✅ 环境变量覆盖测试通过")
    finally:
        # 清理环境变量
        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_MODEL"]
        del os.environ["ENABLE_AI_REWRITE"]
        del os.environ["CACHE_TTL"]


def test_priority_order():
    """测试配置优先级：环境变量 > 配置文件 > 默认值"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max-file", "openai_api_key": "file-key"}
        json.dump(test_config, f)
        temp_path = f.name

    # 设置环境变量
    os.environ["OPENAI_MODEL"] = "qwen-max-env"

    try:
        config = ConfigManager(config_path=temp_path)

        # 环境变量应该覆盖配置文件
        assert config.get("openai_model") == "qwen-max-env"

        # 配置文件应该覆盖默认值
        assert config.get("openai_api_key") == "file-key"

        # 默认值应该存在（未被覆盖）
        assert config.get("template_style") == "retro_chinese"

        print("✅ 配置优先级测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["OPENAI_MODEL"]


def test_comprehensive_priority():
    """测试全面的配置优先级场景"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "openai_model": "qwen-max-file",
            "openai_api_key": "file-key",
            "template_style": "modern_minimal",
            "api": {"openai": {"timeout": 45, "max_retries": 5}},
            "cache": {"enabled": False, "ttl": 1800},
        }
        json.dump(test_config, f)
        temp_path = f.name

    # 设置多个环境变量
    os.environ["OPENAI_MODEL"] = "qwen-turbo-env"
    os.environ["OPENAI_TIMEOUT"] = "60"
    os.environ["CACHE_ENABLED"] = "true"

    try:
        config = ConfigManager(config_path=temp_path)

        # 1. 环境变量优先级最高
        assert config.get("openai_model") == "qwen-turbo-env"
        assert config.get("api.openai.timeout") == 60
        assert config.get("cache.enabled") is True

        # 2. 配置文件次之（未被环境变量覆盖的）
        assert config.get("openai_api_key") == "file-key"
        assert config.get("template_style") == "modern_minimal"
        assert config.get("api.openai.max_retries") == 5
        assert config.get("cache.ttl") == 1800

        # 3. 默认值最低（未被配置文件和环境变量覆盖的）
        assert config.get("image_generation_mode") == "template"
        assert config.get("rate_limit.openai.requests_per_minute") == 60

        print("✅ 全面配置优先级测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["OPENAI_MODEL"]
        del os.environ["OPENAI_TIMEOUT"]
        del os.environ["CACHE_ENABLED"]


def test_env_value_type_conversion():
    """测试环境变量类型转换"""
    # 设置各种类型的环境变量
    os.environ["OPENAI_TIMEOUT"] = "60"  # 整数
    os.environ["CACHE_ENABLED"] = "true"  # 布尔值 true
    os.environ["ENABLE_AI_REWRITE"] = "false"  # 布尔值 false
    os.environ["CACHE_TTL"] = "3600"  # 整数
    os.environ["OPENAI_MODEL"] = "qwen-plus"  # 字符串

    try:
        config = ConfigManager(config_path="nonexistent.json")

        # 验证类型转换
        assert config.get("api.openai.timeout") == 60
        assert isinstance(config.get("api.openai.timeout"), int)

        assert config.get("cache.enabled") is True
        assert isinstance(config.get("cache.enabled"), bool)

        assert config.get("enable_ai_rewrite") is False
        assert isinstance(config.get("enable_ai_rewrite"), bool)

        assert config.get("cache.ttl") == 3600
        assert isinstance(config.get("cache.ttl"), int)

        assert config.get("openai_model") == "qwen-plus"
        assert isinstance(config.get("openai_model"), str)

        print("✅ 环境变量类型转换测试通过")
    finally:
        del os.environ["OPENAI_TIMEOUT"]
        del os.environ["CACHE_ENABLED"]
        del os.environ["ENABLE_AI_REWRITE"]
        del os.environ["CACHE_TTL"]
        del os.environ["OPENAI_MODEL"]


def test_config_source_tracking():
    """测试配置来源追踪"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max-file", "openai_api_key": "file-key"}
        json.dump(test_config, f)
        temp_path = f.name

    # 设置环境变量
    os.environ["OPENAI_MODEL"] = "qwen-turbo-env"

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证配置来源
        assert config.get_config_source("openai_model") == "environment"
        assert config.get_config_source("openai_api_key") == "file"
        assert config.get_config_source("template_style") == "default"
        assert config.get_config_source("nonexistent_key") == "not_found"

        print("✅ 配置来源追踪测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["OPENAI_MODEL"]


def test_nested_env_override():
    """测试嵌套配置的环境变量覆盖"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "api": {"openai": {"timeout": 30, "max_retries": 3}},
            "rate_limit": {"openai": {"requests_per_minute": 50}},
        }
        json.dump(test_config, f)
        temp_path = f.name

    # 设置环境变量覆盖嵌套配置
    os.environ["OPENAI_TIMEOUT"] = "90"
    os.environ["RATE_LIMIT_OPENAI_RPM"] = "100"

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证环境变量覆盖了嵌套配置
        assert config.get("api.openai.timeout") == 90
        assert config.get("rate_limit.openai.requests_per_minute") == 100

        # 验证未覆盖的嵌套配置保持文件值
        assert config.get("api.openai.max_retries") == 3

        print("✅ 嵌套配置环境变量覆盖测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["OPENAI_TIMEOUT"]
        del os.environ["RATE_LIMIT_OPENAI_RPM"]


def test_get_set_methods():
    """测试 get 和 set 方法"""
    config = ConfigManager(config_path="nonexistent.json")

    # 测试简单键
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"

    # 测试嵌套键
    config.set("nested.key.value", 123)
    assert config.get("nested.key.value") == 123

    # 测试默认值
    assert config.get("nonexistent_key", "default") == "default"

    print("✅ get/set 方法测试通过")


def test_validate():
    """测试配置验证"""
    # 创建有效配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        valid_config = {
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "openai_base_url": "https://test.com",
        }
        json.dump(valid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.validate() is True

        print("✅ 配置验证测试通过")
    finally:
        os.unlink(temp_path)


def test_validate_missing_required_fields():
    """测试缺少必需字段的验证"""
    # 创建缺少必需字段的配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        invalid_config = {
            "openai_model": "qwen-plus"
            # 缺少 openai_api_key，openai_base_url 有默认值
        }
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.validate() is False

        errors = config.get_validation_errors()
        assert len(errors) >= 1
        assert any("openai_api_key" in error for error in errors)

        print("✅ 缺少必需字段验证测试通过")
    finally:
        os.unlink(temp_path)


def test_validate_type_errors():
    """测试类型错误验证"""
    # 创建类型错误的配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        invalid_config = {
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "openai_base_url": "https://test.com",
            "api": {"openai": {"timeout": "not-a-number", "max_retries": 3.5}},  # 应该是整数  # 应该是整数
            "cache": {"enabled": "yes"},  # 应该是布尔值
        }
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.validate() is False

        errors = config.get_validation_errors()
        assert len(errors) >= 3
        assert any("超时时间必须是整数" in error for error in errors)
        assert any("最大重试次数必须是整数" in error for error in errors)
        assert any("缓存启用标志必须是布尔值" in error for error in errors)

        print("✅ 类型错误验证测试通过")
    finally:
        os.unlink(temp_path)


def test_validate_value_range():
    """测试值范围验证"""
    # 创建值范围错误的配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        invalid_config = {
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "openai_base_url": "https://test.com",
            "api": {"openai": {"timeout": -10, "max_retries": -1}},  # 应该 > 0  # 应该 >= 0
            "cache": {"ttl": 0},  # 应该 > 0
            "rate_limit": {"openai": {"requests_per_minute": -5}},  # 应该 > 0
        }
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.validate() is False

        errors = config.get_validation_errors()
        assert len(errors) >= 4
        assert any("超时时间必须大于0" in error for error in errors)
        assert any("最大重试次数不能为负数" in error for error in errors)
        assert any("缓存TTL必须大于0" in error for error in errors)
        assert any("速率限制必须大于0" in error for error in errors)

        print("✅ 值范围验证测试通过")
    finally:
        os.unlink(temp_path)


def test_validate_url_format():
    """测试 URL 格式验证"""
    # 创建 URL 格式错误的配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        invalid_config = {
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "openai_base_url": "invalid-url",  # 无效的 URL 格式
        }
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.validate() is False

        errors = config.get_validation_errors()
        assert any("URL格式无效" in error for error in errors)

        print("✅ URL 格式验证测试通过")
    finally:
        os.unlink(temp_path)


def test_validate_enum_values():
    """测试枚举值验证"""
    # 创建枚举值错误的配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        invalid_config = {
            "openai_api_key": "test-key",
            "openai_model": "qwen-plus",
            "openai_base_url": "https://test.com",
            "image_generation_mode": "invalid_mode",  # 无效的模式
            "template_style": "invalid_style",  # 无效的风格
            "logging": {"level": "INVALID_LEVEL"},  # 无效的日志级别
        }
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.validate() is False

        errors = config.get_validation_errors()
        assert len(errors) >= 3
        assert any("图片生成模式无效" in error for error in errors)
        assert any("模板风格无效" in error for error in errors)
        assert any("日志级别无效" in error for error in errors)

        print("✅ 枚举值验证测试通过")
    finally:
        os.unlink(temp_path)


def test_get_validation_errors():
    """测试获取验证错误列表"""
    # 创建多个错误的配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        invalid_config = {
            "openai_model": "qwen-plus",
            # 缺少 openai_api_key (openai_base_url 有默认值)
            "api": {"openai": {"timeout": "invalid"}},  # 类型错误
            "image_generation_mode": "invalid_mode",  # 枚举值错误
        }
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        errors = config.get_validation_errors()

        # 应该有至少 3 个错误：缺少 api_key、timeout 类型错误、image_mode 枚举错误
        assert len(errors) >= 3
        assert isinstance(errors, list)
        assert all(isinstance(error, str) for error in errors)

        print("✅ 获取验证错误列表测试通过")
    finally:
        os.unlink(temp_path)


def test_reload():
    """测试配置重新加载"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.get("openai_model") == "qwen-max"

        # 修改配置
        config.set("openai_model", "qwen-turbo")
        assert config.get("openai_model") == "qwen-turbo"

        # 重新加载应该恢复到文件中的值
        config.reload()
        assert config.get("openai_model") == "qwen-max"

        print("✅ 配置重新加载测试通过")
    finally:
        os.unlink(temp_path)


def test_get_all():
    """测试获取所有配置"""
    config = ConfigManager(config_path="nonexistent.json")
    all_config = config.get_all()

    # 验证返回的是字典
    assert isinstance(all_config, dict)

    # 验证包含默认配置
    assert "openai_model" in all_config
    assert "api" in all_config

    # 验证返回的是深拷贝（修改不影响原配置）
    all_config["openai_model"] = "modified"
    assert config.get("openai_model") != "modified"

    print("✅ get_all 方法测试通过")


def test_manual_reload():
    """测试手动重载配置"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.get("openai_model") == "qwen-max"

        # 修改内存中的配置
        config.set("openai_model", "qwen-turbo")
        assert config.get("openai_model") == "qwen-turbo"

        # 手动重载应该恢复到文件中的值
        config.reload()
        assert config.get("openai_model") == "qwen-max"

        print("✅ 手动重载配置测试通过")
    finally:
        os.unlink(temp_path)


def test_auto_reload_on_file_change():
    """测试文件变化时自动重载"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max", "openai_api_key": "test-key"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        assert config.get("openai_model") == "qwen-max"

        # 启动监控
        config.start_watching(check_interval=0.5)
        assert config.is_watching() is True

        # 等待一小段时间确保监控线程启动
        time.sleep(0.2)

        # 修改配置文件
        with open(temp_path, "w", encoding="utf-8") as f:
            updated_config = {"openai_model": "qwen-turbo", "openai_api_key": "test-key"}
            json.dump(updated_config, f)

        # 等待自动重载（最多等待 2 秒）
        max_wait = 2.0
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if config.get("openai_model") == "qwen-turbo":
                break
            time.sleep(0.1)

        # 验证配置已自动重载
        assert config.get("openai_model") == "qwen-turbo"

        # 停止监控
        config.stop_watching()
        assert config.is_watching() is False

        print("✅ 文件变化自动重载测试通过")
    finally:
        config.stop_watching()
        os.unlink(temp_path)


def test_reload_callbacks():
    """测试重载回调函数"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 用于记录回调是否被调用
        callback_called = {"count": 0}

        def test_callback():
            callback_called["count"] += 1

        # 注册回调
        config.register_reload_callback(test_callback)

        # 手动重载，应该触发回调
        config.reload()
        assert callback_called["count"] == 1

        # 再次重载
        config.reload()
        assert callback_called["count"] == 2

        # 取消注册回调
        config.unregister_reload_callback(test_callback)

        # 重载不应该再触发回调
        config.reload()
        assert callback_called["count"] == 2

        print("✅ 重载回调函数测试通过")
    finally:
        os.unlink(temp_path)


def test_multiple_callbacks():
    """测试多个回调函数"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 用于记录回调调用
        results = []

        def callback1():
            results.append("callback1")

        def callback2():
            results.append("callback2")

        def callback3():
            results.append("callback3")

        # 注册多个回调
        config.register_reload_callback(callback1)
        config.register_reload_callback(callback2)
        config.register_reload_callback(callback3)

        # 重载应该触发所有回调
        config.reload()
        assert len(results) == 3
        assert "callback1" in results
        assert "callback2" in results
        assert "callback3" in results

        print("✅ 多个回调函数测试通过")
    finally:
        os.unlink(temp_path)


def test_thread_safety():
    """测试线程安全性"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max", "counter": 0}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)
        errors = []

        def read_config():
            """读取配置的线程"""
            try:
                for _ in range(50):
                    _ = config.get("openai_model")
                    _ = config.get("counter")
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"读取错误: {e}")

        def write_config():
            """写入配置的线程"""
            try:
                for i in range(50):
                    config.set("counter", i)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"写入错误: {e}")

        def reload_config():
            """重载配置的线程"""
            try:
                for _ in range(10):
                    config.reload()
                    time.sleep(0.005)
            except Exception as e:
                errors.append(f"重载错误: {e}")

        # 创建多个线程并发操作
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=read_config))
        for _ in range(2):
            threads.append(threading.Thread(target=write_config))
        threads.append(threading.Thread(target=reload_config))

        # 启动所有线程
        for t in threads:
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证没有错误
        assert len(errors) == 0, f"线程安全测试失败: {errors}"

        print("✅ 线程安全性测试通过")
    finally:
        os.unlink(temp_path)


def test_watch_nonexistent_file():
    """测试监控不存在的文件"""
    config = ConfigManager(config_path="nonexistent_file.json")

    # 尝试启动监控不存在的文件，应该给出警告但不崩溃
    config.start_watching()
    assert config.is_watching() is False

    print("✅ 监控不存在文件测试通过")


def test_stop_watching_when_not_started():
    """测试停止未启动的监控"""
    config = ConfigManager(config_path="nonexistent.json")

    # 停止未启动的监控，应该不会出错
    config.stop_watching()
    assert config.is_watching() is False

    print("✅ 停止未启动监控测试通过")


def test_duplicate_start_watching():
    """测试重复启动监控"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 第一次启动
        config.start_watching()
        assert config.is_watching() is True

        # 第二次启动应该给出警告但不崩溃
        config.start_watching()
        assert config.is_watching() is True

        # 清理
        config.stop_watching()

        print("✅ 重复启动监控测试通过")
    finally:
        config.stop_watching()
        os.unlink(temp_path)


def test_callback_exception_handling():
    """测试回调函数异常处理"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"openai_model": "qwen-max"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 记录正常回调是否被调用
        normal_callback_called = {"called": False}

        def failing_callback():
            raise ValueError("测试异常")

        def normal_callback():
            normal_callback_called["called"] = True

        # 注册一个会抛出异常的回调和一个正常回调
        config.register_reload_callback(failing_callback)
        config.register_reload_callback(normal_callback)

        # 重载不应该因为回调异常而崩溃
        config.reload()

        # 正常回调应该仍然被调用
        assert normal_callback_called["called"] is True

        print("✅ 回调函数异常处理测试通过")
    finally:
        os.unlink(temp_path)


def test_env_reference_syntax():
    """测试 ${ENV_VAR} 语法支持"""
    # 设置环境变量
    os.environ["TEST_API_KEY"] = "secret-key-123"
    os.environ["TEST_MODEL"] = "qwen-max"
    os.environ["TEST_TIMEOUT"] = "60"

    # 创建包含环境变量引用的配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "openai_api_key": "${TEST_API_KEY}",
            "openai_model": "${TEST_MODEL}",
            "api": {"openai": {"timeout": "${TEST_TIMEOUT}"}},
            "description": "Using ${TEST_MODEL} model",
        }
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证环境变量引用被正确解析
        assert config.get("openai_api_key") == "secret-key-123"
        assert config.get("openai_model") == "qwen-max"
        assert config.get("api.openai.timeout") == "60"  # 注意：这里是字符串，因为在配置文件中
        assert config.get("description") == "Using qwen-max model"

        print("✅ ${ENV_VAR} 语法测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["TEST_API_KEY"]
        del os.environ["TEST_MODEL"]
        del os.environ["TEST_TIMEOUT"]


def test_env_reference_with_default():
    """测试 ${ENV_VAR:default} 语法支持"""
    # 只设置部分环境变量
    os.environ["EXISTING_VAR"] = "existing-value"

    # 创建包含默认值的环境变量引用
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "existing_key": "${EXISTING_VAR}",
            "missing_key": "${MISSING_VAR:default-value}",
            "empty_default": "${ANOTHER_MISSING:}",
        }
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证存在的环境变量
        assert config.get("existing_key") == "existing-value"

        # 验证不存在的环境变量使用默认值
        assert config.get("missing_key") == "default-value"

        # 验证空默认值
        assert config.get("empty_default") == ""

        print("✅ ${ENV_VAR:default} 语法测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["EXISTING_VAR"]


def test_env_reference_in_nested_config():
    """测试嵌套配置中的环境变量引用"""
    os.environ["NESTED_API_KEY"] = "nested-key-123"
    os.environ["NESTED_TIMEOUT"] = "90"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "api": {
                "openai": {"key": "${NESTED_API_KEY}", "timeout": "${NESTED_TIMEOUT}", "base_url": "https://api.test.com"}
            },
            "cache": {"enabled": True, "prefix": "cache_${NESTED_API_KEY}"},
        }
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证嵌套配置中的环境变量引用
        assert config.get("api.openai.key") == "nested-key-123"
        assert config.get("api.openai.timeout") == "90"
        assert config.get("api.openai.base_url") == "https://api.test.com"
        assert config.get("cache.prefix") == "cache_nested-key-123"

        print("✅ 嵌套配置环境变量引用测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["NESTED_API_KEY"]
        del os.environ["NESTED_TIMEOUT"]


def test_env_reference_in_list():
    """测试列表中的环境变量引用"""
    os.environ["LIST_ITEM_1"] = "item-one"
    os.environ["LIST_ITEM_2"] = "item-two"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"items": ["${LIST_ITEM_1}", "${LIST_ITEM_2}", "static-item"], "mixed": ["prefix-${LIST_ITEM_1}", "suffix"]}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证列表中的环境变量引用
        items = config.get("items")
        assert items == ["item-one", "item-two", "static-item"]

        mixed = config.get("mixed")
        assert mixed == ["prefix-item-one", "suffix"]

        print("✅ 列表环境变量引用测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["LIST_ITEM_1"]
        del os.environ["LIST_ITEM_2"]


def test_env_reference_missing_no_default():
    """测试缺失环境变量且无默认值的情况"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {"missing_var": "${TOTALLY_MISSING_VAR}", "normal_key": "normal-value"}
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config = ConfigManager(config_path=temp_path)

        # 验证缺失的环境变量保留原始引用
        assert config.get("missing_var") == "${TOTALLY_MISSING_VAR}"
        assert config.get("normal_key") == "normal-value"

        print("✅ 缺失环境变量无默认值测试通过")
    finally:
        os.unlink(temp_path)


def test_env_reference_priority():
    """测试环境变量引用与直接环境变量的优先级"""
    # 设置环境变量
    os.environ["PRIORITY_TEST_KEY"] = "env-direct-value"
    os.environ["PRIORITY_TEST_REF"] = "env-ref-value"

    # 创建配置文件：使用 ${} 引用和直接映射
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "openai_api_key": "${PRIORITY_TEST_REF}",  # 配置文件中使用 ${} 引用
            "openai_model": "qwen-plus",  # 配置文件中的普通值
        }
        json.dump(test_config, f)
        temp_path = f.name

    try:
        # 设置 OPENAI_API_KEY 环境变量（应该覆盖配置文件）
        os.environ["OPENAI_API_KEY"] = "env-direct-value"

        config = ConfigManager(config_path=temp_path)

        # OPENAI_API_KEY 环境变量应该覆盖配置文件中的 ${} 引用
        # 因为环境变量优先级最高
        assert config.get("openai_api_key") == "env-direct-value"

        # OPENAI_MODEL 环境变量未设置，应该使用配置文件中的值
        assert config.get("openai_model") == "qwen-plus"

        print("✅ 环境变量引用优先级测试通过")
    finally:
        os.unlink(temp_path)
        del os.environ["PRIORITY_TEST_KEY"]
        del os.environ["PRIORITY_TEST_REF"]
        del os.environ["OPENAI_API_KEY"]


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 ConfigManager")
    print("=" * 60)

    test_default_config()
    test_json_config_loading()
    test_yaml_config_loading()
    test_environment_variable_override()
    test_priority_order()
    test_comprehensive_priority()
    test_env_value_type_conversion()
    test_config_source_tracking()
    test_nested_env_override()
    test_get_set_methods()
    test_validate()
    test_validate_missing_required_fields()
    test_validate_type_errors()
    test_validate_value_range()
    test_validate_url_format()
    test_validate_enum_values()
    test_get_validation_errors()
    test_manual_reload()
    test_get_all()

    print("\n" + "=" * 60)
    print("开始测试 ${ENV_VAR} 语法支持")
    print("=" * 60)

    test_env_reference_syntax()
    test_env_reference_with_default()
    test_env_reference_in_nested_config()
    test_env_reference_in_list()
    test_env_reference_missing_no_default()
    test_env_reference_priority()

    print("\n" + "=" * 60)
    print("开始测试配置热重载功能")
    print("=" * 60)

    test_auto_reload_on_file_change()
    test_reload_callbacks()
    test_multiple_callbacks()
    test_thread_safety()
    test_watch_nonexistent_file()
    test_stop_watching_when_not_started()
    test_duplicate_start_watching()
    test_callback_exception_handling()

    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
