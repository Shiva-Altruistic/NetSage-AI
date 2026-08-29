# NetSage AI — Prompt Testing

## Purpose

This folder is for the **Design and Test the AI Prompt** stage.

The existing AI pipeline remains in `Rules/`. The prompt-testing folder keeps
prompt experiments separate so the baseline implementation is not accidentally
overwritten.

## Recommended project structure

```text
NetSage/
├── Dataset/
│   └── cases.csv
│
├── Rules/
│   ├── checker.py
│   ├── evaluator.py
│   ├── prompt_engine.py
│   └── run_diagnosis.py
│
├── Results/
│   ├── prompt_comparison.csv
│   └── prompt_comparison_report.md
│
└── Prompt_Testing/
    ├── README.md
    ├── prompt_v1.py
    ├── prompt_v2.py
    └── test_prompt.py
```

## Prompt versions

- `prompt_v1.py` — baseline prompt corresponding to the current prompt design.
- `prompt_v2.py` — improved prompt to test against V1.
- `test_prompt.py` — A/B comparison harness that runs both prompts through Gemini and scores results.

## Usage

All commands run from the **NetSage project root**.

### Dry run (preview prompts without calling Gemini)

```bash
python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --dry-run
```

### Test a single case (live Gemini call, V1 vs V2)

```bash
python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --case C001
```

### Run V2-only (saves API calls during iteration)

```bash
python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --v2-only
```

### Full 8-case comparison

```bash
python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv
```

### All 30 cases

```bash
python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --all-cases
```

### Run comparison with interactive human review

```bash
python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --review
```

### CLI Flags

| Flag | Description |
|---|---|
| `--csv` | Path to cases.csv (default: `Dataset/cases.csv`) |
| `--case C001` | Run only a specific case ID |
| `--dry-run` | Preview prompts without calling Gemini |
| `--v2-only` | Only run V2 prompt (skip V1) |
| `--all-cases` | Run all 30 cases instead of the 8 test cases |
| `--delay 1.5` | Delay between Gemini calls (default: 1.5s) |
| `--review` | Launch human review workflow immediately after comparison |
| `--api-key` | Override Gemini API key |
| `--output-dir` | Output directory (default: `Results/`) |

## Human Review & Safety Gate

To independently run or benchmark human reviews:

```bash
# Interactive engineer review workflow
python Rules/human_review.py

# Benchmark review comparing V2 diagnoses against ground truth
python Rules/human_review.py --ai-csv Results/prompt_comparison.csv --version V2 --benchmark

# Quick approve for automated CI/CD validation
python Rules/human_review.py --quick-approve --case C001
```

Human review produces:
- `Results/human_review.csv` — full audit trail with reviewer decisions, risk ratings, and overrides.
- `Results/human_review_report.md` — approval rates, agreement scores, and high-risk command alerts.

## Responsible AI Logging & Governance

NetSage AI includes automated Responsible AI telemetry and governance reporting:

```bash
# Compile and generate the complete Responsible AI governance report
python Rules/responsible_ai.py --generate-report

# Deep-dive audit into an intentionally ambiguous case (e.g. C005, C023, C030)
python Rules/responsible_ai.py --audit-case C005

# Re-audit and benchmark all evaluation diagnoses
python Rules/responsible_ai.py --benchmark
```

Responsible AI outputs:
- `Results/responsible_ai_log.jsonl` — immutable append-only JSON event stream of every inference.
- `Results/responsible_ai_log.csv` — tabular audit log for spreadsheets and analytics dashboards.
- `Results/responsible_ai_audit.md` — NIST AI RMF and Google SAIF-aligned governance audit report.

## Output

The harness produces:
- `Results/prompt_comparison.csv` — per-case V1 vs V2 scores
- `Results/prompt_comparison_report.md` — summary report with winner analysis

## Test cases

Start with:

- C001 — known VLAN/gateway diagnosis
- C005 — insufficient evidence
- C011 — lower-performing case
- C018 — lower-performing case
- C023 — insufficient evidence
- C025 — lower-performing case
- C029 — lower-performing case
- C030 — insufficient evidence

Then run the complete 30-case evaluation after the prompt is stable.

## Baseline

Current evaluation baseline:

- Overall: 62.5%
- OSI layer: 86.7%
- Concept tag: 93.3%
- Severity: 76.7%
- Fault similarity: 40.1%
- Fix similarity: 33.9%
- Confidence appropriateness: 90.0%

These values are the baseline for Prompt V2.
