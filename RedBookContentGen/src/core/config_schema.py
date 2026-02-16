#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模式定义模块

使用 Pydantic 定义配置的数据结构和验证规则
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class OpenAIAPIConfig(BaseModel):
    """OpenAI API 配置模式"""

    key: str = Field(..., description="OpenAI API Key", min_length=1, alias="openai_api_key")

    base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="API 基础 URL", alias="openai_base_url"
    )

    model: str = Field(default="qwen-plus", description="模型名称", min_length=1, alias="openai_model")

    timeout: int = Field(default=30, description="请求超时时间（秒）", gt=0, le=300)

    max_retries: int = Field(default=3, description="最大重试次数", ge=0, le=10)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """验证 base_url 格式"""
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("base_url 必须以 http:// 或 https:// 开头")
        return v.rstrip("/")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """验证模型名称"""
        if not v.strip():
            raise ValueError("模型名称不能为空字符串")
        return v.strip()

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "key": "sk-xxx",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-plus",
                "timeout": 30,
                "max_retries": 3,
            }
        }


class ImageAPIConfig(BaseModel):
    """图片生成 API 配置模式"""

    model: str = Field(default="jimeng_t2i_v40", description="图片生成模型名称", min_length=1, alias="image_model")

    size: str = Field(default="1024*1365", description="图片尺寸", pattern=r"^\d+\*\d+$")

    timeout: int = Field(default=180, description="图片生成超时时间（秒）", gt=0, le=600)

    generation_mode: Literal["template", "api"] = Field(
        default="template", description="图片生成模式：template（模板）或 api（API）", alias="image_generation_mode"
    )

    template_style: Optional[Literal["retro_chinese", "modern_minimal", "vintage_film", "warm_memory", "ink_wash", "info_chart"]] = (
        Field(default="retro_chinese", description="模板风格（仅在 template 模式下使用）")
    )

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: str) -> str:
        """验证图片尺寸格式"""
        parts = v.split("*")
        if len(parts) != 2:
            raise ValueError("图片尺寸格式必须为 宽度*高度，例如：1024*1365")

        try:
            width, height = int(parts[0]), int(parts[1])
            if width <= 0 or height <= 0:
                raise ValueError("图片尺寸必须大于 0")
            if width > 4096 or height > 4096:
                raise ValueError("图片尺寸不能超过 4096")
        except ValueError as e:
            raise ValueError(f"图片尺寸格式无效: {e}")

        return v

    @model_validator(mode="after")
    def validate_template_style(self):
        """验证模板风格配置"""
        if self.generation_mode == "template" and not self.template_style:
            raise ValueError("template 模式下必须指定 template_style")
        return self

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "model": "jimeng_t2i_v40",
                "size": "1024*1365",
                "timeout": 180,
                "generation_mode": "template",
                "template_style": "retro_chinese",
            }
        }


class CacheConfig(BaseModel):
    """缓存配置模式"""

    enabled: bool = Field(default=True, description="是否启用缓存")

    ttl: int = Field(default=3600, description="缓存过期时间（秒），0 表示永不过期", ge=0, le=86400 * 7)  # 最长 7 天

    max_size: str = Field(
        default="1GB", description="缓存最大大小，支持单位：KB、MB、GB", pattern=r"^\d+(\.\d+)?(KB|MB|GB)$"
    )

    eviction_policy: Literal["lru", "lfu", "fifo"] = Field(
        default="lru", description="缓存淘汰策略：lru（最近最少使用）、lfu（最不经常使用）、fifo（先进先出）"
    )

    content_cache_enabled: bool = Field(default=True, description="是否启用内容生成缓存")

    image_cache_enabled: bool = Field(default=True, description="是否启用图片生成缓存")

    cache_dir: str = Field(default="cache", description="缓存目录路径", min_length=1)

    @field_validator("max_size")
    @classmethod
    def validate_max_size(cls, v: str) -> str:
        """验证缓存大小格式并检查合理性"""
        import re

        match = re.match(r"^(\d+(?:\.\d+)?)(KB|MB|GB)$", v)
        if not match:
            raise ValueError("缓存大小格式必须为：数字+单位（KB/MB/GB），例如：1GB、500MB")

        size_value = float(match.group(1))
        unit = match.group(2)

        # 转换为字节进行验证
        size_in_bytes = size_value
        if unit == "KB":
            size_in_bytes *= 1024
        elif unit == "MB":
            size_in_bytes *= 1024 * 1024
        elif unit == "GB":
            size_in_bytes *= 1024 * 1024 * 1024

        # 最小 1MB，最大 100GB
        min_size = 1024 * 1024  # 1MB
        max_size = 100 * 1024 * 1024 * 1024  # 100GB

        if size_in_bytes < min_size:
            raise ValueError("缓存大小不能小于 1MB")
        if size_in_bytes > max_size:
            raise ValueError("缓存大小不能超过 100GB")

        return v

    @model_validator(mode="after")
    def validate_cache_settings(self):
        """验证缓存设置的一致性"""
        # 如果缓存未启用，但子缓存启用了，给出警告（不阻止）
        if not self.enabled:
            if self.content_cache_enabled or self.image_cache_enabled:
                # 这里我们允许这种配置，但在实际使用时应该忽略子缓存设置
                pass

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "ttl": 3600,
                "max_size": "1GB",
                "eviction_policy": "lru",
                "content_cache_enabled": True,
                "image_cache_enabled": True,
                "cache_dir": "cache",
            }
        }


class LoggingConfig(BaseModel):
    """日志配置模式"""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="日志级别")

    format: Literal["text", "json"] = Field(default="json", description="日志格式：text（文本）或 json（JSON结构化）")

    file: str = Field(default="logs/app.log", description="日志文件路径", min_length=1)

    max_bytes: int = Field(
        default=10485760, description="单个日志文件最大字节数（用于日志轮转）", gt=0, le=1073741824  # 10MB  # 最大 1GB
    )

    backup_count: int = Field(default=5, description="保留的日志备份文件数量", ge=0, le=100)

    console_output: bool = Field(default=True, description="是否同时输出到控制台")

    date_format: str = Field(default="%Y-%m-%d %H:%M:%S", description="日志时间格式", min_length=1)

    log_dir: str = Field(default="logs", description="日志目录路径", min_length=1)

    enable_rotation: bool = Field(default=True, description="是否启用日志轮转")

    @field_validator("file")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """验证日志文件路径"""
        if not v.strip():
            raise ValueError("日志文件路径不能为空")

        # 检查文件扩展名
        if not v.endswith(".log"):
            raise ValueError("日志文件必须以 .log 结尾")

        return v.strip()

    @field_validator("max_bytes")
    @classmethod
    def validate_max_bytes(cls, v: int) -> int:
        """验证日志文件大小"""
        # 最小 1KB
        min_size = 1024
        if v < min_size:
            raise ValueError("日志文件大小不能小于 1KB (1024 字节)")

        return v

    @model_validator(mode="after")
    def validate_rotation_settings(self):
        """验证日志轮转设置"""
        if self.enable_rotation and self.backup_count == 0:
            raise ValueError("启用日志轮转时，backup_count 必须大于 0")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "level": "INFO",
                "format": "json",
                "file": "logs/app.log",
                "max_bytes": 10485760,
                "backup_count": 5,
                "console_output": True,
                "date_format": "%Y-%m-%d %H:%M:%S",
                "log_dir": "logs",
                "enable_rotation": True,
            }
        }


class OpenAIRateLimitConfig(BaseModel):
    """OpenAI API 速率限制配置"""

    requests_per_minute: int = Field(default=60, description="每分钟最大请求数", gt=0, le=10000)

    tokens_per_minute: int = Field(default=90000, description="每分钟最大令牌数", gt=0, le=10000000)

    enable_rate_limit: bool = Field(default=True, description="是否启用速率限制")

    @model_validator(mode="after")
    def validate_rate_limits(self):
        """验证速率限制设置的合理性"""
        # 检查请求数和令牌数的比例是否合理
        # 一般来说，每个请求平均消耗的令牌数应该在合理范围内
        avg_tokens_per_request = self.tokens_per_minute / self.requests_per_minute

        # 平均每个请求至少应该有 100 个令牌，最多不超过 100000 个令牌
        if avg_tokens_per_request < 100:
            raise ValueError(
                f"令牌数与请求数比例过低（平均每请求 {avg_tokens_per_request:.0f} 令牌），"
                "建议增加 tokens_per_minute 或减少 requests_per_minute"
            )

        if avg_tokens_per_request > 100000:
            raise ValueError(
                f"令牌数与请求数比例过高（平均每请求 {avg_tokens_per_request:.0f} 令牌），"
                "建议减少 tokens_per_minute 或增加 requests_per_minute"
            )

        return self

    class Config:
        json_schema_extra = {
            "example": {"requests_per_minute": 60, "tokens_per_minute": 90000, "enable_rate_limit": True}
        }


class ImageRateLimitConfig(BaseModel):
    """图片生成 API 速率限制配置"""

    requests_per_minute: int = Field(default=10, description="每分钟最大请求数", gt=0, le=1000)

    enable_rate_limit: bool = Field(default=True, description="是否启用速率限制")

    max_concurrent: int = Field(default=3, description="最大并发请求数", gt=0, le=20)

    @model_validator(mode="after")
    def validate_concurrent_limit(self):
        """验证并发限制与速率限制的一致性"""
        # 并发数不应该超过每分钟请求数
        if self.max_concurrent > self.requests_per_minute:
            raise ValueError(f"最大并发数（{self.max_concurrent}）不应超过每分钟请求数（{self.requests_per_minute}）")

        return self

    class Config:
        json_schema_extra = {"example": {"requests_per_minute": 10, "enable_rate_limit": True, "max_concurrent": 3}}


class RateLimitConfig(BaseModel):
    """速率限制配置总模式"""

    openai: OpenAIRateLimitConfig = Field(default_factory=OpenAIRateLimitConfig, description="OpenAI API 速率限制配置")

    image: ImageRateLimitConfig = Field(default_factory=ImageRateLimitConfig, description="图片生成 API 速率限制配置")

    class Config:
        json_schema_extra = {
            "example": {
                "openai": {"requests_per_minute": 60, "tokens_per_minute": 90000, "enable_rate_limit": True},
                "image": {"requests_per_minute": 10, "enable_rate_limit": True, "max_concurrent": 3},
            }
        }


class APIConfig(BaseModel):
    """API 配置总模式"""

    openai: OpenAIAPIConfig = Field(..., description="OpenAI API 配置")

    image: ImageAPIConfig = Field(..., description="图片生成 API 配置")

    class Config:
        json_schema_extra = {
            "example": {
                "openai": {
                    "key": "sk-xxx",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-plus",
                    "timeout": 30,
                    "max_retries": 3,
                },
                "image": {
                    "model": "jimeng_t2i_v40",
                    "size": "1024*1365",
                    "timeout": 180,
                    "generation_mode": "template",
                    "template_style": "retro_chinese",
                },
            }
        }


class AppConfig(BaseModel):
    """应用完整配置模式"""

    api: APIConfig = Field(..., description="API 配置")

    cache: CacheConfig = Field(default_factory=CacheConfig, description="缓存配置")

    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")

    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig, description="速率限制配置")

    class Config:
        json_schema_extra = {
            "example": {
                "api": {
                    "openai": {
                        "key": "sk-xxx",
                        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                        "model": "qwen-plus",
                        "timeout": 30,
                        "max_retries": 3,
                    },
                    "image": {
                        "model": "jimeng_t2i_v40",
                        "size": "1024*1365",
                        "timeout": 180,
                        "generation_mode": "template",
                        "template_style": "retro_chinese",
                    },
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600,
                    "max_size": "1GB",
                    "eviction_policy": "lru",
                    "content_cache_enabled": True,
                    "image_cache_enabled": True,
                    "cache_dir": "cache",
                },
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "file": "logs/app.log",
                    "max_bytes": 10485760,
                    "backup_count": 5,
                    "console_output": True,
                    "date_format": "%Y-%m-%d %H:%M:%S",
                    "log_dir": "logs",
                    "enable_rotation": True,
                },
                "rate_limit": {
                    "openai": {"requests_per_minute": 60, "tokens_per_minute": 90000, "enable_rate_limit": True},
                    "image": {"requests_per_minute": 10, "enable_rate_limit": True, "max_concurrent": 3},
                },
            }
        }
