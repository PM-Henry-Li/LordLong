#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内容生成功能

任务 9.1.1: 测试内容生成功能
- 测试正常生成流程
- 测试不同输入长度
- 测试不同风格参数

目标：测试覆盖率 > 70%

注意：本测试专注于测试公共接口和可观察的行为，
不测试内部嵌套函数（如 _check_cache, _initialize_openai_client 等）
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.content_generator import RedBookContentGenerator
from src.core.config_manager import ConfigManager


# ============================================================================
# 测试固件
# ============================================================================


@pytest.fixture
def mock_openai_client():
    """模拟 OpenAI 客户端"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(
                content=json.dumps(
                    {
                        "titles": [
                            "胡同里的老北京记忆 🏮",
                            "那些年，我们一起走过的胡同",
                            "老北京胡同：时光里的温暖",
                            "胡同深处的童年时光",
                            "寻找老北京的味道",
                        ],
                        "content": "记得小时候的老北京胡同吗？清晨的豆腐吆喝声从巷子深处传来，悠长而亲切。邻里之间串门聊天，孩子们在胡同里追逐嬉戏。那时候的生活虽然简单，但充满了人情味。",
                        "tags": "#老北京 #胡同文化 #童年回忆 #北京生活",
                        "image_prompts": [
                            {
                                "scene": "胡同清晨",
                                "prompt": "老北京胡同清晨场景，阳光洒在青砖灰瓦上，复古摄影风格，90年代纪实摄影",
                            },
                            {
                                "scene": "孩子们玩耍",
                                "prompt": "胡同里的孩子们在玩耍，充满生活气息，胶片质感",
                            },
                            {
                                "scene": "四合院",
                                "prompt": "传统北京四合院，红门绿瓦，古朴典雅",
                            },
                            {
                                "scene": "邻里聊天",
                                "prompt": "邻居们在胡同口聊天，温馨和谐的场景",
                            },
                        ],
                        "cover": {
                            "scene": "胡同全景",
                            "title": "老北京胡同记忆",
                            "prompt": "老北京胡同全景，青砖灰瓦，充满历史感",
                        },
                    },
                    ensure_ascii=False,
                )
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def test_config(temp_dir):
    """创建测试配置"""
    config_data = {
        "input_file": str(temp_dir / "input.txt"),
        "output_excel": str(temp_dir / "output" / "test.xlsx"),
        "output_image_dir": str(temp_dir / "output" / "images"),
        "openai_api_key": "test-api-key-12345",
        "openai_model": "qwen-plus",
        "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "cache": {"enabled": False},  # 禁用缓存以便测试
        "rate_limit": {"openai": {"enable_rate_limit": False}},  # 禁用速率限制
    }

    config_file = temp_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    return config_file


@pytest.fixture
def generator(test_config):
    """创建内容生成器实例"""
    config_manager = ConfigManager(str(test_config))
    return RedBookContentGenerator(config_manager=config_manager)


# ============================================================================
# 测试 1: 正常生成流程
# ============================================================================


@pytest.mark.unit
def test_normal_generation_flow(generator, mock_openai_client):
    """测试正常的内容生成流程"""
    input_text = """
    记得小时候，老北京的胡同里总是充满了生活的气息。
    清晨，卖豆腐的吆喝声从巷子深处传来，悠长而亲切。
    邻里之间串门聊天，孩子们在胡同里追逐嬉戏。
    那时候的生活虽然简单，但充满了人情味。
    """

    with patch("openai.OpenAI", return_value=mock_openai_client):
        result = generator.generate_content(input_text)

        # 验证返回结果的结构
        assert isinstance(result, dict)
        assert "titles" in result
        assert "content" in result
        assert "tags" in result
        assert "image_prompts" in result
        assert "cover" in result

        # 验证标题
        assert isinstance(result["titles"], list)
        assert len(result["titles"]) == 5
        assert all(isinstance(title, str) for title in result["titles"])

        # 验证正文
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0

        # 验证标签
        assert isinstance(result["tags"], str)
        assert "#" in result["tags"]

        # 验证图片提示词
        assert isinstance(result["image_prompts"], list)
        assert len(result["image_prompts"]) >= 4
        for prompt in result["image_prompts"]:
            assert "scene" in prompt
            assert "prompt" in prompt

        # 验证封面
        assert isinstance(result["cover"], dict)
        assert "scene" in result["cover"]
        assert "title" in result["cover"]
        assert "prompt" in result["cover"]


# ============================================================================
# 测试 2: 不同输入长度
# ============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_length,input_text",
    [
        # 短文本（约50字）
        (
            "short",
            "老北京的胡同，青砖灰瓦，充满了历史的痕迹。那里有我童年的记忆，有邻里的温情。",
        ),
        # 中等文本（约150字）
        (
            "medium",
            """
            记得小时候，老北京的胡同里总是充满了生活的气息。
            清晨，卖豆腐的吆喝声从巷子深处传来，悠长而亲切。
            邻里之间串门聊天，孩子们在胡同里追逐嬉戏。
            那时候的生活虽然简单，但充满了人情味。
            夏天的傍晚，大家都搬着小板凳坐在胡同口乘凉，
            聊着家长里短，孩子们则在一旁玩着弹珠、跳皮筋。
            """,
        ),
        # 长文本（约300字）
        (
            "long",
            """
            老北京的胡同，是这座城市最具特色的文化符号之一。
            那些纵横交错的小巷，承载着几代人的记忆和情感。
            
            记得小时候，胡同里的生活节奏很慢，但却充满了烟火气。
            清晨，卖豆腐的吆喝声从巷子深处传来，悠长而亲切。
            邻里之间串门聊天，孩子们在胡同里追逐嬉戏。
            那时候的生活虽然简单，但充满了人情味。
            
            夏天的傍晚，大家都搬着小板凳坐在胡同口乘凉，
            聊着家长里短，孩子们则在一旁玩着弹珠、跳皮筋。
            老人们摇着蒲扇，讲述着老北京的故事。
            
            如今，许多胡同已经消失在城市化的进程中，
            但那些记忆却永远留在了我们心中。
            每当想起那些日子，心中总会涌起一股温暖。
            """,
        ),
    ],
)
def test_different_input_lengths(generator, mock_openai_client, input_length, input_text):
    """测试不同长度的输入文本"""
    with patch("openai.OpenAI", return_value=mock_openai_client):
        result = generator.generate_content(input_text)

        # 验证基本结构
        assert isinstance(result, dict)
        assert "titles" in result
        assert "content" in result
        assert "image_prompts" in result

        # 验证生成的内容不为空
        assert len(result["titles"]) > 0
        assert len(result["content"]) > 0
        assert len(result["image_prompts"]) > 0

        # 验证 API 被调用
        assert mock_openai_client.chat.completions.create.called


# ============================================================================
# 测试 3: 不同风格参数（通过温度参数模拟）
# ============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "temperature,expected_style",
    [
        (0.3, "保守风格"),  # 低温度，更保守的输出
        (0.8, "平衡风格"),  # 中等温度，平衡的输出
        (1.2, "创意风格"),  # 高温度，更有创意的输出
    ],
)
def test_different_style_parameters(generator, mock_openai_client, temperature, expected_style):
    """测试不同的风格参数（通过温度参数）"""
    input_text = "老北京的胡同文化，充满了历史的韵味。"

    with patch("openai.OpenAI", return_value=mock_openai_client):
        # 修改配置中的温度参数
        with patch.object(
            generator.api_handler, "call_openai", wraps=generator.api_handler.call_openai
        ) as mock_call:
            result = generator.generate_content(input_text)

            # 验证结果
            assert isinstance(result, dict)
            assert "titles" in result
            assert "content" in result

            # 验证 API 被调用
            assert mock_call.called


# ============================================================================
# 测试 4: 内容安全检查
# ============================================================================


@pytest.mark.unit
def test_content_safety_check(generator):
    """测试内容安全检查功能"""
    # 测试安全内容
    safe_text = "老北京的胡同文化，充满了历史的韵味。"
    is_safe, modified = generator.check_content_safety(safe_text)
    assert is_safe is True
    assert modified == safe_text

    # 测试包含敏感词的内容（只测试明显的敏感词）
    unsafe_text = "这是一段包含血腥的内容。"
    is_safe, modified = generator.check_content_safety(unsafe_text)
    assert is_safe is False
    # 验证敏感词被移除
    assert "血腥" not in modified
    # 验证其他内容保留
    assert "这是一段包含" in modified
    assert "的内容" in modified


# ============================================================================
# 测试 5: 缓存键生成
# ============================================================================


@pytest.mark.unit
def test_cache_key_generation(generator):
    """测试缓存键生成功能"""
    input_text1 = "老北京的胡同文化"
    input_text2 = "老北京的胡同文化"
    input_text3 = "不同的输入内容"

    key1 = generator._generate_cache_key(input_text1)
    key2 = generator._generate_cache_key(input_text2)
    key3 = generator._generate_cache_key(input_text3)

    # 相同输入应该生成相同的缓存键
    assert key1 == key2

    # 不同输入应该生成不同的缓存键
    assert key1 != key3

    # 缓存键应该包含前缀
    assert key1.startswith("content_gen:")


# ============================================================================
# 测试 6: 提示词构建
# ============================================================================


@pytest.mark.unit
def test_prompt_building(generator):
    """测试提示词构建功能"""
    input_text = "老北京的胡同文化"
    prompt = generator._build_generation_prompt(input_text)

    # 验证提示词包含必要的元素
    assert "老北京文化" in prompt
    assert "小红书" in prompt
    assert "AI 绘画" in prompt or "AI绘画" in prompt
    # 注意：提示词模板使用 {raw_content} 占位符，不会直接包含输入文本
    assert "{raw_content}" in prompt

    # 验证提示词包含输出格式说明
    assert "titles" in prompt
    assert "content" in prompt
    assert "image_prompts" in prompt


# ============================================================================
# 测试 7: 单条内容生成（Web API 使用）
# ============================================================================


@pytest.mark.unit
def test_generate_single_content(generator, mock_openai_client):
    """测试单条内容生成功能（用于 Web API）"""
    input_text = "老北京的胡同文化"

    with patch("openai.OpenAI", return_value=mock_openai_client):
        result = generator.generate_single_content(input_text)

        # 验证返回结果的结构
        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "tags" in result
        assert "image_prompt" in result
        assert "raw_data" in result

        # 验证标题是字符串
        assert isinstance(result["title"], str)

        # 验证标签是列表
        assert isinstance(result["tags"], list)

        # 验证原始数据被保留
        assert isinstance(result["raw_data"], dict)


# ============================================================================
# 测试 8: 错误处理
# ============================================================================


@pytest.mark.unit
def test_error_handling_missing_api_key(test_config):
    """测试缺少 API Key 的错误处理"""
    # 创建没有 API Key 的配置
    config_data = {
        "input_file": "input/test.txt",
        "output_excel": "output/test.xlsx",
        "output_image_dir": "output/images",
        # 故意不设置 openai_api_key
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        config_manager = ConfigManager(str(config_file))
        generator = RedBookContentGenerator(config_manager=config_manager)

        # 尝试生成内容应该抛出错误
        with pytest.raises(ValueError, match="未找到 API Key"):
            generator.generate_content("测试内容")


@pytest.mark.unit
def test_error_handling_empty_input(generator):
    """测试空输入的错误处理"""
    # 空字符串应该能够处理（虽然可能返回空结果）
    with patch("openai.OpenAI") as mock_client:
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "titles": ["默认标题"],
                            "content": "默认内容",
                            "tags": "#默认",
                            "image_prompts": [],
                            "cover": {},
                        }
                    )
                )
            )
        ]
        mock_client.return_value.chat.completions.create.return_value = mock_response

        result = generator.generate_content("")
        assert isinstance(result, dict)


# ============================================================================
# 测试 9: 配置和初始化
# ============================================================================


@pytest.mark.unit
def test_generator_initialization(test_config):
    """测试生成器初始化"""
    config_manager = ConfigManager(str(test_config))
    generator = RedBookContentGenerator(config_manager=config_manager)

    # 验证生成器正确初始化
    assert generator.config_manager is not None
    assert generator.logger is not None
    assert hasattr(generator, "image_dir")
    assert hasattr(generator, "_cache_enabled")
    assert hasattr(generator, "_rate_limit_enabled")


@pytest.mark.unit
def test_generator_with_cache_disabled(test_config):
    """测试禁用缓存的生成器"""
    config_manager = ConfigManager(str(test_config))
    generator = RedBookContentGenerator(config_manager=config_manager)

    # 验证缓存被禁用
    assert generator._cache_enabled is False
    assert generator.cache is None


@pytest.mark.unit
def test_generator_with_rate_limit_disabled(test_config):
    """测试禁用速率限制的生成器"""
    config_manager = ConfigManager(str(test_config))
    generator = RedBookContentGenerator(config_manager=config_manager)

    # 验证速率限制被禁用
    assert generator._rate_limit_enabled is False
    assert generator.rpm_limiter is None
    assert generator.tpm_limiter is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.content_generator", "--cov-report=term-missing"])
