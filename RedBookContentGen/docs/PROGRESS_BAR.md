# 进度条组件使用文档

## 概述

进度条组件用于显示内容生成和图片生成的实时进度，提供友好的用户反馈。

## 功能特性

- ✅ 实时进度显示（0-100%）
- ✅ 动画效果（平滑过渡、闪光效果）
- ✅ 状态文字显示
- ✅ 阶段指示器（生成文案 → 生成图片 → 完成）
- ✅ 预计剩余时间
- ✅ 详细信息显示（当前任务、已完成数、总数）
- ✅ 取消操作支持
- ✅ 重试功能
- ✅ 响应式设计

## 快速开始

### 1. 引入文件

```html
<!-- CSS -->
<link rel="stylesheet" href="static/css/progress.css">

<!-- JavaScript -->
<script src="static/js/progress.js"></script>
```

### 2. 创建容器

```html
<div id="progress-container"></div>
```

### 3. 初始化进度条

```javascript
const progressBar = new ProgressBar('progress-container', {
    showStages: true,      // 显示阶段指示器
    showTime: true,        // 显示剩余时间
    showDetails: true,     // 显示详细信息
    allowCancel: true,     // 允许取消
    autoHide: false,       // 完成后不自动隐藏
    autoHideDelay: 3000    // 自动隐藏延迟（毫秒）
});
```

## API 文档

### 构造函数

```javascript
new ProgressBar(containerId, options)
```

**参数**：
- `containerId` (string): 容器元素ID
- `options` (Object): 配置选项
  - `showStages` (boolean): 是否显示阶段指示器，默认 `true`
  - `showTime` (boolean): 是否显示剩余时间，默认 `true`
  - `showDetails` (boolean): 是否显示详细信息，默认 `true`
  - `allowCancel` (boolean): 是否允许取消，默认 `true`
  - `autoHide` (boolean): 完成后是否自动隐藏，默认 `false`
  - `autoHideDelay` (number): 自动隐藏延迟（毫秒），默认 `3000`
  - `websocketUrl` (string): WebSocket 命名空间，默认 `'/progress'`
  - `autoReconnect` (boolean): 是否自动重连，默认 `true`
  - `reconnectDelay` (number): 重连延迟（毫秒），默认 `3000`
  - `heartbeatInterval` (number): 心跳间隔（毫秒），默认 `30000`

### 方法

#### start(options)

开始进度。

```javascript
progressBar.start({
    taskId: 'task-123',  // 任务ID（可选，用于 WebSocket）
    details: {
        current: '准备生成',
        completed: 0,
        total: 5
    }
});
```

**参数**：
- `options.taskId` (string): 任务ID，用于 WebSocket 订阅
- `options.details` (Object): 详细信息

#### updateProgress(progress, data)

更新进度。

```javascript
progressBar.updateProgress(50, {
    status: 'generating_content',
    statusText: '正在生成文案...',
    stage: 'generating_content',
    details: {
        current: '生成标题',
        completed: 2,
        total: 5
    }
});
```

**参数**：
- `progress` (number): 进度值（0-100）
- `data` (Object): 进度数据
  - `status` (string): 状态（idle, started, generating_content, generating_image, completed, failed, cancelled）
  - `statusText` (string): 状态文字
  - `stage` (string): 阶段（generating_content, generating_image, completed）
  - `details` (Object): 详细信息

#### complete(message)

完成进度。

```javascript
progressBar.complete('生成完成！');
```

#### fail(message)

标记为失败。

```javascript
progressBar.fail('生成失败：API 调用超时');
```

#### cancel()

取消操作。

```javascript
progressBar.cancel();
```

#### reset()

重置进度条。

```javascript
progressBar.reset();
```

#### show() / hide()

显示/隐藏进度条。

```javascript
progressBar.show();
progressBar.hide();
```

#### on(event, callback)

设置回调函数。

```javascript
progressBar.on('cancel', () => {
    console.log('用户取消了操作');
});

progressBar.on('retry', () => {
    console.log('用户点击了重试');
});

progressBar.on('complete', () => {
    console.log('操作完成');
});

// WebSocket 事件
progressBar.on('connect', () => {
    console.log('WebSocket 已连接');
});

progressBar.on('disconnect', (reason) => {
    console.log('WebSocket 已断开:', reason);
});

progressBar.on('error', (error) => {
    console.error('WebSocket 错误:', error);
});
```

**支持的事件**：
- `cancel`: 用户点击取消按钮
- `retry`: 用户点击重试按钮
- `complete`: 操作完成
- `connect`: WebSocket 连接成功
- `disconnect`: WebSocket 断开连接
- `error`: WebSocket 错误

#### isConnected()

获取 WebSocket 连接状态。

```javascript
if (progressBar.isConnected()) {
    console.log('WebSocket 已连接');
}
```

**返回值**：
- `boolean`: 是否已连接

#### getTaskId()

获取当前任务ID。

```javascript
const taskId = progressBar.getTaskId();
console.log('当前任务:', taskId);
```

**返回值**：
- `string|null`: 任务ID

#### joinTaskRoom(taskId)

加入任务房间（订阅任务进度）。

```javascript
progressBar.joinTaskRoom('task-123');
```

**参数**：
- `taskId` (string): 任务ID

#### leaveTaskRoom(taskId)

离开任务房间（取消订阅任务进度）。

```javascript
progressBar.leaveTaskRoom('task-123');
```

**参数**：
- `taskId` (string): 任务ID

#### disconnectWebSocket()

断开 WebSocket 连接。

```javascript
progressBar.disconnectWebSocket();
```

#### destroy()

销毁进度条实例，清理所有资源。

```javascript
progressBar.destroy();
```

## 使用示例

### 示例 1：简单进度

```javascript
// 初始化
const progressBar = new ProgressBar('progress-container');

// 开始
progressBar.start();

// 更新进度
let progress = 0;
const interval = setInterval(() => {
    progress += 10;
    progressBar.updateProgress(progress, {
        statusText: `正在处理... ${progress}%`
    });

    if (progress >= 100) {
        clearInterval(interval);
        progressBar.complete('处理完成！');
    }
}, 500);
```

### 示例 2：阶段进度

```javascript
// 开始
progressBar.start();

// 阶段1：生成文案
progressBar.updateProgress(30, {
    status: 'generating_content',
    statusText: '正在生成文案...',
    stage: 'generating_content'
});

// 阶段2：生成图片
progressBar.updateProgress(70, {
    status: 'generating_image',
    statusText: '正在生成图片...',
    stage: 'generating_image'
});

// 完成
progressBar.updateProgress(100, {
    stage: 'completed'
});
progressBar.complete('所有内容生成完成！');
```

### 示例 3：详细进度

```javascript
// 开始
progressBar.start({
    details: {
        current: '准备生成',
        completed: 0,
        total: 5
    }
});

// 更新详细信息
progressBar.updateProgress(20, {
    statusText: '正在生成标题...',
    details: {
        current: '生成标题',
        completed: 1,
        total: 5
    }
});

progressBar.updateProgress(40, {
    statusText: '正在生成正文...',
    details: {
        current: '生成正文',
        completed: 2,
        total: 5
    }
});

// ... 继续更新
```

### 示例 4：WebSocket 集成

```javascript
// 初始化进度条（启用 WebSocket）
const progressBar = new ProgressBar('progress-container', {
    showStages: true,
    showTime: true,
    showDetails: true,
    allowCancel: true,
    websocketUrl: '/progress',      // WebSocket 命名空间
    autoReconnect: true,            // 自动重连
    reconnectDelay: 3000,           // 重连延迟（毫秒）
    heartbeatInterval: 30000        // 心跳间隔（毫秒）
});

// 监听 WebSocket 事件
progressBar.on('connect', () => {
    console.log('WebSocket 已连接');
});

progressBar.on('disconnect', (reason) => {
    console.log('WebSocket 已断开:', reason);
});

progressBar.on('error', (error) => {
    console.error('WebSocket 错误:', error);
});

// 启动任务并订阅进度更新
function startGeneration() {
    // 从后端获取任务ID
    fetch('/api/generate_content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_text: '老北京胡同' })
    })
    .then(response => response.json())
    .then(data => {
        const taskId = data.task_id;
        
        // 启动进度条并加入任务房间
        progressBar.start({
            taskId: taskId,
            details: {
                current: '准备生成',
                completed: 0,
                total: 5
            }
        });
        
        // 进度更新会自动通过 WebSocket 接收
    })
    .catch(error => {
        console.error('启动任务失败:', error);
    });
}

// 取消任务
progressBar.on('cancel', () => {
    console.log('用户取消了操作');
    // 取消请求会自动通过 WebSocket 发送
});
```

### 示例 5：手动处理 WebSocket 消息

```javascript
// 如果需要手动处理 WebSocket 消息
const progressBar = new ProgressBar('progress-container');

// 访问底层 Socket.IO 实例
const socket = progressBar.socket;

// 监听自定义事件
socket.on('custom_event', (data) => {
    console.log('收到自定义事件:', data);
});

// 发送自定义消息
socket.emit('custom_message', { data: 'hello' });
```

## 状态说明

### 进度状态

| 状态 | 说明 | 图标 |
|------|------|------|
| `idle` | 空闲 | ⏳ |
| `started` | 已开始 | 🚀 |
| `generating_content` | 生成文案中 | 📝 |
| `generating_image` | 生成图片中 | 🖼️ |
| `completed` | 已完成 | ✅ |
| `failed` | 失败 | ❌ |
| `cancelled` | 已取消 | ⚠️ |

### 阶段说明

| 阶段 | 说明 | 对应状态 |
|------|------|----------|
| `content` | 生成文案 | `generating_content` |
| `image` | 生成图片 | `generating_image` |
| `complete` | 完成 | `completed` |

## 样式自定义

### 修改颜色

```css
/* 修改进度条颜色 */
.progress-bar {
    background: linear-gradient(90deg, #your-color-1, #your-color-2);
}

/* 修改完成状态颜色 */
.progress-bar.completed {
    background: linear-gradient(90deg, #your-success-color-1, #your-success-color-2);
}

/* 修改失败状态颜色 */
.progress-bar.failed {
    background: linear-gradient(90deg, #your-error-color-1, #your-error-color-2);
}
```

### 修改尺寸

```css
/* 修改进度条高度 */
.progress-bar-wrapper {
    height: 12px; /* 默认 8px */
}

/* 修改容器内边距 */
.progress-container {
    padding: 32px; /* 默认 24px */
}
```

## 测试页面

- `static/test-progress.html` - 基础功能测试
- `static/test-websocket-progress.html` - WebSocket 集成测试

访问测试页面查看完整的功能演示。

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 注意事项

1. **进度计算**：确保进度值在 0-100 之间
2. **状态一致性**：状态和阶段要保持一致
3. **时间估算**：剩余时间基于已用时间和当前进度计算，初期可能不准确
4. **资源清理**：取消操作时要确保清理相关资源
5. **错误处理**：失败时提供明确的错误信息和修复建议
6. **WebSocket 依赖**：需要引入 Socket.IO 客户端库才能使用 WebSocket 功能
7. **连接管理**：组件会自动管理 WebSocket 连接和重连
8. **任务订阅**：使用 `taskId` 参数自动订阅任务进度更新
9. **资源释放**：页面卸载时调用 `destroy()` 方法清理资源

### WebSocket 依赖

使用 WebSocket 功能需要引入 Socket.IO 客户端库：

```html
<!-- CDN 方式 -->
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<!-- 或本地文件 -->
<script src="/socket.io/socket.io.js"></script>
```

如果未引入 Socket.IO，组件会自动降级为纯前端模式（不支持实时进度推送）。

## 相关文档

- [WebSocket 进度推送](./WEBSOCKET_PROGRESS.md)（待实现）
- [错误处理组件](./ERROR_HANDLER.md)
- [配置管理](./CONFIG.md)

## 更新日志

### v1.1.0 (2026-02-14)

- ✅ WebSocket 实时进度推送
- ✅ 自动连接管理和重连
- ✅ 心跳检测机制
- ✅ 任务房间订阅
- ✅ 远程任务取消
- ✅ 连接状态回调
- ✅ 资源清理和销毁方法

### v1.0.0 (2026-02-14)

- ✅ 初始版本
- ✅ 基础进度显示
- ✅ 阶段指示器
- ✅ 剩余时间估算
- ✅ 详细信息显示
- ✅ 取消和重试功能
- ✅ 响应式设计
