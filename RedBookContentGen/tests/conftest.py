#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置文件

提供全局的测试固件和配置
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# 配置固件
# ============================================================================


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """提供示例配置"""
    return {
        "api": {
            "openai": {
                "key": "test-api-key",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-plus",
                "timeout": 30,
                "max_retries": 3,
            },
            "image": {"model": "wan2.2-t2i-flash", "size": "1024*1365", "timeout": 180},
        },
        "cache": {"enabled": True, "ttl": 3600, "max_size": "1GB"},
        "rate_limit": {
            "openai": {"requests_per_minute": 60, "tokens_per_minute": 90000},
            "image": {"requests_per_minute": 10},
        },
        "logging": {
            "level": "INFO",
            "format": "json",
            "file": "logs/app.log",
            "max_bytes": 10485760,
            "backup_count": 5,
        },
    }


@pytest.fixture
def mock_config_file(temp_dir, sample_config):
    """创建临时配置文件"""
    import json

    config_file = temp_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    return config_file


# ============================================================================
# 环境变量固件
# ============================================================================


@pytest.fixture
def clean_env(monkeypatch):
    """清理环境变量"""
    env_vars = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "RATE_LIMIT_OPENAI_RPM",
        "CACHE_ENABLED",
        "LOG_LEVEL",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def mock_env(monkeypatch):
    """设置模拟环境变量"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-from-env")
    monkeypatch.setenv("OPENAI_MODEL", "qwen-max")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    yield


# ============================================================================
# 测试数据固件
# ============================================================================


@pytest.fixture
def sample_input_text() -> str:
    """提供示例输入文本"""
    return """
    记得小时候，老北京的胡同里总是充满了生活的气息。
    清晨，卖豆腐的吆喝声从巷子深处传来，悠长而亲切。
    邻里之间串门聊天，孩子们在胡同里追逐嬉戏。
    那时候的生活虽然简单，但充满了人情味。
    """


@pytest.fixture
def sample_content_result() -> Dict[str, Any]:
    """提供示例内容生成结果"""
    return {
        "titles": ["胡同里的老北京记忆 🏮", "那些年，我们一起走过的胡同", "老北京胡同：时光里的温暖"],
        "content": "记得小时候的老北京胡同吗？清晨的豆腐吆喝声...",
        "tags": ["#老北京", "#胡同文化", "#童年回忆", "#北京生活"],
        "image_prompts": [
            "老北京胡同清晨场景，阳光洒在青砖灰瓦上",
            "胡同里的孩子们在玩耍，充满生活气息",
            "传统北京四合院，红门绿瓦",
        ],
    }


@pytest.fixture
def sample_image_prompt() -> str:
    """提供示例图片提示词"""
    return "老北京胡同清晨场景，阳光洒在青砖灰瓦上，复古摄影风格"


# ============================================================================
# Mock 固件
# ============================================================================


@pytest.fixture
def mock_openai_response():
    """模拟 OpenAI API 响应"""

    class MockResponse:
        def __init__(self):
            self.choices = [
                type(
                    "obj",
                    (object,),
                    {
                        "message": type(
                            "obj", (object,), {"content": '{"titles": ["测试标题"], "content": "测试内容"}'}
                        )()
                    },
                )()
            ]

    return MockResponse()


@pytest.fixture
def mock_image_api_response():
    """模拟图片生成 API 响应"""
    return {
        "output": {
            "task_id": "test-task-id-123",
            "task_status": "SUCCEEDED",
            "results": [{"url": "https://example.com/image.jpg"}],
        }
    }


# ============================================================================
# 跳过条件
# ============================================================================


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试（超过1秒）")
    config.addinivalue_line("markers", "api: 需要API密钥的测试")
    config.addinivalue_line("markers", "network: 需要网络连接的测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 如果没有 API Key，跳过需要 API 的测试
    if not os.getenv("OPENAI_API_KEY"):
        skip_api = pytest.mark.skip(reason="需要 OPENAI_API_KEY 环境变量")
        for item in items:
            if "api" in item.keywords:
                item.add_marker(skip_api)

    # 如果指定了快速模式，跳过慢速测试
    if config.getoption("-m") == "not slow":
        skip_slow = pytest.mark.skip(reason="跳过慢速测试")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


# ============================================================================
# 测试报告钩子
# ============================================================================


def pytest_report_header(config):
    """添加测试报告头部信息"""
    return ["RedBookContentGen 测试套件", f"Python 版本: {sys.version}", f"项目根目录: {project_root}"]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告"""
    outcome = yield
    rep = outcome.get_result()

    # 为失败的测试添加额外信息
    if rep.when == "call" and rep.failed:
        # 可以在这里添加截图、日志等
        pass
