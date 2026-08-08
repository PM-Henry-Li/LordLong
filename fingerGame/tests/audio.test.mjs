import assert from 'node:assert/strict';
import test from 'node:test';

import { Audio } from '../js/audio.js';

function wait(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

test('本地字母语音播放同步失败时会回退且不会卡住队列', () => {
    const originalWindow = globalThis.window;
    const originalState = {
        enabled: Audio.enabled,
        voicePlayer: Audio.voicePlayer,
        voiceQueue: Audio.voiceQueue,
        voiceQueuePlaying: Audio.voiceQueuePlaying,
        voicePlaybackToken: Audio.voicePlaybackToken
    };
    let fallbackCount = 0;

    class ThrowingAudio {
        pause() {}
        play() { throw new Error('NotAllowedError'); }
    }

    globalThis.window = { Audio: ThrowingAudio };
    Audio.enabled = true;
    Audio.voicePlayer = null;
    Audio.voiceQueue = [];
    Audio.voiceQueuePlaying = false;
    Audio.voicePlaybackToken = 0;

    try {
        assert.equal(Audio.playChineseAsset('啊', () => { fallbackCount += 1; }), true);
        assert.equal(fallbackCount, 1);
        assert.equal(Audio.voiceQueuePlaying, false);
        assert.equal(Audio.voiceQueue.length, 0);
    } finally {
        globalThis.window = originalWindow;
        Object.assign(Audio, originalState);
    }
});

test('切换英文后使用系统英文语音，并在 cancel 后恢复播放', async () => {
    const originalWindow = globalThis.window;
    const originalState = {
        enabled: Audio.enabled,
        letterLanguage: Audio.letterLanguage,
        preferredEnglishVoice: Audio.preferredEnglishVoice,
        voicePlayer: Audio.voicePlayer,
        voiceQueue: Audio.voiceQueue,
        voiceQueuePlaying: Audio.voiceQueuePlaying,
        voicePlaybackToken: Audio.voicePlaybackToken,
        speechRequestId: Audio.speechRequestId
    };
    const utterances = [];
    let cancelCount = 0;
    let resumeCount = 0;

    const speechSynthesis = {
        cancel() { cancelCount += 1; },
        resume() { resumeCount += 1; },
        speak(utterance) { utterances.push(utterance); }
    };
    class MockUtterance {
        constructor(text) {
            this.text = text;
        }
    }

    globalThis.window = {
        speechSynthesis,
        SpeechSynthesisUtterance: MockUtterance
    };
    Audio.enabled = true;
    Audio.letterLanguage = 'en';
    Audio.preferredEnglishVoice = null;
    Audio.voicePlayer = null;
    Audio.voiceQueue = [];
    Audio.voiceQueuePlaying = false;
    Audio.voicePlaybackToken = 0;
    Audio.speechRequestId = 0;

    try {
        Audio.speakLetter('A');
        await wait(50);
        assert.equal(utterances.length, 1);
        assert.equal(utterances[0].text, 'ay');
        assert.ok(cancelCount >= 1);
        assert.ok(resumeCount >= 2);
    } finally {
        globalThis.window = originalWindow;
        Object.assign(Audio, originalState);
    }
});

test('语音预热结束时不会覆盖已经开始的字母音频', async () => {
    const originalWindow = globalThis.window;
    const originalState = {
        enabled: Audio.enabled,
        volume: Audio.volume,
        voicePlayer: Audio.voicePlayer,
        voicePlaybackPrimed: Audio.voicePlaybackPrimed,
        voicePlaybackToken: Audio.voicePlaybackToken
    };
    let pauseCount = 0;

    class PrimingAudio {
        pause() { pauseCount += 1; }
        play() { return Promise.resolve(); }
    }

    globalThis.window = { Audio: PrimingAudio };
    Audio.enabled = true;
    Audio.voicePlayer = null;
    Audio.voicePlaybackPrimed = false;
    Audio.voicePlaybackToken = 0;

    try {
        Audio.primeVoicePlayback();
        Audio.cancelVoicePlayback();
        await wait(0);
        assert.equal(pauseCount, 2);
    } finally {
        globalThis.window = originalWindow;
        Object.assign(Audio, originalState);
    }
});
