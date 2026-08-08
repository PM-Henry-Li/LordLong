import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApiHandler } from './src/http.mjs';
import { createResultStore } from './src/store.mjs';

const projectRoot = resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const port = Number(process.env.PORT || 8080);
const host = process.env.HOST || '127.0.0.1';
const allowedOrigins = String(
    process.env.ALLOWED_ORIGINS || 'https://finger.lordlong.cn,http://127.0.0.1:4173,http://localhost:4173'
).split(',').map(origin => origin.trim()).filter(Boolean);
const dataFile = process.env.RESULTS_FILE || resolve(projectRoot, 'backend/data/results.json');

const store = createResultStore({ filePath: dataFile });
const server = createServer(createApiHandler({
    store,
    allowedOrigins,
    appVersion: process.env.APP_VERSION || '1.1.0'
}));

server.requestTimeout = 10_000;
server.headersTimeout = 12_000;
server.keepAliveTimeout = 5_000;

server.listen(port, host, () => {
    console.log(`拼音探险家 API 已启动：http://${host}:${port}`);
});

function shutdown(signal) {
    console.log(`收到 ${signal}，正在关闭 API 服务...`);
    server.close(error => {
        if (error) {
            console.error(error);
            process.exitCode = 1;
        }
    });
}

process.once('SIGTERM', () => shutdown('SIGTERM'));
process.once('SIGINT', () => shutdown('SIGINT'));
