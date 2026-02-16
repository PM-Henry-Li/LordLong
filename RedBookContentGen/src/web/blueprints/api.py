#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 蓝图
处理所有 API 接口路由
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from flask import Blueprint, jsonify, send_file, current_app, Response, request
from werkzeug.wrappers import Response as WerkzeugResponse
from pydantic import ValidationError
from src.models.requests import ContentGenerationRequest, ImageGenerationRequest, SearchRequest, BatchContentGenerationRequest
from src.models.validation_errors import format_validation_error
from src.web.validators import (
    validate_request,
    validate_json_request,
    LogSearchRequest,
)
from src.web.error_handlers import handle_errors
from src.core.errors import ResourceNotFoundError
from src.utils.export_utils import ExportUtils

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """
    健康检查端点
    
    用于 Docker 健康检查和监控系统
    
    响应示例:
    {
        "status": "healthy",
        "timestamp": "2026-02-14T10:30:00.000000",
        "version": "1.0.0",
        "services": {
            "content_service": "ok",
            "image_service": "ok"
        }
    }
    
    状态码:
    - 200: 服务健康
    - 503: 服务不可用
    """
    try:
        # 检查服务是否可用
        content_service = current_app.config.get("CONTENT_SERVICE")
        image_service = current_app.config.get("IMAGE_SERVICE")
        
        services_status = {
            "content_service": "ok" if content_service else "unavailable",
            "image_service": "ok" if image_service else "unavailable",
        }
        
        # 如果任何服务不可用，返回 503
        if "unavailable" in services_status.values():
            return jsonify({
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "services": services_status,
            }), 503
        
        # 所有服务正常
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": services_status,
        }), 200
        
    except Exception as e:
        # 发生异常，返回 503
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "error": str(e),
        }), 503


@api_bp.route("/generate", methods=["POST"])
@handle_errors
def generate_content_deprecated() -> Tuple[Response, int]:
    """
    Deprecated: 原有接口已废弃
    """
    return jsonify({"success": False, "error": "API已升级，请刷新页面使用新版"}), 410


@api_bp.route("/generate_content", methods=["POST"])
@handle_errors
def generate_content() -> Tuple[Response, int]:
    """
    生成小红书内容
    
    请求体示例:
    {
        "input_text": "记得小时候，老北京的胡同里总是充满了生活的气息...",
        "count": 3,
        "style": "retro_chinese",
        "temperature": 0.8
    }
    
    响应示例:
    {
        "success": true,
        "data": {
            "titles": ["标题1", "标题2", "标题3"],
            "content": "生成的内容...",
            "tags": ["标签1", "标签2"],
            "image_prompts": ["提示词1", "提示词2"]
        }
    }
    
    错误响应示例:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "输入数据验证失败",
            "errors": [
                {
                    "field": "input_text",
                    "field_name": "输入文本",
                    "message": "输入文本长度不能少于 2 个字符（当前：5 个字符）",
                    "suggestions": [
                        "请提供更详细的内容描述",
                        "建议至少输入 10 个字符"
                    ],
                    "error_type": "string_too_short"
                }
            ],
            "total_errors": 1
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 使用 Pydantic 模型验证请求数据
        validated_data = ContentGenerationRequest(**data)
        
        # 调用内容生成服务
        content_service = current_app.config["CONTENT_SERVICE"]
        result = content_service.generate_content(
            validated_data.input_text, 
            validated_data.count
        )
        
        return jsonify({"success": True, "data": result})
        
    except ValidationError as e:
        # 使用 format_validation_error 处理验证错误
        error_response = format_validation_error(e)
        return jsonify(error_response), 400


@api_bp.route("/batch/generate_content", methods=["POST"])
@handle_errors
def batch_generate_content() -> Tuple[Response, int]:
    """
    批量生成小红书内容
    
    请求体示例:
    {
        "inputs": [
            "记得小时候，老北京的胡同里总是充满了生活的气息...",
            "北京的四合院是传统建筑的代表，体现了中国人的居住智慧...",
            "老北京的小吃文化源远流长，每一种小吃都有自己的故事..."
        ],
        "count": 1,
        "style": "retro_chinese",
        "temperature": 0.8
    }
    
    响应示例:
    {
        "success": true,
        "data": {
            "batch_id": "batch_20260213_143000",
            "total": 3,
            "results": [
                {
                    "index": 0,
                    "input_text": "记得小时候，老北京的胡同里...",
                    "status": "success",
                    "data": {
                        "titles": ["标题1", "标题2"],
                        "content": "生成的内容...",
                        "tags": ["标签1", "标签2"],
                        "image_tasks": [...]
                    },
                    "error": null
                },
                {
                    "index": 1,
                    "input_text": "北京的四合院是传统建筑...",
                    "status": "success",
                    "data": {...},
                    "error": null
                },
                {
                    "index": 2,
                    "input_text": "老北京的小吃文化源远流长...",
                    "status": "failed",
                    "data": null,
                    "error": "API调用失败: 超时"
                }
            ],
            "summary": {
                "success": 2,
                "failed": 1,
                "total": 3
            }
        }
    }
    
    错误响应示例:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "输入数据验证失败",
            "errors": [
                {
                    "field": "inputs",
                    "field_name": "批量输入",
                    "message": "批量输入数量不能超过 50 条（当前：100 条）",
                    "suggestions": [
                        "请将输入数量控制在 50 条以内",
                        "可以分多次批量提交"
                    ],
                    "error_type": "value_error"
                }
            ],
            "total_errors": 1
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 使用 Pydantic 模型验证请求数据
        validated_data = BatchContentGenerationRequest(**data)
        
        # 调用批量内容生成服务
        content_service = current_app.config["CONTENT_SERVICE"]
        result = content_service.generate_batch(
            validated_data.inputs,
            validated_data.count
        )
        
        return jsonify({"success": True, "data": result})
        
    except ValidationError as e:
        # 使用 format_validation_error 处理验证错误
        error_response = format_validation_error(e)
        return jsonify(error_response), 400


@api_bp.route("/generate_image", methods=["POST"])
@handle_errors
def generate_image() -> Tuple[Response, int]:
    """
    生成单张图片
    
    请求体示例:
    {
        "prompt": "老北京胡同，复古风格，温暖的阳光",
        "image_mode": "template",
        "template_style": "retro_chinese",
        "image_size": "vertical",
        "title": "老北京的记忆",
        "scene": "夕阳下的胡同",
        "content_text": "记得小时候...",
        "task_id": "task_20260213_001",
        "timestamp": "20260213_143000",
        "task_index": 0,
        "image_type": "content"
    }
    
    响应示例:
    {
        "success": true,
        "data": {
            "image_url": "/api/download/images/20260213/image_001.png",
            "task_id": "task_20260213_001"
        }
    }
    
    错误响应示例:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "输入数据验证失败",
            "errors": [
                {
                    "field": "timestamp",
                    "field_name": "时间戳",
                    "message": "时间戳格式必须为 YYYYMMDD_HHMMSS，例如：20260213_143000",
                    "suggestions": [
                        "时间戳格式必须为 YYYYMMDD_HHMMSS",
                        "示例：20260213_143000"
                    ],
                    "error_type": "value_error"
                }
            ],
            "total_errors": 1
        }
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 使用 Pydantic 模型验证请求数据
        validated_data = ImageGenerationRequest(**data)
        
        # 调用图片生成服务
        image_service = current_app.config["IMAGE_SERVICE"]
        params = _build_image_params(validated_data)
        result = image_service.generate_image(**params)
        
        return jsonify({"success": True, "data": result})
        
    except ValidationError as e:
        # 使用 format_validation_error 处理验证错误
        error_response = format_validation_error(e)
        return jsonify(error_response), 400


@api_bp.route("/models", methods=["GET"])
@handle_errors
def get_models() -> Tuple[Response, int]:
    """获取可用的模型列表"""
    image_service = current_app.config["IMAGE_SERVICE"]

    return jsonify(
        {"success": True, "models": image_service.available_models, "image_sizes": image_service.image_sizes}
    )


@api_bp.route("/download/<path:filename>", methods=["GET"])
@handle_errors
def download_image(filename: str) -> WerkzeugResponse:
    """下载生成的图片"""
    output_dir = current_app.config["OUTPUT_DIR"]
    file_path = output_dir / filename

    if not file_path.exists():
        raise ResourceNotFoundError(message="文件不存在", resource_type="图片文件", resource_id=filename)

    return send_file(file_path, as_attachment=True)


@api_bp.route("/logs/search", methods=["GET"])
@handle_errors
@validate_request(LogSearchRequest)
def search_logs(validated_data: LogSearchRequest) -> Tuple[Response, int]:
    """搜索日志"""
    log_path = _get_log_path()

    if not log_path.exists():
        return _empty_log_response(validated_data)

    logs = _parse_and_filter_logs(
        log_path,
        validated_data.level,
        validated_data.logger,
        validated_data.start_time,
        validated_data.end_time,
        validated_data.keyword,
    )

    return _paginate_logs(logs, validated_data)


@api_bp.route("/logs/stats", methods=["GET"])
@handle_errors
def get_log_stats() -> Tuple[Response, int]:
    """获取日志统计信息"""
    log_path = _get_log_path()

    if not log_path.exists():
        return jsonify({"success": True, "stats": {"total": 0, "error": 0, "warning": 0, "today": 0}})

    stats = _calculate_log_stats(log_path)
    return jsonify({"success": True, "stats": stats})


@api_bp.route("/logs/loggers", methods=["GET"])
@handle_errors
def get_loggers() -> Tuple[Response, int]:
    """获取所有日志来源列表"""
    log_path = _get_log_path()

    if not log_path.exists():
        return jsonify({"success": True, "loggers": []})

    loggers = _extract_loggers(log_path)
    return jsonify({"success": True, "loggers": sorted(list(loggers))})


@api_bp.route("/search", methods=["GET"])
@handle_errors
def search() -> Tuple[Response, int]:
    """
    通用搜索接口
    
    查询参数示例:
    - page: 页码（默认：1）
    - page_size: 每页数量（默认：50，范围：1-200）
    - keyword: 搜索关键词
    - start_time: 开始时间（ISO 8601 格式：YYYY-MM-DDTHH:MM:SS）
    - end_time: 结束时间（ISO 8601 格式：YYYY-MM-DDTHH:MM:SS）
    - sort_by: 排序字段（默认：created_at）
    - sort_order: 排序顺序（asc/desc，默认：desc）
    
    请求示例:
    GET /api/search?keyword=老北京&page=1&page_size=20&sort_order=desc
    
    响应示例:
    {
        "success": true,
        "data": {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0
        },
        "query": {
            "keyword": "老北京",
            "page": 1,
            "page_size": 20,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
    }
    
    错误响应示例:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "输入数据验证失败",
            "errors": [
                {
                    "field": "page_size",
                    "field_name": "每页数量",
                    "message": "每页数量必须小于或等于 200（当前：500）",
                    "suggestions": [
                        "请将每页数量设置为 200 或更小",
                        "建议使用 50-100 的页面大小以获得最佳性能"
                    ],
                    "error_type": "less_than_equal"
                }
            ],
            "total_errors": 1
        }
    }
    
    注意:
    - 此接口为通用搜索接口，当前返回空结果
    - 实际搜索功能需要在实现历史记录、模板管理等功能后集成
    - 接口已集成 SearchRequest 验证模型，确保输入安全
    """
    try:
        # 获取查询参数
        query_params = {
            "page": request.args.get("page", 1, type=int),
            "page_size": request.args.get("page_size", 50, type=int),
            "keyword": request.args.get("keyword"),
            "start_time": request.args.get("start_time"),
            "end_time": request.args.get("end_time"),
            "sort_by": request.args.get("sort_by", "created_at"),
            "sort_order": request.args.get("sort_order", "desc"),
        }
        
        # 使用 SearchRequest 模型验证查询参数
        validated_data = SearchRequest(**query_params)
        
        # TODO: 实际搜索逻辑
        # 当前返回空结果，待实现历史记录、模板管理等功能后集成
        items = []
        total = 0
        total_pages = 0
        
        return jsonify({
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": validated_data.page,
                "page_size": validated_data.page_size,
                "total_pages": total_pages,
            },
            "query": {
                "keyword": validated_data.keyword,
                "page": validated_data.page,
                "page_size": validated_data.page_size,
                "sort_by": validated_data.sort_by,
                "sort_order": validated_data.sort_order,
                "start_time": validated_data.start_time,
                "end_time": validated_data.end_time,
            }
        })
        
    except ValidationError as e:
        # 使用 format_validation_error 处理验证错误
        error_response = format_validation_error(e)
        return jsonify(error_response), 400


@api_bp.route("/batch/export/excel", methods=["POST"])
@handle_errors
def export_batch_excel() -> WerkzeugResponse:
    """
    导出批量生成结果为 Excel 文件
    
    请求体示例:
    {
        "batch_result": {
            "batch_id": "batch_20260213_143000",
            "total": 3,
            "results": [...],
            "summary": {...}
        }
    }
    
    响应:
    - 成功: 返回 Excel 文件下载
    - 失败: 返回错误 JSON
    
    注意:
    - 需要安装 openpyxl 库
    - 文件名格式: {batch_id}_summary.xlsx
    """
    try:
        data = request.get_json()
        batch_result = data.get("batch_result")
        
        if not batch_result:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "缺少 batch_result 参数",
                }
            }), 400
        
        # 导出为 Excel
        excel_data = ExportUtils.export_batch_to_excel(batch_result)
        
        # 生成文件名
        batch_id = batch_result.get("batch_id", "unknown")
        filename = f"{batch_id}_summary.xlsx"
        
        # 返回文件
        return Response(
            excel_data,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )
        
    except ImportError:
        return jsonify({
            "success": False,
            "error": {
                "code": "DEPENDENCY_MISSING",
                "message": "需要安装 openpyxl 库才能导出 Excel 文件",
                "suggestions": [
                    "运行命令: pip install openpyxl",
                    "或使用 ZIP 导出功能",
                ],
            }
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "EXPORT_ERROR",
                "message": f"导出失败: {str(e)}",
            }
        }), 500


@api_bp.route("/batch/export/zip", methods=["POST"])
@handle_errors
def export_batch_zip() -> WerkzeugResponse:
    """
    导出批量生成结果为 ZIP 压缩包
    
    包含内容:
    - Excel 汇总文件（如果 openpyxl 可用）
    - 批次信息文本文件
    - 所有生成的图片文件
    
    请求体示例:
    {
        "batch_result": {
            "batch_id": "batch_20260213_143000",
            "total": 3,
            "results": [...],
            "summary": {...}
        }
    }
    
    响应:
    - 成功: 返回 ZIP 文件下载
    - 失败: 返回错误 JSON
    
    注意:
    - 文件名格式: {batch_id}_export.zip
    """
    try:
        data = request.get_json()
        batch_result = data.get("batch_result")
        
        if not batch_result:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "缺少 batch_result 参数",
                }
            }), 400
        
        # 获取输出目录
        output_dir = current_app.config["OUTPUT_DIR"]
        
        # 创建 ZIP 包
        zip_data = ExportUtils.create_batch_zip(batch_result, output_dir)
        
        # 生成文件名
        batch_id = batch_result.get("batch_id", "unknown")
        filename = f"{batch_id}_export.zip"
        
        # 返回文件
        return Response(
            zip_data,
            mimetype="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/zip",
            }
        )
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "EXPORT_ERROR",
                "message": f"导出失败: {str(e)}",
            }
        }), 500


# ========== 辅助函数 ==========


def _build_image_params(validated_data: ImageGenerationRequest) -> Dict[str, Any]:
    """构建图片生成参数字典"""
    return {
        "prompt": validated_data.prompt,
        "image_mode": validated_data.image_mode,
        "image_model": validated_data.image_model,
        "template_style": validated_data.template_style,
        "image_size": validated_data.image_size,
        "title": validated_data.title,
        "scene": validated_data.scene,
        "content_text": validated_data.content_text,
        "task_id": validated_data.task_id,
        "timestamp": validated_data.timestamp,
        "task_index": validated_data.task_index,
        "image_type": validated_data.image_type,
    }


def _get_log_path() -> Path:
    """获取日志文件路径"""
    config_manager = current_app.config["CONFIG_MANAGER"]
    log_file = config_manager.get("logging.file", "logs/app.log")
    return Path(log_file)


def _empty_log_response(validated_data: LogSearchRequest) -> Tuple[Response, int]:
    """返回空日志响应"""
    return jsonify(
        {"success": True, "logs": [], "total": 0, "page": validated_data.page, "page_size": validated_data.page_size}
    )


def _paginate_logs(logs: List[Dict[str, Any]], validated_data: LogSearchRequest) -> Tuple[Response, int]:
    """对日志进行分页"""
    total = len(logs)
    start_idx = (validated_data.page - 1) * validated_data.page_size
    end_idx = start_idx + validated_data.page_size
    page_logs = logs[start_idx:end_idx]

    return jsonify(
        {
            "success": True,
            "logs": page_logs,
            "total": total,
            "page": validated_data.page,
            "page_size": validated_data.page_size,
        }
    )


def _parse_and_filter_logs(
    log_path: Path, level: str, logger_name: str, start_time: str, end_time: str, keyword: str
) -> List[Dict[str, Any]]:
    """解析和过滤日志"""
    logs: List[Dict[str, Any]] = []

    with open(log_path, "r", encoding="utf - 8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                log_entry = json.loads(line)

                # 应用过滤条件
                if level and log_entry.get("level") != level:
                    continue

                if logger_name and log_entry.get("logger") != logger_name:
                    continue

                if keyword and keyword.lower() not in log_entry.get("message", "").lower():
                    continue

                if start_time and not _check_time_after(log_entry.get("timestamp", ""), start_time):
                    continue

                if end_time and not _check_time_before(log_entry.get("timestamp", ""), end_time):
                    continue

                logs.append(log_entry)

            except (json.JSONDecodeError, TypeError, ValueError):
                continue

    # 按时间倒序排列（字符串比较即可，ISO格式天然支持）
    logs.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return logs


def _check_time_after(log_time_str: str, filter_time_str: str) -> bool:
    """检查日志时间是否在过滤时间之后"""
    try:
        log_time = datetime.fromisoformat(log_time_str)
        filter_time = datetime.fromisoformat(filter_time_str)
        return log_time >= filter_time
    except (ValueError, TypeError):
        return False


def _check_time_before(log_time_str: str, filter_time_str: str) -> bool:
    """检查日志时间是否在过滤时间之前"""
    try:
        log_time = datetime.fromisoformat(log_time_str)
        filter_time = datetime.fromisoformat(filter_time_str)
        return log_time <= filter_time
    except (ValueError, TypeError):
        return False


def _calculate_log_stats(log_path: Path) -> Dict[str, int]:
    """计算日志统计信息"""
    total = 0
    error_count = 0
    warning_count = 0
    today_count = 0
    today = datetime.now().date()

    with open(log_path, "r", encoding="utf - 8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                log_entry = json.loads(line)
                total += 1

                level = log_entry.get("level", "")
                if level in ["ERROR", "CRITICAL"]:
                    error_count += 1
                elif level == "WARNING":
                    warning_count += 1

                timestamp = log_entry.get("timestamp", "")
                if timestamp:
                    try:
                        log_date = datetime.fromisoformat(str(timestamp)).date()
                        if log_date == today:
                            today_count += 1
                    except (ValueError, TypeError):
                        pass

            except (json.JSONDecodeError, TypeError, ValueError):
                continue

    return {"total": total, "error": error_count, "warning": warning_count, "today": today_count}


def _extract_loggers(log_path: Path) -> Set[str]:
    """提取所有日志来源"""
    loggers: Set[str] = set()

    with open(log_path, "r", encoding="utf - 8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                log_entry = json.loads(line)
                logger_name = log_entry.get("logger", "")
                if logger_name:
                    loggers.add(logger_name)

            except (json.JSONDecodeError, TypeError, ValueError):
                continue

    return loggers
