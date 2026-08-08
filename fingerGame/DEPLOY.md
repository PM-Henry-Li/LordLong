# 阿里云部署说明

目标：让 `https://finger.lordlong.cn/` 提供静态前端，并由同一域名下的 `/api/` 反向代理到独立 Node.js API。

## 1. 域名与服务器

1. 在阿里云 DNS 为 `finger.lordlong.cn` 配置 A 记录，指向 ECS 公网 IP。
2. ECS 安全组只开放 TCP `22`、`80`、`443`；`8080` 仅监听 `127.0.0.1`，不要对公网开放。
3. 安装 Node.js 20+、Nginx 和 Certbot（或使用阿里云签发的证书）。

## 2. 发布前检查

```bash
npm ci
npm run check
npm run deploy:check
```

## 3. 部署文件

```bash
sudo mkdir -p /var/www/fingerGame
sudo rsync -a --delete ./ /var/www/fingerGame/
sudo install -d -o www-data -g www-data /var/lib/pinyin-explorer

sudo install -d /etc/pinyin-explorer
sudo cp deploy/api.env.example /etc/pinyin-explorer/api.env
sudo cp infra/nginx/finger.lordlong.cn.conf /etc/nginx/sites-available/finger.lordlong.cn
sudo ln -sfn /etc/nginx/sites-available/finger.lordlong.cn /etc/nginx/sites-enabled/finger.lordlong.cn
sudo cp deploy/systemd/pinyin-explorer-api.service /etc/systemd/system/
```

申请证书后，检查 Nginx 并启动服务：

```bash
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now pinyin-explorer-api
sudo systemctl reload nginx
```

## 4. 验收

```bash
curl -fsS https://finger.lordlong.cn/api/health
curl -I https://finger.lordlong.cn/
```

浏览器打开 `https://finger.lordlong.cn/` 后，完成一局游戏，确认 API 服务日志和 `/var/lib/pinyin-explorer/results.json` 有对应事件。成绩文件放在发布目录之外，避免 `rsync --delete` 发布时误删运行数据。前端即使 API 暂时不可用也会继续使用本地成绩，不会阻断游戏。

## 5. 安全边界

当前 API 保存的是本地随机用户 ID、模式和成绩事件，不保存姓名。它适合作为第一阶段的匿名结果同步；如果后续要做跨设备账号、排行榜或家长端，需要在 API 前增加认证、限流和数据库迁移，不应直接把当前匿名接口当成账号系统。
