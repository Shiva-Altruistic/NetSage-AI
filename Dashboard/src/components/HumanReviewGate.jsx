import React, { useState } from 'react';
import {
  AlertOctagon,
  CheckCircle2,
  Edit3,
  ShieldAlert,
  XCircle,
  FileText,
  Check,
  Sparkles,
  Zap,
  Search,
} from 'lucide-react';

export default function HumanReviewGate({ cases, onReviewUpdate }) {
  const [selectedCase, setSelectedCase] = useState(null);
  const [decision, setDecision] = useState('APPROVED');
  const [notes, setNotes] = useState('');
  const [overrideTag, setOverrideTag] = useState('');
  const [overrideFix, setOverrideFix] = useState('');
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [tableSearch, setTableSearch] = useState('');
  const [inlineApprovingId, setInlineApprovingId] = useState(null);
  const [localApprovals, setLocalApprovals] = useState({});

  // 1-Click Instant Inline Approval right on the row without scrolling!
  const handleQuickInlineApprove = async (c, e) => {
    e.stopPropagation();
    const caseId = c.case_id;
    setInlineApprovingId(caseId);

    // Save current scroll position
    const scrollPos = window.scrollY;

    try {
      const res = await fetch('/api/human-reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          decision: 'APPROVED',
          notes: 'Instant zero-scroll authorized by lead engineer.',
          approved_fix: c.approved_fix || c.ai_fix || c.expected_fix || '',
          override_tag: c.concept_tag || '',
        }),
      });

      if (res.ok) {
        setLocalApprovals((prev) => ({ ...prev, [caseId]: 'APPROVED' }));
        setSuccessMsg(`✓ Case ${caseId} authorized right here without scrolling!`);
        if (onReviewUpdate) onReviewUpdate();

        // Restore scroll position
        window.scrollTo({ top: scrollPos, behavior: 'instant' });

        setTimeout(() => setSuccessMsg(''), 2500);
      }
    } catch (err) {
      console.error('Quick approve failed:', err);
    } finally {
      setInlineApprovingId(null);
    }
  };

  const filteredCases = (cases || []).filter((c) => {
    const currentDec = localApprovals[c.case_id] || c.human_decision;
    if (filterDecision !== 'ALL' && currentDec !== filterDecision) return false;
    if (tableSearch) {
      const term = tableSearch.toLowerCase();
      return (
        c.case_id?.toLowerCase().includes(term) ||
        c.symptom?.toLowerCase().includes(term) ||
        c.concept_tag?.toLowerCase().includes(term)
      );
    }
    return true;
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
    const scrollPos = window.scrollY;

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
        setLocalApprovals((prev) => ({ ...prev, [selectedCase.case_id]: decision }));
        setSuccessMsg(`Case ${selectedCase.case_id} authorized as ${decision}!`);
        if (onReviewUpdate) onReviewUpdate();

        setTimeout(() => {
          setSelectedCase(null);
          setSuccessMsg('');
          window.scrollTo({ top: scrollPos, behavior: 'instant' });
        }, 1000);
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modern-white-card tab-content-enter" style={{ padding: '28px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-emerald">Zero-Scroll Authorization Gate</span>
            <span className="badge badge-amber">Action Risk Screening</span>
          </div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: '800' }}>
            Engineer Review & Safety Authorization Gate
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Approve diagnoses instantly in place with the 1-click <strong>Approve</strong> button, or customize remediation commands.
          </p>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
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

      {/* Instant In-Place Toast */}
      {successMsg && (
        <div className="inline-toast-banner" style={{ marginBottom: '16px' }}>
          <Sparkles size={16} color="#10b981" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Safety Notice Banner */}
      <div
        style={{
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
        }}
      >
        <ShieldAlert size={24} color="#d97706" />
        <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>
          <strong style={{ color: '#d97706' }}>Operational Safety Protocol:</strong> Destructive commands (interface <code>shutdown</code>, <code>clear ip dhcp binding *</code>, or 802.1Q trunk native changes) are screened and mandate senior engineer sign-off.
        </div>
      </div>

      {/* Table Filter Search Bar */}
      <div style={{ marginBottom: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <div className="header-search-box" style={{ maxWidth: '340px' }}>
          <Search size={15} className="search-icon" />
          <input
            type="text"
            placeholder="Quick find case..."
            value={tableSearch}
            onChange={(e) => setTableSearch(e.target.value)}
            className="header-search-input"
          />
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Showing <strong>{filteredCases.length}</strong> of 30 cases
        </span>
      </div>

      {/* 30-Case Review Table with 1-Click Instant In-Place Approvals */}
      <div className="table-wrapper">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Category</th>
              <th>Symptom & Remediation Fix</th>
              <th>Command Risk</th>
              <th>Audit Status</th>
              <th>Reviewer Notes</th>
              <th style={{ textAlign: 'right' }}>Quick Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredCases.map((c) => {
              const currentDec = localApprovals[c.case_id] || c.human_decision;
              const isApproved = currentDec === 'APPROVED';
              const isProcessing = inlineApprovingId === c.case_id;

              return (
                <tr key={c.case_id} id={`case-row-${c.case_id}`}>
                  <td>
                    <div style={{ fontWeight: '800', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      {c.case_id}
                    </div>
                  </td>
                  <td>
                    <span className={`cat-badge cat-${c.concept_tag?.toLowerCase()}`}>
                      {c.concept_tag}
                    </span>
                  </td>
                  <td style={{ maxWidth: '320px' }}>
                    <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.85rem', marginBottom: '4px' }}>
                      {c.symptom}
                    </div>
                    <div
                      style={{
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--terminal-text)',
                        background: 'var(--terminal-bg)',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={c.approved_fix || c.ai_fix || c.expected_fix}
                    >
                      {c.approved_fix || c.ai_fix || c.expected_fix || 'No fix required'}
                    </div>
                  </td>
                  <td>
                    {c.risk_level === 'High' ? (
                      <span className="badge badge-rose" style={{ gap: '4px' }}>
                        <AlertOctagon size={12} /> High
                      </span>
                    ) : c.risk_level === 'Medium' ? (
                      <span className="badge badge-amber" style={{ gap: '4px' }}>
                        <ShieldAlert size={12} /> Medium
                      </span>
                    ) : (
                      <span className="badge badge-emerald" style={{ gap: '4px' }}>
                        <Check size={12} /> Safe
                      </span>
                    )}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        currentDec === 'APPROVED'
                          ? 'badge-emerald'
                          : currentDec === 'MODIFIED'
                          ? 'badge-amber'
                          : currentDec === 'REJECTED'
                          ? 'badge-rose'
                          : 'badge-indigo'
                      }`}
                    >
                      {currentDec || 'Pending'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: '180px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {c.reviewer_notes || '—'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '8px', alignItems: 'center' }}>
                      {/* 1-Click Zero-Scroll Approve Button */}
                      {!isApproved ? (
                        <button
                          className="btn-quick-approve-inline"
                          onClick={(e) => handleQuickInlineApprove(c, e)}
                          disabled={isProcessing}
                          title="Authorize immediately without scrolling away"
                        >
                          <CheckCircle2 size={13} />
                          {isProcessing ? '...' : 'Approve'}
                        </button>
                      ) : (
                        <span className="badge-approved-inline" title="Already Authorized">
                          <Check size={12} /> Approved
                        </span>
                      )}

                      {/* Customize / Override Modal Button */}
                      <button
                        className="btn btn-outline"
                        style={{ padding: '5px 10px', fontSize: '0.75rem', gap: '4px' }}
                        onClick={() => handleOpenReview(c)}
                        title="Open detailed sign-off and override dialog"
                      >
                        <Edit3 size={12} />
                        Edit
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Review Modal (Centered in active viewport with zero scroll jump) */}
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
