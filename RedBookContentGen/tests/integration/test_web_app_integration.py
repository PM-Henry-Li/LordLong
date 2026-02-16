#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 应用集成测试
测试重构后的蓝图架构是否正常工作
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from web_app import create_app


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app("config/config.json")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


class TestWebAppIntegration:
    """Web 应用集成测试"""

    def test_app_creation(self, app):
        """测试应用创建"""
        assert app is not None
        assert app.config["TESTING"] is True

    def test_blueprints_registered(self, app):
        """测试蓝图是否注册"""
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert "main" in blueprint_names
        assert "api" in blueprint_names

    def test_index_page(self, client):
        """测试首页"""
        response = client.get("/")
        assert response.status_code == 200

    def test_logs_page(self, client):
        """测试日志页面"""
        response = client.get("/logs")
        assert response.status_code == 200

    def test_api_models_endpoint(self, client):
        """测试模型列表接口"""
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "models" in data
        assert "image_sizes" in data

    def test_deprecated_api_endpoint(self, client):
        """测试废弃的接口"""
        response = client.post("/api/generate", json={})
        assert response.status_code == 410
        data = response.get_json()
        assert data["success"] is False
        assert "API已升级" in data["error"]

    def test_generate_content_validation_error(self, client):
        """测试内容生成接口验证错误"""
        # 输入文本过短
        response = client.post("/api/generate_content", json={"input_text": "短文本", "count": 1})
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "验证失败" in data["error"]

    def test_generate_content_missing_json(self, client):
        """测试内容生成接口缺少 JSON"""
        response = client.post("/api/generate_content")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "JSON" in data["error"]

    def test_generate_image_validation_error(self, client):
        """测试图片生成接口验证错误"""
        # 无效的图片模式
        response = client.post(
            "/api/generate_image",
            json={"prompt": "测试提示词", "image_mode": "invalid_mode", "timestamp": "20260213_120000"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "验证失败" in data["error"]

    def test_logs_search_endpoint(self, client):
        """测试日志搜索接口"""
        response = client.get("/api/logs/search?page=1&page_size=10")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "logs" in data
        assert "total" in data
        assert "page" in data

    def test_logs_search_validation_error(self, client):
        """测试日志搜索接口验证错误"""
        # 无效的日志级别
        response = client.get("/api/logs/search?level=INVALID_LEVEL")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "验证失败" in data["error"]

    def test_logs_stats_endpoint(self, client):
        """测试日志统计接口"""
        response = client.get("/api/logs/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "stats" in data
        assert "total" in data["stats"]
        assert "error" in data["stats"]
        assert "warning" in data["stats"]
        assert "today" in data["stats"]

    def test_logs_loggers_endpoint(self, client):
        """测试日志来源接口"""
        response = client.get("/api/logs/loggers")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "loggers" in data
        assert isinstance(data["loggers"], list)

    def test_download_nonexistent_file(self, client):
        """测试下载不存在的文件"""
        response = client.get("/api/download/nonexistent.jpg")
        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert "不存在" in data["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
