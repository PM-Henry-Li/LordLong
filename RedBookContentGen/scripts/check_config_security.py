#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置安全检查脚本

检查配置文件中的安全问题，包括：
1. 明文 API Key（以 sk-, dashscope- 等开头）
2. 明文密码和 token
3. 其他敏感信息
4. 提供修复建议

使用方法:
    python scripts/check_config_security.py
    python scripts/check_config_security.py --config path/to/config.json
    python scripts/check_config_security.py --fix  # 自动修复（生成建议的配置文件）
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


class SecurityIssue:
    """安全问题"""

    def __init__(
        self,
        severity: str,
        key_path: str,
        issue_type: str,
        description: str,
        suggestion: str,
        value: str = "",
    ):
        """初始化安全问题

        Args:
            severity: 严重级别（critical, warning, info）
            key_path: 配置键路径
            issue_type: 问题类型
            description: 问题描述
            suggestion: 修复建议
            value: 问题值（可选，用于显示）
        """
        self.severity = severity
        self.key_path = key_path
        self.issue_type = issue_type
        self.description = description
        self.suggestion = suggestion
        self.value = value


class ConfigSecurityChecker:
    """配置安全检查器"""

    # 敏感信息模式
    SENSITIVE_PATTERNS = {
        "api_key": {
            "pattern": r"^(sk-[a-zA-Z0-9]{32,}|dashscope-[a-zA-Z0-9]{32,})",
            "severity": "critical",
            "description": "发现明文 API Key",
        },
        "password": {
            "pattern": r".+",  # 任何非空值
            "severity": "critical",
            "description": "发现明文密码",
        },
        "token": {
            "pattern": r"^[a-zA-Z0-9_-]{20,}$",
            "severity": "critical",
            "description": "发现明文 Token",
        },
        "secret": {
            "pattern": r".+",
            "severity": "critical",
            "description": "发现明文密钥",
        },
        "auth": {
            "pattern": r"^Bearer\s+[a-zA-Z0-9_-]+$",
            "severity": "warning",
            "description": "发现明文认证信息",
        },
    }

    # 敏感字段名称（不区分大小写）
    SENSITIVE_FIELD_NAMES = [
        "api_key",
        "apikey",
        "key",
        "password",
        "passwd",
        "pwd",
        "token",
        "secret",
        "auth",
        "authorization",
        "credential",
        "private_key",
        "access_key",
        "secret_key",
    ]

    # 环境变量引用模式
    ENV_VAR_PATTERN = re.compile(r"^\$\{[^}]+\}$")

    def __init__(self, config_path: str):
        """初始化检查器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.issues: List[SecurityIssue] = []
        self.config_data: Dict[str, Any] = {}

    def load_config(self) -> bool:
        """加载配置文件

        Returns:
            加载是否成功
        """
        if not self.config_path.exists():
            print(f"❌ 配置文件不存在: {self.config_path}")
            return False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件 JSON 格式错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return False

    def check(self) -> List[SecurityIssue]:
        """执行安全检查

        Returns:
            发现的安全问题列表
        """
        self.issues = []
        self._check_dict(self.config_data, "")
        return self.issues

    def _check_dict(self, data: Dict[str, Any], parent_path: str) -> None:
        """递归检查字典

        Args:
            data: 字典数据
            parent_path: 父路径
        """
        for key, value in data.items():
            # 跳过注释字段
            if key.startswith("_"):
                continue

            current_path = f"{parent_path}.{key}" if parent_path else key

            if isinstance(value, dict):
                # 递归检查嵌套字典
                self._check_dict(value, current_path)
            elif isinstance(value, list):
                # 检查列表
                self._check_list(value, current_path)
            elif isinstance(value, str):
                # 检查字符串值
                self._check_string_value(key, value, current_path)

    def _check_list(self, data: List[Any], parent_path: str) -> None:
        """递归检查列表

        Args:
            data: 列表数据
            parent_path: 父路径
        """
        for i, item in enumerate(data):
            current_path = f"{parent_path}[{i}]"

            if isinstance(item, dict):
                self._check_dict(item, current_path)
            elif isinstance(item, list):
                self._check_list(item, current_path)
            elif isinstance(item, str):
                # 检查列表中的字符串值
                self._check_string_value(f"item_{i}", item, current_path)

    def _check_string_value(
        self, key: str, value: str, key_path: str
    ) -> None:
        """检查字符串值

        Args:
            key: 配置键名
            value: 配置值
            key_path: 完整键路径
        """
        # 跳过空值
        if not value or not value.strip():
            return

        # 跳过环境变量引用（这是安全的）
        if self.ENV_VAR_PATTERN.match(value):
            return

        # 检查是否是敏感字段
        key_lower = key.lower()
        is_sensitive_field = any(
            sensitive in key_lower for sensitive in self.SENSITIVE_FIELD_NAMES
        )

        if not is_sensitive_field:
            return

        # 确定问题类型
        issue_type = None
        for pattern_name, pattern_info in self.SENSITIVE_PATTERNS.items():
            if pattern_name in key_lower:
                issue_type = pattern_name
                break

        if not issue_type:
            # 默认为通用敏感信息
            issue_type = "sensitive"

        # 检查值是否匹配敏感模式
        pattern_info = self.SENSITIVE_PATTERNS.get(
            issue_type, {"pattern": r".+", "severity": "warning", "description": "发现敏感信息"}
        )

        if re.match(pattern_info["pattern"], value):
            # 生成修复建议
            env_var_name = self._generate_env_var_name(key_path)
            suggestion = (
                f"建议使用环境变量:\n"
                f"  1. 在 .env 文件中设置: {env_var_name}={value}\n"
                f"  2. 在配置文件中引用: \"${{{env_var_name}}}\"\n"
                f"  3. 或直接使用环境变量: export {env_var_name}={value}"
            )

            # 隐藏部分敏感值
            masked_value = self._mask_value(value)

            issue = SecurityIssue(
                severity=pattern_info["severity"],
                key_path=key_path,
                issue_type=issue_type,
                description=f"{pattern_info['description']}: {masked_value}",
                suggestion=suggestion,
                value=value,
            )
            self.issues.append(issue)

    def _generate_env_var_name(self, key_path: str) -> str:
        """生成环境变量名称

        Args:
            key_path: 配置键路径

        Returns:
            环境变量名称（大写，下划线分隔）
        """
        # 移除数组索引
        key_path = re.sub(r"\[\d+\]", "", key_path)

        # 转换为大写，点号替换为下划线
        env_var = key_path.upper().replace(".", "_")

        return env_var

    def _mask_value(self, value: str) -> str:
        """隐藏敏感值的部分内容

        Args:
            value: 原始值

        Returns:
            隐藏后的值
        """
        if len(value) <= 8:
            return "***"

        # 显示前4个和后4个字符
        return f"{value[:4]}...{value[-4:]}"

    def generate_report(self) -> str:
        """生成检查报告

        Returns:
            报告文本
        """
        if not self.issues:
            return "✅ 未发现安全问题！配置文件安全。"

        # 按严重级别分组
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        warning_issues = [i for i in self.issues if i.severity == "warning"]
        info_issues = [i for i in self.issues if i.severity == "info"]

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("配置安全检查报告")
        report_lines.append("=" * 70)
        report_lines.append(f"配置文件: {self.config_path}")
        report_lines.append(
            f"发现问题: {len(self.issues)} 个 "
            f"(严重: {len(critical_issues)}, 警告: {len(warning_issues)}, 信息: {len(info_issues)})"
        )
        report_lines.append("=" * 70)
        report_lines.append("")

        # 输出严重问题
        if critical_issues:
            report_lines.append("🔴 严重问题 (Critical)")
            report_lines.append("-" * 70)
            for i, issue in enumerate(critical_issues, 1):
                report_lines.append(f"\n{i}. {issue.description}")
                report_lines.append(f"   位置: {issue.key_path}")
                report_lines.append(f"   类型: {issue.issue_type}")
                report_lines.append(f"   修复建议:\n   {issue.suggestion.replace(chr(10), chr(10) + '   ')}")
            report_lines.append("")

        # 输出警告问题
        if warning_issues:
            report_lines.append("🟡 警告问题 (Warning)")
            report_lines.append("-" * 70)
            for i, issue in enumerate(warning_issues, 1):
                report_lines.append(f"\n{i}. {issue.description}")
                report_lines.append(f"   位置: {issue.key_path}")
                report_lines.append(f"   类型: {issue.issue_type}")
                report_lines.append(f"   修复建议:\n   {issue.suggestion.replace(chr(10), chr(10) + '   ')}")
            report_lines.append("")

        # 输出信息问题
        if info_issues:
            report_lines.append("ℹ️  信息提示 (Info)")
            report_lines.append("-" * 70)
            for i, issue in enumerate(info_issues, 1):
                report_lines.append(f"\n{i}. {issue.description}")
                report_lines.append(f"   位置: {issue.key_path}")
                report_lines.append(f"   修复建议:\n   {issue.suggestion.replace(chr(10), chr(10) + '   ')}")
            report_lines.append("")

        # 总结和建议
        report_lines.append("=" * 70)
        report_lines.append("修复步骤总结")
        report_lines.append("=" * 70)
        report_lines.append("1. 创建 .env 文件（如果不存在）")
        report_lines.append("2. 将敏感信息移动到 .env 文件中")
        report_lines.append("3. 在配置文件中使用 ${ENV_VAR} 语法引用环境变量")
        report_lines.append("4. 确保 .env 文件已添加到 .gitignore")
        report_lines.append("5. 重新运行此脚本验证修复结果")
        report_lines.append("")
        report_lines.append("参考文档: docs/CONFIG.md")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)

    def generate_fixed_config(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """生成修复后的配置

        Returns:
            (修复后的配置字典, 环境变量字典)
        """
        fixed_config = self._deep_copy_dict(self.config_data)
        env_vars = {}

        for issue in self.issues:
            if issue.severity in ["critical", "warning"]:
                # 生成环境变量名
                env_var_name = self._generate_env_var_name(issue.key_path)

                # 替换配置值为环境变量引用
                self._set_nested_value(fixed_config, issue.key_path, f"${{{env_var_name}}}")

                # 记录环境变量
                env_vars[env_var_name] = issue.value

        return fixed_config, env_vars

    def _deep_copy_dict(self, data: Any) -> Any:
        """深拷贝字典

        Args:
            data: 数据

        Returns:
            拷贝后的数据
        """
        if isinstance(data, dict):
            return {key: self._deep_copy_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy_dict(item) for item in data]
        else:
            return data

    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any) -> None:
        """设置嵌套值

        Args:
            data: 字典数据
            key_path: 键路径
            value: 值
        """
        # 移除数组索引（暂不支持）
        key_path = re.sub(r"\[\d+\]", "", key_path)

        keys = key_path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="检查配置文件中的安全问题",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查默认配置文件
  python scripts/check_config_security.py

  # 检查指定配置文件
  python scripts/check_config_security.py --config path/to/config.json

  # 生成修复后的配置文件
  python scripts/check_config_security.py --fix

  # 生成修复后的配置文件并指定输出路径
  python scripts/check_config_security.py --fix --output config/config.fixed.json
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        default="config/config.json",
        help="配置文件路径（默认: config/config.json）",
    )

    parser.add_argument(
        "--fix",
        "-f",
        action="store_true",
        help="生成修复后的配置文件和 .env 文件",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="修复后的配置文件输出路径（默认: config/config.fixed.json）",
    )

    parser.add_argument(
        "--env-output",
        "-e",
        help=".env 文件输出路径（默认: .env.generated）",
    )

    args = parser.parse_args()

    # 创建检查器
    checker = ConfigSecurityChecker(args.config)

    # 加载配置
    if not checker.load_config():
        sys.exit(1)

    # 执行检查
    print("🔍 正在检查配置文件安全性...\n")
    issues = checker.check()

    # 生成报告
    report = checker.generate_report()
    print(report)

    # 如果需要修复
    if args.fix and issues:
        print("\n🔧 正在生成修复后的配置文件...\n")

        fixed_config, env_vars = checker.generate_fixed_config()

        # 输出路径
        output_path = args.output or "config/config.fixed.json"
        env_output_path = args.env_output or ".env.generated"

        # 保存修复后的配置
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(fixed_config, f, indent=2, ensure_ascii=False)

            print(f"✅ 修复后的配置文件已保存: {output_path}")
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            sys.exit(1)

        # 保存环境变量
        try:
            env_file = Path(env_output_path)

            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# 自动生成的环境变量文件\n")
                f.write("# 请将此文件重命名为 .env 并添加到 .gitignore\n\n")

                for env_var, value in env_vars.items():
                    f.write(f"{env_var}={value}\n")

            print(f"✅ 环境变量文件已保存: {env_output_path}")
            print(f"\n📝 下一步操作:")
            print(f"   1. 检查生成的文件: {output_path} 和 {env_output_path}")
            print(f"   2. 将 {env_output_path} 重命名为 .env")
            print(f"   3. 确保 .env 已添加到 .gitignore")
            print(f"   4. 使用修复后的配置文件替换原配置文件")
            print(f"   5. 重新运行此脚本验证修复结果")
        except Exception as e:
            print(f"❌ 保存环境变量文件失败: {e}")
            sys.exit(1)

    # 返回退出码
    if issues:
        critical_count = sum(1 for i in issues if i.severity == "critical")
        if critical_count > 0:
            sys.exit(2)  # 有严重问题
        else:
            sys.exit(1)  # 有警告问题
    else:
        sys.exit(0)  # 无问题


if __name__ == "__main__":
    main()
