# RedBookContentGen 文档中心

欢迎来到 RedBookContentGen 文档中心！这里包含了项目的所有配置和使用文档。

## 📚 文档导航

### 配置相关

#### [⚡ 配置快速参考](CONFIG_QUICK_REFERENCE.md)
**适合**: 快速查找配置项和命令

快速参考卡片，包含：
- 常用环境变量速查表
- 配置文件结构示例
- 模型和风格选择指南
- 常用命令速查

**推荐**: 打印或收藏此页面，作为日常开发参考

---

#### [📖 完整配置说明](CONFIG.md)
**适合**: 深入了解所有配置项

详细的配置文档，包含：
- 所有配置项的完整说明
- 配置项类型、默认值、可选值
- 环境变量映射表
- 配置优先级和验证规则
- 完整的配置示例

**推荐**: 首次使用或需要自定义配置时阅读

---

#### [🔄 配置迁移指南](CONFIG_MIGRATION_GUIDE.md)
**适合**: 从旧配置系统迁移

迁移指南，包含：
- 新旧配置方式对比
- 逐步迁移步骤
- 向后兼容性说明
- 常见问题解答
- 迁移检查清单

**推荐**: 升级项目或维护旧代码时阅读

---

#### [💡 配置最佳实践](CONFIG_BEST_PRACTICES.md)
**适合**: 优化配置和解决问题

最佳实践指南，包含：
- 安全性建议（API Key 管理）
- 环境管理策略
- 性能优化技巧
- 调试方法
- 常见场景配置示例
- 故障排查指南

**推荐**: 部署到生产环境前阅读

---

## 🚀 快速开始

### 1. 首次使用

```bash
# 复制配置模板
cp config/config.example.json config/config.json

# 设置 API Key
export OPENAI_API_KEY="your-api-key"

# 运行
python run.py
```

### 2. 查看配置

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
print(config.get('openai_model'))
```

### 3. 验证配置

```python
if config.validate():
    print("✅ 配置正确")
else:
    print("❌ 配置错误")
    print(config.get_validation_errors())
```

## 📋 常见任务

### 更改 AI 模型

```bash
# 方式 1: 环境变量
export OPENAI_MODEL="qwen-max"

# 方式 2: 配置文件
# 编辑 config/config.json
{
  "openai_model": "qwen-max"
}
```

### 切换图片生成模式

```bash
# 模板模式（离线，快速）
export IMAGE_GENERATION_MODE="template"

# API 模式（需要 API Key）
export IMAGE_GENERATION_MODE="api"
```

### 调整速率限制

```json
{
  "rate_limit": {
    "openai": {
      "requests_per_minute": 100
    },
    "image": {
      "requests_per_minute": 20,
      "max_concurrent": 5
    }
  }
}
```

### 启用调试日志

```bash
export LOG_LEVEL="DEBUG"
python run.py
```

## 🔍 按场景查找

### 我想...

- **快速查找配置项** → [配置快速参考](CONFIG_QUICK_REFERENCE.md)
- **了解所有配置选项** → [完整配置说明](CONFIG.md)
- **升级配置系统** → [配置迁移指南](CONFIG_MIGRATION_GUIDE.md)
- **优化性能** → [配置最佳实践](CONFIG_BEST_PRACTICES.md#性能优化)
- **保护 API Key** → [配置最佳实践](CONFIG_BEST_PRACTICES.md#安全性)
- **解决配置问题** → [配置最佳实践](CONFIG_BEST_PRACTICES.md#故障排查)
- **为不同环境配置** → [配置最佳实践](CONFIG_BEST_PRACTICES.md#环境管理)

## 💻 代码示例

### 基本使用

```python
from src.core.config_manager import ConfigManager
from src.content_generator import RedBookContentGenerator

# 创建配置管理器
config = ConfigManager()

# 创建生成器
generator = RedBookContentGenerator(config_manager=config)

# 运行
generator.run()
```

### 自定义配置

```python
# 使用自定义配置文件
config = ConfigManager('config/config.prod.json')

# 运行时修改配置
config.set('openai_model', 'qwen-max')
config.set('rate_limit.openai.requests_per_minute', 100)

# 验证配置
if config.validate():
    generator = RedBookContentGenerator(config_manager=config)
    generator.run()
```

### 配置热重载

```python
config = ConfigManager()

# 注册重载回调
def on_config_reload():
    print("配置已更新")
    # 重新初始化服务...

config.register_reload_callback(on_config_reload)

# 启动监控
config.start_watching(check_interval=1.0)

# 配置文件修改后会自动重新加载
```

## 🛠️ 工具和示例

### 示例代码

项目包含完整的示例代码：

- [`examples/config_usage_example.py`](../examples/config_usage_example.py) - 基本用法示例
- [`examples/config_hot_reload_example.py`](../examples/config_hot_reload_example.py) - 热重载示例

运行示例：

```bash
python examples/config_usage_example.py
python examples/config_hot_reload_example.py
```

### 测试

运行配置相关测试：

```bash
python tests/unit/test_config_manager.py
python tests/unit/test_rate_limit_config.py
```

## 📞 获取帮助

### 遇到问题？

1. **查看文档** - 先查看相关文档章节
2. **运行示例** - 参考示例代码
3. **检查配置** - 使用 `config.validate()` 验证配置
4. **查看日志** - 启用 DEBUG 日志查看详细信息
5. **提交 Issue** - 如果问题仍未解决

### 常见问题

#### Q: 配置文件找不到？
A: 运行 `cp config/config.example.json config/config.json`

#### Q: API Key 未设置？
A: 运行 `export OPENAI_API_KEY="your-key"`

#### Q: 配置未生效？
A: 检查配置优先级：环境变量 > 配置文件 > 默认值

#### Q: 如何查看配置来源？
A: 使用 `config.get_config_source('key')`

更多问题请查看 [配置最佳实践 - 故障排查](CONFIG_BEST_PRACTICES.md#故障排查)

## 📝 贡献文档

发现文档错误或有改进建议？欢迎：

1. 提交 Issue 描述问题
2. 提交 Pull Request 改进文档
3. 分享您的使用经验

## 🔗 相关链接

- [项目 README](../README.md) - 项目主页
- [项目架构说明](../AGENTS.md) - 开发规范
- [阿里云 DashScope](https://dashscope.console.aliyun.com/) - 获取 API Key

---

**最后更新**: 2024-01-19

**文档版本**: 1.0.0
