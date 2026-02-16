#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 蓝图模块
"""

from .api import api_bp
from .main import main_bp

__all__ = ["api_bp", "main_bp"]
