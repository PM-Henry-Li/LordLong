import { readdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const sourceDirs = ['js', 'data', 'backend', 'backend/src', 'frontend'];
const files = [];

for (const directory of sourceDirs) {
    const entries = await readdir(directory, { withFileTypes: true });
    files.push(...entries
        .filter(entry => entry.isFile() && entry.name.endsWith('.js'))
        .map(entry => join(directory, entry.name)));
}

for (const file of files.sort()) {
    const result = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
    if (result.status !== 0) {
        process.stderr.write(result.stderr || `语法检查失败: ${file}\n`);
        process.exit(result.status || 1);
    }
}

console.log(`语法检查通过：${files.length} 个模块`);
