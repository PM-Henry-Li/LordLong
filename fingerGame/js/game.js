/* ===============================================
   游戏核心控制
   =============================================== */

import { Audio } from './audio.js';
import { Api } from './api.js';
import { Keyboard } from './keyboard.js';
import { LettersGame } from './letters.js';
import { PinyinGame } from './pinyin.js';
import { Storage } from './storage.js';
import { Utils } from './utils.js';
import { WordsGame } from './words.js';

export const Game = {
    currentMode: null,
    currentUser: null,
    score: 0,
    correctCount: 0,
    wrongCount: 0,
    errorLetters: [],
    timeRemaining: 300,  // 5分钟 = 300秒
    timerInterval: null,
    pendingTimers: new Set(),
    restTimerInterval: null,
    restReminderTimeout: null,
    isPaused: false,
    isGameOver: false,
    currentSpeed: 0.5,

    /**
     * 初始化游戏
     */
    init() {
        // 初始化各个模块
        Audio.init();
        Keyboard.init('virtual-keyboard');
        LettersGame.init('game-canvas');
        PinyinGame.init();
        WordsGame.init();

        // 绑定按钮事件
        this.bindEvents();
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 暂停按钮
        document.getElementById('btn-pause').addEventListener('click', () => {
            this.pause();
        });

        // 继续按钮
        document.getElementById('btn-resume').addEventListener('click', () => {
            this.resume();
        });

        // 退出按钮
        document.getElementById('btn-quit').addEventListener('click', () => {
            this.quit();
        });

        // 返回模式选择
        document.getElementById('btn-back-mode').addEventListener('click', () => {
            if (!this.isGameOver) {
                this.pause();
            } else {
                this.quit();
            }
        });

        // 再玩一次
        document.getElementById('btn-play-again').addEventListener('click', () => {
            this.playAgain();
        });

        // 返回菜单
        document.getElementById('btn-back-menu').addEventListener('click', () => {
            this.backToMenu();
        });

        // 休息完成
        document.getElementById('btn-rest-done').addEventListener('click', () => {
            this.hideRestReminder();
        });

        // 速度控制
        document.getElementById('btn-speed-up').addEventListener('click', () => {
            this.changeSpeed(0.1);
        });

        document.getElementById('btn-speed-down').addEventListener('click', () => {
            this.changeSpeed(-0.1);
        });

        // 语言切换按钮
        document.getElementById('btn-lang-toggle').addEventListener('click', () => {
            this.toggleLetterLanguage();
        });
    },

    /**
     * 切换字母读音语言
     */
    toggleLetterLanguage() {
        const newLang = Audio.toggleLetterLanguage();
        this.updateLanguageDisplay(newLang);

        // 播放示例音效，让用户听到变化
        Audio.speakLetter('A');
    },

    /**
     * 更新语言显示
     */
    updateLanguageDisplay(lang) {
        const btn = document.getElementById('btn-lang-toggle');
        const langText = document.getElementById('lang-text');

        if (lang === 'zh') {
            btn.classList.add('zh-mode');
            langText.textContent = '中';
        } else {
            btn.classList.remove('zh-mode');
            langText.textContent = 'EN';
        }
    },

    /**
     * 开始游戏
     */
    start(mode) {
        if (!['letters', 'pinyin', 'words'].includes(mode)) return;

        this.stopAllGames();
        this.hideRestReminder();
        this.currentMode = mode;
        this.currentUser = Storage.getCurrentUser();
        if (!this.currentUser) {
            this.currentMode = null;
            return;
        }
        this.score = 0;
        this.correctCount = 0;
        this.wrongCount = 0;
        this.errorLetters = [];
        this.timeRemaining = 300;
        this.isPaused = false;
        this.isGameOver = false;
        this.currentSpeed = 0.5;

        // 更新UI
        this.updateScoreDisplay();
        this.updateTimerDisplay();
        this.updateSpeedDisplay();
        this.updateLanguageDisplay(Audio.getLetterLanguage());

        // 显示游戏界面
        this.showScreen('game-screen');

        // 根据模式启动对应游戏
        switch (mode) {
            case 'letters':
                this.startLettersGame();
                break;
            case 'pinyin':
                this.startPinyinGame();
                break;
            case 'words':
                this.startWordsGame();
                break;
        }

        // 开始倒计时
        this.startTimer();

        // 恢复音频上下文
        Audio.resume();
        Audio.primeVoicePlayback();

        // 语音引导
        this.schedule(() => Audio.speakGuide('游戏开始！'), 500);
    },

    /**
     * 开始字母森林游戏
     */
    startLettersGame() {
        // 显示 Canvas，隐藏其他
        document.getElementById('game-canvas').style.display = 'block';
        document.getElementById('pinyin-display').style.display = 'none';
        document.getElementById('word-display').style.display = 'none';

        // 显示语言切换按钮（只在字母森林模式显示）
        document.getElementById('btn-lang-toggle').style.display = 'flex';

        // 设置回调
        LettersGame.setCallbacks({
            onCorrect: (letter, x, y) => {
                this.addScore(10);
                this.correctCount++;
                this.updateScoreDisplay();
            },
            onWrong: (letter) => {
                this.addScore(-5);
                this.wrongCount++;
                this.errorLetters.push(letter);
                this.updateScoreDisplay();
            },
            onMiss: (letter) => {
                this.addScore(-5);
                this.wrongCount++;
                this.errorLetters.push(letter);
                this.updateScoreDisplay();
            }
        });

        // 开始游戏
        LettersGame.start();

        // 应用初始速度
        LettersGame.setSpeed(this.currentSpeed);
    },

    /**
     * 开始拼音合成室游戏
     */
    startPinyinGame() {
        document.getElementById('game-canvas').style.display = 'none';
        document.getElementById('pinyin-display').style.display = 'flex';
        document.getElementById('word-display').style.display = 'none';

        // 隐藏语言切换按钮（拼音模式只用中文拼音发音）
        document.getElementById('btn-lang-toggle').style.display = 'none';

        PinyinGame.setCallbacks({
            onCorrect: () => {
                this.addScore(15);
                this.correctCount++;
                this.updateScoreDisplay();
            },
            onWrong: () => {
                this.addScore(-5);
                this.wrongCount++;
                this.updateScoreDisplay();
            }
        });

        PinyinGame.start();
    },

    /**
     * 开始词语竞速游戏
     */
    startWordsGame() {
        document.getElementById('game-canvas').style.display = 'none';
        document.getElementById('pinyin-display').style.display = 'none';
        document.getElementById('word-display').style.display = 'block';

        // 隐藏语言切换按钮（词语模式只用中文朗读）
        document.getElementById('btn-lang-toggle').style.display = 'none';

        WordsGame.setCallbacks({
            onCorrect: () => {
                this.addScore(20);
                this.correctCount++;
                this.updateScoreDisplay();
            },
            onWrong: () => {
                this.addScore(-5);
                this.wrongCount++;
                this.updateScoreDisplay();
            }
        });

        WordsGame.start();
    },

    /**
     * 添加分数
     */
    addScore(points) {
        this.score = Math.max(0, this.score + points);
    },

    /**
     * 更新分数显示
     */
    updateScoreDisplay() {
        document.getElementById('score').textContent = this.score;
        document.getElementById('correct-count').textContent = this.correctCount;
        document.getElementById('wrong-count').textContent = this.wrongCount;
    },

    /**
     * 开始计时器
     */
    startTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.timerInterval = setInterval(() => {
            if (this.isPaused || this.isGameOver) return;

            this.timeRemaining--;
            this.updateTimerDisplay();

            // 警告音效
            if (this.timeRemaining === 60) {
                Audio.speakGuide('还剩一分钟！');
            } else if (this.timeRemaining <= 10 && this.timeRemaining > 0) {
                Audio.playTimerWarning();
            }

            // 时间到
            if (this.timeRemaining <= 0) {
                this.gameOver();
            }
        }, 1000);
    },

    /**
     * 更新计时器显示
     */
    updateTimerDisplay() {
        const timerEl = document.getElementById('timer');
        timerEl.textContent = Utils.formatTime(this.timeRemaining);

        // 添加警告样式
        timerEl.classList.remove('timer-warning', 'timer-critical');
        if (this.timeRemaining <= 30) {
            timerEl.classList.add('timer-critical');
        } else if (this.timeRemaining <= 60) {
            timerEl.classList.add('timer-warning');
        }
    },

    /**
     * 暂停游戏
     */
    pause() {
        if (this.isGameOver || this.isPaused || !this.currentMode) return;
        this.isPaused = true;
        document.getElementById('pause-modal').style.display = 'flex';

        // 暂停当前游戏
        switch (this.currentMode) {
            case 'letters':
                LettersGame.pause();
                break;
            case 'pinyin':
                PinyinGame.pause();
                break;
            case 'words':
                WordsGame.pause();
                break;
        }
    },

    /**
     * 继续游戏
     */
    resume() {
        if (!this.isPaused || this.isGameOver) return;
        this.isPaused = false;
        document.getElementById('pause-modal').style.display = 'none';

        // 继续当前游戏
        switch (this.currentMode) {
            case 'letters':
                LettersGame.resume();
                break;
            case 'pinyin':
                PinyinGame.resume();
                break;
            case 'words':
                WordsGame.resume();
                break;
        }
    },

    /**
     * 退出游戏
     */
    quit() {
        this.stopAllGames();
        this.hideRestReminder();
        this.currentMode = null;
        this.isPaused = false;
        this.isGameOver = false;
        this.showScreen('mode-screen');
    },

    /**
     * 停止所有游戏
     */
    stopAllGames() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }

        this.clearTimers();

        LettersGame.stop();
        PinyinGame.stop();
        WordsGame.stop();
        Audio.stopSpeaking();

        document.getElementById('pause-modal').style.display = 'none';
    },

    /**
     * 游戏结束
     */
    gameOver() {
        if (this.isGameOver || !this.currentUser || !this.currentMode) return;
        this.isGameOver = true;
        this.stopAllGames();

        // 保存结果
        const result = Storage.recordGameResult(
            this.currentUser.id,
            this.currentMode,
            this.score,
            this.correctCount,
            this.wrongCount,
            this.errorLetters
        );

        if (!result?.user) {
            this.quit();
            return;
        }

        this.currentUser = result.user;
        void Api.syncGameResult({
            userId: this.currentUser.id,
            mode: this.currentMode,
            score: this.score,
            correct: this.correctCount,
            wrong: this.wrongCount,
            errorLetters: this.errorLetters
        });
        document.dispatchEvent(new CustomEvent('pinyin:user-updated', {
            detail: { user: this.currentUser }
        }));

        // 更新UI
        const resultMessage = Utils.getResultMessage(this.score, this.correctCount, this.wrongCount);
        document.getElementById('result-title').textContent = resultMessage.title;
        document.getElementById('final-score').textContent = this.score;
        document.getElementById('final-correct').textContent = this.correctCount;
        document.getElementById('final-wrong').textContent = this.wrongCount;

        // 显示新勋章
        const badgeEl = document.getElementById('badge-earned');
        if (result.newBadge) {
            badgeEl.style.display = 'block';
            document.getElementById('badge-icon').textContent = result.newBadge.icon;
            document.getElementById('badge-name').textContent = result.newBadge.name;
            Audio.playBadgeUnlock();
            Utils.createConfetti();
        } else {
            badgeEl.style.display = 'none';
        }

        // 播放音效
        if (this.score >= 200) {
            Audio.playVictory();
        } else {
            Audio.playGameOver();
        }

        // 显示结算界面
        this.showScreen('result-screen');

        // 检查防沉迷
        const gameCount = Storage.incrementGameCount();
        if (gameCount >= 2) {
            this.restReminderTimeout = setTimeout(() => {
                this.restReminderTimeout = null;
                this.showRestReminder();
            }, 2000);
        }
    },

    /**
     * 显示休息提醒
     */
    showRestReminder() {
        if (this.restTimerInterval) clearInterval(this.restTimerInterval);
        const modal = document.getElementById('rest-modal');
        const timerEl = document.getElementById('rest-timer');
        const btnDone = document.getElementById('btn-rest-done');

        modal.style.display = 'flex';
        btnDone.disabled = true;

        let restTime = 10;
        timerEl.textContent = restTime;

        this.restTimerInterval = setInterval(() => {
            restTime--;
            timerEl.textContent = restTime;

            if (restTime <= 0) {
                clearInterval(this.restTimerInterval);
                this.restTimerInterval = null;
                btnDone.disabled = false;
                Storage.resetGameCount();
            }
        }, 1000);
    },

    /**
     * 再玩一次
     */
    playAgain() {
        if (this.currentMode) this.start(this.currentMode);
    },

    /**
     * 返回菜单
     */
    backToMenu() {
        this.stopAllGames();
        this.hideRestReminder();
        this.isPaused = false;
        this.isGameOver = false;
        this.showScreen('mode-screen');
    },

    /**
     * 显示指定界面
     */
    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(screenId).classList.add('active');
    },

    /**
     * 调整游戏速度
     */
    changeSpeed(delta) {
        let newSpeed = Math.round((this.currentSpeed + delta) * 10) / 10;
        newSpeed = Math.max(0.5, Math.min(2.0, newSpeed));

        if (newSpeed !== this.currentSpeed) {
            this.currentSpeed = newSpeed;
            this.updateSpeedDisplay();
            this.applySpeed();
        }
    },

    /**
     * 更新速度显示
     */
    updateSpeedDisplay() {
        document.getElementById('speed-value').textContent = this.currentSpeed.toFixed(1) + 'x';
        document.getElementById('btn-speed-up').disabled = this.currentSpeed >= 2.0;
        document.getElementById('btn-speed-down').disabled = this.currentSpeed <= 0.5;
    },

    /**
     * 应用速度设置
     */
    applySpeed() {
        if (this.currentMode === 'letters') {
            LettersGame.setSpeed(this.currentSpeed);
        }
        // 未来可以支持其他模式
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
    },

    hideRestReminder() {
        if (this.restReminderTimeout) {
            clearTimeout(this.restReminderTimeout);
            this.restReminderTimeout = null;
        }
        if (this.restTimerInterval) {
            clearInterval(this.restTimerInterval);
            this.restTimerInterval = null;
        }
        const modal = document.getElementById('rest-modal');
        const btnDone = document.getElementById('btn-rest-done');
        if (modal) modal.style.display = 'none';
        if (btnDone) btnDone.disabled = true;
    }
};
