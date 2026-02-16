#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书内容生成 Web 应用
提供网页界面进行文字输入和内容生成
"""

from pathlib import Path
from typing import Optional
from flask import Flask
from flasgger import Swagger

# 导入现有模块
from src.core.config_manager import ConfigManager
from src.core.logger import Logger
from src.services import ContentService, ImageService
from src.web.blueprints import api_bp, main_bp
from src.web.error_handlers import register_error_handlers


def create_app(config_path: Optional[str] = "config/config.json") -> Flask:
    """
    创建并配置 Flask 应用
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置好的 Flask 应用实例
    """
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size
    
    # 初始化配置管理器
    config_manager = ConfigManager(config_path)
    app.config['CONFIG_MANAGER'] = config_manager
    
    # 初始化日志系统
    Logger.initialize(config_manager)
    
    # 确保输出目录存在
    output_dir = Path("output/web")
    output_dir.mkdir(parents=True, exist_ok=True)
    app.config['OUTPUT_DIR'] = output_dir
    
    # 初始化服务层
    content_service = ContentService(config_manager, output_dir)
    image_service = ImageService(config_manager, output_dir)
    app.config['CONTENT_SERVICE'] = content_service
    app.config['IMAGE_SERVICE'] = image_service
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # 配置 Swagger UI
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs",
        "title": "RedBookContentGen API",
        "version": "1.0.0",
        "description": "老北京文化主题的小红书内容生成工具 API",
        "termsOfService": "",
        "contact": {
            "name": "RedBookContentGen 项目",
        },
        "license": {
            "name": "MIT",
        },
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "RedBookContentGen API",
            "description": "老北京文化主题的小红书内容生成工具 API",
            "version": "1.0.0",
            "contact": {
                "name": "RedBookContentGen 项目",
            },
            "license": {
                "name": "MIT",
            },
        },
        "host": "localhost:8080",
        "basePath": "/",
        "schemes": ["http"],
        "tags": [
            {"name": "内容生成", "description": "小红书内容生成相关接口"},
            {"name": "图片生成", "description": "图片生成和下载相关接口"},
            {"name": "批量处理", "description": "批量生成和导出相关接口"},
            {"name": "日志管理", "description": "日志查询和统计相关接口"},
            {"name": "系统信息", "description": "系统配置和模型信息"},
        ],
    }
    
    # 初始化 Swagger
    Swagger(app, config=swagger_config, template=swagger_template)
    
    # 注册全局错误处理器
    register_error_handlers(app)
    
    return app


# 创建应用实例
app = create_app()




def main() -> None:
    """启动Web应用"""
    Logger.info("=" * 60, logger_name="web_app")
    Logger.info("小红书内容生成 Web 应用", logger_name="web_app")
    Logger.info("=" * 60, logger_name="web_app")
    Logger.info("访问地址: http://localhost:8080", logger_name="web_app")
    Logger.info("API 文档: http://localhost:8080/api/docs", logger_name="web_app")
    Logger.info("按 Ctrl+C 停止服务", logger_name="web_app")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()

