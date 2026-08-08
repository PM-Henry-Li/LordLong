/* ===============================================
   音效管理
   =============================================== */

import { Storage } from './storage.js';
import { LetterPinyinSounds, PinyinSpeechMap } from '../data/voice-map.js';
import { VoiceAssets } from '../data/voice-manifest.js';

export const Audio = {
    context: null,
    sounds: {},
    enabled: true,
    volume: 0.7,

    // 语音相关
    voices: [],
    preferredEnglishVoice: null,
    preferredChineseVoice: null,
    letterLanguage: 'zh',  // 'en' = 英文读音, 'zh' = 中文读音
    voicesLoaded: false,
    voicePlayer: null,
    voiceAssetBasePath: 'audio/voice/zh',
    voiceQueue: [],
    voiceQueuePlaying: false,
    voicePlaybackPrimed: false,
    voicePlaybackToken: 0,
    speechRequestId: 0,

    // 字母的汉语拼音发音映射
    letterPinyinSounds: LetterPinyinSounds,

    /**
     * 初始化音频上下文
     */
    init() {
        const settings = Storage.getSettings();
        this.enabled = settings.soundEnabled !== false;
        this.volume = Number.isFinite(Number(settings.volume))
            ? Math.max(0, Math.min(1, Number(settings.volume)))
            : 0.7;
        this.letterLanguage = settings.letterLanguage === 'zh' ? 'zh' : 'en';

        try {
            this.context = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Web Audio API not supported');
        }

        // Web Audio 不可用时，语音播报仍然可以独立工作。
        this.initVoices();
    },

    /**
     * 初始化语音引擎列表
     */
    initVoices() {
        if (!('speechSynthesis' in window)) return;

        const loadVoices = () => {
            this.voices = speechSynthesis.getVoices();
            if (this.voices.length > 0) {
                this.voicesLoaded = true;
                this.selectPreferredVoices();
                console.log('语音引擎已加载，共', this.voices.length, '个');
            }
        };

        // 立即尝试加载
        loadVoices();

        // 监听 voiceschanged 事件（某些浏览器异步加载）
        speechSynthesis.onvoiceschanged = loadVoices;

        // iOS Safari 备用方案：延迟重试
        if (!this.voicesLoaded) {
            setTimeout(loadVoices, 100);
            setTimeout(loadVoices, 500);
            setTimeout(loadVoices, 1000);
        }
    },

    /**
     * 选择首选的语音引擎
     */
    selectPreferredVoices() {
        this.preferredEnglishVoice = null;
        this.preferredChineseVoice = null;

        // 美音引擎优先级列表
        const englishPreferences = [
            'Samantha',           // iOS/macOS 美音女声
            'Alex',              // macOS 美音男声
            'Google US English', // Chrome 美音
            'en-US',             // 通用美音标识
            'en_US'
        ];

        // 中文引擎优先级列表
        const chinesePreferences = [
            'Tingting',          // iOS/macOS 中文女声
            'Ting-Ting',         // 部分系统使用连字符名称
            'Xiaoxiao',          // Windows/Edge 自然中文女声
            'Yunyang',           // Windows/Edge 自然中文男声
            'Google 普通话',      // Chrome 中文
            'Meijia',            // 台湾中文女声
            'zh-CN',
            'zh_CN'
        ];

        // 选择英文语音
        for (const pref of englishPreferences) {
            const voice = this.voices.find(v =>
                v.name.includes(pref) || v.lang.includes(pref)
            );
            if (voice) {
                this.preferredEnglishVoice = voice;
                console.log('选择英文语音:', voice.name);
                break;
            }
        }

        // 如果没找到首选，使用任意英文语音
        if (!this.preferredEnglishVoice) {
            this.preferredEnglishVoice = this.voices.find(v =>
                v.lang.startsWith('en')
            );
        }

        // 选择中文语音
        for (const pref of chinesePreferences) {
            const voice = this.voices.find(v =>
                v.name.includes(pref) || v.lang.includes(pref)
            );
            if (voice) {
                this.preferredChineseVoice = voice;
                console.log('选择中文语音:', voice.name);
                break;
            }
        }

        // 如果没找到首选，使用任意中文语音
        if (!this.preferredChineseVoice) {
            this.preferredChineseVoice = this.voices.find(v =>
                v.lang.startsWith('zh')
            );
        }
    },

    /**
     * 生成稳定的本地语音资源键，避免在 file:// 页面中依赖 fetch。
     */
    hashText(text) {
        let hash = 2166136261;
        const value = String(text);

        for (let i = 0; i < value.length; i += 1) {
            hash ^= value.charCodeAt(i);
            hash = Math.imul(hash, 16777619);
        }

        return (hash >>> 0).toString(16);
    },

    /**
     * 获取内置中文语音资源路径。
     */
    getVoiceAssetPath(text) {
        return `${this.voiceAssetBasePath}/${this.hashText(text)}.wav`;
    },

    /**
     * 获取复用的 HTMLAudioElement。
     */
    getVoicePlayer() {
        if (!this.voicePlayer) {
            this.voicePlayer = new window.Audio();
        }
        return this.voicePlayer;
    },

    /**
     * 在用户点击“开始游戏”时提前解锁媒体播放，兼容 Safari 和 file:// 页面。
     * 音量设为 0，不会让用户听到额外的提示音。
     */
    primeVoicePlayback() {
        if (!this.enabled || this.voicePlaybackPrimed || !VoiceAssets.has(this.hashText('啊'))) {
            return;
        }

        const player = this.getVoicePlayer();
        const originalVolume = this.volume;
        const playbackToken = this.voicePlaybackToken;
        player.pause();
        player.currentTime = 0;
        player.volume = 0;
        player.onended = null;
        player.onerror = null;
        player.src = this.getVoiceAssetPath('啊');

        const playResult = player.play();
        const restore = () => {
            // 首条字母语音可能在预热音频尚未结束时生成；此时不能再暂停/重置
            // 同一个 Audio 元素，否则会把真实字母语音截断。
            if (playbackToken !== this.voicePlaybackToken) {
                this.voicePlaybackPrimed = true;
                return;
            }
            player.pause();
            player.currentTime = 0;
            player.volume = originalVolume;
            this.voicePlaybackPrimed = true;
        };

        if (playResult && typeof playResult.then === 'function') {
            playResult.then(restore).catch(() => {
                if (playbackToken === this.voicePlaybackToken) {
                    player.volume = originalVolume;
                }
                this.voicePlaybackPrimed = true;
            });
        } else {
            restore();
        }
    },

    /**
     * 取消当前本地语音及排队内容。
     */
    cancelVoicePlayback() {
        this.voicePlaybackToken += 1;
        this.voiceQueue = [];
        this.voiceQueuePlaying = false;

        if (this.voicePlayer) {
            this.voicePlayer.pause();
            this.voicePlayer.currentTime = 0;
            this.voicePlayer.onended = null;
            this.voicePlayer.onerror = null;
        }
    },

    /**
     * 播放队列中的下一条本地语音。
     */
    drainVoiceQueue() {
        if (this.voiceQueuePlaying || this.voiceQueue.length === 0) return;

        const nextVoice = this.voiceQueue.shift();
        this.voiceQueuePlaying = true;
        const playbackToken = this.voicePlaybackToken;
        const player = this.getVoicePlayer();
        let settled = false;

        const finish = () => {
            if (settled || playbackToken !== this.voicePlaybackToken) return;
            settled = true;
            this.voiceQueuePlaying = false;
            player.onended = null;
            player.onerror = null;
            this.drainVoiceQueue();
        };

        const fallback = () => {
            if (playbackToken !== this.voicePlaybackToken) return;
            if (typeof nextVoice.fallback === 'function') nextVoice.fallback();
            finish();
        };

        player.pause();
        player.currentTime = 0;
        player.volume = this.volume;
        player.onended = finish;
        player.onerror = fallback;
        player.src = this.getVoiceAssetPath(nextVoice.text);

        try {
            const playResult = player.play();
            if (playResult && typeof playResult.catch === 'function') {
                playResult.catch(fallback);
            }
        } catch {
            // 某些浏览器会同步抛出 NotAllowedError，必须立即走系统语音兜底，
            // 否则 voiceQueuePlaying 会一直保持 true，后续字母全部无声。
            fallback();
        }
    },

    /**
     * 播放内置语音；资源不存在或浏览器拒绝播放时由调用方回退到系统语音。
     * interrupt=false 时进入本地队列，保证拼音分步朗读不会互相截断。
     */
    playChineseAsset(text, fallback, { interrupt = true } = {}) {
        if (!this.enabled || !VoiceAssets.has(this.hashText(text))) {
            return false;
        }

        if (interrupt) {
            this.cancelVoicePlayback();
        }

        this.voiceQueue.push({ text, fallback });
        this.drainVoiceQueue();
        return true;
    },

    /**
     * 生成简单音效
     */
    playTone(frequency, duration, type = 'sine') {
        if (!this.enabled || !this.context) return;

        try {
            const oscillator = this.context.createOscillator();
            const gainNode = this.context.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(this.context.destination);

            oscillator.type = type;
            oscillator.frequency.setValueAtTime(frequency, this.context.currentTime);

            gainNode.gain.setValueAtTime(this.volume * 0.3, this.context.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.context.currentTime + duration);

            oscillator.start(this.context.currentTime);
            oscillator.stop(this.context.currentTime + duration);
        } catch (e) {
            console.warn('Audio play failed:', e);
        }
    },

    /**
     * 播放正确音效 - 欢快的"叮"声
     */
    playCorrect() {
        if (!this.enabled || !this.context) return;

        // 播放两个音符形成和弦
        this.playTone(523.25, 0.15, 'sine');  // C5
        setTimeout(() => this.playTone(659.25, 0.2, 'sine'), 50);  // E5
        setTimeout(() => this.playTone(783.99, 0.25, 'sine'), 100);  // G5
    },

    /**
     * 播放错误音效 - 低沉的"嘟"声
     */
    playWrong() {
        if (!this.enabled || !this.context) return;

        this.playTone(200, 0.15, 'square');
        setTimeout(() => this.playTone(150, 0.2, 'square'), 100);
    },

    /**
     * 播放按键音效
     */
    playKeyPress() {
        if (!this.enabled || !this.context) return;

        this.playTone(440, 0.05, 'sine');
    },

    /**
     * 播放倒计时警告音
     */
    playTimerWarning() {
        if (!this.enabled || !this.context) return;

        this.playTone(880, 0.1, 'sine');
    },

    /**
     * 播放游戏结束音效
     */
    playGameOver() {
        if (!this.enabled || !this.context) return;

        // 播放下降音阶
        const notes = [523.25, 493.88, 440, 392];
        notes.forEach((freq, i) => {
            setTimeout(() => this.playTone(freq, 0.3, 'sine'), i * 150);
        });
    },

    /**
     * 播放胜利音效
     */
    playVictory() {
        if (!this.enabled || !this.context) return;

        // 播放欢快的上升音阶
        const notes = [392, 440, 493.88, 523.25, 587.33, 659.25];
        notes.forEach((freq, i) => {
            setTimeout(() => this.playTone(freq, 0.15, 'sine'), i * 80);
        });
    },

    /**
     * 播放新勋章音效
     */
    playBadgeUnlock() {
        if (!this.enabled || !this.context) return;

        // 华丽的音效
        setTimeout(() => this.playTone(523.25, 0.2, 'sine'), 0);
        setTimeout(() => this.playTone(659.25, 0.2, 'sine'), 150);
        setTimeout(() => this.playTone(783.99, 0.2, 'sine'), 300);
        setTimeout(() => this.playTone(1046.5, 0.4, 'sine'), 450);
    },

    /**
     * 使用 Web Speech API 朗读文本
     * @param {string} text 要朗读的文本
     * @param {string} lang 语言代码
     * @param {SpeechSynthesisVoice} preferredVoice 首选语音引擎
     */
    speak(text, lang = 'zh-CN', preferredVoice = null, { interrupt = true } = {}) {
        if (!this.enabled) return;

        const requestId = ++this.speechRequestId;
        if (interrupt) this.cancelVoicePlayback();

        const speech = globalThis.window?.speechSynthesis;
        const Utterance = globalThis.window?.SpeechSynthesisUtterance
            || globalThis.SpeechSynthesisUtterance;
        if (speech && typeof Utterance === 'function') {
            if (interrupt) {
                speech.cancel();
                speech.resume?.();
            }

            const utterance = new Utterance(text);
            utterance.lang = lang;
            utterance.rate = 0.82; // 放慢语速，给儿童留出辨音时间
            utterance.pitch = 1.0; // 使用自然音高，减少机械感
            utterance.volume = this.volume;

            // 使用首选语音引擎
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            const speakNow = () => {
                if (interrupt && requestId !== this.speechRequestId) return;
                speech.resume?.();
                speech.speak(utterance);
            };

            // cancel() 后部分 Safari/Chrome 需要一次事件循环再 speak，
            // 否则切换到英文时会出现“按钮有反馈但没有声音”。
            if (interrupt) {
                setTimeout(speakNow, 30);
            } else {
                speakNow();
            }
        }
    },

    /**
     * 朗读字母（根据当前语言设置）
     */
    speakLetter(letter) {
        const upperLetter = String(letter ?? '').toUpperCase();
        if (!upperLetter) return;

        if (this.letterLanguage === 'zh') {
            // 中文模式：读字母的汉语拼音发音（如 A 读 "啊"）
            const pinyinSound = this.letterPinyinSounds[upperLetter] || upperLetter;
            const speakFallback = () => this.speak(
                pinyinSound,
                'zh-CN',
                this.preferredChineseVoice
            );

            if (!this.playChineseAsset(pinyinSound, speakFallback)) {
                speakFallback();
            }
        } else {
            // 英文模式使用可读的单词，避免部分系统将 "A." 当作标点而不发音。
            const englishSounds = {
                A: 'ay', B: 'bee', C: 'see', D: 'dee', E: 'ee', F: 'ef',
                G: 'gee', H: 'aitch', I: 'eye', J: 'jay', K: 'kay', L: 'el',
                M: 'em', N: 'en', O: 'oh', P: 'pee', Q: 'cue', R: 'ar',
                S: 'ess', T: 'tee', U: 'you', V: 'vee', W: 'double you',
                X: 'ex', Y: 'why', Z: 'zee'
            };
            const phoneticText = englishSounds[upperLetter] || upperLetter;
            this.speak(phoneticText, 'en-US', this.preferredEnglishVoice);
        }
    },

    /**
     * 朗读拼音（使用中文发音）
     * 为了确保语音引擎用中文读拼音而不是英文，
     * 我们使用拼音对应的汉字发音
     */
    speakPinyin(pinyin, options = {}) {
        const sourceText = String(pinyin ?? '');
        const lowerPinyin = sourceText.toLowerCase();
        const speechText = PinyinSpeechMap[lowerPinyin] || sourceText;
        const speakFallback = () => this.speak(
            speechText,
            'zh-CN',
            this.preferredChineseVoice,
            options
        );

        if (!this.playChineseAsset(speechText, speakFallback, options)) {
            speakFallback();
        }
    },

    /**
     * 朗读引导语
     */
    speakGuide(text) {
        const speakFallback = () => this.speak(text, 'zh-CN', this.preferredChineseVoice);

        if (!this.playChineseAsset(text, speakFallback)) {
            speakFallback();
        }
    },

    /**
     * 停止当前语音，离开游戏或切换关卡时调用。
     */
    stopSpeaking() {
        this.speechRequestId += 1;
        this.cancelVoicePlayback();
        const speech = globalThis.window?.speechSynthesis;
        if (speech) speech.cancel();
    },

    /**
     * 设置字母读音语言
     * @param {string} lang 'en' = 英文, 'zh' = 中文
     */
    setLetterLanguage(lang) {
        this.letterLanguage = lang === 'zh' ? 'zh' : 'en';
        Storage.saveSettings({ ...Storage.getSettings(), letterLanguage: this.letterLanguage });
    },

    /**
     * 获取当前字母读音语言
     */
    getLetterLanguage() {
        return this.letterLanguage;
    },

    /**
     * 切换字母读音语言
     */
    toggleLetterLanguage() {
        const newLang = this.letterLanguage === 'en' ? 'zh' : 'en';
        this.setLetterLanguage(newLang);
        return newLang;
    },

    /**
     * 设置音效开关
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        Storage.saveSettings({ ...Storage.getSettings(), soundEnabled: enabled });
    },

    /**
     * 设置音量
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        Storage.saveSettings({ ...Storage.getSettings(), volume: this.volume });
    },

    /**
     * 恢复音频上下文（需要用户交互后调用）
     */
    resume() {
        if (this.context && this.context.state === 'suspended') {
            this.context.resume();
        }
    }
};
