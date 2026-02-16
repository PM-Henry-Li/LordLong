#!/bin/bash
# Docker 镜像构建和运行测试脚本
# 用途：验证 Docker 镜像的构建、运行、健康检查和基本功能

set -e

echo "=========================================="
echo "Docker 镜像测试脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
IMAGE_NAME="${IMAGE_NAME:-redbookcontentgen}"
IMAGE_TAG="${IMAGE_TAG:-test}"
CONTAINER_NAME="${CONTAINER_NAME:-rbcg-test}"
HOST_PORT="${HOST_PORT:-8080}"
CONTAINER_PORT="8080"
TEST_TIMEOUT="${TEST_TIMEOUT:-120}"

# 清理标志
CLEANUP_ON_SUCCESS="${CLEANUP_ON_SUCCESS:-true}"
CLEANUP_ON_FAILURE="${CLEANUP_ON_FAILURE:-false}"

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 辅助函数：打印测试标题
print_test_header() {
    echo ""
    echo "测试 $1: $2"
    echo "----------------------------------------"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# 辅助函数：标记测试通过
mark_test_passed() {
    echo -e "${GREEN}✓ $1${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

# 辅助函数：标记测试失败
mark_test_failed() {
    echo -e "${RED}✗ $1${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

# 辅助函数：标记测试警告
mark_test_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 辅助函数：清理资源
cleanup() {
    echo ""
    echo "=========================================="
    echo "清理资源"
    echo "=========================================="
    
    # 停止并删除容器
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "停止容器: ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" > /dev/null 2>&1 || true
        echo "删除容器: ${CONTAINER_NAME}"
        docker rm "${CONTAINER_NAME}" > /dev/null 2>&1 || true
        echo -e "${GREEN}✓ 容器已清理${NC}"
    fi
    
    # 可选：删除测试镜像
    if [ "$1" = "full" ]; then
        if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}:${IMAGE_TAG}$"; then
            echo "删除镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
            docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" > /dev/null 2>&1 || true
            echo -e "${GREEN}✓ 镜像已清理${NC}"
        fi
    fi
}

# 捕获退出信号，确保清理
trap 'cleanup' EXIT

# 检查依赖
echo "检查依赖..."
echo "----------------------------------------"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ 错误: 未安装 Docker${NC}"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装: $(docker --version)${NC}"

if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗ 错误: 未安装 curl${NC}"
    echo "请先安装 curl: brew install curl (macOS) 或 apt-get install curl (Ubuntu)"
    exit 1
fi
echo -e "${GREEN}✓ curl 已安装${NC}"

# 检查 Docker 守护进程
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ 错误: Docker 守护进程未运行${NC}"
    echo "请启动 Docker Desktop 或 Docker 服务"
    exit 1
fi
echo -e "${GREEN}✓ Docker 守护进程运行正常${NC}"

# 清理旧的测试容器和镜像
echo ""
echo "清理旧的测试资源..."
cleanup

# ============================================
# 测试 1: 镜像构建测试
# ============================================
print_test_header "1" "镜像构建测试"

echo "开始构建镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "构建命令: docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
echo ""

BUILD_START=$(date +%s)

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" . 2>&1 | tee /tmp/docker_build.log; then
    BUILD_END=$(date +%s)
    BUILD_TIME=$((BUILD_END - BUILD_START))
    
    mark_test_passed "镜像构建成功 (耗时: ${BUILD_TIME}秒)"
    
    # 检查镜像大小
    IMAGE_SIZE=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    echo "镜像大小: ${IMAGE_SIZE}"
    
    # 检查镜像层数
    IMAGE_LAYERS=$(docker history "${IMAGE_NAME}:${IMAGE_TAG}" --no-trunc | wc -l)
    echo "镜像层数: ${IMAGE_LAYERS}"
else
    mark_test_failed "镜像构建失败"
    echo ""
    echo "构建日志（最后 20 行）："
    tail -20 /tmp/docker_build.log
    exit 1
fi

# ============================================
# 测试 2: 镜像安全检查
# ============================================
print_test_header "2" "镜像安全检查"

# 检查镜像是否使用非 root 用户
USER_INFO=$(docker inspect "${IMAGE_NAME}:${IMAGE_TAG}" --format '{{.Config.User}}')
if [ -n "$USER_INFO" ] && [ "$USER_INFO" != "root" ] && [ "$USER_INFO" != "0" ]; then
    mark_test_passed "使用非 root 用户运行: ${USER_INFO}"
else
    mark_test_warning "镜像使用 root 用户运行（不推荐）"
fi

# 检查健康检查配置
HEALTHCHECK=$(docker inspect "${IMAGE_NAME}:${IMAGE_TAG}" --format '{{.Config.Healthcheck}}')
if [ "$HEALTHCHECK" != "<nil>" ] && [ -n "$HEALTHCHECK" ]; then
    mark_test_passed "已配置健康检查"
    echo "健康检查配置: ${HEALTHCHECK}"
else
    mark_test_warning "未配置健康检查"
fi

# ============================================
# 测试 3: 容器启动测试
# ============================================
print_test_header "3" "容器启动测试"

echo "启动容器: ${CONTAINER_NAME}"
echo "端口映射: ${HOST_PORT}:${CONTAINER_PORT}"
echo ""

# 创建临时配置文件（如果需要）
TEMP_CONFIG_DIR=$(mktemp -d)
if [ -f "config/config.example.json" ]; then
    cp config/config.example.json "${TEMP_CONFIG_DIR}/config.json"
    echo "使用示例配置文件"
fi

# 启动容器
if docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key}" \
    -v "${TEMP_CONFIG_DIR}:/app/config" \
    "${IMAGE_NAME}:${IMAGE_TAG}"; then
    
    mark_test_passed "容器启动成功"
    
    # 等待容器启动
    echo "等待容器启动（最多 ${TEST_TIMEOUT} 秒）..."
    WAIT_COUNT=0
    while [ $WAIT_COUNT -lt $TEST_TIMEOUT ]; do
        if docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -q "${CONTAINER_NAME}"; then
            echo -e "${GREEN}✓ 容器运行中${NC}"
            break
        fi
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
        echo -n "."
    done
    echo ""
    
    if [ $WAIT_COUNT -ge $TEST_TIMEOUT ]; then
        mark_test_failed "容器启动超时"
        echo "容器日志："
        docker logs "${CONTAINER_NAME}"
        exit 1
    fi
else
    mark_test_failed "容器启动失败"
    exit 1
fi

# 显示容器信息
echo ""
echo "容器信息："
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

# ============================================
# 测试 4: 容器健康检查测试
# ============================================
print_test_header "4" "容器健康检查测试"

echo "等待健康检查启动（宽限期 40 秒）..."
sleep 45

# 检查健康状态
HEALTH_STATUS=$(docker inspect "${CONTAINER_NAME}" --format '{{.State.Health.Status}}' 2>/dev/null || echo "none")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    mark_test_passed "容器健康状态: ${HEALTH_STATUS}"
elif [ "$HEALTH_STATUS" = "starting" ]; then
    mark_test_warning "容器健康状态: ${HEALTH_STATUS} (仍在启动中)"
    echo "等待健康检查完成..."
    sleep 30
    HEALTH_STATUS=$(docker inspect "${CONTAINER_NAME}" --format '{{.State.Health.Status}}')
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        mark_test_passed "容器健康状态: ${HEALTH_STATUS}"
    else
        mark_test_failed "容器健康状态: ${HEALTH_STATUS}"
    fi
elif [ "$HEALTH_STATUS" = "none" ]; then
    mark_test_warning "容器未配置健康检查"
else
    mark_test_failed "容器健康状态: ${HEALTH_STATUS}"
    echo "健康检查日志："
    docker inspect "${CONTAINER_NAME}" --format '{{json .State.Health}}' | jq '.' 2>/dev/null || echo "无法解析健康检查日志"
fi

# ============================================
# 测试 5: 应用连接测试
# ============================================
print_test_header "5" "应用连接测试"

HEALTH_URL="http://localhost:${HOST_PORT}/api/health"

echo "测试 URL: ${HEALTH_URL}"
echo "等待应用就绪..."

# 等待应用响应
WAIT_COUNT=0
while [ $WAIT_COUNT -lt 60 ]; do
    if curl -s -f "${HEALTH_URL}" > /dev/null 2>&1; then
        mark_test_passed "应用响应正常"
        break
    fi
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
    echo -n "."
done
echo ""

if [ $WAIT_COUNT -ge 60 ]; then
    mark_test_failed "应用连接超时"
    echo "容器日志："
    docker logs "${CONTAINER_NAME}" --tail 50
    exit 1
fi

# ============================================
# 测试 6: 健康检查端点测试
# ============================================
print_test_header "6" "健康检查端点测试"

RESPONSE=$(curl -s "${HEALTH_URL}")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}")

echo "HTTP 状态码: ${HTTP_CODE}"

if [ "$HTTP_CODE" = "200" ]; then
    mark_test_passed "HTTP 状态码正常"
else
    mark_test_failed "HTTP 状态码异常: ${HTTP_CODE}"
fi

# 检查响应格式
if command -v jq &> /dev/null; then
    echo ""
    echo "响应内容:"
    echo "$RESPONSE" | jq '.'
    
    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    if [ "$STATUS" = "healthy" ]; then
        mark_test_passed "服务状态: ${STATUS}"
    else
        mark_test_warning "服务状态: ${STATUS}"
    fi
else
    echo "响应内容: ${RESPONSE}"
fi

# ============================================
# 测试 7: 响应时间测试
# ============================================
print_test_header "7" "响应时间测试"

RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "${HEALTH_URL}")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

echo "响应时间: ${RESPONSE_TIME_MS} ms"

if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
    mark_test_passed "响应时间正常 (< 1秒)"
elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
    mark_test_warning "响应时间较慢 (1-3秒)"
else
    mark_test_failed "响应时间过慢 (> 3秒)"
fi

# ============================================
# 测试 8: 容器资源使用测试
# ============================================
print_test_header "8" "容器资源使用测试"

# 获取容器资源使用情况
STATS=$(docker stats "${CONTAINER_NAME}" --no-stream --format "{{.CPUPerc}}\t{{.MemUsage}}")
CPU_USAGE=$(echo "$STATS" | awk '{print $1}' | sed 's/%//')
MEM_USAGE=$(echo "$STATS" | awk '{print $2}')

echo "CPU 使用率: ${CPU_USAGE}%"
echo "内存使用: ${MEM_USAGE}"

# CPU 使用率检查（空闲时应该很低）
if (( $(echo "$CPU_USAGE < 10.0" | bc -l) )); then
    mark_test_passed "CPU 使用率正常"
elif (( $(echo "$CPU_USAGE < 50.0" | bc -l) )); then
    mark_test_warning "CPU 使用率较高"
else
    mark_test_warning "CPU 使用率过高"
fi

# ============================================
# 测试 9: 容器日志测试
# ============================================
print_test_header "9" "容器日志测试"

echo "容器日志（最后 20 行）："
docker logs "${CONTAINER_NAME}" --tail 20

# 检查是否有错误日志
ERROR_COUNT=$(docker logs "${CONTAINER_NAME}" 2>&1 | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    mark_test_passed "无错误日志"
else
    mark_test_warning "发现 ${ERROR_COUNT} 条错误日志"
fi

# ============================================
# 测试 10: 容器停止和重启测试
# ============================================
print_test_header "10" "容器停止和重启测试"

echo "停止容器..."
if docker stop "${CONTAINER_NAME}" > /dev/null 2>&1; then
    mark_test_passed "容器停止成功"
else
    mark_test_failed "容器停止失败"
fi

echo "重启容器..."
if docker start "${CONTAINER_NAME}" > /dev/null 2>&1; then
    mark_test_passed "容器重启成功"
    
    # 等待应用恢复
    echo "等待应用恢复..."
    sleep 10
    
    if curl -s -f "${HEALTH_URL}" > /dev/null 2>&1; then
        mark_test_passed "应用恢复正常"
    else
        mark_test_warning "应用恢复较慢"
    fi
else
    mark_test_failed "容器重启失败"
fi

# ============================================
# 测试总结
# ============================================
echo ""
echo "=========================================="
echo "测试总结"
echo "=========================================="
echo ""
echo "总测试数: ${TOTAL_TESTS}"
echo -e "${GREEN}通过: ${PASSED_TESTS}${NC}"
echo -e "${RED}失败: ${FAILED_TESTS}${NC}"
echo ""

# 计算成功率
SUCCESS_RATE=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
echo "成功率: ${SUCCESS_RATE}%"
echo ""

# 镜像信息
echo "镜像信息:"
docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# 容器信息
echo "容器信息:"
docker ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 清理决策
if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    echo ""
    
    if [ "$CLEANUP_ON_SUCCESS" = "true" ]; then
        echo "清理测试资源..."
        cleanup full
    else
        echo "保留测试资源（设置 CLEANUP_ON_SUCCESS=true 以自动清理）"
        echo ""
        echo "手动清理命令:"
        echo "  docker stop ${CONTAINER_NAME}"
        echo "  docker rm ${CONTAINER_NAME}"
        echo "  docker rmi ${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    exit 0
else
    echo -e "${RED}✗ 部分测试失败${NC}"
    echo ""
    
    if [ "$CLEANUP_ON_FAILURE" = "true" ]; then
        echo "清理测试资源..."
        cleanup full
    else
        echo "保留测试资源以便调试（设置 CLEANUP_ON_FAILURE=true 以自动清理）"
        echo ""
        echo "调试命令:"
        echo "  docker logs ${CONTAINER_NAME}"
        echo "  docker exec -it ${CONTAINER_NAME} /bin/bash"
        echo ""
        echo "手动清理命令:"
        echo "  docker stop ${CONTAINER_NAME}"
        echo "  docker rm ${CONTAINER_NAME}"
        echo "  docker rmi ${IMAGE_NAME}:${IMAGE_TAG}"
    fi
    
    exit 1
fi
