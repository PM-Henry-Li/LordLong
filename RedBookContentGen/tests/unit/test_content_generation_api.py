#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容生成 API 接口测试
测试 Pydantic 验证模型的集成
"""

import json
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from src.web.blueprints.api import api_bp


@pytest.fixture
def app():
    """创建测试应用"""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    
    # 模拟服务
    mock_content_service = Mock()
    mock_image_service = Mock()
    test_app.config['CONTENT_SERVICE'] = mock_content_service
    test_app.config['IMAGE_SERVICE'] = mock_image_service
    
    # 注册蓝图
    test_app.register_blueprint(api_bp)
    
    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


class TestContentGenerationAPI:
    """内容生成 API 测试"""
    
    def test_generate_content_success(self, client, app):
        """测试成功生成内容"""
        # 准备测试数据
        request_data = {
            "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息，邻里之间互相帮助",
            "count": 3,
            "style": "retro_chinese",
            "temperature": 0.8
        }
        
        # 模拟服务返回
        mock_result = {
            "titles": ["标题1", "标题2", "标题3"],
            "content": "生成的内容...",
            "tags": ["老北京", "胡同"],
            "image_prompts": ["提示词1", "提示词2"]
        }
        app.config['CONTENT_SERVICE'].generate_content.return_value = mock_result
        
        # 发送请求
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data'] == mock_result
    
    def test_generate_content_input_too_short(self, client):
        """测试输入文本过短"""
        request_data = {
            "input_text": "短文本",
            "count": 1
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert len(data['error']['errors']) > 0
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'input_text'
        assert error['field_name'] == '输入文本'
        assert 'suggestions' in error
        assert len(error['suggestions']) > 0
    
    def test_generate_content_input_too_long(self, client):
        """测试输入文本过长"""
        request_data = {
            "input_text": "a" * 6000,  # 超过 5000 字符限制
            "count": 1
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'input_text'
        assert 'string_too_long' in error['error_type']
    
    def test_generate_content_invalid_count(self, client):
        """测试无效的生成数量"""
        request_data = {
            "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息",
            "count": 15  # 超过 10 的限制
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'count'
        assert error['field_name'] == '生成数量'
    
    def test_generate_content_invalid_style(self, client):
        """测试无效的风格"""
        request_data = {
            "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息",
            "count": 1,
            "style": "invalid_style"
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'style'
    
    def test_generate_content_xss_attack(self, client):
        """测试 XSS 攻击防护"""
        request_data = {
            "input_text": "<script>alert('xss')</script>老北京的胡同",
            "count": 1
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'input_text'
        assert 'script' in error['message'].lower() or '非法' in error['message']
    
    def test_generate_content_sensitive_words(self, client):
        """测试敏感词过滤"""
        request_data = {
            "input_text": "这是一段包含暴力内容的文本，用于测试敏感词过滤功能",
            "count": 1
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'input_text'
        assert '敏感词' in error['message']
    
    def test_generate_content_missing_required_field(self, client):
        """测试缺少必填字段"""
        request_data = {
            "count": 1
            # 缺少 input_text
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'input_text'
        assert '必填' in error['message'] or 'required' in error['message'].lower()
    
    def test_generate_content_multiple_errors(self, client):
        """测试多个验证错误"""
        request_data = {
            "input_text": "短",  # 过短
            "count": 20,  # 超过限制
            "temperature": 3.0  # 超过限制
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证有多个错误
        assert data['error']['total_errors'] >= 2
        assert len(data['error']['errors']) >= 2
    
    def test_generate_content_batch_quality_check(self, client):
        """测试批量生成时的质量检查"""
        request_data = {
            "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息",
            "count": 8,  # 大于 5
            "temperature": 1.5  # 大于 1.0
        }
        
        response = client.post(
            '/api/generate_content',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert '温度' in error['message'] or '质量' in error['message']


class TestImageGenerationAPI:
    """图片生成 API 测试"""
    
    def test_generate_image_success(self, client, app):
        """测试成功生成图片"""
        request_data = {
            "prompt": "老北京胡同，复古风格，温暖的阳光",
            "image_mode": "template",
            "template_style": "retro_chinese",
            "image_size": "vertical",
            "title": "老北京的记忆",
            "timestamp": "20260213_143000"
        }
        
        # 模拟服务返回
        mock_result = {
            "image_url": "/api/download/images/20260213/image_001.png",
            "task_id": "task_20260213_001"
        }
        app.config['IMAGE_SERVICE'].generate_image.return_value = mock_result
        
        # 发送请求
        response = client.post(
            '/api/generate_image',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data'] == mock_result
    
    def test_generate_image_invalid_timestamp(self, client):
        """测试无效的时间戳格式"""
        request_data = {
            "prompt": "老北京胡同",
            "timestamp": "2026-02-13"  # 错误格式
        }
        
        response = client.post(
            '/api/generate_image',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'timestamp'
        assert error['field_name'] == '时间戳'
        assert 'YYYYMMDD_HHMMSS' in error['message']
    
    def test_generate_image_invalid_mode(self, client):
        """测试无效的图片模式"""
        request_data = {
            "prompt": "老北京胡同",
            "image_mode": "invalid_mode",
            "timestamp": "20260213_143000"
        }
        
        response = client.post(
            '/api/generate_image',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'
        
        # 验证错误详情
        error = data['error']['errors'][0]
        assert error['field'] == 'image_mode'
    
    def test_generate_image_xss_in_title(self, client):
        """测试标题中的 XSS 攻击"""
        request_data = {
            "prompt": "老北京胡同",
            "title": "<script>alert('xss')</script>",
            "timestamp": "20260213_143000"
        }
        
        response = client.post(
            '/api/generate_image',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证响应
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
