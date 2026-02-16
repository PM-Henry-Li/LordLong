#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
进度管理器模块

提供任务进度跟踪和 WebSocket 推送功能。
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum
import time
import uuid
from threading import Lock
from src.core.logger import Logger


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待中
    STARTED = "started"           # 已开始
    GENERATING_CONTENT = "generating_content"  # 生成内容中
    GENERATING_IMAGE = "generating_image"      # 生成图片中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class ProgressManager:
    """
    进度管理器
    
    管理任务进度并通过 WebSocket 推送进度更新。
    """
    
    def __init__(self, socketio=None):
        """
        初始化进度管理器
        
        Args:
            socketio: Flask-SocketIO 实例（可选）
        """
        self.socketio = socketio
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
    
    def create_task(self, task_type: str = "generation") -> str:
        """
        创建新任务
        
        Args:
            task_type: 任务类型
            
        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())
        
        with self.lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "task_type": task_type,
                "status": TaskStatus.PENDING,
                "progress": 0,
                "message": "任务创建成功",
                "details": {},
                "created_at": time.time(),
                "updated_at": time.time(),
                "cancelled": False
            }
        
        Logger.info(
            f"创建任务: {task_id}",
            logger_name="progress_manager",
            task_id=task_id,
            task_type=task_type
        )
        
        return task_id
    
    def update_progress(
        self,
        task_id: str,
        progress: int,
        status: Optional[TaskStatus] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        emit_event: bool = True
    ) -> None:
        """
        更新任务进度
        
        Args:
            task_id: 任务 ID
            progress: 进度百分比（0-100）
            status: 任务状态
            message: 进度消息
            details: 详细信息
            emit_event: 是否发送 WebSocket 事件
        """
        with self.lock:
            if task_id not in self.tasks:
                Logger.warning(
                    f"任务不存在: {task_id}",
                    logger_name="progress_manager",
                    task_id=task_id
                )
                return
            
            task = self.tasks[task_id]
            
            # 检查任务是否已取消
            if task.get("cancelled", False):
                Logger.info(
                    f"任务已取消，忽略进度更新: {task_id}",
                    logger_name="progress_manager",
                    task_id=task_id
                )
                return
            
            # 更新任务信息
            task["progress"] = max(0, min(100, progress))
            task["updated_at"] = time.time()
            
            if status is not None:
                task["status"] = status
            
            if message is not None:
                task["message"] = message
            
            if details is not None:
                task["details"].update(details)
        
        # 发送 WebSocket 事件
        if emit_event and self.socketio:
            self._emit_progress_event(task_id)
        
        Logger.debug(
            f"更新任务进度: {task_id}",
            logger_name="progress_manager",
            task_id=task_id,
            progress=progress,
            status=status.value if status else None
        )
    
    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        emit_event: bool = True
    ) -> None:
        """
        完成任务
        
        Args:
            task_id: 任务 ID
            result: 任务结果
            emit_event: 是否发送 WebSocket 事件
        """
        self.update_progress(
            task_id=task_id,
            progress=100,
            status=TaskStatus.COMPLETED,
            message="任务完成",
            details={"result": result} if result else None,
            emit_event=emit_event
        )
        
        Logger.info(
            f"任务完成: {task_id}",
            logger_name="progress_manager",
            task_id=task_id
        )
    
    def fail_task(
        self,
        task_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        emit_event: bool = True
    ) -> None:
        """
        标记任务失败
        
        Args:
            task_id: 任务 ID
            error_message: 错误消息
            error_details: 错误详情
            emit_event: 是否发送 WebSocket 事件
        """
        details = {"error": error_message}
        if error_details:
            details.update(error_details)
        
        self.update_progress(
            task_id=task_id,
            progress=self.get_task_progress(task_id),
            status=TaskStatus.FAILED,
            message=error_message,
            details=details,
            emit_event=emit_event
        )
        
        Logger.error(
            f"任务失败: {task_id}",
            logger_name="progress_manager",
            task_id=task_id,
            error_message=error_message
        )
    
    def cancel_task(self, task_id: str, emit_event: bool = True) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务 ID
            emit_event: 是否发送 WebSocket 事件
            
        Returns:
            是否成功取消
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            # 只能取消进行中的任务
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False
            
            task["cancelled"] = True
            task["status"] = TaskStatus.CANCELLED
            task["message"] = "任务已取消"
            task["updated_at"] = time.time()
        
        if emit_event and self.socketio:
            self._emit_progress_event(task_id)
        
        Logger.info(
            f"任务已取消: {task_id}",
            logger_name="progress_manager",
            task_id=task_id
        )
        
        return True
    
    def is_task_cancelled(self, task_id: str) -> bool:
        """
        检查任务是否已取消
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否已取消
        """
        with self.lock:
            if task_id not in self.tasks:
                return False
            return self.tasks[task_id].get("cancelled", False)
    
    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务信息字典
        """
        with self.lock:
            if task_id not in self.tasks:
                return None
            return self.tasks[task_id].copy()
    
    def get_task_progress(self, task_id: str) -> int:
        """
        获取任务进度
        
        Args:
            task_id: 任务 ID
            
        Returns:
            进度百分比（0-100）
        """
        with self.lock:
            if task_id not in self.tasks:
                return 0
            return self.tasks[task_id]["progress"]
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否成功删除
        """
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                Logger.info(
                    f"删除任务: {task_id}",
                    logger_name="progress_manager",
                    task_id=task_id
                )
                return True
            return False
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        清理旧任务
        
        Args:
            max_age_seconds: 最大保留时间（秒）
            
        Returns:
            清理的任务数量
        """
        current_time = time.time()
        cleaned_count = 0
        
        with self.lock:
            task_ids_to_delete = []
            
            for task_id, task in self.tasks.items():
                age = current_time - task["updated_at"]
                if age > max_age_seconds:
                    task_ids_to_delete.append(task_id)
            
            for task_id in task_ids_to_delete:
                del self.tasks[task_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            Logger.info(
                f"清理了 {cleaned_count} 个旧任务",
                logger_name="progress_manager",
                cleaned_count=cleaned_count
            )
        
        return cleaned_count
    
    def _emit_progress_event(self, task_id: str) -> None:
        """
        发送进度事件
        
        Args:
            task_id: 任务 ID
        """
        if not self.socketio:
            return
        
        task_info = self.get_task_info(task_id)
        if not task_info:
            return
        
        # 准备事件数据
        event_data = {
            "task_id": task_id,
            "status": task_info["status"].value,
            "progress": task_info["progress"],
            "message": task_info["message"],
            "details": task_info["details"],
            "timestamp": task_info["updated_at"]
        }
        
        try:
            # 发送到特定任务的房间
            self.socketio.emit(
                "progress",
                event_data,
                room=task_id,
                namespace="/progress"
            )
            
            Logger.debug(
                f"发送进度事件: {task_id}",
                logger_name="progress_manager",
                task_id=task_id,
                progress=task_info["progress"]
            )
        except Exception as e:
            Logger.error(
                f"发送进度事件失败: {str(e)}",
                logger_name="progress_manager",
                task_id=task_id,
                error=str(e)
            )
    
    def create_progress_callback(self, task_id: str) -> Callable[[int, str, Optional[Dict]], None]:
        """
        创建进度回调函数
        
        Args:
            task_id: 任务 ID
            
        Returns:
            进度回调函数
        """
        def callback(progress: int, message: str = "", details: Optional[Dict[str, Any]] = None) -> None:
            """
            进度回调函数
            
            Args:
                progress: 进度百分比
                message: 进度消息
                details: 详细信息
            """
            self.update_progress(
                task_id=task_id,
                progress=progress,
                message=message,
                details=details
            )
        
        return callback
