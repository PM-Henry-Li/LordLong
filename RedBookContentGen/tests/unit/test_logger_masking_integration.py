#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志脱敏集成测试

测试日志系统中的脱敏功能是否正常工作
"""

import sys
import json
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import Logger, LogContext, mask_sensitive_data


def test_logger_with_sensitive_data():
    """测试日志记录器对敏感数据的脱敏"""
    print("测试日志记录器脱敏功能...")
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        # 初始化日志系统（使用 JSON 格式便于解析）
        from src.core.config_manager import ConfigManager
        
        config = ConfigManager()
        config.set('logging.level', 'INFO')
        config.set('logging.format', 'json')
        config.set('logging.file', log_file)
        
        Logger.initialize(config)
        
        # 记录包含敏感信息的日志
        Logger.info(
            "用户登录",
            logger_name="test",
            api_key="sk-abc123def456ghi789jkl012mno345pqr678",
            password="MyPassword123",
            email="user@example.com",
            phone="13812345678"
        )
        
        # 读取日志文件
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 解析 JSON 日志
        log_lines = [line for line in log_content.strip().split('\n') if line]
        if log_lines:
            last_log = json.loads(log_lines[-1])
            
            # 验证敏感信息已被脱敏
            assert last_log.get('api_key') == "sk-***r678", f"API Key 未正确脱敏: {last_log.get('api_key')}"
            assert last_log.get('password') == "***", f"密码未正确脱敏: {last_log.get('password')}"
            assert last_log.get('email') == "u***@example.com", f"邮箱未正确脱敏: {last_log.get('email')}"
            assert last_log.get('phone') == "138****5678", f"手机号未正确脱敏: {last_log.get('phone')}"
            
            print("✅ 日志记录器脱敏测试通过")
        else:
            print("⚠️  警告：未找到日志记录")
    
    finally:
        # 清理临时文件
        Path(log_file).unlink(missing_ok=True)


def test_log_context_with_sensitive_data():
    """测试日志上下文中的敏感数据脱敏"""
    print("测试日志上下文脱敏功能...")
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        # 初始化日志系统
        from src.core.config_manager import ConfigManager
        
        config = ConfigManager()
        config.set('logging.level', 'INFO')
        config.set('logging.format', 'json')
        config.set('logging.file', log_file)
        
        Logger.initialize(config)
        
        # 使用日志上下文
        with LogContext(
            api_key="sk-abc123def456ghi789jkl012mno345pqr678",
            password="secret",
            user_id="user123"
        ):
            Logger.info("处理请求", logger_name="test")
        
        # 读取日志文件
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 解析 JSON 日志
        log_lines = [line for line in log_content.strip().split('\n') if line]
        if log_lines:
            last_log = json.loads(log_lines[-1])
            
            # 验证上下文中的敏感信息已被脱敏
            context = last_log.get('context', {})
            assert context.get('api_key') == "sk-***r678", f"上下文中的 API Key 未正确脱敏: {context.get('api_key')}"
            assert context.get('password') == "***", f"上下文中的密码未正确脱敏: {context.get('password')}"
            assert context.get('user_id') == "user123", f"上下文中的 user_id 不应被脱敏: {context.get('user_id')}"
            
            print("✅ 日志上下文脱敏测试通过")
        else:
            print("⚠️  警告：未找到日志记录")
    
    finally:
        # 清理临时文件
        Path(log_file).unlink(missing_ok=True)


def test_nested_sensitive_data():
    """测试嵌套结构中的敏感数据脱敏"""
    print("测试嵌套结构脱敏功能...")
    
    # 创建临时日志文件
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        # 初始化日志系统
        from src.core.config_manager import ConfigManager
        
        config = ConfigManager()
        config.set('logging.level', 'INFO')
        config.set('logging.format', 'json')
        config.set('logging.file', log_file)
        
        Logger.initialize(config)
        
        # 记录包含嵌套敏感信息的日志
        Logger.info(
            "用户配置",
            logger_name="test",
            config={
                "api_key": "sk-abc123def456ghi789jkl012mno345pqr678",
                "database": {
                    "url": "postgresql://user:password@host:5432/db",
                    "password": "dbpass123"
                },
                "users": [
                    {"email": "user1@example.com", "phone": "13812345678"},
                    {"email": "user2@example.com", "phone": "19987654321"}
                ]
            }
        )
        
        # 读取日志文件
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 解析 JSON 日志
        log_lines = [line for line in log_content.strip().split('\n') if line]
        if log_lines:
            last_log = json.loads(log_lines[-1])
            
            # 验证嵌套结构中的敏感信息已被脱敏
            config_data = last_log.get('config', {})
            assert config_data.get('api_key') == "sk-***r678", f"嵌套的 API Key 未正确脱敏"
            assert config_data.get('database', {}).get('url') == "postgresql://user:***@host:5432/db", f"数据库 URL 未正确脱敏"
            assert config_data.get('database', {}).get('password') == "***", f"数据库密码未正确脱敏"
            assert config_data.get('users', [])[0].get('email') == "u***@example.com", f"用户邮箱未正确脱敏"
            assert config_data.get('users', [])[0].get('phone') == "138****5678", f"用户手机号未正确脱敏"
            
            print("✅ 嵌套结构脱敏测试通过")
        else:
            print("⚠️  警告：未找到日志记录")
    
    finally:
        # 清理临时文件
        Path(log_file).unlink(missing_ok=True)


def run_all_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("开始测试日志脱敏集成功能")
    print("=" * 60)
    print()
    
    try:
        test_logger_with_sensitive_data()
        test_log_context_with_sensitive_data()
        test_nested_sensitive_data()
        
        print()
        print("=" * 60)
        print("✅ 所有集成测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 测试出错: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
