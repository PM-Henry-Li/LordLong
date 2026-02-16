#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主页面蓝图
处理页面渲染相关的路由
"""

from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index() -> str:
    """首页"""
    # 获取图片服务实例（从应用上下文）
    image_service = current_app.config["IMAGE_SERVICE"]

    # 读取默认输入文案
    import os
    default_input_text = ""
    try:
        input_path = os.path.join(os.getcwd(), "input", "input_content.txt")
        if os.path.exists(input_path):
            with open(input_path, "r", encoding="utf-8") as f:
                default_input_text = f.read().strip()
    except Exception as e:
        print(f"Error reading input_content.txt: {e}")

    return render_template(
        "index.html",
        models=image_service.available_models,
        image_sizes=image_service.image_sizes,
        default_input_text=default_input_text
    )


@main_bp.route("/logs")
def logs_page() -> str:
    """日志查询页面"""
    return render_template("logs.html")


@main_bp.route("/batch")
def batch_page() -> str:
    """批量生成页面"""
    return render_template("batch.html")
