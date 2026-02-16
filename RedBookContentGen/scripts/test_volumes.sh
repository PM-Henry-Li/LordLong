#!/bin/bash
# -*- coding: utf-8 -*-

# Docker 数据卷测试脚本
# 用于验证 Docker Compose 数据卷配置是否正确

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果统计
PASSED=0
FAILED=0

# 打印函数
print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}测试: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
}

# 检查 Docker 和 Docker Compose
check_prerequisites() {
    print_header "检查前置条件"
    
    print_test "检查 Docker 是否安装"
    if command -v docker &> /dev/null; then
        print_success "Docker 已安装: $(docker --version)"
    else
        print_error "Docker 未安装"
        exit 1
    fi
    
    print_test "检查 Docker Compose 是否安装"
    if command -v docker compose &> /dev/null; then
        print_success "Docker Compose 已安装: $(docker compose version)"
    elif command -v docker-compose &> /dev/null; then
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    else
        print_error "Docker Compose 未安装"
        exit 1
    fi
    
    print_test "检查 Docker 守护进程是否运行"
    if docker info &> /dev/null; then
        print_success "Docker 守护进程正在运行"
    else
        print_error "Docker 守护进程未运行"
        exit 1
    fi
}

# 检查必需的目录
check_directories() {
    print_header "检查必需的目录"
    
    REQUIRED_DIRS=("config" "input" "output" "logs")
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        print_test "检查目录: $dir"
        if [ -d "$dir" ]; then
            print_success "目录存在: $dir"
        else
            print_error "目录不存在: $dir"
            echo "  创建目录: $dir"
            mkdir -p "$dir"
        fi
    done
}

# 检查配置文件
check_config_files() {
    print_header "检查配置文件"
    
    print_test "检查 docker-compose.yml"
    if [ -f "docker-compose.yml" ]; then
        print_success "docker-compose.yml 存在"
    else
        print_error "docker-compose.yml 不存在"
        exit 1
    fi
    
    print_test "检查 .env 文件"
    if [ -f ".env" ]; then
        print_success ".env 文件存在"
    else
        echo -e "${YELLOW}  警告: .env 文件不存在，将使用默认配置${NC}"
    fi
    
    print_test "检查 config/config.json"
    if [ -f "config/config.json" ]; then
        print_success "config/config.json 存在"
    else
        echo -e "${YELLOW}  警告: config/config.json 不存在${NC}"
        if [ -f "config/config.example.json" ]; then
            echo "  提示: 可以从 config.example.json 复制"
        fi
    fi
}

# 验证 docker-compose.yml 中的卷配置
validate_compose_volumes() {
    print_header "验证 Docker Compose 卷配置"
    
    print_test "检查卷配置语法"
    if docker compose config &> /dev/null; then
        print_success "docker-compose.yml 语法正确"
    else
        print_error "docker-compose.yml 语法错误"
        docker compose config
        exit 1
    fi
    
    print_test "检查卷挂载配置"
    VOLUMES=$(docker compose config | grep -A 10 "volumes:" | grep -E "^\s+- " | wc -l)
    if [ "$VOLUMES" -ge 4 ]; then
        print_success "找到 $VOLUMES 个卷挂载配置"
    else
        print_error "卷挂载配置不完整（期望至少 4 个，实际 $VOLUMES 个）"
    fi
}

# 启动容器并测试卷挂载
test_volume_mounts() {
    print_header "测试卷挂载"
    
    print_test "启动容器"
    if docker compose up -d &> /dev/null; then
        print_success "容器启动成功"
    else
        print_error "容器启动失败"
        docker compose logs
        exit 1
    fi
    
    # 等待容器启动
    echo "等待容器启动..."
    sleep 5
    
    print_test "检查容器是否运行"
    if docker compose ps | grep -q "Up"; then
        print_success "容器正在运行"
    else
        print_error "容器未运行"
        docker compose ps
        exit 1
    fi
    
    # 测试配置卷（只读）
    print_test "测试配置卷（只读）"
    if docker compose exec -T app test -r /app/config/config.example.json; then
        print_success "配置卷可读"
    else
        print_error "配置卷不可读"
    fi
    
    # 测试配置卷是否只读
    if docker compose exec -T app sh -c "touch /app/config/test.txt 2>&1" | grep -q "Read-only"; then
        print_success "配置卷是只读的"
    else
        echo -e "${YELLOW}  警告: 配置卷可能不是只读的${NC}"
    fi
    
    # 测试输入卷
    print_test "测试输入卷（读写）"
    if docker compose exec -T app test -w /app/input; then
        print_success "输入卷可写"
    else
        print_error "输入卷不可写"
    fi
    
    # 测试输出卷
    print_test "测试输出卷（读写）"
    if docker compose exec -T app test -w /app/output; then
        print_success "输出卷可写"
    else
        print_error "输出卷不可写"
    fi
    
    # 测试日志卷
    print_test "测试日志卷（读写）"
    if docker compose exec -T app test -w /app/logs; then
        print_success "日志卷可写"
    else
        print_error "日志卷不可写"
    fi
}

# 测试文件持久化
test_persistence() {
    print_header "测试数据持久化"
    
    # 创建测试文件
    print_test "在容器中创建测试文件"
    TEST_FILE="test_$(date +%s).txt"
    if docker compose exec -T app sh -c "echo 'test data' > /app/output/$TEST_FILE"; then
        print_success "测试文件创建成功"
    else
        print_error "测试文件创建失败"
    fi
    
    # 检查主机上是否存在
    print_test "检查主机上是否存在测试文件"
    if [ -f "output/$TEST_FILE" ]; then
        print_success "测试文件在主机上可见"
    else
        print_error "测试文件在主机上不可见"
    fi
    
    # 重启容器
    print_test "重启容器后检查文件是否持久化"
    docker compose restart &> /dev/null
    sleep 3
    
    if docker compose exec -T app test -f "/app/output/$TEST_FILE"; then
        print_success "文件在容器重启后仍然存在"
    else
        print_error "文件在容器重启后丢失"
    fi
    
    # 清理测试文件
    rm -f "output/$TEST_FILE"
}

# 测试卷权限
test_permissions() {
    print_header "测试卷权限"
    
    print_test "检查配置卷权限（应该是只读）"
    if docker compose exec -T app sh -c "touch /app/config/test.txt 2>&1" | grep -q "Read-only"; then
        print_success "配置卷正确设置为只读"
    else
        echo -e "${YELLOW}  警告: 配置卷可能不是只读的${NC}"
    fi
    
    print_test "检查输出卷权限（应该可写）"
    TEST_FILE="perm_test_$(date +%s).txt"
    if docker compose exec -T app sh -c "echo 'test' > /app/output/$TEST_FILE && rm /app/output/$TEST_FILE"; then
        print_success "输出卷可读写"
    else
        print_error "输出卷权限不正确"
    fi
    
    print_test "检查日志卷权限（应该可写）"
    TEST_FILE="log_test_$(date +%s).log"
    if docker compose exec -T app sh -c "echo 'test' > /app/logs/$TEST_FILE && rm /app/logs/$TEST_FILE"; then
        print_success "日志卷可读写"
    else
        print_error "日志卷权限不正确"
    fi
}

# 清理测试环境
cleanup() {
    print_header "清理测试环境"
    
    print_test "停止容器"
    if docker compose down &> /dev/null; then
        print_success "容器已停止"
    else
        print_error "停止容器失败"
    fi
}

# 打印测试总结
print_summary() {
    print_header "测试总结"
    
    TOTAL=$((PASSED + FAILED))
    echo -e "总测试数: $TOTAL"
    echo -e "${GREEN}通过: $PASSED${NC}"
    echo -e "${RED}失败: $FAILED${NC}"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ 所有测试通过！${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ 部分测试失败${NC}\n"
        exit 1
    fi
}

# 主函数
main() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Docker 数据卷测试脚本"
    echo "=========================================="
    echo -e "${NC}"
    
    # 切换到项目根目录
    cd "$(dirname "$0")/.."
    
    # 运行测试
    check_prerequisites
    check_directories
    check_config_files
    validate_compose_volumes
    test_volume_mounts
    test_persistence
    test_permissions
    
    # 清理
    cleanup
    
    # 打印总结
    print_summary
}

# 捕获 Ctrl+C
trap cleanup EXIT

# 运行主函数
main
