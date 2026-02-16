#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求模型使用示例

演示如何使用 Pydantic 验证模型进行请求参数验证
"""

from pydantic import ValidationError
from src.models.requests import (
    ContentGenerationRequest,
    ImageGenerationRequest,
    SearchRequest,
)


def example_content_generation():
    """内容生成请求示例"""
    print("=" * 60)
    print("内容生成请求示例")
    print("=" * 60)
    
    # 示例 1：有效的请求
    print("\n1. 有效的请求：")
    try:
        request = ContentGenerationRequest(
            input_text="记得小时候，老北京的胡同里总是充满了生活的气息。"
                      "清晨的叫卖声，傍晚的炊烟，还有那些熟悉的面孔。",
            count=3,
            style="retro_chinese",
            temperature=0.8,
        )
        print(f"✅ 验证通过")
        print(f"   输入文本：{request.input_text[:30]}...")
        print(f"   生成数量：{request.count}")
        print(f"   风格：{request.style}")
        print(f"   温度：{request.temperature}")
    except ValidationError as e:
        print(f"❌ 验证失败：{e}")
    
    # 示例 2：文本过短
    print("\n2. 文本过短（少于 10 个字符）：")
    try:
        request = ContentGenerationRequest(
            input_text="太短了",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 3：包含 XSS 攻击
    print("\n3. 包含 XSS 攻击代码：")
    try:
        request = ContentGenerationRequest(
            input_text="这是一段正常文本<script>alert('xss')</script>还有更多内容",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 4：包含敏感词
    print("\n4. 包含敏感词：")
    try:
        request = ContentGenerationRequest(
            input_text="这是一段包含暴力内容的文本，需要被过滤掉。",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 5：生成数量超出范围
    print("\n5. 生成数量超出范围（大于 10）：")
    try:
        request = ContentGenerationRequest(
            input_text="这是一段有效的输入文本内容，用于测试生成数量验证。",
            count=15,
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 6：无效的风格
    print("\n6. 无效的风格：")
    try:
        request = ContentGenerationRequest(
            input_text="这是一段有效的输入文本内容，用于测试风格验证。",
            style="invalid_style",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 7：高数量 + 高温度（模型级验证）
    print("\n7. 高数量 + 高温度（模型级验证）：")
    try:
        request = ContentGenerationRequest(
            input_text="这是一段有效的输入文本内容，用于测试模型级验证。",
            count=6,
            temperature=1.5,
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   错误：{error['msg']}")


def example_image_generation():
    """图片生成请求示例"""
    print("\n" + "=" * 60)
    print("图片生成请求示例")
    print("=" * 60)
    
    # 示例 1：有效的请求（模板模式）
    print("\n1. 有效的请求（模板模式）：")
    try:
        request = ImageGenerationRequest(
            prompt="老北京胡同，复古风格，温暖的阳光",
            image_mode="template",
            template_style="retro_chinese",
            image_size="vertical",
            title="老北京的记忆",
            timestamp="20260213_143000",
        )
        print(f"✅ 验证通过")
        print(f"   提示词：{request.prompt}")
        print(f"   模式：{request.image_mode}")
        print(f"   风格：{request.template_style}")
        print(f"   尺寸：{request.image_size}")
    except ValidationError as e:
        print(f"❌ 验证失败：{e}")
    
    # 示例 2：有效的请求（API 模式）
    print("\n2. 有效的请求（API 模式）：")
    try:
        request = ImageGenerationRequest(
            prompt="老北京胡同，复古风格",
            image_mode="api",
            image_model="wan2.2-t2i-flash",
            timestamp="20260213_143000",
        )
        print(f"✅ 验证通过")
        print(f"   提示词：{request.prompt}")
        print(f"   模式：{request.image_mode}")
        print(f"   模型：{request.image_model}")
    except ValidationError as e:
        print(f"❌ 验证失败：{e}")
    
    # 示例 3：使用字段别名
    print("\n3. 使用字段别名：")
    try:
        request = ImageGenerationRequest(
            prompt="测试提示词",
            timestamp="20260213_143000",
            content="这是内容文本",  # 使用别名 content
            index=5,                 # 使用别名 index
            type="cover",            # 使用别名 type
        )
        print(f"✅ 验证通过")
        print(f"   内容文本：{request.content_text}")
        print(f"   任务索引：{request.task_index}")
        print(f"   图片类型：{request.image_type}")
    except ValidationError as e:
        print(f"❌ 验证失败：{e}")
    
    # 示例 4：时间戳格式错误
    print("\n4. 时间戳格式错误：")
    try:
        request = ImageGenerationRequest(
            prompt="测试提示词",
            timestamp="2026-02-13 14:30:00",  # 错误格式
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 5：无效的日期
    print("\n5. 无效的日期（13月32日）：")
    try:
        request = ImageGenerationRequest(
            prompt="测试提示词",
            timestamp="20261332_143000",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 6：文本字段包含 XSS
    print("\n6. 文本字段包含 XSS：")
    try:
        request = ImageGenerationRequest(
            prompt="测试<script>alert('xss')</script>",
            timestamp="20260213_143000",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")


def example_search():
    """搜索请求示例"""
    print("\n" + "=" * 60)
    print("搜索请求示例")
    print("=" * 60)
    
    # 示例 1：有效的请求
    print("\n1. 有效的请求：")
    try:
        request = SearchRequest(
            page=1,
            page_size=50,
            keyword="老北京",
            start_time="2026-02-01T00:00:00",
            end_time="2026-02-13T23:59:59",
            sort_by="created_at",
            sort_order="desc",
        )
        print(f"✅ 验证通过")
        print(f"   页码：{request.page}")
        print(f"   每页数量：{request.page_size}")
        print(f"   关键词：{request.keyword}")
        print(f"   时间范围：{request.start_time} ~ {request.end_time}")
    except ValidationError as e:
        print(f"❌ 验证失败：{e}")
    
    # 示例 2：使用默认值
    print("\n2. 使用默认值：")
    try:
        request = SearchRequest()
        print(f"✅ 验证通过")
        print(f"   页码：{request.page}")
        print(f"   每页数量：{request.page_size}")
        print(f"   排序字段：{request.sort_by}")
        print(f"   排序顺序：{request.sort_order}")
    except ValidationError as e:
        print(f"❌ 验证失败：{e}")
    
    # 示例 3：SQL 注入尝试
    print("\n3. SQL 注入尝试：")
    try:
        request = SearchRequest(
            keyword="test' OR '1'='1",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 4：时间范围无效
    print("\n4. 时间范围无效（开始时间晚于结束时间）：")
    try:
        request = SearchRequest(
            start_time="2026-02-13T23:59:59",
            end_time="2026-02-01T00:00:00",
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   错误：{error['msg']}")
    
    # 示例 5：页码无效
    print("\n5. 页码无效（小于 1）：")
    try:
        request = SearchRequest(
            page=0,
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")
    
    # 示例 6：每页数量超出范围
    print("\n6. 每页数量超出范围（大于 200）：")
    try:
        request = SearchRequest(
            page_size=201,
        )
        print(f"✅ 验证通过")
    except ValidationError as e:
        print(f"❌ 验证失败：")
        for error in e.errors():
            print(f"   字段：{error['loc'][0]}")
            print(f"   错误：{error['msg']}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Pydantic 请求模型使用示例")
    print("=" * 60)
    
    # 运行示例
    example_content_generation()
    example_image_generation()
    example_search()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
