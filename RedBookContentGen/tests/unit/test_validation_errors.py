#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证错误处理模块的单元测试
"""

import pytest
from pydantic import ValidationError

from src.models.requests import (
    ContentGenerationRequest,
    ImageGenerationRequest,
    SearchRequest,
)
from src.models.validation_errors import (
    ValidationErrorHandler,
    format_validation_error,
)


class TestValidationErrorHandler:
    """测试 ValidationErrorHandler 类"""
    
    def test_missing_required_field(self):
        """测试缺少必填字段的错误处理"""
        try:
            ContentGenerationRequest()
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            assert result["success"] is False
            assert result["error"]["code"] == "VALIDATION_ERROR"
            assert result["error"]["message"] == "输入数据验证失败"
            assert len(result["error"]["errors"]) > 0
            
            # 检查错误详情
            error = result["error"]["errors"][0]
            assert error["field"] == "input_text"
            assert error["field_name"] == "输入文本"
            assert "必填项" in error["message"]
            assert len(error["suggestions"]) > 0
    
    def test_string_too_short(self):
        """测试字符串过短的错误处理"""
        try:
            ContentGenerationRequest(input_text="短")
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "input_text"
            assert "长度不能少于" in error["message"]
            assert "10" in error["message"]
            assert any("详细" in s for s in error["suggestions"])
    
    def test_string_too_long(self):
        """测试字符串过长的错误处理"""
        long_text = "测试" * 3000  # 超过 5000 字符
        try:
            ContentGenerationRequest(input_text=long_text)
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "input_text"
            assert "长度不能超过" in error["message"]
            assert "5000" in error["message"]
            assert any("精简" in s for s in error["suggestions"])
    
    def test_value_out_of_range(self):
        """测试数值超出范围的错误处理"""
        try:
            ContentGenerationRequest(
                input_text="这是一个测试文本，用于验证数值范围",
                count=20  # 超过最大值 10
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "count"
            assert error["field_name"] == "生成数量"
            assert "小于或等于" in error["message"]
            assert "10" in error["message"]
            assert any("不能超过" in s for s in error["suggestions"])
    
    def test_invalid_enum_value(self):
        """测试无效的枚举值错误处理"""
        try:
            ContentGenerationRequest(
                input_text="这是一个测试文本，用于验证枚举值",
                style="invalid_style"
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "style"
            assert error["field_name"] == "生成风格"
            assert "验证失败" in error["message"]
    
    def test_xss_attack_detection(self):
        """测试 XSS 攻击检测的错误处理"""
        try:
            ContentGenerationRequest(
                input_text="<script>alert('xss')</script>测试文本"
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "input_text"
            assert "非法" in error["message"] or "script" in error["message"]
            assert any("非法字符" in s for s in error["suggestions"])
    
    def test_sensitive_word_detection(self):
        """测试敏感词检测的错误处理"""
        try:
            ContentGenerationRequest(
                input_text="这是一个包含暴力内容的测试文本"
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "input_text"
            assert "敏感词" in error["message"]
    
    def test_multiple_errors(self):
        """测试多个错误的处理"""
        try:
            ContentGenerationRequest(
                input_text="短",  # 过短
                count=20,  # 超出范围
                temperature=3.0,  # 超出范围
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            assert len(result["error"]["errors"]) >= 2
            assert result["error"]["total_errors"] >= 2
            
            # 验证每个错误都有必要的字段
            for error in result["error"]["errors"]:
                assert "field" in error
                assert "field_name" in error
                assert "message" in error
                assert "suggestions" in error
                assert "error_type" in error
    
    def test_image_generation_timestamp_error(self):
        """测试图片生成时间戳格式错误"""
        try:
            ImageGenerationRequest(
                prompt="测试提示词",
                timestamp="invalid_timestamp"
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            error = result["error"]["errors"][0]
            assert error["field"] == "timestamp"
            assert error["field_name"] == "时间戳"
            assert "格式" in error["message"]
            assert any("YYYYMMDD_HHMMSS" in s for s in error["suggestions"])
    
    def test_search_time_range_error(self):
        """测试搜索时间范围错误"""
        try:
            SearchRequest(
                start_time="2026-02-13T14:30:00",
                end_time="2026-02-12T14:30:00"  # 结束时间早于开始时间
            )
        except ValidationError as e:
            result = ValidationErrorHandler.handle_validation_error(e)
            
            # 应该有时间范围错误
            assert result["error"]["code"] == "VALIDATION_ERROR"
            assert len(result["error"]["errors"]) > 0


class TestFormatValidationError:
    """测试 format_validation_error 便捷函数"""
    
    def test_format_validation_error(self):
        """测试便捷函数"""
        try:
            ContentGenerationRequest(input_text="短")
        except ValidationError as e:
            result = format_validation_error(e)
            
            assert result["success"] is False
            assert "error" in result
            assert "errors" in result["error"]
    
    def test_error_response_structure(self):
        """测试错误响应结构的完整性"""
        try:
            ContentGenerationRequest()
        except ValidationError as e:
            result = format_validation_error(e)
            
            # 验证顶层结构
            assert "success" in result
            assert "error" in result
            
            # 验证错误对象结构
            error_obj = result["error"]
            assert "code" in error_obj
            assert "message" in error_obj
            assert "errors" in error_obj
            assert "total_errors" in error_obj
            
            # 验证错误详情结构
            if error_obj["errors"]:
                error_detail = error_obj["errors"][0]
                assert "field" in error_detail
                assert "field_name" in error_detail
                assert "message" in error_detail
                assert "suggestions" in error_detail
                assert "error_type" in error_detail


class TestFieldNameMapping:
    """测试字段名称映射"""
    
    def test_all_request_fields_have_chinese_names(self):
        """测试所有请求字段都有中文名称映射"""
        # 这个测试确保我们为所有常用字段提供了中文名称
        common_fields = [
            "input_text", "count", "style", "temperature",
            "prompt", "image_mode", "title", "timestamp",
            "page", "page_size", "keyword",
        ]
        
        for field in common_fields:
            chinese_name = ValidationErrorHandler.FIELD_NAMES.get(field)
            assert chinese_name is not None, f"字段 {field} 缺少中文名称映射"
            assert len(chinese_name) > 0


class TestFixSuggestions:
    """测试修复建议"""
    
    def test_suggestions_are_helpful(self):
        """测试修复建议是否有帮助"""
        try:
            ContentGenerationRequest(input_text="短")
        except ValidationError as e:
            result = format_validation_error(e)
            
            error = result["error"]["errors"][0]
            suggestions = error["suggestions"]
            
            # 建议应该是非空的
            assert len(suggestions) > 0
            
            # 建议应该是字符串
            for suggestion in suggestions:
                assert isinstance(suggestion, str)
                assert len(suggestion) > 0
    
    def test_default_suggestions_for_unknown_fields(self):
        """测试未知字段的默认建议"""
        # 模拟一个未知字段的错误
        suggestions = ValidationErrorHandler._get_fix_suggestions(
            "unknown_field",
            "value_error"
        )
        
        # 应该返回默认建议
        assert len(suggestions) > 0
        assert any("格式" in s or "文档" in s for s in suggestions)


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_error_context(self):
        """测试空错误上下文"""
        try:
            ContentGenerationRequest(count="not_a_number")
        except ValidationError as e:
            result = format_validation_error(e)
            
            # 应该能够处理类型错误
            assert result["success"] is False
            assert len(result["error"]["errors"]) > 0
    
    def test_nested_field_path(self):
        """测试嵌套字段路径"""
        # 虽然当前模型没有嵌套字段，但测试处理逻辑
        field_path = "api.openai.timeout"
        field_name = ValidationErrorHandler._get_field_name(field_path)
        
        # 应该返回最后一个字段名
        assert field_name == "timeout"
    
    def test_chinese_error_messages(self):
        """测试所有错误消息都是中文"""
        try:
            ContentGenerationRequest(
                input_text="短",
                count=20,
                temperature=-1.0,
            )
        except ValidationError as e:
            result = format_validation_error(e)
            
            # 检查所有错误消息都包含中文字符
            for error in result["error"]["errors"]:
                message = error["message"]
                # 至少应该包含一些中文字符
                assert any('\u4e00' <= char <= '\u9fff' for char in message), \
                    f"错误消息不包含中文：{message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
