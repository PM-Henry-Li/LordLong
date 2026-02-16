#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图片生成服务提供商抽象基类

定义了所有图片生成服务提供商必须实现的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseImageProvider(ABC):
    """图片生成服务提供商抽象基类"""
    
    def __init__(self, config_manager, logger, rate_limiter=None, cache=None):
        """
        初始化图片生成服务提供商
        
        Args:
            config_manager: ConfigManager 实例，用于读取配置
            logger: Logger 实例，用于记录日志
            rate_limiter: RateLimiter 实例（可选），用于速率限制
            cache: CacheManager 实例（可选），用于缓存结果
        """
        self.config_manager = config_manager
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.cache = cache
    
    @abstractmethod
    def generate(self, prompt: str, size: str = "1024*1365", **kwargs) -> Optional[str]:
        """
        生成图片
        
        Args:
            prompt: 图片提示词，描述要生成的图片内容
            size: 图片尺寸，格式为 "宽*高"，默认 "1024*1365"
            **kwargs: 其他参数，如 is_cover（是否为封面图）等
            
        Returns:
            生成的图片 URL，失败返回 None
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取服务提供商名称
        
        Returns:
            服务提供商名称（如 "aliyun", "volcengine"）
        """
        pass
