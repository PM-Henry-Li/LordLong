#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键执行：内容生成 + 图片生成
顺序执行：1. 小红书文案与提示词生成  2. 根据提示词生成图片
支持两种图片生成模式：API模式（通义万相AI）和模板模式（纯编程生成）
支持两种输入模式：file模式（从文件读取）和topic模式（从小红书搜索）
"""

import os
import sys
import argparse
import json


def main():
    parser = argparse.ArgumentParser(
        description="一键执行：内容生成 + 图片生成，完成所有任务"
    )
    parser.add_argument(
        "-c", "--config",
        default="config/config.json",
        help="配置文件路径 (默认: config/config.json)"
    )
    parser.add_argument(
        "--mode",
        choices=["file", "topic"],
        default="file",
        help="运行模式: file=从文件读取, topic=从主题搜索 (默认: file)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="主题关键词 (当mode=topic时必填)"
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="仅执行内容生成，跳过图片生成"
    )
    parser.add_argument(
        "--image-mode",
        choices=["api", "template"],
        help="图片生成模式: api=调用通义万相API, template=纯编程模板生成"
    )
    parser.add_argument(
        "--provider",
        choices=["aliyun", "volcengine"],
        help="图片生成服务提供商: aliyun=阿里云通义万相, volcengine=火山引擎即梦AI (仅在api模式下有效)"
    )
    parser.add_argument(
        "--style",
        choices=["retro_chinese", "modern_minimal", "vintage_film", "warm_memory", "ink_wash"],
        help="模板风格（仅在template模式下有效）"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="搜索最大结果数 (仅在topic模式下有效)"
    )
    parser.add_argument(
        "--min-likes",
        type=int,
        help="最小点赞数阈值 (仅在topic模式下有效)"
    )
    parser.add_argument(
        "--async-mode",
        action="store_true",
        help="使用异步并行生成图片（仅在api模式下有效，性能提升约60%%）"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="最大并发数（仅在async模式下有效，默认: 3）"
    )
    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    config = {}
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 验证topic模式的参数
    if args.mode == "topic":
        if not args.topic:
            print("❌ topic模式需要指定--topic参数")
            print("   示例: python run.py --mode topic --topic '老北京胡同'")
            sys.exit(1)

    image_mode = args.image_mode or config.get("image_generation_mode", "template")
    template_style = args.style or config.get("template_style", "retro_chinese")
    use_async = args.async_mode
    max_concurrent = args.max_concurrent

    print("\n" + "=" * 60)
    if args.mode == "topic":
        print(f"🚀 主题搜索模式: {args.topic}")
    else:
        print("🚀 文件输入模式")
    
    if image_mode == "template":
        print(f"   图片生成: 模板模式 ({template_style})")
    else:
        provider_name = args.provider or config.get("image_api_provider", "aliyun")
        provider_display = "阿里云通义万相" if provider_name == "aliyun" else "火山引擎即梦AI"
        if use_async:
            print(f"   图片生成: AI模式 - {provider_display}（异步并行，{max_concurrent}并发）")
        else:
            print(f"   图片生成: AI模式 - {provider_display}（串行）")
    print("=" * 60 + "\n")

    # Step 0: 如果是topic模式，先搜索和整理内容
    if args.mode == "topic":
        from src.xiaohongshu_scraper import XiaohongshuScraper
        from src.content_organizer import ContentOrganizer
        
        print("📡 第一步: 搜索小红书内容\n")
        
        with XiaohongshuScraper(config_path=config_path) as scraper:
            # 搜索笔记
            notes = scraper.search_by_topic(
                args.topic, 
                max_results=args.max_results
            )
            
            if not notes:
                print("❌ 未找到相关笔记，程序退出")
                sys.exit(1)
            
            # 筛选高质量笔记
            filtered_notes = scraper.filter_high_quality_notes(
                notes, 
                min_likes=args.min_likes
            )
            
            if not filtered_notes:
                print("⚠️  未找到符合点赞数要求的笔记，使用所有搜索结果")
                filtered_notes = notes
            
            # 获取详细内容(取前5条)
            print(f"\n📖 获取笔记详细内容...")
            detailed_notes = []
            for idx, note in enumerate(filtered_notes[:5], 1):
                note_url = note.get("url", "")
                if note_url:
                    print(f"   [{idx}/5] 获取: {note.get('title', '无标题')[:40]}...")
                    detailed = scraper.get_note_content(note_url)
                    if detailed:
                        detailed_notes.append(detailed)
                    else:
                        # 如果获取失败，使用基础信息
                        detailed_notes.append(note)
                else:
                    detailed_notes.append(note)
        
        print(f"\n📝 第二步: 整理内容\n")
        
        organizer = ContentOrganizer(config_path=config_path)
        organized_text = organizer.process_notes(
            detailed_notes,
            topic=args.topic,
            save_to_file=True,
            output_path="input/topic_content.txt"
        )
        
        print(f"\n✅ 内容搜索和整理完成\n")
        print("-" * 60 + "\n")
        print(f"📄 整理后的内容预览:\n")
        print(organized_text[:300] + "..." if len(organized_text) > 300 else organized_text)
        print("\n" + "-" * 60 + "\n")

    # Step 1: 内容生成
    step_label = "第三步" if args.mode == "topic" else "第一步"
    print(f"🎨 {step_label}: 生成小红书文案和图片提示词\n")
    from src.content_generator import RedBookContentGenerator
    from src.core.config_manager import ConfigManager

    # 使用 ConfigManager 加载配置
    config_manager = ConfigManager(config_path)
    
    # 如果命令行指定了 provider，覆盖配置文件中的设置
    if args.provider:
        config_manager.set("image_api_provider", args.provider)
    
    # 如果是topic模式，临时修改输入文件路径
    if args.mode == "topic":
        config_manager.set("input_file", "input/topic_content.txt")
    
    content_gen = RedBookContentGenerator(config_manager=config_manager)
    content_gen.run()

    if args.skip_images:
        print("\n⏭️  已跳过图片生成 (--skip-images)")
        print("=" * 60 + "\n")
        return

    # Step 2: 图片生成（使用刚生成的提示词文件）
    prompts_file = os.path.join(content_gen.image_dir, "image_prompts.txt")
    if not os.path.exists(prompts_file):
        print(f"\n⚠️  未找到提示词文件: {prompts_file}")
        print("   仅完成内容生成，未执行图片生成。")
        print("=" * 60 + "\n")
        return

    print("\n" + "-" * 60 + "\n")

    if image_mode == "template":
        print("🎨 使用模板模式生成图片（无需API Key）\n")
        from src.template_image_generator import TemplateImageGenerator

        template_gen = TemplateImageGenerator(config_path=config_path)
        template_gen.generate_all_from_prompts(prompts_file, style=template_style)
    else:
        if use_async:
            print(f"🎨 使用异步并行模式生成图片（{max_concurrent}并发）\n")
            import asyncio
            from src.async_image_service import AsyncImageService
            from src.image_generator import ImageGenerator
            
            # 使用 ImageGenerator 解析提示词文件
            image_gen = ImageGenerator(config_manager=config_manager)
            prompts, body_text = image_gen.parse_prompts_file(prompts_file)
            
            # 使用异步服务生成图片
            async_service = AsyncImageService(config_manager)
            
            async def generate_images_async():
                results = await async_service.generate_batch_images_async(
                    prompts=prompts,
                    max_concurrent=max_concurrent
                )
                return results, body_text
            
            # 运行异步任务
            results, body_text = asyncio.run(generate_images_async())
            
            # 处理结果：下载图片并添加文字叠加
            prompts_dir = os.path.dirname(prompts_file)
            
            # 分段正文内容
            content_segments = []
            if body_text:
                story_scenes = [p.get('scene', '') for p in prompts if not p.get('is_cover', False)]
                content_segments = image_gen.split_content_by_scenes(body_text, story_scenes)
            
            # 处理每张图片
            success_count = 0
            failed_count = 0
            
            for i, result in enumerate(results):
                prompt_data = prompts[i]
                is_cover = prompt_data.get('is_cover', False)
                index = prompt_data.get('index', i)
                
                if result.success:
                    # 下载图片
                    if is_cover:
                        image_filename = "cover.png"
                    else:
                        image_filename = f"image_{index:02d}.png"
                    
                    save_path = os.path.join(prompts_dir, image_filename)
                    
                    try:
                        image_gen.download_image(result.image_url, save_path)
                        
                        # 添加文字叠加
                        if is_cover:
                            title = prompt_data.get('title', '')
                            if title:
                                image_gen.add_text_overlay(save_path, title, is_cover=True, position="top")
                        else:
                            if content_segments and index > 0 and index <= len(content_segments):
                                content_segment = content_segments[index - 1]
                                if content_segment:
                                    image_gen.add_text_overlay(save_path, content_segment, is_cover=False, position="bottom")
                        
                        success_count += 1
                        print(f"✅ {'封面' if is_cover else f'图{index}'} 生成成功")
                    except Exception as e:
                        failed_count += 1
                        print(f"❌ {'封面' if is_cover else f'图{index}'} 处理失败: {e}")
                else:
                    failed_count += 1
                    print(f"❌ {'封面' if is_cover else f'图{index}'} 生成失败: {result.error}")
            
            print(f"\n📊 生成统计: 成功 {success_count}/{len(results)}, 失败 {failed_count}/{len(results)}")
        else:
            print("🎨 使用串行模式生成图片\n")
            from src.image_generator import ImageGenerator

            image_gen = ImageGenerator(config_manager=config_manager)
            image_gen.generate_all_images(prompts_file)

    print("\n" + "=" * 60)
    if image_mode == "template":
        print("✅ 全部任务完成：内容已生成，模板图片已保存到日期文件夹")
    else:
        print("✅ 全部任务完成：内容已生成，AI图片已保存到日期文件夹")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
