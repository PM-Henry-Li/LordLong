# Docker 数据卷配置说明

## 概述

RedBookContentGen 使用 Docker 数据卷来持久化数据和配置。本文档详细说明了数据卷的配置方式、使用场景和最佳实践。

## 当前配置

### 主机目录挂载（默认方案）

当前 `docker-compose.yml` 使用**主机目录挂载**方式，将主机目录直接映射到容器内：

```yaml
volumes:
  # 配置文件（只读挂载，防止容器内修改）
  - ./config:/app/config:ro
  
  # 输入文件目录
  - ./input:/app/input:rw
  
  # 输出目录（生成的内容和图片）
  - ./output:/app/output:rw
  
  # 日志目录（应用日志）
  - ./logs:/app/logs:rw
  
  # 可选：缓存目录（如果启用文件缓存）
  # - ./cache:/app/cache:rw
```

## 数据卷说明

### 1. 配置卷 (`./config:/app/config:ro`)

**用途**: 存储应用配置文件

**挂载模式**: 只读 (`:ro`)

**包含文件**:
- `config.json` - 主配置文件（gitignored，包含 API Key）
- `config.example.json` - 配置模板

**注意事项**:
- ⚠️ 使用只读挂载，防止容器内意外修改配置
- ⚠️ `config.json` 包含敏感信息，不要提交到 Git
- ✅ 修改配置后需要重启容器生效

**示例**:
```bash
# 修改配置
vim config/config.json

# 重启容器使配置生效
docker-compose restart
```

### 2. 输入卷 (`./input:/app/input:rw`)

**用途**: 存储待处理的输入文件

**挂载模式**: 读写 (`:rw`)

**包含文件**:
- `input_content.txt` - 输入文本内容

**使用方法**:
```bash
# 1. 将输入文件放入 input 目录
echo "老北京胡同的故事..." > input/input_content.txt

# 2. 运行容器生成内容
docker-compose up
```

### 3. 输出卷 (`./output:/app/output:rw`)

**用途**: 存储生成的内容和图片

**挂载模式**: 读写 (`:rw`)

**目录结构**:
```
output/
├── redbook_content.xlsx          # 生成的内容表格
└── images/                       # 生成的图片
    └── YYYYMMDD/                 # 按日期分组
        ├── image_1.jpg
        ├── image_2.jpg
        └── ...
```

**访问方式**:
```bash
# 直接在主机上访问生成的文件
ls -lh output/images/$(date +%Y%m%d)/

# 打开生成的 Excel 文件
open output/redbook_content.xlsx  # macOS
xdg-open output/redbook_content.xlsx  # Linux
```

### 4. 日志卷 (`./logs:/app/logs:rw`)

**用途**: 存储应用日志

**挂载模式**: 读写 (`:rw`)

**日志文件**:
- `app.log` - 应用主日志（JSON 格式）
- `app.log.1`, `app.log.2`, ... - 轮转的历史日志

**日志轮转配置**:
- 单个日志文件最大 10MB
- 保留最近 5 个日志文件
- 总大小约 50MB

**查看日志**:
```bash
# 查看最新日志
tail -f logs/app.log

# 查看 JSON 格式日志（美化输出）
tail -f logs/app.log | jq '.'

# 搜索错误日志
grep '"level":"ERROR"' logs/app.log | jq '.'

# 查看容器日志（标准输出）
docker-compose logs -f app
```

### 5. 缓存卷 (`./cache:/app/cache:rw`) - 可选

**用途**: 存储缓存数据（如果启用文件缓存）

**挂载模式**: 读写 (`:rw`)

**启用方法**:
1. 在 `docker-compose.yml` 中取消注释缓存卷配置
2. 在 `config.json` 中启用文件缓存：
   ```json
   {
     "cache": {
       "enabled": true,
       "backend": "file",
       "file_cache_dir": "/app/cache"
     }
   }
   ```

**清理缓存**:
```bash
# 清理所有缓存
rm -rf cache/*

# 清理过期缓存（保留最近 7 天）
find cache/ -type f -mtime +7 -delete
```

## 挂载模式说明

### 只读挂载 (`:ro`)

**用途**: 防止容器内修改主机文件

**适用场景**:
- 配置文件
- 静态资源
- 模板文件

**示例**:
```yaml
volumes:
  - ./config:/app/config:ro  # 只读
```

### 读写挂载 (`:rw`)

**用途**: 允许容器读写主机文件

**适用场景**:
- 输出目录
- 日志目录
- 缓存目录

**示例**:
```yaml
volumes:
  - ./output:/app/output:rw  # 读写（默认）
```

## 主机目录 vs 命名卷

### 主机目录挂载（当前方案）

**优势**:
- ✅ 直接访问文件，无需 Docker 命令
- ✅ 备份简单（直接复制目录）
- ✅ 便于开发和调试
- ✅ 配置文件可以手动编辑
- ✅ 适合单机部署

**劣势**:
- ⚠️ 路径依赖主机文件系统
- ⚠️ 跨平台可能有权限问题
- ⚠️ 性能依赖主机文件系统

**适用场景**:
- 开发环境
- 单机部署
- 需要频繁访问文件的场景

### 命名卷

**优势**:
- ✅ Docker 管理，跨平台兼容
- ✅ 性能优化的存储驱动
- ✅ 适合生产环境
- ✅ 支持远程存储驱动

**劣势**:
- ❌ 访问文件需要 Docker 命令
- ❌ 备份相对复杂
- ❌ 不便于直接编辑

**适用场景**:
- 生产环境
- 集群部署
- 需要高性能存储的场景

## 切换到命名卷（可选）

如果需要在生产环境使用命名卷，可以按以下步骤操作：

### 1. 修改 docker-compose.yml

```yaml
services:
  app:
    volumes:
      # 使用命名卷
      - config:/app/config:ro
      - input:/app/input:rw
      - output:/app/output:rw
      - logs:/app/logs:rw

# 定义命名卷
volumes:
  config:
    driver: local
  input:
    driver: local
  output:
    driver: local
  logs:
    driver: local
```

### 2. 迁移现有数据

```bash
# 停止容器
docker-compose down

# 创建命名卷
docker volume create redbookcontentgen_config
docker volume create redbookcontentgen_input
docker volume create redbookcontentgen_output
docker volume create redbookcontentgen_logs

# 复制数据到命名卷
docker run --rm -v $(pwd)/config:/source -v redbookcontentgen_config:/dest alpine cp -r /source/. /dest/
docker run --rm -v $(pwd)/input:/source -v redbookcontentgen_input:/dest alpine cp -r /source/. /dest/
docker run --rm -v $(pwd)/output:/source -v redbookcontentgen_output:/dest alpine cp -r /source/. /dest/
docker run --rm -v $(pwd)/logs:/source -v redbookcontentgen_logs:/dest alpine cp -r /source/. /dest/

# 启动容器
docker-compose up -d
```

### 3. 访问命名卷数据

```bash
# 查看卷信息
docker volume inspect redbookcontentgen_output

# 访问卷内文件（使用临时容器）
docker run --rm -v redbookcontentgen_output:/data alpine ls -lh /data

# 复制文件到主机
docker run --rm -v redbookcontentgen_output:/data -v $(pwd):/backup alpine cp -r /data/. /backup/output_backup/
```

## 数据备份

### 主机目录挂载备份

```bash
# 备份所有数据
tar -czf backup_$(date +%Y%m%d).tar.gz config/ input/ output/ logs/

# 恢复数据
tar -xzf backup_20260214.tar.gz
```

### 命名卷备份

```bash
# 备份单个卷
docker run --rm -v redbookcontentgen_output:/data -v $(pwd):/backup alpine tar -czf /backup/output_backup.tar.gz -C /data .

# 恢复卷
docker run --rm -v redbookcontentgen_output:/data -v $(pwd):/backup alpine tar -xzf /backup/output_backup.tar.gz -C /data
```

## 权限问题

### Linux 权限问题

容器内应用以 `root` 用户运行，可能导致生成的文件权限问题。

**解决方案 1**: 修改 Dockerfile，使用非 root 用户

```dockerfile
# 创建应用用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换到应用用户
USER appuser
```

**解决方案 2**: 修改主机目录权限

```bash
# 修改输出目录权限
sudo chown -R $USER:$USER output/ logs/

# 或者使用 chmod
chmod -R 755 output/ logs/
```

### macOS/Windows 权限

macOS 和 Windows 的 Docker Desktop 会自动处理权限映射，通常不需要额外配置。

## 磁盘空间管理

### 监控磁盘使用

```bash
# 查看目录大小
du -sh output/ logs/ cache/

# 查看 Docker 卷使用情况
docker system df -v
```

### 清理策略

```bash
# 清理旧的输出文件（保留最近 30 天）
find output/images/ -type d -mtime +30 -exec rm -rf {} +

# 清理旧的日志文件（保留最近 7 天）
find logs/ -name "*.log.*" -mtime +7 -delete

# 清理缓存
rm -rf cache/*

# 清理 Docker 未使用的卷
docker volume prune
```

## 最佳实践

### 1. 定期备份

```bash
# 创建每日备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d)

# 备份输出和配置
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" config/ output/

# 保留最近 7 天的备份
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到 crontab（每天凌晨 2 点执行）
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### 2. 监控磁盘空间

```bash
# 创建磁盘监控脚本
cat > check_disk.sh << 'EOF'
#!/bin/bash
THRESHOLD=80  # 磁盘使用率阈值

USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "警告：磁盘使用率 ${USAGE}% 超过阈值 ${THRESHOLD}%"
    # 可以添加告警通知
fi
EOF

chmod +x check_disk.sh
```

### 3. 日志轮转

日志轮转已在应用中配置（`src/core/logger.py`），无需额外配置。

如果需要更激进的清理策略，可以使用 `logrotate`：

```bash
# 创建 logrotate 配置
cat > /etc/logrotate.d/redbookcontentgen << 'EOF'
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### 4. 配置文件安全

```bash
# 确保配置文件权限正确
chmod 600 config/config.json

# 不要提交到 Git
echo "config/config.json" >> .gitignore
```

## 故障排查

### 问题 1: 容器无法写入文件

**症状**: 容器日志显示权限错误

**解决方案**:
```bash
# 检查目录权限
ls -ld output/ logs/

# 修改权限
chmod -R 755 output/ logs/

# 或者修改所有者
sudo chown -R $USER:$USER output/ logs/
```

### 问题 2: 磁盘空间不足

**症状**: 容器无法写入文件，日志显示 "No space left on device"

**解决方案**:
```bash
# 检查磁盘使用情况
df -h

# 清理旧文件
find output/images/ -type d -mtime +30 -exec rm -rf {} +
find logs/ -name "*.log.*" -mtime +7 -delete

# 清理 Docker 资源
docker system prune -a
```

### 问题 3: 配置文件修改不生效

**症状**: 修改 `config.json` 后容器行为未改变

**解决方案**:
```bash
# 重启容器
docker-compose restart

# 或者重新创建容器
docker-compose down
docker-compose up -d
```

### 问题 4: 找不到输出文件

**症状**: 容器运行成功但主机上找不到输出文件

**解决方案**:
```bash
# 检查卷挂载
docker-compose config | grep -A 5 volumes

# 检查容器内文件
docker-compose exec app ls -lh /app/output

# 检查主机目录
ls -lh output/
```

## 参考资料

- [Docker Volumes 官方文档](https://docs.docker.com/storage/volumes/)
- [Docker Compose Volumes 配置](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)
- [Docker 数据管理最佳实践](https://docs.docker.com/storage/)

## 相关文档

- [Docker 部署指南](DOCKER_COMPOSE.md)
- [配置管理文档](CONFIG.md)
- [日志系统文档](LOGGER.md)

---

**最后更新**: 2026-02-14  
**文档版本**: v1.0
