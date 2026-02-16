#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证错误处理模块

提供友好的中文错误消息、错误字段定位和修复建议
"""

from typing import Dict, List, Any, Optional
from pydantic import ValidationError


class ValidationErrorHandler:
    """
    验证错误处理器
    
    将 Pydantic 验证错误转换为友好的中文错误消息，
    并提供错误字段定位和修复建议
    """
    
    # 字段名称的中文映射
    FIELD_NAMES = {
        "input_text": "输入文本",
        "count": "生成数量",
        "style": "生成风格",
        "temperature": "生成温度",
        "prompt": "图片提示词",
        "image_mode": "图片模式",
        "image_model": "图片模型",
        "template_style": "模板风格",
        "image_size": "图片尺寸",
        "title": "标题",
        "scene": "场景描述",
        "content_text": "内容文本",
        "content": "内容文本",
        "task_id": "任务ID",
        "timestamp": "时间戳",
        "task_index": "任务索引",
        "index": "任务索引",
        "image_type": "图片类型",
        "type": "图片类型",
        "page": "页码",
        "page_size": "每页数量",
        "keyword": "搜索关键词",
        "start_time": "开始时间",
        "end_time": "结束时间",
        "sort_by": "排序字段",
        "sort_order": "排序顺序",
    }
    
    # 错误类型的中文消息模板
    ERROR_MESSAGES = {
        "missing": "{field}是必填项",
        "string_too_short": "{field}长度不能少于 {min_length} 个字符（当前：{actual_length} 个字符）",
        "string_too_long": "{field}长度不能超过 {max_length} 个字符（当前：{actual_length} 个字符）",
        "greater_than_equal": "{field}必须大于或等于 {ge}（当前：{actual_value}）",
        "less_than_equal": "{field}必须小于或等于 {le}（当前：{actual_value}）",
        "value_error": "{field}验证失败：{error}",
        "type_error": "{field}类型错误：期望 {expected_type}，实际为 {actual_type}",
        "enum": "{field}必须是以下值之一：{allowed_values}",
        "model_error": "数据验证失败：{error}",
    }
    
    # 常见错误的修复建议
    FIX_SUGGESTIONS = {
        "input_text": {
            "string_too_short": [
                "请提供更详细的内容描述",
                "建议至少输入 10 个字符",
                "可以参考示例：记得小时候，老北京的胡同里...",
            ],
            "string_too_long": [
                "请精简输入内容",
                "建议将长文本分段处理",
                "单次输入不要超过 5000 个字符",
            ],
            "value_error": [
                "请检查输入内容是否包含非法字符",
                "确保输入包含有效的中文或英文内容",
                "避免使用特殊符号和敏感词",
            ],
        },
        "count": {
            "greater_than_equal": [
                "生成数量至少为 1",
            ],
            "less_than_equal": [
                "单次生成数量不能超过 10",
                "如需批量生成，建议分批处理",
            ],
        },
        "temperature": {
            "greater_than_equal": [
                "温度值不能为负数",
                "建议使用 0.7-1.0 之间的值",
            ],
            "less_than_equal": [
                "温度值不能超过 2.0",
                "较高的温度会导致输出不稳定",
            ],
        },
        "timestamp": {
            "value_error": [
                "时间戳格式必须为 YYYYMMDD_HHMMSS",
                "示例：20260213_143000",
                "请检查日期和时间是否有效",
            ],
        },
        "start_time": {
            "value_error": [
                "时间格式必须为 ISO 8601：YYYY-MM-DDTHH:MM:SS",
                "示例：2026-02-13T14:30:00",
            ],
        },
        "end_time": {
            "value_error": [
                "时间格式必须为 ISO 8601：YYYY-MM-DDTHH:MM:SS",
                "示例：2026-02-13T23:59:59",
            ],
        },
        "keyword": {
            "value_error": [
                "关键词不能包含特殊字符",
                "请使用普通的中文或英文字符",
            ],
        },
    }
    
    @classmethod
    def handle_validation_error(cls, error: ValidationError) -> Dict[str, Any]:
        """
        处理 Pydantic 验证错误
        
        Args:
            error: Pydantic ValidationError 对象
            
        Returns:
            统一的错误响应格式
        """
        errors = []
        
        for err in error.errors():
            field_path = cls._get_field_path(err)
            field_name = cls._get_field_name(field_path)
            error_type = err["type"]
            error_msg = err.get("msg", "")
            error_ctx = err.get("ctx", {})
            
            # 生成友好的错误消息
            friendly_msg = cls._generate_friendly_message(
                field_name, field_path, error_type, error_msg, error_ctx
            )
            
            # 获取修复建议
            suggestions = cls._get_fix_suggestions(field_path, error_type)
            
            errors.append({
                "field": field_path,
                "field_name": field_name,
                "message": friendly_msg,
                "suggestions": suggestions,
                "error_type": error_type,
            })
        
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "输入数据验证失败",
                "errors": errors,
                "total_errors": len(errors),
            }
        }
    
    @classmethod
    def _get_field_path(cls, error: Dict) -> str:
        """
        获取字段路径
        
        Args:
            error: 错误字典
            
        Returns:
            字段路径字符串，例如 "input_text" 或 "api.timeout"
        """
        loc = error.get("loc", ())
        return ".".join(str(item) for item in loc)
    
    @classmethod
    def _get_field_name(cls, field_path: str) -> str:
        """
        获取字段的中文名称
        
        Args:
            field_path: 字段路径
            
        Returns:
            中文字段名称
        """
        # 获取最后一个字段名
        field = field_path.split(".")[-1]
        return cls.FIELD_NAMES.get(field, field)
    
    @classmethod
    def _generate_friendly_message(
        cls,
        field_name: str,
        field_path: str,
        error_type: str,
        error_msg: str,
        error_ctx: Dict,
    ) -> str:
        """
        生成友好的错误消息
        
        Args:
            field_name: 字段中文名称
            field_path: 字段路径
            error_type: 错误类型
            error_msg: 原始错误消息
            error_ctx: 错误上下文
            
        Returns:
            友好的中文错误消息
        """
        # 处理不同的错误类型
        if error_type == "missing":
            return cls.ERROR_MESSAGES["missing"].format(field=field_name)
        
        elif error_type == "string_too_short":
            min_length = error_ctx.get("min_length", "?")
            actual_length = error_ctx.get("actual_length", "?")
            return cls.ERROR_MESSAGES["string_too_short"].format(
                field=field_name,
                min_length=min_length,
                actual_length=actual_length,
            )
        
        elif error_type == "string_too_long":
            max_length = error_ctx.get("max_length", "?")
            actual_length = error_ctx.get("actual_length", "?")
            return cls.ERROR_MESSAGES["string_too_long"].format(
                field=field_name,
                max_length=max_length,
                actual_length=actual_length,
            )
        
        elif error_type == "greater_than_equal":
            ge = error_ctx.get("ge", "?")
            actual_value = error_ctx.get("actual_value", "?")
            return cls.ERROR_MESSAGES["greater_than_equal"].format(
                field=field_name,
                ge=ge,
                actual_value=actual_value,
            )
        
        elif error_type == "less_than_equal":
            le = error_ctx.get("le", "?")
            actual_value = error_ctx.get("actual_value", "?")
            return cls.ERROR_MESSAGES["less_than_equal"].format(
                field=field_name,
                le=le,
                actual_value=actual_value,
            )
        
        elif error_type == "value_error":
            # 从错误消息中提取具体错误
            error_detail = error_msg.replace("Value error, ", "")
            return cls.ERROR_MESSAGES["value_error"].format(
                field=field_name,
                error=error_detail,
            )
        
        elif error_type.startswith("type_error"):
            expected_type = error_ctx.get("expected_type", "未知类型")
            return cls.ERROR_MESSAGES["type_error"].format(
                field=field_name,
                expected_type=expected_type,
                actual_type="未知类型",
            )
        
        elif error_type == "enum":
            allowed_values = error_ctx.get("expected", "")
            return cls.ERROR_MESSAGES["enum"].format(
                field=field_name,
                allowed_values=allowed_values,
            )
        
        else:
            # 默认消息
            return f"{field_name}验证失败：{error_msg}"
    
    @classmethod
    def _get_fix_suggestions(cls, field_path: str, error_type: str) -> List[str]:
        """
        获取修复建议
        
        Args:
            field_path: 字段路径
            error_type: 错误类型
            
        Returns:
            修复建议列表
        """
        # 获取最后一个字段名
        field = field_path.split(".")[-1]
        
        # 查找字段和错误类型对应的建议
        field_suggestions = cls.FIX_SUGGESTIONS.get(field, {})
        suggestions = field_suggestions.get(error_type, [])
        
        # 如果没有特定建议，返回通用建议
        if not suggestions:
            suggestions = [
                "请检查输入格式是否正确",
                "参考 API 文档了解详细要求",
            ]
        
        return suggestions


def format_validation_error(error: ValidationError) -> Dict[str, Any]:
    """
    格式化验证错误的便捷函数
    
    Args:
        error: Pydantic ValidationError 对象
        
    Returns:
        统一的错误响应格式
        
    Examples:
        >>> from pydantic import ValidationError
        >>> try:
        ...     ContentGenerationRequest(input_text="短")
        ... except ValidationError as e:
        ...     error_response = format_validation_error(e)
        ...     print(error_response["error"]["message"])
        输入数据验证失败
    """
    return ValidationErrorHandler.handle_validation_error(error)
