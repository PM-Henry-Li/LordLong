# 部署指南 - 阿里云 ECS (CentOS 7)

本指南针对您的 **CentOS 7** 系统环境，详细说明如何部署 **RedBookContentGen** 项目。

## 📋 准备工作

### 1. 确认系统环境
根据您提供的信息，您的系统为：
*   **OS**: CentOS Linux 7 (Core)
*   **Kernel**: Linux 3.10.0-xxx

### 2. 安全组设置
登录阿里云控制台，确保ECS实例的安全组开放以下端口：
*   `22` (SSH)
*   `80` (HTTP, Nginx默认端口)
*   `443` (HTTPS, Nginx默认端口)
*   `8080` (应用默认端口，如不使用 Nginx 可直接开放)

---

## 🛠️ 第一步：环境安装 (CentOS 7 专用)

### 1. 更新系统并安装基础工具
```bash
# 更新现有软件包
sudo yum update -y

# 安装常用工具 (git, vim, etc.)
sudo yum install -y yum-utils device-mapper-persistent-data lvm2 git vim
```

### 2. 安装 Docker 和 Docker Compose
CentOS 7 默认源中没有最新的 Docker，推荐使用阿里云镜像源安装：

```bash
# 1. 卸载旧版本 (如果有)
sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine

# 2. 设置阿里云 Docker 镜像仓库
sudo yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 3. 安装 Docker Engine 和 Docker Compose 插件
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. 启动 Docker 并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 5. 验证安装
docker compose version
# 输出示例: Docker Compose version v2.x.x
```

---

## 📂 第二步：部署代码

### 方式 A：通过 Git（推荐）
您的项目是 `LordLong` 仓库中的一个子目录。

#### 情况 1：首次部署（目录不存在）
```bash
cd /opt  # 建议部署在 /opt 目录下

# 克隆仓库
git clone https://github.com/PM-Henry-Li/LordLong.git

# 进入项目目录
cd LordLong/RedBookContentGen
```

#### 情况 2：更新代码（目录已存在）
如果提示 `destination path 'LordLong' already exists`，说明您之前已经克隆过。请执行以下命令更新：

```bash
# 进入仓库根目录
cd /opt/LordLong

# 拉取最新代码
git pull origin main

# 进入项目目录 (关键：必须进入包含 docker-compose.yml 的目录)
cd RedBookContentGen

# 确认文件存在
ls -l docker-compose.yml
# 如果显示 "No such file or directory"，请检查您是否在正确的目录下

# (可选) 如果依赖有更新，重建镜像
docker compose up -d --build
```

### 方式 B：本地上传
在本地终端压缩项目文件，然后上传：
```bash
# 本地压缩
tar -czvf redbook-gen.tar.gz --exclude=venv --exclude=logs --exclude=output --exclude=.git .

# 上传到服务器 (替换 <您的公网IP>)
scp redbook-gen.tar.gz root@<您的公网IP>:/opt/

# 服务器解压
cd /opt
mkdir redbook-gen
tar -xzvf redbook-gen.tar.gz -C redbook-gen
cd redbook-gen
```

---

## ⚙️ 第三步：配置应用

1.  **创建配置文件**
    ```bash
    cp .env.example .env
    ```

2.  **编辑配置**
    ```bash
    vi .env
    ```
    (按 `i` 进入编辑模式，修改完成后按 `Esc`，输入 `:wq` 保存退出)
    
    **关键修改项**：
    *   `OPENAI_API_KEY`: 填入您的阿里云 DashScope API Key。
    *   `IMAGE_GENERATION_MODE`: 建议设为 `api`（使用 AI 绘图）或 `template`。
    *   `TEMPLATE_STYLE`: 设置默认风格。

---

## 🚀 第四步：启动服务

使用 Docker Compose 一键启动：

```bash
# 构建并后台启动
docker compose up -d --build
```

查看运行状态：
```bash
docker compose ps
```

查看应用日志：
```bash
docker compose logs -f app
```

如果一切正常，您可以通过 **`http://<您的公网IP>:8080`** 访问应用。

---

## 🌐 第五步：配置 Nginx (可选，推荐)

CentOS 7 安装 Nginx 需要使用 EPEL 源。

1.  **安装 Nginx**
    ```bash
    # 安装 EPEL 源
    sudo yum install -y epel-release

    # 安装 Nginx
    sudo yum install -y nginx

    # 启动 Nginx 并设置开机自启
    sudo systemctl start nginx
    sudo systemctl enable nginx
    ```

2.  **配置反向代理**
    创建新的配置文件：
    ```bash
    vi /etc/nginx/conf.d/redbook.conf
    ```
    
    写入以下内容 (替换 `<您的域名或IP>`为实际值)：
    ```nginx
    server {
        listen 80;
        server_name <您的域名或IP>;

        location / {
            proxy_pass http://127.0.0.1:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        
        # WebSocket 支持
        location /socket.io {
            proxy_pass http://127.0.0.1:8080/socket.io;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
    ```

3.  **检查配置并重启**
    ```bash
    nginx -t  # 检查配置语法是否正确
    sudo systemctl reload nginx
    ```

现在，您可以直接通过 **`http://<您的公网IP>`** 访问应用。

---

## 🛡️ 常见问题 (CentOS 7)

### 1. 防火墙问题 (Firewalld)
CentOS 7 默认启用 Firewalld。如果无法访问端口，可能需要开放端口：

```bash
# 开放 80 端口
sudo firewall-cmd --zone=public --add-port=80/tcp --permanent
# 开放 8080 端口 (如果不使用 Nginx)
sudo firewall-cmd --zone=public --add-port=8080/tcp --permanent
# 重载防火墙配置
sudo firewall-cmd --reload
```

### 2. 权限问题
如果遇到文件权限问题，确保当前用户（或运行 Docker 的用户）有权访问项目目录。
```bash
# 赋予当前用户对项目目录的所有权
sudo chown -R $USER:$USER /opt/redbook-gen
```

### 3. Docker 拉取镜像超时 (dial tcp i/o timeout)
如果您在中国大陆地区遇到无法拉取镜像的问题，需要配置 Docker 镜像加速。

1.  **修改 Docker 配置** (两种方式任选其一)

    **方式一：一键命令（推荐）**
    直接复制运行：
    ```bash
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json <<-'EOF'
    {
      "registry-mirrors": [
        "https://docker.m.daocloud.io",
        "https://npm.taobao.org"
      ]
    }
    EOF
    ```

    **方式二：手动编辑**
    如果粘贴命令失败，可以使用 `vi` 编辑：
    ```bash
    # 1. 打开文件
    sudo vi /etc/docker/daemon.json

    # 2. 按 'i' 进入编辑模式，粘贴以下内容：
    {
      "registry-mirrors": [
        "https://docker.m.daocloud.io",
        "https://npm.taobao.org"
      ]
    }

    # 3. 按 'Esc'，输入 ':wq' 保存并退出
    ```
    *(注：阿里云 ECS 用户建议使用自己的专属加速器地址，可在阿里云容器镜像服务控制台查看)*

2.  **重启 Docker**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    ```

---

## 🛡️ 常用维护命令

*   **重启服务**: `docker compose restart app`
*   **停止服务**: `docker compose down`
*   **更新代码后重新部署**:
    ```bash
    git pull
    docker compose up -d --build
    ```
*   **查看实时日志**: `docker compose logs -f --tail=100 app`
