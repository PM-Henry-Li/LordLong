# RedBookContentGen Makefile
# 简化常用 Docker Compose 操作

.PHONY: help build up down restart logs ps test clean

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# 帮助信息
help: ## 显示帮助信息
	@echo "$(BLUE)RedBookContentGen Docker Compose 命令$(NC)"
	@echo ""
	@echo "$(GREEN)可用命令:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)示例:$(NC)"
	@echo "  make setup    # 首次使用，配置环境"
	@echo "  make up       # 启动服务"
	@echo "  make logs     # 查看日志"
	@echo "  make down     # 停止服务"

# 环境配置
setup: ## 配置环境（首次使用）
	@echo "$(BLUE)配置环境...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ 已创建 .env 文件$(NC)"; \
		echo "$(YELLOW)⚠ 请编辑 .env 文件并设置 OPENAI_API_KEY$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env 文件已存在$(NC)"; \
	fi
	@if [ ! -f config/config.json ]; then \
		cp config/config.example.json config/config.json; \
		echo "$(GREEN)✓ 已创建 config/config.json 文件$(NC)"; \
	else \
		echo "$(YELLOW)⚠ config/config.json 文件已存在$(NC)"; \
	fi
	@echo "$(GREEN)✓ 环境配置完成$(NC)"

# 构建镜像
build: ## 构建 Docker 镜像
	@echo "$(BLUE)构建镜像...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ 镜像构建完成$(NC)"

# 启动服务
up: ## 启动服务（后台运行）
	@echo "$(BLUE)启动服务...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ 服务已启动$(NC)"
	@echo "$(YELLOW)访问地址: http://localhost:8080$(NC)"

# 启动服务（前台）
up-fg: ## 启动服务（前台运行，查看日志）
	@echo "$(BLUE)启动服务（前台）...$(NC)"
	docker compose up

# 停止服务
down: ## 停止并删除容器
	@echo "$(BLUE)停止服务...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ 服务已停止$(NC)"

# 停止服务（保留数据）
stop: ## 停止服务（保留容器）
	@echo "$(BLUE)停止服务...$(NC)"
	docker compose stop
	@echo "$(GREEN)✓ 服务已停止$(NC)"

# 启动已停止的服务
start: ## 启动已停止的服务
	@echo "$(BLUE)启动服务...$(NC)"
	docker compose start
	@echo "$(GREEN)✓ 服务已启动$(NC)"

# 重启服务
restart: ## 重启服务
	@echo "$(BLUE)重启服务...$(NC)"
	docker compose restart
	@echo "$(GREEN)✓ 服务已重启$(NC)"

# 查看日志
logs: ## 查看服务日志
	docker compose logs -f

# 查看最近日志
logs-tail: ## 查看最近 100 行日志
	docker compose logs --tail=100

# 查看容器状态
ps: ## 查看容器状态
	docker compose ps

# 进入容器
shell: ## 进入容器 Shell
	docker compose exec app /bin/bash

# 健康检查
health: ## 检查服务健康状态
	@echo "$(BLUE)检查服务健康状态...$(NC)"
	@curl -sf http://localhost:8080/api/health | python -m json.tool || echo "$(YELLOW)⚠ 服务未响应$(NC)"

# 运行测试
test: ## 运行 Docker Compose 测试
	@echo "$(BLUE)运行测试...$(NC)"
	./scripts/test_compose.sh

# 运行 Docker 镜像测试
test-docker: ## 运行 Docker 镜像测试
	@echo "$(BLUE)运行 Docker 镜像测试...$(NC)"
	./scripts/test_docker.sh

# 运行数据卷测试
test-volumes: ## 运行数据卷测试
	@echo "$(BLUE)运行数据卷测试...$(NC)"
	./scripts/test_volumes.sh

# 清理资源
clean: ## 清理所有容器、镜像和数据卷
	@echo "$(BLUE)清理资源...$(NC)"
	docker compose down -v --rmi all
	@echo "$(GREEN)✓ 资源清理完成$(NC)"

# 查看配置
config: ## 查看 Docker Compose 配置
	docker compose config

# 重新构建并启动
rebuild: ## 重新构建镜像并启动服务
	@echo "$(BLUE)重新构建并启动...$(NC)"
	docker compose up -d --build
	@echo "$(GREEN)✓ 服务已启动$(NC)"

# 查看资源使用
stats: ## 查看容器资源使用情况
	docker stats redbookcontentgen

# 导出日志
export-logs: ## 导出日志到文件
	@echo "$(BLUE)导出日志...$(NC)"
	@mkdir -p logs/exports
	docker compose logs > logs/exports/docker-logs-$$(date +%Y%m%d-%H%M%S).log
	@echo "$(GREEN)✓ 日志已导出到 logs/exports/$(NC)"

# 备份数据
backup: ## 备份输出和日志数据
	@echo "$(BLUE)备份数据...$(NC)"
	@mkdir -p backups
	tar -czf backups/backup-$$(date +%Y%m%d-%H%M%S).tar.gz output/ logs/ config/config.json .env 2>/dev/null || true
	@echo "$(GREEN)✓ 数据已备份到 backups/$(NC)"

# 更新镜像
update: ## 更新镜像并重启服务
	@echo "$(BLUE)更新镜像...$(NC)"
	docker compose pull
	docker compose up -d
	@echo "$(GREEN)✓ 镜像已更新$(NC)"
