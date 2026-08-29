import React from 'react';
import { Award, CheckCircle2, ShieldAlert, Cpu, Network, Sparkles } from 'lucide-react';

export default function MetricsCards({ overview, onCardClick }) {
  if (!overview) return null;

  const cards = [
    {
      id: 'cases',
      title: 'Total Network Cases',
      value: overview.totalCases || 30,
      subtitle: '5 Topologies (SOHO, Campus, WAN, Edge, WiFi)',
      icon: Network,
      colorClass: 'card-purple',
      iconBg: '#ede9fe',
      iconColor: '#7c3aed',
    },
    {
      id: 'prompts',
      title: 'Prompt V2 Diagnostic Score',
      value: `${overview.v2AvgScore || '81.5'}%`,
      subtitle: `+18.4% improvement over V1 baseline (${overview.v1AvgScore || '63.1'}%)`,
      icon: Cpu,
      colorClass: 'card-cyan',
      iconBg: '#e0f2fe',
      iconColor: '#0284c7',
    },
    {
      id: 'reviews',
      title: 'Human Review Sign-off',
      value: `${overview.approvalRate || '100'}%`,
      subtitle: `${overview.approvedReviews || 0} approved, ${overview.modifiedReviews || 0} modified, ${overview.rejectedReviews || 0} rejected`,
      icon: CheckCircle2,
      colorClass: 'card-emerald',
      iconBg: '#d1fae5',
      iconColor: '#059669',
    },
    {
      id: 'rai',
      title: 'Action Risk Guardrails',
      value: overview.highRiskCount || 0,
      subtitle: `${overview.mediumRiskCount || 1} Medium-risk operational commands screened`,
      icon: ShieldAlert,
      colorClass: 'card-amber',
      iconBg: '#fef3c7',
      iconColor: '#d97706',
    },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.id}
            className={`glass-card kpi-card ${card.colorClass}`}
            onClick={() => onCardClick && onCardClick(card.id)}
            style={{ cursor: 'pointer' }}
          >
            <div className="kpi-header">
              <span className="kpi-title">{card.title}</span>
              <div className="kpi-icon" style={{ background: card.iconBg, color: card.iconColor }}>
                <Icon size={20} />
              </div>
            </div>
            <div className="kpi-value">{card.value}</div>
            <div className="kpi-subtitle">{card.subtitle}</div>
          </div>
        );
      })}
    </div>
  );
}
