#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket 事件处理器模块

处理 WebSocket 连接、断开、房间管理和心跳检测。
"""

from typing import Dict, Any
from flask_socketio import emit, join_room, leave_room, disconnect
from src.core.logger import Logger


class SocketIOHandlers:
    """
    WebSocket 事件处理器
    
    管理客户端连接、房间和心跳检测。
    """
    
    def __init__(self, socketio, progress_manager):
        """
        初始化事件处理器
        
        Args:
            socketio: Flask-SocketIO 实例
            progress_manager: 进度管理器实例
        """
        self.socketio = socketio
        self.progress_manager = progress_manager
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        
        # 注册事件处理器
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """注册所有事件处理器"""
        
        @self.socketio.on("connect", namespace="/progress")
        def handle_connect():
            """处理客户端连接"""
            return self.on_connect()
        
        @self.socketio.on("disconnect", namespace="/progress")
        def handle_disconnect():
            """处理客户端断开"""
            return self.on_disconnect()
        
        @self.socketio.on("join", namespace="/progress")
        def handle_join(data):
            """处理加入房间"""
            return self.on_join(data)
        
        @self.socketio.on("leave", namespace="/progress")
        def handle_leave(data):
            """处理离开房间"""
            return self.on_leave(data)
        
        @self.socketio.on("ping", namespace="/progress")
        def handle_ping():
            """处理心跳检测"""
            return self.on_ping()
        
        @self.socketio.on("cancel_task", namespace="/progress")
        def handle_cancel_task(data):
            """处理取消任务"""
            return self.on_cancel_task(data)
    
    def on_connect(self) -> Dict[str, Any]:
        """
        处理客户端连接
        
        Returns:
            连接响应
        """
        from flask import request
        
        client_id = request.sid
        
        self.connected_clients[client_id] = {
            "connected_at": __import__("time").time(),
            "rooms": set()
        }
        
        Logger.info(
            f"客户端连接: {client_id}",
            logger_name="socketio_handlers",
            client_id=client_id
        )
        
        emit("connected", {
            "status": "success",
            "message": "连接成功",
            "client_id": client_id
        })
        
        return {"status": "connected"}
    
    def on_disconnect(self) -> None:
        """处理客户端断开"""
        from flask import request
        
        client_id = request.sid
        
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        
        Logger.info(
            f"客户端断开: {client_id}",
            logger_name="socketio_handlers",
            client_id=client_id
        )
    
    def on_join(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理加入房间（订阅任务进度）
        
        Args:
            data: 包含 task_id 的数据
            
        Returns:
            加入响应
        """
        from flask import request
        
        client_id = request.sid
        task_id = data.get("task_id")
        
        if not task_id:
            Logger.warning(
                "加入房间失败：缺少 task_id",
                logger_name="socketio_handlers",
                client_id=client_id
            )
            return {
                "status": "error",
                "message": "缺少 task_id"
            }
        
        # 加入房间
        join_room(task_id)
        
        # 记录客户端房间
        if client_id in self.connected_clients:
            self.connected_clients[client_id]["rooms"].add(task_id)
        
        Logger.info(
            f"客户端加入房间: {client_id} -> {task_id}",
            logger_name="socketio_handlers",
            client_id=client_id,
            task_id=task_id
        )
        
        # 发送当前任务状态
        task_info = self.progress_manager.get_task_info(task_id)
        if task_info:
            emit("progress", {
                "task_id": task_id,
                "status": task_info["status"].value,
                "progress": task_info["progress"],
                "message": task_info["message"],
                "details": task_info["details"],
                "timestamp": task_info["updated_at"]
            })
        
        return {
            "status": "success",
            "message": f"已加入任务房间: {task_id}",
            "task_id": task_id
        }
    
    def on_leave(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理离开房间（取消订阅任务进度）
        
        Args:
            data: 包含 task_id 的数据
            
        Returns:
            离开响应
        """
        from flask import request
        
        client_id = request.sid
        task_id = data.get("task_id")
        
        if not task_id:
            return {
                "status": "error",
                "message": "缺少 task_id"
            }
        
        # 离开房间
        leave_room(task_id)
        
        # 更新客户端房间记录
        if client_id in self.connected_clients:
            self.connected_clients[client_id]["rooms"].discard(task_id)
        
        Logger.info(
            f"客户端离开房间: {client_id} <- {task_id}",
            logger_name="socketio_handlers",
            client_id=client_id,
            task_id=task_id
        )
        
        return {
            "status": "success",
            "message": f"已离开任务房间: {task_id}",
            "task_id": task_id
        }
    
    def on_ping(self) -> Dict[str, Any]:
        """
        处理心跳检测
        
        Returns:
            心跳响应
        """
        from flask import request
        
        client_id = request.sid
        
        Logger.debug(
            f"收到心跳: {client_id}",
            logger_name="socketio_handlers",
            client_id=client_id
        )
        
        emit("pong", {
            "timestamp": __import__("time").time()
        })
        
        return {"status": "pong"}
    
    def on_cancel_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理取消任务请求
        
        Args:
            data: 包含 task_id 的数据
            
        Returns:
            取消响应
        """
        from flask import request
        
        client_id = request.sid
        task_id = data.get("task_id")
        
        if not task_id:
            return {
                "status": "error",
                "message": "缺少 task_id"
            }
        
        # 取消任务
        success = self.progress_manager.cancel_task(task_id)
        
        if success:
            Logger.info(
                f"任务取消成功: {task_id}",
                logger_name="socketio_handlers",
                client_id=client_id,
                task_id=task_id
            )
            
            return {
                "status": "success",
                "message": "任务已取消",
                "task_id": task_id
            }
        else:
            Logger.warning(
                f"任务取消失败: {task_id}",
                logger_name="socketio_handlers",
                client_id=client_id,
                task_id=task_id
            )
            
            return {
                "status": "error",
                "message": "任务取消失败（任务不存在或已完成）",
                "task_id": task_id
            }
    
    def get_connected_clients_count(self) -> int:
        """
        获取连接的客户端数量
        
        Returns:
            客户端数量
        """
        return len(self.connected_clients)
    
    def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """
        获取客户端信息
        
        Args:
            client_id: 客户端 ID
            
        Returns:
            客户端信息
        """
        return self.connected_clients.get(client_id, {})
