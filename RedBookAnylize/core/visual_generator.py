"""
视觉提示词生成模块
Visual Prompt Generator Module
为小红书内容生成AI绘画提示词（适用于Midjourney/Stable Diffusion）
"""

import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_MODEL,
    CONTENT_OUTPUT_FILE,
    VISUAL_PROMPTS_FILE
)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class VisualPromptGenerator:
    """视觉提示词生成器 / Visual Prompt Generator"""
    
    def __init__(self):
        """初始化生成器 / Initialize generator"""
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.content_data = None
        self.visual_prompts = []
        
        self._init_client()
    
    def _init_client(self):
        """
        初始化OpenAI客户端 / Initialize OpenAI client
        """
        try:
            if OpenAI is None:
                self.logger.error("未安装openai库，请运行: pip install openai")
                return
            
            if OPENAI_API_KEY == "your-api-key-here":
                self.logger.warning("未设置OPENAI_API_KEY，请在config.py中配置或设置环境变量")
                return
            
            self.client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_API_BASE
            )
            
            self.logger.info("OpenAI客户端初始化成功 / OpenAI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"OpenAI客户端初始化失败 / Failed to initialize OpenAI client: {e}")
    
    def load_content_data(self, filename: str = None):
        """
        加载内容数据 / Load content data
        
        Args:
            filename: 内容文件名 / Content filename
        """
        try:
            filename = filename or CONTENT_OUTPUT_FILE
            
            with open(filename, 'r', encoding='utf-8') as f:
                self.content_data = json.load(f)
            
            self.logger.info(f"成功加载内容数据 / Successfully loaded content data")
            
        except Exception as e:
            self.logger.error(f"加载内容数据失败 / Failed to load content data: {e}")
    
    def _call_ai_api(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        调用AI API / Call AI API
        
        Args:
            system_prompt: 系统提示词 / System prompt
            user_prompt: 用户提示词 / User prompt
            max_retries: 最大重试次数 / Max retry times
            
        Returns:
            AI响应文本 / AI response text
        """
        if not self.client:
            self.logger.error("AI客户端未初始化 / AI client not initialized")
            return None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2500
                )
                
                content = response.choices[0].message.content
                return content
                
            except Exception as e:
                self.logger.warning(f"API调用失败，重试 {attempt + 1}/{max_retries} / API call failed, retry {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"API调用最终失败 / API call finally failed: {e}")
                    return None
        
        return None
    
    def generate_cover_prompt(self, article_content: Dict) -> Dict:
        """
        生成封面图提示词 / Generate cover image prompt
        
        Args:
            article_content: 文章内容字典 / Article content dictionary
            
        Returns:
            封面图提示词字典 / Cover image prompt dictionary
        """
        try:
            title = article_content.get('generated_title', '')
            content = article_content.get('generated_content', '')
            tags = article_content.get('tags', [])
            
            system_prompt = """你是一名专业的AI绘画提示词专家，擅长为小红书内容创作高质量的视觉提示词。

你的任务是为小红书笔记创作封面图提示词，要求：
1. 视觉冲击力强，能吸引用户点击
2. 符合小红书竖屏比例（3:4）
3. 留有文字预留位置（上方或中心）
4. 高审美，符合小红书用户喜好
5. 色彩搭配和谐，有层次感
6. 适用于Midjourney或Stable Diffusion

输出格式要求：
- 必须返回纯JSON格式
- JSON结构: {
    "prompt": "详细的英文提示词",
    "negative_prompt": "负面提示词",
    "style": "艺术风格",
    "colors": "主色调",
    "composition": "构图说明",
    "aspect_ratio": "3:4",
    "keywords": ["关键词1", "关键词2"]
}

提示词要求：
- 用英文编写
- 详细描述主体、背景、光影、色彩、风格
- 包含质量提升词（如: high quality, detailed, professional）
- 包含风格词（如: minimalist, modern, aesthetic）
"""
            
            user_prompt = f"""基于以下小红书笔记内容，创作一个吸引眼球的封面图提示词：

标题: {title}
内容摘要: {content[:200]}...
标签: {', '.join(tags)}

封面图要求：
1. 要能体现文章主题和情感基调
2. 风格要符合小红书年轻化、审美化的特点
3. 要有留白区域用于放置标题文字
4. 色彩要鲜明但不失雅致
5. 构图要简洁有力，一目了然

请生成详细的AI绘画提示词。"""

            # 调用AI
            response = self._call_ai_api(system_prompt, user_prompt)
            
            if not response:
                return self._get_default_cover_prompt(article_content)
            
            # 解析JSON响应
            try:
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                result = json.loads(response)
                
                cover_prompt = {
                    "type": "cover",
                    "article_id": article_content.get('article_id', ''),
                    "prompt": result.get('prompt', ''),
                    "negative_prompt": result.get('negative_prompt', ''),
                    "style": result.get('style', ''),
                    "colors": result.get('colors', ''),
                    "composition": result.get('composition', ''),
                    "aspect_ratio": "3:4",
                    "keywords": result.get('keywords', [])
                }
                
                self.logger.info(f"成功生成封面提示词 / Successfully generated cover prompt for article #{article_content.get('article_id', '')}")
                
                return cover_prompt
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"解析AI响应失败，使用默认提示词 / Failed to parse AI response, using default prompt: {e}")
                return self._get_default_cover_prompt(article_content)
                
        except Exception as e:
            self.logger.error(f"生成封面提示词失败 / Failed to generate cover prompt: {e}")
            return self._get_default_cover_prompt(article_content)
    
    def generate_inner_page_prompts(self, article_content: Dict, num_pages: int = 5) -> List[Dict]:
        """
        生成内页图提示词 / Generate inner page image prompts
        
        Args:
            article_content: 文章内容字典 / Article content dictionary
            num_pages: 内页图数量 / Number of inner page images
            
        Returns:
            内页图提示词列表 / List of inner page image prompts
        """
        try:
            title = article_content.get('generated_title', '')
            content = article_content.get('generated_content', '')
            tags = article_content.get('tags', [])
            
            system_prompt = f"""你是一名专业的AI绘画提示词专家，擅长为小红书内容创作高质量的视觉提示词。

你的任务是为小红书笔记创作内页图提示词，要求：
1. 对应正文的细节展示、步骤图或氛围图
2. 保持与封面图风格统一
3. 每张图都有明确的主题和目的
4. 符合小红书竖屏比例（3:4）或（9:16）
5. 高质量，细节丰富
6. 适用于Midjourney或Stable Diffusion

需要生成 {num_pages} 张内页图。

输出格式要求：
- 必须返回纯JSON格式
- JSON结构: {{
    "inner_pages": [
        {{
            "page_num": 1,
            "purpose": "这张图的目的（如：展示步骤1、营造氛围、对比图等）",
            "prompt": "详细的英文提示词",
            "negative_prompt": "负面提示词",
            "style": "艺术风格",
            "description": "图片内容描述"
        }}
    ]
}}

提示词要求：
- 用英文编写
- 详细描述主体、背景、光影、色彩、风格
- 包含质量提升词
- 保持与封面风格一致"""
            
            user_prompt = f"""基于以下小红书笔记内容，创作 {num_pages} 张内页图的提示词：

标题: {title}
正文内容:
{content}
标签: {', '.join(tags)}

内页图要求：
1. 每张图都要服务于内容的某个部分
2. 可以是步骤展示、对比图、氛围图、细节展示等
3. 保持视觉连贯性
4. 色彩与封面协调
5. 要能增强读者的理解和情感共鸣

请为每一页图生成详细的AI绘画提示词。"""

            # 调用AI
            response = self._call_ai_api(system_prompt, user_prompt)
            
            if not response:
                return self._get_default_inner_page_prompts(article_content, num_pages)
            
            # 解析JSON响应
            try:
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                result = json.loads(response)
                inner_pages = result.get('inner_pages', [])
                
                # 为每页添加额外信息
                processed_pages = []
                for page in inner_pages:
                    processed_page = {
                        "type": "inner_page",
                        "article_id": article_content.get('article_id', ''),
                        "page_num": page.get('page_num', ''),
                        "purpose": page.get('purpose', ''),
                        "prompt": page.get('prompt', ''),
                        "negative_prompt": page.get('negative_prompt', ''),
                        "style": page.get('style', ''),
                        "description": page.get('description', ''),
                        "aspect_ratio": "3:4"
                    }
                    processed_pages.append(processed_page)
                
                self.logger.info(f"成功生成 {len(processed_pages)} 张内页提示词 / Successfully generated {len(processed_pages)} inner page prompts for article #{article_content.get('article_id', '')}")
                
                return processed_pages
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"解析AI响应失败，使用默认提示词 / Failed to parse AI response, using default prompt: {e}")
                return self._get_default_inner_page_prompts(article_content, num_pages)
                
        except Exception as e:
            self.logger.error(f"生成内页提示词失败 / Failed to generate inner page prompts: {e}")
            return self._get_default_inner_page_prompts(article_content, num_pages)
    
    def _get_default_cover_prompt(self, article_content: Dict) -> Dict:
        """
        获取默认封面提示词 / Get default cover prompt
        
        Args:
            article_content: 文章内容字典 / Article content dictionary
            
        Returns:
            默认封面提示词字典 / Default cover prompt dictionary
        """
        title = article_content.get('generated_title', '')
        
        return {
            "type": "cover",
            "article_id": article_content.get('article_id', ''),
            "prompt": f"Minimalist aesthetic social media cover image, clean composition, soft lighting, pastel colors, ample white space at top for text, modern style, high quality, detailed, professional photography, --ar 3:4",
            "negative_prompt": "text, watermark, blur, low quality, distorted, ugly, messy, cluttered",
            "style": "Minimalist Modern",
            "colors": "Pastel tones",
            "composition": "Clean with text space at top",
            "aspect_ratio": "3:4",
            "keywords": ["minimalist", "aesthetic", "clean", "modern", "high quality"]
        }
    
    def _get_default_inner_page_prompts(self, article_content: Dict, num_pages: int = 5) -> List[Dict]:
        """
        获取默认内页提示词 / Get default inner page prompts
        
        Args:
            article_content: 文章内容字典 / Article content dictionary
            num_pages: 内页图数量 / Number of inner page images
            
        Returns:
            默认内页提示词列表 / List of default inner page prompts
        """
        default_prompts = []
        
        for i in range(1, num_pages + 1):
            prompt = {
                "type": "inner_page",
                "article_id": article_content.get('article_id', ''),
                "page_num": i,
                "purpose": f"Inner page {i} - Detail showcase",
                "prompt": f"Minimalist aesthetic image, clean composition, soft natural lighting, harmonious colors, modern style, high quality, detailed, professional photography, social media aesthetic, --ar 3:4",
                "negative_prompt": "text, watermark, blur, low quality, distorted, ugly",
                "style": "Minimalist Modern",
                "description": f"Clean aesthetic image for inner page {i}",
                "aspect_ratio": "3:4"
            }
            default_prompts.append(prompt)
        
        return default_prompts
    
    def generate_all_visual_prompts(self) -> List[Dict]:
        """
        为所有内容生成视觉提示词 / Generate visual prompts for all content
        
        Returns:
            视觉提示词列表 / List of visual prompts
        """
        try:
            if not self.content_data or len(self.content_data) == 0:
                self.logger.error("没有内容数据 / No content data available")
                return []
            
            self.logger.info("开始生成所有视觉提示词 / Starting to generate all visual prompts")
            
            self.visual_prompts = []
            
            for article in self.content_data:
                article_id = article.get('article_id', '')
                
                # 生成封面提示词
                self.logger.info(f"为文章 #{article_id} 生成封面提示词 / Generating cover prompt for article #{article_id}")
                cover_prompt = self.generate_cover_prompt(article)
                self.visual_prompts.append(cover_prompt)
                
                # 生成内页提示词
                self.logger.info(f"为文章 #{article_id} 生成内页提示词 / Generating inner page prompts for article #{article_id}")
                inner_prompts = self.generate_inner_page_prompts(article, num_pages=5)
                self.visual_prompts.extend(inner_prompts)
            
            self.logger.info(f"所有视觉提示词生成完成 / All visual prompts generated successfully")
            
            return self.visual_prompts
            
        except Exception as e:
            self.logger.error(f"生成所有视觉提示词失败 / Failed to generate all visual prompts: {e}")
            return []
    
    def save_visual_prompts(self, prompts: List[Dict] = None, filename: str = None):
        """
        保存视觉提示词 / Save visual prompts
        
        Args:
            prompts: 提示词列表 / Prompt list
            filename: 保存文件名 / Save filename
        """
        try:
            prompts = prompts or self.visual_prompts
            filename = filename or VISUAL_PROMPTS_FILE
            
            if not prompts:
                self.logger.warning("没有提示词可保存 / No prompts to save")
                return
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"视觉提示词已保存到 / Visual prompts saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"保存视觉提示词失败 / Failed to save visual prompts: {e}")
    
    def format_prompts_for_article(self, article_id: int) -> str:
        """
        格式化文章的视觉提示词 / Format visual prompts for an article
        
        Args:
            article_id: 文章ID / Article ID
            
        Returns:
            格式化的文本 / Formatted text
        """
        # 筛选该文章的所有提示词
        article_prompts = [p for p in self.visual_prompts if p.get('article_id') == article_id]
        
        if not article_prompts:
            return ""
        
        formatted = []
        formatted.append("="*60)
        formatted.append(f"文章 #{article_id} - 视觉提示词 / Visual Prompts for Article #{article_id}")
        formatted.append("="*60 + "\n")
        
        # 封面图
        cover_prompts = [p for p in article_prompts if p.get('type') == 'cover']
        if cover_prompts:
            cover = cover_prompts[0]
            formatted.append("【封面图 / Cover Image】")
            formatted.append(f"风格 / Style: {cover.get('style', '')}")
            formatted.append(f"色调 / Colors: {cover.get('colors', '')}")
            formatted.append(f"构图 / Composition: {cover.get('composition', '')}")
            formatted.append(f"\n提示词 / Prompt:\n{cover.get('prompt', '')}")
            formatted.append(f"\n负面提示词 / Negative Prompt:\n{cover.get('negative_prompt', '')}")
            formatted.append("\n" + "-"*60 + "\n")
        
        # 内页图
        inner_prompts = [p for p in article_prompts if p.get('type') == 'inner_page']
        inner_prompts.sort(key=lambda x: x.get('page_num', 0))
        
        for inner in inner_prompts:
            formatted.append(f"【内页图 #{inner.get('page_num', '')} / Inner Page #{inner.get('page_num', '')}】")
            formatted.append(f"目的 / Purpose: {inner.get('purpose', '')}")
            formatted.append(f"\n提示词 / Prompt:\n{inner.get('prompt', '')}")
            formatted.append(f"\n负面提示词 / Negative Prompt:\n{inner.get('negative_prompt', '')}")
            formatted.append("\n" + "-"*60 + "\n")
        
        return "\n".join(formatted)
    
    def generate_midjourney_commands(self) -> List[str]:
        """
        生成Midjourney命令 / Generate Midjourney commands
        
        Returns:
            Midjourney命令列表 / List of Midjourney commands
        """
        commands = []
        
        for prompt in self.visual_prompts:
            prompt_text = prompt.get('prompt', '')
            aspect_ratio = prompt.get('aspect_ratio', '3:4')
            
            # 构建Midjourney命令
            command = f"/imagine prompt: {prompt_text} --ar {aspect_ratio} --v 6.0 --style raw"
            commands.append(command)
        
        return commands


# 便捷函数 / Convenience functions
def generate_visual_prompts_for_content(content_file: str = None) -> List[Dict]:
    """
    便捷的视觉提示词生成函数 / Convenient visual prompt generation function
    
    Args:
        content_file: 内容文件路径 / Content file path
        
    Returns:
        视觉提示词列表 / List of visual prompts
    """
    generator = VisualPromptGenerator()
    generator.load_content_data(content_file)
    prompts = generator.generate_all_visual_prompts()
    generator.save_visual_prompts()
    
    return prompts


if __name__ == "__main__":
    # 设置日志 / Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 示例使用 / Example usage
    generator = VisualPromptGenerator()
    
    # 加载内容数据
    generator.load_content_data()
    
    # 生成视觉提示词
    prompts = generator.generate_all_visual_prompts()
    
    # 保存提示词
    generator.save_visual_prompts()
    
    # 打印提示词
    print("\n" + "="*60)
    print("生成的视觉提示词 / Generated Visual Prompts")
    print("="*60 + "\n")
    
    # 打印每篇文章的提示词
    article_ids = set(p.get('article_id') for p in prompts)
    for article_id in sorted(article_ids):
        print(generator.format_prompts_for_article(article_id))
    
    # 打印Midjourney命令
    print("\n" + "="*60)
    print("Midjourney 命令 / Midjourney Commands")
    print("="*60 + "\n")
    
    commands = generator.generate_midjourney_commands()
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd}\n")
