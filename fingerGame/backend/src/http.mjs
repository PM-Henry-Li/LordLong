import { validateGameResult } from './validation.mjs';

const JSON_HEADERS = {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store'
};

function sendJson(response, statusCode, payload, extraHeaders = {}) {
    response.writeHead(statusCode, { ...JSON_HEADERS, ...extraHeaders });
    response.end(JSON.stringify(payload));
}

function readJson(request, maxBytes = 64 * 1024) {
    return new Promise((resolve, reject) => {
        let body = '';
        let size = 0;
        let settled = false;

        const fail = error => {
            if (settled) return;
            settled = true;
            reject(error);
        };

        request.setEncoding('utf8');
        request.on('data', chunk => {
            size += Buffer.byteLength(chunk);
            if (size > maxBytes) {
                fail(Object.assign(new Error('请求体过大'), { statusCode: 413 }));
                request.destroy?.();
                return;
            }
            body += chunk;
        });
        request.on('end', () => {
            if (settled) return;
            settled = true;
            try {
                resolve(body ? JSON.parse(body) : {});
            } catch {
                reject(Object.assign(new Error('请求体不是有效 JSON'), { statusCode: 400 }));
            }
        });
        request.on('error', fail);
    });
}

function allowOrigin(origin, allowedOrigins) {
    if (!origin) return undefined;
    if (allowedOrigins.includes('*')) return '*';
    return allowedOrigins.includes(origin) ? origin : undefined;
}

export function createApiHandler({
    store,
    allowedOrigins = [],
    appVersion = '1.1.0'
}) {
    return async (request, response) => {
        const url = new URL(request.url || '/', 'http://127.0.0.1');
        const origin = allowOrigin(request.headers.origin, allowedOrigins);
        const corsHeaders = origin
            ? {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                Vary: 'Origin'
            }
            : {};

        if (request.method === 'OPTIONS') {
            response.writeHead(204, corsHeaders);
            response.end();
            return;
        }

        try {
            if (request.method === 'GET' && url.pathname === '/api/health') {
                sendJson(response, 200, {
                    status: 'ok',
                    service: 'pinyin-explorer-api',
                    version: appVersion,
                    timestamp: new Date().toISOString()
                }, corsHeaders);
                return;
            }

            if (request.method === 'GET' && url.pathname === '/api/config') {
                sendJson(response, 200, {
                    apiVersion: 'v1',
                    features: { resultSync: true, leaderboard: true }
                }, corsHeaders);
                return;
            }

            if (request.method === 'GET' && url.pathname === '/api/leaderboard') {
                const leaderboard = await store.leaderboard(url.searchParams.get('limit'));
                sendJson(response, 200, { items: leaderboard }, corsHeaders);
                return;
            }

            if (request.method === 'POST' && url.pathname === '/api/game-results') {
                const input = await readJson(request);
                const result = validateGameResult(input);
                if (!result.ok) {
                    sendJson(response, 400, { error: result.error }, corsHeaders);
                    return;
                }
                const event = await store.append(result.value);
                sendJson(response, 202, { accepted: true, id: event.id }, corsHeaders);
                return;
            }

            sendJson(response, 404, { error: '接口不存在' }, corsHeaders);
        } catch (error) {
            const statusCode = Number(error.statusCode) || 500;
            sendJson(response, statusCode, {
                error: statusCode === 500 ? '服务器内部错误' : error.message
            }, corsHeaders);
        }
    };
}
