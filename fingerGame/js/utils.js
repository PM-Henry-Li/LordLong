/* ===============================================
   工具函数
   =============================================== */

export const Utils = {
    /**
     * 生成随机整数 [min, max]
     */
    randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /**
     * 从数组中随机选择一个元素
     */
    randomChoice(arr) {
        return Array.isArray(arr) && arr.length > 0
            ? arr[Math.floor(Math.random() * arr.length)]
            : undefined;
    },

    /**
     * 格式化时间 (秒 -> MM:SS)
     */
    formatTime(seconds) {
        const safeSeconds = Math.max(0, Math.floor(Number(seconds) || 0));
        const mins = Math.floor(safeSeconds / 60);
        const secs = safeSeconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 创建得分弹出动画
     */
    createScorePopup(x, y, score, container) {
        const popup = document.createElement('div');
        popup.className = `score-popup ${score > 0 ? 'positive' : 'negative'}`;
        popup.textContent = score > 0 ? `+${score}` : score;
        popup.style.left = `${x}px`;
        popup.style.top = `${y}px`;
        container.appendChild(popup);

        setTimeout(() => popup.remove(), 1000);
    },

    /**
     * 创建粒子效果
     */
    createParticles(x, y, count, container, colors = ['#FFD700', '#4CAF50', '#2196F3']) {
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle particle-star';
            particle.style.left = `${x}px`;
            particle.style.top = `${y}px`;
            particle.style.width = `${Utils.randomInt(5, 12)}px`;
            particle.style.height = particle.style.width;
            particle.style.background = Utils.randomChoice(colors);
            particle.style.setProperty('--tx', `${Utils.randomInt(-80, 80)}px`);
            particle.style.setProperty('--ty', `${Utils.randomInt(-100, -20)}px`);
            container.appendChild(particle);

            setTimeout(() => particle.remove(), 800);
        }
    },

    /**
     * 创建彩纸效果
     */
    createConfetti(count = 50) {
        const container = document.createElement('div');
        container.className = 'confetti-container';
        document.body.appendChild(container);

        const colors = ['#FF6B6B', '#FFD93D', '#6BCB77', '#4D96FF', '#9B59B6', '#FF6B9D'];

        for (let i = 0; i < count; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = `${Utils.randomInt(0, 100)}%`;
            confetti.style.background = Utils.randomChoice(colors);
            confetti.style.animationDelay = `${Utils.randomInt(0, 2000)}ms`;
            confetti.style.animationDuration = `${Utils.randomInt(2000, 4000)}ms`;
            container.appendChild(confetti);
        }

        setTimeout(() => container.remove(), 5000);
    },

    /**
     * 震动效果（如果设备支持）
     */
    vibrate(pattern = 50) {
        if (navigator.vibrate) {
            navigator.vibrate(pattern);
        }
    },

    /**
     * 根据总分判断勋章
     */
    getBadge(totalScore) {
        if (totalScore >= 5000) {
            return { icon: '👑', name: '汉字大师', color: '#FFD700' };
        } else if (totalScore >= 3000) {
            return { icon: '🦸', name: '键盘侠客', color: '#9C27B0' };
        } else if (totalScore >= 1500) {
            return { icon: '🌟', name: '拼音达人', color: '#2196F3' };
        } else if (totalScore >= 500) {
            return { icon: '🎓', name: '拼音学徒', color: '#4CAF50' };
        } else if (totalScore >= 100) {
            return { icon: '🌱', name: '初学新手', color: '#8BC34A' };
        }
        return null;
    },

    /**
     * 获取结算评语
     */
    getResultMessage(score, correct, wrong) {
        const accuracy = correct + wrong > 0 ? correct / (correct + wrong) : 0;

        if (score >= 400) return { title: '🎉 太棒了！', message: '你真是太厉害了！' };
        if (score >= 300) return { title: '🌟 非常好！', message: '继续加油！' };
        if (score >= 200) return { title: '👍 不错哦！', message: '再努力一点点！' };
        if (score >= 100) return { title: '😊 还可以！', message: '多练习会更好！' };
        if (accuracy < 0.3) return { title: '💪 别灰心！', message: '慢慢来，你可以的！' };
        return { title: '🎮 完成了！', message: '休息一下再来吧！' };
    },

    /**
     * 去除拼音中的声调符号，只保留基本字母
     * 例如：'bà' -> 'ba', 'xiǎo' -> 'xiao'
     */
    removePinyinTones(pinyin) {
        const toneMap = {
            'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
            'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
            'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
            'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
            'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
            'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ü': 'v'
        };

        return String(pinyin ?? '')
            .toLowerCase()
            .split('')
            .map(char => toneMap[char] || char)
            .join('');
    },

    /**
     * 将拼音转换为键盘可输入的标准形式。
     * ü 在键盘练习中使用 V 代替，空格和声调会被移除。
     */
    normalizePinyinInput(pinyin) {
        return this.removePinyinTones(pinyin)
            .replace(/\s+/g, '')
            .replace(/ü/g, 'v')
            .toUpperCase();
    }
};
