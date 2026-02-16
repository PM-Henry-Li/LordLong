#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求验证模块
提供统一的请求验证装饰器和验证函数
"""

from functools import wraps
from typing import Callable, Optional, Dict, Any, List
from flask import request, jsonify, Response
import re
from pydantic import BaseModel, Field, validator, ValidationError, model_validator


class ContentGenerationRequest(BaseModel):
    """内容生成请求模型"""

    input_text: str = Field(
        ...,
        min_length=2,
        max_length=5000,
        description="输入文本内容，用于生成小红书文案",
        examples=["记得小时候，老北京的胡同里总是充满了生活的气息..."],
    )
    count: int = Field(default=1, ge=1, le=10, description="生成数量")

    class Config:
        """Pydantic 配置"""

        # 自动去除字符串首尾空白
        str_strip_whitespace = True
        # 验证赋值
        validate_assignment = True
        # 使用枚举值
        use_enum_values = True

    @validator("input_text")
    def validate_input_text(cls, v):
        """验证输入文本"""
        if not v:
            raise ValueError("输入文本不能为空")

        # 检查危险字符和XSS攻击模式
        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # script标签
            r"<iframe[^>]*>.*?</iframe>",  # iframe标签
            r"javascript:",  # javascript协议
            r"onerror\s*=",  # onerror事件
            r"onload\s*=",  # onload事件
            r"onclick\s*=",  # onclick事件
            r"<img[^>]+onerror",  # img标签的onerror
            r"eval\s*\(",  # eval函数
            r"expression\s*\(",  # CSS expression
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("输入包含非法内容或潜在的安全风险")

        # 检查是否包含有效的中文或英文内容
        if not re.search(r"[\u4e00-\u9fa5a-zA-Z]", v):
            raise ValueError("输入文本必须包含有效的中文或英文内容")

        return v


class ImageGenerationRequest(BaseModel):
    """图片生成请求模型"""

    prompt: str = Field(..., min_length=1, max_length=2000, description="图片提示词")
    image_mode: str = Field(default="template", description="图片模式")
    image_model: str = Field(default="jimeng_t2i_v40", description="图片模型")
    template_style: str = Field(default="retro_chinese", description="模板风格")
    image_size: str = Field(default="vertical", description="图片尺寸")
    title: str = Field(default="无标题", max_length=100, description="标题")
    scene: str = Field(default="", max_length=500, description="场景描述")
    content_text: str = Field(default="", max_length=1000, description="内容文本", alias="content")
    task_id: str = Field(default="unknown", max_length=100, description="任务ID")
    timestamp: str = Field(..., description="时间戳")
    task_index: int = Field(default=0, ge=0, description="任务索引", alias="index")
    image_type: str = Field(default="content", description="图片类型", alias="type")

    class Config:
        """Pydantic 配置"""

        str_strip_whitespace = True
        validate_assignment = True
        use_enum_values = True
        # 允许字段别名
        populate_by_name = True

    @validator("image_mode")
    def validate_image_mode(cls, v):
        """验证图片模式"""
        allowed_modes = ["template", "api"]
        if v not in allowed_modes:
            raise ValueError(f"图片模式必须是 {allowed_modes} 之一")
        return v

    @validator("image_size")
    def validate_image_size(cls, v):
        """验证图片尺寸"""
        allowed_sizes = ["vertical", "horizontal", "square"]
        if v not in allowed_sizes:
            raise ValueError(f"图片尺寸必须是 {allowed_sizes} 之一")
        return v

    @validator("template_style")
    def validate_template_style(cls, v):
        """验证模板风格"""
        allowed_styles = ["retro_chinese", "modern_minimal", "vintage_film", "warm_memory", "ink_wash", "info_chart"]
        if v not in allowed_styles:
            raise ValueError(f"模板风格必须是 {allowed_styles} 之一")
        return v

    @validator("timestamp")
    def validate_timestamp(cls, v):
        """验证时间戳格式"""
        # 时间戳格式: YYYYMMDD_HHMMSS
        if not re.match(r"^\d{8}_\d{6}$", v):
            raise ValueError("时间戳格式必须为 YYYYMMDD_HHMMSS")
        return v

    @validator("prompt", "title", "scene", "content_text")
    def validate_text_fields(cls, v):
        """验证文本字段，防止XSS"""
        if not v:
            return v

        # 检查危险模式
        dangerous_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("文本包含非法内容")

        return v

    @model_validator(mode="after")
    def validate_api_mode_requirements(self):
        """验证API模式的必需参数"""
        if self.image_mode == "api" and not self.image_model:
            raise ValueError("API模式下必须指定图片模型")

        return self


class LogSearchRequest(BaseModel):
    """日志搜索请求模型"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=50, ge=1, le=200, description="每页数量")
    level: Optional[str] = Field(default="", description="日志级别")
    logger: Optional[str] = Field(default="", description="日志来源")
    start_time: Optional[str] = Field(default="", description="开始时间")
    end_time: Optional[str] = Field(default="", description="结束时间")
    keyword: Optional[str] = Field(default="", max_length=200, description="关键词")

    class Config:
        """Pydantic 配置"""

        str_strip_whitespace = True
        validate_assignment = True

    @validator("level")
    def validate_level(cls, v):
        """验证日志级别"""
        if v and v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("无效的日志级别")
        return v

    @validator("start_time", "end_time")
    def validate_time_format(cls, v):
        """验证时间格式"""
        if not v:
            return v

        # 支持ISO 8601格式: YYYY-MM-DDTHH:MM:SS
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", v):
            raise ValueError("时间格式必须为 YYYY-MM-DDTHH:MM:SS")

        return v

    @validator("keyword")
    def validate_keyword(cls, v):
        """验证关键词"""
        if not v:
            return v

        # 防止SQL注入和特殊字符
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
        for char in dangerous_chars:
            if char in v:
                raise ValueError("关键词包含非法字符")

        return v

    @model_validator(mode="after")
    def validate_time_range(self):
        """验证时间范围"""
        if self.start_time and self.end_time:
            if self.start_time > self.end_time:
                raise ValueError("开始时间不能晚于结束时间")

        return self


def validate_request(model_class: type[BaseModel]) -> Callable:
    """
    请求验证装饰器

    Args:
        model_class: Pydantic 模型类

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 根据请求方法获取数据
                if request.method == "GET":
                    data = request.args.to_dict()
                else:
                    data = request.get_json() or {}

                # 验证数据
                validated_data = model_class(**data)

                # 将验证后的数据传递给路由函数
                return func(validated_data, *args, **kwargs)

            except ValidationError as e:
                # 格式化验证错误
                errors: List[Dict[str, Any]] = []
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    message = error["msg"]
                    error_type = error["type"]

                    # 提供更友好的错误消息
                    friendly_message = _get_friendly_error_message(field, message, error_type, error.get("ctx", {}))

                    errors.append({"field": field, "message": friendly_message, "type": error_type})

                return jsonify({"success": False, "error": "请求参数验证失败", "details": errors}), 400

            except Exception as e:
                return jsonify({"success": False, "error": f"请求处理失败: {str(e)}"}), 500

        return wrapper

    return decorator


def _get_friendly_error_message(field: str, message: str, error_type: str, context: Dict[str, Any]) -> str:
    """
    生成友好的错误消息

    Args:
        field: 字段名
        message: 原始错误消息
        error_type: 错误类型
        context: 错误上下文

    Returns:
        友好的错误消息
    """
    # 字段名映射
    field_names: Dict[str, str] = {
        "input_text": "输入文本",
        "count": "生成数量",
        "prompt": "图片提示词",
        "image_mode": "图片模式",
        "image_size": "图片尺寸",
        "template_style": "模板风格",
        "timestamp": "时间戳",
        "page": "页码",
        "page_size": "每页数量",
        "level": "日志级别",
        "keyword": "关键词",
        "start_time": "开始时间",
        "end_time": "结束时间",
    }

    friendly_field = field_names.get(field, field)

    # 错误类型映射
    if error_type == "value_error.missing":
        return f"{friendly_field}是必填项"
    elif error_type == "value_error.any_str.min_length":
        min_length = context.get("limit_value", "未知")
        return f"{friendly_field}长度不能少于{min_length}个字符"
    elif error_type == "value_error.any_str.max_length":
        max_length = context.get("limit_value", "未知")
        return f"{friendly_field}长度不能超过{max_length}个字符"
    elif error_type == "value_error.number.not_ge":
        limit = context.get("limit_value", "未知")
        return f"{friendly_field}不能小于{limit}"
    elif error_type == "value_error.number.not_le":
        limit = context.get("limit_value", "未知")
        return f"{friendly_field}不能大于{limit}"
    elif "value_error" in error_type:
        # 自定义验证错误，直接返回消息
        return message
    else:
        return f"{friendly_field}: {message}"


def validate_json_request(func: Callable) -> Callable:
    """
    验证 JSON 请求装饰器
    确保请求包含有效的 JSON 数据
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not request.is_json:
            return jsonify({"success": False, "error": "请求必须是 JSON 格式"}), 400

        data = request.get_json()
        if data is None:
            return jsonify({"success": False, "error": "无效的 JSON 数据"}), 400

        return func(*args, **kwargs)

    return wrapper


def serialize_model(model: BaseModel) -> Dict[str, Any]:
    """
    序列化 Pydantic 模型为字典

    Args:
        model: Pydantic 模型实例

    Returns:
        序列化后的字典
    """
    return model.dict(by_alias=True, exclude_none=True)


def deserialize_model(model_class: type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    """
    反序列化字典为 Pydantic 模型

    Args:
        model_class: Pydantic 模型类
        data: 数据字典

    Returns:
        模型实例

    Raises:
        ValidationError: 验证失败
    """
    return model_class(**data)
