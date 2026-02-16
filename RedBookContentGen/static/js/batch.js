/**
 * 批量处理脚本
 * 处理批量内容生成的前端逻辑
 */

// 全局状态
let batchState = {
    inputMode: 'text',  // 输入模式：text 或 file
    tasks: [],          // 任务列表
    batchResult: null,  // 批量生成结果
    isGenerating: false // 是否正在生成
};

/**
 * 切换输入模式
 * @param {string} mode - 输入模式：text 或 file
 */
function switchInputMode(mode) {
    batchState.inputMode = mode;
    
    // 更新按钮状态
    document.getElementById('textInputBtn').classList.toggle('active', mode === 'text');
    document.getElementById('fileInputBtn').classList.toggle('active', mode === 'file');
    
    // 切换显示区域
    document.getElementById('textInputArea').style.display = mode === 'text' ? 'block' : 'none';
    document.getElementById('fileInputArea').style.display = mode === 'file' ? 'block' : 'none';
}

/**
 * 处理文件上传
 * @param {Event} event - 文件上传事件
 */
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileInfo = document.getElementById('fileInfo');
    const fileUpload = document.querySelector('.file-upload');
    
    try {
        fileUpload.classList.add('active');
        fileInfo.textContent = `正在读取文件: ${file.name}...`;
        
        let inputs = [];
        
        // 根据文件类型读取
        if (file.name.endsWith('.txt')) {
            inputs = await readTextFile(file);
        } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            errorHandler.showToast('Excel 文件解析功能开发中，请使用 TXT 文件', 'info');
            return;
        } else {
            throw new Error('不支持的文件格式');
        }
        
        // 验证输入数量
        if (inputs.length === 0) {
            throw new Error('文件内容为空');
        }
        
        if (inputs.length > 50) {
            throw new Error(`输入数量超过限制（${inputs.length}/50）`);
        }
        
        // 更新任务列表
        batchState.tasks = inputs.map((text, index) => ({
            index,
            text,
            status: 'pending'
        }));
        
        renderTaskList();
        
        fileInfo.innerHTML = `<i class="fa-solid fa-check-circle" style="color: #4caf50;"></i> 成功读取 ${inputs.length} 条内容`;
        fileUpload.classList.remove('active');
        
    } catch (error) {
        console.error('文件读取失败:', error);
        fileInfo.innerHTML = `<i class="fa-solid fa-exclamation-circle" style="color: #f44336;"></i> ${error.message}`;
        fileUpload.classList.add('error');
        errorHandler.showToast(error.message, 'error');
    }
}

/**
 * 读取文本文件
 * @param {File} file - 文件对象
 * @returns {Promise<string[]>} 文本行数组
 */
function readTextFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const text = e.target.result;
            const lines = text.split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0);
            resolve(lines);
        };
        
        reader.onerror = () => {
            reject(new Error('文件读取失败'));
        };
        
        reader.readAsText(file, 'UTF-8');
    });
}

/**
 * 清空输入
 */
function clearInput() {
    if (batchState.inputMode === 'text') {
        document.getElementById('batchInput').value = '';
    } else {
        document.getElementById('fileInput').value = '';
        document.getElementById('fileInfo').textContent = '';
        document.querySelector('.file-upload').classList.remove('active', 'error');
    }
    
    batchState.tasks = [];
    renderTaskList();
}

/**
 * 开始批量生成
 */
async function startBatchGeneration() {
    // 获取输入
    let inputs = [];
    
    if (batchState.inputMode === 'text') {
        const text = document.getElementById('batchInput').value.trim();
        if (!text) {
            errorHandler.showToast('请输入内容', 'warning');
            return;
        }
        
        inputs = text.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
    } else {
        inputs = batchState.tasks.map(task => task.text);
    }
    
    // 验证输入
    if (inputs.length === 0) {
        errorHandler.showToast('请输入至少一条内容', 'warning');
        return;
    }
    
    if (inputs.length > 50) {
        errorHandler.showToast(`输入数量超过限制（${inputs.length}/50）`, 'error');
        return;
    }
    
    // 更新任务列表
    batchState.tasks = inputs.map((text, index) => ({
        index,
        text,
        status: 'pending'
    }));
    
    renderTaskList();
    
    // 禁用生成按钮
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 生成中...';
    
    batchState.isGenerating = true;
    
    // 显示进度区域
    document.getElementById('progressSection').style.display = 'block';
    
    try {
        // 获取配置
        const count = parseInt(document.getElementById('imageCount').value);
        
        // 调用批量生成 API
        const response = await fetch('/api/batch/generate_content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                inputs: inputs,
                count: count
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            batchState.batchResult = result.data;
            
            // 更新任务状态
            result.data.results.forEach(item => {
                const task = batchState.tasks[item.index];
                if (task) {
                    task.status = item.status;
                    task.data = item.data;
                    task.error = item.error;
                }
            });
            
            renderTaskList();
            renderBatchProgress(result.data);
            renderResults(result.data);
            
            // 显示结果区域
            document.getElementById('resultsSection').style.display = 'block';
            
            errorHandler.showToast('批量生成完成！', 'success');
            
        } else {
            throw new Error(result.error?.message || '批量生成失败');
        }
        
    } catch (error) {
        console.error('批量生成失败:', error);
        errorHandler.showToast(error.message, 'error');
        
        // 重置任务状态
        batchState.tasks.forEach(task => {
            if (task.status === 'processing') {
                task.status = 'failed';
                task.error = error.message;
            }
        });
        
        renderTaskList();
        
    } finally {
        // 恢复生成按钮
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> 开始批量生成';
        batchState.isGenerating = false;
    }
}

/**
 * 渲染任务列表
 */
function renderTaskList() {
    const container = document.getElementById('taskListContainer');
    const taskCount = document.getElementById('taskCount');
    
    if (batchState.tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon"><i class="fa-regular fa-clipboard"></i></div>
                <h3>暂无任务</h3>
                <p>请在左侧输入内容并开始生成</p>
            </div>
        `;
        taskCount.textContent = '0 条任务';
        return;
    }
    
    taskCount.textContent = `${batchState.tasks.length} 条任务`;
    
    const taskListHTML = `
        <div class="task-list">
            ${batchState.tasks.map(task => `
                <div class="task-item ${task.status}">
                    <div class="task-index">${task.index + 1}</div>
                    <div class="task-content">
                        <div class="task-text" title="${escapeHtml(task.text)}">${escapeHtml(task.text)}</div>
                    </div>
                    <div class="task-status">
                        ${getTaskStatusIcon(task.status)}
                        <span>${getTaskStatusText(task.status)}</span>
                    </div>
                    ${task.status === 'failed' ? `
                        <div class="task-actions">
                            <button class="task-action-btn retry" onclick="retryTask(${task.index})" title="重试">
                                <i class="fa-solid fa-rotate-right"></i>
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = taskListHTML;
}

/**
 * 获取任务状态图标
 * @param {string} status - 任务状态
 * @returns {string} 图标 HTML
 */
function getTaskStatusIcon(status) {
    const icons = {
        pending: '<i class="fa-regular fa-clock task-status-icon"></i>',
        processing: '<i class="fa-solid fa-spinner fa-spin task-status-icon"></i>',
        success: '<i class="fa-solid fa-check-circle task-status-icon"></i>',
        failed: '<i class="fa-solid fa-exclamation-circle task-status-icon"></i>'
    };
    return icons[status] || icons.pending;
}

/**
 * 获取任务状态文本
 * @param {string} status - 任务状态
 * @returns {string} 状态文本
 */
function getTaskStatusText(status) {
    const texts = {
        pending: '等待中',
        processing: '生成中',
        success: '成功',
        failed: '失败'
    };
    return texts[status] || '未知';
}

/**
 * 渲染批量进度
 * @param {Object} batchResult - 批量生成结果
 */
function renderBatchProgress(batchResult) {
    const container = document.getElementById('batchProgress');
    const summary = batchResult.summary;
    
    const successRate = summary.total > 0 
        ? Math.round((summary.success / summary.total) * 100) 
        : 0;
    
    const progressHTML = `
        <div class="batch-progress-summary">
            <div class="batch-progress-stats">
                <div class="batch-stat total">
                    <div class="batch-stat-value">${summary.total}</div>
                    <div class="batch-stat-label">总任务数</div>
                </div>
                <div class="batch-stat success">
                    <div class="batch-stat-value">${summary.success}</div>
                    <div class="batch-stat-label">成功</div>
                </div>
                <div class="batch-stat failed">
                    <div class="batch-stat-value">${summary.failed}</div>
                    <div class="batch-stat-label">失败</div>
                </div>
                <div class="batch-stat processing">
                    <div class="batch-stat-value">${successRate}%</div>
                    <div class="batch-stat-label">成功率</div>
                </div>
            </div>
            
            <div class="batch-progress-bar-wrapper">
                <div class="batch-progress-bar" style="width: ${successRate}%"></div>
            </div>
            
            <div class="batch-progress-info">
                <span class="batch-progress-percentage">${successRate}% 完成</span>
                <span>批次ID: ${batchResult.batch_id}</span>
            </div>
        </div>
    `;
    
    container.innerHTML = progressHTML;
}

/**
 * 渲染结果
 * @param {Object} batchResult - 批量生成结果
 */
function renderResults(batchResult) {
    const container = document.getElementById('resultsContainer');
    
    const resultsHTML = `
        <div class="result-cards">
            ${batchResult.results.map(result => `
                <div class="result-card ${result.status}">
                    <div class="result-card-header">
                        <div class="result-card-index">${result.index + 1}</div>
                        <div class="result-card-title">${escapeHtml(result.input_text)}</div>
                        <div class="result-card-status ${result.status}">
                            ${result.status === 'success' ? '✓ 成功' : '✗ 失败'}
                        </div>
                    </div>
                    <div class="result-card-body">
                        ${result.status === 'success' ? `
                            <div class="result-card-input">
                                <strong>标题：</strong>${escapeHtml(result.data.titles[0] || '')}
                            </div>
                            ${result.data.tags && result.data.tags.length > 0 ? `
                                <div class="result-card-tags">
                                    ${result.data.tags.map(tag => `
                                        <span class="result-card-tag">#${escapeHtml(tag)}</span>
                                    `).join('')}
                                </div>
                            ` : ''}
                        ` : `
                            <div class="result-card-error">
                                <i class="fa-solid fa-exclamation-triangle"></i>
                                ${escapeHtml(result.error || '未知错误')}
                            </div>
                        `}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = resultsHTML;
}

/**
 * 重试单个任务
 * @param {number} index - 任务索引
 */
async function retryTask(index) {
    const task = batchState.tasks[index];
    if (!task) return;
    
    task.status = 'processing';
    renderTaskList();
    
    try {
        const count = parseInt(document.getElementById('imageCount').value);
        
        const response = await fetch('/api/generate_content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                input_text: task.text,
                count: count
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            task.status = 'success';
            task.data = result.data;
            task.error = null;
            errorHandler.showToast(`任务 ${index + 1} 重试成功`, 'success');
        } else {
            throw new Error(result.error?.message || '生成失败');
        }
        
    } catch (error) {
        console.error('任务重试失败:', error);
        task.status = 'failed';
        task.error = error.message;
        errorHandler.showToast(`任务 ${index + 1} 重试失败: ${error.message}`, 'error');
    }
    
    renderTaskList();
    
    // 更新批量结果
    if (batchState.batchResult) {
        const resultItem = batchState.batchResult.results.find(r => r.index === index);
        if (resultItem) {
            resultItem.status = task.status;
            resultItem.data = task.data;
            resultItem.error = task.error;
        }
        
        // 重新计算汇总
        const summary = batchState.batchResult.summary;
        summary.success = batchState.tasks.filter(t => t.status === 'success').length;
        summary.failed = batchState.tasks.filter(t => t.status === 'failed').length;
        
        renderBatchProgress(batchState.batchResult);
        renderResults(batchState.batchResult);
    }
}

/**
 * 下载 Excel
 */
async function downloadExcel() {
    if (!batchState.batchResult) {
        errorHandler.showToast('没有可下载的结果', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/batch/export/excel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                batch_result: batchState.batchResult
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || '导出失败');
        }
        
        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${batchState.batchResult.batch_id}_summary.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        errorHandler.showToast('Excel 文件下载成功', 'success');
        
    } catch (error) {
        console.error('Excel 导出失败:', error);
        errorHandler.showToast(error.message, 'error');
    }
}

/**
 * 下载 ZIP
 */
async function downloadZip() {
    if (!batchState.batchResult) {
        errorHandler.showToast('没有可下载的结果', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/batch/export/zip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                batch_result: batchState.batchResult
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || '导出失败');
        }
        
        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${batchState.batchResult.batch_id}_export.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        errorHandler.showToast('ZIP 文件下载成功', 'success');
        
    } catch (error) {
        console.error('ZIP 导出失败:', error);
        errorHandler.showToast(error.message, 'error');
    }
}

/**
 * 转义 HTML
 * @param {string} text - 文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 设置默认输入模式
    switchInputMode('text');
    
    // 文件拖拽上传
    const fileUpload = document.querySelector('.file-upload');
    
    fileUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUpload.classList.add('active');
    });
    
    fileUpload.addEventListener('dragleave', () => {
        fileUpload.classList.remove('active');
    });
    
    fileUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUpload.classList.remove('active');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('fileInput').files = files;
            handleFileUpload({ target: { files: files } });
        }
    });
});
