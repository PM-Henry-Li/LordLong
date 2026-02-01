/* ===============================================
   字母森林 - 字母掉落游戏逻辑
   =============================================== */

const LettersGame = {
    canvas: null,
    ctx: null,
    fallingLetters: [],
    animationId: null,
    isRunning: false,

    // 游戏配置
    config: {
        baseSpawnInterval: 2000, // 基准生成间隔
        spawnInterval: 2000,      // 当前生成间隔
        baseFallSpeed: 1.5,      // 基准下落速度
        fallSpeed: 1.5,           // 当前下落速度
        letterSize: 60,           // 字母大小
        maxLetters: 5,            // 同时存在的最大字母数
        frequentErrorBoost: 0.3   // 易错字母出现概率提升
    },

    speedFactor: 1.0,

    // 回调函数
    onCorrect: null,
    onWrong: null,
    onMiss: null,

    /**
     * 初始化游戏
     */
    init(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.resize();

        // 监听窗口大小变化
        window.addEventListener('resize', () => this.resize());
    },

    /**
     * 设置游戏速度
     * @param {number} factor 速度倍率 (0.5 - 2.0)
     */
    setSpeed(factor) {
        const oldFactor = this.speedFactor || 1.0;
        this.speedFactor = factor;

        // 更新配置
        this.config.spawnInterval = this.config.baseSpawnInterval / factor;
        this.config.fallSpeed = this.config.baseFallSpeed * factor;

        // 更新现有字母的速度
        this.fallingLetters.forEach(letter => {
            letter.speed = letter.speed * (factor / oldFactor);
        });

        // 如果正在运行，重启生成定时器
        if (this.isRunning && this.spawnTimer) {
            clearInterval(this.spawnTimer);
            this.spawnTimer = setInterval(() => {
                if (this.fallingLetters.length < this.config.maxLetters) {
                    this.spawnLetter();
                }
            }, this.config.spawnInterval);
        }
    },

    /**
     * 调整画布大小
     */
    resize() {
        if (!this.canvas) return;

        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
    },

    /**
     * 开始游戏
     */
    start() {
        this.isRunning = true;
        this.fallingLetters = [];

        // 在下一帧调整大小，确保 DOM 已经渲染
        requestAnimationFrame(() => {
            this.resize();

            // 延迟生成第一个字母，让用户有准备时间
            setTimeout(() => {
                // 开始生成字母
                this.spawnLetter();
                this.spawnTimer = setInterval(() => {
                    if (this.fallingLetters.length < this.config.maxLetters) {
                        this.spawnLetter();
                    }
                }, this.config.spawnInterval);
            }, 1500);

            // 开始动画循环
            this.animate();

            // 设置键盘回调
            Keyboard.setKeyPressCallback((key) => this.handleKeyPress(key));
        });
    },

    /**
     * 停止游戏
     */
    stop() {
        this.isRunning = false;

        if (this.spawnTimer) {
            clearInterval(this.spawnTimer);
            this.spawnTimer = null;
        }

        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        Keyboard.setKeyPressCallback(null);
        Keyboard.reset();
    },

    /**
     * 暂停游戏
     */
    pause() {
        this.isRunning = false;
        if (this.spawnTimer) {
            clearInterval(this.spawnTimer);
        }
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    },

    /**
     * 继续游戏
     */
    resume() {
        if (!this.isRunning) {
            this.isRunning = true;
            this.spawnTimer = setInterval(() => {
                if (this.fallingLetters.length < this.config.maxLetters) {
                    this.spawnLetter();
                }
            }, this.config.spawnInterval);
            this.animate();
        }
    },

    /**
     * 生成一个掉落的字母
     */
    spawnLetter() {
        const allLetters = Keyboard.getAllLetters();
        let letter;

        // 获取用户容易错的字母，提高它们的出现概率
        const currentUser = Storage.getCurrentUser();
        const frequentErrors = currentUser ? Storage.getFrequentErrors(currentUser.id) : [];

        if (frequentErrors.length > 0 && Math.random() < this.config.frequentErrorBoost) {
            letter = Utils.randomChoice(frequentErrors);
        } else {
            letter = Utils.randomChoice(allLetters);
        }

        const x = Utils.randomInt(80, this.canvas.width - 80);

        this.fallingLetters.push({
            letter,
            x,
            y: -this.config.letterSize,
            speed: this.config.fallSpeed + Math.random() * 0.5,
            size: this.config.letterSize,
            rotation: 0,
            rotationSpeed: (Math.random() - 0.5) * 0.05,
            color: this.getLetterColor(letter),
            collected: false
        });

        // 高亮对应的键盘按键
        this.updateHighlight();

        // 朗读字母，起引导作用
        Audio.speakLetter(letter);
    },

    /**
     * 获取字母颜色（区分左右手）
     */
    getLetterColor(letter) {
        if (Keyboard.leftHandKeys.includes(letter)) {
            return '#64B5F6';  // 左手蓝色
        }
        return '#FFB74D';  // 右手橙色
    },

    /**
     * 更新键盘高亮
     */
    updateHighlight() {
        // 高亮最低位置的字母
        const lowestLetter = this.fallingLetters
            .filter(l => !l.collected)
            .sort((a, b) => b.y - a.y)[0];

        if (lowestLetter) {
            Keyboard.highlight(lowestLetter.letter);
        } else {
            Keyboard.clearHighlight();
        }
    },

    /**
     * 处理按键
     */
    handleKeyPress(key) {
        if (!this.isRunning) return;

        // 查找匹配的字母（优先匹配位置最低的）
        const matchingLetter = this.fallingLetters
            .filter(l => !l.collected && l.letter === key)
            .sort((a, b) => b.y - a.y)[0];

        if (matchingLetter) {
            // 正确！
            matchingLetter.collected = true;

            // 视觉反馈
            Keyboard.showCorrect(key);
            Audio.playCorrect();

            // 粒子效果
            const rect = this.canvas.getBoundingClientRect();
            Utils.createParticles(
                rect.left + matchingLetter.x,
                rect.top + matchingLetter.y,
                8,
                document.body
            );

            // 得分动画
            Utils.createScorePopup(
                matchingLetter.x,
                matchingLetter.y,
                10,
                this.canvas.parentElement
            );

            // 回调
            if (this.onCorrect) {
                this.onCorrect(key, matchingLetter.x, matchingLetter.y);
            }

            this.updateHighlight();
        } else {
            // 错误！
            Keyboard.showWrong(key);
            Audio.playWrong();
            Utils.vibrate(100);

            if (this.onWrong) {
                this.onWrong(key);
            }
        }
    },

    /**
     * 动画循环
     */
    animate() {
        if (!this.isRunning) return;

        this.update();
        this.draw();

        this.animationId = requestAnimationFrame(() => this.animate());
    },

    /**
     * 更新游戏状态
     */
    update() {
        const groundY = this.canvas.height - 100;  // 键盘区域上方

        this.fallingLetters = this.fallingLetters.filter(letter => {
            if (letter.collected) {
                return false;  // 移除已收集的字母
            }

            // 更新位置
            letter.y += letter.speed;
            letter.rotation += letter.rotationSpeed;

            // 检查是否掉到底部
            if (letter.y > groundY) {
                // 错过了！
                if (this.onMiss) {
                    this.onMiss(letter.letter);
                }
                Audio.playWrong();
                return false;  // 移除
            }

            return true;
        });

        this.updateHighlight();
    },

    /**
     * 绘制游戏画面
     */
    draw() {
        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制背景装饰（树木等）
        this.drawBackground();

        // 绘制掉落的字母（苹果形状）
        this.fallingLetters.forEach(letter => {
            if (!letter.collected) {
                this.drawApple(letter);
            }
        });
    },

    /**
     * 绘制背景
     */
    drawBackground() {
        const ctx = this.ctx;

        // 绘制一些简单的云朵
        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        this.drawCloud(100, 60, 60);
        this.drawCloud(300, 100, 45);
        this.drawCloud(500, 50, 50);
        this.drawCloud(700, 80, 55);
    },

    /**
     * 绘制云朵
     */
    drawCloud(x, y, size) {
        const ctx = this.ctx;
        ctx.beginPath();
        ctx.arc(x, y, size * 0.5, 0, Math.PI * 2);
        ctx.arc(x + size * 0.4, y - size * 0.1, size * 0.4, 0, Math.PI * 2);
        ctx.arc(x + size * 0.8, y, size * 0.45, 0, Math.PI * 2);
        ctx.fill();
    },

    /**
     * 绘制苹果形状的字母
     */
    drawApple(letter) {
        const ctx = this.ctx;
        const { x, y, size, rotation, color } = letter;

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(rotation);

        // 苹果身体
        const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, size * 0.5);
        gradient.addColorStop(0, '#FF6B6B');
        gradient.addColorStop(0.7, '#E53935');
        gradient.addColorStop(1, '#C62828');

        ctx.beginPath();
        ctx.arc(0, 0, size * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // 苹果梗
        ctx.beginPath();
        ctx.moveTo(0, -size * 0.4);
        ctx.quadraticCurveTo(5, -size * 0.55, 0, -size * 0.6);
        ctx.strokeStyle = '#5D4037';
        ctx.lineWidth = 4;
        ctx.stroke();

        // 叶子
        ctx.beginPath();
        ctx.ellipse(size * 0.15, -size * 0.5, size * 0.12, size * 0.06, Math.PI / 4, 0, Math.PI * 2);
        ctx.fillStyle = '#4CAF50';
        ctx.fill();

        // 高光
        ctx.beginPath();
        ctx.arc(-size * 0.15, -size * 0.15, size * 0.12, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.fill();

        // 字母
        ctx.fillStyle = '#FFFFFF';
        ctx.font = `bold ${size * 0.5}px "Noto Sans SC", sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(letter.letter, 0, 5);

        // 字母阴影
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.lineWidth = 2;
        ctx.strokeText(letter.letter, 0, 5);

        ctx.restore();
    },

    /**
     * 设置游戏配置
     */
    setConfig(config) {
        this.config = { ...this.config, ...config };
    },

    /**
     * 设置回调函数
     */
    setCallbacks({ onCorrect, onWrong, onMiss }) {
        if (onCorrect) this.onCorrect = onCorrect;
        if (onWrong) this.onWrong = onWrong;
        if (onMiss) this.onMiss = onMiss;
    }
};

// 导出到全局
window.LettersGame = LettersGame;
