import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test, { after, before } from 'node:test';

import { createApiHandler } from '../backend/src/http.mjs';
import { createResultStore } from '../backend/src/store.mjs';

let tempDirectory;
let store;
let handler;

async function invoke({ method = 'GET', url = '/', headers = {}, body = '' } = {}) {
    const request = new EventEmitter();
    request.method = method;
    request.url = url;
    request.headers = headers;
    request.setEncoding = () => {};

    let responseStatus;
    let responseHeaders;
    let responseBody = '';
    const response = {
        writeHead(statusCode, responseHeadersValue) {
            responseStatus = statusCode;
            responseHeaders = new Headers(responseHeadersValue);
        },
        end(value = '') {
            responseBody += value;
        }
    };

    const pending = handler(request, response);
    if (method === 'POST') {
        await Promise.resolve();
        request.emit('data', body);
        request.emit('end');
    }
    await pending;
    return {
        status: responseStatus,
        headers: responseHeaders,
        body: responseBody ? JSON.parse(responseBody) : null
    };
}

before(async () => {
    tempDirectory = await mkdtemp(join(tmpdir(), 'pinyin-explorer-'));
    store = createResultStore({ filePath: join(tempDirectory, 'results.json') });
    handler = createApiHandler({
        store,
        allowedOrigins: ['https://finger.lordlong.cn']
    });
});

after(async () => {
    await rm(tempDirectory, { recursive: true, force: true });
});

test('API 健康检查返回版本和服务状态', async () => {
    const response = await invoke({ url: '/api/health' });

    assert.equal(response.status, 200);
    assert.equal(response.body.status, 'ok');
    assert.equal(response.body.service, 'pinyin-explorer-api');
});

test('API 拒绝非法成绩并接受合法成绩事件', async () => {
    const invalid = await invoke({
        method: 'POST',
        url: '/api/game-results',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ userId: 'bad id', mode: 'unknown', score: -1 })
    });
    assert.equal(invalid.status, 400);

    const accepted = await invoke({
        method: 'POST',
        url: '/api/game-results',
        headers: {
            'content-type': 'application/json',
            origin: 'https://finger.lordlong.cn'
        },
        body: JSON.stringify({
            userId: 'local-user-1',
            mode: 'letters',
            score: 10,
            correct: 1,
            wrong: 0,
            errorLetters: ['q', 'not-a-letter']
        })
    });

    assert.equal(accepted.status, 202);
    assert.equal(accepted.body.accepted, true);
    assert.match(accepted.body.id, /^[0-9a-f-]{36}$/);
    assert.equal(accepted.headers.get('access-control-allow-origin'), 'https://finger.lordlong.cn');

    const leaderboard = await invoke({ url: '/api/leaderboard?limit=1' });
    assert.deepEqual(leaderboard.body.items[0], {
        userId: 'local-user-1',
        totalScore: 10,
        gamesPlayed: 1
    });

    const persisted = JSON.parse(await readFile(join(tempDirectory, 'results.json'), 'utf8'));
    assert.equal(persisted.length, 1);
    assert.deepEqual(persisted[0].errorLetters, ['Q']);
});
