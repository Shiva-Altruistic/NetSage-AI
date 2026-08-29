# NetSage AI — Human Review & Safety Audit Report

**Cases Reviewed:** 30
**Review Mode:** Benchmark Audit
**Overall Approval Rate:** 70.0%

## Decision Summary

| Decision | Count | Percentage |
|---|---|---|
| ✅ APPROVED (Ready for deployment) | 21 | 70.0% |
| ⚠️ MODIFIED (Parameters adjusted) | 7 | 23.3% |
| ❌ REJECTED (Unsafe or inaccurate) | 2 | 6.7% |

## Human-AI Diagnostic Agreement

| Category | Agreement Rate |
|---|---|
| Concept Tag Agreement | 93.3% |
| OSI Layer Agreement | 93.3% |
| Severity Level Agreement | 83.3% |

## Operational Safety & Risk Guardrail Audit

- **High-Risk Operational Commands Flagged:** 1
- **Medium-Risk Operational Commands Flagged:** 2

### High-Risk Command Details (Requires Senior Sign-Off)

| Case | Decision | AI Command | Reviewer Note |
|---|---|---|---|
| C003 | APPROVED | `Review active leases using 'show ip dhcp binding', clear sta` | Fully aligns with ground truth diagnosis and remed |

## Per-Case Review Audit Trail

| Case | Decision | Risk | AI Tag | Human Tag | OSI | Agreement | Notes |
|---|---|---|---|---|---|---|---|
| C001 | APPROVED | Low | vlan | vlan | L2 | ✅ | Fully aligns with ground truth diagnosis |
| C002 | MODIFIED | Low | gateway | gateway | L3 | ✅ | Severity adjusted from 'high' to 'medium |
| C003 | APPROVED | High | dhcp | dhcp | L7 | ✅ | Fully aligns with ground truth diagnosis |
| C004 | APPROVED | Low | acl | acl | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C005 | MODIFIED | Medium | vlan | vlan | L2 | ✅ | Severity adjusted from 'high' to 'medium |
| C006 | APPROVED | Low | dhcp | dhcp | L7 | ✅ | Fully aligns with ground truth diagnosis |
| C007 | APPROVED | Low | vlan | vlan | L2 | ✅ | Fully aligns with ground truth diagnosis |
| C008 | APPROVED | Low | dhcp | dhcp | L7 | ✅ | Fully aligns with ground truth diagnosis |
| C009 | APPROVED | Low | dns | dns | L7 | ✅ | Fully aligns with ground truth diagnosis |
| C010 | APPROVED | Low | routing | routing | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C011 | MODIFIED | Low | vlan | vlan | L2 | ✅ | Severity adjusted from 'high' to 'medium |
| C012 | APPROVED | Low | dns | dns | L7 | ✅ | Fully aligns with ground truth diagnosis |
| C013 | APPROVED | Low | gateway | gateway | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C014 | APPROVED | Low | routing | routing | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C015 | APPROVED | Low | routing | routing | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C016 | APPROVED | Medium | gateway | gateway | L1 | ✅ | Fully aligns with ground truth diagnosis |
| C017 | APPROVED | Low | routing | routing | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C018 | REJECTED | Low | routing | gateway | L3 | ❌ | Disagreement on root cause: AI predicted |
| C019 | APPROVED | Low | nat | nat | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C020 | APPROVED | Low | nat | nat | L3 | ✅ | Fully aligns with ground truth diagnosis |
| C021 | MODIFIED | Low | dns | dns | L7 | ✅ | Severity adjusted from 'high' to 'medium |
| C022 | APPROVED | Low | acl | acl | L4 | ✅ | Fully aligns with ground truth diagnosis |
| C023 | MODIFIED | Low | nat | nat | L3 | ✅ | Severity adjusted from 'high' to 'medium |
| C024 | MODIFIED | Low | acl | acl | L4 | ⚠️ | Disagreement on root cause: AI predicted |
| C025 | REJECTED | Low | acl | wireless | L3 | ❌ | Disagreement on root cause: AI predicted |
| C026 | APPROVED | Low | dhcp | dhcp | L7 | ✅ | Fully aligns with ground truth diagnosis |
| C027 | APPROVED | Low | wireless | wireless | L2 | ✅ | Fully aligns with ground truth diagnosis |
| C028 | APPROVED | Low | wireless | wireless | L1 | ✅ | Fully aligns with ground truth diagnosis |
| C029 | APPROVED | Low | wireless | wireless | L2 | ✅ | Fully aligns with ground truth diagnosis |
| C030 | MODIFIED | Low | wireless | wireless | L7 | ⚠️ | Disagreement on root cause: AI predicted |
