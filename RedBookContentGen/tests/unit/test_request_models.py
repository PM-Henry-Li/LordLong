#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求模型单元测试
测试 Pydantic 验证模型的各种验证规则
"""

import pytest
from pydantic import ValidationError
from src.models.requests import (
    ContentGenerationRequest,
    ImageGenerationRequest,
    SearchRequest,
)


class TestContentGenerationRequest:
    """内容生成请求模型测试"""
    
    def test_valid_request(self):
        """测试有效的请求"""
        request = ContentGenerationRequest(
            input_text="记得小时候，老北京的胡同里总是充满了生活的气息",
            count=3,
        )
        assert request.input_text is not None
        assert request.count == 3
        assert request.style == "retro_chinese"  # 默认值
        assert request.temperature == 0.8  # 默认值
    
    def test_input_text_too_short(self):
        """测试输入文本过短"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text="太短了")
        
        errors = exc_info.value.errors()
        assert any("min_length" in str(error) for error in errors)
    
    def test_input_text_too_long(self):
        """测试输入文本过长"""
        long_text = "a" * 5001
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text=long_text)
        
        errors = exc_info.value.errors()
        assert any("max_length" in str(error) for error in errors)
    
    def test_input_text_empty(self):
        """测试空输入文本"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text="")
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_input_text_xss_script_tag(self):
        """测试 XSS 攻击：script 标签"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="这是一段正常文本<script>alert('xss')</script>还有更多内容"
            )
        
        errors = exc_info.value.errors()
        assert any("script" in str(error).lower() for error in errors)
    
    def test_input_text_xss_javascript_protocol(self):
        """测试 XSS 攻击：javascript 协议"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="点击这里：javascript:alert('xss') 查看更多内容"
            )
        
        errors = exc_info.value.errors()
        assert any("javascript" in str(error).lower() for error in errors)
    
    def test_input_text_xss_onerror(self):
        """测试 XSS 攻击：onerror 事件"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="这是一段文本 onerror=alert('xss') 还有更多"
            )
        
        errors = exc_info.value.errors()
        assert any("onerror" in str(error).lower() for error in errors)
    
    def test_input_text_no_valid_content(self):
        """测试没有有效内容（只有标点符号）"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text="！！！。。。？？？")
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_input_text_sensitive_word(self):
        """测试敏感词过滤"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="这是一段包含暴力内容的文本，需要被过滤掉"
            )
        
        errors = exc_info.value.errors()
        assert any("敏感词" in str(error) for error in errors)
    
    def test_count_range(self):
        """测试生成数量范围"""
        # 有效范围
        request = ContentGenerationRequest(
            input_text="这是一段有效的输入文本内容",
            count=5,
        )
        assert request.count == 5
        
        # 小于最小值
        with pytest.raises(ValidationError):
            ContentGenerationRequest(
                input_text="这是一段有效的输入文本内容",
                count=0,
            )
        
        # 大于最大值
        with pytest.raises(ValidationError):
            ContentGenerationRequest(
                input_text="这是一段有效的输入文本内容",
                count=11,
            )
    
    def test_style_validation(self):
        """测试风格验证"""
        # 有效风格
        request = ContentGenerationRequest(
            input_text="这是一段有效的输入文本内容",
            style="modern_minimal",
        )
        assert request.style == "modern_minimal"
        
        # 无效风格
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="这是一段有效的输入文本内容",
                style="invalid_style",
            )
        
        errors = exc_info.value.errors()
        assert any("风格" in str(error) for error in errors)
    
    def test_temperature_range(self):
        """测试温度范围"""
        # 有效范围
        request = ContentGenerationRequest(
            input_text="这是一段有效的输入文本内容",
            temperature=1.5,
        )
        assert request.temperature == 1.5
        
        # 小于最小值
        with pytest.raises(ValidationError):
            ContentGenerationRequest(
                input_text="这是一段有效的输入文本内容",
                temperature=-0.1,
            )
        
        # 大于最大值
        with pytest.raises(ValidationError):
            ContentGenerationRequest(
                input_text="这是一段有效的输入文本内容",
                temperature=2.1,
            )
    
    def test_model_validator_high_count_high_temperature(self):
        """测试模型级验证：高数量 + 高温度"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="这是一段有效的输入文本内容",
                count=6,
                temperature=1.5,
            )
        
        errors = exc_info.value.errors()
        assert any("温度" in str(error) or "质量" in str(error) for error in errors)
    
    def test_strip_whitespace(self):
        """测试自动去除首尾空白"""
        request = ContentGenerationRequest(
            input_text="  这是一段有效的输入文本内容  ",
        )
        assert request.input_text == "这是一段有效的输入文本内容"


class TestImageGenerationRequest:
    """图片生成请求模型测试"""
    
    def test_valid_request(self):
        """测试有效的请求"""
        request = ImageGenerationRequest(
            prompt="老北京胡同，复古风格",
            timestamp="20260213_143000",
        )
        assert request.prompt is not None
        assert request.image_mode == "template"  # 默认值
        assert request.timestamp == "20260213_143000"
    
    def test_prompt_length(self):
        """测试提示词长度"""
        # 过长
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="a" * 2001,
                timestamp="20260213_143000",
            )
    
    def test_image_mode_validation(self):
        """测试图片模式验证"""
        # 有效模式
        request = ImageGenerationRequest(
            prompt="测试提示词",
            image_mode="api",
            timestamp="20260213_143000",
        )
        assert request.image_mode == "api"
        
        # 无效模式
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="测试提示词",
                image_mode="invalid",
                timestamp="20260213_143000",
            )
    
    def test_image_size_validation(self):
        """测试图片尺寸验证"""
        # 有效尺寸
        for size in ["vertical", "horizontal", "square"]:
            request = ImageGenerationRequest(
                prompt="测试提示词",
                image_size=size,
                timestamp="20260213_143000",
            )
            assert request.image_size == size
        
        # 无效尺寸
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="测试提示词",
                image_size="invalid",
                timestamp="20260213_143000",
            )
    
    def test_template_style_validation(self):
        """测试模板风格验证"""
        # 有效风格
        for style in ["retro_chinese", "modern_minimal", "vintage_film", "warm_memory", "ink_wash"]:
            request = ImageGenerationRequest(
                prompt="测试提示词",
                template_style=style,
                timestamp="20260213_143000",
            )
            assert request.template_style == style
        
        # 无效风格
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="测试提示词",
                template_style="invalid",
                timestamp="20260213_143000",
            )
    
    def test_timestamp_format(self):
        """测试时间戳格式"""
        # 有效格式
        request = ImageGenerationRequest(
            prompt="测试提示词",
            timestamp="20260213_143000",
        )
        assert request.timestamp == "20260213_143000"
        
        # 无效格式
        invalid_timestamps = [
            "2026-02-13 14:30:00",  # 错误的分隔符
            "20260213143000",       # 缺少下划线
            "20260213_1430",        # 时间部分太短
            "invalid",              # 完全无效
        ]
        
        for ts in invalid_timestamps:
            with pytest.raises(ValidationError):
                ImageGenerationRequest(
                    prompt="测试提示词",
                    timestamp=ts,
                )
    
    def test_timestamp_invalid_date(self):
        """测试无效的日期"""
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="测试提示词",
                timestamp="20261332_143000",  # 13月32日
            )
    
    def test_text_fields_xss(self):
        """测试文本字段的 XSS 防护"""
        # prompt 字段
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="测试<script>alert('xss')</script>",
                timestamp="20260213_143000",
            )
        
        # title 字段
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="正常提示词",
                title="标题<script>alert('xss')</script>",
                timestamp="20260213_143000",
            )
    
    def test_api_mode_requires_model(self):
        """测试 API 模式需要指定模型"""
        # API 模式但没有模型（使用默认值，应该通过）
        request = ImageGenerationRequest(
            prompt="测试提示词",
            image_mode="api",
            timestamp="20260213_143000",
        )
        assert request.image_model == "wan2.2-t2i-flash"
        
        # API 模式且明确设置模型为空（应该失败）
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                prompt="测试提示词",
                image_mode="api",
                image_model="",
                timestamp="20260213_143000",
            )
    
    def test_field_alias(self):
        """测试字段别名"""
        # 使用别名
        request = ImageGenerationRequest(
            prompt="测试提示词",
            timestamp="20260213_143000",
            content="这是内容文本",  # 使用别名
            index=5,                 # 使用别名
            type="cover",            # 使用别名
        )
        assert request.content_text == "这是内容文本"
        assert request.task_index == 5
        assert request.image_type == "cover"


class TestSearchRequest:
    """搜索请求模型测试"""
    
    def test_valid_request(self):
        """测试有效的请求"""
        request = SearchRequest(
            page=1,
            page_size=50,
            keyword="老北京",
        )
        assert request.page == 1
        assert request.page_size == 50
        assert request.keyword == "老北京"
    
    def test_page_range(self):
        """测试页码范围"""
        # 有效页码
        request = SearchRequest(page=10)
        assert request.page == 10
        
        # 无效页码
        with pytest.raises(ValidationError):
            SearchRequest(page=0)
    
    def test_page_size_range(self):
        """测试每页数量范围"""
        # 有效范围
        request = SearchRequest(page_size=100)
        assert request.page_size == 100
        
        # 小于最小值
        with pytest.raises(ValidationError):
            SearchRequest(page_size=0)
        
        # 大于最大值
        with pytest.raises(ValidationError):
            SearchRequest(page_size=201)
    
    def test_keyword_sql_injection(self):
        """测试关键词 SQL 注入防护"""
        dangerous_keywords = [
            "test' OR '1'='1",
            'test"; DROP TABLE users; --',
            "test/* comment */",
            "test\\x00",
        ]
        
        for keyword in dangerous_keywords:
            with pytest.raises(ValidationError):
                SearchRequest(keyword=keyword)
    
    def test_time_format(self):
        """测试时间格式"""
        # 有效格式
        request = SearchRequest(
            start_time="2026-02-01T00:00:00",
            end_time="2026-02-13T23:59:59",
        )
        assert request.start_time == "2026-02-01T00:00:00"
        assert request.end_time == "2026-02-13T23:59:59"
        
        # 无效格式
        with pytest.raises(ValidationError):
            SearchRequest(start_time="2026/02/01 00:00:00")
    
    def test_time_range_validation(self):
        """测试时间范围验证"""
        # 有效范围
        request = SearchRequest(
            start_time="2026-02-01T00:00:00",
            end_time="2026-02-13T23:59:59",
        )
        assert request.start_time < request.end_time
        
        # 开始时间晚于结束时间
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                start_time="2026-02-13T23:59:59",
                end_time="2026-02-01T00:00:00",
            )
        
        errors = exc_info.value.errors()
        assert any("开始时间" in str(error) for error in errors)
    
    def test_sort_order_validation(self):
        """测试排序顺序验证"""
        # 有效顺序
        for order in ["asc", "desc"]:
            request = SearchRequest(sort_order=order)
            assert request.sort_order == order
        
        # 无效顺序
        with pytest.raises(ValidationError):
            SearchRequest(sort_order="invalid")
    
    def test_default_values(self):
        """测试默认值"""
        request = SearchRequest()
        assert request.page == 1
        assert request.page_size == 50
        assert request.sort_by == "created_at"
        assert request.sort_order == "desc"
        assert request.keyword is None
        assert request.start_time is None
        assert request.end_time is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
