/* ===============================================
   音效管理
   =============================================== */

const Audio = {
    context: null,
    sounds: {},
    enabled: true,
    volume: 0.7,

    // 语音相关
    voices: [],
    preferredEnglishVoice: null,
    preferredChineseVoice: null,
    letterLanguage: 'en',  // 'en' = 英文读音, 'zh' = 中文读音
    voicesLoaded: false,

    // 字母的汉语拼音发音映射
    letterPinyinSounds: {
        'A': '啊', 'B': '波', 'C': '次', 'D': '的', 'E': '鹅',
        'F': '佛', 'G': '哥', 'H': '喝', 'I': '衣', 'J': '机',
        'K': '科', 'L': '了', 'M': '摸', 'N': '呢', 'O': '喔',
        'P': '坡', 'Q': '期', 'R': '日', 'S': '思', 'T': '特',
        'U': '乌', 'V': '于', 'W': '乌', 'X': '西', 'Y': '衣', 'Z': '资'
    },

    /**
     * 初始化音频上下文
     */
    init() {
        try {
            this.context = new (window.AudioContext || window.webkitAudioContext)();
            const settings = Storage.getSettings();
            this.enabled = settings.soundEnabled;
            this.volume = settings.volume;
            this.letterLanguage = settings.letterLanguage || 'en';

            // 初始化语音引擎
            this.initVoices();
        } catch (e) {
            console.warn('Web Audio API not supported');
        }
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
            'Google 普通话',      // Chrome 中文
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
    speak(text, lang = 'zh-CN', preferredVoice = null) {
        if (!this.enabled) return;

        if ('speechSynthesis' in window) {
            // 取消之前的朗读
            speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 0.9;  // 稍慢一点，适合儿童
            utterance.pitch = 1.1; // 稍高一点，更童真
            utterance.volume = this.volume;

            // 使用首选语音引擎
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            speechSynthesis.speak(utterance);
        }
    },

    /**
     * 朗读字母（根据当前语言设置）
     */
    speakLetter(letter) {
        const upperLetter = letter.toUpperCase();

        if (this.letterLanguage === 'zh') {
            // 中文模式：读字母的汉语拼音发音（如 A 读 "啊"）
            const pinyinSound = this.letterPinyinSounds[upperLetter] || upperLetter;
            this.speak(pinyinSound, 'zh-CN', this.preferredChineseVoice);
        } else {
            // 英文模式：使用改进的发音方式避免 iOS "Letter" 前缀
            // 添加一个短元音使发音更自然，避免被识别为拼写模式
            const phoneticText = upperLetter + '.';
            this.speak(phoneticText, 'en-US', this.preferredEnglishVoice);
        }
    },

    /**
     * 朗读拼音（使用中文发音）
     * 为了确保语音引擎用中文读拼音而不是英文，
     * 我们使用拼音对应的汉字发音
     */
    speakPinyin(pinyin) {
        // 常见拼音的汉字发音映射
        const pinyinToHanzi = {
            // 声母（单独读时的发音）
            'b': '波', 'p': '坡', 'm': '摸', 'f': '佛',
            'd': '的', 't': '特', 'n': '呢', 'l': '了',
            'g': '哥', 'k': '科', 'h': '喝',
            'j': '机', 'q': '期', 'x': '西',
            'zh': '知', 'ch': '吃', 'sh': '诗', 'r': '日',
            'z': '资', 'c': '次', 's': '思',
            'y': '衣', 'w': '乌',
            // 单韵母
            'a': '啊', 'o': '哦', 'e': '鹅', 'i': '衣', 'u': '乌', 'v': '于',
            // 复韵母
            'ai': '爱', 'ei': '诶', 'ui': '威', 'ao': '奥', 'ou': '欧',
            'iu': '优', 'ie': '耶', 'ue': '约', 'er': '耳',
            'an': '安', 'en': '恩', 'in': '因', 'un': '温',
            'ang': '昂', 'eng': '鹏', 'ing': '英', 'ong': '翁',
            // 声母 + 单韵母组合
            'ba': '八', 'bo': '波', 'bi': '逼', 'bu': '不',
            'pa': '趴', 'po': '坡', 'pi': '皮', 'pu': '扑',
            'ma': '妈', 'mo': '摸', 'mi': '米', 'mu': '木',
            'fa': '发', 'fo': '佛', 'fu': '福',
            'da': '大', 'de': '的', 'di': '地', 'du': '读',
            'ta': '他', 'te': '特', 'ti': '踢', 'tu': '兔',
            'na': '那', 'ne': '呢', 'ni': '你', 'nu': '怒',
            'la': '拉', 'le': '乐', 'li': '梨', 'lu': '路',
            'ga': '嘎', 'ge': '哥', 'gu': '姑',
            'ka': '卡', 'ke': '可', 'ku': '哭',
            'ha': '哈', 'he': '喝', 'hu': '胡',
            'ji': '鸡', 'ju': '句',
            'qi': '七', 'qu': '去',
            'xi': '西', 'xu': '需',
            // 复韵母组合
            'bai': '白', 'mai': '买', 'hao': '好',
            'xiao': '小', 'niu': '牛', 'liu': '六',
            'xian': '先', 'lian': '连',
            // 鼻韵母组合
            'shan': '山', 'tian': '天', 'yang': '羊',
            'dong': '东', 'xing': '星',
            // zh ch sh r 系列
            'zhi': '知', 'chi': '吃', 'shi': '诗', 'ri': '日',
            'zi': '资', 'ci': '次', 'si': '思',
            // 整体认读音节
            'yi': '衣', 'wu': '乌', 'yu': '雨',
            'ye': '也', 'yue': '月', 'yuan': '圆',
            'yin': '音', 'yun': '云', 'ying': '英'
        };

        const lowerPinyin = pinyin.toLowerCase();

        // 查找对应的汉字发音
        if (pinyinToHanzi[lowerPinyin]) {
            this.speak(pinyinToHanzi[lowerPinyin], 'zh-CN', this.preferredChineseVoice);
        } else {
            // 如果是完整的汉字或词语，直接读
            this.speak(pinyin, 'zh-CN', this.preferredChineseVoice);
        }
    },

    /**
     * 朗读引导语
     */
    speakGuide(text) {
        this.speak(text, 'zh-CN', this.preferredChineseVoice);
    },

    /**
     * 设置字母读音语言
     * @param {string} lang 'en' = 英文, 'zh' = 中文
     */
    setLetterLanguage(lang) {
        this.letterLanguage = lang;
        Storage.saveSettings({ ...Storage.getSettings(), letterLanguage: lang });
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

// 导出到全局
window.Audio = Audio;
