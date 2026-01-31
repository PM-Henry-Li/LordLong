/* ===============================================
   音效管理
   =============================================== */

const Audio = {
    context: null,
    sounds: {},
    enabled: true,
    volume: 0.7,

    /**
     * 初始化音频上下文
     */
    init() {
        try {
            this.context = new (window.AudioContext || window.webkitAudioContext)();
            const settings = Storage.getSettings();
            this.enabled = settings.soundEnabled;
            this.volume = settings.volume;
        } catch (e) {
            console.warn('Web Audio API not supported');
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
     */
    speak(text, lang = 'zh-CN') {
        if (!this.enabled) return;

        if ('speechSynthesis' in window) {
            // 取消之前的朗读
            speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 0.9;  // 稍慢一点，适合儿童
            utterance.pitch = 1.1; // 稍高一点，更童真
            utterance.volume = this.volume;

            speechSynthesis.speak(utterance);
        }
    },

    /**
     * 朗读字母
     */
    speakLetter(letter) {
        this.speak(letter.toUpperCase(), 'en-US');
    },

    /**
     * 朗读拼音
     */
    speakPinyin(pinyin) {
        this.speak(pinyin, 'zh-CN');
    },

    /**
     * 朗读引导语
     */
    speakGuide(text) {
        this.speak(text, 'zh-CN');
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
