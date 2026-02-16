# Docker 镜像测试文档

## 概述

本文档描述如何使用 `scripts/test_docker.sh` 脚本测试 RedBookContentGen 项目的 Docker 镜像构建和运行。

## 测试脚本功能

`test_docker.sh` 脚本提供以下测试功能：

1. **镜像构建测试** - 验证 Dockerfile 构建成功
2. **镜像安全检查** - 检查非 root 用户和健康检查配置
3. **容器启动测试** - 验证容器能够正常启动
4. **容器健康检查测试** - 验证 Docker 健康检查功能
5. **应用连接测试** - 验证应用能够响应请求
6. **健康检查端点测试** - 验证 `/api/health` 端点
7. **响应时间测试** - 测量应用响应性能
8. **容器资源使用测试** - 监控 CPU 和内存使用
9. **容器日志测试** - 检查应用日志
10. **容器停止和重启测试** - 验证容器生命周期管理

## 前置条件

### 必需工具

- **Docker**: 用于构建和运行容器
  ```bash
  # 检查 Docker 版本
  docker --version
  
  # 启动 Docker 守护进程
  # macOS: 启动 Docker Desktop
  # Linux: sudo systemctl start docker
  ```

- **curl**: 用于测试 HTTP 端点
  ```bash
  # macOS
  brew install curl
  
  # Ubuntu/Debian
  sudo apt-get install curl
  ```

- **bc**: 用于浮点数计算（通常已预装）
  ```bash
  # macOS
  brew install bc
  
  # Ubuntu/Debian
  sudo apt-get install bc
  ```

### 可选工具

- **jq**: 用于格式化 JSON 输出（推荐）
  ```bash
  # macOS
  brew install jq
  
  # Ubuntu/Debian
  sudo apt-get install jq
  ```

## 使用方法

### 基本用法

```bash
# 在项目根目录运行
./scripts/test_docker.sh
```

### 自定义配置

脚本支持通过环境变量自定义配置：

```bash
# 自定义镜像名称和标签
IMAGE_NAME=myapp IMAGE_TAG=v1.0 ./scripts/test_docker.sh

# 自定义容器名称和端口
CONTAINER_NAME=myapp-test HOST_PORT=9090 ./scripts/test_docker.sh

# 自定义超时时间（秒）
TEST_TIMEOUT=180 ./scripts/test_docker.sh

# 测试成功后保留资源（用于调试）
CLEANUP_ON_SUCCESS=false ./scripts/test_docker.sh

# 测试失败后自动清理资源
CLEANUP_ON_FAILURE=true ./scripts/test_docker.sh
```

### 配置环境变量

```bash
# 设置 API Key（如果需要测试实际功能）
export OPENAI_API_KEY="sk-your-api-key"

# 运行测试
./scripts/test_docker.sh
```

### 完整示例

```bash
# 设置所有配置并运行测试
IMAGE_NAME=redbookcontentgen \
IMAGE_TAG=latest \
CONTAINER_NAME=rbcg-prod \
HOST_PORT=8080 \
TEST_TIMEOUT=120 \
CLEANUP_ON_SUCCESS=true \
OPENAI_API_KEY="sk-your-api-key" \
./scripts/test_docker.sh
```

## 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `IMAGE_NAME` | `redbookcontentgen` | Docker 镜像名称 |
| `IMAGE_TAG` | `test` | Docker 镜像标签 |
| `CONTAINER_NAME` | `rbcg-test` | 容器名称 |
| `HOST_PORT` | `8080` | 主机端口 |
| `CONTAINER_PORT` | `8080` | 容器端口（固定） |
| `TEST_TIMEOUT` | `120` | 测试超时时间（秒） |
| `CLEANUP_ON_SUCCESS` | `true` | 测试成功后是否清理资源 |
| `CLEANUP_ON_FAILURE` | `false` | 测试失败后是否清理资源 |
| `OPENAI_API_KEY` | `sk-test-key` | OpenAI API Key（可选） |

## 测试输出

### 成功输出示例

```
==========================================
Docker 镜像测试脚本
==========================================

检查依赖...
----------------------------------------
✓ Docker 已安装: Docker version 24.0.0
✓ curl 已安装
✓ Docker 守护进程运行正常

清理旧的测试资源...

测试 1: 镜像构建测试
----------------------------------------
开始构建镜像: redbookcontentgen:test
✓ 镜像构建成功 (耗时: 45秒)
镜像大小: 512MB
镜像层数: 12

测试 2: 镜像安全检查
----------------------------------------
✓ 使用非 root 用户运行: appuser
✓ 已配置健康检查

测试 3: 容器启动测试
----------------------------------------
✓ 容器启动成功
✓ 容器运行中

测试 4: 容器健康检查测试
----------------------------------------
✓ 容器健康状态: healthy

测试 5: 应用连接测试
----------------------------------------
✓ 应用响应正常

测试 6: 健康检查端点测试
----------------------------------------
HTTP 状态码: 200
✓ HTTP 状态码正常
✓ 服务状态: healthy

测试 7: 响应时间测试
----------------------------------------
响应时间: 234.56 ms
✓ 响应时间正常 (< 1秒)

测试 8: 容器资源使用测试
----------------------------------------
CPU 使用率: 2.5%
内存使用: 128MB / 512MB
✓ CPU 使用率正常

测试 9: 容器日志测试
----------------------------------------
✓ 无错误日志

测试 10: 容器停止和重启测试
----------------------------------------
✓ 容器停止成功
✓ 容器重启成功
✓ 应用恢复正常

==========================================
测试总结
==========================================

总测试数: 10
通过: 10
失败: 0

成功率: 100.00%

✓ 所有测试通过！
```

### 失败输出示例

```
测试 4: 容器健康检查测试
----------------------------------------
✗ 容器健康状态: unhealthy
健康检查日志：
{
  "Status": "unhealthy",
  "FailingStreak": 3,
  "Log": [
    {
      "ExitCode": 1,
      "Output": "curl: (7) Failed to connect to localhost port 8080"
    }
  ]
}

==========================================
测试总结
==========================================

总测试数: 10
通过: 8
失败: 2

成功率: 80.00%

✗ 部分测试失败

保留测试资源以便调试
调试命令:
  docker logs rbcg-test
  docker exec -it rbcg-test /bin/bash
```

## 故障排查

### 问题 1: 镜像构建失败

**症状**:
```
✗ 镜像构建失败
```

**可能原因**:
1. Dockerfile 语法错误
2. 依赖包安装失败
3. 网络问题

**解决方案**:
```bash
# 查看完整构建日志
cat /tmp/docker_build.log

# 手动构建并查看详细输出
docker build -t redbookcontentgen:test . --no-cache --progress=plain

# 检查 Dockerfile 语法
docker build -t redbookcontentgen:test . --dry-run
```

### 问题 2: 容器启动失败

**症状**:
```
✗ 容器启动失败
```

**可能原因**:
1. 端口已被占用
2. 配置文件缺失
3. 环境变量未设置

**解决方案**:
```bash
# 检查端口占用
lsof -i :8080
netstat -an | grep 8080

# 使用不同端口
HOST_PORT=9090 ./scripts/test_docker.sh

# 查看容器日志
docker logs rbcg-test

# 手动启动容器调试
docker run -it --rm \
  -p 8080:8080 \
  -e OPENAI_API_KEY="sk-test-key" \
  redbookcontentgen:test \
  /bin/bash
```

### 问题 3: 健康检查失败

**症状**:
```
✗ 容器健康状态: unhealthy
```

**可能原因**:
1. 应用启动时间过长
2. 健康检查端点未实现
3. 应用崩溃

**解决方案**:
```bash
# 查看健康检查日志
docker inspect rbcg-test --format='{{json .State.Health}}' | jq

# 手动测试健康检查
docker exec rbcg-test curl -f http://localhost:8080/api/health

# 增加启动宽限期（修改 Dockerfile）
HEALTHCHECK --start-period=60s ...

# 查看应用日志
docker logs rbcg-test --tail 100
```

### 问题 4: 应用连接超时

**症状**:
```
✗ 应用连接超时
```

**可能原因**:
1. 应用启动慢
2. 端口映射错误
3. 防火墙阻止

**解决方案**:
```bash
# 增加超时时间
TEST_TIMEOUT=300 ./scripts/test_docker.sh

# 检查容器端口映射
docker port rbcg-test

# 检查容器网络
docker inspect rbcg-test --format='{{.NetworkSettings.IPAddress}}'

# 从容器内部测试
docker exec rbcg-test curl http://localhost:8080/api/health
```

### 问题 5: 响应时间过慢

**症状**:
```
⚠ 响应时间过慢 (> 3秒)
```

**可能原因**:
1. 资源不足
2. 应用性能问题
3. 网络延迟

**解决方案**:
```bash
# 检查容器资源使用
docker stats rbcg-test

# 增加容器资源限制
docker run -d \
  --name rbcg-test \
  --memory="1g" \
  --cpus="2" \
  -p 8080:8080 \
  redbookcontentgen:test

# 查看应用性能日志
docker logs rbcg-test | grep -i "slow\|timeout"
```

## 最佳实践

### 1. 持续集成

在 CI/CD 流程中集成测试脚本：

```yaml
# .github/workflows/docker-test.yml
name: Docker Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Run Docker tests
        run: |
          chmod +x scripts/test_docker.sh
          ./scripts/test_docker.sh
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          CLEANUP_ON_SUCCESS: true
          CLEANUP_ON_FAILURE: true
```

### 2. 本地开发

开发时保留测试资源以便调试：

```bash
# 运行测试但不清理
CLEANUP_ON_SUCCESS=false ./scripts/test_docker.sh

# 测试完成后手动调试
docker exec -it rbcg-test /bin/bash

# 查看日志
docker logs -f rbcg-test

# 完成后手动清理
docker stop rbcg-test
docker rm rbcg-test
```

### 3. 性能测试

定期运行性能测试：

```bash
# 运行多次测试并记录结果
for i in {1..5}; do
  echo "测试轮次 $i"
  ./scripts/test_docker.sh 2>&1 | tee "test_results_$i.log"
  sleep 10
done

# 分析响应时间
grep "响应时间" test_results_*.log
```

### 4. 生产环境验证

部署前验证镜像：

```bash
# 使用生产配置测试
IMAGE_TAG=production \
CONTAINER_NAME=rbcg-prod-test \
HOST_PORT=8080 \
OPENAI_API_KEY="${PROD_API_KEY}" \
./scripts/test_docker.sh

# 测试通过后推送镜像
docker tag redbookcontentgen:production registry.example.com/redbookcontentgen:latest
docker push registry.example.com/redbookcontentgen:latest
```

## 相关文档

- [Dockerfile](../Dockerfile) - Docker 镜像构建配置
- [健康检查文档](./HEALTH_CHECK.md) - 健康检查端点详细说明
- [部署指南](./DEPLOYMENT.md) - 生产环境部署指南
- [Docker Compose 配置](../docker-compose.yml) - 容器编排配置

## 更新历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-02-14 | 1.0.0 | 初始版本，创建 Docker 测试脚本和文档 |

## 反馈和贡献

如果您在使用测试脚本时遇到问题或有改进建议，请：

1. 查看[故障排查](#故障排查)章节
2. 查看容器日志：`docker logs rbcg-test`
3. 提交 Issue 或 Pull Request

## 许可证

本文档和测试脚本遵循项目主许可证。
