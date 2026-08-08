import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const projectRoot = resolve(fileURLToPath(new URL('..', import.meta.url)));
const children = [
    spawn(process.execPath, ['backend/server.mjs'], {
        cwd: projectRoot,
        stdio: 'inherit',
        env: { ...process.env, HOST: '127.0.0.1', PORT: '8080' }
    }),
    spawn('python3', ['-m', 'http.server', '4173', '--bind', '127.0.0.1'], {
        cwd: projectRoot,
        stdio: 'inherit'
    })
];

let shuttingDown = false;
function shutdown(code = 0) {
    if (shuttingDown) return;
    shuttingDown = true;
    for (const child of children) child.kill('SIGTERM');
    setTimeout(() => process.exit(code), 300);
}

for (const child of children) {
    child.once('exit', (code, signal) => {
        if (!shuttingDown && code !== 0 && signal !== 'SIGTERM') shutdown(code || 1);
    });
}

process.once('SIGINT', () => shutdown(0));
process.once('SIGTERM', () => shutdown(0));
