# 老北京文化·小红书内容生成器

自动读取文档内容，生成小红书文案和AI绘画提示词，并保存到Excel和文件夹。

## 功能特点

- ✅ **自动读取文档**：从固定文档读取原始内容
- ✅ **AI内容生成**：调用OpenAI API生成小红书文案和绘画提示词
- ✅ **Excel存储**：将生成的内容保存到Excel，方便管理和查看
- ✅ **日期文件夹**：图片提示词保存到以日期命名的文件夹中
- ✅ **完整输出**：同时生成Markdown格式的完整内容预览

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 配置文件 (`config.json`)

```json
{
  "input_file": "input_content.txt",
  "output_excel": "output/redbook_content.xlsx",
  "output_image_dir": "output/images",
  "openai_api_key": "",
  "openai_model": "gpt-4",
  "openai_base_url": null,
  "image_model": "wan2.2-t2i-flash"
}
```

- `image_model`：图片生成模型（通义万相），如 `wan2.2-t2i-flash`、`wan2.2-t2i-plus`，供 `image_generator.py` 使用。

### 2. 设置 API Key

**方式1：环境变量（推荐）**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**方式2：配置文件**
在 `config.json` 中直接填写 `openai_api_key` 字段。

### 3. 使用阿里云通义千问 (Qwen / DashScope)

若使用 **通义千问**，只需将 `openai_model` 设为 `qwen` 或 `qwen-turbo` / `qwen-plus` / `qwen-max`，并填入 DashScope 的 API Key，`openai_base_url` 留空即可，脚本会自动使用 `https://dashscope.aliyuncs.com/compatible-mode/v1`。

- `qwen` 会自动映射为 `qwen-plus`
- API Key 需在 [阿里云 DashScope](https://dashscope.console.aliyun.com/) 获取

## 使用方法

### 1. 准备输入文档

创建或编辑 `input_content.txt` 文件，输入您想分享的老北京故事片段：

```
记得小时候，胡同口那棵大槐树，每到夏天就开满了白花。
傍晚时分，鸽哨声从头顶掠过，那是老北京最熟悉的声音。
...
```

### 2. 运行脚本

**一键执行（推荐）**：内容生成 + 图片生成
```bash
python run_all.py
```

**分步执行**：
```bash
# 仅内容生成
python redbook_content_generator.py

# 仅图片生成（需先有 image_prompts.txt）
python image_generator.py
```

**其他选项**：
```bash
# 指定配置文件
python run_all.py -c my_config.json

# 仅内容生成，跳过图片
python run_all.py --skip-images
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
python image_generator.py

# 或指定提示词文件
python image_generator.py -p output/images/20260119/image_prompts.txt
```

配置项：在 `config.json` 中增加 `"image_model": "wan2.2-t2i-flash"`（通义万相文生图模型）。  
详细说明见 **图片生成使用说明.md**。

## 输出格式说明

### Excel文件结构

| 列名 | 说明 |
|------|------|
| 生成时间 | 内容生成的时间戳 |
| 原始内容 | 输入的原始文档内容（截断至500字符） |
| 标题1-5 | AI生成的5个可选标题 |
| 正文内容 | 完整的小红书文案正文 |
| 标签 | 相关话题标签 |
| 图片提示词1-5 | 3-5个AI绘画提示词 |
| 图片保存路径 | 图片文件夹路径 |

### 图片提示词格式

每个提示词都包含：
- **场景描述**：中文简述
- **完整Prompt**：英文提示词，包含固定风格后缀
  - `1990s Beijing street photography, vintage kodak film, warm nostalgia tone, cinematic lighting, hyper-realistic, grainy texture --ar 3:4`

## 工作流程

1. 📖 **读取文档** → 从 `input_content.txt` 读取原始内容
2. 🤖 **AI生成** → 调用OpenAI API生成：
   - 5个吸引人的标题
   - 带京味儿的小红书正文
   - 相关标签
   - 3-5个AI绘画提示词
3. 💾 **保存Excel** → 追加到 `redbook_content.xlsx`
4. 📁 **创建文件夹** → 以日期命名（如：20241215）
5. 📝 **保存文件** → 保存提示词和完整内容到文件夹

## 示例

### 输入 (`input_content.txt`)
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
2. **输入文档**：确保 `input_content.txt` 文件存在且不为空
3. **网络连接**：需要能够访问OpenAI API
4. **Excel文件**：如果文件不存在会自动创建，如果存在会追加新行

## 故障排除

### 问题：找不到OpenAI API Key
**解决**：设置环境变量 `OPENAI_API_KEY` 或在 `config.json` 中配置

### 问题：输入文件不存在
**解决**：创建 `input_content.txt` 文件并填入内容

### 问题：Excel文件无法写入
**解决**：确保输出目录有写入权限，关闭已打开的Excel文件

## 文件结构

```
RedBookContentGen/
├── run_all.py                    # 一键执行（内容+图片）
├── redbook_content_generator.py  # 内容生成脚本
├── image_generator.py            # 图片生成脚本
├── config.json                   # 配置文件
├── requirements.txt              # 依赖文件
├── README.md                     # 使用说明
├── 图片生成使用说明.md            # 图片生成详细说明
├── input_content.txt             # 输入文档（需创建）
└── output/                       # 输出目录（自动创建）
    ├── redbook_content.xlsx      # Excel文件
    └── images/                   # 图片文件夹
        └── YYYYMMDD/             # 日期文件夹
            ├── image_prompts.txt
            ├── content.md
            ├── image_01.png      # 图片生成器输出
            ├── image_02.png
            └── ...
```

## 许可证

内部使用工具。
