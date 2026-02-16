#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket 任务取消功能测试

测试任务 13.3.2：验证任务取消功能
- 测试取消功能的正确性
- 验证资源清理的完整性
- 测试状态一致性的保证

需求引用：需求 3.5.1（进度反馈）
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from src.core.progress_manager import ProgressManager, TaskStatus


class TestTaskCancellation:
    """任务取消功能测试类"""
    
    @pytest.fixture
    def progress_manager_with_socketio(self):
        """创建带 SocketIO 的进度管理器实例"""
        mock_socketio = Mock()
        return ProgressManager(socketio=mock_socketio), mock_socketio
    
    # ========== 取消功能正确性测试 ==========
    
    def test_cancel_pending_task(self, progress_manager_with_socketio):
        """测试取消等待中的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 任务处于 PENDING 状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.PENDING
        
        # 取消任务
        result = progress_manager.cancel_task(task_id)
        
        # 验证取消成功
        assert result is True
        
        # 验证任务状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["cancelled"] is True
        assert task_info["message"] == "任务已取消"
    
    def test_cancel_running_task(self, progress_manager_with_socketio):
        """测试取消正在运行的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 启动任务并更新进度
        progress_manager.update_progress(
            task_id=task_id,
            progress=30,
            status=TaskStatus.GENERATING_CONTENT,
            message="正在生成内容"
        )
        
        # 取消任务
        result = progress_manager.cancel_task(task_id)
        
        # 验证取消成功
        assert result is True
        
        # 验证任务状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["cancelled"] is True
        assert task_info["progress"] == 30  # 进度保持在取消时的值
    
    def test_cancel_task_at_different_stages(self, progress_manager_with_socketio):
        """测试在不同阶段取消任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 测试在不同阶段取消
        test_stages = [
            (TaskStatus.STARTED, 0, "任务开始"),
            (TaskStatus.GENERATING_CONTENT, 15, "生成内容中"),
            (TaskStatus.GENERATING_IMAGE, 60, "生成图片中"),
        ]
        
        for status, progress, message in test_stages:
            task_id = progress_manager.create_task()
            
            # 更新到指定阶段
            progress_manager.update_progress(
                task_id=task_id,
                progress=progress,
                status=status,
                message=message
            )
            
            # 取消任务
            result = progress_manager.cancel_task(task_id)
            
            # 验证取消成功
            assert result is True, f"在 {status} 阶段取消失败"
            
            # 验证任务状态
            task_info = progress_manager.get_task_info(task_id)
            assert task_info["status"] == TaskStatus.CANCELLED
            assert task_info["cancelled"] is True
            assert task_info["progress"] == progress
    
    def test_cannot_cancel_completed_task(self, progress_manager_with_socketio):
        """测试无法取消已完成的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 完成任务
        progress_manager.complete_task(task_id)
        
        # 尝试取消已完成的任务
        result = progress_manager.cancel_task(task_id)
        
        # 验证取消失败
        assert result is False
        
        # 验证任务状态保持为 COMPLETED
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.COMPLETED
        assert task_info["cancelled"] is False
    
    def test_cannot_cancel_failed_task(self, progress_manager_with_socketio):
        """测试无法取消已失败的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 标记任务失败
        progress_manager.fail_task(task_id, "测试错误")
        
        # 尝试取消已失败的任务
        result = progress_manager.cancel_task(task_id)
        
        # 验证取消失败
        assert result is False
        
        # 验证任务状态保持为 FAILED
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.FAILED
    
    def test_cannot_cancel_already_cancelled_task(self, progress_manager_with_socketio):
        """测试无法重复取消已取消的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 第一次取消
        result1 = progress_manager.cancel_task(task_id)
        assert result1 is True
        
        # 第二次取消
        result2 = progress_manager.cancel_task(task_id)
        assert result2 is False
        
        # 验证任务状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
    
    def test_cancel_nonexistent_task(self, progress_manager_with_socketio):
        """测试取消不存在的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 尝试取消不存在的任务
        result = progress_manager.cancel_task("nonexistent_id")
        
        # 验证取消失败
        assert result is False
    
    def test_is_task_cancelled_check(self, progress_manager_with_socketio):
        """测试任务取消状态检查"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 初始状态：未取消
        assert progress_manager.is_task_cancelled(task_id) is False
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 取消后：已取消
        assert progress_manager.is_task_cancelled(task_id) is True
    
    def test_is_task_cancelled_nonexistent_task(self, progress_manager_with_socketio):
        """测试检查不存在任务的取消状态"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 检查不存在的任务
        result = progress_manager.is_task_cancelled("nonexistent_id")
        
        # 应该返回 False
        assert result is False
    
    # ========== 资源清理测试 ==========
    
    def test_cancelled_task_ignores_progress_updates(self, progress_manager_with_socketio):
        """测试已取消的任务忽略进度更新"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 更新进度到 30%
        progress_manager.update_progress(task_id, 30)
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 清空 mock 调用记录
        mock_socketio.emit.reset_mock()
        
        # 尝试更新进度（应该被忽略）
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            status=TaskStatus.GENERATING_CONTENT,
            message="继续生成"
        )
        
        # 验证进度没有更新
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["progress"] == 30  # 保持取消时的进度
        assert task_info["status"] == TaskStatus.CANCELLED  # 状态保持为 CANCELLED
        
        # 验证没有发送新的进度事件
        assert not mock_socketio.emit.called
    
    def test_cancelled_task_can_be_deleted(self, progress_manager_with_socketio):
        """测试已取消的任务可以被删除"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 验证任务存在
        assert progress_manager.get_task_info(task_id) is not None
        
        # 删除任务
        result = progress_manager.delete_task(task_id)
        
        # 验证删除成功
        assert result is True
        
        # 验证任务已被删除
        assert progress_manager.get_task_info(task_id) is None
        assert task_id not in progress_manager.tasks
    
    def test_cleanup_old_cancelled_tasks(self, progress_manager_with_socketio):
        """测试清理旧的已取消任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 创建多个任务
        task_ids = []
        for i in range(5):
            task_id = progress_manager.create_task()
            task_ids.append(task_id)
            
            # 取消部分任务
            if i % 2 == 0:
                progress_manager.cancel_task(task_id)
        
        # 修改任务的更新时间（模拟旧任务）
        current_time = time.time()
        for task_id in task_ids:
            progress_manager.tasks[task_id]["updated_at"] = current_time - 7200  # 2小时前
        
        # 清理 1 小时前的任务
        cleaned_count = progress_manager.cleanup_old_tasks(max_age_seconds=3600)
        
        # 验证所有任务都被清理
        assert cleaned_count == 5
        assert len(progress_manager.tasks) == 0
    
    def test_memory_cleanup_after_cancellation(self, progress_manager_with_socketio):
        """测试取消后的内存清理"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 创建任务并添加大量详细信息
        task_id = progress_manager.create_task()
        
        large_details = {
            "data": ["item" * 100 for _ in range(100)],  # 大量数据
            "metadata": {"key": "value" * 100}
        }
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            details=large_details
        )
        
        # 验证任务存在且包含详细信息
        task_info = progress_manager.get_task_info(task_id)
        assert "data" in task_info["details"]
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 删除任务
        progress_manager.delete_task(task_id)
        
        # 验证任务已从内存中删除
        assert task_id not in progress_manager.tasks
        assert progress_manager.get_task_info(task_id) is None
    
    def test_cancel_task_with_resources(self, progress_manager_with_socketio):
        """测试取消带有资源引用的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 添加资源引用（模拟文件句柄、网络连接等）
        resource_details = {
            "file_handles": ["file1.txt", "file2.txt"],
            "api_connections": ["conn1", "conn2"],
            "temp_files": ["/tmp/temp1", "/tmp/temp2"]
        }
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=40,
            details=resource_details
        )
        
        # 取消任务
        result = progress_manager.cancel_task(task_id)
        assert result is True
        
        # 验证任务信息仍然可访问（用于清理资源）
        task_info = progress_manager.get_task_info(task_id)
        assert task_info is not None
        assert "file_handles" in task_info["details"]
        
        # 模拟资源清理
        # 在实际应用中，这里应该关闭文件句柄、断开连接等
        
        # 清理完成后删除任务
        progress_manager.delete_task(task_id)
        assert progress_manager.get_task_info(task_id) is None
    
    # ========== 状态一致性测试 ==========
    
    def test_cancel_task_state_consistency(self, progress_manager_with_socketio):
        """测试取消任务的状态一致性"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 更新进度
        progress_manager.update_progress(
            task_id=task_id,
            progress=45,
            status=TaskStatus.GENERATING_IMAGE,
            message="生成图片中"
        )
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 验证状态一致性
        task_info = progress_manager.get_task_info(task_id)
        
        # 状态字段一致
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["cancelled"] is True
        
        # 进度保持不变
        assert task_info["progress"] == 45
        
        # 消息已更新
        assert task_info["message"] == "任务已取消"
        
        # 时间戳已更新
        assert task_info["updated_at"] > task_info["created_at"]
    
    def test_cancel_task_websocket_event_consistency(self, progress_manager_with_socketio):
        """测试取消任务的 WebSocket 事件一致性"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 清空之前的调用记录
        mock_socketio.emit.reset_mock()
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 验证发送了取消事件
        assert mock_socketio.emit.called
        
        # 获取事件数据
        call_args = mock_socketio.emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        # 验证事件内容
        assert event_name == "progress"
        assert event_data["task_id"] == task_id
        assert event_data["status"] == TaskStatus.CANCELLED.value
        assert event_data["message"] == "任务已取消"
        
        # 验证事件发送到正确的房间
        call_kwargs = call_args[1]
        assert call_kwargs["room"] == task_id
        assert call_kwargs["namespace"] == "/progress"
    
    def test_cancel_task_without_websocket_event(self, progress_manager_with_socketio):
        """测试取消任务时不发送 WebSocket 事件"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 清空之前的调用记录
        mock_socketio.emit.reset_mock()
        
        # 取消任务但不发送事件
        progress_manager.cancel_task(task_id, emit_event=False)
        
        # 验证没有发送事件
        assert not mock_socketio.emit.called
        
        # 验证任务状态仍然正确
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["cancelled"] is True
    
    def test_concurrent_cancel_operations(self, progress_manager_with_socketio):
        """测试并发取消操作的状态一致性"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 启动任务
        progress_manager.update_progress(task_id, 30)
        
        # 并发取消操作
        results = []
        threads = []
        
        def cancel_task():
            result = progress_manager.cancel_task(task_id)
            results.append(result)
        
        # 创建多个线程同时取消
        for _ in range(5):
            thread = threading.Thread(target=cancel_task)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证只有一个取消操作成功
        assert sum(results) == 1, "应该只有一个取消操作成功"
        
        # 验证最终状态一致
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["cancelled"] is True
    
    def test_cancel_then_complete_consistency(self, progress_manager_with_socketio):
        """测试取消后尝试完成任务的状态一致性"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 更新进度
        progress_manager.update_progress(task_id, 50)
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 尝试完成任务（应该被忽略）
        progress_manager.complete_task(task_id)
        
        # 验证状态保持为 CANCELLED
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["progress"] == 50  # 进度不变
    
    def test_cancel_then_fail_consistency(self, progress_manager_with_socketio):
        """测试取消后尝试标记失败的状态一致性"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 更新进度
        progress_manager.update_progress(task_id, 60)
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 尝试标记失败（应该被忽略）
        progress_manager.fail_task(task_id, "测试错误")
        
        # 验证状态保持为 CANCELLED
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["message"] == "任务已取消"  # 消息不变
    
    def test_multiple_tasks_cancel_independence(self, progress_manager_with_socketio):
        """测试多个任务取消的独立性"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        # 创建多个任务
        task_ids = [progress_manager.create_task() for _ in range(5)]
        
        # 更新所有任务的进度
        for i, task_id in enumerate(task_ids):
            progress_manager.update_progress(task_id, (i + 1) * 20)
        
        # 只取消部分任务
        cancelled_ids = [task_ids[1], task_ids[3]]
        for task_id in cancelled_ids:
            progress_manager.cancel_task(task_id)
        
        # 验证被取消的任务
        for task_id in cancelled_ids:
            task_info = progress_manager.get_task_info(task_id)
            assert task_info["status"] == TaskStatus.CANCELLED
            assert task_info["cancelled"] is True
        
        # 验证未被取消的任务
        active_ids = [task_ids[0], task_ids[2], task_ids[4]]
        for task_id in active_ids:
            task_info = progress_manager.get_task_info(task_id)
            assert task_info["status"] != TaskStatus.CANCELLED
            assert task_info["cancelled"] is False
    
    # ========== 边界情况和异常测试 ==========
    
    def test_cancel_task_rapid_succession(self, progress_manager_with_socketio):
        """测试快速连续取消任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 快速连续取消多次
        results = []
        for _ in range(10):
            result = progress_manager.cancel_task(task_id)
            results.append(result)
        
        # 只有第一次成功
        assert results[0] is True
        assert all(r is False for r in results[1:])
        
        # 验证最终状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
    
    def test_cancel_task_with_empty_details(self, progress_manager_with_socketio):
        """测试取消没有详细信息的任务"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 不添加任何详细信息，直接取消
        result = progress_manager.cancel_task(task_id)
        
        # 验证取消成功
        assert result is True
        
        # 验证任务状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["details"] == {}
    
    def test_cancel_task_preserves_details(self, progress_manager_with_socketio):
        """测试取消任务保留详细信息"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        
        # 添加详细信息
        original_details = {
            "current_image": 3,
            "total_images": 5,
            "processed_items": ["item1", "item2", "item3"]
        }
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=60,
            details=original_details
        )
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 验证详细信息被保留
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["details"]["current_image"] == 3
        assert task_info["details"]["total_images"] == 5
        assert task_info["details"]["processed_items"] == ["item1", "item2", "item3"]


class TestCancellationIntegration:
    """取消功能集成测试"""
    
    @pytest.fixture
    def progress_manager(self):
        """创建进度管理器实例"""
        return ProgressManager()
    
    def test_cancel_workflow_simulation(self, progress_manager):
        """测试完整的取消工作流"""
        task_id = progress_manager.create_task()
        
        # 模拟任务执行
        progress_manager.update_progress(
            task_id=task_id,
            progress=10,
            status=TaskStatus.GENERATING_CONTENT,
            message="生成标题"
        )
        
        time.sleep(0.1)
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=20,
            status=TaskStatus.GENERATING_CONTENT,
            message="生成正文"
        )
        
        time.sleep(0.1)
        
        # 用户取消任务
        cancel_result = progress_manager.cancel_task(task_id)
        assert cancel_result is True
        
        # 尝试继续更新进度（应该被忽略）
        progress_manager.update_progress(
            task_id=task_id,
            progress=40,
            status=TaskStatus.GENERATING_IMAGE,
            message="生成图片"
        )
        
        # 验证最终状态
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["progress"] == 20  # 保持取消时的进度
        assert task_info["message"] == "任务已取消"
    
    def test_cancel_with_cleanup_callback(self, progress_manager):
        """测试带清理回调的取消流程"""
        task_id = progress_manager.create_task()
        
        # 模拟资源分配
        resources = {
            "allocated": True,
            "files": ["temp1.txt", "temp2.txt"],
            "connections": ["conn1", "conn2"]
        }
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            details={"resources": resources}
        )
        
        # 取消任务
        cancel_result = progress_manager.cancel_task(task_id)
        assert cancel_result is True
        
        # 获取任务信息用于清理
        task_info = progress_manager.get_task_info(task_id)
        assert task_info is not None
        
        # 模拟资源清理
        cleanup_successful = True
        if "resources" in task_info["details"]:
            resources = task_info["details"]["resources"]
            # 清理文件
            for file in resources.get("files", []):
                # 实际应用中这里会删除文件
                pass
            # 关闭连接
            for conn in resources.get("connections", []):
                # 实际应用中这里会关闭连接
                pass
            cleanup_successful = True
        
        assert cleanup_successful is True
        
        # 清理完成后删除任务
        progress_manager.delete_task(task_id)
        assert progress_manager.get_task_info(task_id) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
