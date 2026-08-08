/* ===============================================
   本地存储管理
   =============================================== */

import { Utils } from './utils.js';

export const Storage = {
    MODES: ['letters', 'pinyin', 'words'],
    MAX_SCORE: 100000,
    DEFAULT_SETTINGS: {
        soundEnabled: true,
        musicEnabled: true,
        volume: 0.7,
        letterLanguage: 'zh'
    },

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
        const data = this.readJson(this.KEYS.USERS, []);
        return Array.isArray(data) ? data.map(user => this.normalizeUser(user)) : [];
    },

    /**
     * 保存用户列表
     */
    saveUsers(users) {
        return this.safeSetItem(this.KEYS.USERS, JSON.stringify(users));
    },

    /**
     * 创建新用户
     */
    createUser(name, avatar) {
        const users = this.getUsers();
        const newUser = {
            id: this.createId(),
            name: String(name ?? '').trim().slice(0, 8),
            avatar: avatar || 'cat',
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

        if (!newUser.name) return null;

        users.push(newUser);
        if (!this.saveUsers(users)) return null;
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
            return this.saveUsers(users) ? users[index] : null;
        }
        return null;
    },

    /**
     * 记录游戏结果
     */
    recordGameResult(userId, mode, score, correct, wrong, errorLetters = []) {
        const user = this.getUser(userId);
        if (!user || !this.MODES.includes(mode)) return null;

        // 更新总分
        const safeScore = Math.min(this.MAX_SCORE, Math.max(0, Math.round(Number(score) || 0)));
        user.totalScore = Math.max(0, user.totalScore + safeScore);
        user.gamesPlayed += 1;

        // 更新模式最高分
        if (safeScore > (Number(user.highScores[mode]) || 0)) {
            user.highScores[mode] = safeScore;
        }

        // 记录错误字母
        (Array.isArray(errorLetters) ? errorLetters : []).forEach(letter => {
            const normalizedLetter = String(letter ?? '').toUpperCase();
            if (!/^[A-Z]$/.test(normalizedLetter)) return;
            user.errorLetters[normalizedLetter] = (user.errorLetters[normalizedLetter] || 0) + 1;
        });

        // 检查新勋章
        const badge = Utils.getBadge(user.totalScore);
        let newBadge = null;
        if (badge && !user.badges.includes(badge.name)) {
            user.badges.push(badge.name);
            newBadge = badge;
        }

        const updatedUser = this.updateUser(userId, user);

        return { user: updatedUser, newBadge };
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
        if (userId) {
            this.safeSetItem(this.KEYS.CURRENT_USER, userId);
        } else {
            this.safeRemoveItem(this.KEYS.CURRENT_USER);
        }
    },

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        let userId = null;
        try {
            userId = localStorage.getItem(this.KEYS.CURRENT_USER);
        } catch {
            return null;
        }
        if (!userId) return null;

        const user = this.getUser(userId);
        if (!user) this.setCurrentUser(null);
        return user || null;
    },

    /**
     * 增加游戏计数（用于防沉迷）
     */
    incrementGameCount() {
        let count = this.getGameCount();
        count++;
        this.safeSetItem(this.KEYS.GAME_COUNT, count.toString());
        return count;
    },

    /**
     * 重置游戏计数
     */
    resetGameCount() {
        this.safeSetItem(this.KEYS.GAME_COUNT, '0');
    },

    /**
     * 获取游戏计数
     */
    getGameCount() {
        let rawCount = '0';
        try {
            rawCount = localStorage.getItem(this.KEYS.GAME_COUNT) || '0';
        } catch {
            rawCount = '0';
        }
        const count = Number.parseInt(rawCount, 10);
        return Number.isFinite(count) && count >= 0 ? count : 0;
    },

    /**
     * 保存设置
     */
    saveSettings(settings) {
        const nextSettings = {
            ...this.DEFAULT_SETTINGS,
            ...(settings || {})
        };
        this.safeSetItem(this.KEYS.SETTINGS, JSON.stringify(nextSettings));
        return nextSettings;
    },

    /**
     * 获取设置
     */
    getSettings() {
        return {
            ...this.DEFAULT_SETTINGS,
            ...this.readJson(this.KEYS.SETTINGS, {})
        };
    },

    readJson(key, fallback) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : fallback;
        } catch {
            console.warn(`无法读取本地数据，已使用默认值: ${key}`);
            try {
                localStorage.removeItem(key);
            } catch {
                // 某些隐私模式下 localStorage 可能不可写，保持内存中的默认值即可。
            }
            return fallback;
        }
    },

    createId() {
        if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
        return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    },

    normalizeUser(user = {}) {
        const source = user && typeof user === 'object' ? user : {};
        return {
            id: String(source.id || this.createId()),
            name: String(source.name || '小玩家').trim().slice(0, 8),
            avatar: source.avatar || 'cat',
            totalScore: Math.min(this.MAX_SCORE, Math.max(0, Number(source.totalScore) || 0)),
            highScores: this.MODES.reduce((scores, mode) => {
                scores[mode] = Math.min(this.MAX_SCORE,
                    Math.max(0, Number(source.highScores?.[mode]) || 0));
                return scores;
            }, {}),
            badges: Array.isArray(source.badges) ? source.badges : [],
            errorLetters: this.normalizeErrorLetters(source.errorLetters),
            gamesPlayed: Math.max(0, Number(source.gamesPlayed) || 0),
            createdAt: source.createdAt || new Date().toISOString()
        };
    },

    normalizeErrorLetters(errorLetters) {
        if (!errorLetters || typeof errorLetters !== 'object' || Array.isArray(errorLetters)) {
            return {};
        }
        return Object.entries(errorLetters).reduce((result, [letter, count]) => {
            const normalizedLetter = String(letter).toUpperCase();
            const safeCount = Math.max(0, Math.floor(Number(count) || 0));
            if (/^[A-Z]$/.test(normalizedLetter) && safeCount > 0) {
                result[normalizedLetter] = safeCount;
            }
            return result;
        }, {});
    },

    safeSetItem(key, value) {
        try {
            localStorage.setItem(key, value);
            return true;
        } catch {
            console.warn(`无法写入本地数据: ${key}`);
            return false;
        }
    },

    safeRemoveItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch {
            return false;
        }
    }
};
