#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证错误处理使用示例

演示如何使用 ValidationErrorHandler 处理 Pydantic 验证错误
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pydantic import ValidationError
from src.models.requests import (
    ContentGenerationRequest,
    ImageGenerationRequest,
    SearchRequest,
)
from src.models.validation_errors import format_validation_error
import json


def example_1_missing_required_field():
    """示例 1：缺少必填字段"""
    print("=" * 60)
    print("示例 1：缺少必填字段")
    print("=" * 60)
    
    try:
        # 尝试创建请求但不提供必填的 input_text
        request = ContentGenerationRequest()
    except ValidationError as e:
        # 使用错误处理器格式化错误
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_2_string_too_short():
    """示例 2：字符串过短"""
    print("=" * 60)
    print("示例 2：字符串过短")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(input_text="短")
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_3_value_out_of_range():
    """示例 3：数值超出范围"""
    print("=" * 60)
    print("示例 3：数值超出范围")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(
            input_text="这是一个测试文本，用于验证数值范围",
            count=20,  # 超过最大值 10
            temperature=3.0,  # 超过最大值 2.0
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_4_invalid_enum():
    """示例 4：无效的枚举值"""
    print("=" * 60)
    print("示例 4：无效的枚举值")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(
            input_text="这是一个测试文本，用于验证枚举值",
            style="invalid_style"
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_5_xss_attack():
    """示例 5：XSS 攻击检测"""
    print("=" * 60)
    print("示例 5：XSS 攻击检测")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(
            input_text="<script>alert('xss')</script>测试文本"
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_6_sensitive_word():
    """示例 6：敏感词检测"""
    print("=" * 60)
    print("示例 6：敏感词检测")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(
            input_text="这是一个包含暴力内容的测试文本"
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_7_timestamp_format():
    """示例 7：时间戳格式错误"""
    print("=" * 60)
    print("示例 7：时间戳格式错误")
    print("=" * 60)
    
    try:
        request = ImageGenerationRequest(
            prompt="测试提示词",
            timestamp="2026-02-13"  # 错误格式
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_8_time_range():
    """示例 8：时间范围错误"""
    print("=" * 60)
    print("示例 8：时间范围错误")
    print("=" * 60)
    
    try:
        request = SearchRequest(
            start_time="2026-02-13T14:30:00",
            end_time="2026-02-12T14:30:00"  # 结束时间早于开始时间
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_9_sql_injection():
    """示例 9：SQL 注入检测"""
    print("=" * 60)
    print("示例 9：SQL 注入检测")
    print("=" * 60)
    
    try:
        request = SearchRequest(
            keyword="test' OR '1'='1"
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_10_successful_validation():
    """示例 10：验证成功"""
    print("=" * 60)
    print("示例 10：验证成功")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(
            input_text="记得小时候，老北京的胡同里总是充满了生活的气息，邻里之间互相帮助，孩子们在胡同里嬉戏玩耍。",
            count=3,
            style="retro_chinese",
            temperature=0.8,
        )
        print("✅ 验证成功！")
        print(f"输入文本长度：{len(request.input_text)} 字符")
        print(f"生成数量：{request.count}")
        print(f"生成风格：{request.style}")
        print(f"生成温度：{request.temperature}")
    except ValidationError as e:
        error_response = format_validation_error(e)
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
    
    print()


def example_11_web_api_integration():
    """示例 11：Web API 集成示例"""
    print("=" * 60)
    print("示例 11：Web API 集成示例")
    print("=" * 60)
    
    # 模拟 Flask 路由处理
    def generate_content_api(request_data: dict):
        """
        内容生成 API 端点
        
        Args:
            request_data: 请求数据字典
            
        Returns:
            API 响应
        """
        try:
            # 验证请求数据
            request = ContentGenerationRequest(**request_data)
            
            # 如果验证通过，执行业务逻辑
            return {
                "success": True,
                "data": {
                    "message": "内容生成任务已创建",
                    "task_id": "task_123456",
                }
            }
        
        except ValidationError as e:
            # 返回友好的错误响应
            return format_validation_error(e)
    
    # 测试有效请求
    print("测试有效请求：")
    valid_request = {
        "input_text": "老北京的胡同文化是中国传统文化的重要组成部分",
        "count": 2,
    }
    response = generate_content_api(valid_request)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print()
    
    # 测试无效请求
    print("测试无效请求：")
    invalid_request = {
        "input_text": "短",
        "count": 20,
    }
    response = generate_content_api(invalid_request)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    
    print()


def example_12_error_field_location():
    """示例 12：错误字段定位"""
    print("=" * 60)
    print("示例 12：错误字段定位")
    print("=" * 60)
    
    try:
        request = ContentGenerationRequest(
            input_text="短",
            count=20,
            temperature=-1.0,
            style="invalid",
        )
    except ValidationError as e:
        error_response = format_validation_error(e)
        
        print(f"总共发现 {error_response['error']['total_errors']} 个错误：\n")
        
        for i, error in enumerate(error_response['error']['errors'], 1):
            print(f"错误 {i}:")
            print(f"  字段路径: {error['field']}")
            print(f"  字段名称: {error['field_name']}")
            print(f"  错误类型: {error['error_type']}")
            print(f"  错误消息: {error['message']}")
            print(f"  修复建议:")
            for suggestion in error['suggestions']:
                print(f"    - {suggestion}")
            print()
    
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("验证错误处理使用示例")
    print("=" * 60 + "\n")
    
    example_1_missing_required_field()
    example_2_string_too_short()
    example_3_value_out_of_range()
    example_4_invalid_enum()
    example_5_xss_attack()
    example_6_sensitive_word()
    example_7_timestamp_format()
    example_8_time_range()
    example_9_sql_injection()
    example_10_successful_validation()
    example_11_web_api_integration()
    example_12_error_field_location()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
