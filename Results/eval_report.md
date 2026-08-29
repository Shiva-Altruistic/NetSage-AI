# NetSage AI — Evaluation Report

**Cases evaluated:** 30 (Full Benchmark Suite)
**Average overall score:** 64.9%
**Mean inference latency:** 1.82s

## Accuracy Breakdown

| Metric | Score | Measurement Method |
|---|---|---|
| OSI Layer (exact match) | 93.3% | Exact numeric layer match |
| Concept Tag (exact match) | 93.3% | Ground truth CCNA category match |
| Severity (exact match) | 83.3% | Ground truth severity match |
| Fault Description (text similarity) | 41.1% | TF-IDF Cosine & keyword overlap |
| Fix Quality (text similarity) | 36.3% | Remediation syntax overlap |
| Confidence Appropriateness | 90.0% | Hedging on ambiguous cases |
| Evidence Grounding Rate | 90.0% | Cited interfaces verified in transcript |
| Mean Inference Latency | 1.82s | Wall-clock API response time |

## Per-Category Scores

| Category | Cases | Avg Score |
|---|---|---|
| acl | 3 | 63.2% |
| dhcp | 4 | 68.6% |
| dns | 3 | 64.9% |
| gateway | 4 | 61.7% |
| nat | 3 | 60.9% |
| routing | 4 | 74.5% |
| vlan | 4 | 68.1% |
| wireless | 5 | 57.8% |

## Best Performing Cases

| Case | Score | OSI | Tag | Severity |
|---|---|---|---|---|
| C001 | 81.0% | ✅ | ✅ | ✅ |
| C015 | 80.3% | ✅ | ✅ | ✅ |
| C020 | 76.6% | ✅ | ✅ | ✅ |
| C027 | 76.4% | ✅ | ✅ | ✅ |
| C007 | 75.3% | ✅ | ✅ | ✅ |

## Cases Needing Improvement

| Case | Score | OSI | Tag | Severity |
|---|---|---|---|---|
| C024 | 55.0% | ❌ | ✅ | ✅ |
| C018 | 52.6% | ✅ | ❌ | ✅ |
| C029 | 49.9% | ✅ | ✅ | ✅ |
| C030 | 44.0% | ❌ | ✅ | ✅ |
| C023 | 43.2% | ✅ | ✅ | ❌ |

## Responsible AI — Uncertain Cases

Cases with intentionally insufficient evidence: ['C005', 'C023', 'C030']

- **C005**: ⚠️ Over-confident (score: 61.0%)
- **C023**: ⚠️ Over-confident (score: 43.2%)
- **C030**: ✅ Appropriately hedged (score: 44.0%)
