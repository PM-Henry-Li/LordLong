#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 验证器单元测试
"""

import pytest
from pydantic import ValidationError
from src.web.validators import (
    ContentGenerationRequest,
    ImageGenerationRequest,
    LogSearchRequest,
    serialize_model,
    deserialize_model,
)


class TestContentGenerationRequest:
    """内容生成请求验证测试"""

    def test_valid_request(self):
        """测试有效请求"""
        data = {"input_text": "这是一段测试文本，用于验证内容生成请求", "count": 3}
        request = ContentGenerationRequest(**data)
        assert request.input_text == data["input_text"]
        assert request.count == 3

    def test_default_count(self):
        """测试默认数量"""
        data = {"input_text": "这是一段测试文本，用于验证内容生成请求"}
        request = ContentGenerationRequest(**data)
        assert request.count == 1

    def test_input_text_too_short(self):
        """测试输入文本过短"""
        data = {"input_text": "短文本"}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "at least 10 characters" in str(exc_info.value)

    def test_input_text_too_long(self):
        """测试输入文本过长"""
        data = {"input_text": "a" * 5001}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "at most 5000 characters" in str(exc_info.value)

    def test_count_out_of_range(self):
        """测试数量超出范围"""
        data = {"input_text": "这是一段测试文本，用于验证内容生成请求", "count": 11}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_count_negative(self):
        """测试负数数量"""
        data = {"input_text": "这是一段测试文本，用于验证内容生成请求", "count": -1}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        # Pydantic v2 的错误消息格式
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_dangerous_script_tag(self):
        """测试危险的script标签"""
        data = {"input_text": '这是一段包含<script>alert("xss")</script>的文本', "count": 1}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "非法内容" in str(exc_info.value)

    def test_dangerous_iframe_tag(self):
        """测试危险的iframe标签"""
        data = {"input_text": '这是一段包含<iframe src="evil.com"></iframe>的文本', "count": 1}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "非法内容" in str(exc_info.value)

    def test_dangerous_javascript_protocol(self):
        """测试危险的javascript协议"""
        data = {"input_text": "这是一段包含javascript:alert(1)的文本", "count": 1}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "非法内容" in str(exc_info.value)

    def test_dangerous_onerror_event(self):
        """测试危险的onerror事件"""
        data = {"input_text": '这是一段包含<img onerror="alert(1)">的文本', "count": 1}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "非法内容" in str(exc_info.value)

    def test_strip_whitespace(self):
        """测试去除空白字符"""
        data = {"input_text": "  这是一段测试文本，用于验证内容生成请求  ", "count": 1}
        request = ContentGenerationRequest(**data)
        assert request.input_text == "这是一段测试文本，用于验证内容生成请求"

    def test_no_valid_content(self):
        """测试无有效内容"""
        data = {"input_text": "!@#$%^&*()_+{}[]|\\:\";'<>?,./~`", "count": 1}
        with pytest.raises(ValidationError) as exc_info:
            ContentGenerationRequest(**data)
        assert "有效的中文或英文内容" in str(exc_info.value)


class TestImageGenerationRequest:
    """图片生成请求验证测试"""

    def test_valid_request(self):
        """测试有效请求"""
        data = {
            "prompt": "老北京胡同，复古风格",
            "image_mode": "template",
            "image_size": "vertical",
            "timestamp": "20260213_120000",
        }
        request = ImageGenerationRequest(**data)
        assert request.prompt == data["prompt"]
        assert request.image_mode == "template"
        assert request.image_size == "vertical"

    def test_default_values(self):
        """测试默认值"""
        data = {"prompt": "老北京胡同，复古风格", "timestamp": "20260213_120000"}
        request = ImageGenerationRequest(**data)
        assert request.image_mode == "template"
        assert request.image_model == "wan2.2-t2i-flash"
        assert request.template_style == "retro_chinese"
        assert request.image_size == "vertical"

    def test_invalid_image_mode(self):
        """测试无效的图片模式"""
        data = {"prompt": "老北京胡同，复古风格", "image_mode": "invalid_mode", "timestamp": "20260213_120000"}
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(**data)
        assert "图片模式必须是" in str(exc_info.value)

    def test_invalid_image_size(self):
        """测试无效的图片尺寸"""
        data = {"prompt": "老北京胡同，复古风格", "image_size": "invalid_size", "timestamp": "20260213_120000"}
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(**data)
        assert "图片尺寸必须是" in str(exc_info.value)

    def test_invalid_template_style(self):
        """测试无效的模板风格"""
        data = {"prompt": "老北京胡同，复古风格", "template_style": "invalid_style", "timestamp": "20260213_120000"}
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(**data)
        assert "模板风格必须是" in str(exc_info.value)

    def test_invalid_timestamp_format(self):
        """测试无效的时间戳格式"""
        data = {"prompt": "老北京胡同，复古风格", "timestamp": "2026-02-13 12:00:00"}
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(**data)
        assert "时间戳格式必须为" in str(exc_info.value)

    def test_alias_fields(self):
        """测试字段别名"""
        data = {
            "prompt": "老北京胡同，复古风格",
            "content": "这是内容文本",
            "index": 5,
            "type": "cover",
            "timestamp": "20260213_120000",
        }
        request = ImageGenerationRequest(**data)
        assert request.content_text == "这是内容文本"
        assert request.task_index == 5
        assert request.image_type == "cover"

    def test_dangerous_content_in_prompt(self):
        """测试提示词中的危险内容"""
        data = {"prompt": "老北京胡同<script>alert(1)</script>", "timestamp": "20260213_120000"}
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(**data)
        assert "非法内容" in str(exc_info.value)

    def test_api_mode_validation(self):
        """测试API模式验证"""
        # 测试空字符串会触发验证错误
        data = {
            "prompt": "老北京胡同，复古风格",
            "image_mode": "api",
            "image_model": "",  # API模式下模型为空字符串
            "timestamp": "20260213_120000",
        }
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(**data)
        assert "API模式下必须指定图片模型" in str(exc_info.value)


class TestLogSearchRequest:
    """日志搜索请求验证测试"""

    def test_valid_request(self):
        """测试有效请求"""
        data = {"page": 2, "page_size": 100, "level": "ERROR", "keyword": "错误"}
        request = LogSearchRequest(**data)
        assert request.page == 2
        assert request.page_size == 100
        assert request.level == "ERROR"
        assert request.keyword == "错误"

    def test_default_values(self):
        """测试默认值"""
        data = {}
        request = LogSearchRequest(**data)
        assert request.page == 1
        assert request.page_size == 50
        assert request.level == ""
        assert request.keyword == ""

    def test_invalid_log_level(self):
        """测试无效的日志级别"""
        data = {"level": "INVALID_LEVEL"}
        with pytest.raises(ValidationError) as exc_info:
            LogSearchRequest(**data)
        assert "无效的日志级别" in str(exc_info.value)

    def test_page_size_limit(self):
        """测试页面大小限制"""
        data = {"page_size": 201}
        with pytest.raises(ValidationError) as exc_info:
            LogSearchRequest(**data)
        assert "less than or equal to 200" in str(exc_info.value)

    def test_keyword_length_limit(self):
        """测试关键词长度限制"""
        data = {"keyword": "a" * 201}
        with pytest.raises(ValidationError) as exc_info:
            LogSearchRequest(**data)
        assert "at most 200 characters" in str(exc_info.value)

    def test_invalid_time_format(self):
        """测试无效的时间格式"""
        data = {"start_time": "2026-02-13 12:00:00"}  # 缺少T
        with pytest.raises(ValidationError) as exc_info:
            LogSearchRequest(**data)
        assert "时间格式必须为" in str(exc_info.value)

    def test_valid_time_format(self):
        """测试有效的时间格式"""
        data = {"start_time": "2026-02-13T12:00:00", "end_time": "2026-02-13T18:00:00"}
        request = LogSearchRequest(**data)
        assert request.start_time == "2026-02-13T12:00:00"
        assert request.end_time == "2026-02-13T18:00:00"

    def test_time_range_validation(self):
        """测试时间范围验证"""
        data = {"start_time": "2026-02-13T18:00:00", "end_time": "2026-02-13T12:00:00"}  # 结束时间早于开始时间
        with pytest.raises(ValidationError) as exc_info:
            LogSearchRequest(**data)
        assert "开始时间不能晚于结束时间" in str(exc_info.value)

    def test_dangerous_keyword(self):
        """测试危险的关键词"""
        dangerous_keywords = ["'; DROP TABLE", 'admin"--', "/**/SELECT"]
        for keyword in dangerous_keywords:
            data = {"keyword": keyword}
            with pytest.raises(ValidationError) as exc_info:
                LogSearchRequest(**data)
            assert "非法字符" in str(exc_info.value)


class TestSerializationFunctions:
    """序列化函数测试"""

    def test_serialize_model(self):
        """测试模型序列化"""
        data = {"input_text": "这是一段测试文本，用于验证内容生成请求", "count": 3}
        request = ContentGenerationRequest(**data)
        serialized = serialize_model(request)

        assert isinstance(serialized, dict)
        assert serialized["input_text"] == data["input_text"]
        assert serialized["count"] == 3

    def test_serialize_with_alias(self):
        """测试带别名的序列化"""
        data = {"prompt": "老北京胡同，复古风格", "content": "这是内容文本", "index": 5, "timestamp": "20260213_120000"}
        request = ImageGenerationRequest(**data)
        serialized = serialize_model(request)

        # 使用别名序列化
        assert "content" in serialized
        assert "index" in serialized
        assert serialized["content"] == "这是内容文本"
        assert serialized["index"] == 5

    def test_deserialize_model(self):
        """测试模型反序列化"""
        data = {"input_text": "这是一段测试文本，用于验证内容生成请求", "count": 3}
        request = deserialize_model(ContentGenerationRequest, data)

        assert isinstance(request, ContentGenerationRequest)
        assert request.input_text == data["input_text"]
        assert request.count == 3

    def test_deserialize_invalid_data(self):
        """测试反序列化无效数据"""
        data = {"input_text": "短", "count": 3}  # 太短
        with pytest.raises(ValidationError):
            deserialize_model(ContentGenerationRequest, data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
