#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查端点测试
"""

import pytest
from flask import Flask
from src.web.blueprints.api import api_bp
from src.core.config_manager import ConfigManager
from src.services import ContentService, ImageService
from pathlib import Path


@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # 初始化配置管理器
    config_manager = ConfigManager("config/config.json")
    app.config['CONFIG_MANAGER'] = config_manager
    
    # 初始化服务
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    content_service = ContentService(config_manager, output_dir)
    image_service = ImageService(config_manager, output_dir)
    
    app.config['CONTENT_SERVICE'] = content_service
    app.config['IMAGE_SERVICE'] = image_service
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


class TestHealthCheck:
    """健康检查端点测试"""
    
    def test_health_check_success(self, client):
        """测试健康检查成功"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'services' in data
        assert data['services']['content_service'] == 'ok'
        assert data['services']['image_service'] == 'ok'
    
    def test_health_check_missing_service(self, app, client):
        """测试服务缺失时的健康检查"""
        # 移除一个服务
        app.config.pop('CONTENT_SERVICE', None)
        
        response = client.get('/api/health')
        
        assert response.status_code == 503
        data = response.get_json()
        
        assert data['status'] == 'unhealthy'
        assert data['services']['content_service'] == 'unavailable'
    
    def test_health_check_response_format(self, client):
        """测试健康检查响应格式"""
        response = client.get('/api/health')
        data = response.get_json()
        
        # 验证必需字段
        required_fields = ['status', 'timestamp', 'version', 'services']
        for field in required_fields:
            assert field in data, f"缺少必需字段: {field}"
        
        # 验证服务状态字段
        assert 'content_service' in data['services']
        assert 'image_service' in data['services']
        
        # 验证状态值
        assert data['status'] in ['healthy', 'unhealthy']
        
        # 验证服务状态值
        for service_status in data['services'].values():
            assert service_status in ['ok', 'unavailable']
