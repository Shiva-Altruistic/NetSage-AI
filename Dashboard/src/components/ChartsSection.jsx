import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

export default function ChartsSection({ overview, comparisonData, theme = 'light' }) {
  const isDark = theme === 'dark';
  const textColor = isDark ? '#cbd5e1' : '#475569';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';

  // Category distribution data
  const categories = ['vlan', 'gateway', 'dhcp', 'dns', 'routing', 'acl', 'nat', 'wireless'];
  const categoryCounts = categories.map((cat) => overview?.categoryCounts?.[cat] || 0);

  const categoryBarData = {
    labels: categories.map((c) => c.toUpperCase()),
    datasets: [
      {
        label: 'Cases in Benchmark',
        data: categoryCounts,
        backgroundColor: [
          '#8b5cf6', // VLAN - purple
          '#10b981', // Gateway - emerald
          '#0284c7', // DHCP - sky
          '#f59e0b', // DNS - amber
          '#6366f1', // Routing - indigo
          '#f43f5e', // ACL - rose
          '#0d9488', // NAT - teal
          '#ec4899', // Wireless - pink
        ],
        borderRadius: 8,
      },
    ],
  };

  const categoryBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: isDark ? '#0f172a' : '#1e293b',
        titleColor: '#fff',
        bodyColor: '#e2e8f0',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        borderWidth: 1,
        padding: 10,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: textColor, font: { family: 'Inter', size: 11, weight: '600' } },
      },
      y: {
        grid: { color: gridColor },
        ticks: { color: textColor, stepSize: 1, font: { family: 'Inter', size: 11 } },
      },
    },
  };

  // OSI Layer Doughnut data
  const osiDoughnutData = {
    labels: ['Layer 2 (Data Link)', 'Layer 3 (Network)', 'Layer 4 (Transport)', 'Layer 7 (Application)'],
    datasets: [
      {
        data: [10, 14, 2, 4],
        backgroundColor: [
          '#8b5cf6', // L2 - purple
          '#06b6d4', // L3 - cyan
          '#f59e0b', // L4 - amber
          '#10b981', // L7 - emerald
        ],
        borderColor: isDark ? '#0f172a' : '#ffffff',
        borderWidth: 3,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: textColor, font: { family: 'Inter', size: 11, weight: '600' }, boxWidth: 12 },
      },
    },
  };

  // A/B Benchmark Bar chart
  const compLabels = (comparisonData || []).map((c) => c.case_id);
  const v1Scores = (comparisonData || []).map((c) => parseFloat(c.v1_pct) || 0);
  const v2Scores = (comparisonData || []).map((c) => parseFloat(c.v2_pct) || 0);

  const abBenchmarkData = {
    labels: compLabels,
    datasets: [
      {
        label: 'Prompt V1 (Baseline)',
        data: v1Scores,
        backgroundColor: isDark ? 'rgba(148, 163, 184, 0.4)' : '#cbd5e1',
        borderRadius: 6,
      },
      {
        label: 'Prompt V2 (CCNA/CCNP Disambiguation)',
        data: v2Scores,
        backgroundColor: 'rgba(139, 92, 246, 0.85)',
        borderRadius: 6,
      },
    ],
  };

  const abBenchmarkOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: textColor, font: { family: 'Inter', size: 11, weight: '600' } },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: textColor, font: { family: 'Inter', size: 11, weight: '600' } },
      },
      y: {
        grid: { color: gridColor },
        ticks: { color: textColor, callback: (v) => `${v}%`, font: { family: 'Inter', size: 11 } },
        max: 100,
      },
    },
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '32px' }}>
      {/* Chart 1: Category Distribution */}
      <div className="glass-card" style={{ padding: '24px', minHeight: '320px' }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', fontWeight: '800', marginBottom: '4px' }}>
          Troubleshooting Case Domain Distribution
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '16px' }}>
          Balanced across 8 core CCNA/CCNP routing & switching categories
        </p>
        <div style={{ height: '220px' }}>
          <Bar data={categoryBarData} options={categoryBarOptions} />
        </div>
      </div>

      {/* Chart 2: OSI Layer Breakdown */}
      <div className="glass-card" style={{ padding: '24px', minHeight: '320px' }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', fontWeight: '800', marginBottom: '4px' }}>
          Diagnostic Coverage by OSI Layer
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '16px' }}>
          Distribution of network root cause failures across the protocol stack
        </p>
        <div style={{ height: '220px' }}>
          <Doughnut data={osiDoughnutData} options={doughnutOptions} />
        </div>
      </div>

      {/* Chart 3: Prompt A/B Scores */}
      {comparisonData && comparisonData.length > 0 && (
        <div className="glass-card" style={{ padding: '24px', minHeight: '340px', gridColumn: '1 / -1' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', fontWeight: '800', marginBottom: '4px' }}>
            Prompt V1 vs Prompt V2 Case Evaluation Scores
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '16px' }}>
            A/B evaluation against instructor ground truth across focus test cases
          </p>
          <div style={{ height: '250px' }}>
            <Bar data={abBenchmarkData} options={abBenchmarkOptions} />
          </div>
        </div>
      )}
    </div>
  );
}
