# 小红书主题搜索功能使用指南

## 快速开始

### 1. 安装依赖

首先安装新增的依赖包:

```bash
pip install -r requirements.txt
```

新增依赖包括:
- `selenium`: 浏览器自动化
- `webdriver-manager`: 自动管理浏览器驱动
- `beautifulsoup4`: HTML解析
- `lxml`: XML/HTML解析

### 2. 基本使用

```bash
# 搜索"老北京胡同"主题并生成内容
python run.py --mode topic --topic "老北京胡同"
```

## 完整参数说明

### 必需参数

- `--mode topic`: 启用主题搜索模式
- `--topic "关键词"`: 指定搜索主题

### 可选参数

- `--max-results 数量`: 最多搜索多少条笔记(默认10)
- `--min-likes 数量`: 最小点赞数阈值(默认1000)
- `--skip-images`: 跳过图片生成,仅生成文案
- `--image-mode api|template`: 图片生成模式
- `-c 配置文件`: 指定配置文件路径

## 使用示例

### 示例1: 基础搜索

```bash
python run.py --mode topic --topic "老北京记忆"
```

流程:
1. 搜索小红书"老北京记忆"相关笔记
2. 筛选点赞1000+的高质量内容
3. AI整理提取关键内容
4. 生成新的小红书文案和图片提示词
5. 保存到Excel和日期文件夹

### 示例2: 自定义搜索参数

```bash
python run.py --mode topic --topic "北京烤鸭" --max-results 20 --min-likes 2000
```

- 搜索最多20条笔记
- 只保留点赞2000+的内容

### 示例3: 仅生成文案

```bash
python run.py --mode topic --topic "天坛公园" --skip-images
```

跳过图片生成,快速获取文案内容。

### 示例4: 使用模板图片

```bash
python run.py --mode topic --topic "故宫历史" --image-mode template
```

使用模板模式生成图片(不需要图片生成API)。

## 工作流程详解

### 第一步: 搜索小红书

程序会:
1. 启动Chrome浏览器(无头模式)
2. 访问小红书搜索页面
3. 搜索指定主题的笔记
4. 滑动页面加载更多内容

### 第二步: 筛选高分内容

- 按点赞数排序
- 筛选超过阈值的笔记
- 获取前5条的详细内容

### 第三步: 智能整理

- 提取标题、正文、标签
- 使用AI去重和合并内容
- 生成连贯的文本描述
- 保存到`input/topic_content.txt`

### 第四步: 生成文案

使用整理后的内容:
- 生成5个吸引人的标题
- 创作带京味儿的正文
- 提取相关标签
- 生成4张故事图提示词
- 生成1张封面图提示词

### 第五步: 生成图片(可选)

根据提示词生成配图和封面。

## 输出文件

### 1. Excel文件

`output/redbook_content.xlsx`
- 包含所有生成的内容
- 每次运行添加新行

### 2. 日期文件夹

`output/images/YYYYMMDD/`
- `image_prompts.txt`: 图片提示词
- `content.md`: 完整内容预览
- `image_01.png ~ image_04.png`: 故事图
- `cover.png`: 封面图

### 3. 整理后的输入

`input/topic_content.txt`
- 从小红书整理的内容
- 作为生成文案的输入
- 可查看和手动修改

## 配置说明

在`config/config.json`中可配置:

```json
{
  "xiaohongshu": {
    "search_mode": "browser",      // 搜索模式
    "browser_type": "chrome",      // 浏览器类型
    "headless": true,              // 无头模式
    "max_search_results": 10,      // 默认搜索数量
    "min_likes_threshold": 1000,   // 默认点赞阈值
    "login_required": false,       // 是否需要登录
    "request_delay": 2             // 请求间隔(秒)
  }
}
```

## 注意事项

### 首次使用

首次使用时,`webdriver-manager`会自动下载Chrome驱动,需要:
- 联网环境
- 系统已安装Chrome浏览器

### 反爬虫

为避免触发反爬虫:
- 设置了合理的请求间隔(2秒)
- 使用真实User-Agent
- 模拟人类浏览行为

### 内容审核

- 整理的内容会自动检查敏感词
- 生成的文案会进行安全性检查
- 如有可疑内容会自动修改或标记

### 法律合规

- 仅用于个人学习和内容创作
- 不直接抄袭原创内容
- 尊重原作者权益

## 常见问题

### Q: 浏览器驱动初始化失败?

A: 确保:
1. 系统已安装Chrome浏览器
2. 网络连接正常
3. 首次运行需要下载驱动

### Q: 未找到相关笔记?

A: 尝试:
1. 更换搜索关键词
2. 降低`--min-likes`阈值
3. 增加`--max-results`数量

### Q: 内容质量不理想?

A: 可以:
1. 提高点赞数阈值
2. 手动编辑`input/topic_content.txt`
3. 重新运行内容生成

### Q: 想要更多控制?

A: 可以分步执行:
```bash
# 1. 仅搜索和整理
python -m src.xiaohongshu_scraper "老北京胡同"

# 2. 编辑 input/topic_content.txt

# 3. 生成文案
python -m src.content_generator

# 4. 生成图片  
python -m src.image_generator
```

## 高级用法

### 批量处理多个主题

创建脚本`batch_topics.sh`:

```bash
#!/bin/bash
topics=("老北京胡同" "北京小吃" "故宫历史" "天坛公园")

for topic in "${topics[@]}"
do
    echo "处理主题: $topic"
    python run.py --mode topic --topic "$topic"
    sleep 5
done
```

### 自定义整理逻辑

编辑`src/content_organizer.py`中的`_build_organize_prompt`方法,调整AI整理提示词。

### 定制搜索策略

编辑`src/xiaohongshu_scraper.py`中的`filter_high_quality_notes`方法,添加自定义筛选规则。

## 反馈与改进

如遇到问题或有改进建议,欢迎反馈!
