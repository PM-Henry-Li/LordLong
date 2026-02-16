#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

提供统一的配置管理功能，支持多种配置源和优先级管理
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from copy import deepcopy


class ConfigManager:
    """统一配置管理器

    支持多层配置覆盖：默认值 < 配置文件 < 环境变量
    支持 JSON、YAML 格式的配置文件
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "input_file": "input/input_content.txt",
        "output_excel": "output/redbook_content.xlsx",
        "output_image_dir": "output/images",
        "openai_model": "qwen-plus",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "image_model": "jimeng_t2i_v40",
        "image_generation_mode": "template",
        "image_api_provider": "volcengine",
        "template_style": "retro_chinese",
        "enable_ai_rewrite": False,
        "api": {"openai": {"timeout": 30, "max_retries": 3}, "image": {"size": "1024*1365", "timeout": 180}},
        "cache": {"enabled": True, "ttl": 3600, "max_size": "1GB"},
        "rate_limit": {
            "openai": {"requests_per_minute": 60, "tokens_per_minute": 90000},
            "image": {"requests_per_minute": 10},
        },
        "logging": {
            "level": "INFO",
            "format": "json",
            "file": "logs/app.log",
            "max_bytes": 10485760,
            "backup_count": 5,
        },
        "xiaohongshu": {
            "search_mode": "browser",
            "browser_type": "chrome",
            "headless": False,
            "max_search_results": 10,
            "min_likes_threshold": 1000,
            "login_required": False,
            "request_delay": 2,
        },
        "volcengine": {
            "access_key_id": "",
            "secret_access_key": "",
            "endpoint": "https://visual.volcengineapi.com",
            "service": "cv",
            "region": "cn-north-1",
            "model": "general_v2",
            "timeout": 180,
            "max_retries": 3,
            "retry_delay": 1.0,
            "api_version": "2022-08-31",
        },
    }

    # 环境变量映射
    ENV_VAR_MAPPING = {
        # API 配置
        "OPENAI_API_KEY": "openai_api_key",
        "OPENAI_MODEL": "openai_model",
        "OPENAI_BASE_URL": "openai_base_url",
        "OPENAI_TIMEOUT": "api.openai.timeout",
        "OPENAI_MAX_RETRIES": "api.openai.max_retries",
        # 图片配置
        "IMAGE_MODEL": "image_model",
        "IMAGE_GENERATION_MODE": "image_generation_mode",
        "IMAGE_SIZE": "api.image.size",
        "IMAGE_TIMEOUT": "api.image.timeout",
        "IMAGE_API_PROVIDER": "image_api_provider",
        # 模板配置
        "TEMPLATE_STYLE": "template_style",
        # 功能开关
        "ENABLE_AI_REWRITE": "enable_ai_rewrite",
        # 日志配置
        "LOG_LEVEL": "logging.level",
        "LOG_FORMAT": "logging.format",
        "LOG_FILE": "logging.file",
        # 缓存配置
        "CACHE_ENABLED": "cache.enabled",
        "CACHE_TTL": "cache.ttl",
        "CACHE_MAX_SIZE": "cache.max_size",
        # 速率限制配置
        "RATE_LIMIT_OPENAI_RPM": "rate_limit.openai.requests_per_minute",
        "RATE_LIMIT_OPENAI_TPM": "rate_limit.openai.tokens_per_minute",
        "RATE_LIMIT_IMAGE_RPM": "rate_limit.image.requests_per_minute",
        # 输入输出配置
        "INPUT_FILE": "input_file",
        "OUTPUT_EXCEL": "output_excel",
        "OUTPUT_IMAGE_DIR": "output_image_dir",
        # 火山引擎配置
        "VOLCENGINE_ACCESS_KEY_ID": "volcengine.access_key_id",
        "VOLCENGINE_SECRET_ACCESS_KEY": "volcengine.secret_access_key",
        "VOLCENGINE_ENDPOINT": "volcengine.endpoint",
        "VOLCENGINE_SERVICE": "volcengine.service",
        "VOLCENGINE_REGION": "volcengine.region",
        "VOLCENGINE_MODEL": "volcengine.model",
        "VOLCENGINE_TIMEOUT": "volcengine.timeout",
        "VOLCENGINE_MAX_RETRIES": "volcengine.max_retries",
        "VOLCENGINE_RETRY_DELAY": "volcengine.retry_delay",
        "VOLCENGINE_API_VERSION": "volcengine.api_version",
    }

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 config/config.json
        """
        self._config: Dict[str, Any] = deepcopy(self.DEFAULT_CONFIG)
        self._config_path = config_path or "config/config.json"
        self._config_lock = threading.RLock()  # 线程安全锁
        self._reload_callbacks: list[Callable[[], None]] = []  # 重载回调函数列表
        self._watch_thread: Optional[threading.Thread] = None  # 文件监控线程
        self._watching = False  # 监控状态标志
        self._last_mtime: Optional[float] = None  # 文件最后修改时间
        self._load_config()

    def _load_config(self) -> None:
        """加载配置

        按优先级加载：默认值 < 配置文件 < 环境变量
        """
        with self._config_lock:
            # 1. 默认值已在初始化时设置

            # 2. 加载配置文件
            self._load_from_file()

            # 3. 加载环境变量（最高优先级）
            self._load_from_env()

            # 4. 更新文件修改时间
            self._update_mtime()

    def _load_from_file(self) -> None:
        """从配置文件加载配置

        支持 JSON 和 YAML 格式
        支持 ${ENV_VAR} 语法引用环境变量
        """
        config_path = Path(self._config_path)

        if not config_path.exists():
            print(f"⚠️  配置文件不存在: {self._config_path}，使用默认配置")
            return

        try:
            suffix = config_path.suffix.lower()

            if suffix == ".json":
                with open(config_path, "r", encoding="utf - 8") as f:
                    file_config = json.load(f)
            elif suffix in [".yaml", ".yml"]:
                try:
                    import yaml  # type: ignore

                    with open(config_path, "r", encoding="utf - 8") as f:
                        file_config = yaml.safe_load(f)
                except ImportError:
                    print("⚠️  未安装 PyYAML，无法加载 YAML 配置文件")
                    print("   请运行: pip install pyyaml")
                    return
            else:
                print(f"⚠️  不支持的配置文件格式: {suffix}")
                return

            # 解析环境变量引用
            file_config = self._resolve_env_references(file_config)

            # 深度合并配置
            self._deep_merge(self._config, file_config)
            print(f"✅ 已加载配置文件: {self._config_path}")

        except json.JSONDecodeError as e:
            print(f"❌ 配置文件 JSON 格式错误: {e}")
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")

    def _resolve_env_references(self, config: Any) -> Any:
        """递归解析配置中的环境变量引用

        支持 ${ENV_VAR} 和 ${ENV_VAR:default_value} 语法

        Args:
            config: 配置值（可以是字典、列表、字符串等）

        Returns:
            解析后的配置值
        """
        import re

        if isinstance(config, dict):
            # 递归处理字典
            return {key: self._resolve_env_references(value) for key, value in config.items()}
        elif isinstance(config, list):
            # 递归处理列表
            return [self._resolve_env_references(item) for item in config]
        elif isinstance(config, str):
            # 处理字符串中的环境变量引用
            # 支持 ${ENV_VAR} 和 ${ENV_VAR:default_value} 语法
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

            def replace_env_var(match):
                env_var = match.group(1)
                default_value = match.group(2)  # 可能是 None 或空字符串或有值

                # 检查环境变量是否存在
                if env_var in os.environ:
                    return os.environ[env_var]

                # 环境变量不存在
                if default_value is not None:
                    # 有默认值（可能是空字符串）
                    return default_value
                else:
                    # 没有默认值，保留原始引用
                    return match.group(0)

            return re.sub(pattern, replace_env_var, config)
        else:
            # 其他类型直接返回
            return config

    def _load_from_env(self) -> None:
        """从环境变量加载配置

        环境变量具有最高优先级
        """
        for env_var, config_key in self.ENV_VAR_MAPPING.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # 转换为适当的类型
                converted_value = self._convert_env_value(env_value)

                # 设置配置值（支持嵌套键）
                self._set_nested_value(config_key, converted_value)

    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值为适当的类型

        Args:
            value: 环境变量字符串值

        Returns:
            转换后的值
        """
        # 处理布尔值
        if value.lower() in ["true", "1", "yes", "on"]:
            return True
        if value.lower() in ["false", "0", "no", "off"]:
            return False

        # 处理整数
        if value.isdigit():
            return int(value)

        # 处理浮点数
        try:
            if "." in value:
                return float(value)
        except ValueError:
            pass

        # 处理 None/null
        if value.lower() in ["none", "null"]:
            return None

        # 默认返回字符串
        return value

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """深度合并字典

        Args:
            base: 基础字典（会被修改）
            override: 覆盖字典
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _set_nested_value(self, key_path: str, value: Any) -> None:
        """设置嵌套配置值

        Args:
            key_path: 配置键路径，使用点号分隔，如 "api.openai.timeout"
            value: 配置值
        """
        keys = key_path.split(".")
        current = self._config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _get_nested_value(self, key_path: str, default: Any = None) -> Any:
        """获取嵌套配置值

        Args:
            key_path: 配置键路径，使用点号分隔
            default: 默认值

        Returns:
            配置值，如果不存在则返回默认值
        """
        keys = key_path.split(".")
        current = self._config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置键，支持点号分隔的嵌套键，如 "api.openai.timeout"
            default: 默认值

        Returns:
            配置值
        """
        with self._config_lock:
            if "." in key:
                return self._get_nested_value(key, default)
            return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        with self._config_lock:
            if "." in key:
                self._set_nested_value(key, value)
            else:
                self._config[key] = value

    def validate(self) -> bool:
        """验证配置完整性

        验证包括：
        1. 必需配置项是否存在
        2. 配置值的类型是否正确
        3. 配置值的格式是否有效

        Returns:
            配置是否有效
        """
        errors = self.get_validation_errors()

        # 输出验证结果
        if errors:
            print("❌ 配置验证失败，发现以下问题：")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
            return False

        print("✅ 配置验证通过")
        return True

    def get_validation_errors(self) -> list:
        """获取配置验证错误列表

        Returns:
            错误信息列表，如果配置有效则返回空列表
        """
        errors = []

        # 1. 验证必需配置项
        required_fields = {
            "openai_api_key": "OpenAI API Key",
            "openai_model": "OpenAI 模型名称",
            "openai_base_url": "OpenAI API 基础URL",
        }

        for key, description in required_fields.items():
            value = self.get(key)
            if not value:
                errors.append(f"缺少必需配置项: {key} ({description})")

        # 2. 验证配置值类型
        type_validations = {
            "api.openai.timeout": (int, "API 超时时间必须是整数"),
            "api.openai.max_retries": (int, "最大重试次数必须是整数"),
            "api.image.timeout": (int, "图片生成超时时间必须是整数"),
            "cache.enabled": (bool, "缓存启用标志必须是布尔值"),
            "cache.ttl": (int, "缓存TTL必须是整数"),
            "rate_limit.openai.requests_per_minute": (int, "速率限制必须是整数"),
            "rate_limit.openai.tokens_per_minute": (int, "令牌速率限制必须是整数"),
            "rate_limit.image.requests_per_minute": (int, "图片请求速率限制必须是整数"),
        }

        for key, (expected_type, error_msg) in type_validations.items():
            value = self.get(key)
            if value is not None and not isinstance(value, expected_type):
                errors.append(f"{error_msg}，当前值: {value} (类型: {type(value).__name__})")

        # 3. 验证配置值范围和格式

        # 验证超时时间 > 0
        timeout_keys = [("api.openai.timeout", "OpenAI API 超时时间"), ("api.image.timeout", "图片生成超时时间")]
        for key, description in timeout_keys:
            value = self.get(key)
            if value is not None and isinstance(value, int) and value <= 0:
                errors.append(f"{description}必须大于0，当前值: {value}")

        # 验证重试次数 >= 0
        max_retries = self.get("api.openai.max_retries")
        if max_retries is not None and isinstance(max_retries, int) and max_retries < 0:
            errors.append(f"最大重试次数不能为负数，当前值: {max_retries}")

        # 验证缓存TTL > 0
        cache_ttl = self.get("cache.ttl")
        if cache_ttl is not None and isinstance(cache_ttl, int) and cache_ttl <= 0:
            errors.append(f"缓存TTL必须大于0，当前值: {cache_ttl}")

        # 验证速率限制 > 0
        rate_limit_keys = [
            ("rate_limit.openai.requests_per_minute", "OpenAI 请求速率限制"),
            ("rate_limit.openai.tokens_per_minute", "OpenAI 令牌速率限制"),
            ("rate_limit.image.requests_per_minute", "图片请求速率限制"),
        ]
        for key, description in rate_limit_keys:
            value = self.get(key)
            if value is not None and isinstance(value, int) and value <= 0:
                errors.append(f"{description}必须大于0，当前值: {value}")

        # 验证 URL 格式
        base_url = self.get("openai_base_url")
        if base_url and not (base_url.startswith("http://") or base_url.startswith("https://")):
            errors.append(f"OpenAI API 基础URL格式无效，必须以 http:// 或 https:// 开头，当前值: {base_url}")

        # 验证模型名称不为空
        model = self.get("openai_model")
        if model and not model.strip():
            errors.append("OpenAI 模型名称不能为空字符串")

        # 验证图片生成模式
        valid_image_modes = ["template", "api"]
        image_mode = self.get("image_generation_mode")
        if image_mode and image_mode not in valid_image_modes:
            errors.append(f"图片生成模式无效，必须是 {valid_image_modes} 之一，当前值: {image_mode}")

        # 验证模板风格
        valid_styles = ["retro_chinese", "modern_minimal", "vintage_film", "warm_memory", "ink_wash"]
        template_style = self.get("template_style")
        if template_style and template_style not in valid_styles:
            errors.append(f"模板风格无效，必须是 {valid_styles} 之一，当前值: {template_style}")

        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self.get("logging.level")
        if log_level and log_level not in valid_log_levels:
            errors.append(f"日志级别无效，必须是 {valid_log_levels} 之一，当前值: {log_level}")

        return errors

    def reload(self) -> None:
        """手动重新加载配置

        线程安全地重新加载配置文件，并触发所有注册的回调函数
        """
        with self._config_lock:
            self._config = deepcopy(self.DEFAULT_CONFIG)
            self._load_config()
            print("✅ 配置已重新加载")

            # 触发重载回调
            self._trigger_reload_callbacks()

    def _update_mtime(self) -> None:
        """更新配置文件的最后修改时间"""
        config_path = Path(self._config_path)
        if config_path.exists():
            try:
                self._last_mtime = config_path.stat().st_mtime
            except Exception:
                self._last_mtime = None

    def _check_file_changed(self) -> bool:
        """检查配置文件是否已修改

        Returns:
            如果文件已修改返回 True，否则返回 False
        """
        config_path = Path(self._config_path)
        if not config_path.exists():
            return False

        try:
            current_mtime = config_path.stat().st_mtime
            if self._last_mtime is None:
                return False
            return current_mtime != self._last_mtime
        except Exception:
            return False

    def _watch_file(self, check_interval: float = 1.0) -> None:
        """监控配置文件变化的后台线程

        Args:
            check_interval: 检查间隔（秒）
        """
        while self._watching:
            try:
                if self._check_file_changed():
                    print(f"🔄 检测到配置文件变化: {self._config_path}")
                    self.reload()
            except Exception as e:
                print(f"⚠️  监控配置文件时出错: {e}")

            # 使用小步长睡眠，以便快速响应停止信号
            for _ in range(int(check_interval * 10)):
                if not self._watching:
                    break  # type: ignore[unreachable]
                time.sleep(0.1)

    def start_watching(self, check_interval: float = 1.0) -> None:
        """启动配置文件监控

        当配置文件发生变化时，自动重新加载配置

        Args:
            check_interval: 检查间隔（秒），默认 1 秒
        """
        if self._watching:
            print("⚠️  配置文件监控已在运行中")
            return

        config_path = Path(self._config_path)
        if not config_path.exists():
            print(f"⚠️  配置文件不存在，无法启动监控: {self._config_path}")
            return

        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._watch_file, args=(check_interval,), daemon=True, name="ConfigWatcher"
        )
        self._watch_thread.start()
        print(f"👁️  已启动配置文件监控: {self._config_path}")

    def stop_watching(self) -> None:
        """停止配置文件监控"""
        if not self._watching:
            return

        self._watching = False
        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=2.0)
        self._watch_thread = None
        print("⏹️  已停止配置文件监控")

    def is_watching(self) -> bool:
        """检查是否正在监控配置文件

        Returns:
            如果正在监控返回 True，否则返回 False
        """
        return self._watching

    def register_reload_callback(self, callback: Callable[[], None]) -> None:
        """注册配置重载回调函数

        当配置重新加载时，会调用所有注册的回调函数

        Args:
            callback: 回调函数，无参数无返回值
        """
        with self._config_lock:
            if callback not in self._reload_callbacks:
                self._reload_callbacks.append(callback)

    def unregister_reload_callback(self, callback: Callable[[], None]) -> None:
        """取消注册配置重载回调函数

        Args:
            callback: 要取消的回调函数
        """
        with self._config_lock:
            if callback in self._reload_callbacks:
                self._reload_callbacks.remove(callback)

    def _trigger_reload_callbacks(self) -> None:
        """触发所有注册的重载回调函数"""
        for callback in self._reload_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"⚠️  执行重载回调时出错: {e}")

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置

        Returns:
            配置字典的深拷贝
        """
        return deepcopy(self._config)

    def get_config_source(self, key: str) -> str:
        """获取配置项的来源

        Args:
            key: 配置键

        Returns:
            配置来源：'environment', 'file', 'default', 或 'not_found'
        """
        # 检查是否来自环境变量
        for env_var, config_key in self.ENV_VAR_MAPPING.items():
            if config_key == key and os.environ.get(env_var) is not None:
                return "environment"

        # 检查是否在配置文件中（通过比较当前值和默认值）
        current_value = self.get(key)
        default_value = self._get_nested_value_from_dict(self.DEFAULT_CONFIG, key)

        if current_value != default_value:
            return "file"

        # 检查是否存在于默认配置中
        if default_value is not None:
            return "default"

        return "not_found"

    def _get_nested_value_from_dict(self, d: Dict, key_path: str) -> Any:
        """从字典中获取嵌套值

        Args:
            d: 字典
            key_path: 键路径

        Returns:
            值或 None
        """
        keys = key_path.split(".")
        current = d

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ConfigManager(config_path='{self._config_path}')"

    def __del__(self) -> None:
        """析构函数，确保停止监控线程"""
        try:
            self.stop_watching()
        except Exception:
            pass
