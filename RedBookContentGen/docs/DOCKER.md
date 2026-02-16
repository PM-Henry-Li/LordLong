# Docker 部署指南

本文档介绍如何使用 Docker 容器化部署 RedBookContentGen 项目。

## 目录

- [快速开始](#快速开始)
- [构建镜像](#构建镜像)
- [运行容器](#运行容器)
- [环境变量配置](#环境变量配置)
- [数据持久化](#数据持久化)
- [健康检查](#健康检查)
- [镜像优化](#镜像优化)
- [故障排查](#故障排查)

## 快速开始

### 前提条件

- Docker 20.10 或更高版本
- Docker Compose 2.0 或更高版本（可选）

### 一键启动

```bash
# 1. 构建镜像
docker build -t redbookcontentgen:latest .

# 2. 运行容器
docker run -d \
  --name redbookcontentgen \
  -p 8080:8080 \
  -e OPENAI_API_KEY="your-api-key-here" \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  redbookcontentgen:latest
```

## 构建镜像

### 基础构建

```bash
docker build -t redbookcontentgen:latest .
```

### 指定版本标签

```bash
docker build -t redbookcontentgen:v1.0.0 .
```

### 使用构建参数

```bash
# 指定 Python 版本
docker build --build-arg PYTHON_VERSION=3.10 -t redbookcontentgen:latest .
```

### 查看镜像信息

```bash
# 查看镜像列表
docker images redbookcontentgen

# 查看镜像详细信息
docker inspect redbookcontentgen:latest

# 查看镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" redbookcontentgen
```

## 运行容器

### 基础运行

```bash
docker run -d \
  --name redbookcontentgen \
  -p 8080:8080 \
  -e OPENAI_API_KEY="sk-your-api-key" \
  redbookcontentgen:latest
```

### 完整配置运行

```bash
docker run -d \
  --name redbookcontentgen \
  --restart unless-stopped \
  -p 8080:8080 \
  -e OPENAI_API_KEY="sk-your-api-key" \
  -e OPENAI_MODEL="qwen-plus" \
  -e RATE_LIMIT_OPENAI_RPM="60" \
  -e LOG_LEVEL="INFO" \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/input:/app/input \
  --memory="2g" \
  --cpus="2" \
  redbookcontentgen:latest
```

### 交互式运行（调试）

```bash
docker run -it --rm \
  --name redbookcontentgen-debug \
  -p 8080:8080 \
  -e OPENAI_API_KEY="sk-your-api-key" \
  -v $(pwd)/config:/app/config \
  redbookcontentgen:latest \
  /bin/bash
```

## 环境变量配置

### 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-xxx` 或 `dashscope-xxx` |

### 可选的环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_MODEL` | OpenAI 模型名称 | `qwen-plus` |
| `OPENAI_BASE_URL` | OpenAI API 基础 URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `RATE_LIMIT_OPENAI_RPM` | OpenAI API 速率限制（每分钟请求数） | `60` |
| `RATE_LIMIT_IMAGE_RPM` | 图片生成 API 速率限制 | `10` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `CACHE_ENABLED` | 是否启用缓存 | `true` |
| `CACHE_TTL` | 缓存过期时间（秒） | `3600` |

### 使用 .env 文件

创建 `.env` 文件：

```bash
# API 配置
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=qwen-plus

# 速率限制
RATE_LIMIT_OPENAI_RPM=60
RATE_LIMIT_IMAGE_RPM=10

# 日志配置
LOG_LEVEL=INFO

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=3600
```

使用 .env 文件运行：

```bash
docker run -d \
  --name redbookcontentgen \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/output:/app/output \
  redbookcontentgen:latest
```

## 数据持久化

### 推荐的卷挂载

```bash
docker run -d \
  --name redbookcontentgen \
  -p 8080:8080 \
  -e OPENAI_API_KEY="sk-your-api-key" \
  # 配置文件（只读）
  -v $(pwd)/config:/app/config:ro \
  # 输出目录（读写）
  -v $(pwd)/output:/app/output \
  # 日志目录（读写）
  -v $(pwd)/logs:/app/logs \
  # 输入目录（只读）
  -v $(pwd)/input:/app/input:ro \
  redbookcontentgen:latest
```

### 使用 Docker 卷

```bash
# 创建命名卷
docker volume create redbookcontentgen-output
docker volume create redbookcontentgen-logs

# 使用命名卷运行
docker run -d \
  --name redbookcontentgen \
  -p 8080:8080 \
  -e OPENAI_API_KEY="sk-your-api-key" \
  -v redbookcontentgen-output:/app/output \
  -v redbookcontentgen-logs:/app/logs \
  redbookcontentgen:latest
```

## 健康检查

### 查看容器健康状态

```bash
# 查看容器状态
docker ps

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' redbookcontentgen | jq
```

### 手动健康检查

```bash
# 进入容器
docker exec -it redbookcontentgen /bin/bash

# 检查健康端点
curl http://localhost:8080/health
```

### 健康检查配置

Dockerfile 中的健康检查配置：

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
```

参数说明：
- `--interval=30s`: 每 30 秒检查一次
- `--timeout=3s`: 检查超时时间 3 秒
- `--start-period=40s`: 启动后 40 秒开始检查
- `--retries=3`: 失败 3 次后标记为不健康

## 镜像优化

本项目的 Docker 镜像已经过优化，实现了以下措施：

### 优化措施

✅ **多阶段构建** - 分离构建和运行环境，减少最终镜像大小  
✅ **Slim 基础镜像** - 使用 `python:3.10-slim`，相比完整镜像减少约 795MB  
✅ **清理缓存** - 清理 apt 和 pip 缓存，减少约 80-180MB  
✅ **减少依赖** - 只安装必要的运行时依赖  
✅ **合并指令** - 减少镜像层数 30-40%  
✅ **.dockerignore** - 减少构建上下文大小  

### 优化效果

- **镜像大小**: 约 400-600MB（相比未优化版本减少 70-80%）
- **构建时间**: 2-5 分钟（提升 40-60%）
- **层数**: 减少 30-40%

### 详细说明

查看完整的优化说明和验证方法：[Docker 镜像优化文档](DOCKER_OPTIMIZATION.md)

### 验证优化效果

运行验证脚本：

```bash
./scripts/verify_docker_optimization.sh
```

该脚本会自动：
- 构建优化后的镜像
- 分析镜像大小和层数
- 对比基础镜像
- 验证所有优化措施
- 测试镜像运行

### 查看镜像信息

```bash
# 查看镜像大小
docker images redbookcontentgen:latest

# 查看镜像层
docker history redbookcontentgen:latest

# 查看镜像详细信息
docker inspect redbookcontentgen:latest
```

### 清理未使用的镜像

```bash
# 清理悬空镜像
docker image prune

# 清理所有未使用的镜像
docker image prune -a
```

## 安全建议

1. **不要在镜像中包含敏感信息**
   - 使用环境变量传递 API Key
   - 不要将 `config/config.json` 打包到镜像中
   - 使用 `.dockerignore` 排除敏感文件

2. **使用非 root 用户运行**
   - Dockerfile 已配置使用 `appuser` 用户（UID 1000）
   - 提高容器安全性，减少攻击面

3. **限制容器资源**
   - 使用 `--memory` 限制内存使用（推荐 2GB）
   - 使用 `--cpus` 限制 CPU 使用（推荐 2 核）
   - 防止资源耗尽影响宿主机

4. **定期更新基础镜像**
   - 定期重新构建镜像以获取安全更新
   - 关注 Python 官方镜像的安全公告
   - 使用 `docker pull python:3.10-slim` 更新基础镜像

5. **使用只读卷**
   - 对不需要写入的目录使用 `:ro` 标记
   - 例如：`-v $(pwd)/config:/app/config:ro`
   - 防止容器内进程修改配置文件

6. **网络隔离**
   - 使用 Docker 网络隔离容器
   - 只暴露必要的端口
   - 考虑使用反向代理（Nginx）

## 容器管理

### 查看日志

```bash
# 查看实时日志
docker logs -f redbookcontentgen

# 查看最近 100 行日志
docker logs --tail 100 redbookcontentgen

# 查看带时间戳的日志
docker logs -t redbookcontentgen
```

### 停止和启动

```bash
# 停止容器
docker stop redbookcontentgen

# 启动容器
docker start redbookcontentgen

# 重启容器
docker restart redbookcontentgen
```

### 删除容器

```bash
# 停止并删除容器
docker stop redbookcontentgen
docker rm redbookcontentgen

# 强制删除运行中的容器
docker rm -f redbookcontentgen
```

### 进入容器

```bash
# 使用 bash
docker exec -it redbookcontentgen /bin/bash

# 使用 sh（如果 bash 不可用）
docker exec -it redbookcontentgen /bin/sh

# 执行单个命令
docker exec redbookcontentgen ls -la /app
```

## 故障排查

### 容器无法启动

1. 检查日志：
```bash
docker logs redbookcontentgen
```

2. 检查环境变量：
```bash
docker inspect redbookcontentgen | jq '.[0].Config.Env'
```

3. 检查端口占用：
```bash
# Linux/Mac
lsof -i :8080

# Windows
netstat -ano | findstr :8080
```

### API 调用失败

1. 检查 API Key 配置：
```bash
docker exec redbookcontentgen env | grep OPENAI_API_KEY
```

2. 检查网络连接：
```bash
docker exec redbookcontentgen curl -I https://dashscope.aliyuncs.com
```

3. 查看应用日志：
```bash
docker exec redbookcontentgen cat logs/app.log
```

### 性能问题

1. 查看资源使用：
```bash
docker stats redbookcontentgen
```

2. 限制资源使用：
```bash
docker update --memory="2g" --cpus="2" redbookcontentgen
```

### 权限问题

如果遇到文件权限问题，检查卷挂载的权限：

```bash
# 查看容器内文件权限
docker exec redbookcontentgen ls -la /app

# 修改宿主机目录权限
chmod -R 755 output logs
chown -R 1000:1000 output logs
```

## 镜像优化

本项目的 Docker 镜像已经过优化，实现了以下措施：

### 优化措施

✅ **多阶段构建** - 分离构建和运行环境，减少最终镜像大小  
✅ **Slim 基础镜像** - 使用 `python:3.10-slim`，相比完整镜像减少约 795MB  
✅ **清理缓存** - 清理 apt 和 pip 缓存，减少约 80-180MB  
✅ **减少依赖** - 只安装必要的运行时依赖  
✅ **合并指令** - 减少镜像层数 30-40%  
✅ **.dockerignore** - 减少构建上下文大小  

### 优化效果

- **镜像大小**: 约 400-600MB（相比未优化版本减少 70-80%）
- **构建时间**: 2-5 分钟（提升 40-60%）
- **层数**: 减少 30-40%

### 详细说明

查看完整的优化说明和验证方法：[Docker 镜像优化文档](DOCKER_OPTIMIZATION.md)

### 验证优化效果

运行验证脚本：

```bash
./scripts/verify_docker_optimization.sh
```

该脚本会自动：
- 构建优化后的镜像
- 分析镜像大小和层数
- 对比基础镜像
- 验证所有优化措施
- 测试镜像运行

### 查看镜像层

```bash
docker history redbookcontentgen:latest
```

### 清理未使用的镜像

```bash
# 清理悬空镜像
docker image prune

# 清理所有未使用的镜像
docker image prune -a
```

### 导出和导入镜像

```bash
# 导出镜像
docker save -o redbookcontentgen.tar redbookcontentgen:latest

# 导入镜像
docker load -i redbookcontentgen.tar
```

## 故障排查

1. **不要在镜像中包含敏感信息**
   - 使用环境变量传递 API Key
   - 不要将 `config/config.json` 打包到镜像中

2. **使用非 root 用户运行**
   - Dockerfile 已配置使用 `appuser` 用户

3. **限制容器资源**
   - 使用 `--memory` 和 `--cpus` 限制资源使用

4. **定期更新基础镜像**
   - 定期重新构建镜像以获取安全更新

5. **使用只读卷**
   - 对不需要写入的目录使用 `:ro` 标记

## 生产环境部署

### 使用 Docker Compose

参考 `docker-compose.yml` 文件进行部署。

### 使用反向代理

推荐使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 配置 HTTPS

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com
```

## 参考资料

- [Docker 官方文档](https://docs.docker.com/)
- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Python Docker 镜像](https://hub.docker.com/_/python)
- [项目配置文档](CONFIG.md)

---

**最后更新**: 2026-02-14  
**文档版本**: v1.0
