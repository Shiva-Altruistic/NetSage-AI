#!/usr/bin/env python3
"""NetSage AI — Full diagnosis pipeline runner.

Project layout supported:
    NetSage/
    ├── Dataset/
    │   └── cases.csv
    ├── Rules/
    │   ├── checker.py
    │   ├── evaluator.py
    │   ├── prompt_engine.py
    │   └── run_diagnosis.py
    ├── Results/
    └── .env

Orchestrates:
    load cases → deterministic checker → Gemini diagnosis → evaluation

Examples (run from the NetSage project root):
    python Rules\\run_diagnosis.py --dry-run
    python Rules\\run_diagnosis.py --case C001
    python Rules\\run_diagnosis.py
    python Rules\\run_diagnosis.py --output-dir Results

The Gemini API key can be supplied with --api-key or through:
    GEMINI_API_KEY=your_key
in the project's .env file.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import asdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

RULES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = RULES_DIR.parent
DEFAULT_CSV = PROJECT_ROOT / "Dataset" / "cases.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Results"
ENV_FILE = PROJECT_ROOT / ".env"

# ---------------------------------------------------------------------------
# UTF-8 output
# ---------------------------------------------------------------------------

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Imports from Rules/
# ---------------------------------------------------------------------------

sys.path.insert(0, str(RULES_DIR))

from checker import check_case
from prompt_engine import DiagnosisEngine, Diagnosis, SYSTEM_PROMPT, DEFAULT_API_KEY
from evaluator import score_case, generate_eval_csv, generate_eval_report, CaseScore


def load_dotenv_file(path: Path) -> None:
    """Load simple KEY=VALUE pairs from a .env file.

    This avoids requiring python-dotenv just to load GEMINI_API_KEY.
    Existing environment variables are preserved.
    """
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        # Remove matching single/double quotes.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        # Do not overwrite an explicitly supplied environment variable.
        import os
        os.environ.setdefault(key, value)


# Load the project .env before DiagnosisEngine is instantiated.
load_dotenv_file(ENV_FILE)


def load_cases(csv_path: Path) -> list[dict]:
    """Load cases from CSV and validate required observed-data columns."""
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        required = {"case_id", "symptom", "topology_note", "show_output"}
        missing = required - cols

        if missing:
            raise SystemExit(
                f"Missing required columns in {csv_path}: {sorted(missing)}"
            )

        return list(reader)


def select_targets(cases: list[dict], target_id: str | None) -> list[dict]:
    """Return all cases or one requested case."""
    if not target_id:
        return cases

    targets = [c for c in cases if c.get("case_id") == target_id]
    if not targets:
        raise SystemExit(f"Case {target_id} not found in CSV.")

    return targets


def run_dry_run(cases: list[dict], target_id: str | None = None) -> None:
    """Build and print prompts without calling Gemini."""
    targets = select_targets(cases, target_id)
    engine = DiagnosisEngine(api_key=None)

    for case in targets:
        case_id = case["case_id"]

        print(f"\n{'=' * 70}")
        print(f"  CASE {case_id} - DRY RUN")
        print(f"{'=' * 70}")

        findings = [asdict(f) for f in check_case(case)]
        fails = sum(f["status"] == "FAIL" for f in findings)
        warns = sum(f["status"] == "WARNING" for f in findings)

        print(f"  Checker: {fails} FAILs, {warns} WARNINGs")

        prompt = engine.build_prompt(case, findings)

        print(f"  System prompt: {len(SYSTEM_PROMPT):,} chars")
        print(f"  User prompt:   {len(prompt):,} chars")
        print(f"\n{prompt}")

    print(f"\n{'=' * 70}")
    print(f"  DRY RUN COMPLETE - {len(targets)} case(s) processed")
    print(f"  System prompt size: {len(SYSTEM_PROMPT):,} chars")
    print(f"{'=' * 70}")


def run_full_pipeline(
    cases: list[dict],
    api_key: str | None,
    target_id: str | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    delay: float = 1.0,
) -> None:
    """Full pipeline: checker → Gemini → evaluator."""
    targets = select_targets(cases, target_id)

    output_dir.mkdir(parents=True, exist_ok=True)

    engine = DiagnosisEngine(api_key=api_key)

    diagnoses: list[tuple[dict, Diagnosis]] = []
    scores: list[CaseScore] = []

    total = len(targets)
    print(f"\n>> NetSage AI -- Diagnosing {total} case(s)\n")

    for i, case in enumerate(targets, 1):
        case_id = case["case_id"]
        print(f"[{i}/{total}] {case_id}: ", end="", flush=True)

        # Step 1: deterministic checker
        findings = [asdict(f) for f in check_case(case)]
        fails = sum(f["status"] == "FAIL" for f in findings)

        print(f"checker({fails}F) → ", end="", flush=True)

        # Step 2: Gemini diagnosis
        diagnosis = engine.diagnose(case, findings)
        diagnoses.append((case, diagnosis))

        if "[API ERROR]" in diagnosis.fault or "[PARSE ERROR]" in diagnosis.fault:
            print(f"[!] {diagnosis.fault[:120]}", flush=True)
        else:
            print(
                f"[+] {diagnosis.concept_tag}/{diagnosis.severity} ",
                end="",
                flush=True,
            )

            # Step 3: evaluate against ground truth
            score = score_case(case, diagnosis)
            scores.append(score)

            print(f"(score: {score.overall_score:.0%})", flush=True)

            # Step 4: Responsible AI telemetry logging
            try:
                from responsible_ai import RAILogger
                RAILogger(output_dir=output_dir).audit_case(
                    case=case,
                    diagnosis=asdict(diagnosis),
                    findings=findings,
                    prompt_version="V1",
                    model_name=engine.model_name,
                )
            except Exception:
                pass

        if i < total:
            time.sleep(delay)

    # -----------------------------------------------------------------------
    # Save AI diagnoses
    # -----------------------------------------------------------------------

    diag_path = output_dir / "ai_diagnoses.csv"
    diag_fields = [
        "case_id",
        "fault",
        "osi_layer",
        "concept_tag",
        "severity",
        "confidence",
        "next_command",
        "fix",
        "reasoning",
    ]

    with diag_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=diag_fields)
        writer.writeheader()

        for case, diagnosis in diagnoses:
            row = {
                key: value
                for key, value in asdict(diagnosis).items()
                if key in diag_fields
            }
            row["case_id"] = case["case_id"]
            writer.writerow(row)

    print(f"\n[>] AI diagnoses saved: {diag_path}")

    # -----------------------------------------------------------------------
    # Save evaluation
    # -----------------------------------------------------------------------

    if not scores:
        print("[!] No successful AI diagnoses were available for evaluation.")
        return

    eval_csv_path = output_dir / "eval_results.csv"
    generate_eval_csv(scores, eval_csv_path)
    print(f"[>] Eval results saved: {eval_csv_path}")

    eval_report_path = output_dir / "eval_report.md"
    generate_eval_report(scores, cases, eval_report_path)
    print(f"[>] Eval report saved: {eval_report_path}")

    # Generate Responsible AI Governance Report
    try:
        from responsible_ai import RAILogger
        rai_report = RAILogger(output_dir=output_dir).generate_governance_report()
        print(f"[>] Responsible AI report saved: {rai_report}")
    except Exception:
        pass

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    avg_score = sum(s.overall_score for s in scores) / len(scores)
    osi_acc = sum(s.osi_layer_match for s in scores) / len(scores)
    tag_acc = sum(s.concept_tag_match for s in scores) / len(scores)
    sev_acc = sum(s.severity_match for s in scores) / len(scores)

    print(f"\n{'=' * 60}")
    print(f"  RESULTS SUMMARY ({len(scores)} cases)")
    print(f"{'=' * 60}")
    print(f"  Overall score:    {avg_score:.1%}")
    print(f"  OSI layer match:  {osi_acc:.1%}")
    print(f"  Concept tag:      {tag_acc:.1%}")
    print(f"  Severity:         {sev_acc:.1%}")
    print(f"{'=' * 60}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NetSage AI — full diagnosis and evaluation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Rules\\run_diagnosis.py --dry-run
  python Rules\\run_diagnosis.py --case C001
  python Rules\\run_diagnosis.py
  python Rules\\run_diagnosis.py --delay 2.0
        """,
    )

    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV),
        help=f"Path to cases.csv (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help="Gemini API key; otherwise loaded from .env or defaults",
    )
    parser.add_argument(
        "--case",
        default=None,
        help="Run only a specific case ID, e.g. C001",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build prompts without calling Gemini",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory for generated results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between Gemini calls in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Launch human review workflow immediately following AI diagnosis",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    output_dir = Path(args.output_dir).resolve()

    cases = load_cases(csv_path)
    print(f"[>] Loaded {len(cases)} cases from {csv_path}")

    if args.dry_run:
        run_dry_run(cases, args.case)
    else:
        run_full_pipeline(
            cases=cases,
            api_key=args.api_key,
            target_id=args.case,
            output_dir=output_dir,
            delay=args.delay,
        )
        if args.review:
            from human_review import (
                interactive_review,
                save_review_records,
                generate_review_report,
                load_csv,
            )
            ai_path = output_dir / "ai_diagnoses.csv"
            ai_diagnoses = load_csv(ai_path)
            reviews = interactive_review(cases, ai_diagnoses, target_id=args.case, output_dir=output_dir)
            save_review_records(reviews, output_dir / "human_review.csv")
            generate_review_report(reviews, output_dir / "human_review_report.md")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
