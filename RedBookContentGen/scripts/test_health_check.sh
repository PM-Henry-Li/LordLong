#!/bin/bash
# 健康检查测试脚本

set -e

echo "=========================================="
echo "健康检查测试脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 curl 是否安装
if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗ 错误: 未安装 curl${NC}"
    echo "请先安装 curl: brew install curl (macOS) 或 apt-get install curl (Ubuntu)"
    exit 1
fi

# 检查 jq 是否安装（可选）
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠ 警告: 未安装 jq，将显示原始 JSON${NC}"
    USE_JQ=false
else
    USE_JQ=true
fi

# 配置
HOST="${HOST:-localhost}"
PORT="${PORT:-8080}"
HEALTH_URL="http://${HOST}:${PORT}/api/health"

echo "测试配置:"
echo "  主机: ${HOST}"
echo "  端口: ${PORT}"
echo "  健康检查 URL: ${HEALTH_URL}"
echo ""

# 测试 1: 基本连接测试
echo "测试 1: 基本连接测试"
echo "----------------------------------------"
if curl -s -f "${HEALTH_URL}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 连接成功${NC}"
else
    echo -e "${RED}✗ 连接失败${NC}"
    echo "请确保应用正在运行: python web_app.py"
    exit 1
fi
echo ""

# 测试 2: 响应格式测试
echo "测试 2: 响应格式测试"
echo "----------------------------------------"
RESPONSE=$(curl -s "${HEALTH_URL}")

if [ "$USE_JQ" = true ]; then
    echo "响应内容:"
    echo "$RESPONSE" | jq '.'
    
    # 检查必需字段
    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    TIMESTAMP=$(echo "$RESPONSE" | jq -r '.timestamp')
    VERSION=$(echo "$RESPONSE" | jq -r '.version')
    
    echo ""
    echo "字段验证:"
    
    if [ "$STATUS" != "null" ]; then
        echo -e "${GREEN}✓ status: ${STATUS}${NC}"
    else
        echo -e "${RED}✗ 缺少 status 字段${NC}"
    fi
    
    if [ "$TIMESTAMP" != "null" ]; then
        echo -e "${GREEN}✓ timestamp: ${TIMESTAMP}${NC}"
    else
        echo -e "${RED}✗ 缺少 timestamp 字段${NC}"
    fi
    
    if [ "$VERSION" != "null" ]; then
        echo -e "${GREEN}✓ version: ${VERSION}${NC}"
    else
        echo -e "${RED}✗ 缺少 version 字段${NC}"
    fi
    
    # 检查服务状态
    CONTENT_SERVICE=$(echo "$RESPONSE" | jq -r '.services.content_service')
    IMAGE_SERVICE=$(echo "$RESPONSE" | jq -r '.services.image_service')
    
    echo ""
    echo "服务状态:"
    
    if [ "$CONTENT_SERVICE" = "ok" ]; then
        echo -e "${GREEN}✓ content_service: ${CONTENT_SERVICE}${NC}"
    else
        echo -e "${RED}✗ content_service: ${CONTENT_SERVICE}${NC}"
    fi
    
    if [ "$IMAGE_SERVICE" = "ok" ]; then
        echo -e "${GREEN}✓ image_service: ${IMAGE_SERVICE}${NC}"
    else
        echo -e "${RED}✗ image_service: ${IMAGE_SERVICE}${NC}"
    fi
else
    echo "响应内容:"
    echo "$RESPONSE"
fi
echo ""

# 测试 3: HTTP 状态码测试
echo "测试 3: HTTP 状态码测试"
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ HTTP 状态码: ${HTTP_CODE} (正常)${NC}"
elif [ "$HTTP_CODE" = "503" ]; then
    echo -e "${YELLOW}⚠ HTTP 状态码: ${HTTP_CODE} (服务不可用)${NC}"
else
    echo -e "${RED}✗ HTTP 状态码: ${HTTP_CODE} (异常)${NC}"
fi
echo ""

# 测试 4: 响应时间测试
echo "测试 4: 响应时间测试"
echo "----------------------------------------"
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "${HEALTH_URL}")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

echo "响应时间: ${RESPONSE_TIME_MS} ms"

if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
    echo -e "${GREEN}✓ 响应时间正常 (< 1秒)${NC}"
elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
    echo -e "${YELLOW}⚠ 响应时间较慢 (1-3秒)${NC}"
else
    echo -e "${RED}✗ 响应时间过慢 (> 3秒)${NC}"
fi
echo ""

# 测试 5: 连续请求测试
echo "测试 5: 连续请求测试 (10次)"
echo "----------------------------------------"
SUCCESS_COUNT=0
FAIL_COUNT=0

for i in {1..10}; do
    if curl -s -f "${HEALTH_URL}" > /dev/null 2>&1; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo -n "."
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo -n "x"
    fi
done

echo ""
echo "成功: ${SUCCESS_COUNT}/10"
echo "失败: ${FAIL_COUNT}/10"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ 所有请求成功${NC}"
else
    echo -e "${YELLOW}⚠ 部分请求失败${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo "测试完成"
echo "=========================================="

if [ "$HTTP_CODE" = "200" ] && [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ 健康检查功能正常${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ 健康检查存在问题，请检查日志${NC}"
    exit 1
fi
