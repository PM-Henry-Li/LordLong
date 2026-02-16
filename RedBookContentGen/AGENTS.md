# AGENTS.md

## Communication Language

- All responses, explanations, and comments to the user MUST be in **Chinese (Mandarin/中文)**
- This includes code review feedback, commit messages, PR descriptions, and conversational replies
- Code identifiers (variable names, function names, etc.) remain in English per existing conventions

## Project Overview

RedBookContentGen is a Python CLI tool that generates Xiaohongshu (Little Red Book) social media
content about Old Beijing culture. It reads Chinese text, uses an OpenAI-compatible LLM (Alibaba
Cloud DashScope/Qwen) to produce social media copy and image prompts, then calls the Tongyi
Wanxiang text-to-image API to generate images with text overlay.

## Project Structure

```
RedBookContentGen/
├── run.py                        # Main entry point (orchestrates both phases)
├── requirements.txt              # Python deps: openai, openpyxl, requests, Pillow
├── config/
│   ├── config.json               # Runtime config with API keys (GITIGNORED - never commit)
│   └── config.example.json       # Template config
├── src/
│   ├── __init__.py               # Package init
│   ├── content_generator.py      # RedBookContentGenerator class (~655 lines)
│   ├── image_generator.py        # ImageGenerator class (~1537 lines)
│   ├── image_providers/          # Image generation service providers
│   │   ├── __init__.py           # Package init
│   │   ├── base.py               # BaseImageProvider abstract class
│   │   ├── aliyun_provider.py    # AliyunImageProvider (Aliyun Tongyi Wanxiang)
│   │   └── volcengine_provider.py # VolcengineImageProvider (Volcengine Jimeng AI)
│   ├── volcengine/               # Volcengine utilities
│   │   ├── __init__.py           # Package init
│   │   └── signature.py          # VolcengineSignatureV4 (AWS Signature V4)
│   └── core/
│       ├── __init__.py           # Core module init
│       └── config_manager.py     # ConfigManager class (unified config management)
├── tests/
│   ├── test_ai_rewrite.py        # Tests AI text rewriting
│   ├── test_text_overlay.py      # Tests text wrapping, truncation, content safety
│   ├── verify_fix.py             # Tests text cleaning/sanitization
│   ├── test_volcengine_signature.py # Tests Volcengine signature algorithm
│   └── unit/                     # Unit tests
│       ├── test_config_manager.py
│       ├── test_rate_limit_config.py
│       ├── test_content_generator_integration.py
│       ├── test_config_manager_volcengine_properties.py
│       ├── test_aliyun_provider.py
│       ├── test_volcengine_provider.py
│       ├── test_volcengine_provider_properties.py
│       └── test_image_generator_integration.py
├── docs/                         # Documentation
│   ├── CONFIG.md                 # Complete configuration documentation
│   ├── CONFIG_MIGRATION_GUIDE.md # Migration guide for new config system
│   └── VOLCENGINE.md             # Volcengine Jimeng AI integration guide
├── examples/                     # Usage examples
│   ├── config_usage_example.py
│   └── config_hot_reload_example.py
├── input/
│   └── input_content.txt         # Source text (gitignored)
└── output/                       # Generated output (gitignored)
    ├── redbook_content.xlsx
    └── images/YYYYMMDD/
```

Core classes:
- `RedBookContentGenerator` (content_generator.py) - Content generation
- `ImageGenerator` (image_generator.py) - Image generation coordinator
- `BaseImageProvider` (image_providers/base.py) - Abstract base class for image providers
- `AliyunImageProvider` (image_providers/aliyun_provider.py) - Aliyun Tongyi Wanxiang provider
- `VolcengineImageProvider` (image_providers/volcengine_provider.py) - Volcengine Jimeng AI provider
- `VolcengineSignatureV4` (volcengine/signature.py) - AWS Signature V4 implementation
- `ConfigManager` (core/config_manager.py) - Unified configuration management

Each module can run standalone or be orchestrated by `run.py`.

## Build & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (content generation + image generation)
python run.py

# Run with a custom config
python run.py --config path/to/config.json

# Run content generation only (skip images)
python run.py --skip-images

# Run with template mode (no API key needed, pure programming)
python run.py --image-mode template

# Run with API mode (default, requires API key)
python run.py --image-mode api

# Run with Volcengine Jimeng AI (requires Volcengine API key)
python run.py --image-mode api --provider volcengine

# Run with Aliyun Tongyi Wanxiang (default)
python run.py --image-mode api --provider aliyun

# Specify template style (retro_chinese, modern_minimal, vintage_film, warm_memory, ink_wash)
python run.py --image-mode template --style warm_memory

# Run individual modules standalone
python -m src.content_generator
python -m src.image_generator

# Run template image generator standalone
python -m src.template_image_generator -p output/images/YYYYMMDD/image_prompts.txt -s retro_chinese
```

## Image Generation Modes

### Template Mode (推荐 / 默认)
- **优点**: 完全离线，无需 API Key，速度极快（秒级生成），零成本
- **缺点**: 设计模板风格，非 AI 生成的写实照片
- **可用风格**: `retro_chinese`(复古中国风), `modern_minimal`(现代简约), `vintage_film`(怀旧胶片), `warm_memory`(温暖记忆), `ink_wash`(水墨风格)
- **命令**: `python run.py --image-mode template`

### API Mode (需要 API Key)
- **优点**: AI 生成逼真的摄影风格图片
- **缺点**: 需要阿里云 DashScope API Key，消耗配额，速度较慢（每张约 30 秒-2 分钟）
- **命令**: `python run.py --image-mode api`

## Test Commands

Tests are standalone scripts using manual `sys.path` manipulation and print-based pass/fail output.
Unit tests use the `unittest` framework.

```bash
# Run all tests (run each individually)
python tests/test_text_overlay.py
python tests/test_ai_rewrite.py
python tests/verify_fix.py

# Run Volcengine signature tests
python tests/test_volcengine_signature.py

# Run unit tests
python tests/unit/test_config_manager.py
python tests/unit/test_aliyun_provider.py
python tests/unit/test_volcengine_provider.py
python tests/unit/test_volcengine_provider_properties.py
python tests/unit/test_image_generator_integration.py

# Run a single test file
python tests/test_text_overlay.py

# Run a specific test function (not supported - tests use if __name__ blocks)
```

Note: `test_ai_rewrite.py` requires a valid API key in `config/config.json` to run.
The other test files also import from `src/` and may need the config file present.

## Linting & Formatting

No linting or formatting tools are configured (no flake8, ruff, mypy, black, isort,
pylint, or pre-commit hooks). No CI/CD pipeline exists. If adding tooling, follow PEP 8
conventions already present in the codebase.

## Code Style Guidelines

### Language & Encoding

- All source files start with `#!/usr/bin/env python3` and `# -*- coding: utf-8 -*-`
- Docstrings, comments, and user-facing print messages are written in **Chinese (Mandarin)**
- Keep all new comments and docstrings in Chinese to maintain consistency

### Imports

- Standard library first, third-party second, local third (loosely follows PEP 8 ordering)
- Imports are NOT alphabetically sorted within groups and groups are not blank-line separated
- `typing` imports (`List`, `Dict`, `Tuple`, `Optional`) are used but mixed with third-party
- Conditional imports with `try/except ImportError` for optional deps (e.g., PIL)
- Local imports in `__init__.py` use relative style: `from .content_generator import ...`
- Entry points (`run.py`) use deferred imports inside `main()`
- Tests use `sys.path.insert(0, ...)` for path manipulation

### Naming Conventions

| Element         | Convention    | Examples                                          |
|-----------------|---------------|---------------------------------------------------|
| Files           | snake_case    | `content_generator.py`, `test_text_overlay.py`    |
| Classes         | PascalCase    | `RedBookContentGenerator`, `ImageGenerator`        |
| Methods/funcs   | snake_case    | `generate_content()`, `read_input_file()`          |
| Private methods | _snake_case   | `_load_config()`, `_build_generation_prompt()`     |
| Variables       | snake_case    | `config_path`, `retry_count`, `font_size`          |
| Module flags    | UPPER_SNAKE   | `HAS_PIL`                                          |

### Type Hints

- Applied to method signatures (parameters and return types), not local variables
- Use `typing` module types: `List`, `Dict`, `Tuple`, `Optional`
- Mixed usage of `dict` (lowercase) and `Dict` (typing) exists; prefer `Dict` for consistency
- No mypy or pyright configured; type hints are documentation-only
- Some parameters (especially PIL objects) are left untyped

### String Formatting

- **f-strings exclusively** - no `%` formatting or `.format()` calls
- Single quotes for most strings; double quotes for JSON-like dicts and API parameters
- No enforced line length; lines commonly reach 100-140+ characters

### Code Formatting

- 4-space indentation (no tabs)
- Two blank lines between top-level definitions, one between class methods (PEP 8)
- No trailing commas enforced
- No semicolons

### Docstrings

- Google-style with `Args:` and `Returns:` sections, written in Chinese
- Module-level docstrings on every file (triple-quoted, Chinese)
- Class docstrings are short single-line Chinese descriptions

### Error Handling

- Primary pattern: `try/except Exception as e:` with `print(f"error msg")` then `raise`
- Retry loops for API calls (typically 3 attempts) with conditional re-raise on final attempt
- Explicit `FileNotFoundError` and `ValueError` raises with Chinese emoji-prefixed messages
- Graceful degradation: missing PIL falls back to no text overlay; failed AI rewrite returns original
- Avoid bare `except:` clauses (some exist in font-loading code but should not be replicated)

### Logging

- Uses `print()` with emoji prefixes instead of the `logging` module
- Emoji conventions: `checkmark` success, `cross` error, `warning` warning, `robot` AI ops, `hourglass` waiting, `save` saves, `art` image ops

### Architecture Patterns

- One class per module with a standalone `main()` function and `if __name__ == "__main__":` guard
- **Unified config management**: Use `ConfigManager` for all configuration needs
  - Supports multi-layer override: defaults < config file < environment variables
  - Automatic validation and hot reload support
  - Backward compatible with old config loading method
- API calls use OpenAI-compatible client (`openai` library) pointed at DashScope base URL
- Image generation uses async task polling (submit task, poll for completion, download result)
- Content safety checking with keyword filtering before API submission
- Self-review loop: LLM evaluates its own output up to 3 iterations

### Configuration Management

**New Way (Recommended)**:
```python
from src.core.config_manager import ConfigManager

# Initialize with ConfigManager
config_manager = ConfigManager()
generator = RedBookContentGenerator(config_manager=config_manager)

# Access config
api_key = config_manager.get('openai_api_key')
timeout = config_manager.get('api.openai.timeout')
```

**Old Way (Still Supported)**:
```python
# Backward compatible - will create ConfigManager internally
generator = RedBookContentGenerator(config_path="config/config.json")
```

**Environment Variables**:
All config can be overridden via environment variables:
```bash
export OPENAI_API_KEY="sk-xxx"
export OPENAI_MODEL="qwen-max"
export RATE_LIMIT_OPENAI_RPM="100"
```

See `docs/CONFIG.md` for complete configuration documentation.

## Security Notes

- **NEVER commit `config/config.json`** - it contains API keys and is gitignored
- Always use `config.example.json` as the template for documentation
- The `input/` and `output/` directories are also gitignored
