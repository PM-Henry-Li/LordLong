# 测试目录说明

本目录包含 RedBookContentGen 项目的所有测试代码。

## 目录结构

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
│   ├── mock_data.py
│   └── test_helpers.py
├── test_ai_rewrite.py       # AI重写功能测试
├── test_text_overlay.py     # 文字叠加测试
└── verify_fix.py            # 修复验证测试
```

## 测试类型

### 单元测试 (unit/)
测试单个函数、类或模块的功能，不依赖外部服务。

**特点**:
- 快速执行
- 隔离性强
- 使用 Mock 模拟外部依赖

**运行方式**:
```bash
pytest tests/unit -m unit
```

### 集成测试 (integration/)
测试多个模块协同工作的场景。

**特点**:
- 测试模块间交互
- 可能需要真实的配置文件
- 执行时间较长

**运行方式**:
```bash
pytest tests/integration -m integration
```

### 端到端测试 (e2e/)
测试完整的用户场景，从输入到输出。

**特点**:
- 模拟真实用户操作
- 需要完整的运行环境
- 执行时间最长

**运行方式**:
```bash
pytest tests/e2e -m e2e
```

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定类型的测试
```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 只运行端到端测试
pytest -m e2e
```

### 运行特定文件
```bash
pytest tests/unit/test_config_manager.py
```

### 运行特定测试函数
```bash
pytest tests/unit/test_config_manager.py::TestConfigManager::test_get_default_value
```

### 查看测试覆盖率
```bash
pytest --cov=src --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

### 并行运行测试
```bash
pytest -n auto
```

### 运行慢速测试
```bash
pytest -m slow
```

### 跳过需要网络的测试
```bash
pytest -m "not network"
```

### 跳过需要API密钥的测试
```bash
pytest -m "not api"
```

## 测试标记

使用 pytest 标记来分类测试：

```python
import pytest

@pytest.mark.unit
def test_something():
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
    """需要API密钥的测试"""
    pass

@pytest.mark.network
def test_network_request():
    """需要网络连接的测试"""
    pass

@pytest.mark.asyncio
async def test_async_function():
    """异步测试"""
    pass
```

## 编写测试

### 测试命名规范
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试函数: `test_*`

### 测试结构
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块测试

测试 XXX 模块的功能
"""
import pytest
from src.module import SomeClass

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

### Mock 外部依赖
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

## 测试覆盖率目标

- 整体覆盖率: ≥ 70%
- 核心模块覆盖率: ≥ 80%
- 工具函数覆盖率: ≥ 90%

## 持续集成

测试会在以下情况自动运行：
- 提交代码到 Git 仓库
- 创建 Pull Request
- 合并到主分支

## 常见问题

### 测试失败怎么办？
1. 查看错误信息
2. 使用 `-v` 参数查看详细输出
3. 使用 `-l` 参数查看本地变量
4. 使用 `--pdb` 参数进入调试模式

### 如何跳过某个测试？
```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass
```

### 如何标记预期失败的测试？
```python
@pytest.mark.xfail(reason="已知问题")
def test_known_issue():
    pass
```

## 参考资料

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-mock 文档](https://pytest-mock.readthedocs.io/)
