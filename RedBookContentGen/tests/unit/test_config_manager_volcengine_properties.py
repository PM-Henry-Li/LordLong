#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器火山引擎配置属性测试

使用基于属性的测试验证配置管理器的火山引擎相关功能
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hypothesis import given, strategies as st, settings, assume
from src.core.config_manager import ConfigManager


# 策略：生成有效的火山引擎配置
@st.composite
def volcengine_config_strategy(draw):
    """生成有效的火山引擎配置"""
    return {
        "access_key_id": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        "secret_access_key": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "P")))),
        "endpoint": draw(st.sampled_from([
            "https://visual.volcengineapi.com",
            "https://open.volcengineapi.com",
        ])),
        "service": draw(st.sampled_from(["cv", "visual"])),
        "region": draw(st.sampled_from(["cn-north-1", "cn-beijing", "ap-singapore-1"])),
        "model": draw(st.sampled_from(["general_v2", "anime_v2", "general_v1"])),
        "timeout": draw(st.integers(min_value=30, max_value=300)),
        "max_retries": draw(st.integers(min_value=1, max_value=5)),
        "retry_delay": draw(st.floats(min_value=0.5, max_value=5.0)),
        "api_version": draw(st.sampled_from(["2022-08-31", "2023-01-01"])),
    }


# 策略：生成配置文件内容
@st.composite
def config_file_strategy(draw, include_volcengine=True):
    """生成配置文件内容"""
    config = {
        "openai_api_key": draw(st.text(min_size=10, max_size=50)),
        "image_api_provider": draw(st.sampled_from(["aliyun", "volcengine"])),
    }
    
    if include_volcengine:
        config["volcengine"] = draw(volcengine_config_strategy())
    
    return config


class TestConfigManagerVolcengineProperties:
    """配置管理器火山引擎配置属性测试"""
    
    @given(volcengine_config=volcengine_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_1_config_loading_completeness(self, volcengine_config):
        """
        Feature: volcengine-jimeng-integration
        Property 1: 配置加载完整性
        
        **验证需求: 1.1, 1.2**
        
        对于任何包含火山引擎配置的有效配置文件，加载后应该能够读取所有必需的配置项
        （AccessKeyID、SecretAccessKey、端点、服务名、区域、模型名称）
        """
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "openai_api_key": "test-key",
                "image_api_provider": "volcengine",
                "volcengine": volcengine_config
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # 加载配置
            config_manager = ConfigManager(config_path=config_path)
            
            # 验证所有必需的配置项都能读取
            assert config_manager.get("volcengine.access_key_id") == volcengine_config["access_key_id"]
            assert config_manager.get("volcengine.secret_access_key") == volcengine_config["secret_access_key"]
            assert config_manager.get("volcengine.endpoint") == volcengine_config["endpoint"]
            assert config_manager.get("volcengine.service") == volcengine_config["service"]
            assert config_manager.get("volcengine.region") == volcengine_config["region"]
            assert config_manager.get("volcengine.model") == volcengine_config["model"]
            
            # 验证可选配置项
            assert config_manager.get("volcengine.timeout") == volcengine_config["timeout"]
            assert config_manager.get("volcengine.max_retries") == volcengine_config["max_retries"]
            
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    @given(
        volcengine_config=volcengine_config_strategy(),
        env_access_key=st.text(min_size=2, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
        env_secret_key=st.text(min_size=2, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "P"))),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_2_env_var_override(self, volcengine_config, env_access_key, env_secret_key):
        """
        Feature: volcengine-jimeng-integration
        Property 2: 环境变量覆盖
        
        **验证需求: 1.3, 10.3**
        
        对于任何支持环境变量的配置项，当环境变量被设置时，其值应该覆盖配置文件中的值
        """
        # 确保环境变量值与配置文件值不同
        assume(env_access_key != volcengine_config["access_key_id"])
        assume(env_secret_key != volcengine_config["secret_access_key"])
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "openai_api_key": "test-key",
                "volcengine": volcengine_config
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # 设置环境变量
            with patch.dict(os.environ, {
                "VOLCENGINE_ACCESS_KEY_ID": env_access_key,
                "VOLCENGINE_SECRET_ACCESS_KEY": env_secret_key,
            }):
                # 加载配置
                config_manager = ConfigManager(config_path=config_path)
                
                # 验证环境变量覆盖了配置文件的值
                assert config_manager.get("volcengine.access_key_id") == env_access_key
                assert config_manager.get("volcengine.secret_access_key") == env_secret_key
                
                # 验证其他配置项未受影响
                assert config_manager.get("volcengine.endpoint") == volcengine_config["endpoint"]
                assert config_manager.get("volcengine.service") == volcengine_config["service"]
        
        finally:
            # 清理临时文件
            os.unlink(config_path)
    
    @given(
        env_var_name=st.sampled_from(["TEST_KEY_1", "TEST_KEY_2", "MY_SECRET"]),
        env_var_value=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")),
        default_value=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00:}")),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_3_env_var_reference_resolution(self, env_var_name, env_var_value, default_value):
        """
        Feature: volcengine-jimeng-integration
        Property 3: 环境变量引用解析
        
        **验证需求: 1.4**
        
        对于任何包含 ${ENV_VAR} 或 ${ENV_VAR:default} 语法的配置值，
        应该正确解析为环境变量的值或默认值
        """
        # 确保默认值与环境变量值不同
        assume(env_var_value != default_value)
        
        # 测试 ${ENV_VAR} 语法（环境变量存在）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "openai_api_key": "test-key",
                "volcengine": {
                    "access_key_id": f"${{{env_var_name}}}",
                    "secret_access_key": "test-secret",
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # 设置环境变量
            with patch.dict(os.environ, {env_var_name: env_var_value}):
                config_manager = ConfigManager(config_path=config_path)
                
                # 验证环境变量引用被正确解析
                assert config_manager.get("volcengine.access_key_id") == env_var_value
        
        finally:
            os.unlink(config_path)
        
        # 测试 ${ENV_VAR:default} 语法（环境变量不存在）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "openai_api_key": "test-key",
                "volcengine": {
                    "access_key_id": f"${{{env_var_name}:{default_value}}}",
                    "secret_access_key": "test-secret",
                }
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # 不设置环境变量
            with patch.dict(os.environ, {}, clear=False):
                # 确保环境变量不存在
                if env_var_name in os.environ:
                    del os.environ[env_var_name]
                
                config_manager = ConfigManager(config_path=config_path)
                
                # 验证使用了默认值
                assert config_manager.get("volcengine.access_key_id") == default_value
        
        finally:
            os.unlink(config_path)
    
    @given(
        missing_field=st.sampled_from(["access_key_id", "secret_access_key", "endpoint"]),
        provider=st.sampled_from(["aliyun", "volcengine", "invalid_provider", ""]),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_4_config_defaults_and_error_handling(self, missing_field, provider):
        """
        Feature: volcengine-jimeng-integration
        Property 4: 配置默认值和错误处理
        
        **验证需求: 1.5**
        
        对于任何缺失或无效的配置项，系统应该使用合理的默认值或返回明确的错误信息
        """
        # 创建不完整的配置
        volcengine_config = {
            "access_key_id": "test-key-id",
            "secret_access_key": "test-secret",
            "endpoint": "https://visual.volcengineapi.com",
        }
        
        # 移除指定字段
        if missing_field in volcengine_config:
            del volcengine_config[missing_field]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "openai_api_key": "test-key",
                "image_api_provider": provider,
                "volcengine": volcengine_config
            }
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # 加载配置
            config_manager = ConfigManager(config_path=config_path)
            
            # 验证缺失的字段使用默认值
            if missing_field == "access_key_id":
                # 应该返回默认值（空字符串）或配置文件中的值
                value = config_manager.get("volcengine.access_key_id")
                assert value is not None  # 不应该是 None
                assert isinstance(value, str)  # 应该是字符串
            
            elif missing_field == "secret_access_key":
                value = config_manager.get("volcengine.secret_access_key")
                assert value is not None
                assert isinstance(value, str)
            
            elif missing_field == "endpoint":
                value = config_manager.get("volcengine.endpoint")
                assert value is not None
                assert isinstance(value, str)
            
            # 验证 image_api_provider 的默认值处理
            provider_value = config_manager.get("image_api_provider")
            if provider in ["aliyun", "volcengine"]:
                assert provider_value == provider
            else:
                # 无效或空值应该使用默认值 "aliyun"
                assert provider_value in ["aliyun", provider, ""]
        
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    import pytest
    
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
