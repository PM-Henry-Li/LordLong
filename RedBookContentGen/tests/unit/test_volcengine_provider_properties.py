#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
火山引擎图片生成服务提供商属性测试

使用基于属性的测试（Property-Based Testing）验证 VolcengineImageProvider 的通用属性。
每个属性测试运行至少 100 次迭代，使用随机生成的输入来发现边界情况和异常行为。
"""

import sys
from pathlib import Path
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from hypothesis import given, strategies as st, settings, assume
import requests

from src.image_providers.volcengine_provider import VolcengineImageProvider
from src.core.config_manager import ConfigManager
from src.core.logger import Logger


# ============================================================================
# 测试辅助函数
# ============================================================================

def create_test_provider(max_retries: int = 3) -> VolcengineImageProvider:
    """
    创建测试用的 VolcengineImageProvider 实例
    
    Args:
        max_retries: 最大重试次数
        
    Returns:
        VolcengineImageProvider 实例
    """
    config_manager = ConfigManager()
    config_manager.set("volcengine.access_key_id", "test_access_key_id")
    config_manager.set("volcengine.secret_access_key", "test_secret_access_key")
    config_manager.set("volcengine.endpoint", "https://visual.volcengineapi.com")
    config_manager.set("volcengine.service", "cv")
    config_manager.set("volcengine.region", "cn-north-1")
    config_manager.set("volcengine.model", "general_v2")
    config_manager.set("volcengine.max_retries", max_retries)
    
    Logger.initialize(config_manager)
    
    return VolcengineImageProvider(
        config_manager=config_manager,
        logger=Logger,
        rate_limiter=None,
        cache=None
    )


# ============================================================================
# 属性 10: 尺寸参数传递
# ============================================================================

@given(
    prompt=st.text(min_size=1, max_size=100),
    width=st.integers(min_value=256, max_value=2048),
    height=st.integers(min_value=256, max_value=2048)
)
@settings(max_examples=100, deadline=None)
def test_property_10_size_parameter_passing(prompt, width, height):
    """
    Feature: volcengine-jimeng-integration
    Property 10: 尺寸参数传递
    
    **验证需求: 3.3**
    
    对于任何指定的图片尺寸参数，该参数应该正确传递到 API 请求中。
    
    验证策略:
    1. 使用随机生成的提示词和尺寸参数
    2. Mock API 调用
    3. 验证请求体中的 width 和 height 字段与输入参数匹配
    """
    provider = create_test_provider()
    size = f"{width}*{height}"
    
    with patch('requests.post') as mock_post:
        # Mock 成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 10000,
            "data": {"task_id": "test_task_id"}
        }
        mock_post.return_value = mock_response
        
        # 调用 _create_task
        task_id = provider._create_task(prompt, size)
        
        # 验证 API 被调用
        assert mock_post.called, "API 应该被调用"
        
        # 获取请求参数
        call_args = mock_post.call_args
        request_body = json.loads(call_args[1]['data'])
        
        # 验证尺寸参数正确传递
        assert request_body['width'] == width, f"宽度应为 {width}，实际为 {request_body['width']}"
        assert request_body['height'] == height, f"高度应为 {height}，实际为 {request_body['height']}"
        assert task_id == "test_task_id", "应该返回任务 ID"


# ============================================================================
# 属性 11: 轮询终止条件
# ============================================================================

@given(
    status=st.sampled_from(["success", "failed", "processing"]),
    max_wait=st.integers(min_value=5, max_value=30)
)
@settings(max_examples=100, deadline=None)
def test_property_11_polling_termination_conditions(status, max_wait):
    """
    Feature: volcengine-jimeng-integration
    Property 11: 轮询终止条件
    
    **验证需求: 3.4**
    
    对于任何图片生成任务，轮询应该在以下条件之一满足时终止：
    1. 任务成功（status == "success"）
    2. 任务失败（status == "failed"）
    3. 达到超时时间
    
    验证策略:
    1. Mock API 返回不同的任务状态
    2. 验证轮询在正确条件下终止
    3. 验证返回值符合预期
    """
    provider = create_test_provider()
    task_id = "test_task_id"
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        
        if status == "success":
            # 任务成功，应该返回图片 URL
            mock_response.json.return_value = {
                "code": 10000,
                "data": {
                    "task_id": task_id,
                    "status": "success",
                    "image_urls": ["https://example.com/image.jpg"],
                    "progress": 100
                }
            }
            mock_get.return_value = mock_response
            
            result = provider._poll_status(task_id, max_wait=max_wait)
            assert result == "https://example.com/image.jpg", "成功时应该返回图片 URL"
            
        elif status == "failed":
            # 任务失败，应该返回 None
            mock_response.json.return_value = {
                "code": 10000,
                "data": {
                    "task_id": task_id,
                    "status": "failed",
                    "progress": 0
                }
            }
            mock_get.return_value = mock_response
            
            result = provider._poll_status(task_id, max_wait=max_wait)
            assert result is None, "失败时应该返回 None"
            
        elif status == "processing":
            # 任务处理中，超时后应该返回 None
            mock_response.json.return_value = {
                "code": 10000,
                "data": {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": 50
                }
            }
            mock_get.return_value = mock_response
            
            # 使用较短的超时时间
            result = provider._poll_status(task_id, max_wait=1)
            assert result is None, "超时时应该返回 None"


# ============================================================================
# 属性 12: 图片保存完整性
# ============================================================================

@given(
    prompt=st.text(min_size=1, max_size=100),
    size=st.sampled_from(["1024*1365", "1080*1080", "512*512"])
)
@settings(max_examples=50, deadline=None)
def test_property_12_image_save_integrity(prompt, size):
    """
    Feature: volcengine-jimeng-integration
    Property 12: 图片保存完整性
    
    **验证需求: 3.5**
    
    对于任何成功生成的图片，图片 URL 应该被正确返回。
    
    注意: 由于我们不实际下载和保存图片，这里只验证 URL 的返回。
    实际的文件保存由 ImageGenerator 处理。
    
    验证策略:
    1. Mock 完整的图片生成流程
    2. 验证返回的图片 URL 正确
    """
    provider = create_test_provider()
    expected_url = "https://example.com/generated_image.jpg"
    
    with patch.object(provider, '_create_task') as mock_create:
        with patch.object(provider, '_poll_status') as mock_poll:
            mock_create.return_value = "test_task_id"
            mock_poll.return_value = expected_url
            
            result = provider.generate(prompt, size)
            
            # 验证返回的 URL 正确
            assert result == expected_url, f"应该返回图片 URL: {expected_url}"
            assert mock_create.called, "_create_task 应该被调用"
            assert mock_poll.called, "_poll_status 应该被调用"


# ============================================================================
# 属性 13: API 失败重试
# ============================================================================

@given(
    error_type=st.sampled_from(["timeout", "connection", "http_500", "http_502"])
)
@settings(max_examples=100, deadline=None)
def test_property_13_api_failure_retry(error_type):
    """
    Feature: volcengine-jimeng-integration
    Property 13: API 失败重试
    
    **验证需求: 3.6**
    
    对于任何 API 调用失败，系统应该记录错误信息，并在错误可重试时进行重试。
    
    验证策略:
    1. Mock 不同类型的 API 错误
    2. 验证可重试错误会触发重试
    3. 验证错误信息被正确记录
    """
    provider = create_test_provider(max_retries=3)
    
    # 创建对应的错误
    if error_type == "timeout":
        error = requests.exceptions.Timeout("Connection timeout")
    elif error_type == "connection":
        error = requests.exceptions.ConnectionError("Connection refused")
    elif error_type == "http_500":
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError(response=response)
    elif error_type == "http_502":
        response = Mock()
        response.status_code = 502
        error = requests.exceptions.HTTPError(response=response)
    
    # 测试错误处理
    should_retry, error_msg = provider._handle_api_error(error, retry_count=0)
    
    # 验证可重试错误返回 True
    assert should_retry == True, f"{error_type} 错误应该可以重试"
    assert error_msg is not None, "应该返回错误消息"
    assert len(error_msg) > 0, "错误消息不应为空"


# ============================================================================
# 属性 17: 可重试错误重试次数
# ============================================================================

@given(
    retry_count=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_property_17_retryable_error_retry_count(retry_count):
    """
    Feature: volcengine-jimeng-integration
    Property 17: 可重试错误重试次数
    
    **验证需求: 5.2**
    
    对于任何可重试的错误（网络超时、5xx 错误），系统应该重试最多 3 次。
    
    验证策略:
    1. 使用不同的重试计数
    2. 验证在重试次数 < 3 时返回 True
    3. 验证在重试次数 >= 3 时返回 False
    """
    provider = create_test_provider(max_retries=3)
    
    # 创建可重试错误（超时）
    error = requests.exceptions.Timeout("Connection timeout")
    
    # 测试错误处理
    should_retry, error_msg = provider._handle_api_error(error, retry_count=retry_count)
    
    # 验证重试逻辑
    if retry_count < 3:
        assert should_retry == True, f"重试次数 {retry_count} < 3 时应该重试"
    else:
        assert should_retry == False, f"重试次数 {retry_count} >= 3 时不应该重试"


# ============================================================================
# 属性 18: 不可重试错误立即返回
# ============================================================================

@given(
    status_code=st.sampled_from([400, 401, 403, 404]),
    retry_count=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_property_18_non_retryable_error_immediate_return(status_code, retry_count):
    """
    Feature: volcengine-jimeng-integration
    Property 18: 不可重试错误立即返回
    
    **验证需求: 5.3**
    
    对于任何不可重试的错误（认证失败、4xx 错误），系统应该立即返回错误而不重试。
    
    验证策略:
    1. 使用不同的 4xx 状态码
    2. 使用不同的重试计数
    3. 验证无论重试次数如何，都返回 False（不重试）
    """
    provider = create_test_provider(max_retries=3)
    
    # 创建不可重试错误（4xx 客户端错误）
    response = Mock()
    response.status_code = status_code
    error = requests.exceptions.HTTPError(response=response)
    
    # 测试错误处理
    should_retry, error_msg = provider._handle_api_error(error, retry_count=retry_count)
    
    # 验证不可重试错误立即返回 False
    assert should_retry == False, f"{status_code} 错误不应该重试（重试次数: {retry_count}）"
    assert "客户端错误" in error_msg, f"错误消息应包含'客户端错误': {error_msg}"


# ============================================================================
# 属性 19: 重试耗尽错误返回
# ============================================================================

@given(
    error_type=st.sampled_from(["timeout", "connection", "http_500"])
)
@settings(max_examples=100, deadline=None)
def test_property_19_retry_exhausted_error_return(error_type):
    """
    Feature: volcengine-jimeng-integration
    Property 19: 重试耗尽错误返回
    
    **验证需求: 5.4**
    
    对于任何重试次数耗尽的情况，系统应该返回最后一次的错误信息。
    
    验证策略:
    1. 使用可重试错误
    2. 设置重试次数为最大值（3）
    3. 验证返回 False（不再重试）
    4. 验证返回有效的错误消息
    """
    provider = create_test_provider(max_retries=3)
    
    # 创建可重试错误
    if error_type == "timeout":
        error = requests.exceptions.Timeout("Connection timeout")
        expected_msg = "网络超时"
    elif error_type == "connection":
        error = requests.exceptions.ConnectionError("Connection refused")
        expected_msg = "连接失败"
    elif error_type == "http_500":
        response = Mock()
        response.status_code = 500
        error = requests.exceptions.HTTPError(response=response)
        expected_msg = "服务器错误"
    
    # 测试重试耗尽的情况（retry_count = 3）
    should_retry, error_msg = provider._handle_api_error(error, retry_count=3)
    
    # 验证不再重试
    assert should_retry == False, "重试次数耗尽时不应该重试"
    
    # 验证返回有效的错误消息
    assert error_msg is not None, "应该返回错误消息"
    assert len(error_msg) > 0, "错误消息不应为空"
    assert expected_msg in error_msg, f"错误消息应包含 '{expected_msg}': {error_msg}"


# ============================================================================
# 属性 20: 指数退避策略
# ============================================================================

@given(
    prompt=st.text(min_size=1, max_size=50),
    size=st.sampled_from(["1024*1365", "1080*1080"])
)
@settings(max_examples=50, deadline=None)
def test_property_20_exponential_backoff_strategy(prompt, size):
    """
    Feature: volcengine-jimeng-integration
    Property 20: 指数退避策略
    
    **验证需求: 5.5**
    
    对于任何重试序列，重试之间的时间间隔应该遵循指数退避策略
    （每次重试的等待时间是前一次的 2 倍：1s, 2s, 4s）。
    
    验证策略:
    1. Mock API 调用使其失败（可重试错误）
    2. 记录每次重试之间的时间间隔
    3. 验证时间间隔符合指数退避策略（允许一定误差）
    """
    provider = create_test_provider(max_retries=3)
    
    # 记录 sleep 调用
    sleep_times = []
    
    def mock_sleep(seconds):
        sleep_times.append(seconds)
    
    with patch('time.sleep', side_effect=mock_sleep):
        with patch('requests.post') as mock_post:
            # Mock 超时错误
            mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")
            
            # 调用 _create_task（会触发重试）
            result = provider._create_task(prompt, size)
            
            # 验证返回 None（失败）
            assert result is None, "重试耗尽后应该返回 None"
            
            # 验证重试次数（应该重试 3 次）
            assert len(sleep_times) == 3, f"应该重试 3 次，实际重试 {len(sleep_times)} 次"
            
            # 验证指数退避策略：1s, 2s, 4s
            expected_times = [1, 2, 4]
            for i, (actual, expected) in enumerate(zip(sleep_times, expected_times)):
                assert actual == expected, f"第 {i+1} 次重试等待时间应为 {expected}s，实际为 {actual}s"


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    # 运行所有属性测试
    pytest.main([__file__, "-v", "--tb=short"])
