#!/bin/bash
# -*- coding: utf-8 -*-
# 提交前检查脚本
# 用法: ./scripts/pre-commit-check.sh

set -e  # 遇到错误立即退出

echo "================================================"
echo "🚀 开始提交前检查..."
echo "================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASSED=0
FAILED=0
WARNINGS=0

# 1. 代码格式检查（可选）
echo "📝 1. 代码格式检查 (black)..."
if black --check src/ tests/ 2>/dev/null; then
    echo -e "${GREEN}✅ 代码格式检查通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  代码格式需要调整，运行: black src/ tests/${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 2. Flake8 检查（可选）
echo "🔍 2. Flake8 代码风格检查..."
if flake8 src/ --count --statistics 2>/dev/null; then
    echo -e "${GREEN}✅ Flake8 检查通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Flake8 发现一些问题（不影响提交）${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 3. mypy 类型检查（必须通过）⚠️
echo "🔍 3. mypy 类型检查 (必须通过)..."
if mypy src/ --config-file=mypy.ini; then
    echo -e "${GREEN}✅ mypy 类型检查通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ mypy 类型检查失败！${NC}"
    echo -e "${RED}请修复上述类型错误后再提交代码。${NC}"
    FAILED=$((FAILED + 1))
    exit 1
fi
echo ""

# 4. 单元测试（推荐）
echo "🧪 4. 单元测试..."
if pytest tests/unit/ -v --tb=short 2>/dev/null; then
    echo -e "${GREEN}✅ 单元测试通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  部分单元测试失败（建议修复）${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 5. 导入检查
echo "📦 5. 模块导入检查..."
if python -c "import src.content_generator; import src.image_generator; import src.core.config_manager" 2>/dev/null; then
    echo -e "${GREEN}✅ 模块导入检查通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ 模块导入失败！${NC}"
    FAILED=$((FAILED + 1))
    exit 1
fi
echo ""

# 总结
echo "================================================"
echo "📊 检查结果汇总"
echo "================================================"
echo -e "${GREEN}✅ 通过: $PASSED${NC}"
echo -e "${YELLOW}⚠️  警告: $WARNINGS${NC}"
echo -e "${RED}❌ 失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有必需检查通过，可以提交代码！${NC}"
    echo ""
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}💡 建议修复警告项以提高代码质量${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ 存在必须修复的问题，请修复后再提交${NC}"
    exit 1
fi
