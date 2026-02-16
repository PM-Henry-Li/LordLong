#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置安全检查器单元测试
"""

import json
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.check_config_security import ConfigSecurityChecker, SecurityIssue


def test_detect_api_key():
    """测试检测 API Key"""
    # 创建临时配置文件
    config_data = {
        "openai_api_key": "sk-1234567890abcdefghijklmnopqrstuvwxyz",
        "safe_key": "${OPENAI_API_KEY}",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        # 创建检查器
        checker = ConfigSecurityChecker(temp_path)
        assert checker.load_config()

        # 执行检查
        issues = checker.check()

        # 验证结果
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "api_key"
        assert "openai_api_key" in issues[0].key_path
        print("✅ 测试通过: 检测 API Key")

    finally:
        Path(temp_path).unlink()


def test_detect_password():
    """测试检测密码"""
    config_data = {
        "database": {
            "password": "mypassword123",
            "safe_password": "${DB_PASSWORD}",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        checker = ConfigSecurityChecker(temp_path)
        assert checker.load_config()

        issues = checker.check()

        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "password"
        assert "database.password" in issues[0].key_path
        print("✅ 测试通过: 检测密码")

    finally:
        Path(temp_path).unlink()


def test_detect_token():
    """测试检测 Token"""
    config_data = {
        "auth": {
            "token": "abc123def456ghi789jkl012mno345pqr678",
            "safe_token": "${AUTH_TOKEN}",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        checker = ConfigSecurityChecker(temp_path)
        assert checker.load_config()

        issues = checker.check()

        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "token"
        print("✅ 测试通过: 检测 Token")

    finally:
        Path(temp_path).unlink()


def test_skip_env_var_references():
    """测试跳过环境变量引用"""
    config_data = {
        "openai_api_key": "${OPENAI_API_KEY}",
        "database_url": "${DATABASE_URL:postgresql://localhost/db}",
        "password": "${PASSWORD}",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        checker = ConfigSecurityChecker(temp_path)
        assert checker.load_config()

        issues = checker.check()

        # 不应该发现任何问题
        assert len(issues) == 0
        print("✅ 测试通过: 跳过环境变量引用")

    finally:
        Path(temp_path).unlink()


def test_generate_fixed_config():
    """测试生成修复后的配置"""
    config_data = {
        "openai_api_key": "sk-1234567890abcdefghijklmnopqrstuvwxyz",
        "database": {"password": "mypassword123"},
        "safe_config": "${SAFE_VAR}",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    try:
        checker = ConfigSecurityChecker(temp_path)
        assert checker.load_config()

        checker.check()
        fixed_config, env_vars = checker.generate_fixed_config()

        # 验证修复后的配置
        assert fixed_config["openai_api_key"] == "${OPENAI_API_KEY}"
        assert fixed_config["database"]["password"] == "${DATABASE_PASSWORD}"
        assert fixed_config["safe_config"] == "${SAFE_VAR}"  # 不应该被修改

        # 验证环境变量
        assert "OPENAI_API_KEY" in env_vars
        assert env_vars["OPENAI_API_KEY"] == "sk-1234567890abcdefghijklmnopqrstuvwxyz"
        assert "DATABASE_PASSWORD" in env_vars
        assert env_vars["DATABASE_PASSWORD"] == "mypassword123"

        print("✅ 测试通过: 生成修复后的配置")

    finally:
        Path(temp_path).unlink()


def test_mask_value():
    """测试值隐藏"""
    checker = ConfigSecurityChecker("dummy.json")

    # 测试长值
    masked = checker._mask_value("sk-1234567890abcdefghijklmnopqrstuvwxyz")
    assert masked == "sk-1...wxyz"

    # 测试短值
    masked = checker._mask_value("short")
    assert masked == "***"

    print("✅ 测试通过: 值隐藏")


def test_generate_env_var_name():
    """测试生成环境变量名称"""
    checker = ConfigSecurityChecker("dummy.json")

    # 测试简单路径
    env_var = checker._generate_env_var_name("openai_api_key")
    assert env_var == "OPENAI_API_KEY"

    # 测试嵌套路径
    env_var = checker._generate_env_var_name("database.password")
    assert env_var == "DATABASE_PASSWORD"

    # 测试多层嵌套
    env_var = checker._generate_env_var_name("logging.elasticsearch.password")
    assert env_var == "LOGGING_ELASTICSEARCH_PASSWORD"

    print("✅ 测试通过: 生成环境变量名称")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("配置安全检查器单元测试")
    print("=" * 70)
    print()

    tests = [
        test_detect_api_key,
        test_detect_password,
        test_detect_token,
        test_skip_env_var_references,
        test_generate_fixed_config,
        test_mask_value,
        test_generate_env_var_name,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试错误: {test.__name__}")
            print(f"   错误: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
