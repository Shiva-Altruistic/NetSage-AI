import React from 'react';
import { Activity, Cpu, Layers, ShieldCheck, Terminal, Users, RefreshCw, Sun, Moon } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onRefresh, loading, theme, setTheme }) {
  const tabs = [
    { id: 'overview', label: 'Overview & Analytics', icon: Activity },
    { id: 'cases', label: 'Case Explorer (30)', icon: Terminal },
    { id: 'prompts', label: 'Prompt A/B Studio', icon: Cpu },
    { id: 'reviews', label: 'Human Review Gate', icon: Users },
    { id: 'rai', label: 'Responsible AI', icon: ShieldCheck },
  ];

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <header className="glass-card navbar">
      <div className="brand-section">
        <div className="logo-badge">
          <Layers size={24} />
        </div>
        <div>
          <h1 className="brand-title">NetSage AI</h1>
          <p className="brand-subtitle">Autonomous Cisco IOS Diagnostic & Governance Center</p>
        </div>
      </div>

      <nav className="nav-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Theme Toggle Button */}
        <button
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          aria-label="Toggle Color Theme"
        >
          {theme === 'light' ? <Moon size={18} color="#6366f1" /> : <Sun size={18} color="#f59e0b" />}
        </button>

        <button
          className="btn btn-outline"
          style={{ padding: '7px 12px', fontSize: '0.75rem' }}
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Sync
        </button>

        <div className="status-pill">
          <div className="status-dot"></div>
          Gemini 3.5 Flash Active
        </div>
      </div>
    </header>
  );
}
