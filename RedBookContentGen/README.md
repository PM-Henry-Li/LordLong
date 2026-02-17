# 老北京文化·小红书内容生成器

[![CI](https://github.com/your-username/RedBookContentGen/workflows/CI/badge.svg)](https://github.com/your-username/RedBookContentGen/actions)
[![Type Check](https://github.com/your-username/RedBookContentGen/workflows/Type%20Check/badge.svg)](https://github.com/your-username/RedBookContentGen/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

自动读取文档内容或搜索小红书主题,生成小红书文案和AI绘画提示词,并保存到Excel和文件夹。

## 功能特点

- ✅ **双模式输入**:支持从固定文档读取或从小红书搜索主题内容
- ✅ **智能搜索**:自动搜索小红书高分笔记并整理成输入内容  
- ✅ **AI内容生成**:调用OpenAI API生成小红书文案和绘画提示词
- ✅ **异步并行生成**:图片生成性能提升约60%（可选）
- ✅ **Excel存储**:将生成的内容保存到Excel,方便管理和查看
- ✅ **日期文件夹**:图片提示词保存到以日期命名的文件夹中
- ✅ **完整输出**:同时生成 Markdown 格式的完整内容预览
- ✅ **4 张故事图 + 1 张封面**:至少 4 张故事配图,另生成 1 张带中文短标题的小红书封面
- ✅ **日志查询界面**:Web 界面查看和搜索应用程序日志，支持多条件过滤和统计分析

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 快速开始

1. **复制配置模板**
   ```bash
   cp config/config.example.json config/config.json
   ```

2. **设置 API Key（推荐使用环境变量）**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **（可选）修改配置文件**
   
   编辑 `config/config.json` 自定义配置项

### 配置管理

本项目使用统一的配置管理系统（`ConfigManager`），支持：

- ✅ **多层配置覆盖**：默认值 < 配置文件 < 环境变量
- ✅ **自动配置验证**：启动时检查配置完整性
- ✅ **配置热重载**：运行时更新配置无需重启
- ✅ **环境变量支持**：所有配置项都可通过环境变量覆盖

### 主要配置项

#### API 配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `openai_api_key` | `OPENAI_API_KEY` | - | 阿里云 DashScope API Key（必填） |
| `openai_model` | `OPENAI_MODEL` | `qwen-plus` | AI 模型（qwen-turbo/qwen-plus/qwen-max） |
| `openai_base_url` | `OPENAI_BASE_URL` | DashScope URL | API 基础 URL |
| `image_model` | `IMAGE_MODEL` | `wan2.2-t2i-flash` | 图片生成模型 |

#### 图片生成配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `image_generation_mode` | `IMAGE_GENERATION_MODE` | `template` | 图片生成模式（template/api） |
| `image_api_provider` | `IMAGE_API_PROVIDER` | `aliyun` | 图片生成服务提供商（aliyun/volcengine） |
| `template_style` | `TEMPLATE_STYLE` | `retro_chinese` | 模板风格 |

#### 火山引擎配置（可选）

如果使用火山引擎即梦 AI 生成图片，需要配置以下项：

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| `volcengine.access_key_id` | `VOLCENGINE_ACCESS_KEY_ID` | - | 火山引擎 Access Key ID |
| `volcengine.secret_access_key` | `VOLCENGINE_SECRET_ACCESS_KEY` | - | 火山引擎 Secret Access Key |
| `volcengine.endpoint` | `VOLCENGINE_ENDPOINT`

#### 速率限制配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `rate_limit.openai.requests_per_minute` | 60 | OpenAI API 每分钟请求数 |
| `rate_limit.image.requests_per_minute` | 10 | 图片 API 每分钟请求数 |
| `rate_limit.image.max_concurrent` | 3 | 图片生成最大并发数 |

### 获取 API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录账号
3. 创建 API Key
4. 设置环境变量或配置文件

### 详细文档

- 📖 [完整配置说明](docs/CONFIG.md) - 所有配置项的详细说明
- 🔄 [配置迁移指南](docs/CONFIG_MIGRATION_GUIDE.md) - 从旧配置系统迁移
- 💡 [配置使用示例](examples/config_usage_example.py) - 代码示例

## 使用方法

### 模式1: 文件输入模式(默认)

#### 1. 准备输入文档

创建或编辑 `input/input_content.txt` 文件,输入您想分享的老北京故事片段:

```
记得小时候,胡同口那棵大槐树,每到夏天就开满了白花。
傍晚时分,鸽哨声从头顶掠过,那是老北京最熟悉的声音。
...
```

#### 2. 运行脚本

**一键执行(推荐)**:内容生成 + 图片生成
```bash
# 默认模式（串行生成）
python run.py

# 异步并行模式（性能提升60%）
python run.py --image-mode api --async-mode

# 自定义并发数
python run.py --image-mode api --async-mode --max-concurrent 5
```

**分步执行**:
```bash
# 仅内容生成
python -m src.content_generator

# 仅图片生成(需先有 image_prompts.txt)
python -m src.image_generator
```

**其他选项**:
```bash
# 指定配置文件
python run.py -c config/my_config.json

# 仅内容生成,跳过图片
python run.py --skip-images

# 使用模板模式生成图片（无需API Key）
python run.py --image-mode template --style retro_chinese
```

### 模式2: 主题搜索模式(新功能)

#### 1. 使用主题关键词直接生成

无需准备输入文档,直接指定主题进行搜索:

```bash
# 基本用法
python run.py --mode topic --topic "老北京胡同"

# 自定义搜索参数
python run.py --mode topic --topic "北京小吃" --max-results 15 --min-likes 2000

# 跳过图片生成
python run.py --mode topic --topic "故宫历史" --skip-images
```

#### 2. 工作流程

1. **搜索小红书**:根据主题关键词搜索相关笔记
2. **筛选高分内容**:按点赞数筛选优质笔记  
3. **智能整理**:AI提取和整合多条笔记的关键内容
4. **生成文案**:基于整理后的内容生成新的小红书文案
5. **生成图片**:创建配图和封面

#### 3. 命令行参数

- `--mode topic`:启用主题搜索模式
- `--topic "关键词"`:指定搜索主题(必填)
- `--max-results 数量`:最多搜索多少条笔记(默认10)
- `--min-likes 数量`:最小点赞数阈值(默认1000)

#### 4. 示例

```bash
# 搜索老北京主题
python run.py --mode topic --topic "老北京记忆"

# 搜索北京美食,多获取一些笔记
python run.py --mode topic --topic "北京烤鸭" --max-results 20

# 搜索高质量内容(点赞5000+)
python run.py --mode topic --topic "天坛公园" --min-likes 5000
```

### 3. 查看输出结果

脚本会自动：

1. **生成Excel文件** (`output/redbook_content.xlsx`)
   - 包含所有生成的内容
   - 每次运行添加新的一行
   - 包含：生成时间、原始内容、5个标题、正文、标签、图片提示词等

2. **创建日期文件夹** (`output/images/YYYYMMDD/`)
   - 例如：`output/images/20241215/`
   - 包含：
     - `image_prompts.txt` - 图片提示词列表
     - `content.md` - 完整内容预览（Markdown格式）

### 4. 根据提示词生成图片（可选）

使用 **图片生成器** 根据 `image_prompts.txt` 中的提示词，调用通义万相 API 生成图片，并保存到**同一日期文件夹**：

```bash
# 自动使用最新日期文件夹下的 image_prompts.txt
python -m src.image_generator

# 或指定提示词文件
python -m src.image_generator -p output/images/20260119/image_prompts.txt
```

配置项：在 `config/config.json` 中增加 `"image_model": "wan2.2-t2i-flash"`（通义万相文生图模型）。

## 输出格式说明

### Excel文件结构

| 列名 | 说明 |
|------|------|
| 生成时间 | 内容生成的时间戳 |
| 原始内容 | 输入的原始文档内容（截断至500字符） |
| 标题1-5 | AI生成的5个可选标题 |
| 正文内容 | 完整的小红书文案正文 |
| 标签 | 相关话题标签 |
| 图片提示词1-4 | 至少 4 个故事图提示词 |
| 封面标题 | 封面上的中文短标题 |
| 封面提示词 | 带标题的封面图提示词 |
| 图片保存路径 | 图片文件夹路径 |

### 图片提示词格式

每个提示词都包含：
- **场景描述**：中文简述
- **完整Prompt**：英文提示词，包含固定风格后缀
  - `1990s Beijing street photography, vintage kodak film, warm nostalgia tone, cinematic lighting, hyper-realistic, grainy texture --ar 3:4`

## 工作流程

1. 📖 **读取文档** → 从 `input/input_content.txt` 读取原始内容
2. 🤖 **AI生成** → 调用OpenAI API生成：
   - 5个吸引人的标题
   - 带京味儿的小红书正文
   - 相关标签
   - 3-5个AI绘画提示词
3. 💾 **保存Excel** → 追加到 `redbook_content.xlsx`
4. 📁 **创建文件夹** → 以日期命名（如：20241215）
5. 📝 **保存文件** → 保存提示词和完整内容到文件夹

## 示例

### 输入 (`input/input_content.txt`)
```
记得小时候，胡同口那棵大槐树，每到夏天就开满了白花。
傍晚时分，鸽哨声从头顶掠过，那是老北京最熟悉的声音。
```

### 输出

**Excel文件**：包含生成的所有内容

**Markdown文件** (`content.md`)：
```markdown
# 小红书文案预览

## 📕 可选标题
1. 胡同口的槐花香，那是回不去的夏天
2. 鸽哨声里，藏着老北京最温柔的记忆
...

## 📝 正文内容
记得小时候，胡同口那棵大槐树...
```

**图片提示词文件** (`image_prompts.txt`)：
```
## 图1: 胡同口的槐花树

```
A nostalgic scene of a Beijing hutong entrance with a large locust tree in full bloom, white flowers cascading down, warm evening sunlight filtering through leaves, 1990s Beijing street photography, vintage kodak film, warm nostalgia tone, cinematic lighting, hyper-realistic, grainy texture --ar 3:4
```
```

## 注意事项

1. **API费用**：使用OpenAI API会产生费用，请注意使用量
2. **输入文档**：确保 `input/input_content.txt` 文件存在且不为空
3. **网络连接**：需要能够访问OpenAI API
4. **Excel文件**：如果文件不存在会自动创建，如果存在会追加新行

## 异步并行图片生成（新功能）

### 性能提升

使用异步并行模式可以显著提升图片生成效率：

| 图片数量 | 串行模式 | 异步并行（3并发） | 性能提升 |
|---------|---------|-----------------|---------|
| 5张     | ~5分钟  | ~2分钟          | 60%     |
| 10张    | ~10分钟 | ~4分钟          | 60%     |

### 使用方法

```bash
# 启用异步并行模式（默认3并发）
python run.py --image-mode api --async-mode

# 自定义并发数（推荐3-5）
python run.py --image-mode api --async-mode --max-concurrent 5

# 保守模式（降低并发确保稳定）
python run.py --image-mode api --async-mode --max-concurrent 2
```

### 并发数选择

| 场景 | 并发数 | 说明 |
|------|--------|------|
| 保守 | 1-2 | API配额有限，追求稳定 |
| 推荐 | 3 | 平衡性能和稳定性 |
| 激进 | 4-5 | API配额充足，追求速度 |

### 详细文档

查看 [异步并行图片生成使用指南](docs/ASYNC_IMAGE_GENERATION.md) 了解更多：
- 性能对比
- 配置参数
- 错误处理
- 故障排查
- 最佳实践

## 故障排除

### 问题：找不到OpenAI API Key
**解决**：设置环境变量 `OPENAI_API_KEY` 或在 `config/config.json` 中配置

### 问题：输入文件不存在
**解决**：创建 `input/input_content.txt` 文件并填入内容

### 问题：Excel文件无法写入
**解决**：确保输出目录有写入权限，关闭已打开的Excel文件

## 文件结构

```
RedBookContentGen/
├── run.py                          # 一键执行入口
├── config/                         # 配置文件夹
│   ├── config.json                 # 用户配置（gitignored）
│   └── config.example.json         # 配置模板
├── src/                            # 源代码
│   ├── __init__.py
│   ├── content_generator.py        # 内容生成器
│   ├── image_generator.py          # 图片生成器（串行）
│   ├── async_image_service.py      # 异步图片生成服务
│   └── core/                       # 核心模块
│       ├── __init__.py
│       └── config_manager.py       # 统一配置管理
├── tests/                          # 测试脚本
│   ├── test_ai_rewrite.py
│   ├── test_text_overlay.py
│   ├── test_image_generation_performance.py  # 性能测试
│   ├── verify_fix.py
│   └── unit/                       # 单元测试
│       ├── test_config_manager.py
│       └── test_rate_limit_config.py
├── docs/                           # 文档
│   ├── CONFIG.md                   # 完整配置说明
│   ├── CONFIG_MIGRATION_GUIDE.md   # 配置迁移指南
│   ├── CONFIG_BEST_PRACTICES.md    # 配置最佳实践
│   ├── CONFIG_QUICK_REFERENCE.md   # 配置快速参考
│   └── ASYNC_IMAGE_GENERATION.md   # 异步并行生成指南
├── examples/                       # 使用示例
│   ├── config_usage_example.py
│   └── config_hot_reload_example.py
├── input/                          # 输入目录
│   └── input_content.txt           # 输入文档（需创建）
├── output/                         # 输出目录（自动创建）
│   ├── redbook_content.xlsx        # Excel文件
│   └── images/                     # 图片文件夹
│       └── YYYYMMDD/               # 日期文件夹
│           ├── image_prompts.txt
│           ├── content.md
│           ├── image_01.png～image_04.png   # 故事图
│           ├── cover.png                    # 带短标题的封面
│           └── ...
├── requirements.txt
├── README.md
├── AGENTS.md                       # 项目架构说明
└── .gitignore
```

## 文档

- 📖 [完整配置说明](docs/CONFIG.md) - 所有配置项的详细说明和示例
- 🔄 [配置迁移指南](docs/CONFIG_MIGRATION_GUIDE.md) - 从旧配置系统迁移到新系统
- 💡 [配置最佳实践](docs/CONFIG_BEST_PRACTICES.md) - 安全性、性能优化、调试技巧
- ⚡ [配置快速参考](docs/CONFIG_QUICK_REFERENCE.md) - 常用配置和命令速查
- 🚀 [异步并行生成指南](docs/ASYNC_IMAGE_GENERATION.md) - 异步图片生成使用说明
- 📊 [性能优化报告](PERFORMANCE_REPORT.md) - 性能优化详细报告
- 🏗️ [项目架构说明](AGENTS.md) - 项目结构和开发规范

## 许可证

内部使用工具。

---

## Web 应用模式（新功能）

### 启动 Web 应用

```bash
python3 web_app.py
```

访问地址: http://localhost:5000

### 关闭 Web 应用

```bash
# 方法1：Ctrl + C (推荐)
# 在运行 web_app.py 的终端中按 Ctrl + C

# 方法2：查找并终止进程
ps aux | grep web_app
kill <PID>

# 方法3：查找占用 5000 端口的进程并终止
lsof -ti:5000 | xargs kill -9
```

### Web 功能

1. **文字输入**：在网页文本框中直接输入内容
2. **模式选择**：
   - **模板模式**：快速生成，无需 API Key
   - **AI 模式**：使用阿里云通义万相生成真实图片
3. **模型选择**（AI 模式）：
   - `wan2.2-t2i-flash`：通义万相 2.2 Flash（推荐）
   - `wanx-v1`：通义万相 v1（稳定版）
4. **模板风格**（模板模式）：
   - 复古中国风
   - 现代简约
   - 怀旧胶片
   - 温暖记忆
   - 水墨风格
5. **图片尺寸**：
   - 正方形 (1:1)
   - 竖版 (3:4) - 小红书推荐
   - 横版 (4:3)
6. **生成数量**：1-10 条
7. **富文本输出**：文案可一键复制
8. **日志查询**：
   - 访问 http://localhost:8080/logs 查看应用日志
   - 支持按级别、来源、时间范围、关键词过滤
   - 实时统计：总日志数、错误数、警告数、今日日志
   - 详细文档：[docs/LOG_QUERY.md](docs/LOG_QUERY.md)
8. **图片下载**：生成的图片可直接下载

## 🛠️ 开发者指南

### 代码质量

本项目使用多种工具确保代码质量：

- **类型检查**: mypy（必须通过）
- **代码风格**: flake8, pylint
- **代码格式化**: black
- **测试框架**: pytest
- **测试覆盖率**: pytest-cov

### 提交代码前检查

```bash
# 运行完整的提交前检查（推荐）
./scripts/pre-commit-check.sh

# 或者单独运行各项检查
mypy src/ --config-file=mypy.ini          # 类型检查（必须通过）
flake8 src/                                # 代码风格检查
pylint src/                                # 代码质量检查
pytest tests/unit/ -v                      # 单元测试
```

### CI/CD

项目使用 GitHub Actions 进行持续集成：

- ✅ **类型检查**：mypy 检查失败将阻止代码合并
- ✅ **单元测试**：自动运行所有单元测试
- ✅ **代码质量**：Flake8 和 Pylint 检查（警告不阻止构建）
- ✅ **构建验证**：确保模块可以正常导入

详细说明请参考：
- [CI/CD 集成文档](docs/CI_CD_INTEGRATION.md)
- [CI/CD 快速参考](docs/CI_CD_QUICK_REFERENCE.md)
- [GitHub Actions 配置](.github/README.md)

### 运行测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定测试文件
pytest tests/unit/test_config_manager.py -v

# 生成覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html  # 查看覆盖率报告

# 运行快速测试（跳过慢速测试）
pytest tests/unit/ -v -m "not slow"
```

### 类型检查

```bash
# 基础类型检查
mypy src/ --config-file=mypy.ini

# 显示详细错误信息
mypy src/ --config-file=mypy.ini --show-error-codes --pretty

# 生成 HTML 报告
mypy src/ --config-file=mypy.ini --html-report mypy-report
open mypy-report/index.html
```

### 代码格式化

```bash
# 格式化代码
black src/ tests/

# 检查格式（不修改文件）
black --check src/ tests/
```

