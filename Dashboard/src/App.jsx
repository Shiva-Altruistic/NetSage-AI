import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import MetricsCards from './components/MetricsCards';
import ChartsSection from './components/ChartsSection';
import CaseExplorer from './components/CaseExplorer';
import PromptComparison from './components/PromptComparison';
import HumanReviewGate from './components/HumanReviewGate';
import ResponsibleAICenter from './components/ResponsibleAICenter';
import { Layers, Network, ShieldCheck, Terminal, Cpu } from 'lucide-react';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('netsage_theme') || 'light');
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [cases, setCases] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [loading, setLoading] = useState(true);

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

  const handleCardClick = (tabId) => {
    if (tabId) setActiveTab(tabId);
  };

  const topologyBorders = {
    A: 'var(--cat-vlan)',
    B: 'var(--cat-dhcp)',
    C: 'var(--cat-gateway)',
    D: 'var(--cat-dns)',
    E: 'var(--cat-wireless)',
  };

  return (
    <div className="app-container">
      {/* Top Navigation with Theme Toggle */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onRefresh={fetchData}
        loading={loading}
        theme={theme}
        setTheme={setTheme}
      />

      {/* Main KPI Cards (Interactive click-through to tabs) */}
      <MetricsCards overview={overview} onCardClick={handleCardClick} />

      {/* Tab Contents */}
      {activeTab === 'overview' && (
        <div className="tab-content-enter">
          <ChartsSection overview={overview} comparisonData={comparisonData} theme={theme} />

          {/* Network Topologies Grid with Signature Colors */}
          <div className="glass-card" style={{ padding: '28px', marginBottom: '32px' }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '800', marginBottom: '6px' }}>
              Synthetic Network Topologies (Packet Tracer Specification)
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '20px' }}>
              The 30 benchmark cases cover 5 enterprise network architectures with realistic Cisco IOS configurations.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
              {(overview?.topologies || []).map((t) => {
                const borderAccent = topologyBorders[t.id] || 'var(--accent-purple)';
                return (
                  <div
                    key={t.id}
                    style={{
                      background: 'var(--bg-card-subtle)',
                      border: '1px solid var(--border-subtle)',
                      borderTop: `4px solid ${borderAccent}`,
                      padding: '18px',
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                    }}
                    onClick={() => setActiveTab('cases')}
                    title="Click to view cases for this topology"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span className="badge badge-indigo" style={{ background: `${borderAccent}20`, color: borderAccent, borderColor: `${borderAccent}40` }}>
                        Topology {t.id}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>{t.count} Cases</span>
                    </div>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: '800', marginBottom: '4px', color: 'var(--text-primary)' }}>
                      {t.name}
                    </h4>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      <strong>Devices:</strong> {t.devices}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'cases' && <CaseExplorer cases={cases} />}
      {activeTab === 'prompts' && <PromptComparison comparisonData={comparisonData} />}
      {activeTab === 'reviews' && <HumanReviewGate cases={cases} onReviewUpdate={fetchData} />}
      {activeTab === 'rai' && <ResponsibleAICenter />}

      {/* Footer */}
      <footer style={{ marginTop: '48px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '8px', flexWrap: 'wrap' }}>
          <span>NetSage AI v2.5</span>
          <span>•</span>
          <span>Google Gemini 3.5 Flash</span>
          <span>•</span>
          <span>NIST AI RMF 1.0 Aligned</span>
          <span>•</span>
          <span>Cisco IOS Packet Tracer Verified</span>
        </div>
        <p>© 2026 NetSage AI Project. Autonomous network fault diagnosis and responsible AI governance.</p>
      </footer>
    </div>
  );
}
