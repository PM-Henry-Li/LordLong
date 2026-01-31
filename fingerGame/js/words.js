/* ===============================================
   词语竞速游戏逻辑
   =============================================== */

const WordsGame = {
    currentWord: null,
    currentPinyin: '',
    inputBuffer: '',
    inputIndex: 0,
    isRunning: false,
    showHint: true,  // 是否显示拼音提示
    grade: 1,        // 年级

    // 回调函数
    onCorrect: null,
    onWrong: null,

    // DOM 元素
    elements: {
        hanzi: null,
        pinyinHint: null,
        inputDisplay: null
    },

    /**
     * 初始化
     */
    init() {
        this.elements.hanzi = document.getElementById('hanzi');
        this.elements.pinyinHint = document.getElementById('pinyin-hint');
        this.elements.inputDisplay = document.getElementById('input-display');
    },

    /**
     * 开始游戏
     */
    start(options = {}) {
        this.isRunning = true;
        this.inputBuffer = '';
        this.inputIndex = 0;
        this.showHint = options.showHint !== false;
        this.grade = options.grade || 1;

        // 生成第一个词语
        this.nextWord();

        // 设置键盘回调
        Keyboard.setKeyPressCallback((key) => this.handleKeyPress(key));
    },

    /**
     * 停止游戏
     */
    stop() {
        this.isRunning = false;
        Keyboard.setKeyPressCallback(null);
        Keyboard.reset();
    },

    /**
     * 暂停
     */
    pause() {
        this.isRunning = false;
    },

    /**
     * 继续
     */
    resume() {
        this.isRunning = true;
    },

    /**
     * 获取当前年级的词库
     */
    getWordList() {
        const wordData = window.WordsData;
        if (!wordData || !wordData.grades) {
            return [];
        }
        return wordData.grades[this.grade] || wordData.grades[1] || [];
    },

    /**
     * 生成下一个词语
     */
    nextWord() {
        const wordList = this.getWordList();
        if (wordList.length === 0) {
            console.warn('词库为空');
            return;
        }

        const word = Utils.randomChoice(wordList);
        this.currentWord = word;
        this.currentPinyin = word.pinyin.replace(/\s+/g, '').toUpperCase();
        this.inputBuffer = '';
        this.inputIndex = 0;

        // 更新显示
        this.elements.hanzi.textContent = word.hanzi;
        this.elements.pinyinHint.textContent = this.showHint ? word.pinyin : '';
        this.elements.pinyinHint.style.opacity = this.showHint ? '1' : '0';
        this.elements.inputDisplay.textContent = '';

        // 高亮第一个字母
        if (this.currentPinyin.length > 0) {
            Keyboard.highlight(this.currentPinyin[0]);
        }

        // 朗读汉字
        setTimeout(() => {
            Audio.speakPinyin(word.hanzi);
        }, 300);
    },

    /**
     * 处理按键
     */
    handleKeyPress(key) {
        if (!this.isRunning || !this.currentWord) return;

        const expectedKey = this.currentPinyin[this.inputIndex];

        if (key === expectedKey) {
            // 正确
            this.inputBuffer += key.toLowerCase();
            this.inputIndex++;

            Keyboard.showCorrect(key);
            Audio.playCorrect();

            // 更新输入显示
            this.updateInputDisplay();

            // 检查是否完成
            if (this.inputIndex >= this.currentPinyin.length) {
                this.completeWord();
            } else {
                // 高亮下一个字母
                Keyboard.highlight(this.currentPinyin[this.inputIndex]);
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
     * 更新输入显示
     */
    updateInputDisplay() {
        this.elements.inputDisplay.textContent = this.inputBuffer;
    },

    /**
     * 完成词语
     */
    completeWord() {
        const word = this.currentWord;

        // 显示完成效果
        this.elements.inputDisplay.style.animation = 'scaleBounce 0.5s ease';
        this.elements.hanzi.style.animation = 'scaleBounce 0.5s ease';

        // 朗读
        setTimeout(() => {
            Audio.speakPinyin(word.hanzi);
        }, 300);

        // 回调
        if (this.onCorrect) {
            this.onCorrect();
        }

        // 粒子效果
        Utils.createParticles(
            window.innerWidth / 2,
            window.innerHeight / 3,
            12,
            document.body
        );

        // 下一个词语
        setTimeout(() => {
            if (this.isRunning) {
                this.elements.inputDisplay.style.animation = '';
                this.elements.hanzi.style.animation = '';
                this.nextWord();
            }
        }, 2000);
    },

    /**
     * 切换提示显示
     */
    toggleHint() {
        this.showHint = !this.showHint;
        this.elements.pinyinHint.style.opacity = this.showHint ? '1' : '0';
    },

    /**
     * 设置年级
     */
    setGrade(grade) {
        this.grade = Math.max(1, Math.min(6, grade));
    },

    /**
     * 设置回调
     */
    setCallbacks({ onCorrect, onWrong }) {
        if (onCorrect) this.onCorrect = onCorrect;
        if (onWrong) this.onWrong = onWrong;
    }
};

// 导出到全局
window.WordsGame = WordsGame;
