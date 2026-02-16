#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理器单元测试
"""

import pytest
from flask import Flask, jsonify
from src.core.errors import (
    ErrorCode,
    AppError,
    ValidationError,
    ResourceNotFoundError,
    ContentGenerationError,
    ImageGenerationError,
    APIError,
    create_error_response,
    get_http_status_code,
)
from src.web.error_handlers import handle_errors, register_error_handlers


class TestErrorClasses:
    """测试错误类"""

    def test_app_error_basic(self):
        """测试基础应用错误"""
        error = AppError(message="测试错误", code=ErrorCode.INTERNAL_ERROR, status_code=500)

        assert error.message == "测试错误"
        assert error.code == ErrorCode.INTERNAL_ERROR
        assert error.status_code == 500
        assert error.details == {}
        assert error.suggestions == []

    def test_app_error_with_details(self):
        """测试带详情的应用错误"""
        error = AppError(
            message="测试错误",
            code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details={"field": "input_text"},
            suggestions=["请检查输入"],
        )

        error_dict = error.to_dict()
        assert error_dict["code"] == ErrorCode.INVALID_INPUT.value
        assert error_dict["message"] == "测试错误"
        assert error_dict["details"]["field"] == "input_text"
        assert "请检查输入" in error_dict["suggestions"]

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError(message="输入无效")

        assert error.status_code == 400
        assert error.code == ErrorCode.INVALID_INPUT
        assert "请检查输入参数" in error.suggestions[0]

    def test_resource_not_found_error(self):
        """测试资源不存在错误"""
        error = ResourceNotFoundError(message="文件不存在", resource_type="图片", resource_id="test.png")

        assert error.status_code == 404
        assert error.code == ErrorCode.RESOURCE_NOT_FOUND
        assert error.details["resource_type"] == "图片"
        assert error.details["resource_id"] == "test.png"

    def test_content_generation_error(self):
        """测试内容生成错误"""
        error = ContentGenerationError(message="生成失败")

        assert error.status_code == 500
        assert error.code == ErrorCode.CONTENT_GENERATION_FAILED
        assert len(error.suggestions) > 0

    def test_image_generation_error(self):
        """测试图片生成错误"""
        error = ImageGenerationError(message="图片生成失败", details={"task_id": "test_001"})

        assert error.status_code == 500
        assert error.code == ErrorCode.IMAGE_GENERATION_FAILED
        assert error.details["task_id"] == "test_001"

    def test_api_error(self):
        """测试外部API错误"""
        error = APIError(message="API调用失败", api_name="OpenAI", details={"status_code": 429})

        assert error.status_code == 502
        assert error.code == ErrorCode.API_ERROR
        assert error.details["api_name"] == "OpenAI"
        assert error.details["status_code"] == 429


class TestErrorResponse:
    """测试错误响应"""

    def test_create_error_response_from_app_error(self):
        """测试从应用错误创建响应"""
        error = ValidationError(message="输入无效")
        response = create_error_response(error)

        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == ErrorCode.INVALID_INPUT.value
        assert response["error"]["message"] == "输入无效"

    def test_create_error_response_from_generic_error(self):
        """测试从通用错误创建响应"""
        error = Exception("未知错误")
        response = create_error_response(error)

        assert response["success"] is False
        assert response["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
        assert response["error"]["message"] == "服务器内部错误"

    def test_create_error_response_with_traceback(self):
        """测试包含堆栈跟踪的错误响应"""
        error = Exception("测试错误")
        response = create_error_response(error, include_traceback=True)

        assert "traceback" in response["error"]
        assert "original_error" in response["error"]

    def test_get_http_status_code(self):
        """测试获取HTTP状态码"""
        error1 = ValidationError()
        assert get_http_status_code(error1) == 400

        error2 = ResourceNotFoundError()
        assert get_http_status_code(error2) == 404

        error3 = Exception("未知错误")
        assert get_http_status_code(error3) == 500


class TestErrorHandlerDecorator:
    """测试错误处理装饰器"""

    def test_handle_errors_success(self):
        """测试成功情况"""

        @handle_errors
        def success_route():
            return jsonify({"success": True, "data": "test"})

        # 创建测试应用上下文
        app = Flask(__name__)
        with app.app_context():
            response = success_route()
            # handle_errors 装饰器不会改变成功响应的格式
            assert response.json["success"] is True

    def test_handle_errors_validation_error(self):
        """测试验证错误处理"""

        @handle_errors
        def validation_error_route():
            raise ValidationError(message="输入无效")

        app = Flask(__name__)
        with app.app_context():
            response, status_code = validation_error_route()
            assert status_code == 400
            assert response.json["success"] is False
            assert response.json["error"]["code"] == ErrorCode.INVALID_INPUT.value

    def test_handle_errors_value_error(self):
        """测试值错误处理"""

        @handle_errors
        def value_error_route():
            raise ValueError("内容生成失败")

        app = Flask(__name__)
        with app.app_context():
            response, status_code = value_error_route()
            assert status_code == 500
            assert response.json["success"] is False

    def test_handle_errors_generic_error(self):
        """测试通用错误处理"""

        @handle_errors
        def generic_error_route():
            raise Exception("未知错误")

        app = Flask(__name__)
        app.config["DEBUG"] = False
        with app.app_context():
            response, status_code = generic_error_route()
            assert status_code == 500
            assert response.json["success"] is False
            assert response.json["error"]["code"] == ErrorCode.INTERNAL_ERROR.value


class TestGlobalErrorHandlers:
    """测试全局错误处理器"""

    def test_register_error_handlers(self):
        """测试注册错误处理器"""
        app = Flask(__name__)
        register_error_handlers(app)

        # 验证错误处理器已注册
        assert 400 in app.error_handler_spec[None]
        assert 404 in app.error_handler_spec[None]
        assert 405 in app.error_handler_spec[None]
        assert 500 in app.error_handler_spec[None]

    def test_404_error_handler(self):
        """测试404错误处理"""
        app = Flask(__name__)
        register_error_handlers(app)

        with app.test_client() as client:
            response = client.get("/nonexistent")
            assert response.status_code == 404
            data = response.get_json()
            assert data["success"] is False
            assert data["error"]["code"] == ErrorCode.RESOURCE_NOT_FOUND.value

    def test_405_error_handler(self):
        """测试405错误处理"""
        app = Flask(__name__)
        register_error_handlers(app)

        @app.route("/test", methods=["GET"])
        def test_route():
            return jsonify({"success": True})

        with app.test_client() as client:
            response = client.post("/test")
            assert response.status_code == 405
            data = response.get_json()
            assert data["success"] is False
            assert "不支持的请求方法" in data["error"]["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
