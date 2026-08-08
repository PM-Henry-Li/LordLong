# 前端边界

当前仓库的静态前端以根目录为发布目录，页面入口是 `index.html`，浏览器模块位于 `js/`、`data/`、`css/`、`images/` 和 `audio/`。`frontend/config.js` 只承载运行时环境配置，不把环境变量硬编码进业务模块。

这样保留了 `file://` 直接打开和现有静态部署能力，同时把 API 配置、后端服务和部署配置拆成独立边界：

- `frontend/`：前端运行时配置与前端协作说明。
- `backend/`：Node.js API 服务及持久化实现。
- `infra/`：反向代理和生产流量配置。
- `deploy/`：systemd、环境变量和上线检查。

后续如果需要迁移到 Vite/React，只需把当前静态前端迁移到 `apps/web`，API 契约和 `backend/` 不需要改变。
