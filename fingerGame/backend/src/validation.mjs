export const GAME_MODES = new Set(['letters', 'pinyin', 'words']);

const MAX_SCORE = 100000;
const MAX_COUNT = 100000;

function finiteInteger(value, min, max) {
    const number = Number(value);
    return Number.isInteger(number) && number >= min && number <= max ? number : null;
}

export function validateGameResult(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
        return { ok: false, error: '请求体必须是 JSON 对象' };
    }

    const userId = String(input.userId || '').trim();
    if (!/^[A-Za-z0-9_-]{1,128}$/.test(userId)) {
        return { ok: false, error: 'userId 格式不合法' };
    }

    const mode = String(input.mode || '').trim();
    if (!GAME_MODES.has(mode)) {
        return { ok: false, error: 'mode 不受支持' };
    }

    const score = finiteInteger(input.score, 0, MAX_SCORE);
    const correct = finiteInteger(input.correct, 0, MAX_COUNT);
    const wrong = finiteInteger(input.wrong, 0, MAX_COUNT);
    if (score === null || correct === null || wrong === null) {
        return { ok: false, error: 'score、correct、wrong 必须是有效整数' };
    }

    const errorLetters = Array.isArray(input.errorLetters)
        ? input.errorLetters
            .slice(0, 200)
            .map(letter => String(letter || '').trim().toUpperCase())
            .filter(letter => /^[A-Z]$/.test(letter))
        : [];

    return {
        ok: true,
        value: {
            userId,
            mode,
            score,
            correct,
            wrong,
            errorLetters
        }
    };
}
