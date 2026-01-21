#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
老北京文化·小红书内容生成器
读取文档内容，生成小红书文案和AI绘画提示词，保存到Excel和文件夹
"""

import os
import json
from datetime import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import openai
from typing import List, Dict, Tuple


class RedBookContentGenerator:
    """小红书内容生成器"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化生成器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.setup_paths()
        
        # API Key会在调用时检查，这里不需要初始化
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "input_file": "input_content.txt",
            "output_excel": "output/redbook_content.xlsx",
            "output_image_dir": "output/images",
            "openai_api_key": "",
            "openai_model": "gpt-4",
            "openai_base_url": None
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # 创建默认配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 已创建默认配置文件: {config_path}")
        
        return default_config
    
    def setup_paths(self):
        """设置路径"""
        # 确保输出目录存在
        excel_dir = os.path.dirname(self.config["output_excel"])
        if excel_dir and not os.path.exists(excel_dir):
            os.makedirs(excel_dir)
        
        # 创建图片输出目录（以日期命名）
        today = datetime.now().strftime("%Y%m%d")
        self.image_dir = os.path.join(self.config["output_image_dir"], today)
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
            print(f"✅ 已创建图片目录: {self.image_dir}")
    
    def read_input_file(self) -> str:
        """读取输入文档"""
        input_path = self.config["input_file"]
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"❌ 输入文件不存在: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            raise ValueError(f"❌ 输入文件为空: {input_path}")
        
        print(f"✅ 已读取输入文件: {input_path} ({len(content)} 字符)")
        return content
    
    def generate_content(self, raw_content: str) -> Dict:
        """
        调用AI生成小红书文案和绘画提示词
        
        Args:
            raw_content: 原始文档内容
            
        Returns:
            包含标题、正文、标签、绘画提示词的字典
        """
        prompt = f"""# Role: 老北京文化·小红书金牌运营 & 视觉导演

## Profile
你是一位深耕"老北京记忆"领域的小红书博主，擅长用细腻、怀旧、有温度的笔触重现四九城的往事。同时，你也是一位AI绘画提示词专家，能够将文字画面转化为风格统一的视觉描述。

## Goals
1. 读取用户输入的原始文案（通常是片段式的老北京回忆）。
2. 将其改写为一篇具备"爆款潜质"的小红书文案。
3. 提取文案中的关键画面，生成 3-5 组风格高度统一的 AI 绘画提示词（用于 Nano Banana 或 Stable Diffusion）。

## Constraints & Style
1. **文案风格**：
   - **京味儿**：适当使用北京方言（如：这地界儿、发小儿、甚至、大概齐），但不要过重影响阅读。
   - **沉浸感**：强调感官描写（鸽哨声、冬储大白菜味、煤球味、槐花香）。
   - **情感共鸣**：引发"回不去的小时候"或"岁月静好"的共鸣。
   - **排版**：多分段，每段不超过3行，多用Emoji，视觉舒适。

2. **视觉风格（必须统一）**：
   - 设定为：**90年代胶片摄影风格 (Vintage 90s Film Photography)** 或 **怀旧水彩插画风格 (Nostalgic Watercolor)**。
   - 画面需充满生活气息，色调偏暖（黄昏、灯光、阳光），带有颗粒感。

## Workflow

### Step 1: 文案创作
请提供 5 个吸引人的**【标题】**（包含悬念、情感或特定地名）。
正文请按以下结构撰写：
- **开头**：用一个具体的场景或声音切入，瞬间拉回那个年代。
- **中间**：展开故事，加入感官细节。
- **结尾**：升华情感，引导互动（问问大家还记不记得）。
- **标签**：添加 #老北京 #胡同记忆 #胶片 #童年回忆 等相关Tag。

### Step 2: 画面提取 (AI Image Prompts)
基于改写后的文案，提取 3-5 个最具画面感的场景。
输出格式为英文 Prompt（适合 Nano Banana），必须包含以下**固定风格后缀**以保证统一性：
*`--ar 3:4 --v 6.0 --style raw`*
*Style Keywords to add to every prompt: 1990s Beijing street photography, vintage kodak film, warm nostalgia tone, cinematic lighting, hyper-realistic, grainy texture.*

## Output Format
请严格按照以下JSON格式输出，不要包含任何其他文字：

{{
  "titles": [
    "标题1",
    "标题2",
    "标题3",
    "标题4",
    "标题5"
  ],
  "content": "正文内容（带Emoji，多分段）",
  "tags": "#老北京 #胡同记忆 #胶片 #童年回忆 #...",
  "image_prompts": [
    {{
      "scene": "场景简述",
      "prompt": "完整的英文Prompt，包含风格关键词和参数"
    }},
    {{
      "scene": "场景简述",
      "prompt": "完整的英文Prompt，包含风格关键词和参数"
    }}
  ]
}}

## 用户输入的原始文案：
{raw_content}

请开始生成内容："""

        try:
            # 调用 API（支持 OpenAI 或 阿里云通义千问 DashScope）
            api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("❌ 未找到 API Key，请设置环境变量 OPENAI_API_KEY 或在 config.json 中配置 openai_api_key")
            
            base_url = self.config.get("openai_base_url")
            model = self.config.get("openai_model", "gpt-4")
            
            # 使用通义千问 (Qwen) 且未指定 base_url 时，自动使用 DashScope 兼容接口
            if model == "qwen" or (isinstance(model, str) and model.startswith("qwen-")):
                if not base_url:
                    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
                if model == "qwen":
                    model = "qwen-plus"
            
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            
            client = openai.OpenAI(**client_kwargs)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一位专业的小红书内容创作专家和AI绘画提示词专家。请严格按照用户要求的JSON格式输出，不要添加任何解释性文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON响应
            result = json.loads(result_text)
            
            # 验证必要字段
            required_fields = ["titles", "content", "tags", "image_prompts"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"❌ AI返回结果缺少必要字段: {field}")
            
            print("✅ AI内容生成成功")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            if 'result_text' in locals():
                print(f"原始响应: {result_text[:500]}")
            raise
        except Exception as e:
            print(f"❌ AI生成失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def save_to_excel(self, content_data: Dict, raw_content: str):
        """
        保存内容到Excel文件
        
        Args:
            content_data: 生成的内容数据
            raw_content: 原始输入内容
        """
        excel_path = self.config["output_excel"]
        headers = [
            "生成时间", "原始内容", "标题1", "标题2", "标题3", "标题4", "标题5",
            "正文内容", "标签", "图片提示词1", "图片提示词2", "图片提示词3",
            "图片提示词4", "图片提示词5", "图片保存路径"
        ]
        
        # 检查文件是否存在
        if os.path.exists(excel_path):
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "小红书内容"
            
            # 创建表头
            
            # 设置表头样式
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            
            for col_idx, header in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # 设置列宽
            column_widths = [18, 40, 30, 30, 30, 30, 30, 60, 40, 50, 50, 50, 50, 50, 30]
            for col_idx, width in enumerate(column_widths, start=1):
                ws.column_dimensions[get_column_letter(col_idx)].width = width
        
        # 添加新行
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [
            now,  # 生成时间
            raw_content[:500] if len(raw_content) > 500 else raw_content,  # 原始内容（截断）
        ]
        
        # 添加标题
        titles = content_data.get("titles", [])
        for i in range(5):
            row_data.append(titles[i] if i < len(titles) else "")
        
        # 添加正文和标签
        row_data.append(content_data.get("content", ""))
        row_data.append(content_data.get("tags", ""))
        
        # 添加图片提示词
        image_prompts = content_data.get("image_prompts", [])
        for i in range(5):
            if i < len(image_prompts):
                prompt_text = f"{image_prompts[i].get('scene', '')}: {image_prompts[i].get('prompt', '')}"
                row_data.append(prompt_text)
            else:
                row_data.append("")
        
        # 添加图片保存路径
        row_data.append(self.image_dir)
        
        # 写入数据
        ws.append(row_data)
        
        # 设置数据行样式
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=ws.max_row, column=col_idx)
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        
        # 保存文件
        wb.save(excel_path)
        print(f"✅ 内容已保存到Excel: {excel_path}")
    
    def save_image_prompts(self, content_data: Dict):
        """
        保存图片提示词到文件
        
        Args:
            content_data: 生成的内容数据
        """
        prompts_file = os.path.join(self.image_dir, "image_prompts.txt")
        
        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write("# AI绘画提示词\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            image_prompts = content_data.get("image_prompts", [])
            for idx, prompt_data in enumerate(image_prompts, start=1):
                f.write(f"## 图{idx}: {prompt_data.get('scene', '')}\n\n")
                f.write(f"```\n{prompt_data.get('prompt', '')}\n```\n\n")
        
        print(f"✅ 图片提示词已保存: {prompts_file}")
    
    def save_full_content(self, content_data: Dict, raw_content: str):
        """
        保存完整内容到Markdown文件
        
        Args:
            content_data: 生成的内容数据
            raw_content: 原始输入内容
        """
        md_file = os.path.join(self.image_dir, "content.md")
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 小红书文案预览\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📕 可选标题\n\n")
            titles = content_data.get("titles", [])
            for idx, title in enumerate(titles, start=1):
                f.write(f"{idx}. {title}\n")
            
            f.write("\n## 📝 正文内容\n\n")
            f.write(content_data.get("content", ""))
            
            f.write("\n\n## 🏷️ 标签\n\n")
            f.write(content_data.get("tags", ""))
            
            f.write("\n\n## 🎨 AI绘画提示词 (Nano Banana)\n\n")
            image_prompts = content_data.get("image_prompts", [])
            for idx, prompt_data in enumerate(image_prompts, start=1):
                f.write(f"### 图{idx}: {prompt_data.get('scene', '')}\n\n")
                f.write(f"```\n{prompt_data.get('prompt', '')}\n```\n\n")
            
            f.write("\n---\n\n")
            f.write("## 📄 原始输入内容\n\n")
            f.write(raw_content)
        
        print(f"✅ 完整内容已保存: {md_file}")
    
    def run(self):
        """运行主流程"""
        try:
            print("=" * 60)
            print("🚀 老北京文化·小红书内容生成器")
            print("=" * 60)
            
            # 1. 读取输入文件
            raw_content = self.read_input_file()
            
            # 2. 生成内容
            print("\n🤖 正在调用AI生成内容...")
            content_data = self.generate_content(raw_content)
            
            # 3. 保存到Excel
            print("\n💾 正在保存到Excel...")
            self.save_to_excel(content_data, raw_content)
            
            # 4. 保存图片提示词
            print("\n💾 正在保存图片提示词...")
            self.save_image_prompts(content_data)
            
            # 5. 保存完整内容
            print("\n💾 正在保存完整内容...")
            self.save_full_content(content_data, raw_content)
            
            print("\n" + "=" * 60)
            print("✅ 所有任务完成！")
            print(f"📁 Excel文件: {self.config['output_excel']}")
            print(f"📁 图片目录: {self.image_dir}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="老北京文化·小红书内容生成器")
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="配置文件路径 (默认: config.json)"
    )
    
    args = parser.parse_args()
    
    generator = RedBookContentGenerator(config_path=args.config)
    generator.run()


if __name__ == "__main__":
    main()
