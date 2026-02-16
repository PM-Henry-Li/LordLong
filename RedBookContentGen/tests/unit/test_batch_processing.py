#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理功能单元测试

测试批量内容生成、批量导出等功能
"""

import pytest
from pydantic import ValidationError
from src.models.requests import BatchContentGenerationRequest


class TestBatchContentGenerationRequest:
    """批量内容生成请求模型测试"""
    
    def test_valid_batch_request(self):
        """测试有效的批量请求"""
        data = {
            "inputs": [
                "记得小时候，老北京的胡同里总是充满了生活的气息...",
                "北京的四合院是传统建筑的代表，体现了中国人的居住智慧...",
            ],
            "count": 1,
            "style": "retro_chinese",
            "temperature": 0.8,
        }
        
        request = BatchContentGenerationRequest(**data)
        
        assert len(request.inputs) == 2
        assert request.count == 1
        assert request.style == "retro_chinese"
        assert request.temperature == 0.8
    
    def test_empty_inputs(self):
        """测试空输入列表"""
        data = {
            "inputs": [],
            "count": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BatchContentGenerationRequest(**data)
        
        errors = exc_info.value.errors()
        # Pydantic 内置验证：列表长度至少为 1
        assert any(e['type'] == 'too_short' for e in errors)
    
    def test_too_many_inputs(self):
        """测试输入数量超限"""
        data = {
            "inputs": ["测试文本" * 10] * 51,  # 51 条输入
            "count": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BatchContentGenerationRequest(**data)
        
        errors = exc_info.value.errors()
        # Pydantic 内置验证：列表长度最多为 50
        assert any(e['type'] == 'too_long' for e in errors)
    
    def test_short_input_text(self):
        """测试输入文本过短"""
        data = {
            "inputs": [
                "记得小时候，老北京的胡同里总是充满了生活的气息...",
                "短文本",  # 少于 10 个字符
            ],
            "count": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BatchContentGenerationRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("不能少于 10 个字符" in str(e) for e in errors)
    
    def test_long_input_text(self):
        """测试输入文本过长"""
        data = {
            "inputs": [
                "测试" * 2501,  # 超过 5000 个字符
            ],
            "count": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BatchContentGenerationRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("不能超过 5000 个字符" in str(e) for e in errors)
    
    def test_invalid_content(self):
        """测试无效内容（无中英文）"""
        data = {
            "inputs": [
                "1234567890!!!",  # 无中英文内容
            ],
            "count": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BatchContentGenerationRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("必须包含有效的中文或英文内容" in str(e) for e in errors)
    
    def test_high_temperature_with_many_tasks(self):
        """测试大批量任务时温度过高"""
        data = {
            "inputs": ["测试文本" * 10] * 15,  # 15 条输入
            "count": 1,  # 总共 15 个任务
            "temperature": 1.5,  # 温度过高
        }
        
        with pytest.raises(ValidationError) as exc_info:
            BatchContentGenerationRequest(**data)
        
        errors = exc_info.value.errors()
        assert any("建议将温度设置为 1.0 或更低" in str(e) for e in errors)
    
    def test_default_values(self):
        """测试默认值"""
        data = {
            "inputs": ["记得小时候，老北京的胡同里总是充满了生活的气息..."],
        }
        
        request = BatchContentGenerationRequest(**data)
        
        assert request.count == 1
        assert request.style == "retro_chinese"
        assert request.temperature == 0.8


class TestExportUtils:
    """导出工具测试"""
    
    def test_export_batch_to_excel_without_openpyxl(self):
        """测试在没有 openpyxl 的情况下导出 Excel"""
        from src.utils.export_utils import ExportUtils, HAS_OPENPYXL
        
        if HAS_OPENPYXL:
            pytest.skip("openpyxl 已安装，跳过此测试")
        
        batch_result = {
            "batch_id": "batch_test",
            "total": 1,
            "results": [],
            "summary": {"success": 0, "failed": 0, "total": 0},
        }
        
        with pytest.raises(ImportError) as exc_info:
            ExportUtils.export_batch_to_excel(batch_result)
        
        assert "openpyxl" in str(exc_info.value)
    
    def test_create_batch_info_text(self):
        """测试创建批次信息文本"""
        from src.utils.export_utils import ExportUtils
        
        batch_result = {
            "batch_id": "batch_20260213_143000",
            "total": 2,
            "results": [
                {
                    "index": 0,
                    "input_text": "测试输入1",
                    "status": "success",
                    "data": {
                        "titles": ["测试标题1"],
                        "tags": ["标签1", "标签2"],
                    },
                    "error": None,
                },
                {
                    "index": 1,
                    "input_text": "测试输入2",
                    "status": "failed",
                    "data": None,
                    "error": "测试错误",
                },
            ],
            "summary": {
                "success": 1,
                "failed": 1,
                "total": 2,
            },
        }
        
        text = ExportUtils._create_batch_info_text(batch_result)
        
        assert "batch_20260213_143000" in text
        assert "总任务数: 2" in text
        assert "成功数量: 1" in text
        assert "失败数量: 1" in text
        assert "测试输入1" in text
        assert "测试输入2" in text
        assert "✓ 成功" in text
        assert "✗ 失败" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
