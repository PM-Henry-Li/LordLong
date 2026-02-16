#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书内容整理器
从多条笔记中提取和整理关键内容,生成适合作为输入的文本
"""

import os
import json
from typing import List, Dict
import openai


class ContentOrganizer:
    """内容整理器"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化整理器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf - 8") as f:
                return json.load(f)
        return {}

    def extract_key_content(self, notes: List[Dict]) -> str:
        """
        从多条笔记中提取关键内容

        Args:
            notes: 笔记列表,每个笔记包含 title, content, tags 等

        Returns:
            提取的关键内容文本
        """
        if not notes:
            return ""

        print(f"\n📝 开始整理 {len(notes)} 条笔记内容...")

        # 收集所有内容
        all_titles = []
        all_contents = []
        all_tags = []

        for note in notes:
            title = note.get("title", "")
            if title:
                all_titles.append(title)

            # 优先使用完整内容,没有则使用预览
            content = note.get("content", "") or note.get("preview_text", "")
            if content:
                all_contents.append(content)

            tags = note.get("tags", [])
            if tags:
                all_tags.extend(tags)

        # 去重标签
        unique_tags = list(set(all_tags))

        print(f"   - 标题: {len(all_titles)} 个")
        print(f"   - 内容段落: {len(all_contents)} 个")
        print(f"   - 标签: {len(unique_tags)} 个")

        # 构建原始内容摘要
        raw_summary = {"titles": all_titles, "contents": all_contents, "tags": unique_tags, "note_count": len(notes)}

        return raw_summary

    def merge_and_organize(self, raw_summary: Dict) -> str:
        """
        使用AI合并和组织内容,生成适合作为输入的文本

        Args:
            raw_summary: 原始内容摘要

        Returns:
            整理后的文本
        """
        print("\n🤖 使用AI整理内容...")

        # 获取API配置
        api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  未找到API Key,将使用简单合并方式")
            return self._simple_merge(raw_summary)

        base_url = self.config.get("openai_base_url")
        model = self.config.get("openai_model", "gpt - 4")

        # 兼容性处理
        if model == "qwen" or (isinstance(model, str) and model.startswith("qwen-")):
            if not base_url:
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            if model == "qwen":
                model = "qwen-plus"

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = openai.OpenAI(**client_kwargs)

        # 构建提示词
        prompt = self._build_organize_prompt(raw_summary)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的内容编辑,擅长从多个来源提取和整合信息,生成连贯的文本。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            organized_content = response.choices[0].message.content.strip()

            print("✅ AI整理完成")
            return organized_content

        except Exception as e:
            print(f"⚠️  AI整理失败: {e},使用简单合并方式")
            return self._simple_merge(raw_summary)

    def _build_organize_prompt(self, raw_summary: Dict) -> str:
        """构建整理提示词"""
        # 提取数据（最多10个标题、10段内容、20个标签）
        # titles = raw_summary.get("titles", [])[:10]
        # contents = raw_summary.get("contents", [])[:10]
        # tags = raw_summary.get("tags", [])[:20]

        prompt = """请帮我整理以下从小红书搜索到的{raw_summary.get('note_count', 0)}条高分笔记内容。

**任务要求**:
1. 从这些笔记中提取共同的主题、故事和细节
2. 去除重复内容,保留最有价值的信息
3. 生成一段200 - 500字的连贯文本,具有故事性和画面感
4. 文字要自然、生动,避免机械堆砌
5. 保留原笔记中的情感色彩和细节描写

**笔记标题**:
{chr(10).join([f"- {title}" for title in titles[:5]])}
{'...' if len(titles) > 5 else ''}

**笔记内容片段**:
{chr(10).join([f"「{content[:150]}...」" for content in contents[:5]])}
{'...' if len(contents) > 5 else ''}

**相关标签**: {', '.join(tags[:15])}

请生成整理后的内容(只输出文本内容,不要包含标题等):"""

        return prompt

    def _simple_merge(self, raw_summary: Dict) -> str:
        """
        简单合并方式(不使用AI)

        Args:
            raw_summary: 原始内容摘要

        Returns:
            合并后的文本
        """
        contents = raw_summary.get("contents", [])

        if not contents:
            return "暂无内容"

        # 简单拼接,每段之间换行
        merged = "\n\n".join(contents[:5])  # 最多取5段

        return merged

    def format_as_input(self, organized_content: str, topic: str = "") -> str:
        """
        格式化为适合作为输入的文本

        Args:
            organized_content: 整理后的内容
            topic: 原始搜索主题

        Returns:
            格式化后的输入文本
        """
        print("\n📄 格式化为输入文本...")

        # 添加说明信息
        formatted = """# 基于小红书主题搜索整理的内容

主题: {topic}
整理时间: {self._get_current_time()}

---

{organized_content}
"""

        print("✅ 格式化完成")
        return formatted

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def process_notes(
        self,
        notes: List[Dict],
        topic: str = "",
        save_to_file: bool = False,
        output_path: str = "input/topic_content.txt",
    ) -> str:
        """
        处理笔记的完整流程

        Args:
            notes: 笔记列表
            topic: 搜索主题
            save_to_file: 是否保存到文件
            output_path: 输出文件路径

        Returns:
            处理后的文本
        """
        # 1. 提取关键内容
        raw_summary = self.extract_key_content(notes)

        # 2. 合并和组织
        organized_content = self.merge_and_organize(raw_summary)

        # 3. 格式化
        formatted_text = self.format_as_input(organized_content, topic)

        # 4. 保存到文件(可选)
        if save_to_file:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf - 8") as f:
                f.write(formatted_text)
            print(f"✅ 内容已保存到: {output_path}")

        return formatted_text


def main():
    """测试函数"""
    # 模拟笔记数据
    test_notes = [
        {
            "title": "老北京胡同的夏天",
            "content": "记得小时候,每到夏天,胡同里就特别热闹。大槐树下总聚着一群老人下棋,孩子们在旁边追逐打闹。",
            "tags": ["#老北京", "#胡同", "#童年回忆"],
            "likes": 5000,
        },
        {
            "title": "那些年的胡同生活",
            "content": "胡同口的小卖部,是我们最常去的地方。5毛钱的冰棍,1块钱的汽水,都是最美好的回忆。",
            "tags": ["#老北京", "#胡同", "#80后"],
            "likes": 3000,
        },
    ]

    organizer = ContentOrganizer()
    result = organizer.process_notes(
        test_notes, topic="老北京胡同", save_to_file=True, output_path="output/test_organized.txt"
    )

    print("\n" + "=" * 60)
    print("整理结果:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()
