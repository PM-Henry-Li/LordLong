/**
 * 进度条组件
 * 用于显示内容生成和图片生成的实时进度
 */

class ProgressBar {
    /**
     * 创建进度条实例
     * @param {string} containerId - 容器元素ID
     * @param {Object} options - 配置选项
     */
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`容器元素 #${containerId} 不存在`);
        }

        // 配置选项
        this.options = {
            showStages: true,          // 是否显示阶段
            showTime: true,            // 是否显示剩余时间
            showDetails: true,         // 是否显示详细信息
            allowCancel: true,         // 是否允许取消
            autoHide: false,           // 完成后是否自动隐藏
            autoHideDelay: 3000,       // 自动隐藏延迟（毫秒）
            websocketUrl: '/progress', // WebSocket 命名空间
            autoReconnect: true,       // 是否自动重连
            reconnectDelay: 3000,      // 重连延迟（毫秒）
            heartbeatInterval: 30000,  // 心跳间隔（毫秒）
            ...options
        };

        // 状态
        this.state = {
            progress: 0,               // 当前进度（0-100）
            status: 'idle',            // 状态：idle, started, generating, completed, failed, cancelled
            stage: '',                 // 当前阶段
            startTime: null,           // 开始时间
            estimatedTime: null,       // 预计总时间（秒）
            details: {},               // 详细信息
            taskId: null,              // 当前任务ID
            connected: false           // WebSocket 连接状态
        };

        // WebSocket 相关
        this.socket = null;
        this.heartbeatTimer = null;
        this.reconnectTimer = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        // 回调函数
        this.callbacks = {
            onCancel: null,
            onRetry: null,
            onComplete: null,
            onConnect: null,
            onDisconnect: null,
            onError: null
        };

        this.init();
    }

    /**
     * 初始化进度条
     */
    init() {
        this.render();
        this.bindEvents();
        this.initWebSocket();
    }

    /**
     * 初始化 WebSocket 连接
     */
    initWebSocket() {
        // 检查 Socket.IO 是否可用
        if (typeof io === 'undefined') {
            console.warn('Socket.IO 未加载，WebSocket 功能不可用');
            return;
        }

        try {
            // 创建 Socket.IO 连接
            this.socket = io(this.options.websocketUrl, {
                transports: ['websocket', 'polling'],
                reconnection: this.options.autoReconnect,
                reconnectionDelay: this.options.reconnectDelay,
                reconnectionAttempts: this.maxReconnectAttempts
            });

            // 绑定 WebSocket 事件
            this.bindWebSocketEvents();

            console.log('WebSocket 初始化完成');
        } catch (error) {
            console.error('WebSocket 初始化失败:', error);
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
        }
    }

    /**
     * 绑定 WebSocket 事件
     */
    bindWebSocketEvents() {
        if (!this.socket) return;

        // 连接成功
        this.socket.on('connect', () => {
            console.log('WebSocket 已连接');
            this.state.connected = true;
            this.reconnectAttempts = 0;
            
            // 启动心跳
            this.startHeartbeat();

            // 如果有任务ID，重新加入房间
            if (this.state.taskId) {
                this.joinTaskRoom(this.state.taskId);
            }

            if (this.callbacks.onConnect) {
                this.callbacks.onConnect();
            }
        });

        // 连接断开
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket 已断开:', reason);
            this.state.connected = false;
            
            // 停止心跳
            this.stopHeartbeat();

            if (this.callbacks.onDisconnect) {
                this.callbacks.onDisconnect(reason);
            }

            // 自动重连
            if (this.options.autoReconnect && reason !== 'io client disconnect') {
                this.scheduleReconnect();
            }
        });

        // 连接错误
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket 连接错误:', error);
            this.reconnectAttempts++;

            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }

            // 达到最大重连次数
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('达到最大重连次数，停止重连');
                this.showMessage('error', '连接失败，请刷新页面重试');
            }
        });

        // 接收进度更新
        this.socket.on('progress', (data) => {
            this.handleProgressUpdate(data);
        });

        // 心跳响应
        this.socket.on('pong', (data) => {
            console.debug('收到心跳响应:', data);
        });

        // 连接确认
        this.socket.on('connected', (data) => {
            console.log('连接确认:', data);
        });
    }

    /**
     * 加入任务房间（订阅任务进度）
     * @param {string} taskId - 任务ID
     */
    joinTaskRoom(taskId) {
        if (!this.socket || !this.state.connected) {
            console.warn('WebSocket 未连接，无法加入房间');
            return;
        }

        this.socket.emit('join', { task_id: taskId }, (response) => {
            if (response && response.status === 'success') {
                console.log('成功加入任务房间:', taskId);
                this.state.taskId = taskId;
            } else {
                console.error('加入任务房间失败:', response);
            }
        });
    }

    /**
     * 离开任务房间（取消订阅任务进度）
     * @param {string} taskId - 任务ID
     */
    leaveTaskRoom(taskId) {
        if (!this.socket || !this.state.connected) {
            return;
        }

        this.socket.emit('leave', { task_id: taskId }, (response) => {
            if (response && response.status === 'success') {
                console.log('成功离开任务房间:', taskId);
                if (this.state.taskId === taskId) {
                    this.state.taskId = null;
                }
            }
        });
    }

    /**
     * 处理进度更新
     * @param {Object} data - 进度数据
     */
    handleProgressUpdate(data) {
        console.log('收到进度更新:', data);

        const { task_id, status, progress, message, details, timestamp } = data;

        // 更新进度
        this.updateProgress(progress, {
            status: status,
            statusText: message,
            stage: status,
            details: details
        });

        // 处理特殊状态
        if (status === 'completed') {
            this.complete(message || '生成完成！');
        } else if (status === 'failed') {
            this.fail(message || '生成失败');
        } else if (status === 'cancelled') {
            this.cancel();
        }
    }

    /**
     * 启动心跳检测
     */
    startHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }

        this.heartbeatTimer = setInterval(() => {
            if (this.socket && this.state.connected) {
                this.socket.emit('ping');
            }
        }, this.options.heartbeatInterval);
    }

    /**
     * 停止心跳检测
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * 计划重连
     */
    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`将在 ${this.options.reconnectDelay}ms 后重连...`);
            this.reconnectTimer = setTimeout(() => {
                if (this.socket) {
                    this.socket.connect();
                }
            }, this.options.reconnectDelay);
        }
    }

    /**
     * 断开 WebSocket 连接
     */
    disconnectWebSocket() {
        // 停止心跳
        this.stopHeartbeat();

        // 清除重连定时器
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // 断开连接
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }

        this.state.connected = false;
    }

    /**
     * 渲染进度条HTML
     */
    render() {
        const html = `
            <div class="progress-container hidden">
                <div class="progress-header">
                    <div class="progress-title">生成进度</div>
                    <div class="progress-status">
                        <span class="progress-status-icon">⏳</span>
                        <span class="progress-status-text">准备中...</span>
                    </div>
                </div>

                ${this.options.showStages ? this.renderStages() : ''}

                <div class="progress-bar-wrapper">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>

                <div class="progress-info">
                    <span class="progress-percentage">0%</span>
                    ${this.options.showTime ? '<span class="progress-time"><span class="progress-time-icon">⏱️</span><span class="progress-time-text">计算中...</span></span>' : ''}
                </div>

                ${this.options.showDetails ? this.renderDetails() : ''}

                <div class="progress-actions">
                    ${this.options.allowCancel ? '<button class="progress-button cancel" data-action="cancel"><span>✖️</span><span>取消</span></button>' : ''}
                </div>

                <div class="progress-message hidden"></div>
            </div>
        `;

        this.container.innerHTML = html;
        this.cacheElements();
    }

    /**
     * 渲染阶段指示器
     */
    renderStages() {
        return `
            <div class="progress-stages">
                <div class="progress-stage" data-stage="content">
                    <span class="progress-stage-icon">📝</span>
                    <span>生成文案</span>
                </div>
                <div class="progress-stage" data-stage="image">
                    <span class="progress-stage-icon">🖼️</span>
                    <span>生成图片</span>
                </div>
                <div class="progress-stage" data-stage="complete">
                    <span class="progress-stage-icon">✅</span>
                    <span>完成</span>
                </div>
            </div>
        `;
    }

    /**
     * 渲染详细信息
     */
    renderDetails() {
        return `
            <div class="progress-details hidden">
                <div class="progress-detail-item">
                    <span class="progress-detail-label">当前任务：</span>
                    <span class="progress-detail-value" data-detail="current">-</span>
                </div>
                <div class="progress-detail-item">
                    <span class="progress-detail-label">已完成：</span>
                    <span class="progress-detail-value" data-detail="completed">0</span>
                </div>
                <div class="progress-detail-item">
                    <span class="progress-detail-label">总数：</span>
                    <span class="progress-detail-value" data-detail="total">0</span>
                </div>
            </div>
        `;
    }

    /**
     * 缓存DOM元素
     */
    cacheElements() {
        this.elements = {
            container: this.container.querySelector('.progress-container'),
            statusIcon: this.container.querySelector('.progress-status-icon'),
            statusText: this.container.querySelector('.progress-status-text'),
            bar: this.container.querySelector('.progress-bar'),
            percentage: this.container.querySelector('.progress-percentage'),
            timeText: this.container.querySelector('.progress-time-text'),
            details: this.container.querySelector('.progress-details'),
            stages: this.container.querySelectorAll('.progress-stage'),
            actions: this.container.querySelector('.progress-actions'),
            message: this.container.querySelector('.progress-message')
        };
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 取消按钮
        const cancelBtn = this.container.querySelector('[data-action="cancel"]');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.handleCancel());
        }

        // 重试按钮（动态添加）
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="retry"]')) {
                this.handleRetry();
            }
        });
    }

    /**
     * 显示进度条
     */
    show() {
        this.elements.container.classList.remove('hidden');
    }

    /**
     * 隐藏进度条
     */
    hide() {
        this.elements.container.classList.add('hidden');
    }

    /**
     * 开始进度
     * @param {Object} options - 开始选项
     */
    start(options = {}) {
        this.state.status = 'started';
        this.state.startTime = Date.now();
        this.state.progress = 0;
        this.state.details = options.details || {};

        // 设置任务ID
        if (options.taskId) {
            this.state.taskId = options.taskId;
            // 加入任务房间以接收进度更新
            this.joinTaskRoom(options.taskId);
        }

        this.show();
        this.updateStatus('started', '开始生成...');
        this.updateProgress(0);

        if (this.options.showDetails && options.details) {
            this.updateDetails(options.details);
        }
    }

    /**
     * 更新进度
     * @param {number} progress - 进度值（0-100）
     * @param {Object} data - 进度数据
     */
    updateProgress(progress, data = {}) {
        this.state.progress = Math.min(100, Math.max(0, progress));
        
        // 更新进度条
        this.elements.bar.style.width = `${this.state.progress}%`;
        this.elements.percentage.textContent = `${Math.round(this.state.progress)}%`;

        // 更新状态
        if (data.status) {
            this.updateStatus(data.status, data.statusText);
        }

        // 更新阶段
        if (data.stage) {
            this.updateStage(data.stage);
        }

        // 更新详细信息
        if (data.details) {
            this.updateDetails(data.details);
        }

        // 更新剩余时间
        if (this.options.showTime) {
            this.updateTime();
        }
    }

    /**
     * 更新状态
     * @param {string} status - 状态
     * @param {string} text - 状态文字
     */
    updateStatus(status, text) {
        this.state.status = status;

        // 更新图标
        const icons = {
            idle: '⏳',
            started: '🚀',
            generating_content: '📝',
            generating_image: '🖼️',
            completed: '✅',
            failed: '❌',
            cancelled: '⚠️'
        };

        this.elements.statusIcon.textContent = icons[status] || '⏳';
        this.elements.statusIcon.className = `progress-status-icon ${status}`;
        this.elements.statusText.textContent = text;

        // 更新进度条颜色
        this.elements.bar.className = `progress-bar ${status}`;
    }

    /**
     * 更新阶段
     * @param {string} stage - 阶段名称
     */
    updateStage(stage) {
        this.state.stage = stage;

        if (!this.options.showStages) return;

        // 重置所有阶段
        this.elements.stages.forEach(el => {
            el.classList.remove('active', 'completed');
        });

        // 更新当前阶段
        const stageMap = {
            'generating_content': 'content',
            'generating_image': 'image',
            'completed': 'complete'
        };

        const currentStage = stageMap[stage];
        if (currentStage) {
            const stageEl = this.container.querySelector(`[data-stage="${currentStage}"]`);
            if (stageEl) {
                stageEl.classList.add('active');

                // 标记之前的阶段为已完成
                let prev = stageEl.previousElementSibling;
                while (prev && prev.classList.contains('progress-stage')) {
                    prev.classList.add('completed');
                    prev = prev.previousElementSibling;
                }
            }
        }
    }

    /**
     * 更新详细信息
     * @param {Object} details - 详细信息
     */
    updateDetails(details) {
        if (!this.options.showDetails) return;

        this.state.details = { ...this.state.details, ...details };
        this.elements.details.classList.remove('hidden');

        // 更新各个字段
        Object.keys(details).forEach(key => {
            const el = this.container.querySelector(`[data-detail="${key}"]`);
            if (el) {
                el.textContent = details[key];
                
                // 高亮当前任务
                if (key === 'current') {
                    el.classList.add('active');
                }
            }
        });
    }

    /**
     * 更新剩余时间
     */
    updateTime() {
        if (!this.state.startTime || this.state.progress === 0) {
            this.elements.timeText.textContent = '计算中...';
            return;
        }

        const elapsed = (Date.now() - this.state.startTime) / 1000; // 秒
        const estimated = (elapsed / this.state.progress) * 100;
        const remaining = Math.max(0, estimated - elapsed);

        this.elements.timeText.textContent = this.formatTime(remaining);
    }

    /**
     * 格式化时间
     * @param {number} seconds - 秒数
     * @returns {string} 格式化的时间字符串
     */
    formatTime(seconds) {
        if (seconds < 60) {
            return `剩余 ${Math.round(seconds)} 秒`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.round(seconds % 60);
            return `剩余 ${minutes} 分 ${secs} 秒`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `剩余 ${hours} 小时 ${minutes} 分`;
        }
    }

    /**
     * 完成进度
     * @param {string} message - 完成消息
     */
    complete(message = '生成完成！') {
        this.state.status = 'completed';
        this.state.progress = 100;

        this.updateProgress(100, {
            status: 'completed',
            statusText: message,
            stage: 'completed'
        });

        this.showMessage('success', message);
        this.updateActions('completed');

        if (this.callbacks.onComplete) {
            this.callbacks.onComplete();
        }

        if (this.options.autoHide) {
            setTimeout(() => this.hide(), this.options.autoHideDelay);
        }
    }

    /**
     * 失败
     * @param {string} message - 错误消息
     */
    fail(message = '生成失败') {
        this.state.status = 'failed';

        this.updateStatus('failed', message);
        this.showMessage('error', message);
        this.updateActions('failed');
    }

    /**
     * 取消
     */
    cancel() {
        this.state.status = 'cancelled';

        this.updateStatus('cancelled', '已取消');
        this.showMessage('warning', '操作已取消');
        this.updateActions('cancelled');
    }

    /**
     * 显示消息
     * @param {string} type - 消息类型（success, error, warning）
     * @param {string} text - 消息文本
     */
    showMessage(type, text) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️'
        };

        this.elements.message.className = `progress-message ${type}`;
        this.elements.message.innerHTML = `
            <span class="progress-message-icon">${icons[type]}</span>
            <span>${text}</span>
        `;
        this.elements.message.classList.remove('hidden');
    }

    /**
     * 隐藏消息
     */
    hideMessage() {
        this.elements.message.classList.add('hidden');
    }

    /**
     * 更新操作按钮
     * @param {string} status - 状态
     */
    updateActions(status) {
        const actionsHtml = {
            completed: `
                <button class="progress-button download" data-action="download">
                    <span>⬇️</span><span>下载结果</span>
                </button>
            `,
            failed: `
                <button class="progress-button retry" data-action="retry">
                    <span>🔄</span><span>重试</span>
                </button>
            `,
            cancelled: `
                <button class="progress-button retry" data-action="retry">
                    <span>🔄</span><span>重新开始</span>
                </button>
            `
        };

        if (actionsHtml[status]) {
            this.elements.actions.innerHTML = actionsHtml[status];
        }
    }

    /**
     * 处理取消
     */
    handleCancel() {
        // 通过 WebSocket 发送取消请求
        if (this.socket && this.state.connected && this.state.taskId) {
            this.socket.emit('cancel_task', { task_id: this.state.taskId }, (response) => {
                if (response && response.status === 'success') {
                    console.log('任务取消成功');
                } else {
                    console.error('任务取消失败:', response);
                }
            });
        }

        // 执行回调
        if (this.callbacks.onCancel) {
            this.callbacks.onCancel();
        }

        this.cancel();
    }

    /**
     * 处理重试
     */
    handleRetry() {
        if (this.callbacks.onRetry) {
            this.callbacks.onRetry();
        }
        this.reset();
    }

    /**
     * 重置进度条
     */
    reset() {
        // 离开当前任务房间
        if (this.state.taskId) {
            this.leaveTaskRoom(this.state.taskId);
        }

        this.state = {
            progress: 0,
            status: 'idle',
            stage: '',
            startTime: null,
            estimatedTime: null,
            details: {},
            taskId: null,
            connected: this.state.connected  // 保持连接状态
        };

        this.updateProgress(0);
        this.updateStatus('idle', '准备中...');
        this.hideMessage();
        this.render();
    }

    /**
     * 设置回调函数
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    on(event, callback) {
        if (this.callbacks.hasOwnProperty(`on${event.charAt(0).toUpperCase()}${event.slice(1)}`)) {
            this.callbacks[`on${event.charAt(0).toUpperCase()}${event.slice(1)}`] = callback;
        }
    }

    /**
     * 获取连接状态
     * @returns {boolean} 是否已连接
     */
    isConnected() {
        return this.state.connected;
    }

    /**
     * 获取当前任务ID
     * @returns {string|null} 任务ID
     */
    getTaskId() {
        return this.state.taskId;
    }

    /**
     * 销毁进度条实例
     */
    destroy() {
        // 断开 WebSocket
        this.disconnectWebSocket();

        // 清理定时器
        this.stopHeartbeat();
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        // 清理 DOM
        if (this.container) {
            this.container.innerHTML = '';
        }

        // 清理状态
        this.state = null;
        this.callbacks = null;
        this.elements = null;
    }
}

// 导出到全局
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressBar;
} else {
    window.ProgressBar = ProgressBar;
}
