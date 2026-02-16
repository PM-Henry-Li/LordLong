#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket 进度推送准确性测试

测试任务 13.3.1：验证进度推送准确性
- 验证进度百分比计算
- 测试各阶段进度更新
- 测试性能影响

需求引用：需求 3.5.1（进度反馈）
"""

import pytest
import time
from unittest.mock import Mock, patch, call
from src.core.progress_manager import ProgressManager, TaskStatus


class TestProgressAccuracy:
    """进度推送准确性测试类"""
    
    @pytest.fixture
    def progress_manager_with_socketio(self):
        """创建带 SocketIO 的进度管理器实例"""
        mock_socketio = Mock()
        return ProgressManager(socketio=mock_socketio), mock_socketio
    
    # ========== 进度百分比计算测试 ==========
    
    def test_progress_percentage_calculation_basic(self, progress_manager_with_socketio):
        """测试基本进度百分比计算"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 测试不同的进度值
        test_cases = [0, 25, 50, 75, 100]
        
        for expected_progress in test_cases:
            progress_manager.update_progress(task_id, expected_progress)
            actual_progress = progress_manager.get_task_progress(task_id)
            
            assert actual_progress == expected_progress, \
                f"进度计算错误：期望 {expected_progress}，实际 {actual_progress}"
    
    def test_progress_percentage_calculation_boundaries(self, progress_manager_with_socketio):
        """测试进度百分比边界值"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 测试边界值
        test_cases = [
            (-100, 0, "负数应该被限制为 0"),
            (-1, 0, "负数应该被限制为 0"),
            (0, 0, "0 应该保持为 0"),
            (100, 100, "100 应该保持为 100"),
            (101, 100, "超过 100 应该被限制为 100"),
            (200, 100, "超过 100 应该被限制为 100"),
        ]
        
        for input_progress, expected_progress, message in test_cases:
            progress_manager.update_progress(task_id, input_progress)
            actual_progress = progress_manager.get_task_progress(task_id)
            
            assert actual_progress == expected_progress, \
                f"{message}：输入 {input_progress}，期望 {expected_progress}，实际 {actual_progress}"
    
    def test_progress_percentage_calculation_precision(self, progress_manager_with_socketio):
        """测试进度百分比精度（精确到 1%）"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 测试所有 0-100 的整数值
        for expected_progress in range(0, 101):
            progress_manager.update_progress(task_id, expected_progress)
            actual_progress = progress_manager.get_task_progress(task_id)
            
            assert actual_progress == expected_progress, \
                f"进度精度错误：期望 {expected_progress}%，实际 {actual_progress}%"
    
    def test_progress_percentage_incremental(self, progress_manager_with_socketio):
        """测试进度递增计算"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 模拟实际场景：进度逐步递增
        progress_steps = [0, 10, 20, 35, 50, 65, 80, 90, 100]
        
        for expected_progress in progress_steps:
            progress_manager.update_progress(task_id, expected_progress)
            actual_progress = progress_manager.get_task_progress(task_id)
            
            assert actual_progress == expected_progress, \
                f"递增进度错误：期望 {expected_progress}%，实际 {actual_progress}%"
    
    # ========== 各阶段进度更新测试 ==========
    
    def test_stage_progress_content_generation(self, progress_manager_with_socketio):
        """测试内容生成阶段进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 模拟内容生成阶段（0-20%）
        progress_manager.update_progress(
            task_id=task_id,
            progress=0,
            status=TaskStatus.STARTED,
            message="开始生成内容"
        )
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=10,
            status=TaskStatus.GENERATING_CONTENT,
            message="正在生成标题"
        )
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=20,
            status=TaskStatus.GENERATING_CONTENT,
            message="内容生成完成"
        )
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["progress"] == 20
        assert task_info["status"] == TaskStatus.GENERATING_CONTENT
        
        # 验证 WebSocket 事件被触发
        assert mock_socketio.emit.call_count >= 3
    
    def test_stage_progress_image_generation(self, progress_manager_with_socketio):
        """测试图片生成阶段进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 模拟图片生成阶段（20-100%）
        total_images = 5
        base_progress = 20
        image_progress_range = 80  # 100 - 20
        
        for i in range(total_images):
            current_progress = base_progress + int((i + 1) * image_progress_range / total_images)
            
            progress_manager.update_progress(
                task_id=task_id,
                progress=current_progress,
                status=TaskStatus.GENERATING_IMAGE,
                message=f"正在生成第 {i + 1}/{total_images} 张图片",
                details={
                    "current_image": i + 1,
                    "total_images": total_images
                }
            )
            
            task_info = progress_manager.get_task_info(task_id)
            assert task_info["progress"] == current_progress
            assert task_info["details"]["current_image"] == i + 1
    
    def test_stage_progress_completion(self, progress_manager_with_socketio):
        """测试任务完成阶段进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 完成任务
        result = {"titles": ["标题1"], "content": "内容", "images": ["image1.jpg"]}
        progress_manager.complete_task(task_id, result=result)
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["progress"] == 100
        assert task_info["status"] == TaskStatus.COMPLETED
        assert task_info["details"]["result"] == result
    
    def test_stage_progress_full_workflow(self, progress_manager_with_socketio):
        """测试完整工作流的进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 完整工作流进度
        workflow_stages = [
            (0, TaskStatus.STARTED, "任务开始"),
            (5, TaskStatus.GENERATING_CONTENT, "读取输入文件"),
            (10, TaskStatus.GENERATING_CONTENT, "生成标题"),
            (15, TaskStatus.GENERATING_CONTENT, "生成正文"),
            (20, TaskStatus.GENERATING_CONTENT, "生成图片提示词"),
            (36, TaskStatus.GENERATING_IMAGE, "生成第 1/5 张图片"),
            (52, TaskStatus.GENERATING_IMAGE, "生成第 2/5 张图片"),
            (68, TaskStatus.GENERATING_IMAGE, "生成第 3/5 张图片"),
            (84, TaskStatus.GENERATING_IMAGE, "生成第 4/5 张图片"),
            (100, TaskStatus.COMPLETED, "任务完成"),
        ]
        
        for expected_progress, expected_status, message in workflow_stages:
            if expected_status == TaskStatus.COMPLETED:
                progress_manager.complete_task(task_id)
            else:
                progress_manager.update_progress(
                    task_id=task_id,
                    progress=expected_progress,
                    status=expected_status,
                    message=message
                )
            
            task_info = progress_manager.get_task_info(task_id)
            assert task_info["progress"] == expected_progress, \
                f"阶段 '{message}' 进度错误：期望 {expected_progress}%，实际 {task_info['progress']}%"
            assert task_info["status"] == expected_status, \
                f"阶段 '{message}' 状态错误：期望 {expected_status}，实际 {task_info['status']}"
    
    def test_stage_progress_error_handling(self, progress_manager_with_socketio):
        """测试错误处理阶段进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 模拟任务进行到一半失败
        progress_manager.update_progress(task_id, 50, status=TaskStatus.GENERATING_IMAGE)
        
        # 任务失败
        error_message = "API 调用失败"
        progress_manager.fail_task(task_id, error_message)
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.FAILED
        assert task_info["progress"] == 50  # 进度保持在失败时的值
        assert task_info["message"] == error_message
    
    # ========== WebSocket 事件推送测试 ==========
    
    def test_websocket_event_emission(self, progress_manager_with_socketio):
        """测试 WebSocket 事件推送"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 清空之前的调用记录
        mock_socketio.emit.reset_mock()
        
        # 更新进度
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            status=TaskStatus.GENERATING_CONTENT,
            message="测试消息"
        )
        
        # 验证 emit 被调用
        assert mock_socketio.emit.called
        
        # 验证调用参数
        call_args = mock_socketio.emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == "progress"
        assert event_data["task_id"] == task_id
        assert event_data["progress"] == 50
        assert event_data["status"] == TaskStatus.GENERATING_CONTENT.value
        assert event_data["message"] == "测试消息"
        assert "timestamp" in event_data
    
    def test_websocket_event_data_structure(self, progress_manager_with_socketio):
        """测试 WebSocket 事件数据结构"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        mock_socketio.emit.reset_mock()
        
        # 更新进度并包含详细信息
        details = {
            "current_image": 3,
            "total_images": 5,
            "estimated_time": 120
        }
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=60,
            status=TaskStatus.GENERATING_IMAGE,
            message="生成图片中",
            details=details
        )
        
        # 获取事件数据
        event_data = mock_socketio.emit.call_args[0][1]
        
        # 验证数据结构完整性
        required_fields = ["task_id", "status", "progress", "message", "details", "timestamp"]
        for field in required_fields:
            assert field in event_data, f"事件数据缺少字段: {field}"
        
        # 验证详细信息
        assert event_data["details"]["current_image"] == 3
        assert event_data["details"]["total_images"] == 5
        assert event_data["details"]["estimated_time"] == 120
    
    def test_websocket_event_room_targeting(self, progress_manager_with_socketio):
        """测试 WebSocket 事件房间定向"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        mock_socketio.emit.reset_mock()
        
        progress_manager.update_progress(task_id, 50)
        
        # 验证事件发送到正确的房间
        call_kwargs = mock_socketio.emit.call_args[1]
        assert call_kwargs["room"] == task_id
        assert call_kwargs["namespace"] == "/progress"
    
    def test_websocket_event_no_emit_when_disabled(self, progress_manager_with_socketio):
        """测试禁用事件推送时不发送 WebSocket 事件"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        mock_socketio.emit.reset_mock()
        
        # 禁用事件推送
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            emit_event=False
        )
        
        # 验证 emit 未被调用
        assert not mock_socketio.emit.called
    
    # ========== 性能影响测试 ==========
    
    def test_performance_single_update(self, progress_manager_with_socketio):
        """测试单次进度更新的性能"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 测量单次更新时间
        start_time = time.time()
        progress_manager.update_progress(task_id, 50)
        elapsed_time = time.time() - start_time
        
        # 单次更新应该在 10ms 内完成
        assert elapsed_time < 0.01, \
            f"单次进度更新耗时过长: {elapsed_time * 1000:.2f}ms"
    
    def test_performance_multiple_updates(self, progress_manager_with_socketio):
        """测试多次进度更新的性能"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 测量 100 次更新的总时间
        update_count = 100
        start_time = time.time()
        
        for i in range(update_count):
            progress_manager.update_progress(task_id, i % 101)
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / update_count
        
        # 平均每次更新应该在 5ms 内完成
        assert avg_time < 0.005, \
            f"平均进度更新耗时过长: {avg_time * 1000:.2f}ms"
        
        # 总时间应该在 1 秒内完成
        assert elapsed_time < 1.0, \
            f"100 次更新总耗时过长: {elapsed_time:.2f}s"
    
    def test_performance_concurrent_tasks(self, progress_manager_with_socketio):
        """测试并发任务的性能影响"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 创建多个任务
        task_count = 10
        task_ids = [progress_manager.create_task() for _ in range(task_count)]
        
        # 测量并发更新时间
        start_time = time.time()
        
        for task_id in task_ids:
            for progress in range(0, 101, 10):
                progress_manager.update_progress(task_id, progress)
        
        elapsed_time = time.time() - start_time
        
        # 10 个任务，每个 11 次更新，总共 110 次更新
        total_updates = task_count * 11
        avg_time = elapsed_time / total_updates
        
        # 平均每次更新应该在 5ms 内完成
        assert avg_time < 0.005, \
            f"并发场景下平均更新耗时过长: {avg_time * 1000:.2f}ms"
    
    def test_performance_websocket_overhead(self, progress_manager_with_socketio):
        """测试 WebSocket 推送的性能开销"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 测量不推送事件的时间
        start_time = time.time()
        for i in range(100):
            progress_manager.update_progress(task_id, i % 101, emit_event=False)
        time_without_emit = time.time() - start_time
        
        # 重置任务
        progress_manager.delete_task(task_id)
        task_id = progress_manager.create_task()
        
        # 测量推送事件的时间
        start_time = time.time()
        for i in range(100):
            progress_manager.update_progress(task_id, i % 101, emit_event=True)
        time_with_emit = time.time() - start_time
        
        # WebSocket 推送的开销应该小于 50%
        overhead = (time_with_emit - time_without_emit) / time_without_emit
        assert overhead < 0.5, \
            f"WebSocket 推送开销过大: {overhead * 100:.1f}%"
    
    def test_performance_memory_usage(self, progress_manager_with_socketio):
        """测试进度管理器的内存使用"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 创建大量任务
        task_count = 100
        task_ids = []
        
        for i in range(task_count):
            task_id = progress_manager.create_task()
            task_ids.append(task_id)
            
            # 更新进度
            progress_manager.update_progress(
                task_id=task_id,
                progress=50,
                message=f"任务 {i}",
                details={"index": i}
            )
        
        # 验证所有任务都被正确存储
        assert len(progress_manager.tasks) == task_count
        
        # 清理任务
        for task_id in task_ids:
            progress_manager.delete_task(task_id)
        
        # 验证任务被正确清理
        assert len(progress_manager.tasks) == 0
    
    def test_performance_websocket_message_delay(self, progress_manager_with_socketio):
        """测试 WebSocket 消息延迟（目标 < 100ms）"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 记录更新时间和 emit 调用时间
        delays = []
        
        for i in range(10):
            mock_socketio.emit.reset_mock()
            
            start_time = time.time()
            progress_manager.update_progress(task_id, i * 10)
            
            # 验证 emit 被调用
            assert mock_socketio.emit.called
            
            # 计算延迟
            delay = time.time() - start_time
            delays.append(delay)
        
        # 计算平均延迟
        avg_delay = sum(delays) / len(delays)
        max_delay = max(delays)
        
        # 平均延迟应该小于 10ms
        assert avg_delay < 0.01, \
            f"平均消息延迟过大: {avg_delay * 1000:.2f}ms"
        
        # 最大延迟应该小于 100ms（需求目标）
        assert max_delay < 0.1, \
            f"最大消息延迟超过目标: {max_delay * 1000:.2f}ms"
    
    # ========== 边界情况和异常测试 ==========
    
    def test_update_nonexistent_task(self, progress_manager_with_socketio):
        """测试更新不存在的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 不应该抛出异常
        progress_manager.update_progress("nonexistent_id", 50)
        
        # 验证没有发送事件
        mock_socketio.emit.reset_mock()
        progress_manager.update_progress("nonexistent_id", 50)
        assert not mock_socketio.emit.called
    
    def test_update_cancelled_task_progress(self, progress_manager_with_socketio):
        """测试更新已取消任务的进度"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 更新进度到 30%
        progress_manager.update_progress(task_id, 30)
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        mock_socketio.emit.reset_mock()
        
        # 尝试更新进度（应该被忽略）
        progress_manager.update_progress(task_id, 50)
        
        # 验证进度没有更新
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["progress"] == 30  # 保持取消时的进度
        assert task_info["status"] == TaskStatus.CANCELLED
        
        # 验证没有发送新的进度事件
        assert not mock_socketio.emit.called
    
    def test_rapid_progress_updates(self, progress_manager_with_socketio):
        """测试快速连续的进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 快速连续更新进度
        for i in range(100):
            progress_manager.update_progress(task_id, i)
        
        # 验证最终进度正确
        final_progress = progress_manager.get_task_progress(task_id)
        assert final_progress == 99
        
        # 验证所有更新都触发了事件
        assert mock_socketio.emit.call_count >= 100


class TestProgressCalculationScenarios:
    """进度计算场景测试"""
    
    @pytest.fixture
    def progress_manager(self):
        """创建进度管理器实例"""
        return ProgressManager()
    
    def test_content_generation_progress_distribution(self, progress_manager):
        """测试内容生成阶段的进度分配（0-20%）"""
        task_id = progress_manager.create_task()
        
        # 内容生成阶段的子步骤
        steps = [
            (0, "开始"),
            (5, "读取输入"),
            (10, "生成标题"),
            (15, "生成正文"),
            (20, "生成提示词"),
        ]
        
        for expected_progress, step_name in steps:
            progress_manager.update_progress(
                task_id=task_id,
                progress=expected_progress,
                message=step_name
            )
            
            actual_progress = progress_manager.get_task_progress(task_id)
            assert actual_progress == expected_progress, \
                f"步骤 '{step_name}' 进度错误"
    
    def test_image_generation_progress_distribution(self, progress_manager):
        """测试图片生成阶段的进度分配（20-100%）"""
        task_id = progress_manager.create_task()
        
        # 生成 5 张图片，每张占 16%（80% / 5）
        total_images = 5
        base_progress = 20
        progress_per_image = 16
        
        for i in range(total_images):
            expected_progress = base_progress + (i + 1) * progress_per_image
            
            progress_manager.update_progress(
                task_id=task_id,
                progress=expected_progress,
                message=f"图片 {i + 1}/{total_images}"
            )
            
            actual_progress = progress_manager.get_task_progress(task_id)
            assert actual_progress == expected_progress, \
                f"图片 {i + 1} 进度错误"
    
    def test_variable_image_count_progress(self, progress_manager):
        """测试不同图片数量的进度计算"""
        test_cases = [
            (1, [100]),  # 1 张图片
            (3, [47, 73, 100]),  # 3 张图片
            (5, [36, 52, 68, 84, 100]),  # 5 张图片
            (10, [28, 36, 44, 52, 60, 68, 76, 84, 92, 100]),  # 10 张图片
        ]
        
        for image_count, expected_progresses in test_cases:
            task_id = progress_manager.create_task()
            
            base_progress = 20
            progress_range = 80
            
            for i in range(image_count):
                calculated_progress = base_progress + int((i + 1) * progress_range / image_count)
                
                progress_manager.update_progress(
                    task_id=task_id,
                    progress=calculated_progress
                )
                
                actual_progress = progress_manager.get_task_progress(task_id)
                expected_progress = expected_progresses[i]
                
                # 允许 ±1% 的误差（由于整数除法）
                assert abs(actual_progress - expected_progress) <= 1, \
                    f"{image_count} 张图片，第 {i + 1} 张进度错误：期望 {expected_progress}，实际 {actual_progress}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

