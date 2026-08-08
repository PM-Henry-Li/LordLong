import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { randomUUID } from 'node:crypto';

function isPlainObject(value) {
    return value && typeof value === 'object' && !Array.isArray(value);
}

export function createResultStore({ filePath = null, maxEntries = 10000 } = {}) {
    let entries = [];
    let loaded = false;
    let writeQueue = Promise.resolve();

    async function load() {
        if (loaded) return;
        loaded = true;
        if (!filePath) return;

        try {
            const data = JSON.parse(await readFile(filePath, 'utf8'));
            if (Array.isArray(data)) entries = data.filter(isPlainObject).slice(-maxEntries);
        } catch (error) {
            if (error.code !== 'ENOENT') {
                console.warn(`无法读取成绩事件存储，已使用空数据：${error.message}`);
            }
        }
    }

    async function persist() {
        if (!filePath) return;
        await mkdir(dirname(filePath), { recursive: true });
        const tempPath = `${filePath}.${process.pid}.tmp`;
        await writeFile(tempPath, `${JSON.stringify(entries, null, 2)}\n`, 'utf8');
        await rename(tempPath, filePath);
    }

    return {
        async append(event) {
            await load();
            const storedEvent = {
                id: randomUUID(),
                receivedAt: new Date().toISOString(),
                ...event
            };
            entries.push(storedEvent);
            if (entries.length > maxEntries) entries = entries.slice(-maxEntries);

            writeQueue = writeQueue.catch(() => {}).then(() => persist());
            await writeQueue;
            return storedEvent;
        },

        async leaderboard(limit = 10) {
            await load();
            const grouped = new Map();
            for (const entry of entries) {
                const current = grouped.get(entry.userId) || {
                    userId: entry.userId,
                    totalScore: 0,
                    gamesPlayed: 0
                };
                current.totalScore += entry.score;
                current.gamesPlayed += 1;
                grouped.set(entry.userId, current);
            }
            return [...grouped.values()]
                .sort((left, right) => right.totalScore - left.totalScore)
                .slice(0, Math.max(1, Math.min(100, Number(limit) || 10)));
        },

        async size() {
            await load();
            return entries.length;
        }
    };
}
