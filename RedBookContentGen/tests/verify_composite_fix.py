#!/usr/bin/env python3
"""验证修复效果：语义分段 + 提示词清洗"""
import sys
from pathlib import Path
root_dir = Path("/Users/henry/Documents/LordLong/RedBookContentGen")
sys.path.append(str(root_dir))

from src.services.content_service import ContentService
from src.services.image_service import ImageService
from src.core.config_manager import ConfigManager

config_manager = ConfigManager(root_dir / "config/config.json")
output_dir = root_dir / "data/test_output"
output_dir.mkdir(parents=True, exist_ok=True)

content_service = ContentService(config_manager, output_dir)
image_service = ImageService(config_manager, output_dir)

# 模拟文案
full_text = "嘿，大伙儿好！今天咱们一块儿探秘紫禁城里的一个小秘密——那就是清朝皇帝的大婚洞房。这间神秘的房间位于坤宁宫东端，一共有两间，不大但却极其讲究。房内挂着双喜字的红帐子，铺着龙凤呈祥的被褥，摆放着苹果、红枣、花生等吉祥物品。最特别的是，这里还保留着满族的传统——设有跪拜用的炕桌。"

raw_data = {
    "titles": ["故宫坤宁宫：皇帝的秘密婚房"],
    "content": full_text,
    "cover": {"title": "故宫坤宁宫：皇帝的秘密婚房", "scene": "宫殿入口", "prompt": "故宫坤宁宫外景"},
    "image_prompts": [
        {"scene": "坤宁宫东端的清代皇帝婚房内部", "prompt": "宫殿内部"},
        {"scene": "清代皇帝婚房内的龙凤喜床", "prompt": "龙凤喜床"},
        {"scene": "清代皇帝婚房门口", "prompt": "门口"},
        {"scene": "故宫牌匾特写", "prompt": "牌匾"},
    ]
}

tasks = content_service._build_image_tasks(raw_data, "故宫", 5)

print("=" * 60)
print("📋 图片任务列表 (含分段文案)")
print("=" * 60)
for task in tasks:
    ct = task.get('content_text', '(无)')
    print(f"\n🖼  [{task['type'].upper()}] {task['title']} | {task['scene']}")
    print(f"   content_text: {ct[:80]}{'...' if len(ct)>80 else ''}")
    if task['type'] == 'cover':
        assert ct == "", f"❌ 封面的 content_text 应为空！实际: '{ct}'"
        print("   ✅ 封面无正文 (防止重叠)")
    else:
        assert len(ct) > 0, f"❌ 插图 {task['index']} 的 content_text 不应为空！"

# 检查各插图文案是否不同
content_texts = [t['content_text'] for t in tasks if t['type'] == 'content']
unique_texts = set(content_texts)
print(f"\n📊 插图文案唯一性检查: {len(content_texts)} 张插图, {len(unique_texts)} 个不同文案")
assert len(unique_texts) > 1, "❌ 插图文案全部一样，分段失败！"
print("   ✅ 文案已成功分段")

# 检查提示词清洗
print("\n" + "=" * 60)
print("🧹 提示词清洗验证")
print("=" * 60)
dirty_prompt = "a person with text saying hello, vintage poster with chinese characters"
clean = image_service._build_final_prompt(
    prompt=dirty_prompt, template_style="retro_chinese",
    title="测试", scene="", content_text="", task_index=1,
    image_type="content", task_id="bg_test"
)
print(f"   原始: {dirty_prompt}")
print(f"   清洗: {clean[:100]}...")
assert "no text" in clean, "❌ 未注入负面指令"
print("   ✅ 负面指令注入成功")

print("\n✅ 全部验证通过！")
