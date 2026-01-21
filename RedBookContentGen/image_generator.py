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
from typing import List, Dict


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
    
    def parse_prompts_file(self, prompts_file: str) -> List[Dict]:
        """
        解析图片提示词文件
        
        Args:
            prompts_file: 提示词文件路径
            
        Returns:
            提示词列表，每项包含 scene 和 prompt
        """
        if not os.path.exists(prompts_file):
            raise FileNotFoundError(f"❌ 提示词文件不存在: {prompts_file}")
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析提示词
        prompts = []
        # 匹配格式: ## 图N: 场景描述\n\n```\nprompt\n```
        pattern = r'## 图(\d+): (.*?)\n\n```(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            # 尝试另一种格式: ## 图N: 场景描述\n```\nprompt\n```
            pattern = r'## 图(\d+): (.*?)\n```(.*?)```'
            matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            idx = int(match[0])
            scene = match[1].strip()
            prompt = match[2].strip()  # 代码块中的英文 prompt
            prompts.append({
                "index": idx,
                "scene": scene,
                "prompt": prompt
            })
        
        if not prompts:
            raise ValueError(f"❌ 无法从文件中解析出提示词: {prompts_file}")
        
        print(f"✅ 成功解析 {len(prompts)} 个提示词")
        return prompts
    
    def generate_image_async(self, prompt: str, index: int) -> str:
        """
        异步生成单张图片
        
        Args:
            prompt: 图片提示词
            index: 图片索引
            
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
        
        print(f"  📤 正在生成图{index}: {prompt[:50]}...")
        
        # 创建任务
        response = requests.post(
            self.image_generation_url,
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"❌ 创建任务失败: {response.status_code} - {response.text}")
        
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
    
    def generate_all_images(self, prompts_file: str):
        """
        生成所有图片
        
        Args:
            prompts_file: 提示词文件路径
        """
        print("=" * 60)
        print("🎨 图片生成器")
        print("=" * 60)
        
        # 解析提示词
        print(f"\n📖 正在读取提示词文件: {prompts_file}")
        prompts = self.parse_prompts_file(prompts_file)
        
        # 确定输出目录
        prompts_dir = os.path.dirname(prompts_file)
        if not prompts_dir:
            prompts_dir = "."
        
        print(f"\n📁 输出目录: {prompts_dir}")
        
        # 生成每张图片
        print(f"\n🎨 开始生成图片（模型: {self.image_model}）\n")
        
        for prompt_data in prompts:
            try:
                print(f"\n{'='*50}")
                print(f"图{prompt_data['index']}: {prompt_data['scene'][:60]}...")
                print(f"{'='*50}")
                
                # 生成图片
                image_url = self.generate_image_async(prompt_data['prompt'], prompt_data['index'])
                
                # 下载图片
                image_filename = f"image_{prompt_data['index']:02d}.png"
                save_path = os.path.join(prompts_dir, image_filename)
                self.download_image(image_url, save_path)
                
            except Exception as e:
                print(f"\n❌ 生成图{prompt_data['index']}失败: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("✅ 所有任务完成！")
        print(f"📁 图片已保存到: {prompts_dir}")
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
