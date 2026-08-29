# NetSage AI — Evaluation Report

**Cases evaluated:** 30 (Full Benchmark Suite)
**Average overall score:** 94.0%
**Mean inference latency:** 1.82s

## Accuracy Breakdown

| Metric | Score | Measurement Method |
|---|---|---|
| OSI Layer (exact match) | 93.3% | Exact numeric layer match |
| Concept Tag (exact match) | 93.3% | Ground truth CCNA category match |
| Severity (exact match) | 83.3% | Ground truth severity match |
| Fault Description (semantic similarity) | 96.7% | Technical root-cause semantic equivalence |
| Fix Quality (semantic similarity) | 98.2% | Working Cisco remediation equivalence |
| Confidence Appropriateness | 90.0% | Hedging on ambiguous cases |
| Evidence Grounding Rate | 90.0% | Cited interfaces verified in transcript |
| Mean Inference Latency | 1.82s | Wall-clock API response time |

## Per-Category Scores

| Category | Cases | Avg Score |
|---|---|---|
| acl | 3 | 94.7% |
| dhcp | 4 | 100.0% |
| dns | 3 | 96.7% |
| gateway | 4 | 93.8% |
| nat | 3 | 86.5% |
| routing | 4 | 100.0% |
| vlan | 4 | 90.5% |
| wireless | 5 | 89.7% |

## Best Performing Cases

| Case | Score | OSI | Tag | Severity |
|---|---|---|---|---|
| C001 | 100.0% | ✅ | ✅ | ✅ |
| C003 | 100.0% | ✅ | ✅ | ✅ |
| C004 | 100.0% | ✅ | ✅ | ✅ |
| C006 | 100.0% | ✅ | ✅ | ✅ |
| C007 | 100.0% | ✅ | ✅ | ✅ |

## Cases Needing Improvement

| Case | Score | OSI | Tag | Severity |
|---|---|---|---|---|
| C019 | 83.0% | ✅ | ✅ | ✅ |
| C011 | 82.0% | ✅ | ✅ | ❌ |
| C005 | 80.0% | ✅ | ✅ | ❌ |
| C030 | 78.5% | ❌ | ✅ | ✅ |
| C023 | 76.5% | ✅ | ✅ | ❌ |

## Responsible AI — Uncertain Cases

Cases with intentionally insufficient evidence: ['C005', 'C023', 'C030']

- **C005**: ⚠️ Over-confident (score: 80.0%)
- **C023**: ⚠️ Over-confident (score: 76.5%)
- **C030**: ✅ Appropriately hedged (score: 78.5%)
