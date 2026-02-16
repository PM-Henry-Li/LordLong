
import sys
import os
import json
import logging

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from image_providers.volcengine_provider import VolcengineImageProvider
from core.logger import Logger

# Setup logger to print to stdout
logging.basicConfig(level=logging.INFO)

class MockConfigManager:
    def __init__(self, config):
        self.config = config

    def get(self, key, default=None):
        if key == "volcengine.access_key_id":
            if "volcengine" in self.config:
                return self.config["volcengine"].get("access_key_id")
            return self.config.get("volcengine_access_key")
        elif key == "volcengine.secret_access_key":
            if "volcengine" in self.config:
                return self.config["volcengine"].get("secret_access_key")
            return self.config.get("volcengine_secret_key")
        elif key == "volcengine.endpoint":
            if "volcengine" in self.config:
                return self.config["volcengine"].get("endpoint", "https://visual.volcengineapi.com")
            return "https://visual.volcengineapi.com"
        elif key == "volcengine.timeout":
            if "volcengine" in self.config:
                return self.config["volcengine"].get("timeout", 180)
            return 180
        elif key == "volcengine.max_retries":
            if "volcengine" in self.config:
                return self.config["volcengine"].get("max_retries", 3)
            return 3
        return default

def main():
    try:
        # Load config
        config_path = os.path.join(os.getcwd(), "config", "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            
        mock_config = MockConfigManager(config)
        
        ak = mock_config.get("volcengine.access_key_id")
        
        if not ak:
            print("Missing AK/SK in config")
            return

        print(f"Testing Volcengine/Jimeng with AK: {ak[:4]}...")

        # Logger is a static class
        provider = VolcengineImageProvider(mock_config, Logger)
        
        # Test parameters
        prompt = "故宫雪景"
        
        print("Starting generation...")
        result = provider.generate(
            prompt=prompt,
            model="jimeng_t2i_v40",
            width=1024,
            height=1440, # Vertical
            num_images=1
        )
        
        print(f"Result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
