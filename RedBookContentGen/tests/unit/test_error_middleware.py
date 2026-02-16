#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理中间件单元测试
"""

import pytest
from flask import Flask
from src.web.error_middleware import ErrorMiddleware, create_error_response
from src.core.exceptions import (
    ValidationError,
    APIError,
    APITimeoutError,
    APIRateLimitError,
    ConfigError,
    ServiceError,
    ErrorCode
)


@pytest.fixture
def app():
    """创建测试 Flask 应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def error_middleware(app):
    """创建错误处理中间件"""
    return ErrorMiddleware(app)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


class TestErrorMiddleware:
    """测试错误处理中间件"""
    
    def test_init_with_app(self, app):
        """测试使用 app 初始化"""
        middleware = ErrorMiddleware(app)
        assert middleware.app == app
    
    def test_init_without_app(self):
        """测试不使用 app 初始化"""
        middleware = ErrorMiddleware()
        assert middleware.app is None
    
    def test_handle_validation_error(self, app, error_middleware, client):
        """测试处理验证错误"""
        @app.route('/test')
        def test_route():
            raise ValidationError(
                message="输入验证失败",
                field="email",
                value="invalid"
            )
        
        response = client.get('/test')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.INVALID_INPUT.value
        assert "输入验证失败" in data['error']['message']
        assert data['error']['details']['field'] == "email"
    
    def test_handle_api_error(self, app, error_middleware, client):
        """测试处理 API 错误"""
        @app.route('/test')
        def test_route():
            raise APIError(
                message="API 调用失败",
                api_name="OpenAI",
                status_code=500
            )
        
        response = client.get('/test')
        assert response.status_code == 503
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.API_ERROR.value
        assert data['error']['retryable'] is True
    
    def test_handle_api_timeout_error(self, app, error_middleware, client):
        """测试处理 API 超时错误"""
        @app.route('/test')
        def test_route():
            raise APITimeoutError(
                api_name="OpenAI",
                timeout=30
            )
        
        response = client.get('/test')
        assert response.status_code == 504
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.TIMEOUT.value
        assert data['error']['retryable'] is True
    
    def test_handle_api_rate_limit_error(self, app, error_middleware, client):
        """测试处理 API 速率限制错误"""
        @app.route('/test')
        def test_route():
            raise APIRateLimitError(
                api_name="OpenAI",
                retry_after=60
            )
        
        response = client.get('/test')
        assert response.status_code == 429
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.API_RATE_LIMIT.value
        assert data['error']['retryable'] is True
    
    def test_handle_config_error(self, app, error_middleware, client):
        """测试处理配置错误"""
        @app.route('/test')
        def test_route():
            raise ConfigError(
                message="配置文件缺失",
                config_file="config.json"
            )
        
        response = client.get('/test')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.CONFIG_ERROR.value
    
    def test_handle_service_error(self, app, error_middleware, client):
        """测试处理服务错误"""
        @app.route('/test')
        def test_route():
            raise ServiceError(
                message="服务异常",
                service_name="ContentGenerator"
            )
        
        response = client.get('/test')
        assert response.status_code == 503
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == ErrorCode.SERVICE_ERROR.value
        assert data['error']['retryable'] is True
    
    def test_handle_http_404(self, app, error_middleware, client):
        """测试处理 HTTP 404 错误"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        data = response.get_json()
        assert data['success'] is False
        assert 'HTTP_404' in data['error']['code']
    
    def test_handle_generic_exception(self, app, error_middleware, client):
        """测试处理通用异常"""
        @app.route('/test')
        def test_route():
            raise ValueError("测试异常")
        
        response = client.get('/test')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == "INTERNAL_ERROR"
        assert data['error']['retryable'] is True
    
    def test_error_response_format(self, app, error_middleware, client):
        """测试错误响应格式"""
        @app.route('/test')
        def test_route():
            raise ValidationError(
                message="测试错误",
                field="test_field",
                suggestions=["建议1", "建议2"]
            )
        
        response = client.get('/test')
        data = response.get_json()
        
        # 验证响应格式
        assert 'success' in data
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert 'details' in data['error']
        assert 'severity' in data['error']
        assert 'suggestions' in data['error']
        assert 'retryable' in data['error']
        
        # 验证建议
        assert len(data['error']['suggestions']) == 2
        assert "建议1" in data['error']['suggestions']


class TestCreateErrorResponse:
    """测试创建错误响应函数"""
    
    def test_basic_error_response(self):
        """测试基本错误响应"""
        response = create_error_response(
            code="TEST_ERROR",
            message="测试错误"
        )
        
        assert response['success'] is False
        assert response['error']['code'] == "TEST_ERROR"
        assert response['error']['message'] == "测试错误"
        assert response['error']['details'] == {}
        assert response['error']['suggestions'] == []
        assert response['error']['severity'] == "error"
        assert response['error']['retryable'] is False
    
    def test_error_response_with_details(self):
        """测试带详情的错误响应"""
        response = create_error_response(
            code="TEST_ERROR",
            message="测试错误",
            details={"field": "test", "value": "invalid"},
            suggestions=["建议1", "建议2"],
            severity="warning",
            retryable=True
        )
        
        assert response['error']['details']['field'] == "test"
        assert response['error']['details']['value'] == "invalid"
        assert len(response['error']['suggestions']) == 2
        assert response['error']['severity'] == "warning"
        assert response['error']['retryable'] is True
