/*
 * 前端运行时配置。
 *
 * 生产环境由 Nginx 将 /api 反向代理到独立 API 服务，因此默认使用同源地址。
 * 本地使用 `npm run dev` 时，静态前端在 4173 端口，API 在 8080 端口，需要显式跨端口访问。
 */
(function configurePinyinExplorer() {
    const isLocalDevelopment = ['localhost', '127.0.0.1', '[::1]']
        .includes(window.location.hostname);

    window.__PINYIN_EXPLORER_CONFIG__ = {
        apiBaseUrl: isLocalDevelopment && window.location.port === '4173'
            ? 'http://127.0.0.1:8080/api'
            : '/api',
        requestTimeoutMs: 5000,
        appVersion: '1.1.0'
    };
}());
