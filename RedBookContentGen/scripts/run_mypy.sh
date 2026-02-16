#!/bin/bash
# Mypy 类型检查脚本

echo "🔍 开始运行 mypy 类型检查..."
echo ""

# 检查 mypy 是否安装
if ! command -v mypy &> /dev/null; then
    echo "❌ mypy 未安装，请先运行: pip install mypy>=1.8.0"
    exit 1
fi

# 显示 mypy 版本
echo "📦 Mypy 版本:"
python3 -m mypy --version
echo ""

# 检查核心模块（严格模式）
echo "🔒 检查核心模块（严格模式）..."
python3 -m mypy --config-file mypy.ini src/core/

# 检查业务模块（宽松模式）
echo ""
echo "📝 检查业务模块（宽松模式）..."
python3 -m mypy --config-file mypy.ini src/content_generator.py src/image_generator.py

# 检查 Web 应用
echo ""
echo "🌐 检查 Web 应用..."
python3 -m mypy --config-file mypy.ini web_app.py

echo ""
echo "✅ Mypy 类型检查完成！"
