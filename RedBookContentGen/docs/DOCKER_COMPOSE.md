# Docker Compose 使用指南

## 概述

本文档介绍如何使用 Docker Compose 部署和管理 RedBookContentGen 应用。Docker Compose 简化了容器编排，提供一键启动、配置管理和服务依赖管理功能。

## 前置条件

### 必需工具

- **Docker**: 版本 20.10 或更高
  ```bash
  # 检查 Docker 版本
  docker --version
  
  # 启动 Docker 守护进程
  # macOS: 启动 Docker Desktop
  # Linux: sudo systemctl start docker
  ```

- **Docker Compose**: 版本 2.0 或更高
  ```bash
  # 检查 Docker Compose 版本
  docker compose version
  
  # 如果使用旧版本（v1），命令为 docker-compose
  docker-compose --version
  ```

### 配置文件

在启动前，需要准备以下配置文件：

1. **环境变量文件** (`.env`)
   ```bash
   # 复制示例文件
   cp .env.example .env
   
   # 编辑配置
   vim .env
   ```

2. **应用配置文件** (`config/config.json`)
   ```bash
   # 复制示例文件
   cp config/config.example.json config/config.json
   
   # 编辑配置（可选，环境变量优先级更高）
   vim config/config.json
   ```

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件，至少需要配置 API Key：

```bash
# 必填：OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here

# 可选：其他配置使用默认值
HOST_PORT=8080
IMAGE_GENERATION_MODE=template
TEMPLATE_STYLE=retro_chinese
```

### 2. 启动服务

```bash
# 构建并启动服务（后台运行）
docker compose up -d

# 或者前台运行（查看实时日志）
docker compose up
```

### 3. 验证服务

```bash
# 检查容器状态
docker compose ps

# 查看健康状态
curl http://localhost:8080/api/health

# 预期输出
{
  "status": "healthy",
  "timestamp": "2026-02-14T10:30:00.000000",
  "version": "1.0.0",
  "services": {
    "content_service": "ok",
    "image_service": "ok"
  }
}
```

### 4. 访问应用

打开浏览器访问：http://localhost:8080

## 常用命令

### 服务管理

```bash
# 启动服务（后台运行）
docker compose up -d

# 启动服务（前台运行，查看日志）
docker compose up

# 停止服务（保留容器）
docker compose stop

# 启动已停止的服务
docker compose start

# 重启服务
docker compose restart

# 停止并删除容器
docker compose down

# 停止并删除容器、网络、镜像
docker compose down --rmi all

# 停止并删除容器、网络、数据卷
docker compose down -v
```

### 日志查看

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs app

# 实时跟踪日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail=100

# 查看带时间戳的日志
docker compose logs -t
```

### 容器管理

```bash
# 查看容器状态
docker compose ps

# 查看容器详细信息
docker compose ps -a

# 进入容器 Shell
docker compose exec app /bin/bash

# 以 root 用户进入容器
docker compose exec -u root app /bin/bash

# 在容器中执行命令
docker compose exec app python --version
```

### 镜像管理

```bash
# 构建镜像
docker compose build

# 强制重新构建镜像（不使用缓存）
docker compose build --no-cache

# 拉取镜像
docker compose pull

# 查看镜像
docker compose images
```

### 资源清理

```bash
# 删除停止的容器
docker compose rm

# 删除所有容器和网络
docker compose down

# 删除所有容器、网络和镜像
docker compose down --rmi all

# 删除所有容器、网络和数据卷
docker compose down -v

# 清理未使用的 Docker 资源
docker system prune -a
```

## 配置说明

### 环境变量

Docker Compose 支持通过 `.env` 文件配置环境变量。环境变量优先级：

1. Shell 环境变量（最高）
2. `.env` 文件
3. `docker-compose.yml` 中的默认值（最低）

#### 基础配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST_PORT` | `8080` | 主机端口 |

#### API 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API Key（必填） |
| `OPENAI_MODEL` | `qwen-max` | 模型名称 |
| `OPENAI_BASE_URL` | `https://dashscope.aliyuncs.com/...` | API 基础 URL |

#### 图片生成配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IMAGE_GENERATION_MODE` | `template` | 生成模式（template/api） |
| `TEMPLATE_STYLE` | `retro_chinese` | 模板风格 |

#### 日志配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_FORMAT` | `json` | 日志格式 |

#### 缓存配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CACHE_ENABLED` | `true` | 是否启用缓存 |
| `CACHE_TTL` | `3600` | 缓存过期时间（秒） |

#### 速率限制配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RATE_LIMIT_OPENAI_RPM` | `60` | OpenAI API 每分钟请求数 |
| `RATE_LIMIT_IMAGE_RPM` | `10` | 图片 API 每分钟请求数 |
| `RATE_LIMIT_IMAGE_CONCURRENT` | `3` | 图片生成最大并发数 |

### 数据卷挂载

Docker Compose 配置了以下数据卷挂载：

| 主机路径 | 容器路径 | 权限 | 说明 |
|---------|---------|------|------|
| `./config` | `/app/config` | 只读 (`:ro`) | 配置文件目录 |
| `./input` | `/app/input` | 读写 (`:rw`) | 输入文件目录 |
| `./output` | `/app/output` | 读写 (`:rw`) | 输出文件目录 |
| `./logs` | `/app/logs` | 读写 (`:rw`) | 日志文件目录 |
| `./cache` | `/app/cache` | 读写 (`:rw`) | 缓存目录（可选） |

**数据卷说明**:

1. **配置卷** (`./config:/app/config:ro`)
   - 只读挂载，防止容器内意外修改配置
   - 包含 `config.json` 和 `config.example.json`
   - 修改配置后需要重启容器生效

2. **输入卷** (`./input:/app/input:rw`)
   - 存储待处理的输入文件
   - 支持 TXT、Excel 等格式

3. **输出卷** (`./output:/app/output:rw`)
   - 存储生成的内容和图片
   - 按日期组织：`output/images/YYYYMMDD/`

4. **日志卷** (`./logs:/app/logs:rw`)
   - 存储应用日志（JSON 格式）
   - 自动轮转，保留最近 5 个备份

5. **缓存卷** (`./cache:/app/cache:rw`) - 可选
   - 存储缓存数据（如果启用文件缓存）
   - 需要在 `docker-compose.yml` 中取消注释

**主机目录 vs 命名卷**:

当前使用**主机目录挂载**方式，适合开发环境和需要直接访问文件的场景。如果需要在生产环境使用命名卷，请参考 [Docker 数据卷配置文档](./DOCKER_VOLUMES.md)。

**详细说明**: 参见 [Docker 数据卷配置文档](./DOCKER_VOLUMES.md)

### 资源限制

默认资源限制配置：

```yaml
deploy:
  resources:
    limits:
      cpus: '2'        # 最多使用 2 个 CPU 核心
      memory: 1G       # 最多使用 1GB 内存
    reservations:
      cpus: '0.5'      # 保留 0.5 个 CPU 核心
      memory: 256M     # 保留 256MB 内存
```

可以根据实际需求调整 `docker-compose.yml` 中的资源限制。

### 健康检查

健康检查配置：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
  interval: 30s      # 每 30 秒检查一次
  timeout: 3s        # 单次检查超时 3 秒
  start_period: 40s  # 启动后等待 40 秒
  retries: 3         # 连续失败 3 次标记为不健康
```

## 使用场景

### 场景 1: 开发环境

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env

# 2. 启动服务（前台运行，查看日志）
docker compose up

# 3. 修改代码后重新构建
docker compose build
docker compose up -d

# 4. 查看日志
docker compose logs -f

# 5. 停止服务
docker compose down
```

### 场景 2: 生产环境

```bash
# 1. 配置环境变量（使用生产配置）
cp .env.example .env
vim .env

# 2. 构建镜像
docker compose build --no-cache

# 3. 启动服务（后台运行）
docker compose up -d

# 4. 验证服务
curl http://localhost:8080/api/health

# 5. 查看日志
docker compose logs --tail=100

# 6. 监控服务状态
watch -n 5 'docker compose ps'
```

### 场景 3: 测试环境

```bash
# 1. 使用测试配置
cp .env.example .env.test
vim .env.test

# 2. 指定配置文件启动
docker compose --env-file .env.test up -d

# 3. 运行测试
docker compose exec app pytest

# 4. 清理环境
docker compose down -v
```

### 场景 4: 多实例部署

```bash
# 启动多个实例（不同端口）
HOST_PORT=8081 docker compose -p rbcg-1 up -d
HOST_PORT=8082 docker compose -p rbcg-2 up -d
HOST_PORT=8083 docker compose -p rbcg-3 up -d

# 查看所有实例
docker compose -p rbcg-1 ps
docker compose -p rbcg-2 ps
docker compose -p rbcg-3 ps

# 停止所有实例
docker compose -p rbcg-1 down
docker compose -p rbcg-2 down
docker compose -p rbcg-3 down
```

## 故障排查

### 问题 1: 容器启动失败

**症状**:
```bash
$ docker compose up -d
Error response from daemon: driver failed programming external connectivity
```

**可能原因**:
- 端口已被占用
- Docker 守护进程未运行
- 权限不足

**解决方案**:
```bash
# 检查端口占用
lsof -i :8080
netstat -an | grep 8080

# 使用不同端口
HOST_PORT=9090 docker compose up -d

# 检查 Docker 状态
docker info

# 重启 Docker 守护进程
# macOS: 重启 Docker Desktop
# Linux: sudo systemctl restart docker
```

### 问题 2: 健康检查失败

**症状**:
```bash
$ docker compose ps
NAME                  STATUS
redbookcontentgen     Up 2 minutes (unhealthy)
```

**可能原因**:
- 应用启动时间过长
- 配置错误
- 依赖缺失

**解决方案**:
```bash
# 查看容器日志
docker compose logs app

# 查看健康检查日志
docker inspect redbookcontentgen --format='{{json .State.Health}}' | jq

# 手动测试健康检查
docker compose exec app curl -f http://localhost:8080/api/health

# 增加启动宽限期（修改 docker-compose.yml）
healthcheck:
  start_period: 60s
```

### 问题 3: 环境变量未生效

**症状**:
应用使用默认配置而非 `.env` 文件中的配置

**可能原因**:
- `.env` 文件格式错误
- 环境变量名称错误
- Shell 环境变量覆盖

**解决方案**:
```bash
# 检查 .env 文件格式
cat .env

# 验证环境变量
docker compose config

# 查看容器环境变量
docker compose exec app env | grep OPENAI

# 重新启动服务
docker compose down
docker compose up -d
```

### 问题 4: 数据卷权限问题

**症状**:
```
PermissionError: [Errno 13] Permission denied: '/app/output/...'
```

**可能原因**:
- 主机目录权限不足
- 容器用户权限不匹配

**解决方案**:
```bash
# 检查目录权限
ls -la output/ logs/

# 修改目录权限
chmod -R 755 output/ logs/
chown -R $(id -u):$(id -g) output/ logs/

# 或者以 root 用户运行（不推荐）
docker compose exec -u root app chown -R appuser:appuser /app/output /app/logs
```

### 问题 5: 镜像构建失败

**症状**:
```bash
$ docker compose build
ERROR: failed to solve: process "/bin/sh -c pip install ..." did not complete successfully
```

**可能原因**:
- 网络问题
- 依赖包不存在
- Dockerfile 错误

**解决方案**:
```bash
# 查看完整构建日志
docker compose build --progress=plain

# 清理缓存重新构建
docker compose build --no-cache

# 使用国内镜像源（修改 Dockerfile）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 手动构建调试
docker build -t redbookcontentgen:debug . --progress=plain
```

## 最佳实践

### 1. 使用 .env 文件管理配置

```bash
# 开发环境
cp .env.example .env.dev
vim .env.dev

# 测试环境
cp .env.example .env.test
vim .env.test

# 生产环境
cp .env.example .env.prod
vim .env.prod

# 使用指定配置启动
docker compose --env-file .env.dev up -d
```

### 2. 定期备份数据

```bash
# 备份输出目录
tar -czf output-backup-$(date +%Y%m%d).tar.gz output/

# 备份日志目录
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# 备份配置文件
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/ .env
```

### 3. 监控资源使用

```bash
# 实时监控容器资源
docker stats redbookcontentgen

# 查看容器详细信息
docker inspect redbookcontentgen

# 监控健康状态
watch -n 5 'docker compose ps'
```

### 4. 日志管理

```bash
# 定期清理日志
docker compose exec app find /app/logs -name "*.log" -mtime +7 -delete

# 或者使用日志轮转（已在应用中配置）
# 日志文件会自动轮转，保留最近 5 个备份

# 导出日志
docker compose logs > app-logs-$(date +%Y%m%d).log
```

### 5. 安全加固

```bash
# 1. 使用非 root 用户（已在 Dockerfile 中配置）

# 2. 限制容器权限
# 在 docker-compose.yml 中添加：
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp

# 3. 使用密钥管理工具
# 使用 Docker Secrets 或外部密钥管理服务
# 避免在 .env 文件中存储敏感信息

# 4. 定期更新镜像
docker compose pull
docker compose up -d
```

### 6. 性能优化

```bash
# 1. 调整资源限制
# 根据实际负载调整 docker-compose.yml 中的资源配置

# 2. 使用多阶段构建（已在 Dockerfile 中实现）

# 3. 启用缓存
# 确保 CACHE_ENABLED=true

# 4. 优化并发配置
# 调整 RATE_LIMIT_IMAGE_CONCURRENT 参数
```

## 与 Kubernetes 集成

如果需要在 Kubernetes 中部署，可以使用 Kompose 转换 Docker Compose 配置：

```bash
# 安装 Kompose
# macOS
brew install kompose

# Linux
curl -L https://github.com/kubernetes/kompose/releases/download/v1.28.0/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/

# 转换 Docker Compose 配置
kompose convert

# 生成的文件：
# - app-deployment.yaml
# - app-service.yaml
# - redbookcontentgen-network-networkpolicy.yaml

# 部署到 Kubernetes
kubectl apply -f .
```

## 相关文档

- [Dockerfile](../Dockerfile) - Docker 镜像构建配置
- [健康检查文档](./HEALTH_CHECK.md) - 健康检查端点详细说明
- [Docker 测试文档](./DOCKER_TESTING.md) - Docker 镜像测试指南
- [Docker 数据卷配置](./DOCKER_VOLUMES.md) - 数据卷配置详细说明
- [配置文档](./CONFIG.md) - 完整配置说明
- [部署指南](./DEPLOYMENT.md) - 生产环境部署指南

## 更新历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-02-14 | 1.0.0 | 初始版本，创建 Docker Compose 配置和文档 |

## 反馈和贡献

如果您在使用 Docker Compose 时遇到问题或有改进建议，请：

1. 查看[故障排查](#故障排查)章节
2. 查看容器日志：`docker compose logs`
3. 提交 Issue 或 Pull Request

## 许可证

本文档和配置文件遵循项目主许可证。
