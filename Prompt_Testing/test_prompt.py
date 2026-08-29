#!/usr/bin/env python3
"""NetSage AI — Prompt V1 vs V2 A/B Comparison Harness.

Connects both prompt versions to the Gemini diagnosis engine, runs them
against selected test cases, scores both with the evaluator, and produces
a side-by-side comparison report.

Examples (run from the NetSage project root):
    python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --dry-run
    python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --case C001
    python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --v2-only
    python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROMPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PROMPT_DIR.parent
RULES_DIR = PROJECT_ROOT / "Rules"
DEFAULT_CSV = PROJECT_ROOT / "Dataset" / "cases.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Results"
ENV_FILE = PROJECT_ROOT / ".env"

# Add directories to sys.path for CLI execution
for path_entry in (PROJECT_ROOT, RULES_DIR, PROMPT_DIR):
    if str(path_entry) not in sys.path:
        sys.path.insert(0, str(path_entry))

# Imports supporting both IDE static analysis and direct CLI execution
try:
    from Rules.checker import check_case
    from Rules.prompt_engine import (
        DiagnosisEngine,
        Diagnosis,
        SYSTEM_PROMPT,
        DEFAULT_API_KEY,
    )
    from Rules.evaluator import score_case, CaseScore
except ImportError:
    from checker import check_case
    from prompt_engine import (
        DiagnosisEngine,
        Diagnosis,
        SYSTEM_PROMPT,
        DEFAULT_API_KEY,
    )
    from evaluator import score_case, CaseScore

try:
    from Prompt_Testing.prompt_v2 import SYSTEM_PROMPT_V2
except ImportError:
    from prompt_v2 import SYSTEM_PROMPT_V2


# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------

def load_dotenv_file(path: Path) -> None:
    """Load simple KEY=VALUE pairs from a .env file."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_dotenv_file(ENV_FILE)


# ---------------------------------------------------------------------------
# Test cases (focus cases for prompt iteration)
# ---------------------------------------------------------------------------

TEST_CASES = ["C001", "C005", "C011", "C018", "C023", "C025", "C029", "C030"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_cases(csv_path: Path) -> list[dict]:
    """Load cases from CSV."""
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def select_cases(cases: list[dict], target_id: str | None, all_cases: bool = False) -> list[dict]:
    """Return a single case, the TEST_CASES subset, or all cases."""
    if target_id:
        targets = [c for c in cases if c.get("case_id") == target_id]
        if not targets:
            raise SystemExit(f"Case {target_id} not found in CSV.")
        return targets
    if all_cases:
        return cases
    return [c for c in cases if c.get("case_id") in TEST_CASES]


# ---------------------------------------------------------------------------
# Dry-run mode
# ---------------------------------------------------------------------------

def run_dry_run(cases: list[dict], target_id: str | None = None, all_cases: bool = False) -> None:
    """Build and print prompts for both V1 and V2 without calling Gemini."""
    targets = select_cases(cases, target_id, all_cases=all_cases)

    engine_v1 = DiagnosisEngine(api_key=None, system_prompt=SYSTEM_PROMPT)
    engine_v2 = DiagnosisEngine(api_key=None, system_prompt=SYSTEM_PROMPT_V2)

    for case in targets:
        case_id = case["case_id"]
        findings = [asdict(f) for f in check_case(case)]
        fails = sum(f["status"] == "FAIL" for f in findings)
        warns = sum(f["status"] == "WARNING" for f in findings)

        print(f"\n{'=' * 70}")
        print(f"  CASE {case_id} — DRY RUN")
        print(f"{'=' * 70}")
        print(f"  Checker: {fails} FAILs, {warns} WARNINGs")

        prompt = engine_v1.build_prompt(case, findings)
        print(f"\n  V1 system prompt: {len(SYSTEM_PROMPT):,} chars")
        print(f"  V2 system prompt: {len(SYSTEM_PROMPT_V2):,} chars")
        print(f"  User prompt:      {len(prompt):,} chars")

        print(f"\n▸ PRE-ANALYSIS findings:")
        for f in findings:
            if f["status"] != "NOT_APPLICABLE":
                print(f"  {f['status']:16} {f['rule_id']}: {f['message']}")

    print(f"\n{'=' * 70}")
    print(f"  DRY RUN COMPLETE — {len(targets)} case(s) previewed")
    print(f"  V1 system prompt: {len(SYSTEM_PROMPT):,} chars")
    print(f"  V2 system prompt: {len(SYSTEM_PROMPT_V2):,} chars")
    print(f"{'=' * 70}")
    print(f"\n  Run without --dry-run to call Gemini and compare scores.")


# ---------------------------------------------------------------------------
# Live A/B comparison
# ---------------------------------------------------------------------------

def run_comparison(
    cases: list[dict],
    api_key: str | None,
    target_id: str | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    delay: float = 1.5,
    v2_only: bool = False,
    all_cases: bool = False,
) -> None:
    """Run V1 and/or V2 prompts through Gemini and compare scores."""
    targets = select_cases(cases, target_id, all_cases=all_cases)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine_v1 = DiagnosisEngine(api_key=api_key, system_prompt=SYSTEM_PROMPT)
    engine_v2 = DiagnosisEngine(api_key=api_key, system_prompt=SYSTEM_PROMPT_V2)

    results: list[dict] = []
    total = len(targets)
    versions = ["V2"] if v2_only else ["V1", "V2"]

    print(f"\n>> NetSage AI — Prompt {'V2-only' if v2_only else 'V1 vs V2'} Comparison", flush=True)
    print(f">> Testing {total} case(s): {', '.join(c['case_id'] for c in targets)}\n", flush=True)

    for i, case in enumerate(targets, 1):
        case_id = case["case_id"]

        # Step 1: deterministic checker
        findings = [asdict(f) for f in check_case(case)]
        fails = sum(f["status"] == "FAIL" for f in findings)

        row: dict = {"case_id": case_id, "checker_fails": fails}

        for version in versions:
            engine = engine_v1 if version == "V1" else engine_v2
            label = version

            print(f"[{i}/{total}] {case_id} ({label}): ", end="", flush=True)
            print(f"checker({fails}F) → ", end="", flush=True)

            diagnosis = engine.diagnose(case, findings)

            if "[API ERROR]" in diagnosis.fault or "[PARSE ERROR]" in diagnosis.fault:
                print(f"[!] {diagnosis.fault[:100]}", flush=True)
                row[f"{label}_fault"] = diagnosis.fault[:200]
                row[f"{label}_score"] = 0.0
                row[f"{label}_concept_tag"] = ""
                row[f"{label}_osi_layer"] = 0
                row[f"{label}_severity"] = ""
                row[f"{label}_fix"] = ""
                row[f"{label}_next_command"] = ""
                row[f"{label}_osi_match"] = False
                row[f"{label}_tag_match"] = False
                row[f"{label}_sev_match"] = False
                row[f"{label}_fault_sim"] = 0.0
                row[f"{label}_fix_sim"] = 0.0
                row[f"{label}_conf_ok"] = False
                row[f"{label}_confidence"] = ""
            else:
                score = score_case(case, diagnosis)
                print(
                    f"[+] {diagnosis.concept_tag}/{diagnosis.severity} "
                    f"conf={diagnosis.confidence} "
                    f"(score: {score.overall_score:.0%})",
                    flush=True,
                )
                row[f"{label}_fault"] = diagnosis.fault[:200]
                row[f"{label}_score"] = score.overall_score
                row[f"{label}_concept_tag"] = diagnosis.concept_tag
                row[f"{label}_osi_layer"] = diagnosis.osi_layer
                row[f"{label}_severity"] = diagnosis.severity
                row[f"{label}_fix"] = diagnosis.fix
                row[f"{label}_next_command"] = diagnosis.next_command
                row[f"{label}_osi_match"] = score.osi_layer_match
                row[f"{label}_tag_match"] = score.concept_tag_match
                row[f"{label}_sev_match"] = score.severity_match
                row[f"{label}_fault_sim"] = score.fault_similarity
                row[f"{label}_fix_sim"] = score.fix_similarity
                row[f"{label}_conf_ok"] = score.confidence_appropriate
                row[f"{label}_confidence"] = diagnosis.confidence

            # Delay between API calls
            if not (i == total and version == versions[-1]):
                time.sleep(delay)

        results.append(row)

    # -------------------------------------------------------------------
    # Save comparison CSV
    # -------------------------------------------------------------------
    csv_path = output_dir / "prompt_comparison.csv"
    if results:
        fieldnames = []
        for r in results:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(f"\n[>] Comparison CSV saved: {csv_path}", flush=True)

    # -------------------------------------------------------------------
    # Generate comparison report
    # -------------------------------------------------------------------
    report_path = output_dir / "prompt_comparison_report.md"
    _generate_comparison_report(results, versions, report_path, v2_only)
    print(f"[>] Comparison report saved: {report_path}", flush=True)

    # -------------------------------------------------------------------
    # Generate Responsible AI Governance report
    # -------------------------------------------------------------------
    try:
        try:
            from Rules.responsible_ai import RAILogger
        except ImportError:
            from responsible_ai import RAILogger
        rai_report = RAILogger(output_dir=output_dir).generate_governance_report()
        print(f"[>] Responsible AI report saved: {rai_report}", flush=True)
    except Exception:
        pass


def _generate_comparison_report(
    results: list[dict],
    versions: list[str],
    output_path: Path,
    v2_only: bool,
) -> None:
    """Generate a markdown comparison report."""
    lines = [
        "# NetSage AI — Prompt Comparison Report\n",
    ]

    n = len(results)
    if n == 0:
        lines.append("No cases were evaluated.\n")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return

    if v2_only:
        # V2-only report
        v2_scores = [r.get("V2_score", 0) for r in results]
        avg_v2 = sum(v2_scores) / len(v2_scores) if v2_scores else 0

        lines.extend([
            f"**Mode:** V2-only evaluation",
            f"**Cases evaluated:** {n}",
            f"**V2 average score:** {avg_v2:.1%}\n",
            "## Per-Case Results\n",
            "| Case | V2 Score | OSI | Tag | Sev | Conf |",
            "|---|---|---|---|---|---|",
        ])
        for r in results:
            lines.append(
                f"| {r['case_id']} "
                f"| {r.get('V2_score', 0):.1%} "
                f"| {'✅' if r.get('V2_osi_match') else '❌'} "
                f"| {'✅' if r.get('V2_tag_match') else '❌'} "
                f"| {'✅' if r.get('V2_sev_match') else '❌'} "
                f"| {r.get('V2_confidence', '?')} |"
            )
    else:
        # Full V1 vs V2 comparison
        v1_scores = [r.get("V1_score", 0) for r in results]
        v2_scores = [r.get("V2_score", 0) for r in results]
        avg_v1 = sum(v1_scores) / len(v1_scores) if v1_scores else 0
        avg_v2 = sum(v2_scores) / len(v2_scores) if v2_scores else 0
        delta = avg_v2 - avg_v1

        winner = "V2 🏆" if delta > 0 else ("V1 🏆" if delta < 0 else "Tie")

        lines.extend([
            f"**Cases evaluated:** {n}",
            f"**V1 average score:** {avg_v1:.1%}",
            f"**V2 average score:** {avg_v2:.1%}",
            f"**Delta (V2 − V1):** {delta:+.1%}",
            f"**Winner:** {winner}\n",
            "## Per-Case Comparison\n",
            "| Case | V1 Score | V2 Score | Δ | V2 Better? |",
            "|---|---|---|---|---|",
        ])
        v2_wins = 0
        for r in results:
            s1 = r.get("V1_score", 0)
            s2 = r.get("V2_score", 0)
            d = s2 - s1
            better = "✅" if d > 0.01 else ("❌" if d < -0.01 else "➖")
            if d > 0.01:
                v2_wins += 1
            lines.append(
                f"| {r['case_id']} | {s1:.1%} | {s2:.1%} | {d:+.1%} | {better} |"
            )

        lines.extend([
            "",
            "## Metric Breakdown\n",
            "| Metric | V1 | V2 |",
            "|---|---|---|",
        ])

        for metric, label in [
            ("osi_match", "OSI Layer Match"),
            ("tag_match", "Concept Tag Match"),
            ("sev_match", "Severity Match"),
            ("fault_sim", "Fault Similarity"),
            ("fix_sim", "Fix Similarity"),
            ("conf_ok", "Confidence OK"),
        ]:
            v1_vals = [r.get(f"V1_{metric}", 0) for r in results]
            v2_vals = [r.get(f"V2_{metric}", 0) for r in results]
            v1_avg = sum(v1_vals) / len(v1_vals) if v1_vals else 0
            v2_avg = sum(v2_vals) / len(v2_vals) if v2_vals else 0
            lines.append(f"| {label} | {v1_avg:.1%} | {v2_avg:.1%} |")

        lines.extend([
            "",
            f"## Summary\n",
            f"V2 won on **{v2_wins}/{n}** cases.",
        ])

    # Baseline reference
    lines.extend([
        "",
        "## Baseline Reference\n",
        "| Metric | Baseline |",
        "|---|---|",
        "| Overall | 62.5% |",
        "| OSI Layer | 86.7% |",
        "| Concept Tag | 93.3% |",
        "| Severity | 76.7% |",
        "| Fault Similarity | 40.1% |",
        "| Fix Similarity | 33.9% |",
        "| Confidence | 90.0% |",
    ])

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="NetSage AI — Prompt V1 vs V2 comparison harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --dry-run
  python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --case C001
  python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv --v2-only
  python Prompt_Testing/test_prompt.py --csv Dataset/cases.csv
        """,
    )

    parser.add_argument(
        "--csv", default=str(DEFAULT_CSV),
        help=f"Path to cases.csv (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="Gemini API key (default: from .env or built-in)",
    )
    parser.add_argument(
        "--case", default=None,
        help="Run only a specific case ID, e.g. C001",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview prompts without calling Gemini",
    )
    parser.add_argument(
        "--v2-only", action="store_true",
        help="Only run V2 prompt (saves API calls during iteration)",
    )
    parser.add_argument(
        "--output-dir", default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Delay between Gemini calls in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--all-cases", action="store_true",
        help="Run all 30 cases instead of just the 8 test cases",
    )
    parser.add_argument(
        "--review", action="store_true",
        help="Launch human review workflow immediately after comparison",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    output_dir = Path(args.output_dir).resolve()

    cases = load_cases(csv_path)
    print(f"[>] Loaded {len(cases)} cases from {csv_path}")

    # If --all-cases, override selection to use all
    if args.all_cases:
        target_cases = cases
    else:
        target_cases = cases  # select_cases will filter

    if args.dry_run:
        run_dry_run(cases, args.case, all_cases=args.all_cases)
    else:
        api_key = args.api_key or DEFAULT_API_KEY
        run_comparison(
            cases=cases,
            api_key=api_key,
            target_id=args.case,
            output_dir=output_dir,
            delay=args.delay,
            v2_only=args.v2_only,
            all_cases=args.all_cases,
        )
        if args.review:
            try:
                from Rules.human_review import (
                    interactive_review,
                    save_review_records,
                    generate_review_report,
                    load_ai_diagnoses,
                )
            except ImportError:
                from human_review import (
                    interactive_review,
                    save_review_records,
                    generate_review_report,
                    load_ai_diagnoses,
                )
            comp_path = output_dir / "prompt_comparison.csv"
            ai_diagnoses = load_ai_diagnoses(comp_path, version="V2")
            reviews = interactive_review(cases, ai_diagnoses, target_id=args.case, output_dir=output_dir)
            save_review_records(reviews, output_dir / "human_review.csv")
            generate_review_report(reviews, output_dir / "human_review_report.md")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
