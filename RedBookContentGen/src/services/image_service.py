#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成服务

封装图片生成的业务逻辑
"""

import base64
import time
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from src.image_generator import ImageGenerator
from src.template_image_generator import TemplateImageGenerator
from src.services.composite_service import CompositeImageService
from src.core.config_manager import ConfigManager
from src.core.logger import Logger
from src.core.errors import ImageGenerationError, ValidationError


class ImageService:
    """图片生成服务类"""

    def __init__(self, config_manager: ConfigManager, output_dir: Path):
        """
        初始化图片生成服务

        Args:
            config_manager: 配置管理器实例
            output_dir: 输出目录路径
        """
        self.config_manager = config_manager
        self.output_dir = output_dir
        self.image_generator = ImageGenerator(config_manager=config_manager)
        self.template_generator = TemplateImageGenerator()
        self.composite_service = CompositeImageService(output_dir=output_dir)

        # 可用模型配置
        self.available_models = self._get_available_models()
        self.image_sizes = self._get_image_sizes()

    def generate_image(
        self,
        prompt: str,
        image_mode: str = "template",
        image_model: str = "jimeng_t2i_v40",
        template_style: str = "retro_chinese",
        image_size: str = "vertical",
        title: str = "无标题",
        scene: str = "",
        content_text: str = "",
        task_id: str = "unknown",
        timestamp: Optional[str] = None,
        task_index: int = 0,
        image_type: str = "content",
    ) -> Dict:
        """
        生成单张图片

        Args:
            prompt: 图片提示词
            image_mode: 图片模式 ('api' 或 'template')
            image_model: API模型名称
            template_style: 模板风格
            image_size: 图片尺寸 ('square', 'vertical', 'horizontal')
            title: 标题
            scene: 场景描述
            content_text: 内容文本
            task_id: 任务ID
            timestamp: 时间戳
            task_index: 图片索引
            image_type: 图片类型 ('cover' 或 'content')

        Returns:
            包含图片数据的字典

        Raises:
            ValidationError: 不支持的图片模式
            ImageGenerationError: 生成失败
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        Logger.info("生成图片", logger_name="image_service", task_id=task_id, image_mode=image_mode)

        if image_mode == "api":
            return self._generate_with_api(
                prompt=prompt,
                image_model=image_model,
                image_size=image_size,
                template_style=template_style,
                title=title,
                scene=scene,
                content_text=content_text,
                task_id=task_id,
                timestamp=timestamp,
                task_index=task_index,
                image_type=image_type,
            )
        elif image_mode == "template":
            return self._generate_with_template(
                prompt=prompt,
                template_style=template_style,
                image_size=image_size,
                title=title,
                scene=scene,
                content_text=content_text,
                task_id=task_id,
                timestamp=timestamp,
            )
        elif image_mode == "composite":
            return self._generate_with_composite(
                prompt=prompt,
                image_model=image_model,
                image_size=image_size,
                template_style=template_style,
                title=title,
                scene=scene,
                content_text=content_text,
                task_id=task_id,
                timestamp=timestamp,
                task_index=task_index,
                image_type=image_type,
            )
        else:
            raise ValidationError(
                message=f"不支持的配图模式: {image_mode}",
                details={"image_mode": image_mode, "allowed_modes": ["api", "template", "composite"]},
                suggestions=["请选择 'api'、'template' 或 'composite' 模式"],
            )

    def _generate_with_api(
        self,
        prompt: str,
        image_model: str,
        image_size: str,
        template_style: str,
        title: str,
        scene: str,
        content_text: str,
        task_id: str,
        timestamp: str,
        task_index: int,
        image_type: str,
    ) -> Dict:
        """
        使用API生成图片

        Args:
            各参数同 generate_image

        Returns:
            图片数据字典

        Raises:
            Exception: 生成失败
        """
        # 获取模型信息
        model_info = self.available_models.get(image_model, {})
        api_type = model_info.get("api_type", "wan_async")

        # 构建最终提示词
        final_prompt = self._build_final_prompt(
            prompt, template_style, title, scene, content_text, task_index, image_type, task_id
        )

        # 重试配置
        max_retries = 5
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                Logger.info(
                    f"{task_id}: 第 {attempt} 次尝试",
                    logger_name="image_service",
                    task_id=task_id,
                    attempt=attempt,
                    model=image_model,
                )

                # 设置模型
                self.image_generator.image_model = image_model

                # 获取尺寸配置
                size_config = self.image_sizes[image_size]
                size_str = f"{size_config['width']}*{size_config['height']}"

                # 调用API生成
                image_url = None
                if api_type == "jimeng_async":
                    # 即梦（火山引擎）异步生成
                    from src.image_providers.volcengine_provider import VolcengineImageProvider
                    provider = VolcengineImageProvider(
                        config_manager=self.config_manager,
                        logger=Logger,
                    )
                    image_url = provider.generate(final_prompt, size=size_str)
                elif api_type == "qwen_sync":
                    image_url = self.image_generator.generate_image_sync(final_prompt, size=size_str)
                else:
                    is_cover = image_type == "cover"
                    idx_val = self._extract_index(task_id)
                    image_url = self.image_generator.generate_image_async(final_prompt, idx_val, is_cover=is_cover)

                if image_url:
                    # 下载图片
                    result = self._download_and_save_image(image_url, "api", timestamp, task_id)
                    if result:
                        Logger.info(f"{task_id} 生成成功", logger_name="image_service", task_id=task_id)
                        return result
                    else:
                        last_error = "下载失败"
                else:
                    last_error = "API未返回URL"

            except Exception as e:
                last_error = str(e)
                Logger.warning(f"{task_id} 异常", logger_name="image_service", task_id=task_id, error=str(e))

            if attempt < max_retries:
                time.sleep(attempt * 2)

        # 所有重试失败
        Logger.error(
            f"{task_id} API生成失败，已重试{max_retries}次",
            logger_name="image_service",
            task_id=task_id,
            last_error=last_error,
        )
        raise ImageGenerationError(
            message=f"图片生成失败（已重试{max_retries}次）",
            details={"task_id": task_id, "model": image_model, "last_error": last_error, "retries": max_retries},
            suggestions=["请检查图片生成参数是否正确", "请稍后重试", "可以尝试切换到模板模式"],
        )

    def _generate_with_composite(
        self,
        prompt: str,
        image_model: str,
        image_size: str,
        template_style: str,
        title: str,
        scene: str,
        content_text: str,
        task_id: str,
        timestamp: str,
        task_index: int,
        image_type: str,
    ) -> Dict:
        """
        使用复合模式生成图片（AI背景 + 程序化文字）
        """
        # 第一步：使用 API 生成背景图
        # 注意：这里传入 image_mode='api' 但我们会特殊处理 prompt
        bg_result = self._generate_with_api(
            prompt=prompt,
            image_model=image_model,
            image_size=image_size,
            template_style=template_style,
            title=title,
            scene=scene,
            content_text=content_text,
            task_id=f"bg_{task_id}", # 区分背景图任务
            timestamp=timestamp,
            task_index=task_index,
            image_type=image_type,
        )
        
        # 第二步：使用 CompositeService 叠加文字
        filename = f"composite_{timestamp}_{task_id}.png"
        is_cover = image_type == "cover"
        
        composite_result = self.composite_service.composite_text(
            background_path=bg_result["path"],
            title=title if is_cover else "",
            content_text=content_text if not is_cover else "",
            output_filename=filename,
            is_cover=is_cover
        )
        
        # 组装最终结果
        return {
            "success": True,
            "data": composite_result["data"],
            "path": composite_result["path"],
            "url": f"/api/download/{filename}",
            "is_composite": True
        }

    def _generate_with_template(
        self,
        prompt: str,
        template_style: str,
        image_size: str,
        title: str,
        scene: str,
        content_text: str,
        task_id: str,
        timestamp: str,
    ) -> Dict:
        """
        使用模板生成图片

        Args:
            各参数同 generate_image

        Returns:
            图片数据字典

        Raises:
            Exception: 生成失败
        """
        try:
            # 获取尺寸配置
            size_config = self.image_sizes[image_size]
            width, height = size_config["width"], size_config["height"]

            # 生成文件路径
            temp_filename = f"template_{timestamp}_{task_id}.png"
            temp_path = self.output_dir / temp_filename

            # 构建内容文本
            safe_content = self._build_template_content(scene, prompt, content_text, title)

            # 生成图片
            self.template_generator.generate_image(
                text=safe_content,
                title=title,
                output_path=str(temp_path),
                size=(width, height),
                style=template_style if template_style != "info_chart" else "retro_chinese",
            )

            # 读取并转换为base64
            with open(temp_path, "rb") as f:
                content_bytes = f.read()

            b64 = base64.b64encode(content_bytes).decode("utf - 8")
            return {
                "data": f"data:image/png;base64,{b64}",
                "path": str(temp_path),
                "url": f"/api/download/{temp_filename}",
            }

        except Exception as e:
            Logger.exception(f"{task_id} 模板生成失败", logger_name="image_service", task_id=task_id)
            raise ImageGenerationError(
                message="模板生成失败",
                details={"task_id": task_id, "template_style": template_style, "error": str(e)},
                suggestions=["请检查模板风格是否正确", "请稍后重试", "可以尝试切换到其他模板风格"],
            )

    def _build_final_prompt(
        self,
        prompt: str,
        template_style: str,
        title: str,
        scene: str,
        content_text: str,
        task_index: int,
        image_type: str,
        task_id: str = "unknown",
    ) -> str:
        """构建最终的图片提示词"""
        is_composite = task_id.startswith("bg_")
        
        # 复合模式下：强制去除底图中的文字生成倾向
        if is_composite:
            # 清理原始提示词中可能引导文字生成的词汇
            text_keywords = ["with text", "saying", "written", "quotes", "typography", "characters", "文字", "包含文字", "书写"]
            clean_prompt = prompt
            for kw in text_keywords:
                import re
                clean_prompt = re.sub(rf"\b{kw}\b", "", clean_prompt, flags=re.IGNORECASE)
            
            # 注入强负面指令，确保底图纯净
            negative_prompt = "no text, no watermark, no characters, no alphabet, no chinese characters, blurry text, messy text"
            prompt = f"{clean_prompt}, pure background, atmospheric, (({negative_prompt})::1.5)"

        if template_style == "info_chart":
            chart_topic = title
            chart_desc = scene if scene else content_text[:100]
            if image_type == "cover":
                chart_desc = content_text[:100]
            
            if is_composite:
                return self._build_info_chart_prompt(
                    topic=chart_topic, description=chart_desc, scene=scene, index=task_index, skip_text=True
                )
            
            return self._build_info_chart_prompt(
                topic=chart_topic, description=chart_desc, scene=scene, index=task_index
            )
            
        style_keywords = {
            "retro_chinese": "Chinese retro style, vintage poster, 80s china aesthetic, muted colors, nostalgic atmosphere, flat illustration",
            "modern_minimal": "Modern minimalist style, clean lines, high key lighting, apple design style, less is more, white background, professional photography",
            "vintage_film": "Vintage film photography, Kodak Portra 400, grain, cinematic lighting, nostalgic, film burn, emotional atmosphere",
            "warm_memory": "Warm color palette, soft focus, golden hour, emotional, cozy atmosphere, sunlight, dreamy aesthetic",
            "ink_wash": "Chinese traditional ink wash painting, watercolor style, artistic, black and white with subtle colors, fluid lines, zen, masterpiece"
        }
        
        style_suffix = style_keywords.get(template_style, "")
        if style_suffix:
             return f"{prompt}, {style_suffix}"
             
        return prompt

    def _build_info_chart_prompt(self, topic: str, description: str = "", scene: str = "", index: int = 0, skip_text: bool = False) -> str:
        """
        构建信息图表风格的AI绘画提示词

        Args:
            topic: 主题名称
            description: 描述文字
            scene: 当前图片的具体场景
            index: 图片索引（0=封面）
            skip_text: 是否跳过文字生成指令（用于复合模式）

        Returns:
            信息图表提示词
        """
        # 根据 index 和 scene 构建差异化的核心视觉描述
        if index == 0:
            visual_focus = f"主题为【{topic}】的全景概览信息图表"
            visual_detail = ""
        elif scene:
            visual_focus = f"关于【{topic}】中【{scene}】的详细信息图表"
            visual_detail = f"聚焦展示「{scene}」的具体细节、背景故事和关键信息"
        else:
            visual_focus = f"关于【{topic}】的信息图表（第{index}张）"
            visual_detail = f"从第{index}个角度展示{topic}的独特视角"

        # 尝试检测需要生成的文字内容
        text_content = ""
        if not skip_text:
            import re
            # 匹配中文双引号或单引号内的内容
            matches = re.findall(r'[“"「](.+?)[”"」]', scene + description)
            if matches:
                # 取最长的一个匹配作为主要文字
                main_text = max(matches, key=len)
                if len(main_text) <= 10: # 限制文字长度，太长生成效果不好
                    text_content = f"""
核心文字元素：
画面中必须清晰包含文字"{main_text}"
文字风格：Traditional Chinese Calligraphy (中国传统书法)
载体建议：Plaque (牌匾) 或 Scroll (卷轴)
Clear text, bold strokes, high contrast, legible characters
"""
        
        base_prompt = f"""{visual_focus}

核心视觉：
{visual_detail}
中央为大型手绘风格主图插图
采用干净的墨线勾勒与柔和阴影
{text_content}

艺术风格：
中国平面插画风格
3D等轴测迷你示意图
结构化信息区块
数据标注配有引线

背景设计：
复古米色宣纸纹理
专业教育风格

主色调：
传统紫禁城红 (#8B0000)
皇家黄 (#FFD700)
大理石灰 (#B8860B)
米色背景 (#F5F0E6)

整体美学：
教育性、专业性
干净的图形设计
信息图表布局
4K高清分辨率

版式布局：
大型手绘主图位于中央
角落包含等轴测结构图
配有信息标注和数据展示
比例参数：--ar 3:4

详细描述：
"""

        if description:
            base_prompt += f"{description}\n"
        else:
            base_prompt += """精致的{topic}插图，展现其核心特征和结构细节。
包含整体轮廓、关键元素、细节展示等。
配以专业的标注和说明性文字框。
整体风格融合中国传统美学与现代信息设计。
"""

        base_prompt += """
固定风格关键词：
Chinese illustration, info graphic poster, educational poster, clean graphic design, professional layout, 4K HD, high resolution, traditional colors, vintage rice paper texture, isometric view, information annotations, data labels, professional presentation --ar 3:4"""

        return base_prompt

    def _build_template_content(self, scene: str, prompt: str, content_text: str, title: str) -> str:
        """
        构建模板内容文本

        Args:
            scene: 场景描述
            prompt: 提示词
            content_text: 内容文本
            title: 标题

        Returns:
            安全的内容文本
        """
        if scene:
            return f"{scene}：{prompt[:150]}" if prompt else scene
        elif prompt and prompt != content_text:
            return prompt[:200]
        else:
            return content_text[:200] if content_text else title

    def _download_and_save_image(self, image_url: str, prefix: str, timestamp: str, task_id: str) -> Optional[Dict]:
        """
        下载并保存图片

        Args:
            image_url: 图片URL
            prefix: 文件名前缀
            timestamp: 时间戳
            task_id: 任务ID

        Returns:
            图片数据字典或None
        """
        try:
            import requests
            import os
            import base64

            # 如果是本地路径（以 /static/ 开头），直接读取
            if image_url.startswith("/static/"):
                # 获取绝对路径
                # 假设运行目录是项目根目录，或者从 output_dir 推断
                # output_dir 通常是 .../static/images/generated 或 .../static/output
                # 简单起见，尝试构建完整路径
                project_root = os.getcwd() # 假设当前工作目录是项目根目录
                local_path = os.path.join(project_root, image_url.lstrip("/"))
                
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        content = f.read()
                    
                    b64 = base64.b64encode(content).decode("utf-8")
                    # 直接返回原路径（因为已经是本地可访问的了）
                    return {
                        "data": f"data:image/png;base64,{b64}",
                        "path": local_path,
                        "url": image_url
                    }
                else:
                     Logger.error(f"本地图片不存在: {local_path}", logger_name="image_service")
                     # 尝试回退到下载逻辑（虽然不太可能成功，但作为防御）

            # 正常下载逻辑
            response = requests.get(image_url, timeout=60)
            if response.status_code == 200:
                filename = f"{prefix}_{timestamp}_{task_id}.png"
                path = self.output_dir / filename
                with open(path, "wb") as f:
                    f.write(response.content)

                b64 = base64.b64encode(response.content).decode("utf-8")
                # 返回相对于 static 的 URL
                # 假设 output_dir 是 static/output
                # 这里需要根据实际配置调整，暂时假设标准结构
                relative_path = os.path.relpath(path, os.getcwd())
                if relative_path.startswith("static/"):
                    url = f"/{relative_path}"
                else:
                    url = f"/static/output/{filename}" # Fallback

                return {"data": f"data:image/png;base64,{b64}", "path": str(path), "url": url}
            else:
                Logger.error(f"下载图片失败: {response.status_code}", logger_name="image_service", status_code=response.status_code)
                return None
        except Exception as e:
            Logger.exception(f"下载/读取图片异常: {e}", logger_name="image_service")
            return None

    def _extract_index(self, task_id: str) -> int:
        """
        从任务ID中提取索引

        Args:
            task_id: 任务ID

        Returns:
            索引值
        """
        try:
            return int(task_id.split("_")[-1])
        except Exception:
            return 0

    def _get_available_models(self) -> Dict:
        """获取可用的图片生成模型列表"""
        return {
            "jimeng_t2i_v40": {
                "name": "即梦 Seedream 4.0",
                "version": "v4.0",
                "description": "火山引擎即梦4.0文生图，画面质感好，支持高分辨率",
                "release_date": "2026-01",
                "api_type": "jimeng_async",
            },
            "qwen-image-max": {
                "name": "千问 Qwen-Image Max",
                "version": "latest",
                "description": "最高质量版，图像真实感强，AI合成痕迹低",
                "release_date": "2025-12",
                "api_type": "qwen_sync",
            },
            "wan2.6-image": {
                "name": "万相 2.6",
                "version": "v2.6",
                "description": "支持图像编辑和图文混排输出",
                "release_date": "2026-02",
                "api_type": "wan_async",
            },
        }

    def _get_image_sizes(self) -> Dict:
        """获取小红书图片尺寸配置"""
        return {
            "square": {"width": 1080, "height": 1080, "name": "正方形 (1:1)", "ratio": "1:1"},
            "vertical": {"width": 1080, "height": 1440, "name": "竖版 (3:4)", "ratio": "3:4"},
            "horizontal": {"width": 1440, "height": 1080, "name": "横版 (4:3)", "ratio": "4:3"},
        }
