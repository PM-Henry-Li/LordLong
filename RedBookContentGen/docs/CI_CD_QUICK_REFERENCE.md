# CI/CD 快速参考指南

## 🚀 快速开始

### 提交代码前

```bash
# 运行完整检查（推荐）
./scripts/pre-commit-check.sh

# 或者只运行类型检查
mypy src/ --config-file=mypy.ini
```

### 查看 CI 状态

1. 访问: `https://github.com/your-username/RedBookContentGen/actions`
2. 查看最新的工作流运行状态

## 📋 常用命令

### 类型检查

```bash
# 基础检查
mypy src/ --config-file=mypy.ini

# 显示详细错误
mypy src/ --config-file=mypy.ini --show-error-codes --pretty

# 生成 HTML 报告
mypy src/ --config-file=mypy.ini --html-report mypy-report

# 检查特定文件
mypy src/content_generator.py --config-file=mypy.ini
```

### 代码质量

```bash
# Flake8 检查
flake8 src/ --count --statistics

# Pylint 检查
pylint src/ --exit-zero

# Black 格式化
black src/ tests/

# Black 检查（不修改）
black --check src/ tests/
```

### 测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定测试文件
pytest tests/unit/test_config_manager.py -v

# 生成覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html

# 运行快速测试（跳过慢速测试）
pytest tests/unit/ -v -m "not slow"
```

## 🔍 CI 工作流

### 触发条件

| 事件 | 分支 | 说明 |
|------|------|------|
| Push | main, develop | 自动触发完整 CI |
| Pull Request | main, develop | 自动触发完整 CI |
| 手动触发 | 任意 | 在 Actions 页面手动运行 |

### 检查步骤

| 步骤 | 必须通过 | 说明 |
|------|----------|------|
| 代码质量检查 | ❌ | Flake8/Pylint，失败仅警告 |
| **类型检查** | **✅** | **mypy，失败阻止构建** |
| 单元测试 | ✅ | pytest，必须通过 |
| 集成测试 | ❌ | 仅 main 分支，失败不阻止 |
| 构建检查 | ✅ | 模块导入，必须通过 |

## ❌ 类型检查失败处理

### 1. 查看错误

```bash
# 在 GitHub Actions 日志中查看
# 或在本地运行
mypy src/ --config-file=mypy.ini
```

### 2. 常见错误类型

| 错误代码 | 说明 | 解决方案 |
|----------|------|----------|
| `error: Function is missing a type annotation` | 缺少类型注解 | 添加参数和返回值类型 |
| `error: Incompatible return value type` | 返回值类型不匹配 | 修正返回值类型或函数签名 |
| `error: Argument has incompatible type` | 参数类型不匹配 | 检查传入参数的类型 |
| `error: Name is not defined` | 未定义的名称 | 检查导入或变量定义 |

### 3. 修复示例

**错误**:
```python
def process_data(data):  # error: Function is missing a type annotation
    return data.upper()
```

**修复**:
```python
def process_data(data: str) -> str:
    return data.upper()
```

### 4. 临时跳过（不推荐）

```python
# 单行跳过
result = some_function()  # type: ignore

# 跳过特定错误
result = some_function()  # type: ignore[arg-type]
```

## 📊 查看报告

### 类型检查报告

1. 进入 Actions 页面
2. 点击失败的工作流
3. 下载 "mypy-report" 产物
4. 解压并打开 `index.html`

### 测试覆盖率报告

```bash
# 本地生成
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html  # macOS
```

## 🔧 配置文件位置

| 文件 | 用途 |
|------|------|
| `.github/workflows/ci.yml` | 主 CI 工作流 |
| `.github/workflows/type-check.yml` | 类型检查工作流 |
| `mypy.ini` | mypy 配置 |
| `pytest.ini` | pytest 配置 |
| `.flake8` | Flake8 配置 |
| `.pylintrc` | Pylint 配置 |
| `scripts/pre-commit-check.sh` | 提交前检查脚本 |

## 💡 最佳实践

### ✅ 推荐做法

- ✅ 提交前运行 `./scripts/pre-commit-check.sh`
- ✅ 及时修复类型检查错误
- ✅ 为新代码添加类型注解
- ✅ 小步提交，频繁推送
- ✅ 关注 CI 状态

### ❌ 避免做法

- ❌ 忽略类型检查错误
- ❌ 过度使用 `# type: ignore`
- ❌ 提交未经测试的代码
- ❌ 大规模重构一次性提交
- ❌ 在 CI 失败时强制合并

## 🆘 紧急情况

### CI 阻塞了紧急修复？

1. **首选**: 修复类型错误后提交
2. **备选**: 在代码中添加 `# type: ignore` 注释
3. **最后手段**: 联系维护者临时禁用检查

### 本地检查通过但 CI 失败？

```bash
# 确保环境一致
python --version  # 应该是 3.10
pip install -r requirements.txt --upgrade

# 清理缓存
rm -rf .mypy_cache
mypy src/ --config-file=mypy.ini
```

## 📞 获取帮助

- 📖 详细文档: [CI/CD 集成文档](./CI_CD_INTEGRATION.md)
- 📖 mypy 配置: [MYPY_SETUP_SUMMARY.md](../MYPY_SETUP_SUMMARY.md)
- 📖 测试指南: [TESTING.md](./TESTING.md)
- 🐛 问题反馈: GitHub Issues

---

**快速链接**:
- [GitHub Actions](https://github.com/your-username/RedBookContentGen/actions)
- [mypy 文档](https://mypy.readthedocs.io/)
- [pytest 文档](https://docs.pytest.org/)
