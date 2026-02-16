#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感信息脱敏器测试

测试 SensitiveDataMasker 类的所有脱敏功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import SensitiveDataMasker, mask_sensitive_data, configure_masking


def test_mask_api_key():
    """测试 API Key 脱敏"""
    print("测试 API Key 脱敏...")
    
    # OpenAI API Key
    result1 = SensitiveDataMasker.mask_api_key("sk-abc123def456ghi789jkl012mno345pqr678")
    expected1 = "sk-***r678"
    assert result1 == expected1, f"Expected '{expected1}', got '{result1}'"
    
    result2 = SensitiveDataMasker.mask_api_key("sk-short")
    expected2 = "sk-***"
    assert result2 == expected2, f"Expected '{expected2}', got '{result2}'"
    
    # DashScope API Key
    result3 = SensitiveDataMasker.mask_api_key("dashscope-xyz789abc456def123ghi890jkl567mno234")
    expected3 = "dashscope-***o234"
    assert result3 == expected3, f"Expected '{expected3}', got '{result3}'"
    
    result4 = SensitiveDataMasker.mask_api_key("dashscope-short")
    expected4 = "dashscope-***"
    assert result4 == expected4, f"Expected '{expected4}', got '{result4}'"
    
    # 通用长字符串
    result5 = SensitiveDataMasker.mask_api_key("abcdefghijklmnopqrstuvwxyz")
    expected5 = "abcd...wxyz"
    assert result5 == expected5, f"Expected '{expected5}', got '{result5}'"
    
    print("✅ API Key 脱敏测试通过")


def test_mask_password():
    """测试密码脱敏"""
    print("测试密码脱敏...")
    
    assert SensitiveDataMasker.mask_password("MyP@ssw0rd123") == "***"
    assert SensitiveDataMasker.mask_password("") == ""
    
    print("✅ 密码脱敏测试通过")


def test_mask_token():
    """测试 Token 脱敏"""
    print("测试 Token 脱敏...")
    
    # 长 Token
    assert SensitiveDataMasker.mask_token("abcdefghijklmnopqrstuvwxyz") == "abcd...wxyz"
    
    # 短 Token
    assert SensitiveDataMasker.mask_token("short") == "***"
    assert SensitiveDataMasker.mask_token("12345678") == "***"
    
    print("✅ Token 脱敏测试通过")


def test_mask_phone():
    """测试手机号脱敏"""
    print("测试手机号脱敏...")
    
    # 中国大陆手机号
    assert SensitiveDataMasker.mask_phone("13812345678") == "138****5678"
    assert SensitiveDataMasker.mask_phone("19987654321") == "199****4321"
    
    # 国际手机号
    result = SensitiveDataMasker.mask_phone("+8613812345678")
    assert "****" in result
    
    print("✅ 手机号脱敏测试通过")


def test_mask_email():
    """测试邮箱脱敏"""
    print("测试邮箱脱敏...")
    
    assert SensitiveDataMasker.mask_email("user@example.com") == "u***@example.com"
    assert SensitiveDataMasker.mask_email("admin@test.org") == "a***@test.org"
    assert SensitiveDataMasker.mask_email("test.user@company.co.uk") == "t***@company.co.uk"
    
    print("✅ 邮箱脱敏测试通过")


def test_mask_id_card():
    """测试身份证号脱敏"""
    print("测试身份证号脱敏...")
    
    assert SensitiveDataMasker.mask_id_card("110101199001011234") == "110101****1234"
    assert SensitiveDataMasker.mask_id_card("44010119900101123X") == "440101****123X"
    
    print("✅ 身份证号脱敏测试通过")


def test_mask_url():
    """测试 URL 脱敏"""
    print("测试 URL 脱敏...")
    
    # 数据库连接字符串
    assert SensitiveDataMasker.mask_url("postgresql://user:password@host:5432/db") == "postgresql://user:***@host:5432/db"
    assert SensitiveDataMasker.mask_url("mysql://admin:secret123@localhost:3306/mydb") == "mysql://admin:***@localhost:3306/mydb"
    
    # 带认证的 HTTP URL
    assert SensitiveDataMasker.mask_url("https://user:pass@example.com/path") == "https://user:***@example.com/path"
    
    print("✅ URL 脱敏测试通过")


def test_mask_bearer_token():
    """测试 Bearer Token 脱敏"""
    print("测试 Bearer Token 脱敏...")
    
    assert SensitiveDataMasker.mask_bearer_token("Bearer abc123def456ghi789") == "Bearer ***i789"
    assert SensitiveDataMasker.mask_bearer_token("Bearer xyz") == "Bearer ***"
    
    print("✅ Bearer Token 脱敏测试通过")


def test_mask_dict():
    """测试字典脱敏"""
    print("测试字典脱敏...")
    
    data = {
        "api_key": "sk-abc123def456ghi789jkl012mno345pqr678",
        "password": "MyPassword123",
        "username": "admin",
        "email": "user@example.com",
        "phone": "13812345678",
        "normal_field": "normal_value"
    }
    
    masked = mask_sensitive_data(data)
    
    assert masked["api_key"] == "sk-***r678"
    assert masked["password"] == "***"
    assert masked["username"] == "admin"  # username 不完全隐藏
    assert masked["email"] == "u***@example.com"
    assert masked["phone"] == "138****5678"
    assert masked["normal_field"] == "normal_value"
    
    print("✅ 字典脱敏测试通过")


def test_mask_list():
    """测试列表脱敏"""
    print("测试列表脱敏...")
    
    data = [
        "sk-abc123def456ghi789jkl012mno345pqr678",
        "normal text",
        "13812345678",
        "user@example.com"
    ]
    
    masked = mask_sensitive_data(data)
    
    assert masked[0] == "sk-***r678"
    assert masked[1] == "normal text"
    assert masked[2] == "138****5678"
    assert masked[3] == "u***@example.com"
    
    print("✅ 列表脱敏测试通过")


def test_mask_nested_structure():
    """测试嵌套结构脱敏"""
    print("测试嵌套结构脱敏...")
    
    data = {
        "user": {
            "api_key": "sk-abc123def456ghi789jkl012mno345pqr678",
            "password": "secret",
            "contacts": [
                {"email": "user1@example.com", "phone": "13812345678"},
                {"email": "user2@example.com", "phone": "19987654321"}
            ]
        },
        "config": {
            "database_url": "postgresql://user:password@host:5432/db"
        }
    }
    
    masked = mask_sensitive_data(data)
    
    assert masked["user"]["api_key"] == "sk-***r678"
    assert masked["user"]["password"] == "***"
    assert masked["user"]["contacts"][0]["email"] == "u***@example.com"
    assert masked["user"]["contacts"][0]["phone"] == "138****5678"
    assert masked["config"]["database_url"] == "postgresql://user:***@host:5432/db"
    
    print("✅ 嵌套结构脱敏测试通过")


def test_configure_masking():
    """测试脱敏配置"""
    print("测试脱敏配置...")
    
    # 禁用邮箱脱敏
    configure_masking(mask_emails=False)
    
    result = mask_sensitive_data("user@example.com")
    assert result == "user@example.com"  # 不应该被脱敏
    
    # 重新启用邮箱脱敏
    configure_masking(mask_emails=True)
    
    result = mask_sensitive_data("user@example.com")
    assert result == "u***@example.com"  # 应该被脱敏
    
    # 完全禁用脱敏
    configure_masking(enabled=False)
    
    data = {
        "api_key": "sk-abc123def456ghi789jkl012mno345pqr678",
        "password": "secret"
    }
    
    masked = mask_sensitive_data(data)
    assert masked["api_key"] == "sk-abc123def456ghi789jkl012mno345pqr678"  # 不应该被脱敏
    assert masked["password"] == "secret"  # 不应该被脱敏
    
    # 重新启用脱敏
    configure_masking(enabled=True)
    
    print("✅ 脱敏配置测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试敏感信息脱敏器")
    print("=" * 60)
    print()
    
    try:
        test_mask_api_key()
        test_mask_password()
        test_mask_token()
        test_mask_phone()
        test_mask_email()
        test_mask_id_card()
        test_mask_url()
        test_mask_bearer_token()
        test_mask_dict()
        test_mask_list()
        test_mask_nested_structure()
        test_configure_masking()
        
        print()
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 测试出错: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
