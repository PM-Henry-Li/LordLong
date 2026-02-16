#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入验证综合测试

测试所有 API 接口的输入验证功能，包括：
- 内容生成 API
- 图片生成 API
- 搜索 API

覆盖：
- 正常输入
- 边界值
- 异常输入
- 安全防护（XSS、SQL注入、敏感词）
"""

import pytest
from pydantic import ValidationError
from src.models.requests import (
    ContentGenerationRequest,
    ImageGenerationRequest,
    SearchRequest,
)


class TestContentGenerationValidation:
    """内容生成请求验证测试"""
    
    # ========== 正常输入测试 ==========
    
    def test_valid_minimal_request(self):
        """测试最小有效请求"""
        request = ContentGenerationRequest(
            input_text="记得小时候，老北京的胡同里总是充满了生活的气息"
        )
        assert request.input_text is not None
        assert request.count == 1  # 默认值
        assert request.style == "retro_chinese"  # 默认值
        assert request.temperature == 0.8  # 默认值
    
    def test_valid_full_request(self):
        """测试完整有效请求"""
        request = ContentGenerationRequest(
            input_text="记得小时候，老北京的胡同里总是充满了生活的气息，邻里之间互相帮助，那时候的生活虽然简单，但充满了温情",
            count=5,
            style="modern_minimal",
            temperature=1.0,
        )
        assert request.count == 5
        assert request.style == "modern_minimal"
        assert request.temperature == 1.0

    
    # ========== 边界值测试 ==========
    
    def test_input_text_min_length(self):
        """测试输入文本最小长度（10个字符）"""
        # 正好10个字符（包含中文）
        request = ContentGenerationRequest(input_text="老北京的胡同文化很美")
        assert len(request.input_text) >= 10
    
    def test_input_text_max_length(self):
        """测试输入文本最大长度（5000个字符）"""
        # 正好5000个字符
        long_text = "老北京" * 1666 + "老北"  # 约5000字符
        request = ContentGenerationRequest(input_text=long_text)
        assert len(request.input_text) <= 5000
    
    def test_count_min_value(self):
        """测试生成数量最小值（1）"""
        request = ContentGenerationRequest(
            input_text="记得小时候的老北京胡同",
            count=1,
        )
        assert request.count == 1
    
    def test_count_max_value(self):
        """测试生成数量最大值（10）"""
        request = ContentGenerationRequest(
            input_text="记得小时候的老北京胡同",
            count=10,
        )
        assert request.count == 10
    
    def test_temperature_min_value(self):
        """测试温度最小值（0.0）"""
        request = ContentGenerationRequest(
            input_text="记得小时候的老北京胡同",
            temperature=0.0,
        )
        assert request.temperature == 0.0
    
    def test_temperature_max_value(self):
        """测试温度最大值（2.0）"""
        request = ContentGenerationRequest(
            input_text="记得小时候的老北京胡同",
            temperature=2.0,
        )
        assert request.temperature == 2.0
    
    # ========== 异常输入测试 ==========
    
    def test_missing_input_text(self):
        """测试缺少必填字段 input_text"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(count=1)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert errors[0]["loc"] == ("input_text",)
        assert errors[0]["type"] == "missing"
    
    def test_input_text_too_short(self):
        """测试输入文本过短"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text="短文本")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("input_text",) for err in errors)
    
    def test_input_text_too_long(self):
        """测试输入文本过长"""
        long_text = "a" * 6000  # 超过5000字符
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text=long_text)
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("input_text",) and "string_too_long" in err["type"]
            for err in errors
        )
    
    def test_count_below_min(self):
        """测试生成数量小于最小值"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="记得小时候的老北京",
                count=0,
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("count",) and "greater_than_equal" in err["type"]
            for err in errors
        )
    
    def test_count_above_max(self):
        """测试生成数量超过最大值"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="记得小时候的老北京",
                count=15,
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("count",) and "less_than_equal" in err["type"]
            for err in errors
        )
    
    def test_invalid_style(self):
        """测试无效的风格"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="记得小时候的老北京",
                style="invalid_style",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("style",) for err in errors)
    
    def test_temperature_below_min(self):
        """测试温度低于最小值"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="记得小时候的老北京",
                temperature=-0.5,
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("temperature",) and "greater_than_equal" in err["type"]
            for err in errors
        )
    
    def test_temperature_above_max(self):
        """测试温度超过最大值"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="记得小时候的老北京",
                temperature=3.0,
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("temperature",) and "less_than_equal" in err["type"]
            for err in errors
        )

    
    # ========== 安全防护测试 ==========
    
    def test_xss_script_tag(self):
        """测试 XSS 攻击：script 标签"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="<script>alert('xss')</script>老北京的胡同"
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("input_text",) and "script" in str(err["msg"]).lower()
            for err in errors
        )
    
    def test_xss_iframe_tag(self):
        """测试 XSS 攻击：iframe 标签"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="<iframe src='evil.com'></iframe>老北京的胡同"
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("input_text",) for err in errors)
    
    def test_xss_javascript_protocol(self):
        """测试 XSS 攻击：javascript 协议"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="javascript:alert('xss') 老北京的胡同"
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("input_text",) for err in errors)
    
    def test_xss_onerror_event(self):
        """测试 XSS 攻击：onerror 事件"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="<img onerror='alert(1)' src='x'> 老北京的胡同"
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("input_text",) for err in errors)
    
    def test_sensitive_word_violence(self):
        """测试敏感词：暴力"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="这是一段包含暴力内容的文本，用于测试敏感词过滤功能"
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("input_text",) and "敏感词" in str(err["msg"])
            for err in errors
        )
    
    def test_empty_content(self):
        """测试空内容"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text="   ")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("input_text",) for err in errors)
    
    def test_only_punctuation(self):
        """测试只有标点符号"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(input_text="！！！。。。？？？！！")
        
        errors = exc_info.value.errors()
        # 应该触发有效内容检查或长度检查
        assert any(err["loc"] == ("input_text",) for err in errors)
    
    def test_batch_quality_check(self):
        """测试批量生成时的质量检查"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="记得小时候的老北京",
                count=8,
                temperature=1.5,
            )
        
        errors = exc_info.value.errors()
        # 应该触发模型级别的验证错误
        assert len(errors) > 0


class TestImageGenerationValidation:
    """图片生成请求验证测试"""
    
    # ========== 正常输入测试 ==========
    
    def test_valid_minimal_request(self):
        """测试最小有效请求"""
        request = ImageGenerationRequest(
            prompt="老北京胡同",
            timestamp="20260213_143000",
        )
        assert request.prompt == "老北京胡同"
        assert request.image_mode == "template"  # 默认值
        assert request.template_style == "retro_chinese"  # 默认值
    
    def test_valid_full_request(self):
        """测试完整有效请求"""
        request = ImageGenerationRequest(
            prompt="老北京胡同，复古风格，温暖的阳光",
            image_mode="api",
            image_model="wan2.2-t2i-flash",
            template_style="vintage_film",
            image_size="horizontal",
            title="老北京的记忆",
            scene="夕阳下的胡同",
            content_text="记得小时候...",
            task_id="task_001",
            timestamp="20260213_143000",
            task_index=1,
            image_type="cover",
        )
        assert request.image_mode == "api"
        assert request.image_size == "horizontal"
        assert request.title == "老北京的记忆"
    
    # ========== 边界值测试 ==========
    
    def test_prompt_min_length(self):
        """测试提示词最小长度（1个字符）"""
        request = ImageGenerationRequest(
            prompt="胡",
            timestamp="20260213_143000",
        )
        assert len(request.prompt) == 1
    
    def test_prompt_max_length(self):
        """测试提示词最大长度（2000个字符）"""
        long_prompt = "老北京胡同" * 400  # 约2000字符
        request = ImageGenerationRequest(
            prompt=long_prompt,
            timestamp="20260213_143000",
        )
        assert len(request.prompt) <= 2000
    
    def test_title_max_length(self):
        """测试标题最大长度（100个字符）"""
        long_title = "标题" * 50  # 100字符
        request = ImageGenerationRequest(
            prompt="老北京胡同",
            title=long_title,
            timestamp="20260213_143000",
        )
        assert len(request.title) <= 100

    
    # ========== 异常输入测试 ==========
    
    def test_missing_prompt(self):
        """测试缺少必填字段 prompt"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(timestamp="20260213_143000")
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("prompt",) and err["type"] == "missing"
            for err in errors
        )
    
    def test_missing_timestamp(self):
        """测试缺少必填字段 timestamp"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(prompt="老北京胡同")
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("timestamp",) and err["type"] == "missing"
            for err in errors
        )
    
    def test_prompt_too_long(self):
        """测试提示词过长"""
        long_prompt = "a" * 2500  # 超过2000字符
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt=long_prompt,
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("prompt",) and "string_too_long" in err["type"]
            for err in errors
        )
    
    def test_invalid_image_mode(self):
        """测试无效的图片模式"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                image_mode="invalid_mode",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("image_mode",) for err in errors)
    
    def test_invalid_image_size(self):
        """测试无效的图片尺寸"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                image_size="invalid_size",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("image_size",) for err in errors)
    
    def test_invalid_template_style(self):
        """测试无效的模板风格"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                template_style="invalid_style",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("template_style",) for err in errors)
    
    def test_invalid_image_type(self):
        """测试无效的图片类型"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                image_type="invalid_type",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("image_type",) for err in errors)
    
    def test_invalid_timestamp_format(self):
        """测试无效的时间戳格式"""
        invalid_timestamps = [
            "2026-02-13",  # 错误格式
            "20260213",  # 缺少时间部分
            "20260213_14",  # 时间部分不完整
            "20260213-143000",  # 错误分隔符
            "invalid",  # 完全无效
        ]
        
        for ts in invalid_timestamps:
            with pytest.raises(ValidationError) as exc_info:
                ImageGenerationRequest(
                    prompt="老北京胡同",
                    timestamp=ts,
                )
            
            errors = exc_info.value.errors()
            assert any(err["loc"] == ("timestamp",) for err in errors)
    
    def test_invalid_timestamp_date(self):
        """测试无效的日期"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                timestamp="20261332_143000",  # 13月32日
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("timestamp",) for err in errors)
    
    def test_invalid_timestamp_time(self):
        """测试无效的时间"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                timestamp="20260213_256090",  # 25:60:90
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("timestamp",) for err in errors)
    
    # ========== 安全防护测试 ==========
    
    def test_xss_in_prompt(self):
        """测试提示词中的 XSS 攻击"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="<script>alert('xss')</script>老北京胡同",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("prompt",) for err in errors)
    
    def test_xss_in_title(self):
        """测试标题中的 XSS 攻击"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                title="<script>alert('xss')</script>",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("title",) for err in errors)
    
    def test_xss_in_scene(self):
        """测试场景描述中的 XSS 攻击"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                scene="javascript:alert('xss')",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("scene",) for err in errors)
    
    def test_xss_in_content_text(self):
        """测试内容文本中的 XSS 攻击"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="老北京胡同",
                content_text="<iframe src='evil.com'></iframe>",
                timestamp="20260213_143000",
            )
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("content_text",) for err in errors)
    
    def test_api_mode_without_model(self):
        """测试 API 模式但未指定模型"""
        # 注意：image_model 有默认值，所以这个测试实际上会通过
        # 但我们可以测试空字符串的情况
        request = ImageGenerationRequest(
            prompt="老北京胡同",
            image_mode="api",
            timestamp="20260213_143000",
        )
        # 应该使用默认模型
        assert request.image_model == "wan2.2-t2i-flash"


class TestSearchValidation:
    """搜索请求验证测试"""
    
    # ========== 正常输入测试 ==========
    
    def test_valid_minimal_request(self):
        """测试最小有效请求（无参数）"""
        request = SearchRequest()
        assert request.page == 1  # 默认值
        assert request.page_size == 50  # 默认值
        assert request.sort_by == "created_at"  # 默认值
        assert request.sort_order == "desc"  # 默认值
    
    def test_valid_full_request(self):
        """测试完整有效请求"""
        request = SearchRequest(
            page=2,
            page_size=100,
            keyword="老北京",
            start_time="2026-02-01T00:00:00",
            end_time="2026-02-13T23:59:59",
            sort_by="title",
            sort_order="asc",
        )
        assert request.page == 2
        assert request.page_size == 100
        assert request.keyword == "老北京"
        assert request.sort_by == "title"
        assert request.sort_order == "asc"

    
    # ========== 边界值测试 ==========
    
    def test_page_min_value(self):
        """测试页码最小值（1）"""
        request = SearchRequest(page=1)
        assert request.page == 1
    
    def test_page_size_min_value(self):
        """测试页面大小最小值（1）"""
        request = SearchRequest(page_size=1)
        assert request.page_size == 1
    
    def test_page_size_max_value(self):
        """测试页面大小最大值（200）"""
        request = SearchRequest(page_size=200)
        assert request.page_size == 200
    
    def test_keyword_max_length(self):
        """测试关键词最大长度（200个字符）"""
        long_keyword = "关键词" * 66 + "关键"  # 约200字符
        request = SearchRequest(keyword=long_keyword)
        assert len(request.keyword) <= 200
    
    # ========== 异常输入测试 ==========
    
    def test_page_below_min(self):
        """测试页码小于最小值"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(page=0)
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("page",) and "greater_than_equal" in err["type"]
            for err in errors
        )
    
    def test_page_negative(self):
        """测试负数页码"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(page=-1)
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("page",) for err in errors)
    
    def test_page_size_below_min(self):
        """测试页面大小小于最小值"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(page_size=0)
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("page_size",) for err in errors)
    
    def test_page_size_above_max(self):
        """测试页面大小超过最大值"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(page_size=500)
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("page_size",) and "less_than_equal" in err["type"]
            for err in errors
        )
    
    def test_keyword_too_long(self):
        """测试关键词过长"""
        long_keyword = "a" * 300  # 超过200字符
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword=long_keyword)
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("keyword",) and "string_too_long" in err["type"]
            for err in errors
        )
    
    def test_invalid_sort_order(self):
        """测试无效的排序顺序"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(sort_order="invalid")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("sort_order",) for err in errors)
    
    def test_invalid_time_format(self):
        """测试无效的时间格式"""
        invalid_times = [
            "2026-02-13",  # 缺少时间部分
            "2026/02/13 14:30:00",  # 错误分隔符
            "20260213T143000",  # 缺少分隔符
            "invalid",  # 完全无效
        ]
        
        for time_str in invalid_times:
            with pytest.raises(ValidationError) as exc_info:
                SearchRequest(start_time=time_str)
            
            errors = exc_info.value.errors()
            assert any(err["loc"] == ("start_time",) for err in errors)
    
    def test_invalid_time_range(self):
        """测试无效的时间范围（开始时间晚于结束时间）"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                start_time="2026-02-13T00:00:00",
                end_time="2026-02-01T00:00:00",
            )
        
        errors = exc_info.value.errors()
        # 应该触发模型级别的验证错误
        assert len(errors) > 0
        assert "开始时间" in str(errors[0]["msg"])
    
    # ========== 安全防护测试 ==========
    
    def test_sql_injection_single_quote(self):
        """测试 SQL 注入：单引号"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword="test' OR '1'='1")
        
        errors = exc_info.value.errors()
        assert any(
            err["loc"] == ("keyword",) and "非法字符" in str(err["msg"])
            for err in errors
        )
    
    def test_sql_injection_double_quote(self):
        """测试 SQL 注入：双引号"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword='test" OR "1"="1')
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("keyword",) for err in errors)
    
    def test_sql_injection_semicolon(self):
        """测试 SQL 注入：分号"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword="test; DROP TABLE users;")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("keyword",) for err in errors)
    
    def test_sql_injection_comment(self):
        """测试 SQL 注入：注释符"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword="test-- comment")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("keyword",) for err in errors)
    
    def test_sql_injection_block_comment(self):
        """测试 SQL 注入：块注释"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword="test /* comment */")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("keyword",) for err in errors)
    
    def test_sql_injection_backslash(self):
        """测试 SQL 注入：反斜杠"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword="test\\escape")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("keyword",) for err in errors)
    
    def test_sql_injection_xp_cmdshell(self):
        """测试 SQL 注入：xp_cmdshell"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(keyword="xp_cmdshell")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("keyword",) for err in errors)
    
    def test_valid_chinese_keyword(self):
        """测试有效的中文关键词"""
        request = SearchRequest(keyword="老北京胡同文化")
        assert request.keyword == "老北京胡同文化"
    
    def test_valid_english_keyword(self):
        """测试有效的英文关键词"""
        request = SearchRequest(keyword="Beijing Hutong")
        assert request.keyword == "Beijing Hutong"
    
    def test_valid_mixed_keyword(self):
        """测试有效的中英文混合关键词"""
        request = SearchRequest(keyword="老北京 Beijing 胡同 Hutong")
        assert request.keyword == "老北京 Beijing 胡同 Hutong"


class TestMultipleValidationErrors:
    """多个验证错误测试"""
    
    def test_content_generation_multiple_errors(self):
        """测试内容生成的多个验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(
                input_text="短",  # 过短
                count=20,  # 超过限制
                temperature=3.0,  # 超过限制
                style="invalid",  # 无效风格
            )
        
        errors = exc_info.value.errors()
        # 应该有多个错误
        assert len(errors) >= 3
        
        # 验证每个字段都有错误
        error_fields = {err["loc"][0] for err in errors}
        assert "input_text" in error_fields
        assert "count" in error_fields
        assert "temperature" in error_fields
    
    def test_image_generation_multiple_errors(self):
        """测试图片生成的多个验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(
                prompt="<script>alert('xss')</script>",  # XSS攻击
                image_mode="invalid",  # 无效模式
                timestamp="invalid",  # 无效时间戳
                title="<iframe src='evil.com'></iframe>",  # XSS攻击
            )
        
        errors = exc_info.value.errors()
        # 应该有多个错误
        assert len(errors) >= 3
    
    def test_search_multiple_errors(self):
        """测试搜索的多个验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                page=0,  # 小于最小值
                page_size=500,  # 超过最大值
                keyword="test'; DROP TABLE users;--",  # SQL注入
                sort_order="invalid",  # 无效排序
            )
        
        errors = exc_info.value.errors()
        # 应该有多个错误
        assert len(errors) >= 3


class TestEdgeCases:
    """边缘情况测试"""
    
    def test_whitespace_trimming(self):
        """测试空白字符自动去除"""
        request = ContentGenerationRequest(
            input_text="  记得小时候的老北京胡同  "
        )
        # 应该自动去除首尾空白
        assert request.input_text == "记得小时候的老北京胡同"
    
    def test_unicode_characters(self):
        """测试 Unicode 字符"""
        request = ContentGenerationRequest(
            input_text="老北京的胡同文化🏮🎎"
        )
        assert "🏮" in request.input_text
    
    def test_special_chinese_punctuation(self):
        """测试中文标点符号"""
        request = ContentGenerationRequest(
            input_text="记得小时候，老北京的胡同里……"
        )
        assert "，" in request.input_text
        assert "……" in request.input_text
    
    def test_mixed_language_content(self):
        """测试中英文混合内容"""
        request = ContentGenerationRequest(
            input_text="老北京的 Hutong 文化 is very interesting"
        )
        assert "Hutong" in request.input_text
    
    def test_numbers_in_content(self):
        """测试包含数字的内容"""
        request = ContentGenerationRequest(
            input_text="1980年代的老北京，有着独特的魅力"
        )
        assert "1980" in request.input_text
    
    def test_optional_fields_none(self):
        """测试可选字段为 None"""
        request = SearchRequest(
            keyword=None,
            start_time=None,
            end_time=None,
        )
        assert request.keyword is None
        assert request.start_time is None
        assert request.end_time is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
