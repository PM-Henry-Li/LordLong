#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试环境验证

验证测试环境是否正确配置
"""

import pytest
import sys
from pathlib import Path


@pytest.mark.unit
class TestEnvironment:
    """测试环境验证类"""

    def test_python_version(self):
        """测试 Python 版本"""
        assert sys.version_info >= (3, 10), "需要 Python 3.10 或更高版本"

    def test_project_structure(self):
        """测试项目结构"""
        project_root = Path(__file__).parent.parent

        # 检查关键目录
        assert (project_root / "src").exists(), "src 目录不存在"
        assert (project_root / "tests").exists(), "tests 目录不存在"
        assert (project_root / "config").exists(), "config 目录不存在"

        # 检查关键文件
        assert (project_root / "requirements.txt").exists(), "requirements.txt 不存在"
        assert (project_root / "pytest.ini").exists(), "pytest.ini 不存在"

    def test_imports(self):
        """测试关键模块导入"""
        try:
            import pytest
            import pytest_cov
            import pytest_asyncio
            import pytest_mock
        except ImportError as e:
            pytest.fail(f"导入失败: {e}")

    def test_fixtures_available(self, sample_config, sample_input_text):
        """测试固件是否可用"""
        assert sample_config is not None, "sample_config 固件不可用"
        assert sample_input_text is not None, "sample_input_text 固件不可用"
        assert isinstance(sample_config, dict), "sample_config 应该是字典"
        assert isinstance(sample_input_text, str), "sample_input_text 应该是字符串"

    def test_temp_dir_fixture(self, temp_dir):
        """测试临时目录固件"""
        assert temp_dir.exists(), "临时目录不存在"
        assert temp_dir.is_dir(), "临时目录不是目录"

        # 测试可以在临时目录中创建文件
        test_file = temp_dir / "test.txt"
        test_file.write_text("测试内容", encoding="utf-8")
        assert test_file.exists(), "无法在临时目录中创建文件"
        assert test_file.read_text(encoding="utf-8") == "测试内容"


@pytest.mark.unit
class TestHelpers:
    """测试辅助函数"""

    def test_generate_test_hash(self):
        """测试哈希生成"""
        from tests.fixtures.test_helpers import generate_test_hash

        hash1 = generate_test_hash("test")
        hash2 = generate_test_hash("test")
        hash3 = generate_test_hash("different")

        assert hash1 == hash2, "相同输入应该生成相同哈希"
        assert hash1 != hash3, "不同输入应该生成不同哈希"
        assert len(hash1) == 64, "SHA256 哈希应该是 64 个字符"

    def test_normalize_whitespace(self):
        """测试空白字符规范化"""
        from tests.fixtures.test_helpers import normalize_whitespace

        text = "  这是   一个  \n  测试  \t  文本  "
        normalized = normalize_whitespace(text)

        assert normalized == "这是 一个 测试 文本"

    def test_count_chinese_chars(self):
        """测试中文字符统计"""
        from tests.fixtures.test_helpers import count_chinese_chars

        text = "Hello 世界 123 测试"
        count = count_chinese_chars(text)

        assert count == 4, f"应该有 4 个中文字符，实际: {count}"

    def test_is_valid_json(self):
        """测试 JSON 验证"""
        from tests.fixtures.test_helpers import is_valid_json

        assert is_valid_json('{"key": "value"}') is True
        assert is_valid_json('{"key": "value"') is False
        assert is_valid_json("not json") is False

    def test_mock_logger(self):
        """测试模拟日志记录器"""
        from tests.fixtures.test_helpers import MockLogger

        logger = MockLogger()

        logger.info("测试信息")
        logger.error("测试错误")

        assert len(logger.get_logs("info")) == 1
        assert len(logger.get_logs("error")) == 1
        assert logger.get_logs("info")[0]["message"] == "测试信息"

        logger.clear()
        assert len(logger.get_logs("info")) == 0

    def test_mock_cache(self):
        """测试模拟缓存"""
        from tests.fixtures.test_helpers import MockCache

        cache = MockCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.exists("key1") is True

        cache.delete("key1")
        assert cache.get("key1") is None
        assert cache.exists("key1") is False


@pytest.mark.unit
def test_basic_assertion():
    """测试基本断言"""
    assert 1 + 1 == 2
    assert "hello" in "hello world"
    assert [1, 2, 3] == [1, 2, 3]


@pytest.mark.unit
def test_exception_handling():
    """测试异常处理"""
    with pytest.raises(ValueError):
        raise ValueError("测试异常")

    with pytest.raises(ZeroDivisionError):
        _ = 1 / 0


@pytest.mark.unit
@pytest.mark.parametrize(
    "input,expected",
    [
        (1, 2),
        (2, 4),
        (3, 6),
        (4, 8),
    ],
)
def test_parametrize(input, expected):
    """测试参数化测试"""
    assert input * 2 == expected


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
