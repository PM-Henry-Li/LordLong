"""
内容生成模块
Content Generation Module
使用AI API生成小红书爆款内容
"""

import logging
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

from config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_MODEL,
    NUM_TOPICS_TO_GENERATE,
    CONTENT_STYLE,
    CONTENT_LANGUAGE,
    CONTENT_OUTPUT_FILE,
    ANALYSIS_REPORT_FILE
)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class ContentGenerator:
    """小红书内容生成器 / Xiaohongshu Content Generator"""
    
    def __init__(self):
        """初始化生成器 / Initialize generator"""
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.analysis_data = None
        self.generated_content = []
        
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
    
    def load_analysis_data(self, filename: str = None):
        """
        加载分析数据 / Load analysis data
        
        Args:
            filename: 分析报告文件名 / Analysis report filename
        """
        try:
            filename = filename or ANALYSIS_REPORT_FILE
            
            with open(filename, 'r', encoding='utf-8') as f:
                self.analysis_data = json.load(f)
            
            self.logger.info(f"成功加载分析数据 / Successfully loaded analysis data")
            
        except Exception as e:
            self.logger.error(f"加载分析数据失败 / Failed to load analysis data: {e}")
    
    def _build_analysis_summary(self) -> str:
        """
        构建分析摘要 / Build analysis summary
        
        用于发送给AI的背景信息
        
        Returns:
            分析摘要文本 / Analysis summary text
        """
        if not self.analysis_data:
            return ""
        
        summary_parts = []
        
        # 基本统计
        basic_stats = self.analysis_data.get('basic_stats', {})
        summary_parts.append(f"### 竞品数据概况")
        summary_parts.append(f"- 分析文章总数: {basic_stats.get('total_articles', 0)} 篇")
        summary_parts.append(f"- 平均热度指数: {basic_stats.get('avg_engagement_index', 0):.2f}")
        summary_parts.append(f"- 平均点赞数: {basic_stats.get('avg_likes', 0):.0f}")
        summary_parts.append(f"- 平均收藏数: {basic_stats.get('avg_collects', 0):.0f}")
        summary_parts.append(f"- 平均评论数: {basic_stats.get('avg_comments', 0):.0f}")
        
        # 标题分析
        title_analysis = self.analysis_data.get('title_analysis', {})
        summary_parts.append(f"\n### 标题特征")
        summary_parts.append(f"- 平均标题长度: {title_analysis.get('avg_title_length', 0):.0f} 字")
        
        # 关键词
        keywords = self.analysis_data.get('keywords_analysis', {}).get('top_keywords', [])
        if keywords:
            top_keywords = ", ".join([kw['word'] for kw in keywords[:10]])
            summary_parts.append(f"- 热门关键词: {top_keywords}")
        
        # 互动分析
        engagement = self.analysis_data.get('engagement_analysis', {})
        summary_parts.append(f"\n### 互动特征")
        summary_parts.append(f"- 平均收藏率: {engagement.get('collect_rate_avg', 0):.3f}")
        summary_parts.append(f"- 平均评论率: {engagement.get('comment_rate_avg', 0):.3f}")
        
        # 洞察
        insights = self.analysis_data.get('insights', [])
        if insights:
            summary_parts.append(f"\n### 关键洞察")
            for i, insight in enumerate(insights, 1):
                summary_parts.append(f"{i}. {insight}")
        
        return "\n".join(summary_parts)
    
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
                    temperature=0.8,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content
                return content
                
            except Exception as e:
                self.logger.warning(f"API调用失败，重试 {attempt + 1}/{max_retries} / API call failed, retry {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    self.logger.error(f"API调用最终失败 / API call finally failed: {e}")
                    return None
        
        return None
    
    def generate_topics(self, keyword: str = None) -> List[Dict]:
        """
        生成内容主题 / Generate content topics
        
        Args:
            keyword: 目标关键词 / Target keyword
            
        Returns:
            主题列表 / List of topics
        """
        try:
            self.logger.info("开始生成内容主题 / Starting content topic generation")
            
            # 构建提示词
            analysis_summary = self._build_analysis_summary()
            
            system_prompt = f"""你是一名资深的小红书内容运营专家，擅长创造爆款内容。你的任务是：
1. 基于竞品数据分析，生成高潜力的内容主题
2. 主题必须符合小红书用户的喜好和平台调性
3. 主题要有明确的痛点和价值主张
4. 主题要有情感共鸣和社交传播潜力

输出格式要求：
- 必须返回纯JSON格式
- JSON结构: {{"topics": [{{"id": 1, "title": "主题标题", "pain_point": "痛点描述", "solution": "解决方案", "emotion": "情感点", "keywords": ["关键词1", "关键词2"]}}]}}
- 生成 {NUM_TOPICS_TO_GENERATE} 个主题"""

            user_prompt = f"""基于以下竞品数据分析，为"{keyword}"赛道生成 {NUM_TOPICS_TO_GENERATE} 个高潜力的爆款内容主题：

{analysis_summary}

请确保主题：
1. 有明确的痛点切入
2. 有可落地的解决方案
3. 有情感共鸣点
4. 标题符合小红书风格（简洁有力、数字开头、情绪化表达）
5. 包含高转化关键词"""

            # 调用AI
            response = self._call_ai_api(system_prompt, user_prompt)
            
            if not response:
                self.logger.error("AI未返回响应 / AI did not return response")
                return []
            
            # 解析JSON响应
            try:
                # 清理可能的markdown代码块标记
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                result = json.loads(response)
                topics = result.get('topics', [])
                
                self.logger.info(f"成功生成 {len(topics)} 个主题 / Successfully generated {len(topics)} topics")
                
                return topics
                
            except json.JSONDecodeError as e:
                self.logger.error(f"解析AI响应失败 / Failed to parse AI response: {e}")
                self.logger.debug(f"原始响应 / Original response: {response}")
                return []
                
        except Exception as e:
            self.logger.error(f"生成主题失败 / Failed to generate topics: {e}")
            return []
    
    def generate_article_content(self, topic: Dict) -> Dict:
        """
        生成文章完整内容 / Generate complete article content
        
        Args:
            topic: 主题字典 / Topic dictionary
            
        Returns:
            包含标题和正文的字典 / Dictionary containing title and content
        """
        try:
            self.logger.info(f"生成主题内容: {topic.get('title', '')}")
            
            system_prompt = f"""你是一名小红书爆款内容创作者。你的任务是：
1. 基于给定的主题信息，创作完整的小红书笔记
2. 标题要吸引眼球，包含数字、情绪词或痛点
3. 正文结构清晰，分段明确
4. 使用丰富的Emoji表情增加趣味性
5. 语言风格要贴近小红书用户（亲切、真诚、有干货）
6. 包含明确的行动呼吁

输出格式要求：
- 必须返回纯JSON格式
- JSON结构: {{"title": "吸引眼球的标题", "content": "正文内容（包含Emoji，分段清晰）", "tags": ["标签1", "标签2", "标签3"]}}"""

            user_prompt = f"""基于以下主题信息，创作一篇小红书爆款笔记：

主题标题: {topic.get('title', '')}
痛点: {topic.get('pain_point', '')}
解决方案: {topic.get('solution', '')}
情感点: {topic.get('emotion', '')}
关键词: {', '.join(topic.get('keywords', []))}

创作要求：
1. 标题要包含数字、情绪词，15-25字
2. 正文结构：开头抓眼球 + 痛点描述 + 解决方案 + 情感共鸣 + 行动呼吁
3. 每段不超过100字，使用换行符分段
4. 适当使用Emoji（💡✨🔥💪等）
5. 结尾添加相关话题标签（3-5个）"""

            # 调用AI
            response = self._call_ai_api(system_prompt, user_prompt)
            
            if not response:
                self.logger.error("AI未返回响应 / AI did not return response")
                return None
            
            # 解析JSON响应
            try:
                # 清理可能的markdown代码块标记
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                result = json.loads(response)
                
                # 合并主题信息和生成的内容
                content_data = {
                    **topic,
                    "generated_title": result.get('title', ''),
                    "generated_content": result.get('content', ''),
                    "tags": result.get('tags', []),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.logger.info(f"成功生成文章内容 / Successfully generated article content")
                
                return content_data
                
            except json.JSONDecodeError as e:
                self.logger.error(f"解析AI响应失败 / Failed to parse AI response: {e}")
                self.logger.debug(f"原始响应 / Original response: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"生成文章内容失败 / Failed to generate article content: {e}")
            return None
    
    def generate_all_content(self, keyword: str = None) -> List[Dict]:
        """
        生成所有内容 / Generate all content
        
        完整流程：
        1. 生成主题
        2. 为每个主题生成完整文章
        
        Args:
            keyword: 目标关键词 / Target keyword
            
        Returns:
            生成的内容列表 / List of generated content
        """
        try:
            self.logger.info("开始生成所有内容 / Starting to generate all content")
            
            # 1. 生成主题
            topics = self.generate_topics(keyword)
            
            if not topics:
                self.logger.error("未能生成主题 / Failed to generate topics")
                return []
            
            # 2. 为每个主题生成完整内容
            self.generated_content = []
            
            for i, topic in enumerate(topics, 1):
                self.logger.info(f"生成第 {i}/{len(topics)} 篇文章 / Generating article {i}/{len(topics)}")
                
                content_data = self.generate_article_content(topic)
                
                if content_data:
                    content_data['article_id'] = i
                    self.generated_content.append(content_data)
            
            self.logger.info(f"所有内容生成完成，共 {len(self.generated_content)} 篇 / All content generation completed, total {len(self.generated_content)} articles")
            
            return self.generated_content
            
        except Exception as e:
            self.logger.error(f"生成所有内容失败 / Failed to generate all content: {e}")
            return []
    
    def save_content(self, content_list: List[Dict] = None, filename: str = None):
        """
        保存生成的内容 / Save generated content
        
        Args:
            content_list: 内容列表 / Content list
            filename: 保存文件名 / Save filename
        """
        try:
            content_list = content_list or self.generated_content
            filename = filename or CONTENT_OUTPUT_FILE
            
            if not content_list:
                self.logger.warning("没有内容可保存 / No content to save")
                return
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content_list, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"生成的内容已保存到 / Generated content saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"保存内容失败 / Failed to save content: {e}")
    
    def format_content_for_display(self, content: Dict) -> str:
        """
        格式化内容用于显示 / Format content for display
        
        Args:
            content: 内容字典 / Content dictionary
            
        Returns:
            格式化的文本 / Formatted text
        """
        formatted = []
        
        formatted.append("="*60)
        formatted.append(f"文章 #{content.get('article_id', '')}")
        formatted.append("="*60)
        formatted.append(f"\n【标题 / Title】\n{content.get('generated_title', '')}")
        formatted.append(f"\n【主题 / Topic】\n{content.get('title', '')}")
        formatted.append(f"\n【正文 / Content】\n{content.get('generated_content', '')}")
        formatted.append(f"\n【标签 / Tags】\n{', '.join(content.get('tags', []))}")
        formatted.append("\n" + "="*60 + "\n")
        
        return "\n".join(formatted)


# 便捷函数 / Convenience functions
def generate_rednote_content(keyword: str, analysis_file: str = None) -> List[Dict]:
    """
    便捷的内容生成函数 / Convenient content generation function
    
    Args:
        keyword: 目标关键词 / Target keyword
        analysis_file: 分析报告文件 / Analysis report file
        
    Returns:
        生成的内容列表 / List of generated content
    """
    generator = ContentGenerator()
    generator.load_analysis_data(analysis_file)
    content_list = generator.generate_all_content(keyword)
    generator.save_content()
    
    return content_list


if __name__ == "__main__":
    # 设置日志 / Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 示例使用 / Example usage
    generator = ContentGenerator()
    
    # 加载分析数据
    generator.load_analysis_data()
    
    # 生成内容
    keyword = "极简装修"
    content_list = generator.generate_all_content(keyword)
    
    # 保存内容
    generator.save_content()
    
    # 打印内容
    print("\n" + "="*60)
    print("生成的爆款内容 / Generated Viral Content")
    print("="*60 + "\n")
    
    for content in content_list:
        print(generator.format_content_for_display(content))
