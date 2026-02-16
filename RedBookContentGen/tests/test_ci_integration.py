#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI/CD 集成测试

测试 CI/CD 配置是否正确
"""

import subprocess
import sys
from pathlib import Path


def test_mypy_check_passes():
    """测试 mypy 类型检查是否通过"""
    result = subprocess.run(
        ["mypy", "src/", "--config-file=mypy.ini"],
        capture_output=True,
        text=True
    )
    
    # mypy 应该返回 0（成功）
    assert result.returncode == 0, f"mypy 检查失败:\n{result.stdout}\n{result.stderr}"


def test_github_workflows_exist():
    """测试 GitHub Actions 工作流文件是否存在"""
    workflows_dir = Path(".github/workflows")
    
    assert workflows_dir.exists(), "GitHub workflows 目录不存在"
    assert (workflows_dir / "ci.yml").exists(), "ci.yml 工作流文件不存在"
    assert (workflows_dir / "type-check.yml").exists(), "type-check.yml 工作流文件不存在"


def test_pre_commit_script_exists():
    """测试提交前检查脚本是否存在且可执行"""
    script_path = Path("scripts/pre-commit-check.sh")
    
    assert script_path.exists(), "提交前检查脚本不存在"
    assert script_path.stat().st_mode & 0o111, "提交前检查脚本不可执行"


def test_mypy_config_exists():
    """测试 mypy 配置文件是否存在"""
    mypy_config = Path("mypy.ini")
    
    assert mypy_config.exists(), "mypy.ini 配置文件不存在"


def test_ci_documentation_exists():
    """测试 CI/CD 文档是否存在"""
    docs = [
        Path("docs/CI_CD_INTEGRATION.md"),
        Path("docs/CI_CD_QUICK_REFERENCE.md"),
        Path(".github/README.md")
    ]
    
    for doc in docs:
        assert doc.exists(), f"文档 {doc} 不存在"


if __name__ == "__main__":
    # 运行所有测试
    print("🧪 运行 CI/CD 集成测试...")
    
    tests = [
        ("mypy 类型检查", test_mypy_check_passes),
        ("GitHub 工作流文件", test_github_workflows_exist),
        ("提交前检查脚本", test_pre_commit_script_exists),
        ("mypy 配置文件", test_mypy_config_exists),
        ("CI/CD 文档", test_ci_documentation_exists)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}: 通过")
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: 失败 - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name}: 错误 - {e}")
            failed += 1
    
    print(f"\n📊 测试结果: {passed} 通过, {failed} 失败")
    
    sys.exit(0 if failed == 0 else 1)
