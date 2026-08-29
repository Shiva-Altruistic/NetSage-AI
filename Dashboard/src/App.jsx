import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import ChartsSection from './components/ChartsSection';
import CaseExplorer from './components/CaseExplorer';
import PromptComparison from './components/PromptComparison';
import HumanReviewGate from './components/HumanReviewGate';
import ResponsibleAICenter from './components/ResponsibleAICenter';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('netsage_theme') || 'light');
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [cases, setCases] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('netsage_theme', theme);
  }, [theme]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ovRes, casesRes, compRes] = await Promise.all([
        fetch('/api/overview'),
        fetch('/api/cases'),
        fetch('/api/prompt-comparison'),
      ]);

      const [ovData, casesData, compData] = await Promise.all([
        ovRes.json(),
        casesRes.json(),
        compRes.json(),
      ]);

      setOverview(ovData);
      setCases(casesData);
      setComparisonData(compData);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleQuickApproveFromDash = () => {
    fetchData();
  };

  return (
    <div className="reference-app-wrapper">
      {/* Main Container Shell matching the user reference screenshot */}
      <div className="app-canvas-container">
        {/* Left Emerald Sidebar Navigation */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          theme={theme}
          setTheme={setTheme}
          onRefresh={fetchData}
          loading={loading}
          reviewStats={{
            approved: overview?.approvedReviews || 21,
            pending: 30 - (overview?.approvedReviews || 21),
          }}
        />

        {/* Right Main Dashboard Area */}
        <main className="app-main-panel">
          {/* Top Header with Search Pill, Notification & User Avatar */}
          <Navbar
            onSearch={(term) => {
              setSearchQuery(term);
              if (term && activeTab === 'overview') {
                setActiveTab('cases');
              }
            }}
            activeTab={activeTab}
            overview={overview}
            onQuickApproveClick={() => setActiveTab('reviews')}
          />

          {/* Active Tab View */}
          <div className="tab-scroll-container">
            {activeTab === 'overview' && (
              <ChartsSection
                overview={overview}
                comparisonData={comparisonData}
                theme={theme}
                cases={cases}
                onQuickApprove={handleQuickApproveFromDash}
                onViewCase={() => setActiveTab('cases')}
              />
            )}

            {activeTab === 'cases' && (
              <CaseExplorer cases={cases} initialSearch={searchQuery} />
            )}

            {activeTab === 'prompts' && (
              <PromptComparison comparisonData={comparisonData} />
            )}

            {activeTab === 'reviews' && (
              <HumanReviewGate cases={cases} onReviewUpdate={fetchData} />
            )}

            {activeTab === 'rai' && (
              <ResponsibleAICenter overview={overview} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
