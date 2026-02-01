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
        // 去除声调符号并转大写，用于与键盘输入匹配
        this.currentPinyin = Utils.removePinyinTones(word.pinyin.replace(/\s+/g, '')).toUpperCase();
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

        // 拼读引导：先读拼音的各个部分，再读声调，最后读汉字
        // 例如：r en 的二声 人
        setTimeout(() => {
            // 解析拼音，分成声母和韵母部分
            const pinyinParts = this.parsePinyinParts(word.pinyin);
            // 获取声调
            const tone = this.getToneFromPinyin(word.pinyin);

            let delay = 0;
            // 依次朗读每个拼音部分
            pinyinParts.forEach((part, index) => {
                setTimeout(() => {
                    Audio.speakPinyin(part);
                }, delay);
                delay += 500;
            });

            // 读声调（如果有的话）
            if (tone) {
                setTimeout(() => {
                    Audio.speakPinyin(tone);
                }, delay);
                delay += 600;
            }

            // 最后朗读汉字
            setTimeout(() => {
                Audio.speakPinyin(word.hanzi);
            }, delay + 300);
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

        // 下一个词语（增加延迟以便完成拼读）
        setTimeout(() => {
            if (this.isRunning) {
                this.elements.inputDisplay.style.animation = '';
                this.elements.hanzi.style.animation = '';
                this.nextWord();
            }
        }, 4000);
    },

    /**
     * 从拼音中提取声调
     * 返回如 "的一声"、"的二声" 等
     */
    getToneFromPinyin(pinyin) {
        // 声调符号映射
        const toneMarks = {
            // 一声（阴平）
            'ā': 1, 'ē': 1, 'ī': 1, 'ō': 1, 'ū': 1, 'ǖ': 1,
            // 二声（阳平）
            'á': 2, 'é': 2, 'í': 2, 'ó': 2, 'ú': 2, 'ǘ': 2,
            // 三声（上声）
            'ǎ': 3, 'ě': 3, 'ǐ': 3, 'ǒ': 3, 'ǔ': 3, 'ǚ': 3,
            // 四声（去声）
            'à': 4, 'è': 4, 'ì': 4, 'ò': 4, 'ù': 4, 'ǜ': 4
        };

        const toneNames = {
            1: '一声',
            2: '二声',
            3: '三声',
            4: '四声'
        };

        // 查找拼音中的声调标记
        for (const char of pinyin) {
            if (toneMarks[char]) {
                return toneNames[toneMarks[char]];
            }
        }

        // 没有声调标记，可能是轻声
        return null;
    },

    /**
     * 解析拼音，分成声母和韵母部分
     * 例如：'rén' -> ['r', 'en'], 'xué xiào' -> ['x', 'ue', 'x', 'iao']
     */
    parsePinyinParts(pinyin) {
        // 去除声调
        const cleanPinyin = Utils.removePinyinTones(pinyin.toLowerCase());

        // 声母表
        const shengmu = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l',
            'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w'];

        const parts = [];
        const syllables = cleanPinyin.split(/\s+/);

        syllables.forEach(syllable => {
            if (!syllable) return;

            // 尝试匹配声母
            let foundShengmu = null;
            for (const sm of shengmu) {
                if (syllable.startsWith(sm)) {
                    foundShengmu = sm;
                    break;
                }
            }

            if (foundShengmu) {
                parts.push(foundShengmu);
                const yunmu = syllable.slice(foundShengmu.length);
                if (yunmu) {
                    parts.push(yunmu);
                }
            } else {
                // 没有声母，整个是韵母（如 a, o, e, ai 等）
                parts.push(syllable);
            }
        });

        return parts;
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
