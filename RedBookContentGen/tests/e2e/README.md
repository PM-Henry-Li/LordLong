# 端到端测试 (E2E Tests)

本目录包含使用 Selenium WebDriver 进行的端到端测试，用于测试 Web 应用的用户界面和交互。

## 测试文件

- `test_error_ui.py` - 前端错误处理端到端测试
- `ERROR_UI_TEST_SUMMARY.md` - 前端错误处理测试总结

## 环境要求

### 1. 安装依赖

```bash
# 安装 Selenium
pip install selenium

# 安装 pytest（如果还没有安装）
pip install pytest
```

### 2. 安装 ChromeDriver

#### macOS

```bash
brew install chromedriver
```

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

#### Windows

1. 下载 ChromeDriver: https://chromedriver.chromium.org/
2. 解压并将 `chromedriver.exe` 添加到 PATH

#### 验证安装

```bash
chromedriver --version
```

### 3. 启动 Web 应用

测试需要 Web 应用运行在 `http://localhost:5000`：

```bash
# 在项目根目录运行
python web_app.py
```

或者在后台运行：

```bash
python web_app.py &
```

## 运行测试

### 运行所有 E2E 测试

```bash
# 在项目根目录运行
python3 -m pytest tests/e2e/ -v
```

### 运行特定测试文件

```bash
python3 -m pytest tests/e2e/test_error_ui.py -v
```

### 运行特定测试类

```bash
# 测试 Toast 显示
python3 -m pytest tests/e2e/test_error_ui.py::TestErrorToastDisplay -v

# 测试错误对话框
python3 -m pytest tests/e2e/test_error_ui.py::TestErrorDialog -v

# 测试重试逻辑
python3 -m pytest tests/e2e/test_error_ui.py::TestRetryLogic -v
```

### 运行单个测试

```bash
python3 -m pytest tests/e2e/test_error_ui.py::TestErrorToastDisplay::test_show_error_toast -v
```

### 显示详细输出

```bash
# 显示 print 输出
python3 -m pytest tests/e2e/ -v -s

# 显示完整的错误堆栈
python3 -m pytest tests/e2e/ -v --tb=long
```

### 生成测试报告

```bash
# 生成 HTML 报告
pip install pytest-html
python3 -m pytest tests/e2e/ -v --html=report.html --self-contained-html

# 生成覆盖率报告
pip install pytest-cov
python3 -m pytest tests/e2e/ -v --cov=static/js --cov-report=html
```

## 测试配置

### 修改测试 URL

如果 Web 应用运行在不同的地址，可以修改 `test_error_ui.py` 中的 `TEST_URL` 常量：

```python
TEST_URL = "http://localhost:8080"  # 修改为实际地址
```

### 修改超时时间

如果测试经常超时，可以增加 `TIMEOUT` 常量：

```python
TIMEOUT = 20  # 增加到 20 秒
```

### 禁用无头模式

如果想看到浏览器操作过程，可以注释掉无头模式：

```python
@pytest.fixture(scope="module")
def driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 注释掉这一行
    # ...
```

## 故障排查

### 问题 1: ChromeDriver 版本不匹配

**错误信息**:
```
SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX
```

**解决方案**:
1. 检查 Chrome 浏览器版本: `google-chrome --version` 或 `chromium --version`
2. 下载匹配的 ChromeDriver 版本: https://chromedriver.chromium.org/
3. 或者更新 ChromeDriver: `brew upgrade chromedriver` (macOS)

### 问题 2: Web 应用未运行

**错误信息**:
```
WebDriverException: Message: unknown error: net::ERR_CONNECTION_REFUSED
```

**解决方案**:
1. 确保 Web 应用正在运行: `python web_app.py`
2. 检查应用是否运行在正确的端口: `http://localhost:5000`
3. 检查防火墙设置

### 问题 3: 元素未找到

**错误信息**:
```
NoSuchElementException: Message: no such element
```

**解决方案**:
1. 增加等待时间（修改 `TIMEOUT` 常量）
2. 检查元素选择器是否正确
3. 使用显式等待: `wait.until(EC.presence_of_element_located(...))`
4. 检查页面是否完全加载

### 问题 4: 测试超时

**错误信息**:
```
TimeoutException: Message: timeout
```

**解决方案**:
1. 增加 `TIMEOUT` 常量值
2. 检查网络连接
3. 检查 Web 应用性能
4. 使用更长的等待时间

### 问题 5: ChromeDriver 权限问题 (macOS)

**错误信息**:
```
"chromedriver" cannot be opened because the developer cannot be verified
```

**解决方案**:
```bash
# 移除隔离属性
xattr -d com.apple.quarantine /usr/local/bin/chromedriver

# 或者在系统偏好设置中允许运行
```

## 测试最佳实践

### 1. 使用显式等待

```python
# 推荐
wait.until(EC.presence_of_element_located((By.ID, "element")))

# 不推荐
time.sleep(5)
```

### 2. 使用 Page Object 模式

```python
class ErrorHandlerPage:
    def __init__(self, driver):
        self.driver = driver
    
    def show_error_toast(self, message):
        self.driver.execute_script(f"""
            errorHandler.showToast('{message}', 'error');
        """)
```

### 3. 清理测试数据

```python
@pytest.fixture(autouse=True)
def cleanup(driver):
    yield
    # 清理操作
    driver.execute_script("""
        document.querySelectorAll('.toast').forEach(t => t.remove());
    """)
```

### 4. 使用有意义的测试名称

```python
# 好的测试名称
def test_show_error_toast_with_chinese_message():
    pass

# 不好的测试名称
def test_1():
    pass
```

### 5. 独立的测试

每个测试应该独立运行，不依赖其他测试的状态。

## 持续集成 (CI)

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
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
        pip install selenium pytest
        sudo apt-get install chromium-chromedriver
    
    - name: Start web app
      run: |
        python web_app.py &
        sleep 5
    
    - name: Run E2E tests
      run: |
        python3 -m pytest tests/e2e/ -v
```

## 相关文档

- [前端错误处理测试总结](ERROR_UI_TEST_SUMMARY.md)
- [项目改进需求文档](../../.kiro/specs/project-improvement/requirements.md)
- [项目改进设计文档](../../.kiro/specs/project-improvement/design.md)
- [项目改进任务列表](../../.kiro/specs/project-improvement/tasks.md)

## 贡献指南

### 添加新测试

1. 在 `test_error_ui.py` 中添加新的测试类或测试方法
2. 使用描述性的测试名称
3. 添加必要的注释说明测试目的
4. 更新 `ERROR_UI_TEST_SUMMARY.md` 文档

### 测试命名规范

- 测试类: `Test<功能名称>`
- 测试方法: `test_<具体测试内容>`
- 使用下划线分隔单词
- 使用英文命名，注释使用中文

### 代码风格

遵循项目的代码风格指南（参考 `AGENTS.md`）：
- 使用 4 空格缩进
- 使用中文注释和文档字符串
- 遵循 PEP 8 规范

## 许可证

本项目遵循项目根目录的许可证。

---

**最后更新**: 2026-02-15  
**维护者**: RedBookContentGen 团队
