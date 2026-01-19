import React, { useState } from 'react';
import { Save, AlertTriangle, HelpCircle } from 'lucide-react';

const ConfigPanel = () => {
    // Mock Config Data
    const [config, setConfig] = useState({
        dynamicDifficulty: {
            minSample: 30, // N
            rules: [
                { currentLevel: 1, pMin: 0.15, pMax: 0.35, action: '升级 -> 2星' },
                { currentLevel: 2, pMin: 0.35, pMax: 0.60, action: '升级 -> 3星' },
                { currentLevel: 3, pMin: 0.60, pMax: 0.80, action: '保持' },
            ]
        },
        schoolLevels: [
            { id: 1, name: '985/顶尖院校', targetScore: 380, mastery: ['S', 'A', 'B'] },
            { id: 2, name: '211/重点院校', targetScore: 340, mastery: ['S', 'A'] },
            { id: 3, name: '普通院校', targetScore: 290, mastery: ['S'] },
        ]
    });

    const handleSave = () => {
        alert('配置已保存 (Mock)');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Section 1: Dynamic Difficulty */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <h3 style={{ fontSize: 18, fontWeight: 'bold' }}>题目难度动态调整模型 (Dynamic Difficulty)</h3>
                        <div style={{ position: 'relative' }} className="group">
                            <HelpCircle className="w-4 h-4 text-gray" style={{ cursor: 'help' }} />
                        </div>
                    </div>
                    <button className="btn btn-primary" onClick={handleSave}>
                        <Save className="w-4 h-4" /> 保存配置
                    </button>
                </div>

                <div className="form-grid">
                    <div>
                        <label className="input-label">置信样本量阈值 (N)</label>
                        <div className="flex items-center gap-2">
                            <input
                                type="number"
                                value={config.dynamicDifficulty.minSample}
                                onChange={(e) => setConfig({ ...config, dynamicDifficulty: { ...config.dynamicDifficulty, minSample: parseInt(e.target.value) } })}
                                style={{ width: 128 }}
                            />
                            <span className="text-gray text-sm">次作答</span>
                        </div>
                        <p className="text-xs text-gray mt-2">
                            只有当题目累计作答次数超过此阈值时，才会触发难度评估。
                            <br />
                            <span style={{ color: '#d35400', display: 'inline-flex', alignItems: 'center', marginTop: 4 }}>
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                新题冷启动策略：N=10时会触发一次快速评估
                            </span>
                        </p>
                    </div>

                    <div>
                        <label className="input-label">难度判定规则预览</label>
                        <div style={{ background: '#fafafa', border: '1px solid #eee', borderRadius: 4, padding: 12, fontSize: 13, height: 128, overflowY: 'auto' }}>
                            {config.dynamicDifficulty.rules.map((rule, idx) => (
                                <div key={idx} className="flex justify-between" style={{ borderBottom: '1px solid #eee', padding: '4px 0' }}>
                                    <span>Lv.{rule.currentLevel}</span>
                                    <span className="text-gray">{rule.pMin} ≤ P &lt; {rule.pMax}</span>
                                    <span style={{ fontWeight: 'bold', color: '#1976d2' }}>{rule.action}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Section 2: Target Score Mapping */}
            <div className="card">
                <h3 style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 24 }}>院校目标分映射配置 (Target Score Mapping)</h3>

                <table className="data-table">
                    <thead>
                        <tr>
                            <th>院校等级</th>
                            <th>目标总分线</th>
                            <th>知识点掌握要求</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {config.schoolLevels.map((level, idx) => (
                            <tr key={level.id}>
                                <td style={{ padding: 12 }}>
                                    <input
                                        type="text"
                                        value={level.name}
                                        style={{ width: 180 }}
                                        onChange={(e) => {
                                            const newLevels = [...config.schoolLevels];
                                            newLevels[idx].name = e.target.value;
                                            setConfig({ ...config, schoolLevels: newLevels });
                                        }}
                                    />
                                </td>
                                <td style={{ padding: 12 }}>
                                    <input
                                        type="number"
                                        value={level.targetScore}
                                        style={{ width: 96 }}
                                        onChange={(e) => {
                                            const newLevels = [...config.schoolLevels];
                                            newLevels[idx].targetScore = parseInt(e.target.value);
                                            setConfig({ ...config, schoolLevels: newLevels });
                                        }}
                                    />
                                </td>
                                <td style={{ padding: 12 }}>
                                    <div className="flex gap-2">
                                        {['S', 'A', 'B'].map(rank => (
                                            <label key={rank} className="flex items-center gap-1" style={{ fontWeight: 'normal', cursor: 'pointer' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={level.mastery.includes(rank)}
                                                    onChange={(e) => {
                                                        const newLevels = [...config.schoolLevels];
                                                        if (e.target.checked) {
                                                            newLevels[idx].mastery.push(rank);
                                                        } else {
                                                            newLevels[idx].mastery = newLevels[idx].mastery.filter(r => r !== rank);
                                                        }
                                                        setConfig({ ...config, schoolLevels: newLevels });
                                                    }}
                                                />
                                                {rank}
                                            </label>
                                        ))}
                                    </div>
                                </td>
                                <td style={{ padding: 12, color: '#d32f2f', cursor: 'pointer' }}>删除</td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                <button className="btn btn-ghost" style={{ marginTop: 16, width: '100%', border: '1px dashed #90caf9', color: '#1976d2' }}>
                    + 添加院校等级
                </button>
            </div>
        </div>
    );
};

export default ConfigPanel;
