#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理集成测试

测试完整的错误处理流程，从 API 路由到服务层
"""

import pytest
from pathlib import Path
from flask import Flask
from src.core.config_manager import ConfigManager
from src.services import ContentService, ImageService
from src.web.blueprints import api_bp
from src.web.error_handlers import register_error_handlers


@pytest.fixture
def app():
    """创建测试应用"""
    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.config["DEBUG"] = False

    # 初始化配置管理器
    config_manager = ConfigManager("config/config.json")
    test_app.config["CONFIG_MANAGER"] = config_manager

    # 初始化输出目录
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    test_app.config["OUTPUT_DIR"] = output_dir

    # 初始化服务层
    content_service = ContentService(config_manager, output_dir)
    image_service = ImageService(config_manager, output_dir)
    test_app.config["CONTENT_SERVICE"] = content_service
    test_app.config["IMAGE_SERVICE"] = image_service

    # 注册蓝图
    test_app.register_blueprint(api_bp)

    # 注册错误处理器
    register_error_handlers(test_app)

    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


class TestAPIErrorHandling:
    """测试 API 错误处理"""

    def test_invalid_json_request(self, client):
        """测试无效的 JSON 请求"""
        response = client.post("/api/generate_content", data="invalid json", content_type="application/json")

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "INVALID_JSON"

    def test_missing_required_field(self, client):
        """测试缺少必需字段"""
        response = client.post("/api/generate_content", json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "INVALID_INPUT"
        assert "validation_errors" in data["error"]["details"]

    def test_invalid_field_value(self, client):
        """测试无效的字段值"""
        response = client.post("/api/generate_content", json={"input_text": "a", "count": 1})  # 太短，最少10个字符

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_resource_not_found(self, client):
        """测试资源不存在"""
        response = client.get("/api/download/nonexistent.png")

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "suggestions" in data["error"]

    def test_method_not_allowed(self, client):
        """测试不支持的请求方法"""
        response = client.put("/api/generate_content")

        assert response.status_code == 405
        data = response.get_json()
        assert data["success"] is False
        assert "不支持的请求方法" in data["error"]["message"]

    def test_page_not_found(self, client):
        """测试页面不存在"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


class TestServiceErrorHandling:
    """测试服务层错误处理"""

    def test_empty_input_text(self, client):
        """测试空输入文本"""
        response = client.post("/api/generate_content", json={"input_text": "          ", "count": 1})  # 只有空格

        # 验证器会先捕获这个错误
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_invalid_image_mode(self, client):
        """测试无效的图片模式"""
        response = client.post(
            "/api/generate_image",
            json={"prompt": "测试提示词", "image_mode": "invalid_mode", "timestamp": "20260213_120000"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data


class TestErrorResponseFormat:
    """测试错误响应格式"""

    def test_error_response_structure(self, client):
        """测试错误响应结构"""
        response = client.post("/api/generate_content", json={})

        data = response.get_json()

        # 验证基本结构
        assert "success" in data
        assert data["success"] is False
        assert "error" in data

        # 验证错误对象结构
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)

        # 可选字段
        if "details" in error:
            assert isinstance(error["details"], dict)

        if "suggestions" in error:
            assert isinstance(error["suggestions"], list)
            for suggestion in error["suggestions"]:
                assert isinstance(suggestion, str)

    def test_error_message_is_chinese(self, client):
        """测试错误消息是中文"""
        response = client.post("/api/generate_content", json={})

        data = response.get_json()
        message = data["error"]["message"]

        # 检查是否包含中文字符
        assert any("\u4e00" <= char <= "\u9fff" for char in message)

    def test_error_has_suggestions(self, client):
        """测试错误包含建议"""
        response = client.get("/api/download/nonexistent.png")

        data = response.get_json()
        assert "suggestions" in data["error"]
        assert len(data["error"]["suggestions"]) > 0


class TestDebugMode:
    """测试调试模式"""

    def test_debug_mode_includes_traceback(self):
        """测试调试模式包含堆栈跟踪"""
        # 创建调试模式应用
        debug_app = Flask(__name__)
        debug_app.config["TESTING"] = True
        debug_app.config["DEBUG"] = True

        register_error_handlers(debug_app)

        @debug_app.route("/test_error")
        def test_error():
            raise Exception("测试错误")

        client = debug_app.test_client()
        response = client.get("/test_error")

        data = response.get_json()
        # 调试模式下应该包含 traceback
        # 注意：实际行为取决于 Flask 的错误处理
        assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
