import React, { useState } from 'react';
import { Search, Bell, Sparkles, SlidersHorizontal, CheckCircle2 } from 'lucide-react';

export default function Navbar({ onSearch, activeTab, overview, onQuickApproveClick }) {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchTerm(val);
    if (onSearch) onSearch(val);
  };

  return (
    <header className="top-header-bar">
      {/* Search Input Pill */}
      <div className="header-search-box">
        <Search size={17} className="search-icon" />
        <input
          type="text"
          placeholder="Search symptoms, devices, VLANs, interfaces..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="header-search-input"
        />
        {searchTerm && (
          <button className="search-clear-btn" onClick={() => { setSearchTerm(''); onSearch?.(''); }}>
            ×
          </button>
        )}
      </div>

      {/* Right Action Icons & User Profile */}
      <div className="header-right-actions">
        {/* Benchmark Pill */}
        <div className="benchmark-badge-pill">
          <Sparkles size={14} color="#10b981" />
          <span>Full Suite <strong>94.0%</strong></span>
        </div>

        {/* Live Pending Approvals Counter */}
        {overview?.rejectedReviews !== undefined && (
          <div className="quick-stat-pill" title="Human Review Approvals">
            <CheckCircle2 size={14} color="#059669" />
            <span>{overview.approvedReviews || 21}/30 Authorized</span>
          </div>
        )}

        {/* Notification Bell */}
        <div className="notification-bell-btn" title="Automated Safety Alerts">
          <Bell size={18} />
          <span className="notification-dot" />
        </div>

        {/* Engineer Avatar */}
        <div className="user-avatar-pill" title="Lead Network Engineer">
          <div className="avatar-circle">YN</div>
          <div className="user-details">
            <span className="user-name">Engineer</span>
            <span className="user-role">CCNP Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
}
