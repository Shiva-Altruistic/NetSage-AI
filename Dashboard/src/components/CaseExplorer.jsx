import React, { useState } from 'react';
import { Search, Terminal, AlertTriangle, CheckCircle, HelpCircle, Copy, X, ExternalLink, ArrowUpDown } from 'lucide-react';

export default function CaseExplorer({ cases }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState(null);
  const [copied, setCopied] = useState(false);
  const [sortBy, setSortBy] = useState('id'); // 'id', 'layer', 'severity'

  const categories = [
    { id: 'ALL', label: 'All Categories', color: '#6366f1', bg: '#e0e7ff' },
    { id: 'vlan', label: 'VLAN (L2)', color: '#8b5cf6', bg: '#ede9fe' },
    { id: 'gateway', label: 'Gateway (L3)', color: '#10b981', bg: '#d1fae5' },
    { id: 'dhcp', label: 'DHCP', color: '#0284c7', bg: '#e0f2fe' },
    { id: 'dns', label: 'DNS', color: '#f59e0b', bg: '#fef3c7' },
    { id: 'routing', label: 'Routing', color: '#6366f1', bg: '#e0e7ff' },
    { id: 'acl', label: 'ACL (Security)', color: '#f43f5e', bg: '#ffe4e6' },
    { id: 'nat', label: 'NAT / PAT', color: '#0d9488', bg: '#ccfbf1' },
    { id: 'wireless', label: 'Wireless', color: '#ec4899', bg: '#fce7f3' },
  ];

  let filteredCases = (cases || []).filter((c) => {
    const matchesSearch =
      c.case_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.symptom?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.topology_note?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.concept_tag?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === 'ALL' ||
      c.concept_tag?.toLowerCase() === selectedCategory.toLowerCase();

    return matchesSearch && matchesCategory;
  });

  // Sorting
  filteredCases.sort((a, b) => {
    if (sortBy === 'layer') {
      return (parseInt(a.osi_layer) || 0) - (parseInt(b.osi_layer) || 0);
    }
    if (sortBy === 'severity') {
      return (a.severity === 'high' ? -1 : 1);
    }
    return a.case_id?.localeCompare(b.case_id);
  });

  const handleCopyFix = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getCategoryClass = (tag) => {
    return `cat-badge cat-${tag?.toLowerCase()}`;
  };

  return (
    <div className="glass-card tab-content-enter" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.4rem', fontWeight: '800' }}>
            Cisco IOS Diagnostic Case Explorer
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Interactive inspection of all 30 benchmark cases, evidence transcripts, and AI remediation plans.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', width: '100%', maxWidth: '420px' }}>
          <div style={{ position: 'relative', width: '100%' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-search"
              placeholder="Search symptom, IP, VLAN, or case ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '38px' }}
            />
          </div>

          <button
            className="btn btn-outline"
            style={{ padding: '9px 12px', fontSize: '0.8rem', whiteSpace: 'nowrap', gap: '6px' }}
            onClick={() => setSortBy((prev) => (prev === 'id' ? 'layer' : prev === 'layer' ? 'severity' : 'id'))}
            title="Toggle sort order"
          >
            <ArrowUpDown size={14} />
            Sort: {sortBy.toUpperCase()}
          </button>
        </div>
      </div>

      {/* Colorful Category Filter Pills */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', overflowX: 'auto', paddingBottom: '6px' }}>
        {categories.map((cat) => {
          const isSelected = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className="btn btn-outline"
              style={{
                padding: '6px 14px',
                fontSize: '0.775rem',
                fontWeight: '700',
                borderRadius: '20px',
                backgroundColor: isSelected ? cat.bg : 'var(--bg-card)',
                borderColor: isSelected ? cat.color : 'var(--border-card)',
                color: isSelected ? cat.color : 'var(--text-secondary)',
                boxShadow: isSelected ? `0 2px 10px ${cat.color}33` : 'none',
                transition: 'all 0.2s ease',
              }}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Category</th>
              <th>OSI Layer</th>
              <th>Severity</th>
              <th>Symptom Preview</th>
              <th>Topology</th>
              <th>Human Review</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredCases.map((c) => (
              <tr key={c.case_id}>
                <td>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: 'var(--accent-purple)' }}>
                    {c.case_id}
                  </span>
                </td>
                <td>
                  <span className={getCategoryClass(c.concept_tag)}>{c.concept_tag}</span>
                </td>
                <td>
                  <span className="badge badge-cyan">Layer {c.osi_layer}</span>
                </td>
                <td>
                  <span className={`badge ${c.severity === 'high' ? 'badge-rose' : 'badge-amber'}`}>
                    {c.severity}
                  </span>
                </td>
                <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {c.symptom}
                </td>
                <td style={{ maxWidth: '180px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text-muted)' }}>
                  {c.topology_note}
                </td>
                <td>
                  <span className={`badge ${c.human_decision === 'APPROVED' ? 'badge-emerald' : c.human_decision === 'MODIFIED' ? 'badge-amber' : 'badge-indigo'}`}>
                    {c.human_decision || 'Pending'}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-outline"
                    style={{ padding: '5px 12px', fontSize: '0.75rem', gap: '4px', fontWeight: '700' }}
                    onClick={() => setSelectedCase(c)}
                  >
                    <ExternalLink size={12} />
                    Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Case Details Modal */}
      {selectedCase && (
        <div className="modal-overlay" onClick={() => setSelectedCase(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', fontWeight: '800', color: 'var(--accent-purple)' }}>
                  {selectedCase.case_id}
                </span>
                <span className={getCategoryClass(selectedCase.concept_tag)}>{selectedCase.concept_tag}</span>
                <span className="badge badge-cyan">OSI Layer {selectedCase.osi_layer}</span>
                <span className={`badge ${selectedCase.severity === 'high' ? 'badge-rose' : 'badge-amber'}`}>
                  {selectedCase.severity} severity
                </span>
              </div>
              <button
                className="btn btn-outline"
                style={{ padding: '6px', borderRadius: '50%' }}
                onClick={() => setSelectedCase(null)}
              >
                <X size={18} />
              </button>
            </div>

            {/* Symptom & Topology Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '6px', fontWeight: '700' }}>
                  Observed Network Symptom
                </h4>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>{selectedCase.symptom}</p>
              </div>

              <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '6px', fontWeight: '700' }}>
                  Topology Context
                </h4>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{selectedCase.topology_note}</p>
              </div>
            </div>

            {/* Raw Show-Command Terminal */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Terminal size={15} color="var(--accent-purple)" />
                  Raw Cisco IOS Show-Command Evidence
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Packet Tracer IOS Transcript</span>
              </div>
              <div className="cisco-terminal">{selectedCase.show_output}</div>
            </div>

            {/* Root Cause & Remediation */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '6px', fontWeight: '700' }}>
                  Root Cause Diagnosis
                </h4>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: '10px' }}>
                  {selectedCase.ai_fault || selectedCase.expected_fault}
                </p>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Next Command: <code style={{ color: 'var(--accent-purple)', fontWeight: '700' }}>{selectedCase.expected_next_command}</code>
                </div>
              </div>

              <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <h4 style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: '700' }}>
                    Remediation Fix Commands
                  </h4>
                  <button
                    className="btn btn-outline"
                    style={{ padding: '3px 10px', fontSize: '0.7rem', gap: '4px' }}
                    onClick={() => handleCopyFix(selectedCase.ai_fix || selectedCase.expected_fix)}
                  >
                    <Copy size={12} />
                    {copied ? 'Copied!' : 'Copy Fix'}
                  </button>
                </div>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.825rem', color: '#059669', background: 'var(--terminal-bg)', padding: '12px', borderRadius: '6px', whiteSpace: 'pre-wrap', border: '1px solid var(--border-subtle)' }}>
                  {selectedCase.ai_fix || selectedCase.expected_fix}
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => setSelectedCase(null)}>
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
