/* ===============================================
   虚拟键盘控制
   =============================================== */

const Keyboard = {
    container: null,
    keys: {},
    currentHighlight: null,
    onKeyPress: null,  // 按键回调

    // 键盘布局
    layout: [
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
    ],

    // 左手区按键
    leftHandKeys: ['Q', 'W', 'E', 'R', 'T', 'A', 'S', 'D', 'F', 'G', 'Z', 'X', 'C', 'V', 'B'],

    // 手指指法映射（对应 HTML data-finger 属性）
    fingerGuide: {
        'Q': 'left-pinky', 'A': 'left-pinky', 'Z': 'left-pinky',
        'W': 'left-ring', 'S': 'left-ring', 'X': 'left-ring',
        'E': 'left-middle', 'D': 'left-middle', 'C': 'left-middle',
        'R': 'left-index', 'F': 'left-index', 'V': 'left-index',
        'T': 'left-index', 'G': 'left-index', 'B': 'left-index',
        'Y': 'right-index', 'H': 'right-index', 'N': 'right-index',
        'U': 'right-index', 'J': 'right-index', 'M': 'right-index',
        'I': 'right-middle', 'K': 'right-middle',
        'O': 'right-ring', 'L': 'right-ring',
        'P': 'right-pinky'
    },

    // 虚拟手元素
    leftHand: null,
    rightHand: null,

    /**
     * 初始化键盘
     */
    init(containerId) {
        this.container = document.getElementById(containerId);
        // 不再需要获取整个 leftHand/rightHand，我们需要操作具体的 finger
        this.render();
        this.bindEvents();
    },

    /**
     * 渲染键盘
     */
    render() {
        if (!this.container) return;

        this.container.innerHTML = '';
        this.keys = {};

        this.layout.forEach((row, rowIndex) => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'keyboard-row';

            row.forEach(key => {
                const keyBtn = document.createElement('button');
                keyBtn.className = 'key';
                keyBtn.dataset.key = key;
                keyBtn.textContent = key;

                // 添加左右手区分
                if (this.leftHandKeys.includes(key)) {
                    keyBtn.classList.add('left-hand');
                } else {
                    keyBtn.classList.add('right-hand');
                }

                // 添加手指指引
                const fingerGuide = document.createElement('span');
                fingerGuide.className = 'finger-guide';
                fingerGuide.textContent = this.fingerGuide[key];
                keyBtn.appendChild(fingerGuide);

                rowDiv.appendChild(keyBtn);
                this.keys[key] = keyBtn;
            });

            this.container.appendChild(rowDiv);
        });
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 物理键盘事件
        document.addEventListener('keydown', (e) => {
            const key = e.key.toUpperCase();
            if (this.keys[key]) {
                e.preventDefault();
                this.handleKeyPress(key);
            }
        });

        document.addEventListener('keyup', (e) => {
            const key = e.key.toUpperCase();
            if (this.keys[key]) {
                this.keys[key].classList.remove('pressed');
            }
        });

        // 虚拟键盘点击事件
        this.container.addEventListener('click', (e) => {
            const keyBtn = e.target.closest('.key');
            if (keyBtn) {
                const key = keyBtn.dataset.key;
                this.handleKeyPress(key);
            }
        });

        // 触摸事件（移动端优化）
        this.container.addEventListener('touchstart', (e) => {
            const keyBtn = e.target.closest('.key');
            if (keyBtn) {
                keyBtn.classList.add('pressed');
            }
        }, { passive: true });

        this.container.addEventListener('touchend', (e) => {
            const keyBtn = e.target.closest('.key');
            if (keyBtn) {
                keyBtn.classList.remove('pressed');
            }
        }, { passive: true });
    },

    /**
     * 处理按键
     */
    handleKeyPress(key) {
        const keyBtn = this.keys[key];
        if (!keyBtn) return;

        // 添加按下效果
        keyBtn.classList.add('pressed');
        setTimeout(() => keyBtn.classList.remove('pressed'), 100);

        // 播放按键音
        Audio.playKeyPress();

        // 调用回调
        if (this.onKeyPress) {
            this.onKeyPress(key);
        }
    },

    /**
     * 高亮按键并显示手指引导
     */
    highlight(key) {
        // 移除之前的高亮
        this.clearHighlight();

        const keyBtn = this.keys[key.toUpperCase()];
        if (keyBtn) {
            keyBtn.classList.add('highlight');
            this.currentHighlight = key.toUpperCase();

            // 显示手指引导
            this.showFingerGuide(key.toUpperCase());
        }
    },

    /**
     * 显示手指引导 - 高亮对应 CSS 手指
     */
    showFingerGuide(key) {
        const fingerId = this.fingerGuide[key];
        if (!fingerId) return;

        // 清除所有手指高亮
        document.querySelectorAll('.css-finger').forEach(el => {
            el.classList.remove('active', 'pressing', 'success');
        });

        // 找到对应的 CSS 手指元素
        const cssFinger = document.querySelector(`.css-finger[data-finger="${fingerId}"]`);
        if (cssFinger) {
            cssFinger.classList.add('active');
        }
    },

    /**
     * 清除高亮和手指引导
     */
    clearHighlight() {
        if (this.currentHighlight && this.keys[this.currentHighlight]) {
            this.keys[this.currentHighlight].classList.remove('highlight');
        }
        this.currentHighlight = null;

        // 清除所有手指高亮
        document.querySelectorAll('.css-finger').forEach(el => {
            el.classList.remove('active', 'pressing', 'success');
        });
    },

    /**
     * 显示正确反馈
     */
    showCorrect(key) {
        const keyBtn = this.keys[key.toUpperCase()];
        if (keyBtn) {
            keyBtn.classList.remove('highlight');
            keyBtn.classList.add('correct');
            setTimeout(() => keyBtn.classList.remove('correct'), 500);
        }

        // CSS 手指按压动画
        const fingerId = this.fingerGuide[key.toUpperCase()];
        if (fingerId) {
            const cssFinger = document.querySelector(`.css-finger[data-finger="${fingerId}"]`);
            if (cssFinger) {
                // 移除 active，添加 pressing
                cssFinger.classList.remove('active');
                cssFinger.classList.add('pressing');

                // 播放完按下动画后显示成功色
                setTimeout(() => {
                    cssFinger.classList.remove('pressing');
                    cssFinger.classList.add('success');
                }, 100);

                // 最后清除
                setTimeout(() => {
                    cssFinger.classList.remove('success');
                }, 600);
            }
        }
    },

    /**
     * 显示错误反馈
     */
    showWrong(key) {
        const keyBtn = this.keys[key.toUpperCase()];
        if (keyBtn) {
            keyBtn.classList.add('wrong');
            setTimeout(() => keyBtn.classList.remove('wrong'), 500);
        }
    },

    /**
     * 设置按键回调
     */
    setKeyPressCallback(callback) {
        this.onKeyPress = callback;
    },

    /**
     * 重置键盘状态
     */
    reset() {
        this.clearHighlight();
        Object.values(this.keys).forEach(keyBtn => {
            keyBtn.classList.remove('correct', 'wrong', 'pressed');
        });
    },

    /**
     * 获取所有字母
     */
    getAllLetters() {
        return this.layout.flat();
    },

    /**
     * 显示/隐藏键盘
     */
    show() {
        const container = document.getElementById('keyboard-container');
        if (container) container.style.display = 'block';
    },

    hide() {
        const container = document.getElementById('keyboard-container');
        if (container) container.style.display = 'none';
    }
};

// 导出到全局
window.Keyboard = Keyboard;
