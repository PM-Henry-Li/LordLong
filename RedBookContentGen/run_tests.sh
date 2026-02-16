#!/bin/bash
# -*- coding: utf-8 -*-
# 测试运行脚本

set -e

echo "🧪 RedBookContentGen 测试套件"
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python3 --version

# 检查依赖
echo ""
echo "📦 检查测试依赖..."
python3 -c "import pytest; import pytest_cov; import pytest_asyncio; import pytest_mock" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 测试依赖已安装${NC}"
else
    echo -e "${RED}✗ 测试依赖未安装${NC}"
    echo "正在安装测试依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "================================"
echo ""

# 解析命令行参数
TEST_TYPE=${1:-all}
VERBOSE=${2:--v}

case $TEST_TYPE in
    unit)
        echo "🔬 运行单元测试..."
        python3 -m pytest tests/unit -m unit $VERBOSE
        ;;
    integration)
        echo "🔗 运行集成测试..."
        python3 -m pytest tests/integration -m integration $VERBOSE
        ;;
    e2e)
        echo "🌐 运行端到端测试..."
        python3 -m pytest tests/e2e -m e2e $VERBOSE
        ;;
    fast)
        echo "⚡ 运行快速测试（跳过慢速测试）..."
        python3 -m pytest -m "not slow" $VERBOSE
        ;;
    coverage)
        echo "📊 运行测试并生成覆盖率报告..."
        python3 -m pytest --cov=src --cov-report=html --cov-report=term-missing $VERBOSE
        echo ""
        echo -e "${GREEN}✓ 覆盖率报告已生成: htmlcov/index.html${NC}"
        ;;
    env)
        echo "🔧 验证测试环境..."
        python3 -m pytest tests/test_environment.py $VERBOSE
        ;;
    all)
        echo "🚀 运行所有测试..."
        python3 -m pytest $VERBOSE
        ;;
    *)
        echo -e "${RED}未知的测试类型: $TEST_TYPE${NC}"
        echo ""
        echo "用法: ./run_tests.sh [测试类型] [选项]"
        echo ""
        echo "测试类型:"
        echo "  all          - 运行所有测试（默认）"
        echo "  unit         - 只运行单元测试"
        echo "  integration  - 只运行集成测试"
        echo "  e2e          - 只运行端到端测试"
        echo "  fast         - 运行快速测试（跳过慢速测试）"
        echo "  coverage     - 运行测试并生成覆盖率报告"
        echo "  env          - 验证测试环境"
        echo ""
        echo "选项:"
        echo "  -v           - 详细输出（默认）"
        echo "  -vv          - 更详细的输出"
        echo "  -q           - 简洁输出"
        echo ""
        echo "示例:"
        echo "  ./run_tests.sh                    # 运行所有测试"
        echo "  ./run_tests.sh unit               # 只运行单元测试"
        echo "  ./run_tests.sh coverage           # 生成覆盖率报告"
        echo "  ./run_tests.sh all -vv            # 运行所有测试，详细输出"
        exit 1
        ;;
esac

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 测试通过！${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ 测试失败！${NC}"
    exit 1
fi
