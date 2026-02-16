#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 模块
包含蓝图、验证器等 Web 相关组件
"""

from .blueprints import api_bp, main_bp
from .validators import (
    validate_request,
    validate_json_request,
    ContentGenerationRequest,
    ImageGenerationRequest,
    LogSearchRequest,
)

__all__ = [
    "api_bp",
    "main_bp",
    "validate_request",
    "validate_json_request",
    "ContentGenerationRequest",
    "ImageGenerationRequest",
    "LogSearchRequest",
]
