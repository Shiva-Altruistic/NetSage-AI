# NetSage AI — Human Review & Safety Audit Report

**Cases Reviewed:** 8
**Review Mode:** Benchmark Audit
**Overall Approval Rate:** 37.5%

## Decision Summary

| Decision | Count | Percentage |
|---|---|---|
| ✅ APPROVED (Ready for deployment) | 3 | 37.5% |
| ⚠️ MODIFIED (Parameters adjusted) | 4 | 50.0% |
| ❌ REJECTED (Unsafe or inaccurate) | 1 | 12.5% |

## Human-AI Diagnostic Agreement

| Category | Agreement Rate |
|---|---|
| Concept Tag Agreement | 87.5% |
| OSI Layer Agreement | 87.5% |
| Severity Level Agreement | 50.0% |

## Operational Safety & Risk Guardrail Audit

- **High-Risk Operational Commands Flagged:** 0
- **Medium-Risk Operational Commands Flagged:** 1

## Per-Case Review Audit Trail

| Case | Decision | Risk | AI Tag | Human Tag | OSI | Agreement | Notes |
|---|---|---|---|---|---|---|---|
| C001 | APPROVED | Low | vlan | vlan | L2 | ✅ | Fully aligns with ground truth diagnosis |
| C005 | MODIFIED | Medium | vlan | vlan | L2 | ✅ | Severity adjusted from 'unspecified' to  |
| C011 | MODIFIED | Low | vlan | vlan | L2 | ✅ | Severity adjusted from 'unspecified' to  |
| C018 | APPROVED | Low | gateway | gateway | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C023 | MODIFIED | Low | nat | nat | L3 | ✅ | Severity adjusted from 'unspecified' to  |
| C025 | REJECTED | Low |  | wireless | L3 | ❌ | Disagreement on root cause: AI predicted |
| C029 | MODIFIED | Low | wireless | wireless | L2 | ✅ | Severity adjusted from 'unspecified' to  |
| C030 | APPROVED | Low | wireless | wireless | L7 | ✅ | Fully aligns with ground truth diagnosis |
