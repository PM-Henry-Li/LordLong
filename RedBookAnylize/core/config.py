"""
配置文件 - 小红书竞品分析系统
Config File - Xiaohongshu Competitor Analysis System
"""

import os

# ========================================
# API 配置 / API Configuration
# ========================================

# OpenAI API Key (用于内容生成 / For content generation)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "bf75eff8cd9e4e6d8aba4b7051aa8946.Kp5hGceCbXpwXuxm")
OPENAI_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
OPENAI_MODEL = "GLM-4"  # 或 "gpt-4"

# 备用: 可以使用其他兼容OpenAI格式的API
# Alternative: Use other OpenAI-compatible APIs
# OPENAI_API_BASE = "https://api.deepseek.com/v1"

# ========================================
# 爬虫配置 / Crawler Configuration
# ========================================

# 搜索关键词 / Search keyword
TARGET_KEYWORD = "长白山旅行"  # 用户可修改 / User can modify

# 采集数量 / Collection count
MAX_ARTICLES_TO_SCRAPE = 200  # 初始爬取数量
TOP_ARTICLES_TO_ANALYZE = 50  # 最终分析数量

# 请求延时 / Request delay (秒 / seconds)
# 按照解决方案7优化：增加延时，降低请求频率
REQUEST_DELAY_MIN = 5  # 从2秒增加到5秒，降低请求频率
REQUEST_DELAY_MAX = 15  # 从5秒增加到15秒，避免触发频率限制

# 重试次数 / Retry times
MAX_RETRIES = 3

# 爬虫超时时间 / Crawler timeout (秒 / seconds)
CRAWLER_TIMEOUT = 300  # 5分钟超时时间

# ========================================
# 数据存储路径 / Data Storage Paths
# ========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 创建必要的目录 / Create necessary directories
for directory in [DATA_DIR, OUTPUT_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

RAW_DATA_FILE = os.path.join(DATA_DIR, "raw_articles.csv")
PROCESSED_DATA_FILE = os.path.join(DATA_DIR, "processed_articles.csv")
ANALYSIS_REPORT_FILE = os.path.join(OUTPUT_DIR, "analysis_report.json")
CONTENT_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "generated_content.json")
VISUAL_PROMPTS_FILE = os.path.join(OUTPUT_DIR, "visual_prompts.json")

# ========================================
# 数据分析配置 / Data Analysis Configuration
# ========================================

# 热度指数权重 / Engagement Index Weights
WEIGHTS = {
    "likes": 1,      # 点赞权重 / Likes weight
    "collects": 2,   # 收藏权重 / Collects weight
    "comments": 3,   # 评论权重 / Comments weight
    "views": 0.1     # 阅读权重 / Views weight (较低)
}

# 最小互动数阈值 / Minimum engagement threshold
MIN_ENGAGEMENT = 100  # 低于此值的文章将被过滤 / Articles below this will be filtered

# ========================================
# 内容生成配置 / Content Generation Configuration
# ========================================

# 生成主题数量 / Number of topics to generate
NUM_TOPICS_TO_GENERATE = 5

# 内容风格 / Content style
CONTENT_STYLE = "小红书风格"  # "小红书风格", "知乎风格", "抖音风格"

# 语言 / Language
CONTENT_LANGUAGE = "中文"

# ========================================
# 日志配置 / Logging Configuration
# ========================================

import logging

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOG_DIR, "rednote_analysis.log")

# ========================================
# 浏览器配置 / Browser Configuration
# ========================================

# 浏览器设置 / Browser settings
BROWSER_HEADLESS = False  # 是否无头模式 / Whether to use headless mode
BROWSER_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 窗口大小 / Window size (模拟移动端 / Simulate mobile)
WINDOW_SIZE = (375, 812)  # iPhone X 尺寸

# ========================================
# 反爬虫配置 / Anti-Crawler Configuration
# ========================================

# User-Agent池 / User-Agent pool
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

# ========================================
# 实用函数 / Utility Functions
# ========================================

def setup_logging():
    """设置日志配置 / Setup logging configuration"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_config():
    """验证配置 / Validate configuration"""
    errors = []
    
    if OPENAI_API_KEY == "your-api-key-here":
        errors.append("请设置有效的 OPENAI_API_KEY / Please set valid OPENAI_API_KEY")
    
    if TARGET_KEYWORD:
        print(f"目标关键词 / Target Keyword: {TARGET_KEYWORD}")
    else:
        errors.append("请设置 TARGET_KEYWORD / Please set TARGET_KEYWORD")
    
    if errors:
        print("配置错误 / Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

if __name__ == "__main__":
    logger = setup_logging()
    if validate_config():
        logger.info("配置验证成功 / Configuration validated successfully")
    else:
        logger.error("配置验证失败 / Configuration validation failed")
