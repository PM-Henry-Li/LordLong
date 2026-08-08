import assert from 'node:assert/strict';
import test from 'node:test';

import { Api } from '../js/api.js';

test('前端 API 客户端按运行时配置请求并返回 JSON', async () => {
    const originalFetch = globalThis.fetch;
    let receivedUrl;
    let receivedOptions;

    globalThis.fetch = async (url, options) => {
        receivedUrl = url;
        receivedOptions = options;
        return {
            ok: true,
            async json() {
                return { accepted: true };
            }
        };
    };

    try {
        Api.init({ apiBaseUrl: 'https://finger.lordlong.cn/api', requestTimeoutMs: 1000 });
        const result = await Api.syncGameResult({ userId: 'u1', mode: 'letters', score: 10 });

        assert.deepEqual(result, { accepted: true });
        assert.equal(receivedUrl, 'https://finger.lordlong.cn/api/game-results');
        assert.equal(receivedOptions.method, 'POST');
        assert.equal(receivedOptions.headers['Content-Type'], 'application/json');
    } finally {
        globalThis.fetch = originalFetch;
    }
});

test('前端 API 网络异常时返回 null，不阻断离线模式', async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => { throw new Error('offline'); };

    try {
        Api.init({ apiBaseUrl: 'http://127.0.0.1:1/api', requestTimeoutMs: 1000 });
        assert.equal(await Api.health(), null);
    } finally {
        globalThis.fetch = originalFetch;
    }
});
