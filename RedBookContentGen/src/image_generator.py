#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成器
读取图片提示词文件，调用通义万相API生成图片
"""

import os
import re
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("⚠️  警告: 未安装PIL/Pillow，无法使用文字叠加功能。请运行: pip install Pillow")


class ImageGenerator:
    """图片生成器"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化生成器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # API Key检查
        self.api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ 未找到API Key，请设置环境变量 OPENAI_API_KEY 或在config.json中配置 openai_api_key")
        
        # 通义万相API配置（文生图）
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.image_generation_url = f"{self.base_url}/services/aigc/text2image/image-synthesis"
        self.task_status_url = f"{self.base_url}/tasks"
        
        # 图片生成模型
        self.image_model = self.config.get("image_model", "wan2.2-t2i-flash")
        
        # AI改写配置
        self.enable_ai_rewrite = self.config.get("enable_ai_rewrite", True)
        self.rewrite_model = self.config.get("rewrite_model", "qwen-max")
        
        # 通义千问API配置(用于文案改写)
        self.llm_base_url = self.config.get("openai_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        # 可疑内容记录文件
        self.suspicious_content_file = None
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            "openai_api_key": "",
            "image_model": "wan2.2-t2i-flash",
            "output_image_dir": "output/images"
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def check_content_safety(self, prompt: str, content_type: str = "prompt") -> Tuple[bool, str]:
        """
        检查内容是否可能触发内容审核失败
        
        注意：此函数只检查真正敏感的内容，不会误杀正常的历史文化内容
        （如天安门、故宫、广场等历史文化地标是正常的）
        
        Args:
            prompt: 要检查的内容（提示词或正文）
            content_type: 内容类型（"prompt" 或 "content"）
            
        Returns:
            (是否安全, 修改后的内容)
        """
        if not prompt:
            return True, prompt
        
        # 真正敏感的词汇（只检查明显不当的内容）
        # 注意：不包含"天安门"、"广场"、"故宫"等正常历史文化词汇
        sensitive_keywords = [
            # 明显政治敏感（不含正常历史描述）
            '革命', '暴动', '叛乱', '政变',
            # 明显暴力
            '血腥', '杀戮', '屠杀', '武器', '枪', '刀',
            # 明显色情
            '色情', '裸露', '情色',
            # 其他明显敏感
            '恐怖', '爆炸', '毒品', '赌博',
        ]
        
        # 检查是否包含敏感词
        # 注意：中文没有词边界，所以直接检查是否包含关键词
        # 但只检查明显敏感的词，不误杀正常历史文化内容
        found_keywords = []
        for keyword in sensitive_keywords:
            if keyword in prompt:
                found_keywords.append(keyword)
        
        if found_keywords:
            # 尝试移除敏感词
            modified_prompt = prompt
            for keyword in found_keywords:
                modified_prompt = modified_prompt.replace(keyword, '')
            # 清理多余空格
            modified_prompt = re.sub(r'\s+', ' ', modified_prompt).strip()
            return False, modified_prompt
        
        return True, prompt
    
    def save_suspicious_content(self, prompts_dir: str, content: str, content_type: str, reason: str):
        """
        保存可疑内容到文件，供用户修改
        
        Args:
            prompts_dir: 输出目录
            content: 可疑内容
            content_type: 内容类型
            reason: 失败原因
        """
        if self.suspicious_content_file is None:
            self.suspicious_content_file = os.path.join(prompts_dir, "suspicious_content.txt")
            with open(self.suspicious_content_file, 'w', encoding='utf-8') as f:
                f.write("# 可疑内容记录\n\n")
                f.write("以下内容在生成图片时可能触发内容审核失败，请手动修改后重新生成。\n\n")
                f.write("=" * 60 + "\n\n")
        
        with open(self.suspicious_content_file, 'a', encoding='utf-8') as f:
            f.write(f"## {content_type}\n\n")
            f.write(f"**失败原因**: {reason}\n\n")
            f.write(f"**原始内容**:\n```\n{content}\n```\n\n")
            f.write("**建议**: 请移除或替换上述敏感词汇，然后重新运行脚本。\n\n")
            f.write("-" * 60 + "\n\n")
    
    def parse_prompts_file(self, prompts_file: str) -> Tuple[List[Dict], str]:
        """
        解析图片提示词文件
        
        Args:
            prompts_file: 提示词文件路径
            
        Returns:
            (提示词列表, 正文内容)
        """
        if not os.path.exists(prompts_file):
            raise FileNotFoundError(f"❌ 提示词文件不存在: {prompts_file}")
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析正文内容
        body_text = ""
        body_match = re.search(r'## 正文内容\n\n(.*?)\n\n---', content, re.DOTALL)
        if body_match:
            body_text = body_match.group(1).strip()
        
        # 解析提示词：图1-4（故事图）+ 封面
        prompts = []
        # 匹配 ## 图N: 场景\n\n``` prompt ```
        for m in re.finditer(r'## 图(\d+): (.*?)\n\n```(.*?)```', content, re.DOTALL):
            idx = int(m.group(1))
            scene = m.group(2).strip()
            prompt = m.group(3).strip()
            prompts.append({"index": idx, "scene": scene, "prompt": prompt, "is_cover": False, "title": None})
        
        # 匹配 ## 封面: 短标题\n\n``` prompt ```
        cover_m = re.search(r'## 封面:\s*(.*?)\n\n```(.*?)```', content, re.DOTALL)
        if cover_m:
            title = cover_m.group(1).strip()
            prompt = cover_m.group(2).strip()
            prompts.append({"index": 0, "scene": f"封面：{title}", "prompt": prompt, "is_cover": True, "title": title})
        
        if not prompts:
            raise ValueError(f"❌ 无法从文件中解析出提示词: {prompts_file}")
        
        n_cover = sum(1 for p in prompts if p.get("is_cover"))
        print(f"✅ 成功解析 {len(prompts)} 个提示词" + ("（含 1 张封面）" if n_cover else ""))
        if body_text:
            print(f"✅ 已读取正文内容（{len(body_text)} 字符）")
        return prompts, body_text
    
    def generate_image_async(self, prompt: str, index: int, is_cover: bool = False) -> str:
        """
        异步生成单张图片
        
        Args:
            prompt: 图片提示词
            index: 图片索引
            is_cover: 是否为封面图
            
        Returns:
            图片URL
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        # 清理提示词，移除 --ar --v 等参数（通义万相不需要）
        clean_prompt = re.sub(r'--ar\s*\d+:\d+', '', prompt)
        clean_prompt = re.sub(r'--v\s*\d+(\.\d+)?', '', clean_prompt)
        clean_prompt = re.sub(r'--style\s+\w+', '', clean_prompt)
        clean_prompt = clean_prompt.strip()
        
        # 构建请求数据
        data = {
            "model": self.image_model,
            "input": {
                "prompt": clean_prompt
            },
            "parameters": {
                "size": "1024*1365",  # 3:4 比例
                "n": 1,
                "watermark": False
            }
        }
        
        # 默认负面提示词（用于所有图片）
        default_negative_prompt = "nsfw, text, watermark, username, signature, logo, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, blurry"
        
        # 如果是封面图，添加额外的负面提示词
        if is_cover:
            # 针对文字的负面提示词
            cover_negative = "乱码文字，错误汉字，无法识别的字符，文字模糊，文字扭曲，文字重叠，非标准汉字，错别字，文字不清晰，字符遗漏，文字不完整，缺少汉字"
            data["input"]["negative_prompt"] = f"{default_negative_prompt}, {cover_negative}"
        else:
            # 故事图也可以使用默认负面提示词
            data["input"]["negative_prompt"] = default_negative_prompt
        
        lab = "封面" if index == "封面" else f"图{index}"
        print(f"  📤 正在生成{lab}: {prompt[:50]}...")
        
        # 创建任务
        response = requests.post(
            self.image_generation_url,
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            error_text = response.text
            # 检查是否是内容不当的错误
            if response.status_code == 400:
                try:
                    error_json = response.json()
                    if error_json.get("code") == "DataInspectionFailed" or "inappropriate content" in error_text.lower():
                        raise ValueError(f"内容审核未通过: {error_json.get('message', '内容可能包含不当信息')}")
                except:
                    pass
            raise Exception(f"❌ 创建任务失败: {response.status_code} - {error_text}")
        
        resp_json = response.json()
        
        if "output" not in resp_json or "task_id" not in resp_json["output"]:
            raise Exception(f"❌ 响应格式错误: {resp_json}")
        
        task_id = resp_json["output"]["task_id"]
        print(f"  ✅ 任务创建成功: {task_id}")
        
        # 轮询任务状态
        return self._wait_for_task_completion(task_id)
    
    def _wait_for_task_completion(self, task_id: str, max_wait: int = 300) -> str:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait: 最大等待时间（秒）
            
        Returns:
            图片URL
        """
        status_url = f"{self.task_status_url}/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start_time = time.time()
        poll_interval = 3
        
        while time.time() - start_time < max_wait:
            response = requests.get(status_url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"❌ 查询任务状态失败: {response.status_code} - {response.text}")
            
            resp_json = response.json()
            task_status = resp_json.get("output", {}).get("task_status", "")
            
            if task_status == "SUCCEEDED":
                # 获取图片URL（兼容 output.results[0].url 与 output.choices[0].image）
                output = resp_json.get("output", {})
                results = output.get("results", [])
                if results and "url" in results[0]:
                    image_url = results[0]["url"]
                    print(f"  ✅ 图片生成成功")
                    return image_url
                choices = output.get("choices", [])
                if choices and choices[0].get("image"):
                    image_url = choices[0]["image"]
                    print(f"  ✅ 图片生成成功")
                    return image_url
                raise Exception("❌ 任务成功但未返回图片URL")
            
            elif task_status == "FAILED":
                raise Exception(f"❌ 任务失败: {resp_json}")
            
            elif task_status in ["PENDING", "RUNNING", "INITIALIZING"]:
                print(f"  ⏳ 等待中... 状态: {task_status}", end="\r")
                time.sleep(poll_interval)
            
            else:
                print(f"  ⚠️  未知状态: {task_status}")
                time.sleep(poll_interval)
        
        raise Exception(f"❌ 任务超时（{max_wait}秒）")
    
    def download_image(self, image_url: str, save_path: str):
        """
        下载图片
        
        Args:
            image_url: 图片URL
            save_path: 保存路径
        """
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(image_url, headers=headers, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"❌ 下载图片失败: {response.status_code}")
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"  💾 已保存: {save_path}")
    
    def clean_text_for_display(self, text: str) -> str:
        """
        清理文字，移除特殊符号，只保留纯文案
        
        Args:
            text: 原始文字
            
        Returns:
            清理后的文字
        """
        if not text:
            return ""
        
        # 移除emoji和特殊符号
        # 保留中文、英文、数字、常用标点符号（。，！？：；、""''（））
        import re
        
        # 移除emoji（Unicode范围）
        text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # 表情符号
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # 表情符号
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # 交通和地图符号
        text = re.sub(r'[\U00002600-\U000026FF]', '', text)  # 杂项符号
        text = re.sub(r'[\U00002700-\U000027BF]', '', text)  # 装饰符号
        text = re.sub(r'[\U0001FA00-\U0001FAFF]', '', text)  # 扩展A
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # 补充符号
        
        # 移除其他特殊符号（保留常用标点）
        # 移除箭头、特殊标记等
        text = re.sub(r'[👇👆🔔🌿👴💡⭐🌟✨🔥💯📝📖📕📝🎨🏷️]', '', text)  # 常见emoji
        text = re.sub(r'[→←↑↓⇒⇐⇑⇓↗↘↙↖]', '', text)  # 箭头
        text = re.sub(r'[【】《》〈〉「」『』]', '', text)  # 特殊括号
        
        # 移除其他特殊字符，但保留常用标点
        # 保留：。，！？：；、""''（）【】《》——…（中文标点）
        # 移除其他特殊符号
        # 使用更精确的字符类匹配
        # 保留：中文字符、英文字母、数字、常用中文标点、常用英文标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff。，！？：；、""''（）【】《》——…\n]', '', text)
        
        # 清理多余空白
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符合并为一个空格
        
        # 修复转义换行符 - 关键修复:处理字符串中的\n字面量
        # 问题: 正文内容中的\n是字符串字面量,不是真正的换行符
        # 解决: 将字符串"\\n"(两个字符:反斜杠+n)替换为真正的换行符
        text = text.replace('\\\\n', '\n')  # 处理双反斜杠+n
        text = text.replace('\\n', '\n')    # 处理单个反斜杠+n
        
        # 进一步清理：移除残留的孤立 'n' 字符
        # 这些通常是 \n 被分割或处理后留下的单一字母 n
        lines_temp = text.split('\n')
        cleaned_lines = []
        for line in lines_temp:
            # 1. 如果整行只有字母 n 或其重复（如 nn, n n），跳过
            stripped = line.strip()
            if re.fullmatch(r'[n\s]+', stripped):
                continue
            
            # 2. 移除行首/句首的 'n' (后面紧跟中文或空格)
            line = re.sub(r'^n\s*', '', line)
            
            # 3. 移除中文字符之间的孤立 'n' (可能带空格或标点)
            # 例如 "处理。n每" -> "处理。每", "宫殿，n它" -> "宫殿，它"
            # 匹配逻辑：[中文字符/标点] + [n/带空格的n] + [中文字符]
            line = re.sub(r'([\u4e00-\u9fff]|[，。！？：；、])\s*n\s*(?=[\u4e00-\u9fff])', r'\1', line)
            
            # 4. 移除行尾的孤立 n
            line = re.sub(r'\s*n$', '', line)
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行合并为两个
        text = re.sub(r' +\n', '\n', text)  # 行尾空格
        text = re.sub(r'\n +', '\n', text)  # 行首空格
        text = text.strip()
        
        return text
    
    def _estimate_max_chars(self, max_width: int, max_lines: int, font, draw) -> int:
        """
        估算给定宽度和行数下,最多可以容纳多少字符
        
        Args:
            max_width: 每行最大宽度(像素)
            max_lines: 最大行数
            font: 字体对象
            draw: 绘图对象
            
        Returns:
            估算的最大字符数
        """
        # 使用常见中文字符测试平均宽度
        test_chars = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"
        
        # 计算单个字符平均宽度
        total_width = 0
        sample_size = min(50, len(test_chars))
        for char in test_chars[:sample_size]:
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            total_width += char_width
        
        avg_char_width = total_width / sample_size if sample_size > 0 else font.size
        
        # 估算每行字符数
        chars_per_line = int(max_width / avg_char_width)
        
        # 总字符数 = 每行字符数 × 行数,留10%余量
        estimated_chars = int(chars_per_line * max_lines * 0.9)
        
        return max(10, estimated_chars)  # 至少10个字符
    
    def rewrite_text_for_display(self, text: str, max_chars: int, context: str = "") -> str:
        """
        使用AI改写文案,使其符合长度限制且语义通顺
        
        Args:
            text: 原始文案
            max_chars: 最大字符数
            context: 上下文信息(如场景描述)
            
        Returns:
            改写后的文案,如果改写失败则返回原文
        """
        # 如果未启用AI改写,直接返回原文
        if not self.enable_ai_rewrite:
            return text
        
        # 如果文案本身就不长,无需改写
        if len(text) <= max_chars:
            return text
        
        try:
            # 构建改写提示词
            prompt = f"""请将以下文案精简改写,要求:
1. 保留核心信息和关键内容
2. 语言通顺流畅,符合小红书风格
3. 控制在{max_chars}字以内
4. 不要添加任何额外说明,只输出改写后的文案

原文案({len(text)}字):
{text}

改写后的文案:"""
            
            # 调用通义千问API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.rewrite_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_chars * 2  # 留足够的token空间
            }
            
            response = requests.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                rewritten = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                # 验证改写结果
                if rewritten and len(rewritten) <= max_chars * 1.1:  # 允许10%误差
                    print(f"  ✨ AI改写成功: {len(text)}字 → {len(rewritten)}字")
                    return rewritten
                else:
                    print(f"  ⚠️  AI改写结果不符合要求,使用原文")
                    return text
            else:
                print(f"  ⚠️  AI改写API调用失败: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"  ⚠️  AI改写失败: {e}")
            return text

    
    def add_text_overlay(self, image_path: str, text: str, output_path: Optional[str] = None, 
                        is_cover: bool = True, position: str = "top"):
        """
        在图片上叠加文字（用于封面图和故事图）
        
        Args:
            image_path: 图片路径
            text: 要叠加的文字
            output_path: 输出路径（如果为None，则覆盖原文件）
            is_cover: 是否为封面图（True=封面，False=故事图）
            position: 文字位置（"top"=顶部，"bottom"=底部）
        """
        if not HAS_PIL:
            print("  ⚠️  跳过文字叠加：未安装PIL/Pillow")
            return
        
        if not text or not text.strip():
            print("  ⚠️  跳过文字叠加：文字为空")
            return
        
        # 清理文字，移除特殊符号
        text = self.clean_text_for_display(text)
        
        if not text or not text.strip():
            print("  ⚠️  跳过文字叠加：清理后文字为空")
            return
        
        try:
            # 打开图片
            img = Image.open(image_path)
            img = img.convert('RGB')  # 确保是RGB模式
            
            # 创建绘图对象
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # 字体路径列表
            font_paths = [
                # macOS - 优先使用粗体字体
                "/System/Library/Fonts/PingFang.ttc",  # 尝试不同索引获取粗体
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                # Windows - 优先黑体
                "C:/Windows/Fonts/simhei.ttf",  # 黑体（粗体）
                "C:/Windows/Fonts/simkai.ttf",  # 楷体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑粗体
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                # Linux
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/arphic/uming.ttc",
            ]
            
            def load_font(size):
                """加载指定大小的字体"""
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            if font_path.endswith('.ttc'):
                                from PIL import ImageFont
                                try:
                                    return ImageFont.truetype(font_path, size, index=1)
                                except:
                                    return ImageFont.truetype(font_path, size, index=0)
                            else:
                                return ImageFont.truetype(font_path, size)
                        except:
                            continue
                # 如果找不到字体，使用默认字体
                try:
                    return ImageFont.truetype("arial.ttf", size)
                except:
                    return ImageFont.load_default()
            
            # 根据图片类型设置字体大小
            if is_cover:
                font_size = int(height * 0.10)  # 封面：字体大小为图片高度的10%
            else:
                font_size = int(height * 0.06)  # 故事图：字体大小为图片高度的6%，较小不遮挡画面
            
            font = load_font(font_size)
            
            # 计算可用宽度（留出左右边距）
            margin = int(width * 0.1)  # 左右各留10%边距
            available_width = width - 2 * margin
            
            # 检测文字是否需要换行
            # 使用实际文字计算高度（使用包含上下字符的测试文本，更准确）
            # 使用包含上下字符的测试文本，获取准确的行高
            test_chars = "测\n测"  # 包含上下字符
            bbox_test = draw.textbbox((0, 0), test_chars, font=font)
            # 如果textbbox不支持换行，使用单行但包含上下字符
            if bbox_test[3] - bbox_test[1] < font_size * 1.5:  # 如果高度异常小，说明不支持换行
                # 使用单行包含上下字符的文字
                test_chars = "测"  # 使用单个字符
                bbox_test = draw.textbbox((0, 0), test_chars, font=font)
                text_height = bbox_test[3] - bbox_test[1]
            else:
                text_height = (bbox_test[3] - bbox_test[1]) / 2  # 单行高度
            
            # 计算文字宽度
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            
            # 如果文字宽度超过可用宽度，需要换行或调整字体
            if text_width > available_width:
                # 尝试缩小字体
                max_font_size = font_size
                min_font_size = int(height * 0.06)  # 最小字体为高度的6%
                
                # 二分查找合适的字体大小
                optimal_font_size = max_font_size
                optimal_font = font
                
                for test_size in range(max_font_size, min_font_size - 1, -2):
                    try:
                        test_font = load_font(test_size)
                        test_bbox = draw.textbbox((0, 0), text, font=test_font)
                        test_width = test_bbox[2] - test_bbox[0]
                        if test_width <= available_width:
                            optimal_font_size = test_size
                            optimal_font = test_font
                            break
                    except:
                        continue
                
                font = optimal_font
                font_size = optimal_font_size
                
                # 重新计算文字尺寸
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            
            # 使用简化的换行逻辑
            max_lines = 3
            lines = self._wrap_text_simple(text, available_width, font, draw, max_lines)
            
            # 如果文字超过最大行数,尝试AI改写
            if len(lines) > max_lines:
                # 估算最大字符数
                estimated_max_chars = self._estimate_max_chars(available_width, max_lines, font, draw)
                print(f"  📏 文字超长({len(text)}字),尝试AI改写到{estimated_max_chars}字以内...")
                
                # 尝试AI改写
                rewritten_text = self.rewrite_text_for_display(text, estimated_max_chars)
                
                # 如果改写成功且不同于原文,使用改写后的文字
                if rewritten_text and rewritten_text != text:
                    text = rewritten_text
                    lines = self._wrap_text_simple(text, available_width, font, draw, max_lines)
                
                # 如果改写后仍超长,或改写失败,使用截断
                if len(lines) > max_lines:
                    print(f"  ✂️  改写后仍超长,使用智能截断")
                    lines = self._smart_truncate_simple(text, max_lines, available_width, font, draw)
            
            # 计算行高（固定比例，确保不重叠）
            test_bbox = draw.textbbox((0, 0), "测", font=font)
            line_height = int((test_bbox[3] - test_bbox[1]) * 1.7)  # 行高 = 字体高度 * 1.7(修复重叠)
            total_height = len(lines) * line_height
            
            # 计算起始Y位置
            margin_y = int(height * 0.08)
            if position == "bottom":
                start_y = height - total_height - margin_y
                if start_y < height * 0.5:  # 确保不遮挡画面中央以上
                    start_y = int(height * 0.5)
            else:
                start_y = margin_y
            
            # 确保不超出边界
            if start_y + total_height > height - margin_y:
                start_y = height - total_height - margin_y
            if start_y < margin_y:
                start_y = margin_y
            
            # 设置颜色
            # 说明：
            # - 行高用字体metrics（更稳定），再叠加“leading(行距)”和描边影响
            # - 行数少时行距更紧凑，行数多时略放大
            shadow_offset = int(font_size * 0.08)  # 描边宽度
            try:
                ascent, descent = font.getmetrics()
                base_line_height = ascent + descent
            except Exception:
                base_line_height = int(text_height)

            n_lines = max(1, len(lines))
            
            # 行间距：使用固定的合理比例，避免过大或过小
            # 封面图：行间距稍小（更紧凑）
            # 故事图：行间距稍大（更易读）
            if is_cover:
                # 封面：行间距为字体高度的25%
                line_spacing_ratio = 0.25
            else:
                # 故事图：行间距为字体高度的30%
                line_spacing_ratio = 0.30
            
            # 计算行间距（像素）
            line_spacing = int(base_line_height * line_spacing_ratio)
            # 描边会让上下“吃”掉空间，这里给一点补偿，但不让间距失控
            outline_px = max(2, shadow_offset // 2)

            # 行高 = 字体高度 + 行间距
            line_height = base_line_height + line_spacing
            # 确保行高不会太小（至少是字体高度的1.2倍）或太大（最多是字体高度的1.6倍）
            min_line_height = int(base_line_height * 1.2)
            max_line_height = int(base_line_height * 1.6)
            line_height = max(min_line_height, min(line_height, max_line_height))

            total_height = (n_lines - 1) * line_height + base_line_height
            
            # 根据位置参数计算起始Y位置，确保文字完整显示在图片范围内
            if position == "bottom":
                # 底部位置：距离底部一定距离（适合故事图）
                start_y = height - total_height - int(height * 0.15)  # 增加底部边距
                # 确保文字在画面下半部分，不遮挡主要画面，且完整显示
                if start_y < height * 0.55:  # 确保不遮挡画面中央以上区域
                    start_y = int(height * 0.55)
                # 确保最后一行文字不会超出图片底部
                last_line_y = start_y + (len(lines) - 1) * line_height
                margin_bottom = int(height * 0.08)  # 底部边距8%
                if last_line_y + text_height > height - margin_bottom:
                    # 如果超出，重新计算最大行数并截断
                    available_height = height - start_y - margin_bottom
                    max_lines_by_height = int(available_height / line_height)
                    max_lines = min(max_lines_by_height, 3)  # 最多3行
                    if max_lines < 1:
                        max_lines = 1
                    
                    if len(lines) > max_lines:
                        # 使用智能截断
                        lines = self._smart_truncate(text, max_lines, available_width, font, draw)
                        # 重新计算总高度
                        n_lines = len(lines)
                        total_height = (n_lines - 1) * line_height + base_line_height
                        start_y = height - total_height - margin_bottom
                    else:
                        # 缩小字体
                        font_size = int(font_size * 0.9)
                        font = load_font(font_size)
                        test_chars = "测"
                        bbox = draw.textbbox((0, 0), test_chars, font=font)
                        text_height = bbox[3] - bbox[1]
                        shadow_offset = int(font_size * 0.08)
                        spacing_multiplier = 2.5 if not is_cover else 2.2
                        line_height = int(text_height * spacing_multiplier) + shadow_offset + 5
                        total_height = (len(lines) - 1) * line_height + text_height
                        start_y = height - total_height - int(height * 0.15)
            else:
                # 顶部位置（封面图）
                start_y = int(height * 0.20)  # 距离顶部20%
                if total_height > height * 0.3:  # 如果总高度超过30%，调整位置
                    start_y = int(height * 0.15)
                # 确保文字不会超出图片顶部
                if start_y < int(height * 0.1):
                    start_y = int(height * 0.1)
            
            # 设置颜色
            if is_cover:
                text_color = (101, 67, 33)
                shadow_color = (255, 255, 255)
            else:
                text_color = (255, 255, 255)
                shadow_color = (0, 0, 0)
            
            # 绘制每一行
            shadow_offset = max(2, int(font_size * 0.05))
            margin_x = int(width * 0.08)
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                
                # 确保不超出左右边界
                if x < margin_x:
                    x = margin_x
                elif x + line_width > width - margin_x:
                    x = width - line_width - margin_x
                
                y = start_y + i * line_height
                
                # 确保不超出上下边界
                if y < margin_y or y + line_height > height - margin_y:
                    continue
                
                # 绘制描边
                for dx in range(-shadow_offset, shadow_offset + 1):
                    for dy in range(-shadow_offset, shadow_offset + 1):
                        if abs(dx) + abs(dy) <= shadow_offset:
                            draw.text((x + dx, y + dy), line, font=font, fill=shadow_color)
                
                # 绘制主文字
                draw.text((x, y), line, font=font, fill=text_color)
            
            # 保存图片
            if output_path is None:
                output_path = image_path
            img.save(output_path, 'PNG', quality=95)
            print(f"  ✨ 已添加文字叠加: {text[:30]}...")
            
        except Exception as e:
            print(f"  ⚠️  文字叠加失败: {e}")
            import traceback
            traceback.print_exc()
    
    def split_content_by_scenes(self, content: str, scenes: List[str]) -> List[str]:
        """
        根据图片场景描述，智能分段正文内容，确保文字与图片场景有契合度
        
        Args:
            content: 完整正文内容
            scenes: 场景描述列表（对应每张图片）
            
        Returns:
            分段后的正文内容列表
        """
        if not content or not scenes:
            return []
        
        # 清理内容：移除多余空白，但保留换行结构（emoji会在叠加时清理）
        clean_content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 按段落分割（双换行或单行）
        # 先按双换行分割
        paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]
        
        # 如果段落内部还有单换行，进一步分割（但保持逻辑连贯性）
        refined_paragraphs = []
        for para in paragraphs:
            # 如果段落很长（超过100字），尝试在句号、问号、感叹号处分割
            if len(para) > 120:
                sentences = re.split(r'([。！？\n])', para)
                current_sentence = ""
                for i in range(0, len(sentences), 2):
                    if i < len(sentences):
                        current_sentence += sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                        if len(current_sentence) > 100:  # 每段约100字(修复语义截断)
                            refined_paragraphs.append(current_sentence.strip())
                            current_sentence = ""
                if current_sentence.strip():
                    refined_paragraphs.append(current_sentence.strip())
            else:
                refined_paragraphs.append(para)
        
        paragraphs = refined_paragraphs if refined_paragraphs else paragraphs
        
        # 如果段落数少于图片数，需要拆分段落
        if len(paragraphs) < len(scenes):
            # 将较长的段落拆分
            expanded_paragraphs = []
            for para in paragraphs:
                if len(para) > 150:
                    # 按句子拆分
                    sentences = re.split(r'([。！？])', para)
                    current = ""
                    for i in range(0, len(sentences), 2):
                        if i < len(sentences):
                            current += sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                            if len(current) > 100:
                                expanded_paragraphs.append(current.strip())
                                current = ""
                    if current.strip():
                        expanded_paragraphs.append(current.strip())
                else:
                    expanded_paragraphs.append(para)
            paragraphs = expanded_paragraphs
        
        # 分配段落到图片
        result = []
        para_index = 0
        
        for i, scene in enumerate(scenes):
            # 每张图分配1-2个段落，确保故事完整性
            segments_for_image = []
            
            # 第一张图：分配开头段落
            if i == 0:
                if para_index < len(paragraphs):
                    segments_for_image.append(paragraphs[para_index])
                    para_index += 1
                # 如果段落还多，可以再分配一个
                if para_index < len(paragraphs) and len(paragraphs) > len(scenes):
                    segments_for_image.append(paragraphs[para_index])
                    para_index += 1
            
            # 中间图片：分配1-2个段落
            elif i < len(scenes) - 1:
                segments_count = 1
                # 如果剩余段落较多，可以多分配
                remaining_paras = len(paragraphs) - para_index
                remaining_images = len(scenes) - i
                if remaining_paras > remaining_images:
                    segments_count = min(2, remaining_paras - remaining_images + 1)
                
                for _ in range(segments_count):
                    if para_index < len(paragraphs):
                        segments_for_image.append(paragraphs[para_index])
                        para_index += 1
            
            # 最后一张图：分配剩余所有段落
            else:
                while para_index < len(paragraphs):
                    segments_for_image.append(paragraphs[para_index])
                    para_index += 1
            
            # 合并段落
            result.append("\n\n".join(segments_for_image) if segments_for_image else "")
        
        return result
    
    def _wrap_text_simple(self, text: str, max_width: int, font, draw, max_lines: int = 3) -> List[str]:
        """
        简化的文字换行函数，确保稳定可靠
        """
        if not text:
            return []
        
        lines = []
        current_line = ""
        punctuation = set(['。', '，', '！', '？', '；', '：', '、'])
        
        for char in text:
            test = current_line + char
            try:
                bbox = draw.textbbox((0, 0), test, font=font)
                test_width = bbox[2] - bbox[0]
            except:
                # 如果textbbox失败，使用字符数估算（中文字符约等于字体大小）
                test_width = len(test) * (font.size if hasattr(font, 'size') else 60)
            
            if test_width <= max_width:
                current_line = test
            else:
                # 当前行已满，需要换行
                if current_line:
                    lines.append(current_line)
                    if len(lines) >= max_lines:
                        break
                    current_line = char
                else:
                    # 单个字符就超出，强制添加（避免死循环）
                    current_line = char
        
        # 添加最后一行
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        
        # 后处理：合并单独的标点符号
        result = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if len(line) == 1 and line in punctuation and result:
                result[-1] += line
            else:
                result.append(line)
        
        return result if result else [text[:20]]  # 至少返回一行
    
    def _smart_truncate_simple(self, text: str, max_lines: int, max_width: int, font, draw) -> List[str]:
        """
        简化的智能截断函数
        """
        lines = self._wrap_text_simple(text, max_width, font, draw, max_lines + 1)
        if len(lines) <= max_lines:
            return lines
        
        # 截断到max_lines行，最后一行加省略号
        result = lines[:max_lines-1] if max_lines > 1 else []
        last = "".join(lines[max_lines-1:])
        
        ellipsis = "…"
        ellipsis_w = draw.textbbox((0, 0), ellipsis, font=font)[2] - draw.textbbox((0, 0), ellipsis, font=font)[0]
        available = max_width - ellipsis_w - 5
        
        last_line = ""
        for char in last:
            test = last_line + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= available:
                last_line = test
            else:
                break
        
        if last_line:
            result.append(last_line + ellipsis)
        elif result:
            # 如果最后一行放不下，在前一行末尾加省略号
            prev = result[-1]
            while len(prev) > 0:
                test = prev + ellipsis
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    result[-1] = test
                    break
                prev = prev[:-1]
        
        return result if result else [ellipsis]
    
    def _smart_truncate(self, text: str, max_lines: int, max_width: int, font, draw) -> List[str]:
        """
        智能截断文字，确保不超过指定行数，并在合适位置添加省略号
        
        Args:
            text: 原始文字
            max_lines: 最大行数
            max_width: 每行最大宽度
            font: 字体对象
            draw: 绘图对象
            
        Returns:
            截断后的文字行列表（最多max_lines行）
        """
        if not text:
            return []
        
        # 先按宽度换行
        all_lines = self._wrap_text(text, max_width, font, draw)
        
        # 如果行数不超过限制，直接返回
        if len(all_lines) <= max_lines:
            return all_lines
        
        # 如果超过，只取前max_lines-1行，最后一行添加省略号
        result_lines = all_lines[:max_lines-1]
        
        # 计算省略号宽度
        ellipsis = "…"
        ellipsis_bbox = draw.textbbox((0, 0), ellipsis, font=font)
        ellipsis_width = ellipsis_bbox[2] - ellipsis_bbox[0]
        available_for_last_line = max_width - ellipsis_width - 5  # 留5像素安全边距
        
        # 从剩余文字中截取能放入最后一行的内容
        remaining_text = "".join(all_lines[max_lines-1:])
        last_line = ""
        
        # 优先在标点符号处截断（更自然），但避免标点符号单独成行
        punctuation_marks = ['。', '，', '！', '？', '；', '：', '、', '…', '.', ',', '!', '?', ';', ':']
        
        for char in remaining_text:
            test_line = last_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width <= available_for_last_line:
                last_line = test_line
                # 如果遇到标点符号，且已经有足够内容，可以在这里截断（更自然）
                # 但确保标点符号不会单独成行（即last_line长度>1）
                if char in punctuation_marks and len(last_line) > 1:
                    # 检查标点符号是否在行尾（如果是，可以截断）
                    break
            else:
                # 如果超出，尝试在最后一个标点处截断
                if len(last_line) > 1:  # 确保不是只有标点符号
                    # 从后往前找标点符号，但确保标点符号前面有内容
                    for i in range(len(last_line) - 1, 0, -1):  # 从倒数第二个字符开始，避免只有标点
                        if last_line[i] in punctuation_marks:
                            last_line = last_line[:i+1]
                            break
                break
        
        # 如果最后一行有内容，添加省略号
        if last_line:
            # 确保添加省略号后不超出
            test_line = last_line + ellipsis
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width <= max_width:
                result_lines.append(test_line)
            else:
                # 如果超出，移除最后一个字符再添加省略号
                while len(last_line) > 0:
                    last_line = last_line[:-1]
                    test_line = last_line + ellipsis
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    test_width = bbox[2] - bbox[0]
                    if test_width <= max_width:
                        result_lines.append(test_line)
                        break
                else:
                    # 如果还是放不下，只用省略号
                    result_lines.append(ellipsis)
        else:
            # 如果最后一行放不下任何内容，在前一行的末尾添加省略号
            if result_lines:
                prev_line = result_lines[-1]
                if len(prev_line) > 0:
                    # 尝试移除字符直到能放下省略号
                    while len(prev_line) > 0:
                        test_line = prev_line + ellipsis
                        bbox = draw.textbbox((0, 0), test_line, font=font)
                        test_width = bbox[2] - bbox[0]
                        if test_width <= max_width:
                            result_lines[-1] = test_line
                            break
                        prev_line = prev_line[:-1]
                    else:
                        # 如果还是放不下，直接用省略号替换
                        result_lines[-1] = ellipsis
                else:
                    result_lines.append(ellipsis)
            else:
                result_lines.append(ellipsis)
        
        return result_lines
    
    def _wrap_text(self, text: str, max_width: int, font, draw) -> List[str]:
        """
        将文字按宽度自动换行，智能处理标点符号，避免标点单独成行
        
        Args:
            text: 原始文字
            max_width: 最大宽度
            font: 字体对象
            draw: 绘图对象
            
        Returns:
            分行后的文字列表（已优化，避免标点单独成行）
        """
        if not text:
            return []
        
        # 定义标点符号（不应单独成行）
        punctuation_marks = set(['。', '，', '！', '？', '；', '：', '、', '…', '.', ',', '!', '?', ';', ':', '…'])
        # 前引号、后引号等特殊标点
        opening_punctuation = set(['（', '(', '【', '[', '《', '<', '"', '"', ''', '''])
        closing_punctuation = set(['）', ')', '】', ']', '》', '>', '"', '"', ''', '''])
        
        lines = []
        current_line = ""
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # 测试添加当前字符后的宽度
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                # 可以添加，继续
                current_line = test_line
                i += 1
            else:
                # 当前行已满，需要换行
                if current_line:
                    # 检查当前行末尾是否是标点符号
                    # 如果是标点，应该保留在当前行，不换行
                    if current_line[-1] in punctuation_marks:
                        # 标点已经在行尾，保留在当前行
                        lines.append(current_line)
                        current_line = ""
                    else:
                        # 尝试向后查找，看下一个字符是否是标点
                        if i < len(text) and text[i] in punctuation_marks:
                            # 下一个字符是标点，应该保留在当前行
                            # 尝试缩小字体或截断，但这里先尝试将标点加入当前行
                            # 如果标点加入后仍然超出，则保留当前行，标点放到下一行
                            test_with_punct = current_line + text[i]
                            bbox_punct = draw.textbbox((0, 0), test_with_punct, font=font)
                            if bbox_punct[2] - bbox_punct[0] <= max_width:
                                # 标点可以加入当前行
                                current_line = test_with_punct
                                i += 1
                                lines.append(current_line)
                                current_line = ""
                            else:
                                # 标点加入后超出，保留当前行，标点放到下一行（但我们会后续优化）
                                lines.append(current_line)
                                current_line = text[i]
                                i += 1
                        else:
                            # 下一个字符不是标点，正常换行
                            lines.append(current_line)
                            current_line = char
                            i += 1
                else:
                    # 当前行为空，但单个字符就超出（不应该发生，但处理一下）
                    # 强制添加，因为单个字符必须显示
                    current_line = char
                    i += 1
        
        # 添加最后一行
        if current_line:
            lines.append(current_line)
        
        # 后处理：优化标点符号位置，避免标点单独成行
        optimized_lines = []
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 如果当前行只有一个标点符号，尝试合并到上一行
            if len(line) == 1 and line in punctuation_marks:
                if optimized_lines:
                    # 合并到上一行
                    optimized_lines[-1] = optimized_lines[-1] + line
                else:
                    # 没有上一行，保留（但这种情况应该很少）
                    optimized_lines.append(line)
            # 如果当前行以标点开头，且上一行存在，尝试合并
            elif line and line[0] in punctuation_marks and optimized_lines:
                # 检查合并后是否超出宽度
                merged = optimized_lines[-1] + line
                bbox_merged = draw.textbbox((0, 0), merged, font=font)
                if bbox_merged[2] - bbox_merged[0] <= max_width:
                    optimized_lines[-1] = merged
                else:
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)
        
        # 如果只有一行且仍然超出，强制按字符数分割（每行最多10个字符）
        if len(optimized_lines) == 1 and len(text) > 10:
            # 智能分割：尽量在语义断点分割
            optimized_lines = []
            # 尝试在"的"、"之"、"前"、"后"等字后分割
            split_points = ['的', '之', '前', '后', '上', '下', '里', '中', '为', '是', '，', '。', '！', '？']
            current_line = ""
            
            for i, char in enumerate(text):
                current_line += char
                # 如果当前行达到一定长度，且在分割点，则换行
                if len(current_line) >= 8 and char in split_points:
                    optimized_lines.append(current_line)
                    current_line = ""
                # 如果当前行超过10个字符，强制换行
                elif len(current_line) >= 10:
                    optimized_lines.append(current_line)
                    current_line = ""
            
            if current_line:
                optimized_lines.append(current_line)
        
        return optimized_lines if optimized_lines else [text]
    
    def generate_all_images(self, prompts_file: str):
        """
        生成所有图片
        
        Args:
            prompts_file: 提示词文件路径
        """
        print("=" * 60)
        print("🎨 图片生成器")
        print("=" * 60)
        
        # 解析提示词和正文内容
        print(f"\n📖 正在读取提示词文件: {prompts_file}")
        prompts, body_text = self.parse_prompts_file(prompts_file)
        
        # 如果有正文内容，进行智能分段
        content_segments = []
        if body_text:
            story_scenes = [p.get('scene', '') for p in prompts if not p.get('is_cover', False)]
            content_segments = self.split_content_by_scenes(body_text, story_scenes)
            print(f"✅ 正文内容已分段为 {len(content_segments)} 段")
        
        # 确定输出目录
        prompts_dir = os.path.dirname(prompts_file)
        if not prompts_dir:
            prompts_dir = "."
        
        print(f"\n📁 输出目录: {prompts_dir}")
        
        # 初始化可疑内容记录文件
        self.suspicious_content_file = None
        
        # 预检查所有提示词和正文内容
        print(f"\n🔍 正在预检查内容安全性...")
        checked_prompts = []
        for prompt_data in prompts:
            is_cover = prompt_data.get("is_cover", False)
            prompt = prompt_data.get('prompt', '')
            
            # 检查提示词
            is_safe, modified_prompt = self.check_content_safety(prompt, "提示词")
            if not is_safe:
                print(f"  ⚠️  检测到可疑内容（{'封面' if is_cover else f'图{prompt_data.get("index", 0)}'}），已自动修改")
                prompt_data['prompt'] = modified_prompt
                # 如果修改后仍然可疑，记录
                is_safe_after, _ = self.check_content_safety(modified_prompt, "提示词")
                if not is_safe_after:
                    self.save_suspicious_content(
                        prompts_dir, 
                        prompt, 
                        f"{'封面' if is_cover else f'图{prompt_data.get("index", 0)}'}提示词",
                        "包含敏感词汇，自动修改后仍可能有问题"
                    )
            
            checked_prompts.append(prompt_data)
        
        # 检查正文内容分段
        if content_segments:
            for idx, segment in enumerate(content_segments, start=1):
                is_safe, modified_segment = self.check_content_safety(segment, "正文内容")
                if not is_safe:
                    print(f"  ⚠️  检测到可疑正文内容（图{idx}），已自动修改")
                    content_segments[idx - 1] = modified_segment
                    is_safe_after, _ = self.check_content_safety(modified_segment, "正文内容")
                    if not is_safe_after:
                        self.save_suspicious_content(
                            prompts_dir,
                            segment,
                            f"图{idx}正文内容",
                            "包含敏感词汇，自动修改后仍可能有问题"
                        )
        
        prompts = checked_prompts
        print(f"✅ 内容预检查完成\n")
        
        # 生成每张图片
        print(f"\n🎨 开始生成图片（模型: {self.image_model}）\n")
        
        for prompt_data in prompts:
            max_retries = 3  # 最多重试3次
            retry_count = 0
            success = False
            original_prompt = prompt_data['prompt']  # 保存原始提示词
            
            while retry_count <= max_retries and not success:
                try:
                    is_cover = prompt_data.get("is_cover", False)
                    if is_cover:
                        print(f"\n{'='*50}")
                        print(f"封面: {prompt_data.get('title', '')}")
                        print(f"{'='*50}")
                        lbl = "封面"
                    else:
                        print(f"\n{'='*50}")
                        print(f"图{prompt_data['index']}: {prompt_data['scene'][:60]}...")
                        print(f"{'='*50}")
                        lbl = prompt_data['index']
                    
                    # 如果是重试，进一步修改提示词
                    current_prompt = prompt_data['prompt']
                    if retry_count > 0:
                        print(f"  🔄 第 {retry_count} 次重试，正在进一步修改提示词...")
                        # 再次检查并修改
                        is_safe, modified_prompt = self.check_content_safety(current_prompt, "提示词")
                        if not is_safe:
                            current_prompt = modified_prompt
                        # 移除更多可能敏感的关键词
                        sensitive_words = ['血腥', '暴力', '色情', '政治', '敏感', '争议', '战争', '武器']
                        for word in sensitive_words:
                            current_prompt = current_prompt.replace(word, '')
                        # 简化描述
                        current_prompt = re.sub(r'\s+', ' ', current_prompt).strip()
                        prompt_data['prompt'] = current_prompt
                        print(f"  ✅ 提示词已修改")
                    
                    image_url = self.generate_image_async(current_prompt, lbl, is_cover=is_cover)
                    
                    if is_cover:
                        image_filename = "cover.png"
                    else:
                        image_filename = f"image_{prompt_data['index']:02d}.png"
                    save_path = os.path.join(prompts_dir, image_filename)
                    self.download_image(image_url, save_path)
                    
                    # 添加文字叠加
                    if is_cover:
                        # 封面图：叠加标题
                        title = prompt_data.get('title', '')
                        if title:
                            print(f"  📝 正在添加文字叠加: {title}")
                            self.add_text_overlay(save_path, title, is_cover=True, position="top")
                    else:
                        # 故事图：叠加正文内容分段
                        idx = prompt_data.get('index', 0)
                        if content_segments and idx > 0 and idx <= len(content_segments):
                            content_segment = content_segments[idx - 1]
                            if content_segment:
                                print(f"  📝 正在添加文字叠加: {content_segment[:30]}...")
                                self.add_text_overlay(save_path, content_segment, is_cover=False, position="bottom")
                        else:
                            # 如果没有正文分段，使用场景描述作为后备
                            scene = prompt_data.get('scene', '')
                            if scene:
                                print(f"  📝 正在添加文字叠加（场景描述）: {scene[:30]}...")
                                self.add_text_overlay(save_path, scene, is_cover=False, position="bottom")
                    
                    success = True
                    
                except ValueError as e:
                    # 内容审核未通过的错误
                    who = "封面" if prompt_data.get("is_cover") else f"图{prompt_data['index']}"
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"\n⚠️  生成{who}失败（内容审核未通过）: {e}")
                        print(f"  🔄 将尝试修改提示词后重试...")
                    else:
                        print(f"\n❌ 生成{who}失败（已重试{max_retries}次）: {e}")
                        # 保存可疑内容到文件
                        self.save_suspicious_content(
                            prompts_dir,
                            original_prompt,
                            f"{who}提示词",
                            f"内容审核未通过，已尝试{max_retries}次自动修改仍失败"
                        )
                        print(f"  📝 可疑内容已保存到: {os.path.basename(self.suspicious_content_file)}")
                        print(f"  💡 请查看可疑内容文件，手动修改后重新运行脚本")
                        success = False
                        break
                        
                except Exception as e:
                    who = "封面" if prompt_data.get("is_cover") else f"图{prompt_data['index']}"
                    error_msg = str(e)
                    # 检查是否是内容不当的错误
                    if "DataInspectionFailed" in error_msg or "inappropriate content" in error_msg.lower():
                        if retry_count < max_retries:
                            retry_count += 1
                            print(f"\n⚠️  生成{who}失败（内容审核未通过）: {e}")
                            print(f"  🔄 将尝试修改提示词后重试...")
                        else:
                            print(f"\n❌ 生成{who}失败（已重试{max_retries}次）: {e}")
                            # 保存可疑内容到文件
                            self.save_suspicious_content(
                                prompts_dir,
                                original_prompt,
                                f"{who}提示词",
                                f"内容审核未通过，已尝试{max_retries}次自动修改仍失败"
                            )
                            print(f"  📝 可疑内容已保存到: {os.path.basename(self.suspicious_content_file)}")
                            print(f"  💡 请查看可疑内容文件，手动修改后重新运行脚本")
                            success = False
                            break
                    else:
                        print(f"\n❌ 生成{who}失败: {e}")
                        success = False
                        break
        
        print(f"\n{'='*60}")
        print("✅ 所有任务完成！")
        print(f"📁 图片已保存到: {prompts_dir}")
        if self.suspicious_content_file and os.path.exists(self.suspicious_content_file):
            print(f"⚠️  发现可疑内容，已保存到: {os.path.basename(self.suspicious_content_file)}")
            print(f"   请查看并手动修改后重新生成相关图片")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="图片生成器 - 基于提示词文件生成图片")
    parser.add_argument(
        "-p", "--prompts",
        help="提示词文件路径（默认：使用最新日期文件夹下的 image_prompts.txt）"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="配置文件路径（默认：config.json）"
    )
    
    args = parser.parse_args()
    
    generator = ImageGenerator(config_path=args.config)
    
    # 确定提示词文件路径
    if args.prompts:
        prompts_file = args.prompts
    else:
        # 使用最新日期文件夹
        output_dir = generator.config.get("output_image_dir", "output/images")
        if os.path.exists(output_dir):
            # 找出最新的日期文件夹
            date_dirs = sorted([d for d in os.listdir(output_dir) 
                             if os.path.isdir(os.path.join(output_dir, d))], 
                            reverse=True)
            if date_dirs:
                prompts_file = os.path.join(output_dir, date_dirs[0], "image_prompts.txt")
                print(f"💡 使用最新日期文件夹: {date_dirs[0]}")
            else:
                raise FileNotFoundError(f"❌ 在 {output_dir} 中未找到日期文件夹")
        else:
            raise FileNotFoundError(f"❌ 输出目录不存在: {output_dir}")
    
    # 生成所有图片
    generator.generate_all_images(prompts_file)


if __name__ == "__main__":
    main()
