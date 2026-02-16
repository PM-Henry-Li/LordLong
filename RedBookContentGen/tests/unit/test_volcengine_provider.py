#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
火山引擎图片生成服务提供商单元测试

测试 VolcengineImageProvider 类的基本功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.image_providers.volcengine_provider import VolcengineImageProvider
from src.core.config_manager import ConfigManager
from src.core.logger import Logger


def test_volcengine_provider_initialization():
    """测试 VolcengineImageProvider 初始化"""
    print("=" * 60)
    print("测试: VolcengineImageProvider 初始化")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 设置测试配置
    config_manager.set("volcengine.access_key_id", "test_access_key_id")
    config_manager.set("volcengine.secret_access_key", "test_secret_access_key")
    config_manager.set("volcengine.endpoint", "https://visual.volcengineapi.com")
    config_manager.set("volcengine.service", "cv")
    config_manager.set("volcengine.region", "cn-north-1")
    config_manager.set("volcengine.model", "general_v2")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证初始化
    assert provider is not None, "Provider 实例不应为 None"
    assert provider.access_key_id == "test_access_key_id", "AccessKeyID 不匹配"
    assert provider.secret_access_key == "test_secret_access_key", "SecretAccessKey 不匹配"
    assert provider.endpoint == "https://visual.volcengineapi.com", "Endpoint 不匹配"
    assert provider.service == "cv", "Service 不匹配"
    assert provider.region == "cn-north-1", "Region 不匹配"
    assert provider.model == "general_v2", "Model 不匹配"
    assert provider.signer is not None, "Signer 不应为 None"
    
    print("✅ 初始化测试通过")
    print()


def test_volcengine_provider_get_provider_name():
    """测试 get_provider_name() 方法"""
    print("=" * 60)
    print("测试: get_provider_name() 方法")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证提供商名称
    provider_name = provider.get_provider_name()
    assert provider_name == "volcengine", f"提供商名称应为 'volcengine'，实际为 '{provider_name}'"
    
    print(f"✅ 提供商名称: {provider_name}")
    print()


def test_volcengine_provider_without_credentials():
    """测试没有凭证时的初始化"""
    print("=" * 60)
    print("测试: 没有凭证时的初始化")
    print("=" * 60)
    
    # 创建配置管理器（不设置凭证）
    config_manager = ConfigManager()
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证 signer 为 None
    assert provider.signer is None, "没有凭证时 signer 应为 None"
    
    print("✅ 没有凭证时正确处理")
    print()


def test_volcengine_provider_default_values():
    """测试默认配置值"""
    print("=" * 60)
    print("测试: 默认配置值")
    print("=" * 60)
    
    # 创建配置管理器（只设置必需的凭证）
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 验证默认值
    assert provider.endpoint == "https://visual.volcengineapi.com", "默认 endpoint 不正确"
    assert provider.service == "cv", "默认 service 不正确"
    assert provider.region == "cn-north-1", "默认 region 不正确"
    assert provider.model == "general_v2", "默认 model 不正确"
    assert provider.timeout == 180, "默认 timeout 不正确"
    assert provider.max_retries == 3, "默认 max_retries 不正确"
    
    print("✅ 默认配置值正确")
    print()


def test_handle_api_error_timeout():
    """测试 _handle_api_error() 处理超时错误"""
    print("=" * 60)
    print("测试: _handle_api_error() 处理超时错误")
    print("=" * 60)
    
    import requests
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    config_manager.set("volcengine.max_retries", 3)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 测试超时错误（可重试）
    timeout_error = requests.exceptions.Timeout("Connection timeout")
    
    # 第 1 次重试
    should_retry, error_msg = provider._handle_api_error(timeout_error, 0)
    assert should_retry == True, "第 1 次超时应该重试"
    assert error_msg == "网络超时", f"错误消息不正确: {error_msg}"
    
    # 第 2 次重试
    should_retry, error_msg = provider._handle_api_error(timeout_error, 1)
    assert should_retry == True, "第 2 次超时应该重试"
    
    # 第 3 次重试
    should_retry, error_msg = provider._handle_api_error(timeout_error, 2)
    assert should_retry == True, "第 3 次超时应该重试"
    
    # 第 4 次（超过最大重试次数）
    should_retry, error_msg = provider._handle_api_error(timeout_error, 3)
    assert should_retry == False, "超过最大重试次数不应该重试"
    
    print("✅ 超时错误处理正确")
    print()


def test_handle_api_error_connection():
    """测试 _handle_api_error() 处理连接错误"""
    print("=" * 60)
    print("测试: _handle_api_error() 处理连接错误")
    print("=" * 60)
    
    import requests
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    config_manager.set("volcengine.max_retries", 3)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 测试连接错误（可重试）
    connection_error = requests.exceptions.ConnectionError("Connection refused")
    
    # 第 1 次重试
    should_retry, error_msg = provider._handle_api_error(connection_error, 0)
    assert should_retry == True, "第 1 次连接错误应该重试"
    assert error_msg == "连接失败", f"错误消息不正确: {error_msg}"
    
    # 第 3 次重试
    should_retry, error_msg = provider._handle_api_error(connection_error, 2)
    assert should_retry == True, "第 3 次连接错误应该重试"
    
    # 第 4 次（超过最大重试次数）
    should_retry, error_msg = provider._handle_api_error(connection_error, 3)
    assert should_retry == False, "超过最大重试次数不应该重试"
    
    print("✅ 连接错误处理正确")
    print()


def test_handle_api_error_http_4xx():
    """测试 _handle_api_error() 处理 4xx 客户端错误"""
    print("=" * 60)
    print("测试: _handle_api_error() 处理 4xx 客户端错误")
    print("=" * 60)
    
    import requests
    from unittest.mock import Mock
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    config_manager.set("volcengine.max_retries", 3)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 测试 400 错误（不可重试）
    response_400 = Mock()
    response_400.status_code = 400
    http_error_400 = requests.exceptions.HTTPError(response=response_400)
    
    should_retry, error_msg = provider._handle_api_error(http_error_400, 0)
    assert should_retry == False, "400 错误不应该重试"
    assert "客户端错误: 400" in error_msg, f"错误消息不正确: {error_msg}"
    
    # 测试 401 错误（不可重试）
    response_401 = Mock()
    response_401.status_code = 401
    http_error_401 = requests.exceptions.HTTPError(response=response_401)
    
    should_retry, error_msg = provider._handle_api_error(http_error_401, 0)
    assert should_retry == False, "401 错误不应该重试"
    
    # 测试 404 错误（不可重试）
    response_404 = Mock()
    response_404.status_code = 404
    http_error_404 = requests.exceptions.HTTPError(response=response_404)
    
    should_retry, error_msg = provider._handle_api_error(http_error_404, 0)
    assert should_retry == False, "404 错误不应该重试"
    
    print("✅ 4xx 客户端错误处理正确")
    print()


def test_handle_api_error_http_429():
    """测试 _handle_api_error() 处理 429 速率限制错误"""
    print("=" * 60)
    print("测试: _handle_api_error() 处理 429 速率限制错误")
    print("=" * 60)
    
    import requests
    from unittest.mock import Mock
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    config_manager.set("volcengine.max_retries", 3)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 测试 429 错误（可重试）
    response_429 = Mock()
    response_429.status_code = 429
    http_error_429 = requests.exceptions.HTTPError(response=response_429)
    
    # 第 1 次重试
    should_retry, error_msg = provider._handle_api_error(http_error_429, 0)
    assert should_retry == True, "429 错误应该重试"
    assert error_msg == "速率限制", f"错误消息不正确: {error_msg}"
    
    # 第 3 次重试
    should_retry, error_msg = provider._handle_api_error(http_error_429, 2)
    assert should_retry == True, "第 3 次 429 错误应该重试"
    
    # 第 4 次（超过最大重试次数）
    should_retry, error_msg = provider._handle_api_error(http_error_429, 3)
    assert should_retry == False, "超过最大重试次数不应该重试"
    
    print("✅ 429 速率限制错误处理正确")
    print()


def test_handle_api_error_http_5xx():
    """测试 _handle_api_error() 处理 5xx 服务器错误"""
    print("=" * 60)
    print("测试: _handle_api_error() 处理 5xx 服务器错误")
    print("=" * 60)
    
    import requests
    from unittest.mock import Mock
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    config_manager.set("volcengine.max_retries", 3)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 测试 500 错误（可重试）
    response_500 = Mock()
    response_500.status_code = 500
    http_error_500 = requests.exceptions.HTTPError(response=response_500)
    
    # 第 1 次重试
    should_retry, error_msg = provider._handle_api_error(http_error_500, 0)
    assert should_retry == True, "500 错误应该重试"
    assert "服务器错误: 500" in error_msg, f"错误消息不正确: {error_msg}"
    
    # 测试 502 错误（可重试）
    response_502 = Mock()
    response_502.status_code = 502
    http_error_502 = requests.exceptions.HTTPError(response=response_502)
    
    should_retry, error_msg = provider._handle_api_error(http_error_502, 1)
    assert should_retry == True, "502 错误应该重试"
    
    # 测试 503 错误（可重试）
    response_503 = Mock()
    response_503.status_code = 503
    http_error_503 = requests.exceptions.HTTPError(response=response_503)
    
    should_retry, error_msg = provider._handle_api_error(http_error_503, 2)
    assert should_retry == True, "503 错误应该重试"
    
    # 第 4 次（超过最大重试次数）
    should_retry, error_msg = provider._handle_api_error(http_error_500, 3)
    assert should_retry == False, "超过最大重试次数不应该重试"
    
    print("✅ 5xx 服务器错误处理正确")
    print()


def test_handle_api_error_unknown():
    """测试 _handle_api_error() 处理未知错误"""
    print("=" * 60)
    print("测试: _handle_api_error() 处理未知错误")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_key")
    config_manager.set("volcengine.secret_access_key", "test_secret")
    config_manager.set("volcengine.max_retries", 3)
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 创建 VolcengineImageProvider 实例
    provider = VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )
    
    # 测试未知错误（不可重试）
    unknown_error = Exception("Unknown error")
    
    should_retry, error_msg = provider._handle_api_error(unknown_error, 0)
    assert should_retry == False, "未知错误不应该重试"
    assert "未知错误" in error_msg, f"错误消息不正确: {error_msg}"
    
    print("✅ 未知错误处理正确")
    print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始运行 VolcengineImageProvider 单元测试")
    print("=" * 60 + "\n")
    
    try:
        test_volcengine_provider_initialization()
        test_volcengine_provider_get_provider_name()
        test_volcengine_provider_without_credentials()
        test_volcengine_provider_default_values()
        test_handle_api_error_timeout()
        test_handle_api_error_connection()
        test_handle_api_error_http_4xx()
        test_handle_api_error_http_429()
        test_handle_api_error_http_5xx()
        test_handle_api_error_unknown()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
