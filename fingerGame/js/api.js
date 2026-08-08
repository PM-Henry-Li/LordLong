/* ===============================================
   前后端 API 客户端
   =============================================== */

export const Api = {
    baseUrl: '/api',
    requestTimeoutMs: 5000,
    enabled: true,

    init(config = globalThis.__PINYIN_EXPLORER_CONFIG__ || {}) {
        this.baseUrl = String(config.apiBaseUrl || '/api').replace(/\/$/, '') || '/api';
        this.requestTimeoutMs = Math.max(1000, Number(config.requestTimeoutMs) || 5000);
        this.enabled = config.apiEnabled !== false;
    },

    async request(path, options = {}) {
        if (!this.enabled || typeof globalThis.fetch !== 'function') return null;

        const controller = typeof AbortController === 'function' ? new AbortController() : null;
        const timeout = controller
            ? setTimeout(() => controller.abort(), this.requestTimeoutMs)
            : null;

        try {
            const response = await fetch(`${this.baseUrl}/${String(path).replace(/^\//, '')}`, {
                ...options,
                headers: {
                    Accept: 'application/json',
                    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
                    ...(options.headers || {})
                },
                signal: controller?.signal
            });

            if (!response.ok) return null;
            return await response.json();
        } catch {
            // API 同步是增强能力，网络失败不能阻断离线游戏。
            return null;
        } finally {
            if (timeout) clearTimeout(timeout);
        }
    },

    syncGameResult(payload) {
        return this.request('/game-results', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    health() {
        return this.request('/health');
    }
};
