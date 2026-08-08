import assert from 'node:assert/strict';
import { statSync } from 'node:fs';
import { resolve } from 'node:path';
import test from 'node:test';

import { PinyinData } from '../data/pinyin-data.js';
import { WordsData } from '../data/words-data.js';
import { LetterPinyinSounds, PinyinSpeechMap } from '../data/voice-map.js';
import { VoiceAssets } from '../data/voice-manifest.js';

const assetDirectory = resolve(process.cwd(), 'audio/voice/zh');

function hashText(text) {
    let hash = 2166136261;
    const value = String(text);

    for (let i = 0; i < value.length; i += 1) {
        hash ^= value.charCodeAt(i);
        hash = Math.imul(hash, 16777619);
    }

    return (hash >>> 0).toString(16);
}

test('本地语音资源覆盖字母、拼音和词库内容', () => {
    const requiredTexts = [
        ...Object.values(LetterPinyinSounds),
        ...Object.values(PinyinSpeechMap),
        ...PinyinData.combinations.map(item => item.example),
        ...Object.values(WordsData.grades).flat().map(item => item.hanzi),
        '一声',
        '二声',
        '三声',
        '四声',
        '游戏开始！',
        '还剩一分钟！',
        '请选择一个头像',
        '请输入你的名字'
    ];

    for (const text of requiredTexts) {
        assert.equal(
            VoiceAssets.has(hashText(text)),
            true,
            `缺少本地语音资源：${text}`
        );
    }

    for (const assetKey of VoiceAssets) {
        const assetSize = statSync(resolve(assetDirectory, `${assetKey}.wav`)).size;
        assert.ok(assetSize > 4096, `本地语音资源为空：${assetKey}.wav`);
    }
});
