#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求数据模型
使用 Pydantic v2 定义所有 API 请求的验证模型
"""

import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class ContentGenerationRequest(BaseModel):
    """
    内容生成请求模型
    
    用于验证小红书内容生成的输入参数，包括：
    - 输入文本的长度和格式验证
    - 生成数量的范围限制
    - 内容安全检查（XSS、注入攻击等）
    - 敏感词过滤
    """
    
    model_config = ConfigDict(
        # 自动去除字符串首尾空白
        str_strip_whitespace=True,
        # 验证赋值
        validate_assignment=True,
        # 使用枚举值
        use_enum_values=True,
        # 额外字段处理：忽略
        extra='ignore',
    )
    
    input_text: str = Field(
        ...,
        min_length=2,
        max_length=5000,
        description="输入文本内容，用于生成小红书文案",
        examples=["记得小时候，老北京的胡同里总是充满了生活的气息..."],
    )
    
    count: int = Field(
        default=1,
        ge=1,
        le=10,
        description="生成内容的数量，范围 1-10",
        examples=[1, 3, 5],
    )
    
    style: Optional[str] = Field(
        default="retro_chinese",
        description="生成风格，可选值：retro_chinese（复古中国风）、modern_minimal（现代简约）等",
        examples=["retro_chinese", "modern_minimal"],
    )
    
    temperature: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="生成温度，控制创意程度，范围 0.0-2.0",
        examples=[0.7, 0.8, 1.0],
    )
    
    @field_validator('input_text')
    @classmethod
    def validate_input_text(cls, v: str) -> str:
        """
        验证输入文本
        
        检查项：
        1. 非空验证
        2. XSS 攻击模式检测
        3. 危险字符过滤
        4. 有效内容检查（必须包含中文或英文）
        
        Args:
            v: 输入文本
            
        Returns:
            验证通过的文本
            
        Raises:
            ValueError: 验证失败时抛出，包含具体的错误原因
        """
        if not v or not v.strip():
            raise ValueError("输入文本不能为空")
        
        # 检查危险的 XSS 攻击模式
        dangerous_patterns = [
            (r"<script[^>]*>.*?</script>", "包含 script 标签"),
            (r"<iframe[^>]*>.*?</iframe>", "包含 iframe 标签"),
            (r"javascript:", "包含 javascript 协议"),
            (r"onerror\s*=", "包含 onerror 事件处理器"),
            (r"onload\s*=", "包含 onload 事件处理器"),
            (r"onclick\s*=", "包含 onclick 事件处理器"),
            (r"<img[^>]+onerror", "包含危险的 img 标签"),
            (r"eval\s*\(", "包含 eval 函数调用"),
            (r"expression\s*\(", "包含 CSS expression"),
            (r"<embed[^>]*>", "包含 embed 标签"),
            (r"<object[^>]*>", "包含 object 标签"),
        ]
        
        for pattern, reason in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"输入包含非法内容：{reason}")
        
        # 检查是否包含有效的中文或英文内容
        if not re.search(r"[\u4e00-\u9fa5a-zA-Z]", v):
            raise ValueError("输入文本必须包含有效的中文或英文内容")
        
        # 检查敏感词（示例，实际应用中应该从配置文件或数据库加载）
        sensitive_words = ["暴力", "色情", "赌博", "毒品"]
        for word in sensitive_words:
            if word in v:
                raise ValueError(f"输入包含敏感词：{word}")
        
        # 检查文本质量：不能全是标点符号或空格
        text_without_punctuation = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', v)
        if len(text_without_punctuation) < 5:
            raise ValueError("输入文本有效内容过少，请提供更多实质性内容")
        
        return v
    
    @field_validator('style')
    @classmethod
    def validate_style(cls, v: Optional[str]) -> Optional[str]:
        """
        验证生成风格
        
        Args:
            v: 风格值
            
        Returns:
            验证通过的风格值
            
        Raises:
            ValueError: 风格不在允许列表中
        """
        if v is None:
            return v
        
        allowed_styles = [
            "retro_chinese",      # 复古中国风
            "modern_minimal",     # 现代简约
            "vintage_film",       # 怀旧胶片
            "warm_memory",        # 温暖记忆
            "ink_wash",           # 水墨风格
            "info_chart",         # 信息图表
        ]
        
        if v not in allowed_styles:
            raise ValueError(
                f"风格必须是以下之一：{', '.join(allowed_styles)}"
            )
        
        return v
    
    @model_validator(mode='after')
    def validate_model(self):
        """
        模型级别的验证
        
        在所有字段验证通过后执行，用于检查字段之间的关系
        
        Returns:
            验证通过的模型实例
            
        Raises:
            ValueError: 模型验证失败
        """
        # 如果生成数量大于 5，建议降低温度以保证质量
        if self.count > 5 and self.temperature and self.temperature > 1.0:
            raise ValueError(
                "批量生成时（数量 > 5），建议将温度设置为 1.0 或更低以保证质量"
            )
        
        return self


class ImageGenerationRequest(BaseModel):
    """
    图片生成请求模型
    
    用于验证图片生成的输入参数，包括：
    - 提示词的长度和格式验证
    - 图片模式、尺寸、风格的枚举验证
    - 时间戳格式验证
    - 文本字段的安全检查
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        extra='ignore',
        # 允许字段别名
        populate_by_name=True,
    )
    
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="图片生成提示词",
        examples=["老北京胡同，复古风格，温暖的阳光"],
    )
    
    image_mode: str = Field(
        default="template",
        description="图片生成模式：template（模板模式）或 api（API模式）",
        examples=["template", "api"],
    )
    
    image_model: str = Field(
        default="jimeng_t2i_v40",
        description="图片生成模型名称（API模式使用）",
        examples=["jimeng_t2i_v40", "wan2.6-image", "qwen-image-max"],
    )
    
    template_style: str = Field(
        default="retro_chinese",
        description="模板风格（模板模式使用）",
        examples=["retro_chinese", "modern_minimal", "vintage_film"],
    )
    
    image_size: str = Field(
        default="vertical",
        description="图片尺寸：vertical（竖版）、horizontal（横版）、square（方形）",
        examples=["vertical", "horizontal", "square"],
    )
    
    title: str = Field(
        default="无标题",
        max_length=100,
        description="图片标题",
        examples=["老北京的记忆", "胡同里的故事"],
    )
    
    scene: str = Field(
        default="",
        max_length=500,
        description="场景描述",
        examples=["夕阳下的胡同", "热闹的菜市场"],
    )
    
    content_text: str = Field(
        default="",
        max_length=1000,
        description="叠加在图片上的内容文本",
        alias="content",
        examples=["记得小时候..."],
    )
    
    task_id: str = Field(
        default="unknown",
        max_length=100,
        description="任务ID，用于追踪和管理",
        examples=["task_20260213_001"],
    )
    
    timestamp: str = Field(
        ...,
        description="时间戳，格式：YYYYMMDD_HHMMSS",
        examples=["20260213_143000"],
    )
    
    task_index: int = Field(
        default=0,
        ge=0,
        description="任务索引，用于批量生成时的排序",
        alias="index",
        examples=[0, 1, 2],
    )
    
    image_type: str = Field(
        default="content",
        description="图片类型：content（内容图）、cover（封面图）",
        alias="type",
        examples=["content", "cover"],
    )
    
    @field_validator('image_mode')
    @classmethod
    def validate_image_mode(cls, v: str) -> str:
        """验证图片模式"""
        allowed_modes = ["template", "api"]
        if v not in allowed_modes:
            raise ValueError(f"图片模式必须是 {', '.join(allowed_modes)} 之一")
        return v
    
    @field_validator('image_size')
    @classmethod
    def validate_image_size(cls, v: str) -> str:
        """验证图片尺寸"""
        allowed_sizes = ["vertical", "horizontal", "square"]
        if v not in allowed_sizes:
            raise ValueError(f"图片尺寸必须是 {', '.join(allowed_sizes)} 之一")
        return v
    
    @field_validator('template_style')
    @classmethod
    def validate_template_style(cls, v: str) -> str:
        """验证模板风格"""
        allowed_styles = [
            "retro_chinese",
            "modern_minimal",
            "vintage_film",
            "warm_memory",
            "ink_wash",
            "info_chart",
        ]
        if v not in allowed_styles:
            raise ValueError(f"模板风格必须是 {', '.join(allowed_styles)} 之一")
        return v
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """
        验证时间戳格式
        
        格式：YYYYMMDD_HHMMSS
        例如：20260213_143000
        """
        if not re.match(r'^\d{8}_\d{6}$', v):
            raise ValueError("时间戳格式必须为 YYYYMMDD_HHMMSS，例如：20260213_143000")
        
        # 验证日期和时间的有效性
        try:
            date_part = v.split('_')[0]
            time_part = v.split('_')[1]
            
            year = int(date_part[0:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            hour = int(time_part[0:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])
            
            # 创建 datetime 对象验证有效性
            datetime(year, month, day, hour, minute, second)
        except (ValueError, IndexError):
            raise ValueError("时间戳包含无效的日期或时间")
        
        return v
    
    @field_validator('image_type')
    @classmethod
    def validate_image_type(cls, v: str) -> str:
        """验证图片类型"""
        allowed_types = ["content", "cover"]
        if v not in allowed_types:
            raise ValueError(f"图片类型必须是 {', '.join(allowed_types)} 之一")
        return v
    
    @field_validator('prompt', 'title', 'scene', 'content_text')
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        """
        验证文本字段，防止 XSS 攻击
        
        Args:
            v: 文本值
            
        Returns:
            验证通过的文本
            
        Raises:
            ValueError: 包含危险内容
        """
        if not v:
            return v
        
        # 检查危险模式
        dangerous_patterns = [
            (r"<script[^>]*>", "script 标签"),
            (r"javascript:", "javascript 协议"),
            (r"onerror\s*=", "onerror 事件"),
            (r"onload\s*=", "onload 事件"),
            (r"<iframe", "iframe 标签"),
        ]
        
        for pattern, reason in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"文本包含非法内容：{reason}")
        
        return v
    
    @model_validator(mode='after')
    def validate_api_mode_requirements(self):
        """
        验证 API 模式的必需参数
        
        当使用 API 模式时，必须指定有效的图片模型
        """
        if self.image_mode == "api" and not self.image_model:
            raise ValueError("API 模式下必须指定图片模型")
        
        return self


class BatchContentGenerationRequest(BaseModel):
    """
    批量内容生成请求模型
    
    用于验证批量生成小红书内容的输入参数，包括：
    - 批量输入文本列表验证
    - 批量数量限制
    - 单个文本的长度和格式验证
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        extra='ignore',
    )
    
    inputs: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="批量输入文本列表，每个文本用于生成一组内容",
        examples=[
            ["记得小时候，老北京的胡同里...", "北京的四合院是传统建筑..."],
        ],
    )
    
    count: int = Field(
        default=1,
        ge=1,
        le=5,
        description="每个输入生成的内容数量，范围 1-5",
        examples=[1, 3],
    )
    
    style: Optional[str] = Field(
        default="retro_chinese",
        description="生成风格",
        examples=["retro_chinese", "modern_minimal"],
    )
    
    temperature: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="生成温度，范围 0.0-2.0",
        examples=[0.7, 0.8],
    )
    
    @field_validator('inputs')
    @classmethod
    def validate_inputs(cls, v: List[str]) -> List[str]:
        """
        验证批量输入文本列表
        
        检查项：
        1. 列表不能为空
        2. 每个文本长度在 10-5000 字符之间
        3. 每个文本必须包含有效内容
        4. 批量数量不超过 50 条
        
        Args:
            v: 输入文本列表
            
        Returns:
            验证通过的文本列表
            
        Raises:
            ValueError: 验证失败
        """
        if not v:
            raise ValueError("输入文本列表不能为空")
        
        if len(v) > 50:
            raise ValueError(f"批量输入数量不能超过 50 条（当前：{len(v)} 条）")
        
        # 验证每个文本
        validated_inputs = []
        for i, text in enumerate(v):
            if not text or not text.strip():
                raise ValueError(f"第 {i + 1} 条输入文本不能为空")
            
            text = text.strip()
            
            # 长度检查
            if len(text) < 10:
                raise ValueError(
                    f"第 {i + 1} 条输入文本长度不能少于 10 个字符（当前：{len(text)} 个字符）"
                )
            
            if len(text) > 5000:
                raise ValueError(
                    f"第 {i + 1} 条输入文本长度不能超过 5000 个字符（当前：{len(text)} 个字符）"
                )
            
            # 内容检查
            if not re.search(r"[\u4e00-\u9fa5a-zA-Z]", text):
                raise ValueError(f"第 {i + 1} 条输入文本必须包含有效的中文或英文内容")
            
            validated_inputs.append(text)
        
        return validated_inputs
    
    @model_validator(mode='after')
    def validate_batch_model(self):
        """
        批量模型级别的验证
        
        Returns:
            验证通过的模型实例
            
        Raises:
            ValueError: 模型验证失败
        """
        # 批量生成时建议降低温度
        total_tasks = len(self.inputs) * self.count
        if total_tasks > 10 and self.temperature and self.temperature > 1.0:
            raise ValueError(
                f"批量任务数量较多（{total_tasks} 个任务），建议将温度设置为 1.0 或更低以保证质量"
            )
        
        return self


class SearchRequest(BaseModel):
    """
    搜索请求模型
    
    用于验证搜索和查询的输入参数，包括：
    - 分页参数验证
    - 时间范围验证
    - 关键词安全检查
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore',
    )
    
    page: int = Field(
        default=1,
        ge=1,
        description="页码，从 1 开始",
        examples=[1, 2, 3],
    )
    
    page_size: int = Field(
        default=50,
        ge=1,
        le=200,
        description="每页数量，范围 1-200",
        examples=[10, 50, 100],
    )
    
    keyword: Optional[str] = Field(
        default=None,
        max_length=200,
        description="搜索关键词",
        examples=["老北京", "胡同"],
    )
    
    start_time: Optional[str] = Field(
        default=None,
        description="开始时间，ISO 8601 格式：YYYY-MM-DDTHH:MM:SS",
        examples=["2026-02-01T00:00:00"],
    )
    
    end_time: Optional[str] = Field(
        default=None,
        description="结束时间，ISO 8601 格式：YYYY-MM-DDTHH:MM:SS",
        examples=["2026-02-13T23:59:59"],
    )
    
    sort_by: Optional[str] = Field(
        default="created_at",
        description="排序字段",
        examples=["created_at", "updated_at", "title"],
    )
    
    sort_order: Optional[str] = Field(
        default="desc",
        description="排序顺序：asc（升序）或 desc（降序）",
        examples=["asc", "desc"],
    )
    
    @field_validator('keyword')
    @classmethod
    def validate_keyword(cls, v: Optional[str]) -> Optional[str]:
        """
        验证关键词，防止 SQL 注入和特殊字符攻击
        
        Args:
            v: 关键词
            
        Returns:
            验证通过的关键词
            
        Raises:
            ValueError: 包含危险字符
        """
        if not v:
            return v
        
        # 防止 SQL 注入和特殊字符
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "\\", "xp_", "sp_"]
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"关键词包含非法字符：{char}")
        
        return v
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """
        验证时间格式
        
        支持 ISO 8601 格式：YYYY-MM-DDTHH:MM:SS
        
        Args:
            v: 时间字符串
            
        Returns:
            验证通过的时间字符串
            
        Raises:
            ValueError: 时间格式无效
        """
        if not v:
            return v
        
        # 支持 ISO 8601 格式
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', v):
            raise ValueError("时间格式必须为 YYYY-MM-DDTHH:MM:SS，例如：2026-02-13T14:30:00")
        
        # 验证时间有效性
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("时间包含无效的日期或时间")
        
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: Optional[str]) -> Optional[str]:
        """验证排序顺序"""
        if v is None:
            return v
        
        allowed_orders = ["asc", "desc"]
        if v not in allowed_orders:
            raise ValueError(f"排序顺序必须是 {', '.join(allowed_orders)} 之一")
        
        return v
    
    @model_validator(mode='after')
    def validate_time_range(self):
        """
        验证时间范围
        
        确保开始时间不晚于结束时间
        
        Returns:
            验证通过的模型实例
            
        Raises:
            ValueError: 时间范围无效
        """
        if self.start_time and self.end_time:
            try:
                start = datetime.fromisoformat(self.start_time)
                end = datetime.fromisoformat(self.end_time)
                
                if start > end:
                    raise ValueError("开始时间不能晚于结束时间")
            except ValueError as e:
                if "开始时间" in str(e):
                    raise
                # 其他 ValueError 已经在字段验证中处理
        
        return self
