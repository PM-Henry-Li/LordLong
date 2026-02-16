# Docker Compose 快速开始指南

## 🚀 5 分钟快速部署

### 前置条件

- Docker 20.10+
- Docker Compose 2.0+

### 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 设置 OPENAI_API_KEY

# 2. 启动服务
docker compose up -d

# 3. 验证服务
curl http://localhost:8080/api/health

# 4. 访问应用
open http://localhost:8080
```

### 常用命令

```bash
# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看状态
docker compose ps
```

## 📖 详细文档

- [Docker Compose 完整指南](docs/DOCKER_COMPOSE.md)
- [健康检查文档](docs/HEALTH_CHECK.md)
- [Docker 测试文档](docs/DOCKER_TESTING.md)

## 🔧 配置说明

### 必需配置

在 `.env` 文件中设置：

```bash
# OpenAI API Key（必填）
OPENAI_API_KEY=sk-your-api-key-here
```

### 可选配置

```bash
# 主机端口（默认：8080）
HOST_PORT=8080

# 图片生成模式（默认：template）
IMAGE_GENERATION_MODE=template

# 模板风格（默认：retro_chinese）
TEMPLATE_STYLE=retro_chinese
```

完整配置选项请参考 [.env.example](.env.example)

## 🧪 测试

```bash
# 运行 Docker Compose 测试
./scripts/test_compose.sh

# 运行 Docker 镜像测试
./scripts/test_docker.sh
```

## 🐛 故障排查

### 问题：端口被占用

```bash
# 使用不同端口
HOST_PORT=9090 docker compose up -d
```

### 问题：健康检查失败

```bash
# 查看日志
docker compose logs app

# 手动测试健康检查
docker compose exec app curl http://localhost:8080/api/health
```

### 问题：环境变量未生效

```bash
# 验证配置
docker compose config

# 查看容器环境变量
docker compose exec app env | grep OPENAI
```

更多故障排查请参考 [Docker Compose 文档](docs/DOCKER_COMPOSE.md#故障排查)

## 📚 相关资源

- [项目主 README](README.md)
- [配置文档](docs/CONFIG.md)
- [API 文档](docs/API_EXAMPLES.md)
- [部署指南](docs/DEPLOYMENT.md)

## 💡 提示

- 使用 `template` 模式无需 API Key 即可生成图片
- 日志文件保存在 `logs/` 目录
- 输出文件保存在 `output/` 目录
- 配置文件位于 `config/` 目录

## 🤝 获取帮助

如有问题，请：

1. 查看[故障排查](#故障排查)章节
2. 查看[完整文档](docs/DOCKER_COMPOSE.md)
3. 提交 Issue

---

**快速链接**：[完整文档](docs/DOCKER_COMPOSE.md) | [配置说明](docs/CONFIG.md) | [API 文档](docs/API_EXAMPLES.md)
