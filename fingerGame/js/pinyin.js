/* ===============================================
   拼音合成室游戏逻辑
   =============================================== */

const PinyinGame = {
    currentPinyin: null,
    inputBuffer: '',
    inputIndex: 0,
    isRunning: false,

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
        this.isRunning = true;
        this.inputBuffer = '';
        this.inputIndex = 0;

        // 生成第一个拼音
        this.nextPinyin();

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
     * 生成下一个拼音
     */
    nextPinyin() {
        // 从拼音数据中随机选择
        const pinyin = Utils.randomChoice(window.PinyinData.combinations);
        this.currentPinyin = pinyin;
        this.inputBuffer = '';
        this.inputIndex = 0;

        // 更新显示
        this.elements.shengmu.textContent = pinyin.shengmu;
        this.elements.yunmu.textContent = pinyin.yunmu;
        this.elements.result.textContent = '?';

        // 高亮第一个字母
        const fullPinyin = pinyin.shengmu + pinyin.yunmu;
        if (fullPinyin.length > 0) {
            Keyboard.highlight(fullPinyin[0].toUpperCase());
        }

        // 朗读提示
        setTimeout(() => {
            Audio.speakPinyin(pinyin.shengmu);
        }, 300);
    },

    /**
     * 处理按键
     */
    handleKeyPress(key) {
        if (!this.isRunning || !this.currentPinyin) return;

        const fullPinyin = (this.currentPinyin.shengmu + this.currentPinyin.yunmu).toUpperCase();
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

        // 显示结果
        this.elements.result.textContent = pinyin.shengmu + pinyin.yunmu;
        this.elements.result.style.animation = 'scaleBounce 0.5s ease';

        // 朗读完整拼音
        setTimeout(() => {
            Audio.speakPinyin(`${pinyin.shengmu}, ${pinyin.yunmu}, ${pinyin.shengmu}${pinyin.yunmu}`);
            if (pinyin.example) {
                setTimeout(() => {
                    Audio.speakPinyin(pinyin.example);
                }, 1500);
            }
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
        setTimeout(() => {
            if (this.isRunning) {
                this.elements.result.style.animation = '';
                this.nextPinyin();
            }
        }, 2500);
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
window.PinyinGame = PinyinGame;
