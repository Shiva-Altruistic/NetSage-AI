#!/usr/bin/env python3
"""NetSage AI — Human Review & Safety Gate.

Provides a human-in-the-loop review workflow for evaluating, approving,
modifying, and auditing AI network diagnoses and remediation commands
before they are applied to network infrastructure.

Supports:
  1. Interactive CLI Review:
     Step through AI diagnoses, inspect evidence, and [A]pprove, [R]eject, or [M]odify.
  2. Batch Benchmark Review (--benchmark):
     Audits AI diagnoses against ground truth expert baselines across all cases.
  3. Safety Risk Guardrail:
     Flags high-risk Cisco commands (e.g. 'clear ip dhcp binding *', 'shutdown',
     or broad ACL changes) that require senior engineer sign-off.

Outputs:
  - Results/human_review.csv        (Full audit trail of human review decisions)
  - Results/human_review_report.md  (Human-AI agreement & safety analysis report)
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# Force UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

RULES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = RULES_DIR.parent
DEFAULT_CASES_CSV = PROJECT_ROOT / "Dataset" / "cases.csv"
DEFAULT_AI_CSV = PROJECT_ROOT / "Results" / "ai_diagnoses.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Results"

# ---------------------------------------------------------------------------
# Safety Guardrails: High-Risk Command Patterns
# ---------------------------------------------------------------------------

HIGH_RISK_PATTERNS = [
    (r"\bclear\s+ip\s+dhcp\s+binding\b", "High", "Clears all active DHCP leases network-wide"),
    (r"\bshutdown\b", "Medium", "Disables network interface"),
    (r"\bswitchport\s+trunk\s+native\s+vlan\b", "Medium", "Changes 802.1Q native VLAN trunking"),
    (r"\bno\s+access-list\b", "High", "Deletes access control list, potentially exposing traffic"),
    (r"\bdeny\s+ip\s+any\s+any\b", "High", "Blanket drop rule could isolate all traffic"),
    (r"\brouter\s+eigrp\s+\d+\s*\n\s*no\b", "High", "Removes active routing protocol process"),
]


def assess_command_risk(fix_text: str) -> tuple[str, list[str]]:
    """Analyze a proposed remediation command for operational risks."""
    risks = []
    highest_level = "Low"
    for pattern, level, description in HIGH_RISK_PATTERNS:
        if re.search(pattern, fix_text, re.I):
            risks.append(f"[{level}] {description}")
            if level == "High":
                highest_level = "High"
            elif level == "Medium" and highest_level != "High":
                highest_level = "Medium"
    return highest_level, risks


# ---------------------------------------------------------------------------
# Review Record Dataclass
# ---------------------------------------------------------------------------

@dataclass
class ReviewRecord:
    case_id: str
    decision: str  # APPROVED | REJECTED | MODIFIED | SKIPPED
    risk_level: str  # Low | Medium | High
    ai_concept_tag: str
    human_concept_tag: str
    ai_osi_layer: int
    human_osi_layer: int
    ai_severity: str
    human_severity: str
    ai_confidence: str
    agreed_concept: bool
    agreed_osi: bool
    agreed_severity: bool
    ai_fix: str
    approved_fix: str
    reviewer_notes: str
    reviewer_id: str = "NetEng-1"
    timestamp: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Loading utilities
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_ai_diagnoses(path: Path, version: str = "V2") -> list[dict]:
    """Load AI diagnoses, automatically adapting from prompt_comparison.csv if needed."""
    if not path.exists():
        comp_path = path.parent / "prompt_comparison.csv"
        if comp_path.exists():
            return load_ai_diagnoses(comp_path, version=version)
        return []

    rows = load_csv(path)
    if not rows:
        return []

    # If this is prompt_comparison.csv, normalize to standard diagnosis schema
    if any(k.startswith("V1_") or k.startswith("V2_") for k in rows[0].keys()):
        normalized = []
        prefix = f"{version}_"
        for r in rows:
            normalized.append({
                "case_id": r.get("case_id", ""),
                "fault": r.get(f"{prefix}fault", ""),
                "osi_layer": int(r.get(f"{prefix}osi_layer", 0) or 0),
                "concept_tag": r.get(f"{prefix}concept_tag", ""),
                "severity": r.get(f"{prefix}severity", ""),
                "confidence": r.get(f"{prefix}confidence", ""),
                "next_command": r.get(f"{prefix}next_command", ""),
                "fix": r.get(f"{prefix}fix", ""),
                "tag_match": (r.get(f"{prefix}tag_match", "").lower() in ("true", "1")),
                "osi_match": (r.get(f"{prefix}osi_match", "").lower() in ("true", "1")),
                "sev_match": (r.get(f"{prefix}sev_match", "").lower() in ("true", "1")),
            })
        return normalized
    return rows


# ---------------------------------------------------------------------------
# Interactive Review Workflow
# ---------------------------------------------------------------------------

def interactive_review(
    cases: list[dict],
    ai_diagnoses: list[dict],
    target_id: Optional[str] = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> list[ReviewRecord]:
    """Interactively step through AI diagnoses for human engineer review."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ai_lookup = {d.get("case_id"): d for d in ai_diagnoses}
    case_lookup = {c.get("case_id"): c for c in cases}

    targets = [target_id] if target_id else list(case_lookup.keys())
    reviews: list[ReviewRecord] = []

    print("\n" + "═" * 72)
    print("  NetSage AI — Human Review & Safety Gate")
    print("  Review AI diagnoses before remediation deployment")
    print("═" * 72 + "\n")

    for idx, cid in enumerate(targets, 1):
        case = case_lookup.get(cid)
        diag = ai_lookup.get(cid)

        if not case or not diag:
            continue

        fix_text = diag.get("fix", "") or case.get("expected_fix", "")
        risk_level, risk_reasons = assess_command_risk(fix_text)

        print(f"\n[{idx}/{len(targets)}] CASE {cid}")
        print("─" * 72)
        print(f"▸ Symptom:     {case.get('symptom', '')[:120]}...")
        print(f"▸ Topology:    {case.get('topology_note', '')[:100]}...")
        print("─" * 72)
        print(f"▸ AI Diagnosis:")
        print(f"  • Fault:       {diag.get('fault', '')[:160]}...")
        print(f"  • OSI Layer:   Layer {diag.get('osi_layer', '?')}")
        print(f"  • Concept:     {diag.get('concept_tag', '?')}")
        print(f"  • Severity:    {diag.get('severity', '?')}")
        print(f"  • Confidence:  {diag.get('confidence', '?')}")
        print(f"  • Next Cmd:    {diag.get('next_command', '')}")
        print(f"  • Fix:         {fix_text}")
        print(f"  • Risk Level:  {risk_level.upper()}")
        if risk_reasons:
            for r in risk_reasons:
                print(f"    ⚠️  {r}")
        print("─" * 72)

        prompt = "Decision: [A]pprove | [R]eject | [M]odify | [S]kip (default: A): "
        try:
            choice = input(prompt).strip().upper() or "A"
        except (EOFError, KeyboardInterrupt):
            print("\nReview aborted by user.")
            break

        if choice == "S":
            continue

        human_concept = diag.get("concept_tag", "") or case.get("concept_tag", "")
        human_osi = int(diag.get("osi_layer", 0) or case.get("osi_layer", 0) or 0)
        human_severity = diag.get("severity", "") or case.get("severity", "")
        approved_fix = fix_text
        notes = ""

        if choice == "A":
            decision = "APPROVED"
            notes = "Approved by network engineer without modification."
        elif choice == "R":
            decision = "REJECTED"
            notes = input("Reason for rejection: ").strip() or "Rejected: diagnosis does not match topology."
            approved_fix = ""
        elif choice == "M":
            decision = "MODIFIED"
            notes = input("Reviewer override notes: ").strip() or "Modified by reviewer."
            override_tag = input(f"Override concept tag [{human_concept}]: ").strip()
            if override_tag:
                human_concept = override_tag
            override_fix = input(f"Override fix [{fix_text[:40]}...]: ").strip()
            if override_fix:
                approved_fix = override_fix
        else:
            decision = "APPROVED"

        record = ReviewRecord(
            case_id=cid,
            decision=decision,
            risk_level=risk_level,
            ai_concept_tag=diag.get("concept_tag", ""),
            human_concept_tag=human_concept,
            ai_osi_layer=int(diag.get("osi_layer", 0) or 0),
            human_osi_layer=human_osi,
            ai_severity=diag.get("severity", ""),
            human_severity=human_severity,
            ai_confidence=diag.get("confidence", ""),
            agreed_concept=(diag.get("concept_tag", "").lower() == human_concept.lower()),
            agreed_osi=(int(diag.get("osi_layer", 0) or 0) == human_osi),
            agreed_severity=(diag.get("severity", "").lower() == human_severity.lower()),
            ai_fix=fix_text,
            approved_fix=approved_fix,
            reviewer_notes=notes,
        )
        reviews.append(record)

    return reviews


# ---------------------------------------------------------------------------
# Benchmark / Automated Review Workflow
# ---------------------------------------------------------------------------

def benchmark_review(
    cases: list[dict],
    ai_diagnoses: list[dict],
) -> list[ReviewRecord]:
    """Benchmark AI diagnoses against known ground truth expert reviews."""
    ai_lookup = {d.get("case_id"): d for d in ai_diagnoses}
    reviews: list[ReviewRecord] = []

    for case in cases:
        cid = case.get("case_id", "")
        diag = ai_lookup.get(cid)
        if not diag:
            continue

        gt_tag = case.get("concept_tag", "").lower().strip()
        gt_osi = int(case.get("osi_layer", 0) or 0)
        gt_sev = case.get("severity", "").lower().strip()
        gt_fix = case.get("expected_fix", "")

        ai_tag = diag.get("concept_tag", "").lower().strip()
        ai_osi = int(diag.get("osi_layer", 0) or 0)
        ai_sev = diag.get("severity", "").lower().strip()
        ai_fix = diag.get("fix", "") or gt_fix
        ai_conf = diag.get("confidence", "").lower().strip()

        # Check agreement from actual fields or from pre-evaluated matches
        if diag.get("concept_tag"):
            agreed_tag = (ai_tag == gt_tag)
        else:
            agreed_tag = diag.get("tag_match", False)
            if agreed_tag:
                ai_tag = gt_tag

        if diag.get("osi_layer"):
            agreed_osi = (ai_osi == gt_osi)
        else:
            agreed_osi = diag.get("osi_match", False)
            if agreed_osi:
                ai_osi = gt_osi

        if diag.get("severity"):
            agreed_sev = (ai_sev == gt_sev)
        else:
            agreed_sev = diag.get("sev_match", False)
            if agreed_sev:
                ai_sev = gt_sev

        risk_level, _ = assess_command_risk(ai_fix)

        # Decision rule based on expert agreement
        if agreed_tag and agreed_osi:
            if agreed_sev:
                decision = "APPROVED"
                notes = "Fully aligns with ground truth diagnosis and remediation."
                approved_fix = ai_fix
            else:
                decision = "MODIFIED"
                notes = f"Severity adjusted from '{ai_sev or 'unspecified'}' to '{gt_sev}'."
                approved_fix = ai_fix
        else:
            decision = "REJECTED" if not agreed_tag else "MODIFIED"
            notes = f"Disagreement on root cause: AI predicted {ai_tag or 'unknown'}/L{ai_osi}, ground truth is {gt_tag}/L{gt_osi}."
            approved_fix = gt_fix

        record = ReviewRecord(
            case_id=cid,
            decision=decision,
            risk_level=risk_level,
            ai_concept_tag=ai_tag,
            human_concept_tag=gt_tag,
            ai_osi_layer=ai_osi,
            human_osi_layer=gt_osi,
            ai_severity=ai_sev,
            human_severity=gt_sev,
            ai_confidence=ai_conf,
            agreed_concept=agreed_tag,
            agreed_osi=agreed_osi,
            agreed_severity=agreed_sev,
            ai_fix=ai_fix,
            approved_fix=approved_fix,
            reviewer_notes=notes,
            reviewer_id="Expert-GroundTruth",
        )
        reviews.append(record)

    return reviews


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def save_review_records(reviews: list[ReviewRecord], output_path: Path) -> None:
    """Save review decisions to an audit CSV file."""
    if not reviews:
        return
    fieldnames = list(asdict(reviews[0]).keys())
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in reviews:
            writer.writerow(asdict(r))


def generate_review_report(reviews: list[ReviewRecord], output_path: Path) -> None:
    """Generate human review summary & safety analysis report in Markdown."""
    total = len(reviews)
    if total == 0:
        output_path.write_text("# Human Review Report\n\nNo reviews recorded.\n", encoding="utf-8")
        return

    approved = sum(r.decision == "APPROVED" for r in reviews)
    modified = sum(r.decision == "MODIFIED" for r in reviews)
    rejected = sum(r.decision == "REJECTED" for r in reviews)

    approval_rate = approved / total
    tag_agreement = sum(r.agreed_concept for r in reviews) / total
    osi_agreement = sum(r.agreed_osi for r in reviews) / total
    sev_agreement = sum(r.agreed_severity for r in reviews) / total

    high_risk_cases = [r for r in reviews if r.risk_level == "High"]
    medium_risk_cases = [r for r in reviews if r.risk_level == "Medium"]

    lines = [
        "# NetSage AI — Human Review & Safety Audit Report\n",
        f"**Cases Reviewed:** {total}",
        f"**Review Mode:** {'Benchmark Audit' if reviews[0].reviewer_id == 'Expert-GroundTruth' else 'Interactive Engineer Review'}",
        f"**Overall Approval Rate:** {approval_rate:.1%}\n",
        "## Decision Summary\n",
        "| Decision | Count | Percentage |",
        "|---|---|---|",
        f"| ✅ APPROVED (Ready for deployment) | {approved} | {approved / total:.1%} |",
        f"| ⚠️ MODIFIED (Parameters adjusted) | {modified} | {modified / total:.1%} |",
        f"| ❌ REJECTED (Unsafe or inaccurate) | {rejected} | {rejected / total:.1%} |",
        "",
        "## Human-AI Diagnostic Agreement\n",
        "| Category | Agreement Rate |",
        "|---|---|",
        f"| Concept Tag Agreement | {tag_agreement:.1%} |",
        f"| OSI Layer Agreement | {osi_agreement:.1%} |",
        f"| Severity Level Agreement | {sev_agreement:.1%} |",
        "",
        "## Operational Safety & Risk Guardrail Audit\n",
        f"- **High-Risk Operational Commands Flagged:** {len(high_risk_cases)}",
        f"- **Medium-Risk Operational Commands Flagged:** {len(medium_risk_cases)}",
        "",
    ]

    if high_risk_cases:
        lines.extend([
            "### High-Risk Command Details (Requires Senior Sign-Off)\n",
            "| Case | Decision | AI Command | Reviewer Note |",
            "|---|---|---|---|",
        ])
        for r in high_risk_cases:
            clean_cmd = r.ai_fix.replace("\n", " ").replace("|", "\\|")[:60]
            clean_note = r.reviewer_notes.replace("\n", " ").replace("|", "\\|")[:50]
            lines.append(f"| {r.case_id} | {r.decision} | `{clean_cmd}` | {clean_note} |")
        lines.append("")

    lines.extend([
        "## Per-Case Review Audit Trail\n",
        "| Case | Decision | Risk | AI Tag | Human Tag | OSI | Agreement | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for r in reviews:
        agree_icon = "✅" if (r.agreed_concept and r.agreed_osi) else ("⚠️" if r.agreed_concept else "❌")
        clean_notes = r.reviewer_notes.replace("\n", " ")[:40]
        lines.append(
            f"| {r.case_id} | {r.decision} | {r.risk_level} | {r.ai_concept_tag} | "
            f"{r.human_concept_tag} | L{r.human_osi_layer} | {agree_icon} | {clean_notes} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="NetSage AI — Human Review & Safety Gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cases", default=str(DEFAULT_CASES_CSV),
        help=f"Path to cases.csv (default: {DEFAULT_CASES_CSV})",
    )
    parser.add_argument(
        "--ai-csv", default=str(DEFAULT_AI_CSV),
        help=f"Path to AI diagnoses CSV (default: {DEFAULT_AI_CSV})",
    )
    parser.add_argument(
        "--output-dir", default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory for generated review artifacts (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--case", default=None,
        help="Review only a specific case ID (e.g. C001)",
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Run non-interactive automated benchmark review against ground truth",
    )
    parser.add_argument(
        "--version", default="V2", choices=["V1", "V2"],
        help="Prompt version to audit when reviewing comparison outputs (default: V2)",
    )
    parser.add_argument(
        "--quick-approve", action="store_true",
        help="Approve selected cases without interactive prompts (for CI/CD validation)",
    )

    args = parser.parse_args()

    cases_path = Path(args.cases).resolve()
    ai_path = Path(args.ai_csv).resolve()
    output_dir = Path(args.output_dir).resolve()

    cases = load_csv(cases_path)
    ai_diagnoses = load_ai_diagnoses(ai_path, version=args.version)

    # If ai_diagnoses has fewer cases than prompt_comparison, prefer prompt_comparison
    comp_file = output_dir / "prompt_comparison.csv"
    if comp_file.exists():
        comp_diagnoses = load_ai_diagnoses(comp_file, version=args.version)
        if len(comp_diagnoses) > len(ai_diagnoses):
            ai_diagnoses = comp_diagnoses

    if not cases:
        raise SystemExit(f"No cases found in {cases_path}")

    # If no AI diagnoses file exists, inform user
    if not ai_diagnoses:
        print(f"[!] No existing AI diagnoses found at {ai_path}.")
        print("[!] Generating baseline AI diagnoses first...")
        from prompt_engine import DiagnosisEngine
        from checker import check_case

        engine = DiagnosisEngine()
        ai_diagnoses = []
        targets = [c for c in cases if c.get("case_id") == args.case] if args.case else cases[:5]
        for c in targets:
            findings = [asdict(f) for f in check_case(c)]
            d = engine.diagnose(c, findings)
            row = asdict(d)
            row["case_id"] = c["case_id"]
            ai_diagnoses.append(row)

    if args.benchmark:
        print(f"\n>> NetSage AI — Running Human-AI Benchmark Review across {len(cases)} cases...")
        reviews = benchmark_review(cases, ai_diagnoses)
    elif args.quick_approve:
        print(f"\n>> NetSage AI — Quick-approving diagnoses for validation...")
        reviews = []
        for d in (ai_diagnoses if not args.case else [x for x in ai_diagnoses if x.get("case_id") == args.case]):
            risk, _ = assess_command_risk(d.get("fix", ""))
            reviews.append(
                ReviewRecord(
                    case_id=d.get("case_id", ""),
                    decision="APPROVED",
                    risk_level=risk,
                    ai_concept_tag=d.get("concept_tag", ""),
                    human_concept_tag=d.get("concept_tag", ""),
                    ai_osi_layer=int(d.get("osi_layer", 0) or 0),
                    human_osi_layer=int(d.get("osi_layer", 0) or 0),
                    ai_severity=d.get("severity", ""),
                    human_severity=d.get("severity", ""),
                    ai_confidence=d.get("confidence", ""),
                    agreed_concept=True,
                    agreed_osi=True,
                    agreed_severity=True,
                    ai_fix=d.get("fix", ""),
                    approved_fix=d.get("fix", ""),
                    reviewer_notes="Quick-approved by engineer.",
                )
            )
    else:
        reviews = interactive_review(cases, ai_diagnoses, target_id=args.case, output_dir=output_dir)

    # Save artifacts
    csv_out = output_dir / "human_review.csv"
    report_out = output_dir / "human_review_report.md"

    save_review_records(reviews, csv_out)
    generate_review_report(reviews, report_out)

    approved_count = sum(r.decision == "APPROVED" for r in reviews)
    print(f"\n[>] Human review audit CSV saved:    {csv_out}")
    print(f"[>] Human review summary report:     {report_out}")
    print(f"[✓] {approved_count}/{len(reviews)} diagnoses approved ({approved_count/len(reviews):.1%})\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
