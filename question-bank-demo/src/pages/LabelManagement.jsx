import React, { useState } from 'react';
import { Plus, Search, Edit2, Trash2, X, ChevronRight, Check } from 'lucide-react';
import classNames from 'classnames';

const LABEL_TYPES = [
    { value: 'ABILITY', label: '能力项' },
    { value: 'PRODUCT_LINE', label: '产品线' },
    { value: 'PROJECT', label: '项目' },
    { value: 'STAGE', label: '阶段' },
    { value: 'TEXTBOOK', label: '教材' },
    { value: 'TYPE', label: '题型' },
    { value: 'CROWD', label: '人群标签' },
];

const MOCK_LABELS = [
    { id: 75, name: '测试标签分类', type: 'ABILITY', status: 'NEW' },
    { id: 74, name: '管综能力项', type: 'ABILITY', status: 'ACTIVE' },
    { id: 72, name: '考研经综', type: 'PRODUCT_LINE', status: 'ACTIVE' },
    { id: 64, name: '英语测试', type: 'ABILITY', status: 'ACTIVE' },
    { id: 22, name: '英语的能力项', type: 'ABILITY', status: 'ACTIVE' },
];

const LabelManagement = () => {
    const [labels, setLabels] = useState(MOCK_LABELS);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingLabel, setEditingLabel] = useState(null);

    // Filter States
    const [searchName, setSearchName] = useState('');
    const [searchType, setSearchType] = useState('');

    const handleEdit = (label) => {
        setEditingLabel(label);
        setIsModalOpen(true);
    };

    const handleCreate = () => {
        setEditingLabel(null);
        setIsModalOpen(true);
    };

    const handleDelete = (id) => {
        if (confirm('确认删除该标签吗？')) {
            setLabels(labels.filter(l => l.id !== id));
        }
    };

    const filteredLabels = labels.filter(l =>
        l.name.includes(searchName) && (searchType === '' || l.type === searchType)
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Search & Actions */}
            <div className="card flex items-end justify-between">
                <div className="flex gap-4" style={{ flex: 1 }}>
                    <div style={{ width: '256px' }}>
                        <label className="input-label">标签名称</label>
                        <div style={{ position: 'relative' }}>
                            <Search style={{ position: 'absolute', left: 12, top: 10, width: 16, height: 16, color: '#bdc3c7' }} />
                            <input
                                type="text"
                                placeholder="请输入标签名称"
                                style={{ paddingLeft: 36 }}
                                value={searchName}
                                onChange={(e) => setSearchName(e.target.value)}
                            />
                        </div>
                    </div>
                    <div style={{ width: '192px' }}>
                        <label className="input-label">标签类型</label>
                        <select
                            value={searchType}
                            onChange={(e) => setSearchType(e.target.value)}
                        >
                            <option value="">全部</option>
                            {LABEL_TYPES.map(t => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <button className="btn btn-primary" onClick={handleCreate}>
                    <Plus className="w-4 h-4" />
                    新建标签
                </button>
            </div>

            {/* Table */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>标签ID</th>
                            <th>标签名称</th>
                            <th>标签分类</th>
                            <th>状态</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredLabels.map((label) => (
                            <tr key={label.id}>
                                <td className="text-gray">{label.id}</td>
                                <td style={{ fontWeight: 500 }}>{label.name}</td>
                                <td>
                                    <span style={{ padding: '2px 6px', background: '#f5f5f5', borderRadius: 4, fontSize: 12 }}>
                                        {LABEL_TYPES.find(t => t.value === label.type)?.label || label.type}
                                    </span>
                                </td>
                                <td>
                                    <span style={{
                                        padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 500,
                                        background: label.status === 'NEW' ? '#e3f2fd' : '#e8f5e9',
                                        color: label.status === 'NEW' ? '#1976d2' : '#2e7d32'
                                    }}>
                                        {label.status === 'NEW' ? '新建' : '有效'}
                                    </span>
                                </td>
                                <td className="flex gap-2">
                                    <button className="btn btn-ghost" style={{ color: '#1976d2', padding: '4px 8px' }} onClick={() => handleEdit(label)}>
                                        编辑
                                    </button>
                                    {label.status === 'NEW' && (
                                        <button className="btn btn-ghost" style={{ color: '#d32f2f', padding: '4px 8px' }} onClick={() => handleDelete(label.id)}>
                                            删除
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {filteredLabels.length === 0 && (
                    <div style={{ padding: 32, textAlign: 'center', color: '#bdc3c7' }}>暂无数据</div>
                )}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <LabelModal
                    isOpen={isModalOpen}
                    initialData={editingLabel}
                    onClose={() => setIsModalOpen(false)}
                    onSave={(data) => {
                        if (editingLabel) {
                            setLabels(labels.map(l => l.id === editingLabel.id ? { ...l, ...data } : l));
                        } else {
                            setLabels([{ ...data, id: Date.now(), status: 'NEW' }, ...labels]);
                        }
                        setIsModalOpen(false);
                    }}
                />
            )}
        </div>
    );
};

// Modal Component
const LabelModal = ({ isOpen, initialData, onClose, onSave }) => {
    const [formData, setFormData] = useState({
        name: initialData?.name || '',
        type: initialData?.type || '',
    });

    const isEdit = !!initialData;

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!formData.name || !formData.type) return;
        onSave(formData);
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <div className="modal-header">
                    <h3>{isEdit ? '编辑标签' : '新建标签'}</h3>
                    <button onClick={onClose} style={{ color: '#999' }}>
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="modal-body">
                        {/* Progress Indicator */}
                        <div className="flex items-center mb-4 text-sm">
                            <div className="flex items-center text-primary" style={{ fontWeight: 500, color: 'var(--color-primary)' }}>
                                <span style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--color-primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8 }}>1</span>
                                基本信息
                            </div>
                            <div style={{ width: 40, height: 1, background: '#eee', margin: '0 8px' }}></div>
                            <div className="flex items-center text-gray">
                                <span style={{ width: 24, height: 24, borderRadius: '50%', background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 8 }}>2</span>
                                管理标签值
                            </div>
                        </div>

                        <div className="input-group">
                            <label className="input-label">标签名称 <span className="text-red">*</span></label>
                            <input
                                type="text"
                                placeholder="请输入标签名称"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                autoFocus
                            />
                        </div>

                        <div className="input-group">
                            <label className="input-label">标签类型 <span className="text-red">*</span></label>
                            <select
                                value={formData.type}
                                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                                disabled={isEdit}
                                style={isEdit ? { background: '#f5f5f5', cursor: 'not-allowed' } : {}}
                            >
                                <option value="" disabled>请选择标签类型</option>
                                {LABEL_TYPES.map(t => (
                                    <option key={t.value} value={t.value}>{t.label}</option>
                                ))}
                            </select>
                            <p className="text-xs text-gray mt-2">创建后类型不可修改</p>
                        </div>
                    </div>

                    <div className="modal-footer">
                        <button type="button" className="btn btn-ghost" onClick={onClose}>取消</button>
                        <button type="submit" className="btn btn-primary">
                            {isEdit ? '保存' : '保存并下一步'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default LabelManagement;
