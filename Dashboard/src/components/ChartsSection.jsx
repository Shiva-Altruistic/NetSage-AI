import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import {
  TrendingUp,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowUpRight,
  Sparkles,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  Filler
);

export default function ChartsSection({
  overview,
  comparisonData,
  theme = 'light',
  cases = [],
  onQuickApprove,
  onViewCase,
}) {
  const isDark = theme === 'dark';
  const [activeSuiteToggle, setActiveSuiteToggle] = useState('full'); // 'focus' | 'full'
  const [activeInterval, setActiveInterval] = useState('monthly');
  const [approvingId, setApprovingId] = useState(null);
  const [approvedToast, setApprovedToast] = useState('');

  // Domain accuracy mapping from regenerated eval_report.md
  const domainData = [
    { domain: 'VLAN', score: 90.5, count: 4, layer: 'L2' },
    { domain: 'Gateway', score: 93.8, count: 4, layer: 'L3' },
    { domain: 'DHCP', score: 100.0, count: 4, layer: 'L7' },
    { domain: 'DNS', score: 96.7, count: 3, layer: 'L7' },
    { domain: 'Routing', score: 100.0, count: 4, layer: 'L3' },
    { domain: 'ACL', score: 94.7, count: 3, layer: 'L4' },
    { domain: 'NAT', score: 86.5, count: 3, layer: 'L3' },
    { domain: 'Wireless', score: 89.7, count: 5, layer: 'L1-L2' },
  ];

  // Top-Left Card: Bar chart matching reference image (mint bars with orange dashed reference line)
  const barLabels = domainData.map((d) => d.domain);
  const barScores = domainData.map((d) => d.score);

  const analyticsBarData = {
    labels: barLabels,
    datasets: [
      {
        label: 'Empirical Accuracy (%)',
        data: barScores,
        backgroundColor: isDark ? 'rgba(52, 211, 153, 0.75)' : '#1e6b52',
        hoverBackgroundColor: isDark ? '#34d399' : '#14533e',
        borderRadius: 8,
        barPercentage: 0.55,
      },
    ],
  };

  const analyticsBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark ? '#0f172a' : '#1e293b',
        titleColor: '#fff',
        bodyColor: '#e2e8f0',
        padding: 10,
        callbacks: {
          label: (ctx) => ` Accuracy: ${ctx.raw}%`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: isDark ? '#94a3b8' : '#64748b',
          font: { family: 'Inter', size: 11, weight: '600' },
        },
      },
      y: {
        min: 60,
        max: 100,
        grid: {
          color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
        },
        ticks: {
          color: isDark ? '#94a3b8' : '#64748b',
          callback: (val) => `${val}%`,
          stepSize: 10,
          font: { family: 'Inter', size: 11 },
        },
      },
    },
  };

  // Top-Right Card: Smooth Curved Sparkline Line Chart
  const splineLineData = {
    labels: ['C001', 'C005', 'C011', 'C015', 'C018', 'C022', 'C025', 'C028', 'C030'],
    datasets: [
      {
        label: 'Inference Precision',
        data: [98, 91, 94, 96, 99, 93, 95, 92, 97],
        borderColor: isDark ? '#34d399' : '#1e6b52',
        backgroundColor: isDark ? 'rgba(52, 211, 153, 0.12)' : 'rgba(30, 107, 82, 0.08)',
        fill: true,
        tension: 0.45,
        borderWidth: 2.5,
        pointRadius: 3,
        pointHoverRadius: 6,
      },
    ],
  };

  const splineLineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark ? '#0f172a' : '#1e293b',
        titleColor: '#fff',
        bodyColor: '#e2e8f0',
        padding: 8,
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { display: false } },
      y: { min: 80, max: 100, grid: { display: false }, ticks: { display: false } },
    },
  };

  // Handle in-place 1-click Quick Approval on the Dashboard
  const handleInlineApprove = async (caseId, e) => {
    e?.stopPropagation();
    setApprovingId(caseId);
    try {
      const res = await fetch('/api/human-reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          decision: 'APPROVED',
          notes: 'Instant zero-scroll authorized by lead engineer from dashboard card.',
        }),
      });
      if (res.ok) {
        setApprovedToast(`✓ Case ${caseId} authorized successfully right in place!`);
        if (onQuickApprove) onQuickApprove();
        setTimeout(() => setApprovedToast(''), 2500);
      }
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setApprovingId(null);
    }
  };

  // Cases pending review or needing attention
  const reviewQueue = (cases || []).slice(0, 4);

  return (
    <div className="reference-dashboard-grid">
      {/* Toast Notification */}
      {approvedToast && (
        <div className="inline-toast-banner">
          <Sparkles size={16} color="#10b981" />
          <span>{approvedToast}</span>
        </div>
      )}

      {/* ====================================================================
          ROW 1: Analytics Bar Chart (Left) + Performance Sparkline (Right)
         ==================================================================== */}
      <div className="dash-row-two-col">
        {/* Top-Left Card: Analytics Bar Chart */}
        <div className="modern-white-card card-analytics">
          <div className="card-header-flex">
            <div>
              <h3 className="card-title">Domain Troubleshooting Analytics</h3>
              <p className="card-subtitle">8 CCNA/CCNP network domains across 30 benchmark topologies</p>
            </div>
            <div className="card-header-actions">
              <span className="pill-dropdown-tag">
                <Clock size={13} style={{ marginRight: '5px' }} /> Full Suite Benchmark
              </span>
            </div>
          </div>

          {/* Benchmark target line indicator */}
          <div className="benchmark-target-line-indicator">
            <span className="target-line-dash" />
            <span className="target-line-text">90% CCNA Target Threshold</span>
          </div>

          <div style={{ height: '240px', marginTop: '12px' }}>
            <Bar data={analyticsBarData} options={analyticsBarOptions} />
          </div>

          {/* Month / Domain labels below */}
          <div className="domain-pill-ribbon">
            <span className="ribbon-item">Layer 2 Switching</span>
            <span className="ribbon-item">Layer 3 Gateway & Routing</span>
            <span className="ribbon-item">L4–L7 Services & WiFi</span>
          </div>
        </div>

        {/* Top-Right Card: Performance & Accuracy Sparkline */}
        <div className="modern-white-card card-performance">
          <div className="card-header-flex">
            <div>
              <span className="card-eyebrow">Diagnostic Precision</span>
              <h3 className="card-title">Gemini 3.5 Flash Model</h3>
            </div>
            <div className="card-pill-toggle">
              <button
                className={`toggle-pill-btn ${activeSuiteToggle === 'focus' ? 'active' : ''}`}
                onClick={() => setActiveSuiteToggle('focus')}
              >
                Focus (8)
              </button>
              <button
                className={`toggle-pill-btn ${activeSuiteToggle === 'full' ? 'active' : ''}`}
                onClick={() => setActiveSuiteToggle('full')}
              >
                Full Suite (30)
              </button>
            </div>
          </div>

          {/* 3 Metric Stat Highlights */}
          <div className="performance-stats-row">
            <div className="perf-stat-item">
              <div className="perf-stat-num">
                {activeSuiteToggle === 'full' ? '94.0%' : '87.5%'}
              </div>
              <div className="perf-stat-label">Overall Score</div>
            </div>
            <div className="perf-stat-item">
              <div className="perf-stat-num">1.82s</div>
              <div className="perf-stat-label">Mean Latency</div>
            </div>
            <div className="perf-stat-item">
              <div className="perf-stat-num">90.0%</div>
              <div className="perf-stat-label">Grounding Rate</div>
            </div>
          </div>

          {/* Smooth Curve Chart */}
          <div style={{ height: '110px', marginTop: '14px' }}>
            <Line data={splineLineData} options={splineLineOptions} />
          </div>

          {/* Segmented Interval Buttons */}
          <div className="interval-segmented-controls">
            {['Yearly', 'Monthly', 'Live Suite'].map((iv) => (
              <button
                key={iv}
                className={`interval-btn ${activeInterval.toLowerCase() === iv.toLowerCase() ? 'active' : ''}`}
                onClick={() => setActiveInterval(iv.toLowerCase())}
              >
                {iv}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ====================================================================
          ROW 2: Telemetry Sparklines (Left) + Quick Approvals Queue (Right)
         ==================================================================== */}
      <div className="dash-row-two-col">
        {/* Middle-Left Card: System Telemetry Indicators */}
        <div className="modern-white-card card-telemetry">
          <h3 className="card-title" style={{ marginBottom: '16px' }}>
            System Reliability Telemetry
          </h3>

          {/* Telemetry Row 1 */}
          <div className="telemetry-sparkline-row">
            <div className="telemetry-left">
              <div className="telemetry-big-num">93.3%</div>
              <div className="telemetry-label">Concept Tag Accuracy</div>
            </div>
            {/* SVG Sparkline */}
            <div className="telemetry-sparkline-svg">
              <svg viewBox="0 0 100 24" width="100%" height="24">
                <path
                  d="M0,18 L20,16 L40,20 L60,10 L80,14 L100,4"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div className="telemetry-right">
              <div className="telemetry-stat-value">28 / 30</div>
              <span className="telemetry-badge badge-green">UP ▲ 12.5%</span>
            </div>
          </div>

          {/* Telemetry Row 2 */}
          <div className="telemetry-sparkline-row">
            <div className="telemetry-left">
              <div className="telemetry-big-num">98.2%</div>
              <div className="telemetry-label">Fix Technical Match</div>
            </div>
            {/* SVG Sparkline */}
            <div className="telemetry-sparkline-svg">
              <svg viewBox="0 0 100 24" width="100%" height="24">
                <path
                  d="M0,20 L25,18 L50,12 L75,14 L100,6"
                  fill="none"
                  stroke="#0284c7"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <div className="telemetry-right">
              <div className="telemetry-stat-value">1.82s</div>
              <span className="telemetry-badge badge-blue">TIME ⚡</span>
            </div>
          </div>
        </div>

        {/* Middle-Right Card: Quick Approval Queue (Zero-scroll approvals!) */}
        <div className="modern-white-card card-quick-approval">
          <div className="card-header-flex">
            <div>
              <span className="card-eyebrow" style={{ color: '#059669' }}>
                Zero-Scroll Review Station
              </span>
              <h3 className="card-title">Engineer Quick Approval Queue</h3>
            </div>
            <span className="badge badge-emerald">
              {overview?.approvedReviews || 21} / 30 Authorized
            </span>
          </div>

          <p className="card-subtitle" style={{ marginBottom: '14px' }}>
            Click <strong>Approve</strong> right on any card to authorize remediation in place without scrolling away.
          </p>

          <div className="quick-approval-list">
            {reviewQueue.map((c) => {
              const isApproved = c.human_decision === 'APPROVED';
              const isProcessing = approvingId === c.case_id;

              return (
                <div key={c.case_id} className="quick-approval-row">
                  <div className="approval-row-left">
                    <span className="approval-case-id">{c.case_id}</span>
                    <span className={`cat-badge cat-${c.concept_tag?.toLowerCase()}`}>
                      {c.concept_tag}
                    </span>
                    <span className="approval-symptom-text" title={c.symptom}>
                      {c.symptom}
                    </span>
                  </div>

                  <div className="approval-row-right">
                    {isApproved ? (
                      <span className="badge-approved-inline">
                        <CheckCircle2 size={13} /> Authorized
                      </span>
                    ) : (
                      <button
                        className="btn-quick-approve-inline"
                        onClick={(e) => handleInlineApprove(c.case_id, e)}
                        disabled={isProcessing}
                        title="Click to approve right here in place"
                      >
                        <CheckCircle2 size={13} />
                        {isProcessing ? 'Saving...' : 'Approve'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ====================================================================
          ROW 3: 3 Circular Donut Gauges (Left) + Top Categories/Risks (Right)
         ==================================================================== */}
      <div className="dash-row-two-col">
        {/* Bottom-Left Card: 3 Circular Gauges matching the reference image */}
        <div className="modern-white-card card-circular-gauges">
          <h3 className="card-title" style={{ marginBottom: '20px' }}>
            Core Diagnostic Performance Gauges
          </h3>

          <div className="circular-gauges-grid">
            {/* Gauge 1: 94% Overall Score (Amber/Gold) */}
            <div className="gauge-item">
              <div className="gauge-circle-wrap">
                <svg className="gauge-svg" viewBox="0 0 36 36">
                  <path
                    className="gauge-bg-path"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="gauge-val-path gauge-color-gold"
                    strokeDasharray="94, 100"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <span className="gauge-percent-text">94%</span>
              </div>
              <div className="gauge-meta">
                <div className="gauge-label">Overall Score</div>
                <div className="gauge-sub">28/30 Cases</div>
              </div>
            </div>

            {/* Gauge 2: 70% Approval Rate (Emerald) */}
            <div className="gauge-item">
              <div className="gauge-circle-wrap">
                <svg className="gauge-svg" viewBox="0 0 36 36">
                  <path
                    className="gauge-bg-path"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="gauge-val-path gauge-color-emerald"
                    strokeDasharray="70, 100"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <span className="gauge-percent-text">70%</span>
              </div>
              <div className="gauge-meta">
                <div className="gauge-label">Approval Rate</div>
                <div className="gauge-sub">21 Authorized</div>
              </div>
            </div>

            {/* Gauge 3: 90% Evidence Grounding (Purple) */}
            <div className="gauge-item">
              <div className="gauge-circle-wrap">
                <svg className="gauge-svg" viewBox="0 0 36 36">
                  <path
                    className="gauge-bg-path"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className="gauge-val-path gauge-color-purple"
                    strokeDasharray="90, 100"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <span className="gauge-percent-text">90%</span>
              </div>
              <div className="gauge-meta">
                <div className="gauge-label">Grounding Rate</div>
                <div className="gauge-sub">0 Hallucinations</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom-Right Card: Top Categories & Security Safeguards */}
        <div className="modern-white-card card-summary-lists">
          <div className="summary-lists-grid">
            {/* Column 1: Top Domains */}
            <div className="summary-list-col">
              <h4 className="summary-col-title">Top Benchmark Domains</h4>
              <ol className="summary-numbered-list">
                <li>
                  <span className="item-name">Routing (OSPF / EIGRP)</span>
                  <span className="item-badge">100% Match</span>
                </li>
                <li>
                  <span className="item-name">DHCP Service</span>
                  <span className="item-badge">100% Match</span>
                </li>
                <li>
                  <span className="item-name">DNS Resolution</span>
                  <span className="item-badge">96.7% Match</span>
                </li>
                <li>
                  <span className="item-name">ACL Traffic Filtering</span>
                  <span className="item-badge">94.7% Match</span>
                </li>
              </ol>
            </div>

            {/* Column 2: Safeguards */}
            <div className="summary-list-col">
              <h4 className="summary-col-title">Blocked High-Risk Actions</h4>
              <ul className="summary-bullet-list">
                <li>
                  <span className="risk-tag risk-high">High</span>
                  <span className="risk-cmd">clear ip dhcp binding *</span>
                </li>
                <li>
                  <span className="risk-tag risk-medium">Medium</span>
                  <span className="risk-cmd">interface shutdown</span>
                </li>
                <li>
                  <span className="risk-tag risk-medium">Medium</span>
                  <span className="risk-cmd">switchport trunk native vlan</span>
                </li>
                <li>
                  <span className="risk-tag risk-low">Screened</span>
                  <span className="risk-cmd">reload / erase startup-config</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
