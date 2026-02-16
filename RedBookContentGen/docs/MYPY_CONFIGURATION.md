# Mypy 类型检查配置文档

## 概述

本项目使用 mypy 进行静态类型检查，以提高代码质量和可维护性。配置文件为 `mypy.ini`。

## 配置说明

### 基础配置

- **Python 版本**: 3.10
- **缓存目录**: `.mypy_cache`
- **错误显示**: 显示错误代码、列号和上下文

### 严格模式

项目采用渐进式严格模式：

#### 核心模块（严格检查）

以下模块启用了严格的类型检查：

- `src.core.config_manager` - 配置管理器
- `src.core.logger` - 日志系统
- `src.core.cache_manager` - 缓存管理器
- `src.core.rate_limiter` - 速率限制器
- `src.core.api_handler` - API 处理器
- `src.core.retry_handler` - 重试处理器
- `src.core.exceptions` - 异常定义

这些模块要求：
- 所有函数必须有类型注解（`disallow_untyped_defs = True`）
- 警告任何返回值（`warn_return_any = True`）
- 警告不可达代码（`warn_unreachable = True`）

#### 业务模块（宽松检查）

以下模块采用宽松的类型检查：

- `src.content_generator` - 内容生成器
- `src.image_generator` - 图片生成器
- `src.async_image_service` - 异步图片服务
- `web_app` - Web 应用

这些模块：
- 不强制要求所有函数有类型注解
- 但仍然警告返回值类型

### 第三方库忽略规则

以下第三方库没有类型存根，已配置忽略：

- `openpyxl` - Excel 操作库
- `PIL` - 图片处理库
- `selenium` - 浏览器自动化
- `flask_socketio` - WebSocket 支持
- `flask_cors` - CORS 支持
- `aiohttp` - 异步 HTTP 客户端
- `openai` - OpenAI API 客户端
- `requests` - HTTP 请求库
- `pydantic` - 数据验证库

### 排除的文件和目录

以下文件和目录不进行类型检查：

- 虚拟环境目录：`.venv/`, `venv/`, `env/`
- 构建目录：`build/`, `dist/`, `.eggs/`, `.tox/`
- 缓存目录：`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`
- 输出目录：`output/`, `test_output/`, `htmlcov/`, `logs/`
- 调试脚本：`debug_*.py`, `check_type_annotations.py`, `test_log_api.py`

## 使用方法

### 安装 mypy

```bash
pip install mypy>=1.8.0
```

或者安装所有依赖：

```bash
pip install -r requirements.txt
```

### 检查单个文件

```bash
python3 -m mypy src/core/config_manager.py
```

### 检查整个模块

```bash
python3 -m mypy src/core/
```

### 检查整个项目

```bash
python3 -m mypy src/
```

### 使用配置文件

```bash
python3 -m mypy --config-file mypy.ini src/
```

### 安装缺失的类型存根

如果遇到缺失类型存根的警告，可以安装对应的类型包：

```bash
# 安装 PyYAML 的类型存根
python3 -m pip install types-PyYAML

# 安装 requests 的类型存根
python3 -m pip install types-requests

# 安装 openpyxl 的类型存根
python3 -m pip install types-openpyxl

# 或者一次性安装所有缺失的类型存根
python3 -m mypy --install-types
```

## 常见错误及解决方法

### 1. 缺少类型注解

**错误信息**:
```
error: Function is missing a type annotation [no-untyped-def]
```

**解决方法**:
```python
# 错误
def my_function(x):
    return x + 1

# 正确
def my_function(x: int) -> int:
    return x + 1
```

### 2. 返回值类型不匹配

**错误信息**:
```
error: Incompatible return value type (got "str", expected "int") [return-value]
```

**解决方法**:
```python
# 错误
def get_number() -> int:
    return "123"

# 正确
def get_number() -> int:
    return 123
```

### 3. 可选值未检查

**错误信息**:
```
error: Item "None" of "str | None" has no attribute "upper" [union-attr]
```

**解决方法**:
```python
# 错误
def process(text: Optional[str]) -> str:
    return text.upper()

# 正确
def process(text: Optional[str]) -> str:
    if text is None:
        return ""
    return text.upper()
```

### 4. 使用 Any 类型

**错误信息**:
```
error: Returning Any from function declared to return "str" [return-any]
```

**解决方法**:
```python
from typing import Any, cast

# 如果确实需要使用 Any，可以使用 cast
def process(data: Any) -> str:
    return cast(str, data)

# 或者添加类型忽略注释（不推荐）
def process(data: Any) -> str:
    return data  # type: ignore
```

## 渐进式迁移策略

### 阶段 1：核心模块（已完成）

核心模块已经启用严格类型检查，包括：
- 配置管理
- 日志系统
- 缓存管理
- 速率限制
- API 处理
- 异常定义

### 阶段 2：业务模块（进行中）

逐步为业务模块添加类型注解：
1. 为所有公共方法添加类型注解
2. 为所有私有方法添加类型注解
3. 为复杂的局部变量添加类型注解
4. 启用 `disallow_untyped_defs = True`

### 阶段 3：测试模块（计划中）

为测试模块添加类型注解，提高测试代码质量。

## 集成到 CI/CD

### GitHub Actions 示例

```yaml
name: Type Check

on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run mypy
        run: |
          python3 -m mypy src/
```

### Pre-commit Hook 示例

在 `.pre-commit-config.yaml` 中添加：

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--config-file=mypy.ini]
        additional_dependencies: [types-PyYAML, types-requests]
```

## 最佳实践

### 1. 优先使用具体类型

```python
# 不推荐
def process(data: Any) -> Any:
    return data

# 推荐
def process(data: Dict[str, str]) -> List[str]:
    return list(data.values())
```

### 2. 使用 Optional 表示可选值

```python
from typing import Optional

# 推荐
def find_user(user_id: int) -> Optional[User]:
    # 可能返回 None
    return None
```

### 3. 使用 Union 表示多种类型

```python
from typing import Union

def process(value: Union[int, str]) -> str:
    if isinstance(value, int):
        return str(value)
    return value
```

### 4. 使用泛型提高灵活性

```python
from typing import TypeVar, List

T = TypeVar('T')

def first(items: List[T]) -> Optional[T]:
    return items[0] if items else None
```

### 5. 使用 Protocol 定义接口

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None:
        ...

def render(obj: Drawable) -> None:
    obj.draw()
```

## 参考资料

- [Mypy 官方文档](https://mypy.readthedocs.io/)
- [Python 类型提示 PEP 484](https://www.python.org/dev/peps/pep-0484/)
- [Python 类型系统最佳实践](https://docs.python.org/3/library/typing.html)

## 更新日志

- **2026-02-13**: 创建 mypy 配置文件和文档
  - 配置渐进式严格模式
  - 为核心模块启用严格检查
  - 配置第三方库忽略规则
  - 添加使用文档和最佳实践
