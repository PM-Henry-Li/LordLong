import React from 'react';
import { NavLink } from 'react-router-dom';
import { Tags, Network, Settings, BookOpen } from 'lucide-react';
import classNames from 'classnames';

const Sidebar = () => {
  const navItems = [
    { path: '/labels', name: '标签管理', icon: Tags },
    { path: '/knowledge-graph', name: '知识图谱管理', icon: Network },
    { path: '/config', name: '计算模型配置', icon: Settings },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <BookOpen className="w-6 h-6 mr-2" style={{ color: 'var(--color-primary)' }} />
        <span>题库配置中心</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              classNames('nav-item', { 'active': isActive })
            }
          >
            <item.icon className="w-5 h-5 mr-2" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: 16, borderTop: '1px solid #EBEEF0' }}>
        <div style={{ fontSize: 12, color: '#BDC3C7', textAlign: 'center' }}>
          v2.0 Demo Build
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
