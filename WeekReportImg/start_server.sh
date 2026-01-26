#!/bin/bash
# 启动周报图片生成器 Web 服务

cd "$(dirname "$0")"

echo "检查 Flask 依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Flask 未安装，正在安装..."
    pip3 install -r requirements-web.txt
    if [ $? -ne 0 ]; then
        echo "❌ Flask 安装失败，请手动运行："
        echo "   pip3 install flask"
        exit 1
    fi
fi

echo "✓ Flask 已安装"
echo ""
echo "启动 Web 服务..."
echo "访问地址: http://127.0.0.1:5555"
echo "按 Ctrl+C 停止服务"
echo ""

python3 app.py
