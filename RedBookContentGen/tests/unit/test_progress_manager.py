#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
进度管理器单元测试
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.core.progress_manager import ProgressManager, TaskStatus


class TestProgressManager:
    """进度管理器测试类"""
    
    @pytest.fixture
    def progress_manager(self):
        """创建进度管理器实例"""
        return ProgressManager()
    
    @pytest.fixture
    def progress_manager_with_socketio(self):
        """创建带 SocketIO 的进度管理器实例"""
        mock_socketio = Mock()
        return ProgressManager(socketio=mock_socketio), mock_socketio
    
    def test_create_task(self, progress_manager):
        """测试创建任务"""
        task_id = progress_manager.create_task(task_type="test")
        
        assert task_id is not None
        assert len(task_id) > 0
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info is not None
        assert task_info["task_type"] == "test"
        assert task_info["status"] == TaskStatus.PENDING
        assert task_info["progress"] == 0
    
    def test_update_progress(self, progress_manager):
        """测试更新进度"""
        task_id = progress_manager.create_task()
        
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            status=TaskStatus.GENERATING_CONTENT,
            message="生成内容中",
            details={"step": 1}
        )
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["progress"] == 50
        assert task_info["status"] == TaskStatus.GENERATING_CONTENT
        assert task_info["message"] == "生成内容中"
        assert task_info["details"]["step"] == 1
    
    def test_update_progress_bounds(self, progress_manager):
        """测试进度边界值"""
        task_id = progress_manager.create_task()
        
        # 测试负数
        progress_manager.update_progress(task_id, -10)
        assert progress_manager.get_task_progress(task_id) == 0
        
        # 测试超过 100
        progress_manager.update_progress(task_id, 150)
        assert progress_manager.get_task_progress(task_id) == 100
    
    def test_complete_task(self, progress_manager):
        """测试完成任务"""
        task_id = progress_manager.create_task()
        
        result = {"output": "test_result"}
        progress_manager.complete_task(task_id, result=result)
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.COMPLETED
        assert task_info["progress"] == 100
        assert task_info["details"]["result"] == result
    
    def test_fail_task(self, progress_manager):
        """测试任务失败"""
        task_id = progress_manager.create_task()
        
        error_message = "测试错误"
        error_details = {"error_code": "TEST_ERROR"}
        
        progress_manager.fail_task(
            task_id=task_id,
            error_message=error_message,
            error_details=error_details
        )
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.FAILED
        assert task_info["message"] == error_message
        assert task_info["details"]["error"] == error_message
        assert task_info["details"]["error_code"] == "TEST_ERROR"
    
    def test_cancel_task(self, progress_manager):
        """测试取消任务"""
        task_id = progress_manager.create_task()
        
        # 更新进度
        progress_manager.update_progress(task_id, 30, status=TaskStatus.STARTED)
        
        # 取消任务
        success = progress_manager.cancel_task(task_id)
        assert success is True
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        assert task_info["cancelled"] is True
    
    def test_cancel_completed_task(self, progress_manager):
        """测试取消已完成的任务"""
        task_id = progress_manager.create_task()
        
        # 完成任务
        progress_manager.complete_task(task_id)
        
        # 尝试取消
        success = progress_manager.cancel_task(task_id)
        assert success is False
        
        # 状态应该保持为 COMPLETED
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.COMPLETED
    
    def test_is_task_cancelled(self, progress_manager):
        """测试检查任务是否已取消"""
        task_id = progress_manager.create_task()
        
        assert progress_manager.is_task_cancelled(task_id) is False
        
        progress_manager.cancel_task(task_id)
        assert progress_manager.is_task_cancelled(task_id) is True
    
    def test_update_cancelled_task(self, progress_manager):
        """测试更新已取消的任务"""
        task_id = progress_manager.create_task()
        
        # 取消任务
        progress_manager.cancel_task(task_id)
        
        # 尝试更新进度（应该被忽略）
        progress_manager.update_progress(task_id, 50)
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["status"] == TaskStatus.CANCELLED
        # 进度不应该更新
        assert task_info["progress"] != 50
    
    def test_get_task_info_nonexistent(self, progress_manager):
        """测试获取不存在的任务信息"""
        task_info = progress_manager.get_task_info("nonexistent_id")
        assert task_info is None
    
    def test_get_task_progress(self, progress_manager):
        """测试获取任务进度"""
        task_id = progress_manager.create_task()
        
        assert progress_manager.get_task_progress(task_id) == 0
        
        progress_manager.update_progress(task_id, 75)
        assert progress_manager.get_task_progress(task_id) == 75
    
    def test_delete_task(self, progress_manager):
        """测试删除任务"""
        task_id = progress_manager.create_task()
        
        success = progress_manager.delete_task(task_id)
        assert success is True
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info is None
    
    def test_delete_nonexistent_task(self, progress_manager):
        """测试删除不存在的任务"""
        success = progress_manager.delete_task("nonexistent_id")
        assert success is False
    
    def test_cleanup_old_tasks(self, progress_manager):
        """测试清理旧任务"""
        # 创建多个任务
        task_ids = []
        for i in range(3):
            task_id = progress_manager.create_task()
            task_ids.append(task_id)
        
        # 手动修改第一个任务的更新时间（模拟旧任务）
        with progress_manager.lock:
            progress_manager.tasks[task_ids[0]]["updated_at"] = time.time() - 7200  # 2小时前
        
        # 清理 1 小时前的任务
        cleaned_count = progress_manager.cleanup_old_tasks(max_age_seconds=3600)
        
        assert cleaned_count == 1
        assert progress_manager.get_task_info(task_ids[0]) is None
        assert progress_manager.get_task_info(task_ids[1]) is not None
        assert progress_manager.get_task_info(task_ids[2]) is not None
    
    def test_emit_progress_event(self, progress_manager_with_socketio):
        """测试发送进度事件"""
        progress_manager, mock_socketio = progress_manager_with_socketio
        
        task_id = progress_manager.create_task()
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            message="测试进度"
        )
        
        # 验证 emit 被调用
        assert mock_socketio.emit.called
        
        # 获取调用参数
        call_args = mock_socketio.emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == "progress"
        assert event_data["task_id"] == task_id
        assert event_data["progress"] == 50
        assert event_data["message"] == "测试进度"
    
    def test_create_progress_callback(self, progress_manager):
        """测试创建进度回调函数"""
        task_id = progress_manager.create_task()
        
        callback = progress_manager.create_progress_callback(task_id)
        
        # 使用回调更新进度
        callback(30, "测试回调", {"key": "value"})
        
        task_info = progress_manager.get_task_info(task_id)
        assert task_info["progress"] == 30
        assert task_info["message"] == "测试回调"
        assert task_info["details"]["key"] == "value"
    
    def test_thread_safety(self, progress_manager):
        """测试线程安全"""
        import threading
        
        task_id = progress_manager.create_task()
        
        def update_progress():
            for i in range(10):
                progress_manager.update_progress(task_id, i * 10)
        
        # 创建多个线程同时更新进度
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_progress)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证任务仍然存在且数据一致
        task_info = progress_manager.get_task_info(task_id)
        assert task_info is not None
        assert 0 <= task_info["progress"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
