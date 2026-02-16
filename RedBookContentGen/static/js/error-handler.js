/**
 * 错误处理模块
 * 
 * 提供统一的错误提示、Toast 通知和错误对话框功能
 */

class ErrorHandler {
    constructor() {
        this.toastContainer = null;
        this.init();
    }

    /**
     * 初始化错误处理器
     */
    init() {
        // 创建 Toast 容器
        this.createToastContainer();
        
        // 监听全局错误
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event.error);
        });
        
        // 监听未处理的 Promise 拒绝
        window.addEventListener('unhandledrejection', (event) => {
            this.handleGlobalError(event.reason);
        });
    }

    /**
     * 创建 Toast 容器
     */
    createToastContainer() {
        if (this.toastContainer) return;
        
        this.toastContainer = document.createElement('div');
        this.toastContainer.id = 'toast-container';
        this.toastContainer.className = 'toast-container';
        document.body.appendChild(this.toastContainer);
    }

    /**
     * 显示 Toast 通知
     * 
     * @param {string} message - 错误消息
     * @param {string} type - 类型：error, warning, info, success
     * @param {number} duration - 显示时长（毫秒）
     */
    showToast(message, type = 'error', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // 图标
        const icon = this.getIcon(type);
        
        // 内容
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // 添加动画
        setTimeout(() => toast.classList.add('toast-show'), 10);
        
        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.remove('toast-show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    }

    /**
     * 显示错误对话框
     * 
     * @param {Object} error - 错误对象
     * @param {Object} options - 选项
     */
    showErrorDialog(error, options = {}) {
        const {
            title = '错误',
            showDetails = true,
            showRetry = false,
            onRetry = null,
            showHelp = false,
            helpUrl = null
        } = options;
        
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'error-dialog-overlay';
        
        // 创建对话框
        const dialog = document.createElement('div');
        dialog.className = 'error-dialog';
        
        // 解析错误信息
        const errorInfo = this.parseError(error);
        
        // 构建对话框内容
        let dialogHTML = `
            <div class="error-dialog-header">
                <div class="error-dialog-icon">${this.getIcon('error')}</div>
                <h3 class="error-dialog-title">${this.escapeHtml(title)}</h3>
                <button class="error-dialog-close" onclick="this.closest('.error-dialog-overlay').remove()">×</button>
            </div>
            <div class="error-dialog-body">
                <p class="error-dialog-message">${this.escapeHtml(errorInfo.message)}</p>
        `;
        
        // 显示详细信息
        if (showDetails && errorInfo.details) {
            dialogHTML += `
                <div class="error-dialog-details">
                    <strong>详细信息：</strong>
                    <pre>${this.escapeHtml(JSON.stringify(errorInfo.details, null, 2))}</pre>
                </div>
            `;
        }
        
        // 显示修复建议
        if (errorInfo.suggestions && errorInfo.suggestions.length > 0) {
            dialogHTML += `
                <div class="error-dialog-suggestions">
                    <strong>修复建议：</strong>
                    <ul>
                        ${errorInfo.suggestions.map(s => `<li>${this.escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        dialogHTML += `</div><div class="error-dialog-footer">`;
        
        // 重试按钮
        if (showRetry && onRetry) {
            dialogHTML += `
                <button class="btn btn-primary" onclick="errorHandler.retry(this, ${JSON.stringify(onRetry)})">
                    重试
                </button>
            `;
        }
        
        // 帮助链接
        if (showHelp && helpUrl) {
            dialogHTML += `
                <a href="${this.escapeHtml(helpUrl)}" target="_blank" class="btn btn-link">
                    查看帮助文档
                </a>
            `;
        }
        
        dialogHTML += `
            <button class="btn btn-secondary" onclick="this.closest('.error-dialog-overlay').remove()">
                关闭
            </button>
        </div>`;
        
        dialog.innerHTML = dialogHTML;
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        // 添加动画
        setTimeout(() => overlay.classList.add('show'), 10);
    }

    /**
     * 处理 API 错误
     * 
     * @param {Response} response - Fetch Response 对象
     * @returns {Promise<Object>} 错误信息
     */
    async handleApiError(response) {
        let errorData;
        
        try {
            errorData = await response.json();
        } catch (e) {
            errorData = {
                error: {
                    code: 'UNKNOWN_ERROR',
                    message: `HTTP ${response.status}: ${response.statusText}`,
                    severity: 'error'
                }
            };
        }
        
        // 显示错误提示
        if (errorData.error) {
            const { message, severity = 'error' } = errorData.error;
            this.showToast(message, severity);
        }
        
        return errorData;
    }

    /**
     * 处理全局错误
     * 
     * @param {Error} error - 错误对象
     */
    handleGlobalError(error) {
        console.error('全局错误:', error);
        
        // 只在开发环境显示详细错误
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.showToast(error.message || '发生未知错误', 'error');
        } else {
            this.showToast('抱歉，发生了一个错误。请刷新页面重试。', 'error');
        }
    }

    /**
     * 解析错误对象
     * 
     * @param {Object|Error|string} error - 错误
     * @returns {Object} 解析后的错误信息
     */
    parseError(error) {
        if (typeof error === 'string') {
            return {
                message: error,
                code: 'UNKNOWN_ERROR',
                severity: 'error'
            };
        }
        
        if (error instanceof Error) {
            return {
                message: error.message,
                code: 'JAVASCRIPT_ERROR',
                severity: 'error',
                details: {
                    stack: error.stack
                }
            };
        }
        
        if (error && error.error) {
            return {
                message: error.error.message || '发生错误',
                code: error.error.code || 'UNKNOWN_ERROR',
                severity: error.error.severity || 'error',
                details: error.error.details,
                suggestions: error.error.suggestions,
                retryable: error.error.retryable
            };
        }
        
        return {
            message: '发生未知错误',
            code: 'UNKNOWN_ERROR',
            severity: 'error'
        };
    }

    /**
     * 获取图标
     * 
     * @param {string} type - 类型
     * @returns {string} 图标 HTML
     */
    getIcon(type) {
        const icons = {
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️',
            success: '✅'
        };
        return icons[type] || icons.info;
    }

    /**
     * 转义 HTML
     * 
     * @param {string} text - 文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 重试操作
     * 
     * @param {HTMLElement} button - 按钮元素
     * @param {Function} retryFn - 重试函数
     */
    async retry(button, retryFn) {
        button.disabled = true;
        button.textContent = '重试中...';
        
        try {
            await retryFn();
            // 关闭对话框
            button.closest('.error-dialog-overlay').remove();
            this.showToast('操作成功', 'success');
        } catch (error) {
            this.showToast('重试失败: ' + error.message, 'error');
            button.disabled = false;
            button.textContent = '重试';
        }
    }

    /**
     * 显示加载错误
     * 
     * @param {string} message - 错误消息
     */
    showLoadingError(message) {
        this.showToast(message, 'error', 0);
    }

    /**
     * 显示网络错误
     */
    showNetworkError() {
        this.showToast('网络连接失败，请检查您的网络连接', 'error', 0);
    }

    /**
     * 显示超时错误
     */
    showTimeoutError() {
        this.showToast('请求超时，请稍后重试', 'warning');
    }

    /**
     * 显示验证错误
     * 
     * @param {Object} errors - 验证错误对象
     */
    showValidationErrors(errors) {
        if (Array.isArray(errors)) {
            errors.forEach(error => {
                this.showToast(error.message || error, 'warning');
            });
        } else if (typeof errors === 'object') {
            Object.entries(errors).forEach(([field, message]) => {
                this.showToast(`${field}: ${message}`, 'warning');
            });
        } else {
            this.showToast(errors, 'warning');
        }
    }
}

// 创建全局实例
const errorHandler = new ErrorHandler();

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}
