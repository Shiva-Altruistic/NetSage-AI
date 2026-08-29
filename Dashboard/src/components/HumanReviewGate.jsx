import React, { useState } from 'react';
import { AlertOctagon, CheckCircle2, Edit3, ShieldAlert, XCircle, FileText, Check, Sparkles } from 'lucide-react';

export default function HumanReviewGate({ cases, onReviewUpdate }) {
  const [selectedCase, setSelectedCase] = useState(null);
  const [decision, setDecision] = useState('APPROVED');
  const [notes, setNotes] = useState('');
  const [overrideTag, setOverrideTag] = useState('');
  const [overrideFix, setOverrideFix] = useState('');
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const filteredCases = (cases || []).filter((c) => {
    if (filterDecision === 'ALL') return true;
    return c.human_decision === filterDecision;
  });

  const handleOpenReview = (c) => {
    setSelectedCase(c);
    setDecision(c.human_decision === 'PENDING' ? 'APPROVED' : c.human_decision);
    setNotes(c.reviewer_notes || '');
    setOverrideTag(c.concept_tag || '');
    setOverrideFix(c.approved_fix || c.ai_fix || c.expected_fix || '');
    setSuccessMsg('');
  };

  const handleSubmitReview = async () => {
    if (!selectedCase) return;
    setSubmitting(true);
    try {
      const res = await fetch('/api/human-reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: selectedCase.case_id,
          decision,
          notes,
          approved_fix: overrideFix,
          override_tag: overrideTag,
        }),
      });

      if (res.ok) {
        setSuccessMsg(`Case ${selectedCase.case_id} authorized as ${decision}!`);
        if (onReviewUpdate) onReviewUpdate();
        setTimeout(() => {
          setSelectedCase(null);
          setSuccessMsg('');
        }, 1200);
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="glass-card tab-content-enter" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-emerald">Human-in-the-Loop Gate</span>
            <span className="badge badge-amber">Action Risk Screening</span>
          </div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: '800' }}>
            Engineer Review & Safety Authorization Gate
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Inspect, override, and sign off on AI network diagnoses and remediation commands before infrastructure deployment.
          </p>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {[
            { id: 'ALL', label: 'All Reviews' },
            { id: 'APPROVED', label: 'Approved', color: '#059669' },
            { id: 'MODIFIED', label: 'Modified', color: '#d97706' },
            { id: 'REJECTED', label: 'Rejected', color: '#e11d48' },
            { id: 'PENDING', label: 'Pending', color: '#6366f1' },
          ].map((d) => (
            <button
              key={d.id}
              onClick={() => setFilterDecision(d.id)}
              className="btn btn-outline"
              style={{
                padding: '6px 14px',
                fontSize: '0.75rem',
                fontWeight: '700',
                borderRadius: '16px',
                backgroundColor: filterDecision === d.id ? 'var(--bg-secondary)' : 'var(--bg-card)',
                borderColor: filterDecision === d.id ? (d.color || 'var(--accent-purple)') : 'var(--border-card)',
                color: filterDecision === d.id ? (d.color || 'var(--accent-purple)') : 'var(--text-secondary)',
              }}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div
        style={{
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          padding: '16px 20px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
        }}
      >
        <ShieldAlert size={26} color="#d97706" />
        <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>
          <strong style={{ color: '#d97706' }}>Operational Safety Protocol:</strong> Destructive commands (interface <code>shutdown</code>, <code>clear ip dhcp binding *</code>, or 802.1Q trunk native changes) are blocked from automated deployment and mandate senior network engineer approval.
        </div>
      </div>

      {/* Reviews Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Category</th>
              <th>AI Diagnosis & Remediation</th>
              <th>Operational Risk</th>
              <th>Decision</th>
              <th>Reviewer Notes</th>
              <th>Sign-Off Action</th>
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
                  <span className={`cat-badge cat-${c.concept_tag?.toLowerCase()}`}>{c.concept_tag}</span>
                </td>
                <td style={{ maxWidth: '320px' }}>
                  <div style={{ fontSize: '0.825rem', color: 'var(--text-primary)', marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: '500' }}>
                    {c.ai_fault || c.expected_fault}
                  </div>
                  <code style={{ fontSize: '0.75rem', color: '#059669', background: 'var(--bg-card-subtle)', padding: '3px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)', display: 'inline-block' }}>
                    {(c.ai_fix || c.expected_fix || '').slice(0, 55)}...
                  </code>
                </td>
                <td>
                  <span
                    className={`badge ${
                      c.risk_level === 'High'
                        ? 'badge-rose'
                        : c.risk_level === 'Medium'
                        ? 'badge-amber'
                        : 'badge-emerald'
                    }`}
                  >
                    {c.risk_level || 'Low'} Risk
                  </span>
                </td>
                <td>
                  <span
                    className={`badge ${
                      c.human_decision === 'APPROVED'
                        ? 'badge-emerald'
                        : c.human_decision === 'MODIFIED'
                        ? 'badge-amber'
                        : c.human_decision === 'REJECTED'
                        ? 'badge-rose'
                        : 'badge-indigo'
                    }`}
                  >
                    {c.human_decision || 'Pending'}
                  </span>
                </td>
                <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {c.reviewer_notes || '—'}
                </td>
                <td>
                  <button
                    className="btn btn-primary"
                    style={{ padding: '6px 14px', fontSize: '0.75rem', gap: '5px' }}
                    onClick={() => handleOpenReview(c)}
                  >
                    <Edit3 size={13} />
                    Sign Off
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Review Modal */}
      {selectedCase && (
        <div className="modal-overlay" onClick={() => setSelectedCase(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.35rem', fontWeight: '800' }}>
                Sign Off & Authorize Diagnosis: Case {selectedCase.case_id}
              </h3>
              <span className={`cat-badge cat-${selectedCase.concept_tag?.toLowerCase()}`}>{selectedCase.concept_tag}</span>
            </div>

            {successMsg && (
              <div style={{ background: '#dcfce7', border: '1px solid #10b981', color: '#15803d', padding: '12px', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700' }}>
                <Sparkles size={18} /> {successMsg}
              </div>
            )}

            <div style={{ marginBottom: '18px', background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Network Symptom</div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginTop: '4px' }}>{selectedCase.symptom}</div>
            </div>

            {/* Decision Buttons */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', fontWeight: '700' }}>
                Reviewer Verdict
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  type="button"
                  className={`btn ${decision === 'APPROVED' ? 'btn-success' : 'btn-outline'}`}
                  onClick={() => setDecision('APPROVED')}
                  style={{ flex: 1, padding: '12px' }}
                >
                  <CheckCircle2 size={18} /> Approve
                </button>
                <button
                  type="button"
                  className={`btn ${decision === 'MODIFIED' ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => setDecision('MODIFIED')}
                  style={{ flex: 1, padding: '12px' }}
                >
                  <Edit3 size={18} /> Modify Fix / Tags
                </button>
                <button
                  type="button"
                  className={`btn ${decision === 'REJECTED' ? 'btn-danger' : 'btn-outline'}`}
                  onClick={() => setDecision('REJECTED')}
                  style={{ flex: 1, padding: '12px' }}
                >
                  <XCircle size={18} /> Reject Diagnosis
                </button>
              </div>
            </div>

            {/* Overrides if Modified */}
            {decision === 'MODIFIED' && (
              <div style={{ marginBottom: '20px', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px', background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: '700' }}>
                    Override Concept Tag
                  </label>
                  <input
                    type="text"
                    className="input-search"
                    value={overrideTag}
                    onChange={(e) => setOverrideTag(e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: '700' }}>
                    Authorized Remediation Fix Command(s)
                  </label>
                  <textarea
                    className="input-search"
                    rows="3"
                    value={overrideFix}
                    onChange={(e) => setOverrideFix(e.target.value)}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.825rem' }}
                  />
                </div>
              </div>
            )}

            {/* Reviewer Feedback Notes */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: '700' }}>
                Engineer Reviewer Comments & Rationale
              </label>
              <textarea
                className="input-search"
                rows="2"
                placeholder="Add audit sign-off rationale or deployment notes..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button className="btn btn-outline" onClick={() => setSelectedCase(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSubmitReview} disabled={submitting}>
                {submitting ? 'Saving...' : 'Authorize & Persist Decision'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
