# 拼音探险家

这是一个面向儿童的拼音键盘练习小游戏，包含字母森林、拼音合成室和词语竞速三种模式。

项目现在按前后端边界组织：根目录是可直接部署的静态前端，`backend/` 是独立 Node.js API，`frontend/` 管理前端运行时配置，`infra/` 和 `deploy/` 管理 Nginx/systemd 生产部署。前端成绩先写入本地存储，再异步同步到 API；API 不可用时不影响离线练习。

源代码采用原生 ES Modules；页面运行时使用零依赖生成的单文件运行包，因此既支持静态服务，也支持直接双击 `index.html` 打开。

## 运行

项目不依赖构建框架或第三方运行时。直接修改源码模块后，先生成运行包：

```bash
npm run build
```

也可以通过本地静态服务打开：

```bash
npm run serve
```

然后访问 `http://127.0.0.1:4173/`。

同时启动前后端开发服务：

```bash
npm run dev
```

前端访问 `http://127.0.0.1:4173/`，API 健康检查为 `http://127.0.0.1:8080/api/health`。

中文语音默认优先使用 `audio/voice/zh/` 下的本地音频，保证直接打开 `index.html` 时音色和发音一致；未收录的动态文本会自动回退到系统中文语音。macOS 可以使用以下命令重新生成语音资源：

```bash
npm run voice:generate
```

当前资源使用系统 `Tingting` 中文音色生成。后续如果替换为人工录音或神经网络音色，只需要替换同目录资源并重新生成清单，不需要修改游戏逻辑。

## 架构约定

- `js/main.js`：应用入口和页面导航，只处理页面事件与展示状态。
- `js/game.js`：游戏会话编排、计时、得分和模式生命周期。
- `js/letters.js`、`js/pinyin.js`、`js/words.js`：三种玩法的独立领域逻辑。
- `js/keyboard.js`、`js/audio.js`：可复用交互能力。
- `js/storage.js`：本地数据读写、旧数据归一化和容错。
- `js/utils.js`：无业务状态的纯工具函数。
- `js/api.js`：前端 API 客户端，网络失败时自动降级为本地模式。
- `data/`：只读词库模块，不再通过 `window` 注入全局变量。
- `backend/server.mjs`：API 进程入口。
- `backend/src/`：HTTP 路由、输入校验和成绩事件存储。
- `infra/nginx/`、`deploy/`：阿里云服务器的反向代理、systemd 和环境变量模板。

所有模块通过显式 `import/export` 连接；新增异步定时器必须由所属模块登记并在 `stop()` / `pause()` 中清理。

## 检查

```bash
npm run check
```

该命令会执行全部模块语法检查和核心数据/存储单元测试。

生产部署步骤见 [DEPLOY.md](./DEPLOY.md)，目标域名为 `https://finger.lordlong.cn/`。
