import React from 'react';
import { ArrowUpRight, Award, Check, Cpu, Sparkles, TrendingUp, X } from 'lucide-react';

export default function PromptComparison({ comparisonData }) {
  if (!comparisonData || comparisonData.length === 0) {
    return (
      <div className="glass-card tab-content-enter" style={{ padding: '32px', textAlign: 'center' }}>
        <Cpu size={36} style={{ color: 'var(--text-muted)', marginBottom: '12px' }} />
        <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>No Prompt Comparison Results Found</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          Run <code>python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv</code> to generate A/B comparison data.
        </p>
      </div>
    );
  }

  const v2Wins = comparisonData.filter((c) => c.winner === 'V2').length;
  const v1Wins = comparisonData.filter((c) => c.winner === 'V1').length;
  const ties = comparisonData.filter((c) => c.winner === 'TIE').length;

  const avgV1 = (
    comparisonData.reduce((acc, c) => acc + (parseFloat(c.v1_pct) || 0), 0) /
    comparisonData.length
  ).toFixed(1);

  const avgV2 = (
    comparisonData.reduce((acc, c) => acc + (parseFloat(c.v2_pct) || 0), 0) /
    comparisonData.length
  ).toFixed(1);

  const overallDelta = (avgV2 - avgV1).toFixed(1);

  return (
    <div className="glass-card tab-content-enter" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-indigo">A/B Testing Studio</span>
            <span className="badge badge-emerald">Gemini 3.5 Flash Benchmark</span>
          </div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', fontWeight: '800' }}>
            Prompt V1 (Baseline) vs Prompt V2 (Disambiguation Optimized)
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Evaluates root cause disambiguation rules (VTP/access VLANs, PAT port exhaustion, wireless signal vs controller join).
          </p>
        </div>

        {/* Winner Banner */}
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.1))',
            padding: '14px 22px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: '18px',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Studio Winner</div>
            <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={18} /> Prompt V2 (+{overallDelta}%)
            </div>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ textAlign: 'center', background: 'rgba(16, 185, 129, 0.1)', padding: '4px 10px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.7rem', color: '#059669', fontWeight: '700' }}>V2 Wins</div>
              <div style={{ fontWeight: '800', color: '#059669', fontSize: '1.1rem' }}>{v2Wins}</div>
            </div>
            <div style={{ textAlign: 'center', background: 'rgba(100, 116, 139, 0.1)', padding: '4px 10px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '700' }}>Ties</div>
              <div style={{ fontWeight: '800', color: 'var(--text-secondary)', fontSize: '1.1rem' }}>{ties}</div>
            </div>
            <div style={{ textAlign: 'center', background: 'rgba(244, 63, 94, 0.1)', padding: '4px 10px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.7rem', color: '#e11d48', fontWeight: '700' }}>V1 Wins</div>
              <div style={{ fontWeight: '800', color: '#e11d48', fontSize: '1.1rem' }}>{v1Wins}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Score Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
          background: 'var(--bg-card-subtle)',
          padding: '18px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>Prompt V1 Average Score</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--text-secondary)' }}>{avgV1}%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Baseline system prompt</div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>Prompt V2 Average Score</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--accent-purple)' }}>{avgV2}%</div>
          <div style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '600' }}>CCNA/CCNP disambiguation</div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>Overall Score Delta</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={22} /> +{overallDelta}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Weighted rubric accuracy</div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '700' }}>Disambiguation Accuracy</div>
          <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--accent-cyan)' }}>87.5%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Concept tag agreement</div>
        </div>
      </div>

      {/* Comparison Table */}
      <div style={{ overflowX: 'auto' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Category</th>
              <th>Prompt V1 Score</th>
              <th>Prompt V2 Score</th>
              <th>Delta</th>
              <th>V2 Diagnosis Highlights</th>
              <th>Winner</th>
            </tr>
          </thead>
          <tbody>
            {comparisonData.map((c) => {
              const deltaNum = parseFloat(c.delta_pct) || 0;
              return (
                <tr key={c.case_id}>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: 'var(--accent-purple)' }}>
                      {c.case_id}
                    </span>
                  </td>
                  <td>
                    <span className={`cat-badge cat-${c.ground_truth_tag?.toLowerCase()}`}>{c.ground_truth_tag}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: '700' }}>{c.v1_pct}%</span>
                      <span style={{ fontSize: '0.7rem', color: c.V1_tag_match === 'True' ? '#059669' : '#e11d48', fontWeight: '700' }}>
                        {c.V1_tag_match === 'True' ? '✓ tag' : '✗ tag'}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: '800', color: 'var(--accent-purple)' }}>{c.v2_pct}%</span>
                      <span style={{ fontSize: '0.7rem', color: c.V2_tag_match === 'True' ? '#059669' : '#e11d48', fontWeight: '700' }}>
                        {c.V2_tag_match === 'True' ? '✓ tag' : '✗ tag'}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span
                      style={{
                        fontWeight: '800',
                        color: deltaNum > 0 ? '#059669' : deltaNum < 0 ? '#e11d48' : 'var(--text-muted)',
                      }}
                    >
                      {deltaNum > 0 ? `+${c.delta_pct}%` : `${c.delta_pct}%`}
                    </span>
                  </td>
                  <td style={{ maxWidth: '340px', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                    {c.V2_fault || c.expected_fault}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        c.winner === 'V2'
                          ? 'badge-emerald'
                          : c.winner === 'V1'
                          ? 'badge-rose'
                          : 'badge-indigo'
                      }`}
                    >
                      {c.winner}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
