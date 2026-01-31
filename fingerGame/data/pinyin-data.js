/* ===============================================
   拼音数据库
   =============================================== */

window.PinyinData = {
    // 声母表
    shengmu: [
        'b', 'p', 'm', 'f',
        'd', 't', 'n', 'l',
        'g', 'k', 'h',
        'j', 'q', 'x',
        'zh', 'ch', 'sh', 'r',
        'z', 'c', 's',
        'y', 'w'
    ],

    // 单韵母
    danYunmu: ['a', 'o', 'e', 'i', 'u', 'ü'],

    // 复韵母
    fuYunmu: ['ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 'üe', 'er'],

    // 鼻韵母
    biYunmu: ['an', 'en', 'in', 'un', 'ün', 'ang', 'eng', 'ing', 'ong'],

    // 整体认读音节
    zhengtiridu: [
        'zhi', 'chi', 'shi', 'ri',
        'zi', 'ci', 'si',
        'yi', 'wu', 'yu',
        'ye', 'yue', 'yuan',
        'yin', 'yun', 'ying'
    ],

    // 拼音组合（用于练习）
    combinations: [
        // 简单组合 - ba 系列
        { shengmu: 'b', yunmu: 'a', example: '爸爸的爸' },
        { shengmu: 'b', yunmu: 'o', example: '薄薄的薄' },
        { shengmu: 'b', yunmu: 'i', example: '笔的笔' },
        { shengmu: 'b', yunmu: 'u', example: '不的不' },

        // pa 系列
        { shengmu: 'p', yunmu: 'a', example: '爬山的爬' },
        { shengmu: 'p', yunmu: 'o', example: '坡的坡' },
        { shengmu: 'p', yunmu: 'i', example: '皮的皮' },
        { shengmu: 'p', yunmu: 'u', example: '扑的扑' },

        // ma 系列
        { shengmu: 'm', yunmu: 'a', example: '妈妈的妈' },
        { shengmu: 'm', yunmu: 'o', example: '摸的摸' },
        { shengmu: 'm', yunmu: 'i', example: '米饭的米' },
        { shengmu: 'm', yunmu: 'u', example: '木头的木' },

        // fa 系列
        { shengmu: 'f', yunmu: 'a', example: '发的发' },
        { shengmu: 'f', yunmu: 'o', example: '佛的佛' },
        { shengmu: 'f', yunmu: 'u', example: '服的服' },

        // da 系列
        { shengmu: 'd', yunmu: 'a', example: '大的大' },
        { shengmu: 'd', yunmu: 'e', example: '的的的' },
        { shengmu: 'd', yunmu: 'i', example: '弟弟的弟' },
        { shengmu: 'd', yunmu: 'u', example: '读书的读' },

        // ta 系列
        { shengmu: 't', yunmu: 'a', example: '他她它' },
        { shengmu: 't', yunmu: 'e', example: '特别的特' },
        { shengmu: 't', yunmu: 'i', example: '踢球的踢' },
        { shengmu: 't', yunmu: 'u', example: '兔子的兔' },

        // na 系列
        { shengmu: 'n', yunmu: 'a', example: '那个的那' },
        { shengmu: 'n', yunmu: 'e', example: '呢的呢' },
        { shengmu: 'n', yunmu: 'i', example: '你好的你' },
        { shengmu: 'n', yunmu: 'u', example: '女孩的女' },

        // la 系列
        { shengmu: 'l', yunmu: 'a', example: '拉的拉' },
        { shengmu: 'l', yunmu: 'e', example: '乐的乐' },
        { shengmu: 'l', yunmu: 'i', example: '梨的梨' },
        { shengmu: 'l', yunmu: 'u', example: '路的路' },

        // ga 系列
        { shengmu: 'g', yunmu: 'a', example: '嘎的嘎' },
        { shengmu: 'g', yunmu: 'e', example: '哥哥的哥' },
        { shengmu: 'g', yunmu: 'u', example: '姑姑的姑' },

        // ka 系列
        { shengmu: 'k', yunmu: 'a', example: '卡片的卡' },
        { shengmu: 'k', yunmu: 'e', example: '可以的可' },
        { shengmu: 'k', yunmu: 'u', example: '哭的哭' },

        // ha 系列
        { shengmu: 'h', yunmu: 'a', example: '哈哈的哈' },
        { shengmu: 'h', yunmu: 'e', example: '喝水的喝' },
        { shengmu: 'h', yunmu: 'u', example: '胡的胡' },

        // ji 系列
        { shengmu: 'j', yunmu: 'i', example: '鸡的鸡' },
        { shengmu: 'j', yunmu: 'u', example: '句的句' },

        // qi 系列
        { shengmu: 'q', yunmu: 'i', example: '七的七' },
        { shengmu: 'q', yunmu: 'u', example: '去的去' },

        // xi 系列
        { shengmu: 'x', yunmu: 'i', example: '西瓜的西' },
        { shengmu: 'x', yunmu: 'u', example: '需要的需' },

        // 复韵母组合
        { shengmu: 'b', yunmu: 'ai', example: '白的白' },
        { shengmu: 'm', yunmu: 'ai', example: '买的买' },
        { shengmu: 'h', yunmu: 'ao', example: '好的好' },
        { shengmu: 'x', yunmu: 'iao', example: '小的小' },
        { shengmu: 'n', yunmu: 'iu', example: '牛的牛' },
        { shengmu: 'l', yunmu: 'iu', example: '六的六' },

        // 鼻韵母组合
        { shengmu: 'sh', yunmu: 'an', example: '山的山' },
        { shengmu: 't', yunmu: 'ian', example: '天的天' },
        { shengmu: 'y', yunmu: 'ang', example: '羊的羊' },
        { shengmu: 'd', yunmu: 'ong', example: '东的东' },
        { shengmu: 'x', yunmu: 'ing', example: '星星的星' }
    ]
};
