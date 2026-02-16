#!/usr/bin/env bash
# -*- coding: utf-8 -*-

# ============================================
# Docker Compose 测试脚本
# ============================================
# 用途：测试 Docker Compose 配置和服务编排
# 作者：RedBookContentGen Team
# 日期：2026-02-14
# ============================================

set -e  # 遇到错误立即退出

# ============================================
# 配置变量
# ============================================

# 项目名称（用于隔离测试环境）
PROJECT_NAME="${PROJECT_NAME:-rbcg-compose-test}"

# 测试超时时间（秒）
TEST_TIMEOUT="${TEST_TIMEOUT:-180}"

# 是否在测试成功后清理资源
CLEANUP_ON_SUCCESS="${CLEANUP_ON_SUCCESS:-true}"

# 是否在测试失败后清理资源
CLEANUP_ON_FAILURE="${CLEANUP_ON_FAILURE:-false}"

# 主机端口（避免与现有服务冲突）
HOST_PORT="${HOST_PORT:-8090}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ============================================
# 辅助函数
# ============================================

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 打印分隔线
print_separator() {
    echo "----------------------------------------"
}

# 打印测试标题
print_test_title() {
    echo ""
    echo "测试 $1: $2"
    print_separator
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# 等待服务就绪
wait_for_service() {
    local url=$1
    local timeout=$2
    local elapsed=0
    local interval=2
    
    print_info "等待服务就绪: $url"
    
    while [ $elapsed -lt $timeout ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            print_success "服务就绪 (耗时: ${elapsed}秒)"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    
    echo ""
    print_error "服务启动超时 (${timeout}秒)"
    return 1
}

# 清理测试资源
cleanup() {
    print_info "清理测试资源..."
    
    # 停止并删除容器
    docker compose -p "$PROJECT_NAME" down -v 2>/dev/null || true
    
    # 删除测试用的 .env 文件
    rm -f .env.test
    
    print_success "清理完成"
}

# ============================================
# 测试函数
# ============================================

# 测试 1: 检查依赖
test_dependencies() {
    print_test_title 1 "检查依赖"
    
    # 检查 Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version)
        print_success "Docker 已安装: $docker_version"
    else
        print_error "Docker 未安装"
        return 1
    fi
    
    # 检查 Docker Compose
    if docker compose version &> /dev/null; then
        local compose_version=$(docker compose version)
        print_success "Docker Compose 已安装: $compose_version"
    elif command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version)
        print_warning "使用旧版 docker-compose: $compose_version"
        print_warning "建议升级到 Docker Compose V2"
    else
        print_error "Docker Compose 未安装"
        return 1
    fi
    
    # 检查 Docker 守护进程
    if docker info &> /dev/null; then
        print_success "Docker 守护进程运行正常"
    else
        print_error "Docker 守护进程未运行"
        return 1
    fi
    
    # 检查 curl
    if command -v curl &> /dev/null; then
        print_success "curl 已安装"
    else
        print_error "curl 未安装"
        return 1
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
    return 0
}

# 测试 2: 配置文件验证
test_config_files() {
    print_test_title 2 "配置文件验证"
    
    # 检查 docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        print_success "docker-compose.yml 存在"
    else
        print_error "docker-compose.yml 不存在"
        return 1
    fi
    
    # 验证 docker-compose.yml 语法
    if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
        print_success "docker-compose.yml 语法正确"
    else
        print_error "docker-compose.yml 语法错误"
        docker compose -f docker-compose.yml config
        return 1
    fi
    
    # 检查 .env.example
    if [ -f ".env.example" ]; then
        print_success ".env.example 存在"
    else
        print_warning ".env.example 不存在"
    fi
    
    # 检查 Dockerfile
    if [ -f "Dockerfile" ]; then
        print_success "Dockerfile 存在"
    else
        print_error "Dockerfile 不存在"
        return 1
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
    return 0
}

# 测试 3: 创建测试环境变量
test_create_env() {
    print_test_title 3 "创建测试环境变量"
    
    # 创建测试用的 .env 文件
    cat > .env.test << EOF
# Docker Compose 测试环境变量
HOST_PORT=${HOST_PORT}
OPENAI_API_KEY=sk-test-key-for-compose-testing
OPENAI_MODEL=qwen-max
IMAGE_GENERATION_MODE=template
TEMPLATE_STYLE=retro_chinese
LOG_LEVEL=INFO
CACHE_ENABLED=true
EOF
    
    if [ -f ".env.test" ]; then
        print_success "测试环境变量文件创建成功"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "测试环境变量文件创建失败"
        return 1
    fi
}

# 测试 4: 服务启动
test_service_start() {
    print_test_title 4 "服务启动测试"
    
    # 使用测试环境变量启动服务
    print_info "启动服务..."
    if docker compose -p "$PROJECT_NAME" --env-file .env.test up -d; then
        print_success "服务启动命令执行成功"
    else
        print_error "服务启动命令执行失败"
        return 1
    fi
    
    # 等待容器启动
    sleep 5
    
    # 检查容器状态
    local container_status=$(docker compose -p "$PROJECT_NAME" ps --format json | grep -o '"State":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$container_status" = "running" ]; then
        print_success "容器运行中"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "容器未运行，状态: $container_status"
        docker compose -p "$PROJECT_NAME" logs
        return 1
    fi
}

# 测试 5: 健康检查
test_health_check() {
    print_test_title 5 "健康检查测试"
    
    # 等待健康检查通过
    local max_wait=60
    local elapsed=0
    local interval=5
    
    print_info "等待健康检查通过（最多 ${max_wait} 秒）..."
    
    while [ $elapsed -lt $max_wait ]; do
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "${PROJECT_NAME}-app-1" 2>/dev/null || echo "unknown")
        
        if [ "$health_status" = "healthy" ]; then
            print_success "容器健康状态: healthy"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        elif [ "$health_status" = "unhealthy" ]; then
            print_error "容器健康状态: unhealthy"
            docker inspect --format='{{json .State.Health}}' "${PROJECT_NAME}-app-1" 2>/dev/null || true
            return 1
        fi
        
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    echo ""
    print_warning "健康检查超时，当前状态: $health_status"
    return 1
}

# 测试 6: 应用连接
test_app_connection() {
    print_test_title 6 "应用连接测试"
    
    local url="http://localhost:${HOST_PORT}/api/health"
    
    if wait_for_service "$url" "$TEST_TIMEOUT"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "应用连接失败"
        docker compose -p "$PROJECT_NAME" logs --tail=50
        return 1
    fi
}

# 测试 7: 健康检查端点
test_health_endpoint() {
    print_test_title 7 "健康检查端点测试"
    
    local url="http://localhost:${HOST_PORT}/api/health"
    local response=$(curl -s "$url")
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    echo "HTTP 状态码: $http_code"
    echo "响应内容: $response"
    
    if [ "$http_code" = "200" ]; then
        print_success "HTTP 状态码正常"
    else
        print_error "HTTP 状态码异常: $http_code"
        return 1
    fi
    
    # 检查响应内容
    if echo "$response" | grep -q '"status":"healthy"'; then
        print_success "服务状态: healthy"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "服务状态异常"
        return 1
    fi
}

# 测试 8: 数据卷挂载
test_volume_mounts() {
    print_test_title 8 "数据卷挂载测试"
    
    # 检查配置目录
    if docker compose -p "$PROJECT_NAME" exec -T app test -d /app/config; then
        print_success "配置目录挂载正常"
    else
        print_error "配置目录挂载失败"
        return 1
    fi
    
    # 检查输出目录
    if docker compose -p "$PROJECT_NAME" exec -T app test -d /app/output; then
        print_success "输出目录挂载正常"
    else
        print_error "输出目录挂载失败"
        return 1
    fi
    
    # 检查日志目录
    if docker compose -p "$PROJECT_NAME" exec -T app test -d /app/logs; then
        print_success "日志目录挂载正常"
    else
        print_error "日志目录挂载失败"
        return 1
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
    return 0
}

# 测试 9: 环境变量传递
test_environment_variables() {
    print_test_title 9 "环境变量传递测试"
    
    # 检查 OPENAI_API_KEY
    local api_key=$(docker compose -p "$PROJECT_NAME" exec -T app printenv OPENAI_API_KEY)
    if [ -n "$api_key" ]; then
        print_success "OPENAI_API_KEY 已设置"
    else
        print_error "OPENAI_API_KEY 未设置"
        return 1
    fi
    
    # 检查 LOG_LEVEL
    local log_level=$(docker compose -p "$PROJECT_NAME" exec -T app printenv LOG_LEVEL)
    if [ "$log_level" = "INFO" ]; then
        print_success "LOG_LEVEL 设置正确: $log_level"
    else
        print_warning "LOG_LEVEL 设置异常: $log_level"
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
    return 0
}

# 测试 10: 服务重启
test_service_restart() {
    print_test_title 10 "服务重启测试"
    
    # 重启服务
    print_info "重启服务..."
    if docker compose -p "$PROJECT_NAME" restart; then
        print_success "服务重启命令执行成功"
    else
        print_error "服务重启命令执行失败"
        return 1
    fi
    
    # 等待服务恢复
    sleep 10
    
    # 检查服务是否正常
    local url="http://localhost:${HOST_PORT}/api/health"
    if curl -sf "$url" > /dev/null 2>&1; then
        print_success "服务恢复正常"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "服务恢复失败"
        return 1
    fi
}

# ============================================
# 主函数
# ============================================

main() {
    echo "=========================================="
    echo "Docker Compose 测试脚本"
    echo "=========================================="
    echo ""
    
    # 清理旧的测试资源
    print_info "清理旧的测试资源..."
    cleanup
    echo ""
    
    # 运行测试
    local test_failed=false
    
    test_dependencies || test_failed=true
    test_config_files || test_failed=true
    test_create_env || test_failed=true
    test_service_start || test_failed=true
    test_health_check || test_failed=true
    test_app_connection || test_failed=true
    test_health_endpoint || test_failed=true
    test_volume_mounts || test_failed=true
    test_environment_variables || test_failed=true
    test_service_restart || test_failed=true
    
    # 打印测试总结
    echo ""
    echo "=========================================="
    echo "测试总结"
    echo "=========================================="
    echo ""
    echo "总测试数: $TOTAL_TESTS"
    echo "通过: $PASSED_TESTS"
    echo "失败: $FAILED_TESTS"
    echo ""
    
    # 计算成功率
    if [ $TOTAL_TESTS -gt 0 ]; then
        local success_rate=$(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS / $TOTAL_TESTS) * 100}")
        echo "成功率: ${success_rate}%"
        echo ""
    fi
    
    # 清理资源
    if [ "$test_failed" = true ]; then
        print_error "部分测试失败"
        echo ""
        
        if [ "$CLEANUP_ON_FAILURE" = true ]; then
            cleanup
        else
            print_warning "保留测试资源以便调试"
            echo "调试命令:"
            echo "  docker compose -p $PROJECT_NAME logs"
            echo "  docker compose -p $PROJECT_NAME exec app /bin/bash"
            echo "  docker compose -p $PROJECT_NAME down -v  # 清理资源"
        fi
        
        exit 1
    else
        print_success "所有测试通过！"
        echo ""
        
        if [ "$CLEANUP_ON_SUCCESS" = true ]; then
            cleanup
        else
            print_info "保留测试资源"
            echo "访问应用: http://localhost:${HOST_PORT}"
            echo "清理命令: docker compose -p $PROJECT_NAME down -v"
        fi
        
        exit 0
    fi
}

# 捕获 Ctrl+C 信号
trap cleanup INT TERM

# 运行主函数
main
