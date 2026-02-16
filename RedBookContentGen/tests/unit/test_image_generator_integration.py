#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ImageGenerator 集成测试

测试 ImageGenerator 与图片生成服务提供商的集成。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.image_generator import ImageGenerator
from src.core.config_manager import ConfigManager
from src.image_providers.aliyun_provider import AliyunImageProvider
from src.image_providers.volcengine_provider import VolcengineImageProvider


class TestImageGeneratorIntegration(unittest.TestCase):
    """ImageGenerator 集成测试"""

    def setUp(self):
        """测试前准备"""
        # 创建测试配置
        self.test_config = {
            "openai_api_key": "test-key-12345",
            "image_model": "wanx-v1",
            "image_api_provider": "aliyun",
            "volcengine": {
                "access_key_id": "test-volcengine-key",
                "secret_access_key": "test-volcengine-secret",
                "endpoint": "https://visual.volcengineapi.com",
                "service": "cv",
                "region": "cn-north-1",
                "model": "general_v2"
            },
            "cache": {
                "enabled": False
            },
            "rate_limit": {
                "image": {
                    "enable_rate_limit": False
                }
            }
        }

    def _create_mock_config_manager(self, config):
        """创建 mock ConfigManager"""
        mock_cm = Mock(spec=ConfigManager)
        mock_cm.get = Mock(side_effect=lambda key, default=None: self._get_nested_value(config, key, default))
        return mock_cm

    def _get_nested_value(self, config, key, default=None):
        """获取嵌套配置值"""
        keys = key.split('.')
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @patch('src.core.logger.Logger.initialize')
    def test_factory_method_returns_aliyun_provider(self, mock_logger):
        """
        测试工厂方法返回阿里云提供商
        
        **属性 9: 提供商选择正确性**
        对于任何配置的 image_api_provider 值，系统应该选择对应的图片生成服务提供商实现
        """
        # 配置返回阿里云
        self.test_config["image_api_provider"] = "aliyun"
        mock_config = self._create_mock_config_manager(self.test_config)
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 获取提供商
        provider = generator._get_image_provider()
        
        # 验证返回的是阿里云提供商
        self.assertIsInstance(provider, AliyunImageProvider)
        self.assertEqual(provider.get_provider_name(), "aliyun")

    @patch('src.core.logger.Logger.initialize')
    def test_factory_method_returns_volcengine_provider(self, mock_logger):
        """
        测试工厂方法返回火山引擎提供商
        
        **属性 9: 提供商选择正确性**
        对于任何配置的 image_api_provider 值，系统应该选择对应的图片生成服务提供商实现
        """
        # 配置返回火山引擎
        self.test_config["image_api_provider"] = "volcengine"
        mock_config = self._create_mock_config_manager(self.test_config)
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 获取提供商
        provider = generator._get_image_provider()
        
        # 验证返回的是火山引擎提供商
        self.assertIsInstance(provider, VolcengineImageProvider)
        self.assertEqual(provider.get_provider_name(), "volcengine")

    @patch('src.core.logger.Logger.initialize')
    def test_factory_method_defaults_to_aliyun(self, mock_logger):
        """
        测试工厂方法默认返回阿里云提供商
        
        **属性 14: 默认提供商回退**
        对于任何未设置、为空、或无效的 image_api_provider 配置，
        系统应该使用默认的阿里云通义万相
        """
        # 测试未设置的情况
        test_cases = [
            {},  # 未设置
            {"image_api_provider": ""},  # 空字符串
            {"image_api_provider": None},  # None
            {"image_api_provider": "invalid_provider"},  # 无效值
        ]
        
        for test_config in test_cases:
            # 合并基础配置
            config = {**self.test_config, **test_config}
            mock_config = self._create_mock_config_manager(config)
            
            generator = ImageGenerator(config_manager=mock_config)
            
            # 获取提供商
            provider = generator._get_image_provider()
            
            # 验证返回的是阿里云提供商（默认值）
            self.assertIsInstance(provider, AliyunImageProvider)
            self.assertEqual(provider.get_provider_name(), "aliyun")

    @patch('src.core.logger.Logger.initialize')
    @patch('src.image_providers.aliyun_provider.AliyunImageProvider.generate')
    def test_generate_single_image_uses_provider(self, mock_generate, mock_logger):
        """
        测试 generate_single_image 使用提供商接口
        
        **属性 26: API 接口兼容性**
        对于任何现有的 ImageGenerator 调用方式，系统应该保持原有行为不变，
        接口签名应该保持不变
        """
        # 配置
        mock_config = self._create_mock_config_manager(self.test_config)
        mock_generate.return_value = "https://example.com/image.jpg"
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 调用 generate_single_image
        result = generator.generate_single_image("test prompt", "1024*1365")
        
        # 验证调用了提供商的 generate 方法
        mock_generate.assert_called_once_with("test prompt", "1024*1365")
        self.assertEqual(result, "https://example.com/image.jpg")

    @patch('src.core.logger.Logger.initialize')
    @patch('src.image_providers.volcengine_provider.VolcengineImageProvider.generate')
    def test_generate_image_async_uses_provider(self, mock_generate, mock_logger):
        """
        测试 generate_image_async 使用提供商接口
        
        **属性 26: API 接口兼容性**
        对于任何现有的 ImageGenerator 调用方式，系统应该保持原有行为不变，
        接口签名应该保持不变
        """
        # 配置使用火山引擎
        self.test_config["image_api_provider"] = "volcengine"
        mock_config = self._create_mock_config_manager(self.test_config)
        mock_generate.return_value = "https://example.com/image.jpg"
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 调用 generate_image_async
        result = generator.generate_image_async("test prompt", 1, is_cover=True)
        
        # 验证调用了提供商的 generate 方法
        mock_generate.assert_called_once_with("test prompt", "1024*1365", is_cover=True)
        self.assertEqual(result, "https://example.com/image.jpg")

    @patch('src.core.logger.Logger.initialize')
    def test_provider_receives_config_manager(self, mock_logger):
        """
        测试提供商接收到 ConfigManager 实例
        
        **属性 27: 配置结构兼容性**
        对于任何现有的配置文件，系统应该能够正常加载和使用，
        新配置项应该是可选的
        """
        mock_config = self._create_mock_config_manager(self.test_config)
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 获取提供商
        provider = generator._get_image_provider()
        
        # 验证提供商有 config_manager 属性
        self.assertIsNotNone(provider.config_manager)

    @patch('src.core.logger.Logger.initialize')
    def test_provider_receives_logger(self, mock_logger):
        """测试提供商接收到 Logger 实例"""
        mock_config = self._create_mock_config_manager(self.test_config)
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 获取提供商
        provider = generator._get_image_provider()
        
        # 验证提供商有 logger 属性
        self.assertIsNotNone(provider.logger)

    @patch('src.core.logger.Logger.initialize')
    def test_provider_receives_rate_limiter(self, mock_logger):
        """测试提供商接收到 RateLimiter 实例（如果启用）"""
        # 启用速率限制
        self.test_config["rate_limit"]["image"]["enable_rate_limit"] = True
        self.test_config["rate_limit"]["image"]["requests_per_minute"] = 10
        mock_config = self._create_mock_config_manager(self.test_config)
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 获取提供商
        provider = generator._get_image_provider()
        
        # 验证提供商有 rate_limiter 属性
        self.assertIsNotNone(provider.rate_limiter)

    @patch('src.core.logger.Logger.initialize')
    def test_provider_receives_cache(self, mock_logger):
        """测试提供商接收到 CacheManager 实例（如果启用）"""
        # 启用缓存
        self.test_config["cache"]["enabled"] = True
        self.test_config["cache"]["ttl"] = 86400
        self.test_config["cache"]["max_size"] = 1000
        mock_config = self._create_mock_config_manager(self.test_config)
        
        generator = ImageGenerator(config_manager=mock_config)
        
        # 获取提供商
        provider = generator._get_image_provider()
        
        # 验证提供商有 cache 属性
        self.assertIsNotNone(provider.cache)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestImageGeneratorIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
