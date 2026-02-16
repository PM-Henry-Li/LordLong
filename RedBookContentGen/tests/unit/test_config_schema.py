#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模式测试模块

测试 Pydantic 配置模式的验证功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from pydantic import ValidationError
from src.core.config_schema import OpenAIAPIConfig, ImageAPIConfig, APIConfig, CacheConfig, LoggingConfig


class TestOpenAIAPIConfig:
    """测试 OpenAI API 配置模式"""

    def test_valid_config(self):
        """测试有效配置"""
        config = OpenAIAPIConfig(
            openai_api_key="sk-test-key-123",
            openai_base_url="https://api.openai.com/v1",
            openai_model="gpt-4",
            timeout=30,
            max_retries=3,
        )

        assert config.key == "sk-test-key-123"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_default_values(self):
        """测试默认值"""
        config = OpenAIAPIConfig(openai_api_key="sk-test")

        assert config.key == "sk-test"
        assert config.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert config.model == "qwen-plus"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_missing_api_key(self):
        """测试缺少 API Key"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAPIConfig()

        errors = exc_info.value.errors()
        # 检查错误中包含 key 或 openai_api_key 字段
        assert any("key" in str(error["loc"]) or "openai_api_key" in str(error["loc"]) for error in errors)

    def test_empty_api_key(self):
        """测试空 API Key"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAPIConfig(openai_api_key="")

        errors = exc_info.value.errors()
        assert any("key" in str(error["loc"]) for error in errors)

    def test_invalid_base_url(self):
        """测试无效的 base_url"""
        with pytest.raises(ValidationError) as exc_info:
            OpenAIAPIConfig(openai_api_key="sk-test", openai_base_url="invalid-url")

        errors = exc_info.value.errors()
        assert any("base_url" in str(error["loc"]) for error in errors)

    def test_base_url_trailing_slash(self):
        """测试 base_url 末尾斜杠自动移除"""
        config = OpenAIAPIConfig(openai_api_key="sk-test", openai_base_url="https://api.openai.com/v1/")

        assert config.base_url == "https://api.openai.com/v1"

    def test_invalid_timeout(self):
        """测试无效的超时时间"""
        # 超时时间 <= 0
        with pytest.raises(ValidationError):
            OpenAIAPIConfig(openai_api_key="sk-test", timeout=0)

        # 超时时间过大
        with pytest.raises(ValidationError):
            OpenAIAPIConfig(openai_api_key="sk-test", timeout=400)

    def test_invalid_max_retries(self):
        """测试无效的最大重试次数"""
        # 负数
        with pytest.raises(ValidationError):
            OpenAIAPIConfig(openai_api_key="sk-test", max_retries=-1)

        # 过大
        with pytest.raises(ValidationError):
            OpenAIAPIConfig(openai_api_key="sk-test", max_retries=20)

    def test_empty_model_name(self):
        """测试空模型名称"""
        with pytest.raises(ValidationError):
            OpenAIAPIConfig(openai_api_key="sk-test", openai_model="   ")


class TestImageAPIConfig:
    """测试图片生成 API 配置模式"""

    def test_valid_config(self):
        """测试有效配置"""
        config = ImageAPIConfig(
            image_model="wan2.2-t2i-flash",
            size="1024*1365",
            timeout=180,
            image_generation_mode="template",
            template_style="retro_chinese",
        )

        assert config.model == "wan2.2-t2i-flash"
        assert config.size == "1024*1365"
        assert config.timeout == 180
        assert config.generation_mode == "template"
        assert config.template_style == "retro_chinese"

    def test_default_values(self):
        """测试默认值"""
        config = ImageAPIConfig()

        assert config.model == "wan2.2-t2i-flash"
        assert config.size == "1024*1365"
        assert config.timeout == 180
        assert config.generation_mode == "template"
        assert config.template_style == "retro_chinese"

    def test_invalid_size_format(self):
        """测试无效的图片尺寸格式"""
        # 缺少分隔符
        with pytest.raises(ValidationError):
            ImageAPIConfig(size="1024x1365")

        # 非数字
        with pytest.raises(ValidationError):
            ImageAPIConfig(size="abc*def")

        # 负数
        with pytest.raises(ValidationError):
            ImageAPIConfig(size="-1024*1365")

        # 过大
        with pytest.raises(ValidationError):
            ImageAPIConfig(size="5000*5000")

    def test_valid_size_formats(self):
        """测试有效的图片尺寸格式"""
        valid_sizes = ["512*512", "1024*768", "2048*2048", "1920*1080"]

        for size in valid_sizes:
            config = ImageAPIConfig(size=size)
            assert config.size == size

    def test_invalid_timeout(self):
        """测试无效的超时时间"""
        with pytest.raises(ValidationError):
            ImageAPIConfig(timeout=0)

        with pytest.raises(ValidationError):
            ImageAPIConfig(timeout=700)

    def test_invalid_generation_mode(self):
        """测试无效的生成模式"""
        with pytest.raises(ValidationError):
            ImageAPIConfig(image_generation_mode="invalid_mode")

    def test_valid_generation_modes(self):
        """测试有效的生成模式"""
        for mode in ["template", "api"]:
            config = ImageAPIConfig(image_generation_mode=mode)
            assert config.generation_mode == mode

    def test_invalid_template_style(self):
        """测试无效的模板风格"""
        with pytest.raises(ValidationError):
            ImageAPIConfig(template_style="invalid_style")

    def test_valid_template_styles(self):
        """测试有效的模板风格"""
        valid_styles = ["retro_chinese", "modern_minimal", "vintage_film", "warm_memory", "ink_wash"]

        for style in valid_styles:
            config = ImageAPIConfig(template_style=style)
            assert config.template_style == style

    def test_template_mode_requires_style(self):
        """测试 template 模式需要指定风格"""
        # template 模式下，如果 template_style 为 None，应该触发验证错误
        with pytest.raises(ValidationError) as exc_info:
            ImageAPIConfig(image_generation_mode="template", template_style=None)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_api_mode_without_style(self):
        """测试 api 模式可以不指定风格"""
        config = ImageAPIConfig(image_generation_mode="api", template_style=None)
        assert config.generation_mode == "api"
        assert config.template_style is None


class TestCacheConfig:
    """测试缓存配置模式"""

    def test_valid_config(self):
        """测试有效配置"""
        config = CacheConfig(
            enabled=True,
            ttl=7200,
            max_size="2GB",
            eviction_policy="lru",
            content_cache_enabled=True,
            image_cache_enabled=True,
            cache_dir="output/cache",
        )

        assert config.enabled is True
        assert config.ttl == 7200
        assert config.max_size == "2GB"
        assert config.eviction_policy == "lru"
        assert config.content_cache_enabled is True
        assert config.image_cache_enabled is True
        assert config.cache_dir == "output/cache"

    def test_default_values(self):
        """测试默认值"""
        config = CacheConfig()

        assert config.enabled is True
        assert config.ttl == 3600
        assert config.max_size == "1GB"
        assert config.eviction_policy == "lru"
        assert config.content_cache_enabled is True
        assert config.image_cache_enabled is True
        assert config.cache_dir == "cache"

    def test_disabled_cache(self):
        """测试禁用缓存"""
        config = CacheConfig(enabled=False)

        assert config.enabled is False

    def test_zero_ttl(self):
        """测试 TTL 为 0（永不过期）"""
        config = CacheConfig(ttl=0)

        assert config.ttl == 0

    def test_invalid_ttl(self):
        """测试无效的 TTL"""
        # 负数
        with pytest.raises(ValidationError):
            CacheConfig(ttl=-1)

        # 超过 7 天
        with pytest.raises(ValidationError):
            CacheConfig(ttl=86400 * 8)

    def test_valid_max_sizes(self):
        """测试有效的缓存大小格式"""
        valid_sizes = ["1MB", "500MB", "1.5GB", "2GB", "100GB"]

        for size in valid_sizes:
            config = CacheConfig(max_size=size)
            assert config.max_size == size

    def test_invalid_max_size_format(self):
        """测试无效的缓存大小格式"""
        invalid_sizes = [
            "1gb",  # 小写单位
            "1G",  # 错误单位
            "1TB",  # 不支持的单位
            "abc",  # 非数字
            "1 GB",  # 包含空格
            "GB1",  # 单位在前
        ]

        for size in invalid_sizes:
            with pytest.raises(ValidationError):
                CacheConfig(max_size=size)

    def test_max_size_too_small(self):
        """测试缓存大小过小"""
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(max_size="500KB")

        errors = exc_info.value.errors()
        assert any("max_size" in str(error["loc"]) for error in errors)

    def test_max_size_too_large(self):
        """测试缓存大小过大"""
        with pytest.raises(ValidationError) as exc_info:
            CacheConfig(max_size="101GB")

        errors = exc_info.value.errors()
        assert any("max_size" in str(error["loc"]) for error in errors)

    def test_valid_eviction_policies(self):
        """测试有效的淘汰策略"""
        valid_policies = ["lru", "lfu", "fifo"]

        for policy in valid_policies:
            config = CacheConfig(eviction_policy=policy)
            assert config.eviction_policy == policy

    def test_invalid_eviction_policy(self):
        """测试无效的淘汰策略"""
        with pytest.raises(ValidationError):
            CacheConfig(eviction_policy="invalid_policy")

    def test_partial_cache_disable(self):
        """测试部分禁用缓存"""
        # 只禁用内容缓存
        config1 = CacheConfig(enabled=True, content_cache_enabled=False, image_cache_enabled=True)
        assert config1.content_cache_enabled is False
        assert config1.image_cache_enabled is True

        # 只禁用图片缓存
        config2 = CacheConfig(enabled=True, content_cache_enabled=True, image_cache_enabled=False)
        assert config2.content_cache_enabled is True
        assert config2.image_cache_enabled is False

    def test_empty_cache_dir(self):
        """测试空缓存目录"""
        with pytest.raises(ValidationError):
            CacheConfig(cache_dir="")

    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "enabled": True,
            "ttl": 1800,
            "max_size": "500MB",
            "eviction_policy": "lfu",
            "content_cache_enabled": True,
            "image_cache_enabled": False,
            "cache_dir": "custom/cache",
        }

        config = CacheConfig(**config_dict)

        assert config.enabled is True
        assert config.ttl == 1800
        assert config.max_size == "500MB"
        assert config.eviction_policy == "lfu"
        assert config.content_cache_enabled is True
        assert config.image_cache_enabled is False
        assert config.cache_dir == "custom/cache"

    def test_to_dict(self):
        """测试转换为字典"""
        config = CacheConfig(enabled=True, ttl=7200, max_size="2GB")

        config_dict = config.model_dump()

        assert config_dict["enabled"] is True
        assert config_dict["ttl"] == 7200
        assert config_dict["max_size"] == "2GB"


class TestAPIConfig:
    """测试 API 配置总模式"""

    def test_valid_config(self):
        """测试有效的完整配置"""
        config = APIConfig(openai=OpenAIAPIConfig(openai_api_key="sk-test"), image=ImageAPIConfig())

        assert config.openai.key == "sk-test"
        assert config.image.model == "wan2.2-t2i-flash"

    def test_nested_validation(self):
        """测试嵌套验证"""
        # OpenAI 配置无效
        with pytest.raises(ValidationError):
            APIConfig(openai=OpenAIAPIConfig(openai_api_key="sk-test", timeout=-1), image=ImageAPIConfig())

        # Image 配置无效
        with pytest.raises(ValidationError):
            APIConfig(openai=OpenAIAPIConfig(openai_api_key="sk-test"), image=ImageAPIConfig(size="invalid"))

    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "openai": {"openai_api_key": "sk-test-123", "openai_model": "qwen-max", "timeout": 60},
            "image": {"image_model": "wan2.2-t2i-flash", "size": "2048*2048", "image_generation_mode": "api"},
        }

        config = APIConfig(**config_dict)

        assert config.openai.key == "sk-test-123"
        assert config.openai.model == "qwen-max"
        assert config.openai.timeout == 60
        assert config.image.model == "wan2.2-t2i-flash"
        assert config.image.size == "2048*2048"
        assert config.image.generation_mode == "api"

    def test_to_dict(self):
        """测试转换为字典"""
        config = APIConfig(openai=OpenAIAPIConfig(openai_api_key="sk-test"), image=ImageAPIConfig())

        config_dict = config.model_dump()

        assert "openai" in config_dict
        assert "image" in config_dict
        assert config_dict["openai"]["key"] == "sk-test"
        assert config_dict["image"]["model"] == "wan2.2-t2i-flash"


class TestLoggingConfig:
    """测试日志配置模式"""

    def test_valid_config(self):
        """测试有效配置"""
        config = LoggingConfig(
            level="DEBUG",
            format="json",
            file="logs/test.log",
            max_bytes=20971520,  # 20MB
            backup_count=10,
            console_output=True,
            date_format="%Y-%m-%d %H:%M:%S",
            log_dir="logs",
            enable_rotation=True,
        )

        assert config.level == "DEBUG"
        assert config.format == "json"
        assert config.file == "logs/test.log"
        assert config.max_bytes == 20971520
        assert config.backup_count == 10
        assert config.console_output is True
        assert config.date_format == "%Y-%m-%d %H:%M:%S"
        assert config.log_dir == "logs"
        assert config.enable_rotation is True

    def test_default_values(self):
        """测试默认值"""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "json"
        assert config.file == "logs/app.log"
        assert config.max_bytes == 10485760  # 10MB
        assert config.backup_count == 5
        assert config.console_output is True
        assert config.date_format == "%Y-%m-%d %H:%M:%S"
        assert config.log_dir == "logs"
        assert config.enable_rotation is True

    def test_valid_log_levels(self):
        """测试有效的日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = LoggingConfig(level=level)
            assert config.level == level

    def test_invalid_log_level(self):
        """测试无效的日志级别"""
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID")

        with pytest.raises(ValidationError):
            LoggingConfig(level="debug")  # 必须大写

    def test_valid_formats(self):
        """测试有效的日志格式"""
        for fmt in ["text", "json"]:
            config = LoggingConfig(format=fmt)
            assert config.format == fmt

    def test_invalid_format(self):
        """测试无效的日志格式"""
        with pytest.raises(ValidationError):
            LoggingConfig(format="xml")

    def test_invalid_file_path(self):
        """测试无效的日志文件路径"""
        # 空路径
        with pytest.raises(ValidationError):
            LoggingConfig(file="")

        # 不以 .log 结尾
        with pytest.raises(ValidationError):
            LoggingConfig(file="logs/app.txt")

    def test_valid_file_paths(self):
        """测试有效的日志文件路径"""
        valid_paths = ["app.log", "logs/app.log", "output/logs/application.log", "/var/log/app.log"]

        for path in valid_paths:
            config = LoggingConfig(file=path)
            assert config.file == path

    def test_invalid_max_bytes(self):
        """测试无效的日志文件大小"""
        # 小于 1KB
        with pytest.raises(ValidationError):
            LoggingConfig(max_bytes=512)

        # 负数
        with pytest.raises(ValidationError):
            LoggingConfig(max_bytes=-1)

        # 超过 1GB
        with pytest.raises(ValidationError):
            LoggingConfig(max_bytes=1073741825)

    def test_valid_max_bytes(self):
        """测试有效的日志文件大小"""
        valid_sizes = [1024, 1048576, 10485760, 104857600, 1073741824]  # 1KB  # 1MB  # 10MB  # 100MB  # 1GB

        for size in valid_sizes:
            config = LoggingConfig(max_bytes=size)
            assert config.max_bytes == size

    def test_invalid_backup_count(self):
        """测试无效的备份文件数量"""
        # 负数
        with pytest.raises(ValidationError):
            LoggingConfig(backup_count=-1)

        # 超过最大值
        with pytest.raises(ValidationError):
            LoggingConfig(backup_count=101)

    def test_valid_backup_counts(self):
        """测试有效的备份文件数量"""
        # backup_count=0 时需要禁用轮转
        config0 = LoggingConfig(backup_count=0, enable_rotation=False)
        assert config0.backup_count == 0

        # 其他有效值
        valid_counts = [1, 5, 10, 50, 100]

        for count in valid_counts:
            config = LoggingConfig(backup_count=count)
            assert config.backup_count == count

    def test_console_output_flag(self):
        """测试控制台输出标志"""
        config1 = LoggingConfig(console_output=True)
        assert config1.console_output is True

        config2 = LoggingConfig(console_output=False)
        assert config2.console_output is False

    def test_custom_date_format(self):
        """测试自定义日期格式"""
        custom_formats = ["%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%d-%m-%Y %H:%M:%S.%f", "%Y%m%d_%H%M%S"]

        for fmt in custom_formats:
            config = LoggingConfig(date_format=fmt)
            assert config.date_format == fmt

    def test_empty_date_format(self):
        """测试空日期格式"""
        with pytest.raises(ValidationError):
            LoggingConfig(date_format="")

    def test_empty_log_dir(self):
        """测试空日志目录"""
        with pytest.raises(ValidationError):
            LoggingConfig(log_dir="")

    def test_rotation_enabled_without_backup(self):
        """测试启用轮转但备份数为0"""
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(enable_rotation=True, backup_count=0)

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_rotation_disabled_with_zero_backup(self):
        """测试禁用轮转且备份数为0"""
        config = LoggingConfig(enable_rotation=False, backup_count=0)

        assert config.enable_rotation is False
        assert config.backup_count == 0

    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "level": "WARNING",
            "format": "text",
            "file": "logs/warning.log",
            "max_bytes": 5242880,  # 5MB
            "backup_count": 3,
            "console_output": False,
            "date_format": "%Y-%m-%d",
            "log_dir": "output/logs",
            "enable_rotation": True,
        }

        config = LoggingConfig(**config_dict)

        assert config.level == "WARNING"
        assert config.format == "text"
        assert config.file == "logs/warning.log"
        assert config.max_bytes == 5242880
        assert config.backup_count == 3
        assert config.console_output is False
        assert config.date_format == "%Y-%m-%d"
        assert config.log_dir == "output/logs"
        assert config.enable_rotation is True

    def test_to_dict(self):
        """测试转换为字典"""
        config = LoggingConfig(level="ERROR", format="json", file="logs/error.log")

        config_dict = config.model_dump()

        assert config_dict["level"] == "ERROR"
        assert config_dict["format"] == "json"
        assert config_dict["file"] == "logs/error.log"
        assert "max_bytes" in config_dict
        assert "backup_count" in config_dict


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试配置模式...")
    print("=" * 60)

    # 运行 pytest
    exit_code = pytest.main([__file__, "-v", "--tb=short", "-W", "ignore::DeprecationWarning"])

    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 部分测试失败")
        print("=" * 60)

    return exit_code


if __name__ == "__main__":
    exit(run_tests())
