import assert from 'node:assert/strict';
import test from 'node:test';

import { PinyinData } from '../data/pinyin-data.js';
import { WordsData } from '../data/words-data.js';
import { Storage } from '../js/storage.js';
import { Utils } from '../js/utils.js';

const memory = new Map();
globalThis.localStorage = {
    getItem: key => memory.has(key) ? memory.get(key) : null,
    setItem: (key, value) => memory.set(key, String(value)),
    removeItem: key => memory.delete(key)
};

test('工具函数可以稳定处理时间和拼音输入', () => {
    assert.equal(Utils.formatTime(300), '5:00');
    assert.equal(Utils.formatTime(-1), '0:00');
    assert.equal(Utils.normalizePinyinInput('cǜ lüè'), 'CVLVE');
    assert.equal(Utils.randomChoice([]), undefined);
});

test('新用户默认使用中文拼音读音', () => {
    assert.equal(Storage.DEFAULT_SETTINGS.letterLanguage, 'zh');
});

test('词库数据可以转换为键盘可输入的字母序列', () => {
    assert.ok(PinyinData.combinations.length > 0);
    assert.ok(Object.values(WordsData.grades).flat().length > 0);

    for (const combination of PinyinData.combinations) {
        assert.match(
            Utils.normalizePinyinInput(`${combination.shengmu}${combination.yunmu}`),
            /^[A-Z]+$/
        );
    }
});

test('存储层可以容错坏数据并保持分数为有效数字', () => {
    memory.set(Storage.KEYS.USERS, '{bad json');
    assert.deepEqual(Storage.getUsers(), []);

    const user = Storage.createUser('<测试玩家>', 'cat');
    assert.ok(user?.id);
    const result = Storage.recordGameResult(user.id, 'letters', 10, 1, 0, ['q']);

    assert.equal(result.user.totalScore, 10);
    assert.equal(result.user.gamesPlayed, 1);
    assert.equal(result.user.errorLetters.Q, 1);
    assert.equal(Storage.recordGameResult(user.id, 'unknown', 10, 1, 0), null);
    const safeResult = Storage.recordGameResult(user.id, 'letters', -10, 1, 0, ['LONG', '1']);
    assert.equal(safeResult.user.totalScore, 10);
    assert.equal(safeResult.user.errorLetters.LONG, undefined);
});

test('存储层可以归一化空用户记录并容忍写入失败', () => {
    memory.set(Storage.KEYS.USERS, JSON.stringify([null, 42, { id: 'safe-user', name: '安全' }]));
    const users = Storage.getUsers();
    assert.equal(users.length, 3);
    assert.equal(users[2].id, 'safe-user');
    assert.deepEqual(users[2].highScores, { letters: 0, pinyin: 0, words: 0 });

    const originalStorage = globalThis.localStorage;
    globalThis.localStorage = {
        getItem: () => null,
        setItem: () => { throw new Error('quota exceeded'); },
        removeItem: () => { throw new Error('readonly'); }
    };
    try {
        assert.equal(Storage.createUser('无法保存', 'cat'), null);
        assert.equal(Storage.getCurrentUser(), null);
    } finally {
        globalThis.localStorage = originalStorage;
    }
});
