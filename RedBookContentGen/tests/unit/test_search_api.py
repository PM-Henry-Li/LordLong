#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索 API 接口测试
测试通用搜索接口的验证和响应
"""

import pytest
from flask import Flask
from web_app import create_app


@pytest.fixture
def app() -> Flask:
    """创建测试应用"""
    app = create_app("config/config.json")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app: Flask):
    """创建测试客户端"""
    return app.test_client()


class TestSearchAPI:
    """搜索 API 测试类"""
    
    def test_search_default_params(self, client):
        """测试默认参数的搜索请求"""
        response = client.get("/api/search")
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "data" in data
        assert "query" in data
        
        # 验证默认值
        assert data["query"]["page"] == 1
        assert data["query"]["page_size"] == 50
        assert data["query"]["sort_by"] == "created_at"
        assert data["query"]["sort_order"] == "desc"
        
        # 验证响应结构
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]
        assert "total_pages" in data["data"]
    
    def test_search_with_keyword(self, client):
        """测试带关键词的搜索"""
        response = client.get("/api/search?keyword=老北京")
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["query"]["keyword"] == "老北京"
    
    def test_search_with_pagination(self, client):
        """测试分页参数"""
        response = client.get("/api/search?page=2&page_size=20")
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["query"]["page"] == 2
        assert data["query"]["page_size"] == 20
    
    def test_search_with_time_range(self, client):
        """测试时间范围参数"""
        response = client.get(
            "/api/search?"
            "start_time=2026-02-01T00:00:00&"
            "end_time=2026-02-13T23:59:59"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["query"]["start_time"] == "2026-02-01T00:00:00"
        assert data["query"]["end_time"] == "2026-02-13T23:59:59"
    
    def test_search_with_sorting(self, client):
        """测试排序参数"""
        response = client.get("/api/search?sort_by=title&sort_order=asc")
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["query"]["sort_by"] == "title"
        assert data["query"]["sort_order"] == "asc"
    
    def test_search_invalid_page(self, client):
        """测试无效的页码"""
        response = client.get("/api/search?page=0")
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        
        # 验证错误详情
        errors = data["error"]["errors"]
        assert len(errors) > 0
        assert errors[0]["field"] == "page"
    
    def test_search_invalid_page_size(self, client):
        """测试无效的页面大小"""
        response = client.get("/api/search?page_size=500")
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        
        # 验证错误详情
        errors = data["error"]["errors"]
        assert len(errors) > 0
        assert errors[0]["field"] == "page_size"
        assert "200" in errors[0]["message"]
    
    def test_search_invalid_sort_order(self, client):
        """测试无效的排序顺序"""
        response = client.get("/api/search?sort_order=invalid")
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["success"] is False
        assert "error" in data
        
        # 验证错误详情
        errors = data["error"]["errors"]
        assert len(errors) > 0
        assert errors[0]["field"] == "sort_order"
    
    def test_search_invalid_time_format(self, client):
        """测试无效的时间格式"""
        response = client.get("/api/search?start_time=2026-02-01")
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["success"] is False
        assert "error" in data
        
        # 验证错误详情
        errors = data["error"]["errors"]
        assert len(errors) > 0
        assert errors[0]["field"] == "start_time"
        assert "YYYY-MM-DDTHH:MM:SS" in errors[0]["message"]
    
    def test_search_invalid_time_range(self, client):
        """测试无效的时间范围（开始时间晚于结束时间）"""
        response = client.get(
            "/api/search?"
            "start_time=2026-02-13T00:00:00&"
            "end_time=2026-02-01T00:00:00"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["success"] is False
        assert "error" in data
        
        # 验证错误消息
        errors = data["error"]["errors"]
        assert len(errors) > 0
        assert "开始时间" in str(errors[0]["message"])
    
    def test_search_sql_injection_prevention(self, client):
        """测试 SQL 注入防护"""
        dangerous_keywords = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
        ]
        
        for keyword in dangerous_keywords:
            response = client.get(f"/api/search?keyword={keyword}")
            
            assert response.status_code == 400
            data = response.get_json()
            
            assert data["success"] is False
            assert "error" in data
            assert "非法字符" in str(data["error"])
    
    def test_search_xss_prevention(self, client):
        """测试 XSS 攻击防护"""
        # 注意：SearchRequest 的 keyword 字段会检查危险字符
        # 但不会像 ContentGenerationRequest 那样检查 HTML 标签
        # 因为搜索关键词可能包含特殊字符
        
        # 测试包含单引号的关键词（应该被拒绝）
        response = client.get("/api/search?keyword=test'script")
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data["success"] is False
    
    def test_search_all_params(self, client):
        """测试所有参数组合"""
        response = client.get(
            "/api/search?"
            "keyword=老北京&"
            "page=1&"
            "page_size=20&"
            "start_time=2026-02-01T00:00:00&"
            "end_time=2026-02-13T23:59:59&"
            "sort_by=created_at&"
            "sort_order=desc"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["query"]["keyword"] == "老北京"
        assert data["query"]["page"] == 1
        assert data["query"]["page_size"] == 20
        assert data["query"]["start_time"] == "2026-02-01T00:00:00"
        assert data["query"]["end_time"] == "2026-02-13T23:59:59"
        assert data["query"]["sort_by"] == "created_at"
        assert data["query"]["sort_order"] == "desc"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
