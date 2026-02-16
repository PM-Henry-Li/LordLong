#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试辅助函数

提供测试中常用的辅助函数和工具
"""

import json
import hashlib
from typing import Any, Dict, List
from pathlib import Path


def generate_test_hash(data: str) -> str:
    """
    生成测试数据的哈希值

    Args:
        data: 输入数据

    Returns:
        哈希值
    """
    return hashlib.sha256(data.encode()).hexdigest()


def load_test_data(filename: str) -> Any:
    """
    加载测试数据文件

    Args:
        filename: 文件名

    Returns:
        测试数据
    """
    test_data_dir = Path(__file__).parent.parent / "fixtures"
    file_path = test_data_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"测试数据文件不存在: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        if filename.endswith(".json"):
            return json.load(f)
        else:
            return f.read()


def create_mock_response(status_code: int = 200, data: Dict = None) -> Any:
    """
    创建模拟的 HTTP 响应对象

    Args:
        status_code: 状态码
        data: 响应数据

    Returns:
        模拟响应对象
    """

    class MockResponse:
        def __init__(self, status_code: int, data: Dict):
            self.status_code = status_code
            self._data = data or {}

        def json(self):
            return self._data

        @property
        def text(self):
            return json.dumps(self._data)

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    return MockResponse(status_code, data)


def assert_dict_contains(actual: Dict, expected: Dict) -> None:
    """
    断言字典包含预期的键值对

    Args:
        actual: 实际字典
        expected: 预期包含的键值对

    Raises:
        AssertionError: 如果不包含预期的键值对
    """
    for key, value in expected.items():
        assert key in actual, f"缺少键: {key}"
        if isinstance(value, dict):
            assert_dict_contains(actual[key], value)
        else:
            assert actual[key] == value, f"键 {key} 的值不匹配: {actual[key]} != {value}"


def assert_list_contains_items(actual: List, expected_items: List) -> None:
    """
    断言列表包含预期的元素

    Args:
        actual: 实际列表
        expected_items: 预期包含的元素

    Raises:
        AssertionError: 如果不包含预期的元素
    """
    for item in expected_items:
        assert item in actual, f"列表中缺少元素: {item}"


def normalize_whitespace(text: str) -> str:
    """
    规范化文本中的空白字符

    Args:
        text: 输入文本

    Returns:
        规范化后的文本
    """
    return " ".join(text.split())


def create_temp_file(temp_dir: Path, filename: str, content: str) -> Path:
    """
    创建临时测试文件

    Args:
        temp_dir: 临时目录
        filename: 文件名
        content: 文件内容

    Returns:
        文件路径
    """
    file_path = temp_dir / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


def count_chinese_chars(text: str) -> int:
    """
    统计文本中的中文字符数量

    Args:
        text: 输入文本

    Returns:
        中文字符数量
    """
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def is_valid_json(text: str) -> bool:
    """
    检查字符串是否为有效的 JSON

    Args:
        text: 输入字符串

    Returns:
        是否为有效 JSON
    """
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def mock_api_call(success: bool = True, data: Dict = None, error_msg: str = None):
    """
    模拟 API 调用

    Args:
        success: 是否成功
        data: 返回数据
        error_msg: 错误信息

    Returns:
        模拟的 API 响应
    """
    if success:
        return {"success": True, "data": data or {}, "error": None}
    else:
        return {"success": False, "data": None, "error": error_msg or "API 调用失败"}


class MockLogger:
    """模拟日志记录器"""

    def __init__(self):
        self.logs = {"debug": [], "info": [], "warning": [], "error": []}

    def debug(self, message: str, **kwargs):
        self.logs["debug"].append({"message": message, "context": kwargs})

    def info(self, message: str, **kwargs):
        self.logs["info"].append({"message": message, "context": kwargs})

    def warning(self, message: str, **kwargs):
        self.logs["warning"].append({"message": message, "context": kwargs})

    def error(self, message: str, **kwargs):
        self.logs["error"].append({"message": message, "context": kwargs})

    def get_logs(self, level: str = None) -> List[Dict]:
        """获取日志记录"""
        if level:
            return self.logs.get(level, [])
        return self.logs

    def clear(self):
        """清空日志"""
        for level in self.logs:
            self.logs[level] = []


class MockCache:
    """模拟缓存"""

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = None):
        self._cache[key] = value

    def delete(self, key: str):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def exists(self, key: str) -> bool:
        return key in self._cache
