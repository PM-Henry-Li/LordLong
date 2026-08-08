/* ===============================================
   拼音合成室游戏逻辑
   =============================================== */

import { Audio } from './audio.js';
import { Keyboard } from './keyboard.js';
import { PinyinData } from '../data/pinyin-data.js';
import { Utils } from './utils.js';

export const PinyinGame = {
    currentPinyin: null,
    inputBuffer: '',
    inputIndex: 0,
    isRunning: false,
    pendingTimers: new Set(),

    // 回调函数
    onCorrect: null,
    onWrong: null,

    // DOM 元素
    elements: {
        shengmu: null,
        yunmu: null,
        result: null
    },

    /**
     * 初始化
     */
    init() {
        this.elements.shengmu = document.getElementById('shengmu');
        this.elements.yunmu = document.getElementById('yunmu');
        this.elements.result = document.getElementById('pinyin-result');
    },

    /**
     * 开始游戏
     */
    start() {
        this.clearTimers();
        this.isRunning = true;
        this.inputBuffer = '';
        this.inputIndex = 0;
        this.currentPinyin = null;

        // 设置键盘回调
        Keyboard.setKeyPressCallback((key) => this.handleKeyPress(key));

        // 延迟生成第一个拼音，让用户有准备时间
        this.schedule(() => {
            if (this.isRunning) this.nextPinyin();
        }, 1500);
    },

    /**
     * 停止游戏
     */
    stop() {
        this.isRunning = false;
        this.clearTimers();
        this.currentPinyin = null;
        Keyboard.setKeyPressCallback(null);
        Keyboard.reset();
        Audio.stopSpeaking();
    },

    /**
     * 暂停
     */
    pause() {
        this.isRunning = false;
        this.clearTimers();
        Audio.stopSpeaking();
    },

    /**
     * 继续
     */
    resume() {
        this.isRunning = true;
        if (!this.currentPinyin || this.isCurrentComplete()) {
            this.schedule(() => {
                if (this.isRunning) this.nextPinyin();
            }, 0);
        }
    },

    /**
     * 生成下一个拼音
     */
    nextPinyin() {
        // 从拼音数据中随机选择
        const pinyin = Utils.randomChoice(PinyinData.combinations);
        if (!pinyin) return;
        this.currentPinyin = pinyin;
        this.inputBuffer = '';
        this.inputIndex = 0;

        // 更新显示
        this.elements.shengmu.textContent = pinyin.shengmu;
        this.elements.yunmu.textContent = pinyin.yunmu;
        this.elements.result.textContent = '?';

        // 高亮第一个字母
        const fullPinyin = Utils.normalizePinyinInput(pinyin.shengmu + pinyin.yunmu);
        if (fullPinyin.length > 0) {
            Keyboard.highlight(fullPinyin[0]);
        }

        // 朗读完整拼音引导（中文拼音发音）
        this.schedule(() => {
            if (!this.isRunning) return;
            // 朗读完整拼音组合
            Audio.speakPinyin(pinyin.shengmu + pinyin.yunmu);
        }, 300);
    },

    /**
     * 处理按键
     */
    handleKeyPress(key) {
        if (!this.isRunning || !this.currentPinyin) return;

        const fullPinyin = Utils.normalizePinyinInput(
            this.currentPinyin.shengmu + this.currentPinyin.yunmu
        );
        const expectedKey = fullPinyin[this.inputIndex];

        if (key === expectedKey) {
            // 正确
            this.inputBuffer += key.toLowerCase();
            this.inputIndex++;

            Keyboard.showCorrect(key);
            Audio.playCorrect();

            // 检查是否完成
            if (this.inputIndex >= fullPinyin.length) {
                // 完成拼音
                this.completePinyin();
            } else {
                // 高亮下一个字母
                Keyboard.highlight(fullPinyin[this.inputIndex]);
            }
        } else {
            // 错误
            Keyboard.showWrong(key);
            Audio.playWrong();

            if (this.onWrong) {
                this.onWrong();
            }
        }
    },

    /**
     * 完成拼音
     */
    completePinyin() {
        const pinyin = this.currentPinyin;
        const fullPinyin = Utils.normalizePinyinInput(pinyin.shengmu + pinyin.yunmu);

        // 显示结果
        this.elements.result.textContent = fullPinyin;
        this.elements.result.style.animation = 'scaleBounce 0.5s ease';

        // 朗读完整拼音（分步朗读：声母 -> 韵母 -> 完整拼音）
        this.schedule(() => {
            if (!this.isRunning) return;
            // 先读声母（如果有的话）
            if (pinyin.shengmu) {
                Audio.speakPinyin(pinyin.shengmu, { interrupt: true });
            }

            // 再读韵母
            this.schedule(() => {
                if (!this.isRunning) return;
                Audio.speakPinyin(pinyin.yunmu, { interrupt: false });

                // 最后读完整拼音
                this.schedule(() => {
                    if (!this.isRunning) return;
                    Audio.speakPinyin(pinyin.shengmu + pinyin.yunmu, { interrupt: false });

                    // 如果有例字，朗读例字
                    if (pinyin.example) {
                        this.schedule(() => {
                            if (this.isRunning) Audio.speakPinyin(pinyin.example, { interrupt: false });
                        }, 800);
                    }
                }, 600);
            }, 600);
        }, 300);

        // 回调
        if (this.onCorrect) {
            this.onCorrect();
        }

        // 粒子效果
        Utils.createParticles(
            window.innerWidth / 2,
            window.innerHeight / 2,
            12,
            document.body
        );

        // 下一个拼音
        this.schedule(() => {
            if (this.isRunning) {
                this.elements.result.style.animation = '';
                this.nextPinyin();
            }
        }, 3500);
    },

    /**
     * 设置回调
     */
    setCallbacks({ onCorrect, onWrong }) {
        this.onCorrect = onCorrect || null;
        this.onWrong = onWrong || null;
    },

    isCurrentComplete() {
        if (!this.currentPinyin) return false;
        const fullPinyin = Utils.normalizePinyinInput(
            this.currentPinyin.shengmu + this.currentPinyin.yunmu
        );
        return this.inputIndex >= fullPinyin.length;
    },

    schedule(callback, delay) {
        const timer = setTimeout(() => {
            this.pendingTimers.delete(timer);
            callback();
        }, delay);
        this.pendingTimers.add(timer);
        return timer;
    },

    clearTimers() {
        this.pendingTimers.forEach(timer => clearTimeout(timer));
        this.pendingTimers.clear();
    }
};
