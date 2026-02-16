#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查类型注解覆盖率的脚本
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def count_functions_and_annotations(file_path: Path) -> Tuple[int, int, List[str]]:
    """
    统计文件中的函数数量和带类型注解的函数数量
    
    Args:
        file_path: 文件路径
        
    Returns:
        (总函数数, 带注解函数数, 未注解函数列表)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    
    total_functions = 0
    annotated_functions = 0
    unannotated_functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 跳过私有方法和特殊方法（以 __ 开头和结尾）
            if node.name.startswith('__') and node.name.endswith('__'):
                continue
            
            total_functions += 1
            
            # 检查返回值类型注解
            has_return_annotation = node.returns is not None
            
            # 检查参数类型注解（跳过 self 和 cls）
            has_param_annotations = True
            for arg in node.args.args:
                if arg.arg in ('self', 'cls'):
                    continue
                if arg.annotation is None:
                    has_param_annotations = False
                    break
            
            # 如果有返回值注解或参数注解，认为已注解
            if has_return_annotation or has_param_annotations:
                annotated_functions += 1
            else:
                unannotated_functions.append(node.name)
    
    return total_functions, annotated_functions, unannotated_functions


def main():
    """主函数"""
    files_to_check = [
        "web_app.py",
        "src/web/blueprints/api.py",
        "src/web/blueprints/main.py",
        "src/web/error_handlers.py",
        "src/web/validators.py",
    ]
    
    print("=" * 60)
    print("类型注解覆盖率检查")
    print("=" * 60)
    print()
    
    total_all = 0
    annotated_all = 0
    
    for file_path_str in files_to_check:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue
        
        total, annotated, unannotated = count_functions_and_annotations(file_path)
        total_all += total
        annotated_all += annotated
        
        coverage = (annotated / total * 100) if total > 0 else 0
        
        print(f"📄 {file_path}")
        print(f"   总函数数: {total}")
        print(f"   已注解: {annotated}")
        print(f"   覆盖率: {coverage:.1f}%")
        
        if unannotated:
            print(f"   未注解函数: {', '.join(unannotated)}")
        
        print()
    
    print("=" * 60)
    overall_coverage = (annotated_all / total_all * 100) if total_all > 0 else 0
    print(f"总体覆盖率: {annotated_all}/{total_all} = {overall_coverage:.1f}%")
    print("=" * 60)
    
    if overall_coverage >= 80:
        print("✅ 类型注解覆盖率达标（>= 80%）")
        return 0
    else:
        print(f"❌ 类型注解覆盖率未达标（< 80%），当前: {overall_coverage:.1f}%")
        return 1


if __name__ == "__main__":
    sys.exit(main())
