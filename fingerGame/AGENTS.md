# 多 agent 协作约定

## 目录 ownership

| 领域 | 目录/文件 | 主要职责 |
| --- | --- | --- |
| Web 页面 | `index.html`、`css/`、`frontend/`、`js/main.js`、`js/game.js` | 页面交互、导航、游戏编排 |
| 玩法与数据 | `js/letters.js`、`js/pinyin.js`、`js/words.js`、`data/` | 玩法规则、词库和语音清单 |
| API | `backend/`、`js/api.js` | HTTP 接口、校验、成绩事件存储、前端同步 |
| 发布运维 | `infra/`、`deploy/`、`scripts/dev.mjs` | Nginx、systemd、本地前后端启动和发布检查 |
| 测试 | `tests/` | 单元测试、API 契约测试、资源完整性测试 |

## 协作规则

1. 每个 agent 一次只负责一个 ownership，跨边界变更先在任务说明中写清接口和验收口径。
2. `js/app.bundle.js` 是构建产物，禁止手工编辑；修改模块后执行 `npm run build` 生成。
3. API 变更必须同时更新 `backend/src/validation.mjs`、前端 `js/api.js` 和 `tests/backend.test.mjs`。
4. 修改词库或语音资源后必须执行 `npm run check`，确认资源清单、语法和测试都通过。
5. 合并前至少执行 `npm run check && npm run deploy:check`，并在交付说明中写明未运行的环境级检查（例如真实域名、证书或 ECS）。
6. 生产数据写入 `/var/lib/pinyin-explorer`，不能把运行数据提交进发布目录或通过 `rsync --delete` 覆盖。

## 本地开发入口

```bash
npm run dev       # 前端 4173 + API 8080
npm run check     # 构建、语法、全部测试
npm run deploy:check
```

## API 最小契约

- `GET /api/health`：健康检查。
- `GET /api/config`：API 版本和能力开关。
- `POST /api/game-results`：提交匿名成绩事件。
- `GET /api/leaderboard`：读取匿名成绩聚合结果。

当前 API 不承载账号认证和敏感个人信息。需要跨设备账号时，应先补认证、限流和数据库方案，再扩展接口。
