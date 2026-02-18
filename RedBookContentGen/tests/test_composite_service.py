import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.services.composite_service import CompositeImageService
from PIL import Image

def test_composite():
    output_dir = Path("output/test_composite")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    service = CompositeImageService(output_dir=output_dir)
    
    # Create a dummy background
    bg = Image.new("RGB", (1080, 1440), (200, 200, 200))
    bg_path = output_dir / "dummy_bg.png"
    bg.save(bg_path)
    
    print(f"Generating cover style...")
    result_cover = service.composite_text(
        background_path=str(bg_path),
        title="故宫游玩攻略：如何避雷？",
        content_text="",
        output_filename="test_cover.png",
        is_cover=True
    )
    print(f"Cover generated: {result_cover['path']}")
    
    print(f"Generating story style...")
    result_story = service.composite_text(
        background_path=str(bg_path),
        title="",
        content_text="这里的城墙非常有历史感，建议下午4点以后来拍照，光线非常柔和。",
        output_filename="test_story.png",
        is_cover=False
    )
    print(f"Story generated: {result_story['path']}")

if __name__ == "__main__":
    test_composite()
