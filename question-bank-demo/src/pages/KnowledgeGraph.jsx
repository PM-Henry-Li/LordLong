import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Folder, FileText, Save, Plus, AlertCircle } from 'lucide-react';
import classNames from 'classnames';

// Mock Tree Data
const INITIAL_TREE = [
    {
        id: 1,
        name: '高等数学',
        level: 1,
        children: [
            {
                id: 11,
                name: '函数与极限',
                level: 2,
                children: [
                    {
                        id: 111,
                        name: '映射与函数',
                        level: 3,
                        internal_code: 'M01-01',
                        importance: 'S',
                        duration: 2,
                        mastery_standard: '顶级: S+A+B\n211: S+A\n普通: S'
                    },
                    {
                        id: 112,
                        name: '数列的极限',
                        level: 3,
                        internal_code: 'M01-02',
                        importance: 'A',
                        duration: 3
                    }
                ]
            }
        ]
    },
    {
        id: 2,
        name: '线性代数',
        level: 1,
        children: []
    }
];

const KnowledgeGraph = () => {
    const [treeData, setTreeData] = useState(INITIAL_TREE);
    const [selectedNode, setSelectedNode] = useState(null);

    const handleNodeClick = (node) => {
        setSelectedNode(node);
    };

    const handleUpdateNode = (updatedNode) => {
        // Recursive update function
        const updateTree = (nodes) => {
            return nodes.map(node => {
                if (node.id === updatedNode.id) return { ...node, ...updatedNode };
                if (node.children) return { ...node, children: updateTree(node.children) };
                return node;
            });
        };
        setTreeData(updateTree(treeData));
        setSelectedNode(updatedNode); // Update local state to reflect changes
    };

    return (
        <div className="split-view">
            {/* Left: Tree View */}
            <div className="split-panel-left card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-gray-700">知识点结构</h3>
                    <button className="btn btn-ghost text-sm" style={{ color: '#1976d2', padding: 0 }}>
                        <Plus className="w-4 h-4 mr-1" /> 添加根节点
                    </button>
                </div>
                <div style={{ flex: 1, overflowY: 'auto' }}>
                    {treeData.map(node => (
                        <TreeNode key={node.id} node={node} selectedId={selectedNode?.id} onClick={handleNodeClick} />
                    ))}
                </div>
            </div>

            {/* Right: Edit Panel */}
            <div className="split-panel-right card">
                {selectedNode ? (
                    <EditPanel node={selectedNode} onSave={handleUpdateNode} />
                ) : (
                    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#bdc3c7' }}>
                        <FileText className="w-16 h-16 mb-4" />
                        <p>请选择左侧知识点进行编辑</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// Recursive Tree Node Component
const TreeNode = ({ node, selectedId, onClick }) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const hasChildren = node.children && node.children.length > 0;

    return (
        <div style={{ userSelect: 'none' }}>
            <div
                className={classNames("flex items-center")}
                style={{
                    padding: '8px',
                    borderRadius: 4,
                    cursor: 'pointer',
                    background: selectedId === node.id ? '#e3f2fd' : 'transparent',
                    color: selectedId === node.id ? '#1976d2' : '#2c3e50',
                    paddingLeft: `${(node.level - 1) * 20 + 8}px`
                }}
                onClick={() => onClick(node)}
            >
                <button
                    style={{ padding: 4, marginRight: 4, color: '#bdc3c7', background: 'transparent' }}
                    onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}
                >
                    {hasChildren ? (
                        isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />
                    ) : <span style={{ width: 16, display: 'inline-block' }} />}
                </button>

                {hasChildren ? <Folder className="w-4 h-4 mr-2" style={{ color: '#fbc02d' }} /> : <FileText className="w-4 h-4 mr-2" style={{ color: '#bdc3c7' }} />}
                <span style={{ fontSize: 14, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.name}</span>
            </div>

            {hasChildren && isExpanded && (
                <div>
                    {node.children.map(child => (
                        <TreeNode key={child.id} node={child} selectedId={selectedId} onClick={onClick} />
                    ))}
                </div>
            )}
        </div>
    );
};

// Edit Panel Component
const EditPanel = ({ node, onSave }) => {
    const [formData, setFormData] = useState({ ...node });
    const [dirty, setDirty] = useState(false);

    // Sync form data when node changes
    React.useEffect(() => {
        setFormData({
            ...node,
            internal_code: node.internal_code || '',
            importance: node.importance || 'B',
            duration: node.duration || 0,
            mastery_standard: node.mastery_standard || ''
        });
        setDirty(false);
    }, [node]);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        setDirty(true);
    };

    const handleSave = () => {
        onSave(formData);
        setDirty(false);
        // Simulate API Toast
        alert('保存成功');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="flex items-center justify-between" style={{ borderBottom: '1px solid #eee', paddingBottom: 16 }}>
                <div>
                    <h2 style={{ fontSize: 20, fontWeight: 'bold', color: '#2c3e50' }}>{formData.name}</h2>
                    <p className="text-gray text-sm">ID: {formData.id}</p>
                </div>
                <button
                    className={classNames("btn", dirty ? "btn-primary" : "btn-ghost")}
                    style={!dirty ? { background: '#f5f5f5', color: '#bdc3c7', cursor: 'not-allowed' } : {}}
                    onClick={handleSave}
                    disabled={!dirty}
                >
                    <Save className="w-4 h-4" />
                    保存变更
                </button>
            </div>

            <div className="form-grid">
                <div className="form-full">
                    <label className="input-label">知识点名称</label>
                    <input
                        type="text"
                        value={formData.name}
                        onChange={e => handleChange('name', e.target.value)}
                    />
                </div>

                {/* New PRD Fields */}
                <div>
                    <label className="input-label flex items-center gap-2">
                        内部编码 <span className="text-red">*</span>
                        <div style={{ position: 'relative', display: 'inline-block' }} className="group">
                            <AlertCircle className="w-3 h-3 text-gray" style={{ cursor: 'help' }} />
                        </div>
                    </label>
                    <input
                        type="text"
                        placeholder="如: M01-01"
                        value={formData.internal_code}
                        onChange={e => handleChange('internal_code', e.target.value)}
                        style={{ fontFamily: 'monospace', background: '#fafafa' }}
                    />
                </div>

                <div>
                    <label className="input-label">重要程度 <span className="text-red">*</span></label>
                    <select
                        value={formData.importance}
                        onChange={e => handleChange('importance', e.target.value)}
                    >
                        <option value="S">S - 高频 (核心考点)</option>
                        <option value="A">A - 中频 (重要考点)</option>
                        <option value="B">B - 低频 (基础考点)</option>
                    </select>
                </div>

                <div>
                    <label className="input-label">标准习得用时 (小时)</label>
                    <input
                        type="number"
                        min="0" step="0.5"
                        value={formData.duration}
                        onChange={e => handleChange('duration', parseFloat(e.target.value))}
                    />
                </div>

                <div className="form-full">
                    <label className="input-label">掌握标准定义</label>
                    <textarea
                        rows="4"
                        style={{ width: '100%', padding: 8, border: '1px solid #eee', borderRadius: 4, fontFamily: 'monospace', fontSize: 14 }}
                        placeholder={`例如：\n顶级: S+A+B\n211: S+A\n普通: S`}
                        value={formData.mastery_standard}
                        onChange={e => handleChange('mastery_standard', e.target.value)}
                    />
                    <p className="text-xs text-gray mt-2">定义不同目标层级学员的掌握要求</p>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeGraph;
