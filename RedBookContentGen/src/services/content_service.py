#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容生成服务

封装小红书内容生成的业务逻辑
"""

from typing import Dict, List
from datetime import datetime
from pathlib import Path

from src.content_generator import RedBookContentGenerator
from src.core.config_manager import ConfigManager
from src.core.logger import Logger
from src.core.errors import ContentGenerationError, ValidationError


class ContentService:
    """内容生成服务类"""

    def __init__(self, config_manager: ConfigManager, output_dir: Path):
        """
        初始化内容生成服务

        Args:
            config_manager: 配置管理器实例
            output_dir: 输出目录路径
        """
        self.config_manager = config_manager
        self.output_dir = output_dir
        self.content_generator = RedBookContentGenerator(config_manager=config_manager)

    def generate_content(self, input_text: str, count: int = 1) -> Dict:
        """
        生成小红书内容（文案和图片提示词）

        Args:
            input_text: 输入文本
            count: 生成数量（限制最多5条）

        Returns:
            包含文案数据和图片任务列表的字典

        Raises:
            ValidationError: 输入文本为空
            ContentGenerationError: 生成失败
        """
        # 验证输入
        if not input_text or not input_text.strip():
            raise ValidationError(
                message="输入文本不能为空",
                details={"field": "input_text"},
                suggestions=["请输入至少10个字符的内容描述"],
            )

        input_text = input_text.strip()
        count = min(int(count), 5)  # 限制最多5条

        # 保存输入文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / f"input_{timestamp}.txt").write_text(input_text, encoding="utf - 8")

        Logger.info("开始生成小红书文案", logger_name="content_service", input_preview=input_text[:20])

        try:
            # 调用内容生成器
            raw_data = self.content_generator.generate_content(input_text)

            # 解析数据
            titles = raw_data.get("titles", [])
            title = titles[0] if titles else "小红书笔记"
            content = raw_data.get("content", "")
            tags_str = raw_data.get("tags", "")
            tags = [t.strip().replace("#", "") for t in tags_str.split("#") if t.strip()]

            # 构造图片任务列表
            image_tasks = self._build_image_tasks(raw_data, input_text, count)

            return {
                "title": title,
                "titles": titles,
                "content": content,
                "tags": tags,
                "image_tasks": image_tasks,
                "raw_data": raw_data,
                "timestamp": timestamp,
            }

        except Exception as e:
            Logger.exception("文案生成失败", logger_name="content_service")
            raise ContentGenerationError(
                message=f"文案生成失败: {str(e)}",
                details={"input_preview": input_text[:50]},
                suggestions=["请检查输入文本是否符合要求", "请稍后重试", "如果问题持续，请联系技术支持"],
            )

    def generate_batch(self, inputs: List[str], count: int = 1) -> Dict:
        """
        批量生成小红书内容
        
        Args:
            inputs: 输入文本列表
            count: 每个输入生成的内容数量
            
        Returns:
            包含批量生成结果的字典：
            {
                "batch_id": "批次ID",
                "total": 总任务数,
                "results": [
                    {
                        "index": 索引,
                        "input_text": "输入文本",
                        "status": "success/failed",
                        "data": {...} or None,
                        "error": "错误信息" or None
                    },
                    ...
                ],
                "summary": {
                    "success": 成功数量,
                    "failed": 失败数量,
                    "total": 总数量
                }
            }
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        Logger.info(
            "开始批量生成内容",
            logger_name="content_service",
            batch_id=batch_id,
            total_inputs=len(inputs),
            count_per_input=count,
        )
        
        results = []
        success_count = 0
        failed_count = 0
        
        for i, input_text in enumerate(inputs):
            try:
                Logger.info(
                    f"处理第 {i + 1}/{len(inputs)} 条输入",
                    logger_name="content_service",
                    batch_id=batch_id,
                    index=i + 1,
                )
                
                # 生成单条内容
                result = self.generate_content(input_text, count)
                
                results.append({
                    "index": i,
                    "input_text": input_text[:50] + "..." if len(input_text) > 50 else input_text,
                    "status": "success",
                    "data": result,
                    "error": None,
                })
                success_count += 1
                
            except Exception as e:
                Logger.error(
                    f"第 {i + 1} 条输入生成失败",
                    logger_name="content_service",
                    batch_id=batch_id,
                    index=i + 1,
                    error=str(e),
                )
                
                results.append({
                    "index": i,
                    "input_text": input_text[:50] + "..." if len(input_text) > 50 else input_text,
                    "status": "failed",
                    "data": None,
                    "error": str(e),
                })
                failed_count += 1
        
        Logger.info(
            "批量生成完成",
            logger_name="content_service",
            batch_id=batch_id,
            success=success_count,
            failed=failed_count,
        )
        
        return {
            "batch_id": batch_id,
            "total": len(inputs),
            "results": results,
            "summary": {
                "success": success_count,
                "failed": failed_count,
                "total": len(inputs),
            },
        }

    def _build_image_tasks(self, raw_data: Dict, input_text: str, count: int) -> List[Dict]:
        """
        构建图片任务列表，并实现内容智能分段
        """
        tasks = []
        content = raw_data.get("content", "")
        
        # 1. 封面图
        cover_data = raw_data.get("cover", {})
        tasks.append({
            "id": "cover",
            "type": "cover",
            "title": cover_data.get("title", raw_data.get("titles", ["小红书"])[0]),
            "scene": cover_data.get("scene", "封面大片"),
            "prompt": cover_data.get("prompt", input_text),
            "content_text": "", # 封面不显示正文摘要，防止重叠
            "index": 0,
        })

        # 2. 插图内容预处理：智能分段
        image_prompts = raw_data.get("image_prompts", [])
        content_images_count = len(image_prompts) if image_prompts else 3
        
        # 智能切分正文为 N 份
        content_chunks = self._split_content_into_chunks(content, content_images_count)

        if not image_prompts:
            for i in range(3):
                tasks.append({
                    "id": f"content_{i + 1}",
                    "type": "content",
                    "title": f"图{i + 1}",
                    "scene": "细节展示",
                    "prompt": input_text,
                    "content_text": content_chunks[i] if i < len(content_chunks) else "",
                    "index": i + 1,
                })
        else:
            for i, p in enumerate(image_prompts):
                tasks.append({
                    "id": f"content_{i + 1}",
                    "type": "content",
                    "title": f"图{i + 1}",
                    "scene": p.get("scene", f"细节{i + 1}"),
                    "prompt": p.get("prompt", input_text),
                    "content_text": content_chunks[i] if i < len(content_chunks) else "",
                    "index": i + 1,
                })

        return tasks

    def _split_content_into_chunks(self, text: str, n: int) -> List[str]:
        """将长文本按语义边界切分为 n 份"""
        if not text or n <= 0:
            return [""] * n
            
        import re
        # 按句子结束符切分
        sentences = re.split(r'([。！？；\n])', text)
        processed_sentences = []
        for i in range(0, len(sentences)-1, 2):
            processed_sentences.append(sentences[i] + sentences[i+1])
        if len(sentences) % 2 == 1 and sentences[-1]:
            processed_sentences.append(sentences[-1])
            
        if not processed_sentences:
            return [text[:len(text)//n]] * n
            
        # 尽量均匀分配句子到 n 个块
        chunks = []
        avg = len(processed_sentences) / n
        last = 0.0
        while last < len(processed_sentences):
            start = int(last)
            end = int(last + avg)
            chunks.append("".join(processed_sentences[start:end]))
            last += avg
            
        # 确保返回的总数一致
        while len(chunks) < n:
            chunks.append("")
        return chunks[:n]
