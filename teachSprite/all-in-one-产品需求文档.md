# 群发与学习任务 · 单页聚合（all-in-one）产品需求文档

本文档基于 `base_info/需求文档模板.md` 编写，描述 **all-in-one.html** 单页聚合方案相对于原「index + 多 HTML + iframe」的**新增功能**与详细方案。

---

## 目录

1. 修改记录
2. 需求背景及核心沟通记录
3. 收益评估
4. 统计需求
5. Feature list & 流程结构图
6. 详细方案
7. 核心沟通记录

---

## 1. 修改记录

| 时间 | 动作 | 操作人 | 备注 |
|------|------|--------|------|
| 2026.01.21 | 新建 | — | all-in-one 单页聚合需求，基于需求文档模板 |

---

## 2. 需求背景及核心沟通记录

### 需求背景

原有「群发与学习任务」能力分布在多个 HTML 中：**index.html** 作为统一入口，通过 **iframe** 加载「群发配置-发送内容扩展.html」「学习任务-H5落地页.html」「做任务-试卷详情.html」。该方案存在：

- **多文件依赖**：需同时部署多个 HTML，路径与 iframe src 需保持一致；
- **跨页跳转**：学习任务 H5 的「去完成」需跳转至独立「做任务-试卷详情.html」，在 index 内嵌 iframe 时需通过 **postMessage** 通知父级切换 iframe src 并高亮菜单；
- **独立访问受限**：单打开某一个 HTML（如学习任务 H5）时，无法在同一页面内完成「去完成 → 做任务」的完整路径，必须依赖 index + iframe 或多次整页跳转。

为支持**单文件、可独立完整访问**的演示、内部分享或轻量部署，需在保持**群发配置、学习任务 H5、做任务-试卷**三类功能一致的前提下，将上述能力**聚合到一个 HTML（all-in-one.html）** 中，通过**视图切换 + Hash 路由**替代 iframe，**去完成** 改为**本页内切换到做任务-试卷视图**并完成参数传递，从而**仅打开一个 HTML 即可完整体验全部流程**。

### 核心沟通结论

- **单文件交付**：all-in-one.html 内置群发配置、学习任务 H5、做任务-试卷的全部 DOM、样式与脚本；除 `base_info/企微页面.jpg` 等静态资源外，不依赖其他 HTML。
- **路由与视图**：使用 Hash 路由 `#config` / `#task-h5` / `#do-quiz` 对应三个视图；左侧菜单点击切换视图并同步 hash；刷新、书签、直接打开带 hash 的链接均可正确展示对应视图。
- **去完成 → 做任务**：在学习任务 H5 点击「去完成」且为**试卷**时，不再跳转独立页面或 postMessage，而是：将 `taskId、title、due、quizTitle、count` 等写入 `window.__doQuizParams`，并 `location.hash = '#do-quiz'`，从而切换到做任务-试卷视图；该视图展示时从 `__doQuizParams` 或 URL 的 `?title=、?due=、…` 回填。
- **做任务「返回」**：使用 `history.back()`；从「去完成」进入时，可回到学习任务 H5（#task-h5）。
- **弹窗与视图**：群发相关弹窗挂载在 body 下；切换视图时自动关闭所有弹窗，避免弹窗滞留或层级错乱。

---

## 3. 收益评估

| 维度 | 说明 |
|------|------|
| **部署与分享** | 单文件即可完成群发配置、学习任务 H5、做任务的完整演示或内部分享，降低多文件与路径的协作成本。 |
| **独立访问** | 不依赖 index + iframe 或服务端路由，任意环境（本地、静态服务器、网盘、邮件附件等）打开 all-in-one.html 即可完整使用。 |
| **流程连贯** | 「去完成」→ 做任务-试卷 在同一页面内完成，无整页跳转、无 postMessage 依赖，体验更连贯。 |
| **可维护性** | 与现有多 HTML 方案在**业务功能**上对齐，便于后续将 all-in-one 作为「单页参考实现」做功能同步或回归。 |

收益可在上线或对外分享后，通过**单页使用次数、从学习任务到做任务的完成率**等（若接入统计）做后续评估。

---

## 4. 统计需求

当前 all-in-one 为**纯前端单页**，无新增数据埋点；若后续接入统一埋点体系，可考虑：

- 视图切换：`view_switch`，属性 `from_view`、`to_view`（config / task-h5 / do-quiz）；
- 去完成（学习任务 → 做任务）：`task_do_click`，属性 `source=all-in-one`、`type=paper|free`、`task_id`；
- 做任务「开始作答」：`quiz_start_click`，属性 `source=all-in-one`、`task_id`。

具体埋点与口径以实际统计平台为准，本文档仅作预留说明。

---

## 5. Feature list & 流程结构图

### 5.1 Feature list

| 模块序号 | 子功能 | 功能说明 | 备注/优先级 |
|----------|--------|----------|-------------|
| 1 | 单文件聚合 | 将群发配置、学习任务 H5、做任务-试卷的 DOM / 样式 / 脚本合并进 all-in-one.html，无 iframe、无多 HTML 依赖 | P0 |
| 2 | 统一左侧菜单与视图切换 | 左侧固定菜单「群发配置」「学习任务 H5」「做任务-试卷」，点击后隐藏其他视图、显示对应视图并高亮菜单 | P0 |
| 3 | Hash 路由 | 支持 #config、#task-h5、#do-quiz；缺省或无法识别时默认 #config；切换视图时同步 hash；监听 hashchange 实现刷新、书签、直接打开链接正确展示 | P0 |
| 4 | 去完成 → 做任务（本页切换） | 学习任务 H5 点击「去完成」且为试卷时：写 __doQuizParams，置 hash=#do-quiz，切到做任务-试卷视图；做任务视图展示时从 __doQuizParams 或 URL 查询参数回填 | P0 |
| 5 | 做任务「返回」 | 做任务-试卷视图「返回」使用 history.back()；从「去完成」进入时可回到 #task-h5 | P0 |
| 6 | 学习任务 URL 参数 | 学习任务视图支持 ?type=free（展示自由任务）、?bg=img（以 base_info/企微页面.jpg 为背景）；切换进该视图时按 search 生效 | P1 |
| 7 | 做任务 URL 参数 | 做任务视图支持 ?taskId、?title、?sub、?due、?quizTitle、?count 回填；从「去完成」进入时以 __doQuizParams 优先 | P0 |
| 8 | 弹窗与视图联动 | 群发 5 组弹窗挂载在 body；切换视图时自动关闭所有弹窗，避免残留或挡底 | P0 |

### 5.2 流程结构图

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                 all-in-one.html 单页                     │
                    │  ┌─────────────┐  ┌──────────────────────────────────┐  │
                    │  │ 左侧菜单     │  │ 主内容区（三视图之一）             │  │
                    │  │ ·群发配置   │  │  #config  → 群发配置 + 底部栏     │  │
                    │  │ ·学习任务H5 │  │  #task-h5 → 企微拟真 + 学习任务卡片│  │
                    │  │ ·做任务-试卷│  │  #do-quiz → 做任务-试卷           │  │
                    │  └──────┬──────┘  └──────────────────────────────────┘  │
                    │         │ 点击             Hash 路由                     │
                    │         └──────────────► #config | #task-h5 | #do-quiz   │
                    └─────────────────────────────────────────────────────────┘

  学习任务 H5 内点击「去完成」(试卷)
         │
         ▼
  ┌──────────────────────┐     location.hash = '#do-quiz'
  │ __doQuizParams = {   │     ────────────────────────────►  做任务-试卷视图
  │   taskId, title,     │           hashchange               (从 __doQuizParams
  │   due, quizTitle,    │           → showView('do')         或 ?title= 等回填)
  │   count              │           → applyDoQuizParams()
  │ }                    │
  └──────────────────────┘

  做任务-试卷 内点击「返回」
         │
         ▼
  history.back()  ──────►  若由「去完成」进入，则回到 #task-h5（学习任务 H5 视图）
```

---

## 6. 详细方案

*(按 Feature 与交互拆分)*

| 序号 | 原型/界面 | 需求描述 | 备注 |
|------|-----------|----------|------|
| **1** | all-in-one 整体布局 | **单文件结构**：一个 HTML 内包含（1）左侧 .sidebar 统一菜单，（2）右侧 .main 主内容区，其中为三块 .view：`#view-config`（群发配置）、`#view-task-h5`（学习任务 H5）、`#view-do-quiz`（做任务-试卷）。同一时刻仅一个 .view 带 .active，占据主内容区。群发 5 组弹窗（选择任务类型、新建试卷/自由任务、试卷库、添加题目）的 modal-mask / modal-wrap 作为 body 直接子节点，不放入任一 view。 | 样式需对 .layout .sidebar / .layout .main 做作用域隔离，避免与左侧统一菜单的 .sidebar 冲突。 |
| **2** | 左侧菜单 | **菜单项**：群发配置（data-key=config）、学习任务 H5（data-key=task）、做任务-试卷（data-key=do）。**点击**：调用 showView(key)，隐藏所有 .view、去掉所有 .nav-item.active，显示 `#view-config` / `#view-task-h5` / `#view-do-quiz` 中对应视图并为其添加 .active，为当前菜单项添加 .active；若当前 `location.hash` 与目标不一致，则赋 `location.hash` 为 `#config` / `#task-h5` / `#do-quiz`。 | 仅最外层 .sidebar 的 .nav-item 参与高亮，群发内部的 .layout .sidebar 不参与。 |
| **3** | Hash 路由 | **约定**：`#config` → 群发配置，`#task-h5` → 学习任务 H5，`#do-quiz` → 做任务-试卷。**监听**：`hashchange` 及首屏执行 `onHash()`：从 `location.hash` 解析出 key，调用 `showView(key)`。**默认**：`location.hash` 为空或无法解析时，按 `#config` 处理。 | 刷新、书签、直接打开 `all-in-one.html#task-h5` 等均能正确展示。 |
| **4** | 学习任务 H5「去完成」 | **试卷**（`type` 非 `free` 或未传）：从卡片 DOM 取 `title`、`due`（或兜底），从 `location.search` 取 `taskId`；构造 `window.__doQuizParams = { taskId, title, due, quizTitle: title, count: '' }`，并执行 `location.hash = '#do-quiz'`。由 hashchange 触发 `showView('do')`，进而 `applyDoQuizParams()`，做任务-试卷视图从 `__doQuizParams` 回填 taskName、dueText、quizTitle、quizCount 等。**自由任务**（`type=free`）：仍为 `alert` 占位，不切视图。 | 与原多 HTML 方案中「跳转做任务-试卷详情.html 或 postMessage 父级」的行为等效，改为本页切换。 |
| **5** | 做任务-试卷「返回」 | 点击「返回」执行 `history.back()`。若由学习任务 H5 的「去完成」进入，则 history 中存在 `#task-h5`，back 后回到学习任务 H5 视图。若直接打开 `#do-quiz` 则 back 至浏览器上一页。 | 与现有做任务-试卷详情页行为一致。 |
| **6** | 学习任务视图的 URL 参数 | 进入学习任务视图（`showView('task')`）时：解析 `location.search`。**`?bg=img`**：为 `body` 添加 .bg-img，以 `base_info/企微页面.jpg` 为全屏背景、仅叠卡片；否则移除 .bg-img。**`?type=free`**：将卡片内「📋 试卷」改为「📋 自由任务」；否则为「📋 试卷」。 | 与原学习任务-H5落地页.html 的 ?bg=img、?type=free 语义一致。 |
| **7** | 做任务视图的参数回填 | **来源**：优先 `window.__doQuizParams`；若 `__doQuizParams.title` 为空且 `location.search` 存在，则从 search 解析 `taskId,title,sub,due,quizTitle,count` 并入参对象。**回填**： taskName ← title；taskSub ← sub；dueText ← due + '截止'；quizTitle ← quizTitle 或 title；quizCount ← count。未传入的字段保持 DOM 默认或留空。 | 直接打开 `all-in-one.html?title=周测&due=01月27日18:00#do-quiz` 时，做任务视图能正确展示。 |
| **8** | 视图切换与弹窗 | 每次 `showView(key)` 时，先执行 `hideAllModals()`，对所有群发相关 modal-mask / modal-wrap 移除 .show。群发弹窗仅从群发配置视图内的「发送学习任务」等按钮触发；弹窗打开时叠在任意视图之上（因挂载在 body）。 | 从群发配置切到学习任务或做任务时，若曾打开过弹窗未关闭，会被自动关掉，避免弹窗悬空。 |
| **9** | 群发配置、学习任务 H5、做任务-试卷 功能 | 三者**功能与原独立 HTML 一致**：群发配置含发送学习任务入口及 5 层弹窗流程、底部栏；学习任务 H5 含企微拟真布局、学习任务卡片、去完成；做任务-试卷含状态栏、任务概览、试卷卡片、开始作答、时钟。仅「去完成」的跳转逻辑、做任务的数据来源按上述 4、7 改为本页视图切换与 __doQuizParams / URL。 | 不做业务新增，仅承载方式从多页/iframe 改为单页视图。 |
| **10** | 资源依赖 | all-in-one.html 除可选 `base_info/企微页面.jpg`（`?bg=img` 时）外，不依赖其他 HTML。字体、图标等为内联或通用。部署时需保证 all-in-one.html 与 base_info 的相对路径正确。 | 若不存在企微页面.jpg，?bg=img 时背景图 404，不影响其余功能。 |

---

## 7. 核心沟通记录

- 单页聚合以「可独立完整访问」为首要目标，与 index + iframe 方案并存，不替代原有 index 入口。
- 「去完成」→ 做任务 在 all-in-one 内采用本页视图切换 + __doQuizParams，不再使用 postMessage 或 iframe src 切换。
- 群发、学习任务 H5、做任务-试卷 的业务规则、字段、校验与现有 PRD 及独立 HTML 保持一致，本需求仅规定**聚合方式、路由、跳转与参数**。

---

*文档结束。关联文件：`teachSprite/all-in-one.html`。*
