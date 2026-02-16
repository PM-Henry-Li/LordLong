# 健康检查配置文档

## 概述

本文档描述了 RedBookContentGen 项目的健康检查功能，包括端点配置、Docker 健康检查和监控集成。

## 健康检查端点

### 端点信息

- **路径**: `/api/health`
- **方法**: `GET`
- **用途**: 用于 Docker 健康检查、负载均衡器和监控系统

### 响应格式

#### 成功响应 (200 OK)

```json
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

#### 失败响应 (503 Service Unavailable)

```json
{
  "status": "unhealthy",
  "timestamp": "2026-02-14T10:30:00.000000",
  "version": "1.0.0",
  "services": {
    "content_service": "unavailable",
    "image_service": "ok"
  }
}
```

#### 异常响应 (503 Service Unavailable)

```json
{
  "status": "unhealthy",
  "timestamp": "2026-02-14T10:30:00.000000",
  "version": "1.0.0",
  "error": "错误详细信息"
}
```

### 状态码说明

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 200 | 服务健康 | 所有服务正常运行 |
| 503 | 服务不可用 | 一个或多个服务不可用，或发生异常 |

### 检查逻辑

健康检查端点会验证以下服务：

1. **内容生成服务** (`content_service`)
   - 检查服务实例是否存在
   - 状态：`ok` 或 `unavailable`

2. **图片生成服务** (`image_service`)
   - 检查服务实例是否存在
   - 状态：`ok` 或 `unavailable`

如果任何服务不可用，端点返回 503 状态码。

## Docker 健康检查配置

### Dockerfile 配置

```dockerfile
# 健康检查
# 配置说明：
# - interval: 每 30 秒检查一次
# - timeout: 单次检查超时时间 3 秒
# - start-period: 容器启动后等待 40 秒再开始检查（给应用足够的启动时间）
# - retries: 连续失败 3 次后标记为不健康
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1
```

### 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--interval` | 30s | 健康检查间隔时间 |
| `--timeout` | 3s | 单次检查超时时间 |
| `--start-period` | 40s | 容器启动后的宽限期 |
| `--retries` | 3 | 连续失败次数阈值 |

### 检查流程

1. **启动阶段** (0-40秒)
   - 容器启动后等待 40 秒
   - 此期间的失败不计入重试次数
   - 给应用足够的初始化时间

2. **正常检查** (40秒后)
   - 每 30 秒执行一次健康检查
   - 使用 `curl -f` 请求 `/api/health` 端点
   - 超时时间为 3 秒

3. **失败处理**
   - 连续失败 3 次后标记为不健康
   - Docker 会将容器状态设置为 `unhealthy`
   - 可以配合重启策略自动恢复

## 使用示例

### 本地测试

```bash
# 启动应用
python web_app.py

# 测试健康检查端点
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

### Docker 容器测试

```bash
# 构建镜像
docker build -t redbookcontentgen .

# 运行容器
docker run -d --name rbcg -p 8080:8080 redbookcontentgen

# 查看容器健康状态
docker ps
# 输出示例：
# CONTAINER ID   IMAGE               STATUS                    PORTS
# abc123def456   redbookcontentgen   Up 2 minutes (healthy)    0.0.0.0:8080->8080/tcp

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' rbcg | jq

# 手动触发健康检查
docker exec rbcg curl -f http://localhost:8080/api/health
```

### Docker Compose 配置

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 3s
      start_period: 40s
      retries: 3
    restart: unless-stopped
```

## 监控集成

### Prometheus 监控

可以使用 Prometheus 的 `blackbox_exporter` 监控健康检查端点：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'redbookcontentgen_health'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://localhost:8080/api/health
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

### Kubernetes 健康检查

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: redbookcontentgen
spec:
  containers:
  - name: app
    image: redbookcontentgen:latest
    ports:
    - containerPort: 8080
    livenessProbe:
      httpGet:
        path: /api/health
        port: 8080
      initialDelaySeconds: 40
      periodSeconds: 30
      timeoutSeconds: 3
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /api/health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 3
```

### 负载均衡器配置

#### Nginx

```nginx
upstream redbookcontentgen {
    server localhost:8080 max_fails=3 fail_timeout=30s;
    
    # 健康检查（需要 nginx-plus 或第三方模块）
    check interval=30000 rise=2 fall=3 timeout=3000 type=http;
    check_http_send "GET /api/health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

#### HAProxy

```haproxy
backend redbookcontentgen
    option httpchk GET /api/health
    http-check expect status 200
    server app1 localhost:8080 check inter 30s fall 3 rise 2
```

## 故障排查

### 健康检查失败

#### 问题：容器标记为 unhealthy

**可能原因**：
1. 应用启动时间过长
2. 服务初始化失败
3. 网络问题
4. 资源不足

**排查步骤**：

```bash
# 1. 查看容器日志
docker logs rbcg

# 2. 查看健康检查历史
docker inspect --format='{{json .State.Health}}' rbcg | jq

# 3. 手动测试健康检查
docker exec rbcg curl -v http://localhost:8080/api/health

# 4. 检查应用进程
docker exec rbcg ps aux

# 5. 检查端口监听
docker exec rbcg netstat -tlnp
```

**解决方案**：

1. **增加启动宽限期**
   ```dockerfile
   HEALTHCHECK --start-period=60s ...
   ```

2. **调整检查间隔**
   ```dockerfile
   HEALTHCHECK --interval=60s ...
   ```

3. **增加重试次数**
   ```dockerfile
   HEALTHCHECK --retries=5 ...
   ```

### 服务不可用

#### 问题：健康检查返回 503

**可能原因**：
1. 配置管理器初始化失败
2. 服务依赖缺失
3. API Key 配置错误

**排查步骤**：

```bash
# 1. 检查环境变量
docker exec rbcg env | grep OPENAI

# 2. 检查配置文件
docker exec rbcg cat config/config.json

# 3. 查看应用日志
docker logs rbcg --tail 100

# 4. 测试服务端点
curl http://localhost:8080/api/health
```

**解决方案**：

1. **检查配置**
   - 确保 `config/config.json` 存在
   - 验证 API Key 配置正确

2. **检查依赖**
   - 确保所有 Python 依赖已安装
   - 验证字体文件存在

3. **重启容器**
   ```bash
   docker restart rbcg
   ```

## 最佳实践

### 1. 合理设置检查参数

- **启动宽限期**：根据应用启动时间设置，建议 30-60 秒
- **检查间隔**：平衡监控精度和系统负载，建议 30-60 秒
- **超时时间**：考虑网络延迟，建议 3-5 秒
- **重试次数**：避免误报，建议 3-5 次

### 2. 监控健康检查状态

- 定期查看容器健康状态
- 配置告警通知
- 记录健康检查历史

### 3. 结合重启策略

```yaml
services:
  app:
    restart: unless-stopped
    healthcheck:
      # ... 健康检查配置
```

### 4. 日志记录

健康检查端点的访问会记录在应用日志中，可以通过日志查询接口查看：

```bash
# 查询健康检查日志
curl "http://localhost:8080/api/logs/search?keyword=health&page=1&page_size=20"
```

## 相关文档

- [Docker 健康检查官方文档](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Kubernetes 健康检查](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [API 文档](./API_EXAMPLES.md)
- [部署指南](./DEPLOYMENT.md)

## 更新历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-02-14 | 1.0.0 | 初始版本，添加健康检查端点和 Docker 配置 |
