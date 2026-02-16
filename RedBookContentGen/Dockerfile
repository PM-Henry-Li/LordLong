# RedBookContentGen Dockerfile
# 基于 Python 3.10 slim 镜像构建，优化镜像大小

# ============================================
# 阶段 1: 构建阶段 - 安装依赖
# ============================================
FROM python:3.10-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖（仅在需要编译 Python 包时使用）
# 换源（针对中国大陆网络优化）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到用户目录（避免污染系统 Python）
# 使用 --no-cache-dir 避免缓存 pip 包
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# 阶段 2: 最终镜像 - 运行时环境
# ============================================
FROM python:3.10-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 设置工作目录
WORKDIR /app

# 安装运行时依赖（合并到单个 RUN 指令减少层数）
# 使用 --no-install-recommends 避免安装推荐包
# 清理 apt 缓存和临时文件以减小镜像大小
# 换源（针对中国大陆网络优化）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 中文字体支持（只保留一个字体包以减小体积）
    fonts-wqy-microhei \
    # 健康检查和调试工具
    curl \
    # 清理 apt 缓存、列表和临时文件
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# 创建非 root 用户（安全最佳实践）
# 必须先创建用户，才能在 COPY 时使用chown
RUN useradd -m -u 1000 appuser

# 从构建阶段复制已安装的 Python 包到 appuser 的目录
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# 创建必要的目录并设置权限
RUN mkdir -p logs output input config && \
    chown -R appuser:appuser /app

# 复制应用代码（放在后面以利用 Docker 缓存）
# 只复制必要的文件，其他文件通过 .dockerignore 排除
COPY --chown=appuser:appuser . .

# 切换到非 root 用户
USER appuser

# 暴露端口（Flask 默认端口）
EXPOSE 8080

# 健康检查
# 配置说明：
# - interval: 每 30 秒检查一次
# - timeout: 单次检查超时时间 3 秒
# - start-period: 容器启动后等待 40 秒再开始检查（给应用足够的启动时间）
# - retries: 连续失败 3 次后标记为不健康
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# 启动命令（使用 gunicorn 生产级服务器）
# -w 4: 4个工作进程
# -k gevent: 使用 gevent 异步模式
# --timeout 120: 超时时间120秒（AI生成可能耗时）
CMD ["gunicorn", "-w", "4", "-k", "gevent", "--timeout", "120", "-b", "0.0.0.0:8080", "web_app:app"]
