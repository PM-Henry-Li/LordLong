/* ===============================================
   主入口
   =============================================== */

import { Audio } from './audio.js';
import { Api } from './api.js';
import { Game } from './game.js';
import { Storage } from './storage.js';

export const Main = {
    currentUser: null,
    selectedAvatar: null,
    currentHelpMode: null,

    /**
     * 初始化应用
     */
    init() {
        Api.init();
        // 初始化游戏模块
        Game.init();

        // 绑定UI事件
        this.bindEvents();

        // 加载已有用户
        this.loadExistingUsers();

        // 检查是否有当前用户
        const currentUser = Storage.getCurrentUser();
        if (currentUser) {
            this.currentUser = currentUser;
            this.showScreen('mode-screen');
            this.updateUserInfo();
            this.updateModeCards();
        }

        document.addEventListener('pinyin:user-updated', (event) => {
            this.currentUser = event.detail?.user || null;
            this.updateUserInfo();
            this.updateModeCards();
            this.loadExistingUsers();
        });

        console.log('🎮 拼音探险家已加载！');
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        // 头像选择
        document.querySelector('.avatar-grid').addEventListener('click', (event) => {
            const avatarButton = event.target.closest('.avatar-btn');
            if (avatarButton) this.selectAvatar(avatarButton.dataset.avatar);
        });

        // 开始冒险按钮
        document.getElementById('btn-enter').addEventListener('click', () => {
            this.handleEnter();
        });

        // 返回开始界面
        document.getElementById('btn-back-start').addEventListener('click', () => {
            this.showScreen('start-screen');
        });

        // 帮助按钮
        document.querySelectorAll('.btn-help').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();  // 阻止冒泡，防止触发模式选择
                const mode = btn.dataset.mode;
                this.showHelp(mode);
            });
        });

        // 关闭帮助弹窗
        document.getElementById('btn-close-help').addEventListener('click', () => {
            this.hideHelp();
        });

        // 从帮助弹窗开始游戏
        document.getElementById('btn-start-game').addEventListener('click', () => {
            const currentMode = this.currentHelpMode;
            this.hideHelp();
            if (currentMode) {
                this.startGame(currentMode);
            }
        });

        // 模式选择
        document.querySelectorAll('.mode-card').forEach(card => {
            card.addEventListener('click', () => {
                if (!card.classList.contains('locked')) {
                    const mode = card.dataset.mode;
                    this.startGame(mode);
                } else {
                    Audio.playWrong();
                    card.style.animation = 'shake 0.3s ease';
                    setTimeout(() => card.style.animation = '', 300);
                }
            });
        });

        // 已有用户选择
        document.getElementById('user-list').addEventListener('click', (e) => {
            const userItem = e.target.closest('.user-item');
            if (userItem) {
                document.querySelectorAll('.user-item').forEach(item => item.classList.remove('selected'));
                userItem.classList.add('selected');

                const userId = userItem.dataset.userId;
                this.currentUser = Storage.getUser(userId);
                if (!this.currentUser) {
                    this.loadExistingUsers();
                    return;
                }
                Storage.setCurrentUser(userId);

                // 清除新用户输入
                document.getElementById('username').value = '';
                document.querySelectorAll('.avatar-btn').forEach(button => {
                    button.classList.remove('selected');
                    button.setAttribute('aria-pressed', 'false');
                });
                this.selectedAvatar = null;

                Audio.playCorrect();
            }
        });

        // 用户名输入时取消选中已有用户
        document.getElementById('username').addEventListener('input', () => {
            document.querySelectorAll('.user-item').forEach(item => item.classList.remove('selected'));
        });
    },

    /**
     * 选择头像，并清除已有玩家选择，避免两种入口同时生效。
     */
    selectAvatar(avatar) {
        const avatarButton = document.querySelector(`.avatar-btn[data-avatar="${avatar}"]`);
        if (!avatarButton) return;

        document.querySelectorAll('.avatar-btn').forEach(button => {
            const selected = button === avatarButton;
            button.classList.toggle('selected', selected);
            button.setAttribute('aria-pressed', String(selected));
        });
        document.querySelectorAll('.user-item').forEach(item => item.classList.remove('selected'));
        this.selectedAvatar = avatar;
        Audio.playKeyPress();
    },

    /**
     * 显示帮助弹窗
     */
    showHelp(mode) {
        this.currentHelpMode = mode;

        // 隐藏所有帮助内容
        document.getElementById('help-letters').style.display = 'none';
        document.getElementById('help-pinyin').style.display = 'none';
        document.getElementById('help-words').style.display = 'none';

        // 显示对应模式的帮助内容
        document.getElementById(`help-${mode}`).style.display = 'block';

        // 检查模式是否锁定
        const isLocked = this.isModeLocked(mode);
        const startBtn = document.getElementById('btn-start-game');
        const requiredScores = { letters: 0, pinyin: 500, words: 1500 };

        if (isLocked) {
            const requiredScore = requiredScores[mode] ?? 0;
            startBtn.textContent = `🔒 需要 ${requiredScore} 分解锁`;
            startBtn.disabled = true;
            startBtn.classList.add('btn-disabled');
        } else {
            startBtn.textContent = '🚀 开始游戏';
            startBtn.disabled = false;
            startBtn.classList.remove('btn-disabled');
        }

        // 显示弹窗
        document.getElementById('help-modal').style.display = 'flex';

        Audio.playKeyPress();
    },

    /**
     * 检查模式是否锁定，卡片和帮助弹窗共用同一套规则。
     */
    isModeLocked(mode) {
        const user = this.currentUser || Storage.getCurrentUser();
        const requiredScores = { letters: 0, pinyin: 500, words: 1500 };
        return !user || (user.totalScore || 0) < (requiredScores[mode] ?? Number.MAX_SAFE_INTEGER);
    },

    /**
     * 隐藏帮助弹窗
     */
    hideHelp() {
        document.getElementById('help-modal').style.display = 'none';
        this.currentHelpMode = null;
    },

    /**
     * 加载已有用户
     */
    loadExistingUsers() {
        const users = Storage.getUsers();
        const container = document.getElementById('existing-users');
        const list = document.getElementById('user-list');

        if (users.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        list.replaceChildren();

        users.forEach(user => {
            const avatarEmoji = this.getAvatarEmoji(user.avatar);
            const item = document.createElement('div');
            item.className = 'user-item';
            item.dataset.userId = user.id;

            const avatar = document.createElement('span');
            avatar.className = 'user-item-avatar';
            avatar.textContent = avatarEmoji;

            const name = document.createElement('span');
            name.className = 'user-item-name';
            name.textContent = user.name;

            const score = document.createElement('span');
            score.className = 'user-item-score';
            score.textContent = `🏆 ${user.totalScore}`;

            item.append(avatar, name, score);
            list.appendChild(item);
        });
    },

    /**
     * 获取头像 emoji
     */
    getAvatarEmoji(avatar) {
        const avatars = {
            'cat': '🐱',
            'dog': '🐶',
            'rabbit': '🐰',
            'bear': '🐻',
            'panda': '🐼',
            'fox': '🦊'
        };
        return avatars[avatar] || '🐱';
    },

    /**
     * 处理进入游戏
     */
    handleEnter() {
        const username = document.getElementById('username').value.trim();

        // 检查是否选择了已有用户
        const selectedExisting = document.querySelector('.user-item.selected');
        if (selectedExisting) {
            const userId = selectedExisting.dataset.userId;
            this.currentUser = Storage.getUser(userId);
            if (!this.currentUser) {
                this.loadExistingUsers();
                return;
            }
            Storage.setCurrentUser(userId);
        } else if (username && this.selectedAvatar) {
            // 创建新用户
            this.currentUser = Storage.createUser(username, this.selectedAvatar);
            if (!this.currentUser) return;
        } else {
            // 提示选择
            Audio.playWrong();
            if (!this.selectedAvatar) {
                Audio.speakGuide('请选择一个头像');
            } else if (!username) {
                Audio.speakGuide('请输入你的名字');
            }
            return;
        }

        Audio.playCorrect();
        Audio.speakGuide(`你好, ${this.currentUser.name}`);

        this.showScreen('mode-screen');
        this.updateUserInfo();
        this.updateModeCards();
    },

    /**
     * 更新用户信息显示
     */
    updateUserInfo() {
        if (!this.currentUser) return;

        document.getElementById('current-avatar').textContent = this.getAvatarEmoji(this.currentUser.avatar);
        document.getElementById('current-name').textContent = this.currentUser.name;
        document.getElementById('total-score').textContent = this.currentUser.totalScore;
    },

    /**
     * 更新模式卡片锁定状态
     */
    updateModeCards() {
        const totalScore = this.currentUser?.totalScore || 0;
        const requiredScores = { letters: 0, pinyin: 500, words: 1500 };

        document.querySelectorAll('.mode-card').forEach(card => {
            const mode = card.dataset.mode;
            const locked = totalScore < (requiredScores[mode] ?? Number.MAX_SAFE_INTEGER);
            card.classList.toggle('locked', locked);
            card.setAttribute('aria-disabled', String(locked));

            const lockOverlay = card.querySelector('.lock-overlay');
            if (lockOverlay) lockOverlay.style.display = locked ? 'flex' : 'none';
        });
    },

    /**
     * 开始游戏
     */
    startGame(mode) {
        if (!this.currentUser || this.isModeLocked(mode)) {
            Audio.playWrong();
            return;
        }
        Audio.playCorrect();
        Game.start(mode);
    },

    /**
     * 显示指定界面
     */
    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        const target = document.getElementById(screenId);
        if (target) target.classList.add('active');
    }
};

// DOM 加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Main.init(), { once: true });
} else {
    Main.init();
}
