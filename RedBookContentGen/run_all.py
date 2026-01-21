#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键执行：内容生成 + 图片生成
顺序执行：1. 小红书文案与提示词生成  2. 根据提示词生成图片
"""

import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="一键执行：内容生成 + 图片生成，完成所有任务"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="配置文件路径 (默认: config.json)"
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="仅执行内容生成，跳过图片生成"
    )
    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🚀 一键执行：内容生成 + 图片生成")
    print("=" * 60 + "\n")

    # Step 1: 内容生成
    from redbook_content_generator import RedBookContentGenerator

    content_gen = RedBookContentGenerator(config_path=config_path)
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

    from image_generator import ImageGenerator

    image_gen = ImageGenerator(config_path=config_path)
    image_gen.generate_all_images(prompts_file)

    print("\n" + "=" * 60)
    print("✅ 全部任务完成：内容已生成，图片已保存到日期文件夹")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
