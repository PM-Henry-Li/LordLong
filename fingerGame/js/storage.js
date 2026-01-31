/* ===============================================
   本地存储管理
   =============================================== */

const Storage = {
    KEYS: {
        USERS: 'pinyin_explorer_users',
        CURRENT_USER: 'pinyin_explorer_current_user',
        SETTINGS: 'pinyin_explorer_settings',
        GAME_COUNT: 'pinyin_explorer_game_count'
    },

    /**
     * 获取所有用户
     */
    getUsers() {
        const data = localStorage.getItem(this.KEYS.USERS);
        return data ? JSON.parse(data) : [];
    },

    /**
     * 保存用户列表
     */
    saveUsers(users) {
        localStorage.setItem(this.KEYS.USERS, JSON.stringify(users));
    },

    /**
     * 创建新用户
     */
    createUser(name, avatar) {
        const users = this.getUsers();
        const newUser = {
            id: Date.now().toString(),
            name,
            avatar,
            totalScore: 0,
            highScores: {
                letters: 0,
                pinyin: 0,
                words: 0
            },
            badges: [],
            errorLetters: {},  // 记录容易错的字母 { 'A': 5, 'B': 3 }
            gamesPlayed: 0,
            createdAt: new Date().toISOString()
        };

        users.push(newUser);
        this.saveUsers(users);
        this.setCurrentUser(newUser.id);

        return newUser;
    },

    /**
     * 获取用户
     */
    getUser(userId) {
        const users = this.getUsers();
        return users.find(u => u.id === userId);
    },

    /**
     * 更新用户数据
     */
    updateUser(userId, updates) {
        const users = this.getUsers();
        const index = users.findIndex(u => u.id === userId);

        if (index !== -1) {
            users[index] = { ...users[index], ...updates };
            this.saveUsers(users);
            return users[index];
        }
        return null;
    },

    /**
     * 记录游戏结果
     */
    recordGameResult(userId, mode, score, correct, wrong, errorLetters = []) {
        const user = this.getUser(userId);
        if (!user) return null;

        // 更新总分
        user.totalScore += score;
        user.gamesPlayed += 1;

        // 更新模式最高分
        if (score > (user.highScores[mode] || 0)) {
            user.highScores[mode] = score;
        }

        // 记录错误字母
        errorLetters.forEach(letter => {
            user.errorLetters[letter] = (user.errorLetters[letter] || 0) + 1;
        });

        // 检查新勋章
        const badge = Utils.getBadge(user.totalScore);
        let newBadge = null;
        if (badge && !user.badges.includes(badge.name)) {
            user.badges.push(badge.name);
            newBadge = badge;
        }

        this.updateUser(userId, user);

        return { user, newBadge };
    },

    /**
     * 获取用户容易出错的字母（返回前5个）
     */
    getFrequentErrors(userId, limit = 5) {
        const user = this.getUser(userId);
        if (!user || !user.errorLetters) return [];

        return Object.entries(user.errorLetters)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
            .map(([letter]) => letter);
    },

    /**
     * 设置当前用户
     */
    setCurrentUser(userId) {
        localStorage.setItem(this.KEYS.CURRENT_USER, userId);
    },

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        const userId = localStorage.getItem(this.KEYS.CURRENT_USER);
        return userId ? this.getUser(userId) : null;
    },

    /**
     * 增加游戏计数（用于防沉迷）
     */
    incrementGameCount() {
        let count = parseInt(localStorage.getItem(this.KEYS.GAME_COUNT) || '0');
        count++;
        localStorage.setItem(this.KEYS.GAME_COUNT, count.toString());
        return count;
    },

    /**
     * 重置游戏计数
     */
    resetGameCount() {
        localStorage.setItem(this.KEYS.GAME_COUNT, '0');
    },

    /**
     * 获取游戏计数
     */
    getGameCount() {
        return parseInt(localStorage.getItem(this.KEYS.GAME_COUNT) || '0');
    },

    /**
     * 保存设置
     */
    saveSettings(settings) {
        localStorage.setItem(this.KEYS.SETTINGS, JSON.stringify(settings));
    },

    /**
     * 获取设置
     */
    getSettings() {
        const data = localStorage.getItem(this.KEYS.SETTINGS);
        return data ? JSON.parse(data) : {
            soundEnabled: true,
            musicEnabled: true,
            volume: 0.7
        };
    }
};

// 导出到全局
window.Storage = Storage;
