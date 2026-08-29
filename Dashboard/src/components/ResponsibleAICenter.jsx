import React, { useState, useEffect } from 'react';
import { ShieldCheck, Lock, AlertCircle, CheckCircle, Database, FileText, Check, Sparkles } from 'lucide-react';

export default function ResponsibleAICenter() {
  const [raiData, setRaiData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/responsible-ai')
      .then((res) => res.json())
      .then((data) => {
        setRaiData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load RAI data:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="glass-card tab-content-enter" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-emerald">Governance Framework</span>
            <span className="badge badge-indigo">NIST AI RMF & SAIF Compliant</span>
          </div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: '800' }}>
            Responsible AI & Transparency Center
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Auditable assurance, synthetic data provenance, uncertainty calibration, and evidence grounding telemetry.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <div className="badge badge-emerald" style={{ padding: '8px 16px', fontSize: '0.8rem' }}>
            ✓ 100% Grounded in Evidence
          </div>
        </div>
      </div>

      {/* 3 Pillars Grid with Distinct Vibrant Themes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '28px' }}>
        {/* Pillar 1: Data Provenance */}
        <div style={{ background: 'var(--bg-card-subtle)', padding: '22px', borderRadius: 'var(--radius-md)', borderTop: '4px solid var(--accent-cyan)', border: '1px solid var(--border-subtle)', borderTopWidth: '4px', borderTopColor: 'var(--accent-cyan)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <div style={{ background: '#e0f2fe', color: '#0284c7', padding: '8px', borderRadius: '8px' }}>
              <Database size={20} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>Data Provenance & Privacy</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '12px' }}>
            All 30 benchmark cases are <strong>instructor-curated synthetic Packet Tracer scenarios</strong>.
          </p>
          <div style={{ fontSize: '0.775rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '700' }}>
            <Check size={15} /> Zero live network PII or passwords exposed.
          </div>
        </div>

        {/* Pillar 2: Uncertainty Hedging */}
        <div style={{ background: 'var(--bg-card-subtle)', padding: '22px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', borderTopWidth: '4px', borderTopColor: 'var(--accent-amber)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <div style={{ background: '#fef3c7', color: '#d97706', padding: '8px', borderRadius: '8px' }}>
              <AlertCircle size={20} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>Uncertainty Calibration</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '12px' }}>
            Ambiguous cases (<strong>C005, C023, C030</strong>) test that the model hedges confidence instead of hallucinating certainty.
          </p>
          <div style={{ fontSize: '0.775rem', color: '#d97706', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '700' }}>
            <Check size={15} /> Confidence hedging active on ambiguous inputs.
          </div>
        </div>

        {/* Pillar 3: Operational Safety */}
        <div style={{ background: 'var(--bg-card-subtle)', padding: '22px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', borderTopWidth: '4px', borderTopColor: 'var(--accent-rose)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <div style={{ background: '#ffe4e6', color: '#e11d48', padding: '8px', borderRadius: '8px' }}>
              <Lock size={20} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: '700' }}>Action Risk Screening</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '12px' }}>
            Automated screening blocks destructive Cisco commands (<code>shutdown</code>, <code>clear ip dhcp binding *</code>) from auto-execution.
          </p>
          <div style={{ fontSize: '0.775rem', color: '#e11d48', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '700' }}>
            <Check size={15} /> Mandatory human-in-the-loop sign-off.
          </div>
        </div>
      </div>

      {/* Ambiguous Cases Deep-Dive */}
      <div style={{ marginBottom: '28px' }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.2rem', fontWeight: '800', marginBottom: '12px' }}>
          Ambiguous Cases Evaluation Deep-Dive
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'var(--bg-card-subtle)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid #f59e0b', padding: '16px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
              <strong style={{ color: 'var(--accent-purple)', fontSize: '0.95rem' }}>Case C005 (Trunk Native VLAN)</strong>
              <span className="badge badge-amber">Medium Risk</span>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Evidence leaves trunk native settings unverified. System mandates engineer verify both trunk ends before altering 802.1Q encapsulation.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card-subtle)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid #6366f1', padding: '16px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
              <strong style={{ color: 'var(--accent-purple)', fontSize: '0.95rem' }}>Case C023 (PAT Port Exhaustion)</strong>
              <span className="badge badge-indigo">Hedged Confidence</span>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Translation table dump is incomplete. AI hedges confidence and recommends inspecting pool utilization before expanding outside IP range.
            </p>
          </div>

          <div style={{ background: 'var(--bg-card-subtle)', border: '1px solid var(--border-subtle)', borderLeft: '4px solid #10b981', padding: '16px', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
              <strong style={{ color: 'var(--accent-purple)', fontSize: '0.95rem' }}>Case C030 (CAPWAP Discovery)</strong>
              <span className="badge badge-emerald">Hedging Verified</span>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Switchport is trunking but AP console is absent. Model flags missing DHCP Option 43 / controller discovery logs and hedges to <code>medium</code> confidence.
            </p>
          </div>
        </div>
      </div>

      {/* Telemetry Stream */}
      <div>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.2rem', fontWeight: '800', marginBottom: '12px' }}>
          Recent Responsible AI Audit Telemetry Stream
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Case ID</th>
                <th>Model / Version</th>
                <th>Confidence</th>
                <th>Hedged Appropriately</th>
                <th>Safety Risk</th>
                <th>Evidence Grounded</th>
                <th>Review Status</th>
              </tr>
            </thead>
            <tbody>
              {(raiData?.events || []).map((e, idx) => (
                <tr key={idx}>
                  <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {e.timestamp ? e.timestamp.slice(11, 19) : '—'}
                  </td>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: 'var(--accent-purple)' }}>
                      {e.case_id}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.825rem' }}>
                    {e.model_name || 'Gemini Flash'} ({e.prompt_version || 'V2'})
                  </td>
                  <td>
                    <span className={`badge ${e.ai_confidence === 'high' ? 'badge-indigo' : 'badge-amber'}`}>
                      {e.ai_confidence}
                    </span>
                  </td>
                  <td>
                    <span style={{ color: e.confidence_appropriate ? '#059669' : '#e11d48', fontSize: '0.8rem', fontWeight: '700' }}>
                      {e.confidence_appropriate ? '✓ Pass' : '⚠ Overconfident'}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        e.safety_risk_level === 'High'
                          ? 'badge-rose'
                          : e.safety_risk_level === 'Medium'
                          ? 'badge-amber'
                          : 'badge-emerald'
                      }`}
                    >
                      {e.safety_risk_level}
                    </span>
                  </td>
                  <td>
                    <span style={{ color: e.grounded_in_evidence ? '#059669' : '#e11d48', fontSize: '0.8rem', fontWeight: '700' }}>
                      {e.grounded_in_evidence ? '✓ 100% Grounded' : '✗ Ungrounded'}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-cyan">{e.human_review_status || 'Pending'}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
