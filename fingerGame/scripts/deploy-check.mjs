import { access, stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = fileURLToPath(new URL('..', import.meta.url));
const requiredFiles = [
    'index.html',
    'frontend/config.js',
    'js/app.bundle.js',
    'backend/server.mjs',
    'infra/nginx/finger.lordlong.cn.conf',
    'deploy/systemd/pinyin-explorer-api.service'
];

for (const relativePath of requiredFiles) {
    const absolutePath = resolve(projectRoot, relativePath);
    await access(absolutePath);
    const metadata = await stat(absolutePath);
    if (!metadata.isFile() || metadata.size === 0) {
        throw new Error(`部署文件无效：${relativePath}`);
    }
}

console.log(`部署前检查通过：${requiredFiles.length} 个关键文件`);
