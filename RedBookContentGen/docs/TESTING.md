# 测试指南

本文档介绍 RedBookContentGen 项目的测试框架和最佳实践。

## 目录

- [快速开始](#快速开始)
- [测试框架](#测试框架)
- [测试结构](#测试结构)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [测试覆盖率](#测试覆盖率)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 快速开始

### 安装测试依赖

```bash
pip install -r requirements.txt
```

### 运行所有测试

```bash
# 使用 pytest 直接运行
pytest

# 或使用测试脚本
./run_tests.sh
```

### 查看测试覆盖率

```bash
./run_tests.sh coverage
```

覆盖率报告将生成在 `htmlcov/index.html`，用浏览器打开即可查看。

## 测试框架

项目使用以下测试工具：

- **pytest**: 测试框架
- **pytest-cov**: 测试覆盖率
- **pytest-asyncio**: 异步测试支持
- **pytest-mock**: Mock 和 Stub 支持
- **pytest-xdist**: 并行测试执行
- **pytest-timeout**: 测试超时控制

## 测试结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_config_manager.py
│   ├── test_logger.py
│   └── ...
├── integration/             # 集成测试
│   ├── test_content_generation_flow.py
│   └── test_image_generation_flow.py
├── e2e/                     # 端到端测试
│   └── test_web_app.py
├── fixtures/                # 测试固件和辅助函数
│   ├── __init__.py
│   └── test_helpers.py
├── conftest.py              # pytest 配置和全局固件
├── test_environment.py      # 测试环境验证
└── README.md                # 测试目录说明
```

### 测试类型

#### 单元测试 (Unit Tests)

测试单个函数、类或模块的功能，不依赖外部服务。

**特点**:
- 快速执行（< 100ms）
- 完全隔离
- 使用 Mock 模拟外部依赖

**示例**:
```python
@pytest.mark.unit
def test_config_get_default_value():
    """测试获取默认配置值"""
    config = ConfigManager()
    assert config.get('api.timeout', 30) == 30
```

#### 集成测试 (Integration Tests)

测试多个模块协同工作的场景。

**特点**:
- 测试模块间交互
- 可能需要真实配置
- 执行时间较长（1-5秒）

**示例**:
```python
@pytest.mark.integration
def test_content_generation_flow():
    """测试内容生成完整流程"""
    generator = ContentGenerator(config)
    result = generator.generate("测试输入")
    assert result.titles
    assert result.content
```

#### 端到端测试 (E2E Tests)

测试完整的用户场景，从输入到输出。

**特点**:
- 模拟真实用户操作
- 需要完整运行环境
- 执行时间最长（> 5秒）

**示例**:
```python
@pytest.mark.e2e
def test_web_app_generation():
    """测试 Web 应用完整生成流程"""
    client = app.test_client()
    response = client.post('/api/generate', json={
        'input_text': '测试内容'
    })
    assert response.status_code == 200
```

## 运行测试

### 使用测试脚本（推荐）

```bash
# 运行所有测试
./run_tests.sh

# 只运行单元测试
./run_tests.sh unit

# 只运行集成测试
./run_tests.sh integration

# 只运行端到端测试
./run_tests.sh e2e

# 运行快速测试（跳过慢速测试）
./run_tests.sh fast

# 生成覆盖率报告
./run_tests.sh coverage

# 验证测试环境
./run_tests.sh env
```

### 使用 pytest 直接运行

```bash
# 运行所有测试
pytest

# 运行特定目录
pytest tests/unit

# 运行特定文件
pytest tests/unit/test_config_manager.py

# 运行特定测试
pytest tests/unit/test_config_manager.py::TestConfigManager::test_get_default_value

# 使用标记过滤
pytest -m unit              # 只运行单元测试
pytest -m "not slow"        # 跳过慢速测试
pytest -m "not api"         # 跳过需要 API 的测试

# 并行运行
pytest -n auto              # 使用所有 CPU 核心
pytest -n 4                 # 使用 4 个进程

# 详细输出
pytest -v                   # 详细模式
pytest -vv                  # 更详细模式
pytest -s                   # 显示 print 输出

# 只运行失败的测试
pytest --lf                 # last failed
pytest --ff                 # failed first

# 调试模式
pytest --pdb                # 失败时进入调试器
pytest -x                   # 第一个失败后停止
```

## 编写测试

### 测试命名规范

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试函数: `test_*`

### 基本测试结构

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块测试

测试 XXX 模块的功能
"""
import pytest
from src.module import SomeClass


@pytest.mark.unit
class TestSomeClass:
    """SomeClass 测试类"""
    
    def test_basic_functionality(self):
        """测试基本功能"""
        # Arrange (准备)
        obj = SomeClass()
        
        # Act (执行)
        result = obj.do_something()
        
        # Assert (断言)
        assert result == expected_value
    
    def test_error_handling(self):
        """测试错误处理"""
        obj = SomeClass()
        
        with pytest.raises(ValueError):
            obj.do_something_invalid()
```

### 使用 Fixture

Fixture 提供可重用的测试数据和设置。

```python
import pytest


@pytest.fixture
def sample_config():
    """提供测试配置"""
    return {
        "api_key": "test-key",
        "timeout": 30
    }


def test_with_fixture(sample_config):
    """使用 fixture 的测试"""
    assert sample_config["api_key"] == "test-key"
```

### 使用 Mock

Mock 用于模拟外部依赖。

```python
from unittest.mock import Mock, patch


def test_with_mock(mocker):
    """使用 mock 的测试"""
    # 使用 pytest-mock
    mock_api = mocker.patch('src.module.api_call')
    mock_api.return_value = {"status": "success"}
    
    result = some_function()
    
    assert result["status"] == "success"
    mock_api.assert_called_once()
```

### 参数化测试

参数化测试可以用不同的输入运行同一个测试。

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply_by_two(input, expected):
    """测试乘以2"""
    assert input * 2 == expected
```

### 异步测试

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await async_function()
    assert result == expected_value
```

### 测试标记

使用标记来分类和过滤测试。

```python
import pytest


@pytest.mark.unit
def test_unit():
    """单元测试"""
    pass


@pytest.mark.integration
def test_integration():
    """集成测试"""
    pass


@pytest.mark.slow
def test_slow_operation():
    """慢速测试"""
    pass


@pytest.mark.api
def test_api_call():
    """需要 API 密钥的测试"""
    pass


@pytest.mark.skip(reason="暂时跳过")
def test_skip():
    """跳过的测试"""
    pass


@pytest.mark.xfail(reason="已知问题")
def test_known_issue():
    """预期失败的测试"""
    pass
```

## 测试覆盖率

### 查看覆盖率

```bash
# 生成 HTML 报告
pytest --cov=src --cov-report=html

# 生成终端报告
pytest --cov=src --cov-report=term-missing

# 生成 XML 报告（用于 CI）
pytest --cov=src --cov-report=xml
```

### 覆盖率目标

- **整体覆盖率**: ≥ 70%
- **核心模块覆盖率**: ≥ 80%
- **工具函数覆盖率**: ≥ 90%

### 排除代码

某些代码不需要测试覆盖：

```python
def debug_function():  # pragma: no cover
    """调试函数，不需要测试"""
    print("Debug info")


if __name__ == "__main__":  # pragma: no cover
    main()
```

## 最佳实践

### 1. 测试应该快速

- 单元测试应该在 100ms 内完成
- 使用 Mock 避免真实的网络请求和文件 I/O
- 使用 `@pytest.mark.slow` 标记慢速测试

### 2. 测试应该独立

- 每个测试应该能够独立运行
- 不依赖其他测试的执行顺序
- 使用 fixture 提供测试数据

### 3. 测试应该可重复

- 测试结果应该是确定的
- 避免依赖当前时间、随机数等
- 使用固定的测试数据

### 4. 测试应该清晰

- 使用描述性的测试名称
- 遵循 Arrange-Act-Assert 模式
- 一个测试只测试一个功能点

### 5. 测试应该覆盖边界情况

- 空输入
- 最大/最小值
- 特殊字符
- 错误情况

### 6. 使用有意义的断言消息

```python
# 不好
assert result == expected

# 好
assert result == expected, f"期望 {expected}，实际 {result}"
```

### 7. 避免测试实现细节

测试应该关注行为，而不是实现。

```python
# 不好 - 测试实现细节
def test_internal_method():
    obj = MyClass()
    assert obj._internal_method() == "value"

# 好 - 测试公共接口
def test_public_behavior():
    obj = MyClass()
    assert obj.public_method() == expected_result
```

## 常见问题

### Q: 测试失败怎么办？

1. 查看错误信息
2. 使用 `-v` 参数查看详细输出
3. 使用 `-l` 参数查看本地变量
4. 使用 `--pdb` 参数进入调试模式

```bash
pytest tests/test_file.py -v -l --pdb
```

### Q: 如何跳过某个测试？

```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass
```

### Q: 如何只运行某些测试？

```bash
# 使用标记
pytest -m unit

# 使用文件名
pytest tests/unit/

# 使用测试名称
pytest -k "test_config"
```

### Q: 如何处理需要 API 密钥的测试？

```python
import os
import pytest


@pytest.mark.api
@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="需要 OPENAI_API_KEY 环境变量"
)
def test_api_call():
    """需要 API 密钥的测试"""
    pass
```

### Q: 如何测试异常？

```python
import pytest


def test_exception():
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("错误信息")
    
    assert "错误信息" in str(exc_info.value)
```

### Q: 如何测试日志输出？

```python
def test_logging(caplog):
    """测试日志输出"""
    logger.info("测试消息")
    
    assert "测试消息" in caplog.text
    assert caplog.records[0].levelname == "INFO"
```

### Q: 如何测试打印输出？

```python
def test_print(capsys):
    """测试打印输出"""
    print("Hello, World!")
    
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out
```

## 持续集成

测试会在以下情况自动运行：

- 提交代码到 Git 仓库
- 创建 Pull Request
- 合并到主分支

## 参考资料

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-mock 文档](https://pytest-mock.readthedocs.io/)
- [Python 测试最佳实践](https://docs.python-guide.org/writing/tests/)

## 贡献

如果你发现测试相关的问题或有改进建议，欢迎提交 Issue 或 Pull Request。
