#!/bin/bash
# WeekReportImg 快速部署脚本
# 使用方法: sudo bash deploy.sh

set -e

echo "=========================================="
echo "WeekReportImg 服务器部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 配置变量（可根据实际情况修改）
PROJECT_DIR="/opt/WeekReportImg"
SERVICE_USER="www-data"
SERVICE_NAME="weekreportimg"
SERVICE_PORT="5555"

# 检测当前目录
CURRENT_DIR=$(pwd)
if [ -f "app.py" ] && [ -f "weeKReportImgGen.py" ]; then
    echo -e "${GREEN}检测到项目文件，使用当前目录: $CURRENT_DIR${NC}"
    PROJECT_DIR="$CURRENT_DIR"
else
    echo -e "${YELLOW}未在当前目录检测到项目文件${NC}"
    echo -e "${YELLOW}将使用默认目录: $PROJECT_DIR${NC}"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 检查 Python
echo ""
echo "1. 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3，请先安装 Python 3.7+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}Python 版本: $(python3 --version)${NC}"

# 2. 安装依赖
echo ""
echo "2. 安装项目依赖..."
if [ -f "requirements-web.txt" ]; then
    pip3 install -r requirements-web.txt
    echo -e "${GREEN}依赖安装完成${NC}"
else
    echo -e "${YELLOW}警告: 未找到 requirements-web.txt，跳过依赖安装${NC}"
fi

# 3. 创建必要目录
echo ""
echo "3. 创建必要目录..."
mkdir -p "$PROJECT_DIR/output"
chmod 755 "$PROJECT_DIR/output"
echo -e "${GREEN}目录创建完成${NC}"

# 4. 修改 app.py（关闭 debug 模式）
echo ""
echo "4. 配置生产环境..."
if [ -f "$PROJECT_DIR/app.py" ]; then
    # 备份原文件
    cp "$PROJECT_DIR/app.py" "$PROJECT_DIR/app.py.bak"
    # 替换 debug=True 为 debug=False
    sed -i 's/debug=True/debug=False/g' "$PROJECT_DIR/app.py"
    echo -e "${GREEN}已配置生产环境（关闭 debug 模式）${NC}"
fi

# 5. 设置文件权限
echo ""
echo "5. 设置文件权限..."
# 检测用户是否存在
if id "$SERVICE_USER" &>/dev/null; then
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    echo -e "${GREEN}已设置用户权限: $SERVICE_USER${NC}"
else
    echo -e "${YELLOW}警告: 用户 $SERVICE_USER 不存在，跳过权限设置${NC}"
    echo -e "${YELLOW}提示: 您可以稍后手动设置: sudo chown -R user:user $PROJECT_DIR${NC}"
fi
chmod -R 755 "$PROJECT_DIR"

# 6. 创建 systemd 服务文件
echo ""
echo "6. 创建 systemd 服务..."
PYTHON_PATH=$(which python3)
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=WeekReportImg Web Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=$PYTHON_PATH $PROJECT_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}服务文件已创建: $SERVICE_FILE${NC}"

# 7. 重新加载 systemd 并启动服务
echo ""
echo "7. 启动服务..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# 等待服务启动
sleep 2

# 8. 检查服务状态
echo ""
echo "8. 检查服务状态..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ 服务运行正常${NC}"
else
    echo -e "${RED}✗ 服务启动失败，请查看日志: sudo journalctl -u $SERVICE_NAME${NC}"
    exit 1
fi

# 9. 配置防火墙
echo ""
echo "9. 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow "$SERVICE_PORT/tcp" 2>/dev/null || true
    echo -e "${GREEN}已配置 UFW 防火墙${NC}"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port="$SERVICE_PORT/tcp" 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo -e "${GREEN}已配置 firewalld 防火墙${NC}"
else
    echo -e "${YELLOW}未检测到防火墙工具，请手动开放端口 $SERVICE_PORT${NC}"
fi

# 10. 显示服务信息
echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务信息:"
echo "  - 服务名称: $SERVICE_NAME"
echo "  - 项目目录: $PROJECT_DIR"
echo "  - 访问地址: http://$(hostname -I | awk '{print $1}'):$SERVICE_PORT"
echo ""
echo "常用命令:"
echo "  - 查看状态: sudo systemctl status $SERVICE_NAME"
echo "  - 查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo "  - 重启服务: sudo systemctl restart $SERVICE_NAME"
echo "  - 停止服务: sudo systemctl stop $SERVICE_NAME"
echo ""
echo "注意:"
echo "  - 如果使用云服务器，请在控制台配置安全组规则，开放端口 $SERVICE_PORT"
echo "  - 建议配置 Nginx 反向代理和 SSL 证书（参考部署指南.md）"
echo ""
