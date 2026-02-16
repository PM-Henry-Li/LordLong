#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket 事件处理器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.web.socketio_handlers import SocketIOHandlers
from src.core.progress_manager import ProgressManager, TaskStatus


class TestSocketIOHandlers:
    """WebSocket 事件处理器测试类"""
    
    @pytest.fixture
    def mock_socketio(self):
        """创建 Mock SocketIO 实例"""
        socketio = Mock()
        socketio.on = Mock(side_effect=lambda event, namespace: lambda f: f)
        return socketio
    
    @pytest.fixture
    def progress_manager(self):
        """创建进度管理器实例"""
        return ProgressManager()
    
    @pytest.fixture
    def handlers(self, mock_socketio, progress_manager):
        """创建事件处理器实例"""
        return SocketIOHandlers(mock_socketio, progress_manager)
    
    @patch("flask.request")
    @patch("flask_socketio.emit")
    def test_on_connect(self, mock_emit, mock_request, handlers):
        """测试客户端连接"""
        mock_request.sid = "test_client_123"
        
        result = handlers.on_connect()
        
        assert result["status"] == "connected"
        assert "test_client_123" in handlers.connected_clients
        assert mock_emit.called
    
    @patch("flask.request")
    def test_on_disconnect(self, mock_request, handlers):
        """测试客户端断开"""
        mock_request.sid = "test_client_123"
        
        # 先连接
        handlers.on_connect()
        assert "test_client_123" in handlers.connected_clients
        
        # 再断开
        handlers.on_disconnect()
        assert "test_client_123" not in handlers.connected_clients
    
    @patch("flask.request")
    @patch("flask_socketio.join_room")
    @patch("flask_socketio.emit")
    def test_on_join(self, mock_emit, mock_join_room, mock_request, handlers, progress_manager):
        """测试加入房间"""
        mock_request.sid = "test_client_123"
        
        # 先连接
        handlers.on_connect()
        
        # 创建任务
        task_id = progress_manager.create_task()
        
        # 加入房间
        result = handlers.on_join({"task_id": task_id})
        
        assert result["status"] == "success"
        assert result["task_id"] == task_id
        assert mock_join_room.called
        assert task_id in handlers.connected_clients["test_client_123"]["rooms"]
    
    @patch("flask.request")
    def test_on_join_missing_task_id(self, mock_request, handlers):
        """测试加入房间时缺少 task_id"""
        mock_request.sid = "test_client_123"
        
        handlers.on_connect()
        
        result = handlers.on_join({})
        
        assert result["status"] == "error"
        assert "缺少 task_id" in result["message"]
    
    @patch("flask.request")
    @patch("flask_socketio.join_room")
    @patch("flask_socketio.leave_room")
    def test_on_leave(self, mock_leave_room, mock_join_room, mock_request, handlers, progress_manager):
        """测试离开房间"""
        mock_request.sid = "test_client_123"
        
        # 先连接并加入房间
        handlers.on_connect()
        task_id = progress_manager.create_task()
        handlers.on_join({"task_id": task_id})
        
        # 离开房间
        result = handlers.on_leave({"task_id": task_id})
        
        assert result["status"] == "success"
        assert result["task_id"] == task_id
        assert mock_leave_room.called
        assert task_id not in handlers.connected_clients["test_client_123"]["rooms"]
    
    @patch("flask.request")
    def test_on_leave_missing_task_id(self, mock_request, handlers):
        """测试离开房间时缺少 task_id"""
        mock_request.sid = "test_client_123"
        
        handlers.on_connect()
        
        result = handlers.on_leave({})
        
        assert result["status"] == "error"
        assert "缺少 task_id" in result["message"]
    
    @patch("flask.request")
    @patch("flask_socketio.emit")
    def test_on_ping(self, mock_emit, mock_request, handlers):
        """测试心跳检测"""
        mock_request.sid = "test_client_123"
        
        result = handlers.on_ping()
        
        assert result["status"] == "pong"
        assert mock_emit.called
        
        # 验证 pong 响应
        call_args = mock_emit.call_args
        assert call_args[0][0] == "pong"
        assert "timestamp" in call_args[0][1]
    
    @patch("flask.request")
    def test_on_cancel_task_success(self, mock_request, handlers, progress_manager):
        """测试成功取消任务"""
        mock_request.sid = "test_client_123"
        
        # 创建任务
        task_id = progress_manager.create_task()
        progress_manager.update_progress(task_id, 30, status=TaskStatus.STARTED)
        
        # 取消任务
        result = handlers.on_cancel_task({"task_id": task_id})
        
        assert result["status"] == "success"
        assert result["task_id"] == task_id
        assert progress_manager.is_task_cancelled(task_id)
    
    @patch("flask.request")
    def test_on_cancel_task_failure(self, mock_request, handlers, progress_manager):
        """测试取消不存在的任务"""
        mock_request.sid = "test_client_123"
        
        result = handlers.on_cancel_task({"task_id": "nonexistent_id"})
        
        assert result["status"] == "error"
        assert "取消失败" in result["message"]
    
    @patch("flask.request")
    def test_on_cancel_task_missing_task_id(self, mock_request, handlers):
        """测试取消任务时缺少 task_id"""
        mock_request.sid = "test_client_123"
        
        result = handlers.on_cancel_task({})
        
        assert result["status"] == "error"
        assert "缺少 task_id" in result["message"]
    
    @patch("flask.request")
    def test_get_connected_clients_count(self, mock_request, handlers):
        """测试获取连接客户端数量"""
        assert handlers.get_connected_clients_count() == 0
        
        # 连接多个客户端
        for i in range(3):
            mock_request.sid = f"client_{i}"
            handlers.on_connect()
        
        assert handlers.get_connected_clients_count() == 3
    
    @patch("flask.request")
    def test_get_client_info(self, mock_request, handlers):
        """测试获取客户端信息"""
        mock_request.sid = "test_client_123"
        
        handlers.on_connect()
        
        client_info = handlers.get_client_info("test_client_123")
        
        assert client_info is not None
        assert "connected_at" in client_info
        assert "rooms" in client_info
    
    @patch("flask.request")
    def test_get_client_info_nonexistent(self, mock_request, handlers):
        """测试获取不存在的客户端信息"""
        client_info = handlers.get_client_info("nonexistent_client")
        
        assert client_info == {}
    
    @patch("flask.request")
    @patch("flask_socketio.join_room")
    @patch("flask_socketio.emit")
    def test_join_sends_current_progress(self, mock_emit, mock_join_room, mock_request, handlers, progress_manager):
        """测试加入房间时发送当前进度"""
        mock_request.sid = "test_client_123"
        
        handlers.on_connect()
        
        # 创建任务并更新进度
        task_id = progress_manager.create_task()
        progress_manager.update_progress(
            task_id=task_id,
            progress=50,
            status=TaskStatus.GENERATING_CONTENT,
            message="生成中"
        )
        
        # 加入房间
        handlers.on_join({"task_id": task_id})
        
        # 验证发送了进度事件
        assert mock_emit.called
        
        # 查找 progress 事件
        progress_event_found = False
        for call in mock_emit.call_args_list:
            if call[0][0] == "progress":
                progress_event_found = True
                event_data = call[0][1]
                assert event_data["task_id"] == task_id
                assert event_data["progress"] == 50
                assert event_data["status"] == TaskStatus.GENERATING_CONTENT.value
                break
        
        assert progress_event_found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
