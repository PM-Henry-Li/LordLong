import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const MainLayout = () => {
    return (
        <div className="app-container">
            <Sidebar />
            <div className="main-content">
                <header className="top-header">
                    <h2 style={{ fontSize: '18px', fontWeight: 500, color: 'var(--color-text-main)' }}>
                        系统演示
                    </h2>
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-gray">Demo User</span>
                        <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#E0E4E8', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)', fontWeight: 'bold' }}>
                            U
                        </div>
                    </div>
                </header>
                <main className="page-container">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
