import React from 'react';
import {
  LayoutDashboard,
  Terminal,
  Cpu,
  UserCheck,
  ShieldCheck,
  Zap,
  Sun,
  Moon,
  RefreshCw,
  LogOut,
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, theme, setTheme, onRefresh, loading, reviewStats }) {
  const menuItems = [
    { id: 'overview', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'cases', label: 'Case Explorer', icon: Terminal, badge: '30' },
    { id: 'prompts', label: 'Prompt Studio', icon: Cpu },
    { id: 'reviews', label: 'Human Review', icon: UserCheck, badge: reviewStats?.pending ? `${reviewStats.pending}` : null },
    { id: 'rai', label: 'Responsible AI', icon: ShieldCheck },
  ];

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <aside className="emerald-sidebar">
      {/* Brand Logo */}
      <div className="sidebar-brand">
        <div className="brand-icon-box">
          <Zap size={22} color="#ffffff" />
        </div>
        <div className="brand-text">
          <span className="brand-title">NetSage AI</span>
          <span className="brand-tagline">Cisco Diagnostic OS</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <div className="nav-item-left">
                <Icon size={19} className="nav-item-icon" />
                <span className="nav-item-label">{item.label}</span>
              </div>
              <div className="nav-item-right">
                {item.badge && <span className="nav-item-badge">{item.badge}</span>}
                {isActive && <span className="nav-active-dot" />}
              </div>
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-status-card">
          <div className="status-indicator-dot" />
          <div className="status-info">
            <div className="status-title">Gemini 3.5 Flash</div>
            <div className="status-sub">24 Rules Pre-Screening</div>
          </div>
        </div>

        <div className="sidebar-bottom-actions">
          <button
            className="sidebar-action-btn"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
            <span>{theme === 'light' ? 'Dark' : 'Light'}</span>
          </button>

          <button
            className="sidebar-action-btn"
            onClick={onRefresh}
            disabled={loading}
            title="Synchronize Data"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span>Sync</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
