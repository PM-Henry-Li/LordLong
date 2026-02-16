#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块

提供结构化日志记录功能，支持 JSON 格式输出、文件轮转和上下文管理
"""

import json
import logging
import logging.handlers
import re
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Callable, Union
from contextvars import ContextVar

# 日志上下文变量（线程安全）
_log_context: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})


# ============================================================================
# 敏感信息脱敏模块
# ============================================================================

class SensitiveDataMasker:
    """敏感信息脱敏器
    
    提供敏感信息的识别和脱敏功能，支持：
    - API Key、Token、密码等认证信息
    - 手机号、邮箱、身份证等个人信息
    - 数据库连接字符串、URL 等
    - 自定义脱敏规则
    - 递归处理字典、列表等复杂数据结构
    """
    
    # 编译后的正则表达式（性能优化）
    _PATTERNS: Dict[str, Pattern] = {}
    
    # Critical 级别敏感字段名（不区分大小写）
    CRITICAL_FIELD_NAMES = {
        'api_key', 'apikey', 'key',
        'password', 'passwd', 'pwd',
        'secret', 'secret_key',
        'access_key', 'private_key',
        'credential', 'token',
        'auth_token', 'access_token', 'refresh_token',
        'id_card', 'identity_card', 'ssn',
    }
    
    # Warning 级别敏感字段名（不区分大小写）
    WARNING_FIELD_NAMES = {
        'authorization', 'auth',
        'phone', 'mobile', 'telephone',
        'email', 'mail',
        'username', 'user', 'account',
    }
    
    # 脱敏配置
    _config = {
        'enabled': True,
        'mask_api_keys': True,
        'mask_passwords': True,
        'mask_tokens': True,
        'mask_phone_numbers': True,
        'mask_emails': True,
        'mask_id_cards': True,
        'mask_urls': True,
    }
    
    @classmethod
    def _compile_patterns(cls) -> None:
        """编译正则表达式（延迟初始化）"""
        if cls._PATTERNS:
            return
        
        cls._PATTERNS = {
            # API Keys
            'openai_api_key': re.compile(r'sk-[a-zA-Z0-9]{32,}'),
            'dashscope_api_key': re.compile(r'dashscope-[a-zA-Z0-9]{32,}'),
            
            # Tokens
            'bearer_token': re.compile(r'Bearer\s+([a-zA-Z0-9_-]+)'),
            'basic_auth': re.compile(r'Basic\s+([a-zA-Z0-9+/=]+)'),
            'generic_token': re.compile(r'\b[a-zA-Z0-9_-]{20,}\b'),
            
            # 手机号
            'china_mobile': re.compile(r'1[3-9]\d{9}'),
            'intl_mobile': re.compile(r'(\+|00)\d{1,3}[-\s]?\d{6,14}'),
            
            # 邮箱
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            
            # 身份证
            'id_card': re.compile(r'\b\d{17}[\dXx]\b'),
            
            # 数据库连接字符串
            'db_url': re.compile(r'(postgresql|mysql|mongodb)://([^:]+):([^@]+)@([^/]+)/(.+)'),
            
            # 带认证的 URL
            'auth_url': re.compile(r'(https?://)([^:]+):([^@]+)@(.+)'),
        }
    
    @classmethod
    def configure(cls, **config: Any) -> None:
        """配置脱敏行为
        
        Args:
            **config: 配置选项
                - enabled: 是否启用脱敏（默认 True）
                - mask_api_keys: 是否脱敏 API Key（默认 True）
                - mask_passwords: 是否脱敏密码（默认 True）
                - mask_tokens: 是否脱敏 Token（默认 True）
                - mask_phone_numbers: 是否脱敏手机号（默认 True）
                - mask_emails: 是否脱敏邮箱（默认 True）
                - mask_id_cards: 是否脱敏身份证（默认 True）
                - mask_urls: 是否脱敏 URL（默认 True）
        """
        cls._config.update(config)
    
    @classmethod
    def mask_api_key(cls, value: str) -> str:
        """脱敏 API Key
        
        Args:
            value: API Key 字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_api_key("sk-abc123def456ghi789jkl012mno345pqr678")
            "sk-***r678"
            >>> mask_api_key("dashscope-xyz789abc456def123ghi890jkl567mno234")
            "dashscope-***o234"
        """
        if not value or not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        # OpenAI API Key
        if value.startswith('sk-'):
            # sk- 后面至少要有 8 个字符才显示后4位
            if len(value) > 11:  # sk- (3) + 至少8个字符
                return f"sk-***{value[-4:]}"
            else:
                return "sk-***"
        
        # DashScope API Key
        if value.startswith('dashscope-'):
            # dashscope- 后面至少要有 8 个字符才显示后4位
            if len(value) > 18:  # dashscope- (10) + 至少8个字符
                return f"dashscope-***{value[-4:]}"
            else:
                return "dashscope-***"
        
        # 通用 API Key（长字符串）
        if len(value) >= 20:
            return f"{value[:4]}...{value[-4:]}"
        
        return "***"
    
    @classmethod
    def mask_password(cls, value: str) -> str:
        """脱敏密码
        
        Args:
            value: 密码字符串
            
        Returns:
            完全隐藏的字符串
            
        Examples:
            >>> mask_password("MyP@ssw0rd123")
            "***"
        """
        return "***" if value else ""
    
    @classmethod
    def mask_token(cls, value: str) -> str:
        """脱敏 Token
        
        Args:
            value: Token 字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_token("abcdefghijklmnopqrstuvwxyz")
            "abcd...wxyz"
            >>> mask_token("short")
            "***"
        """
        if not value or not isinstance(value, str):
            return value
        
        # 短 Token 完全隐藏
        if len(value) <= 8:
            return "***"
        
        # 长 Token 显示前4位和后4位
        return f"{value[:4]}...{value[-4:]}"
    
    @classmethod
    def mask_phone(cls, value: str) -> str:
        """脱敏手机号
        
        Args:
            value: 手机号字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_phone("13812345678")
            "138****5678"
            >>> mask_phone("+8613812345678")
            "+86****5678"
        """
        if not value or not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        # 国际手机号
        intl_match = cls._PATTERNS['intl_mobile'].search(value)
        if intl_match:
            prefix = intl_match.group(1)  # + 或 00
            # 提取国家代码和号码
            full_number = intl_match.group(0)
            if len(full_number) > 8:
                return f"{full_number[:4]}****{full_number[-4:]}"
            return f"{prefix}****"
        
        # 中国大陆手机号
        china_match = cls._PATTERNS['china_mobile'].search(value)
        if china_match:
            number = china_match.group(0)
            return f"{number[:3]}****{number[-4:]}"
        
        return value
    
    @classmethod
    def mask_email(cls, value: str) -> str:
        """脱敏邮箱
        
        Args:
            value: 邮箱字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_email("user@example.com")
            "u***@example.com"
            >>> mask_email("admin@test.org")
            "a***@test.org"
        """
        if not value or not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        email_match = cls._PATTERNS['email'].search(value)
        if email_match:
            email = email_match.group(0)
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                # 显示用户名首字母
                masked_username = f"{username[0]}***" if username else "***"
                return f"{masked_username}@{domain}"
        
        return value
    
    @classmethod
    def mask_id_card(cls, value: str) -> str:
        """脱敏身份证号
        
        Args:
            value: 身份证号字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_id_card("110101199001011234")
            "110101****1234"
        """
        if not value or not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        id_match = cls._PATTERNS['id_card'].search(value)
        if id_match:
            id_card = id_match.group(0)
            return f"{id_card[:6]}****{id_card[-4:]}"
        
        return value
    
    @classmethod
    def mask_url(cls, value: str) -> str:
        """脱敏 URL（隐藏密码部分）
        
        Args:
            value: URL 字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_url("postgresql://user:password@host:5432/db")
            "postgresql://user:***@host:5432/db"
            >>> mask_url("https://user:pass@example.com/path")
            "https://user:***@example.com/path"
        """
        if not value or not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        # 数据库连接字符串
        db_match = cls._PATTERNS['db_url'].search(value)
        if db_match:
            protocol = db_match.group(1)
            username = db_match.group(2)
            host = db_match.group(4)
            database = db_match.group(5)
            return f"{protocol}://{username}:***@{host}/{database}"
        
        # 带认证的 HTTP URL
        auth_match = cls._PATTERNS['auth_url'].search(value)
        if auth_match:
            protocol = auth_match.group(1)
            username = auth_match.group(2)
            rest = auth_match.group(4)
            return f"{protocol}{username}:***@{rest}"
        
        return value
    
    @classmethod
    def mask_bearer_token(cls, value: str) -> str:
        """脱敏 Bearer Token
        
        Args:
            value: Bearer Token 字符串
            
        Returns:
            脱敏后的字符串
            
        Examples:
            >>> mask_bearer_token("Bearer abc123def456ghi789")
            "Bearer ***i789"
        """
        if not value or not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        bearer_match = cls._PATTERNS['bearer_token'].search(value)
        if bearer_match:
            token = bearer_match.group(1)
            masked_token = f"***{token[-4:]}" if len(token) > 4 else "***"
            return f"Bearer {masked_token}"
        
        return value
    
    @classmethod
    def _is_sensitive_field(cls, field_name: str) -> tuple[bool, str]:
        """判断字段名是否为敏感字段
        
        Args:
            field_name: 字段名称
            
        Returns:
            (是否敏感, 敏感级别): 敏感级别为 'critical' 或 'warning'
        """
        if not field_name:
            return False, ''
        
        field_lower = field_name.lower()
        
        if field_lower in cls.CRITICAL_FIELD_NAMES:
            return True, 'critical'
        
        if field_lower in cls.WARNING_FIELD_NAMES:
            return True, 'warning'
        
        return False, ''
    
    @classmethod
    def _mask_value_by_pattern(cls, value: str) -> str:
        """根据值的模式进行脱敏
        
        Args:
            value: 要检查的值
            
        Returns:
            脱敏后的值
        """
        if not isinstance(value, str):
            return value
        
        cls._compile_patterns()
        
        # 检查 API Key
        if cls._config.get('mask_api_keys', True):
            if cls._PATTERNS['openai_api_key'].search(value):
                return cls.mask_api_key(value)
            if cls._PATTERNS['dashscope_api_key'].search(value):
                return cls.mask_api_key(value)
        
        # 检查 Bearer Token
        if cls._config.get('mask_tokens', True):
            if cls._PATTERNS['bearer_token'].search(value):
                return cls.mask_bearer_token(value)
        
        # 检查手机号
        if cls._config.get('mask_phone_numbers', True):
            if cls._PATTERNS['china_mobile'].search(value) or cls._PATTERNS['intl_mobile'].search(value):
                return cls.mask_phone(value)
        
        # 检查邮箱
        if cls._config.get('mask_emails', True):
            if cls._PATTERNS['email'].search(value):
                return cls.mask_email(value)
        
        # 检查身份证
        if cls._config.get('mask_id_cards', True):
            if cls._PATTERNS['id_card'].search(value):
                return cls.mask_id_card(value)
        
        # 检查 URL
        if cls._config.get('mask_urls', True):
            if cls._PATTERNS['db_url'].search(value) or cls._PATTERNS['auth_url'].search(value):
                return cls.mask_url(value)
        
        return value
    
    @classmethod
    def mask_sensitive_data(cls, data: Any, field_name: str = "") -> Any:
        """脱敏敏感数据（递归处理复杂数据结构）
        
        Args:
            data: 要脱敏的数据（可以是字符串、字典、列表等）
            field_name: 字段名称（用于判断是否为敏感字段）
            
        Returns:
            脱敏后的数据
            
        Examples:
            >>> mask_sensitive_data("sk-abc123def456ghi789jkl012mno345pqr678")
            "sk-***r678"
            
            >>> mask_sensitive_data({
            ...     "api_key": "sk-abc123",
            ...     "password": "secret",
            ...     "username": "admin"
            ... })
            {"api_key": "sk-***", "password": "***", "username": "admin"}
            
            >>> mask_sensitive_data(["sk-abc123", "normal text"])
            ["sk-***", "normal text"]
        """
        if not cls._config.get('enabled', True):
            return data
        
        # None 值直接返回
        if data is None:
            return data
        
        # 字符串类型
        if isinstance(data, str):
            # 检查字段名是否为敏感字段
            is_sensitive, level = cls._is_sensitive_field(field_name)
            
            if is_sensitive:
                if level == 'critical':
                    # Critical 级别：根据字段名选择脱敏方式
                    field_lower = field_name.lower()
                    if 'password' in field_lower or 'passwd' in field_lower or 'pwd' in field_lower:
                        return cls.mask_password(data)
                    elif 'key' in field_lower or 'secret' in field_lower:
                        return cls.mask_api_key(data)
                    elif 'token' in field_lower:
                        return cls.mask_token(data)
                    else:
                        return cls.mask_token(data)
                elif level == 'warning':
                    # Warning 级别：根据字段名选择脱敏方式
                    field_lower = field_name.lower()
                    if 'phone' in field_lower or 'mobile' in field_lower or 'telephone' in field_lower:
                        return cls.mask_phone(data)
                    elif 'email' in field_lower or 'mail' in field_lower:
                        return cls.mask_email(data)
                    elif 'authorization' in field_lower or 'auth' in field_lower:
                        return cls.mask_bearer_token(data)
                    # username 等字段不完全隐藏，只做模式匹配
            
            # 根据值的模式进行脱敏
            return cls._mask_value_by_pattern(data)
        
        # 字典类型（递归处理）
        if isinstance(data, dict):
            return {key: cls.mask_sensitive_data(value, key) for key, value in data.items()}
        
        # 列表类型（递归处理）
        if isinstance(data, (list, tuple)):
            masked_list = [cls.mask_sensitive_data(item, field_name) for item in data]
            return type(data)(masked_list)
        
        # 其他类型直接返回
        return data


def _mask_sensitive_data_helper(data: Any, field_name: str = "") -> Any:
    """脱敏敏感数据的辅助函数（供格式化器使用）
    
    Args:
        data: 要脱敏的数据
        field_name: 字段名称
        
    Returns:
        脱敏后的数据
    """
    return SensitiveDataMasker.mask_sensitive_data(data, field_name)


# ============================================================================
# 日志格式化器
# ============================================================================


class JSONFormatter(logging.Formatter):
    """JSON 格式化器

    将日志记录格式化为 JSON 格式，便于日志收集和分析
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            JSON 格式的日志字符串
        """
        # 基础日志信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加上下文信息（脱敏）
        context = _log_context.get()
        if context:
            # SensitiveDataMasker 在文件末尾定义，需要延迟调用
            masked_context = _mask_sensitive_data_helper(context.copy())
            log_data["context"] = masked_context

        # 添加额外字段（脱敏）
        if hasattr(record, "extra_fields"):
            masked_extra = _mask_sensitive_data_helper(record.extra_fields)
            log_data.update(masked_extra)

        # 添加异常信息
        if record.exc_info:
            exc_type = record.exc_info[0]
            log_data["exception"] = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """文本格式化器

    将日志记录格式化为易读的文本格式
    """

    # Emoji 映射
    EMOJI_MAP = {"DEBUG": "🔍", "INFO": "✅", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🔥"}

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        # 获取 emoji
        emoji = self.EMOJI_MAP.get(record.levelname, "📝")

        # 基础格式
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        message = f"{emoji} [{timestamp}] [{record.levelname}] {record.name}: {record.getMessage()}"

        # 添加上下文信息（脱敏）
        context = _log_context.get()
        if context:
            # SensitiveDataMasker 在文件末尾定义，需要延迟调用
            masked_context = _mask_sensitive_data_helper(context)
            context_str = ", ".join(f"{k}={v}" for k, v in masked_context.items())
            message += f" | {context_str}"

        # 添加额外字段（脱敏）
        if hasattr(record, "extra_fields"):
            masked_extra = _mask_sensitive_data_helper(record.extra_fields)
            extra_str = ", ".join(f"{k}={v}" for k, v in masked_extra.items())
            message += f" | {extra_str}"

        # 添加异常信息
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return message


class Logger:
    """结构化日志记录器

    提供统一的日志记录接口，支持：
    - 多种日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
    - JSON 和文本两种格式
    - 文件轮转（基于大小和时间）
    - 日志上下文管理
    - 日志收集（Elasticsearch、Logstash、HTTP 等）
    - 线程安全
    """

    _loggers: Dict[str, logging.Logger] = {}
    _lock = threading.Lock()
    _initialized = False
    _config = None
    _collector_handlers: List[Any] = []

    @classmethod
    def initialize(cls, config: Optional[Any] = None) -> None:
        """初始化日志系统

        Args:
            config: 配置管理器实例，如果为 None 则使用默认配置
        """
        with cls._lock:
            if cls._initialized:
                return

            cls._config = config
            cls._initialized = True

            # 获取日志配置
            log_level = cls._get_config("logging.level", "INFO")
            log_format = cls._get_config("logging.format", "text")
            log_file = cls._get_config("logging.file", "logs/app.log")
            max_bytes = cls._get_config("logging.max_bytes", 10485760)  # 10MB
            backup_count = cls._get_config("logging.backup_count", 5)

            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, log_level))

            # 清除现有处理器
            root_logger.handlers.clear()

            # 添加控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level))
            console_handler.setFormatter(TextFormatter())
            root_logger.addHandler(console_handler)

            # 添加文件处理器（带轮转）
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf - 8"
            )
            file_handler.setLevel(getattr(logging, log_level))

            # 根据配置选择格式化器
            if log_format == "json":
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(TextFormatter())

            root_logger.addHandler(file_handler)

            # 设置日志收集（如果配置了）
            cls._setup_log_collector()

    @classmethod
    def _setup_log_collector(cls) -> None:
        """设置日志收集"""
        if cls._config is None:
            return

        try:
            # 导入日志收集模块
            from .log_collector import LogCollector

            # 从配置创建收集处理器
            handlers = LogCollector.setup_from_config(cls._config)
            cls._collector_handlers.extend(handlers)

        except ImportError:
            # 日志收集模块不可用
            pass
        except Exception as e:
            print(f"⚠️  设置日志收集失败: {e}")

    @classmethod
    def _get_config(cls, key: str, default: Any) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        if cls._config is None:
            return default

        try:
            return cls._config.get(key, default)
        except Exception:
            return default

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取日志记录器

        Args:
            name: 日志记录器名称，通常使用模块名 __name__

        Returns:
            日志记录器实例
        """
        # 确保已初始化
        if not cls._initialized:
            cls.initialize()

        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = logging.getLogger(name)
            return cls._loggers[name]

    @classmethod
    def debug(cls, message: str, logger_name: str = "app", **kwargs: Any) -> None:
        """记录调试日志

        Args:
            message: 日志消息
            logger_name: 日志记录器名称
            **kwargs: 额外字段
        """
        logger = cls.get_logger(logger_name)
        cls._log(logger, logging.DEBUG, message, kwargs)

    @classmethod
    def info(cls, message: str, logger_name: str = "app", **kwargs: Any) -> None:
        """记录信息日志

        Args:
            message: 日志消息
            logger_name: 日志记录器名称
            **kwargs: 额外字段
        """
        logger = cls.get_logger(logger_name)
        cls._log(logger, logging.INFO, message, kwargs)

    @classmethod
    def warning(cls, message: str, logger_name: str = "app", **kwargs: Any) -> None:
        """记录警告日志

        Args:
            message: 日志消息
            logger_name: 日志记录器名称
            **kwargs: 额外字段
        """
        logger = cls.get_logger(logger_name)
        cls._log(logger, logging.WARNING, message, kwargs)

    @classmethod
    def error(cls, message: str, logger_name: str = "app", **kwargs: Any) -> None:
        """记录错误日志

        Args:
            message: 日志消息
            logger_name: 日志记录器名称
            **kwargs: 额外字段
        """
        logger = cls.get_logger(logger_name)
        cls._log(logger, logging.ERROR, message, kwargs)

    @classmethod
    def critical(cls, message: str, logger_name: str = "app", **kwargs: Any) -> None:
        """记录严重错误日志

        Args:
            message: 日志消息
            logger_name: 日志记录器名称
            **kwargs: 额外字段
        """
        logger = cls.get_logger(logger_name)
        cls._log(logger, logging.CRITICAL, message, kwargs)

    @classmethod
    def exception(cls, message: str, logger_name: str = "app", **kwargs: Any) -> None:
        """记录异常日志（包含堆栈跟踪）

        Args:
            message: 日志消息
            logger_name: 日志记录器名称
            **kwargs: 额外字段
        """
        logger = cls.get_logger(logger_name)
        cls._log(logger, logging.ERROR, message, kwargs, exc_info=True)

    @classmethod
    def _log(
        cls, logger: logging.Logger, level: int, message: str, extra_fields: Dict[str, Any], exc_info: bool = False
    ) -> None:
        """内部日志记录方法

        Args:
            logger: 日志记录器
            level: 日志级别
            message: 日志消息
            extra_fields: 额外字段
            exc_info: 是否包含异常信息
        """
        # 创建日志记录
        record = logger.makeRecord(
            logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None if not exc_info else sys.exc_info(),
            "(unknown function)",
        )

        # 添加额外字段（不在这里脱敏，在格式化器中脱敏）
        if extra_fields:
            record.extra_fields = extra_fields

        # 处理日志记录
        logger.handle(record)


class LogContext:
    """日志上下文管理器

    用于在特定代码块中添加上下文信息到日志中

    使用示例:
        with LogContext(request_id="req - 123", user_id="user - 456"):
            Logger.info("处理请求")
            # 日志会自动包含 request_id 和 user_id
    """

    def __init__(self, **context: Any) -> None:
        """初始化日志上下文

        Args:
            **context: 上下文键值对
        """
        self.context = context
        self.token: Any = None
        self.previous_context: Dict[str, Any] = {}

    def __enter__(self) -> "LogContext":
        """进入上下文"""
        # 保存之前的上下文
        self.previous_context = _log_context.get().copy()

        # 合并新上下文
        new_context = self.previous_context.copy()
        new_context.update(self.context)

        # 设置新上下文
        self.token = _log_context.set(new_context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出上下文"""
        # 恢复之前的上下文
        if self.token is not None:
            _log_context.reset(self.token)

    @staticmethod
    def set(**context: Any) -> None:
        """设置全局日志上下文（不在这里脱敏，在格式化器中脱敏）

        Args:
            **context: 上下文键值对
        """
        current = _log_context.get().copy()
        current.update(context)
        _log_context.set(current)

    @staticmethod
    def clear() -> None:
        """清除全局日志上下文"""
        _log_context.set({})

    @staticmethod
    def get() -> Dict[str, Any]:
        """获取当前日志上下文

        Returns:
            上下文字典
        """
        return _log_context.get().copy()


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器（便捷函数）

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return Logger.get_logger(name)


def debug(message: str, **kwargs: Any) -> None:
    """记录调试日志（便捷函数）"""
    Logger.debug(message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """记录信息日志（便捷函数）"""
    Logger.info(message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """记录警告日志（便捷函数）"""
    Logger.warning(message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """记录错误日志（便捷函数）"""
    Logger.error(message, **kwargs)


def critical(message: str, **kwargs: Any) -> None:
    """记录严重错误日志（便捷函数）"""
    Logger.critical(message, **kwargs)


def exception(message: str, **kwargs: Any) -> None:
    """记录异常日志（便捷函数）"""
    Logger.exception(message, **kwargs)


# ============================================================================
# 脱敏便捷函数
# ============================================================================

def mask_sensitive_data(data: Any, field_name: str = "") -> Any:
    """脱敏敏感数据（便捷函数）
    
    Args:
        data: 要脱敏的数据
        field_name: 字段名称
        
    Returns:
        脱敏后的数据
    """
    return SensitiveDataMasker.mask_sensitive_data(data, field_name)


def configure_masking(**config: Any) -> None:
    """配置脱敏行为（便捷函数）
    
    Args:
        **config: 配置选项
    """
    SensitiveDataMasker.configure(**config)
