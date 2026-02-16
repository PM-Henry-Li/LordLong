
import unittest
from pathlib import Path
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.image_service import ImageService
from src.core.config_manager import ConfigManager

class TestPromptBuilder(unittest.TestCase):
    def setUp(self):
        # Patch dependencies manually
        self.patcher1 = unittest.mock.patch('src.services.image_service.ImageGenerator')
        self.patcher2 = unittest.mock.patch('src.services.image_service.TemplateImageGenerator')
        self.MockImageGen = self.patcher1.start()
        self.MockTemplateGen = self.patcher2.start()
        self.addCleanup(self.patcher1.stop)
        self.addCleanup(self.patcher2.stop)

        self.mock_config = MagicMock(spec=ConfigManager)
        
        def config_side_effect(key, default=None):
            return default

        self.mock_config.get.side_effect = config_side_effect
        self.output_dir = Path("/tmp")
        
        # Initialize service with mocked generators
        self.service = ImageService(self.mock_config, self.output_dir)

    def test_retro_chinese(self):
        prompt = self.service._build_final_prompt(
            prompt="A girl",
            template_style="retro_chinese",
            title="Title",
            scene="Scene",
            content_text="Content",
            task_index=0,
            image_type="content"
        )
        self.assertIn("Chinese retro style", prompt)
        self.assertIn("A girl", prompt)

    def test_modern_minimal(self):
        prompt = self.service._build_final_prompt(
            prompt="A car",
            template_style="modern_minimal",
            title="Title",
            scene="Scene",
            content_text="Content",
            task_index=0,
            image_type="content"
        )
        self.assertIn("Modern minimalist style", prompt)

    def test_info_chart(self):
        prompt = self.service._build_final_prompt(
            prompt="Data",
            template_style="info_chart",
            title="Chart Topic",
            scene="Scene",
            content_text="Content",
            task_index=0,
            image_type="content"
        )
        self.assertIn("全景概览信息图表", prompt)
        self.assertIn("Chart Topic", prompt)
        # Info chart ignores the original prompt in some cases or uses it differently
        # Verify it uses the specific info chart logic

    def test_unknown_style(self):
        # Should return raw prompt
        prompt = self.service._build_final_prompt(
            prompt="Raw prompt",
            template_style="unknown_style",
            title="Title",
            scene="Scene",
            content_text="Content",
            task_index=0,
            image_type="content"
        )
        self.assertEqual(prompt, "Raw prompt")

if __name__ == '__main__':
    unittest.main()
