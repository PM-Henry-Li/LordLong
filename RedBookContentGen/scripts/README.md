# 测试脚本说明

本目录包含项目的各种测试和工具脚本。

## 可用脚本

### 1. test_docker.sh

**用途**: 测试 Docker 镜像的构建和运行

**功能**:
- 镜像构建测试
- 容器启动和健康检查
- 应用连接和性能测试
- 资源使用监控
- 容器生命周期管理

**使用方法**:
```bash
# 基本用法
./scripts/test_docker.sh

# 自定义配置
IMAGE_NAME=myapp IMAGE_TAG=v1.0 ./scripts/test_docker.sh

# 详细文档
查看 docs/DOCKER_TESTING.md
```

**前置条件**:
- Docker
- curl
- bc
- jq (可选)

---

### 2. test_health_check.sh

**用途**: 测试应用的健康检查端点

**功能**:
- 基本连接测试
- 响应格式验证
- HTTP 状态码检查
- 响应时间测试
- 连续请求测试

**使用方法**:
```bash
# 基本用法
./scripts/test_health_check.sh

# 自定义主机和端口
HOST=localhost PORT=8080 ./scripts/test_health_check.sh

# 详细文档
查看 docs/HEALTH_CHECK.md
```

**前置条件**:
- curl
- jq (可选)
- bc

---

### 3. check_config_security.py

**用途**: 检查配置文件的安全性

**功能**:
- 检测明文 API Key
- 验证敏感信息保护
- 提供安全建议

**使用方法**:
```bash
# 检查配置文件
python scripts/check_config_security.py

# 详细文档
查看 docs/CONFIG.md
```

**前置条件**:
- Python 3.10+

---

## 脚本开发规范

### 命名规范

- 测试脚本: `test_*.sh`
- 工具脚本: `*_tool.sh` 或 `*.py`
- 使用小写字母和下划线

### 脚本结构

```bash
#!/bin/bash
# 脚本用途说明

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 配置参数
PARAM="${PARAM:-default_value}"

# 主要逻辑
echo "开始执行..."

# 错误处理
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 成功${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
    exit 1
fi
```

### 最佳实践

1. **添加帮助信息**
   ```bash
   if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
       echo "用法: $0 [选项]"
       echo "选项:"
       echo "  --help, -h    显示帮助信息"
       exit 0
   fi
   ```

2. **参数验证**
   ```bash
   if [ -z "$REQUIRED_PARAM" ]; then
       echo "错误: 缺少必需参数"
       exit 1
   fi
   ```

3. **清理资源**
   ```bash
   cleanup() {
       echo "清理资源..."
       # 清理逻辑
   }
   trap cleanup EXIT
   ```

4. **详细输出**
   ```bash
   # 使用颜色区分不同类型的输出
   echo -e "${GREEN}✓ 成功${NC}"
   echo -e "${RED}✗ 失败${NC}"
   echo -e "${YELLOW}⚠ 警告${NC}"
   ```

5. **可配置性**
   ```bash
   # 支持环境变量配置
   PARAM="${PARAM:-default_value}"
   ```

## 添加新脚本

1. 创建脚本文件
2. 添加执行权限: `chmod +x scripts/new_script.sh`
3. 测试脚本: `bash -n scripts/new_script.sh`
4. 更新本 README
5. 编写相关文档

## 相关文档

- [Docker 测试文档](../docs/DOCKER_TESTING.md)
- [健康检查文档](../docs/HEALTH_CHECK.md)
- [配置管理文档](../docs/CONFIG.md)
- [测试指南](../docs/TESTING.md)

## 许可证

所有脚本遵循项目主许可证。
